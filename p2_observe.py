"""Paper 2 observation model: what a method is allowed to see, and how it is corrupted.

PREREG_P2_discoverability.md §4.2. Every discovery method and the identifiability
analysis read data ONLY through `observe()`, so the corruption is identical for all
of them (information parity, paper 1's rule). Deterministic: the same (cell,
replicate, sigma, eps, obs) always yields the same draw.

Observation models
  O1  interior c, q, T at N_PROBE equally spaced positions (q observed: optimistic)
  O2  interior c, T at the same positions (q latent -- what probes can measure)
  O3  outlet c(t), T(t) only (the standard experiment)
Every model is sampled at N_T times, uniform over the solved horizon.

Noise: i.i.d. Gaussian on each observed channel, SD = sigma x (that channel's range in
the cell's ground truth). Relative to range, not to the local value, so a quiet
channel is not made artificially clean.

Isotherm error: the method is given q*_meas(c, T) = q*(c, T) * (1 + eps * g(c / c_in)),
g a smooth random function (4 random Fourier modes on [0, 1]) normalised to unit RMS,
drawn once per replicate. Smooth, because a measured isotherm is wrong by a smooth
calibration/fit error, not by point noise; relative, because isotherm errors are
reported in relative terms. The TRUE q* never leaves this module.

    python p2_observe.py --selftest
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np

from fetch_real_mof_data import get_mof303_physics
from isotherm import q_star_np
from solver_fd import AdsorptionPhysicsConfig

DATA = "data/p2"
N_PROBE = 20
N_T = 200
N_MODES = 4


def _rng(*keys):
    h = hashlib.sha256("|".join(map(str, keys)).encode()).hexdigest()
    return np.random.default_rng(int(h[:16], 16))


def load_cell(name):
    d = np.load(os.path.join(DATA, name + ".npz"))
    man = json.load(open(os.path.join(DATA, "manifest.json")))["cells"][name]
    return {k: d[k] for k in ("z", "t", "c", "q", "T")}, man


def physics_for(man):
    p = AdsorptionPhysicsConfig() if man["iso"] == "langmuir" else get_mof303_physics()
    return p


def isotherm_error_fn(name, rep, eps):
    """g(x) on x = c/c_in in [0, 1]: smooth, unit RMS, fixed per (cell, replicate)."""
    r = _rng(name, rep, "iso")
    a, ph = r.normal(size=N_MODES), r.uniform(0, 2 * np.pi, N_MODES)
    xs = np.linspace(0, 1, 2001)
    raw = sum(a[j] * np.sin((j + 1) * np.pi * xs + ph[j]) for j in range(N_MODES))
    scale = np.sqrt(np.mean(raw ** 2))

    def g(x):
        x = np.clip(np.asarray(x, dtype=float), 0.0, 1.0)
        return sum(a[j] * np.sin((j + 1) * np.pi * x + ph[j]) for j in range(N_MODES)) / scale
    return lambda c, c_in: eps * g(np.asarray(c) / c_in)


def observe(name, rep, sigma, eps, obs):
    f, man = load_cell(name)
    p = physics_for(man)
    it = np.linspace(0, len(f["t"]) - 1, N_T).round().astype(int)
    iz = (np.linspace(0, len(f["z"]) - 1, N_PROBE).round().astype(int) if obs in ("O1", "O2")
          else np.array([len(f["z"]) - 1]))
    chans = {"O1": ("c", "q", "T"), "O2": ("c", "T"), "O3": ("c", "T")}[obs]
    r = _rng(name, rep, sigma, obs, "noise")
    data = {}
    for ch in chans:
        true = f[ch][np.ix_(iz, it)].astype(float)
        rng_ch = float(f[ch].max() - f[ch].min())
        data[ch] = true + (r.normal(scale=sigma * rng_ch, size=true.shape) if sigma > 0 else 0.0)
    err = isotherm_error_fn(name, rep, eps)
    c_in = man["c_in"]

    def qstar_meas(c, T):
        q = q_star_np(np.asarray(c, float), np.asarray(T, float), p)
        return q * (1.0 + err(c, c_in))
    return {"t": f["t"][it].astype(float), "z": f["z"][iz].astype(float), "obs": obs,
            "channels": data, "qstar_meas": qstar_meas, "c_in": c_in,
            "meta": {k: man[k] for k in ("iso", "law", "pe_mult", "Da", "q_max", "T_in")}}


def selftest():
    names = sorted(json.load(open(os.path.join(DATA, "manifest.json")))["cells"])
    nm = names[0]
    f, man = load_cell(nm)
    o = observe(nm, 0, 0.0, 0.0, "O1")
    it = np.linspace(0, len(f["t"]) - 1, N_T).round().astype(int)
    iz = np.linspace(0, len(f["z"]) - 1, N_PROBE).round().astype(int)
    assert np.allclose(o["channels"]["q"], f["q"][np.ix_(iz, it)]), "sigma=0 must be exact"
    p = physics_for(man)
    c, T = f["c"][iz][:, it], f["T"][iz][:, it]
    assert np.allclose(o["qstar_meas"](c, T), q_star_np(c.astype(float), T.astype(float), p)), \
        "eps=0 must return the true isotherm"
    o2 = observe(nm, 0, 0.02, 0.0, "O1")
    rng_c = float(f["c"].max() - f["c"].min())
    sd = float(np.std(o2["channels"]["c"] - f["c"][np.ix_(iz, it)]))
    assert abs(sd / (0.02 * rng_c) - 1) < 0.05, f"noise SD {sd} vs {0.02 * rng_c}"
    xs = np.linspace(0, 1, 2001)
    e = isotherm_error_fn(nm, 3, 0.05)(xs, 1.0)
    assert abs(np.sqrt(np.mean(e ** 2)) / 0.05 - 1) < 1e-3, "isotherm error RMS must equal eps"
    a = observe(nm, 1, 0.02, 0.02, "O3")["channels"]["c"]
    b = observe(nm, 1, 0.02, 0.02, "O3")["channels"]["c"]
    assert np.array_equal(a, b), "draws must be deterministic"
    assert set(observe(nm, 0, 0, 0, "O2")["channels"]) == {"c", "T"}, "O2 must hide q"
    assert observe(nm, 0, 0, 0, "O3")["z"].size == 1, "O3 is outlet only"
    print(f"selftest OK on {nm}: exact at sigma=eps=0; noise SD ratio {sd / (0.02 * rng_c):.3f}; "
          f"isotherm-error RMS exact; deterministic; O2 hides q; O3 outlet-only")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        selftest()
