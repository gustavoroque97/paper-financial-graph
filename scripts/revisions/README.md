# Revision scripts (R3 / R8 / S1)

Runnable scripts implementing the empirical items left as **Pending** in
`reviews/review1_response.md`. They consume the artefacts already produced by
the pipeline and never fabricate results.

## Requirements

The scripts use the project's Poetry environment:

```bash
poetry install
poetry shell
```

Minimum imports: `numpy`, `pandas`, `pyarrow`, `networkx`.
`scikit-learn` is needed only for `r3_stocks_only.py --mode rebuild`.

## Quick start

```bash
# 0. verify inputs / schemas
python scripts/revisions/_sanity_check.py

# 1. R3 — stocks-only replication (fast, refiltering the existing TMFG)
python scripts/revisions/r3_stocks_only.py --mode refilter --metrics hcm,pozzi

#    faithful version (re-estimates correlation + TMFG on stocks only)
python scripts/revisions/r3_stocks_only.py --mode rebuild --metrics hcm
python scripts/revisions/r3_stocks_only.py --mode rebuild --tau 1.0   # tau sensitivity

# 2. R2 — size double-sort + BAB spanning (illiquidity needs volume data)
python scripts/revisions/r2_spanning.py

# 3. R8 — sub-period + multiple testing + decile-count sensitivity
python scripts/revisions/r8_multiple_testing.py --metric hcm

# 3b. Treynor-Black — reproduce the ORIGINAL implementation (~/treynor-black)
python scripts/revisions/tb_reproduce.py

# 3. S1 — liquidity-conditioned costs + capacity
python scripts/revisions/s1_costs_capacity.py --metric hcm --velocity 0.005
python scripts/revisions/s1_costs_capacity.py --metric hcm \
    --strategy-returns path/to/strategy_daily_returns.csv   # optional
```

Or: `bash scripts/revisions/run_all.sh`.

All outputs land in `reviews/outputs/`.

## What each script produces

| Script | Output | Answers |
|--------|--------|---------|
| `tb_reproduce.py` | stdout | Runs the canonical Treynor-Black implementation from `~/treynor-black` and reproduces the published tables (MDDs match exactly). See `reviews/tb_reconstruction.md`. |
| `r2_spanning.py` | `r2_size_doublesort.csv`, `r2_bab_spanning.csv` | R2/DA-1: is the peripheral alpha a size or low-beta artefact? |
| `r3_stocks_only.py` | `r3_{metric}_{mode}_ff3.csv`, `_performance.csv`, `_centrality.csv` | DA-1/DA-2: is the core/periphery result an ETF artefact? |
| `r8_multiple_testing.py` | `r8_{metric}_subperiod_*.csv`, `_multiplicity.csv`, `_decile_sensitivity.csv` | R1-W4: are the marginal t-stats multiplicity-robust? Do results hold by regime? |
| `s1_costs_capacity.py` | `s1_{metric}_cost_repricing.csv`, `_capacity.csv` | R3-W1: do net returns survive realistic costs, and at what AUM? |

## Method notes / assumptions

* **Centrality** is recomputed with the exact definitions in `common.py`
  (HCM = PCA-weighted distance degree/closeness/eigenvector, then negated so
  decile 1 = core; Pozzi = Z-scored X+Y, also oriented small = central).
* **Deciles** are re-cut *within the stocks-only universe* (R3) or across
  parameterised quantiles (R8), per year, using `rank` to avoid duplicate edges.
* **FF3** uses `data/02_clean/fama_french_factors.parquet` (stored in percent,
  converted to decimals) with Newey-West HAC (5 lags); cross-year aggregation
  uses the Fama-MacBeth-style *mean alpha / (std / sqrt(n_years))* t-statistic
  and **annualizes the intercept as `const x 252`**, exactly as
  `code/graphs/regressions.ipynb` does (otherwise alphas are ~252x too small).
* **Portfolio construction** is **buy-and-hold 1/N** (`fillna(0)`, cumulative
  product, cross-sectional mean) on the **out-of-sample** year `t+1` returns,
  with `HYFT` excluded. This reproduces the published tables: with the default
  settings the scripts give Global-benchmark-like D1 CAGR 8.5%, D10 CAGR 15.2%,
  D1&D10 12.1% (paper: 8.4%, 15.1%, 12.0%). Daily-rebalanced EW would give very
  different (much higher, microcap-inflated) numbers — do not use it.
* **Costs (S1)** add `turnover x bps / 1e4` at the first trading day of each
  year. The tiered grid (ETF/CEF 10 bps, D1 25, D10 75, middle 40) is an
  assumption to be justified in the paper.
* **Capacity (S1)** uses the square-root impact law
  `impact_bps = coef * sqrt(AUM / ADV_proxy) * 1e4`, where
  `ADV_proxy = mean(member market cap) * velocity`. `velocity` (default 0.5%
  of market cap per day) is an **assumption**; replace it with observed dollar
  volume / ADV before reporting capacity.

## Validated results (reference run)

Run on the current `data/` tree with the `hcm` metric. These reproduce the
published numbers and quantify the reviewer's concerns.

**R8 — the published peripheral alpha survives multiple testing, but is regime-specific**
* Pooled OOS FF3: D10 alpha = **0.1011** (t = 2.93; Holm-adjusted p = 0.034; Reality-Check p = 0.006) — matches the published 0.1013.
* Sub-period: D10 alpha = **0.206** (t = 2.77) in 2015-2019 but **0.014** (n.s.) in 2020-2024; the core's negative alpha is concentrated in 2020-2024.
* Conclusion: the periphery premium is real but not stable across regimes.

**R3 — the core/periphery separation is materially inflated by non-stocks (ETFs/CEFs/REITs)**
* Full universe (published): D1 alpha -0.024, D10 alpha +0.101, D10 beta 0.281.
* Stocks-only (refilter): D1 alpha +0.003 (n.s.), D10 alpha +0.028, D10 beta 0.746.
* Stocks-only (rebuild): D1 alpha +0.093 (n.s.), D10 alpha +0.048 (t = 2.74), D10 beta 0.718.
* Conclusion: the peripheral alpha shrinks by ~50-70% and the periphery is no longer near-zero-beta once ETFs are removed — the ETF contamination flagged by the reviewer is quantitatively important.

**S1 — costs and capacity**
* Re-pricing D1/D10/D1&D10 with and without liquidity-tiered costs: the drag is small (turnover ~0.46-0.51/yr) under the tiered grid, but the grid is an assumption.
* Capacity (square-root impact, ADV proxy ≈ mean mcap × 0.5%/day): net alpha stays near the gross level up to ~$1bn and decays thereafter; up to ~$10bn it remains positive under these assumptions, but replace the velocity/impact assumptions with observed ADV before publishing.

## Known limitations of the scripts

* The Treynor-Black strategy weights are not persisted by the existing
  notebooks; S1 can only re-price the live strategy if its daily returns are
  exported (pass `--strategy-returns`). Exporting them is a 5-line addition to
  `code/trading/trading.ipynb` (save `strategy_ret` and `turnover` to CSV).
* Sub-period and multiplicity analyses use the decile portfolios as-is; they do
  not re-estimate the network day-by-day.
* No LaTeX is required.
