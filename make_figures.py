"""Figures. Every series is computed from data or from a loaded model — never drawn.

`validate.py` enforces two rules on this file and any other that imports pyplot:

  * no synthesised series may be labelled as a model prediction
  * anything labelling a model curve must call `load_state_dict`

Those rules exist because the first version of this project shipped a
"publication-ready" figure whose MLP-failure curve was `c_true + 0.15*sin(t/50)`
and whose PIKAN-success curve was `c_true + N(0, 0.001)` (retraction A1). The
figures below either plot the reference solution, plot analytic functions, or
plot a checkpoint's actual output — nothing else.

Usage
-----
    python make_figures.py               # all figures that have inputs available
    python make_figures.py --only fig1
"""
from __future__ import annotations

import argparse
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from fetch_real_mof_data import get_mof303_physics, rh_to_conc
from isotherm import q_star_np
from solver_fd import AdsorptionPhysicsConfig

OUT = "figures"
plt.rcParams.update({
    "figure.dpi": 160, "savefig.dpi": 300, "font.size": 9,
    "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False,
    "axes.spines.right": False, "legend.frameon": False,
})


def _save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {OUT}/{name}.png/.pdf")


# ─────────────────────────────────────────────────────────────────────────────

def fig_isotherm():
    """Why the isotherm form is the whole story for AWH."""
    phys = get_mof303_physics()
    T = phys.T_in
    rh = np.linspace(1e-4, 0.95, 2000)
    c = rh_to_conc(rh, T)
    q_v = q_star_np(c, np.full_like(c, T), phys)

    # Type I comparison at MATCHED saturation capacity and matched dH
    import copy
    lang = copy.deepcopy(phys)
    lang.isotherm_n = 1.0
    lang.henry_fraction = 1.0
    lang.b0 = 1.0 / rh_to_conc(0.15, T) / np.exp(-lang.delta_H / (8.314 * T))
    lang.b_H0 = lang.b0
    q_l = q_star_np(c, np.full_like(c, T), lang)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.4, 3.2))
    ax1.plot(100 * rh, q_v, lw=2, label="Type V (Do–Do, this work)")
    ax1.plot(100 * rh, q_l, lw=2, ls="--", label="Type I (Langmuir)")
    ax1.set_xlabel("relative humidity (%)")
    ax1.set_ylabel("q* (mol kg$^{-1}$)")
    ax1.set_title("A. Equilibrium uptake")
    ax1.legend(loc="lower right")

    ax2.plot(100 * rh, np.gradient(q_v, rh), lw=2)
    ax2.plot(100 * rh, np.gradient(q_l, rh), lw=2, ls="--")
    ax2.set_xlabel("relative humidity (%)")
    ax2.set_ylabel("dq*/d(RH)  (mol kg$^{-1}$)")
    ax2.set_title("B. Uptake gradient — the working-capacity driver")
    ax2.set_yscale("log")
    ax2.annotate("Type I peaks at RH→0:\nno usable working capacity",
                 xy=(3, np.gradient(q_l, rh)[40]), xytext=(25, 3),
                 arrowprops=dict(arrowstyle="->", lw=0.8), fontsize=8)
    _save(fig, "Fig1_isotherm_form")


def fig_ground_truth():
    """The verified reference solution both datasets are built from."""
    specs = [("data/synthetic_breakthrough.npz", "generic Type I sorbent"),
             ("data/mof303_breakthrough.npz", "MOF-303-like, Type V")]
    avail = [(p, lab) for p, lab in specs if os.path.exists(p)]
    if not avail:
        print("  skip: no datasets")
        return
    fig, axes = plt.subplots(2, len(avail), figsize=(4.6 * len(avail), 6.2), squeeze=False)
    fig.subplots_adjust(hspace=0.45)
    for k, (path, label) in enumerate(avail):
        d = np.load(path)
        z, t, y = d["z"], d["t"], d["y"]
        n = len(z)
        c_in = float(d["c_in"])
        c, q, T = y[:n] / c_in, y[n:2 * n], y[2 * n:]

        ax = axes[0][k]
        ax.plot(t / 3600, c[-1], lw=2, color="k")
        ax.set_xlabel("time (h)")
        ax.set_ylabel("$c/c_{in}$ at outlet")
        ax.set_title(f"{label}\nbreakthrough curve")
        ax.set_ylim(-0.02, 1.05)

        ax = axes[1][k]
        im = ax.pcolormesh(t / 3600, z * 1e3, q, shading="auto", cmap="viridis")
        ax.set_xlabel("time (h)")
        ax.set_ylabel("z (mm)")
        ax.set_title("solid loading q(z,t)  (mol kg$^{-1}$)")
        fig.colorbar(im, ax=ax, pad=0.02)
    fig.tight_layout(h_pad=2.0)
    _save(fig, "Fig2_ground_truth")


