"""The amortised cost of the surrogate, in the units a screening study is paid in.

WHY THIS SCRIPT EXISTS.  The introduction asserts that a surrogate cannot beat its own
reference on accuracy -- the reference is exact by construction -- so a synthetic study
can only measure accuracy per unit inference cost, or accuracy from less information.
The manuscript then never gave the cost.  For a CMAME paper that is the missing half of
the argument: the entire case for a learned surrogate of a fixed-bed column is that
thousands of screening queries are cheaper through the surrogate than through the
solver, and nobody in this project had ever written down the crossing point.

THE ACCOUNTING, and why it is stated in solve-equivalents.  A surrogate's total cost is

    (training-set cost) + (training cost) + n_query * (cost per surrogate query)

against  n_query * (cost per solve)  for the reference.  Every term except the last two
is paid once.  Expressing all of them in SOLVE-EQUIVALENTS -- multiples of the cost of
one reference simulation -- removes the machine, the thread count and the wall clock
from the comparison, and leaves a number a reader can carry to their own hardware.

The break-even query count is then

    n_be = (n_train + c_train) / (1 - r)        r = (cost per query)/(cost per solve)

and because r is bounded well below 1 (a forward pass through a 3x256 perceptron plus
three 64-mode reconstructions against a 2000-cell implicit solve to breakthrough),
n_be is bounded below by n_train + c_train WITHOUT measuring r at all.  That bound is
the honest headline, it needs no timing, and it is reported as a bound.  The measured
r sharpens it and is reported separately, only when it can be measured cleanly.

WHAT THIS IS NOT.  It is not a claim that the surrogate and the solver are
interchangeable.  They are not: the surrogate answers with a held-out error that this
paper spends nine sections measuring, and the solver answers exactly.  Every statement
here is cost AT A STATED ACCURACY, never cost at equal accuracy, and the accuracy is
carried alongside the cost in every row of the frontier below.

TIMING AND CONTENTION.  A timing measured while a training chain saturates the machine
is not a timing.  The measured branch REFUSES to run when a known runner process is
alive, and records why.  Rule 6: a gate that can be bypassed is not a gate.

    python cost_accounting.py                 # recorded accounting + the bound
    python cost_accounting.py --time          # additionally measure r (needs an idle machine)
    python cost_accounting.py --time --force  # time anyway, and mark the result contended

Writes results/cost_accounting.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time

import numpy as np

MANIFEST = "data/parametric_v2/manifest.json"
GEN_LOG = "gen_v2.log"
LC_VERDICT = "results/learning_curve_v2_verdict.json"
L1_LOG = "l1_v2.log"
OUT = "results/cost_accounting.json"

# The architecture whose query cost is being timed: L1-v2's reported arm.
# run_l1.make_arm("mlp") -> MLPRegressor(hidden_layer_sizes=(256, 256, 256)) inside a
# TransformedTargetRegressor, predicting 3 * n_modes POD coefficients from 11 params.
N_PARAMS = 11
HIDDEN = (256, 256, 256)
N_MODES = 64
CHANNELS = 3
FIELD_RES = 128

# The runner names resume.sh watches for.  Same list, deliberately: two places that
# must agree about "is a training job alive" should not drift apart.
RUNNERS = "run_l4b_v2|refine_l4b_v2|run_l6_v2|run_l1_v2|run_l2_v2|run_l5_fno"


def runners_alive():
    """Count live training runners via the Windows command line, as resume.sh does.

    `ps -ef` under Git Bash shows only the interpreter path, never the script, so
    grepping it always returns zero and the guard would never fire.
    """
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             f"Where-Object {{ $_.CommandLine -match '{RUNNERS}' }}).Count"],
            capture_output=True, text=True, timeout=60)
        return int(r.stdout.strip() or 0)
    except Exception as exc:                                  # noqa: BLE001
        # Unknown is not zero.  Refuse rather than assume an idle machine.
        raise RuntimeError(f"could not determine whether a runner is alive: {exc}")


def workers_from_gen_log(path):
    """The worker count of the generation run, read from its own log.

    A hard failure if absent: the wall time means nothing without it, and guessing 4
    because the log 'probably' said 4 is exactly the unowned number rule 10 forbids.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path}: the generation log carries the worker count")
    with open(path, encoding="utf-8", errors="replace") as fh:
        head = fh.read(4000)
    m = re.search(r"^workers=(\d+)\s*$", head, re.M)
    if not m:
        raise ValueError(f"{path}: no 'workers=N' line in the first 4 kB; "
                         "the generation cost cannot be normalised without it")
    return int(m.group(1))


