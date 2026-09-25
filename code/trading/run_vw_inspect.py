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
    if df_ret_oos.empty: continue

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
            
            if len(valid_vw) == 0: continue
                
            mcaps = pd.Series({v: mcap_dict[v] for v in valid_vw})
            w_initial_vw = mcaps / mcaps.sum()
            
            df_ret_filled = df_ret_oos[valid_vw].fillna(0)
            cum_ret_ativos = (1 + df_ret_filled).cumprod()
            port_cum_ret_vw = (cum_ret_ativos * w_initial_vw).sum(axis=1)
            
            ret_vw = port_cum_ret_vw.pct_change()
            ret_vw.iloc[0] = port_cum_ret_vw.iloc[0] - 1
            
            turnover = w_initial_vw.sub(w_last_vw[metric][chave_decil], fill_value=0).abs().sum()
            tc = c_tc * turnover
            ret_vw.iloc[0] -= tc
            
            ret_vw = np.log1p(ret_vw)
            results_vw[metric][chave_decil].append(ret_vw)
            
            w_final_vw = cum_ret_ativos.iloc[-1] * w_initial_vw
            w_last_vw[metric][chave_decil] = w_final_vw / w_final_vw.sum()

def calculate_metrics(returns_simple, series_name):
    if len(returns_simple) < 252: return pd.Series(dtype=float)
    cum_wealth = (1 + returns_simple).cumprod()
    years_count = len(returns_simple) / 252.0
    cagr = (cum_wealth.iloc[-1] ** (1 / years_count)) - 1
    return pd.Series({"CAGR": cagr}, name=series_name)

for m in metrics:
    ret_long_vw = np.expm1(pd.concat(results_vw[m]["decil_10"]).sort_index())
    ret_short_vw = np.expm1(pd.concat(results_vw[m]["decil_1"]).sort_index())
    spread_vw = ret_long_vw - ret_short_vw
    
    print(f"--- {m} ---")
    print("Long D10 VW CAGR:", calculate_metrics(ret_long_vw, "D10")["CAGR"])
    print("Short D1 VW CAGR:", calculate_metrics(ret_short_vw, "D1")["CAGR"])
    print("Spread VW CAGR:", calculate_metrics(spread_vw, "Spread")["CAGR"])

