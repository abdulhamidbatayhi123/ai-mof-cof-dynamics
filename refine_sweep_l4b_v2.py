"""POST-HOC: does physics at inference fail, or did one configuration of it fail?

**This is not part of `PREREG_L4b_v2.md` and must never be reported as though it
were.** The pre-registered Q3 specifies exactly one configuration — 300 Adam steps at
lr 1e-4, all weights free — and its verdict is computed by `analyze_l4b_v2.py` in the
pre-declared words. This script runs *afterwards* and asks the rule-4 question that
the pre-registration did not: **is that verdict a property of physics at inference, or
a property of that configuration?**

Why it exists. L4b-v2 exists because L4b-v1's headline rested on one weighting rule,
one optimiser and one step count — "rule 4 turned inward", audit P7. Q1 and Q2 fixed
that for the *loss* weighting: ten schemes, four decades of fixed weight, gradient-norm
at three targets, NTK, self-adaptive. **Q3 did not get the same treatment**, and the
pre-registered run degrades held-out error by ~5x on both axes while *also* destroying
the seen window on the time axis (0.0127 -> 0.0945, a 643 % rise against the
pre-declared 10 % tolerance — PREREG §4.3's invalidation condition, fired). A refiner
that walks that far from the trained solution is a badly-configured optimiser, not a
refuted idea, and reporting it as a refuted idea would be the mistake this project
audits for.

What it measures, on the MATERIAL axis — the axis where physics at inference is the
only form of physics-informing that can act on transfer at all:

  * `--lrs`   the refinement learning rate over decades. 1e-4 is the pre-registered
              value and is included so the sweep contains its own reference point.
  * step count, FOR FREE: the held-out error is evaluated at every checkpoint in
              `--eval-at`, not only at the end, so "would stopping earlier have
              helped?" is answered without re-running anything. Step 0 is evaluated
              too and must reproduce the un-refined error exactly — a self-check.
  * `--scope` `all` refines every weight (the pre-registered choice); `last` refines
              only the output layer. Constraining the adapted subspace is the standard
              way test-time adaptation avoids catastrophic drift, so `last` is a
              genuinely STRONGER configuration of the arm being argued against, which
              is what rule 4 requires us to compare against.

Nothing here changes any pre-registered verdict. It can only (a) confirm it across a
grid, which is the outcome that would let "physics at inference does not help" be
stated as a property rather than an anecdote, or (b) overturn it, in which case the
pre-registered verdict is reported AND the sweep is reported as the reason it does not
generalise. Both outcomes are written here, before the run, deliberately.

    python refine_sweep_l4b_v2.py                          # the default grid
    python refine_sweep_l4b_v2.py --scope last --lrs 1e-4
"""
from __future__ import annotations

import argparse
import copy
import gc
import json
import os
import time

import numpy as np
import torch

import ladder_data
from run_l4 import DEVICE, ParametricPINN, build_phys_table
from run_l4b import eval_window
from run_l4b_v2 import ckpt_path, physics_terms
from v2_common import FIELD_RES, ROOT_V2, get_path, load_or_init, set_path, write_atomic

OUT = "results/l4b_v2_refine_sweep.json"


def trainable(model, scope):
    """The parameter subset the refiner is allowed to move."""
    if scope == "all":
        return list(model.parameters())
    if scope == "last":
        # the final Linear of the trunk — the smallest subspace that can still
        # re-map the output, and the one test-time adaptation normally uses
        lin = [m for m in model.modules() if isinstance(m, torch.nn.Linear)]
        if not lin:
            raise RuntimeError("no Linear layer found to refine")
        return list(lin[-1].parameters())
    raise ValueError(scope)


