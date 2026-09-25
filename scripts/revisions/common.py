"""
Shared utilities for the revision analyses (R3 / R8 / S1).

Design goals
------------
* Reuse the *exact* artefacts produced by the existing pipeline (TMFG graphs,
  decile portfolios, metadata, Fama-French factors).
* Keep the dependency surface small: numpy + pandas + pyarrow + networkx.
  (scikit-learn is required only by the optional network-rebuild path.)
* Never fabricate results: every function reads from disk and fails loudly.

The centrality definitions mirror ``code/graphs/build_portfolios.ipynb``
(cells 3 and 4) verbatim in spirit, so that the stocks-only replication is
directly comparable to the published tables.
"""

from __future__ import annotations

import pickle
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
from statistics import NormalDist

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
CLEAN = DATA / "02_clean"
GRAPHS = DATA / "04_graphs"
PORT = DATA / "06_portfolios"
META = DATA / "07_portfolios_metadata"
OUT = REPO / "reviews" / "outputs"

YEARS = list(range(2014, 2025))
OOS_YEARS = list(range(2015, 2025))          # years with an observable t+1 return


def ensure_out() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    return OUT


# --------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------
def load_factors(path: Path | None = None) -> pd.DataFrame:
    """Fama-French factors in decimals (source file is in percent)."""
    p = Path(path) if path else CLEAN / "fama_french_factors.parquet"
    f = pd.read_parquet(p) / 100.0
    f.index = pd.to_datetime(f.index)
    ren = {}
    for c in f.columns:
        cl = str(c).strip().lower()
        if cl in ("mkt-rf", "mkt_rf", "mkt rf"):
            ren[c] = "Mkt-RF"
        elif cl == "smb":
            ren[c] = "SMB"
        elif cl == "hml":
            ren[c] = "HML"
        elif cl in ("rf", "riskfree", "risk-free", "risk_free"):
            ren[c] = "RF"
    f = f.rename(columns=ren)
    missing = {"Mkt-RF", "SMB", "HML", "RF"} - set(f.columns)
    if missing:
        raise KeyError(f"Factor file is missing columns: {missing}. Found {list(f.columns)}")
    return f


def load_returns(year: int) -> pd.DataFrame:
    return pd.read_parquet(CLEAN / f"returns_new_{year}.parquet")


def load_window_returns(year: int, years_back: int = 5) -> pd.DataFrame:
    """5-year lookback used to estimate the network for target ``year``."""
    return pd.read_parquet(CLEAN / f"returns_new_{year - years_back + 1}_{year}.parquet")


def load_asset_meta() -> pd.DataFrame:
    p = CLEAN / "metadata - metadata_att.csv"
    if not p.exists():
        cand = sorted(CLEAN.glob("metadata*.csv"))
        if not cand:
            raise FileNotFoundError("Could not find an asset-metadata CSV in data/02_clean")
        p = cand[0]
    return pd.read_csv(p)


def load_graph(year: int, k: int = 5) -> nx.Graph:
    with open(GRAPHS / f"{year}_{k}" / "graph.gpickle", "rb") as fh:
        return pickle.load(fh)


def load_decile_returns(metric: str, decile: int, year: int) -> pd.Series:
    """Equal-weighted daily return of an *in-sample* decile portfolio (year t)."""
    tag = "hrm" if metric.lower() in ("hcm", "hrm") else metric.lower()
    p = PORT / f"decil_{decile}_{year}_{tag}.parquet"
    r = pd.read_parquet(p)
    return bh_portfolio_returns(list(r.columns), r).rename(f"{metric}_d{decile}_{year}")


def load_complete_metadata(metric: str) -> pd.DataFrame:
    # NOTE: the decile *returns* use the 'hrm' suffix, but the combined metadata
    # file is named complete_metadata_hcm.parquet.
    tag = "hcm" if metric.lower() in ("hcm", "hrm") else metric.lower()
    p = META / f"complete_metadata_{tag}.parquet"
    if not p.exists() and tag == "hcm":
        p = META / "complete_metadata_hrm.parquet"
    if not p.exists():
        raise FileNotFoundError(p)
    return pd.read_parquet(p)


