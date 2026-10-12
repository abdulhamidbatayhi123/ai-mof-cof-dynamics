"""Paper 2 confirmatory grid: the methods p2_grid_o1.py does not run (PREREG_P2 §3, §4.3).

p2_grid_o1.py runs the sparse solvers (M2 weak, M2b strong, M3, M4) on L1 cells. This
driver runs the rest, each exactly as the prereg declares, with the same freeze guard:

  m6   SINDy-PI on the ISOTHERMAL CONTROL (Lib-A without T: no isotherm, no
       temperature), O1, every sigma, eps = 0 (M6 is given no isotherm, so isotherm
       error does not apply), 60 replicates (A1), strong form; success = p2.metric.success_M6.
  m9   slow-manifold discovery on every non-isothermal L1 cell, O1, every (sigma, eps),
       60 replicates (A1): the STATE q regressed on q-free features {1, c, T, c^2, q*_meas};
       success = p2.metric.success_manifold.
  l2   the L2 cells (step isotherm, k(q)), O1, every (sigma, eps), 60 replicates (A1), every
       sparse solver in both forms; success = p2.metric.success_L2 (H2d, exploratory).
  m8   KAN symbolic extraction, best configuration, on the DECLARED SUBGRID (all Da x
       sigma in {0.5, 2 %} x eps in {0, 2 %} x both isotherms x Pe x1, O1), 3 replicates;
       success = success_L1. Runs only if its per-fit cost gate passed (COST_GATES).
  m7   PySR on the same subgrid, 60 replicates (A1), only if its inclusion gate
       (results/p2_pilot_m7.json) says INCLUDE; success = success_L1.
  o1ident  identifiability on O1 (the confirmatory side of H2b): profile likelihood
       of k with the law known, over ALL probes, every non-isothermal L1 cell, every
       (sigma, eps), 60 replicates (A1); the profile refits k with the MEASURED isotherm
       (information parity); success = identifiable.
  m5   EIV best-subset (classical mixed LS-TLS on the single rate law, p2/eiv.py) on
       every non-isothermal L1 cell, O1, every (sigma, eps), 60 replicates (A1), strong form;
       success = success_L1. Pure linear algebra, so it needs no cost gate.

  m1   the S1 pipeline as a labelled demonstration (fit_m1): Langmuir, Pe x1, sigma 2 %,
       eps 0, O3, 9 Da levels, one replicate; UDE trained through the column by L-BFGS
       (<= 50 steps, 2 h), read out by sparse (M4) and symbolic (PySR) regression.

    python p2_grid_extra.py {m1,m6,m9,l2,m8,m5,m7,o1ident}
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
M1_NZ, M1_MAXITER, M1_BUDGET_S = 50, 50, 7200    # PREREG_P2 s.3 M1: L-BFGS, <= 50 steps, 2 h budget
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


def _m1_rate(c, q, T, qs, args):
    """The UDE's uptake term: a 2 x 32 tanh network of (c, q, T, q*), as in the M1 pilot,
    inputs scaled by the feed concentration, the capacity and the feed temperature."""
    import jax.numpy as jnp
    x = jnp.stack([c / args["c_in"], q / args["q_max"], (T - args["T_in"]) / 10.0,
                   qs / args["q_max"]], -1)
    h = jnp.tanh(x @ args["W1"] + args["b1"])
    h = jnp.tanh(h @ args["W2"] + args["b2"])
    return (h @ args["W3"])[..., 0] * args["scale"]


def fit_m1(rec, obs, seed=0, maxiter=M1_MAXITER, budget_s=M1_BUDGET_S, n_z=M1_NZ, symbolic=True):
    """M1, the S1 pipeline as a labelled demonstration (PREREG_P2 s.3): a UDE with a network
    in the uptake term, trained THROUGH the column model (p2.jaxcol, the differentiable
    column verified against the reference solver) on the O3 outlet c(t), T(t) by L-BFGS,
    at most `maxiter` steps or `budget_s` seconds; then read out by M4's exact best-subset
    (sparse) and by PySR (symbolic) on the trained network's rate over the solved states.
    The network's output scale is q_max / t_stoich, which needs no knowledge of k.
    Returns (coefs of the sparse readout, success, details)."""
    import jax
    import jax.numpy as jnp
    from jax.flatten_util import ravel_pytree
    from scipy.optimize import minimize

    from p2.jaxcol import solve
    from p2.pysr_method import pysr_sr
    from p2_observe import physics_for
    jax.config.update("jax_enable_x64", True)
    phys = physics_for(rec)
    phys.D_L = rec["D_L"]
    ts = np.asarray(obs["t"], float)
    c_obs, T_obs = np.asarray(obs["channels"]["c"][0]), np.asarray(obs["channels"]["T"][0])
    rc, rT = float(np.ptp(c_obs)) or 1.0, float(np.ptp(T_obs)) or 1.0
    k1, k2, k3 = jax.random.split(jax.random.PRNGKey(seed), 3)
    train = {"W1": 0.3 * jax.random.normal(k1, (4, 32)), "b1": jnp.zeros(32),
             "W2": 0.3 * jax.random.normal(k2, (32, 32)), "b2": jnp.zeros(32),
             "W3": 0.3 * jax.random.normal(k3, (32, 1))}
    fixed = {"scale": rec["q_max"] / rec["t_stoich_s"], "c_in": rec["c_in"],
             "q_max": rec["q_max"], "T_in": rec["T_in"]}
    x0, unravel = ravel_pytree(train)

    def loss(x):
        y = solve(phys, n_z, rec["c_in"], float(ts[-1]), ts, rate=_m1_rate,
                  args={**unravel(x), **fixed})
        return (jnp.mean(((y[:, n_z - 1] - c_obs) / rc) ** 2)
                + jnp.mean(((y[:, 3 * n_z - 1] - T_obs) / rT) ** 2))
    vg = jax.jit(jax.value_and_grad(loss))
    t0, best, hist = time.time(), {"f": np.inf, "x": np.asarray(x0)}, []

    class _Budget(Exception):
        pass

    def fun(x):
        if time.time() - t0 > budget_s:
            raise _Budget
        v, g = vg(jnp.asarray(x))
        v, g = float(v), np.asarray(g, float)
        hist.append(v)
        if v < best["f"]:
            best.update(f=v, x=np.array(x))
        return v, g
    stopped = "maxiter"
    try:
        minimize(fun, np.asarray(x0, float), jac=True, method="L-BFGS-B",
                 options={"maxiter": maxiter, "maxfun": maxiter + 10})
    except _Budget:
        stopped = "budget"
    prm = {**unravel(jnp.asarray(best["x"])), **fixed}
    y = np.asarray(solve(phys, n_z, rec["c_in"], float(ts[-1]), ts, rate=_m1_rate, args=prm))
    c, q, T = y[:, :n_z].ravel(), y[:, n_z:2 * n_z].ravel(), y[:, 2 * n_z:].ravel()
    qs = obs["qstar_meas"](c, T)
    rate = np.asarray(_m1_rate(jnp.asarray(c), jnp.asarray(q), jnp.asarray(T), jnp.asarray(qs), prm))
    F = lib_b(c, q, T, qs)
    co = methods.best_subset(F, rate)
    ok_sparse = bool(success_L1(co))
    co_sr, ok_sr = {}, False
    try:
        if symbolic:
            co_sr, _ = pysr_sr({k: v for k, v in F.items() if k != "1"}, rate, seed=seed)
            ok_sr = bool(success_L1(co_sr))
    except Exception as e:   # recorded, never dropped
        co_sr, ok_sr = {"error": f"{type(e).__name__}: {e}"}, False
    return co, ok_sparse or ok_sr, {"loss_first": hist[0] if hist else None, "loss_best": best["f"],
                                     "n_evals": len(hist), "stopped": stopped,
                                     "readout_sparse": {k: float(v) for k, v in co.items()},
                                     "success_sparse": ok_sparse, "success_symbolic": ok_sr,
                                     "readout_symbolic": {k: (float(v) if not isinstance(v, str) else v)
                                                          for k, v in co_sr.items()}}


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
        if rec.get("refined") and cmd not in ("m5", "m7"):
            continue   # A1: H2c refinement cells serve H2c only (M5, M7 and the O1 solvers)
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
        elif cmd == "m1":
            # PREREG_P2 s.3: the minimal demonstration -- Langmuir, Pe x1, sigma = 2 %,
            # eps = 0, O3, the 9 Da levels, one replicate
            if iso != "langmuir" or law != "L1" or rec["pe_mult"] != 1.0 or rec.get("refined"):
                continue
            grid = [(0.02, 0.0, 0, "m1_ude", "o3")]
        elif cmd == "m5":
            if iso == "langmuir_iso" or law != "L1":
                continue
            grid = itertools.product(*(((0.02,), (0.02,)) if rec.get("refined") else (SIGMAS, EPSS)),
                                     range(N_REP), ("eiv_best_subset",), ("strong",))
        else:   # m8, m7: the declared subgrid
            if iso == "langmuir_iso" or law != "L1" or rec["pe_mult"] != 1.0:
                continue
            # A1: M7 runs at the full replicate count on its subgrid, so it can take part in
            # the selection/estimation split; M8 (not run, cost gate) keeps the declared 3
            grid = itertools.product(*(((0.02,), (0.02,)) if rec.get("refined") else (SUB_SIGMAS, SUB_EPSS)),
                                     range(N_REP if cmd == "m7" else SUB_REP),
                                     (cmd,), ("strong",))
        t0 = time.time()
        for sigma, eps, rep, solver, form in grid:
            key = f"{name}|{sigma}|{eps}|{rep}|{solver}|{form}"
            if key in res["rows"]:
                continue
            obs = observe(name, rep, sigma, eps, "O3" if cmd == "m1" else "O1")
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
                elif cmd == "m1":
                    co, ok, m1_detail = fit_m1(rec, obs, seed=rep)
                else:   # m5
                    co, ok = fit_m5(obs, sigma, eps)
                res["rows"][key] = {"success": bool(ok), "sec": time.time() - t1,
                                    **({"interval": co} if cmd == "o1ident" else {"support": sorted(co)}),
                                    # A1: the fitted k, for the k-aware sensitivity analysis
                                    **({"k_hat": float(-co.get("q", 0.0))} if cmd in ("m1", "m5", "m7", "l2") else {}),
                                    **({"m1": m1_detail} if cmd == "m1" else {})}
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
