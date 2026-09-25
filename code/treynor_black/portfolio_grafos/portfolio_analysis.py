"""
Módulo de análise setorial, industrial, decis de rede e metadados de carteira.
Permite decompor as alocações das estratégias por setores da economia,
analisar tilts ativos, concentração (HHI, N efetivo), active share e fatores ponderados.
"""

from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd

from .strategy import (
    load_metadata_market_caps,
    _normalize_strategy_key,
)


def compute_sector_allocations(
    results: dict,
    strategy: str = "treynor_black",
    metric: str = "hrm",
    metadata_dir: Optional[Path] = None,
    as_percentage: bool = True,
    start_year: Optional[int] = None,
) -> pd.DataFrame:
    """
    Calculates the portfolio percentage distribution across economic sectors for each rebalancing year.
    
    Args:
        results: Dictionary returned by run_treynor_black_backtest.
        strategy: 'treynor_black', 'treynor_black_long_only' or 'benchmark'.
        metric: Network centrality metric ('hrm', 'pozzi', 'hcm').
        metadata_dir: Directory for metadata files.
        as_percentage: If True, expresses weights in percent (0 to 100%).
        start_year: Minimum year to include (e.g. 2015 to exclude warmup 2014).
        
    Returns:
        pd.DataFrame indexed by Year with Sectors in columns.
    """
    key = _normalize_strategy_key(strategy)
    weights_dict = results[key]
    if start_year is not None:
        weights_dict = {y: w for y, w in weights_dict.items() if y >= start_year}

    records = {}
    for year, w in weights_dict.items():
        meta = load_metadata_market_caps(year, metric=metric, metadata_dir=metadata_dir)
        sectors = meta["Sector"].reindex(w.index).fillna("Unclassified")
        sec_w = w.groupby(sectors).sum()
        if as_percentage:
            sec_w = sec_w * 100.0
        records[year] = sec_w

    df = pd.DataFrame(records).T.fillna(0.0)
    df.index.name = "Year"
    return df


def compute_active_sector_tilts(
    results: dict,
    strategy: str = "treynor_black",
    metric: str = "hrm",
    metadata_dir: Optional[Path] = None,
    as_percentage: bool = True,
    start_year: Optional[int] = None,
) -> pd.DataFrame:
    """
    Calculates active sector tilts relative to the market benchmark:
    Delta w_sector = w_strategy, sector - w_benchmark, sector.
    
    Args:
        results: Dictionary returned by run_treynor_black_backtest.
        strategy: 'treynor_black' or 'treynor_black_long_only'.
        metric: Centrality metric ('hrm', 'pozzi', 'hcm').
        metadata_dir: Directory of metadata files.
        as_percentage: If True, expresses active tilts in percentage points (pp).
        start_year: Minimum year to include (e.g. 2015).
        
    Returns:
        pd.DataFrame (Year x Sectors) with active tilts.
    """
    strat_sec = compute_sector_allocations(
        results, strategy=strategy, metric=metric, metadata_dir=metadata_dir, as_percentage=as_percentage, start_year=start_year
    )
    bmark_sec = compute_sector_allocations(
        results, strategy="benchmark", metric=metric, metadata_dir=metadata_dir, as_percentage=as_percentage, start_year=start_year
    )

    all_cols = sorted(list(set(strat_sec.columns).union(set(bmark_sec.columns))))
    strat_sec = strat_sec.reindex(columns=all_cols, fill_value=0.0)
    bmark_sec = bmark_sec.reindex(columns=all_cols, fill_value=0.0)

    tilts = strat_sec - bmark_sec
    tilts.index.name = "Year"
    return tilts


