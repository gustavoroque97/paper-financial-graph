"""
Módulo de regressões multi-fatoriais de Fama-French para análise de atribuição de risco e alfa.
Implementa o modelo de 3 fatores de Fama-French (1993) e CAPM com erros padrão robustos
HAC (Newey-West / Heteroskedasticity and Autocorrelation Consistent).
"""

from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
import statsmodels.api as sm

from .strategy import resolve_data_dirs


def resolve_fama_french_dir(base_dir: Optional[Path] = None) -> Path:
    """Localiza o arquivo ou pasta de fatores de Fama-French."""
    if base_dir is None:
        base_dir = Path.cwd()

    candidates = [
        base_dir / "data" / "03_fama_french",
        base_dir.parent / "data" / "03_fama_french",
        base_dir / "data" / "05_fama_french",
        base_dir.parent / "paper-financial-graph" / "data" / "05_fama_french",
    ]
    for c in candidates:
        if c.exists():
            return c

    # Tenta usar o arquivo direto
    direct = base_dir / "data" / "03_fama_french" / "fama_french_factors.parquet"
    if direct.exists():
        return direct.parent

    raise FileNotFoundError(f"Diretório de Fama-French não encontrado a partir de {base_dir}.")


def load_fama_french_factors(
    data_dir: Optional[Path] = None,
    scale_to_decimal: bool = True,
) -> pd.DataFrame:
    """
    Carrega a série diária dos fatores de Fama-French (Mkt-RF, SMB, HML, RF).
    
    Args:
        data_dir: Diretório onde se localiza o arquivo fama_french_factors.parquet.
        scale_to_decimal: Se True, divide os valores por 100 para converter de percentual
            (padrão Kenneth French Data Library) para escala decimal, tornando compatível
            com os retornos diários das ações.
            
    Returns:
        pd.DataFrame indexado por DatetimeIndex com as colunas ['Mkt-RF', 'SMB', 'HML', 'RF'].
    """
    if data_dir is None:
        data_dir = resolve_fama_french_dir()

    file_path = data_dir / "fama_french_factors.parquet"
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo de fatores Fama-French não encontrado: {file_path}")

    df = pd.read_parquet(file_path)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    if scale_to_decimal:
        # Fatores originais vêm em % (ex: 0.05 = 0.05%), convertendo para decimal (0.0005)
        df = df / 100.0

    return df


def _pvalue_to_stars(pval: float) -> str:
    """Retorna os asteriscos de significância estatística."""
    if pval < 0.01:
        return "***"
    elif pval < 0.05:
        return "**"
    elif pval < 0.10:
        return "*"
    return ""


