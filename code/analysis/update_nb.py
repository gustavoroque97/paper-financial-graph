import json

with open('../../code/analysis/graph_analysis.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        updated = False
        # Substitui a paleta de cores antiga pela do paper
        if 'palette = sns.color_palette("colorblind")' in source:
            source = source.replace('palette = sns.color_palette("colorblind")', '')
            source = source.replace('central_color = palette[1]', 'central_color = "#22125F"')
            source = source.replace('peripheral_color = palette[0]', 'peripheral_color = "#2E5C6E"')
            source = source.replace('middle_color = "#BDC3C7"', 'middle_color = "#E5E5E5"')
            updated = True
        
        # Aumentar tamanho das fontes
        if 'fontsize=25' in source:
            source = source.replace('fontsize=25', 'fontsize=28')
            updated = True
            
        # Adicionar o suptitle com HCM/POZZI
        if '# fig.suptitle' in source:
            new_sup = 'fig.suptitle(f"Temporal Network Evolution — Central vs. Peripheral ({\'HCM\' if metric == \'hrm\' else \'POZZI\'})", fontsize=38, fontweight="bold", y=1.03)'
            source = source.replace('# fig.suptitle("TMFG Network by Year — Central vs Peripheral Stocks", fontsize=16, fontweight="bold")', new_sup)
            updated = True

        if updated:
            lines = [line + '\n' for line in source.split('\n')]
            if lines:
                lines[-1] = lines[-1].rstrip('\n')
            cell['source'] = lines

with open('../../code/analysis/graph_analysis.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook updated successfully.")
