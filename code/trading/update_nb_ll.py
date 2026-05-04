import json

with open('c:/Users/madug/paper-financial-graph/code/graphs/lead_lag_relation.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find cell with portfolios = {} and k_values = [1, 10, 30]
new_load_cell = '''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import pickle
import os

centralities = ["central", "peripheral"]
years = range(2015, 2025)

portfolios = {}
market_returns_dict = {}

k_values = [1, 10, 30]

for year in years:
    for k in k_values:
        try:
            full_ret = pd.read_parquet(f"../../data/02_clean/returns_new_{year-29}_{year}.parquet")
        except:
            full_ret = pd.read_parquet(f"../../data/02_clean/returns_new_{year-k+1}_{year}.parquet")
            
        market_returns_dict[f"{year}_{k}"] = np.log1p(full_ret).mean(axis=1)
        
        for centrality in centralities:
            cols = pd.read_csv(f"../../data/06_portfolios/{centrality}_{year}_{k}.csv", index_col="Date").columns.tolist()
            valid_cols = [c for c in cols if c in full_ret.columns]
            portfolios[f"{centrality}_{year}_{k}"] = full_ret[valid_cols]
'''

# Find cell with weekly_returns = {}
new_resample_cell = '''weekly_returns = {}
weekly2_returns = {}
monthly_returns = {}
daily_returns = {}

for name, portfolio in portfolios.items():
    year = int(name.split('_')[1])
    k = int(name.split('_')[2])
    
    log_returns = np.log1p(portfolio)
    R_m = market_returns_dict[f"{year}_{k}"]
    
    # Calculate excess returns
    daily_returns[name] = log_returns.mean(axis=1) - R_m
    
    weekly_m = R_m.resample("W-FRI").sum()
    weekly_returns[name] = log_returns.resample("W-FRI").sum().mean(axis=1) - weekly_m
    
    weekly2_m = R_m.resample("2W-FRI").sum()
    weekly2_returns[name] = log_returns.resample("2W-FRI").sum().mean(axis=1) - weekly2_m
    
    monthly_m = R_m.resample("ME").sum()
    monthly_returns[name] = log_returns.resample("ME").sum().mean(axis=1) - monthly_m
'''

# Find cell with def autocorrelation_matrix and plot_antisymmetric_autocorr
new_acm_cell = '''def autocorrelation_matrix(X, lag):
    X_t = X.iloc[lag:]
    X_tk = X.shift(lag).iloc[lag:]

    mu_t = X_t.mean().values
    mu_tk = X_tk.mean().values

    Xc_t = X_t.values - mu_t
    Xc_tk = X_tk.values - mu_tk

    Sigma_k = (Xc_tk.T @ Xc_t) / len(Xc_t)

    std_t = X_t.std(ddof=0).values
    std_tk = X_tk.std(ddof=0).values

    # Avoid division by zero
    std_t[std_t == 0] = 1e-8
    std_tk[std_tk == 0] = 1e-8

    return Sigma_k / np.outer(std_tk, std_t)

def plot_antisymmetric_autocorr(
    returns_list,
    column_names,
    labels,
    lags=(1, 2, 3, 4),
    figsize=(12, 8),
    cmap="Blues",
    title_prefix="Y",
    annot=False,
    diff=True,
    fig_title=None
):
    X = pd.concat(returns_list, axis=1).dropna()
    X.columns = column_names

    fig, axes = plt.subplots(2, 2, figsize=figsize)
    axes = axes.flatten()

    if len(lags) == 1:
        axes = [axes]

    for ax, lag in zip(axes, lags):
        T = autocorrelation_matrix(X, lag)

        if diff:
            A = pd.DataFrame(
                T - T.T,
                index=labels,
                columns=labels
            )
            title = f"{title_prefix}({lag}) - {title_prefix}'({lag})"
        else:
            A = pd.DataFrame(
                T,
                index=labels,
                columns=labels
            )
            title = f"{title_prefix}({lag})"

        sns.heatmap(A, ax=ax, cmap=cmap, center=0, annot=annot)
        ax.set_title(title)

    if fig_title:
        fig.suptitle(fig_title, fontsize=14)
    plt.tight_layout()
    plt.show()
'''

new_lead_lag_cell = '''years = range(2015, 2025)

for year in years:
    for k in k_values:
        try:
            R1 = daily_returns[f"peripheral_{year}_{k}"]
            R2 = daily_returns[f"central_{year}_{k}"]
            R3 = weekly_returns[f"peripheral_{year}_{k}"]
            R4 = weekly_returns[f"central_{year}_{k}"]
            R5 = weekly2_returns[f"peripheral_{year}_{k}"]
            R6 = weekly2_returns[f"central_{year}_{k}"]
            R7 = monthly_returns[f"peripheral_{year}_{k}"]
            R8 = monthly_returns[f"central_{year}_{k}"]

        except KeyError as e:
            print(f"Missing data for {year}: {e}")

        # =============================
        # 5. Lead–lag matrix
        # =============================
        matrix = []

        pairs = [(R1, R2), (R3, R4), (R5, R6), (R7, R8)]
        max_lag = 5

        for R_peri, R_cent in pairs:
            X = pd.concat([R_peri, R_cent], axis=1).dropna()
            X.columns = ["Peripheral", "Central"]
            
            valid_lags = [l for l in range(1, max_lag + 1) if len(X) >= l + 4]
            if not valid_lags:
                matrix.append(float('nan'))
                continue
                
            total_lead_lag = 0
            for l in valid_lags:
                acm = autocorrelation_matrix(X, lag=l)
                lag_matrix = acm - acm.T
                total_lead_lag += lag_matrix[1, 0]
            
            matrix.append(total_lead_lag)

        # =============================
        # 6. DataFrame final
        # =============================
        cols = ["cp1d", "cp1w", "cp2w", "cp1m"]

        leadlag_df = pd.DataFrame(
            [matrix],
            columns=cols,
            index=[year]
        )

        leadlag_df.to_csv(
            f"../../data/08_lead_lag/leadlag_df_{year}_{k}.csv"
        )
'''

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        
        # 1. Replace load cell
        if 'for year in years:' in source and 'centralities = ["central", "peripheral"]' in source:
            cell['source'] = [line + '\n' for line in new_load_cell.split('\n')]
            cell['source'][-1] = cell['source'][-1].strip('\n')
            
        # 2. Replace resample cell
        elif 'weekly_returns = {}' in source and 'for name, portfolio in portfolios.items():' in source:
            cell['source'] = [line + '\n' for line in new_resample_cell.split('\n')]
            cell['source'][-1] = cell['source'][-1].strip('\n')
            
        # 3. Replace acm cell
        elif 'def autocorrelation_matrix(X, lag):' in source:
            cell['source'] = [line + '\n' for line in new_acm_cell.split('\n')]
            cell['source'][-1] = cell['source'][-1].strip('\n')
            
        # 4. Replace lead lag calc cell
        elif 'for year in years:' in source and 'R1 = daily_returns[' in source:
            cell['source'] = [line + '\n' for line in new_lead_lag_cell.split('\n')]
            cell['source'][-1] = cell['source'][-1].strip('\n')

with open('c:/Users/madug/paper-financial-graph/code/graphs/lead_lag_relation.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