def refine_unit_traj(model0, d, uidx, Pz, table, tau_all, args, rng, eval_at):
    """Refine one unit, evaluating held-out error at every checkpoint in `eval_at`.

    Returns {step: per-sample errors} and the residual-loss trajectory. Evaluating
    inside the loop is what makes the step count a swept axis rather than a fixed one,
    at the cost of a few forward passes against 300 optimisation steps.
    """
    model = copy.deepcopy(model0)
    params = trainable(model, args.scope)
    for p in model.parameters():
        p.requires_grad_(False)
    for p in params:
        p.requires_grad_(True)
    opt = torch.optim.Adam(params, lr=args.refine_lr)
    per_step, hist = {}, []
    want = sorted(set(eval_at))

    if 0 in want:
        model.eval()
        per_step[0] = eval_window(model, d, uidx, d.params_z, 0.0, 1.0)
    model.train()
    for step in range(1, max(want) + 1):
        opt.zero_grad(set_to_none=True)
        cg = uidx[rng.integers(0, len(uidx), args.n_colloc)]
        zc = torch.rand(args.n_colloc, 1, device=DEVICE)
        tc = torch.rand(args.n_colloc, 1, device=DEVICE)
        bg = cg[:args.n_bc]
        tb = torch.rand(len(bg), 1, device=DEVICE)
        res_sq, bc_sq = physics_terms(model, Pz, table, tau_all, cg, zc, tc, bg, tb)
        z0 = torch.rand(args.n_bc, 1, device=DEVICE)
        g0 = torch.tensor(uidx[rng.integers(0, len(uidx), args.n_bc)], device=DEVICE)
        p0 = model(Pz[g0], z0, torch.zeros_like(z0))
        loss = (res_sq.mean() + bc_sq.mean()
                + (p0[:, 0:2] ** 2).mean() + ((p0[:, 2:3] - 1.0) ** 2).mean())
        if not torch.isfinite(loss):
            return per_step, hist, True
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        if step % 50 == 0 or step == max(want):
            hist.append({"step": step, "loss": float(loss.detach())})
        if step in want:
            model.eval()
            per_step[step] = eval_window(model, d, uidx, d.params_z, 0.0, 1.0)
            model.train()
    return per_step, hist, False


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT_V2)
    ap.add_argument("--field-res", type=int, default=FIELD_RES)
    ap.add_argument("--arm", default="data_only",
                    help="which trained checkpoint to refine (the sweep's own arms)")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--lrs", type=float, nargs="+", default=[1e-6, 1e-5, 1e-4, 1e-3])
    ap.add_argument("--scope", choices=["all", "last"], default="all")
    ap.add_argument("--eval-at", type=int, nargs="+", default=[0, 25, 50, 100, 200, 300])
    ap.add_argument("--width", type=int, default=192)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--n-colloc", type=int, default=512)
    ap.add_argument("--n-bc", type=int, default=128)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    if args.threads:
        torch.set_num_threads(args.threads)

    t0 = time.time()
    d = ladder_data.load(args.root, field_res=args.field_res)
    nm = d.idx("novel_material")
    Pz = torch.tensor(d.params_z, dtype=torch.float32, device=DEVICE)
    table = build_phys_table(d.params, DEVICE, d.param_keys)
    tau_all = torch.tensor(
        [d.t_final[i] / (0.10 / d.params[i][d.pidx("v")]) for i in range(len(d.params))],
        dtype=torch.float32, device=DEVICE).unsqueeze(1)
    units = [(int(m), nm[d.material_ids[nm] == m]) for m in np.unique(d.material_ids[nm])]

    header = {"POST_HOC": True, "not_in_prereg": "PREREG_L4b_v2.md specifies one Q3 "
              "configuration (300 steps, lr 1e-4, all weights). This sweep runs after it "
              "and tests whether that verdict is configuration-dependent (rule 4).",
              "root": args.root, "field_res": args.field_res, "axis": "material",
              "arm": args.arm, "seeds": args.seeds, "eval_at": args.eval_at,
              "n_colloc": args.n_colloc, "n_bc": args.n_bc,
              "prereg_config": {"steps": 300, "lr": 1e-4, "scope": "all"}}
    res, resumed = load_or_init(args.out, header,
                                ("root", "field_res", "arm", "seeds", "eval_at", "n_colloc", "n_bc"))
    if resumed:
        print(f"  resuming {args.out}")
    print(f"physics at inference — POST-HOC configuration sweep (material axis)\n"
          f"  arm {args.arm}; scope {args.scope}; lrs {args.lrs}; eval at {args.eval_at}; "
          f"{len(units)} held-out materials\n")

    for lr in args.lrs:
        args.refine_lr = lr
        key = f"{args.scope}/lr{lr:g}"
        for seed in args.seeds:
            if get_path(res, "cells", key, str(seed)) is not None:
                continue
            ck = ckpt_path("material", args.arm, seed)
            if not os.path.exists(ck):
                print(f"  {key} seed {seed}: checkpoint missing ({ck}); skipped")
                continue
            t1 = time.time()
            model0 = ParametricPINN(n_params_in=d.params.shape[1], width=args.width,
                                    depth=args.depth, bounded=True).to(DEVICE)
            model0.load_state_dict(torch.load(ck, map_location=DEVICE))
            model0.eval()
            rng = np.random.default_rng(seed)
            acc = {s: [] for s in args.eval_at}
            ids, cids, fails, hists = [], [], 0, {}
            for m, uidx in units:
                per_step, hist, bad = refine_unit_traj(model0, d, uidx, Pz, table,
                                                       tau_all, args, rng, args.eval_at)
                hists[str(m)] = hist
                fails += int(bad)
                base = per_step.get(0)
                for s in args.eval_at:
                    acc[s] += per_step.get(s, base if base is not None else [])
                ids += [m] * len(uidx)
                cids += d.condition_ids[uidx].tolist()
                gc.collect()
            rec = {"means": {str(s): float(np.mean(acc[s])) for s in args.eval_at},
                   "per_sample": {str(s): acc[s] for s in args.eval_at},
                   "material_ids": ids, "condition_ids": cids,
                   "n_failed_units": fails, "loss_hist_per_unit": hists,
                   "lr": lr, "scope": args.scope}
            set_path(res, rec, "cells", key, str(seed))
            write_atomic(res, args.out)
            tr = "  ".join(f"{s}:{rec['means'][str(s)]:.4f}" for s in args.eval_at)
            print(f"  {key:<18} seed {seed}: {tr}   failed {fails}  [{time.time()-t1:.0f}s]",
                  flush=True)
            del model0
            gc.collect()

    print(f"\nwrote {args.out}  [{time.time()-t0:.0f}s]")
    print("\nREAD THIS BEFORE REPORTING: step 0 must reproduce the un-refined error of the\n"
          "same checkpoint in results/l4b_v2_refine.json to within float noise. If it does\n"
          "not, the two scripts are not scoring the same thing and neither number is usable.")


if __name__ == "__main__":
    main()
