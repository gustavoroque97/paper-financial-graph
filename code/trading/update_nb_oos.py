import json
import re

with open('c:/Users/madug/paper-financial-graph/code/trading/out_of_sample.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_func = '''def out_of_sample_lead_lag(n_months: int):
    years = range(2015, 2025)
    centralities = ["central", "peripheral"]
    portfolios = {}
    market_returns_dict = {}

    # 1. Load Data & Calculate Market Return
    for year in years:
        end_date = (
            pd.Timestamp(year=year + 1, month=n_months, day=1)
            + pd.offsets.MonthEnd(0)
        )
        path_ret = f"../../data/02_clean/returns_new_{year + 1}.parquet"
        full_ret = pd.read_parquet(path_ret).loc[:end_date]
        
        # Log market return for the OOS period
        market_returns_dict[year] = np.log1p(full_ret).mean(axis=1)
        
        for centrality in centralities:
            for k in k_values:
                path_csv = f"../../data/06_portfolios/{centrality}_{year}_{k}.csv"
                cols = pd.read_csv(path_csv, index_col="Date").columns.tolist()
                
                # Keep only valid columns
                valid_cols = [c for c in cols if c in full_ret.columns]
                portfolios[f"{centrality}_{year}_{k}"] = full_ret[valid_cols]

    # 2. Resample Returns to Excess Returns
    weekly_returns = {}
    daily_returns = {}
    weekly2_returns = {}
    monthly_returns = {}
    
    for name, portfolio in portfolios.items():
        year = int(name.split("_")[1])
        log_returns = np.log1p(portfolio)
        R_m = market_returns_dict[year]
        
        # Aggregating across stocks in the portfolio (mean) minus Market Return
        daily_returns[name] = log_returns.mean(axis=1) - R_m
        
        weekly_m = R_m.resample("W-FRI").sum()
        weekly_returns[name] = log_returns.resample("W-FRI").sum().mean(axis=1) - weekly_m
        
        weekly2_m = R_m.resample("2W-FRI").sum()
        weekly2_returns[name] = log_returns.resample("2W-FRI").sum().mean(axis=1) - weekly2_m
        
        monthly_m = R_m.resample("ME").sum()
        monthly_returns[name] = log_returns.resample("ME").sum().mean(axis=1) - monthly_m

    # 3. Build Lead-Lag Dataframes (Centrality)
    leadlag_by_k = {}
    for k in k_values:
        temp_list = [] # Use a list for concat
        for year in years:
            # Pair corresponding returns
            pairs = [
                (daily_returns[f"peripheral_{year}_{k}"], daily_returns[f"central_{year}_{k}"]),
                (weekly_returns[f"peripheral_{year}_{k}"], weekly_returns[f"central_{year}_{k}"]),
                (weekly2_returns[f"peripheral_{year}_{k}"], weekly2_returns[f"central_{year}_{k}"]),
                (monthly_returns[f"peripheral_{year}_{k}"], monthly_returns[f"central_{year}_{k}"])
            ]

            matrix = []
            for R_peri, R_cent in pairs:
                X = pd.concat([R_peri, R_cent], axis=1).dropna()
                X.columns = ["Peripheral", "Central"]
                
                max_lag = 5
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

            # Store result for the year
            df_year = pd.DataFrame(
                [matrix], 
                index=[year + 1], 
                columns=["cp1d", "cp1w", "cp2w", "cp1m"]
            )
            temp_list.append(df_year)

        # FIX: Concat the list of DataFrames
        leadlag_by_k[k] = pd.concat(temp_list)

    # --- PLOTTING (Paper Style) - COMBINED ---
    sns.set_theme(style="whitegrid", context="paper")
    palette = sns.color_palette("colorblind")

    TITLE_SIZE, LABEL_SIZE = 25, 22
    TICK_SIZE, LEGEND_SIZE = 18, 18
    LINE_WIDTH, MARKER_SIZE = 2.5, 9

    fig, axes = plt.subplots(2, 2, figsize=(18, 12), sharex=True, sharey=True)
    axes_flat = axes.flatten()

    panels_cp = ["cp1d", "cp1w", "cp2w", "cp1m"]
    panel_titles = [
        f"Next {n_months}-Months: 1-Day Lag",
        f"Next {n_months}-Months: 1-Week Lag",
        f"Next {n_months}-Months: 2-Weeks Lag",
        f"Next {n_months}-Months: 1-Month Lag",
    ]

    k_styles = {
        k_values[0]: {"color": palette[0], "label": f"Central vs Periph ($k={k_values[0]}$)", "marker": "o"},
        k_values[1]: {"color": palette[1], "label": f"Central vs Periph ($k={k_values[1]}$)", "marker": "s"},
    }

    legend_handles = []
    for i, ax in enumerate(axes_flat):
        col_cp = panels_cp[i]
        title = panel_titles[i]

        # Plot Central-Peripheral lines
        for k, style in k_styles.items():
            df = leadlag_by_k[k]
            line, = ax.plot(
                df.index, df[col_cp],
                lw=LINE_WIDTH, color=style["color"],
                marker=style["marker"], markersize=MARKER_SIZE,
                label=style["label"], alpha=0.85
            )
            if i == 0: legend_handles.append(line)

        ax.set_title(title, fontsize=TITLE_SIZE, fontweight="bold", pad=15)
        ax.tick_params(axis="both", labelsize=TICK_SIZE)
        ax.axhline(0, color="black", linewidth=2, linestyle="--", alpha=0.6)
        
        if i >= 2: ax.set_xlabel("Year", fontsize=LABEL_SIZE, fontweight="bold")
        if i % 2 == 0: ax.set_ylabel("Excess Lead–Lag Measure", fontsize=LABEL_SIZE, fontweight="bold")
        
        ax.grid(alpha=0.3)

    fig.legend(
        legend_handles, [h.get_label() for h in legend_handles],
        loc="lower center", ncol=2, frameon=False,
        fontsize=LEGEND_SIZE, bbox_to_anchor=(0.5, -0.02)
    )

    sns.despine(fig=fig)
    plt.tight_layout(rect=[0, 0.08, 1, 1])
    plt.savefig(f"../../figures/oos_combined_leadlag_{n_months}.png", dpi=300, bbox_inches="tight")
    plt.show()'''

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'def out_of_sample_lead_lag' in source:
            cell['source'] = [line + '\n' for line in new_func.split('\n')]
            cell['source'][-1] = cell['source'][-1].strip('\n')

with open('c:/Users/madug/paper-financial-graph/code/trading/out_of_sample.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