# --------------------------------------------------------------------------
# Asset-class classification (mirrors code/analysis/*.py)
# --------------------------------------------------------------------------
def classify_asset_type(industry, sector) -> str:
    industry = str(industry).lower()
    sector = str(sector).lower()
    if "exchange traded fund" in industry or "etf" in industry:
        return "ETF"
    if "closed-end fund" in industry:
        return "Closed-End Fund"
    if "reit" in industry or "reit" in sector:
        return "REIT"
    if "mutual fund" in industry or "fund" in industry:
        return "Other Fund"
    return "Stock"


def stock_tickers(meta: pd.DataFrame | None = None) -> set:
    meta = load_asset_meta() if meta is None else meta
    cls = meta.apply(lambda r: classify_asset_type(r["Industry"], r["Sector"]), axis=1)
    return set(meta.loc[cls == "Stock", "Ticker"].astype(str))


def asset_class_map(meta: pd.DataFrame | None = None) -> dict:
    meta = load_asset_meta() if meta is None else meta
    return {
        str(t): classify_asset_type(i, s)
        for t, i, s in zip(meta["Ticker"], meta["Industry"], meta["Sector"])
    }


# --------------------------------------------------------------------------
# TMFG construction (verbatim port of code/graphs/functions.py:get_network_TMFG)
# --------------------------------------------------------------------------
def get_network_TMFG(corr_matrix) -> nx.Graph:
    if isinstance(corr_matrix, pd.DataFrame):
        labels = corr_matrix.index.to_list()
        C = corr_matrix.values
    else:
        labels = list(range(corr_matrix.shape[0]))
        C = np.asarray(corr_matrix).copy()

    C = np.abs(C)
    n = C.shape[0]

    if n < 4:
        G = nx.Graph()
        G.add_nodes_from(labels)
        for u in range(n):
            for v in range(u + 1, n):
                G.add_edge(labels[u], labels[v], weight=C[u, v])
        return G

    strength = C.sum(axis=1)
    seed = np.argsort(strength)[-4:]

    G = nx.Graph()
    G.add_nodes_from(labels)
    for i in range(4):
        for j in range(i + 1, 4):
            u, v = seed[i], seed[j]
            G.add_edge(labels[u], labels[v], weight=C[u, v])

    max_faces = 4 + 3 * (n - 4)
    gains = np.full((n, max_faces), -np.inf)
    faces = [
        (seed[0], seed[1], seed[2]),
        (seed[0], seed[1], seed[3]),
        (seed[0], seed[2], seed[3]),
        (seed[1], seed[2], seed[3]),
    ]
    is_remaining = np.ones(n, dtype=bool)
    is_remaining[seed] = False

    for f_idx, f in enumerate(faces):
        gains[is_remaining, f_idx] = C[is_remaining, f[0]] + C[is_remaining, f[1]] + C[is_remaining, f[2]]

    next_face_idx = 4
    max_gain = np.full(n, -np.inf)
    best_face_idx_for_node = np.full(n, -1, dtype=int)

    rem_nodes = np.where(is_remaining)[0]
    if len(rem_nodes) > 0:
        best_f = np.argmax(gains[rem_nodes, :next_face_idx], axis=1)
        max_gain[rem_nodes] = gains[rem_nodes, best_f]
        best_face_idx_for_node[rem_nodes] = best_f

    for _ in range(n - 4):
        best_node = int(np.argmax(max_gain))
        best_face_idx = int(best_face_idx_for_node[best_node])
        i, j, k = faces[best_face_idx]

        G.add_edge(labels[best_node], labels[i], weight=C[best_node, i])
        G.add_edge(labels[best_node], labels[j], weight=C[best_node, j])
        G.add_edge(labels[best_node], labels[k], weight=C[best_node, k])

        is_remaining[best_node] = False
        max_gain[best_node] = -np.inf
        gains[best_node, :] = -np.inf
        gains[:, best_face_idx] = -np.inf

        new_faces = [(best_node, i, j), (best_node, i, k), (best_node, j, k)]
        new_face_indices = [next_face_idx, next_face_idx + 1, next_face_idx + 2]

        rem_nodes = np.where(is_remaining)[0]
        if len(rem_nodes) == 0:
            break

        for f_idx, new_f in zip(new_face_indices, new_faces):
            faces.append(new_f)
            gains[rem_nodes, f_idx] = C[rem_nodes, new_f[0]] + C[rem_nodes, new_f[1]] + C[rem_nodes, new_f[2]]

        next_face_idx += 3

        case1_mask = best_face_idx_for_node[rem_nodes] == best_face_idx
        case1_nodes = rem_nodes[case1_mask]
        case2_nodes = rem_nodes[~case1_mask]

        if len(case1_nodes) > 0:
            best_f_case1 = np.argmax(gains[case1_nodes, :next_face_idx], axis=1)
            max_gain[case1_nodes] = gains[case1_nodes, best_f_case1]
            best_face_idx_for_node[case1_nodes] = best_f_case1

        if len(case2_nodes) > 0:
            new_gains = gains[case2_nodes[:, None], new_face_indices]
            new_gains_max = np.max(new_gains, axis=1)
            new_gains_argmax = np.argmax(new_gains, axis=1)
            better_mask = new_gains_max > max_gain[case2_nodes]
            better_nodes = case2_nodes[better_mask]
            if len(better_nodes) > 0:
                max_gain[better_nodes] = new_gains_max[better_mask]
                best_face_idx_for_node[better_nodes] = np.array(new_face_indices)[new_gains_argmax[better_mask]]

    return G