def fig_verification():
    """L0 — solver against closed-form solutions."""
    p = "verify_solver.json"
    if not os.path.exists(p):
        print("  skip: verify_solver.json absent")
        return
    r = json.load(open(p))
    names = ["tracer\nprofile", "tracer\nfront", "retarded\nfront", "thermal\nwave", "LDF vs\nAnzelius"]
    vals = [r["tracer_van_genuchten"]["max_abs_err_vs_third_type"],
            r["tracer_van_genuchten"]["front_rel_err"],
            r["retarded_front"]["rel_err"],
            r["thermal_wave"]["rel_err"],
            r["ldf_anzelius_schumann"]["max_abs_err"]]
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    ax.bar(names, vals, color="#3b6ea5")
    ax.axhline(5e-3, color="crimson", ls="--", lw=1, label="gate threshold")
    ax.set_yscale("log")
    ax.set_ylabel("error vs closed form")
    ax.set_title("L0: ground-truth verification")
    ax.legend()
    for i, v in enumerate(vals):
        ax.text(i, v * 1.35, f"{v:.1e}", ha="center", fontsize=7)
    _save(fig, "Fig3_L0_verification")


def fig_parametric_coverage():
    """What the parametric dataset actually spans, and how it splits."""
    man = "data/parametric/manifest.json"
    if not os.path.exists(man):
        print("  skip: parametric manifest absent")
        return
    m = json.load(open(man))
    S = m["samples"]
    mats = {mm["material_id"]: mm for mm in m["materials"]}
    colours = {"train": "#3b6ea5", "novel_condition": "#e08b3a", "novel_material": "#b5423f"}

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
    for ax, (xk, yk, xl, yl) in zip(axes, [
        ("step_rh", "isotherm_n", "cooperative step (RH)", "cooperativity n"),
        ("q_max", "k_LDF", "q$_{max}$ (mol kg$^{-1}$)", "k$_{LDF}$ (s$^{-1}$)"),
        ("delta_H", "eps_t", "ΔH (J mol$^{-1}$)", "porosity ε"),
    ]):
        for split, col in colours.items():
            xs = [mats[s["mat"]][xk] for s in S if s["split"] == split]
            ys = [mats[s["mat"]][yk] for s in S if s["split"] == split]
            ax.scatter(xs, ys, s=9, alpha=0.55, c=col, label=split, edgecolors="none")
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)
    axes[0].legend(fontsize=7, markerscale=1.6)
    fig.suptitle(f"Parametric dataset: {len(S)} runs, "
                 f"{len({s['mat'] for s in S})} materials  "
                 f"(rejected {m['n_rejected']})", y=1.04)
    _save(fig, "Fig4_parametric_coverage")


