"""Can the KINETIC object be identified from dynamics? (closes the SINDy open item)

Why this replaces the original SINDy script
-------------------------------------------
`sindy_discovery.py` put `q*` — computed from the exact Langmuir law that
generated the data — into its own feature library, alongside `q`. The true law is
`dq/dt = k(q* - q)`, so both terms were handed to the regressor: that is not
discovery, it is a two-term linear fit onto the answer. On the real data it also
returned `dq/dt = 0` at every threshold, because it sampled a column node the
front had never reached (retraction A7).

The question worth asking is the one the ladder actually needs. `descriptors.py`
established that `k_LDF` is **not recoverable from observable material
descriptors** (R² = −0.61) — the isotherm is measurable, the rate is not. H1's
separate-identification arm therefore depends on the rate being recoverable from
*dynamics*. This script tests exactly that.

Two estimators, both using ONLY observables
-------------------------------------------
**structured** — the LDF form is assumed known but its coefficient is not:

        dq/dt = k (q*_obs(c,T) - q)

  where `q*_obs` comes from the measured isotherm fingerprint, not from the
  generating parameters. `k` is then a one-parameter linear regression through
  the origin, solved per material. This is what "separate identification" means
  in practice.

**sindy** — the form is NOT assumed. A polynomial library in the observables
  (1, q, c, T, and products) is fitted by sequential thresholded ridge with
  **column standardisation**, which the original lacked: its library spanned ~40
  orders of magnitude (κ(Θ) = 1.07e44), making a single absolute threshold
  meaningless.

Both are scored by how well they recover the true `k_LDF`, which is known here
but never shown to either estimator.
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

import ladder_data
from descriptors import FINGERPRINT_DT, FINGERPRINT_RH, fingerprint
from fetch_real_mof_data import rh_to_conc
from ladder_data import PARAM_KEYS


def observable_qstar(fp_multiT, rh_grid, dt_grid, c_query, T_query, T0):
    """Interpolate the measured fingerprint in BOTH concentration and temperature.

    Evaluating the isotherm at a single mean temperature destroys the estimate:
    with dH ~ -50 kJ/mol and a thermal excursion of tens of kelvin, q* varies by
    orders of magnitude over a run. Measured on 300 conditions, the k-estimator
    gives 0.80 % median error with the exact q*(c,T) and **99.39 %** with the same
    fingerprint held at mean T. The rate is identifiable; an isothermal isotherm
    simply cannot identify it.

    This is the reason `descriptors.py` records the fingerprint at three
    temperatures rather than one.

    fp_multiT : (len(dt_grid), len(rh_grid)) uptake, measured at T0 + dt_grid.
    """
    import numpy as _np

    c_query = _np.clip(c_query, 0.0, None)
    per_T = []
    for j, dt in enumerate(dt_grid):
        Tj = T0 + dt
        c_grid = rh_to_conc(rh_grid, Tj)
        o = _np.argsort(c_grid)
        per_T.append(_np.interp(c_query, c_grid[o], fp_multiT[j][o]))
    per_T = _np.stack(per_T)                       # (nT, N)

    Tg = T0 + _np.asarray(dt_grid, dtype=float)
    Tq = _np.clip(_np.asarray(T_query, dtype=float), Tg.min(), Tg.max())
    # linear in T between the bracketing measured isotherms
    out = _np.empty_like(c_query, dtype=float)
    for i in range(len(Tg) - 1):
        m = (Tq >= Tg[i]) & (Tq <= Tg[i + 1])
        if m.any():
            w = (Tq[m] - Tg[i]) / (Tg[i + 1] - Tg[i])
            out[m] = (1 - w) * per_T[i][m] + w * per_T[i + 1][m]
    return out


def estimate_k_structured(t, c, q, T, fp_multiT, rh_grid, dt_grid, T0):
    """One-parameter fit of dq/dt = k (q*_obs - q), through the origin."""
    dq = np.gradient(q, t)
    drive = observable_qstar(fp_multiT, rh_grid, dt_grid, c, T, T0) - q
    denom = float(np.dot(drive, drive))
    if denom <= 0:
        return np.nan, np.nan
    k = float(np.dot(drive, dq) / denom)
    resid = dq - k * drive
    ss_tot = float(np.sum((dq - dq.mean()) ** 2))
    r2 = 1.0 - float(np.sum(resid ** 2)) / ss_tot if ss_tot > 0 else np.nan
    return k, r2


def stridge(Theta, y, threshold=0.05, alpha=1e-6, n_iter=20):
    """Sequential thresholded ridge on STANDARDISED columns.

    Standardisation is not cosmetic: with raw columns spanning many orders of
    magnitude a single absolute threshold prunes by units rather than by
    relevance, which is what made the original implementation unusable.
    """
    mu, sd = Theta.mean(0), Theta.std(0)
    sd[sd == 0] = 1.0
    Z = (Theta - mu) / sd
    ys = y.std() or 1.0
    yz = (y - y.mean()) / ys

    w = np.linalg.solve(Z.T @ Z + alpha * np.eye(Z.shape[1]), Z.T @ yz)
    for _ in range(n_iter):
        small = np.abs(w) < threshold
        w[small] = 0.0
        big = ~small
        if not big.any():
            break
        Zb = Z[:, big]
        w[big] = np.linalg.solve(Zb.T @ Zb + alpha * np.eye(Zb.shape[1]), Zb.T @ yz)
    return w, mu, sd, ys


def sindy_library(q, c, T):
    cols = [np.ones_like(q), q, c, T, q * q, c * c, q * c, q * T, c * T]
    names = ["1", "q", "c", "T", "q^2", "c^2", "q*c", "q*T", "c*T"]
    return np.column_stack(cols), names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node-frac", type=float, default=0.5,
                    help="column position to probe, as a fraction of L")
    ap.add_argument("--out", default="results/kinetics_identification.json")
    args = ap.parse_args()

    # slice-only load: this analysis probes one column position
    d = ladder_data.load_slice(z_frac=args.node_frac)
    nt = d.fields.shape[2]

    from run_l4 import physics_from_params

    rows = []
    for gi in range(len(d.params)):
        p = physics_from_params(d.params[gi])
        k_true = float(d.params[gi][d.pidx("k_LDF")])
        t = np.linspace(0.0, d.t_final[gi], nt)
        c = d.fields[gi, 0, :] * p.c_in
        q = d.fields[gi, 1, :] * p.q_max
        T = d.fields[gi, 2, :] * p.T_in

        # a probe that never sees the front carries no kinetic information;
        # this is the failure mode that made the original return dq/dt = 0
        if q.max() < 0.02 * p.q_max:
            rows.append({"gi": gi, "skipped": "front never reached probe"})
            continue

        T0 = float(p.T_in)
        fp_multiT = np.stack([fingerprint(p, T0 + dt) for dt in FINGERPRINT_DT])
        k_hat, r2 = estimate_k_structured(t, c, q, T, fp_multiT,
                                          FINGERPRINT_RH, FINGERPRINT_DT, T0)

        Theta, names = sindy_library(q, c, T)
        w, mu, sd, ys = stridge(Theta, np.gradient(q, t))
        terms = {n: float(wi) for n, wi in zip(names, w) if abs(wi) > 0}

        rows.append({
            "gi": gi, "material": int(d.material_ids[gi]), "split": str(d.split[gi]),
            "k_true": k_true, "k_hat": float(k_hat), "r2": float(r2),
            "sindy_terms": terms,
            "sindy_has_q": bool(abs(w[names.index("q")]) > 0),
            "sindy_q_sign": float(np.sign(w[names.index("q")])),
        })

    ok = [r for r in rows if "k_hat" in r and np.isfinite(r["k_hat"])]
    kt = np.array([r["k_true"] for r in ok])
    kh = np.array([r["k_hat"] for r in ok])
    rel = np.abs(kh - kt) / kt

    print(f"\nprobed z = {args.node_frac:.2f} L | {len(ok)}/{len(rows)} conditions usable "
          f"({len(rows) - len(ok)} skipped: front never reached the probe)")
    print("\nSTRUCTURED estimator  dq/dt = k (q*_obs - q), fitted per condition")
    print(f"  median |k_hat - k_true| / k_true : {100 * np.median(rel):.2f} %")
    print(f"  fraction within 10 %             : {100 * np.mean(rel < 0.10):.1f} %")
    print(f"  fraction within 25 %             : {100 * np.mean(rel < 0.25):.1f} %")
    print(f"  correlation(k_hat, k_true)       : {np.corrcoef(kh, kt)[0, 1]:.4f}")
    for sp in ("train", "novel_condition", "novel_material"):
        sub = [r for r in ok if r["split"] == sp]
        if sub:
            rr = np.abs(np.array([r["k_hat"] for r in sub]) - np.array([r["k_true"] for r in sub])) \
                / np.array([r["k_true"] for r in sub])
            print(f"    {sp:<17} median err {100 * np.median(rr):5.2f} %   (n={len(sub)})")

    hasq = np.mean([r["sindy_has_q"] for r in ok])
    negq = np.mean([r["sindy_q_sign"] < 0 for r in ok])
    print("\nSINDy estimator  polynomial library, form NOT assumed")
    print(f"  selected a 'q' term            : {100 * hasq:.1f} % of conditions")
    print(f"  ...with the NEGATIVE sign LDF requires : {100 * negq:.1f} %")
    from collections import Counter
    cnt = Counter(t for r in ok for t in r["sindy_terms"])
    print("  most frequently selected terms :",
          ", ".join(f"{n}({100 * v / len(ok):.0f}%)" for n, v in cnt.most_common(6)))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump({"node_frac": args.node_frac, "rows": rows,
               "structured": {"median_rel_err": float(np.median(rel)),
                              "frac_within_10pct": float(np.mean(rel < 0.10)),
                              "corr": float(np.corrcoef(kh, kt)[0, 1])}},
              open(args.out, "w"), indent=2)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