def run_fama_french_regression(
    strategy_returns: pd.Series,
    ff_factors: Optional[pd.DataFrame] = None,
    model: str = "3-factor",
    cov_type: str = "HAC",
    maxlags: int = 5,
    rf_series: Optional[pd.Series] = None,
) -> dict:
    """
    Executa a regressão do excesso de retorno da estratégia contra os fatores de risco.
    
    Modelos suportados:
    - '3-factor': R_p - R_f = alpha + beta_Mkt * (Mkt - RF) + beta_SMB * SMB + beta_HML * HML + e
    - 'capm' ou '1-factor': R_p - R_f = alpha + beta_Mkt * (Mkt - RF) + e
    
    Args:
        strategy_returns: Série temporal de retornos diários da estratégia.
        ff_factors: DataFrame com fatores Fama-French (se None, carrega automaticamente).
        model: '3-factor' ou 'capm'.
        cov_type: Tipo de matriz de covariância ('HAC' para Newey-West robusto, 'HC1', ou 'nonrobust').
        maxlags: Quantidade de defasagens para o estimador HAC (padrão: 5).
        rf_series: Série customizada da taxa livre de risco (se None, utiliza RF dos fatores).
        
    Returns:
        dict com coeficientes, estatísticas t, p-valores, alfas anualizados e métricas do modelo.
    """
    if ff_factors is None:
        ff_factors = load_fama_french_factors(scale_to_decimal=True)

    # Alinhar datas
    strat_s = strategy_returns.copy()
    strat_s.index = pd.to_datetime(strat_s.index)

    aligned = pd.concat([strat_s.rename("strat"), ff_factors], axis=1).dropna()

    if len(aligned) < 30:
        raise ValueError(f"Amostra insuficiente ({len(aligned)} dias) para estimar regressão de fatores.")

    # Excesso de retorno
    rf = aligned["RF"] if rf_series is None else rf_series.reindex(aligned.index).fillna(0.0)
    y = aligned["strat"] - rf

    # Matriz de variáveis explicativas
    model_clean = model.lower().strip()
    if model_clean in {"capm", "1-factor", "1_factor"}:
        factor_cols = ["Mkt-RF"]
    elif model_clean in {"3-factor", "3_factor", "fama_french_3"}:
        factor_cols = ["Mkt-RF", "SMB", "HML"]
    else:
        raise ValueError(f"Modelo não reconhecido: {model}. Opções: '3-factor' ou 'capm'.")

    X = sm.add_constant(aligned[factor_cols])

    # Estimação OLS com matriz de covariância robusta
    ols_model = sm.OLS(y, X)
    if cov_type == "HAC":
        fit_res = ols_model.fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    elif cov_type in {"HC1", "HC2", "HC3"}:
        fit_res = ols_model.fit(cov_type=cov_type)
    else:
        fit_res = ols_model.fit()

    params = fit_res.params
    bse = fit_res.bse
    tvalues = fit_res.tvalues
    pvalues = fit_res.pvalues

    alpha_daily = float(params["const"])
    alpha_ann = alpha_daily * 252.0
    alpha_ann_pct = alpha_ann * 100.0

    resid_std_daily = float(np.std(fit_res.resid, ddof=len(params)))
    resid_std_ann_pct = resid_std_daily * np.sqrt(252.0) * 100.0

    result = {
        "model": model,
        "n_obs": int(fit_res.nobs),
        "r2": float(fit_res.rsquared),
        "r2_adj": float(fit_res.rsquared_adj),
        "f_stat": float(fit_res.fvalue) if hasattr(fit_res, "fvalue") and fit_res.fvalue is not None else np.nan,
        "f_pval": float(fit_res.f_pvalue) if hasattr(fit_res, "f_pvalue") and fit_res.f_pvalue is not None else np.nan,
        "alpha_daily": alpha_daily,
        "alpha_ann": alpha_ann,
        "alpha_ann_pct": alpha_ann_pct,
        "alpha_se": float(bse["const"]),
        "alpha_tstat": float(tvalues["const"]),
        "alpha_pval": float(pvalues["const"]),
        "alpha_stars": _pvalue_to_stars(pvalues["const"]),
        "beta_mkt": float(params["Mkt-RF"]),
        "beta_mkt_se": float(bse["Mkt-RF"]),
        "beta_mkt_tstat": float(tvalues["Mkt-RF"]),
        "beta_mkt_pval": float(pvalues["Mkt-RF"]),
        "beta_mkt_stars": _pvalue_to_stars(pvalues["Mkt-RF"]),
        "resid_std_ann_pct": resid_std_ann_pct,
        "model_fit": fit_res,
    }

    if "SMB" in factor_cols:
        result["beta_smb"] = float(params["SMB"])
        result["beta_smb_se"] = float(bse["SMB"])
        result["beta_smb_tstat"] = float(tvalues["SMB"])
        result["beta_smb_pval"] = float(pvalues["SMB"])
        result["beta_smb_stars"] = _pvalue_to_stars(pvalues["SMB"])

    if "HML" in factor_cols:
        result["beta_hml"] = float(params["HML"])
        result["beta_hml_se"] = float(bse["HML"])
        result["beta_hml_tstat"] = float(tvalues["HML"])
        result["beta_hml_pval"] = float(pvalues["HML"])
        result["beta_hml_stars"] = _pvalue_to_stars(pvalues["HML"])

    return result


