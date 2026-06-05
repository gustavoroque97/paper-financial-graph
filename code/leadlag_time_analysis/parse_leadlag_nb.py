import json

with open('../../code/leadlag_time_analysis/time_analysis.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        print(f"\n--- Cell {i} ---")
        print(source)
