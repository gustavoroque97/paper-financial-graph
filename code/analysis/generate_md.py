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
    return count_pct.fillna(0), mcap_pct.fillna(0)

# formatting helper
def fmt(df):
    return df.applymap(lambda x: f"{x:.2f}%").to_markdown()

print("## Tabelas Geradas")

print("\n### 2. Ações vs Não-Ações por Ano (Quantidade %)")
c_pct, m_pct = analyze_composition(df_hcm, 'year', 'Main_Type')
print(fmt(c_pct))

print("\n### 3. Ações vs Não-Ações por Ano (Market Cap %)")
print(fmt(m_pct))

non_stocks = df_hcm[df_hcm['Main_Type'] == 'Non-Stock']
c_pct_ns, m_pct_ns = analyze_composition(non_stocks, 'year', 'Asset_Class')

print("\n### 4. Detalhe de Não-Ações por Ano (Quantidade %)")
print(fmt(c_pct_ns))

print("\n### 5. Detalhe de Não-Ações por Ano (Market Cap %)")
print(fmt(m_pct_ns))

stocks_hcm = df_hcm[df_hcm['Main_Type']=='Stock']
c_pct_s, m_pct_s = analyze_composition(stocks_hcm, 'year', 'Sector')

print("\n### 6. Ações por Setor e Ano (Quantidade %)")
print(fmt(c_pct_s))

print("\n### 7. Ações por Setor e Ano (Market Cap %)")
print(fmt(m_pct_s))

print("\n### 8. HCM: Decil 1 (Central) vs Decil 10 (Periférico) - Tipos de Ativo (Count %)")
d1 = df_hcm[df_hcm['portfolio'] == 'decil_1']
d10 = df_hcm[df_hcm['portfolio'] == 'decil_10']
c1, _ = analyze_composition(d1, 'year', 'Main_Type')
c10, _ = analyze_composition(d10, 'year', 'Main_Type')
print("#### Decil 1 (Núcleo)")
print(fmt(c1))
print("#### Decil 10 (Periferia)")
print(fmt(c10))

print("\n### 9. Pozzi: Decil 1 (Central) vs Decil 10 (Periférico) - Tipos de Ativo (Count %)")
d1_p = df_pozzi[df_pozzi['portfolio'] == 'decil_1']
d10_p = df_pozzi[df_pozzi['portfolio'] == 'decil_10']
c1_p, _ = analyze_composition(d1_p, 'year', 'Main_Type')
c10_p, _ = analyze_composition(d10_p, 'year', 'Main_Type')
print("#### Decil 1 (Núcleo)")
print(fmt(c1_p))
print("#### Decil 10 (Periferia)")
print(fmt(c10_p))

print("\n### 10. HCM: Setores nas Ações - Decil 1 vs Decil 10 (Count %)")
s_d1 = stocks_hcm[stocks_hcm['portfolio'] == 'decil_1']
s_d10 = stocks_hcm[stocks_hcm['portfolio'] == 'decil_10']
sc1, _ = analyze_composition(s_d1, 'year', 'Sector')
sc10, _ = analyze_composition(s_d10, 'year', 'Sector')
print("#### Decil 1 (Núcleo)")
print(fmt(sc1))
print("#### Decil 10 (Periferia)")
print(fmt(sc10))

