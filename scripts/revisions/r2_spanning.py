"""
R2 — Spanning tests: is the peripheral alpha just size / low-beta in disguise?

Two designs (no volume data locally, so a true Amihud illiquidity factor is not
possible here and is flagged as such):

1. size double-sort
   Within each year and each market-capitalization tercile, re-sort the universe
   by HCM and take the extreme deciles.  If the peripheral alpha survives inside
   the *large-cap* tercile, it is not merely a small-cap premium.

2. BAB spanning
   Build a betting-against-beta (BAB) factor (low-beta minus high-beta decile,
   equal-weighted, OOS) and add it to the FF3 regression of the peripheral
   portfolio.  If alpha survives the BAB factor, it is not pure low-beta.

Outputs -> reviews/outputs/r2_*.csv
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from common import (YEARS, OOS_YEARS, ensure_out, load_factors, load_returns,
                    load_graph, load_complete_metadata, hybrid_centrality,
                    bh_portfolio_returns, ff3_year, aggregate_fm, nw_ols)


def full_universe_centrality(years=YEARS) -> pd.DataFrame:
    rows = []
    for y in years:
        G = load_graph(y)
        hcm, _, _, _, _ = hybrid_centrality(G)
        rows.append(pd.DataFrame({"Ticker": list(hcm), "year": str(y), "hcm": list(hcm.values())}))
    return pd.concat(rows, ignore_index=True)


def mcap_long(meta: pd.DataFrame) -> pd.DataFrame:
    out = []
    for y in YEARS:
        col = f"mcap_{y}"
        if col not in meta.columns:
            continue
        sub = meta[meta["year"].astype(str) == str(y)][["Ticker", col]].copy()
        sub = sub.rename(columns={col: "mcap"})
        sub["year"] = str(y)
        out.append(sub)
    return pd.concat(out, ignore_index=True)


def oos_bh(members, year):
    try:
        rets = load_returns(year + 1)
    except FileNotFoundError:
        return pd.Series(dtype=float)
    return bh_portfolio_returns(members, rets)


def size_double_sort(meta, factors, years):
    cent = full_universe_centrality(years)
    d = cent.merge(mcap_long(meta), on=["Ticker", "year"], how="inner")
    d = d[pd.to_numeric(d["mcap"], errors="coerce").notna()]
    d["mcap"] = pd.to_numeric(d["mcap"], errors="coerce")
    d["size_t"] = d.groupby("year")["mcap"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 3, labels=False))
    d["hcm_d"] = d.groupby(["year", "size_t"])["hcm"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 10, labels=False) + 1)

    rows = []
    for st, label in [(0, "Small"), (1, "Mid"), (2, "Large")]:
        sub = d[d["size_t"] == st]
        for dec, side in [(1, "Central"), (10, "Peripheral")]:
            recs = []
            for y in years:
                members = sub[(sub["year"] == str(y)) & (sub["hcm_d"] == dec)]["Ticker"].tolist()
                p = oos_bh(members, y)
                if len(p):
                    r = ff3_year(p, factors)
                    if r:
                        recs.append(r)
            agg = aggregate_fm(recs)
            if agg:
                agg.update({"size_tercile": label, "side": side, "decile": dec})
                rows.append(agg)
    return pd.DataFrame(rows)


def bab_spanning(meta, factors, years):
    # BAB factor: low-beta minus high-beta decile, OOS, equal weighted
    meta = meta.copy()
    meta["year"] = meta["year"].astype(str)
    bab_parts = []
    for y in years:
        col = f"beta_{y}"
        if col not in meta.columns:
            continue
        sub = meta[meta["year"] == str(y)].copy()
        sub[col] = pd.to_numeric(sub[col], errors="coerce")
        sub = sub.dropna(subset=[col])
        try:
            rets = load_returns(y + 1)
        except FileNotFoundError:
            continue
        below = sub[col] <= sub[col].quantile(1 / 3)
        above = sub[col] >= sub[col].quantile(2 / 3)
        r_low = bh_portfolio_returns(sub.loc[below, "Ticker"].tolist(), rets)
        r_high = bh_portfolio_returns(sub.loc[above, "Ticker"].tolist(), rets)
        if len(r_low) and len(r_high):
            bab_parts.append((r_low - r_high).rename(f"bab_{y}"))
    if not bab_parts:
        return pd.DataFrame(), {}
    bab = pd.concat(bab_parts).sort_index()

    # peripheral OOS series
    per = []
    for y in years:
        members = meta[(meta["year"] == str(y)) & (meta["portfolio"] == "decil_10")]["Ticker"].tolist()
        per.append(oos_bh(members, y))
    per = pd.concat([p for p in per if len(p)]).sort_index()

    df = pd.concat([per.rename("r"), bab.rename("BAB"), factors], axis=1, join="inner").dropna()
    res = {}
    if len(df) > 60:
        y3 = (df["r"] - df["RF"]).values
        X3 = df[["Mkt-RF", "SMB", "HML"]].values
        b3, se3, r2_3 = nw_ols(y3, X3)
        X4 = df[["Mkt-RF", "SMB", "HML", "BAB"]].values
        b4, se4, r2_4 = nw_ols(y3, X4)
        res = {
            "alpha_ff3": b3[0] * 252, "alpha_ff3_t": b3[0] / se3[0],
            "alpha_ff3_bab": b4[0] * 252, "alpha_ff3_bab_t": b4[0] / se4[0],
            "bab_loading": b4[4], "bab_t": b4[4] / se4[4],
            "r2_ff3": r2_3, "r2_ff3_bab": r2_4, "n": len(df),
        }
    return pd.DataFrame([res]), res


def main():
    out = ensure_out()
    factors = load_factors()
    meta = load_complete_metadata("hcm")
    years = [y for y in YEARS if y + 1 in YEARS + [2025]]

    print("[R2] Size double-sort ...")
    sd = size_double_sort(meta, factors, years)
    if not sd.empty:
        sd.to_csv(out / "r2_size_doublesort.csv", index=False)
        print(sd[["size_tercile", "side", "alpha", "alpha_t", "mkt_beta", "r_squared"]].to_string(index=False))

    print("\n[R2] BAB spanning ...")
    bab_tab, res = bab_spanning(meta, factors, years)
    if not bab_tab.empty:
        bab_tab.to_csv(out / "r2_bab_spanning.csv", index=False)
        print(bab_tab.to_string(index=False))
    print("[R2] Note: illiquidity (Amihud) spanning needs volume data, not available here.")


if __name__ == "__main__":
    main()