def fig_l1():
    """L1 result and the measured Kolmogorov n-width."""
    import json as _j
    if not (os.path.exists("results/l1_results.json") and os.path.exists("results/nwidth.json")):
        print("  skip: L1 or n-width results absent")
        return
    r = _j.load(open("results/l1_results.json"))
    nw = _j.load(open("results/nwidth.json"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 3.4))

    # A: arms vs POD floor, novel-material split
    arms = list(r["arms"])
    means, sds = [], []
    for a in arms:
        v = [r["arms"][a][str(s)]["novel_material"]["mean"]["c"] for s in r["seeds"]]
        means.append(np.mean(v)); sds.append(np.std(v))
    order = np.argsort(means)
    arms = [arms[i] for i in order]; means = [means[i] for i in order]; sds = [sds[i] for i in order]
    floor = r["pod_floor"]["novel_material"]["c"]
    ax1.bar(arms, means, yerr=sds, capsize=4, color="#3b6ea5")
    ax1.axhline(floor, color="crimson", ls="--", lw=1.2,
                label="POD floor %.1e\n(best any fixed basis can do)" % floor)
    ax1.set_yscale("log")
    ax1.set_ylabel("nRMSE (c), novel materials")
    ax1.set_title("A. L1: data-driven arms vs the representation floor")
    ax1.legend(fontsize=7, loc="lower right")
    ax1.set_ylim(floor * 0.5, max(means) * 3.0)
    for i, (m, s) in enumerate(zip(means, sds)):
        ax1.text(i, m * 1.25, f"{m / floor:.0f}x floor", ha="center", fontsize=7.5)

    # B: n-width spectrum, algebraic vs exponential
    n = np.arange(1, len(nw["c"]["explained_variance_ratio"]) + 1)
    for ch, col in zip(("c", "q", "T"), ("#3b6ea5", "#e08b3a", "#b5423f")):
        tail = 1.0 - np.cumsum(nw[ch]["explained_variance_ratio"])
        ok = tail > 1e-12
        ax2.loglog(n[ok], np.sqrt(tail[ok]), color=col, lw=1.8,
                   label=r"%s:  $d_n \sim n^{%.2f}$" % (ch, nw[ch]["algebraic_exponent"] / 2))
        # Draw the fitted power law over the range it was actually fitted on, so
        # the reader sees both the fit quality and where it stops holding. The
        # measured spectrum steepens beyond n ~ 64; with 691 training samples the
        # high-n tail is not reliably estimated, so the claim is scoped to 8-64.
        a = nw[ch]["algebraic_exponent"] / 2
        fit_n = np.arange(8, 65)
        anchor = np.sqrt(tail[15]) / (16.0 ** a)
        ax2.loglog(fit_n, anchor * fit_n ** a, color=col, lw=0.9, ls=":", alpha=0.9)
    ax2.axvspan(8, 64, color="grey", alpha=0.10)
    ax2.text(11, 3.5e-3, "fit range\nn = 8–64", fontsize=6.5, color="0.35")
    ax2.set_xlabel("POD modes  n")
    ax2.set_ylabel("$d_n$ = sqrt(residual energy)")
    ax2.set_title("B. n-width: algebraic over the fitted range")
    ax2.legend(fontsize=7)
    ax2.grid(True, which="both", alpha=0.2)
    _save(fig, "Fig5_L1_and_nwidth")


