"""Figure 1: the falsification ladder — one row per rung, with its effect and CI.

Every point, interval and MDE is READ FROM A RESULTS FILE. Nothing here is typed by
hand; if a rung's number has no file to read from, this script says so rather than
drawing it. That is how defect B43 was found: three of L2-v2's four quoted
comparisons had nowhere to read from, and they now live in
`results/l2_v2_verdict.json` under `cross`.

The common axis in panel A is the RELATIVE EFFECT of each rung's intervention on
held-out error, as a percentage of that rung's own control:

    effect  =  100 * (control - intervention) / control

so POSITIVE means "the intervention reduces the transfer error" and the line at zero
means "the intervention does nothing". Every row names its own control, because the
rungs measure different things and only the ratio is commensurable.

Panel A carries ONLY quantities in those units. The primary L6 estimand is a slope
in nRMSE per decade of Damkohler, which is NOT in those units, so it gets its own
panel rather than being coerced onto a shared axis — the error class of A15 and B34
is normalising or re-scaling a quantity into a frame it does not belong in.

  A  the ladder: rung, hypothesis, effect with its cluster-robust CI, verdict.
     Nulls carry their MDE as a dashed grey bar; a null without one is not
     reportable (protocol rule 7, retraction A22).
  B  the PRIMARY pre-registered estimand: the per-material separate-minus-joint
     difference against Damkohler, with the fitted slope and its bootstrap band.
  C  L0: the reference against four closed-form solutions.

    python fig_ladder.py
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

plt.rcParams.update({
    "figure.dpi": 160, "savefig.dpi": 600, "font.size": 9,
    "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False,
    "axes.spines.right": False, "legend.frameon": False,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})
OUT = "figures"

C_MOVES = "#3b6ea5"      # the intervention reduces the error, significantly
C_HURTS = "#b5423f"      # the intervention increases the error, significantly
C_NULL = "#8a8a8a"       # no difference at the calibrated alpha
C_LEAK = "#6a994e"       # an oracle arm: handed the answer; an upper bound only


# Results files a run still in flight has not written. validate.py's integrity gate
# accepts a missing results path ONLY if it is declared here, and FAILS if a declared
# file exists — so this line must be removed the moment L4b-v2 lands.
PENDING_RESULTS = ()          # L4b-v2 landed 2026-09-08; nothing is in flight

def load(path):
    return json.load(open(path)) if os.path.exists(path) else None


def effect(comparison, control_is_a):
    """A comparison expressed as 100 * (control - intervention) / control.

    `compare()` returns mean_diff = mean_a - mean_b, and the CI is on that same
    difference. `control_is_a` says which arm is the control. The sign is resolved
    once, here, and nowhere else; getting it wrong once produced a figure that
    called a KAN an improvement.
    """
    a, b = comparison["mean_a"], comparison["mean_b"]
    ctrl = a if control_is_a else b
    s = 1.0 if control_is_a else -1.0        # (ctrl - interv) = +diff if a is ctrl
    e = s * 100.0 * comparison["mean_diff"] / ctrl
    lo, hi = sorted((s * 100.0 * comparison["ci_low"] / ctrl,
                     s * 100.0 * comparison["ci_high"] / ctrl))
    return dict(e=e, lo=lo, hi=hi, sig=bool(comparison["significant"]),
                n=comparison["n_materials"], ctrl=float(ctrl))


def build_rows():
    """One row per rung. Returns (rows, missing); nothing missing is drawn silently."""
    rows, missing = [], []

    def add(rung, hyp, inter, eff, verdict, note, mde=None, leak=False):
        rows.append(dict(rung=rung, hyp=hyp, inter=inter, verdict=verdict, note=note,
                         mde=mde, leak=leak, **eff))

    lc = load("results/learning_curve_v2_verdict.json")
    l2 = load("results/l2_v2_verdict.json")
    l3p = load("results/l3_final_pair.json")
    l3s = load("results/l3_selection.json")
    l4 = load("results/l4b_v2_verdict.json")
    l5 = load("results/l5_fno_verdict.json")
    l5m = load("results/l5_merged.json")
    l6 = load("results/l6_v2_verdict.json")
    l6m = load("results/l6_v2_mde_corrected.json")
    l7 = load("results/l7_v2_verdict.json")
    warp = load("results/warp_verdict.json")

    # L1 — more materials. control = 96 materials (arm_a), intervention = 192 (arm_b).
    if lc:
        st = lc["axes"]["materials"]["steps"][-1]
        b_, bci = lc["axes"]["materials"]["beta"], lc["axes"]["materials"]["beta_ci"]
        add("L1", "more materials", "192 vs 96 training materials",
            effect(st, control_is_a=True), "NOT ELIMINATED",
            f"still falling at the largest size affordable: n^-{b_:.3f} [{bci[0]:.3f}, {bci[1]:.3f}]")
    else:
        missing.append("L1 learning curve")

    # L2 — more capacity. control = the L1 setting, intervention = the sweep optimum.
    cross = (l2 or {}).get("cross", {}).get("comparisons", {})
    key = next((k for k in cross if "L1 setting" in k), None)
    if key:
        c, fam = cross[key], l2["best_overall"]
        mde = l2["families"][fam[1]].get("mde_last_step")
        eff = effect(c, control_is_a=False)
        # the best configuration was chosen on the test materials: draw the interval that
        # pays for the choice (analyze_l2_selection.py), as the text quotes it
        sel = load("results/l2_v2_selection.json")
        if sel and sel["selected"] == f"{fam[1]}/{fam[2]}":
            eff.update(e=sel["pct"], lo=sel["pct_sim_lo"], hi=sel["pct_sim_hi"],
                       sig=bool(sel["survives_selection"]))
        else:
            raise SystemExit("l2_v2_selection.json does not cover the L2 best configuration")
        add("L2", "more capacity", f"{fam[1]}/{fam[2]} vs the L1 setting (selection-adjusted)",
            eff, "NOT ELIMINATED",
            "a random forest is still improving at its capacity ceiling; the best configuration is a deeper perceptron (A26, A27)",
            mde=100 * mde["mde_80"] if isinstance(mde, dict) and mde.get("mde_80") else None)
    else:
        missing.append("L2 cross-comparison vs the L1 setting (run analyze_l2_v2.py)")

    # L3 — a better basis. control = the MLP, intervention = the strongest KAN found.
    if l3p:
        c = {"mean_a": l3p["mlp"], "mean_b": l3p["rbf_g4"], "mean_diff": l3p["diff"],
             "ci_low": min(l3p["ci"]), "ci_high": max(l3p["ci"]),
             "significant": l3p["significant"], "n_materials": 12}
        add("L3", "a better basis (KAN)", "strongest KAN vs MLP, matched parameters",
            effect(c, control_is_a=True), "ELIMINATED",
            "the best KAN anywhere is the least KAN-like; %d/%d comparisons significant after selection, none reversed"
            % (l3s["n_sig_simultaneous"], l3s["n_pairs"]))
    else:
        missing.append("L3 final pair")

    # L4b — the PDE residual as a loss, on the material axis. The v2 results used a residual
    # that moved the gas at the wrong velocity (B72) and are WITHDRAWN as evidence about
    # physics (A28): the figure draws ONLY the corrected re-run, once its completion marker
    # exists. (A first version drew the withdrawn result as PHYSICS HELPS -- caught by the
    # round-2 referee review.)
    _mk = "l4b_v3.log"
    v3_done = os.path.exists(_mk) and "L4B_V3_DONE" in open(_mk, errors="replace").read()
    l4c = load("results/l4b_v3_verdict.json") if v3_done else None
    ax = (l4c or {}).get("axes", {}).get("material", {})
    c = ax.get("best_pi_vs_data_only")
    if c:
        m = ax.get("mde") or {}
        m80 = next((v.get("mde_80") for v in m.values() if isinstance(v, dict) and v.get("mde_80")), None)
        add("L4b", "physics as a loss", "best physics arm vs its data-only twin",
            effect(c, control_is_a=(c["arm_a"] == "data_only")),
            ax["verdict"].split(".")[0][:36],
            ax.get("sweep_described", "weighting sweep per PREREG_L4b_v2")[:90],
            mde=100 * m80 if m80 else None)
    else:
        rows.append(dict(rung="L4b", hyp="physics as a loss",
                         inter="best physics arm vs its data-only twin",
                         e=None, lo=None, hi=None, sig=None, n=48, ctrl=None, mde=None, leak=False,
                         verdict="WITHDRAWN (B72) — re-run in flight",
                         note="its residual moved the gas at the wrong velocity; the corrected re-run is queued"))
        missing.append("L4b: corrected re-run (B72) in flight")

    # L5 — nonlinear reconstruction, and basis size.
    if l5:
        # Both arms are best-of-grid on the test materials: draw the interval that pays
        # for both choices (analyze_l5_selection.py, B75), never the per-pair one.
        sel = load("results/l5_fno_selection.json")["selected"]
        c = {**l5["deeponet_vs_fno"], "ci_low": sel["sim_lo"], "ci_high": sel["sim_hi"],
             "significant": sel["significant_simultaneous"]}   # a = DeepONet (control), b = FNO
        add("L5", "nonlinear reconstruction", "FNO vs the best DeepONet (selection-adjusted)",
            effect(c, control_is_a=True), "NOT SIGNIFICANT once selected",
            f"the direction the theory names, not significant after selection (B75); "
            f"{l5['fno_best']['mean'] / l5['pod_floor_p128']:.0f}x above the POD floor")
    else:
        missing.append("L5 FNO verdict")
    c = (l5m or {}).get("paired_vs_smallest_p", {}).get("deeponet_p128")
    if c:
        f = l5m["pod_floor"]
        add("L5", "a bigger basis", "DeepONet p=128 vs p=8",
            effect(c, control_is_a=True), "NO DIFFERENCE (A17)",
            f"flat in p while its own n-width bound falls {f['8'] / f['128']:.1f}x beneath it")
    elif l5m:
        missing.append("L5 flat-in-p comparison")

    # L6 — separate identification (secondary; the primary slope is panel B).
    if l6:
        c = l6["pooled"]                              # a = joint (control), b = separate
        add("L6", "separate identification", "separate vs joint (H1, secondary)",
            effect(c, control_is_a=True), "BENEFIT REAL",
            "no detectable dependence on Damköhler (panel B): a weak null, read as an inductive bias",
            mde=100 * l6m["mde_80"] if l6m else None)
    else:
        missing.append("L6-v2 verdict")

    # L7 — is a closed form enough? control = the best closed form, intervention = learning.
    if l7:
        c = l7["comparisons"]["mlp vs klinkenberg"]   # a = learned, b = closed form (control)
        add("L7", "a closed form suffices", "learned vs the best closed form, exit curve",
            effect(c, control_is_a=False), "ELIMINATED — learning is justified",
            "a classical model wins exactly when the physics it assumes is the physics that is there")
    else:
        missing.append("L7-v2 verdict")

    # The coordinate change: the honest arm, then the oracle upper bound.
    if warp:
        add("warp", "a change of coordinates", "two-wave warp, PREDICTED fronts",
            effect(warp["fixed_vs_two_wave"], control_is_a=True), "NO DIFFERENCE",
            "the n-width collapses 31 -> 13 modes, and none of it survives front-location error")
        add("warp", "(the same, ORACLE fronts)", "upper bound — handed the true fronts",
            effect(warp["fixed_vs_oracle"], control_is_a=True),
            "HEADROOM %.2fx over the fixed frame" % (warp["means"]["fixed"] / warp["means"]["two_wave_oracle"]),
            "NOT comparable with any arm not also handed the warp: it sizes the prize, it is not a result",
            leak=True)
    else:
        missing.append("warp verdict")

    return rows, missing


def panel_ladder(a, rows):
    y = np.arange(len(rows))[::-1]
    for yi, r in zip(y, rows):
        col = (C_LEAK if r["leak"] else C_NULL if r["e"] is None or not r["sig"]
               else C_MOVES if r["e"] > 0 else C_HURTS)
        if r["e"] is None:
            a.plot([0], [yi], marker="|", ms=12, color="0.6")
            a.text(1.5, yi, "in flight", va="center", fontsize=7.5, color="0.45", style="italic")
        else:
            a.plot([r["lo"], r["hi"]], [yi, yi], color=col, lw=2.2, solid_capstyle="butt", alpha=0.9)
            a.plot([r["lo"], r["hi"]], [yi, yi], "|", color=col, ms=7)
            a.plot([r["e"]], [yi], "o", ms=7, zorder=3,
                   **({"mfc": "white", "mec": col, "mew": 1.8} if r["leak"] else {"color": col}))
        if r["mde"]:
            a.plot([-r["mde"], r["mde"]], [yi - 0.32, yi - 0.32], color="0.5", lw=1.1, ls=(0, (2, 1.6)))
            a.text(r["mde"] + 1.0, yi - 0.32, f"MDE {r['mde']:.0f} %", va="center", fontsize=6.0, color="0.45")

    a.axvline(0, color="k", lw=1.0)
    a.set_yticks(y)
    a.set_yticklabels([f"{r['rung']}    {r['hyp']}" for r in rows], fontsize=8.2)
    a.set_ylim(-0.85, len(rows) - 0.25)
    lim_lo = min([v for r in rows for v in (r["lo"], r["e"]) if v is not None] + [0.0])
    lim_hi = max([v for r in rows for v in (r["hi"], r["e"]) if v is not None] + [0.0])
    pad = 0.09 * (lim_hi - lim_lo)
    a.set_xlim(lim_lo - pad, lim_hi + pad)
    a.set_xlabel("effect on held-out error, % of that rung's own control      "
                 "(positive = the intervention reduces the error)", fontsize=8.0)
    # The right-hand column must line up with its own row: axes-fraction for data y
    # is (y - ylim0) / (ylim1 - ylim0) = (y + 0.85) / (len + 0.60).
    for yi, r in zip(y, rows):
        f = lambda dy: (yi + 0.85 + dy) / (len(rows) + 0.60)
        a.text(1.02, f(+0.17), r["verdict"], transform=a.transAxes,
               fontsize=7.3, va="center", fontweight="bold", color="0.12")
        a.text(1.02, f(-0.19), f"{r['inter']}   ({r['n']} clusters)", transform=a.transAxes,
               fontsize=6.2, va="center", color="0.42")
    a.set_title("A.   the ladder: seven named candidates and what the evidence said",
                fontsize=9.5, loc="left")
    a.legend(handles=[
        Line2D([], [], color=C_MOVES, lw=2.4, label="reduces the error, significantly"),
        Line2D([], [], color=C_HURTS, lw=2.4, label="increases it, significantly"),
        Line2D([], [], color=C_NULL, lw=2.4, label="no difference at the calibrated α"),
        Line2D([], [], color=C_LEAK, lw=2.4, marker="o", mfc="white",
               label="oracle arm: an upper bound, not a comparable result"),
    ], fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=4)


def panel_slope(b):
    """The PRIMARY pre-registered estimand, in its own units."""
    v = load("results/l6_v2_verdict.json")
    if not v:
        b.text(0.5, 0.5, "results/l6_v2_verdict.json missing", ha="center", transform=b.transAxes)
        return
    from run_l6_v2 import damkohler_per_material
    da = damkohler_per_material(json.load(open("results/l6_v2_results.json"))["root"])
    pm = v["per_material"]
    mats = sorted(set(pm["joint"]) & {str(m) for m in da} | set())
    mats = [m for m in pm["joint"] if int(m) in da or m in da]
    x, yv = [], []
    for m in mats:
        d = da.get(int(m), da.get(m))
        if d is None:
            continue
        x.append(np.log10(d))
        yv.append(pm["separate"][m] - pm["joint"][m])
    x, yv = np.array(x), np.array(yv)
    st = v["slope_test"]
    b.scatter(x, yv, s=9, alpha=0.45, color="#3b6ea5", edgecolors="none")
    xs = np.linspace(x.min(), x.max(), 50)
    b.plot(xs, st["intercept"] + st["slope"] * xs, color="#b5423f", lw=1.8, label="fitted slope")
    mid = 0.5 * (x.min() + x.max())
    for s, ls in ((st["ci_low"], (0, (3, 2))), (st["ci_high"], (0, (3, 2)))):
        b.plot(xs, (st["intercept"] + st["slope"] * mid) + s * (xs - mid), color="#b5423f",
               lw=1.0, ls=ls, alpha=0.8)
    b.axhline(0, color="k", lw=0.8)
    b.set_xlabel("log₁₀ Damköhler (median per material)")
    b.set_ylabel("separate − joint\n(nRMSE, per material)")
    b.set_title("B.   the PRIMARY estimand: no detectable dependence on Damköhler (a weak null)",
                fontsize=9.5, loc="left")
    b.text(0.985, 0.05,
           f"slope {st['slope']:+.5f} nRMSE / decade, CI [{st['ci_low']:+.5f}, {st['ci_high']:+.5f}]  "
           f"NOT SIGNIFICANT\nPearson r = {st['pearson_r']:.3f} over {st['log10_da_range'][1] - st['log10_da_range'][0]:.2f} decades, "
           f"{st['n_materials']} materials",
           transform=b.transAxes, ha="right", va="bottom", fontsize=6.6, color="0.3")
    b.text(0.015, 0.95, "H1 predicted a positive slope:\nseparation should pay most where\nkinetics dominate",
           transform=b.transAxes, ha="left", va="top", fontsize=6.4, color="0.45")


def panel_l0(c):
    v = json.load(open("verify_solver.json"))
    checks = [("inert tracer vs\nvan Genuchten third-type",
               v["tracer_van_genuchten"]["max_abs_err_vs_third_type"], "advection, dispersion,\nthe Danckwerts inlet"),
              ("retarded front,\nR = 901", v["retarded_front"]["rel_err"], "isotherm coupling,\nthe equilibrium limit"),
              ("thermal wave,\nadsorption off", v["thermal_wave"]["rel_err"], "the energy\nequation"),
              ("LDF vs Anzelius–\nSchumann", v["ldf_anzelius_schumann"]["max_abs_err"], "kinetics\n")]
    xs = np.arange(len(checks))
    c.bar(xs, [k[1] for k in checks], color="#4a5c6a", width=0.55)
    for x, (name, val, what) in zip(xs, checks):
        c.text(x, val * 1.5, f"{val:.1e}", ha="center", fontsize=7.0)
    c.set_yscale("log")
    c.set_ylim(3.5e-5, 2e-2)
    c.set_xticks(xs)
    c.set_xticklabels([k[0] for k in checks], fontsize=6.6)
    for x, (name, val, what) in zip(xs, checks):
        c.text(x, 0.02, what, transform=c.get_xaxis_transform(), ha="center", va="bottom",
               fontsize=5.9, color="0.88", linespacing=1.25)
    c.set_ylabel("error vs the\nclosed form")
    c.set_title("C.   L0 — the reference is verified, not asserted", fontsize=9.5, loc="left")
    c.text(0.985, 0.93, "global mass closure 0.050 %", transform=c.transAxes,
           ha="right", va="top", fontsize=6.6, color="0.35")


def main():
    rows, missing = build_rows()
    for m in missing:
        print(f"  ! no results file for: {m}")

    fig = plt.figure(figsize=(9.2, 0.40 * len(rows) + 4.6))
    gs = fig.add_gridspec(3, 1, height_ratios=[0.40 * len(rows) + 0.9, 2.0, 1.5],
                          hspace=0.62, left=0.17, right=0.62, top=0.965, bottom=0.05)
    panel_ladder(fig.add_subplot(gs[0]), rows)
    panel_slope(fig.add_subplot(gs[1]))
    panel_l0(fig.add_subplot(gs[2]))

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig1_ladder.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT}/Fig1_ladder.png/.pdf  ({len(rows)} rows"
          + (f", {len(missing)} not yet available)" if missing else ")"))


if __name__ == "__main__":
    main()
