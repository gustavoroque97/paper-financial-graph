"""
Módulo de implementação da estratégia de trading baseada no modelo de Treynor-Black
e decis de centralidade de rede financeira.
"""

from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd


# Ativos identificados com anomalias severas de dados:
# - BRK-A: Capitalização de mercado corrompida (US$ 1 quadrilhão em 2022-2024), distorcendo o benchmark
# - Ativos em D10 com splits reversos não ajustados ou retornos diários espúrios (> 200% em um dia)
DEFAULT_EXCLUDED_TICKERS = {
    "BRK-A",  # Erro de escala de market cap (1.02e15 a 1.47e15)
    "ABVC",   # Retorno espúrio de +4.165% em um único dia (2015)
    "NCPL",   # Retorno espúrio de +2.665% em um único dia (2020)
    "TPST",   # Retorno espúrio de +3.971% em um único dia (2023)
    "SOBR",   # Retorno espúrio de +2.988% em um único dia (2020)
    "NIXX",   # Retorno espúrio de +2.532% em um único dia (2017)
    "SRXH",   # Retorno espúrio de +1.757% em um único dia (2015)
    "WKSP",   # Retorno espúrio de +1.487% em um único dia (2019)
    "AYTU",   # Retorno espúrio de +1.150% em um único dia (2015)
    "GDC",    # Retorno espúrio de +1.140% em um único dia (2023)
    "GBR",    # Retorno espúrio de +959% em um único dia (2021)
    "MNPR",   # Retorno espúrio de +605% em um único dia (2024)
    "SOWG",   # Alfa espúrio > 700% em 2017
    "LIXT",   # Alfa espúrio > 700% em 2014
    "IVDA",   # Alfa espúrio > 700% em 2019
    "SLNO",   # Retorno espúrio de +504% em 2023
    "RCAT",   # Alfa espúrio > 600% em 2019
}


def resolve_data_dirs(base_dir: Optional[Path] = None) -> tuple[Path, Path]:
    """
    Localiza os diretórios de portfolios de retornos e metadata, compatível
    tanto com o caminho relativo quanto com caminhos de projetos anteriores.
    """
    if base_dir is None:
        base_dir = Path.cwd()

    candidates_portfolios = [
        base_dir / "data" / "01_portfolios",
        base_dir.parent / "data" / "01_portfolios",
        base_dir / "data" / "06_portfolios",
        base_dir.parent / "paper-financial-graph" / "data" / "06_portfolios",
    ]

    candidates_metadata = [
        base_dir / "data" / "02_portfolios_metadata",
        base_dir.parent / "data" / "02_portfolios_metadata",
        base_dir / "data" / "07_portfolios_metadata",
        base_dir.parent / "paper-financial-graph" / "data" / "07_portfolios_metadata",
    ]

    portfolios_dir = next((p for p in candidates_portfolios if p.exists()), None)
    metadata_dir = next((p for p in candidates_metadata if p.exists()), None)

    if portfolios_dir is None or metadata_dir is None:
        raise FileNotFoundError(
            f"Diretórios de dados não encontrados a partir de {base_dir}. "
            f"Portfólios: {portfolios_dir}, Metadata: {metadata_dir}"
        )

    return portfolios_dir, metadata_dir


