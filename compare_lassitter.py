"""The reference solver against Lassitter et al. (2024) Fig. 10. Design: PREREG_LASSITTER.md.

No parameter is fitted. Inputs are the cited MOF-303 isotherm, the SI's bed and
operating values, and the declared bands for the three quantities the source does
not give (k_LDF, pellet size for dispersion, thermal coupling).

    python compare_lassitter.py
"""
from __future__ import annotations

import csv
import json
import os
import time

import numpy as np

from fetch_real_mof_data import get_mof303_physics, rh_to_conc
from metrics import breakthrough_times
from solver_fd import generate_breakthrough_data

RH_IN = 0.328
T_K = 298.15
HORIZON_MIN = 600.0
N_SNAP = 1200
KS = (0.011, 0.05, 0.20)
DPS = (1e-3, 3e-3, 5e-3)
THERMAL = (("isothermal", 1e4, 1000.0), ("hw10_cps900", 10.0, 900.0),
           ("hw10_cps1000", 10.0, 1000.0), ("hw10_cps2400", 10.0, 2400.0))
PRIMARY = (0.20, 3e-3, "isothermal")
DIGITISED = "refs/Lassitter2024_fig10_digitised.csv"


def physics(k, d_p, h_w, c_ps):
    p = get_mof303_physics()
    p.L = 0.00635
    p.D_in = 0.0381
    p.v = 0.0098062
    p.T_in = p.T_w = T_K
    p.eps_t = 0.4
    p.rho_p = 429.58 / (1.0 - p.eps_t)
    p.d_p = d_p
    p.D_L = 0.7 * 2.5e-5 + 0.5 * d_p * (p.v / p.eps_t)      # Ruthven, as in the datasets
    p.k_LDF = k
    p.h_w = h_w
    p.C_ps = c_ps
    return p


def solve(p, c_in, n_z):
    z, t, y = generate_breakthrough_data(p, N_z=n_z, t_final=HORIZON_MIN * 60.0, c_in=c_in,
                                         T_in=T_K, n_snapshots=N_SNAP, verbose=False)
    n = len(z)
    return t / 60.0, y[n - 1, :] / c_in, y[3 * n - 1, :]         # minutes, exit c/c_in, exit T


def load_digitised():
    rows = list(csv.DictReader(open(DIGITISED)))
    eff = np.array(sorted((float(r["t_min"]), float(r["rh_percent"])) for r in rows if r["series"] == "effluent_circle"))
    com = np.array(sorted((float(r["t_min"]), float(r["rh_percent"])) for r in rows if r["series"] == "comsol_model_line"))
    inl = np.array(sorted((float(r["t_min"]), float(r["rh_percent"])) for r in rows if r["series"] == "inlet_square"))
    return eff, com, inl


def describe(t_min, frac, eff):
    """The pre-declared descriptive quantities for one exit curve (fraction of inlet)."""
    lev = breakthrough_times(frac, t_min)                      # first crossings, minutes
    win = (t_min >= 150) & (t_min <= 250)
    plateau = float(frac[win].mean())
    # an intermediate plateau: effluent between 0.15 and 0.45 of the inlet for >= 60 min before the shock
    inside = (frac > 0.15) & (frac < 0.45)
    dt = t_min[1] - t_min[0]
    longest = 0; run = 0
    for v in inside:
        run = run + 1 if v else 0
        longest = max(longest, run)
    model_at_pts = np.interp(eff[:, 0], t_min, frac) * RH_IN * 100.0
    nrmse = float(np.sqrt(np.mean((model_at_pts - eff[:, 1]) ** 2)) / (RH_IN * 100.0))
    return {"t05_min": lev[0.05], "t50_min": lev[0.50], "t95_min": lev[0.95],
            "plateau_150_250_frac": plateau, "has_plateau": bool(longest * dt >= 60.0),
            "plateau_duration_min": float(longest * dt), "nrmse_vs_effluent": nrmse}


