import json

md_source = "## Estratégia Dinâmica (Lead-Lag Reversal)\nEstratégia que opera o spread diário comprando o *Lag* (Periferia) e vendendo o *Lead* (Centro) se o *Lead* subiu no dia anterior. Caso contrário, inverte a mão. Inclui desconto rigoroso de custos de transação no *Turnover* diário do fator."

code_source = """# =========================================================================
# LEAD-LAG DYNAMIC STRATEGY (TREND FOLLOWING / REVERSAL)
# =========================================================================
# Sinal no dia t: +1 se Retorno_Lead(t) > 0, -1 se Retorno_Lead(t) <= 0
# Posição no dia t+1: +1 (Comprado no Lag, Vendido no Lead) se Sinal == 1
#                     -1 (Vendido no Lag, Comprado no Lead) se Sinal == -1
# Retorno Bruto no dia t+1 = Posicao(t) * (Retorno_Lag(t+1) - Retorno_Lead(t+1)) / 2

c_tc = 0.001
spread_pairs = [(10, 1), (9, 2), (8, 3), (7, 4), (6, 5)]

modelos = [("hrm", "HCM"), ("pozzi", "Pozzi")]
retornos_dict = retornos_consolidados_ew # Usando Equally-Weighted como base

for model_key, model_name in modelos:
    list_leadlag = [metrics_bench, metrics_smb_ff]
    
    if model_key in retornos_dict:
        for lead_d, lag_d in spread_pairs:
            k_lead = f"decil_{lead_d}"
            k_lag = f"decil_{lag_d}"
            
            if k_lead in retornos_dict[model_key] and k_lag in retornos_dict[model_key]:
                ret_lead = np.expm1(retornos_dict[model_key][k_lead])
                ret_lag = np.expm1(retornos_dict[model_key][k_lag])
                
                # O sinal é gerado no final do dia t
                signal = np.where(ret_lead > 0, 1, -1)
                signal_series = pd.Series(signal, index=ret_lead.index)
                
                # A posição só pode ser assumida no dia seguinte (t+1) para evitar look-ahead bias
                position = signal_series.shift(1).fillna(0) # Primeiro dia não tem posição
                
                # Retorno do spread padrão no dia t+1
                spread_return = (0.5 * ret_lag) - (0.5 * ret_lead)
                
                # Retorno Bruto da estratégia dinâmica
                strat_gross_return = position * spread_return
                
                # Custos de transação baseados na mudança de posição (Turnover)
                # Flip de +1 para -1 gera uma mudança absoluta de 2.
                # Como a exposição bruta do spread é 100% (50% long + 50% short = 1), 
                # a mudança de 2 * c_tc reflete exatamente a liquidação de uma ponta e montagem da outra.
                position_change = position.diff().fillna(0).abs()
                strat_net_return = strat_gross_return - (position_change * c_tc)
                
                list_leadlag.append(calculate_metrics(strat_net_return, f"Lead-Lag D{lead_d}-D{lag_d}"))
        
        if len(list_leadlag) > 2:
            df_leadlag = pd.DataFrame(list_leadlag)
            df_leadlag.index = df_leadlag.index.rename("Strategy")
            print(f"\\n--- {model_name} Lead-Lag Dynamic Metrics (EW) ---")
            display(format_table_simple(df_leadlag))
"""

def create_markdown_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")]
    }

def create_code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.split("\n")]
    }

nb_path = '../../code/trading/trading.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Append new cells
nb['cells'].append(create_markdown_cell(md_source.strip()))
nb['cells'].append(create_code_cell(code_source.strip()))

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Appended Lead-Lag strategy cells to the notebook.")
