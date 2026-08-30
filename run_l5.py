"""L5 — the operator rung, and a direct test of the n-width prediction.

Hypothesis under test: *"you need an operator."*

Two questions, one experiment.

**(a) The n-width test.** A DeepONet's output is exactly

        u(params, z, t) = sum_{k=1..p} b_k(params) * t_k(z, t)  + bias

a LINEAR reconstruction in a learned p-term basis. Section 6d measured the
Kolmogorov n-width of this solution manifold as **algebraic**, d_n ~ n^-1.23 over
n = 8-64. Any linear-reconstruction method is bounded below by that decay, so:

    prediction: DeepONet error falls ALGEBRAICALLY with p, tracking the POD
    floor's slope, and cannot be rescued by widening the branch or trunk.

The branch and trunk change b_k and t_k. They do not make the reconstruction
nonlinear. If error-vs-p is flat in branch/trunk width but falls with p, the
bottleneck is the basis size, i.e. the n-width - not capacity.

**(b) Family comparison at matched parameters.** DeepONet vs DeepOKAN (RBF-KAN
branch/trunk) at equal parameter count and equal p. L3 found KAN edges
significantly WORSE at matched parameters in a pointwise regressor; the n-width
argument predicts the operator setting is no different, because the binding
constraint is the linear reconstruction rather than the edge family.

Encoding is frozen for this rung: all arms see the same subsampled (nz_s, nt_s)
grid. Cross-rung comparison against L1-L4 absolute numbers is NOT valid and is
not made.
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
from output_head import apply_bounded_head

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

NZ_S, NT_S = 128, 128          # frozen encoding for this rung


def mlp(n_in, n_out, width, depth):
    layers, d = [], n_in
    for _ in range(depth):
        layers += [nn.Linear(d, width), nn.GELU()]
        d = width
    layers.append(nn.Linear(d, n_out))
    return nn.Sequential(*layers)


class RBFKANStack(nn.Module):
    """Gaussian-RBF edges with a SiLU base path (the L3 `rbf_kan` block)."""

    def __init__(self, n_in, n_out, width, depth, grids=4):
        super().__init__()
        dims = [n_in] + [width] * depth + [n_out]
        self.blocks = nn.ModuleList()
        for i in range(len(dims) - 1):
            self.blocks.append(_RBFBlock(dims[i], dims[i + 1], grids))

    def forward(self, x):
        for i, b in enumerate(self.blocks):
            x = b(x) if i == len(self.blocks) - 1 else torch.nn.functional.gelu(b(x))
        return x


class _RBFBlock(nn.Module):
    def __init__(self, i, o, grids):
        super().__init__()
        self.base = nn.Linear(i, o, bias=False)
        self.act = nn.SiLU()
        self.register_buffer("centers", torch.linspace(-2.0, 2.0, grids))
        self.h = 4.0 / max(grids - 1, 1)
        self.coeffs = nn.Parameter(torch.randn(i, o, grids) / np.sqrt(i * grids))

    def forward(self, x):
        z = (x.unsqueeze(-1) - self.centers) / self.h
        return self.base(self.act(x)) + torch.einsum("nig,iog->no", torch.exp(-z * z), self.coeffs)


class DeepONet(nn.Module):
    """u = sum_k b_k(params) t_k(z,t). `kan=True` swaps both nets for RBF-KAN stacks."""

    def __init__(self, n_params, p=64, width=128, depth=3, kan=False, grids=4):
        super().__init__()
        self.p = p
        make = (lambda i, o: RBFKANStack(i, o, width, depth, grids)) if kan else \
               (lambda i, o: mlp(i, o, width, depth))
        self.branch = make(n_params, 3 * p)
        self.trunk = make(2, 3 * p)
        self.bias = nn.Parameter(torch.zeros(3))

    def forward(self, params, coords):
        """params (B, P); coords (N, 2) shared across the batch -> (B, N, 3)."""
        B = params.shape[0]
        N = coords.shape[0]
        b = self.branch(params).view(B, 3, self.p)
        t = self.trunk(coords).view(N, 3, self.p)
        raw = torch.einsum("bcp,ncp->bnc", b, t) + self.bias
        c, q, T = apply_bounded_head(raw[..., 0:1], raw[..., 1:2], raw[..., 2:3])
        return torch.cat([c, q, T], dim=-1)


def n_params_of(m):
    return sum(x.numel() for x in m.parameters())


def solve_width(n_in, p, depth, target, kan, grids=4):
    best = None
    for w in range(8, 700, 2):
        n = n_params_of(DeepONet(n_in, p=p, width=w, depth=depth, kan=kan, grids=grids))
        d = abs(n - target)
        if best is None or d < best[0]:
            best = (d, w, n)
        if n > 2.5 * target:
            break
    return best[1], best[2]


def subsample(d):
    """Frozen encoding: (NZ_S, NT_S) grid, and the matching coordinate list."""
    nz, nt = d.fields.shape[2:]
    zi = np.linspace(0, nz - 1, NZ_S).astype(int)
    ti = np.linspace(0, nt - 1, NT_S).astype(int)
    F = d.fields[:, :, zi][:, :, :, ti].astype(np.float32)      # (N,3,NZ_S,NT_S)
    zg, tg = np.meshgrid(zi / (nz - 1), ti / (nt - 1), indexing="ij")
    coords = np.stack([zg.ravel(), tg.ravel()], 1).astype(np.float32)
    return F, coords


def pod_floor(F, tr_idx, p):
    """Best achievable by ANY p-term linear basis, per channel — the n-width bound."""
    from sklearn.decomposition import PCA
    n = F.shape[0]
    errs = np.zeros(n)
    rng = np.zeros(n)
    for ch in range(3):
        X = F[:, ch].reshape(n, -1)
        pca = PCA(n_components=p, svd_solver="randomized", random_state=0).fit(X[tr_idx])
        rec = pca.inverse_transform(pca.transform(X))
        if ch == 0:
            errs = np.sqrt(((rec - X) ** 2).mean(1))
            rng = X.max(1) - X.min(1)
    return errs / np.maximum(rng, 1e-12)


def train_eval(F, coords, d, args, p, width, kan, seed):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    tr, nm = d.idx("train"), d.idx("novel_material")
    model = DeepONet(d.params_z.shape[1], p=p, width=width, depth=args.depth,
                     kan=kan, grids=args.grids).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.steps, eta_min=args.lr * 1e-2)

    Pz = torch.tensor(d.params_z, dtype=torch.float32, device=DEVICE)
    C = torch.tensor(coords, device=DEVICE)
    Ft = torch.tensor(F.reshape(F.shape[0], 3, -1).transpose(0, 2, 1), device=DEVICE)  # (N, P, 3)

    for step in range(args.steps):
        opt.zero_grad(set_to_none=True)
        bi = torch.tensor(tr[rng.integers(0, len(tr), args.batch)], device=DEVICE)
        pi = torch.tensor(rng.integers(0, C.shape[0], args.n_pts), device=DEVICE)
        pred = model(Pz[bi], C[pi])
        loss = nn.functional.mse_loss(pred, Ft[bi][:, pi, :])
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss at step {step}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sch.step()

    model.eval()
    out = {}
    with torch.no_grad():
        for tag, idx in (("train", tr[:150]), ("novel_material", nm)):
            per = []
            for s0 in range(0, len(idx), 16):
                bi = torch.tensor(idx[s0:s0 + 16], device=DEVICE)
                pr = model(Pz[bi], C).cpu().numpy()[..., 0]          # channel c
                tr_ = Ft[bi].cpu().numpy()[..., 0]
                rngc = tr_.max(1) - tr_.min(1)
                per += list(np.sqrt(((pr - tr_) ** 2).mean(1)) / np.maximum(rngc, 1e-12))
            out[tag] = {"c": float(np.mean(per)), "per_sample_nrmse_c": [float(x) for x in per],
                        "material_ids": d.material_ids[idx].tolist()}
    del model; gc.collect()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ps", type=int, nargs="+", default=[8, 16, 32, 64, 128])
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--budget", type=int, default=200_000)
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--grids", type=int, default=4)
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--lrs", type=float, nargs="+", default=[1e-3, 3e-4, 1e-4],
                    help="swept; each (family, p) reported at ITS best (protocol s3). "
                         "A single lr saturates the narrow RBF-KAN stack -- defect B22.")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--n-pts", type=int, default=2048)
    ap.add_argument("--out", default="results/l5_results.json")
    ap.add_argument("--families", nargs="+", default=["deeponet", "deepokan"],
                    choices=["deeponet", "deepokan"],
                    help="restrict the sweep; used to resume one family without "
                         "re-running the other. analyze_l5.merge() recombines the "
                         "files and refuses duplicate (family, p, lr) keys.")
    ap.add_argument("--threads", type=int, default=0,
                    help="torch intra-op threads. 0 leaves the default. Set this "
                         "when running sweeps concurrently: three unbounded jobs "
                         "put 85 threads on 12 cores and one made no progress for "
                         "52 minutes.")
    args = ap.parse_args()
    if args.threads > 0:
        torch.set_num_threads(args.threads)

    t0 = time.time()
    d = ladder_data.load()
    F, coords = subsample(d)
    print(f"\nfrozen encoding {NZ_S}x{NT_S}; fields {F.shape}; coords {coords.shape}")
    tr = d.idx("train")

    res = {"nz_s": NZ_S, "nt_s": NT_S, "ps": args.ps, "seeds": args.seeds,
           "budget": args.budget, "depth": args.depth, "steps": args.steps,
           "splits": d.summary(), "pod_floor": {}, "arms": []}

    print("\nPOD floor at each p (the n-width bound on ANY linear reconstruction):")
    for p in args.ps:
        e = pod_floor(F, tr, p)
        res["pod_floor"][str(p)] = {
            "train": float(e[tr].mean()),
            "novel_material": float(e[d.idx("novel_material")].mean())}
        print(f"  p={p:>4}  novel-material {res['pod_floor'][str(p)]['novel_material']:.5f}")
        gc.collect()

    print()
    for kan in (False, True):
        name = "deepokan" if kan else "deeponet"
        if name not in args.families:
            continue
        for p in args.ps:
            w, npar = solve_width(d.params_z.shape[1], p, args.depth, args.budget, kan, args.grids)
            for lr in args.lrs:
                args.lr = lr
                rec = {"family": name, "p": p, "width": w, "n_params": npar,
                       "lr": lr, "seeds": {}}
                for seed in args.seeds:
                    t1 = time.time()
                    o = train_eval(F, coords, d, args, p, w, kan, seed)
                    rec["seeds"][str(seed)] = o
                    print(f"  {name:<9} p={p:>4} w{w:<4} lr{lr:.0e} seed {seed}: "
                          f"train={o['train']['c']:.4f} novel={o['novel_material']['c']:.4f} "
                          f"[{time.time() - t1:.0f}s]", flush=True)
                res["arms"].append(rec)
                os.makedirs(os.path.dirname(args.out), exist_ok=True)
                json.dump(res, open(args.out, "w"), indent=2)
            os.makedirs(os.path.dirname(args.out), exist_ok=True)
            json.dump(res, open(args.out, "w"), indent=2)

    print(f"\nwrote {args.out}  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
