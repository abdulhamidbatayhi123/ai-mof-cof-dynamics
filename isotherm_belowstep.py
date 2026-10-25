"""What the "primary" (Henry) sites actually hold, given b_H = b_C / 20.

Why this exists (Digital Discovery rework, 2026-10-25): a domain reviewer pointed out
that the generator sets the primary-site affinity 20x WEAKER than the cluster affinity
(B_H_RATIO = 20; gen_parametric_dataset.build_physics). At the step, b_C c = 1, so
b_H c = 1/20 and the Langmuir term is only 1/21 filled. The manuscript described f_H as
"the fraction of capacity the primary sites hold below the step"; that is not what f_H
is in this parameterisation. This script measures, from the isotherm alone and for
every v2 material at its own step and a reference temperature, the quantities the text
should report instead:

  below_step_fraction    q*(c_step / 2) / q_max     uptake at half the step humidity
  primary_share          the Langmuir term's share of that uptake
  primary_fill_at_step   b_H c_step / (1 + b_H c_step)

plus the same numbers for the MOF-303 parameterisation used at the anchor.
No solve; seconds.

    python isotherm_belowstep.py
Writes results/isotherm_belowstep.json.
"""
from __future__ import annotations

import json
import os

import numpy as np

import gen_parametric_dataset as gen
from fetch_real_mof_data import get_mof303_physics, rh_to_conc
from isotherm import R_GAS, q_star_np
from v2_common import ROOT_V2, write_atomic

T_REF = 298.15


def terms(p, c, T):
    kT = np.exp(-p.delta_H / (R_GAS * T))
    bH, bC = p.b_H0 * kT, p.b0 * kT
    lang = p.henry_fraction * bH * c / (1 + bH * c)
    sips = (1 - p.henry_fraction) * (bC * c) ** p.isotherm_n / (1 + (bC * c) ** p.isotherm_n)
    return lang, sips, bH * c


def main():
    man = json.load(open(os.path.join(ROOT_V2, "manifest.json")))
    cond = {"rh_feed": 0.3, "v": 0.1, "T_in": T_REF, "condition_id": -1}
    rows = []
    for m in man["materials"]:
        p = gen.build_physics(m, cond)
        c_step = gen.rh_to_conc(m["step_rh"], T_REF)
        lang, sips, _ = terms(p, 0.5 * c_step, T_REF)
        total = float(q_star_np(np.array([0.5 * c_step]), np.array([T_REF]), p)[0]) / p.q_max
        if abs(total - (lang + sips)) > 1e-9:
            raise AssertionError("term split does not reproduce q_star")
        _, _, bh_step = terms(p, c_step, T_REF)
        rows.append({"material_id": m["material_id"], "f_H": m["henry_fraction"],
                     "n": m["isotherm_n"], "below_step_fraction": total,
                     "primary_share": lang / total if total > 0 else 0.0,
                     "primary_fill_at_step": bh_step / (1 + bh_step)})
    mof = get_mof303_physics()
    c_step = rh_to_conc(0.15, T_REF)
    lang, sips, _ = terms(mof, 0.5 * c_step, T_REF)
    c_feed = rh_to_conc(0.328, T_REF)
    lang_f, sips_f, bh_f = terms(mof, c_feed, T_REF)
    arr = lambda k: np.array([r[k] for r in rows])
    out = {"_what": __doc__.split("\n\n")[0], "T_ref": T_REF, "b_C_over_b_H": gen.B_H_RATIO,
           "n_materials": len(rows),
           "below_step_fraction_median": float(np.median(arr("below_step_fraction"))),
           "below_step_fraction_range": [float(arr("below_step_fraction").min()), float(arr("below_step_fraction").max())],
           "primary_share_median": float(np.median(arr("primary_share"))),
           "primary_fill_at_step": float(rows[0]["primary_fill_at_step"]),
           "f_H_range": [float(arr("f_H").min()), float(arr("f_H").max())],
           "mof303": {"f_H": mof.henry_fraction, "below_step_fraction": float(lang + sips),
                      "primary_share_below_step": float(lang / (lang + sips)),
                      "primary_fraction_of_qmax_at_feed": float(lang_f),
                      "primary_fill_at_feed": float(bh_f / (1 + bh_f))},
           "materials": rows}
    write_atomic(out, "results/isotherm_belowstep.json")
    print({k: v for k, v in out.items() if k != "materials"})


if __name__ == "__main__":
    main()
