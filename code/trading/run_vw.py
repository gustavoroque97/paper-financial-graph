import pandas as pd
import numpy as np
years = range(2014, 2025)
c_tc = 0.001
metrics = ["hrm", "pozzi"]

df_ret_full = pd.read_parquet("../../data/01_raw/returns.parquet")
df_ret_full = df_ret_full[df_ret_full.index >= pd.Timestamp(2015, 1, 1)]
if 'HYFT' in df_ret_full.columns: df_ret_full = df_ret_full.drop(columns=['HYFT'])

df_screen = pd.read_parquet("../../data/01_raw/screener_result.parquet")
mcap_dict = df_screen.dropna(subset=['Market Cap', 'Ticker']).set_index('Ticker')['Market Cap'].to_dict()

results_vw = {m: {"decil_1": [], "decil_10": []} for m in metrics}
w_last_vw = {m: {"decil_1": pd.Series(dtype=float), "decil_10": pd.Series(dtype=float)} for m in metrics}

for year in years:
    test_year = year + 1
    df_ret_oos = df_ret_full[df_ret_full.index.year == test_year]
    
    if df_ret_oos.empty:
        continue

    for metric in metrics:
        for decil in [1, 10]:
            chave_decil = f"decil_{decil}"
            metric_file_name = "hcm" if metric == "hrm" else metric 
            d_label = f"decil_{decil}_{year}_{metric_file_name}"
            
            try:
                cols_decil = pd.read_parquet(f"../../data/06_portfolios/{d_label}.parquet").columns
            except FileNotFoundError:
                d_label_fallback = f"decil_{decil}_{year}_{metric}"
                cols_decil = pd.read_parquet(f"../../data/06_portfolios/{d_label_fallback}.parquet").columns
            
            valid = list(set(cols_decil).intersection(df_ret_oos.columns))
            valid_vw = [v for v in valid if v in mcap_dict]
            
            if len(valid_vw) == 0:
                continue
                
            mcaps = pd.Series({v: mcap_dict[v] for v in valid_vw})
            w_initial_vw = mcaps / mcaps.sum()
            
            df_ret_filled = df_ret_oos[valid_vw].fillna(0)
            cum_ret_ativos = (1 + df_ret_filled).cumprod()
            port_cum_ret_vw = (cum_ret_ativos * w_initial_vw).sum(axis=1)
            
            ret_vw = port_cum_ret_vw.pct_change()
            ret_vw.iloc[0] = port_cum_ret_vw.iloc[0] - 1
            
            turnover = w_initial_vw.sub(w_last_vw[metric][chave_decil], fill_value=0).abs().sum()
            tc = c_tc * turnover
            ret_vw.iloc[0] = ret_vw.iloc[0] - tc
            
            ret_vw = np.log1p(ret_vw)
            results_vw[metric][chave_decil].append(ret_vw)
            
            w_final_vw = cum_ret_ativos.iloc[-1] * w_initial_vw
            w_last_vw[metric][chave_decil] = w_final_vw / w_final_vw.sum()

retornos_vw = {}
for metric in metrics:
    retornos_vw[metric] = {}
    for decil in [1, 10]:
        chave_decil = f"decil_{decil}"
        if len(results_vw[metric][chave_decil]) > 0:
            retornos_vw[metric][chave_decil] = pd.concat(results_vw[metric][chave_decil]).sort_index()

ret_long_vw = np.expm1(retornos_vw["hrm"]["decil_10"])
ret_short_vw = np.expm1(retornos_vw["hrm"]["decil_1"])
spread_vw = ret_long_vw - ret_short_vw
print("Value Weighted D10-D1:")
print(spread_vw.describe())