def compute_robust_corr_lw(returns_by_year: dict, target_year: int, years_back: int = 5,
                           tau: float = 2.5, window_days: int = 252, min_frac: float = 0.8) -> pd.DataFrame:
    """Ledoit-Wolf shrunk covariances over ``years_back`` annual windows, exponentially weighted.

    Requires scikit-learn (already a project dependency).  Used only by the
    faithful ``--mode rebuild`` path of R3.
    """
    from sklearn.covariance import LedoitWolf

    df = returns_by_year[target_year]
    t_idx = len(df) - 1
    covs = []
    for k in range(years_back):
        end = t_idx - k * window_days
        start = end - window_days
        if start < 0:
            continue
        w = df.iloc[start:end].dropna(axis=0)
        if len(w) >= window_days * min_frac:
            covs.append(LedoitWolf().fit(w.values).covariance_)
    if not covs:
        raise ValueError(f"No valid windows for {target_year}")
    covs = covs[::-1]  # chronological
    wts = np.exp(-np.arange(len(covs)) / tau)
    wts /= wts.sum()
    cov = np.sum([wt * c for wt, c in zip(wts, covs)], axis=0)
    std = np.sqrt(np.diag(cov))
    corr = cov / np.outer(std, std)
    return pd.DataFrame(corr, index=df.columns, columns=df.columns)


# --------------------------------------------------------------------------
# Centrality (HCM + Pozzi)
# --------------------------------------------------------------------------
def _zscore(d: dict) -> dict:
    v = np.array(list(d.values()), dtype=float)
    sd = v.std()
    if sd == 0:
        return {k: 0.0 for k in d}
    return {k: (val - v.mean()) / sd for k, val in d.items()}


