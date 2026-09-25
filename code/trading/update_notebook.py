import json

with open('../../code/trading/trading.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the cell containing the benchmark and strategies logic
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "benchmark_anual = []" in source or "for year in years:" in source:
            print(f"Cell {i} matches!")
            
