"""Seed robustness of PREREG_DD_ADDITIONS B1 and B2 (NOT pre-registered; a check).

The pre-registration fixed one training seed (42) for both learned arms. The project's
standing rule 3 (RETRACTIONS.md) forbids single-seed numbers in a table, so the same
arms, with every setting unchanged, are re-run at seeds 43 and 44 and the spread is
reported beside the frozen seed-42 verdicts. Nothing here can change a verdict: the
verdicts stay those of the frozen analysis; this file reports how far they move.

    python dd_seed_robustness.py b2    # refit on all 240, predict the six frameworks
    python dd_seed_robustness.py b1    # out-of-fold, five folds
    python dd_seed_robustness.py summary

Output: results/dd_seed_robustness.json (resumable per seed, arm and fold).
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

import dd_screening_frameworks as dd
from v2_common import assert_disjoint, load_folds, standardise_params, write_atomic

SEEDS = (43, 44)
OUT = "results/dd_seed_robustness.json"


def _res():
    return dd.load_json(OUT, {"_what": "seed robustness of PREREG_DD_ADDITIONS (not pre-registered)",
                              "seeds": list(SEEDS), "b2": {}, "b1": {}})


def phase_b2():
    import ladder_data
    d, C, Ft = dd.load_v2()
    b2 = dd.load_json(dd.OUT_B2)
    man = json.load(open(os.path.join(dd.ROOT_V2, "manifest.json")))
    keys = list(ladder_data.param_keys_for(man))
    conds = {c["condition_id"]: c for c in man["conditions"]}
    cells = [(k, c) for k, c in b2["cells"].items() if c["ok"]]
    raw = np.array([[(b2["frameworks"][c["framework"]] if kk in b2["frameworks"][c["framework"]]
                      else conds[c["cond"]])[kk] for kk in keys] for _, c in cells], dtype=np.float64)
    all_idx = np.arange(len(d.params))
    mu, sd = d.params.mean(0), d.params.std(0)
    sd[sd == 0] = 1.0
    Pz_all, Pz_new = (d.params - mu) / sd, (raw - mu) / sd
    X = d.fields[:, 0].reshape(len(d.fields), -1)
    truth = np.array([c["truth_c"] for _, c in cells], dtype=np.float64)
    res = _res()
    for seed in SEEDS:
        for arm, fitter in (("hgb_p16", lambda s=seed: dd.fit_hgb(X, Pz_all, all_idx, seed=s)),
                            ("deeponet_p16", lambda s=seed: dd.fit_deeponet(Ft, C, Pz_all, all_idx, seed=s))):
            key = f"{arm}|{seed}"
            if key in res["b2"]:
                continue
            t1 = time.time()
            nr, t50 = dd.score(fitter()(Pz_new), truth)
            per_fw = {}
            for (k, c), a, b in zip(cells, nr, t50):
                per_fw.setdefault(c["framework"], {"nrmse": [], "t50": [], "true": [], "tf": [], "cond": []})
                r = per_fw[c["framework"]]
                r["nrmse"].append(float(a)); r["t50"].append(b); r["true"].append(c["t50_true_norm"])
                r["tf"].append(c["t_final"]); r["cond"].append(c["cond"])
            res["b2"][key] = per_fw
            write_atomic(res, OUT)
            print(f"  B2 {key}: framework nRMSE mean {nr.mean():.4f} [{time.time() - t1:.0f}s]", flush=True)


def trunk_floor(model, C, U, Pz=None, iters=200, tol=1e-9):
    """DeepONet's own basis floor on the c channel: the error left when its trained trunk
    is kept and the coefficients are chosen per sample to fit the TRUE field,
        min_a || u - sigmoid(T a + b0) ||,
    the analogue of the POD projection floor for a basis seen through a sigmoid head.

    Each sample is its own least-squares problem, solved by batched Levenberg-Marquardt with a
    per-sample damping factor (PREREG_DD_V3 amendment A1). Two starts are run and the better
    kept: the model's OWN predicted coefficients branch(Pz) (so the floor can never exceed the
    model's error: only improving steps are accepted), and least squares on logit(u). The first
    version (L-BFGS, one shared line search for a batch of separable problems, 60 iterations)
    did not converge and returned "floors" above the model's own error for up to a fifth of the
    samples (ledger B89).

    Returns (floor_nrmse, converged, own_nrmse): per-sample nRMSE normalised as `score` does,
    whether the relative gradient norm fell below sqrt(tol) or the step stalled, and the error
    of the model's own coefficients through the same reconstruction (a check: equals the
    surrogate's error).
    """
    import torch
    with torch.no_grad():
        T = model.trunk(C).view(C.shape[0], 3, model.p)[:, 0, :].double()   # (N, p)
        b0 = float(model.bias[0])
        A_own = None
        if Pz is not None:
            Pt = torch.as_tensor(Pz, dtype=torch.float32)
            A_own = torch.cat([model.branch(Pt[i:i + 256]).view(-1, 3, model.p)[:, 0, :].double()
                               for i in range(0, len(Pt), 256)])
    N, p = T.shape
    batch = max(1, int(2.0e7 // (N * p)))
    floors, conv, owns = [], [], []

    def sse(A, u):
        return ((torch.sigmoid(A @ T.T + b0) - u) ** 2).sum(1)

    def lm(A, u):
        lam = torch.full((A.shape[0],), 1e-3, dtype=torch.float64)
        f = sse(A, u)
        done = torch.zeros(A.shape[0], dtype=torch.bool)
        eye = torch.eye(p, dtype=torch.float64)
        for _ in range(iters):
            s = torch.sigmoid(A @ T.T + b0)
            w = s * (1 - s)                                            # (B, N)
            r = s - u
            g = (w * r) @ T                                           # (B, p)  J^T r
            H = torch.einsum("bn,np,nq->bpq", w * w, T, T)            # (B, p, p) J^T J
            gn = g.norm(dim=1) / (f.sqrt() * T.norm() + 1e-30)
            done |= gn < tol ** 0.5
            if bool(done.all()):
                break
            D = torch.diagonal(H, dim1=1, dim2=2).clamp_min(1e-12)
            step = torch.linalg.solve(H + lam[:, None, None] * torch.diag_embed(D) + 1e-12 * eye, -g)
            A_new = A + step
            f_new = sse(A_new, u)
            better = (f_new < f) & ~done
            A = torch.where(better[:, None], A_new, A)
            rel = (f - f_new) / f.clamp_min(1e-300)
            done |= better & (rel < tol)                               # converged by stalled decrease
            f = torch.where(better, f_new, f)
            lam = torch.where(better, lam * 0.3, lam * 10.0).clamp(1e-12, 1e12)
            done |= lam >= 1e12                                        # no descent direction left
        return A, f, done

    for s0 in range(0, len(U), batch):
        u = torch.as_tensor(U[s0:s0 + batch], dtype=torch.float64)
        z = torch.logit(u.clamp(1e-4, 1 - 1e-4)) - b0
        starts = [torch.linalg.lstsq(T, z.T).solution.T.clone()]
        if A_own is not None:
            starts.insert(0, A_own[s0:s0 + batch].clone())
        best_f, best_c = None, None
        for A0 in starts:
            _, f, c = lm(A0, u)
            if best_f is None:
                best_f, best_c = f, c
            else:
                take = f < best_f
                best_f, best_c = torch.where(take, f, best_f), torch.where(take, c, best_c)
        rng = (u.max(1).values - u.min(1).values).clamp_min(1e-12)
        floors.append(((best_f / N).sqrt() / rng).numpy())
        conv.append(best_c.numpy())
        if A_own is not None:
            owns.append(((sse(A_own[s0:s0 + batch], u) / N).sqrt() / rng).numpy())
    own = np.concatenate(owns) if owns else None
    return np.concatenate(floors), np.concatenate(conv), own


def phase_b1():
    d, C, Ft = dd.load_v2()
    fold_of, n_folds, _ = load_folds(d.material_ids)
    X = d.fields[:, 0].reshape(len(d.fields), -1)
    res = _res()
    for seed in SEEDS:
        for f in range(n_folds):
            key = f"deeponet_p16|{seed}|{f}"
            if key in res["b1"]:
                continue
            tr, te = np.where(fold_of != f)[0], np.where(fold_of == f)[0]
            assert_disjoint(tr, te, f"seed {seed} fold {f}")
            Pz = standardise_params(d.params, tr)
            t1 = time.time()
            pred = dd.fit_deeponet(Ft, C, Pz, tr, seed=seed)
            nr, t50 = dd.score(pred(Pz[te]), X[te])
            floor = trunk_floor(pred.model, C, X[te])
            res["b1"][key] = {"material_ids": d.material_ids[te].tolist(), "condition_ids": d.condition_ids[te].tolist(),
                              "nrmse_c": nr.tolist(), "t50_norm": t50, "trunk_floor_c": floor.tolist()}
            write_atomic(res, OUT)
            print(f"  B1 {key}: nRMSE {nr.mean():.4f}, own trunk floor {floor.mean():.5f} "
                  f"[{time.time() - t1:.0f}s]", flush=True)


def phase_summary():
    """Point estimates per seed, in the frozen analysis's definitions; seed 42 from its files."""
    res, b1, b2v = _res(), dd.load_json(dd.OUT_B1), dd.load_json(dd.OUT_VERDICT)["b2"]
    tf_of, true_of = {}, {}
    for r in b1["folds"].values():
        for m, c, tf, t in zip(r["material_ids"], r["condition_ids"], r["t_final"], r["t50_true_norm"]):
            tf_of[(m, c)], true_of[(m, c)] = tf, t

    def b1_metrics(rows):                       # rows: (mat, cond, nrmse, t50_norm)
        conds = sorted({c for _, c, _, _ in rows})
        sp, rc = [], []
        for c in conds:
            rr = [r for r in rows if r[1] == c]
            tt = np.array([true_of[(m, c)] * tf_of[(m, c)] for m, _, _, _ in rr])
            pp = np.array([t * tf_of[(m, c)] for m, _, _, t in rr], float)
            sp.append(dd.spearman(tt, pp)); rc.append(dd.topk_recall(tt, pp))
        per_mat = {}
        for m, _, nr, _ in rows:
            per_mat.setdefault(m, []).append(nr)
        return {"spearman_mean": float(np.nanmean(sp)), "top10_recall_mean": float(np.nanmean(rc)),
                "field_nrmse_mean": float(np.mean([r[2] for r in rows])),
                "p95_heldout_material_nrmse": float(np.percentile([np.mean(v) for v in per_mat.values()], 95))}

    out = {"_what": res["_what"], "b1": {}, "b2": {}}
    rows42 = [(m, c, nr, t) for r in b1["folds"].values()
              for m, c, nr, t in zip(r["material_ids"], r["condition_ids"],
                                     r["deeponet_p16"]["nrmse_c"], r["deeponet_p16"]["t50_norm"])]
    out["b1"]["42"] = b1_metrics(rows42)
    p95 = {"42": out["b1"]["42"]["p95_heldout_material_nrmse"]}
    for seed in SEEDS:
        recs = [res["b1"].get(f"deeponet_p16|{seed}|{f}") for f in range(5)]
        if all(recs):
            rows = [(m, c, nr, t) for r in recs
                    for m, c, nr, t in zip(r["material_ids"], r["condition_ids"], r["nrmse_c"], r["t50_norm"])]
            out["b1"][str(seed)] = b1_metrics(rows)
            p95[str(seed)] = out["b1"][str(seed)]["p95_heldout_material_nrmse"]
    for arm in ("deeponet_p16", "hgb_p16"):
        per = {"42": {n: r[arm]["nrmse_c"] for n, r in b2v["frameworks"].items()}}
        for seed in SEEDS:
            rec = res["b2"].get(f"{arm}|{seed}")
            if rec:
                per[str(seed)] = {n: float(np.mean(r["nrmse"])) for n, r in rec.items()}
        names = list(per["42"])
        out["b2"][arm] = {n: {"per_seed": {s: per[s][n] for s in per}, "min": min(per[s][n] for s in per),
                              "max": max(per[s][n] for s in per)} for n in names}
        if arm == "deeponet_p16":
            # does the in/out verdict change with the seed? against the frozen seed-42 threshold
            thr = b2v["p95_heldout_material_nrmse"][arm]
            out["b2"][arm + "_inside_by_seed"] = {s: {n: bool(per[s][n] <= thr) for n in names} for s in per}
    out["seeds_complete"] = {"b1": sorted(out["b1"]), "b2": sorted({k.split("|")[1] for k in res["b2"]} | {"42"})}
    write_atomic(dict(res, summary=out), OUT)
    print(json.dumps(out, indent=1)[:2500])


if __name__ == "__main__":
    {"b2": phase_b2, "b1": phase_b1, "summary": phase_summary}[sys.argv[1]]()
