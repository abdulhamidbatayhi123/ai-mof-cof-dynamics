"""L4b — WHERE does physics-as-a-loss help? Two axes, one experiment.

L4 tests physics-informing on the novel-MATERIAL axis and (early indications) it
does not help. That is surprising only if one expects a PDE residual to transfer
across materials. It cannot, and the reason is structural:

    A residual can be evaluated at any (z, t), including where there is no data.
    That is the entire mechanism by which physics-informing helps - it supervises
    the DATA-FREE REGION of the coordinates the PDE constrains.

    It is only ever evaluated for materials in the training set, and at inference
    it is not evaluated at all. A held-out material has different PDE
    coefficients the model never saw. Nothing in the residual for material A
    constrains material B.

L4's training data also samples the FULL (z,t) domain for every training
material, so there is no data-free region for the residual to fill. The physics
term is largely redundant with data already present.

This script tests that explanation instead of asserting it, by running the SAME
two arms on two different held-out axes:

  TIME axis      train on t* < `t_cut`, test on t* > `t_cut`, SAME materials.
                 The residual IS evaluated over the full t range, so it supervises
                 exactly where the data stops. Physics SHOULD help here.

  MATERIAL axis  train on all t*, test on held-out materials.
                 The residual says nothing about unseen materials.
                 Physics should NOT help here.

A double dissociation - help on one axis, none on the other - would confirm the
mechanism. Both arms see identical supervised data on each axis, so any
difference is the physics term.

This is also the fair version of the comparison that produced retraction A8,
where the physics arm saw the test window and the baselines did not.
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
from run_l4 import (DEVICE, ParametricPINN, boundary_residual, build_phys_table,
                    causal_weights, index_phys, pde_residual)
from ladder_data import PARAM_KEYS


def sample_supervised_window(d, idx, n, rng, t_lo, t_hi):
    """Supervised points restricted to a time window [t_lo, t_hi] in t*."""
    nz, nt = d.fields.shape[2:]
    lo, hi = int(t_lo * (nt - 1)), int(t_hi * (nt - 1))
    hi = max(hi, lo + 1)
    rows = rng.integers(0, len(idx), n)
    zi = rng.integers(0, nz, n)
    ti = rng.integers(lo, hi + 1, n)
    g = idx[rows]
    return (g, (zi / (nz - 1)).astype(np.float32), (ti / (nt - 1)).astype(np.float32),
            d.fields[g, :, zi, ti].astype(np.float32))


@torch.no_grad()
def eval_window(model, d, idx, params_z, t_lo, t_hi, chunk=65536):
    """nRMSE on c restricted to a time window — per sample."""
    nz, nt = d.fields.shape[2:]
    lo, hi = int(t_lo * (nt - 1)), int(t_hi * (nt - 1))
    ts = np.arange(lo, hi + 1)
    zg, tg = np.meshgrid(np.linspace(0, 1, nz, dtype=np.float32),
                         (ts / (nt - 1)).astype(np.float32), indexing="ij")
    zf = torch.tensor(zg.ravel(), device=DEVICE).unsqueeze(1)
    tf = torch.tensor(tg.ravel(), device=DEVICE).unsqueeze(1)
    out = []
    for gi in idx:
        pv = torch.tensor(params_z[gi], dtype=torch.float32, device=DEVICE)
        chunks = []
        for s0 in range(0, zf.shape[0], chunk):
            e = min(s0 + chunk, zf.shape[0])
            chunks.append(model(pv.unsqueeze(0).expand(e - s0, -1), zf[s0:e], tf[s0:e]).cpu().numpy())
        pred = np.concatenate(chunks, 0).T.reshape(3, nz, len(ts))
        true = d.fields[gi][:, :, ts]
        # Normalise by the range over the FULL reference field, never the range
        # within the evaluation window. After breakthrough c is flat at c_in, so
        # the in-window range collapses (median 0.30, p05 0.0048, min 6.0e-08)
        # and nRMSE explodes for any finite absolute error -- which is what
        # produced the spurious "divergence to nRMSE 26,000" (retraction A15).
        rng_c = float(d.fields[gi][0].max() - d.fields[gi][0].min())
        out.append(float(np.sqrt(np.mean((pred[0] - true[0]) ** 2)) / max(rng_c, 1e-12)))
    return out


def train(arm, d, tr_idx, args, seed, t_lo, t_hi):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = ParametricPINN(width=args.width, depth=args.depth,
                           bounded=args.bounded).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.steps, eta_min=args.lr * 1e-2)
    Pz = torch.tensor(d.params_z, dtype=torch.float32, device=DEVICE)
    table = build_phys_table(d.params, DEVICE)
    tau_all = torch.tensor(
        [d.t_final[i] / (0.10 / d.params[i][d.pidx("v")]) for i in range(len(d.params))],
        dtype=torch.float32, device=DEVICE).unsqueeze(1)

    use_phys = arm != "data_only"
    w_pde = args.w_pde
    for step in range(args.steps):
        opt.zero_grad(set_to_none=True)
        g, z, t, y = sample_supervised_window(d, tr_idx, args.n_sup, rng, t_lo, t_hi)
        gt = torch.tensor(g, device=DEVICE)
        pred = model(Pz[gt], torch.tensor(z, device=DEVICE).unsqueeze(1),
                     torch.tensor(t, device=DEVICE).unsqueeze(1))
        loss = nn.functional.mse_loss(pred, torch.tensor(y, device=DEVICE))
        if args.bounded:
            # the bounded head drops the t-envelope, so the initial condition
            # c(z,0)=q(z,0)=0 becomes an explicit residual
            z0 = torch.rand(args.n_sup // 8, 1, device=DEVICE)
            g0 = tr_idx[rng.integers(0, len(tr_idx), z0.shape[0])]
            p0 = model(Pz[torch.tensor(g0, device=DEVICE)], z0, torch.zeros_like(z0))
            loss = loss + (p0[:, 0:2] ** 2).mean() + ((p0[:, 2:3] - 1.0) ** 2).mean()

        if use_phys:
            cg = tr_idx[rng.integers(0, len(tr_idx), args.n_colloc)]
            cgt = torch.tensor(cg, device=DEVICE)
            # collocation spans the FULL time range, including the held-out window.
            # That is the whole point: the residual supervises where data stops.
            zc = torch.rand(args.n_colloc, 1, device=DEVICE)
            tc = torch.rand(args.n_colloc, 1, device=DEVICE)
            pb = index_phys(table, cgt)
            rm, rk, re = pde_residual(model, Pz[cgt], pb, zc, tc, tau_all[cgt])
            res_sq = rm.pow(2) + rk.pow(2) + re.pow(2)
            # Boundary residuals share the physics weight: without them the PDE
            # term does not determine a solution (defect B20).
            tb = torch.rand(args.n_bc, 1, device=DEVICE)
            bgt = cgt[:args.n_bc] if args.n_bc <= len(cgt) else cgt
            b1, b2, b3, b4 = boundary_residual(model, Pz[bgt], index_phys(table, bgt),
                                               tb[:len(bgt)], tau_all[bgt])
            lp = res_sq.mean() + sum(x.pow(2).mean() for x in (b1, b2, b3, b4))
            if step % args.balance_every == 0:
                gd = torch.autograd.grad(loss, list(model.parameters()), retain_graph=True, allow_unused=True)
                gp = torch.autograd.grad(lp, list(model.parameters()), retain_graph=True, allow_unused=True)
                nd = torch.sqrt(sum(x.pow(2).sum() for x in gd if x is not None))
                npd = torch.sqrt(sum(x.pow(2).sum() for x in gp if x is not None))
                if float(npd) > 0:
                    # `balance_target` is the DESIRED ratio of physics-gradient to
                    # data-gradient norm. Setting it to 1.0 gives the physics term
                    # half the total gradient budget, which measurably starves the
                    # primary objective: at 15000 steps the physics arm still fits
                    # the training data 2x worse than its data-only twin. The
                    # target is therefore swept and each arm reported at ITS best
                    # (protocol s3), rather than fixed at an arbitrary parity.
                    tgt = args.balance_target * float(nd / npd)
                    w_pde = float(np.clip((1 - 0.1) * w_pde + 0.1 * tgt, 1e-8, 1e3))
            loss = loss + w_pde * lp

        if not torch.isfinite(loss):
            raise RuntimeError(f"{arm} non-finite loss at step {step}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sch.step()
    return model, w_pde


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms", nargs="+", default=["data_only", "pi_gradnorm"])
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--t-cut", type=float, default=0.5)
    ap.add_argument("--bounded", action="store_true",
                    help="enforce 0<=c<=c_in, 0<=q<=q_max architecturally")
    ap.add_argument("--width", type=int, default=192)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--n-sup", type=int, default=4096)
    ap.add_argument("--n-colloc", type=int, default=1024)
    ap.add_argument("--n-bc", type=int, default=512)
    ap.add_argument("--w-pde", type=float, default=1.0)
    ap.add_argument("--balance-every", type=int, default=50)
    ap.add_argument("--balance-target", type=float, default=1.0,
                    help="desired |grad L_pde| / |grad L_data|; swept, best kept")
    ap.add_argument("--n-eval", type=int, default=120)
    ap.add_argument("--out", default="results/l4b_results.json")
    args = ap.parse_args()

    t0 = time.time()
    d = ladder_data.load()
    tr = d.idx("train")
    nm = d.idx("novel_material")
    tc = args.t_cut

    print(f"\nTIME axis     : train t* in [0, {tc}]   test t* in [{tc}, 1]  (same materials)")
    print(f"MATERIAL axis : train t* in [0, 1]     test = {len(nm)} held-out materials")
    print(f"{args.steps} steps, {len(args.seeds)} seeds\n")

    res = {"t_cut": tc, "steps": args.steps, "seeds": args.seeds,
           "splits": d.summary(), "axes": {}}

    for axis in ("time", "material"):
        res["axes"][axis] = {}
        lo, hi = (0.0, tc) if axis == "time" else (0.0, 1.0)
        for arm in args.arms:
            res["axes"][axis][arm] = {}
            for seed in args.seeds:
                t1 = time.time()
                model, wf = train(arm, d, tr, args, seed, lo, hi)
                model.eval()
                if axis == "time":
                    seen = eval_window(model, d, tr[:args.n_eval], d.params_z, 0.0, tc)
                    held = eval_window(model, d, tr[:args.n_eval], d.params_z, tc, 1.0)
                    ids = d.material_ids[tr[:args.n_eval]]
                else:
                    seen = eval_window(model, d, tr[:args.n_eval], d.params_z, 0.0, 1.0)
                    held = eval_window(model, d, nm[:args.n_eval], d.params_z, 0.0, 1.0)
                    ids = d.material_ids[nm[:args.n_eval]]
                res["axes"][axis][arm][str(seed)] = {
                    "balance_target": args.balance_target,
                    "seen": float(np.mean(seen)), "held": float(np.mean(held)),
                    "per_sample_held": [float(x) for x in held],
                    "material_ids": ids.tolist(), "w_pde_final": wf,
                }
                print(f"  [{axis:<8}] {arm:<12} seed {seed}: seen={np.mean(seen):.4f} "
                      f"held={np.mean(held):.4f}  [{time.time() - t1:.0f}s]", flush=True)
                del model; gc.collect()
            os.makedirs(os.path.dirname(args.out), exist_ok=True)
            json.dump(res, open(args.out, "w"), indent=2)

    print(f"\nwrote {args.out}  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
