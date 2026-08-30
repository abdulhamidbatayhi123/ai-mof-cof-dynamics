"""L4 — the physics-as-a-loss rung.

Hypothesis under test: *"add the PDE residual and it will generalise."*

This is the rung the whole project rests on. L1-L3 eliminated representation,
capacity and architecture; if physics-informing does not close the ~33x gap to
held-out materials either, then "physics as a soft penalty" is not the answer and
the thesis has to be structural (L6).

Formulation
-----------
Unlike L1-L3, this rung cannot use the POD-coefficient regression: a PDE residual
needs the actual field and its derivatives. The model here is a parametric PINN,

    (material+operating params [11], z*, t*)  ->  (c*, q*, T*)

so the comparison in this rung is INTERNAL: physics-informed against a
data-only twin with identical architecture, parameter count, optimiser,
schedule, step count, seeds and supervised sample budget. The only difference is
whether the PDE residual term is present.

Cross-rung comparison of absolute numbers against L1-L3 is NOT valid (different
function class, different supervision), and is not made.

Arms
    data_only : supervised loss on sampled field points
    pi        : supervised loss + PDE residual + Danckwerts boundary residual
    pi_causal : as `pi`, with causal time weighting (Wang et al. CMAME 2024)

Every arm sees the same supervised points, so any difference is attributable to
the physics term rather than to data.
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
from isotherm import q_star_torch
from ladder_data import PARAM_KEYS
from solver_fd import AdsorptionPhysicsConfig

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
R_GAS = 8.314


def physics_from_params(vec, keys=PARAM_KEYS):
    """Rebuild an AdsorptionPhysicsConfig from an 11-vector (raw, not standardised).

    `keys` names the vector's columns and MUST come from the dataset that produced
    it — pass `d.param_keys`. The legacy and v2 designs use different vectors of
    the same length (position 5 is `k_LDF` under legacy, `d_p` under v2), so a
    default is a footgun; it is retained only so legacy callers keep working, and
    the reconstruction below is asserted rather than assumed.
    """
    p = AdsorptionPhysicsConfig()
    d = dict(zip(keys, vec))
    p.q_max = d["q_max"]
    p.delta_H = d["delta_H"]
    p.isotherm_n = d["isotherm_n"]
    p.henry_fraction = d["henry_fraction"]
    p.rho_p = d["rho_p"]
    p.eps_t = d["eps_t"]
    p.T_in = d["T_in"]
    p.T_w = d["T_in"]
    p.v = d["v"]
    p.L = 0.10
    # d_p is a sampled material property under design v2 and fixed at 2 mm under
    # legacy. It enters BOTH the axial dispersion correlation and (under v2) the
    # mass-transfer coefficient, so getting it from the wrong place changes the
    # PDE the residual is computed against.
    p.d_p = float(d.get("d_p", 0.002))
    p.D_L = 0.7 * 2.5e-5 + 0.5 * p.d_p * (p.v / p.eps_t)

    from gen_parametric_dataset import B_H_RATIO, k_ldf_glueckauf, rh_to_conc
    from isotherm import calibrate_step
    c_step = rh_to_conc(d["step_rh"], d["T_in"])
    p.b0 = calibrate_step(p, c_step, d["T_in"])
    p.b_H0 = p.b0 / B_H_RATIO
    p.c_in = rh_to_conc(d["rh_feed"], d["T_in"])

    # KINETICS. Under legacy, k_LDF is in the vector. Under v2 it is derived from
    # the particle exactly as the generator derived it — reconstructing it any
    # other way would compute the residual against a different PDE than the one
    # that produced the data, which is the single worst thing this function can do.
    if "k_LDF" in d:
        p.k_LDF = d["k_LDF"]
    else:
        p.k_LDF = k_ldf_glueckauf(p, p.c_in, d["T_in"], p.d_p)
    return p


class ParametricPINN(nn.Module):
    """(params, z*, t*) -> (c*, q*, T*), with the shared bounded output head."""

    def __init__(self, n_params_in=11, width=192, depth=4, dT_max=0.5, bounded=False):
        super().__init__()
        layers, d = [], n_params_in + 2
        for _ in range(depth):
            layers += [nn.Linear(d, width), nn.GELU()]
            d = width
        layers.append(nn.Linear(d, 3))
        self.net = nn.Sequential(*layers)
        self.dT_max = dT_max
        self.bounded = bounded

    def forward(self, params, z, t):
        h = self.net(torch.cat([params, z, t], dim=1))
        from output_head import apply_bounded_head, apply_output_head
        if self.bounded:
            c, q, T = apply_bounded_head(h[:, 0:1], h[:, 1:2], h[:, 2:3], self.dT_max)
        else:
            c, q, T = apply_output_head(h[:, 0:1], h[:, 1:2], h[:, 2:3], t, self.dT_max)
        return torch.cat([c, q, T], dim=1)


def pde_residual(model, params_z, phys_batch, z, t, tau_batch):
    """Normalised residuals for a batch whose rows may have DIFFERENT physics.

    Every group is precomputed per row as a tensor, so one autograd pass covers
    the whole batch even though each sample has its own material.
    """
    z = z.requires_grad_(True)
    t = t.requires_grad_(True)
    out = model(params_z, z, t)
    c, q, T = out[:, 0:1], out[:, 1:2], out[:, 2:3]
    ones = torch.ones_like(z)

    def d(y, x):
        return torch.autograd.grad(y, x, ones, create_graph=True)[0]

    dc_dz, dc_dt = d(c, z), d(c, t)
    dq_dt = d(q, t)
    dT_dz, dT_dt = d(T, z), d(T, t)
    d2c = d(dc_dz, z)
    d2T = d(dT_dz, z)

    P = phys_batch                    # dict of (N,1) tensors
    tau = tau_batch
    c_dim = P["c_in"] * c
    T_dim = P["T_in"] * T

    # Per-ROW isotherm parameters. Using a batch mean here would apply one
    # averaged isotherm to every material in the batch, which is exactly the
    # physics the rung is supposed to be testing. isotherm.py is batch-aware.
    class _Row:                        # duck-type for q_star_torch
        pass
    row = _Row()
    row.q_max, row.delta_H = P["q_max"], P["delta_H"]
    row.isotherm_n = P["isotherm_n"]
    row.henry_fraction = P["henry_fraction"]
    row.b0, row.b_H0 = P["b0"], P["b_H0"]
    q_star = q_star_torch(c_dim, T_dim, row) / P["q_max"]

    Lam, Pe, Da = P["Lambda"], P["Pe"], P["Da"]
    beta, St, Pe_T, vT = P["beta"], P["St"], P["Pe_T"], P["v_T"]

    res_mass = (dc_dt / Lam) + (tau / Lam) * dc_dz - (tau / (Pe * Lam)) * d2c + dq_dt
    res_kin = dq_dt / (tau * Da) - (q_star - q)
    res_en = dT_dt + tau * vT * dT_dz - (tau / Pe_T) * d2T - beta * dq_dt + tau * St * (T - 1.0)
    return res_mass, res_kin, res_en


def boundary_residual(model, params_z, phys_batch, t, tau_batch):
    """Danckwerts boundary residuals, per row.

    A PDE residual ALONE does not determine a solution. The same equation admits
    different solutions under different boundary conditions, so enforcing only
    the interior residual leaves the model free to satisfy the physics with the
    wrong inflow — and it did: without these terms the physics arm still diverged
    by a factor of 5,480 outside the training time window (defect B20).

      inlet  z=0 :  c* - (1/Pe) dc*/dz* = 1        flux matching (c scaled by c_in)
                    T* = T_in / T_ref = 1
      outlet z=1 :  dc*/dz* = 0,  dT*/dz* = 0      convective outflow
    """
    z0 = torch.zeros_like(t, requires_grad=True)
    z1 = torch.ones_like(t, requires_grad=True)
    ones = torch.ones_like(t)
    Pe = phys_batch["Pe"]

    o0 = model(params_z, z0, t)
    c0, T0 = o0[:, 0:1], o0[:, 2:3]
    dc0 = torch.autograd.grad(c0, z0, ones, create_graph=True)[0]

    o1 = model(params_z, z1, t)
    c1, T1 = o1[:, 0:1], o1[:, 2:3]
    dc1 = torch.autograd.grad(c1, z1, ones, create_graph=True)[0]
    dT1 = torch.autograd.grad(T1, z1, ones, create_graph=True)[0]

    return (c0 - (1.0 / Pe) * dc0 - 1.0), (T0 - 1.0), dc1, dT1


def build_phys_table(raw_params, device):
    """Per-row dimensionless groups for EVERY sample, computed ONCE.

    The first version rebuilt an AdsorptionPhysicsConfig for all 1024 collocation
    rows on every optimiser step -- a Python loop with an exponential and a step
    calibration per row, which dominated the step time. Building the table once
    and indexing into it makes the physics term nearly free.
    """
    return build_phys_batch(raw_params, np.arange(len(raw_params)), device)


def index_phys(table, idx):
    """Gather the per-row groups for a batch of sample indices."""
    return {k: v[idx] for k, v in table.items()}


def build_phys_batch(raw_params, idx, device):
    """Precompute per-row dimensionless groups for the rows in `idx`."""
    keys = ("q_max", "delta_H", "b0", "b_H0", "c_in", "T_in", "isotherm_n",
            "henry_fraction", "Lambda", "Pe", "Da", "beta", "St", "Pe_T", "v_T", "t_ref")
    cols = {k: [] for k in keys}
    for i in idx:
        p = physics_from_params(raw_params[i])
        eps, Ct = p.eps_t, p.C_term
        t_ref = p.L / p.v
        cols["q_max"].append(p.q_max); cols["delta_H"].append(p.delta_H)
        cols["b0"].append(p.b0); cols["b_H0"].append(p.b_H0)
        cols["c_in"].append(p.c_in); cols["T_in"].append(p.T_in)
        cols["isotherm_n"].append(p.isotherm_n); cols["henry_fraction"].append(p.henry_fraction)
        cols["Lambda"].append((1 - eps) * p.rho_p * p.q_max / (eps * p.c_in))
        cols["Pe"].append(p.v * p.L / p.D_L)
        cols["Da"].append(p.k_LDF * t_ref)
        cols["beta"].append((1 - eps) * p.rho_p * (-p.delta_H) * p.q_max / (Ct * p.T_in))
        cols["St"].append(4 * p.h_w * p.L / (p.D_in * Ct * p.v))
        cols["Pe_T"].append(Ct * p.v * p.L / p.k_z)
        cols["v_T"].append(p.rho_g * p.C_pg / Ct)
        cols["t_ref"].append(t_ref)
    return {k: torch.tensor(v, dtype=torch.float32, device=device).unsqueeze(1)
            for k, v in cols.items()}


def causal_weights(res_sq, t_col, n_bins=24, w_floor=1e-2):
    edges = torch.linspace(0.0, 1.0, n_bins + 1, device=t_col.device)
    b = torch.clamp(torch.bucketize(t_col.squeeze(1), edges) - 1, 0, n_bins - 1)
    flat = res_sq.detach().squeeze(1)
    per = torch.zeros(n_bins, device=t_col.device).index_add_(0, b, flat)
    cnt = torch.zeros(n_bins, device=t_col.device).index_add_(0, b, torch.ones_like(flat))
    per = per / cnt.clamp(min=1.0)
    cum = torch.cat([torch.zeros(1, device=t_col.device), torch.cumsum(per, 0)[:-1]])
    cmax = float(cum.max())
    eps = (-np.log(w_floor) / cmax) if cmax > 0 else 0.0
    return torch.exp(-eps * cum)[b].unsqueeze(1)


# ─────────────────────────────────────────────────────────────────────────────

def sample_supervised(d, idx, n_per_sample, rng):
    """Sample supervised (row, z, t) points from the stored fields."""
    nz, nt = d.fields.shape[2:]
    rows = rng.integers(0, len(idx), n_per_sample)
    zi = rng.integers(0, nz, n_per_sample)
    ti = rng.integers(0, nt, n_per_sample)
    g = idx[rows]
    z = (zi / (nz - 1)).astype(np.float32)
    t = (ti / (nt - 1)).astype(np.float32)
    y = d.fields[g, :, zi, ti].astype(np.float32)
    return g, z, t, y


@torch.no_grad()
def eval_fields(model, d, idx, params_z, batch_rows=4):
    """Reconstruct each sample's full (3, nz, nt) field and score it."""
    from run_l1 import CHANNELS  # noqa: F401  (kept for symmetry)
    from metrics import breakthrough_times, per_variable_nrmse
    nz, nt = d.fields.shape[2:]
    zg, tg = np.meshgrid(np.linspace(0, 1, nz, dtype=np.float32),
                         np.linspace(0, 1, nt, dtype=np.float32), indexing="ij")
    zf = torch.tensor(zg.ravel(), device=DEVICE).unsqueeze(1)
    tf = torch.tensor(tg.ravel(), device=DEVICE).unsqueeze(1)
    t_norm = np.linspace(0.0, 1.0, nt)
    rows = []
    CH = 65536          # query points per forward pass; keeps peak memory bounded
    for k, gi in enumerate(idx):
        pv = torch.tensor(params_z[gi], dtype=torch.float32, device=DEVICE)
        chunks = []
        for s0 in range(0, zf.shape[0], CH):
            e = min(s0 + CH, zf.shape[0])
            pr = pv.unsqueeze(0).expand(e - s0, -1)
            chunks.append(model(pr, zf[s0:e], tf[s0:e]).cpu().numpy())
        out = np.concatenate(chunks, 0).T.reshape(3, nz, nt)
        true = d.fields[gi]
        m = per_variable_nrmse(out, true)
        bp = breakthrough_times(out[0, -1, :], t_norm)
        bt = breakthrough_times(true[0, -1, :], t_norm)
        for lev in (0.05, 0.50, 0.95):
            a, b = bp[lev], bt[lev]
            m[f"dt_bt{int(lev*100):02d}"] = (abs(a - b) * d.t_final[gi]
                                             if np.isfinite(a) and np.isfinite(b) else np.nan)
        rows.append(m)
    return rows


