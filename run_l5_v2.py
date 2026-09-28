"""L5 on dataset v2 — the DeepONet / DeepOKAN flat-in-p sweep, 5-fold over 240 materials.

Port of `run_l5.py` specified by audit_2026-09-24/audit_risk.md findings #1-#13.
Model, parameter-matched width solver, budget, depth, grids, batch, sampled points
and optimiser are imported from / identical to `run_l5.py`; what changes is the
data plumbing, so that L5 reports over the SAME 240 materials in the SAME folds as
L1/L2/L6/L7:

  #1  data: ladder_data.load(ROOT_V2, field_res=FIELD_RES) — 128x128 on load, so the
      frozen L5 encoding (NZ_S = NT_S = 128) needs no second subsample.
  #2  split: the L6-v2 fold map (v2_common.load_folds); `--design manifest` keeps the
      dataset's own 48-material split as a clearly separate, labelled view.
  #3  per-fold parameter standardisation on the fit set only (standardise_params),
      assert_disjoint before every fit; d.params_z (manifest-train scaler) is unused.
  #4  POD floor per fold, c channel only (the only scored channel), per-sample floor
      vector with material/condition ids for out-of-fold pooling.
  #5  train diagnostic on a RANDOM subset (rng seeded by fold); held-out tag "test".
  #11 no extra full copies of the fields: d.fields is already (N,3,128,128) and the
      torch tensor is a zero-copy strided view of it.
  #12 resumable: load_or_init + get_path/set_path, write_atomic after EVERY
      (fold, family, p, lr, seed) cell.
  #10 lr grid default 3e-3 1e-2 3e-2 (the top point is new: 1e-2 was unbracketed).
  #13 `--arm steps`: the pre-declared step-count sensitivity arm — p in {8,128} at a
      given lr, steps in {8000, 24000}, 3 seeds, one fold — written to its own file.

    python run_l5_v2.py                                   # the sweep (folds design)
    python run_l5_v2.py --only-folds 0 1 --families deeponet
    python run_l5_v2.py --arm steps --steps-lr 1e-2 --steps-fold 0
"""
from __future__ import annotations

import argparse
import gc
import time

import numpy as np
import torch
import torch.nn as nn

import ladder_data
from run_l5 import DEVICE, NZ_S, NT_S, DeepONet, solve_width
from v2_common import (FIELD_RES, FOLDS_FILE, ROOT_V2, assert_disjoint, get_path,
                       load_folds, load_or_init, set_path, standardise_params,
                       write_atomic)


# ─────────────────────────────────────────────────────────────────────────────
# encoding and floor
# ─────────────────────────────────────────────────────────────────────────────

def coords_for(fields):
    """Coordinate list for the frozen (NZ_S, NT_S) encoding, WITHOUT copying fields (#11).

    ladder_data.load(field_res=128) already subsampled with the same linspace rule
    run_l5.subsample uses, so the grid is the (normalised) 128x128 lattice.
    """
    nz, nt = fields.shape[2:]
    if (nz, nt) != (NZ_S, NT_S):
        raise SystemExit(f"fields are {nz}x{nt}; L5's frozen encoding is {NZ_S}x{NT_S}. "
                         f"Load with field_res={NZ_S}.")
    zg, tg = np.meshgrid(np.arange(nz) / (nz - 1), np.arange(nt) / (nt - 1), indexing="ij")
    return np.stack([zg.ravel(), tg.ravel()], 1).astype(np.float32)


def field_view(fields):
    """(N, P, 3) float32 torch view sharing memory with d.fields (no copy on CPU)."""
    n = fields.shape[0]
    v = fields.reshape(n, 3, -1).transpose(0, 2, 1)          # numpy view, positive strides
    return torch.from_numpy(v) if DEVICE.type == "cpu" else torch.tensor(v, device=DEVICE)


def pod_floor_c(fields, fit_idx, held_idx, p, chunk=256):
    """Per-sample c-channel POD floor on `held_idx`, basis fitted on `fit_idx` only (#4)."""
    from sklearn.decomposition import PCA
    assert_disjoint(fit_idx, held_idx, f"POD floor basis (p={p})")
    X_fit = fields[fit_idx, 0].reshape(len(fit_idx), -1)
    pca = PCA(n_components=p, svd_solver="randomized", random_state=0).fit(X_fit)
    del X_fit
    out = []
    for s in range(0, len(held_idx), chunk):              # chunked: no full-size reconstruction
        X = fields[held_idx[s:s + chunk], 0].reshape(len(held_idx[s:s + chunk]), -1)
        rec = pca.inverse_transform(pca.transform(X))
        out.append(np.sqrt(((rec - X) ** 2).mean(1)) / np.maximum(X.max(1) - X.min(1), 1e-12))
    return np.concatenate(out)


# ─────────────────────────────────────────────────────────────────────────────
# one cell
# ─────────────────────────────────────────────────────────────────────────────

