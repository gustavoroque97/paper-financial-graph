import json
with open('../../code/trading/trading.ipynb', 'r', encoding='utf-8') as f: nb = json.load(f)
for i in [6, 7]:
    source = "".join(nb['cells'][i].get('source', []))
    print(f"--- CELL {i} ---\n{source[:200]}...\n{source[-200:]}")
