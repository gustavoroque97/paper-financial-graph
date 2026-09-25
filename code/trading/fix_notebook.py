import json

cell1_source = """import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import os
import warnings
from IPython.display import display

warnings.filterwarnings('ignore')

# --- CONFIGURAÇÃO ---
years = range(2014, 2025)
metrics = ["hrm", "pozzi"]
deciles = list(range(1, 11))
spread_pairs = [(10, 1), (9, 2), (8, 3), (7, 4), (6, 5)]
c_tc = 0.001 # Custo de transação (10 bps)

# --- CARREGAMENTO DE DADOS ---
df_ret_full = pd.read_parquet("../../data/01_raw/returns.parquet")
if 'HYFT' in df_ret_full.columns:
    df_ret_full = df_ret_full.drop(columns=['HYFT'])

df_screen = pd.read_parquet("../../data/01_raw/screener_result.parquet")
mcap_dict = df_screen.dropna(subset=['Market Cap', 'Ticker']).set_index('Ticker')['Market Cap'].to_dict()
"""

cell2_source = """# =========================================================================
# BACKTEST: BENCHMARK E ESTRATÉGIAS (COM FILTRO DE LIQUIDEZ E OPÇÃO 1)
# =========================================================================

# --- 1. BENCHMARK GLOBAL ---
benchmark_anual = []
w_last_bench = pd.Series(dtype=float) 
df_ret_pos_2015 = df_ret_full[df_ret_full.index >= pd.Timestamp(2015, 1, 1)]

for year in df_ret_pos_2015.index.year.unique():
    df_ano = df_ret_pos_2015[df_ret_pos_2015.index.year == year]
    valid_cols = df_ano.dropna(axis=1, how='all').columns
    
    # Opção 1 para o Benchmark:
    if w_last_bench.empty:
        w_initial_bench = pd.Series(1.0 / len(valid_cols), index=valid_cols)
    else:
        survivors = list(set(w_last_bench.index).intersection(valid_cols))
        exits = list(set(w_last_bench.index) - set(valid_cols))
        new_entrants = list(set(valid_cols) - set(w_last_bench.index))
        
        w_freed = w_last_bench[exits].sum() if len(exits) > 0 else 0.0
        w_initial_bench = pd.Series(0.0, index=valid_cols)
        
        if len(survivors) > 0:
            w_initial_bench[survivors] = w_last_bench[survivors]
        
        if len(new_entrants) > 0:
            w_initial_bench[new_entrants] = w_freed / len(new_entrants)
        elif w_freed > 0 and len(survivors) > 0:
            w_initial_bench[survivors] += w_freed * (w_initial_bench[survivors] / w_initial_bench[survivors].sum())
            
    df_ano_filled = df_ano[valid_cols].fillna(0)
    cum_ret_ativos = (1 + df_ano_filled).cumprod()
    port_cum_ret = (cum_ret_ativos * w_initial_bench).sum(axis=1)
    
    ret = port_cum_ret.pct_change()
    ret.iloc[0] = port_cum_ret.iloc[0] - 1
    
    turnover = w_initial_bench.sub(w_last_bench, fill_value=0).abs().sum()
    ret.iloc[0] -= (c_tc * turnover)
    
    benchmark_anual.append(ret)
    
    w_final_bench = cum_ret_ativos.iloc[-1] * w_initial_bench
    w_last_bench = w_final_bench / w_final_bench.sum()

market_benchmark_global = pd.concat(benchmark_anual).sort_index()

# --- 2. ESTRATÉGIAS (DECIS) ---
results_ew = {m: {f"decil_{d}": [] for d in deciles} for m in metrics}
results_vw = {m: {"decil_1": [], "decil_10": []} for m in metrics}

w_last_ew = {m: {f"decil_{d}": pd.Series(dtype=float) for d in deciles} for m in metrics}
w_last_vw = {m: {"decil_1": pd.Series(dtype=float), "decil_10": pd.Series(dtype=float)} for m in metrics}

for year in years:
    test_year = year + 1
    
    df_ret_in_sample = df_ret_full[df_ret_full.index.year == year]
    df_ret_oos = df_ret_full[df_ret_full.index.year == test_year]
    
    if df_ret_oos.empty or df_ret_in_sample.empty: continue
        
    # Filtro de Liquidez (<= 20% dias zerados)
    total_dias_is = len(df_ret_in_sample)
    proporcao_zeros = (df_ret_in_sample == 0.0).sum() / total_dias_is
    acoes_liquidas = set(proporcao_zeros[proporcao_zeros <= 0.20].index.tolist())

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
            
            valid_ew = list(set(cols_decil).intersection(df_ret_oos.columns).intersection(acoes_liquidas))
            if len(valid_ew) == 0: continue

            # --- EW: OPÇÃO 1 (Buy & Hold Parcial) ---
            w_last = w_last_ew[metric][chave_decil]
            if w_last.empty:
                w_initial_ew = pd.Series(1.0 / len(valid_ew), index=valid_ew)
            else:
                survivors = list(set(w_last.index).intersection(valid_ew))
                exits = list(set(w_last.index) - set(valid_ew))
                new_entrants = list(set(valid_ew) - set(w_last.index))
                
                w_freed = w_last[exits].sum() if len(exits) > 0 else 0.0
                w_initial_ew = pd.Series(0.0, index=valid_ew)
                
                if len(survivors) > 0: w_initial_ew[survivors] = w_last[survivors]
                if len(new_entrants) > 0: w_initial_ew[new_entrants] = w_freed / len(new_entrants)
                elif w_freed > 0 and len(survivors) > 0:
                    w_initial_ew[survivors] += w_freed * (w_initial_ew[survivors] / w_initial_ew[survivors].sum())
            
            df_ret_filled_ew = df_ret_oos[valid_ew].fillna(0)
            cum_ret_ativos_ew = (1 + df_ret_filled_ew).cumprod()
            port_cum_ret_ew = (cum_ret_ativos_ew * w_initial_ew).sum(axis=1)
            
            ret_ew = port_cum_ret_ew.pct_change()
            ret_ew.iloc[0] = port_cum_ret_ew.iloc[0] - 1
            
            turnover_ew = w_initial_ew.sub(w_last, fill_value=0).abs().sum()
            ret_ew.iloc[0] -= (c_tc * turnover_ew)
            
            results_ew[metric][chave_decil].append(np.log1p(ret_ew))
            
            w_final_ew = cum_ret_ativos_ew.iloc[-1] * w_initial_ew
            w_last_ew[metric][chave_decil] = w_final_ew / w_final_ew.sum()
            
            # --- VW (Value-Weighted): APENAS D1 E D10 ---
            if decil in [1, 10]:
                valid_vw = [v for v in valid_ew if v in mcap_dict]
                if len(valid_vw) > 0:
                    mcaps = pd.Series({v: mcap_dict[v] for v in valid_vw})
                    w_initial_vw = mcaps / mcaps.sum()
                    
                    df_ret_filled_vw = df_ret_oos[valid_vw].fillna(0)
                    cum_ret_ativos_vw = (1 + df_ret_filled_vw).cumprod()
                    port_cum_ret_vw = (cum_ret_ativos_vw * w_initial_vw).sum(axis=1)
                    
                    ret_vw = port_cum_ret_vw.pct_change()
                    ret_vw.iloc[0] = port_cum_ret_vw.iloc[0] - 1
                    
                    turnover_vw = w_initial_vw.sub(w_last_vw[metric][chave_decil], fill_value=0).abs().sum()
                    ret_vw.iloc[0] -= (c_tc * turnover_vw)
                    
                    results_vw[metric][chave_decil].append(np.log1p(ret_vw))
                    
                    w_final_vw = cum_ret_ativos_vw.iloc[-1] * w_initial_vw
                    w_last_vw[metric][chave_decil] = w_final_vw / w_final_vw.sum()

# Consolidando séries
retornos_consolidados_ew = {}
retornos_consolidados_vw = {}
for metric in metrics:
    retornos_consolidados_ew[metric] = {}
    for decil in deciles:
        chave_decil = f"decil_{decil}"
        if len(results_ew[metric][chave_decil]) > 0:
            retornos_consolidados_ew[metric][chave_decil] = pd.concat(results_ew[metric][chave_decil]).sort_index()
            
    retornos_consolidados_vw[metric] = {}
    for decil in [1, 10]:
        chave_decil = f"decil_{decil}"
        if len(results_vw[metric][chave_decil]) > 0:
            retornos_consolidados_vw[metric][chave_decil] = pd.concat(results_vw[metric][chave_decil]).sort_index()
"""

