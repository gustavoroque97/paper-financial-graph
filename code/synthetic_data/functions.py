import pandas as pd
import numpy as np
import networkx as nx
from sklearn.covariance import LedoitWolf
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm import tqdm
import os

def corr_matrix(mode, min_obs=50, min_assets_frac=0.7):
    """
    Compute absolute correlation matrix using a dense
    subpanel of the mode.
    
    Returns both correlation matrix and asset names.
    """
    n_assets = mode.shape[1]

    # Keep dates with enough assets
    valid_rows = mode.notna().sum(axis=1) >= int(min_assets_frac * n_assets)
    X = mode.loc[valid_rows]

    # Keep assets with enough observations
    valid_cols = X.notna().sum(axis=0) >= min_obs
    X = X.loc[:, valid_cols]

    # Drop remaining NaNs (small)
    X = X.dropna(axis=0, how="any")

    if X.shape[0] < min_obs or X.shape[1] < 5:
        raise ValueError("Panel too sparse to compute correlation.")

    lw = LedoitWolf().fit(X.values)
    cov = lw.covariance_

    std = np.sqrt(np.diag(cov))
    corr = cov / np.outer(std, std)

    # Retorna matriz de correlação e nomes dos ativos
    return pd.DataFrame(corr, index=X.columns, columns=X.columns)

def get_network_TMFG(corr_matrix):
    """
    O(N^2) TMFG implementation.
    Accepts pandas DataFrame or NumPy array.
    """

    # -----------------------------
    # Handle DataFrame input
    # -----------------------------
    if isinstance(corr_matrix, pd.DataFrame):
        labels = corr_matrix.index.to_list()
        C = corr_matrix.values
    else:
        labels = list(range(corr_matrix.shape[0]))
        C = corr_matrix.copy()

    C = np.abs(C)
    n = C.shape[0]

    # -----------------------------
    # Node strength (O(N^2))
    # -----------------------------
    strength = C.sum(axis=1)

    # Initial 4-clique: top-4 strengths
    seed = np.argsort(strength)[-4:]

    G = nx.Graph()
    G.add_nodes_from(labels)

    # Add edges of the initial clique
    for i in seed:
        for j in seed:
            if i < j:
                G.add_edge(labels[i], labels[j], weight=C[i, j])

    active = set(seed)
    remaining = set(range(n)) - active

    # Initial triangular faces
    faces = [
        tuple(face) for face in [
            (seed[0], seed[1], seed[2]),
            (seed[0], seed[1], seed[3]),
            (seed[0], seed[2], seed[3]),
            (seed[1], seed[2], seed[3])
        ]
    ]

    # -----------------------------
    # TMFG growth (O(N^2))
    # -----------------------------
    while remaining:
        best_gain = -np.inf
        best_node = None
        best_face = None

        # Winner-take-all
        for u in remaining:
            # Vectorized gain computation
            gains = [
                C[u, f[0]] + C[u, f[1]] + C[u, f[2]]
                for f in faces
            ]
            max_gain = max(gains)
            if max_gain > best_gain:
                best_gain = max_gain
                best_node = u
                best_face = faces[np.argmax(gains)]

        i, j, k = best_face

        # Add edges
        G.add_edge(labels[best_node], labels[i], weight=C[best_node, i])
        G.add_edge(labels[best_node], labels[j], weight=C[best_node, j])
        G.add_edge(labels[best_node], labels[k], weight=C[best_node, k])

        # Update sets
        active.add(best_node)
        remaining.remove(best_node)

        # Update faces
        faces.remove(best_face)
        faces.extend([
            (best_node, i, j),
            (best_node, i, k),
            (best_node, j, k)
        ])

    return G

def build_and_save_graph(year, speed, corr_dict):
    """
    Constroi grafo TMFG e salva em .pkl
    """
    corr_matrix = corr_dict[f"corr_{speed}_{year}"]
    G = get_network_TMFG(corr_matrix)  # não mostra barra aqui

    # Cria pasta se não existir
    base_path = f"../../data/04_graphs/{year}"
    os.makedirs(base_path, exist_ok=True)

    # Salva grafo
    file_path = os.path.join(base_path, f"{speed}_graph.pkl")
    nx.write_gpickle(G, file_path)

    return f"graph_{speed}_{year}", G