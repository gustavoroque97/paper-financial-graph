"""
S1 — Liquidity-conditioned transaction costs and capacity.

The paper applies a flat 10 bps drag to all turnover.  Because the peripheral
portfolio holds small / illiquid names, this is optimistic.  This script

1. re-prices the decile and D1&D10 combination strategies under alternative cost
   grids (flat vs liquidity-tiered);
2. produces a heuristic capacity curve using the common square-root impact law
   with a configurable ADV proxy (market cap x assumed daily turnover velocity).

If the Treynor-Black strategy daily returns are exported to CSV (one column of
returns, date index), pass `--strategy-returns path.csv` and the same analysis is
applied to the live strategy.  The TB notebooks currently save only figures, so
exporting those returns is a prerequisite for the strategy-level numbers.

Outputs -> reviews/outputs/s1_*.csv

Assumptions that MUST be shown in the paper
-------------------------------------------
* velocity         : assumed fraction of market cap traded per day (default 0.5%).
* impact_coef      : coefficient of the square-root impact law (default 0.1).
* tiered cost grid : ETF/CEF 10 bps; D1 25 bps; D10 75 bps; middle 40 bps.
"""

from __future__ import annotations

import argparse
import numpy as np
import pandas as pd

from common import (YEARS, ensure_out, load_decile_returns, load_complete_metadata,
                    oos_bh_returns, perf_metrics, flat_cost_bps, tiered_cost_bps,
                    apply_annual_cost, capacity_curve, META)


def strategy_series(metric: str, deciles, years) -> pd.Series:
    """OOS buy-and-hold return of one or several deciles (matches the paper)."""
    parts = [oos_bh_returns(metric, deciles, y) for y in years]
    parts = [p for p in parts if len(p) > 0]
    return pd.concat(parts).sort_index() if parts else pd.Series(dtype=float)


def combination_series(metric: str, years) -> pd.Series:
    return strategy_series(metric, [1, 10], years)


def turnover_table(metric: str) -> pd.DataFrame:
    tag = "hcm" if metric.lower() in ("hcm", "hrm") else metric.lower()
    p = META / f"turnover_rate_table_{tag}.csv"
    df = pd.read_csv(p)
    df["year"] = df["year"].astype(int)
    return df


def turnover_map(metric: str, which: str) -> dict:
    """``which`` in {'Central (D1)', 'Peripheral (D10)'}."""
    df = turnover_table(metric)
    return dict(zip(df["year"], df[which] / 100.0))


def adv_proxy(metric: str, decile: int, years, velocity: float) -> float:
    """Average daily dollar-volume proxy for the decile (sum of member mcap x velocity)."""
    meta = load_complete_metadata(metric)
    meta["year"] = meta["year"].astype(str)
    totals = []
    for y in years:
        sub = meta[(meta["year"] == str(y)) & (meta["portfolio"] == f"decil_{decile}")]
        col = f"mcap_{y}"
        if col in sub.columns:
            vals = pd.to_numeric(sub[col], errors="coerce")
            totals.append(float(vals.sum(skipna=True)))
    return (np.mean(totals) * velocity) if totals else np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", default="hcm")
    ap.add_argument("--years", default=",".join(str(y) for y in YEARS))
    ap.add_argument("--velocity", type=float, default=0.005, help="daily turnover velocity of mcap")
    ap.add_argument("--impact-coef", type=float, default=0.1)
    ap.add_argument("--strategy-returns", default=None, help="optional CSV of TB strategy daily returns")
    args = ap.parse_args()

    out = ensure_out()
    years = [int(y) for y in args.years.split(",")]
    metric = args.metric

    # ---- 1. cost re-pricing on deciles / combination ---------------------
    turn_d1 = turnover_map(metric, "Central (D1)")
    turn_d10 = turnover_map(metric, "Peripheral (D10)")
    turn_comb = {y: 0.5 * (turn_d1.get(y, np.nan) + turn_d10.get(y, np.nan)) for y in turn_d1}

    strategies = {
        "D1": (strategy_series(metric, [1], years), turn_d1, tiered_cost_bps, {"decile": 1}),
        "D10": (strategy_series(metric, [10], years), turn_d10, tiered_cost_bps, {"decile": 10}),
        "D1&D10": (combination_series(metric, years), turn_comb, tiered_cost_bps, {"decile": 10}),
    }
    rows = []
    for name, (s, turn, cost_fn, kw) in strategies.items():
        if s.empty:
            continue
        gross = perf_metrics(s)
        net_flat = perf_metrics(apply_annual_cost(s, turn, flat_cost_bps))
        net_tiered = perf_metrics(apply_annual_cost(s, turn, lambda **k: cost_fn(**kw)))
        rows.append({
            "strategy": name, "metric": metric,
            "mean_turnover": np.nanmean(list(turn.values())),
            "cagr_gross": gross.get("cagr"), "sharpe_gross": gross.get("sharpe"),
            "cagr_flat10": net_flat.get("cagr"), "sharpe_flat10": net_flat.get("sharpe"),
            "cagr_tiered": net_tiered.get("cagr"), "sharpe_tiered": net_tiered.get("sharpe"),
        })
    cost_tab = pd.DataFrame(rows)
    cost_tab.to_csv(out / f"s1_{metric}_cost_repricing.csv", index=False)
    print(f"\n[S1] Cost re-pricing ({metric}):")
    print(cost_tab.to_string(index=False))

    # ---- 2. capacity curve for the peripheral strategy -------------------
    alpha = 0.1013  # HCM peripheral OOS FF3 alpha (Table 5); override below if available
    pub = META / f"table_famamacbeth_{'hcm' if metric in ('hcm', 'hrm') else metric}.csv"
    if pub.exists():
        t = pd.read_csv(pub)
        try:
            alpha = float(t.loc[t.iloc[:, 0].astype(str).str.contains("10"), "Alpha"].iloc[0])
        except Exception:
            pass
    adv_d10 = adv_proxy(metric, 10, years, args.velocity)
    turn10 = float(np.nanmean(list(turn_d10.values())))
    cap = capacity_curve(alpha, turn10, adv_d10, impact_coef=args.impact_coef,
                         aum_grid=np.array([1e6, 5e6, 1e7, 5e7, 1e8, 5e8, 1e9, 5e9, 1e10]))
    cap["metric"] = metric
    cap["adv_proxy"] = adv_d10
    cap.to_csv(out / f"s1_{metric}_capacity.csv", index=False)
    print(f"\n[S1] Capacity curve ({metric}, ADV proxy={adv_d10:,.0f}, alpha={alpha:.4f}):")
    print(cap.to_string(index=False))

    # ---- 3. optional: live TB strategy ----------------------------------
    if args.strategy_returns:
        s = pd.read_csv(args.strategy_returns, index_col=0, parse_dates=True).iloc[:, 0]
        gross = perf_metrics(s)
        tiers = {name: perf_metrics(apply_annual_cost(s, turn10, fn))
                 for name, fn in [("flat10", flat_cost_bps), ("tiered", lambda **k: tiered_cost_bps(decile=10))]}
        oos = pd.DataFrame([{"strategy": "TB", **gross,
                             "cagr_flat10": tiers["flat10"].get("cagr"),
                             "cagr_tiered": tiers["tiered"].get("cagr")}])
        oos.to_csv(out / f"s1_{metric}_tb_strategy.csv", index=False)
        print("\n[S1] TB strategy cost analysis:")
        print(oos.to_string(index=False))

    print(f"\n[S1] Done. Outputs in {out}")


if __name__ == "__main__":
    main()