def fig_l2_l3():
    """L2 capacity and L3 architecture: two eliminations."""
    import json as _j
    need = ["results/l2_results.json", "results/l3_results.json", "results/l3_audit.json"]
    if not all(os.path.exists(p) for p in need):
        print("  skip: L2/L3 results absent")
        return
    l2 = _j.load(open(need[0])); l3 = _j.load(open(need[1])); aud = _j.load(open(need[2]))
    # A figure must never silently plot a stale results file (defect B15).
    import analyze_l3
    analyze_l3.assert_wellformed(l3)
    floor = l2["pod_floor"]["novel_material"]

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.5))

    # A: L2 — train vs novel as capacity rises (xgb, the clearest case)
    ax = axes[0]
    recs = sorted([r for r in l2["sweep"] if r["family"] == "xgb_depth"], key=lambda x: x["capacity"])
    caps = [r["capacity"] for r in recs]
    trn = [np.mean([r["seeds"][s]["train"]["c"] for s in r["seeds"]]) for r in recs]
    nov = [np.mean([r["seeds"][s]["novel_material"]["c"] for s in r["seeds"]]) for r in recs]
    ax.plot(caps, trn, "o-", lw=2, label="train")
    ax.plot(caps, nov, "s-", lw=2, label="novel material")
    ax.axhline(floor, color="crimson", ls="--", lw=1, label="POD floor")
    ax.set_yscale("log"); ax.set_xlabel("XGBoost max_depth (capacity)")
    ax.set_ylabel("nRMSE (c)")
    ax.set_title("A. L2: capacity buys fit, not generalisation")
    ax.legend(fontsize=7)
    ax.annotate("train falls 41x,\nnovel gets worse", xy=(8, nov[5]), xytext=(3.2, 0.004),
                arrowprops=dict(arrowstyle="->", lw=0.8), fontsize=7.5)

    # B: L3 — families at matched parameters
    ax = axes[1]
    best = {}
    for a in l3["arms"]:
        k = (a["budget"], a["family"])
        nv = np.mean([a["seeds"][s]["novel_material"]["c"] for s in a["seeds"]])
        if k not in best or nv < best[k][0]:
            best[k] = (nv, np.std([a["seeds"][s]["novel_material"]["c"] for s in a["seeds"]]))
    budgets = sorted({b for b, _ in best})
    for fam, col, mk in (("mlp", "#3b6ea5", "o"), ("rbf_kan", "#e08b3a", "s"),
                         ("cheby_kan", "#b5423f", "^")):
        y = [best[(b, fam)][0] for b in budgets]
        e = [best[(b, fam)][1] for b in budgets]
        ax.errorbar(budgets, y, yerr=e, marker=mk, lw=2, capsize=3, color=col, label=fam)
    ax.set_xscale("log"); ax.set_xlabel("matched parameter budget")
    ax.set_ylabel("nRMSE (c), novel materials")
    ax.set_title("B. L3: ordering identical at every budget")
    ax.legend(fontsize=7)

    # C: the dose-response in KAN-ness
    ax = axes[2]
    g = sorted([(int(k.split("g")[1]), v) for k, v in aud.items() if k.startswith("rbf_g")])
    dgs = sorted([(int(k.split("d")[1]), v) for k, v in aud.items() if k.startswith("cheby_d")])
    ax.plot([x for x, _ in g], [y for _, y in g], "s-", lw=2, color="#e08b3a",
            label="RBF-KAN (grids/edge)")
    ax.plot([x for x, _ in dgs], [y for _, y in dgs], "^-", lw=2, color="#b5423f",
            label="Chebyshev-KAN (degree)")
    ax.axhline(aud["mlp"], color="#3b6ea5", ls="--", lw=1.5, label="MLP (1 param/edge)")
    ax.set_xlabel("basis functions per edge")
    ax.set_ylabel("nRMSE (c), novel materials")
    ax.set_title("C. More basis per edge -> worse generalisation")
    ax.legend(fontsize=7)
    _save(fig, "Fig6_L2_L3_eliminations")