cell3_source = """# =========================================================================
# FAMA-FRENCH E FUNÇÕES DE MÉTRICAS
# =========================================================================
def calculate_metrics(returns_simple, series_name):
    if len(returns_simple) < 252:
        return pd.Series(dtype=float)
        
    cum_wealth = (1 + returns_simple).cumprod()
    years_count = len(returns_simple) / 252.0
    cagr = (cum_wealth.iloc[-1] ** (1 / years_count)) - 1
    vol_annual = returns_simple.std() * np.sqrt(252)
    sharpe = (returns_simple.mean() * 252) / vol_annual if vol_annual != 0 else 0
    neg_returns = returns_simple[returns_simple < 0]
    downside_std = neg_returns.std() * np.sqrt(252)
    sortino = (returns_simple.mean() * 252) / downside_std if downside_std != 0 else 0
    
    highwater_mark = cum_wealth.cummax()
    drawdown = (cum_wealth / highwater_mark) - 1
    max_dd = drawdown.min()
    underwater = drawdown[drawdown < 0]
    avg_dd = underwater.mean() if len(underwater) > 0 else 0
        
    var_99 = np.percentile(returns_simple, 1)
    cvar_99 = returns_simple[returns_simple <= var_99].mean()
    
    metrics_dict = {
        "CAGR": cagr, "Annual Volatility": vol_annual,
        "Sharpe Ratio": sharpe, "Sortino Ratio": sortino,
        "Max Drawdown": max_dd, "Average Drawdown": avg_dd,
        "VaR 99%": var_99, "CVaR 99%": cvar_99
    }
    return pd.Series(metrics_dict, name=series_name)

# Benchmark Global
metrics_bench = calculate_metrics(market_benchmark_global, "Global Benchmark")

# SMB Fama-French
ff_df = pd.read_parquet("../../data/02_clean/fama_french_factors.parquet")
ff_df = ff_df / 100
smb_ff = ff_df[ff_df.index >= pd.Timestamp("2015-01-01")]["SMB"]
smb_ff_aligned = smb_ff.reindex(market_benchmark_global.index).fillna(0)
metrics_smb_ff = calculate_metrics(smb_ff_aligned, "Fama-French SMB")
"""