def train_eval(Ft, C, Pz, d, tr, eval_sets, p, width, kan, seed, lr, steps, args):
    """Train on `tr` (per-fold standardised Pz), score channel c on each eval set.

    Identical optimisation to run_l5.train_eval: Adam, cosine to lr/100, grad-clip 1,
    batch x n_pts random points per step, MSE on all three channels.
    """
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = DeepONet(Pz.shape[1], p=p, width=width, depth=args.depth,
                     kan=kan, grids=args.grids).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps, eta_min=lr * 1e-2)
    for step in range(steps):
        opt.zero_grad(set_to_none=True)
        bi = torch.as_tensor(tr[rng.integers(0, len(tr), args.batch)], device=DEVICE)
        pi = torch.as_tensor(rng.integers(0, C.shape[0], args.n_pts), device=DEVICE)
        pred = model(Pz[bi], C[pi])
        loss = nn.functional.mse_loss(pred, Ft[bi[:, None], pi[None, :]])
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss at step {step}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sch.step()

    model.eval()
    out = {}
    with torch.no_grad():
        for tag, idx in eval_sets.items():
            per = []
            for s0 in range(0, len(idx), 16):
                bi = torch.as_tensor(idx[s0:s0 + 16], device=DEVICE)
                pr = model(Pz[bi], C)[..., 0].cpu().numpy()
                tt = Ft[bi][..., 0].cpu().numpy()
                per += list(np.sqrt(((pr - tt) ** 2).mean(1)) / np.maximum(tt.max(1) - tt.min(1), 1e-12))
            rec = {"c": float(np.mean(per))}
            if tag != "train":                               # per-sample vectors for held-out only
                rec.update({"per_sample_nrmse_c": [float(x) for x in per],
                            "material_ids": d.material_ids[idx].tolist(),
                            "condition_ids": d.condition_ids[idx].tolist()})
            out[tag] = rec
    del model, opt
    gc.collect()
    return out


# ─────────────────────────────────────────────────────────────────────────────
# driver
# ─────────────────────────────────────────────────────────────────────────────

def run_unit(res, path_prefix, d, Ft, C, tr, te, held_tag, cells, args, out_path, label, seed_rng):
    """Floors + every (family, p, lr, steps, seed) cell of one fold / split, resumably."""
    assert_disjoint(tr, te, f"DeepONet parameter scaler ({label})")        # #3
    Pz_np = standardise_params(d.params, tr)
    Pz = torch.as_tensor(Pz_np, dtype=torch.float32, device=DEVICE)
    print(f"\n=== {label}: train {len(tr)} conds / {len(np.unique(d.material_ids[tr]))} materials | "
          f"held-out {len(te)} conds / {len(np.unique(d.material_ids[te]))} materials ===")

    if get_path(res, *path_prefix, "sizes") is None:
        set_path(res, {"n_train": int(len(tr)), "n_test": int(len(te)),
                       "test_materials": sorted(map(int, np.unique(d.material_ids[te])))},
                 *path_prefix, "sizes")
        write_atomic(res, out_path)
    for p in sorted({c[1] for c in cells}):                                   # #4
        if get_path(res, *path_prefix, "pod_floor_per_sample", str(p)) is None:
            e = pod_floor_c(d.fields, tr, te, p)
            set_path(res, {"per_sample_nrmse_c": [float(x) for x in e], "mean": float(e.mean()),
                           "material_ids": d.material_ids[te].tolist(),
                           "condition_ids": d.condition_ids[te].tolist()},
                     *path_prefix, "pod_floor_per_sample", str(p))
            write_atomic(res, out_path)
            print(f"  POD floor p={p:>4}  {held_tag} c={e.mean():.5f}", flush=True)
            gc.collect()

    rng = np.random.default_rng(seed_rng)                                     # #5
    tr_eval = np.sort(rng.choice(tr, size=min(args.train_eval_cap, len(tr)), replace=False))
    widths = {}
    for fam, p, lr, steps, seed in cells:
        key = (*path_prefix, "arms", fam, str(p), f"{lr:.0e}")
        key = key + ((str(steps),) if args.arm == "steps" else ()) + (str(seed),)
        if get_path(res, *key) is not None:
            continue
        kan = fam == "deepokan"
        if (fam, p) not in widths:
            widths[(fam, p)] = solve_width(Pz.shape[1], p, args.depth, args.budget, kan, args.grids)
        w, npar = widths[(fam, p)]
        t1 = time.time()
        rec = train_eval(Ft, C, Pz, d, tr, {"train": tr_eval, held_tag: te},
                         p, w, kan, seed, lr, steps, args)
        rec.update({"width": w, "n_params": npar, "steps": steps, "wall_s": round(time.time() - t1, 1)})
        set_path(res, rec, *key)
        write_atomic(res, out_path)                                           # #12
        print(f"  {fam:<9} p={p:>4} w{w:<4} lr{lr:.0e} steps {steps} seed {seed}: "
              f"train={rec['train']['c']:.4f} {held_tag}={rec[held_tag]['c']:.4f} "
              f"[{rec['wall_s']:.0f}s]", flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT_V2)
    ap.add_argument("--field-res", type=int, default=FIELD_RES)
    ap.add_argument("--design", choices=["folds", "manifest"], default="folds")
    ap.add_argument("--arm", choices=["sweep", "steps"], default="sweep",
                    help="'steps' = the pre-declared step-sensitivity arm (audit #13)")
    ap.add_argument("--only-folds", type=int, nargs="+", default=None)
    ap.add_argument("--ps", type=int, nargs="+", default=[8, 16, 32, 64, 128])
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--lrs", type=float, nargs="+", default=[3e-3, 1e-2, 3e-2])
    ap.add_argument("--families", nargs="+", default=["deeponet", "deepokan"],
                    choices=["deeponet", "deepokan"])
    ap.add_argument("--budget", type=int, default=200_000)
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--grids", type=int, default=4)
    ap.add_argument("--steps", type=int, default=8000)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--n-pts", type=int, default=2048)
    ap.add_argument("--train-eval-cap", type=int, default=600)
    # step-sensitivity arm (#13)
    ap.add_argument("--steps-lr", type=float, default=None,
                    help="--arm steps: the lr SELECTED by the sweep for deeponet (required)")
    ap.add_argument("--steps-fold", type=int, default=0)
    ap.add_argument("--steps-grid", type=int, nargs="+", default=[8000, 24000])
    ap.add_argument("--steps-ps", type=int, nargs="+", default=[8, 128])
    ap.add_argument("--max-samples", type=int, default=None,
                    help="SMOKE ONLY: keep the first N samples of each selected fold after loading")
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    if args.threads > 0:
        torch.set_num_threads(args.threads)
    if args.arm == "steps":
        if args.steps_lr is None:
            raise SystemExit("--arm steps needs --steps-lr (the lr the sweep selected)")
        if args.design != "folds":
            raise SystemExit("--arm steps is declared on one fold of the folds design")
        args.ps, args.lrs, args.only_folds = args.steps_ps, [args.steps_lr], [args.steps_fold]
        if args.families == ["deeponet", "deepokan"]:
            args.families = ["deeponet"]                  # the flat-in-p claim is DeepONet's
    out_path = args.out or ("results/l5_v2_steps.json" if args.arm == "steps"
                            else "results/l5_v2_results.json" if args.design == "folds"
                            else "results/l5_v2_manifest.json")

    t0 = time.time()
    d = ladder_data.load(args.root, field_res=args.field_res)                 # #1
    fold_of, n_folds, fold_seed = load_folds(d.material_ids)                  # #2
    C = torch.as_tensor(coords_for(d.fields), device=DEVICE)
    Ft = field_view(d.fields)                                                 # #11 (no copy)
    print(f"frozen encoding {NZ_S}x{NT_S}; fields {d.fields.shape} "
          f"({d.fields.nbytes / 1e9:.2f} GB, shared with the torch view)")

    steps_list = args.steps_grid if args.arm == "steps" else [args.steps]
    header = {"root": args.root, "design_of_data": d.meta.get("design", "legacy"),
              "design": args.design, "arm": args.arm,
              "field_res": args.field_res, "nz_s": NZ_S, "nt_s": NT_S,
              "budget": args.budget, "depth": args.depth, "grids": args.grids,
              "steps": steps_list, "batch": args.batch, "n_pts": args.n_pts,
              "seeds": args.seeds, "ps": args.ps, "lrs": args.lrs, "families": args.families,
              "train_eval_cap": args.train_eval_cap, "fold_file": FOLDS_FILE,
              "fold_seed": fold_seed, "n_folds": n_folds, "param_keys": list(d.param_keys),
              "smoke_max_samples": args.max_samples}
    res, resumed = load_or_init(out_path, header,
                                ("root", "design", "arm", "field_res", "budget", "depth", "steps",
                                 "batch", "n_pts", "seeds", "fold_seed", "n_folds", "smoke_max_samples"))
    if resumed:
        print(f"  resuming {out_path}")

    cells = [(fam, p, lr, st, s) for fam in ("deeponet", "deepokan") if fam in args.families
             for p in args.ps for lr in args.lrs for st in steps_list for s in args.seeds]
    cap = (lambda ix: ix[:args.max_samples]) if args.max_samples else (lambda ix: ix)

    if args.design == "manifest":
        tr, te = cap(d.idx("train")), cap(d.idx("novel_material"))
        run_unit(res, ("manifest",), d, Ft, C, tr, te, "novel_material", cells, args,
                 out_path, "MANIFEST SPLIT", 0)
    else:
        folds = args.only_folds if args.only_folds is not None else list(range(n_folds))
        for f in folds:
            te = cap(np.where(fold_of == f)[0])
            tr = cap(np.where(fold_of != f)[0])
            run_unit(res, ("folds", str(f)), d, Ft, C, tr, te, "test", cells, args,
                     out_path, f"FOLD {f}", f)
    write_atomic(res, out_path)
    print(f"\nwrote {out_path}  [{time.time() - t0:.0f}s]")
    return out_path


if __name__ == "__main__":
    main()