def load_year_returns(
    year: int,
    metric: str = "hrm",
    portfolios_dir: Optional[Path] = None,
    exclude_tickers: Optional[set[str]] = None,
    max_daily_return_threshold: float = 2.5,
) -> tuple[pd.DataFrame, dict[int, list[str]]]:
    """
    Carrega todos os retornos diários dos 10 decis para um determinado ano,
    removendo ativos da lista de exclusão e filtrando artefatos de splits espúrios.
    
    Retorna:
        all_returns: DataFrame contendo todas as ações dos 10 decis para o ano.
        decile_map: Dicionário mapeando número do decil (1..10) para lista de tickers válidos.
    """
    if portfolios_dir is None:
        portfolios_dir, _ = resolve_data_dirs()

    if exclude_tickers is None:
        exclude_tickers = DEFAULT_EXCLUDED_TICKERS

    decile_map = {}
    dfs = []
    metric_key = metric.lower()
    for d in range(1, 11):
        file_path = portfolios_dir / f"decil_{d}_{year}_{metric_key}.parquet"
        if not file_path.exists() and metric_key == "hcm":
            file_path = portfolios_dir / f"decil_{d}_{year}_hrm.parquet"
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo de decil não encontrado: {file_path}")
        df_d = pd.read_parquet(file_path)

        # Filtrar tickers excluídos e anomalias de retornos diários > threshold
        valid_cols = [
            c for c in df_d.columns
            if c not in exclude_tickers and float(df_d[c].max()) <= max_daily_return_threshold
        ]
        df_d_clean = df_d[valid_cols]
        decile_map[d] = valid_cols
        dfs.append(df_d_clean)

    all_returns = pd.concat(dfs, axis=1)
    return all_returns, decile_map


def load_metadata_market_caps(
    year: int,
    metric: str = "hrm",
    metadata_dir: Optional[Path] = None,
    exclude_tickers: Optional[set[str]] = None,
) -> pd.DataFrame:
    """
    Carrega os metadados e valor de mercado (Market Cap) para o ano especificado,
    excluindo ativos corrompidos (como BRK-A).
    """
    if metadata_dir is None:
        _, metadata_dir = resolve_data_dirs()

    if exclude_tickers is None:
        exclude_tickers = DEFAULT_EXCLUDED_TICKERS

    metric_key = metric.lower()
    complete_file = metadata_dir / f"complete_metadata_{metric_key}.parquet"
    if not complete_file.exists() and metric_key == "hcm":
        complete_file = metadata_dir / "complete_metadata_hrm.parquet"
    if complete_file.exists():
        df_meta = pd.read_parquet(complete_file)
        sub_meta = df_meta[df_meta["year"] == str(year)].copy()
        sub_meta = sub_meta.set_index("Ticker")
        
        # Remover ativos excluídos
        sub_meta = sub_meta.drop(index=[t for t in exclude_tickers if t in sub_meta.index], errors="ignore")
        
        mcap_col = f"mcap_{year}"
        if mcap_col in sub_meta.columns:
            mcap_series = pd.to_numeric(sub_meta[mcap_col], errors="coerce")
            sub_meta["mcap"] = mcap_series
        else:
            sub_meta["mcap"] = np.nan
        return sub_meta

    # Fallback: tentar carregar os arquivos individuais por decil
    records = []
    for d in range(1, 11):
        f = metadata_dir / f"decil_{d}_metadata_{year}_{metric_key}.parquet"
        if not f.exists() and metric_key == "hcm":
            f = metadata_dir / f"decil_{d}_metadata_{year}_hrm.parquet"
        if f.exists():
            df_d = pd.read_parquet(f)
            df_d["portfolio"] = f"decil_{d}"
            records.append(df_d)
    if records:
        combined = pd.concat(records, axis=0).drop_duplicates(subset=["Ticker"])
        combined = combined.set_index("Ticker")
        combined = combined.drop(index=[t for t in exclude_tickers if t in combined.index], errors="ignore")
        mcap_col = f"mcap_{year}"
        if mcap_col in combined.columns:
            combined["mcap"] = pd.to_numeric(combined[mcap_col], errors="coerce")
        else:
            mcap_cols = [c for c in combined.columns if "mcap_" in c]
            combined["mcap"] = pd.to_numeric(combined[mcap_cols[0]], errors="coerce") if mcap_cols else np.nan
        return combined

    raise FileNotFoundError(f"Metadados para o ano {year} e métrica {metric} não encontrados em {metadata_dir}.")