cell4_source = """# =========================================================================
# EXIBIÇÃO DE RESULTADOS
# =========================================================================
def format_table_simple(df):
    df_fmt = pd.DataFrame()
    df_fmt["CAGR"] = df["CAGR"].apply(lambda x: f"{x:.2%}")
    df_fmt["Annual Volatility"] = df["Annual Volatility"].apply(lambda x: f"{x:.2%}")
    df_fmt["Sharpe Ratio"] = df["Sharpe Ratio"].apply(lambda x: f"{x:.2f}")
    df_fmt["Sortino Ratio"] = df["Sortino Ratio"].apply(lambda x: f"{x:.2f}")
    df_fmt["Max Drawdown"] = df["Max Drawdown"].apply(lambda x: f"{x:.2%}")
    df_fmt["Average Drawdown"] = df["Average Drawdown"].apply(lambda x: f"{x:.2%}")
    df_fmt["VaR 99%"] = df["VaR 99%"].apply(lambda x: f"{x:.2%}")
    df_fmt["CVaR 99%"] = df["CVaR 99%"].apply(lambda x: f"{x:.2%}")
    df_fmt.index = df.index
    return df_fmt

# --- 1. TABELAS DE DECIS INDIVIDUAIS (EW) ---
for metric in metrics:
    metric_name = "HCM" if metric == "hrm" else "Pozzi"
    list_deciles = [metrics_bench]
    for d in deciles:
        chave = f"decil_{d}"
        if chave in retornos_consolidados_ew[metric]:
            strat_simple = np.expm1(retornos_consolidados_ew[metric][chave])
            list_deciles.append(calculate_metrics(strat_simple, f"Decil {d}"))
            
    df_deciles = pd.DataFrame(list_deciles)
    df_deciles.index = df_deciles.index.rename("Strategy")
    print(f"--- {metric_name} Deciles Metrics (EW) ---")
    display(format_table_simple(df_deciles))

# --- 2. TABELAS DE SPREADS LONG-SHORT (EW vs VW) ---
modelos = [("hrm", "HCM"), ("pozzi", "Pozzi")]
pesos = [("ew", "Equally Weighted"), ("vw", "Value Weighted")]

for model_key, model_name in modelos:
    for weight_key, weight_name in pesos:
        list_spreads = [metrics_smb_ff]
        dicionario_alvo = retornos_consolidados_ew if weight_key == "ew" else retornos_consolidados_vw
        
        if model_key in dicionario_alvo:
            for long_d, short_d in spread_pairs:
                k_long = f"decil_{long_d}"
                k_short = f"decil_{short_d}"
                
                if k_long in dicionario_alvo[model_key] and k_short in dicionario_alvo[model_key]:
                    ret_long = np.expm1(dicionario_alvo[model_key][k_long])
                    ret_short = np.expm1(dicionario_alvo[model_key][k_short])
                    spread_simple = (0.5 * ret_long) - (0.5 * ret_short)
                    list_spreads.append(calculate_metrics(spread_simple, f"Spread D{long_d}-D{short_d}"))
            
            if len(list_spreads) > 1:
                df_spread = pd.DataFrame(list_spreads)
                df_spread.index = df_spread.index.rename("Strategy")
                print(f"\n--- {model_name} Spread Metrics ({weight_name}) ---")
                display(format_table_simple(df_spread))
"""

# Read the original notebook
nb_path = '../../code/trading/trading.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Keep only the first Markdown cell if it exists, otherwise empty
new_cells = []
if len(nb['cells']) > 0 and nb['cells'][0]['cell_type'] == 'markdown':
    new_cells.append(nb['cells'][0])

def create_code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.split("\n")]
    }

new_cells.append(create_code_cell(cell1_source.strip()))
new_cells.append(create_code_cell(cell2_source.strip()))
new_cells.append(create_code_cell(cell3_source.strip()))
new_cells.append(create_code_cell(cell4_source.strip()))

nb['cells'] = new_cells

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook updated successfully!")