def compute_industry_allocations(
    results: dict,
    strategy: str = "treynor_black",
    year: Optional[int] = None,
    top_n: int = 10,
    metric: str = "hrm",
    metadata_dir: Optional[Path] = None,
    as_percentage: bool = True,
    start_year: Optional[int] = None,
) -> pd.DataFrame | pd.Series:
    """
    Calculates portfolio distribution across industries.
    """
    key = _normalize_strategy_key(strategy)
    weights_dict = results[key]
    if start_year is not None:
        weights_dict = {y: w for y, w in weights_dict.items() if y >= start_year}

    if year is not None:
        w = weights_dict[year]
        meta = load_metadata_market_caps(year, metric=metric, metadata_dir=metadata_dir)
        industries = meta["Industry"].reindex(w.index).fillna("Unclassified")
        ind_w = w.groupby(industries).sum().sort_values(ascending=False)
        if as_percentage:
            ind_w = ind_w * 100.0
        return ind_w.head(top_n)

    yearly_ind = {}
    for y, w in weights_dict.items():
        meta = load_metadata_market_caps(y, metric=metric, metadata_dir=metadata_dir)
        industries = meta["Industry"].reindex(w.index).fillna("Unclassified")
        ind_w = w.groupby(industries).sum()
        yearly_ind[y] = ind_w

    df = pd.DataFrame(yearly_ind).T.fillna(0.0)
    top_cols = df.mean().sort_values(ascending=False).head(top_n).index
    df_top = df[top_cols]
    if as_percentage:
        df_top = df_top * 100.0
    df_top.index.name = "Year"
    return df_top


def compute_decile_allocations(
    results: dict,
    strategy: str = "treynor_black",
    metric: str = "hrm",
    metadata_dir: Optional[Path] = None,
    as_percentage: bool = True,
    start_year: Optional[int] = None,
) -> pd.DataFrame:
    """
    Maps weight allocations across the 10 network centrality deciles (D1 to D10) over time.
    """
    key = _normalize_strategy_key(strategy)
    weights_dict = results[key]
    if start_year is not None:
        weights_dict = {y: w for y, w in weights_dict.items() if y >= start_year}

    decile_order = [f"decil_{d}" for d in range(1, 11)]

    records = {}
    for year, w in weights_dict.items():
        meta = load_metadata_market_caps(year, metric=metric, metadata_dir=metadata_dir)
        if "portfolio" in meta.columns:
            deciles = meta["portfolio"].reindex(w.index).fillna("Other")
        else:
            deciles = pd.Series("Other", index=w.index)
        dec_w = w.groupby(deciles).sum()
        if as_percentage:
            dec_w = dec_w * 100.0
        records[year] = dec_w

    df = pd.DataFrame(records).T.fillna(0.0)
    cols = [c for c in decile_order if c in df.columns] + [c for c in df.columns if c not in decile_order]
    df = df[cols]
    df.index.name = "Year"
    return df