def compute_market_cap_weights(
    tickers: list[str],
    metadata_df: pd.DataFrame,
) -> pd.Series:
    """
    Calcula os pesos de mercado (Market Cap Weighting) para uma lista de tickers.
    Trata valores ausentes/não-positivos preenchendo com a mediana do universo.
    """
    mcap = metadata_df["mcap"].reindex(tickers)
    valid_median = mcap[mcap > 0].median()
    if pd.isna(valid_median) or valid_median <= 0:
        valid_median = 1.0

    mcap_filled = mcap.fillna(valid_median)
    mcap_filled = mcap_filled.apply(lambda v: valid_median if v <= 0 else v)

    weights = mcap_filled / mcap_filled.sum()
    return weights


def fit_single_index_model(
    asset_returns: pd.DataFrame,
    market_returns: pd.Series,
    rf_daily: float = 0.0,
) -> pd.DataFrame:
    """
    Estima o Single-Index Model (CAPM):
    R_i - R_f = alpha_i + beta_i * (R_m - R_f) + e_i
    
    Retorna DataFrame indexado por Ticker com:
    - beta: sensibilidade ao mercado
    - alpha: alfa diário
    - alpha_ann: alfa anualizado (252 dias)
    - resid_var: variância do resíduo (diária)
    - resid_var_ann: variância do resíduo anualizada (252 dias)
    - resid_std_ann: volatilidade idiossincrática anualizada
    """
    r_m_excess = market_returns - rf_daily
    var_m = float(r_m_excess.var(ddof=1))
    mean_m = float(r_m_excess.mean())

    if var_m <= 1e-12:
        raise ValueError("A variância do retorno de mercado é aproximadamente zero.")

    # Excesso de retorno dos ativos
    r_i_excess = asset_returns.sub(rf_daily, axis=0)

    # Co-variância de cada ativo com o mercado
    cov_i_m = r_i_excess.apply(lambda col: col.cov(r_m_excess))
    beta = cov_i_m / var_m

    # Alfa diário e anualizado
    mean_i = r_i_excess.mean()
    alpha_daily = mean_i - beta * mean_m
    alpha_ann = alpha_daily * 252.0

    # Resíduos: e_i = (R_i - R_f) - beta * (R_m - R_f)
    residuals = r_i_excess.sub(r_m_excess.values[:, None] * beta.values, axis=1)
    resid_var_daily = residuals.var(ddof=1)
    resid_var_ann = resid_var_daily * 252.0
    resid_std_ann = np.sqrt(resid_var_ann)

    results = pd.DataFrame(
        {
            "beta": beta,
            "alpha_daily": alpha_daily,
            "alpha_ann": alpha_ann,
            "resid_var_daily": resid_var_daily,
            "resid_var_ann": resid_var_ann,
            "resid_std_ann": resid_std_ann,
        },
        index=asset_returns.columns,
    )
    return results


