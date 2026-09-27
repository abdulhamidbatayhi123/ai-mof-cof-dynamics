"""Derivative estimation and the equilibrium-informed library Lib-B (PREREG_P2 §3).
q* here is ALWAYS the measured equilibrium the method is given, never the truth."""
import numpy as np
from scipy.signal import savgol_filter


def derivative(y, t, window=21, order=3):
    """Savitzky-Golay derivative on a uniform grid (p2_observe samples uniformly)."""
    dt = float(t[1] - t[0])
    w = min(window, (len(y) // 2) * 2 - 1)
    return savgol_filter(y, w, min(order, w - 1), deriv=1, delta=dt)


def lib_b(c, q, T, qstar):
    return {"1": np.ones_like(c), "c": c, "q": q, "T": T, "c*q": c * q,
            "q^2": q ** 2, "c^2": c ** 2, "qstar": qstar}
