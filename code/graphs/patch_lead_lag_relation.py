import json

def patch_notebook(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    replacement_str = """    log_returns = np.log1p(portfolio)
    R_m = market_returns_dict[f"{year}_{k}"]
    
    mcap_col = f"mcap_{year}"
    if mcap_col not in df_mcap.columns:
        mcap_col = [c for c in df_mcap.columns if "mcap_" in c][-1]
        
    tickers = portfolio.columns.tolist()
    mcaps = df_mcap[df_mcap["Ticker"].isin(tickers)][["Ticker", mcap_col]].copy()
    mcaps[mcap_col] = pd.to_numeric(
        mcaps[mcap_col].astype(str).str.replace(',', '.'), 
        errors='coerce'
    ).fillna(0)
    
    weights_df = pd.DataFrame({"Ticker": tickers}).merge(mcaps, on="Ticker", how="left").fillna(0)
    w = weights_df[mcap_col].values
    if w.sum() == 0:
        w = np.ones(len(w)) / len(w)
    else:
        w = w / w.sum()
        
    vw_returns = (log_returns * w).sum(axis=1)
    
    # Calculate excess returns
    daily_returns[name] = vw_returns - R_m
    
    weekly_m = R_m.resample("W-FRI").sum()
    weekly_returns[name] = (log_returns.resample("W-FRI").sum() * w).sum(axis=1) - weekly_m
    
    weekly2_m = R_m.resample("2W-FRI").sum()
    weekly2_returns[name] = (log_returns.resample("2W-FRI").sum() * w).sum(axis=1) - weekly2_m
    
    monthly_m = R_m.resample("ME").sum()
    monthly_returns[name] = (log_returns.resample("ME").sum() * w).sum(axis=1) - monthly_m"""

    target_old = """    log_returns = np.log1p(portfolio)
    R_m = market_returns_dict[f"{year}_{k}"]
    
    # Calculate excess returns
    daily_returns[name] = log_returns.mean(axis=1) - R_m
    
    weekly_m = R_m.resample("W-FRI").sum()
    weekly_returns[name] = log_returns.resample("W-FRI").sum().mean(axis=1) - weekly_m
    
    weekly2_m = R_m.resample("2W-FRI").sum()
    weekly2_returns[name] = log_returns.resample("2W-FRI").sum().mean(axis=1) - weekly2_m
    
    monthly_m = R_m.resample("ME").sum()
    monthly_returns[name] = log_returns.resample("ME").sum().mean(axis=1) - monthly_m"""

    target_old_init = """for name, portfolio in portfolios.items():"""
    replacement_str_init = """df_mcap = pd.read_csv("../../data/07_portfolios_metadata/all_tickers_complete_metadata.csv")\n\nfor name, portfolio in portfolios.items():"""

    modified = False
    for cell in nb.get('cells', []):
        if cell.get('cell_type') == 'code':
            source_str = "".join(cell.get('source', []))
            if target_old in source_str:
                source_str = source_str.replace(target_old, replacement_str)
                source_str = source_str.replace(target_old_init, replacement_str_init)
                cell['source'] = [line + ('\\n' if i < len(source_str.split('\\n')) - 1 and not line.endswith('\\n') else '') for i, line in enumerate(source_str.split('\\n'))]
                # Fix double newlines
                cell['source'] = [line.replace('\\n\\n', '\\n') if line.endswith('\\n\\n') else line for line in cell['source']]
                modified = True
                
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
            print(f'Patched {filepath}')
    else:
        print(f'No replacements made in {filepath}')

patch_notebook('c:/Users/madug/paper-financial-graph/code/graphs/lead_lag_relation.ipynb')
