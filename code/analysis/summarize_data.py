import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

df_hcm = pd.read_parquet("../../data/07_portfolios_metadata/complete_metadata_hcm.parquet")
df_pozzi = pd.read_parquet("../../data/07_portfolios_metadata/complete_metadata_pozzi.parquet")

def extract_mcap(df):
    def get_mcap(row):
        year = int(row['year'])
        col = f'mcap_{year}'
        if col in row.index:
            return row[col]
        return np.nan
    df['mcap'] = df.apply(get_mcap, axis=1)
    return df

df_hcm = extract_mcap(df_hcm)
df_pozzi = extract_mcap(df_pozzi)

def classify_asset_type(row):
    industry = str(row['Industry']).lower()
    sector = str(row['Sector']).lower()
    if 'exchange traded fund' in industry or 'etf' in industry: return 'ETF'
    elif 'closed-end fund' in industry: return 'Closed-End Fund'
    elif 'reit' in industry or 'reit' in sector: return 'REIT'
    elif 'mutual fund' in industry or 'fund' in industry: return 'Other Fund'
    else: return 'Stock'

for df in [df_hcm, df_pozzi]:
    df['Asset_Class'] = df.apply(classify_asset_type, axis=1)
    df['Main_Type'] = df['Asset_Class'].apply(lambda x: 'Stock' if x == 'Stock' else 'Non-Stock')

def analyze_composition(df, group_col, columns_col):
    count_df = df.groupby([group_col, columns_col]).size().unstack(fill_value=0)
    count_pct = count_df.div(count_df.sum(axis=1), axis=0) * 100
    mcap_df = df.groupby([group_col, columns_col])['mcap'].sum().unstack(fill_value=0)
    mcap_pct = mcap_df.div(mcap_df.sum(axis=1).replace(0, np.nan), axis=0) * 100
    return count_pct.fillna(0).round(2), mcap_pct.fillna(0).round(2)

print("\n--- 4.1 HCM: Decil Central (decil_1) vs Periferico (decil_10) ---")
for decil, label in [('decil_1', 'Central (HCM)'), ('decil_10', 'Periferico (HCM)')]:
    print(f"\n{label}:")
    d_df = df_hcm[df_hcm['portfolio'] == decil]
    c_pct, m_pct = analyze_composition(d_df, 'year', 'Main_Type')
    print("Count %:")
    print(c_pct.mean())
    
print("\n--- 4.2 Pozzi: Decil Central (decil_1) vs Periferico (decil_10) ---")
for decil, label in [('decil_1', 'Central (Pozzi)'), ('decil_10', 'Periferico (Pozzi)')]:
    print(f"\n{label}:")
    d_df = df_pozzi[df_pozzi['portfolio'] == decil]
    c_pct, m_pct = analyze_composition(d_df, 'year', 'Main_Type')
    print("Count %:")
    print(c_pct.mean())

print("\n--- 4.3 Setores nas Acoes HCM: Decil 1 vs 10 ---")
stocks_hcm = df_hcm[df_hcm['Main_Type']=='Stock']
for decil in ['decil_1', 'decil_10']:
    print(f"\nSetor - HCM {decil}:")
    c_pct, m_pct = analyze_composition(stocks_hcm[stocks_hcm['portfolio'] == decil], 'year', 'Sector')
    print("Count % Mean:")
    print(c_pct.mean().sort_values(ascending=False).head(3))