def mlp_train_seconds(path):
    """The wall time of L1-v2's reported MLP arm, from its own log, per seed.

    Parsed rather than typed, and every matching line is returned so the caller can
    see the spread instead of trusting one number.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    secs = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.match(r"\s*mlp\s+seed\s+\d+:.*\[(\d+)s\]\s*$", line)
            if m:
                secs.append(int(m.group(1)))
    if not secs:
        raise ValueError(f"{path}: no 'mlp seed NN: ... [NNs]' lines found")
    return secs


def time_query(n_rep=200, batch=1):
    """Seconds per surrogate query: parameter vector -> reconstructed field.

    Timed on an untrained model of the identical architecture.  Inference cost is a
    property of the shapes -- 11 -> 256 -> 256 -> 256 -> 3*64, then three
    (64 x 128*128) reconstructions -- and not of the weight VALUES, so a model fitted
    for one iteration on random data times exactly like the reported one.  Saying this
    out loud matters: a reader must be able to see that no trained checkpoint is being
    smuggled in as a timing.
    """
    from sklearn.neural_network import MLPRegressor

    rng = np.random.default_rng(0)
    x = rng.standard_normal((64, N_PARAMS))
    y = rng.standard_normal((64, CHANNELS * N_MODES))
    model = MLPRegressor(hidden_layer_sizes=HIDDEN, max_iter=1)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")            # max_iter=1 never converges; that is the point
        model.fit(x, y)

    bases = rng.standard_normal((CHANNELS, N_MODES, FIELD_RES * FIELD_RES)).astype(np.float32)
    exit_rows = np.ascontiguousarray(bases[:, :, -FIELD_RES:])   # one z-slice: the exit curve
    q = rng.standard_normal((batch, N_PARAMS))

    def one(full):
        c = model.predict(q).reshape(batch, CHANNELS, N_MODES).astype(np.float32)
        tgt = bases if full else exit_rows
        for ch in range(CHANNELS):
            _ = c[:, ch, :] @ tgt[ch]

    out = {}
    for label, full in (("field", True), ("exit_curve", False)):
        one(full)                                    # warm up allocators and BLAS
        t0 = time.perf_counter()
        for _ in range(n_rep):
            one(full)
        out[label] = (time.perf_counter() - t0) / (n_rep * batch)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time", action="store_true",
                    help="also measure the per-query cost (needs an idle machine)")
    ap.add_argument("--force", action="store_true",
                    help="time even while a runner is alive; the result is marked contended")
    args = ap.parse_args()

    man = json.load(open(MANIFEST))
    lc = json.load(open(LC_VERDICT))

    n_solves = len([s for s in man["samples"] if s.get("ok", True)])
    wall_s = float(man["elapsed_s"])
    workers = workers_from_gen_log(GEN_LOG)
    # The screen rejects BEFORE a solve is spent (gen_parametric_dataset.screen), so
    # the rejected candidates cost essentially nothing and the wall time divides by
    # the ACCEPTED count.  If that ever changes this number silently becomes wrong,
    # so the manifest's own tally is carried alongside it.
    worker_s_per_solve = wall_s * workers / n_solves

    train_secs = mlp_train_seconds(L1_LOG)
    # In solve-equivalents.  The training wall time is single-process, so it is
    # compared against ONE worker's second, which is what worker_s_per_solve is.
    c_train = float(np.median(train_secs)) / worker_s_per_solve

    out = {
        "_what": "amortised cost of the L1-v2 surrogate against its own reference, "
                 "in solve-equivalents",
        "_unit": "one solve-equivalent = the cost of one reference simulation at "
                 "production settings (solve_nz=%d, stored %dx%d)"
                 % (man["solve_nz"], man["store_nz"], man["store_nt"]),
        "_accuracy_caveat": "every cost below is cost AT A STATED ACCURACY. The "
                            "surrogate does not reproduce the solver; its held-out "
                            "error is carried in the frontier rows.",
        "generation": {
            "n_solves": n_solves,
            "n_rejected_before_solving": man["n_rejected"],
            "wall_s": wall_s,
            "workers": workers,
            "worker_seconds_per_solve": worker_s_per_solve,
            "_caveat": "worker-seconds, not CPU-seconds: a worker's own numerical "
                       "libraries may use more than one thread, so this is an upper "
                       "bound on the serial cost and a lower bound on the machine cost.",
        },
        "training": {
            "arm": "MLPRegressor(256,256,256) on 64 POD modes/channel, L1-v2's arm",
            "seconds_per_seed": train_secs,
            "median_seconds": float(np.median(train_secs)),
            "solve_equivalents": c_train,
        },
    }

    # ---------------------------------------------------------- the frontier
    # Each learning-curve size costs its own training simulations and buys its own
    # held-out error.  This is the table a practitioner actually needs: not "what is
    # the best error" but "what does each error cost".
    rows = []
    axis = lc["axes"]["materials"]
    for r in axis["rows"]:
        # n_train is the MEAN training-set size over the five folds, so it is not an
        # integer (196.4 at twelve materials).  Kept as a float: rounding it here
        # would quietly invent a precision the folds do not have.
        n_train = float(r["n_train"])
        err = float(r["refit"])
        # break-even, as a BOUND: n_be = (n_train + c_train)/(1 - r) >= n_train + c_train
        rows.append({
            "n_materials": int(r["n_materials"]),
            "n_train_sims_mean_over_folds": n_train,
            "held_out_nrmse": err,
            "data_cost_solve_equivalents": n_train,
            "total_amortised_cost_solve_equivalents": n_train + c_train,
            "break_even_queries_lower_bound": n_train + c_train,
        })
    out["frontier"] = rows
    out["headline"] = {
        "n_train_at_largest": rows[-1]["n_train_sims_mean_over_folds"],
        "nrmse_at_largest": rows[-1]["held_out_nrmse"],
        "break_even_queries_lower_bound": rows[-1]["break_even_queries_lower_bound"],
        "_reading": "the surrogate cannot repay its own construction in fewer than "
                    "this many screening queries, whatever the per-query cost is, "
                    "because that is what its training set and its fit cost.",
    }

    # --------------------------------------------------------- the timing branch
    alive = runners_alive()
    if args.time:
        if alive and not args.force:
            out["query"] = {
                "measured": False,
                "_refused": f"{alive} training runner(s) alive; a timing taken under "
                            "contention is not a timing. Re-run on an idle machine, "
                            "or pass --force to record a contended measurement.",
            }
        else:
            t = time_query()
            r_field = t["field"] / worker_s_per_solve
            out["query"] = {
                "measured": True,
                "contended": bool(alive),
                "runners_alive": alive,
                "seconds_per_query_field": t["field"],
                "seconds_per_query_exit_curve": t["exit_curve"],
                "solve_equivalents_per_query_field": r_field,
                "solve_equivalents_per_query_exit_curve": t["exit_curve"] / worker_s_per_solve,
                "speedup_field": worker_s_per_solve / t["field"],
                "speedup_exit_curve": worker_s_per_solve / t["exit_curve"],
                "_note": "timed on an untrained model of the identical architecture; "
                         "inference cost depends on the shapes, not the weight values.",
            }
            for row in out["frontier"]:
                row["break_even_queries"] = row["total_amortised_cost_solve_equivalents"] \
                    / (1.0 - r_field)
            out["headline"]["break_even_queries"] = out["frontier"][-1]["break_even_queries"]
    else:
        out["query"] = {"measured": False,
                        "_note": "run with --time on an idle machine to measure it"}

    os.makedirs("results", exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)

    g = out["generation"]
    print(f"reference:  {g['n_solves']} solves, {g['wall_s'] / 3600:.1f} h wall on "
          f"{g['workers']} workers")
    print(f"            {g['worker_seconds_per_solve']:.1f} worker-seconds per solve "
          f"(= 1 solve-equivalent)")
    t = out["training"]
    print(f"training:   {t['median_seconds']:.0f} s median over {len(t['seconds_per_seed'])} "
          f"seeds = {t['solve_equivalents']:.1f} solve-equivalents")
    print()
    print("  materials  train sims   held-out nRMSE   amortised cost   break-even (>=)")
    for r in out["frontier"]:
        print(f"  {r['n_materials']:>9}  {r['n_train_sims_mean_over_folds']:>10.0f}   "
              f"{r['held_out_nrmse']:>14.5f}   "
              f"{r['total_amortised_cost_solve_equivalents']:>14.1f}   "
              f"{r['break_even_queries_lower_bound']:>15.0f}")
    q = out["query"]
    print()
    if q.get("measured"):
        print(f"query:      {q['seconds_per_query_field']*1e3:.3f} ms per full field "
              f"({q['speedup_field']:.0f}x a solve), "
              f"{q['seconds_per_query_exit_curve']*1e3:.3f} ms per exit curve "
              f"({q['speedup_exit_curve']:.0f}x)"
              + ("   [CONTENDED]" if q.get("contended") else ""))
    else:
        print(f"query:      not measured -- {q.get('_refused') or q.get('_note')}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
