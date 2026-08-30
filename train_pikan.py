"""Train a PIKAN / PINN surrogate on 1D adsorption dynamics.

Written so that every component the ladder needs to ablate is a flag, and so that
the loss-weighting scheme is a named, citable choice rather than a hand-tuned
constant. See `03_LADDER_PROTOCOL.md` for the protocol these runs must satisfy.

Loss weighting
--------------
The residuals from `pde_adsorption` are already normalised per equation, so what
remains is the genuinely adaptive part:

  causal   Wang, Sankaran & Perdikaris (CMAME 2024). Residuals are binned in time
           and weighted w_i = exp(-eps * sum_{k<i} L_r(t_k)), so the network is
           not rewarded for satisfying the PDE at late times before the early-time
           solution is correct. For a propagating front this matters more than any
           other single choice: full-domain collocation on a moving MTZ otherwise
           converges to a smeared, causally inconsistent solution.

  rba      Residual-based attention (Anagnostopoulos et al. 2024). Pointwise
           multipliers as an EMA of the normalised residual, which concentrates
           capacity on the front automatically. Cheap; best effort-to-payoff here.

  ntk      Wang, Yu & Perdikaris (JCP 2022). lambda_i = Tr(K)/Tr(K_i) with
           Tr(K_i) = sum_j ||grad_theta r_i(x_j)||^2, recomputed every
           `--ntk-every` steps. The principled version of hand-tuning.

  none     Equal weights. The L4 control arm.

Usage
-----
    python train_pikan.py --smoke                     # 60s sanity run
    python train_pikan.py --arm pikan --seed 42       # full run
    python train_pikan.py --arm data-only             # no physics loss (L4 control)
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
import torch

from kan_model import PIKAN_Adsorption
from pde_adsorption import (
    NondimConfig,
    boundary_residuals,
    compute_adsorption_pde_residuals,
    term_coefficients,
)
from solver_fd import AdsorptionPhysicsConfig

DATASETS = {
    "default": ("data/synthetic_breakthrough.npz", lambda: AdsorptionPhysicsConfig()),
    "mof303": ("data/mof303_breakthrough.npz", None),  # resolved lazily
}


def load_case(case):
    path, factory = DATASETS[case]
    if factory is None:
        from fetch_real_mof_data import get_mof303_physics

        factory = get_mof303_physics
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} missing — run regen_datasets.py first")
    d = np.load(path)
    physics = factory()
    c_in = float(d["c_in"])
    nondim = NondimConfig(physics, t_final=float(d["t"][-1]), c_in=c_in)
    return d, physics, nondim


def anchors(d, nondim, frac, seed, device):
    """Sparse supervised anchors, sampled uniformly over the full (z,t) field.

    NOTE: this is a full-field sample. Any temporal-extrapolation claim requires a
    time-restricted split applied to EVERY arm — see protocol section 5. Reporting
    extrapolation while the physics arm has seen the test window is the single
    error most likely to invalidate the study.
    """
    z, t, y = d["z"], d["t"], d["y"]
    nz, nt = len(z), len(t)
    Z, T = np.meshgrid(z, t, indexing="ij")
    C, Q, Tm = y[:nz], y[nz : 2 * nz], y[2 * nz :]

    rng = np.random.default_rng(seed)
    n = int(frac * Z.size)
    idx = rng.choice(Z.size, n, replace=False)

    def col(a, scale):
        return torch.tensor(a.ravel()[idx] / scale, dtype=torch.float32, device=device).unsqueeze(1)

    return (
        col(Z, nondim.L_ref), col(T, nondim.t_final),
        col(C, nondim.c_ref), col(Q, nondim.q_ref), col(Tm, nondim.T_ref),
    )


def causal_weights(res_sq, t_col, n_bins, w_floor):
    """Causal weights w_i = exp(-eps * cumulative upstream residual), per time bin.

    `eps` is SOLVED FOR rather than fixed, so that min(w) == w_floor exactly.

    A fixed eps is unusable here. The residual magnitude changes by orders of
    magnitude during training, so any constant eps is either inert (early, when
    residuals are small) or saturating (late, or at initialisation, when the
    cumulative sum reaches several hundred and exp(-eps*cum) underflows to
    exactly 0). The latter is what happened with eps = 1.0: every time bin past
    the first was assigned weight 0, so the network was trained on the first
    1/32 of the time domain and nothing else, silently.

    Solving eps = -ln(w_floor)/max(cum) keeps the weighting profile scale-free
    and self-annealing: as the early-time solution improves, cum shrinks, eps
    grows, and the causal front advances. It also cannot silently zero anything.
    """
    edges = torch.linspace(0.0, 1.0, n_bins + 1, device=t_col.device)
    bin_id = torch.clamp(torch.bucketize(t_col.squeeze(1), edges) - 1, 0, n_bins - 1)

    flat = res_sq.detach().squeeze(1)
    per_bin = torch.zeros(n_bins, device=t_col.device).index_add_(0, bin_id, flat)
    counts = torch.zeros(n_bins, device=t_col.device).index_add_(0, bin_id, torch.ones_like(flat))
    per_bin = per_bin / counts.clamp(min=1.0)

    cum = torch.cat([torch.zeros(1, device=t_col.device), torch.cumsum(per_bin, 0)[:-1]])
    cmax = float(cum.max())
    eps = (-np.log(w_floor) / cmax) if cmax > 0 else 0.0
    w = torch.exp(-eps * cum)
    return w[bin_id].unsqueeze(1), float(w.min()), eps


def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    d, physics, nondim = load_case(args.case)
    print(f"case={args.case} arm={args.arm} seed={args.seed} device={device}")
    print("  groups: " + "  ".join(f"{k}={v:.3e}" for k, v in nondim.groups(physics).items()))
    if args.verbose:
        for eq, terms in term_coefficients(nondim, physics).items():
            print(f"    {eq:>9}: " + "  ".join(f"{k}={v:.2e}" for k, v in terms.items()))

    model = PIKAN_Adsorption(
        width=args.width, depth=args.depth, num_grids=args.grids
    ).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  parameters: {n_params:,}")

    z_a, t_a, c_a, q_a, T_a = anchors(d, nondim, args.anchor_frac, args.seed, device)
    print(f"  anchors: {len(z_a):,}  collocation: {args.n_colloc:,}")

    use_physics = args.arm != "data-only"
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.steps, eta_min=args.lr * 1e-2)

    rba = None
    history, t0 = [], time.time()

    for step in range(args.steps):
        opt.zero_grad(set_to_none=True)

        out = model(z_a, t_a)
        loss_data = (
            (out[:, 0:1] - c_a).pow(2).mean()
            + (out[:, 1:2] - q_a).pow(2).mean()
            + (out[:, 2:3] - T_a).pow(2).mean()
        )

        loss = args.w_data * loss_data
        parts = {"data": float(loss_data.detach())}

        if use_physics:
            z_c = torch.rand(args.n_colloc, 1, device=device)
            t_c = torch.rand(args.n_colloc, 1, device=device)
            r_g, r_k, r_e = compute_adsorption_pde_residuals(model, z_c, t_c, nondim, physics)
            res_sq = r_g.pow(2) + r_k.pow(2) + r_e.pow(2)

            w = torch.ones_like(res_sq)
            if args.weighting in ("causal", "causal+rba"):
                w_causal, w_min, eps_eff = causal_weights(
                    res_sq, t_c, args.causal_bins, args.causal_w_floor
                )
                w = w * w_causal
                parts["causal_w_min"] = w_min
                parts["causal_eps"] = eps_eff
            if args.weighting in ("rba", "causal+rba"):
                r_norm = (res_sq.detach().sqrt() / res_sq.detach().sqrt().max().clamp(min=1e-30))
                rba = r_norm if rba is None or rba.shape != r_norm.shape else args.rba_gamma * rba + args.rba_eta * r_norm
                w = w * (1.0 + rba)

            loss_pde = (w * res_sq).mean()
            loss = loss + args.w_pde * loss_pde
            parts["pde"] = float(loss_pde.detach())

            t_b = torch.rand(args.n_bc, 1, device=device)
            b_in_c, b_in_T, b_out_c, b_out_T = boundary_residuals(model, t_b, nondim, physics)
            loss_bc = sum(x.pow(2).mean() for x in (b_in_c, b_in_T, b_out_c, b_out_T))
            loss = loss + args.w_bc * loss_bc
            parts["bc"] = float(loss_bc.detach())

        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss at step {step}: {parts}")

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), args.clip)
        opt.step()
        sched.step()

        if step % max(1, args.steps // 20) == 0 or step == args.steps - 1:
            msg = f"  {step:6d}  total={float(loss.detach()):.4e}  " + "  ".join(
                f"{k}={v:.3e}" for k, v in parts.items()
            )
            print(msg, flush=True)
            history.append({"step": step, "total": float(loss.detach()), **parts})

    elapsed = time.time() - t0
    bad = sum(int((~torch.isfinite(p)).sum()) for p in model.parameters())
    if bad:
        raise RuntimeError(f"{bad} non-finite parameters at end of training — refusing to save")

    os.makedirs("data", exist_ok=True)
    # The tag MUST encode the architecture. Without it, a width-24 smoke run and
    # a width-64 production run of the same (case, arm, weighting, seed) write to
    # the same path and silently overwrite each other -- and a ladder whose whole
    # validity rests on matched-parameter comparisons cannot afford to load the
    # wrong weights. `smoke_` also makes a sanity run impossible to mistake for
    # a reported one.
    arch = f"w{args.width}d{args.depth}g{args.grids}"
    prefix = "smoke_" if args.smoke else ""
    tag = f"{prefix}{args.case}_{args.arm}_{args.weighting}_{arch}_s{args.seed}"
    torch.save(model.state_dict(), f"data/pikan_{tag}.pth")
    with open(f"data/pikan_{tag}_history.json", "w") as f:
        json.dump(
            {"args": vars(args), "n_params": n_params, "elapsed_s": elapsed, "history": history},
            f, indent=2,
        )
    print(f"  done in {elapsed:.1f}s -> data/pikan_{tag}.pth")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--case", default="default", choices=list(DATASETS))
    p.add_argument("--arm", default="pikan", choices=["pikan", "data-only"])
    p.add_argument("--weighting", default="causal+rba", choices=["none", "causal", "rba", "causal+rba"])
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--width", type=int, default=64)
    p.add_argument("--depth", type=int, default=3)
    p.add_argument("--grids", type=int, default=20)
    p.add_argument("--steps", type=int, default=20000)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--clip", type=float, default=1.0)
    p.add_argument("--n-colloc", type=int, default=8000)
    p.add_argument("--n-bc", type=int, default=1000)
    p.add_argument("--anchor-frac", type=float, default=0.02)
    p.add_argument("--w-data", type=float, default=1.0)
    p.add_argument("--w-pde", type=float, default=1.0)
    p.add_argument("--w-bc", type=float, default=1.0)
    p.add_argument("--causal-bins", type=int, default=32)
    p.add_argument("--causal-w-floor", type=float, default=1e-2,
                   help="target minimum causal weight; eps is solved to hit it")
    p.add_argument("--rba-gamma", type=float, default=0.999)
    p.add_argument("--rba-eta", type=float, default=0.01)
    p.add_argument("--smoke", action="store_true", help="60s sanity run")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    if args.smoke:
        # A smoke test must finish in under a minute on CPU. The RBF-KAN edge is
        # ~in*out*grids MACs per sample per layer, and the PDE residual needs a
        # double backward for d2/dz2, so the full config costs ~2 s/step on CPU.
        args.steps, args.n_colloc, args.n_bc = 30, 400, 200
        args.anchor_frac, args.width, args.depth, args.grids = 0.002, 24, 2, 8
        args.verbose = True
    train(args)


if __name__ == "__main__":
    main()