def compute_treynor_black_weights(
    all_tickers: list[str],
    benchmark_weights: pd.Series,
    d10_tickers: list[str],
    d1_tickers: list[str],
    sim_results: pd.DataFrame,
    mkt_mean_ann: float,
    mkt_var_ann: float,
    allow_short: bool = True,
    active_budget_cap: float = 0.20,
    top_k: int = 25,
) -> tuple[pd.Series, pd.Series, dict]:
    """
    Calcula a reponderação Treynor-Black do portfólio a partir dos pesos de mercado:
    - Seleciona os top_k ativos de D10 com maior alfa positivo (alpha > 0)
    - Seleciona os top_k ativos de D1 com menor alfa negativo (alpha < 0)
    - Pondera via razão de Treynor-Black: w_i^0 = alpha_i / sigma_{e, i}^2
    - Aplica o tilt ativo diretamente sobre a base de pesos de mercado (Market Cap)
    """
    valid_d10 = [t for t in d10_tickers if t in sim_results.index]
    valid_d1 = [t for t in d1_tickers if t in sim_results.index]

    d10_cands = sim_results.loc[valid_d10]
    d1_cands = sim_results.loc[valid_d1]

    d10_pos = d10_cands[d10_cands["alpha_ann"] > 0]
    d1_neg = d1_cands[d1_cands["alpha_ann"] < 0]

    if top_k is not None and top_k > 0:
        d10_sel = d10_pos.sort_values(by="alpha_ann", ascending=False).head(top_k).index
        d1_sel = d1_neg.sort_values(by="alpha_ann", ascending=True).head(top_k).index
    else:
        d10_sel = d10_pos.index
        d1_sel = d1_neg.index

    if len(d10_sel) == 0 and len(d1_sel) == 0:
        return benchmark_weights.copy(), pd.Series(dtype=float), {"wA_star": 0.0}

    # Pesos brutos de Treynor-Black: w_i^0 = alpha_i / sigma_{e, i}^2
    sigmas_10 = sim_results.loc[d10_sel, "resid_var_ann"].replace(0, np.nan).fillna(1.0)
    sigmas_1 = sim_results.loc[d1_sel, "resid_var_ann"].replace(0, np.nan).fillna(1.0)

    w0_10 = sim_results.loc[d10_sel, "alpha_ann"] / sigmas_10
    w0_1 = sim_results.loc[d1_sel, "alpha_ann"] / sigmas_1

    w10_norm = w0_10 / w0_10.sum() if w0_10.sum() > 0 else pd.Series(0.0, index=d10_sel)
    w1_norm = w0_1 / w0_1.abs().sum() if w0_1.abs().sum() > 0 else pd.Series(0.0, index=d1_sel)

    # Reponderação ativa a partir dos pesos de mercado:
    # Aumenta posição em D10 (maior alfa positivo) e diminui em D1 (alfa negativo)
    final_weights = benchmark_weights.copy()
    final_weights.loc[d10_sel] = final_weights.loc[d10_sel] + active_budget_cap * w10_norm
    final_weights.loc[d1_sel] = final_weights.loc[d1_sel] - active_budget_cap * w1_norm.abs()

    if not allow_short:
        final_weights = final_weights.clip(lower=0.0)
        final_weights = final_weights / final_weights.sum()
    else:
        final_weights = final_weights / final_weights.sum()

    alpha_A = float((w10_norm * sim_results.loc[d10_sel, "alpha_ann"]).sum())
    beta_A = float((w10_norm * sim_results.loc[d10_sel, "beta"]).sum())
    sigma_A = float(np.sqrt(((w10_norm ** 2) * sigmas_10).sum()))

    diagnostics = {
        "n_d10_pos": len(d10_sel),
        "n_d1_neg": len(d1_sel),
        "alpha_A": alpha_A,
        "beta_A": beta_A,
        "sigma_A": sigma_A,
        "wA_star_clipped": active_budget_cap,
    }

    active_weights = pd.concat([w10_norm, w1_norm])
    return final_weights, active_weights, diagnostics


