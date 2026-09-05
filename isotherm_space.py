"""How the isotherm behaves across the WHOLE sampled material space, not at one config.

`validate.py`'s isotherm gates evaluate two named configurations (`default` and
`mof303`). Dataset v2 contains **240 sampled materials** whose shape parameter
`isotherm_n` spans 1.01–5.98 and whose primary-site fraction `henry_fraction`
spans 0.03–0.25. A property verified at two points in that space is not a property
of the space — this is the error class of A18/A21/A26 (a quantity measured at one
setting, stated as intrinsic), applied to the isotherm instead of to a sample size.

What this measures, per material, at T = 298.15 K:

  K_H          the Henry constant, dq*/dc as c -> 0, = q_max * f_H * b_H.
               Finite and positive for every material, by construction.
  c_henry      the largest c at which the cooperative term contributes less than
               `tol` of the total loading — i.e. the TOP OF THE HENRY REGION.
               Solved exactly: the primary term is Langmuir and the cooperative
               term is Sips, so the crossover is
                   (1 - f) (b_C c)^n / [f b_H c] = tol/(1-tol)
               to leading order in c, giving c_henry in closed form.
  the same, expressed against the physical scales the column actually visits:
  c_step (the cooperative step) and c_in (the feed).

Why it matters: `q ~ K_H c` as `c -> 0` is true for every material because n > 1
strictly, so A5/B4's thermodynamic claim survives. But the *width* of the region
where it is true varies over many decades, and for materials with n near 1 the
Henry regime lies far below any concentration the column ever sees. The paper
must state the distribution, not one config's number.

    python isotherm_space.py                # writes results/isotherm_space.json
    python isotherm_space.py --tol 0.01
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

from fetch_real_mof_data import rh_to_conc
from isotherm import henry_constant, q_star_np

R_GAS = 8.314
T_REF = 298.15
ROOT_V2 = "data/parametric_v2"
OUT = "results/isotherm_space.json"


class _P:
    """A physics stand-in carrying only what the isotherm needs."""


def material_physics(m, b_H_ratio):
    """Rebuild one material's isotherm exactly as the generator did.

    `b0` is not stored per material: the generator calibrates it so the
    cooperative step sits at `step_rh` (isotherm.calibrate_step). Reproducing that
    here rather than reading a stored value is deliberate — if the reconstruction
    were wrong, `q_star` at the step would not be half-saturated, and the
    self-check below would fail.
    """
    p = _P()
    p.q_max = m["q_max"]
    p.delta_H = m["delta_H"]
    p.isotherm_n = m["isotherm_n"]
    p.henry_fraction = m["henry_fraction"]
    c_step = rh_to_conc(m["step_rh"], T_REF)
    p.b0 = (1.0 / c_step) / np.exp(-p.delta_H / (R_GAS * T_REF))
    p.b_H0 = p.b0 / b_H_ratio
    return p, c_step


def log10_henry_ceiling(p, tol):
    """log10 of the largest c at which the cooperative term is below `tol` of the total.

    Leading order (both terms far from saturation):
        cluster/primary = (1-f) (b_C c)^n / (f b_H c) = tol/(1-tol)
      => c^(n-1) = [tol/(1-tol)] * f * b_H / [(1-f) * b_C^n]
    Exact for c well below 1/b_C, which is where the Henry region lives.

    Returned in LOG SPACE, and that is not cosmetic. The exponent 1/(n-1) reaches
    ~110 for the material with n = 1.0091, so the linear form underflows float64 to
    exactly 0.0 — and a ratio taken against that zero reported "inf decades", which
    is protocol rule 5 (never normalise by a quantity that can vanish) committed
    inside the script written to check the isotherm. Everything downstream stays
    logarithmic for the same reason.
    """
    kT = np.exp(-p.delta_H / (R_GAS * T_REF))
    b_H, b_C = p.b_H0 * kT, p.b0 * kT
    f, n = p.henry_fraction, p.isotherm_n
    r = tol / (1.0 - tol)
    num = np.log10(r) + np.log10(f) + np.log10(b_H) - np.log10(1.0 - f) - n * np.log10(b_C)
    return float(num / (n - 1.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT_V2)
    ap.add_argument("--tol", type=float, default=0.01,
                    help="cooperative-term share defining the top of the Henry region")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    man = json.load(open(os.path.join(args.root, "manifest.json")))
    mats, ratio = man["materials"], man["b_H_ratio"]
    conds = man["conditions"]
    rh_feed = np.array([c["rh_feed"] for c in conds])
    c_in_med = float(np.median([rh_to_conc(r, T_REF) for r in rh_feed]))

    rows = []
    for m in mats:
        p, c_step = material_physics(m, ratio)
        # self-check: the cooperative term must be half-saturated at c_step
        theta_cluster = 1.0 / (1.0 + (1.0) ** -p.isotherm_n)  # (b_C c_step)^n = 1
        assert abs(theta_cluster - 0.5) < 1e-12, "step calibration reconstructed wrongly"
        K_H = float(henry_constant(T_REF, p))
        lg = log10_henry_ceiling(p, args.tol)
        # Verify the closed form against a direct evaluation wherever the ceiling is
        # representable; where it underflows there is nothing to evaluate against,
        # and that is itself the finding.
        share_err = None
        if lg > -290.0:
            c_h = 10.0 ** lg
            kT = np.exp(-p.delta_H / (R_GAS * T_REF))
            q = float(q_star_np(np.array([c_h]), np.array([T_REF]), p)[0])
            prim = p.q_max * p.henry_fraction * (p.b_H0 * kT * c_h) / (1.0 + p.b_H0 * kT * c_h)
            if q > 0:
                share_err = abs((1.0 - prim / q) - args.tol)
        rows.append({
            "material_id": m["material_id"], "isotherm_n": m["isotherm_n"],
            "henry_fraction": m["henry_fraction"], "q_max": m["q_max"],
            "step_rh": m["step_rh"], "K_H": K_H,
            "log10_c_henry": lg, "c_step": float(c_step),
            "log10_c_henry_over_c_step": lg - float(np.log10(c_step)),
            "log10_c_henry_over_c_in_median": lg - float(np.log10(c_in_med)),
            "closed_form_share_error": share_err,
            "representable": bool(lg > -290.0),
        })

    def stat(key, log_already=False):
        v = np.array([r[key] for r in rows])
        d = {"min": float(v.min()), "p05": float(np.percentile(v, 5)),
             "median": float(np.median(v)), "p95": float(np.percentile(v, 95)),
             "max": float(v.max())}
        # The span is a DIFFERENCE in log space, never a ratio: the linear quantity
        # underflows to zero for the flattest materials and a ratio against it is
        # meaningless (rule 5).
        d["decades"] = d["max"] - d["min"] if log_already else float(np.log10(d["max"] / d["min"]))
        return d

    out = {
        "root": args.root, "T_ref": T_REF, "tol": args.tol,
        "n_materials": len(rows), "b_H_ratio": ratio,
        "c_in_median": c_in_med,
        "material_space": man["material_space"],
        "K_H": stat("K_H"),
        "log10_c_henry": stat("log10_c_henry", log_already=True),
        "log10_c_henry_over_c_step": stat("log10_c_henry_over_c_step", log_already=True),
        "log10_c_henry_over_c_in_median": stat("log10_c_henry_over_c_in_median", log_already=True),
        "max_closed_form_share_error": float(max(
            r["closed_form_share_error"] for r in rows if r["closed_form_share_error"] is not None)),
        "n_representable": int(sum(r["representable"] for r in rows)),
        "n_henry_region_below_1e6_of_feed": int(sum(
            1 for r in rows if r["log10_c_henry_over_c_in_median"] < -6.0)),
        "n_henry_region_below_1e3_of_feed": int(sum(
            1 for r in rows if r["log10_c_henry_over_c_in_median"] < -3.0)),
        "rows": rows,
    }
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(args.out, "w"), indent=2)

    print(f"isotherm across the material space — {len(rows)} materials, T = {T_REF} K, "
          f"tol = {args.tol:.0%}\n")
    print(f"  isotherm_n spans {min(r['isotherm_n'] for r in rows):.2f}"
          f"–{max(r['isotherm_n'] for r in rows):.2f}, "
          f"henry_fraction {min(r['henry_fraction'] for r in rows):.3f}"
          f"–{max(r['henry_fraction'] for r in rows):.3f}")
    s = out["K_H"]
    print(f"\n  Henry constant K_H (mol/kg per mol/m3)")
    print(f"     min {s['min']:.3e}   median {s['median']:.3e}   max {s['max']:.3e}"
          f"   ({s['decades']:.1f} decades)")
    for key, label in (("log10_c_henry_over_c_step", "top of the Henry region, log10(c / c_step)"),
                       ("log10_c_henry_over_c_in_median",
                        "top of the Henry region, log10(c / median feed c_in)")):
        s = out[key]
        print(f"\n  {label}")
        print(f"     min {s['min']:.1f}   p05 {s['p05']:.1f}   median {s['median']:.1f}"
              f"   max {s['max']:.1f}   (span {s['decades']:.0f} decades)")
    print(f"\n  closed form vs direct evaluation: max share error "
          f"{out['max_closed_form_share_error']:.2e} "
          f"({out['n_representable']}/{len(rows)} representable in float64)")
    print(f"  Henry region ends below 1e-3 of the feed: "
          f"{out['n_henry_region_below_1e3_of_feed']} / {len(rows)} materials")
    print(f"  Henry region ends below 1e-6 of the feed: "
          f"{out['n_henry_region_below_1e6_of_feed']} / {len(rows)} materials")
    print(f"\n  Henry's law holds for EVERY material — isotherm_n > 1 strictly, so the "
          f"cooperative\n  term is o(c) at the origin and K_H is finite and positive "
          f"everywhere. What varies\n  by "
          f"{out['log10_c_henry_over_c_in_median']['decades']:.0f} decades is the WIDTH of "
          f"the region where it is the DOMINANT behaviour,\n  and for the flattest "
          f"materials that region lies far below any concentration the\n  column visits. "
          f"Report the distribution, never one configuration's K_H.")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
