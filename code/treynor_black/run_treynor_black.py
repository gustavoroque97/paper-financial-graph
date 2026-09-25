"""
Reproduce the paper's Treynor-Black results (Section 5.4).

Run from the repository root:

    python code/treynor_black/run_treynor_black.py

The backtest spans 2014-2024, but all reported metrics are computed over the
2015-2024 out-of-sample window (2014 is the warm-up year), which reproduces the
published tables to two decimals.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from portfolio_grafos.strategy import run_treynor_black_backtest
from portfolio_grafos.metrics import calculate_performance_metrics


def main():
    for metric in ["hrm", "pozzi"]:
        res = run_treynor_black_backtest(
            years=range(2014, 2025),
            metric=metric,
            active_budget_cap=0.20,
            top_k=25,
            allow_short=True,
            tc_rate=0.001,
        )
        bench = res["benchmark"]
        for label, series in [
            ("Benchmark", bench),
            ("TB Unconstrained", res["treynor_black"]),
            ("TB Long-Only", res["treynor_black_long_only"]),
        ]:
            s = series[series.index >= "2015-01-01"]
            b = bench[bench.index >= "2015-01-01"]
            m = calculate_performance_metrics(s, b, rf_annual=0.0)
            print(
                f"{metric:5s} {label:18s} CAGR={m['CAGR (%)']:6.2f}% "
                f"vol={m['Volatilidade Anual (%)']:6.2f}% "
                f"Sharpe={m['Sharpe Ratio']:5.2f} MDD={m['Max Drawdown (%)']:7.2f}%"
            )


if __name__ == "__main__":
    main()
