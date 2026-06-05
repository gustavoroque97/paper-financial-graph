import json

nb = {
    "cells": [],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

def add_markdown(source):
    lines = [line + '\n' for line in source.split('\n')]
    if lines: lines[-1] = lines[-1][:-1] # remove last newline
    nb["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": lines
    })

def add_code(source):
    lines = [line + '\n' for line in source.split('\n')]
    if lines: lines[-1] = lines[-1][:-1]
    nb["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines
    })


markdown_1 = """# Análise Descritiva da Base de Dados (Year-over-Year)

Este notebook tem como objetivo descrever a composição da base de dados completa (todos os ativos), ano a ano, após os filtros de liquidez e qualidade aplicados na metodologia.
Ele substitui a necessidade de cruzar os arquivos de retornos antigos (que foram deletados do repositório), pois extrai as informações da base unificada `complete_metadata_hcm.parquet`."""

code_1 = """import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from IPython.display import display

# Configuração de Estilo para o Paper
sns.set_theme(style="whitegrid", context="paper", font_scale=1.5)

# O arquivo Parquet já contém toda a base de dados ano a ano com os fatores (Beta, Momentum, MCap)
df_meta = pd.read_parquet("../../data/07_portfolios_metadata/complete_metadata_hcm.parquet")

# Como queremos a visão geral (full market), podemos analisar todos os ativos agrupados por ano.
# OBS: Uma mesma empresa aparecerá em vários anos, pois a análise é cross-sectional por ano.
years = sorted(df_meta['year'].unique())
print(f"Anos disponíveis na base: {years}")
print(f"Total de registros (ticker-ano): {len(df_meta)}")"""

markdown_2 = "## 1. Composição Setorial Ano a Ano"

code_2 = """# Tabela de Contagem Setorial Ano a Ano
sector_counts = df_meta.groupby(['year', 'Sector']).size().unstack(fill_value=0)

# Transforma em Porcentagem
sector_pct = sector_counts.div(sector_counts.sum(axis=1), axis=0) * 100

# Ordena as colunas pelo peso médio histórico (Setores mais relevantes primeiro)
sector_order = sector_pct.mean().sort_values(ascending=False).index
sector_pct = sector_pct[sector_order]

print("\\n=== Porcentagem Setorial Ano a Ano (%) ===")
display(sector_pct.round(2))

# Salva a tabela
out_path = Path("../../data/07_portfolios_metadata")
out_path.mkdir(parents=True, exist_ok=True)
sector_pct.round(2).to_csv(out_path / "sector_composition_yoy.csv")"""

markdown_3 = "## 2. Composição por Indústria Ano a Ano (Top 10 + Outros)"

code_3 = """# Tabela de Contagem de Indústria Ano a Ano
industry_counts = df_meta.groupby(['year', 'Industry']).size().unstack(fill_value=0)

# Transforma em Porcentagem
industry_pct = industry_counts.div(industry_counts.sum(axis=1), axis=0) * 100

# Como existem muitas indústrias, vamos focar no Top 10 histórico e agrupar o resto em "Others"
top_10_industries = industry_pct.mean().sort_values(ascending=False).head(10).index

# Criar a nova tabela agrupada
industry_pct_top = industry_pct[top_10_industries].copy()
industry_pct_top['Others'] = industry_pct.drop(columns=top_10_industries).sum(axis=1)

print("\\n=== Porcentagem por Indústria Ano a Ano (%) ===")
display(industry_pct_top.round(2))

# Salva a tabela
industry_pct_top.round(2).to_csv(out_path / "industry_composition_yoy.csv")"""

markdown_4 = "## 3. Evolução das Métricas (MCap, Beta, Momentum) para o Mercado Total"

code_4 = """# Mapeamento das métricas
METRICS = {
    "mcap":     {"ylabel": "Market Cap (log scale)", "title": "Market Cap Evolution (Full Market)", "log_scale": True},
    "beta":     {"ylabel": "Beta",                   "title": "Beta Evolution (Full Market)",       "log_scale": False},
    "momentum": {"ylabel": "Momentum",               "title": "Momentum Evolution (Full Market)",   "log_scale": False}
}

records = []
for year in years:
    df_year = df_meta[df_meta['year'] == year]
    
    for metric_prefix in METRICS.keys():
        col_name = f"{metric_prefix}_{year}"
        if col_name in df_year.columns:
            series = df_year[col_name].dropna()
            
            # Tratamento de segurança caso a coluna seja string com vírgula
            if series.dtype == 'object' or series.dtype.name == 'string':
                series = series.astype(str).str.replace(',', '.', regex=False)
                series = pd.to_numeric(series, errors='coerce').dropna()
                
            for val in series.values:
                records.append({
                    "Portfolio": "Full Market",
                    "Year": int(year),
                    "Metric": metric_prefix,
                    "Value": val
                })

df_long = pd.DataFrame(records)

# Preparando o Grid 3x1
fig, axes = plt.subplots(3, 1, figsize=(16, 18), sharex=True)

# Cor neutra para o mercado total
palette = sns.color_palette("colorblind", n_colors=1)

for ax, (metric_prefix, cfg) in zip(axes, METRICS.items()):
    df_metric = df_long[df_long['Metric'] == metric_prefix]
    
    sns.boxplot(
        data=df_metric, 
        x='Year', 
        y='Value', 
        color='#2E5C6E',
        ax=ax,
        showfliers=False,       # Sem outliers extremos para manter a densidade central visível
        linewidth=1.5,
        boxprops=dict(alpha=0.85, edgecolor='black'),
        medianprops=dict(color='white', linewidth=2.5),
        whiskerprops=dict(color='black', linewidth=1.5),
        capprops=dict(color='black', linewidth=1.5)
    )
    
    if cfg['log_scale']:
        ax.set_yscale('log')
        
    ax.set_ylabel(cfg['ylabel'], fontsize=20, fontweight='bold', labelpad=10)
    ax.set_title(cfg['title'], fontsize=24, fontweight='bold', pad=15)
    ax.tick_params(axis='both', which='major', labelsize=16)
    
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_xlabel("")

# Eixo X apenas no último painel
axes[-1].set_xlabel("Year", fontsize=22, fontweight='bold', labelpad=15)
axes[-1].set_xticklabels(axes[-1].get_xticklabels(), rotation=45)

sns.despine(fig=fig)
plt.tight_layout()

# Salva figura em qualidade de publicação
fig_path = Path("../../figures")
fig_path.mkdir(parents=True, exist_ok=True)
plt.savefig(fig_path / "full_market_mcap_beta_momentum.png", dpi=300, bbox_inches="tight")
plt.show()"""

add_markdown(markdown_1)
add_code(code_1)
add_markdown(markdown_2)
add_code(code_2)
add_markdown(markdown_3)
add_code(code_3)
add_markdown(markdown_4)
add_code(code_4)

with open('comparison.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook gerado via JSON com sucesso!")
