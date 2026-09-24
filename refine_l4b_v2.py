"""Physics at inference — test-time refinement of a trained L4b-v2 model (PREREG Q3).

The legacy argument for why a PDE residual cannot help on the material axis was
that it is "evaluated only for training materials and never at inference". True of
the arm as built; not of physics-informed learning. This is the version that CAN
act on the material axis: freeze the trained model, and for each unseen unit
minimise the residual for that unit's own parameters with NO data.

  material axis   each of the 48 held-out materials, all its conditions batched,
                  collocation over the full (z, t) domain, residual + BC + IC,
                  300 Adam steps at lr 1e-4, all weights free. No anchor: nothing
                  about the material is known.
  time axis       each training material in the evaluation subset, collocation over
                  the full domain, plus an anchor (MSE to the frozen model's own
                  prediction on the seen window t* < t_cut, weight 1) so the seen
                  region cannot drift.

Scored before and after, per sample, on the same held-out quantity as the sweep.
Applied to data_only and, as a control, to the best physics arm of the sweep.
Cells are written as they complete and skipped on resume.
"""
from __future__ import annotations

import argparse
import copy
import gc
import os
import time

import numpy as np

from v2_common import best_physics_arm
import torch
import torch.nn as nn

import ladder_data
from run_l4 import DEVICE, ParametricPINN, build_phys_table
from run_l4b import eval_window
from run_l4b_v2 import ckpt_path, eval_subset, physics_terms
from v2_common import FIELD_RES, ROOT_V2, get_path, load_or_init, set_path, write_atomic


