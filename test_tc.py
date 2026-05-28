import pandas as pd
import numpy as np

df_ret_full = pd.read_parquet("data/01_raw/returns.parquet")
df_ret_full = df_ret_full[df_ret_full.index >= pd.Timestamp(2015, 1, 1)]

c = 0.001

is_active = df_ret_full.notna() & (df_ret_full != 0).cummax()
W_mkt = is_active.astype(float).div(is_active.sum(axis=1), axis=0)
R_mkt_all = df_ret_full.fillna(0)
W_mkt_drift = W_mkt.shift(1) * (1 + R_mkt_all.shift(1))
W_mkt_drift = W_mkt_drift.div(W_mkt_drift.sum(axis=1), axis=0)
turnover_mkt = (W_mkt - W_mkt_drift).abs().sum(axis=1).fillna(0)

# The first row of turnover will be 0 since W_mkt.shift(1) is NaN, so fillna(0) handles it.
# Actually, the first row should have turnover = 1 (buying the portfolio).
# But since we just want to track ongoing turnover, we can leave it as 0 or 1.
market_benchmark_global_gross = np.log1p(df_ret_full.where(is_active)).mean(axis=1)
market_benchmark_global_net = market_benchmark_global_gross - (c * turnover_mkt)

print("Market Gross Return:", market_benchmark_global_gross.sum())
print("Market Net Return:", market_benchmark_global_net.sum())
print("Avg Daily Mkt Turnover:", turnover_mkt.mean())