def train_arm(arm, d, tr_idx, args, seed):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = ParametricPINN(width=args.width, depth=args.depth).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.steps, eta_min=args.lr * 1e-2)

    Pz = torch.tensor(d.params_z, dtype=torch.float32, device=DEVICE)
    phys_table = build_phys_table(d.params, DEVICE)   # once, not per step
    tau_all = torch.tensor(
        [d.t_final[i] / (0.10 / d.params[i][d.pidx("v")]) for i in range(len(d.params))],
        dtype=torch.float32, device=DEVICE).unsqueeze(1)

    use_phys = arm != "data_only"
    use_causal = "causal" in arm
    adaptive = "gradnorm" in arm
    # Gradient-norm balancing (Wang, Teng & Perdikaris, SISC 2021).
    #
    # A FIXED weight is not a fair test of physics-informing. Measured at
    # w_pde = 1.0 the PDE term starts at 9.87 against a data loss of 0.130 -- 76x
    # -- and the optimiser abandons the data fit entirely: the data loss RISES
    # 0.130 -> 0.214 while the residual falls. That would have been reported as
    # "physics does not help" when it is really "this weight does not work".
    #
    # w_pde is instead set so the two terms contribute comparable gradient norms,
    # re-estimated every `balance_every` steps and smoothed by an EMA.
    w_pde = args.w_pde
    hist = []
    for step in range(args.steps):
        opt.zero_grad(set_to_none=True)
        g, z, t, y = sample_supervised(d, tr_idx, args.n_sup, rng)
        gt = torch.tensor(g, device=DEVICE)
        pred = model(Pz[gt], torch.tensor(z, device=DEVICE).unsqueeze(1),
                     torch.tensor(t, device=DEVICE).unsqueeze(1))
        loss = nn.functional.mse_loss(pred, torch.tensor(y, device=DEVICE))
        parts = {"data": float(loss.detach())}

        if use_phys:
            cg = tr_idx[rng.integers(0, len(tr_idx), args.n_colloc)]
            zc = torch.rand(args.n_colloc, 1, device=DEVICE)
            tc = torch.rand(args.n_colloc, 1, device=DEVICE)
            cgt = torch.tensor(cg, device=DEVICE)
            pb = index_phys(phys_table, cgt)
            rm, rk, re = pde_residual(model, Pz[cgt], pb, zc, tc, tau_all[cgt])
            res_sq = rm.pow(2) + rk.pow(2) + re.pow(2)
            # Boundary conditions are part of the physics, not an extra. Without
            # them the residual does not determine a solution (defect B20).
            tb = torch.rand(min(args.n_bc, len(cgt)), 1, device=DEVICE)
            bgt = cgt[:tb.shape[0]]
            b_res = boundary_residual(model, Pz[bgt], index_phys(phys_table, bgt), tb, tau_all[bgt])
            bc_sq = sum(x.pow(2).mean() for x in b_res)
            w = causal_weights(res_sq, tc) if use_causal else torch.ones_like(res_sq)
            lp = (w * res_sq).mean() + bc_sq

            if adaptive and (step % args.balance_every == 0):
                gd = torch.autograd.grad(loss, list(model.parameters()),
                                         retain_graph=True, allow_unused=True)
                gp = torch.autograd.grad(lp, list(model.parameters()),
                                         retain_graph=True, allow_unused=True)
                nd = torch.sqrt(sum((g.pow(2).sum() for g in gd if g is not None)))
                npd = torch.sqrt(sum((g.pow(2).sum() for g in gp if g is not None)))
                if float(npd) > 0:
                    target = float(nd / npd)
                    w_pde = (1 - args.balance_alpha) * w_pde + args.balance_alpha * target
                    w_pde = float(np.clip(w_pde, 1e-6, 1e3))

            loss = loss + w_pde * lp
            parts["pde"] = float(lp.detach())
            parts["w_pde"] = float(w_pde)

        if not torch.isfinite(loss):
            raise RuntimeError(f"{arm} non-finite loss at step {step}: {parts}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sch.step()
        if step % max(1, args.steps // 8) == 0:
            hist.append({"step": step, **parts})
    return model, hist


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms", nargs="+",
                    default=["data_only", "pi", "pi_gradnorm", "pi_gradnorm_causal"])
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--width", type=int, default=192)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--n-sup", type=int, default=4096)
    ap.add_argument("--n-colloc", type=int, default=1024)
    ap.add_argument("--n-bc", type=int, default=384)
    ap.add_argument("--w-pde", type=float, default=1.0,
                    help="fixed weight, or the INITIAL weight for gradnorm arms")
    ap.add_argument("--balance-every", type=int, default=50)
    ap.add_argument("--balance-alpha", type=float, default=0.1)
    ap.add_argument("--out", default="results/l4_results.json")
    args = ap.parse_args()

    t0 = time.time()
    d = ladder_data.load()
    tr = d.idx("train")
    n_par = sum(p.numel() for p in ParametricPINN(width=args.width, depth=args.depth).parameters())
    print(f"\nParametricPINN width {args.width} depth {args.depth}: {n_par:,} parameters")
    print(f"arms {args.arms} | {args.steps} steps | {args.n_sup} supervised pts/step "
          f"| {args.n_colloc} collocation pts/step\n")

    res = {"width": args.width, "depth": args.depth, "steps": args.steps,
           "n_params": n_par, "n_sup": args.n_sup, "n_colloc": args.n_colloc,
           "seeds": args.seeds, "splits": d.summary(), "arms": {}}

    for arm in args.arms:
        res["arms"][arm] = {}
        for seed in args.seeds:
            t1 = time.time()
            model, hist = train_arm(arm, d, tr, args, seed)
            model.eval()
            per = {}
            for split in ("train", "novel_material"):
                idx = d.idx(split)
                sub = idx if split != "train" else idx[:200]   # train scored on a subset
                rows = eval_fields(model, d, sub, d.params_z)
                per[split] = {
                    "c": float(np.nanmean([r["c"] for r in rows])),
                    "q": float(np.nanmean([r["q"] for r in rows])),
                    "T": float(np.nanmean([r["T"] for r in rows])),
                    "dt_bt50": float(np.nanmean([r["dt_bt50"] for r in rows])),
                    "per_sample_nrmse_c": [float(r["c"]) for r in rows],
                    "material_ids": d.material_ids[sub].tolist(),
                }
            res["arms"][arm][str(seed)] = {**per, "history": hist}
            nm = per["novel_material"]
            print(f"  {arm:<10} seed {seed}: train={per['train']['c']:.4f}  "
                  f"novel={nm['c']:.4f}  q={nm['q']:.4f}  T={nm['T']:.4f}  "
                  f"dt50={nm['dt_bt50']/3600:.2f}h  [{time.time()-t1:.0f}s]", flush=True)
            del model; gc.collect()
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        json.dump(res, open(args.out, "w"), indent=2)
    print(f"\nwrote {args.out}  [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
