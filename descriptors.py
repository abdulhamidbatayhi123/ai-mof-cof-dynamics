"""Observable material descriptors — the non-degenerate input set for L6.

Why this exists
---------------
`ladder_data.PARAM_KEYS` hands every arm the eleven *generative* parameters. That
is legitimate for L1-L5, which ask about representation, capacity, architecture,
physics-as-loss and operator family. It is NOT legitimate for L6, which asks
whether identifying the equilibrium and kinetic objects *separately* helps: given
the generative parameters there is nothing to identify, and the rung has a
foregone answer (defect B19).

This module replaces them with what a screening campaign actually measures.

    ISOTHERM FINGERPRINT   uptake q*(RH) at K relative humidities, measured at
                           THREE temperatures (T_in - 10, T_in, T_in + 10 K).
                           This is the standard characterisation, and the
                           multi-temperature part is not optional: a single
                           isotherm cannot reveal the temperature dependence, so
                           with one temperature dH is unrecoverable (measured
                           R^2 = -0.81) and any model would be blind to the
                           isosteric heat. Real campaigns measure several
                           temperatures for exactly this reason.

    BED / OPERATING        rho_p, eps_t, v, T_in, rh_feed. Genuinely known.

    WITHHELD               k_LDF. The mass-transfer coefficient is not directly
                           observable; it has to be inferred from dynamics. This
                           is what makes the equilibrium/kinetic split a real
                           decomposition rather than a relabelling of the inputs.

    ALSO WITHHELD          q_max, delta_H, step_rh, isotherm_n, henry_fraction -
                           the parametric form of the isotherm. A model may learn
                           the isotherm from the fingerprint; it may not be told
                           the equation.

The fingerprint is a *lossy* view: many parameter sets map to nearly the same K
points, so recovering the isotherm is a genuine inference problem, and recovering
the rate is a harder one.
"""
from __future__ import annotations

import numpy as np

from fetch_real_mof_data import rh_to_conc
from isotherm import q_star_np
from ladder_data import PARAM_KEYS

# Relative humidities at which the isotherm is "measured". Spaced to bracket the
# cooperative step across the whole material space (step_rh spans 0.08-0.45).
FINGERPRINT_RH = np.array([0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30,
                           0.40, 0.50, 0.65, 0.80, 0.95])
# Offsets from the material's operating temperature at which the isotherm is
# "measured".
#
# These must span the process's ACTUAL thermal excursion, not a symmetric window
# about ambient. Measured at the mid-column probe over all 988 conditions:
#
#     minimum excursion : +0.00 K at every condition  (adsorption is exothermic,
#                                                      the bed only ever heats)
#     median peak       : +14.4 K
#     p95 peak          : +34.5 K
#     extreme           : +66.6 K
#
# A symmetric +-10 K window therefore wasted its cold point entirely and clipped
# q* for 75 % of conditions. With dH ~ -50 kJ/mol that clipping is fatal: the
# kinetic estimator returned 97.6 % error from the clipped fingerprint against
# 0.80 % from the exact q*(c,T).
FINGERPRINT_DT = np.array([0.0, +10.0, +25.0, +45.0])

OBSERVABLE_KEYS = ["rho_p", "eps_t", "v", "T_in", "rh_feed"]
WITHHELD_KEYS = ["q_max", "delta_H", "step_rh", "isotherm_n", "henry_fraction", "k_LDF"]


def fingerprint(physics, T, rh=FINGERPRINT_RH):
    """Measured uptake q*(RH) at the material's operating temperature (mol/kg)."""
    c = rh_to_conc(rh, T)
    return q_star_np(c, np.full_like(c, T), physics)


def multi_T_fingerprint(physics, T0, rh=FINGERPRINT_RH, dts=FINGERPRINT_DT):
    """Stacked q*(RH) at several temperatures — enough to infer a van't Hoff slope."""
    return np.concatenate([fingerprint(physics, T0 + dt, rh) for dt in dts])


def build(d, normalise_fingerprint=True):
    """Return (X, names) — observable descriptors for every sample in `d`.

    `normalise_fingerprint=True` additionally divides the fingerprint by its own
    maximum and appends that maximum as a separate feature, so shape and scale
    are separable. A network can then learn the *shape* of the step without
    having to also carry the capacity, which is the physically meaningful split.
    """
    from run_l4 import physics_from_params

    rows, names = [], None
    for i in range(len(d.params)):
        p = physics_from_params(d.params[i])
        fp = multi_T_fingerprint(p, p.T_in)
        feats, nms = [], []
        if normalise_fingerprint:
            scale = float(fp.max())
            feats += list(fp / max(scale, 1e-12)) + [scale]
            nms += [f"fp_T{int(dt):+d}_rh{int(100 * r):02d}"
                    for dt in FINGERPRINT_DT for r in FINGERPRINT_RH] + ["fp_scale"]
        else:
            feats += list(fp)
            nms += [f"fp_T{int(dt):+d}_rh{int(100 * r):02d}"
                    for dt in FINGERPRINT_DT for r in FINGERPRINT_RH]
        for k in OBSERVABLE_KEYS:
            feats.append(d.params[i][d.pidx(k)])
            nms.append(k)
        rows.append(feats)
        names = nms
    return np.array(rows, dtype=np.float64), names


def standardise(X, train_idx):
    """Standardise using TRAIN statistics only (no leakage from held-out materials)."""
    mu = X[train_idx].mean(axis=0)
    sd = X[train_idx].std(axis=0)
    sd[sd == 0] = 1.0
    return (X - mu) / sd, mu, sd


def check_non_degenerate(d, X, verbose=True):
    """Confirm the descriptors really are a LOSSY view of the generative parameters.

    If a withheld parameter can be recovered from the descriptors to near-machine
    precision, the substitution has not removed the degeneracy and L6 would still
    be measuring nothing. Reported as R^2 of a strong regressor per withheld key.
    """
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import r2_score

    tr, te = d.idx("train"), d.idx("novel_material")
    out = {}
    if verbose:
        print(f"  {'withheld parameter':<18} {'R2 from descriptors':>21}  recoverable?")
        print("  " + "-" * 58)
    for k in WITHHELD_KEYS:
        y = d.params[:, d.pidx(k)]
        m = RandomForestRegressor(n_estimators=200, random_state=0, n_jobs=-1)
        m.fit(X[tr], y[tr])
        r2 = float(r2_score(y[te], m.predict(X[te])))
        out[k] = r2
        if verbose:
            tag = "YES - still degenerate" if r2 > 0.98 else ("partly" if r2 > 0.7 else "no")
            print(f"  {k:<18} {r2:>21.4f}  {tag}")
    return out


if __name__ == "__main__":
    import ladder_data

    d = ladder_data.load()
    X, names = build(d)
    print(f"\ndescriptors: {X.shape[1]} features")
    print("  " + ", ".join(names))
    print(f"\nwithheld: {WITHHELD_KEYS}")
    print("\nDegeneracy check — can the withheld parameters be read off the descriptors?")
    check_non_degenerate(d, X)