def compare_fama_french_models(
    returns_dict: dict[str, pd.Series],
    ff_factors: Optional[pd.DataFrame] = None,
    model: str = "3-factor",
    cov_type: str = "HAC",
    maxlags: int = 5,
) -> pd.DataFrame:
    """
    Compara os resultados das regressões de Fama-French para múltiplas estratégias,
    gerando uma tabela acadêmica elegante e completa com estrelas de significância estatística.
    
    Args:
        returns_dict: Dicionário {Nome_Estratégia: pd.Series de retornos diários}.
        ff_factors: DataFrame dos fatores Fama-French.
        model: '3-factor' ou 'capm'.
        cov_type: Tipo de erro padrão ('HAC' recomendado).
        
    Returns:
        pd.DataFrame formatado pronto para publicação e visualização executiva.
    """
    if ff_factors is None:
        ff_factors = load_fama_french_factors(scale_to_decimal=True)

    cols = {}
    for name, s in returns_dict.items():
        res = run_fama_french_regression(
            strategy_returns=s,
            ff_factors=ff_factors,
            model=model,
            cov_type=cov_type,
            maxlags=maxlags,
        )

        col_data = {
            "Annualized Alpha (%)": f"{res['alpha_ann_pct']:+.2f}% {res['alpha_stars']}".strip(),
            "  t(Alpha)": f"({res['alpha_tstat']:.2f})",
            "  p-value(Alpha)": f"{res['alpha_pval']:.4f}",
            "Market Beta (Mkt-RF)": f"{res['beta_mkt']:.3f} {res['beta_mkt_stars']}".strip(),
            "  t(Beta Mkt)": f"({res['beta_mkt_tstat']:.2f})",
        }

        if model in {"3-factor", "3_factor", "fama_french_3"}:
            col_data["Size Beta (SMB)"] = f"{res['beta_smb']:.3f} {res['beta_smb_stars']}".strip()
            col_data["  t(Beta SMB)"] = f"({res['beta_smb_tstat']:.2f})"
            col_data["Value Beta (HML)"] = f"{res['beta_hml']:.3f} {res['beta_hml_stars']}".strip()
            col_data["  t(Beta HML)"] = f"({res['beta_hml_tstat']:.2f})"

        col_data["R² (%)"] = f"{res['r2'] * 100.0:.2f}%"
        col_data["Adjusted R² (%)"] = f"{res['r2_adj'] * 100.0:.2f}%"
        col_data["F-Statistic"] = f"{res['f_stat']:.1f}"
        col_data["Annual Residual Volatility (%)"] = f"{res['resid_std_ann_pct']:.2f}%"
        col_data["Observations"] = f"{res['n_obs']:,}"

        cols[name] = col_data

    df_comp = pd.DataFrame(cols)
    return df_comp


def run_rolling_fama_french(
    strategy_returns: pd.Series,
    ff_factors: Optional[pd.DataFrame] = None,
    window: int = 252,
    model: str = "3-factor",
    step: int = 21,
    cov_type: str = "HAC",
) -> pd.DataFrame:
    """
    Calculates factor exposures and rolling alpha over rolling windows (e.g. 1 year = 252 trading days).
    """
    if ff_factors is None:
        ff_factors = load_fama_french_factors(scale_to_decimal=True)

    strat_s = strategy_returns.copy()
    strat_s.index = pd.to_datetime(strat_s.index)
    aligned = pd.concat([strat_s.rename("strat"), ff_factors], axis=1).dropna()

    n = len(aligned)
    if n < window:
        raise ValueError(f"Series with {n} observations is shorter than rolling window of {window} days.")

    dates = []
    alphas = []
    beta_mkts = []
    beta_smbs = []
    beta_hmls = []
    r2_adjs = []

    for i in range(window, n + 1, step):
        sub = aligned.iloc[i - window : i]
        end_date = sub.index[-1]
        y_sub = sub["strat"] - sub["RF"]

        if model in {"capm", "1-factor"}:
            cols = ["Mkt-RF"]
        else:
            cols = ["Mkt-RF", "SMB", "HML"]

        X_sub = sm.add_constant(sub[cols])
        try:
            fit = sm.OLS(y_sub, X_sub).fit(cov_type=cov_type if cov_type != "HAC" else "nonrobust")
            alpha_ann = float(fit.params["const"] * 252.0 * 100.0)
            b_mkt = float(fit.params["Mkt-RF"])
            b_smb = float(fit.params["SMB"]) if "SMB" in cols else np.nan
            b_hml = float(fit.params["HML"]) if "HML" in cols else np.nan
            r2_a = float(fit.rsquared_adj * 100.0)
        except Exception:
            continue

        dates.append(end_date)
        alphas.append(alpha_ann)
        beta_mkts.append(b_mkt)
        beta_smbs.append(b_smb)
        beta_hmls.append(b_hml)
        r2_adjs.append(r2_a)

    df_roll = pd.DataFrame(
        {
            "Annualized Alpha (% p.a.)": alphas,
            "Market Beta (Mkt-RF)": beta_mkts,
            "Size Beta (SMB)": beta_smbs,
            "Value Beta (HML)": beta_hmls,
            "Adjusted R² (%)": r2_adjs,
        },
        index=dates,
    )
    df_roll.index.name = "Date"
    return df_roll

