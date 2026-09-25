import pandas as pd

df_hcm = pd.read_parquet("../../data/07_portfolios_metadata/complete_metadata_hcm.parquet")
df_pozzi = pd.read_parquet("../../data/07_portfolios_metadata/complete_metadata_pozzi.parquet")

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

def get_top_5(df_comp, year, decil):
    sub_df = df_comp[(df_comp['year'] == str(year)) & 
                     (df_comp['portfolio'] == decil) & 
                     (df_comp['Main_Type'] == 'Stock')]
    result = []
    if not sub_df.empty:
        top5 = sub_df['Industry'].value_counts(normalize=True).head(5)
        result = [f"{nome} ({val*100:.1f}%)" for nome, val in top5.items()]
    while len(result) < 5:
        result.append("-")
    return result

def gen_md_tables(df_comp, metric_name):
    years = sorted(df_comp['year'].dropna().unique())
    d1_data = []
    d10_data = []
    
    for y in years:
        d1_data.append([y] + get_top_5(df_comp, y, 'decil_1'))
        d10_data.append([y] + get_top_5(df_comp, y, 'decil_10'))
        
    cols = ['Year', 'Top 1', 'Top 2', 'Top 3', 'Top 4', 'Top 5']
    d1_df = pd.DataFrame(d1_data, columns=cols).set_index('Year')
    d10_df = pd.DataFrame(d10_data, columns=cols).set_index('Year')
    
    md = f"#### {metric_name} - Ranking Top 5 Indústrias\n"
    md += "**Decil 1 (Núcleo)**\n\n" + d1_df.to_markdown() + "\n\n"
    md += "**Decil 10 (Periferia)**\n\n" + d10_df.to_markdown() + "\n\n"
    return md

md_append = "\n### 6.4 Indústrias nas Ações Extremos (Top 5 Ranking)\n"
md_append += "Abaixo estão as 5 indústrias mais frequentes (em quantidade de ativos) dentro do grupo de Ações para o Núcleo (Decil 1) e Periferia (Decil 10) ao longo do tempo. Isso permite rastrear quais nichos específicos a rede isola ou centraliza.\n\n"
md_append += gen_md_tables(df_hcm, "Topologia HCM")
md_append += gen_md_tables(df_pozzi, "Topologia Pozzi")

with open("new_artifact.md", "a") as f:
    f.write(md_append)

