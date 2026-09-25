"""Run the ORIGINAL Treynor-Black implementation from ~/treynor-black to confirm
reproducibility of the published tables. Read-only with respect to that repo."""
import sys
import numpy as np

sys.path.insert(0, "/home/gustavoroque_visagi/treynor-black/src")
from portfolio_grafos.strategy import run_treynor_black_backtest
from portfolio_grafos.metrics import calculate_performance_metrics


def show(name, s, bench):
    m = calculate_performance_metrics(s, bench, rf_annual=0.0)
    print(f"{name:28s} CAGR={m['CAGR (%)']:6.2f}% vol={m['Volatilidade Anual (%)']:6.2f}% "
          f"Sharpe={m['Sharpe Ratio']:5.2f} MDD={m['Max Drawdown (%)']:7.2f}%")


for metric in ["hrm", "pozzi"]:
    print("=" * 80)
    print("METRIC:", metric)
    res = run_treynor_black_backtest(
        years=range(2014, 2025), metric=metric, active_budget_cap=0.20,
        top_k=25, allow_short=True, tc_rate=0.001,
    )
    b = res["benchmark"]
    show("Benchmark", b, b)
    show("TB Unconstrained", res["treynor_black"], b)
    show("TB Long-Only", res["treynor_black_long_only"], b)
    d = res["yearly_diagnostics"]
    print("mean turnover unc=%.3f lo=%.3f" % (d["turnover_unconstrained"].mean(), d["turnover_long_only"].mean()))
    print("mean cost bps unc=%.1f lo=%.1f" % (d["cost_unconstrained"].mean()*1e4, d["cost_long_only"].mean()*1e4))
