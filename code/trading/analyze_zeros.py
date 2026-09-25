import pandas as pd
import numpy as np

# Load returns
df_ret = pd.read_parquet("../../data/01_raw/returns.parquet")
df_ret = df_ret[df_ret.index >= pd.Timestamp("2014-01-01")] # include 2014 to check past year

# Calculate proportion of zeros per year
results = []
for year in range(2014, 2025):
    df_year = df_ret[df_ret.index.year == year]
    if df_year.empty: continue
    
    # Calculate % of exactly zero returns (or missing)
    zeros = (df_year == 0.0).sum()
    nans = df_year.isna().sum()
    total_days = len(df_year)
    
    # We only care about active stocks. Let's say a stock is active if it has at least 100 non-NaN days
    active = df_year.columns[nans < (total_days - 100)]
    
    if len(active) == 0: continue
    
    zero_prop = zeros[active] / total_days
    
    results.append({
        'year': year,
        'active_stocks': len(active),
        '>10% zeros': (zero_prop > 0.10).sum(),
        '>20% zeros': (zero_prop > 0.20).sum(),
        '>30% zeros': (zero_prop > 0.30).sum(),
        '>50% zeros': (zero_prop > 0.50).sum()
    })

res_df = pd.DataFrame(results)
print(res_df.to_string(index=False))