def run_treynor_black_backtest(
    years: range = range(2014, 2025),
    metric: str = "hrm",
    active_budget_cap: float = 0.20,
    top_k: int = 25,
    allow_short: bool = True,
    tc_rate: float = 0.001,
    warmup_first_year: bool = True,
    exclude_tickers: Optional[set[str]] = None,
    max_daily_return_threshold: float = 2.5,
) -> dict:
    """
    Executa o backtest completo walk-forward out-of-sample da estratégia Treynor-Black:
    - Ano a ano, constrói o portfólio de mercado com todas as ações ponderadas por Market Cap.
    - No ano t (para t >= 2015), estima alpha e resíduos estritamente com base nos retornos de t-1
      (100% out-of-sample, sem qualquer lookahead bias).
    - Para o primeiro ano (2014):
      * Se warmup_first_year=True (padrão): o portfólio mantém 100% de peso no benchmark passivo
        (zero aposta ativa, zero lookahead bias), servindo 2014 como janela de lookback para 2015.
      * Se warmup_first_year=False: estima in-sample para 2014.
    - Deduz custos de transação (tc_rate, ex: 10 bps = 0.001) no primeiro dia útil de cada rebalanceamento anual.
    - Retorna séries temporais diárias (líquidas e brutas) e diagnósticos anuais.
    """
    portfolios_dir, metadata_dir = resolve_data_dirs()

    # Pré-carregar dados de retornos e metadata para todos os anos
    years_list = list(years)
    market_data = {}
    for y in years_list:
        rets, dec_map = load_year_returns(
            y,
            metric=metric,
            portfolios_dir=portfolios_dir,
            exclude_tickers=exclude_tickers,
            max_daily_return_threshold=max_daily_return_threshold,
        )
        meta = load_metadata_market_caps(
            y,
            metric=metric,
            metadata_dir=metadata_dir,
            exclude_tickers=exclude_tickers,
        )
        w_mkt = compute_market_cap_weights(list(rets.columns), meta)
        r_mkt = rets.dot(w_mkt)
        market_data[y] = {
            "rets": rets,
            "decile_map": dec_map,
            "meta": meta,
            "w_mkt": w_mkt,
            "r_mkt": r_mkt,
        }

    # Armazenamento das séries de retornos
    daily_bmark = []
    daily_tb_gross = []
    daily_tb_net = []
    daily_tb_lo_gross = []
    daily_tb_lo_net = []
    daily_d1_ew = []
    daily_d10_ew = []
    yearly_diagnostics = []

    yearly_weights_tb = {}
    yearly_weights_tb_lo = {}
    yearly_weights_bmark = {}
    yearly_weights_active = {}

    prev_weights_tb = None
    prev_weights_tb_lo = None

    for idx, y in enumerate(years_list):
        curr = market_data[y]
        rets_curr = curr["rets"]
        w_mkt_curr = curr["w_mkt"]
        dec_map_curr = curr["decile_map"]
        r_mkt_curr = curr["r_mkt"]

        daily_bmark.append(r_mkt_curr)
        daily_d1_ew.append(rets_curr[dec_map_curr[1]].mean(axis=1))
        daily_d10_ew.append(rets_curr[dec_map_curr[10]].mean(axis=1))

        if idx == 0 and warmup_first_year:
            # 100% Livre de Lookahead: no ano inicial sem dados anteriores,
            # mantém a carteira de mercado passiva (sem tilts ativos in-sample)
            w_tb = w_mkt_curr.copy()
            w_tb_lo = w_mkt_curr.copy()
            diag = {
                "n_d10_pos": 0,
                "n_d1_neg": 0,
                "alpha_A": 0.0,
                "beta_A": 1.0,
                "sigma_A": 0.0,
                "wA_star_clipped": 0.0,
            }
        else:
            # Janela de estimação: walk-forward (ano anterior t-1 se idx > 0, ou ano corrente se warmup=False)
            if idx > 0:
                est_year = years_list[idx - 1]
                est_data = market_data[est_year]
                rets_est = est_data["rets"]
                r_mkt_est = est_data["r_mkt"]
            else:
                rets_est = rets_curr
                r_mkt_est = r_mkt_curr

            # Estimação do Single-Index Model
            common_tickers = list(rets_est.columns.intersection(rets_curr.columns))
            sim_results = fit_single_index_model(
                rets_est[common_tickers],
                r_mkt_est,
            )

            mkt_mean_ann = float(r_mkt_est.mean() * 252.0)
            mkt_var_ann = float(r_mkt_est.var(ddof=1) * 252.0)

            d10_candidates = [t for t in dec_map_curr[10] if t in common_tickers]
            d1_candidates = [t for t in dec_map_curr[1] if t in common_tickers]

            # 1. Treynor-Black Clássico (Unconstrained / com tilt ativo)
            w_tb, _, diag = compute_treynor_black_weights(
                all_tickers=list(rets_curr.columns),
                benchmark_weights=w_mkt_curr,
                d10_tickers=d10_candidates,
                d1_tickers=d1_candidates,
                sim_results=sim_results,
                mkt_mean_ann=mkt_mean_ann,
                mkt_var_ann=mkt_var_ann,
                allow_short=allow_short,
                active_budget_cap=active_budget_cap,
                top_k=top_k,
            )

            # 2. Treynor-Black Long-Only (Sem posições vendidas)
            w_tb_lo, _, _ = compute_treynor_black_weights(
                all_tickers=list(rets_curr.columns),
                benchmark_weights=w_mkt_curr,
                d10_tickers=d10_candidates,
                d1_tickers=d1_candidates,
                sim_results=sim_results,
                mkt_mean_ann=mkt_mean_ann,
                mkt_var_ann=mkt_var_ann,
                allow_short=False,
                active_budget_cap=active_budget_cap,
                top_k=top_k,
            )

        # Armazenamento anual de pesos
        yearly_weights_tb[y] = w_tb
        yearly_weights_tb_lo[y] = w_tb_lo
        yearly_weights_bmark[y] = w_mkt_curr
        yearly_weights_active[y] = w_tb - w_mkt_curr

        # Retornos diários brutos
        r_tb_gross_y = rets_curr.dot(w_tb)
        r_tb_lo_gross_y = rets_curr.dot(w_tb_lo)

        # Cálculo de Turnover Anual
        if prev_weights_tb is not None:
            all_union_tb = list(set(prev_weights_tb.index).union(set(w_tb.index)))
            w_old_tb = prev_weights_tb.reindex(all_union_tb).fillna(0.0)
            w_new_tb = w_tb.reindex(all_union_tb).fillna(0.0)
            turnover_tb = float((w_new_tb - w_old_tb).abs().sum())
        else:
            turnover_tb = float((w_tb - w_mkt_curr).abs().sum())

        if prev_weights_tb_lo is not None:
            all_union_lo = list(set(prev_weights_tb_lo.index).union(set(w_tb_lo.index)))
            w_old_lo = prev_weights_tb_lo.reindex(all_union_lo).fillna(0.0)
            w_new_lo = w_tb_lo.reindex(all_union_lo).fillna(0.0)
            turnover_tb_lo = float((w_new_lo - w_old_lo).abs().sum())
        else:
            turnover_tb_lo = float((w_tb_lo - w_mkt_curr).abs().sum())

        prev_weights_tb = w_tb
        prev_weights_tb_lo = w_tb_lo

        # Aplicação dos Custos de Transação (10 bps = 0.001 sobre o turnover de rebalanceamento)
        cost_tb = turnover_tb * tc_rate
        cost_tb_lo = turnover_tb_lo * tc_rate

        r_tb_net_y = r_tb_gross_y.copy()
        r_tb_lo_net_y = r_tb_lo_gross_y.copy()

        if len(r_tb_net_y) > 0 and cost_tb > 0:
            r_tb_net_y.iloc[0] -= cost_tb
        if len(r_tb_lo_net_y) > 0 and cost_tb_lo > 0:
            r_tb_lo_net_y.iloc[0] -= cost_tb_lo

        daily_tb_gross.append(r_tb_gross_y)
        daily_tb_net.append(r_tb_net_y)
        daily_tb_lo_gross.append(r_tb_lo_gross_y)
        daily_tb_lo_net.append(r_tb_lo_net_y)

        diag["year"] = y
        diag["turnover_unconstrained"] = turnover_tb
        diag["turnover_long_only"] = turnover_tb_lo
        diag["cost_unconstrained"] = cost_tb
        diag["cost_long_only"] = cost_tb_lo
        yearly_diagnostics.append(diag)

    # Consolidação das séries temporais diárias
    series_bmark = pd.concat(daily_bmark)
    series_tb_net = pd.concat(daily_tb_net)
    series_tb_gross = pd.concat(daily_tb_gross)
    series_tb_lo_net = pd.concat(daily_tb_lo_net)
    series_tb_lo_gross = pd.concat(daily_tb_lo_gross)
    series_d1_ew = pd.concat(daily_d1_ew)
    series_d10_ew = pd.concat(daily_d10_ew)

    diag_df = pd.DataFrame(yearly_diagnostics).set_index("year")

    return {
        "benchmark": series_bmark,
        "treynor_black": series_tb_net,
        "treynor_black_gross": series_tb_gross,
        "treynor_black_long_only": series_tb_lo_net,
        "treynor_black_long_only_gross": series_tb_lo_gross,
        "decil_1_central": series_d1_ew,
        "decil_10_peripheral": series_d10_ew,
        "yearly_diagnostics": diag_df,
        "turnover_by_year": diag_df["turnover_unconstrained"],
        "weights_treynor_black": yearly_weights_tb,
        "weights_treynor_black_long_only": yearly_weights_tb_lo,
        "weights_benchmark": yearly_weights_bmark,
        "active_weights": yearly_weights_active,
        "weights_by_year": {
            y: {
                "benchmark": yearly_weights_bmark[y],
                "treynor_black": yearly_weights_tb[y],
                "treynor_black_long_only": yearly_weights_tb_lo[y],
                "active": yearly_weights_active[y],
            }
            for y in years_list
        },
    }


