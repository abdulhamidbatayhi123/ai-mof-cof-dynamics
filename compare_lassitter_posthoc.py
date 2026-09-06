"""POST-HOC sensitivity for the Lassitter comparison — declared as such, kept apart.

`compare_lassitter.py` is the pre-registered run and is not modified. After seeing
its result, one closure stood out: the Ruthven axial-dispersion correlation used
for every dataset in this project, D_L = 0.7 D_m + 0.5 d_p u, gives Pe = vL/D_L of
order 1 on a bed 6.35 mm tall (one to two pellets deep), where the correlation has
no business being applied. The authors' COMSOL model uses the Bruggeman closure
D_e = eps^1.5 D_m (SI Eq. S2-S3), about ten times less dispersion. This script runs
the primary configuration under that closure, and under it with the step-minimum
CSFR rate, and reports the same descriptive quantities. It is a sensitivity chosen
AFTER the data were seen; it is not a fit and may not be reported as the result.

    python compare_lassitter_posthoc.py
"""
from __future__ import annotations

import json
import os

import numpy as np

from compare_lassitter import (DIGITISED, HORIZON_MIN, N_SNAP, RH_IN, T_K, describe,
                               load_digitised, physics, solve)
from fetch_real_mof_data import rh_to_conc

D_M_SI = 2.19e-5      # their Table S8 diffusivity of water in air


def main():
    eff, com, inl = load_digitised()
    c_in = rh_to_conc(RH_IN, T_K)
    base = json.load(open("results/lassitter_comparison.json"))
    out = {"note": "POST-HOC sensitivity, chosen after seeing the pre-registered result; not a fit, not the result",
           "runs": {}}
    curves = {}
    for label, k, closure in (("bruggeman_k0.2", 0.20, "bruggeman"), ("bruggeman_k0.011", 0.011, "bruggeman"),
                              ("ruthven_dp3mm_k0.2 (primary, for reference)", 0.20, "ruthven")):
        p = physics(k, 3e-3, 1e4, 1000.0)
        if closure == "bruggeman":
            p.D_L = p.eps_t ** 1.5 * D_M_SI
        pe = p.v * p.L / p.D_L
        t_min, frac, T_exit = solve(p, c_in, 500)
        d = describe(t_min, frac, eff)
        d.update({"D_L": float(p.D_L), "Pe": float(pe), "k_LDF": k, "closure": closure})
        out["runs"][label] = d
        curves[label] = (t_min, frac)
        print(f"  {label:<44} D_L {p.D_L:.2e} Pe {pe:6.2f} | t05 {d['t05_min']:6.1f} t50 {d['t50_min']:6.1f} "
              f"t95 {d['t95_min']:6.1f} | plateau {d['plateau_150_250_frac']:.3f} | nRMSE {d['nrmse_vs_effluent']:.4f}")
    print(f"  experiment: t05 {base['experiment']['t05_min']:.0f} t50 {base['experiment']['t50_min']:.0f} "
          f"t95 {base['experiment']['t95_min']:.0f}, plateau {base['experiment']['plateau_150_250_frac']:.3f}; "
          f"authors' COMSOL nRMSE {base['comsol_line']['nrmse_vs_effluent']:.4f}")
    json.dump(out, open("results/lassitter_comparison_posthoc.json", "w"), indent=2)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42, "font.size": 9, "axes.grid": True,
                         "grid.alpha": 0.25, "axes.spines.top": False, "axes.spines.right": False,
                         "legend.frameon": False})
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    t_min, frac = curves["ruthven_dp3mm_k0.2 (primary, for reference)"]
    ax.plot(t_min, frac * RH_IN * 100, color="#3b6ea5", lw=2.0, label="pre-registered primary (Ruthven D_L, Pe ≈ 1)")
    t_min, frac = curves["bruggeman_k0.2"]
    ax.plot(t_min, frac * RH_IN * 100, color="#e08b3a", lw=1.6, ls="-.",
            label="POST-HOC: authors' Bruggeman D_e (Pe ≈ 11), k = 0.2")
    t_min, frac = curves["bruggeman_k0.011"]
    ax.plot(t_min, frac * RH_IN * 100, color="#6a994e", lw=1.2, ls=":",
            label="POST-HOC: Bruggeman D_e, k = 0.011 (step minimum)")
    ax.plot(com[:, 0], com[:, 1], color="crimson", lw=1.0, ls="--", label="authors' COMSOL (fitted CSFR kinetics)")
    ax.plot(eff[:, 0], eff[:, 1], "o", ms=4, mfc="none", mec="k", label="experiment, effluent (digitised)")
    ax.set_xlim(0, HORIZON_MIN); ax.set_ylim(0, 36)
    ax.set_xlabel("time (min)"); ax.set_ylabel("% RH")
    ax.set_title("post-hoc dispersion sensitivity — labelled as such, not the result")
    ax.legend(fontsize=7, loc="lower right")
    for ext in ("png", "pdf"):
        fig.savefig(f"figures/Fig7b_anchor_posthoc.{ext}", dpi=600, bbox_inches="tight")
    print("wrote results/lassitter_comparison_posthoc.json and figures/Fig7b_anchor_posthoc.png/.pdf")


if __name__ == "__main__":
    main()
