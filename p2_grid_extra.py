"""Paper 2 confirmatory grid: the methods p2_grid_o1.py does not run (PREREG_P2 §3, §4.3).

p2_grid_o1.py runs the sparse solvers (M2 weak, M2b strong, M3, M4) on L1 cells. This
driver runs the rest, each exactly as the prereg declares, with the same freeze guard:

  m6   SINDy-PI on the ISOTHERMAL CONTROL (Lib-A without T: no isotherm, no
       temperature), O1, every sigma, eps = 0 (M6 is given no isotherm, so isotherm
       error does not apply), 20 replicates, strong form; success = p2.metric.success_M6.
  m9   slow-manifold discovery on every non-isothermal L1 cell, O1, every (sigma, eps),
       20 replicates: the STATE q regressed on q-free features {1, c, T, c^2, q*_meas};
       success = p2.metric.success_manifold.
  l2   the L2 cells (step isotherm, k(q)), O1, every (sigma, eps), 20 replicates, every
       sparse solver in both forms; success = p2.metric.success_L2 (H2d, exploratory).
  m8   KAN symbolic extraction, best configuration, on the DECLARED SUBGRID (all Da x
       sigma in {0.5, 2 %} x eps in {0, 2 %} x both isotherms x Pe x1, O1), 3 replicates;
       success = success_L1. Runs only if its per-fit cost gate passed (COST_GATES).
  m7   PySR on the same subgrid, 3 replicates, only if its inclusion gate
       (results/p2_pilot_m7.json) says INCLUDE; success = success_L1.
  o1ident  identifiability on O1 (the confirmatory side of H2b): profile likelihood
       of k with the law known, over ALL probes, every non-isothermal L1 cell, every
       (sigma, eps), 20 replicates; the profile refits k with the MEASURED isotherm
       (information parity); success = identifiable.
  m5   EIV best-subset (classical mixed LS-TLS on the single rate law, p2/eiv.py) on
       every non-isothermal L1 cell, O1, every (sigma, eps), 20 replicates, strong form;
       success = success_L1. Pure linear algebra, so it needs no cost gate.

    python p2_grid_extra.py {m6,m9,l2,m8,m5,m7,o1ident}
"""
import itertools
import json
import os
import sys
import time

import numpy as np

from p2 import methods
from p2.features import derivative, lib_b
from p2.metric import success_L1, success_L2, success_M6, success_manifold
from p2.run_o1 import SOLVERS, discover_o1
from p2_grid_o1 import EPSS, FORMS, N_REP, SIGMAS, frozen
from p2_observe import observe
from v2_common import write_atomic

SUB_SIGMAS, SUB_EPSS, SUB_REP = (0.005, 0.02), (0.0, 0.02), 3
COST_GATES = "results/p2_cost_gates.json"      # written by p2_pilot_costs.py, pre-freeze


def _stack_probes(obs, build):
    rows = [build(obs["channels"]["c"][j], obs["channels"]["q"][j], obs["channels"]["T"][j])
            for j in range(obs["channels"]["q"].shape[0])]
    F = {k: np.concatenate([r[0][k] for r in rows]) for k in rows[0][0]}
    return F, np.concatenate([r[1] for r in rows])


def fit_m6(obs):
    t = obs["t"]
    F, dq = _stack_probes(obs, lambda c, q, T: (
        {"1": np.ones_like(c), "c": c, "q": q, "c*q": c * q, "q^2": q ** 2, "c^2": c ** 2},
        derivative(q, t)))
    _, co = methods.sindy_pi(F, dq)
    return co, success_M6(co)


def fit_m9(obs):
    qs = obs["qstar_meas"]
    F, q = _stack_probes(obs, lambda c, q, T: (
        {"1": np.ones_like(c), "c": c, "T": T, "c^2": c ** 2, "qstar": qs(c, T)}, q))
    co = methods.slow_manifold(F, q)
    return co, success_manifold(co)


