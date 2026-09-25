import pandas as pd

df = pd.read_parquet("../../data/07_portfolios_metadata/complete_metadata_hcm.parquet")

def classify_asset_type(row):
    industry = str(row['Industry']).lower()
    sector = str(row['Sector']).lower()
    if 'exchange traded fund' in industry or 'etf' in industry: return 'ETF'
    elif 'closed-end fund' in industry: return 'Closed-End Fund'
    elif 'reit' in industry or 'reit' in sector: return 'REIT'
    elif 'mutual fund' in industry or 'fund' in industry: return 'Other Fund'
    else: return 'Stock'

df['Asset_Class'] = df.apply(classify_asset_type, axis=1)
df['Main_Type'] = df['Asset_Class'].apply(lambda x: 'Stock' if x == 'Stock' else 'Non-Stock')

for year in [2018, 2019]:
    df_y = df[df['year'] == str(year)].copy()
    mcap_col = f'mcap_{year}'
    
    print(f"\n--- YEAR {year} ---")
    print(f"Missing {mcap_col}:")
    print(df_y.groupby('Main_Type')[mcap_col].apply(lambda x: f"{x.isna().sum()} out of {len(x)}"))
    
    print(f"\nSum of {mcap_col}:")
    print(df_y.groupby('Main_Type')[mcap_col].sum())
    
    print("\nTop 3 by Market Cap (Stocks):")
    top_s = df_y[df_y['Main_Type'] == 'Stock'].sort_values(by=mcap_col, ascending=False).head(3)[['Main_Type', 'Sector', 'Industry', mcap_col]]
    print(top_s)
    
    print("\nTop 3 by Market Cap (Non-Stocks):")
    top_ns = df_y[df_y['Main_Type'] == 'Non-Stock'].sort_values(by=mcap_col, ascending=False).head(3)[['Main_Type', 'Sector', 'Industry', mcap_col]]
    print(top_ns)