def _eigenvector_centrality_power(G: nx.Graph, weight: str = "weight", tol: float = 1e-9, max_iter: int = 1000) -> dict:
    """Power iteration for eigenvector centrality (avoids a scipy dependency).

    On disconnected graphs (common when inducing a stocks-only subgraph) the
    dominant eigenvector is computed on the largest connected component and all
    other nodes receive 0, matching the fallback used for the Pozzi metric.
    """
    if G.number_of_nodes() > 0 and not nx.is_connected(G):
        lcc = G.subgraph(max(nx.connected_components(G), key=len)).copy()
    else:
        lcc = G
    full_nodes = list(G.nodes)
    G = lcc
    nodes = list(G.nodes)
    n = len(nodes)
    if n == 0:
        return {node: 0.0 for node in full_nodes}
    idx = {node: i for i, node in enumerate(nodes)}
    A = np.zeros((n, n), dtype=float)
    for u, v, d in G.edges(data=True):
        w = abs(float(d.get(weight, 1.0)))
        A[idx[u], idx[v]] = w
        A[idx[v], idx[u]] = w
    x = np.ones(n) / np.sqrt(n)
    for _ in range(max_iter):
        x_new = A @ x
        norm = np.linalg.norm(x_new)
        if norm == 0:
            break
        x_new /= norm
        if np.linalg.norm(x_new - x) < tol:
            x = x_new
            break
        x = x_new
    out = {node: 0.0 for node in full_nodes}
    out.update({node: float(x[idx[node]]) for node in nodes})
    return out


def hybrid_centrality(G: nx.Graph, use_pca: bool = True, custom_weights: dict | None = None):
    """Return (hibrido, weights, degree, closeness, eigenvector).

    ``hibrido`` is already negated (as in the pipeline) so that **small values =
    central** and decile 1 = core.
    """
    G = G.copy()
    for _, _, d in G.edges(data=True):
        d["distance"] = np.sqrt(2 * max(0.0, 1 - float(d.get("weight", 0.0))))

    degree = dict(G.degree(weight="weight"))
    closeness = nx.closeness_centrality(G, distance="distance")
    eig = _eigenvector_centrality_power(G, weight="weight")

    nd, nc, ne = _zscore(degree), _zscore(closeness), _zscore(eig)
    nodes = list(G.nodes)

    if use_pca and len(nodes) >= 3:
        F = np.array([[nd[x], nc[x], ne[x]] for x in nodes], dtype=float)
        # PC1 = first eigenvector of the 3x3 covariance matrix
        cov = np.cov(F, rowvar=False)
        evals, evecs = np.linalg.eigh(cov)
        load = np.abs(evecs[:, np.argmax(evals)])
        wts = load / load.sum() if load.sum() > 0 else np.array([1 / 3, 1 / 3, 1 / 3])
    else:
        wts = np.array([1 / 3, 1 / 3, 1 / 3]) if custom_weights is None else np.array(
            [custom_weights["degree"], custom_weights["closeness"], custom_weights["eigenvector"]]
        )

    score = {x: wts[0] * nd[x] + wts[1] * nc[x] + wts[2] * ne[x] for x in nodes}
    hybrid = {x: -score[x] for x in nodes}
    weights = {"degree": float(wts[0]), "closeness": float(wts[1]), "eigenvector": float(wts[2])}
    return hybrid, weights, degree, closeness, eig


def _eccentricity(G: nx.Graph):
    if nx.is_connected(G):
        raw = nx.eccentricity(G)
    else:
        lcc = G.subgraph(max(nx.connected_components(G), key=len))
        raw = nx.eccentricity(lcc)
        raw = {n: raw.get(n, np.nan) for n in G.nodes()}
    vals = np.array([v for v in raw.values() if not np.isnan(v)])
    lo, hi = vals.min(), vals.max()
    if hi == lo:
        return {n: 0.0 for n in G.nodes()}
    return {n: (raw[n] - lo) / (hi - lo) if not np.isnan(raw.get(n, np.nan)) else np.nan for n in G.nodes()}


