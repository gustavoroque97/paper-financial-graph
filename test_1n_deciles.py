import pandas as pd
import numpy as np

# Create mock data
dates = pd.date_range("2016-01-01", periods=5, freq='B')
df_ret_full = pd.DataFrame({
    'A': [0, 0, 0.1, 0.05, -0.05],
    'B': [0.01, -0.01, 0.02, 0.01, 0],
}, index=dates)

is_active = df_ret_full.notna() & (df_ret_full != 0).cummax()
df_ret_oos = df_ret_full
is_active_oos = is_active
valid_d = ['A', 'B']

c = 0.001

ret_d_active = df_ret_oos[valid_d].where(is_active_oos[valid_d])
ret_d_gross = np.log1p(ret_d_active).mean(axis=1).fillna(0)

W_d_active_mask = is_active_oos[valid_d].astype(float)
W_d_target = W_d_active_mask.div(W_d_active_mask.sum(axis=1), axis=0).fillna(0)

R_oos_d = df_ret_oos[valid_d].fillna(0)
W_d_drift = W_d_target.shift(1).fillna(0) * (1 + R_oos_d.shift(1).fillna(0))
W_d_drift = W_d_drift.div(W_d_drift.sum(axis=1).replace(0, 1), axis=0)

turnover_d = (W_d_target - W_d_drift).abs().sum(axis=1).fillna(0)
ret_d_net = ret_d_gross - (c * turnover_d)

print("ret_d_gross:\n", ret_d_gross)
print("turnover_d:\n", turnover_d)
print("ret_d_net:\n", ret_d_net)
