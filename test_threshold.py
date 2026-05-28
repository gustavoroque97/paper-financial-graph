import pandas as pd
import numpy as np

# Mock data to simulate spread
np.random.seed(42)
spread = pd.Series(np.random.normal(0, 0.005, 252)) # std dev of 0.5% daily

def generate_lazy_signal(spread_series, threshold):
    signal = np.zeros(len(spread_series))
    current_pos = 0 
    for i in range(len(spread_series)):
        s = spread_series.iloc[i]
        if s > threshold:
            current_pos = 1
        elif s < -threshold:
            current_pos = -1
        signal[i] = current_pos
    return pd.Series(signal, index=spread_series.index)

# User's threshold
sig_user = generate_lazy_signal(spread, 0.02)
print("User threshold (0.02) non-zero days:", (sig_user != 0).sum())

# Correct threshold
sig_correct = generate_lazy_signal(spread, 0.002)
print("Correct threshold (0.002) non-zero days:", (sig_correct != 0).sum())