def compute_portfolio_metadata_summary(
    results: dict,
    strategy: str = "treynor_black",
    metric: str = "hrm",
    metadata_dir: Optional[Path] = None,
    start_year: Optional[int] = None,
) -> pd.DataFrame:
    """
    Generates annual summary of portfolio concentration and characteristics:
    - Total Assets, Long Positions, Short Positions
    - HHI & Effective N (1/HHI)
    - Active Share (%) vs. Benchmark
    - Top 10 Weight (%)
    - Weighted Beta & Weighted Momentum
    - Weighted Market Cap ($B)
    - Net & Gross Exposure (%)
    """
    key = _normalize_strategy_key(strategy)
    strat_weights = results[key]
    bmark_weights = results["weights_benchmark"]

    if start_year is not None:
        strat_weights = {y: w for y, w in strat_weights.items() if y >= start_year}

    records = []
    for year, w in strat_weights.items():
        w_bmark = bmark_weights[year]
        meta = load_metadata_market_caps(year, metric=metric, metadata_dir=metadata_dir)

        n_total = int((w.abs() > 1e-6).sum())
        n_long = int((w > 1e-6).sum())
        n_short = int((w < -1e-6).sum())

        w_norm = w / w.abs().sum() if w.abs().sum() > 0 else w
        hhi = float((w_norm ** 2).sum())
        n_effective = float(1.0 / hhi) if hhi > 0 else 0.0

        all_tickers = sorted(list(set(w.index).union(set(w_bmark.index))))
        w_aligned = w.reindex(all_tickers).fillna(0.0)
        wb_aligned = w_bmark.reindex(all_tickers).fillna(0.0)
        active_share = float(0.5 * (w_aligned - wb_aligned).abs().sum() * 100.0)

        top10_weight = float(w.sort_values(ascending=False).head(10).sum() * 100.0)

        net_exposure = float(w.sum() * 100.0)
        gross_exposure = float(w.abs().sum() * 100.0)

        beta_col = f"beta_{year}"
        if beta_col in meta.columns:
            beta_vals = meta[beta_col].reindex(w.index).fillna(1.0)
            weighted_beta = float((w * beta_vals).sum())
        else:
            weighted_beta = np.nan

        mom_col = f"momentum_{year}"
        if mom_col in meta.columns:
            mom_vals = meta[mom_col].reindex(w.index).fillna(0.0)
            weighted_mom = float((w * mom_vals).sum())
        else:
            weighted_mom = np.nan

        if "mcap" in meta.columns:
            mcap_vals = meta["mcap"].reindex(w.index).fillna(0.0)
            weighted_mcap_bi = float((w * mcap_vals).sum() / 1e9)
        else:
            weighted_mcap_bi = np.nan

        records.append(
            {
                "Year": year,
                "Total Assets": n_total,
                "Long Positions": n_long,
                "Short Positions": n_short,
                "Effective N (1/HHI)": round(n_effective, 1),
                "HHI": round(hhi, 4),
                "Active Share (%)": active_share,
                "Top 10 Weight (%)": top10_weight,
                "Weighted Beta": weighted_beta,
                "Weighted Momentum": weighted_mom,
                "Weighted Market Cap ($B)": weighted_mcap_bi,
                "Net Exposure (%)": net_exposure,
                "Gross Exposure (%)": gross_exposure,
            }
        )

    df_res = pd.DataFrame(records).set_index("Year")
    return df_res


def compute_fixed_income_blends(
    portfolio_returns: pd.Series,
    rf_series: pd.Series,
    rf_weights: Optional[list[float]] = None,
) -> dict[str, pd.Series]:
    """
    Computes daily returns for convex combinations between Fixed Income (RF) and a risky portfolio:
    R_blend(t) = w_rf * RF(t) + (1 - w_rf) * R_portfolio(t)
    
    Args:
        portfolio_returns: Daily returns of the risky portfolio.
        rf_series: Daily returns of the risk-free rate.
        rf_weights: List of weights in fixed income (default: 0.0 to 0.50 in 5% steps, plus 1.0).
        
    Returns:
        dict mapping label -> pd.Series of daily blend returns.
    """
    if rf_weights is None:
        rf_weights = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 1.0]

    aligned = pd.concat([portfolio_returns.rename("portfolio"), rf_series.rename("rf")], axis=1).dropna()
    r_p = aligned["portfolio"]
    r_rf = aligned["rf"]

    blends = {}
    for w in rf_weights:
        blend_s = w * r_rf + (1.0 - w) * r_p
        if w == 0.0:
            label = "0% RF (100% Equity)"
        elif w == 1.0:
            label = "100% Pure Fixed Income"
        else:
            label = f"{int(round(w * 100))}% RF / {int(round((1.0 - w) * 100))}% Equity"
        blends[label] = blend_s

    return blends


