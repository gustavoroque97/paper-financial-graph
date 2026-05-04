import json

def patch_notebook(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    replacement_str = """    # Load Market Cap metadata for Value Weighting
    df_mcap = pd.read_csv("../../data/07_portfolios_metadata/all_tickers_complete_metadata.csv")
    
    # 2. Resample Returns to Excess Returns
    weekly_returns = {}
    daily_returns = {}
    weekly2_returns = {}
    monthly_returns = {}
    
    for name, portfolio in portfolios.items():
        year = int(name.split("_")[1])
        log_returns = np.log1p(portfolio)
        R_m = market_returns_dict[year]
        
        mcap_col = f"mcap_{year}"
        if mcap_col not in df_mcap.columns:
            mcap_col = [c for c in df_mcap.columns if "mcap_" in c][-1]
        
        tickers = portfolio.columns.tolist()
        mcaps = df_mcap[df_mcap["Ticker"].isin(tickers)][["Ticker", mcap_col]].copy()
        
        # Clean mcap strings that might have commas or be #ERROR!
        mcaps[mcap_col] = pd.to_numeric(
            mcaps[mcap_col].astype(str).str.replace(',', '.'), 
            errors='coerce'
        ).fillna(0)
        
        weights_df = pd.DataFrame({"Ticker": tickers}).merge(mcaps, on="Ticker", how="left").fillna(0)
        weights = weights_df[mcap_col].values
        if weights.sum() == 0:
            weights = np.ones(len(weights)) / len(weights)
        else:
            weights = weights / weights.sum()
            
        vw_returns = (log_returns * weights).sum(axis=1)
        
        # Aggregating across stocks in the portfolio (value-weighted) minus Market Return
        daily_returns[name] = vw_returns - R_m
        
        weekly_m = R_m.resample("W-FRI").sum()
        weekly_returns[name] = (log_returns.resample("W-FRI").sum() * weights).sum(axis=1) - weekly_m
        
        weekly2_m = R_m.resample("2W-FRI").sum()
        weekly2_returns[name] = (log_returns.resample("2W-FRI").sum() * weights).sum(axis=1) - weekly2_m
        
        monthly_m = R_m.resample("ME").sum()
        monthly_returns[name] = (log_returns.resample("ME").sum() * weights).sum(axis=1) - monthly_m"""

    target_old = """    # 2. Resample Returns to Excess Returns
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
        monthly_returns[name] = log_returns.resample("ME").sum().mean(axis=1) - monthly_m"""

    modified = False
    for cell in nb.get('cells', []):
        if cell.get('cell_type') == 'code':
            source_str = "".join(cell.get('source', []))
            if target_old in source_str:
                source_str = source_str.replace(target_old, replacement_str)
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

patch_notebook('c:/Users/madug/paper-financial-graph/code/trading/out_of_sample.ipynb')
