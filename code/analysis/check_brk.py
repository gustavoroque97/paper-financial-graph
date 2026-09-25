import pandas as pd

df = pd.read_parquet("../../data/07_portfolios_metadata/complete_metadata_hcm.parquet")

brk_a = df[df['Ticker'] == 'BRK-A']
brk_b = df[df['Ticker'] == 'BRK-B']

years = range(2014, 2025)
print("Year | BRK-A Mcap | BRK-B Mcap")
print("-" * 40)
for y in years:
    mcap_col = f'mcap_{y}'
    
    val_a = brk_a[brk_a['year'] == str(y)][mcap_col].values
    val_a = val_a[0] if len(val_a) > 0 else float('nan')
    
    val_b = brk_b[brk_b['year'] == str(y)][mcap_col].values
    val_b = val_b[0] if len(val_b) > 0 else float('nan')
    
    print(f"{y} | {val_a:12.2e} | {val_b:12.2e}")

