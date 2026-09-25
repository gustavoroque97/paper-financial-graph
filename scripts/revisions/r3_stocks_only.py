"""
R3 — Stocks-only replication.

Question: are the paper's core results (HCM isolates a high-beta core and a
positive-alpha periphery; the core leads the periphery) driven by the ETF/CEF/REIT
component of the universe?

Two modes
---------
refilter (default, fast)
    Take the *existing* TMFG graph, induce the subgraph on individual stocks,
    recompute HCM/Pozzi on that subgraph, re-cut deciles within stocks only.
    No network re-estimation; uses only networkx.

rebuild (faithful, slower)
    Re-estimate the correlation matrix on stocks only (Ledoit-Wolf + exponential
    weights, tau=2.5, 5 annual windows), rebuild the TMFG, recompute centrality.
    Requires scikit-learn.

Outputs -> reviews/outputs/r3_*.csv

Usage
-----
python scripts/revisions/r3_stocks_only.py --mode refilter
python scripts/revisions/r3_stocks_only.py --mode rebuild --metrics hcm
"""

from __future__ import annotations

import argparse
import numpy as np
import pandas as pd

from common import (YEARS, OOS_YEARS, ensure_out, load_factors, load_returns,
                    load_window_returns, load_graph, stock_tickers, asset_class_map,
                    get_network_TMFG, compute_robust_corr_lw, hybrid_centrality,
                    pozzi_centrality, recut_deciles, bh_portfolio_returns,
                    ff3_year, aggregate_fm, perf_metrics, two_sided_p,
                    load_complete_metadata, META)


def centrality_for(year: int, universe: str, metric: str, mode: str, stocks: set,
                   meta_map: dict, tau: float = 2.5):
    """Return DataFrame [node, year, value] of the requested centrality."""
    if mode == "refilter":
        G = load_graph(year)
        if universe == "stocks":
            G = G.subgraph([n for n in G.nodes if n in stocks]).copy()
        hcm, _, _, _, _ = hybrid_centrality(G)
        vals = hcm
        if metric == "pozzi":
            vals = pozzi_centrality(G)
    else:  # rebuild
        rets = load_window_returns(year)
        if universe == "stocks":
            keep = [c for c in rets.columns if c in stocks]
            rets = rets[keep]
        corr = compute_robust_corr_lw({year: rets}, year, tau=tau)
        G = get_network_TMFG(corr)
        hcm, _, _, _, _ = hybrid_centrality(G)
        vals = hcm if metric == "hcm" else pozzi_centrality(G)

    # for pozzi: orient so that small = central (mirror the published pipeline)
    s = pd.Series(vals, name="value")
    if metric == "pozzi":
        s = -s
    return pd.DataFrame({"node": s.index, "year": str(year), "value": s.values})


def build(metric: str, mode: str, n_deciles: int, years, stocks: set, meta_map: dict,
          tau: float = 2.5):
    parts = [centrality_for(y, "stocks", metric, mode, stocks, meta_map, tau=tau) for y in years]
    cent = pd.concat(parts, ignore_index=True)
    cent = recut_deciles(cent, "value", n=n_deciles)
    return cent


def oos_portfolio_returns(cent: pd.DataFrame, year: int, decile: int) -> pd.Series:
    members = cent[(cent["year"] == str(year)) & (cent["decile"] == decile)]["node"].tolist()
    try:
        rets = load_returns(year + 1)
    except FileNotFoundError:
        return pd.Series(dtype=float)
    return bh_portfolio_returns(members, rets)


def ff3_table(cent: pd.DataFrame, factors: pd.DataFrame, metric: str, years) -> pd.DataFrame:
    rows = []
    for dec in range(1, 11):
        recs, alphas = [], []
        for y in years:
            p = oos_portfolio_returns(cent, y, dec)
            if p.empty:
                continue
            r = ff3_year(p, factors)
            if r is not None:
                recs.append(r)
                alphas.append(r["alpha"])
        agg = aggregate_fm(recs)
        if agg:
            agg["decile"] = dec
            agg["metric"] = metric
            rows.append(agg)
    return pd.DataFrame(rows)


def performance_table(cent: pd.DataFrame, metric: str, years):
    def join(series_dict):
        return pd.concat(series_dict, axis=1, join="outer").mean(axis=1)

    d1, d10 = {}, {}
    for y in years:
        a, b = oos_portfolio_returns(cent, y, 1), oos_portfolio_returns(cent, y, 10)
        if not a.empty:
            d1[f"d1_{y}"] = a
        if not b.empty:
            d10[f"d10_{y}"] = b
    comb = {**{f"d1_{k}": v for k, v in d1.items()}, **{f"d10_{k}": v for k, v in d10.items()}}
    series = {
        "Decile 1 (Central)": join(list(d1.values())),
        "Decile 10 (Peripheral)": join(list(d10.values())),
        "D1 & D10 (1/N)": join(list(comb.values())),
    }
    out = []
    for name, s in series.items():
        m = perf_metrics(s)
        if m:
            m["strategy"] = name
            m["metric"] = metric
            out.append(m)
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["refilter", "rebuild"], default="refilter")
    ap.add_argument("--metrics", default="hcm", help="comma list: hcm,pozzi")
    ap.add_argument("--years", default=",".join(str(y) for y in YEARS))
    ap.add_argument("--n-deciles", type=int, default=10)
    ap.add_argument("--tau", type=float, default=2.5, help="exp-weight decay for --mode rebuild")
    args = ap.parse_args()

    years = [int(y) for y in args.years.split(",")]
    metrics = [m.strip() for m in args.metrics.split(",")]
    out = ensure_out()
    factors = load_factors()
    stocks = stock_tickers()
    meta_map = asset_class_map()
    print(f"[R3] mode={args.mode} | stock tickers={len(stocks)}")

    for metric in metrics:
        cent = build(metric, args.mode, args.n_deciles, years, stocks, meta_map, tau=args.tau)
        cent.to_csv(out / f"r3_{metric}_{args.mode}_centrality.csv", index=False)
        if args.n_deciles == 10:
            tab = ff3_table(cent, factors, metric, [y for y in years if y + 1 in YEARS + [2025]])
            tab.to_csv(out / f"r3_{metric}_{args.mode}_ff3.csv", index=False)
            print(f"\n[R3] FF3 (stocks-only, {metric}, {args.mode}):")
            print(tab[["decile", "alpha", "alpha_t", "mkt_beta", "r_squared"]].to_string(index=False))
            perf = performance_table(cent, metric, [y for y in years if y + 1 in YEARS + [2025]])
            perf.to_csv(out / f"r3_{metric}_{args.mode}_performance.csv", index=False)
            print(f"\n[R3] Performance (stocks-only, {metric}, {args.mode}):")
            print(perf[["strategy", "cagr", "ann_vol", "sharpe", "max_drawdown"]].to_string(index=False))

    # published benchmark table for side-by-side comparison
    pub = META / "table_famamacbeth_hcm.csv"
    if pub.exists():
        full = pd.read_csv(pub).rename(columns={"Unnamed: 0": "decile"})
        full.to_csv(out / "r3_full_universe_ff3_published.csv", index=False)
        print(f"\n[R3] Copied published full-universe FF3 table -> r3_full_universe_ff3_published.csv")
    print(f"\n[R3] Done. Outputs in {out}")


if __name__ == "__main__":
    main()
