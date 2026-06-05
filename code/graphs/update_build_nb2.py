import json

c12_new = """import matplotlib.pyplot as plt
import seaborn as sns
import os

sns.set_theme(style="white", context="paper")

# 1. Criar a matriz de contagem cruzada entre os decis
# Usamos os labels ordenados para garantir que o gráfico vá do decil_1 ao decil_10 certinho
matriz_contingencia = pd.crosstab(
    df_year["decil_hrm"], 
    df_year["decil_pozzi"], 
    normalize="index"  # Mostra a proporção (porcentagem) em cada linha
)

# Limpar os nomes (remover "decil_") para deixar só o número
matriz_contingencia.index = matriz_contingencia.index.str.replace("decil_", "")
matriz_contingencia.columns = matriz_contingencia.columns.str.replace("decil_", "")

TITLE_SIZE = 26
LABEL_SIZE = 22
TICK_SIZE = 18
ANNOTATE_SIZE = 16

# 2. Plotar o Heatmap
fig, ax = plt.subplots(figsize=(14, 10))
sns.heatmap(
    matriz_contingencia, 
    annot=True,          
    fmt=".2f",           
    cmap="Blues",        
    linewidths=.5,
    annot_kws={"size": ANNOTATE_SIZE, "fontweight": "bold"},
    cbar_kws={'shrink': 0.8},
    ax=ax
)

ax.set_title("Classification Dispersion: Decile HCM vs Decile POZZI", fontsize=TITLE_SIZE, fontweight="bold", pad=20)
ax.set_xlabel("POZZI Deciles", fontsize=LABEL_SIZE, fontweight="bold", labelpad=15)
ax.set_ylabel("HCM Deciles", fontsize=LABEL_SIZE, fontweight="bold", labelpad=15)

# Aumentar tamanho das fontes dos eixos e colorbar
ax.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=TICK_SIZE)

plt.tight_layout()
os.makedirs("../../figures", exist_ok=True)
plt.savefig("../../figures/heatmap_dispersao_hcm_pozzi.png", dpi=300, bbox_inches="tight")
plt.show()
"""

with open('../../code/graphs/build_portfolios.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if 'matriz_contingencia = pd.crosstab(' in source:
            lines = [line + '\n' for line in c12_new.split('\n')]
            if lines: lines[-1] = lines[-1].rstrip('\n')
            cell['source'] = lines
            break

with open('../../code/graphs/build_portfolios.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("build_portfolios.ipynb updated successfully")
