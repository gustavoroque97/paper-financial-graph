"""
R8 — Multiple-testing control and sub-period robustness.

Three analyses
--------------
1. subperiod    : recompute FF3 (Fama-MacBeth-style aggregation) and performance
                  for 2015-2019 vs 2020-2024.
2. multiplicity : pooled out-of-sample FF3 alphas for the ten deciles, with
                  White Reality-Check block bootstrap and Holm-Bonferroni
                  adjusted p-values.
3. deciles      : decile-count sensitivity (5 / 10 / 20) re-cut from the
                  centrality table cached by `r3_stocks_only.py` (run it first).

Outputs -> reviews/outputs/r8_*.csv
"""

from __future__ import annotations

import argparse
import numpy as np
import pandas as pd

from common import (YEARS, ensure_out, load_factors, load_returns,
                    load_decile_returns, load_complete_metadata, bh_portfolio_returns,
                    oos_bh_returns, ff3_year, aggregate_fm, perf_metrics, nw_ols,
                    two_sided_p, holm_bonferroni, block_bootstrap_fwer, recut_deciles, OUT)


def tag(metric: str) -> str:
    return "hrm" if metric.lower() in ("hcm", "hrm") else metric.lower()


# --------------------------------------------------------------------------
# Strategy series
# --------------------------------------------------------------------------
def performance_series(metric: str, deciles, years) -> pd.Series:
    """Concatenated OOS buy-and-hold strategy return (matches the performance tables)."""
    parts = [oos_bh_returns(metric, deciles, y) for y in years]
    parts = [p for p in parts if len(p) > 0]
    return pd.concat(parts).sort_index() if parts else pd.Series(dtype=float)


def oos_decile_return(metric: str, decile: int, year: int) -> pd.Series:
    """Decile formed at year t (metadata), evaluated on year t+1 returns."""
    meta = load_complete_metadata(metric)
    yr = meta["year"].astype(str)
    members = meta[(yr == str(year)) & (meta["portfolio"] == f"decil_{decile}")]["Ticker"].tolist()
    try:
        rets = load_returns(year + 1)
    except FileNotFoundError:
        return pd.Series(dtype=float)
    return bh_portfolio_returns(members, rets)


def oos_matrix(metric: str, years) -> pd.DataFrame:
    cols = {}
    for d in range(1, 11):
        parts = [oos_decile_return(metric, d, y) for y in years]
        parts = [p for p in parts if len(p) > 0]
        if parts:
            cols[f"D{d}"] = pd.concat(parts).sort_index()
    return pd.DataFrame(cols)


# --------------------------------------------------------------------------
# Analyses
# --------------------------------------------------------------------------
def subperiod(metric: str, periods: dict):
    rows = []
    for label, years in periods.items():
        for name, dec in [("D1", [1]), ("D10", [10]), ("D1&D10", [1, 10])]:
            s = performance_series(metric, dec, years)
            if s.empty:
                continue
            m = perf_metrics(s)
            m.update({"period": label, "strategy": name, "metric": metric})
            rows.append(m)
    return pd.DataFrame(rows)


def subperiod_ff3(metric: str, periods: dict):
    factors = load_factors()
    rows = []
    for label, years in periods.items():
        for d in [1, 10]:
            recs = []
            for y in years:
                p = oos_decile_return(metric, d, y)
                if len(p) == 0:
                    continue
                r = ff3_year(p, factors)
                if r:
                    recs.append(r)
            agg = aggregate_fm(recs)
            if agg:
                agg.update({"period": label, "decile": d, "metric": metric})
                rows.append(agg)
    return pd.DataFrame(rows)


def multiplicity(metric: str, years):
    factors = load_factors()
    M = oos_matrix(metric, years)
    if M.empty:
        return pd.DataFrame(), {}
    # pooled FF3 per decile
    rows = []
    tstats = {}
    for col in M.columns:
        r = ff3_year(M[col], factors)
        if r:
            p = two_sided_p(r["alpha_t"])
            rows.append({"decile": col, "alpha": r["alpha"], "t": r["alpha_t"], "p": p,
                         "mkt_beta": r["mkt_beta"], "r_squared": r["r_squared"]})
            tstats[col] = p
    tab = pd.DataFrame(rows)
    holm = holm_bonferroni(tstats)
    tab["p_holm"] = tab["decile"].map(holm)

    # reality check on mean excess returns (recenter under H0)
    ex = M.sub(factors["RF"], axis=0).dropna(how="all")
    rc = block_bootstrap_fwer(ex, B=2000, block=20, seed=7)
    return tab, rc


def decile_sensitivity(metric: str, centrality_csv: str, factors, years):
    p = OUT / centrality_csv
    if not p.exists():
        print(f"[R8] centrality cache {p} not found — run r3_stocks_only.py first. Skipping.")
        return pd.DataFrame()
    cent = pd.read_csv(p)
    rows = []
    for n in (5, 10, 20):
        c = recut_deciles(cent[["node", "year", "value"]].copy(), "value", n=n)
        for d in (1, n):
            recs = []
            for y in years:
                members = c[(c["year"] == str(y)) & (c["decile"] == d)]["node"].tolist()
                try:
                    rets = load_returns(y + 1)
                except FileNotFoundError:
                    continue
                r = ff3_year(bh_portfolio_returns(members, rets), factors)
                if r:
                    recs.append(r)
            agg = aggregate_fm(recs)
            if agg:
                agg.update({"n_deciles": n, "extreme": "central" if d == 1 else "peripheral"})
                rows.append(agg)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", default="hcm")
    ap.add_argument("--years", default=",".join(str(y) for y in range(2015, 2025)))
    args = ap.parse_args()

    out = ensure_out()
    factors = load_factors()
    years = [int(y) for y in args.years.split(",")]
    periods = {"2015-2019": list(range(2015, 2020)), "2020-2024": list(range(2020, 2025))}

    sp = subperiod(args.metric, periods)
    sp.to_csv(out / f"r8_{args.metric}_subperiod_performance.csv", index=False)
    spf = subperiod_ff3(args.metric, periods)
    spf.to_csv(out / f"r8_{args.metric}_subperiod_ff3.csv", index=False)
    print("\n[R8] Sub-period FF3:")
    if not spf.empty:
        print(spf[["period", "decile", "alpha", "alpha_t", "mkt_beta", "r_squared"]].to_string(index=False))

    tab, rc = multiplicity(args.metric, years)
    if not tab.empty:
        tab.to_csv(out / f"r8_{args.metric}_multiplicity.csv", index=False)
        print("\n[R8] Pooled OOS FF3 with Holm-adjusted p-values:")
        print(tab.to_string(index=False))
        print(f"[R8] Reality-Check (max alpha) stat={rc.get('stat'):.3f} p={rc.get('p_value'):.4f} "
              f"(B={rc.get('B')}, block={rc.get('block')})")

    sens = decile_sensitivity(args.metric, f"r3_{args.metric}_refilter_centrality.csv", factors, years)
    if not sens.empty:
        sens.to_csv(out / f"r8_{args.metric}_decile_sensitivity.csv", index=False)
        print("\n[R8] Decile-count sensitivity:")
        print(sens[["n_deciles", "extreme", "alpha", "alpha_t", "mkt_beta"]].to_string(index=False))

    print(f"\n[R8] Done. Outputs in {out}")


if __name__ == "__main__":
    main()
