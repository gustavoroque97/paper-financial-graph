"""
Biblioteca portfolio_grafos para análise e estratégias quantitativas em grafos financeiros.
"""

from .strategy import (
    DEFAULT_EXCLUDED_TICKERS,
    resolve_data_dirs,
    load_year_returns,
    load_metadata_market_caps,
    compute_market_cap_weights,
    fit_single_index_model,
    compute_treynor_black_weights,
    run_treynor_black_backtest,
    get_strategy_weights,
    get_portfolio_holdings,
    get_active_bets,
)
from .metrics import (
    calculate_performance_metrics,
    format_metrics_table,
    calculate_var_cvar,
    compute_drawdown_series,
)
from .portfolio_analysis import (
    compute_sector_allocations,
    compute_active_sector_tilts,
    compute_industry_allocations,
    compute_decile_allocations,
    compute_portfolio_metadata_summary,
    compute_fixed_income_blends,
    evaluate_fixed_income_blends,
)
from .fama_french import (
    resolve_fama_french_dir,
    load_fama_french_factors,
    run_fama_french_regression,
    compare_fama_french_models,
    run_rolling_fama_french,
)
from .visualization import (
    setup_plot_style,
    plot_strategy_comparison,
    plot_annual_returns_bar,
    plot_sector_allocations,
    plot_active_sector_tilts,
    plot_decile_allocations,
    plot_fama_french_betas,
    plot_rolling_fama_french,
    plot_efficient_frontier_cal,
    plot_fixed_income_blends_growth,
    plot_blends_tradeoff,
    COLOR_UNCONSTRAINED,
    COLOR_LONG_ONLY,
    COLOR_BENCHMARK,
    COLOR_RF,
)

__all__ = [
    # Colors
    "COLOR_UNCONSTRAINED",
    "COLOR_LONG_ONLY",
    "COLOR_BENCHMARK",
    "COLOR_RF",
    # Strategy & Weights
    "DEFAULT_EXCLUDED_TICKERS",
    "resolve_data_dirs",
    "load_year_returns",
    "load_metadata_market_caps",
    "compute_market_cap_weights",
    "fit_single_index_model",
    "compute_treynor_black_weights",
    "run_treynor_black_backtest",
    "get_strategy_weights",
    "get_portfolio_holdings",
    "get_active_bets",
    # Performance & Risk Metrics
    "calculate_performance_metrics",
    "format_metrics_table",
    "calculate_var_cvar",
    "compute_drawdown_series",
    # Sector & Portfolio Analysis
    "compute_sector_allocations",
    "compute_active_sector_tilts",
    "compute_industry_allocations",
    "compute_decile_allocations",
    "compute_portfolio_metadata_summary",
    "compute_fixed_income_blends",
    "evaluate_fixed_income_blends",
    # Fama-French Regressions
    "resolve_fama_french_dir",
    "load_fama_french_factors",
    "run_fama_french_regression",
    "compare_fama_french_models",
    "run_rolling_fama_french",
    # Visualizations
    "setup_plot_style",
    "plot_strategy_comparison",
    "plot_annual_returns_bar",
    "plot_sector_allocations",
    "plot_active_sector_tilts",
    "plot_decile_allocations",
    "plot_fama_french_betas",
    "plot_rolling_fama_french",
    "plot_efficient_frontier_cal",
    "plot_fixed_income_blends_growth",
    "plot_blends_tradeoff",
]


