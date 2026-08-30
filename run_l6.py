"""L6 — identification structure. This is H1, the project's primary hypothesis.

Question: does identifying the **equilibrium** object and the **kinetic** object
separately, and composing them through the known conservation structure, transfer
to held-out materials better than fitting the field jointly — at matched
parameter count and matched inputs?

Inputs are the OBSERVABLE descriptors (`descriptors.py`), not the generative
parameters. Under the generative parameterisation the rung is degenerate: a
separate arm would have nothing to identify (defect B19). Under the observable
one, the equilibrium object is largely visible (a measured isotherm) while the
kinetic coefficient is not recoverable at all (R^2 = -0.61), so the decomposition
is real work.

Arms (identical descriptors, matched parameter count, same seeds/steps/optimiser)

  joint      one network:  descriptors, z*, t*  ->  (c*, q*, T*)
             Free-form. Nothing is imposed.

  separate   three small heads, composed through the LDF structure:
               eq_head(descriptors, c*, T*) -> q*_eq        the equilibrium object
               kin_head(descriptors)        -> log k        the kinetic object
               field_head(descriptors,z*,t*)-> (c*, T*)     transport
             q* is then NOT a free output. It is obtained by integrating

                 dq/dt = k (q*_eq - q)

             along t with an exponential-integrator (Duhamel) quadrature, which
             is exact for the linear LDF law given q*_eq. So the kinetic object
             enters as STRUCTURE rather than as a penalty, and q inherits the
             correct relaxation behaviour by construction.

  separate_noeq  ablation: same composition, but the equilibrium head is replaced
             by a free output. Isolates how much of any gain comes from the
             STRUCTURE versus from having an equilibrium object at all.

Pre-declared: if the separate-vs-joint gap on novel materials has a bootstrap CI
including zero at 3 seeds and the calibrated alpha, H1 is reported as NOT
SUPPORTED, in the abstract, in those words.
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

import descriptors as DSC
import ladder_data
from output_head import apply_output_head

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def mlp(n_in, n_out, width, depth):
    layers, d = [], n_in
    for _ in range(depth):
        layers += [nn.Linear(d, width), nn.GELU()]
        d = width
    layers.append(nn.Linear(d, n_out))
    return nn.Sequential(*layers)


class Joint(nn.Module):
    """descriptors, z, t -> (c, q, T). Free-form."""

    def __init__(self, n_desc, width=160, depth=4, dT_max=0.5):
        super().__init__()
        self.net = mlp(n_desc + 2, 3, width, depth)
        self.dT_max = dT_max

    def forward(self, desc, z, t, ray_shape=None, **_):
        h = self.net(torch.cat([desc, z, t], dim=1))
        c, q, T = apply_output_head(h[:, 0:1], h[:, 1:2], h[:, 2:3], t, self.dT_max)
        return torch.cat([c, q, T], dim=1)


class Separate(nn.Module):
    """Equilibrium + kinetics identified separately, composed by Duhamel.

    q(z,t) = int_0^t k exp(-k (t-s)) q_eq(c(z,s), T(z,s)) ds

    which is the exact solution of dq/dt = k (q_eq - q) with q(0)=0. Evaluating it
    needs the field along the whole time ray up to t, so the trunk is queried at
    `n_quad` points on [0,t] per collocation point. That makes this arm more
    expensive per step than `joint`; the parameter counts are matched, the
    FLOPs are not, and that is reported.
    """

    def __init__(self, n_desc, width=128, depth=4, dT_max=0.5, learn_eq=True):
        super().__init__()
        self.field = mlp(n_desc + 2, 2, width, depth)        # c, T
        self.learn_eq = learn_eq
        if learn_eq:
            self.eq = mlp(n_desc + 2, 1, width // 2, 2)      # (desc, c, T) -> q_eq
        else:
            self.free_q = mlp(n_desc + 2, 1, width // 2, 2)  # ablation: free q
        self.log_k = mlp(n_desc, 1, width // 2, 2)           # (desc) -> log k
        self.dT_max = dT_max

    def _field(self, desc, z, t):
        h = self.field(torch.cat([desc, z, t], dim=1))
        c = t * nn.functional.softplus(h[:, 0:1])
        T = 1.0 + self.dT_max * torch.tanh(t * h[:, 1:2])
        return c, T

    def forward(self, desc, z, t, ray_shape=None, **_):
        """`ray_shape` = (n_rays, n_t) when inputs are laid out as contiguous rays.

        With rays, q follows from the exponential-integrator scan along each ray
        and costs ONE network evaluation per point. Without it, q would need a
        quadrature per point; that path is not used.
        """
        c, T = self._field(desc, z, t)
        if not self.learn_eq:
            q = t * nn.functional.softplus(self.free_q(torch.cat([desc, c, T], dim=1)))
            return torch.cat([c, q, T], dim=1)

        q_eq = nn.functional.softplus(self.eq(torch.cat([desc, c, T], dim=1)))
        k = torch.exp(torch.clamp(self.log_k(desc), -8.0, 4.0))

        if ray_shape is None:
            raise ValueError("Separate(learn_eq=True) needs ray_shape; see sample_rays()")
        R, Q = ray_shape
        qe = q_eq.view(R, Q)
        kk = k.view(R, Q)[:, :1]
        tt = t.view(R, Q)
        dt = (tt[:, 1:2] - tt[:, 0:1]).clamp(min=1e-8)
        a = torch.exp(-kk * dt)                       # (R,1)
        qs = [torch.zeros_like(qe[:, 0])]
        for i in range(1, Q):                          # dq/dt = k (q_eq - q), exact
            qs.append(a[:, 0] * qs[-1] + (1.0 - a[:, 0]) * qe[:, i - 1])
        q = torch.stack(qs, dim=1).reshape(-1, 1)
        return torch.cat([c, q.clamp(min=0.0), T], dim=1)


ARMS = {
    "joint": lambda n, w, dp: Joint(n, width=w, depth=dp),
    "separate": lambda n, w, dp: Separate(n, width=w, depth=dp, learn_eq=True),
    "separate_noeq": lambda n, w, dp: Separate(n, width=w, depth=dp, learn_eq=False),
}


def solve_width(arm, n_desc, target, depth):
    best = None
    for w in range(16, 900, 2):
        p = sum(x.numel() for x in ARMS[arm](n_desc, w, depth).parameters())
        dv = abs(p - target)
        if best is None or dv < best[0]:
            best = (dv, w, p)
        if p > 2.5 * target:
            break
    return best[1], best[2]


def sample_rays(d, idx, n_rays, n_t, rng):
    """Sample (material, z) RAYS and observe the whole time series along each.

    Not iid points. Two reasons:

    1. It is what a breakthrough measurement actually is - a probe at one
       position recording concentration over time.
    2. It makes the `separate` arm affordable. The Duhamel integral along a ray
       is an exponential-integrator SCAN over the ray's own time points, so the
       kinetic structure costs one network evaluation per point instead of
       `n_quad`. Pointwise iid sampling forced 12x the forward passes and put the
       arm at ~1.17 s/step, which does not finish.

    Every arm uses this sampling, so the supervised budget (n_rays * n_t points)
    is identical across arms and parity is preserved.
    """
    nz, nt = d.fields.shape[2:]
    rows = rng.integers(0, len(idx), n_rays)
    zi = rng.integers(0, nz, n_rays)
    g = idx[rows]                                     # (R,)
    ti = np.linspace(0, nt - 1, n_t).astype(int)      # shared time grid
    y = d.fields[np.repeat(g, n_t), :,
                 np.repeat(zi, n_t), np.tile(ti, n_rays)].astype(np.float32)
    z = np.repeat((zi / (nz - 1)).astype(np.float32), n_t)
    t = np.tile((ti / (nt - 1)).astype(np.float32), n_rays)
    return np.repeat(g, n_t), z, t, y, n_rays, n_t


@torch.no_grad()
def _grid_predict(model, dv, zf, tf, nz, nt, n_quad, chunk):
    """Field on the full (z,t) grid.

    For `Separate`, evaluating the Duhamel integral pointwise costs `n_quad`
    network calls per query — 201 samples x 131,072 points x 12 = 3.2e8 forward
    passes, which does not finish on CPU.

    On a REGULAR grid it is unnecessary. The convolution

        q(t) = int_0^t k exp(-k (t-s)) q_eq(s) ds

    satisfies the exponential-integrator recurrence, exact for piecewise-constant
    q_eq on a uniform t-grid:

        q_{i+1} = e^{-k dt} q_i + (1 - e^{-k dt}) q_eq,i

    so the trunk is evaluated ONCE per grid point and q follows by a scan along t.
    That is both `n_quad` times cheaper and more accurate than the quadrature,
    because it integrates every step rather than `n_quad` sample points.
    """
    if not isinstance(model, Separate) or not model.learn_eq:
        outs = []
        for s0 in range(0, zf.shape[0], chunk):
            e = min(s0 + chunk, zf.shape[0])
            outs.append(model(dv.unsqueeze(0).expand(e - s0, -1),
                              zf[s0:e], tf[s0:e], n_quad=n_quad).cpu().numpy())
        return np.concatenate(outs, 0).T.reshape(3, nz, nt)

    cs, Ts, qe = [], [], []
    for s0 in range(0, zf.shape[0], chunk):
        e = min(s0 + chunk, zf.shape[0])
        df = dv.unsqueeze(0).expand(e - s0, -1)
        c_, T_ = model._field(df, zf[s0:e], tf[s0:e])
        qe_ = nn.functional.softplus(model.eq(torch.cat([df, c_, T_], dim=1)))
        cs.append(c_); Ts.append(T_); qe.append(qe_)
    c = torch.cat(cs).view(nz, nt)
    T = torch.cat(Ts).view(nz, nt)
    q_eq = torch.cat(qe).view(nz, nt)

    k = float(torch.exp(torch.clamp(model.log_k(dv.unsqueeze(0)), -8.0, 4.0)))
    dt = 1.0 / (nt - 1)
    a = float(np.exp(-k * dt))
    q = torch.zeros_like(q_eq)
    for i in range(1, nt):                      # exponential-integrator scan
        q[:, i] = a * q[:, i - 1] + (1.0 - a) * q_eq[:, i - 1]
    return torch.stack([c, q, T]).cpu().numpy()


@torch.no_grad()
def eval_fields(model, d, idx, X, n_quad, chunk=32768):
    from metrics import breakthrough_times, per_variable_nrmse
    nz, nt = d.fields.shape[2:]
    zg, tg = np.meshgrid(np.linspace(0, 1, nz, dtype=np.float32),
                         np.linspace(0, 1, nt, dtype=np.float32), indexing="ij")
    zf = torch.tensor(zg.ravel(), device=DEVICE).unsqueeze(1)
    tf = torch.tensor(tg.ravel(), device=DEVICE).unsqueeze(1)
    t_norm = np.linspace(0.0, 1.0, nt)
    rows = []
    for gi in idx:
        dv = torch.tensor(X[gi], dtype=torch.float32, device=DEVICE)
        out = _grid_predict(model, dv, zf, tf, nz, nt, n_quad, chunk)
        true = d.fields[gi]
        m = per_variable_nrmse(out, true)
        m["exit_nrmse"] = float(np.sqrt(np.mean((out[0, -1] - true[0, -1]) ** 2))
                                / max(true[0, -1].max() - true[0, -1].min(), 1e-12))
        bp, bt = breakthrough_times(out[0, -1], t_norm), breakthrough_times(true[0, -1], t_norm)
        a, b = bp[0.50], bt[0.50]
        m["dt_bt50"] = abs(a - b) * d.t_final[gi] if np.isfinite(a) and np.isfinite(b) else np.nan
        rows.append(m)
    return rows


def train(arm, d, X, tr_idx, args, seed):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    w, npar = solve_width(arm, X.shape[1], args.budget, args.depth)
    model = ARMS[arm](X.shape[1], w, args.depth).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.steps, eta_min=args.lr * 1e-2)
    Xt = torch.tensor(X, dtype=torch.float32, device=DEVICE)

    for step in range(args.steps):
        opt.zero_grad(set_to_none=True)
        g, z, t, y, R, Q = sample_rays(d, tr_idx, args.n_rays, args.n_t, rng)
        gt = torch.tensor(g, device=DEVICE)
        pred = model(Xt[gt], torch.tensor(z, device=DEVICE).unsqueeze(1),
                     torch.tensor(t, device=DEVICE).unsqueeze(1), ray_shape=(R, Q))
        loss = nn.functional.mse_loss(pred, torch.tensor(y, device=DEVICE))
        if not torch.isfinite(loss):
            raise RuntimeError(f"{arm} non-finite loss at step {step}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sch.step()
    return model, w, npar


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms", nargs="+", default=["joint", "separate", "separate_noeq"])
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--budget", type=int, default=120_000)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--steps", type=int, default=12000)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--n-rays", type=int, default=128)
    ap.add_argument("--n-t", type=int, default=32)     # 128*32 = 4096 supervised points
    ap.add_argument("--out", default="results/l6_results.json")
    args = ap.parse_args()

    t0 = time.time()
    d = ladder_data.load()
    X_raw, names = DSC.build(d)
    tr = d.idx("train")
    X, mu, sd = DSC.standardise(X_raw, tr)
    print(f"\nobservable descriptors: {X.shape[1]} features (generative parameters WITHHELD)")
    print(f"matched parameter budget ~{args.budget:,}, depth {args.depth}\n")

    res = {"budget": args.budget, "depth": args.depth, "steps": args.steps,
           "seeds": args.seeds, "n_desc": X.shape[1], "descriptor_names": names,
           "splits": d.summary(), "arms": {}}

    for arm in args.arms:
        res["arms"][arm] = {}
        for seed in args.seeds:
            t1 = time.time()
            model, w, npar = train(arm, d, X, tr, args, seed)
            model.eval()
            per = {}
            for split in ("train", "novel_material"):
                idx = d.idx(split)
                sub = idx if split != "train" else idx[:200]
                rows = eval_fields(model, d, sub, X, args.n_t)
                per[split] = {
                    "c": float(np.nanmean([r["c"] for r in rows])),
                    "q": float(np.nanmean([r["q"] for r in rows])),
                    "T": float(np.nanmean([r["T"] for r in rows])),
                    "exit_nrmse": float(np.nanmean([r["exit_nrmse"] for r in rows])),
                    "dt_bt50": float(np.nanmean([r["dt_bt50"] for r in rows])),
                    "per_sample_nrmse_c": [float(r["c"]) for r in rows],
                    "material_ids": d.material_ids[sub].tolist(),
                }
            res["arms"][arm][str(seed)] = {**per, "width": w, "n_params": npar}
            nm = per["novel_material"]
            print(f"  {arm:<14} w{w:<4} {npar:>8,}p seed {seed}: "
                  f"train={per['train']['c']:.4f} novel={nm['c']:.4f} "
                  f"q={nm['q']:.4f} exit={nm['exit_nrmse']:.4f} "
                  f"dt50={nm['dt_bt50']/3600:.2f}h  [{time.time()-t1:.0f}s]", flush=True)
            del model; gc.collect()
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        json.dump(res, open(args.out, "w"), indent=2)
    print(f"\nwrote {args.out}  [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
