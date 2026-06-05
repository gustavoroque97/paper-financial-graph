import json

with open('../../code/graphs/lead_lag_relation.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if 'def autocorrelation_matrix' in source:
            print("FOUND IT:")
            print(source)
