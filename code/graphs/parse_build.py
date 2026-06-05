import json

with open('../../code/graphs/build_portfolios.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if 'matriz_contingencia = pd.crosstab(' in source:
            print(f"--- Cell {i} ---")
            print(source)
