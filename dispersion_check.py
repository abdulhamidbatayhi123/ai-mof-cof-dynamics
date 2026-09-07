"""B53: the particle Peclet range of dataset v2 and of the experimental anchor,
against the correlation our axial-dispersion closure is the limiting case of.

WHY THIS SCRIPT EXISTS.  The datasets and the anchor use

    D_L = 0.7 D_m + 0.5 d_p u,          u = v / eps_t   (interstitial)

which the manuscript's limitations section attributes to Wakao & Funazkri (1978)
rather than to the textbook we first cited (defect B53), and which Perry's handbook
presents as a LOWER BOUND for NONPOROUS particles.  The citation ledger records the
Edwards & Richardson (1968) form, read through Perry's, as

    D_L = 0.73 D_m + [0.5 / (1 + 9.7 D_m / (d_p u))] d_p u

i.e. the same mechanical coefficient ONLY in the limit d_p u / D_m >> 9.7.  The ledger
entry ends "Check the project's actual Peclet range against this before finalising the
limitations."  This script is that check.  It states a range and a discrepancy factor;
it does not re-run the solver and it changes no reported surrogate number, because the
solver is the reference whatever closure it uses.

WHAT IT IS NOT.  It is not a claim that Edwards & Richardson is right and our closure
is wrong.  It is the size of the disagreement between two published correlations at the
particle Peclet numbers this study actually visits, which is what bounds how far the
reference may be read as physical.

RULE 5 (never normalise by a quantity that can vanish).  Every denominator here is
bounded away from zero by construction and the bound is ASSERTED, not assumed:
d_p, u and D_m are strictly positive over the sampled space, so d_p*u/D_m > 0; and
both closures are bounded below by their molecular term, 0.7 D_m and 0.73 D_m.

Writes results/dispersion_check.json.  No number from this file may be quoted in the
manuscript except through paper/numbers.py.
"""

import json
import math
import os

import numpy as np

MANIFEST = "data/parametric_v2/manifest.json"
OUT = "results/dispersion_check.json"

# The molecular diffusivity that appears in the dispersion closure as the solver
# writes it (solver_fd.axial_dispersion default and gen_parametric_dataset line 238).
# NOTE it is 2.5e-5 there while the Glueckauf intraparticle relation in the v2
# manifest uses 2.6e-5; both are water-in-air at ambient and the 4 % difference is
# immaterial to the ratios below, but the two values are not the same number and the
# discrepancy is reported rather than silently reconciled.
D_M_DISPERSION = 2.5e-5

# Edwards & Richardson, through Perry's (CITATIONS.md tranche 4e, VERIFIED):
# gamma_1 = 0.73, gamma_2 = 0.5 / (1 + 9.7 D_m / (d_p u)).
ER_GAMMA1 = 0.73
ER_GAMMA2_NUM = 0.5
ER_C = 9.7

# Ours, as written in gen_parametric_dataset.py:238 and solver_fd.axial_dispersion.
OURS_GAMMA1 = 0.7
OURS_GAMMA2 = 0.5

L_BED = 0.10  # column length in the parametric datasets, gen_parametric_dataset.py


def _pos(name, a):
    """Assert strict positivity of a quantity used as a denominator (rule 5)."""
    a = np.asarray(a, dtype=float)
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{name}: non-finite value")
    if not np.all(a > 0.0):
        raise ValueError(f"{name}: min {a.min():.6g} is not strictly positive; "
                         "rule 5 forbids dividing by it")
    return a


def d_l_ours(d_p, u):
    return OURS_GAMMA1 * D_M_DISPERSION + OURS_GAMMA2 * d_p * u


def d_l_edwards_richardson(d_p, u):
    pe_p = _pos("pe_p", d_p * u / D_M_DISPERSION)
    gamma2 = ER_GAMMA2_NUM / (1.0 + ER_C / pe_p)
    return ER_GAMMA1 * D_M_DISPERSION + gamma2 * d_p * u


def _stats(name, a):
    a = np.asarray(a, dtype=float)
    return {
        "n": int(a.size),
        "min": float(a.min()),
        "median": float(np.median(a)),
        "max": float(a.max()),
        "mean": float(a.mean()),
        "decades": float(math.log10(a.max() / a.min())) if a.min() > 0 else None,
        "_name": name,
    }