def pozzi_centrality(G: nx.Graph, weight_attr: str = "weight") -> dict:
    """Pozzi et al. (2013) composite X+Y (higher = more peripheral? see note).

    The published pipeline combines X and Y into a single score and orients it
    like HCM (small = central).  We return ``X + Y`` so callers can decide.
    """
    N = G.number_of_nodes()
    G_corr = nx.Graph(); G_dist = nx.Graph()
    G_corr.add_nodes_from(G.nodes()); G_dist.add_nodes_from(G.nodes())
    for u, v, data in G.edges(data=True):
        r = float(data.get(weight_attr, 0.0))
        G_corr.add_edge(u, v, weight=1.0 + r)
        G_dist.add_edge(u, v, weight=np.sqrt(2.0 * (1.0 - r)))

    Du = nx.degree_centrality(G)
    BCu = nx.betweenness_centrality(G, normalized=True)
    Cu = nx.closeness_centrality(G)
    ECu = _eigenvector_centrality_power(G, weight="weight")
    Dw = nx.degree_centrality(G_corr)
    BCw = nx.betweenness_centrality(G_dist, weight="weight", normalized=True)
    Cw = nx.closeness_centrality(G_dist, distance="weight")
    ECw = _eigenvector_centrality_power(G_corr, weight="weight")
    Eu, Ew = _eccentricity(G), _eccentricity(G_dist)

    cols = {"Du": Du, "Dw": Dw, "BCu": BCu, "BCw": BCw, "Eu": Eu, "Ew": Ew,
            "Cu": Cu, "Cw": Cw, "ECu": ECu, "ECw": ECw}
    df = pd.DataFrame(cols)
    df = (df - df.mean()) / df.std()
    X = (df["Du"] + df["Dw"] + df["BCu"] + df["BCw"]) / 4
    Y = (df["Eu"] + df["Ew"] + df["Cu"] + df["Cw"] + df["ECu"] + df["ECw"]) / 6
    return (X + Y).to_dict()


# --------------------------------------------------------------------------
# Deciles and portfolios
# --------------------------------------------------------------------------
def recut_deciles(df: pd.DataFrame, metric_col: str, n: int = 10,
                  year_col: str = "year") -> pd.DataFrame:
    """Assign quantile deciles per year (1 = lowest metric value = central)."""
    out = df.copy()
    out["decile"] = (
        out.groupby(year_col)[metric_col]
        .transform(lambda s: pd.qcut(s.rank(method="first"), n, labels=False) + 1)
    )
    return out


OUTLIER_TICKERS = {"HYFT"}  # dropped by code/graphs/regressions.ipynb


def bh_portfolio_returns(tickers, returns: pd.DataFrame) -> pd.Series:
    """Buy-and-hold 1/N portfolio (matches code/graphs/regressions.ipynb)."""
    cols = [t for t in tickers if t in returns.columns and t not in OUTLIER_TICKERS]
    if not cols:
        return pd.Series(dtype=float)
    filled = returns[cols].fillna(0.0)
    port_cum = (1 + filled).cumprod().mean(axis=1)
    ret = port_cum.pct_change()
    if len(ret):
        ret.iloc[0] = port_cum.iloc[0] - 1.0
    return ret


def ew_portfolio_returns(tickers, returns: pd.DataFrame) -> pd.Series:
    """Daily-rebalanced equal-weight portfolio (kept for reference)."""
    cols = [t for t in tickers if t in returns.columns and t not in OUTLIER_TICKERS]
    if not cols:
        return pd.Series(dtype=float)
    return returns[cols].mean(axis=1)


def oos_bh_returns(metric: str, deciles, year: int) -> pd.Series:
    """Out-of-sample buy-and-hold return of one or several deciles.

    Membership is taken from year ``t`` metadata; returns are from year ``t+1``.
    This mirrors the construction behind the published performance / FF3 tables.
    """
    if isinstance(deciles, int):
        deciles = [deciles]
    meta = load_complete_metadata(metric)
    yr = meta["year"].astype(str)
    labels = {f"decil_{d}" for d in deciles}
    members = meta[(yr == str(year)) & (meta["portfolio"].isin(labels))]["Ticker"].tolist()
    try:
        rets = load_returns(year + 1)
    except FileNotFoundError:
        return pd.Series(dtype=float)
    return bh_portfolio_returns(members, rets)