def evaluate_fixed_income_blends(
    portfolio_returns: pd.Series,
    rf_series: pd.Series,
    rf_weights: Optional[list[float]] = None,
    trading_days_per_year: int = 252,
) -> pd.DataFrame:
    """
    Evaluates risk and return performance metrics across convex combinations with fixed income:
    - CAGR (%)
    - Annual Volatility (%)
    - Sharpe Ratio (annualized excess return over RF)
    - Max Drawdown (%)
    - Calmar Ratio
    - Sortino Ratio
    - Total Return (%)
    """
    if rf_weights is None:
        rf_weights = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 1.0]

    aligned = pd.concat([portfolio_returns.rename("portfolio"), rf_series.rename("rf")], axis=1).dropna()
    r_p = aligned["portfolio"]
    r_rf = aligned["rf"]
    n_days = len(aligned)
    years = n_days / float(trading_days_per_year)

    records = []
    for w in rf_weights:
        blend_s = w * r_rf + (1.0 - w) * r_p

        cum_wealth = (1.0 + blend_s).cumprod()
        tot_ret = float(cum_wealth.iloc[-1] - 1.0)
        cagr = float(cum_wealth.iloc[-1] ** (1.0 / years) - 1.0) if cum_wealth.iloc[-1] > 0 else -1.0

        daily_std = float(blend_s.std(ddof=1))
        ann_vol = daily_std * np.sqrt(trading_days_per_year)

        excess_mean = float((blend_s - r_rf).mean()) * trading_days_per_year
        sharpe_excess = (excess_mean / ann_vol) if ann_vol > 1e-6 else 0.0

        mean_ret_ann = float(blend_s.mean()) * trading_days_per_year
        sharpe_zero_rf = (mean_ret_ann / ann_vol) if ann_vol > 1e-6 else np.nan

        # Sortino with target = RF (Standard excess Sortino over total sample N)
        downside_rf = np.minimum(blend_s - r_rf, 0.0)
        downside_var_rf = float((downside_rf ** 2).mean())
        if downside_var_rf > 1e-12:
            downside_std_rf = np.sqrt(downside_var_rf) * np.sqrt(trading_days_per_year)
            sortino_rf = (excess_mean / downside_std_rf) if downside_std_rf > 1e-6 else np.nan
        else:
            sortino_rf = np.nan

        # Sortino with MAR = 0.0% (Zero-threshold Sortino over total sample N)
        downside_zero = np.minimum(blend_s, 0.0)
        downside_var_zero = float((downside_zero ** 2).mean())
        if downside_var_zero > 1e-12:
            downside_std_zero = np.sqrt(downside_var_zero) * np.sqrt(trading_days_per_year)
            sortino_zero = (mean_ret_ann / downside_std_zero) if downside_std_zero > 1e-6 else np.nan
        else:
            sortino_zero = np.nan

        peak = cum_wealth.cummax()
        dd = (cum_wealth - peak) / peak
        max_dd = float(dd.min())
        calmar = (cagr / abs(max_dd)) if abs(max_dd) > 1e-6 else np.nan

        if w == 0.0:
            label = "0% RF (100% Equity)"
        elif w == 1.0:
            label = "100% Pure Fixed Income"
        else:
            label = f"{int(round(w * 100))}% RF / {int(round((1.0 - w) * 100))}% Equity"

        records.append(
            {
                "Allocation Label": label,
                "RF Weight (%)": float(w * 100.0),
                "Equity Weight (%)": float((1.0 - w) * 100.0),
                "CAGR (%)": float(cagr * 100.0),
                "Annual Volatility (%)": float(ann_vol * 100.0),
                "Sharpe Ratio (vs RF)": float(sharpe_excess),
                "Sharpe (Zero RF)": float(sharpe_zero_rf) if not np.isnan(sharpe_zero_rf) else np.nan,
                "Sortino Ratio (vs RF)": float(sortino_rf) if not np.isnan(sortino_rf) else np.nan,
                "Sortino (MAR=0)": float(sortino_zero) if not np.isnan(sortino_zero) else np.nan,
                "Max Drawdown (%)": float(max_dd * 100.0),
                "Calmar Ratio": float(calmar) if not np.isnan(calmar) else np.nan,
                "Total Return (%)": float(tot_ret * 100.0),
            }
        )

    df_eval = pd.DataFrame(records).set_index("Allocation Label")
    return df_eval


