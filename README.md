# paper-financial-graph

Reproducibility repository for the manuscript:

> Roque, G. R. O., Ferraresi, M., & Borges, C. C. H. (2026).
> *Hybrid Centrality and Network Topology in Equity Markets: Asset Pricing and
> Portfolio Implications.*

The repository contains the network-construction pipeline, the portfolio
analyses, the Treynor-Black active-strategy implementation, and the manuscript
source. All results reported in the paper can be reproduced from the files here.

## Table of Contents

- [Overview](#overview)
- [Manuscript](#manuscript)
- [Project Structure](#project-structure)
- [Requirements & Installation](#requirements--installation)
- [Pipeline Execution](#pipeline-execution)
- [Treynor-Black pipeline (Section 5.4)](#treynor-black-pipeline-section-54)

## Overview

This paper investigates whether information diffusion dynamics in equity markets
are associated with the topology of correlation-based financial networks. Using
shrinkage estimators and the Triangulated Maximally Filtered Graph (TMFG), we
construct sparse, robust correlation networks and introduce a Hybrid Centrality
Metric (HCM) integrating degree, closeness, and eigenvector centrality to
partition the universe into central and peripheral portfolios. We study the
resulting asset-pricing characteristics, lead–lag dynamics, and out-of-sample
portfolio performance, including a reproducible Treynor-Black active overlay.

## Manuscript

The LaTeX source is under `paper/` (`main.tex`, `references.bib`, `rbfin.cls`,
`figures/`). Build with `latexmk -pdf main.tex` or
`tectonic -X compile main.tex` from the `paper/` directory.

Repository: <https://github.com/gustavoroque97/paper-financial-graph>

## Project Structure

- **`paper/`**: manuscript source (`main.tex`) and figures.
- **`code/`**: analysis pipeline (Jupyter notebooks and modules).
  - **`code/treynor_black/`**: Treynor-Black active-strategy implementation and
    runner (Section 5.4 of the paper).
- **`scripts/revisions/`**: revision analyses — robustness (multiple testing,
  size/BAB spanning, stocks-only), top-k/budget sensitivity, and the
  Treynor-Black reproduction.
- **`data/`**: inputs and intermediate outputs (portfolio returns, metadata, TMFG
  graphs).
- The original pipeline is organized into modular notebooks:
  - **`data_clean/`**: data ingestion, cleaning, baseline financial metrics.
  - **`graphs/`**: network construction and centrality metrics.
  - **`leadlag_time_analysis/`**: time-domain lead–lag analysis.
  - **`analysis/`**: yearly sub-period analyses and dataset organization.
  - **`portfolios/`**: centrality-based portfolio construction.
  - **`trading/`**: out-of-sample backtesting of the graph-based strategies.

## Requirements & Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.
Requires Python >= 3.11.

```bash
poetry install
```

Key dependencies: `pandas`, `numpy`, `scikit-learn`, `statsmodels` (data and
computation) and `networkx` (network analysis).

## Pipeline Execution

The research pipeline is built to be run sequentially through the notebooks:

1. Run notebooks in `data_clean/` to prepare the datasets.
2. Build the lead-lag networks using the notebooks in `graphs/`.
3. Perform the data analysis in `analysis/`.
4. Construct and evaluate the lead-lag relationships using
   `leadlag_time_analysis/` and `trading/out_of_sample.ipynb`.

## Treynor-Black pipeline (Section 5.4)

```bash
python code/treynor_black/run_treynor_black.py
```

Running with the default settings (`top_k=25`, `w_A=0.20`, 10 bps costs)
reproduces the published table over the 2015–2024 out-of-sample window:
benchmark 20.96%, HCM Unconstrained 25.31%, HCM Long-Only 23.51%, Pozzi
21.16% / 21.05%.

Sensitivity to the top-$k$ alpha screen and the active budget:

```bash
python scripts/revisions/tb_sensitivity.py
```