# --------------------------------------------------------------------------
# Fama-French 3-factor regressions with Newey-West HAC
# --------------------------------------------------------------------------
def nw_ols(y: np.ndarray, X: np.ndarray, L: int = 5, add_const: bool = True):
    y = np.asarray(y, dtype=float).ravel()
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    if add_const:
        X = np.column_stack([np.ones(len(X)), X])
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    e = y - X @ beta
    u = X * e[:, None]
    S = u.T @ u
    for l in range(1, L + 1):
        w = 1.0 - l / (L + 1.0)
        G = u[l:].T @ u[:-l]
        S += w * (G + G.T)
    cov = XtX_inv @ S @ XtX_inv
    se = np.sqrt(np.clip(np.diag(cov), 0, None))
    ss_res = float(e @ e)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return beta, se, r2


def ff3_year(port_ret: pd.Series, factors: pd.DataFrame, L: int = 5) -> dict | None:
    df = pd.concat([port_ret.rename("r"), factors], axis=1, join="inner").dropna()
    if len(df) < 30:
        return None
    y = (df["r"] - df["RF"]).values
    X = df[["Mkt-RF", "SMB", "HML"]].values
    beta, se, r2 = nw_ols(y, X, L=L)
    # The published pipeline annualizes the intercept as const * 252; mirror it.
    return {
        "alpha_daily": beta[0],
        "alpha": beta[0] * 252,          # annualized, comparable to table_famamacbeth_*.csv
        "alpha_t": beta[0] / se[0] if se[0] > 0 else np.nan,
        "mkt_beta": beta[1], "smb_beta": beta[2], "hml_beta": beta[3],
        "r_squared": r2, "n_obs": len(df),
    }


def aggregate_fm(records: list[dict]) -> dict:
    """Fama-MacBeth-style aggregation of yearly FF3 estimates (mean alpha / SE)."""
    records = [r for r in records if r is not None]
    if not records:
        return {}
    a = np.array([r["alpha"] for r in records], dtype=float)          # annualized
    ad = np.array([r.get("alpha_daily", r["alpha"] / 252) for r in records], dtype=float)
    n = len(a)
    return {
        "alpha": a.mean(),
        "alpha_daily": ad.mean(),
        "alpha_t": a.mean() / (a.std(ddof=1) / np.sqrt(n)) if n > 1 and a.std(ddof=1) > 0 else np.nan,
        "mkt_beta": np.mean([r["mkt_beta"] for r in records]),
        "smb_beta": np.mean([r["smb_beta"] for r in records]),
        "hml_beta": np.mean([r["hml_beta"] for r in records]),
        "r_squared": np.mean([r["r_squared"] for r in records]),
        "n_years": n,
    }


# --------------------------------------------------------------------------
# Performance metrics
# --------------------------------------------------------------------------
def perf_metrics(daily: pd.Series, periods: int = 252) -> dict:
    d = daily.dropna()
    n = len(d)
    if n == 0:
        return {}
    total = float((1 + d).prod())
    cagr = total ** (periods / n) - 1
    vol = float(d.std() * np.sqrt(periods))
    sharpe = float(d.mean() * periods / vol) if vol > 0 else np.nan
    neg = d[d < 0]
    dvol = float(neg.std() * np.sqrt(periods)) if len(neg) > 1 else np.nan
    sortino = float(d.mean() * periods / dvol) if dvol and dvol > 0 else np.nan
    cum = (1 + d).cumprod()
    dd = cum / cum.cummax() - 1
    q = d.quantile(0.01)
    return {
        "total_return": total - 1, "cagr": cagr, "ann_vol": vol,
        "sharpe": sharpe, "sortino": sortino, "max_drawdown": float(dd.min()),
        "var99": float(q), "cvar99": float(d[d <= q].mean()),
        "n_obs": n,
    }


def two_sided_p(t: float) -> float:
    if not np.isfinite(t):
        return np.nan
    return 2 * (1 - NormalDist().cdf(abs(t)))


# --------------------------------------------------------------------------
# Multiple-testing helpers (R8)
# --------------------------------------------------------------------------
def holm_bonferroni(pvals: dict) -> dict:
    items = sorted(((k, v) for k, v in pvals.items() if np.isfinite(v)), key=lambda kv: kv[1])
    m = len(items)
    out, prev = {}, 0.0
    for rank, (k, p) in enumerate(items):
        adj = min(1.0, p * (m - rank))
        adj = max(adj, prev)
        prev = adj
        out[k] = adj
    for k in pvals:
        out.setdefault(k, np.nan)
    return out


