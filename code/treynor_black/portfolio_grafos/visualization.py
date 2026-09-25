"""
Visualization module for comparative analysis of cumulative returns,
drawdowns, sector distributions, and factor loadings in financial portfolios.

Follows the clean, minimalist publication aesthetics of 'paper-financial-graph':
- Color palette:
  * Treynor-Black Unconstrained / Peripheral / Active: #2E5C6E (Deep Teal / Petrol Blue)
  * Treynor-Black Long-Only / Central / Pozzi: #22125F (Deep Navy / Violet)
  * Market Benchmark (Market Cap): #A93226 (Crimson Red highlight)
  * Fixed Income / Risk-Free / Inactive: #7F8C8D / #BDC3C7 (Slate Gray)
- Minimalist paper style:
  * No titles (publication ready for LaTeX captions)
  * No grids (clean white background)
  * Despined top and right axes
  * Frameless, lightweight legends
"""

from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Canonical Color Constants from paper-financial-graph
COLOR_UNCONSTRAINED = "#2E5C6E"  # Petrol Blue / Deep Teal (HRM & Peripheral active strategy)
COLOR_LONG_ONLY = "#22125F"      # Deep Navy / Violet (Pozzi & Central benchmark/strategy)
COLOR_BENCHMARK = "#A93226"      # Crimson Red (Market Cap highlight)
COLOR_RF = "#7F8C8D"             # Slate Gray (Risk-Free / Fixed Income)
COLOR_MUTED = "#BDC3C7"          # Light Gray (Intermediate deciles / reference)

STRATEGY_COLORS = {
    "Treynor-Black (Unconstrained)": COLOR_UNCONSTRAINED,
    "Treynor-Black Unconstrained (HCM)": COLOR_UNCONSTRAINED,
    "Treynor-Black Unconstrained (HRM)": COLOR_UNCONSTRAINED,
    "Treynor-Black (Long-Only)": COLOR_LONG_ONLY,
    "Treynor-Black Long-Only (HCM)": COLOR_LONG_ONLY,
    "Treynor-Black Long-Only (HRM)": COLOR_LONG_ONLY,
    "Treynor-Black Unconstrained (Pozzi)": "#3A738A",
    "Treynor-Black Long-Only (Pozzi)": "#554B92",
    "Benchmark (Market Cap)": COLOR_BENCHMARK,
    "Market Benchmark": COLOR_BENCHMARK,
    "Decile 1 (Central)": COLOR_LONG_ONLY,
    "Decil 1 (Centrais)": COLOR_LONG_ONLY,
    "Decile 1 (Central - HCM)": COLOR_LONG_ONLY,
    "Decil 1 (Centrais - HCM)": COLOR_LONG_ONLY,
    "Decile 10 (Peripheral)": COLOR_UNCONSTRAINED,
    "Decil 10 (Periféricas)": COLOR_UNCONSTRAINED,
    "Decile 10 (Peripheral - HCM)": COLOR_UNCONSTRAINED,
    "Decil 10 (Periféricas - HCM)": COLOR_UNCONSTRAINED,
    "100% Pure Fixed Income": COLOR_RF,
}


def setup_plot_style():
    """Configures clean, minimalist paper aesthetics: white background, no grid, no clutter."""
    sns.set_theme(style="white", context="paper")
    plt.rcParams.update(
        {
            "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
            "axes.edgecolor": "#333333",
            "axes.linewidth": 0.8,
            "axes.grid": False,
            "grid.color": "none",
            "grid.alpha": 0.0,
            "legend.frameon": False,
            "figure.autolayout": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.edgecolor": "none",
        }
    )


