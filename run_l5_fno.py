"""L5, the arm the frozen protocol named and nobody ran: FNO.

Why this matters more than one more baseline
--------------------------------------------
`03_LADDER_PROTOCOL.md` line 62 specifies L5's arms as "DeepONet, **FNO**, **WNO**,
DeepOKAN, matched budget". `run_l5.py` restricts `--families` to deeponet and
deepokan; FNO and WNO were never run and the deviation was never recorded
(retraction **B33**).

That is not a bookkeeping problem, because of what the two arms that DID run have
in common. A DeepONet computes

        u(params, z, t) = sum_{k=1..p} b_k(params) * t_k(z, t)

which is a LINEAR reconstruction in a learned p-term basis, and DeepOKAN is the
same reconstruction with KAN edges. Lanthaler, Molinaro, Hadorn & Mishra (ICLR
2023, arXiv:2210.01074) prove that *any* operator architecture with a linear
reconstruction step is lower-bounded on advection-dominated and discontinuous
problems, and that architectures with a NONLINEAR reconstruction -- FNO,
shift-DeepONet -- escape that bound.

So L5 as it stands eliminated only the family the theory already condemned. A
referee will say so, and they will be right. FNO is the cheapest available test of
whether the wall this project measured is a property of the PROBLEM or a property
of linear reconstruction.

**Pre-registered prediction, written before running this** (protocol convention:
the prediction is recorded so it can be wrong):

    If the coefficient-map wall is a property of the problem, FNO plateaus at
    roughly DeepONet's level (~0.028 novel-material nRMSE on c) and does not
    improve materially with Fourier modes. If it is a property of linear
    reconstruction, FNO breaks the plateau.

Both outcomes are publishable and the paper says so in advance. The first
strengthens the central claim considerably -- the wall survives the escape route
the theory names. The second narrows L5's conclusion honestly to
linear-reconstruction operators, which is still a real and citable result.

Information parity (protocol section 3), held exactly
-----------------------------------------------------
Same 128x128 frozen encoding, same splits, same seeds, same optimiser, same
schedule, same 8000 steps, same batch and point counts, same ~200k parameter
budget, and -- importantly -- the SAME OUTPUT HEAD. `fno_model_adsorption.py`
ships with `apply_output_head` (softplus + t-envelope) while `run_l5.py`'s
DeepONet uses `apply_bounded_head` (sigmoid, no envelope). Those are different
architectures, not different operators, and L4b measured the difference between
them to be worth up to 11.5x. This runner therefore forces the bounded head onto
FNO so the comparison is about the operator and nothing else.

FNO has no basis size `p`. Its analogous capacity-in-frequency knob is the number
of retained Fourier `modes`, which is what is swept here, at matched parameters.

Usage
    python run_l5_fno.py --modes 4 8 16 32 --lrs 1e-2 3e-3 1e-3 --seeds 42 43 44
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
from fno_model_adsorption import SpectralConv2d
from output_head import apply_bounded_head
from run_l5 import NZ_S, NT_S, subsample

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class FNOArm(nn.Module):
    """FNO2d over the (z,t) grid, with L5's bounded output head.

    Differs from `fno_model_adsorption.FNO2d_Adsorption` in exactly one way: the
    output head. That file uses `apply_output_head` (softplus times a t-envelope);
    L5's DeepONet uses `apply_bounded_head` (sigmoid, initial condition left to a
    residual). Mixing the two would confound the operator comparison with the
    head comparison L4b already ran separately, so the head is pinned here.
    """

    def __init__(self, n_params, modes=16, width=32, n_layers=4):
        super().__init__()
        self.modes, self.width, self.n_layers = modes, width, n_layers
        self.lift = nn.Conv2d(2 + n_params, width, 1)
        self.spectral = nn.ModuleList(SpectralConv2d(width, width, modes)
                                      for _ in range(n_layers))
        self.pointwise = nn.ModuleList(nn.Conv2d(width, width, 1) for _ in range(n_layers))
        self.act = nn.GELU()
        self.proj1 = nn.Conv2d(width, width, 1)
        self.proj2 = nn.Conv2d(width, 3, 1)
        az = torch.linspace(0.0, 1.0, NZ_S)
        at = torch.linspace(0.0, 1.0, NT_S)
        gz, gt = torch.meshgrid(az, at, indexing="ij")
        self.register_buffer("grid", torch.stack([gz, gt]).unsqueeze(0))

    def full_grid(self, params):
        B = params.shape[0]
        cond = params[:, :, None, None].expand(-1, -1, NZ_S, NT_S)
        x = torch.cat([self.grid.expand(B, -1, -1, -1), cond], dim=1)
        x = self.lift(x)
        for spec, pw in zip(self.spectral, self.pointwise):
            x = self.act(spec(x) + pw(x))
        raw = self.proj2(self.act(self.proj1(x)))              # (B,3,NZ,NT)
        c, q, T = apply_bounded_head(raw[:, 0:1], raw[:, 1:2], raw[:, 2:3])
        return torch.cat([c, q, T], dim=1)

    def forward(self, params, point_idx=None):
        """Returns (B, N, 3): the full grid flattened, optionally gathered at `point_idx`.

        The gather keeps the training loss identical in form to DeepONet's -- the
        same random subset of grid points, the same batch -- so neither arm sees
        more of the field than the other per step.
        """
        g = self.full_grid(params)                              # (B,3,NZ,NT)
        flat = g.reshape(g.shape[0], 3, -1).permute(0, 2, 1)    # (B, NZ*NT, 3)
        return flat if point_idx is None else flat[:, point_idx, :]


def n_params_of(m):
    return sum(x.numel() for x in m.parameters())


def solve_width(n_in, modes, target, n_layers):
    """Widest channel count within the parameter budget, matched like every other arm."""
    best = None
    for w in range(4, 200, 1):
        n = n_params_of(FNOArm(n_in, modes=modes, width=w, n_layers=n_layers))
        d = abs(n - target)
        if best is None or d < best[0]:
            best = (d, w, n)
        if n > 2.5 * target:
            break
    return best[1], best[2]


def train_eval(F, d, args, modes, width, lr, seed):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    tr, nm = d.idx("train"), d.idx("novel_material")
    model = FNOArm(d.params_z.shape[1], modes=modes, width=width,
                   n_layers=args.layers).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.steps, eta_min=lr * 1e-2)

    Pz = torch.tensor(d.params_z, dtype=torch.float32, device=DEVICE)
    Ft = torch.tensor(F.reshape(F.shape[0], 3, -1).transpose(0, 2, 1), device=DEVICE)
    n_grid = NZ_S * NT_S

    for step in range(args.steps):
        opt.zero_grad(set_to_none=True)
        bi = torch.tensor(tr[rng.integers(0, len(tr), args.batch)], device=DEVICE)
        pi = torch.tensor(rng.integers(0, n_grid, args.n_pts), device=DEVICE)
        pred = model(Pz[bi], pi)
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
            for s0 in range(0, len(idx), 8):
                bi = torch.tensor(idx[s0:s0 + 8], device=DEVICE)
                pr = model(Pz[bi]).cpu().numpy()[..., 0]
                tr_ = Ft[bi].cpu().numpy()[..., 0]
                rngc = tr_.max(1) - tr_.min(1)
                per += list(np.sqrt(((pr - tr_) ** 2).mean(1)) / np.maximum(rngc, 1e-12))
            out[tag] = {"c": float(np.mean(per)),
                        "per_sample_nrmse_c": [float(x) for x in per],
                        "material_ids": d.material_ids[idx].tolist()}
    del model; gc.collect()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modes", type=int, nargs="+", default=[4, 8, 16, 32])
    ap.add_argument("--lrs", type=float, nargs="+", default=[1e-2, 3e-3, 1e-3])
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--budget", type=int, default=200_000)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--steps", type=int, default=8000)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--n-pts", type=int, default=2048)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--out", default="results/l5_fno.json")
    args = ap.parse_args()
    if args.threads > 0:
        torch.set_num_threads(args.threads)

    t0 = time.time()
    d = ladder_data.load()
    F, _ = subsample(d)
    print(f"\nfrozen encoding {NZ_S}x{NT_S}; fields {F.shape}")
    print(f"budget ~{args.budget:,} params, {args.steps} steps — identical to run_l5.py\n")

    res = {"nz_s": NZ_S, "nt_s": NT_S, "modes": args.modes, "seeds": args.seeds,
           "budget": args.budget, "layers": args.layers, "steps": args.steps,
           "splits": d.summary(), "arms": []}

    for m in args.modes:
        w, n = solve_width(d.params_z.shape[1], m, args.budget, args.layers)
        print(f"  modes {m:3d}: width {w:3d}, {n:,} params ({100*(n-args.budget)/args.budget:+.1f}%)")
        for lr in args.lrs:
            rec = {"family": "fno", "modes": m, "width": w, "n_params": n,
                   "lr": lr, "seeds": {}}
            for seed in args.seeds:
                t1 = time.time()
                try:
                    per = train_eval(F, d, args, m, w, lr, seed)
                except RuntimeError as e:
                    print(f"    modes={m} lr={lr:.0e} seed {seed}: FAILED — {e}", flush=True)
                    rec["seeds"][str(seed)] = {"failed": True, "error": str(e)}
                    continue
                rec["seeds"][str(seed)] = per
                print(f"    modes={m:3d} w{w:<3} lr{lr:.0e} seed {seed}: "
                      f"train={per['train']['c']:.4f} novel={per['novel_material']['c']:.4f} "
                      f"[{time.time()-t1:.0f}s]", flush=True)
            res["arms"].append(rec)
            os.makedirs("results", exist_ok=True)
            json.dump(res, open(args.out, "w"), indent=2)

    print(f"\nwrote {args.out}  [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
