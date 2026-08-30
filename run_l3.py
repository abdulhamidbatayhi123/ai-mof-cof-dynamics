"""L3 — the architecture-family rung.

Hypothesis under test: *"you need a better basis."*

This is the direct test of H2, and of the premise behind PIKAN/DeepOKAN: that
replacing an MLP's fixed activations with learnable univariate edge functions
(Gaussian RBF, or Chebyshev polynomials) makes a material difference.

Two independent prior measurements say it does not:

  * Shukla, Toscano, Wang, Zou & Karniadakis (CMAME 2024): KAN variants are at
    best comparable to MLPs for PDE and operator learning, and less robust
    across seeds.
  * Our own prior project on transient conduction: retraction A3 withdrew "the
    KAN flip" — gaps of 0.17-0.33 against a ~0.3 noise floor, i.e. within noise
    at parity.

So the expected result is a null. The point of running it is that a null at
matched parameters is a *result* — it says the basis is not where the problem
is — and neither prior measurement was made on adsorption.

MATCHED PARAMETER COUNT IS THE WHOLE EXPERIMENT
-----------------------------------------------
A KAN edge carries `num_grids` coefficients where an MLP edge carries one, so a
KAN at equal WIDTH has roughly `num_grids` times the parameters. Comparing at
equal width and declaring the KAN better is the single most common error in this
literature. Widths here are solved per family to hit a common parameter budget
within +-10 %, and the achieved counts are reported in every table.

Everything else is held fixed: POD basis, splits, inputs, target standardisation,
optimiser, schedule, training steps, seeds.
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
from run_l1 import CHANNELS, evaluate, fit_pod, project

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ─────────────────────────────────────────────────────────────────────────────
# edge families
# ─────────────────────────────────────────────────────────────────────────────

class MLPBlock(nn.Module):
    """Standard affine + fixed nonlinearity. One parameter per edge."""

    def __init__(self, i, o):
        super().__init__()
        self.lin = nn.Linear(i, o)
        self.act = nn.GELU()

    def forward(self, x):
        return self.act(self.lin(x))


class RBFKANBlock(nn.Module):
    """Gaussian-RBF edges + SiLU base path. `grids` parameters per edge."""

    def __init__(self, i, o, grids=8):
        super().__init__()
        self.base = nn.Linear(i, o, bias=False)
        self.act = nn.SiLU()
        self.register_buffer("centers", torch.linspace(-2.0, 2.0, grids))
        self.h = 4.0 / max(grids - 1, 1)
        self.coeffs = nn.Parameter(torch.randn(i, o, grids) / np.sqrt(i * grids))

    def forward(self, x):
        base = self.base(self.act(x))
        z = (x.unsqueeze(-1) - self.centers) / self.h
        phi = torch.exp(-z * z)
        return base + torch.einsum("nig,iog->no", phi, self.coeffs)


class ChebyKANBlock(nn.Module):
    """Chebyshev-polynomial edges. `degree+1` parameters per edge.

    Inputs are squashed by tanh so the Chebyshev recursion stays inside [-1, 1],
    where the polynomials are bounded. Without that the T_k blow up like x^k and
    training diverges for k >= 4 — the instability Shukla et al. report for
    higher-order orthogonal-polynomial KANs.
    """

    def __init__(self, i, o, degree=7):
        super().__init__()
        self.degree = degree
        self.coeffs = nn.Parameter(torch.randn(i, o, degree + 1) / np.sqrt(i * (degree + 1)))

    def forward(self, x):
        x = torch.tanh(x)
        T = [torch.ones_like(x), x]
        for _ in range(2, self.degree + 1):
            T.append(2.0 * x * T[-1] - T[-2])
        Ts = torch.stack(T, dim=-1)                     # (N, i, degree+1)
        return torch.einsum("nik,iok->no", Ts, self.coeffs)


def build(family, width, depth, n_in, n_out, grids=8, degree=7):
    blocks, d = [], n_in
    for _ in range(depth):
        if family == "mlp":
            blocks.append(MLPBlock(d, width))
        elif family == "rbf_kan":
            blocks.append(RBFKANBlock(d, width, grids))
        elif family == "cheby_kan":
            blocks.append(ChebyKANBlock(d, width, degree))
        else:
            raise ValueError(family)
        d = width
    blocks.append(nn.Linear(d, n_out))
    return nn.Sequential(*blocks)


def n_params(m):
    return sum(p.numel() for p in m.parameters())


def solve_width(family, target, depth, n_in, n_out, **kw):
    """Smallest width whose parameter count is nearest `target`."""
    best = None
    for w in range(4, 1400):
        p = n_params(build(family, w, depth, n_in, n_out, **kw))
        d = abs(p - target)
        if best is None or d < best[0]:
            best = (d, w, p)
        if p > 2.2 * target:
            break
    return best[1], best[2]


# ─────────────────────────────────────────────────────────────────────────────

def train_one(family, width, depth, Xtr, Ytr, seed, steps=4000, lr=3e-3,
              val_frac=0.12, patience=400, **kw):
    """Train to the best VALIDATION loss, not to convergence on the training set.

    Without this, 4000 unregularised steps on 691 samples overfit hard: measured
    train 0.0213 vs novel-material 0.1197, a 5.6x gap, against 1.2x for sklearn's
    early-stopped MLP. Every family would have been handicapped equally, but the
    comparison would then be between three over-fitted models rather than three
    properly-trained ones — and an architecture difference could easily hide
    inside that. Same class of error as B14.

    The validation split is carved out of TRAIN. Selecting on novel-material
    would leak the test set into model selection.
    """
    torch.manual_seed(seed)
    model = build(family, width, depth, Xtr.shape[1], Ytr.shape[1], **kw).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps, eta_min=lr * 1e-2)

    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(Xtr))
    n_val = max(8, int(val_frac * len(Xtr)))
    vi, fi = perm[:n_val], perm[n_val:]

    Xf = torch.tensor(Xtr[fi], dtype=torch.float32, device=DEVICE)
    Yf = torch.tensor(Ytr[fi], dtype=torch.float32, device=DEVICE)
    Xv = torch.tensor(Xtr[vi], dtype=torch.float32, device=DEVICE)
    Yv = torch.tensor(Ytr[vi], dtype=torch.float32, device=DEVICE)

    best_val, best_state, best_step, since = np.inf, None, 0, 0
    for step in range(steps):
        model.train()
        opt.zero_grad(set_to_none=True)
        loss = nn.functional.mse_loss(model(Xf), Yf)
        if not torch.isfinite(loss):
            raise RuntimeError(f"{family} diverged at width {width}, seed {seed}, step {step}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()

        if step % 25 == 0 or step == steps - 1:
            model.eval()
            with torch.no_grad():
                v = float(nn.functional.mse_loss(model(Xv), Yv))
            if v < best_val - 1e-9:
                best_val, best_step, since = v, step, 0
                best_state = {k: t.detach().clone() for k, t in model.state_dict().items()}
            else:
                since += 25
                if since >= patience:
                    break

    if best_state is not None:
        model.load_state_dict(best_state)
    return model, {"best_val": best_val, "best_step": best_step, "stopped_at": step}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modes", type=int, default=64)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--budgets", type=int, nargs="+", default=[50_000, 200_000, 800_000])
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--lrs", type=float, nargs="+", default=[3e-3, 1e-3],
                    help="swept; each family is reported at ITS best lr (protocol s3)")
    ap.add_argument("--out", default="results/l3_results.json")
    args = ap.parse_args()

    t0 = time.time()
    d = ladder_data.load()
    shape = d.fields.shape[2:]
    tr = d.idx("train")
    print(f"\nPOD ({args.modes} modes/channel, train only) — identical to L1/L2:")
    bases, _ = fit_pod(d.fields, tr, args.modes)
    coeffs = project(d.fields, bases)
    gc.collect()

    floor = {}
    for split in ladder_data.SPLITS:
        idx = d.idx(split)
        rows = evaluate(coeffs[idx], d.fields[idx], bases, shape, d.t_final[idx])
        floor[split] = float(np.nanmean([r["c"] for r in rows]))
    print(f"POD floor (novel-material): {floor['novel_material']:.4e}")

    # target standardisation — the B14 lesson: unscaled POD coefficients span 309x
    mu, sd = coeffs[tr].mean(0), coeffs[tr].std(0)
    sd[sd == 0] = 1.0
    Y = (coeffs - mu) / sd

    n_in, n_out = d.params_z.shape[1], coeffs.shape[1]
    results = {"modes": args.modes, "seeds": args.seeds, "depth": args.depth,
               "steps": args.steps, "pod_floor": floor, "splits": d.summary(), "arms": []}

    print(f"\nmatched-parameter widths (depth {args.depth}, {n_in} -> {n_out}):")
    plan = []
    for budget in args.budgets:
        for fam in ("mlp", "rbf_kan", "cheby_kan"):
            w, p = solve_width(fam, budget, args.depth, n_in, n_out)
            for lr in args.lrs:
                plan.append((budget, fam, w, p, lr))
            print(f"  budget {budget:>8,}  {fam:<10} width {w:>4}  params {p:>9,}"
                  f"  ({100 * (p - budget) / budget:+.1f}%)  lrs {args.lrs}")

    print()
    for budget, fam, w, p, lr in plan:
        rec = {"budget": budget, "family": fam, "width": w, "n_params": p,
               "lr": lr, "seeds": {}}
        for seed in args.seeds:
            t1 = time.time()
            model, info = train_one(fam, w, args.depth, d.params_z[tr], Y[tr],
                                    seed, steps=args.steps, lr=lr)
            model.eval()
            per = {}
            with torch.no_grad():
                for split in ("train", "novel_material"):
                    idx = d.idx(split)
                    X = torch.tensor(d.params_z[idx], dtype=torch.float32, device=DEVICE)
                    pred = model(X).cpu().numpy() * sd + mu
                    rows = evaluate(pred, d.fields[idx], bases, shape, d.t_final[idx])
                    per[split] = {
                        "c": float(np.nanmean([r["c"] for r in rows])),
                        "dt_bt50": float(np.nanmean([r["dt_bt50"] for r in rows])),
                        "per_sample_nrmse_c": [float(r["c"]) for r in rows],
                        "material_ids": d.material_ids[idx].tolist(),
                    }
            per["early_stop"] = info
            rec["seeds"][str(seed)] = per
            print(f"  {budget:>8,} {fam:<10} w{w:<4} lr{lr:.0e} seed {seed}: "
                  f"train={per['train']['c']:.4f}  novel={per['novel_material']['c']:.4f}"
                  f"  (best@{info['best_step']}/{info['stopped_at']})"
                  f"  [{time.time() - t1:.0f}s]", flush=True)
            del model
            gc.collect()
        results["arms"].append(rec)
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2)

    print(f"\nwrote {args.out}  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
