"""Does the operator improve with material count too, or only POD + boosting?

`learning_curve.py` found that novel-material error falls steeply with the number
of distinct training MATERIALS while being flat in every capacity axis the ladder
tested. If that holds only for POD + gradient boosting it is a property of one
weak arm; if it holds for DeepONet — the best arm anywhere in the ladder — it is a
property of the problem, and it overturns L1's recorded verdict.

Same architecture, encoding, budget, optimiser and seeds as `run_l5.py` at its
best setting (p = 32, lr = 1e-3, 8000 steps, ~200 k parameters). The ONLY thing
that varies is how many training materials the model sees. Subsampling is by
MATERIAL, keeping all of that material's conditions, because novel-material
transfer is the axis in question.

Matched budget is preserved on purpose: every arm trains for the same 8000 steps
regardless of dataset size, so a smaller-data arm is not additionally handicapped
by fewer gradient updates. That confound produced retractions A14 and A16.

Output: results/deeponet_lc.json
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn

import ladder_data
from run_l5 import DEVICE, DeepONet, n_params_of, solve_width, subsample

FRACS = (0.25, 0.50, 0.75, 1.00)


def train_eval_subset(F, coords, d, tr_sub, args, p, width, seed):
    """run_l5.train_eval, but training only on `tr_sub`."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    nm = d.idx("novel_material")
    model = DeepONet(d.params_z.shape[1], p=p, width=width, depth=args.depth,
                     kan=False).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.steps,
                                                     eta_min=args.lr * 1e-2)
    Pz = torch.tensor(d.params_z, dtype=torch.float32, device=DEVICE)
    C = torch.tensor(coords, device=DEVICE)
    Ft = torch.tensor(F.reshape(F.shape[0], 3, -1).transpose(0, 2, 1), device=DEVICE)

    for step in range(args.steps):
        opt.zero_grad(set_to_none=True)
        bi = torch.tensor(tr_sub[rng.integers(0, len(tr_sub), args.batch)], device=DEVICE)
        pi = torch.tensor(rng.integers(0, C.shape[0], args.n_pts), device=DEVICE)
        loss = nn.functional.mse_loss(model(Pz[bi], C[pi]), Ft[bi][:, pi, :])
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss at step {step}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sch.step()

    model.eval()
    out = {}
    with torch.no_grad():
        for tag, idx in (("train", tr_sub[:150]), ("novel_material", nm)):
            per = []
            for s0 in range(0, len(idx), 16):
                bi = torch.tensor(idx[s0:s0 + 16], device=DEVICE)
                pr = model(Pz[bi], C).cpu().numpy()[..., 0]
                tr_ = Ft[bi].cpu().numpy()[..., 0]
                rngc = tr_.max(1) - tr_.min(1)
                per += list(np.sqrt(((pr - tr_) ** 2).mean(1)) / np.maximum(rngc, 1e-12))
            out[tag] = {"c": float(np.mean(per)),
                        "per_sample_nrmse_c": [float(x) for x in per],
                        "material_ids": d.material_ids[idx].tolist()}
    del model; gc.collect()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--steps", type=int, default=8000)
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--budget", type=int, default=200_000)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--n-pts", type=int, default=2048)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--fracs", type=float, nargs="+", default=list(FRACS))
    ap.add_argument("--out", default="results/deeponet_lc.json")
    args = ap.parse_args()

    t0 = time.time()
    d = ladder_data.load()
    F, coords = subsample(d)
    tr = d.idx("train")
    tr_mats = np.unique(d.material_ids[tr])
    w, npar = solve_width(d.params_z.shape[1], args.p, args.depth, args.budget, False)
    print(f"\nDeepONet p={args.p} width={w} params={npar} lr={args.lr} "
          f"steps={args.steps} (matched at every data size)")
    print(f"train pool: {len(tr)} conditions over {len(tr_mats)} materials\n")

    res = {"p": args.p, "lr": args.lr, "steps": args.steps, "width": w,
           "n_params": npar, "fracs": args.fracs, "seeds": args.seeds,
           "n_train_materials": int(len(tr_mats)), "rows": []}

    for f in args.fracs:
        row = {"frac": f, "seeds": {}}
        for seed in args.seeds:
            rng = np.random.default_rng(seed)
            if f >= 1.0:
                sub = tr
            else:
                k = max(2, int(round(f * len(tr_mats))))
                keep = set(rng.choice(tr_mats, size=k, replace=False))
                sub = np.array([i for i in tr if d.material_ids[i] in keep])
            t1 = time.time()
            o = train_eval_subset(F, coords, d, sub, args, args.p, w, seed)
            o["n_train"] = int(len(sub))
            o["n_materials"] = int(len(np.unique(d.material_ids[sub])))
            row["seeds"][str(seed)] = o
            print(f"  frac={f:.2f}  {o['n_materials']:>2} mats / {len(sub):>3} cond  "
                  f"seed {seed}: train={o['train']['c']:.4f} "
                  f"novel={o['novel_material']['c']:.4f} [{time.time() - t1:.0f}s]",
                  flush=True)
        m = np.mean([row["seeds"][s]["novel_material"]["c"] for s in row["seeds"]])
        sd = np.std([row["seeds"][s]["novel_material"]["c"] for s in row["seeds"]])
        row["novel_mean"], row["novel_sd"] = float(m), float(sd)
        print(f"  -> frac={f:.2f}: novel {m:.4f} +- {sd:.4f}\n")
        res["rows"].append(row)
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        json.dump(res, open(args.out, "w"), indent=2)

    a, b = res["rows"][0], res["rows"][-1]
    print(f"novel-material error {a['novel_mean']:.4f} -> {b['novel_mean']:.4f} "
          f"({a['novel_mean'] / b['novel_mean']:.2f}x) as materials go "
          f"{a['seeds'][str(args.seeds[0])]['n_materials']} -> "
          f"{b['seeds'][str(args.seeds[0])]['n_materials']}")
    print(f"\nwrote {args.out}  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
