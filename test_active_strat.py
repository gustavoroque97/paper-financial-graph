import pandas as pd
import numpy as np

# Create mock data
dates = pd.date_range("2016-01-01", periods=5, freq='B')
df_ret_full = pd.DataFrame({
    'A': [0, 0, 0.1, 0.05, -0.05], # Starts trading on day 3
    'B': [0.01, -0.01, 0.02, 0.01, 0],
    'C': [0.05, 0.05, 0, 0, 0], # Stops trading (but we just see 0s)
    'D': [-0.01, 0.02, -0.02, 0.01, 0.01]
}, index=dates)

is_active = df_ret_full.notna() & (df_ret_full != 0).cummax()

valid_p = ['A', 'B']
valid_c = ['C', 'D']

df_ret_oos = df_ret_full
is_active_oos = is_active

# Returns
ret_p_active = df_ret_oos[valid_p].where(is_active_oos[valid_p])
ret_c_active = df_ret_oos[valid_c].where(is_active_oos[valid_c])

ret_p = np.log1p(ret_p_active).mean(axis=1)
ret_c = np.log1p(ret_c_active).mean(axis=1)

print("ret_p:")
print(ret_p)

# Strategy Weights
signal = pd.Series([1, 1, -1, 0, 1], index=dates)

W_p_active = is_active_oos[valid_p].astype(float)
W_c_active = is_active_oos[valid_c].astype(float)

W_p_internal = W_p_active.div(W_p_active.sum(axis=1), axis=0).fillna(0)
W_c_internal = W_c_active.div(W_c_active.sum(axis=1), axis=0).fillna(0)

W_p_target = W_p_internal.multiply(signal, axis=0)
W_c_target = W_c_internal.multiply(-signal, axis=0)
W_target = W_p_target.add(W_c_target, fill_value=0)

print("\nW_target:")
print(W_target)

R_oos = df_ret_oos[W_target.columns].fillna(0)
W_drift = W_target.shift(1).fillna(0) * (1 + R_oos.shift(1).fillna(0))

turnover_strat = (W_target - W_drift).abs().sum(axis=1).fillna(0)

print("\nTurnover:")
print(turnover_strat)

