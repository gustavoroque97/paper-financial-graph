import pandas as pd
import numpy as np

years = range(2014, 2025)
c_tc = 0.001
df_ret_full = pd.read_parquet("../../data/01_raw/returns.parquet")
df_ret_full = df_ret_full[df_ret_full.index >= pd.Timestamp(2015, 1, 1)]
if 'HYFT' in df_ret_full.columns: df_ret_full = df_ret_full.drop(columns=['HYFT'])

df_screen = pd.read_parquet("../../data/01_raw/screener_result.parquet")
df_screen = df_screen.dropna(subset=['Market Cap', 'Ticker'])

results_small = []
results_big = []
w_last_small = pd.Series(dtype=float)
w_last_big = pd.Series(dtype=float)

for year in years:
    test_year = year + 1
    df_ret_oos = df_ret_full[df_ret_full.index.year == test_year]
    if df_ret_oos.empty: continue
    
    active_tickers = df_ret_oos.dropna(axis=1, how='all').columns
    active_with_mcap = df_screen[df_screen['Ticker'].isin(active_tickers)]
    if active_with_mcap.empty: continue
    
    median_mcap = active_with_mcap['Market Cap'].median()
    small_tickers = active_with_mcap[active_with_mcap['Market Cap'] <= median_mcap]['Ticker'].tolist()
    big_tickers = active_with_mcap[active_with_mcap['Market Cap'] > median_mcap]['Ticker'].tolist()
    
    df_small = df_ret_oos[small_tickers].fillna(0)
    cum_ret_small = (1 + df_small).cumprod()
    port_cum_ret_small = cum_ret_small.mean(axis=1)
    ret_small = port_cum_ret_small.pct_change()
    ret_small.iloc[0] = port_cum_ret_small.iloc[0] - 1
    
    w_new_small = pd.Series(1.0 / len(small_tickers), index=small_tickers)
    turnover_small = w_new_small.sub(w_last_small, fill_value=0).abs().sum()
    ret_small.iloc[0] = ret_small.iloc[0] - (c_tc * turnover_small)
    results_small.append(np.log1p(ret_small))
    w_last_small = cum_ret_small.iloc[-1] / cum_ret_small.iloc[-1].sum()
    
    df_big = df_ret_oos[big_tickers].fillna(0)
    cum_ret_big = (1 + df_big).cumprod()
    port_cum_ret_big = cum_ret_big.mean(axis=1)
    ret_big = port_cum_ret_big.pct_change()
    ret_big.iloc[0] = port_cum_ret_big.iloc[0] - 1
    
    w_new_big = pd.Series(1.0 / len(big_tickers), index=big_tickers)
    turnover_big = w_new_big.sub(w_last_big, fill_value=0).abs().sum()
    ret_big.iloc[0] = ret_big.iloc[0] - (c_tc * turnover_big)
    results_big.append(np.log1p(ret_big))
    w_last_big = cum_ret_big.iloc[-1] / cum_ret_big.iloc[-1].sum()

serie_small = pd.concat(results_small).sort_index()
serie_big = pd.concat(results_big).sort_index()
smb_simple = np.expm1(serie_small) - np.expm1(serie_big)

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
        "CAGR": cagr, "Annual Volatility": vol_annual,
        "Sharpe Ratio": sharpe, "Sortino Ratio": sortino
    }
    return pd.Series(metrics_dict, name=series_name)

metricas_smb = calculate_metrics(smb_simple, "SMB (Small Minus Big)")
print(metricas_smb)