def _normalize_strategy_key(strategy: str) -> str:
    """Normaliza o nome da estratégia para a chave correspondente de pesos."""
    s = strategy.lower().strip().replace("-", "_").replace(" ", "_")
    if s in {"treynor_black", "tb", "unconstrained"}:
        return "weights_treynor_black"
    elif s in {"treynor_black_long_only", "tb_lo", "long_only", "lo"}:
        return "weights_treynor_black_long_only"
    elif s in {"benchmark", "bmark", "mkt", "market"}:
        return "weights_benchmark"
    elif s in {"active", "tilt", "active_weights"}:
        return "active_weights"
    elif s in {"weights_treynor_black", "weights_treynor_black_long_only", "weights_benchmark", "active_weights"}:
        return s
    raise ValueError(f"Estratégia desconhecida: {strategy}. Opções: treynor_black, treynor_black_long_only, benchmark, active.")


def get_strategy_weights(
    results: dict,
    strategy: str = "treynor_black",
    year: Optional[int] = None,
) -> pd.Series | pd.DataFrame:
    """
    Retorna os pesos alocados na estratégia solicitada.
    
    Args:
        results: Dicionário retornado por run_treynor_black_backtest.
        strategy: 'treynor_black', 'treynor_black_long_only', 'benchmark' ou 'active'.
        year: Ano desejado (ex: 2020). Se None, retorna DataFrame consolidado (tickers x anos).
        
    Returns:
        pd.Series com pesos do ano (se year fornecido) ou pd.DataFrame com anos nas colunas.
    """
    key = _normalize_strategy_key(strategy)
    weights_dict = results.get(key)
    if weights_dict is None:
        raise KeyError(f"Chave de pesos '{key}' não encontrada nos resultados do backtest.")

    if year is not None:
        if year not in weights_dict:
            raise KeyError(f"Ano {year} não encontrado nos pesos da estratégia. Anos disponíveis: {list(weights_dict.keys())}")
        return weights_dict[year].copy()

    # Consolidar todos os anos em um único DataFrame
    df = pd.DataFrame(weights_dict).fillna(0.0)
    df.index.name = "Ticker"
    return df