def fig_l5():
    """L5: the n-width bound is real, inactive, and the coefficient map is why."""
    import json as _j
    need = ["results/l5_results.json", "results/l5_analysis.json",
            "results/l5_bottleneck.json"]
    if not all(os.path.exists(p) for p in need):
        print("  skip: L5 results absent")
        return
    raw = _j.load(open(need[0]))
    an = _j.load(open(need[1]))
    bt = _j.load(open(need[2]))

    # Never plot a stale or clobbered results file (defect B15). The panels read
    # the ANALYSED file, so figure and table cannot drift apart.
    import analyze_l5
    analyze_l5.assert_wellformed(raw, need[0])

    ps = raw["ps"]
    floor = [raw["pod_floor"][str(p)]["novel_material"] for p in ps]
    don = [an["best_per_p"]["deeponet"][str(p)]["mean"] for p in ps]
    dok = [an["best_per_p"]["deepokan"][str(p)]["mean"] for p in ps]

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.2))

    # A — the refutation: the bound falls, the methods do not
    ax = axes[0, 0]
    ax.plot(ps, floor, "o--", color="crimson", lw=2,
            label=f"POD floor (n-width bound), falls {floor[0] / floor[-1]:.1f}x")
    ax.plot(ps, don, "s-", color="#1f77b4", lw=2.2,
            label=f"DeepONet, moves {don[-1] / don[0]:.2f}x")
    ax.plot(ps, dok, "^-", color="#ff7f0e", lw=2.2, label="DeepOKAN")
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.set_xticks(ps); ax.set_xticklabels(ps)
    ax.set_xlabel("basis size p"); ax.set_ylabel("nRMSE (c), novel materials")
    ax.set_title("A. The n-width bound is real and inactive")
    ax.legend(fontsize=7, loc="lower left")
    # Mark the gap itself rather than either curve, so the label is unambiguous.
    ax.annotate("", xy=(ps[-1], don[-1]), xytext=(ps[-1], floor[-1]),
                arrowprops=dict(arrowstyle="<->", lw=1.1, color="0.25"))
    ax.text(ps[-1] * 0.93, (don[-1] * floor[-1]) ** 0.5,
            f"{don[-1] / floor[-1]:.0f}x", fontsize=9, fontweight="bold",
            color="0.25", ha="right", va="center")

    # B — which term binds, measured in the OPTIMAL basis
    ax = axes[0, 1]
    bp = [r["p"] for r in bt["rows"]]
    ax.plot(bp, [r["basis_floor_novel"] for r in bt["rows"]], "o--", color="crimson",
            lw=2, label="basis error (true coefficients)")
    ax.plot(bp, [r["coef_pred_novel"] for r in bt["rows"]], "D-", color="#2ca02c",
            lw=2.2, label="coefficient-map error (predicted)")
    ax.plot(ps, don, "s-", color="#1f77b4", lw=1.6, alpha=0.75, label="DeepONet")
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.set_xticks(bp); ax.set_xticklabels(bp)
    ax.set_xlabel("basis size p"); ax.set_ylabel("nRMSE (c), novel materials")
    ax.set_title("B. The coefficient map is what binds")
    ax.legend(fontsize=7, loc="lower left")

    # C — the mechanism, per mode
    ax = axes[1, 0]
    r2 = np.array([r for r in bt["rows"] if r["p"] == max(bp)][0]["mode_r2_novel"])
    k = min(32, len(r2))
    ax.bar(np.arange(1, k + 1), np.clip(r2[:k], -0.5, 1.0),
           color=["#2ca02c" if v > 0.5 else "#bbbbbb" for v in r2[:k]], width=0.8)
    ax.axhline(0.0, color="k", lw=0.8)
    ax.axhline(0.5, color="crimson", ls=":", lw=1)
    ax.set_xlabel("POD mode index"); ax.set_ylabel("R² of params → coefficient")
    ax.set_title("C. Only the first few coefficients are predictable")
    ax.set_ylim(-0.55, 1.05)
    ax.annotate(f"median R² beyond mode 24 = {np.median(r2[24:]):+.3f}\n"
                f"(worse than predicting the mean)",
                xy=(0.42, 0.80), xycoords="axes fraction", fontsize=7.5)

    # D — DeepOKAN's optimisation failure is width-driven
    ax = axes[1, 1]
    width = {}
    for a in raw["arms"]:
        if a["family"] == "deepokan":
            width[a["p"]] = a["width"]
    coll = {p: 0 for p in ps}
    for c in an["collapsed"]["deepokan"]:
        coll[c["p"]] += 1
    tot = len(raw["seeds"]) * len({a["lr"] for a in raw["arms"]})
    w = [width[p] for p in ps]
    ax.bar(range(len(ps)), [100.0 * coll[p] / tot for p in ps], color="#ff7f0e", width=0.6)
    ax.set_xticks(range(len(ps)))
    ax.set_xticklabels([f"p={p}\nwidth {width[p]}" for p in ps], fontsize=7.5)
    ax.set_ylabel(f"% of runs collapsed ({tot} runs per p)")
    ax.set_title("D. DeepOKAN collapse is driven by stack width")
    ax.annotate("DeepONet: 0 of 45 runs collapsed",
                xy=(0.04, 0.90), xycoords="axes fraction", fontsize=8, color="#1f77b4")
    ax.annotate("all collapsed runs agree to 2.7e-7\nacross p, lr AND seed",
                xy=(0.04, 0.74), xycoords="axes fraction", fontsize=7.5)

    fig.tight_layout()
    _save(fig, "Fig7_L5_operators_and_nwidth")


FIGS = {"fig1": fig_isotherm, "fig2": fig_ground_truth,
        "fig3": fig_verification, "fig4": fig_parametric_coverage,
        "fig5": fig_l1,
        "fig6": fig_l2_l3,
        "fig7": fig_l5}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=sorted(FIGS))
    a = ap.parse_args()
    todo = {a.only: FIGS[a.only]} if a.only else FIGS
    for name, fn in todo.items():
        print(f"{name}: {fn.__doc__.splitlines()[0]}")
        fn()


if __name__ == "__main__":
    main()
