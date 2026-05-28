import pandas as pd
import numpy as np

df_ret_full = pd.read_parquet("data/01_raw/returns.parquet")
df_ret_full = df_ret_full[df_ret_full.index >= pd.Timestamp(2015, 1, 1)]

c = 0.001
year = 2015
test_year = 2016
metric = "hrm"
c_idx, p_idx = 1, 10

df_ret_oos = df_ret_full[df_ret_full.index.year == test_year]

c_label = f"decil_{c_idx}_{year}_{metric}"
p_label = f"decil_{p_idx}_{year}_{metric}"

cols_c = pd.read_parquet(f"data/06_portfolios/{c_label}.parquet").columns
cols_p = pd.read_parquet(f"data/06_portfolios/{p_label}.parquet").columns

valid_c = cols_c.intersection(df_ret_oos.columns)
valid_p = cols_p.intersection(df_ret_oos.columns)

ret_c = np.log1p(df_ret_oos[valid_c]).mean(axis=1)
ret_p = np.log1p(df_ret_oos[valid_p]).mean(axis=1)

signal = np.sign((ret_c - ret_p).shift(1)).fillna(0)
strat_ret_gross = signal * (ret_p - ret_c)

W_p_target = pd.DataFrame(1/len(valid_p), index=df_ret_oos.index, columns=valid_p).multiply(signal, axis=0)
W_c_target = pd.DataFrame(1/len(valid_c), index=df_ret_oos.index, columns=valid_c).multiply(-signal, axis=0)
W_target = W_p_target.add(W_c_target, fill_value=0)

R_oos = df_ret_oos[W_target.columns].fillna(0)
W_drift = W_target.shift(1) * (1 + R_oos.shift(1))

turnover_strat = (W_target - W_drift).abs().sum(axis=1).fillna(0)
strat_ret_net = strat_ret_gross - (c * turnover_strat)

print("Gross Return 2016:", strat_ret_gross.sum())
print("Net Return 2016:", strat_ret_net.sum())
print("Avg Daily Turnover:", turnover_strat.mean())

