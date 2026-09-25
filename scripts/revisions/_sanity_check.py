"""Print the schema of every input the revision scripts rely on.

Run this first; if a required artefact is missing or renamed, the scripts will
fail loudly and you can adjust `common.py` before running the analyses.

    python scripts/revisions/_sanity_check.py
"""

from __future__ import annotations

import pandas as pd
from common import (CLEAN, GRAPHS, PORT, META, load_graph, load_factors,
                    load_returns, load_asset_meta, load_complete_metadata)


def show(name, obj):
    print("=" * 70)
    print(name)
    if isinstance(obj, pd.DataFrame):
        print("shape:", obj.shape)
        print("columns:", list(obj.columns)[:40])
        print(obj.head(3).to_string())
    else:
        print(obj)


def main():
    show("Fama-French factors", load_factors())
    show("returns_new_2015", load_returns(2015))
    show("asset metadata (Ticker/Sector/Industry)",
         load_asset_meta()[["Ticker", "Company", "Sector", "Industry"]].head(5))
    show("complete_metadata_hcm", load_complete_metadata("hcm").head(3))
    try:
        g = load_graph(2015)
        print("=" * 70)
        print("graph 2015: nodes =", g.number_of_nodes(), " edges =", g.number_of_edges())
        sample = list(g.edges(data=True))[:2]
        print("sample edges:", sample)
    except Exception as e:
        print("graph load failed:", e)

    print("=" * 70)
    for p in [PORT, META]:
        print(f"\n{p}:")
        for f in sorted(p.glob("*.parquet"))[:8]:
            print("  ", f.name)
    print("\nIf any of the above is empty, run r3_stocks_only.py --mode refilter first.")


if __name__ == "__main__":
    main()
