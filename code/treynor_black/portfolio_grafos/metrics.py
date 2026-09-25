"""
Módulo de cálculo de métricas de desempenho e risco financeiro.
Implementa métricas completas para análise de estratégias quantitativas:
- Retorno Acumulado e CAGR
- Volatilidade anualizada
- Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Maximum Drawdown
- Value-at-Risk (VaR) e Conditional Value-at-Risk (CVaR / Expected Shortfall) em 95% e 99%
- Beta, Alfa de Jensen (anualizado), Tracking Error, Information Ratio
- Win Rate diário e Profit Factor
"""

import numpy as np
import pandas as pd


def compute_drawdown_series(returns: pd.Series) -> pd.Series:
    """Calcula a série temporal percentual de drawdown a partir dos retornos diários."""
    cum_wealth = (1.0 + returns).cumprod()
    peak = cum_wealth.cummax()
    drawdown = (cum_wealth - peak) / peak
    return drawdown


def calculate_var_cvar(returns: pd.Series, alpha: float = 0.95):
    """
    Calcula o Value at Risk (VaR) e Conditional Value at Risk (CVaR / Expected Shortfall)
    histórico para o nível de confiança alpha (ex: 0.95 ou 0.99).
    Retorna valores positivos representando a perda percentual.
    """
    clean_rets = returns.dropna()
    if len(clean_rets) == 0:
        return np.nan, np.nan
    cutoff = (1.0 - alpha) * 100.0
    var = -np.percentile(clean_rets, cutoff)
    cvar = -clean_rets[clean_rets <= -var].mean()
    return float(var), float(cvar)


def calculate_performance_metrics(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    rf_annual: float = 0.0,
    trading_days_per_year: int = 252,
) -> dict:
    """
    Calcula conjunto exaustivo de métricas de performance e risco para uma série de retornos diários.
    
    Args:
        strategy_returns: Série temporal de retornos diários da estratégia.
        benchmark_returns: Série temporal de retornos diários do benchmark de mercado.
        rf_annual: Taxa livre de risco anualizada (default: 0.0).
        trading_days_per_year: Dias úteis por ano (default: 252).
        
    Returns:
        dict com métricas numéricas e formatadas.
    """
    # Alinhamento de datas
    aligned = pd.concat([strategy_returns, benchmark_returns], axis=1).dropna()
    aligned.columns = ["strat", "bmark"]
    r_strat = aligned["strat"]
    r_bmark = aligned["bmark"]

    n_days = len(r_strat)
    if n_days == 0:
        raise ValueError("A série de retornos está vazia após alinhamento.")

    years = n_days / float(trading_days_per_year)
    rf_daily = (1.0 + rf_annual) ** (1.0 / trading_days_per_year) - 1.0

    # 1. Retorno Cumulativo e CAGR
    cum_wealth = (1.0 + r_strat).cumprod()
    total_cum_ret = float(cum_wealth.iloc[-1] - 1.0)
    cagr = float(cum_wealth.iloc[-1] ** (1.0 / years) - 1.0) if cum_wealth.iloc[-1] > 0 else -1.0

    # 2. Volatilidade Anualizada
    daily_std = float(r_strat.std(ddof=1))
    ann_vol = daily_std * np.sqrt(trading_days_per_year)

    # 3. Sharpe Ratio
    excess_ret = r_strat - rf_daily
    mean_excess = float(excess_ret.mean())
    sharpe = (mean_excess / daily_std) * np.sqrt(trading_days_per_year) if daily_std > 0 else 0.0

    # 4. Sortino Ratio (Downside deviation over total sample N)
    downside_diff = np.minimum(r_strat - rf_daily, 0.0)
    downside_variance = float((downside_diff ** 2).mean())
    if downside_variance > 1e-12:
        downside_std_ann = np.sqrt(downside_variance) * np.sqrt(trading_days_per_year)
        sortino = (mean_excess * trading_days_per_year) / downside_std_ann
    else:
        sortino = np.nan

    # 5. Drawdown e Calmar Ratio
    dd_series = compute_drawdown_series(r_strat)
    max_dd = float(dd_series.min())
    calmar = cagr / abs(max_dd) if abs(max_dd) > 1e-6 else 0.0

    # 6. VaR e CVaR (95% e 99%)
    var_95, cvar_95 = calculate_var_cvar(r_strat, 0.95)
    var_99, cvar_99 = calculate_var_cvar(r_strat, 0.99)

    # 7. Beta, Alfa de Jensen, Tracking Error e Information Ratio
    cov_matrix = np.cov(r_strat, r_bmark)
    cov_strat_bmark = float(cov_matrix[0, 1])
    var_bmark = float(cov_matrix[1, 1])

    beta = cov_strat_bmark / var_bmark if var_bmark > 1e-9 else 1.0
    alpha_daily = float(r_strat.mean() - beta * r_bmark.mean())
    alpha_ann = alpha_daily * trading_days_per_year

    active_returns = r_strat - r_bmark
    tracking_error = float(active_returns.std(ddof=1)) * np.sqrt(trading_days_per_year)
    mean_active = float(active_returns.mean()) * trading_days_per_year
    information_ratio = mean_active / tracking_error if tracking_error > 1e-9 else 0.0

    # 8. Estatísticas adicionais: Win Rate e Profit Factor
    win_rate = float((r_strat > 0).mean())
    sum_pos = float(r_strat[r_strat > 0].sum())
    sum_neg = float(abs(r_strat[r_strat < 0].sum()))
    profit_factor = sum_pos / sum_neg if sum_neg > 1e-9 else np.nan

    # 9. Momentos de distribuição (Skewness & Kurtosis)
    skewness = float(r_strat.skew())
    kurtosis = float(r_strat.kurtosis())

    return {
        "Retorno Total (%)": total_cum_ret * 100.0,
        "CAGR (%)": cagr * 100.0,
        "Volatilidade Anual (%)": ann_vol * 100.0,
        "Sharpe Ratio": sharpe,
        "Sortino Ratio": sortino,
        "Max Drawdown (%)": max_dd * 100.0,
        "Calmar Ratio": calmar,
        "VaR 95% Diário (%)": var_95 * 100.0,
        "CVaR 95% Diário (%)": cvar_95 * 100.0,
        "VaR 99% Diário (%)": var_99 * 100.0,
        "CVaR 99% Diário (%)": cvar_99 * 100.0,
        "Beta": beta,
        "Alfa Anualizado (%)": alpha_ann * 100.0,
        "Tracking Error (%)": tracking_error * 100.0,
        "Information Ratio": information_ratio,
        "Win Rate Diário (%)": win_rate * 100.0,
        "Profit Factor": profit_factor,
        "Skewness": skewness,
        "Kurtosis": kurtosis,
    }


