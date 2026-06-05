import json

with open('../../code/analysis/graph_analysis.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if 'plt.' in source or 'sns.' in source:
            print(f"--- Cell {i} ---")
            print(source)
