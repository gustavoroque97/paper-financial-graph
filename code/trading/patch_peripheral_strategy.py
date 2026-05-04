import json

def patch_notebook(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    replacement_str = """        # 3. Calculate Daily Log Returns for each group (VW Excess)
        mcap_col = f"mcap_{year}"
        if mcap_col not in df_mcap.columns:
            mcap_col = [c for c in df_mcap.columns if "mcap_" in c][-1]
            
        def get_vw_returns(port_cols):
            mcaps = df_mcap[df_mcap["Ticker"].isin(port_cols)][["Ticker", mcap_col]].copy()
            mcaps[mcap_col] = pd.to_numeric(
                mcaps[mcap_col].astype(str).str.replace(',', '.'), 
                errors='coerce'
            ).fillna(0)
            weights_df = pd.DataFrame({"Ticker": port_cols}).merge(mcaps, on="Ticker", how="left").fillna(0)
            w = weights_df[mcap_col].values
            if w.sum() == 0:
                w = np.ones(len(w)) / len(w)
            else:
                w = w / w.sum()
            return (np.log1p(df_ret[port_cols]) * w).sum(axis=1)
            
        R_m = np.log1p(df_ret).mean(axis=1)
        
        ret_central = get_vw_returns(cols_central) - R_m
        ret_peripheral = get_vw_returns(cols_peripheral) - R_m"""

    target_old = """        # 3. Calculate Daily Log Returns for each group
        ret_central = np.log1p(df_ret[cols_central]).mean(axis=1)
        ret_peripheral = np.log1p(df_ret[cols_peripheral]).mean(axis=1)"""

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

patch_notebook('c:/Users/madug/paper-financial-graph/code/trading/peripheral_strategy.ipynb')