def fit_m5(obs, sigma, eps):
    """M5 as run: EIV best-subset (p2/eiv.py) on Lib-B, strong form. Error SDs are the
    DECLARED observation errors (an experimenter knows instrument noise and roughly how
    good the isotherm is): sigma x channel range for c, q, T; eps x |q*| for the measured
    isotherm (plus its sensitivity to the c-noise); first-order propagation to products;
    the target's SD is the Savitzky-Golay derivative of white noise of the q-channel SD,
    measured, not assumed."""
    from p2.eiv import eiv_best_subset
    t = obs["t"]
    ch = obs["channels"]
    rc, rq, rT = (float(np.ptp(ch[k])) for k in ("c", "q", "T"))
    sc, sq, sT = sigma * rc, sigma * rq, sigma * rT
    from scipy.signal import savgol_coeffs
    qsm = obs["qstar_meas"]

    def build(c, q, T):
        lib = lib_b(c, q, T, qsm(c, T))
        h = 1e-6 * max(float(np.ptp(c)), 1e-12)         # dq*/dc by a direct finite difference
        lib["_dqs_dc"] = (qsm(c + h, T) - qsm(c, T)) / h
        return lib, derivative(q, t)

    F, y = _stack_probes(obs, build)
    dqs = F.pop("_dqs_dc")
    qs = F["qstar"]
    sd = {"1": 0.0, "c": sc, "q": sq, "T": sT,
          "c*q": np.sqrt((F["q"] * sc) ** 2 + (F["c"] * sq) ** 2),
          "q^2": np.abs(2 * F["q"] * sq), "c^2": np.abs(2 * F["c"] * sc),
          "qstar": np.sqrt((eps * qs) ** 2 + (dqs * sc) ** 2)}
    # the Savitzky-Golay derivative is a linear filter: white noise of SD s comes out
    # with SD s * ||h|| (h its coefficients) -- exact, no random draw needed
    dt = float(t[1] - t[0])
    w = min(21, (len(t) // 2) * 2 - 1)
    gain = float(np.linalg.norm(savgol_coeffs(w, min(3, w - 1), deriv=1, delta=dt)))
    sd_y = sq * gain if sigma > 0 else 1e-12
    co = eiv_best_subset(F, y, sd, sd_y)
    return co, success_L1(co)


def _gate(method):
    if not os.path.exists(COST_GATES):
        sys.exit(f"REFUSED: {COST_GATES} missing -- run the pre-freeze cost pilot first")
    g = json.load(open(COST_GATES)).get(method)
    if not g or not g.get("run"):
        sys.exit(f"{method}: NOT RUN by its pre-registered cost gate ({g}); reported as such")
    return g


def run(cmd, man):
    out = f"results/p2_extra_{cmd}.json"
    res = json.load(open(out)) if os.path.exists(out) else {"freeze_commit": frozen()[1], "rows": {}}
    if cmd == "m8":
        _gate(cmd)
    if cmd == "m7":
        g = json.load(open("results/p2_pilot_m7.json")) if os.path.exists("results/p2_pilot_m7.json") else {}
        if not str(g.get("decision", "")).startswith("INCLUDE"):
            sys.exit(f"m7: NOT RUN by its pre-registered inclusion gate ({g.get('decision', 'pilot not run')})")
    for name, rec in sorted(man.items()):
        iso, law = rec["iso"], rec["law"]
        if cmd == "m6":
            if iso != "langmuir_iso":
                continue
            grid = itertools.product(SIGMAS, (0.0,), range(N_REP), ("sindy_pi",), ("strong",))
        elif cmd == "m9":
            if iso == "langmuir_iso" or law != "L1":
                continue
            grid = itertools.product(SIGMAS, EPSS, range(N_REP), ("slow_manifold",), ("strong",))
        elif cmd == "l2":
            if law != "L2":
                continue
            grid = itertools.product(SIGMAS, EPSS, range(N_REP), SOLVERS, FORMS)
        elif cmd == "o1ident":
            if iso == "langmuir_iso" or law != "L1":
                continue
            grid = itertools.product(SIGMAS, EPSS, range(N_REP), ("profile",), ("o1",))
        elif cmd == "m5":
            if iso == "langmuir_iso" or law != "L1":
                continue
            grid = itertools.product(SIGMAS, EPSS, range(N_REP), ("eiv_best_subset",), ("strong",))
        else:   # m8, m7: the declared subgrid
            if iso == "langmuir_iso" or law != "L1" or rec["pe_mult"] != 1.0:
                continue
            grid = itertools.product(SUB_SIGMAS, SUB_EPSS, range(SUB_REP), (cmd,), ("strong",))
        t0 = time.time()
        for sigma, eps, rep, solver, form in grid:
            key = f"{name}|{sigma}|{eps}|{rep}|{solver}|{form}"
            if key in res["rows"]:
                continue
            obs = observe(name, rep, sigma, eps, "O1")
            t1 = time.time()
            try:
                if cmd == "m6":
                    co, ok = fit_m6(obs)
                elif cmd == "m9":
                    co, ok = fit_m9(obs)
                elif cmd == "l2":
                    co = discover_o1(obs, solver, form)
                    ok = success_L2(co, obs["channels"]["c"].ravel(), obs["channels"]["q"].ravel(),
                                    rec["q_max"])
                elif cmd == "m8":
                    V = {"c": np.concatenate(obs["channels"]["c"]), "q": np.concatenate(obs["channels"]["q"]),
                         "T": np.concatenate(obs["channels"]["T"]),
                         "qstar": np.concatenate([obs["qstar_meas"](c, T) for c, T in
                                                  zip(obs["channels"]["c"], obs["channels"]["T"])])}
                    y = np.concatenate([derivative(q, obs["t"]) for q in obs["channels"]["q"]])
                    co = methods.kan_symbolic(V, y, seed=rep)
                    ok = success_L1(co)
                elif cmd == "o1ident":
                    from p2.identifiability import identifiable, profile_interval_o1
                    ch = obs["channels"]
                    sq = max(sigma, 1e-4) * float(np.ptp(ch["q"]))
                    lo, hi = profile_interval_o1(obs["t"], list(ch["c"]), list(ch["q"]),
                                                 obs["qstar_meas"], sq, Ts=list(ch["T"]))
                    co = {"lo": lo, "hi": hi}
                    ok = identifiable(lo, hi, rec["k_LDF"])
                elif cmd == "m7":
                    from p2.pysr_method import pysr_sr
                    F, y = _stack_probes(obs, lambda c, q, T: (
                        {k: v for k, v in lib_b(c, q, T, obs["qstar_meas"](c, T)).items() if k != "1"},
                        derivative(q, obs["t"])))
                    co, _ = pysr_sr(F, y, seed=rep)
                    ok = success_L1(co)
                else:   # m5
                    co, ok = fit_m5(obs, sigma, eps)
                res["rows"][key] = {"success": bool(ok), "sec": time.time() - t1,
                                    **({"interval": co} if cmd == "o1ident" else {"support": sorted(co)})}
            except Exception as e:   # recorded, never dropped
                res["rows"][key] = {"success": False, "error": f"{type(e).__name__}: {e}"}
        write_atomic(res, out)
        print(f"{cmd} {name:<34} [{time.time() - t0:.0f}s]", flush=True)


def main():
    ok, why = frozen()
    if not ok:
        sys.exit(f"REFUSED: the pre-registration is not frozen ({why}).")
    run(sys.argv[1], json.load(open("data/p2/manifest.json"))["cells"])


if __name__ == "__main__":
    main()
