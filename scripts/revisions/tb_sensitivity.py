"""
Treynor-Black sensitivity to the two discretionary tuning choices:
the top-k alpha screen and the active budget.

Runs the canonical implementation (`~/treynor-black`) over 2015-2024 and reports
CAGR, Sharpe, max drawdown and the FF3 (Newey-West) alpha for a grid of
top_k x active_budget values. Writes reviews/outputs/tb_sensitivity.csv.
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/home/gustavoroque_visagi/treynor-black/src")
sys.path.insert(0, "/home/gustavoroque_visagi/paper-financial-graph/scripts/revisions")
from portfolio_grafos.strategy import run_treynor_black_backtest
from portfolio_grafos.metrics import calculate_performance_metrics
from common import load_factors, nw_ols, OUT

factors = load_factors()


def ff3_alpha(net):
    d = pd.concat([net.rename("r"), factors], axis=1, join="inner").dropna()
    y = (d["r"] - d["RF"]).values
    X = d[["Mkt-RF", "SMB", "HML"]].values
    b, se, _ = nw_ols(y, X, L=5)
    return b[0] * 252, b[0] / se[0]


rows = []
for metric in ["hrm", "pozzi"]:
    for k in [10, 25, 50]:
        for bud in [0.10, 0.20, 0.30]:
            res = run_treynor_black_backtest(
                years=range(2014, 2025), metric=metric, active_budget_cap=bud,
                top_k=k, allow_short=True, tc_rate=0.001,
            )
            s = res["treynor_black"]; s = s[s.index >= "2015-01-01"]
            b = res["benchmark"]; b = b[b.index >= "2015-01-01"]
            m = calculate_performance_metrics(s, b, rf_annual=0.0)
            a, t = ff3_alpha(s)
            rows.append({
                "metric": metric, "top_k": k, "budget": bud,
                "cagr": m["CAGR (%)"] / 100, "sharpe": m["Sharpe Ratio"],
                "mdd": m["Max Drawdown (%)"] / 100,
                "ff3_alpha": a, "ff3_t": t,
            })
            print(f"{metric} k={k:2d} bud={bud:.2f} CAGR={m['CAGR (%)']:5.2f}% "
                  f"Sharpe={m['Sharpe Ratio']:4.2f} MDD={m['Max Drawdown (%)']:6.2f}% "
                  f"FF3alpha={a:+.4f} t={t:+.2f}")

df = pd.DataFrame(rows)
df.to_csv(OUT / "tb_sensitivity.csv", index=False)
print("\nSaved", OUT / "tb_sensitivity.csv")
