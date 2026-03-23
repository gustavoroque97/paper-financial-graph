# paper-financial-graph

Code repository for the upcoming paper

This project implements a novel financial analysis pipeline that involves correlation matrix estimation, network theory, and portfolio optimization to analyze lead-lag relationships between financial assets.

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Requirements & Installation](#requirements--installation)
- [Pipeline Execution](#pipeline-execution)
- [License](#license)

## Overview

This paper investigates whether financial network topology identifies lead–lag
relationships in stock returns. Using shrinkage estimators and the Triangulated Maximally
Filtered Graph (TMFG), we construct sparse, robust correlation networks to represent
cross-asset dependence. We introduce a hybrid centrality score integrating degree, close-
ness, and eigenvector centrality to rank assets by topological importance. Stocks are then
sorted into central and peripheral portfolios. Using lagged cross-covariance matrices, we
analyze information diffusion across different frequencies. Empirical results reveal that
central portfolios significantly lead peripheral portfolios, particularly at the daily horizon.
Notably, this lead–lag effect persists even when controlling for traditional factors like
size, beta, and momentum, suggesting that network topology captures distinct, econom-
ically relevant information. Our findings demonstrate that hybrid centrality measures
offer a powerful tool for understanding return predictability and the structural dynamics
of equity markets.

## Project Structure

The codebase is organized into modular Jupyter Notebooks representing different stages of the research pipeline:

- **`data_clean/`**: Initial data ingestion, cleaning, and computation of baseline financial metrics.
- **`graphs/`**: Network construction and analysis. Builds yearly lead-lag relationship graphs and explores network centrality metrics.
- **`leadlag_time_analysis/`**: Time-domain analysis of the lead-lag dynamics between assets.
- **`analysis/`**: Yearly sub-period analyses and dataset organization.
- **`portfolios/`**: Portfolio construction based on centrality and lead-lag relationships.
- **`trading/`**: Out-of-sample backtesting and performance evaluation of the graph-based trading strategies.

## Requirements & Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management. Requires Python >= 3.11.

To install the dependencies, clone the repository and run:

```bash
poetry install
```

Key dependencies include:
- **Data & Computation**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`
- **Network Analysis**: `networkx`

## Pipeline Execution

The research pipeline is built to be run sequentially through the notebooks:
1. Run notebooks in `data_clean/` to prepare the datasets.
2. Build the lead-lag networks using the notebooks in `graphs/`.
3. Perform the data analysis in `analysis/`.
4. Construct and evaluate the lead-lag relationship using `leadlag_time_analysis/` and `trading/out_of_sample.ipynb`.
