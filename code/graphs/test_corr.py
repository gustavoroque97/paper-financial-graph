import pandas as pd
import numpy as np

# Create dummy data where Large strictly leads Small
Large = pd.Series([1, 2, 3, 4, 5, 1, 2, 3, 4, 5])
Small = pd.Series([0, 1, 2, 3, 4, 5, 1, 2, 3, 4]) # Small is Large shifted by 1 (Large leads Small)

X = pd.concat([Large, Small], axis=1)
X.columns = ["Large", "Small"]

# Assume autocorrelation_matrix uses corr() with shift
def autocorrelation_matrix(df, lag=1):
    # What does the user's function do? 
    # Usually it's df.corr() between df and df.shift(lag)
    # Let's see pandas corrwith
    return df.corrwith(df.shift(lag))

print(X.corr())