def format_metrics_table(metrics_dict: dict[str, dict]) -> pd.DataFrame:
    """
    Converte um dicionário de {nome_da_estrategia: métricas} em um DataFrame elegante formatado.
    """
    df = pd.DataFrame(metrics_dict)
    
    # Especificação de formatos
    formats = {
        "Retorno Total (%)": "{:,.2f}%",
        "CAGR (%)": "{:,.2f}%",
        "Volatilidade Anual (%)": "{:,.2f}%",
        "Sharpe Ratio": "{:.2f}",
        "Sortino Ratio": "{:.2f}",
        "Max Drawdown (%)": "{:,.2f}%",
        "Calmar Ratio": "{:.2f}",
        "VaR 95% Diário (%)": "{:,.2f}%",
        "CVaR 95% Diário (%)": "{:,.2f}%",
        "VaR 99% Diário (%)": "{:,.2f}%",
        "CVaR 99% Diário (%)": "{:,.2f}%",
        "Beta": "{:.2f}",
        "Alfa Anualizado (%)": "{:,.2f}%",
        "Tracking Error (%)": "{:,.2f}%",
        "Information Ratio": "{:.2f}",
        "Win Rate Diário (%)": "{:,.2f}%",
        "Profit Factor": "{:.2f}",
        "Skewness": "{:.2f}",
        "Kurtosis": "{:.2f}",
    }
    
    formatted_df = pd.DataFrame(index=df.index, columns=df.columns)
    for metric, fmt in formats.items():
        if metric in df.index:
            formatted_df.loc[metric] = df.loc[metric].map(
                lambda v: fmt.format(v) if pd.notnull(v) and not np.isinf(v) else "N/A"
            )
            
    return formatted_df
