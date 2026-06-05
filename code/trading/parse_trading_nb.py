import json

with open('../../code/trading/out_of_sample.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        print(f"\n--- Cell {i} ---")
        print("".join(cell['source']))
