"""L4b on dataset v2 — the physics-weighting sweep. Design frozen in PREREG_L4b_v2.md.

The disputed legacy claim: with a bounded output head, physics-as-a-loss is WORSE
than its data-only twin on the time axis and no better on the material axis. It
rested on one weighting rule at one target. This script gives the physics arm
every weighting scheme the literature offers, at matched architecture, steps,
supervised budget and seeds, and records what each does.

Arms (all bounded head; the unbounded head is settled)
  data_only              no physics term
  pi_fixed_w{W}          fixed w_pde, W in {1e-4, 1e-3, 1e-2, 1e-1, 1}
  pi_gradnorm_t{T}       gradient-norm balancing at target ratio T in {0.1, 1.0, 10}
                         (Wang, Teng & Perdikaris, SISC 2021; T = 1.0 is legacy L4b)
  pi_ntk                 NTK weighting (Wang, Yu & Perdikaris, JCP 2022): per-term
                         weights from per-point gradient norms, EMA-smoothed
  pi_sa                  self-adaptive weights (McClenny & Braga-Neto, JCP 2023):
                         a fixed collocation set with one trainable weight per
                         point, maximised while the network minimises

Every physics arm carries the interior residual AND the Danckwerts boundary
residuals (defect B20). Every arm carries the initial-condition residual the
bounded head needs.

Axes
  time       train t* in [0, 0.5], score t* in [0.5, 1] on a material-stratified
             subset of the TRAINING samples (4 conditions x 192 materials)
  material   train t* in [0, 1], score all 793 held-out samples (48 materials)

Stages
  --stage sweep    the arms above (default)
  --stage polish   L-BFGS polish of data_only and the best physics arm per axis,
                   loaded from their checkpoints (PREREG Q4)

Every (axis, arm, seed) cell is written as it completes and skipped on resume;
every trained model's state_dict is saved under data/l4b_v2_ckpt/ for the
refinement and polish stages and for figure regeneration.
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
                    index_phys, pde_residual)
from run_l4b import eval_window, sample_supervised_window
from v2_common import FIELD_RES, ROOT_V2, get_path, load_or_init, set_path, write_atomic
from v2_common import best_physics_arm

CKPT_DIR = "data/l4b_v2_ckpt"
ARMS = ["data_only",
        # w1e-5 is the PREREG §4.2 extension: the fixed-weight optimum sat on the
        # bottom edge of the original four-decade grid and was NOT saturated
        # against the data-only twin on the time axis, so the rule binds.
        "pi_fixed_w1e-5",
        "pi_fixed_w1e-4", "pi_fixed_w1e-3", "pi_fixed_w1e-2", "pi_fixed_w1e-1", "pi_fixed_w1",
        "pi_gradnorm_t0.1", "pi_gradnorm_t1.0", "pi_gradnorm_t10",
        "pi_ntk", "pi_sa"]
AXES = ("time", "material")


def parse_arm(arm):
    if arm == "data_only":
        return {"scheme": "none"}
    if arm.startswith("pi_fixed_w"):
        return {"scheme": "fixed", "w": float(arm[len("pi_fixed_w"):])}
    if arm.startswith("pi_gradnorm_t"):
        return {"scheme": "gradnorm", "target": float(arm[len("pi_gradnorm_t"):])}
    if arm == "pi_ntk":
        return {"scheme": "ntk"}
    if arm == "pi_sa":
        return {"scheme": "sa"}
    raise ValueError(arm)


def ckpt_path(axis, arm, seed, tag=""):
    return os.path.join(CKPT_DIR, f"{axis}_{arm}_s{seed}{tag}.pth")


def eval_subset(d, tr_idx, per_material=4, seed=0):
    """Material-stratified training subset for the time axis and for train error.

    Legacy L4b scored `tr[:120]` — about seven materials. Four conditions from each
    of the 192 training materials gives 192 clusters, drawn once and identical for
    every arm and seed.
    """
    rng = np.random.default_rng(seed)
    out = []
    for m in np.unique(d.material_ids[tr_idx]):
        idx = tr_idx[d.material_ids[tr_idx] == m]
        out.extend(rng.choice(idx, size=min(per_material, len(idx)), replace=False).tolist())
    return np.array(sorted(out))


def ic_residual(model, Pz, tr_idx, rng, n):
    z0 = torch.rand(n, 1, device=DEVICE)
    g0 = tr_idx[rng.integers(0, len(tr_idx), n)]
    p0 = model(Pz[torch.tensor(g0, device=DEVICE)], z0, torch.zeros_like(z0))
    return (p0[:, 0:2] ** 2).mean() + ((p0[:, 2:3] - 1.0) ** 2).mean()


def physics_terms(model, Pz, table, tau_all, cg, zc, tc, bg, tb):
    """Per-point interior residual (n,1) and per-point boundary residual (m,1)."""
    cgt = torch.tensor(cg, device=DEVICE)
    rm, rk, re = pde_residual(model, Pz[cgt], index_phys(table, cgt), zc, tc, tau_all[cgt])
    res_sq = rm.pow(2) + rk.pow(2) + re.pow(2)
    bgt = torch.tensor(bg, device=DEVICE)
    b1, b2, b3, b4 = boundary_residual(model, Pz[bgt], index_phys(table, bgt), tb, tau_all[bgt])
    bc_sq = b1.pow(2) + b2.pow(2) + b3.pow(2) + b4.pow(2)
    return res_sq, bc_sq


def grad_norm(loss, params):
    g = torch.autograd.grad(loss, params, retain_graph=True, allow_unused=True)
    return torch.sqrt(sum(x.pow(2).sum() for x in g if x is not None))


def ntk_trace(residuals, params):
    """Mean over points of ||grad_theta r_j||^2, summed over residual components.

    `residuals` is a list of (n,1) tensors that share a graph. This is the
    per-point (diagonal) estimate of the trace of the term's empirical NTK,
    normalised per point so that it matches a mean-over-points loss.
    """
    tot, n = 0.0, 0
    for r in residuals:
        for j in range(r.shape[0]):
            g = torch.autograd.grad(r[j, 0], params, retain_graph=True, allow_unused=True)
            tot += float(sum(x.pow(2).sum() for x in g if x is not None))
            n += 1
    return tot / max(n, 1)


def train(arm, d, tr_idx, args, seed, t_lo, t_hi):
    cfg = parse_arm(arm)
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = ParametricPINN(n_params_in=d.params.shape[1], width=args.width, depth=args.depth,
                           bounded=True).to(DEVICE)
    params = list(model.parameters())
    opt = torch.optim.Adam(params, lr=args.lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.steps, eta_min=args.lr * 1e-2)
    Pz = torch.tensor(d.params_z, dtype=torch.float32, device=DEVICE)
    table = build_phys_table(d.params, DEVICE, d.param_keys)
    tau_all = torch.tensor(
        [d.t_final[i] / (0.10 / d.params[i][d.pidx("v")]) for i in range(len(d.params))],
        dtype=torch.float32, device=DEVICE).unsqueeze(1)

    scheme = cfg["scheme"]
    w_pde = {"fixed": cfg.get("w", 1.0), "gradnorm": args.w_init, "ntk": args.w_init,
             "sa": 1.0, "none": 0.0}[scheme]
    w_bc = w_pde
    sa = None
    if scheme == "sa":
        # a fixed collocation pool with one trainable weight per point; each step
        # draws a minibatch of the pool so the per-step cost matches the other arms
        n_pool, n_bpool = args.sa_pool, args.sa_pool // 2
        sa = {"cg": tr_idx[rng.integers(0, len(tr_idx), n_pool)],
              "zc": torch.rand(n_pool, 1, device=DEVICE), "tc": torch.rand(n_pool, 1, device=DEVICE),
              "bg": tr_idx[rng.integers(0, len(tr_idx), n_bpool)],
              "tb": torch.rand(n_bpool, 1, device=DEVICE)}
        s0 = float(np.log(np.e - 1.0))                           # softplus(s0) = 1
        sa["s_pde"] = torch.full((n_pool, 1), s0, device=DEVICE, requires_grad=True)
        sa["s_bc"] = torch.full((n_bpool, 1), s0, device=DEVICE, requires_grad=True)
        sa["opt"] = torch.optim.Adam([sa["s_pde"], sa["s_bc"]], lr=args.sa_lr, maximize=True)

    hist, failed = [], None
    for step in range(args.steps):
        opt.zero_grad(set_to_none=True)
        g, z, t, y = sample_supervised_window(d, tr_idx, args.n_sup, rng, t_lo, t_hi)
        gt = torch.tensor(g, device=DEVICE)
        pred = model(Pz[gt], torch.tensor(z, device=DEVICE).unsqueeze(1),
                     torch.tensor(t, device=DEVICE).unsqueeze(1))
        l_data = nn.functional.mse_loss(pred, torch.tensor(y, device=DEVICE))
        l_data = l_data + ic_residual(model, Pz, tr_idx, rng, args.n_sup // 8)
        loss = l_data
        rec = {"step": step, "data": float(l_data.detach())}

        if scheme != "none":
            if scheme == "sa":
                if sa["opt"] is not None:
                    sa["opt"].zero_grad(set_to_none=True)
                ci = torch.tensor(rng.integers(0, args.sa_pool, args.n_colloc), device=DEVICE)
                bi = torch.tensor(rng.integers(0, args.sa_pool // 2, args.n_bc), device=DEVICE)
                res_sq, bc_sq = physics_terms(model, Pz, table, tau_all,
                                              sa["cg"][ci.cpu().numpy()], sa["zc"][ci], sa["tc"][ci],
                                              sa["bg"][bi.cpu().numpy()], sa["tb"][bi])
                wp = nn.functional.softplus(sa["s_pde"][ci])
                wb = nn.functional.softplus(sa["s_bc"][bi])
                l_pde = (wp * res_sq).mean()
                l_bc = (wb * bc_sq).mean()
                loss = loss + l_pde + l_bc
                rec.update({"pde": float(res_sq.mean().detach()), "bc": float(bc_sq.mean().detach()),
                            "w_pde": float(wp.mean().detach()), "w_bc": float(wb.mean().detach())})
            else:
                cg = tr_idx[rng.integers(0, len(tr_idx), args.n_colloc)]
                zc = torch.rand(args.n_colloc, 1, device=DEVICE)
                tc = torch.rand(args.n_colloc, 1, device=DEVICE)      # full time range, on purpose
                bg = cg[:args.n_bc]
                tb = torch.rand(len(bg), 1, device=DEVICE)
                res_sq, bc_sq = physics_terms(model, Pz, table, tau_all, cg, zc, tc, bg, tb)
                l_pde, l_bc = res_sq.mean(), bc_sq.mean()
                if scheme == "gradnorm" and step % args.balance_every == 0:
                    nd = grad_norm(l_data, params)
                    npd = grad_norm(l_pde + l_bc, params)
                    if float(npd) > 0:
                        tgt = cfg["target"] * float(nd / npd)
                        w_pde = float(np.clip(0.9 * w_pde + 0.1 * tgt, 1e-8, 1e3))
                    w_bc = w_pde
                elif scheme == "ntk" and step % args.balance_every == 0:
                    k = args.ntk_pts
                    tr_d = ntk_trace([pred[:k, i:i + 1] - torch.tensor(y[:k, i:i + 1], device=DEVICE)
                                      for i in range(3)], params)
                    cgt = torch.tensor(cg[:k], device=DEVICE)
                    rm, rk, re = pde_residual(model, Pz[cgt], index_phys(table, cgt), zc[:k], tc[:k], tau_all[cgt])
                    tr_p = ntk_trace([rm, rk, re], params)
                    bgt = torch.tensor(bg[:k], device=DEVICE)
                    bres = boundary_residual(model, Pz[bgt], index_phys(table, bgt), tb[:k], tau_all[bgt])
                    tr_b = ntk_trace(list(bres), params)
                    if tr_p > 0 and tr_b > 0 and tr_d > 0:
                        w_pde = float(np.clip(0.9 * w_pde + 0.1 * (tr_d / tr_p), 1e-8, 1e3))
                        w_bc = float(np.clip(0.9 * w_bc + 0.1 * (tr_d / tr_b), 1e-8, 1e3))
                loss = loss + w_pde * l_pde + w_bc * l_bc
                rec.update({"pde": float(l_pde.detach()), "bc": float(l_bc.detach()),
                            "w_pde": w_pde, "w_bc": w_bc})

        if not torch.isfinite(loss):
            failed = f"non-finite loss at step {step}"
            break
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step(); sch.step()
        if sa is not None:
            sa["opt"].step()
        if step % max(1, args.steps // 16) == 0 or step == args.steps - 1:
            hist.append(rec)
    final = {"w_pde": w_pde, "w_bc": w_bc}
    if sa is not None:
        final = {"w_pde": float(nn.functional.softplus(sa["s_pde"]).mean()),
                 "w_bc": float(nn.functional.softplus(sa["s_bc"]).mean()),
                 "w_pde_p95": float(nn.functional.softplus(sa["s_pde"]).quantile(0.95))}
    return model, hist, final, failed


def score(model, d, axis, tr_eval, nm, tc):
    """Per-sample nRMSE(c): seen window/materials, and held-out."""
    if axis == "time":
        seen = eval_window(model, d, tr_eval, d.params_z, 0.0, tc)
        held = eval_window(model, d, tr_eval, d.params_z, tc, 1.0)
        ids = d.material_ids[tr_eval]; cids = d.condition_ids[tr_eval]
    else:
        seen = eval_window(model, d, tr_eval, d.params_z, 0.0, 1.0)
        held = eval_window(model, d, nm, d.params_z, 0.0, 1.0)
        ids = d.material_ids[nm]; cids = d.condition_ids[nm]
    return {"seen": float(np.mean(seen)), "held": float(np.mean(held)),
            "per_sample_held": [float(x) for x in held], "per_sample_seen": [float(x) for x in seen],
            "material_ids": ids.tolist(), "condition_ids": cids.tolist()}


# ─────────────────────────────────────────────────────────────────────────────
# stage 2: L-BFGS polish (PREREG Q4)
# ─────────────────────────────────────────────────────────────────────────────

def polish(model, d, tr_idx, args, seed, t_lo, t_hi, w_pde, w_bc, use_phys):
    """Identical L-BFGS polish on FIXED batches for both arms of a pair."""
    rng = np.random.default_rng(10_000 + seed)
    Pz = torch.tensor(d.params_z, dtype=torch.float32, device=DEVICE)
    table = build_phys_table(d.params, DEVICE, d.param_keys)
    tau_all = torch.tensor(
        [d.t_final[i] / (0.10 / d.params[i][d.pidx("v")]) for i in range(len(d.params))],
        dtype=torch.float32, device=DEVICE).unsqueeze(1)
    g, z, t, y = sample_supervised_window(d, tr_idx, args.polish_sup, rng, t_lo, t_hi)
    gt = torch.tensor(g, device=DEVICE)
    zt, tt, yt = (torch.tensor(z, device=DEVICE).unsqueeze(1), torch.tensor(t, device=DEVICE).unsqueeze(1),
                  torch.tensor(y, device=DEVICE))
    n_ic = args.polish_sup // 8
    z0 = torch.rand(n_ic, 1, device=DEVICE)
    g0 = torch.tensor(tr_idx[rng.integers(0, len(tr_idx), n_ic)], device=DEVICE)
    cg = tr_idx[rng.integers(0, len(tr_idx), args.polish_colloc)]
    zc = torch.rand(args.polish_colloc, 1, device=DEVICE)
    tcl = torch.rand(args.polish_colloc, 1, device=DEVICE)
    bg = cg[:args.polish_bc]
    tb = torch.rand(len(bg), 1, device=DEVICE)
    params = list(model.parameters())
    opt = torch.optim.LBFGS(params, lr=1.0, max_iter=args.polish_iters, history_size=50,
                            line_search_fn="strong_wolfe", tolerance_grad=1e-10, tolerance_change=1e-12)
    state = {"n": 0, "last": None}

    def closure():
        opt.zero_grad(set_to_none=True)
        pred = model(Pz[gt], zt, tt)
        loss = nn.functional.mse_loss(pred, yt)
        p0 = model(Pz[g0], z0, torch.zeros_like(z0))
        loss = loss + (p0[:, 0:2] ** 2).mean() + ((p0[:, 2:3] - 1.0) ** 2).mean()
        if use_phys:
            res_sq, bc_sq = physics_terms(model, Pz, table, tau_all, cg, zc, tcl, bg, tb)
            loss = loss + w_pde * res_sq.mean() + w_bc * bc_sq.mean()
        if not torch.isfinite(loss):
            raise RuntimeError("non-finite loss in L-BFGS polish")
        loss.backward()
        state["n"] += 1; state["last"] = float(loss)
        return loss

    opt.step(closure)
    return state["n"], state["last"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT_V2)
    ap.add_argument("--field-res", type=int, default=FIELD_RES)
    ap.add_argument("--stage", choices=["sweep", "polish"], default="sweep")
    ap.add_argument("--arms", nargs="+", default=ARMS)
    ap.add_argument("--axes", nargs="+", default=list(AXES))
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--t-cut", type=float, default=0.5)
    ap.add_argument("--width", type=int, default=192)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--steps", type=int, default=8000)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--n-sup", type=int, default=4096)
    ap.add_argument("--n-colloc", type=int, default=1024)
    ap.add_argument("--n-bc", type=int, default=512)
    ap.add_argument("--w-init", type=float, default=1.0, help="initial weight for gradnorm/ntk")
    ap.add_argument("--balance-every", type=int, default=50)
    ap.add_argument("--ntk-pts", type=int, default=16)
    ap.add_argument("--sa-pool", type=int, default=16384)
    ap.add_argument("--sa-lr", type=float, default=5e-3)
    ap.add_argument("--eval-per-material", type=int, default=4)
    ap.add_argument("--polish-iters", type=int, default=500)
    ap.add_argument("--polish-sup", type=int, default=16384)
    ap.add_argument("--polish-colloc", type=int, default=2048)
    ap.add_argument("--polish-bc", type=int, default=512)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--out", default="results/l4b_v2_results.json")
    args = ap.parse_args()
    if args.threads:
        torch.set_num_threads(args.threads)

    t0 = time.time()
    d = ladder_data.load(args.root, field_res=args.field_res)
    tr, nm = d.idx("train"), d.idx("novel_material")
    tr_eval = eval_subset(d, tr, args.eval_per_material)
    n_par = sum(p.numel() for p in ParametricPINN(n_params_in=d.params.shape[1], width=args.width,
                                                   depth=args.depth, bounded=True).parameters())

    # B37's class: the Glueckauf k_LDF rebuilt from the vector must match the record
    man_k = {(s["mat"], s["cond"]): s.get("k_LDF") for s in d.meta["samples"]}
    from run_l4 import physics_from_params
    for i in range(0, len(d.params), 97):
        k_rec = man_k.get((int(d.material_ids[i]), int(d.condition_ids[i])))
        if k_rec is not None:
            k_der = physics_from_params(d.params[i], d.param_keys).k_LDF
            if abs(k_der - k_rec) > 1e-9 * abs(k_rec):
                raise SystemExit(f"ABORT: k_LDF mismatch at sample {i}: {k_der} vs {k_rec} (B37)")

    header = {"root": args.root, "field_res": args.field_res, "field_shape": list(d.fields.shape[2:]),
              "t_cut": args.t_cut, "width": args.width, "depth": args.depth, "n_params": n_par,
              "steps": args.steps, "lr": args.lr, "n_sup": args.n_sup, "n_colloc": args.n_colloc,
              "n_bc": args.n_bc, "seeds": args.seeds, "balance_every": args.balance_every,
              "sa_pool": args.sa_pool, "sa_lr": args.sa_lr, "ntk_pts": args.ntk_pts,
              "eval_per_material": args.eval_per_material, "n_eval_time": int(len(tr_eval)),
              "n_eval_material": int(len(nm)), "arms_all": ARMS, "param_keys": list(d.param_keys)}
    res, resumed = load_or_init(args.out, header, ("root", "field_res", "t_cut", "width", "depth",
                                                   "steps", "lr", "n_sup", "n_colloc", "n_bc", "seeds",
                                                   "eval_per_material"))
    if resumed:
        print(f"  resuming {args.out}")
        # load_or_init returns the PREVIOUS header on resume, so `arms_all` would
        # stay the eleven-arm list after the PREREG §4.2 extension adds a twelfth
        # and the analyser would print "12/11 arms complete". `arms_all` is the
        # only machine-readable record of what the sweep was meant to contain, so
        # any completeness assertion built on it has to see the extension.
        res["arms_all"] = sorted(set(res.get("arms_all", [])) | set(ARMS))
    os.makedirs(CKPT_DIR, exist_ok=True)
    print(f"\nParametricPINN (bounded) width {args.width} depth {args.depth}: {n_par:,} parameters | "
          f"{args.steps} steps | time-axis eval {len(tr_eval)} samples / "
          f"{len(np.unique(d.material_ids[tr_eval]))} materials | material-axis eval {len(nm)} / "
          f"{len(np.unique(d.material_ids[nm]))}")

    if args.stage == "sweep":
        for axis in args.axes:
            lo, hi = (0.0, args.t_cut) if axis == "time" else (0.0, 1.0)
            for arm in args.arms:
                for seed in args.seeds:
                    if get_path(res, "sweep", axis, arm, str(seed)) is not None:
                        continue
                    t1 = time.time()
                    model, hist, final, failed = train(arm, d, tr, args, seed, lo, hi)
                    model.eval()
                    rec = {"failed": failed, "history": hist, "final_weights": final}
                    if failed is None:
                        rec.update(score(model, d, axis, tr_eval, nm, args.t_cut))
                        torch.save(model.state_dict(), ckpt_path(axis, arm, seed))
                    set_path(res, rec, "sweep", axis, arm, str(seed))
                    write_atomic(res, args.out)
                    if failed:
                        print(f"  [{axis:<8}] {arm:<18} seed {seed}: FAILED — {failed}  [{time.time()-t1:.0f}s]", flush=True)
                    else:
                        print(f"  [{axis:<8}] {arm:<18} seed {seed}: seen={rec['seen']:.4f} held={rec['held']:.4f} "
                              f"w_pde={final['w_pde']:.2e}  [{time.time()-t1:.0f}s]", flush=True)
                    del model; gc.collect()

    else:   # polish
        for axis in args.axes:
            lo, hi = (0.0, args.t_cut) if axis == "time" else (0.0, 1.0)
            sw = res.get("sweep", {}).get(axis, {})
            best_pi = best_physics_arm(sw, args.seeds)
            if "data_only" not in sw or len(sw["data_only"]) < len(args.seeds) or not best_pi:
                print(f"  [{axis}] sweep incomplete; polish skipped")
                continue
            print(f"  [{axis}] polishing data_only and best physics arm {best_pi}")
            for arm in ("data_only", best_pi):
                for seed in args.seeds:
                    if get_path(res, "polish", axis, arm, str(seed)) is not None:
                        continue
                    t1 = time.time()
                    model = ParametricPINN(n_params_in=d.params.shape[1], width=args.width,
                                           depth=args.depth, bounded=True).to(DEVICE)
                    model.load_state_dict(torch.load(ckpt_path(axis, arm, seed), map_location=DEVICE))
                    fw = sw[arm][str(seed)]["final_weights"]
                    n_it, last = polish(model, d, tr, args, seed, lo, hi, fw["w_pde"], fw["w_bc"],
                                        arm != "data_only")
                    model.eval()
                    rec = {"iters": n_it, "final_loss": last, "weights_used": fw,
                           **score(model, d, axis, tr_eval, nm, args.t_cut)}
                    torch.save(model.state_dict(), ckpt_path(axis, arm, seed, "_lbfgs"))
                    set_path(res, rec, "polish", axis, arm, str(seed))
                    set_path(res, best_pi, "polish", axis, "best_pi")
                    write_atomic(res, args.out)
                    print(f"  [{axis:<8}] {arm:<18} seed {seed} +L-BFGS({n_it} it): seen={rec['seen']:.4f} "
                          f"held={rec['held']:.4f}  [{time.time()-t1:.0f}s]", flush=True)
                    del model; gc.collect()

    print(f"\nwrote {args.out}  [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