def get_portfolio_holdings(
    results: dict,
    year: int,
    strategy: str = "treynor_black",
    top_k: Optional[int] = None,
    min_weight: float = 0.0,
    sort_by: str = "Weight",
    ascending: bool = False,
    metric: str = "hrm",
    metadata_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Retorna a tabela detalhada de ativos e pesos alocados em um ano de rebalanceamento,
    enriquecida com metadados econômicos e setoriais.
    
    Args:
        results: Dicionário retornado por run_treynor_black_backtest.
        year: Ano do rebalanceamento (ex: 2020).
        strategy: 'treynor_black', 'treynor_black_long_only' ou 'benchmark'.
        top_k: Quantidade de ativos a retornar (ex: 20). Se None, retorna todos acima de min_weight.
        min_weight: Filtro de peso absoluto mínimo (ex: 0.001 para 0.1%).
        sort_by: Coluna para ordenação ('Weight', 'Active_Weight', 'Market_Cap', etc.).
        ascending: Ordem crescente ou decrescente.
        metric: Métrica de centralidade de rede ('hrm', 'pozzi', 'hcm').
        metadata_dir: Diretório de metadados (opcional).
        
    Returns:
        pd.DataFrame com colunas:
        - Ticker
        - Weight (%): Peso final da estratégia
        - Benchmark_Weight (%): Peso no benchmark de mercado
        - Active_Weight (%): Peso ativo (tilt: Estratégia - Benchmark)
        - Sector: Setor econômico
        - Industry: Indústria
        - Decile: Decil de centralidade de rede (1..10)
        - Market_Cap: Capitalização de mercado
        - Beta: Beta em relação ao mercado
        - Momentum: Momentum 12M
    """
    key = _normalize_strategy_key(strategy)
    w_strat = results[key][year]
    w_bmark = results["weights_benchmark"][year]

    # Carregar metadados do ano
    meta = load_metadata_market_caps(year, metric=metric, metadata_dir=metadata_dir)

    all_tickers = sorted(list(set(w_strat.index).union(set(w_bmark.index))))
    df = pd.DataFrame(index=all_tickers)
    df["Weight"] = w_strat.reindex(all_tickers).fillna(0.0)
    df["Benchmark_Weight"] = w_bmark.reindex(all_tickers).fillna(0.0)
    df["Active_Weight"] = df["Weight"] - df["Benchmark_Weight"]

    # Enriquecimento com metadados
    if "Sector" in meta.columns:
        df["Sector"] = meta["Sector"].reindex(all_tickers).fillna("Não Classificado")
    else:
        df["Sector"] = "N/A"

    if "Industry" in meta.columns:
        df["Industry"] = meta["Industry"].reindex(all_tickers).fillna("N/A")
    else:
        df["Industry"] = "N/A"

    if "portfolio" in meta.columns:
        df["Decile"] = meta["portfolio"].reindex(all_tickers).fillna("N/A")
    else:
        df["Decile"] = "N/A"

    if "mcap" in meta.columns:
        df["Market_Cap"] = meta["mcap"].reindex(all_tickers)
    else:
        df["Market_Cap"] = np.nan

    beta_col = f"beta_{year}"
    if beta_col in meta.columns:
        df["Beta"] = meta[beta_col].reindex(all_tickers)
    else:
        df["Beta"] = np.nan

    mom_col = f"momentum_{year}"
    if mom_col in meta.columns:
        df["Momentum"] = meta[mom_col].reindex(all_tickers)
    else:
        df["Momentum"] = np.nan

    # Filtro de peso mínimo
    if min_weight > 0.0:
        df = df[df["Weight"].abs() >= min_weight]

    # Ordenação
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)
    elif sort_by == "abs_active":
        df = df.iloc[df["Active_Weight"].abs().argsort()[::-1]]

    if top_k is not None and top_k > 0:
        df = df.head(top_k)

    df.index.name = "Ticker"
    return df


def get_active_bets(
    results: dict,
    year: int,
    strategy: str = "treynor_black",
    top_k: int = 15,
    metric: str = "hrm",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Retorna as maiores apostas ativas (tilts) da estratégia em um dado ano:
    - top_overweight: ações mais sobreponderadas (Active_Weight > 0)
    - top_underweight: ações mais subponderadas ou vendidas (Active_Weight < 0)
    """
    holdings = get_portfolio_holdings(
        results=results,
        year=year,
        strategy=strategy,
        top_k=None,
        min_weight=0.0,
        metric=metric,
    )

    top_overweight = holdings[holdings["Active_Weight"] > 0].sort_values(
        by="Active_Weight", ascending=False
    ).head(top_k)

    top_underweight = holdings[holdings["Active_Weight"] < 0].sort_values(
        by="Active_Weight", ascending=True
    ).head(top_k)

    return top_overweight, top_underweight

