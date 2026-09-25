import json

with open('../../code/analysis/universe_composition_analysis.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        for output in cell.get('outputs', []):
            if output.get('output_type') == 'stream':
                print(output['text'][0].strip())
            if output.get('output_type') == 'display_data' and 'data' in output and 'text/plain' in output['data']:
                text_plain = "".join(output['data']['text/plain'])
                if "Styler" not in text_plain:
                    print(text_plain)
