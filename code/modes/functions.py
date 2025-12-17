import pandas as pd
import numpy as np
from PyEMD import EMD
from vmdpy import VMD
from tqdm import tqdm
from scipy.signal import welch

def get_valid_segment(s):
    valid = s.dropna()
    if len(valid) < 10:  # mínimo pra EMD/VMD fazer sentido
        return None, None, None
    
    start, end = valid.index[0], valid.index[-1]
    return start, end, s.loc[start:end]

def emd_modes(data):
    fast, medium, slow = {}, {}, {}
    emd = EMD()

    for col in tqdm(data.columns):
        s = data[col]

        start, end, seg = get_valid_segment(s)
        if seg is None:
            continue

        x = seg.interpolate(limit_area="inside").values
        t = np.arange(len(x))

        try:
            imfs = emd.emd(x, t)
        except Exception:
            continue

        N = len(imfs)
        if N < 3:
            continue  # not enough structure

        # ---- adaptive split ----
        k = N // 3

        if k == 0:
            fast_imfs = imfs[:1]
            medium_imfs = imfs[1:2] if N > 1 else []
            slow_imfs = imfs[2:]
        else:
            fast_imfs = imfs[:k]
            medium_imfs = imfs[k:2*k]
            slow_imfs = imfs[2*k:]

        # ---- aggregate ----
        f = np.sum(fast_imfs, axis=0) if len(fast_imfs) else np.zeros(len(x))
        m = np.sum(medium_imfs, axis=0) if len(medium_imfs) else np.zeros(len(x))
        sl = np.sum(slow_imfs, axis=0) if len(slow_imfs) else np.zeros(len(x))

        # ---- full-length series ----
        f_full = pd.Series(np.nan, index=data.index)
        m_full = pd.Series(np.nan, index=data.index)
        sl_full = pd.Series(np.nan, index=data.index)

        f_full.loc[start:end] = f
        m_full.loc[start:end] = m
        sl_full.loc[start:end] = sl

        fast[col] = f_full
        medium[col] = m_full
        slow[col] = sl_full

    return (
        pd.DataFrame(fast),
        pd.DataFrame(medium),
        pd.DataFrame(slow),
    )

def vmd_modes(data, alpha=2000, tau=0, K=3, DC=0, init=1, tol=1e-7):

    # one dict per mode
    modes = [dict() for _ in range(K)]

    for col in tqdm(data.columns):
        s = data[col]

        start, end, seg = get_valid_segment(s)
        if seg is None:
            continue

        # interpolate only inside valid region
        x = seg.interpolate(limit_area="inside").values

        try:
            u, _, _ = VMD(
                x,
                alpha=alpha,
                tau=tau,
                K=K,
                DC=DC,
                init=init,
                tol=tol
            )
        except Exception:
            continue

        # u.shape = (K, T)
        T = u.shape[1]
        idx = seg.index[:T]

        for k in range(K):
            full = pd.Series(np.nan, index=data.index)
            full.loc[idx] = u[k]
            modes[k][col] = full

    # convert dicts → DataFrames
    modes = [pd.DataFrame(m) for m in modes]

    return modes

def dominant_period(x, fs=1):
    x = x[~np.isnan(x)]
    if len(x) < 32:
        return np.nan

    f, Pxx = welch(x.to_numpy(), fs=fs, nperseg=min(256, len(x)))
    f, Pxx = f[1:], Pxx[1:]  # drop zero freq
    return 1 / f[np.argmax(Pxx)]

def mean_zero_crossing_distance(x):
    x = x.dropna().to_numpy()
    if len(x) < 10:
        return np.nan

    signs = np.sign(x)
    zc = np.where(np.diff(signs))[0]

    if len(zc) < 2:
        return np.nan

    return np.mean(np.diff(zc))

def acf_decay_lag(x, max_lag=250, threshold=0.1):
    x = x.dropna().to_numpy()
    if len(x) < max_lag:
        return np.nan

    x = x - x.mean()
    var = np.dot(x, x)

    if var == 0:
        return np.nan  # sinal degenerado

    acf = np.correlate(x, x, mode="full")
    acf = acf[len(acf)//2:]
    acf /= var

    for lag in range(1, min(len(acf), max_lag)):
        if abs(acf[lag]) < threshold:
            return lag

    return max_lag