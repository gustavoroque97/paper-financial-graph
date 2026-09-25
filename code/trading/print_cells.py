import json
with open('../../code/trading/trading.ipynb', 'r', encoding='utf-8') as f: nb = json.load(f)
for i in [1, 4, 5]:
    source = "".join(nb['cells'][i]['source'])
    print(f"--- CELL {i} ---\n{source[:200]}...\n{source[-200:]}")
