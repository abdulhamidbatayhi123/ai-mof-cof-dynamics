"""PREREG_P2 §3, M7 feasibility gate: does PySR run here, and recover a planted law?

Owner of results/p2_pilot_m7.json. Run BEFORE the freeze-gated confirmatory grid, on
the tests' known-answer system only (p2.synthetic.ldf_series, never the grid). The
rule, written into the prereg before this runs:

  M7 is INCLUDED on its declared subgrid iff, on 3 seeds of the known-answer LDF
  system (k = 0.02, 0.5 % noise on q and on the measured q*), PySR
    (i)  recovers the law -- p2.metric.success_L1 true -- in at least 2 of 3 seeds,
    (ii) finishes each search within 30 min of wall time, and
    (iii) keeps the process's peak resident memory under 3 GB.
  Otherwise M7 is reported as NOT RUN, with these numbers as the reason. (ii) and (iii)
  are machine limits, not method judgements: a method this machine cannot run is
  reported as unrun, never as failed.

    .venv/Scripts/python.exe p2_pilot_m7.py
"""
import json
import threading
import time

import numpy as np
import psutil

from p2.features import derivative, lib_b
from p2.metric import k_accuracy, success_L1
from p2.pysr_method import pysr_sr
from p2.synthetic import ldf_series

OUT = "results/p2_pilot_m7.json"
SEEDS = (0, 1, 2)
K_TRUE = 0.02
NOISE = 0.005
LIMIT_S, LIMIT_GB = 1800, 3.0


def peak_rss(stop, box):
    proc = psutil.Process()
    while not stop.is_set():
        try:
            rss = proc.memory_info().rss + sum(c.memory_info().rss for c in proc.children(recursive=True))
            box[0] = max(box[0], rss)
        except psutil.Error:
            pass
        time.sleep(1.0)


def main():
    rows = []
    for seed in SEEDS:
        s = ldf_series(k=K_TRUE, seed=seed)
        rng = np.random.default_rng(1000 + seed)
        q = s["q"] * (1 + NOISE * rng.standard_normal(s["q"].size))
        qstar = s["qstar"] * (1 + NOISE * rng.standard_normal(s["q"].size))
        dq = derivative(q, s["t"])
        F = lib_b(s["c"], q, s["T"], qstar)
        F = {k: v for k, v in F.items() if k != "1"}         # PySR adds constants itself
        box, stop = [0], threading.Event()
        th = threading.Thread(target=peak_rss, args=(stop, box), daemon=True); th.start()
        t0 = time.time()
        try:
            coefs, expr = pysr_sr(F, dq, seed=seed, timeout_s=LIMIT_S)
            err = None
        except Exception as e:
            coefs, expr, err = {}, None, f"{type(e).__name__}: {e}"
        wall = time.time() - t0
        stop.set(); th.join()
        ok = bool(coefs) and success_L1(coefs)
        row = {"seed": seed, "expr": expr, "success_L1": ok, "wall_s": wall, "peak_rss_gb": box[0] / 2 ** 30,
               "k_rel_err": k_accuracy(coefs, K_TRUE) if coefs else None, "error": err}
        rows.append(row)
        print(f"seed {seed}: {expr}  success={ok}  {wall:.0f}s  peak {box[0] / 2 ** 30:.2f} GB", flush=True)
    n_ok = sum(r["success_L1"] for r in rows)
    feasible = all(r["wall_s"] <= LIMIT_S and r["peak_rss_gb"] <= LIMIT_GB and r["error"] is None for r in rows)
    decision = "INCLUDE M7 on its declared subgrid" if (n_ok >= 2 and feasible) else (
        "M7 NOT RUN: infeasible on this machine" if not feasible else "M7 NOT RUN: fails the known-answer test")
    json.dump({"_what": __doc__.splitlines()[0], "k_true": K_TRUE, "noise": NOISE, "limits": {"wall_s": LIMIT_S,
               "peak_gb": LIMIT_GB}, "rows": rows, "n_success": n_ok, "feasible": feasible, "decision": decision},
              open(OUT, "w"), indent=2)
    print(decision)
    print("P2_PILOT_M7_DONE")


if __name__ == "__main__":
    main()
