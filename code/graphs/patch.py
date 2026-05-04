import json

def patch_notebook(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    modified = False
    for cell in nb.get('cells', []):
        if cell.get('cell_type') == 'code':
            new_source = []
            for line in cell.get('source', []):
                for old_str, new_str in replacements:
                    if old_str in line:
                        line = line.replace(old_str, new_str)
                        modified = True
                new_source.append(line)
            cell['source'] = new_source
            
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
            print(f'Patched {filepath}')
    else:
        print(f'No replacements made in {filepath}')

replacements = [
    ('q75 = df.groupby("year")["hrm"].quantile(0.80).reset_index(name="p75")', 'q75 = df.groupby("year")["hrm"].quantile(0.75).reset_index(name="p75")'),
    ('q25 = df.groupby("year")["hrm"].quantile(0.20).reset_index(name="p25")', 'q25 = df.groupby("year")["hrm"].quantile(0.25).reset_index(name="p25")'),
    ('# --- Composite scores (each metric already in [0,1]) ---', '# --- Z-score standardization ---\\n    cols = ["Du", "Dw", "BCu", "BCw", "Eu", "Ew", "Cu", "Cw", "ECu", "ECw"]\\n    for col in cols:\\n        df[col] = (df[col] - df[col].mean()) / df[col].std()\\n\\n    # --- Composite scores ---'),
    ('        vals = np.array([v for v in raw.values() if not np.isnan(v)])\\n', ''),
    ('        lo, hi = vals.min(), vals.max()\\n', ''),
    ('            n: (raw[n] - lo) / (hi - lo) if not np.isnan(raw.get(n, np.nan)) else np.nan\\n', '            n: -raw.get(n, np.nan) if not pd.isna(raw.get(n, np.nan)) else np.nan\\n')
]

patch_notebook('c:/Users/madug/paper-financial-graph/code/graphs/build_portfolios.ipynb', replacements)