def block_bootstrap_fwer(ret_matrix: pd.DataFrame, B: int = 2000, block: int = 20,
                         seed: int = 0, studentize: bool = True) -> dict:
    """White's Reality Check / max-statistic bootstrap across strategies.

    ``ret_matrix`` columns are strategies (e.g. the ten deciles), rows are daily
    returns.  Tests H0: max_k E[r_k] <= 0 against H1: some E[r_k] > 0.
    Returns observed max statistic and the bootstrap p-value.
    """
    R = ret_matrix.dropna(how="all").values
    T, K = R.shape
    mean = np.nanmean(R, axis=0)
    se = np.nanstd(R, axis=0, ddof=1) / np.sqrt(T)
    stat_obs = np.nanmax(mean / se) if studentize else np.nanmax(mean)

    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(T / block))
    boot = np.empty(B)
    for b in range(B):
        starts = rng.integers(0, T - block, size=n_blocks)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:T]
        Rb = R[idx]
        Rb = Rb - mean  # recenter under H0
        mb = np.nanmean(Rb, axis=0)
        sb = np.nanstd(Rb, axis=0, ddof=1) / np.sqrt(T)
        boot[b] = np.nanmax(mb / sb) if studentize else np.nanmax(mb)
    p = float((1 + (boot >= stat_obs).sum()) / (B + 1))
    return {"stat": float(stat_obs), "p_value": p, "B": B, "block": block}


# --------------------------------------------------------------------------
# Cost models (S1)
# --------------------------------------------------------------------------
def flat_cost_bps(**_):
    return 10.0


def tiered_cost_bps(asset_class: str = "Stock", decile: int | None = None, **_):
    """Liquidity-scaled cost grid for the extremes (round-trip, bps)."""
    if asset_class in ("ETF", "Closed-End Fund"):
        return 10.0
    if decile is not None and decile >= 10:
        return 75.0
    if decile is not None and decile <= 1:
        return 25.0
    return 40.0


def apply_annual_cost(daily: pd.Series, turnover_by_year: dict, cost_fn,
                      year_of=None) -> pd.Series:
    """Subtract ``turnover * cost_bps / 1e4`` on the first trading day of each year."""
    net = daily.copy()
    dates = net.index
    for year, turn in turnover_by_year.items():
        mask = dates.year == year
        if mask.sum() == 0:
            continue
        bps = cost_fn()
        first = dates[mask][0]
        net.loc[first] -= turn * (bps / 1e4)
    return net


def capacity_curve(alpha_annual: float, ann_turnover: float, adv_proxy: float,
                   impact_coef: float = 0.1, costs_fixed_bps: float = 10.0,
                   aum_grid=None) -> pd.DataFrame:
    """Heuristic capacity curve.

    Market impact follows the common square-root law:
        impact_bps = impact_coef * sqrt(participation) * 1e4
    where participation = (AUM / ADV_proxy).  ``adv_proxy`` is the portfolio's
    average daily dollar volume proxy in the same currency units as AUM.
    Returns net alpha by AUM.
    """
    if aum_grid is None:
        aum_grid = np.array([1e6, 5e6, 1e7, 5e7, 1e8, 5e8, 1e9, 5e9, 1e10])
    rows = []
    for aum in aum_grid:
        participation = aum / adv_proxy if adv_proxy > 0 else np.nan
        impact_bps = impact_coef * np.sqrt(max(participation, 0.0)) * 1e4
        cost_annual = ann_turnover * (impact_bps + costs_fixed_bps) / 1e4
        rows.append({
            "AUM": aum, "participation": participation,
            "impact_bps_per_trade": impact_bps,
            "annual_cost": cost_annual, "net_alpha": alpha_annual - cost_annual,
        })
    return pd.DataFrame(rows)
