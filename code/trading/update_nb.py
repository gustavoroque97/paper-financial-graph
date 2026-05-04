import json
import re

with open('c:/Users/madug/paper-financial-graph/code/trading/out_of_sample.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_multi_lag_peri_cent = '''            matrix = []
            for R_peri, R_cent in pairs:
                X = pd.concat([R_peri, R_cent], axis=1).dropna()
                X.columns = ["Peripheral", "Central"]
                
                max_lag = 5
                valid_lags = [l for l in range(1, max_lag + 1) if len(X) >= l + 4]
                if not valid_lags:
                    matrix.append(float('nan'))
                    continue
                    
                total_lead_lag = 0
                for l in valid_lags:
                    acm = autocorrelation_matrix(X, lag=l)
                    lag_matrix = acm - acm.T
                    total_lead_lag += lag_matrix[1, 0]
                
                matrix.append(total_lead_lag)'''

new_multi_lag_small_large = '''        matrix = []
        for R_small, R_large in pairs:
            X = pd.concat([R_small, R_large], axis=1).dropna()
            X.columns = ["Small", "Large"]
            
            max_lag = 5
            valid_lags = [l for l in range(1, max_lag + 1) if len(X) >= l + 4]
            if not valid_lags:
                matrix.append(float('nan'))
                continue
                
            total_lead_lag = 0
            for l in valid_lags:
                acm = autocorrelation_matrix(X, lag=l)
                lag_matrix = acm - acm.T
                total_lead_lag += lag_matrix[1, 0]
                
            matrix.append(total_lead_lag)'''

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'def out_of_sample_lead_lag' in source:
            source = re.sub(r'            matrix = \[\]\n            for R_peri, R_cent in pairs:\n                X = pd\.concat\(\[R_peri, R_cent\], axis=1\)\.dropna\(\)\n                X\.columns = \["Peripheral", "Central"\]\n                \n                # Assumes autocorrelation_matrix is defined in your environment\n                acm = autocorrelation_matrix\(X, lag=1\)\n                lag_matrix = acm - acm\.T\n                matrix\.append\(lag_matrix\[1, 0\]\)', new_multi_lag_peri_cent, source, flags=re.DOTALL)
            
            source = re.sub(r'        matrix = \[\]\n        for R_small, R_large in pairs:\n            X = pd\.concat\(\[R_small, R_large\], axis=1\)\.dropna\(\)\n            X\.columns = \["Small", "Large"\]\n            \n            acm = autocorrelation_matrix\(X, lag=1\)\n            lag_matrix = acm - acm\.T\n            matrix\.append\(lag_matrix\[1, 0\]\)', new_multi_lag_small_large, source, flags=re.DOTALL)

            cell['source'] = [line + '\n' for line in source.split('\n')]
            cell['source'][-1] = cell['source'][-1].strip('\n')

with open('c:/Users/madug/paper-financial-graph/code/trading/out_of_sample.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