def main():
    t0 = time.time()
    eff, com, inl = load_digitised()
    c_in = rh_to_conc(RH_IN, T_K)
    print(f"feed {RH_IN * 100:.1f} % RH at {T_K} K -> c_in {c_in:.4f} mol/m3 (SI: 0.42212)")

    # the experiment, on the same terms
    tt = np.linspace(0, HORIZON_MIN, N_SNAP)
    exp_frac = np.interp(tt, eff[:, 0], eff[:, 1]) / (RH_IN * 100.0)
    exp_desc = describe(tt, exp_frac, eff)
    com_frac = np.interp(tt, com[:, 0], com[:, 1]) / (RH_IN * 100.0)
    com_desc = describe(tt, com_frac, eff)
    print(f"experiment: t05 {exp_desc['t05_min']:.0f} t50 {exp_desc['t50_min']:.0f} t95 {exp_desc['t95_min']:.0f} min; "
          f"plateau {exp_desc['plateau_150_250_frac']:.3f} of inlet; inlet drift {inl[:, 1].min():.1f}-{inl[:, 1].max():.1f} % RH")
    print(f"authors' COMSOL line: t50 {com_desc['t50_min']:.0f} min, plateau {com_desc['plateau_150_250_frac']:.3f}, "
          f"nRMSE vs points {com_desc['nrmse_vs_effluent']:.4f}")

    out = {"design": "PREREG_LASSITTER.md", "rh_in": RH_IN, "T_K": T_K, "c_in": float(c_in),
           "experiment": exp_desc, "comsol_line": com_desc, "primary": list(PRIMARY), "runs": {}}
    p0 = physics(0.20, 3e-3, 1e4, 1000.0)
    print(f"stoichiometric time at the feed: {p0.stoichiometric_time(c_in, T_K) / 60:.0f} min; "
          f"MTZ estimate: {p0.mtz_width(c_in, T_K)}")

    # grid convergence, primary configuration
    conv = {}
    for nz in (250, 500, 1000):
        t_min, frac, _ = solve(physics(*PRIMARY[:2], 1e4, 1000.0), c_in, nz)
        conv[nz] = frac
        print(f"  N_z {nz}: t50 {breakthrough_times(frac, t_min)[0.5]:.1f} min  [{time.time() - t0:.0f}s]")
    out["grid_convergence_max_abs_change_frac"] = {
        "250_vs_500": float(np.max(np.abs(conv[250] - conv[500]))),
        "500_vs_1000": float(np.max(np.abs(conv[500] - conv[1000])))}
    print(f"  grid: max|Δ| 250→500 {out['grid_convergence_max_abs_change_frac']['250_vs_500']:.4f}, "
          f"500→1000 {out['grid_convergence_max_abs_change_frac']['500_vs_1000']:.4f}")

    curves = {}
    for k in KS:
        for d_p in DPS:
            for name, h_w, c_ps in THERMAL:
                key = f"k{k:g}_dp{d_p * 1e3:g}mm_{name}"
                t_min, frac, T_exit = solve(physics(k, d_p, h_w, c_ps), c_in, 500)
                d = describe(t_min, frac, eff)
                d["T_exit_peak_rise_K"] = float(T_exit.max() - T_K)
                d["primary"] = (k, d_p, name) == PRIMARY
                out["runs"][key] = d
                curves[key] = (t_min, frac)
                print(f"  {key:<28} t05 {d['t05_min']:6.1f} t50 {d['t50_min']:6.1f} t95 {d['t95_min']:6.1f} | "
                      f"plateau {d['plateau_150_250_frac']:.3f} ({'yes' if d['has_plateau'] else 'no'}) | "
                      f"nRMSE {d['nrmse_vs_effluent']:.4f} | ΔT {d['T_exit_peak_rise_K']:.1f} K"
                      + ("   <- PRIMARY" if d["primary"] else ""), flush=True)

    pk = f"k{PRIMARY[0]:g}_dp{PRIMARY[1] * 1e3:g}mm_{PRIMARY[2]}"
    pr = out["runs"][pk]
    ok_plateau = pr["has_plateau"]
    ok_t50 = abs(pr["t50_min"] / exp_desc["t50_min"] - 1) <= 0.20
    ok_level = 1 / 1.5 <= pr["plateau_150_250_frac"] / max(exp_desc["plateau_150_250_frac"], 1e-9) <= 1.5
    verdict = ("REPRODUCES the experiment under the pre-declared reading (plateau present, t50 within 20 %, "
               "plateau level within 1.5x), with no parameter fitted" if (ok_plateau and ok_t50 and ok_level) else
               f"DISCREPANCY under the pre-declared reading: plateau {'present' if ok_plateau else 'ABSENT'}, "
               f"t50 {'within' if ok_t50 else 'OUTSIDE'} 20 % ({pr['t50_min']:.0f} vs {exp_desc['t50_min']:.0f} min), "
               f"plateau level {'within' if ok_level else 'OUTSIDE'} 1.5x ({pr['plateau_150_250_frac']:.3f} vs "
               f"{exp_desc['plateau_150_250_frac']:.3f})")
    closest = min(out["runs"], key=lambda k_: out["runs"][k_]["nrmse_vs_effluent"])
    print(f"\nPRIMARY ({pk}): {verdict}")
    print(f"closest band member by nRMSE (a SENSITIVITY, not a fit): {closest} "
          f"nRMSE {out['runs'][closest]['nrmse_vs_effluent']:.4f}")
    out["verdict_primary"] = verdict
    out["closest_band_member"] = closest
    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/lassitter_comparison.json", "w"), indent=2)

    # figure: experiment, the authors' line, the primary run, and the band
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42, "font.size": 9, "axes.grid": True,
                         "grid.alpha": 0.25, "axes.spines.top": False, "axes.spines.right": False,
                         "legend.frameon": False})
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    for key, (t_min, frac) in curves.items():
        if key != pk:
            ax.plot(t_min, frac * RH_IN * 100, color="0.8", lw=0.6, zorder=1)
    ax.plot([], [], color="0.8", lw=0.6, label="declared band (k, d_p, thermal), no fitting")
    t_min, frac = curves[pk]
    ax.plot(t_min, frac * RH_IN * 100, color="#3b6ea5", lw=2.0, zorder=3, label="this solver, cited MOF-303, primary")
    ax.plot(com[:, 0], com[:, 1], color="crimson", lw=1.0, ls="--", zorder=2, label="authors' COMSOL (fitted CSFR kinetics)")
    ax.plot(eff[:, 0], eff[:, 1], "o", ms=4, mfc="none", mec="k", zorder=4, label="experiment, effluent (digitised)")
    ax.plot(inl[:, 0], inl[:, 1], "s", ms=3, mfc="none", mec="0.5", zorder=4, label="experiment, inlet")
    ax.set_xlim(0, HORIZON_MIN); ax.set_ylim(0, 36)
    ax.set_xlabel("time (min)"); ax.set_ylabel("% RH")
    ax.set_title("MOF-303 bed, 6.35 mm, 32.8 % RH, 298 K — Lassitter et al. 2024 Fig. 10")
    ax.legend(fontsize=7, loc="lower right")
    os.makedirs("figures", exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"figures/Fig7_anchor.{ext}", dpi=600, bbox_inches="tight")
    print(f"wrote results/lassitter_comparison.json and figures/Fig7_anchor.png/.pdf  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
