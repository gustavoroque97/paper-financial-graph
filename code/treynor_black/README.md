# Treynor-Black pipeline (Section 5.4)

Part of the reproducibility repository
<https://github.com/gustavoroque97/paper-financial-graph>.

This is the Treynor-Black implementation used to produce the paper's Section 5.4
tables (turnover, out-of-sample performance, Fama-French attribution, CAL). It
reads the portfolio returns and metadata from `data/06_portfolios/` and
`data/07_portfolios_metadata/`.

## Run

From the repository root:

```bash
python code/treynor_black/run_treynor_black.py
```

The backtest runs 2014--2024; reported metrics use the 2015--2024 out-of-sample
window (2014 is the warm-up year). With the default settings
(`top_k=25`, `w_A=0.20`, `tc_rate=10bps`) the output reproduces the published
table: benchmark CAGR 20.96%, HCM Unconstrained 25.31%, HCM Long-Only 23.51%,
Pozzi 21.16% / 21.05%, with maximum drawdowns of −34.28%, −27.85%, −34.42%,
−30.50% and −34.83%, respectively.

## Contents

- `portfolio_grafos/` — the implementation (`strategy.py` contains the
  walk-forward backtest, the top-25 alpha screen, the ±20% active tilt and the
  turnover/cost calculation).
- `run_treynor_black.py` — minimal runner.

Sensitivity to the top-$k$ screen and the active budget is produced by
`scripts/revisions/tb_sensitivity.py`.