def refine_unit(model0, d, unit_idx, Pz, table, tau_all, args, rng, anchor_window=None):
    """Return a refined COPY of model0 for the samples in `unit_idx`."""
    model = copy.deepcopy(model0)
    model.train()
    frozen = copy.deepcopy(model0).eval()
    opt = torch.optim.Adam(model.parameters(), lr=args.refine_lr)
    hist = []
    for step in range(args.refine_steps):
        opt.zero_grad(set_to_none=True)
        cg = unit_idx[rng.integers(0, len(unit_idx), args.n_colloc)]
        zc = torch.rand(args.n_colloc, 1, device=DEVICE)
        tc = torch.rand(args.n_colloc, 1, device=DEVICE)
        bg = cg[:args.n_bc]
        tb = torch.rand(len(bg), 1, device=DEVICE)
        res_sq, bc_sq = physics_terms(model, Pz, table, tau_all, cg, zc, tc, bg, tb)
        n_ic = args.n_bc
        z0 = torch.rand(n_ic, 1, device=DEVICE)
        g0 = torch.tensor(unit_idx[rng.integers(0, len(unit_idx), n_ic)], device=DEVICE)
        p0 = model(Pz[g0], z0, torch.zeros_like(z0))
        loss = res_sq.mean() + bc_sq.mean() + (p0[:, 0:2] ** 2).mean() + ((p0[:, 2:3] - 1.0) ** 2).mean()
        if anchor_window is not None:
            lo, hi = anchor_window
            ga = torch.tensor(unit_idx[rng.integers(0, len(unit_idx), args.n_colloc)], device=DEVICE)
            za = torch.rand(args.n_colloc, 1, device=DEVICE)
            ta = lo + (hi - lo) * torch.rand(args.n_colloc, 1, device=DEVICE)
            with torch.no_grad():
                target = frozen(Pz[ga], za, ta)
            loss = loss + args.anchor_w * nn.functional.mse_loss(model(Pz[ga], za, ta), target)
        if not torch.isfinite(loss):
            return None, hist
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step % 50 == 0 or step == args.refine_steps - 1:
            hist.append({"step": step, "loss": float(loss.detach())})
    model.eval()
    return model, hist


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT_V2)
    ap.add_argument("--field-res", type=int, default=FIELD_RES)
    ap.add_argument("--sweep", default="results/l4b_v2_results.json")
    ap.add_argument("--arms", nargs="+", default=None,
                    help="default: data_only and the best physics arm per axis from the sweep")
    ap.add_argument("--axes", nargs="+", default=["material", "time"])
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--t-cut", type=float, default=0.5)
    ap.add_argument("--width", type=int, default=192)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--refine-steps", type=int, default=300)
    ap.add_argument("--refine-lr", type=float, default=1e-4)
    ap.add_argument("--n-colloc", type=int, default=512)
    ap.add_argument("--n-bc", type=int, default=128)
    ap.add_argument("--anchor-w", type=float, default=1.0)
    ap.add_argument("--eval-per-material", type=int, default=4)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--out", default="results/l4b_v2_refine.json")
    args = ap.parse_args()
    if args.threads:
        torch.set_num_threads(args.threads)

    t0 = time.time()
    import json
    sw = json.load(open(args.sweep))
    d = ladder_data.load(args.root, field_res=args.field_res)
    tr, nm = d.idx("train"), d.idx("novel_material")
    tr_eval = eval_subset(d, tr, args.eval_per_material)
    Pz = torch.tensor(d.params_z, dtype=torch.float32, device=DEVICE)
    table = build_phys_table(d.params, DEVICE, d.param_keys)
    tau_all = torch.tensor(
        [d.t_final[i] / (0.10 / d.params[i][d.pidx("v")]) for i in range(len(d.params))],
        dtype=torch.float32, device=DEVICE).unsqueeze(1)

    header = {"root": args.root, "field_res": args.field_res, "t_cut": args.t_cut, "sweep": args.sweep,
              "refine_steps": args.refine_steps, "refine_lr": args.refine_lr, "n_colloc": args.n_colloc,
              "n_bc": args.n_bc, "anchor_w": args.anchor_w, "seeds": args.seeds,
              "eval_per_material": args.eval_per_material}
    res, resumed = load_or_init(args.out, header, ("root", "field_res", "t_cut", "refine_steps",
                                                   "refine_lr", "n_colloc", "n_bc", "anchor_w", "seeds"))
    if resumed:
        print(f"  resuming {args.out}")

    for axis in args.axes:
        S = sw.get("sweep", {}).get(axis, {})
        arms = args.arms
        if arms is None:
            # PREREG §4.1's eligibility, shared with the analyser and the polish.
            # This site used to apply only the non-finite-loss half, so it could
            # refine an arm the analyser simultaneously reports as failed-to-train.
            bp = best_physics_arm(S, args.seeds)
            arms = ["data_only"] + ([bp] if bp else [])
        units = ([(int(m), nm[d.material_ids[nm] == m]) for m in np.unique(d.material_ids[nm])]
                 if axis == "material" else
                 [(int(m), tr_eval[d.material_ids[tr_eval] == m]) for m in np.unique(d.material_ids[tr_eval])])
        win = (0.0, args.t_cut) if axis == "time" else None
        print(f"\n[{axis}] arms {arms}; {len(units)} units")
        for arm in arms:
            if str(args.seeds[0]) not in S.get(arm, {}):
                print(f"  {arm}: not in the sweep yet; skipped")
                continue
            for seed in args.seeds:
                if get_path(res, axis, arm, str(seed)) is not None:
                    continue
                if not os.path.exists(ckpt_path(axis, arm, seed)):
                    print(f"  {arm} seed {seed}: checkpoint missing; skipped")
                    continue
                t1 = time.time()
                model0 = ParametricPINN(n_params_in=d.params.shape[1], width=args.width,
                                        depth=args.depth, bounded=True).to(DEVICE)
                model0.load_state_dict(torch.load(ckpt_path(axis, arm, seed), map_location=DEVICE))
                model0.eval()
                rng = np.random.default_rng(seed)
                before, after, seen_b, seen_a, ids, cids, fails, hists = [], [], [], [], [], [], 0, {}
                for m, uidx in units:
                    if axis == "time":
                        b = eval_window(model0, d, uidx, d.params_z, args.t_cut, 1.0)
                        sb = eval_window(model0, d, uidx, d.params_z, 0.0, args.t_cut)
                    else:
                        b = eval_window(model0, d, uidx, d.params_z, 0.0, 1.0)
                        sb = b
                    model, hist = refine_unit(model0, d, uidx, Pz, table, tau_all, args, rng, anchor_window=win)
                    hists[str(m)] = hist                     # the residual-loss trajectory, per unit
                    if model is None:
                        fails += 1
                        a, sa_ = b, sb
                    elif axis == "time":
                        a = eval_window(model, d, uidx, d.params_z, args.t_cut, 1.0)
                        sa_ = eval_window(model, d, uidx, d.params_z, 0.0, args.t_cut)
                    else:
                        a = eval_window(model, d, uidx, d.params_z, 0.0, 1.0)
                        sa_ = a
                    before += b; after += a; seen_b += sb; seen_a += sa_
                    ids += [m] * len(uidx); cids += d.condition_ids[uidx].tolist()
                    del model; gc.collect()
                rec = {"before": float(np.mean(before)), "after": float(np.mean(after)),
                       "seen_before": float(np.mean(seen_b)), "seen_after": float(np.mean(seen_a)),
                       "per_sample_before": before, "per_sample_after": after,
                       "per_sample_seen_before": seen_b, "per_sample_seen_after": seen_a,
                       "material_ids": ids, "condition_ids": cids, "n_failed_units": fails,
                       "loss_hist_per_unit": hists}
                set_path(res, rec, axis, arm, str(seed))
                write_atomic(res, args.out)
                print(f"  [{axis:<8}] {arm:<18} seed {seed}: held {rec['before']:.4f} -> {rec['after']:.4f} | "
                      f"seen {rec['seen_before']:.4f} -> {rec['seen_after']:.4f} | failed units {fails}  "
                      f"[{time.time()-t1:.0f}s]", flush=True)
                del model0; gc.collect()

    print(f"\nwrote {args.out}  [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
