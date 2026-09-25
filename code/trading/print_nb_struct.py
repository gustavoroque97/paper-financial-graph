import json
with open('../../code/trading/trading.ipynb', 'r', encoding='utf-8') as f: nb = json.load(f)
for i, cell in enumerate(nb['cells']):
    print(f"Cell {i}: {cell['cell_type']} - {len(''.join(cell.get('source', [])))} chars")
