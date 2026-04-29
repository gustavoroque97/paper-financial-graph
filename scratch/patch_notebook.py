import json

file_path = 'c:/Users/groque/Desktop/paper-financial-graph/code/analysis/graph_analysis.ipynb'

with open(file_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "from matplotlib.lines import Line2D" in source:
            # Modify font sizes
            source = source.replace('font_size=5', 'font_size=8')
            source = source.replace('font_size=6', 'font_size=8')
            source = source.replace('font_size=7', 'font_size=10')
            source = source.replace('fontsize=14', 'fontsize=18')
            source = source.replace('fontsize=11', 'fontsize=16')
            source = source.replace('fontsize=16', 'fontsize=20')
            source = source.replace('fontsize=12', 'fontsize=16')
            
            # Put it back to cell['source']
            cell['source'] = [line + ('\n' if i < len(source.split('\n')) - 1 else '') for i, line in enumerate(source.split('\n'))]

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
