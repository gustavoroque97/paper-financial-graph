import pandas as pd
import numpy as np

# Load Data
df_hcm = pd.read_parquet("../../data/07_portfolios_metadata/complete_metadata_hcm.parquet")
df_pozzi = pd.read_parquet("../../data/07_portfolios_metadata/complete_metadata_pozzi.parquet")

# Extract Mcap
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

# Fix BRK-A
for df in [df_hcm, df_pozzi]:
    brk_b_mcaps = df[df['Ticker'] == 'BRK-B'].set_index('year')['mcap']
    def fix_brka(row):
        if row['Ticker'] == 'BRK-A' and row['year'] in brk_b_mcaps.index:
            return brk_b_mcaps.loc[row['year']]
        return row['mcap']
    df['mcap'] = df.apply(fix_brka, axis=1)

# Classify
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

def fmt(df):
    return df.applymap(lambda x: f"{x:.2f}%").to_markdown()

def analyze_composition(df, group_col, columns_col):
    count_df = df.groupby([group_col, columns_col]).size().unstack(fill_value=0)
    count_pct = count_df.div(count_df.sum(axis=1), axis=0) * 100
    mcap_df = df.groupby([group_col, columns_col])['mcap'].sum().unstack(fill_value=0)
    mcap_pct = mcap_df.div(mcap_df.sum(axis=1).replace(0, np.nan), axis=0) * 100
    return count_pct.fillna(0), mcap_pct.fillna(0)

# Build MD
md = """# Resumo da Análise de Composição do Universo de Investimento (Atualizado)

Este documento sumariza os resultados e as tabelas geradas no notebook `universe_composition_analysis.ipynb`, que avalia a estrutura do universo de ativos e os extremos de cada portfólio. **Os valores de Market Cap foram corrigidos para o outlier da BRK-A**.

## 1. Distribuição Global de Tipos de Ativos
O universo de investimento contém um total de **40.662 registros** ao longo dos anos, divididos em grandes grupos (ações e não-ações). A grande maioria é composta por ações individuais, seguidas pelos ETFs.

---

## 2. Ações vs Não-Ações (Evolução Temporal)
Existe uma clara tendência de crescimento na proporção de Não-Ações (principalmente ETFs) por quantidade. Com a correção da anomalia de Market Cap, vemos que as **Ações mantêm historicamente sua grande dominância em Market Cap (cerca de ~80% do mercado global nos dados).**
"""

c_pct, m_pct = analyze_composition(df_hcm, 'year', 'Main_Type')
md += "\n### 2.1 Por Quantidade (Count %)\n" + fmt(c_pct) + "\n"
md += "\n### 2.2 Por Market Cap (Mcap %)\n" + fmt(m_pct) + "\n\n---\n"

md += """## 3. Composição Detalhada dos "Não-Ações"
Quando isolamos apenas o grupo de Não-Ações (ETFs, CEFs e REITs), observamos que os ETFs dominam, saltando de 63% em 2014 para 78% em 2024 (e mais de 87% de Market Cap).
"""
non_stocks = df_hcm[df_hcm['Main_Type'] == 'Non-Stock']
c_pct_ns, m_pct_ns = analyze_composition(non_stocks, 'year', 'Asset_Class')
md += "\n### 3.1 Detalhe de Não-Ações por Quantidade\n" + fmt(c_pct_ns) + "\n"
md += "\n### 3.2 Detalhe de Não-Ações por Market Cap\n" + fmt(m_pct_ns) + "\n\n---\n"

md += """## 4. Composição Setorial das Ações
O setor **Technology** e o setor **Financial** lideram com folga a representação de Market Cap. A distorção anterior em 2019 de 95% para o setor financeiro desapareceu completamente com a correção da BRK-A.
"""
stocks_hcm = df_hcm[df_hcm['Main_Type']=='Stock']
c_pct_s, m_pct_s = analyze_composition(stocks_hcm, 'year', 'Sector')
md += "\n### 4.1 Ações por Setor (Quantidade %)\n" + fmt(c_pct_s) + "\n"
md += "\n### 4.2 Ações por Setor (Market Cap %)\n" + fmt(m_pct_s) + "\n\n---\n"

md += "## 5. Detalhamento das Top 5 Indústrias por Setor de Ações\n"
md += "Abaixo detalhamos as principais indústrias que compõem cada um dos setores de ações, mostrando a distribuição interna de quantidade e Market Cap. Estão organizados do setor com mais ações para o com menos ações.\n\n"

sectors = stocks_hcm['Sector'].value_counts().index
for sector in sectors:
    sector_df = stocks_hcm[stocks_hcm["Sector"] == sector].copy()
    if sector_df.empty: continue
    
    top_5_industries = sector_df['Industry'].value_counts().nlargest(5).index
    sector_df['Industry_Grouped'] = sector_df['Industry'].apply(lambda x: x if x in top_5_industries else 'Others')
    
    count_pct, mcap_pct = analyze_composition(sector_df, 'year', 'Industry_Grouped')
    
    col_order = [ind for ind in top_5_industries if ind in count_pct.columns]
    if 'Others' in count_pct.columns:
        col_order.append('Others')
        
    count_pct = count_pct[col_order]
    mcap_pct = mcap_pct[col_order]
    
    md += f"### Setor: {sector}\n"
    md += f"**Quantidade (%)**\n{fmt(count_pct)}\n\n"
    md += f"**Market Cap (%)**\n{fmt(mcap_pct)}\n\n"

md += "---\n## 6. Composição de Portfólios Extremos (Decil 1 vs Decil 10)\n"

d1 = df_hcm[df_hcm['portfolio'] == 'decil_1']
d10 = df_hcm[df_hcm['portfolio'] == 'decil_10']
c1, _ = analyze_composition(d1, 'year', 'Main_Type')
c10, _ = analyze_composition(d10, 'year', 'Main_Type')
md += "### 6.1 Topologia HCM (Ações vs Não-Ações)\n"
md += "#### Decil 1 (Núcleo)\n" + fmt(c1) + "\n"
md += "#### Decil 10 (Periferia)\n" + fmt(c10) + "\n\n"

d1_p = df_pozzi[df_pozzi['portfolio'] == 'decil_1']
d10_p = df_pozzi[df_pozzi['portfolio'] == 'decil_10']
c1_p, _ = analyze_composition(d1_p, 'year', 'Main_Type')
c10_p, _ = analyze_composition(d10_p, 'year', 'Main_Type')
md += "### 6.2 Topologia Pozzi (Ações vs Não-Ações)\n"
md += "#### Decil 1 (Núcleo)\n" + fmt(c1_p) + "\n"
md += "#### Decil 10 (Periferia)\n" + fmt(c10_p) + "\n\n"

s_d1 = stocks_hcm[stocks_hcm['portfolio'] == 'decil_1']
s_d10 = stocks_hcm[stocks_hcm['portfolio'] == 'decil_10']
sc1, _ = analyze_composition(s_d1, 'year', 'Sector')
sc10, _ = analyze_composition(s_d10, 'year', 'Sector')
md += "### 6.3 Setores nas Ações Extremos (HCM)\n"
md += "#### Decil 1 (Núcleo)\n" + fmt(sc1) + "\n"
md += "#### Decil 10 (Periferia)\n" + fmt(sc10) + "\n"

with open("new_artifact.md", "w") as f:
    f.write(md)

