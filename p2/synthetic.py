"""A known-answer LDF system: dq/dt = k (q*(c) - q), c(t) a smooth breakthrough ramp,
q*(c) Langmuir. Used ONLY by tests, never on the confirmatory grid."""
import numpy as np
from scipy.integrate import solve_ivp


def ldf_series(k, n=400, seed=0, t_end=600.0, qmax=5.0, b=3.0):
    t = np.linspace(0.0, t_end, n)

    def c_of(tt):
        return 1.0 / (1.0 + np.exp(-(tt - 0.4 * t_end) / (0.05 * t_end)))

    def qs_of(cc):
        return qmax * b * cc / (1.0 + b * cc)

    sol = solve_ivp(lambda tt, q: k * (qs_of(c_of(tt)) - q), (0, t_end), [0.0],
                    t_eval=t, rtol=1e-10, atol=1e-12)
    c = c_of(t)
    return {"t": t, "c": c, "q": sol.y[0], "T": np.full(n, 298.0), "qstar": qs_of(c)}
