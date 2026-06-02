import json

with open('financial_metrics.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_cell_1_source = """import pandas as pd
import numpy as np
import yfinance as yf
import statsmodels.api as sm
from tqdm import tqdm

df_metrics = pd.read_parquet("../../data/02_clean/df_metrics.parquet")
tickers = df_metrics['node'].unique().tolist()
years = df_metrics['year'].unique().tolist()

def beta_ols(rp, rm):
    rm = rm.squeeze().rename("rm")
    joined = rp.to_frame("rp").join(rm, how="inner").dropna()
    if len(joined) < 20:  # not enough observations
        return np.nan
    y = joined["rp"]
    X = sm.add_constant(joined["rm"])
    model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    return model.params["rm"]

def momentum_12m(prices):
    \"\"\"Total return over the year.\"\"\"
    prices = prices.dropna()
    if len(prices) < 2:
        return np.nan
    return (prices.iloc[-1] / prices.iloc[0]) - 1

records = []

for year in sorted(years):
    print(f"\\n=== {year} ===")
    start, end = f"{year}-01-01", f"{year}-12-31"

    # Market returns
    sp500_prices = yf.download("^GSPC", start=start, end=end, progress=False)["Close"]
    sp500_dr = sp500_prices.pct_change().dropna()
    sp500_dr.name = "rm"

    # Tickers to process this year
    tickers_year = df_metrics[df_metrics['year'] == year]['node'].tolist()
    
    # Download all tickers at once
    raw = yf.download(tickers_year, start=start, end=end, progress=False)["Close"]
    if isinstance(raw, pd.Series):
        raw = raw.to_frame(name=tickers_year[0])

    for ticker in tqdm(tickers_year, desc=f"Computing {year}"):
        if ticker not in raw.columns:
            records.append({"node": ticker, "year": year, "beta": np.nan, "momentum": np.nan})
            continue
            
        prices = raw[ticker].dropna()
        returns = prices.pct_change().dropna()

        b = beta_ols(returns, sp500_dr)
        m = momentum_12m(prices)

        records.append({
            "node": ticker,
            "year": year,
            "beta": b,
            "momentum": m
        })

beta_momentum_df = pd.DataFrame(records)
print(beta_momentum_df.describe())
"""

new_cell_2_source = """# Join with df_metrics
df_metrics = df_metrics.merge(beta_momentum_df, on=["node", "year"], how="left")

# Save updated metrics
df_metrics.to_parquet("../../data/02_clean/df_metrics.parquet", index=False)
df_metrics.head()
"""

# Find the cell that contains "def beta_ols(rp, rm):" in the middle of the notebook
found = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "def beta_ols(rp, rm):" in source and "records.append({" in source:
            # Replace its source
            nb['cells'][i]['source'] = [line + '\n' for line in new_cell_1_source.split('\n')]
            # Remove trailing newline from the last item
            nb['cells'][i]['source'][-1] = nb['cells'][i]['source'][-1].strip('\n')
            nb['cells'][i]['outputs'] = []
            nb['cells'][i]['execution_count'] = None
            found = True
            insert_idx = i + 1
            break

if found:
    # Delete the next few cells that were previously used to save/merge wide format
    # The next cell is 'from functools import reduce'
    # The cell after is 'combined_df'
    # Let's just remove them based on their content
    cells_to_keep = []
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            if "from functools import reduce" in source or "combined_df" in source:
                continue
        cells_to_keep.append(cell)
    nb['cells'] = cells_to_keep

    # Find where to insert our new_cell_2 (right after new_cell_1)
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            if "df_metrics = pd.read_parquet" in source and "beta_momentum_df = pd.DataFrame" in source:
                new_cell = {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [line + '\n' for line in new_cell_2_source.split('\n')]
                }
                new_cell["source"][-1] = new_cell["source"][-1].strip('\n')
                nb['cells'].insert(i+1, new_cell)
                break

    with open('financial_metrics.ipynb', 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("Notebook updated successfully.")
else:
    print("Cell not found.")