def main():
    with open(MANIFEST) as fh:
        man = json.load(fh)

    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    samples = [s for s in man["samples"] if s.get("ok", True)]

    d_p = np.array([mats[s["mat"]]["d_p"] for s in samples])
    eps = np.array([mats[s["mat"]]["eps_t"] for s in samples])
    v = np.array([conds[s["cond"]]["v"] for s in samples])

    _pos("d_p", d_p)
    _pos("eps_t", eps)
    _pos("v", v)

    u = v / eps                       # interstitial, as the closure is written
    pe_p = d_p * u / D_M_DISPERSION   # particle Peclet on the interstitial velocity
    pe_p_sup = d_p * v / D_M_DISPERSION   # the same on the superficial velocity

    ours = d_l_ours(d_p, u)
    er = d_l_edwards_richardson(d_p, u)
    _pos("D_L (Edwards & Richardson)", er)
    ratio = ours / er                 # > 1 means our closure disperses more

    # The mechanical term alone, which is where the two forms differ.  The molecular
    # terms agree to 4 %.  suppression = gamma_2(E&R) / 0.5, the factor by which the
    # full form reduces the mechanical coefficient at this Peclet number.
    suppression = (ER_GAMMA2_NUM / (1.0 + ER_C / pe_p)) / OURS_GAMMA2

    # Column Peclet under each closure: how sharp a front the reference can hold.
    # TWO CONVENTIONS, both reported, because they differ by 1/eps_t ~ 2-3x and the
    # anchor script (compare_lassitter_posthoc.py) uses the SUPERFICIAL one while the
    # dispersion closure itself is written on the interstitial velocity.  Quoting one
    # of these as "the Peclet number" without its denominator is the B63 defect.
    pe_col_ours = u * L_BED / ours
    pe_col_er = u * L_BED / er
    pe_col_ours_sup = v * L_BED / ours
    pe_col_er_sup = v * L_BED / er

    # Where in Peclet the two closures disagree.  The ratio is NOT monotone.  As
    # Pe -> 0 both forms collapse onto their molecular terms and the ratio tends to
    # 0.7/0.73 = 0.96; as Pe -> infinity both are dominated by 0.5 d_p u and the ratio
    # tends to 1; in between it peaks.  So "the Peclet below which they differ" is not
    # a single crossing but a BAND.  The first version of this script assumed
    # monotonicity, took the first index below the threshold and reported the grid's
    # own lower endpoint as if it were an answer.  Report the band and the peak.
    grid = np.logspace(-2, 4, 600001)
    r_grid = d_l_ours(np.full_like(grid, 1.0), grid * D_M_DISPERSION) / \
        d_l_edwards_richardson(np.full_like(grid, 1.0), grid * D_M_DISPERSION)

    def band(thresh):
        """The interval of particle Peclet over which ours/E&R exceeds thresh."""
        idx = np.nonzero(r_grid > thresh)[0]
        if idx.size == 0:
            return None
        lo, hi = float(grid[idx[0]]), float(grid[idx[-1]])
        # the exceedance set must be a single interval for "band" to mean anything
        if idx.size != idx[-1] - idx[0] + 1:
            raise ValueError(f"exceedance set at {thresh} is not an interval")
        return {"pe_lo": lo, "pe_hi": hi}

    peak_i = int(np.argmax(r_grid))

    out = {
        "_what": "B53: particle Peclet range of dataset v2 and of the Lassitter anchor, "
                 "and the disagreement between our axial-dispersion closure and the "
                 "Edwards & Richardson form it is the high-Peclet limit of.",
        "_closure_ours": "D_L = 0.7 D_m + 0.5 d_p u, u = v/eps_t "
                         "(gen_parametric_dataset.py:238, solver_fd.axial_dispersion)",
        "_closure_er": "D_L = 0.73 D_m + [0.5/(1 + 9.7 D_m/(d_p u))] d_p u "
                       "(Edwards & Richardson 1968, read through Perry's; "
                       "CITATIONS.md tranche 4e, VERIFIED)",
        "_velocity_convention": "interstitial u = v/eps_t, matching the closure as written; "
                                "the superficial-velocity Peclet is reported alongside "
                                "because the two conventions differ by 1/eps_t ~ 2-3x",
        "D_m_dispersion": D_M_DISPERSION,
        "D_m_glueckauf": man["glueckauf"]["D_m"],
        "D_m_discrepancy_pct": 100.0 * abs(man["glueckauf"]["D_m"] - D_M_DISPERSION)
                               / D_M_DISPERSION,
        "n_samples": int(len(samples)),

        "pe_particle_interstitial": _stats("Pe_p (interstitial)", pe_p),
        "pe_particle_superficial": _stats("Pe_p (superficial)", pe_p_sup),

        "frac_below_ER_constant": float(np.mean(pe_p < ER_C)),
        "ER_constant": ER_C,

        "dl_ratio_ours_over_er": _stats("D_L ours / D_L E&R", ratio),
        "mechanical_suppression": _stats(
            "gamma_2(E&R)/0.5 -- the factor the full form applies to the "
            "mechanical coefficient", suppression),

        "frac_ratio_above_1p10": float(np.mean(ratio > 1.10)),
        "frac_ratio_above_1p25": float(np.mean(ratio > 1.25)),
        "frac_ratio_above_1p50": float(np.mean(ratio > 1.50)),
        "frac_ratio_above_2": float(np.mean(ratio > 2.0)),

        "disagreement_band_10pct": band(1.10),
        "disagreement_band_25pct": band(1.25),
        "disagreement_peak": {"pe": float(grid[peak_i]),
                              "ratio": float(r_grid[peak_i])},

        "pe_column_ours": _stats("Pe_L = uL/D_L (ours, interstitial u)", pe_col_ours),
        "pe_column_er": _stats("Pe_L = uL/D_L (E&R, interstitial u)", pe_col_er),
        "pe_column_ours_superficial": _stats("Pe_L = vL/D_L (ours, superficial v)",
                                             pe_col_ours_sup),
        "pe_column_er_superficial": _stats("Pe_L = vL/D_L (E&R, superficial v)",
                                           pe_col_er_sup),
    }

    # ---- the experimental anchor (Lassitter 2024 Fig. 10), compare_lassitter.py ----
    # A separate bed, and the one where the manuscript already names "too dispersed"
    # as a discrepancy.  Its declared d_p band is 1-5 mm with 3 mm primary.
    a_v, a_eps, a_L = 0.0098062, 0.4, 0.00635
    a_u = a_v / a_eps
    anchor = {}
    for label, dp in (("dp1mm", 1e-3), ("dp3mm_primary", 3e-3), ("dp5mm", 5e-3)):
        pe = dp * a_u / D_M_DISPERSION
        o, e = d_l_ours(dp, a_u), d_l_edwards_richardson(dp, a_u)
        anchor[label] = {
            "d_p_m": dp,
            "pe_particle": float(pe),
            "D_L_ours": float(o),
            "D_L_er": float(e),
            "ratio_ours_over_er": float(o / e),
            "pe_column_ours": float(a_u * a_L / o),
            "pe_column_er": float(a_u * a_L / e),
            "pe_column_ours_superficial": float(a_v * a_L / o),
            "pe_column_er_superficial": float(a_v * a_L / e),
            "pellets_deep": float(a_L / dp),
        }
    out["anchor"] = {
        "_bed": "Lassitter 2024 Fig. 10 as set up in compare_lassitter.py:34-46",
        "v": a_v, "eps_t": a_eps, "L": a_L, "u_interstitial": a_u,
        "cases": anchor,
    }

    os.makedirs("results", exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)

    # ---------------------------------------------------------------- report
    p = out["pe_particle_interstitial"]
    print(f"dataset v2, n = {out['n_samples']} accepted samples")
    print(f"  particle Peclet d_p u / D_m (interstitial u = v/eps_t)")
    print(f"    {p['min']:.2f} -- {p['max']:.1f}, median {p['median']:.1f}, "
          f"{p['decades']:.2f} decades")
    ps = out["pe_particle_superficial"]
    print(f"  the same on the superficial velocity: {ps['min']:.2f} -- {ps['max']:.1f}, "
          f"median {ps['median']:.1f}")
    print(f"  fraction below the E&R constant 9.7: "
          f"{100 * out['frac_below_ER_constant']:.1f} %")
    r = out["dl_ratio_ours_over_er"]
    print(f"  D_L(ours)/D_L(E&R): {r['min']:.2f} -- {r['max']:.2f}, "
          f"median {r['median']:.2f}")
    print(f"    above 1.10x: {100 * out['frac_ratio_above_1p10']:.1f} %   "
          f"above 1.25x: {100 * out['frac_ratio_above_1p25']:.1f} %   "
          f"above 1.50x: {100 * out['frac_ratio_above_1p50']:.1f} %   "
          f"above 2x: {100 * out['frac_ratio_above_2']:.1f} %")
    b10, b25 = out["disagreement_band_10pct"], out["disagreement_band_25pct"]
    pk = out["disagreement_peak"]
    print(f"    they differ by >10 % over Pe_p {b10['pe_lo']:.2f}-{b10['pe_hi']:.1f} "
          f"and by >25 % over {b25['pe_lo']:.2f}-{b25['pe_hi']:.1f}; "
          f"worst at Pe_p {pk['pe']:.2f} ({pk['ratio']:.2f}x)")
    pc = out["pe_column_ours"]
    pcs = out["pe_column_ours_superficial"]
    print(f"  column Peclet (ours): interstitial uL/D_L {pc['min']:.1f}--{pc['max']:.1f} "
          f"(median {pc['median']:.1f}); superficial vL/D_L {pcs['min']:.1f}--"
          f"{pcs['max']:.1f} (median {pcs['median']:.1f})")
    print()
    print("anchor (Lassitter 2024 Fig. 10):")
    for label, a in anchor.items():
        print(f"  {label:14s} Pe_p {a['pe_particle']:6.2f}  "
              f"D_L ours/E&R {a['ratio_ours_over_er']:5.2f}x  "
              f"Pe_col(sup) ours {a['pe_column_ours_superficial']:5.2f} -> "
              f"E&R {a['pe_column_er_superficial']:5.2f}  "
              f"({a['pellets_deep']:.1f} pellets deep)")
    print()
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
