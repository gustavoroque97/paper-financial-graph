import pandas as pd
import numpy as np
import yfinance as yf
import statsmodels.api as sm
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")

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
    """Total return over the year."""
    prices = prices.dropna()
    if len(prices) < 2:
        return np.nan
    return (prices.iloc[-1] / prices.iloc[0]) - 1

records = []

for year in sorted(years):
    print(f"\n=== {year} ===")
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

# Join with df_metrics
df_metrics = df_metrics.merge(beta_momentum_df, on=["node", "year"], how="left")

# Save updated metrics
df_metrics.to_parquet("../../data/02_clean/df_metrics.parquet", index=False)
print("Finished!")
