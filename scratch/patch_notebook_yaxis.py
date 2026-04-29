import json

file_path = 'c:/Users/groque/Desktop/paper-financial-graph/code/analysis/year_to_year_analysis.ipynb'

with open(file_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "def plot_metric_boxplot_evolution(" in source:
            # Add pad_inches=0.2 to savefig and adjust tight_layout
            source = source.replace('bbox_inches="tight"', 'bbox_inches="tight", pad_inches=0.3')
            # For plt.tight_layout(), we can add rect=[0,0,1,0.95] if title is used, but for now just use it as is or add pad
            if 'plt.tight_layout()' in source:
                source = source.replace('plt.tight_layout()', 'plt.tight_layout(pad=1.5)')
            
            # Reconstruct the cell source
            cell['source'] = [line + ('\n' if i < len(source.split('\n')) - 1 else '') for i, line in enumerate(source.split('\n'))]

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
