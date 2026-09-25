import pandas as pd
import numpy as np

# Copiando a configuração do notebook
years = range(2014, 2025)
metrics = ["hrm", "pozzi"]
deciles = list(range(1, 11))
c_tc = 0.001

df_ret_full = pd.read_parquet("../../data/01_raw/returns.parquet")
df_ret_full = df_ret_full[df_ret_full.index >= pd.Timestamp(2015, 1, 1)]
if 'HYFT' in df_ret_full.columns:
    df_ret_full = df_ret_full.drop(columns=['HYFT'])

results_strat = {m: {f"decil_{d}": [] for d in deciles} for m in metrics}
w_last_strat = {m: {f"decil_{d}": pd.Series(dtype=float) for d in deciles} for m in metrics}

for year in years:
    test_year = year + 1
    df_ret_oos = df_ret_full[df_ret_full.index.year == test_year]
    if df_ret_oos.empty: continue

    for metric in metrics:
        for decil in deciles:
            chave_decil = f"decil_{decil}"
            metric_file_name = "hcm" if metric == "hrm" else metric 
            d_label = f"decil_{decil}_{year}_{metric_file_name}"
            
            try:
                cols_decil = pd.read_parquet(f"../../data/06_portfolios/{d_label}.parquet").columns
            except FileNotFoundError:
                d_label_fallback = f"decil_{decil}_{year}_{metric}"
                cols_decil = pd.read_parquet(f"../../data/06_portfolios/{d_label_fallback}.parquet").columns
            
            valid = list(set(cols_decil).intersection(df_ret_oos.columns))
            if len(valid) == 0: continue

            df_ret_filled = df_ret_oos[valid].fillna(0)
            cum_ret_ativos = (1 + df_ret_filled).cumprod()
            port_cum_ret = cum_ret_ativos.mean(axis=1)
            
            ret = port_cum_ret.pct_change()
            ret.iloc[0] = port_cum_ret.iloc[0] - 1
            
            w_new = pd.Series(1.0 / len(valid), index=valid)
            turnover = w_new.sub(w_last_strat[metric][chave_decil], fill_value=0).abs().sum()
            tc = c_tc * turnover
            ret.iloc[0] = ret.iloc[0] - tc
            ret = np.log1p(ret)

            results_strat[metric][chave_decil].append(ret)
            w_last_strat[metric][chave_decil] = cum_ret_ativos.iloc[-1] / cum_ret_ativos.iloc[-1].sum()

retornos_consolidados = {}
for metric in metrics:
    retornos_consolidados[metric] = {}
    for decil in deciles:
        chave_decil = f"decil_{decil}"
        if len(results_strat[metric][chave_decil]) > 0:
            serie_completa = pd.concat(results_strat[metric][chave_decil])
            retornos_consolidados[metric][chave_decil] = serie_completa.sort_index()

def calculate_metrics(returns_simple, series_name):
    if len(returns_simple) < 252: return pd.Series(dtype=float)
    cum_wealth = (1 + returns_simple).cumprod()
    years_count = len(returns_simple) / 252.0
    cagr = (cum_wealth.iloc[-1] ** (1 / years_count)) - 1
    vol_annual = returns_simple.std() * np.sqrt(252)
    sharpe = (returns_simple.mean() * 252) / vol_annual if vol_annual != 0 else 0
    neg_returns = returns_simple[returns_simple < 0]
    downside_std = neg_returns.std() * np.sqrt(252)
    sortino = (returns_simple.mean() * 252) / downside_std if downside_std != 0 else 0
    
    metrics_dict = {
        "CAGR": f"{cagr:.2%}", "Annual Volatility": f"{vol_annual:.2%}",
        "Sharpe Ratio": f"{sharpe:.2f}", "Sortino Ratio": f"{sortino:.2f}"
    }
    return pd.Series(metrics_dict, name=series_name)

spread_pairs = [(10, 1), (9, 2), (8, 3), (7, 4), (6, 5)]

for metric in metrics:
    print(f"\n--- {metric.upper()} Spread Metrics ---")
    list_spread = []
    for long_d, short_d in spread_pairs:
        k_long = f"decil_{long_d}"
        k_short = f"decil_{short_d}"
        if k_long in retornos_consolidados[metric] and k_short in retornos_consolidados[metric]:
            ret_long = np.expm1(retornos_consolidados[metric][k_long])
            ret_short = np.expm1(retornos_consolidados[metric][k_short])
            spread_simple = ret_long - ret_short
            list_spread.append(calculate_metrics(spread_simple, f"Spread D{long_d}-D{short_d}"))
    df_spread = pd.DataFrame(list_spread)
    print(df_spread.to_string())