def plot_strategy_comparison(
    returns_dict: dict[str, pd.Series],
    title: Optional[str] = None,
    save_path: Optional[Path] = None,
    figsize: tuple[int, int] = (14, 9),
) -> plt.Figure:
    """
    Generates a 2-panel comparative chart:
    1. Cumulative Wealth Growth (Wealth Index, log scale)
    2. Drawdown Dynamics (Underwater Chart)
    """
    setup_plot_style()

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=figsize, sharex=True, gridspec_kw={"height_ratios": [2.2, 1.0]}
    )

    # 1. Cumulative Return Curve
    for name, s in returns_dict.items():
        cum_ret = (1.0 + s).cumprod()
        color = STRATEGY_COLORS.get(name, "#333333")

        is_primary = "Treynor-Black" in name or "Benchmark" in name
        linewidth = 2.2 if is_primary else 1.2
        linestyle = "-" if is_primary else "--"
        alpha = 1.0 if is_primary else 0.55

        ax1.plot(
            cum_ret.index,
            cum_ret.values,
            label=f"{name} ({cum_ret.iloc[-1]:.2f}x)",
            linewidth=linewidth,
            linestyle=linestyle,
            color=color,
            alpha=alpha,
        )

    ax1.set_ylabel("Cumulative Wealth (Base = 1.0)", fontsize=11)
    ax1.legend(loc="upper left", fontsize=10, frameon=False)
    ax1.set_yscale("log")
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.1f}x" if y < 10 else f"{int(y)}x"))
    ax1.grid(False)
    sns.despine(ax=ax1, top=True, right=True)

    # 2. Drawdowns (Underwater Chart)
    for name, s in returns_dict.items():
        if "decil 10" in name.lower() or "decile 10" in name.lower():
            continue
        cum_ret = (1.0 + s).cumprod()
        peak = cum_ret.cummax()
        dd = (cum_ret - peak) / peak
        color = STRATEGY_COLORS.get(name, "#333333")

        is_primary = "Treynor-Black" in name or "Benchmark" in name
        linewidth = 1.8 if is_primary else 1.0
        alpha = 0.9 if is_primary else 0.5

        ax2.plot(
            dd.index,
            dd.values * 100.0,
            label=f"{name} ({dd.min() * 100.0:.1f}%)",
            linewidth=linewidth,
            color=color,
            alpha=alpha,
        )

    ax2.set_ylabel("Drawdown (%)", fontsize=11)
    ax2.set_xlabel("Date", fontsize=11)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax2.axhline(0, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
    ax2.legend(loc="lower left", fontsize=9, frameon=False)
    ax2.grid(False)
    sns.despine(ax=ax2, top=True, right=True)

    plt.tight_layout()

    if save_path is not None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_annual_returns_bar(
    returns_dict: dict[str, pd.Series],
    title: Optional[str] = None,
    save_path: Optional[Path] = None,
    figsize: tuple[int, int] = (12, 5),
) -> plt.Figure:
    """
    Generates a grouped bar chart comparing annual returns across strategies.
    """
    setup_plot_style()

    annual_data = {}
    for name, s in returns_dict.items():
        if "decil" in name.lower() or "decile" in name.lower():
            continue
        ann = s.groupby(s.index.year).apply(lambda x: (1.0 + x).prod() - 1.0) * 100.0
        annual_data[name] = ann

    df_ann = pd.DataFrame(annual_data)

    fig, ax = plt.subplots(figsize=figsize)
    bar_colors = [STRATEGY_COLORS.get(c, "#555555") for c in df_ann.columns]

    df_ann.plot(kind="bar", ax=ax, width=0.75, color=bar_colors, edgecolor="none")

    ax.set_ylabel("Annual Return (%)", fontsize=11)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.axhline(0, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax.legend(title="", fontsize=10, frameon=False)
    ax.grid(False)
    sns.despine(ax=ax, top=True, right=True)

    plt.tight_layout()

    if save_path is not None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_sector_allocations(
    sector_df: pd.DataFrame,
    title: Optional[str] = None,
    save_path: Optional[Path] = None,
    figsize: tuple[int, int] = (14, 7),
) -> plt.Figure:
    """
    Generates a clean stacked bar chart displaying sector composition over time.
    """
    setup_plot_style()

    fig, ax = plt.subplots(figsize=figsize)
    n_cols = len(sector_df.columns)

    # Harmonious palette inspired by paper-financial-graph (shades of navy, petrol blue, slate, light gray)
    base_tones = ["#22125F", "#2E5C6E", "#3A738A", "#4A8A9E", "#5FA0B3", "#76B4C5", "#8CA8B5", "#A4BFCB", "#BED3DC", "#D7E4EA", "#BDC3C7"]
    if n_cols <= len(base_tones):
        colors = base_tones[:n_cols]
    else:
        colors = sns.color_palette("Blues_r", n_colors=n_cols)

    sector_df.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        width=0.75,
        color=colors,
        edgecolor="#ffffff",
        linewidth=0.5,
    )

    ax.set_ylabel("Portfolio Allocation (%)", fontsize=11)
    ax.set_xlabel("Rebalancing Year", fontsize=11)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax.legend(
        title="Sectors",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        fontsize=9,
        frameon=False,
    )
    ax.grid(False)
    sns.despine(ax=ax, top=True, right=True)

    plt.tight_layout()

    if save_path is not None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_active_sector_tilts(
    tilts_df: pd.DataFrame,
    title: Optional[str] = None,
    save_path: Optional[Path] = None,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """
    Generates a clean heatmap of active sector tilts (Strategy - Benchmark) over time.
    """
    setup_plot_style()

    fig, ax = plt.subplots(figsize=figsize)
    data = tilts_df.T

    max_abs = max(abs(data.min().min()), abs(data.max().max()), 5.0)
    sns.heatmap(
        data,
        cmap="vlag_r",
        center=0.0,
        vmin=-max_abs,
        vmax=max_abs,
        annot=True,
        fmt=".1f",
        linewidths=0.6,
        linecolor="#ffffff",
        cbar_kws={"label": "Active Difference (pp)"},
        ax=ax,
    )

    ax.set_xlabel("Rebalancing Year", fontsize=11)
    ax.set_ylabel("Economic Sector", fontsize=11)
    ax.grid(False)

    plt.tight_layout()

    if save_path is not None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_decile_allocations(
    decile_df: pd.DataFrame,
    title: Optional[str] = None,
    save_path: Optional[Path] = None,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """
    Generates a clean stacked bar chart with portfolio weights across network deciles (D1 to D10).
    Transitioning from Central (D1 = #22125F) to Peripheral (D10 = #2E5C6E).
    """
    setup_plot_style()

    fig, ax = plt.subplots(figsize=figsize)
    n_dec = len(decile_df.columns)

    # Custom decile palette from paper-financial-graph:
    # D1 (Navy #22125F) -> Intermediate grays/blues -> D10 (Teal #2E5C6E)
    colors = [
        "#22125F", "#3B2D78", "#554B92", "#736DAB", "#9390C3",
        "#BDC3C7", "#98B5BE", "#6F9DAF", "#4B859D", "#2E5C6E",
    ][:n_dec]

    decile_df.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        width=0.75,
        color=colors,
        edgecolor="#ffffff",
        linewidth=0.5,
    )

    ax.set_ylabel("Allocation (%)", fontsize=11)
    ax.set_xlabel("Rebalancing Year", fontsize=11)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax.legend(
        title="Network Decile",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        fontsize=9,
        frameon=False,
    )
    ax.grid(False)
    sns.despine(ax=ax, top=True, right=True)

    plt.tight_layout()

    if save_path is not None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_fama_french_betas(
    ff_results_dict: dict[str, dict],
    title: Optional[str] = None,
    save_path: Optional[Path] = None,
    figsize: tuple[int, int] = (12, 5),
) -> plt.Figure:
    """
    Generates a clean grouped bar chart comparing factor loadings (Mkt-RF, SMB, HML) across strategies.
    """
    setup_plot_style()

    records = []
    for name, res in ff_results_dict.items():
        records.append(
            {
                "Strategy": name,
                "Market Beta (Mkt-RF)": res.get("beta_mkt", np.nan),
                "Size Beta (SMB)": res.get("beta_smb", np.nan),
                "Value Beta (HML)": res.get("beta_hml", np.nan),
            }
        )

    df = pd.DataFrame(records).set_index("Strategy")

    fig, ax = plt.subplots(figsize=figsize)
    factor_colors = [COLOR_UNCONSTRAINED, COLOR_LONG_ONLY, "#8CA8B5"]

    df.plot(kind="bar", ax=ax, width=0.75, color=factor_colors, edgecolor="none")

    ax.set_ylabel("Factor Loading (Beta)", fontsize=11)
    ax.set_xlabel("", fontsize=11)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha="right", fontsize=9.5)
    ax.axhline(0, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.legend(title="", fontsize=10, frameon=False)
    ax.grid(False)
    sns.despine(ax=ax, top=True, right=True)

    plt.tight_layout()

    if save_path is not None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_rolling_fama_french(
    rolling_df: pd.DataFrame,
    title: Optional[str] = None,
    save_path: Optional[Path] = None,
    figsize: tuple[int, int] = (14, 8),
) -> plt.Figure:
    """
    Generates a clean 2-panel chart:
    1. Trajectory of Factor Betas (Mkt-RF, SMB, HML)
    2. Trajectory of Annualized Rolling Alpha (% p.a.)
    """
    setup_plot_style()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True, gridspec_kw={"height_ratios": [1.4, 1.0]})

    # 1. Betas
    for col_cand in ["Market Beta (Mkt-RF)", "Beta Mercado (Mkt-RF)"]:
        if col_cand in rolling_df.columns:
            ax1.plot(rolling_df.index, rolling_df[col_cand], label="Market Beta (Mkt-RF)", color=COLOR_UNCONSTRAINED, linewidth=1.8)
            break
    for col_cand in ["Size Beta (SMB)", "Beta Tamanho (SMB)"]:
        if col_cand in rolling_df.columns:
            ax1.plot(rolling_df.index, rolling_df[col_cand], label="Size Beta (SMB)", color=COLOR_LONG_ONLY, linewidth=1.6)
            break
    for col_cand in ["Value Beta (HML)", "Beta Valor (HML)"]:
        if col_cand in rolling_df.columns:
            ax1.plot(rolling_df.index, rolling_df[col_cand], label="Value Beta (HML)", color="#8CA8B5", linewidth=1.6)
            break

    ax1.axhline(1.0, color="black", linestyle=":", linewidth=0.8, alpha=0.5, label="Beta = 1.0")
    ax1.axhline(0.0, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
    ax1.set_ylabel("Factor Loading (Beta)", fontsize=11)
    ax1.legend(loc="upper left", fontsize=9, frameon=False)
    ax1.grid(False)
    sns.despine(ax=ax1, top=True, right=True)

    # 2. Rolling Alpha
    for col_cand in ["Annualized Alpha (% p.a.)", "Annualized Alpha (%)", "Alfa Anualizado (%)"]:
        if col_cand in rolling_df.columns:
            ax2.plot(rolling_df.index, rolling_df[col_cand], label="Annualized Rolling Alpha (% p.a.)", color=COLOR_BENCHMARK, linewidth=1.8)
            ax2.fill_between(rolling_df.index, rolling_df[col_cand], 0, color=COLOR_BENCHMARK, alpha=0.12)
            break

    ax2.axhline(0.0, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
    ax2.set_ylabel("Rolling Alpha (% p.a.)", fontsize=11)
    ax2.set_xlabel("Date", fontsize=11)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:+.0f}%"))
    ax2.legend(loc="upper left", fontsize=9, frameon=False)
    ax2.grid(False)
    sns.despine(ax=ax2, top=True, right=True)

    plt.tight_layout()

    if save_path is not None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_efficient_frontier_cal(
    blends_eval_dict: dict[str, pd.DataFrame],
    title: Optional[str] = None,
    save_path: Optional[Path] = None,
    figsize: tuple[int, int] = (12, 7),
) -> plt.Figure:
    """
    Plots the Capital Allocation Lines (CAL) / Efficient Frontier of convex combinations
    between Fixed Income (RF) and risky equity strategies:
    - Treynor-Black (Unconstrained) + RF
    - Treynor-Black (Long-Only) + RF
    - Market Benchmark + RF
    """
    setup_plot_style()

    fig, ax = plt.subplots(figsize=figsize)

    colors = {
        "Treynor-Black (Unconstrained)": COLOR_UNCONSTRAINED,
        "Treynor-Black Unconstrained (HCM)": COLOR_UNCONSTRAINED,
        "Treynor-Black Unconstrained (HRM)": COLOR_UNCONSTRAINED,
        "Treynor-Black (Long-Only)": COLOR_LONG_ONLY,
        "Treynor-Black Long-Only (HCM)": COLOR_LONG_ONLY,
        "Treynor-Black Long-Only (HRM)": COLOR_LONG_ONLY,
        "Treynor-Black Unconstrained (Pozzi)": "#3A738A",
        "Treynor-Black Long-Only (Pozzi)": "#554B92",
        "Benchmark (Market Cap)": COLOR_BENCHMARK,
    }
    markers = {
        "Treynor-Black (Unconstrained)": "o",
        "Treynor-Black Unconstrained (HCM)": "o",
        "Treynor-Black Unconstrained (HRM)": "o",
        "Treynor-Black (Long-Only)": "s",
        "Treynor-Black Long-Only (HCM)": "s",
        "Treynor-Black Long-Only (HRM)": "s",
        "Treynor-Black Unconstrained (Pozzi)": "D",
        "Treynor-Black Long-Only (Pozzi)": "v",
        "Benchmark (Market Cap)": "^",
    }

    # Plot each CAL line
    for name, df in blends_eval_dict.items():
        color = colors.get(name, "#555555")
        marker = markers.get(name, "o")

        # Sort by Volatility ascending
        df_sorted = df.sort_values(by="Annual Volatility (%)")
        vols = df_sorted["Annual Volatility (%)"].values
        cagrs = df_sorted["CAGR (%)"].values
        sharpe_col = "Sharpe Ratio (vs RF)" if "Sharpe Ratio (vs RF)" in df_sorted.columns else "Sharpe Ratio"
        sharpes = df_sorted[sharpe_col].values if sharpe_col in df_sorted.columns else np.array([0.0])

        max_sharpe = sharpes.max() if len(sharpes) > 0 else 0.0

        ax.plot(
            vols,
            cagrs,
            label=f"{name} (Sharpe: {max_sharpe:.2f})",
            color=color,
            linewidth=2.0 if "Treynor" in name else 1.8,
            linestyle="-" if "Unconstrained" in name else ("--" if "Long-Only" in name else ":"),
            alpha=0.9,
        )

        ax.scatter(
            vols,
            cagrs,
            color=color,
            marker=marker,
            s=40,
            edgecolors="#ffffff",
            linewidth=0.8,
            zorder=4,
        )

        # Annotate key allocation percentages (0%, 10%, 20%, 30%, 50% RF)
        for _, row in df.iterrows():
            w_rf = int(round(row["RF Weight (%)"]))
            if w_rf in {0, 10, 20, 30, 50} and ("Unconstrained" in name and ("HCM" in name or "HRM" in name) or name == "Treynor-Black (Unconstrained)"):
                ax.annotate(
                    f"{w_rf}% RF",
                    xy=(row["Annual Volatility (%)"], row["CAGR (%)"]),
                    xytext=(6, -2),
                    textcoords="offset points",
                    fontsize=8,
                    fontweight="bold" if w_rf in {0, 20} else "normal",
                    color=color,
                )

    # Plot Pure RF point
    first_df = next(iter(blends_eval_dict.values()))
    if "100% Pure Fixed Income" in first_df.index:
        rf_row = first_df.loc["100% Pure Fixed Income"]
        ax.scatter(
            [rf_row["Annual Volatility (%)"]],
            [rf_row["CAGR (%)"]],
            color=COLOR_RF,
            marker="*",
            s=200,
            edgecolors="black",
            linewidth=0.8,
            label=f"100% Pure Fixed Income ({rf_row['CAGR (%)']:.2f}%)",
            zorder=5,
        )

    ax.set_xlabel("Annualized Volatility (%)", fontsize=11)
    ax.set_ylabel("Compound Annual Growth Rate - CAGR (%)", fontsize=11)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax.legend(loc="upper left", fontsize=10, frameon=False)
    ax.grid(False)
    sns.despine(ax=ax, top=True, right=True)

    plt.tight_layout()

    if save_path is not None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_fixed_income_blends_growth(
    blends_dict: dict[str, pd.Series],
    benchmark_returns: pd.Series,
    rf_returns: pd.Series,
    title: Optional[str] = None,
    save_path: Optional[Path] = None,
    figsize: tuple[int, int] = (14, 7),
) -> plt.Figure:
    """
    Plots cumulative wealth growth across different fixed income blend allocations alongside
    the Market Benchmark and 100% Pure Fixed Income.
    """
    setup_plot_style()

    fig, ax = plt.subplots(figsize=figsize)

    # 1. Pure Fixed Income
    cum_rf = (1.0 + rf_returns).cumprod()
    ax.plot(
        cum_rf.index,
        cum_rf.values,
        label=f"100% Pure Fixed Income ({cum_rf.iloc[-1]:.2f}x)",
        color=COLOR_RF,
        linestyle=":",
        linewidth=1.6,
        alpha=0.85,
    )

    # 2. 100% Equity Benchmark
    cum_bm = (1.0 + benchmark_returns).cumprod()
    ax.plot(
        cum_bm.index,
        cum_bm.values,
        label=f"100% Market Benchmark ({cum_bm.iloc[-1]:.2f}x)",
        color=COLOR_BENCHMARK,
        linestyle="-",
        linewidth=2.0,
        alpha=0.9,
    )

    # 3. Strategy Blends
    is_pozzi = any("Pozzi" in k for k in blends_dict.keys())
    is_long_only = any("Long-Only" in k for k in blends_dict.keys())
    if is_pozzi:
        primary_color = "#554B92" if is_long_only else "#3A738A"
    else:
        primary_color = COLOR_LONG_ONLY if is_long_only else COLOR_UNCONSTRAINED

    # Generate sequential tints
    n_blends = len(blends_dict)
    palette = sns.light_palette(primary_color, n_colors=n_blends + 3, reverse=True)[1 : n_blends + 1]

    for (label, s), color in zip(blends_dict.items(), palette):
        cum_s = (1.0 + s).cumprod()
        is_key = "0%" in label or "20%" in label
        ax.plot(
            cum_s.index,
            cum_s.values,
            label=f"{label} ({cum_s.iloc[-1]:.2f}x)",
            color=color,
            linewidth=2.0 if is_key else 1.2,
            linestyle="-" if is_key else "--",
            alpha=1.0 if is_key else 0.75,
        )

    ax.set_ylabel("Cumulative Wealth (Base = 1.0)", fontsize=11)
    ax.set_xlabel("Date", fontsize=11)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.1f}x" if y < 10 else f"{int(y)}x"))
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    ax.grid(False)
    sns.despine(ax=ax, top=True, right=True)

    plt.tight_layout()

    if save_path is not None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_blends_tradeoff(
    blends_eval_dict: dict[str, pd.DataFrame],
    title: Optional[str] = None,
    save_path: Optional[Path] = None,
    figsize: tuple[int, int] = (14, 5.5),
) -> plt.Figure:
    """
    Generates a 2-panel chart:
    1. CAGR (%) vs. Fixed Income Allocation (%)
    2. Max Drawdown (%) vs. Fixed Income Allocation (%)
    """
    setup_plot_style()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    colors = {
        "Treynor-Black (Unconstrained)": COLOR_UNCONSTRAINED,
        "Treynor-Black Unconstrained (HCM)": COLOR_UNCONSTRAINED,
        "Treynor-Black Unconstrained (HRM)": COLOR_UNCONSTRAINED,
        "Treynor-Black (Long-Only)": COLOR_LONG_ONLY,
        "Treynor-Black Long-Only (HCM)": COLOR_LONG_ONLY,
        "Treynor-Black Long-Only (HRM)": COLOR_LONG_ONLY,
        "Treynor-Black Unconstrained (Pozzi)": "#3A738A",
        "Treynor-Black Long-Only (Pozzi)": "#554B92",
        "Benchmark (Market Cap)": COLOR_BENCHMARK,
    }

    for name, df in blends_eval_dict.items():
        color = colors.get(name, "#555555")
        sub = df[df["RF Weight (%)"] <= 50.0].sort_values(by="RF Weight (%)")

        # 1. CAGR
        ax1.plot(
            sub["RF Weight (%)"],
            sub["CAGR (%)"],
            label=name,
            color=color,
            linewidth=1.8,
            marker="o",
            markersize=4.5,
        )

        # 2. Max Drawdown
        ax2.plot(
            sub["RF Weight (%)"],
            sub["Max Drawdown (%)"],
            label=name,
            color=color,
            linewidth=1.8,
            marker="s",
            markersize=4.5,
        )

    ax1.set_xlabel("Fixed Income Allocation (%)", fontsize=11)
    ax1.set_ylabel("CAGR (%)", fontsize=11)
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax1.legend(loc="upper right", fontsize=9, frameon=False)
    ax1.grid(False)
    sns.despine(ax=ax1, top=True, right=True)

    ax2.set_xlabel("Fixed Income Allocation (%)", fontsize=11)
    ax2.set_ylabel("Max Drawdown (%)", fontsize=11)
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax2.legend(loc="lower right", fontsize=9, frameon=False)
    ax2.grid(False)
    sns.despine(ax=ax2, top=True, right=True)

    plt.tight_layout()

    if save_path is not None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig
