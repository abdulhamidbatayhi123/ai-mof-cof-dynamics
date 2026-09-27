"""Weak-form transform (M2b, after Messenger & Bortz's WSINDy, S19/S54).

For dq/dt = sum_j theta_j f_j, multiply by a compactly supported test function phi_i
and integrate by parts (phi vanishes at its ends):

    -int phi_i' q dt  =  sum_j theta_j int phi_i f_j dt

so the target needs NO derivative of noisy data. Returns (G, b) in the same
{term: column} / target form every sparse solver in p2.methods takes, so each of them
gets a weak-form variant with no further code.

Test functions: phi(t) = ((t - a)(b - t))^p on [a, b], p = 8, overlapping supports
of `support` samples, stride support // 4.
"""
import numpy as np


def _trapz_weights(t):
    w = np.zeros_like(t)
    d = np.diff(t)
    w[:-1] += d / 2
    w[1:] += d / 2
    return w


def weak_system(F, q, t, support=61, power=8):
    t = np.asarray(t, float)
    n = len(t)
    support = min(support, n - (1 - n % 2))
    stride = max(support // 4, 1)
    w = _trapz_weights(t)
    rows_G = {k: [] for k in F}
    b = []
    for s0 in range(0, n - support + 1, stride):
        idx = slice(s0, s0 + support)
        tt = t[idx]
        a, bb = tt[0], tt[-1]
        x = (tt - a) * (bb - tt)
        phi = x ** power
        dphi = power * x ** (power - 1) * ((bb - tt) - (tt - a))
        scale = np.max(np.abs(phi)) or 1.0
        phi, dphi = phi / scale, dphi / scale
        ww = w[idx]
        b.append(-np.sum(dphi * q[idx] * ww))
        for k, col in F.items():
            rows_G[k].append(np.sum(phi * col[idx] * ww))
    return {k: np.array(v) for k, v in rows_G.items()}, np.array(b)
