"""PREREG_DD_ADDITIONS: B1 (screening, out of fold) and B2 (named frameworks).

Every setting below is fixed by PREREG_DD_ADDITIONS.md (frozen 071ca9a, amendment 1
98ca243), committed before any of these runs. Phases, each resumable:

    python dd_screening_frameworks.py coarse     # N_z = 50 solve of every stored sample
    python dd_screening_frameworks.py b1         # out-of-fold HGB-p16 and DeepONet-p16
    python dd_screening_frameworks.py b2solve    # production + coarse solves, 6 frameworks
    python dd_screening_frameworks.py b2fit      # arms refit on all 240, predict frameworks
    python dd_screening_frameworks.py analyse    # metrics, intervals, verdicts

Outputs: results/dd_coarse_all.json, results/dd_b1_predictions.json,
results/dd_b2_frameworks.json, results/dd_additions_verdict.json.
Low CPU priority throughout; memory: phases b1/b2fit hold the 128x128 v2 fields (~0.8 GB).
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np

import gen_parametric_dataset as gen
from coarse_solver_baseline import solve_fields, sub
from metrics import per_variable_nrmse
from v2_common import FIELD_RES, ROOT_V2, assert_disjoint, load_folds, standardise_params, write_atomic

P = 16                      # basis size for both learned arms
LR, STEPS, SEED = 3e-3, 24000, 42
BUDGET, DEPTH, GRIDS, BATCH, NPTS = 200_000, 3, 4, 32, 2048
NZ_COARSE = 50
ALPHA, N_BOOT, BOOT_SEED = 0.02, 4000, 20261025
_TAG = os.environ.get("DD_TAG", "")          # "_v3" under PREREG_DD_V3; empty for the frozen runs
OUT_COARSE = f"results/dd_coarse_all{_TAG}.json"
OUT_B1 = f"results/dd_b1_predictions{_TAG}.json"
OUT_B2 = f"results/dd_b2_frameworks{_TAG}.json"
OUT_VERDICT = f"results/dd_additions_verdict{_TAG}.json"
STORE_NT = 256
T_GRID = np.linspace(0, STORE_NT - 1, FIELD_RES).astype(int) / (STORE_NT - 1)   # normalised times


def low_priority():
    """Lower this process's CPU priority only if DD_LOW_PRIORITY=1.

    Off by default: on a saturated machine a below-normal process barely runs (the first
    map-term run got 4 CPU-minutes in two hours), and the author made Paper 1 the priority.
    """
    if os.environ.get("DD_LOW_PRIORITY") != "1":
        return
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 10)
    except Exception:
        pass


def load_json(p, default=None):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def t_cross_norm(outlet, level):
    """First crossing of c/c_in = level on the outlet curve, linear interpolation, in t/t_final."""
    o = np.asarray(outlet, float)
    above = np.where(o >= level)[0]
    if len(above) == 0:
        return float("nan")
    i = int(above[0])
    if i == 0:
        return float(T_GRID[0])
    t0, t1, y0, y1 = T_GRID[i - 1], T_GRID[i], o[i - 1], o[i]
    return float(t0 + (level - y0) * (t1 - t0) / max(y1 - y0, 1e-12))


def t50_norm(outlet):
    """First crossing of c/c_in = 0.5 on the outlet curve, linear interpolation, in t/t_final."""
    return t_cross_norm(outlet, 0.5)


def t90_norm(outlet):
    """First crossing of c/c_in = 0.9: set by the main (pore-filling) front, not the pre-step
    wave (PREREG_DD_V3 amendment A1, the capacity-front screening metric)."""
    return t_cross_norm(outlet, 0.9)


# ─────────────────────────────── coarse solves ───────────────────────────────
def _coarse_one(args):
    """One coarse solve; a top-level function so a process pool can run it.

    Wall time is measured inside the worker, so it is the solve's own cost; with several
    workers the machine is shared, which can only make the coarse route look slower.
    """
    s, mat, cond, store_nz, store_nt = args
    low_priority()
    key = f"m{s['mat']:04d}_c{s['cond']:04d}"
    p = gen.build_physics(mat, cond)
    c_in = gen.rh_to_conc(cond["rh_feed"], cond["T_in"])
    truth = sub(np.load(os.path.join(ROOT_V2, f"{key}.npy")), FIELD_RES)
    t1 = time.perf_counter()
    try:
        f, exit_ratio = solve_fields(p, c_in, s["t_final"], NZ_COARSE, store_nz, store_nt)
        f = sub(f, FIELD_RES)
        ok = exit_ratio >= 0.90 and bool(np.all(np.isfinite(f)))
        cell = {"mat": s["mat"], "cond": s["cond"], "wall_s": time.perf_counter() - t1, "accepted": ok,
                "nrmse_c": float(per_variable_nrmse(f, truth)["c"]),
                "t50_norm": t50_norm(f[0, -1]), "t50_true_norm": t50_norm(truth[0, -1]),
                "t90_norm": t90_norm(f[0, -1]), "t90_true_norm": t90_norm(truth[0, -1]),
                "t_final": s["t_final"]}
    except Exception as e:
        cell = {"mat": s["mat"], "cond": s["cond"], "wall_s": time.perf_counter() - t1, "accepted": False,
                "failed": f"{type(e).__name__}: {e}", "t50_true_norm": t50_norm(truth[0, -1]),
                "t90_true_norm": t90_norm(truth[0, -1]),
                "t_final": s["t_final"]}
    return key, cell


def phase_coarse(workers=5):
    from multiprocessing import Pool
    man = json.load(open(os.path.join(ROOT_V2, "manifest.json")))
    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    res = load_json(OUT_COARSE, {"_what": "N_z=50 coarse solve of every stored v2 sample (B1)", "cells": {}})
    res["t_prod_s"] = load_json("results/coarse_solver_baseline.json")["summary"]["t_prod_s"]
    res["_timing_note"] = ("wall_s is measured inside each worker; up to %d workers shared the machine, "
                           "so it is an upper bound on the solve's own cost" % workers)
    samples = [s for s in man["samples"] if s.get("ok", True)
               and os.path.exists(os.path.join(ROOT_V2, f"m{s['mat']:04d}_c{s['cond']:04d}.npy"))]
    todo = [(s, mats[s["mat"]], conds[s["cond"]], man["store_nz"], man["store_nt"]) for s in samples
            if f"m{s['mat']:04d}_c{s['cond']:04d}" not in res["cells"]]
    print(f"  coarse: {len(samples) - len(todo)} done, {len(todo)} to go, {workers} workers", flush=True)
    with Pool(workers) as pool:
        for k, (key, cell) in enumerate(pool.imap_unordered(_coarse_one, todo, chunksize=4)):
            res["cells"][key] = cell
            if k % 50 == 0 or k == len(todo) - 1:
                write_atomic(res, OUT_COARSE)
                print(f"  coarse {len(res['cells'])}/{len(samples)}", flush=True)
    write_atomic(res, OUT_COARSE)


# ─────────────────────────────── learned arms ────────────────────────────────
def fit_hgb(X, Pz, fit_idx, seed=SEED):
    from sklearn.decomposition import PCA
    from sklearn.ensemble import HistGradientBoostingRegressor
    pca = PCA(n_components=P, svd_solver="randomized", random_state=0).fit(X[fit_idx])
    A = pca.transform(X[fit_idx])
    amu, asd = A.mean(0), A.std(0)
    asd[asd == 0] = 1.0
    Az = (A - amu) / asd
    models = []
    for k in range(P):
        m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06, early_stopping=True, random_state=seed)
        m.fit(Pz[fit_idx], Az[:, k])
        models.append(m)

    def predict(Pz_new):
        Azp = np.stack([m.predict(Pz_new) for m in models], 1)
        return pca.inverse_transform(Azp * asd + amu)          # (n, 128*128) c field
    return predict


def fit_deeponet(Ft, C, Pz_np, fit_idx, seed=SEED):
    import torch
    import torch.nn as nn
    from run_l5 import DEVICE, DeepONet, solve_width
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    Pz = torch.as_tensor(Pz_np, dtype=torch.float32, device=DEVICE)
    w, _ = solve_width(Pz.shape[1], P, DEPTH, BUDGET, False, GRIDS)
    model = DeepONet(Pz.shape[1], p=P, width=w, depth=DEPTH, kan=False, grids=GRIDS).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=STEPS, eta_min=LR * 1e-2)
    for step in range(STEPS):
        opt.zero_grad(set_to_none=True)
        bi = torch.as_tensor(fit_idx[rng.integers(0, len(fit_idx), BATCH)], device=DEVICE)
        pi = torch.as_tensor(rng.integers(0, C.shape[0], NPTS), device=DEVICE)
        loss = nn.functional.mse_loss(model(Pz[bi], C[pi]), Ft[bi[:, None], pi[None, :]])
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss at step {step}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sch.step()
    model.eval()

    def predict(Pz_new_np):
        out = []
        Pn = torch.as_tensor(Pz_new_np, dtype=torch.float32, device=DEVICE)
        with torch.no_grad():
            for s0 in range(0, len(Pn), 16):
                out.append(model(Pn[s0:s0 + 16], C)[..., 0].cpu().numpy())
        return np.concatenate(out)                                # (n, 128*128) c field
    predict.model = model          # read by dd_seed_robustness.trunk_floor; no effect here
    return predict


def load_v2():
    import ladder_data
    from run_l5_v2 import coords_for, field_view
    import torch
    d = ladder_data.load(ROOT_V2, field_res=FIELD_RES)
    C = torch.as_tensor(coords_for(d.fields))
    Ft = field_view(d.fields)
    return d, C, Ft


def score(pred_c, truth_c):
    """per-sample nRMSE (rule 5) and t50 for flattened 128x128 c fields."""
    rng = truth_c.max(1) - truth_c.min(1)
    nr = np.sqrt(((pred_c - truth_c) ** 2).mean(1)) / np.maximum(rng, 1e-12)
    pf = pred_c.reshape(-1, FIELD_RES, FIELD_RES)
    return nr, [t50_norm(f[-1]) for f in pf]


def phase_b1():
    d, C, Ft = load_v2()
    fold_of, n_folds, _ = load_folds(d.material_ids)
    X = d.fields[:, 0].reshape(len(d.fields), -1)
    res = load_json(OUT_B1, {"_what": "B1 out-of-fold predictions (PREREG_DD_ADDITIONS)", "folds": {}})
    for f in range(n_folds):
        tr, te = np.where(fold_of != f)[0], np.where(fold_of == f)[0]
        assert_disjoint(tr, te, f"B1 fold {f}")
        Pz = standardise_params(d.params, tr)
        rec = res["folds"].setdefault(str(f), {"material_ids": d.material_ids[te].tolist(),
                                              "condition_ids": d.condition_ids[te].tolist(),
                                              "t_final": d.t_final[te].tolist(),
                                              "t50_true_norm": [t50_norm(x[0, -1]) for x in d.fields[te]]})
        for arm, fitter in (("hgb_p16", lambda: fit_hgb(X, Pz, tr)),
                            ("deeponet_p16", lambda: fit_deeponet(Ft, C, Pz, tr))):
            if arm in rec:
                continue
            t1 = time.time()
            pred = fitter()(Pz[te])
            nr, t50 = score(pred, X[te])
            rec[arm] = {"nrmse_c": nr.tolist(), "t50_norm": t50, "secs": time.time() - t1}
            write_atomic(res, OUT_B1)
            print(f"  B1 fold {f} {arm}: nRMSE {nr.mean():.4f} [{time.time() - t1:.0f}s]", flush=True)


# ─────────────────────────────── named frameworks ────────────────────────────
def framework_params():
    """The rule of PREREG_DD_ADDITIONS B2, applied to research/water_mof_parameters.json."""
    src = json.load(open("research/water_mof_parameters.json", encoding="utf-8"))["materials"]
    man = json.load(open(os.path.join(ROOT_V2, "manifest.json")))
    med = {k: float(np.median([m[k] for m in man["materials"]]))
           for k in ("isotherm_n", "henry_fraction", "d_p", "rho_p", "eps_t")}
    # stated rise intervals (p10, p90), read from the quotes in the JSON (see each entry)
    rise = {"MOF-303": (0.08, 0.18), "MOF-801": (0.05, 0.10), "CAU-10-H": (0.19, 0.22),
            "Al-fumarate (Basolite A520)": (0.23, 0.30)}
    out = {}
    for name, v in src.items():
        q = [e["converted"] for e in v["q_sat"] if "20% RH" not in e["unit"]]
        step = float(np.mean([e["converted"] for e in v["RH_step"]]))
        dh = []
        for e in v["heat_of_adsorption"]:
            val = e.get("converted", e.get("value"))
            nums = [abs(float(x)) for x in str(val).replace("to", " ").split() if x.replace(".", "").replace("-", "").isdigit()]
            dh.append(float(np.mean(nums)) if nums else abs(float(val)))
        n = math.log(81) / math.log(rise[name][1] / rise[name][0]) if name in rise else med["isotherm_n"]
        out[name] = {"q_max": float(np.mean(q)), "delta_H": -1000.0 * float(np.mean(dh)), "step_rh": step,
                     "isotherm_n": n, "henry_fraction": med["henry_fraction"], "d_p": med["d_p"],
                     "rho_p": med["rho_p"], "eps_t": med["eps_t"]}
    ranges = {k: (min(m[k] for m in man["materials"]), max(m[k] for m in man["materials"]))
              for k in ("q_max", "delta_H", "step_rh", "isotherm_n")}
    for name, m in out.items():
        m["outside"] = [k for k, (lo, hi) in ranges.items() if not lo <= m[k] <= hi]
    return out, man


def phase_b2solve():
    fw, man = framework_params()
    res = load_json(OUT_B2, {"_what": "B2 named frameworks (PREREG_DD_ADDITIONS)", "frameworks": fw, "cells": {}})
    res["frameworks"] = fw
    for name, mat in fw.items():
        for cond in man["conditions"]:
            key = f"{name}|c{cond['condition_id']:04d}"
            if key in res["cells"]:
                continue
            m = dict(mat, material_id=-1)
            t1 = time.perf_counter()
            r = gen.run_one((m, cond))
            cell = {"framework": name, "cond": cond["condition_id"], "ok": bool(r["ok"]),
                    "prod_wall_s": time.perf_counter() - t1}
            if r["ok"]:
                truth = sub(r["fields"], FIELD_RES)
                np.save(os.path.join("results", f"dd_b2_fields{_TAG}", f"{name.split()[0]}_c{cond['condition_id']:04d}.npy"),
                        truth.astype(np.float32)) if os.path.isdir(os.path.join("results", f"dd_b2_fields{_TAG}")) else None
                p = gen.build_physics(m, cond)
                t2 = time.perf_counter()
                try:
                    fc, ex = solve_fields(p, r["c_in"], r["t_final"], NZ_COARSE, man["store_nz"], man["store_nt"])
                    fc = sub(fc, FIELD_RES)
                    cell.update({"coarse_ok": ex >= 0.90, "coarse_nrmse_c": float(per_variable_nrmse(fc, truth)["c"]),
                                 "coarse_t50_norm": t50_norm(fc[0, -1]), "coarse_wall_s": time.perf_counter() - t2})
                except Exception as e:
                    cell.update({"coarse_ok": False, "coarse_failed": f"{type(e).__name__}: {e}"})
                cell.update({"t_final": r["t_final"], "t50_true_norm": t50_norm(truth[0, -1]),
                             "truth_c": truth[0].ravel().round(6).tolist()})
            else:
                cell["reason"] = r["reason"]
            res["cells"][key] = cell
            write_atomic(res, OUT_B2)
            print(f"  B2 solve {key}: " + ("ok" if cell["ok"] else cell["reason"]), flush=True)


def phase_b2fit():
    d, C, Ft = load_v2()
    res = load_json(OUT_B2)
    man = d.manifest if hasattr(d, "manifest") else json.load(open(os.path.join(ROOT_V2, "manifest.json")))
    keys = list(d.keys) if hasattr(d, "keys") else None
    import ladder_data
    keys = list(ladder_data.param_keys_for(json.load(open(os.path.join(ROOT_V2, "manifest.json")))))
    conds = {c["condition_id"]: c for c in json.load(open(os.path.join(ROOT_V2, "manifest.json")))["conditions"]}
    cells = [(k, c) for k, c in res["cells"].items() if c["ok"]]
    raw = np.array([[(res["frameworks"][c["framework"]] if kk in res["frameworks"][c["framework"]] else conds[c["cond"]])[kk]
                     for kk in keys] for _, c in cells], dtype=np.float64)
    all_idx = np.arange(len(d.params))
    mu, sd = d.params[all_idx].mean(0), d.params[all_idx].std(0)
    sd[sd == 0] = 1.0
    Pz_all = (d.params - mu) / sd
    Pz_new = (raw - mu) / sd
    X = d.fields[:, 0].reshape(len(d.fields), -1)
    truth = np.array([c["truth_c"] for _, c in cells], dtype=np.float64)
    for arm, fitter in (("hgb_p16", lambda: fit_hgb(X, Pz_all, all_idx)),
                        ("deeponet_p16", lambda: fit_deeponet(Ft, C, Pz_all, all_idx))):
        if res.get("fit", {}).get(arm):
            continue
        pred = fitter()(Pz_new)
        nr, t50 = score(pred, truth)
        for (key, c), a, b in zip(cells, nr, t50):
            c[f"{arm}_nrmse_c"], c[f"{arm}_t50_norm"] = float(a), b
        res.setdefault("fit", {})[arm] = True
        write_atomic(res, OUT_B2)
        print(f"  B2 {arm} fitted on all 240; framework nRMSE mean {nr.mean():.4f}", flush=True)


# ─────────────────────────────── analysis ────────────────────────────────────
def spearman(a, b):
    from scipy.stats import spearmanr
    ok = np.isfinite(a) & np.isfinite(b)
    return float(spearmanr(a[ok], b[ok]).correlation) if ok.sum() > 2 else float("nan")


def topk_recall(true, pred, frac=0.10):
    ok = np.isfinite(true) & np.isfinite(pred)
    t, p = true[ok], pred[ok]
    k = max(1, int(round(frac * len(t))))
    return len(set(np.argsort(-t)[:k]) & set(np.argsort(-p)[:k])) / k


def phase_analyse():
    b1 = load_json(OUT_B1)
    co = load_json(OUT_COARSE)
    # cost per coarse solve: the clean single-process timing of B-COARSE, not this run's
    # wall times, which were measured with several workers sharing the machine
    se_base = load_json("results/coarse_solver_baseline.json")["summary"]["per_nz"][str(NZ_COARSE)]["solve_equivalents"]
    rows = []
    for f, r in b1["folds"].items():
        for i, (m, c) in enumerate(zip(r["material_ids"], r["condition_ids"])):
            cc = co["cells"].get(f"m{m:04d}_c{c:04d}", {})
            tf = r["t_final"][i]
            rows.append({"mat": m, "cond": c, "t_true": r["t50_true_norm"][i] * tf,
                         "hgb": r["hgb_p16"]["t50_norm"][i] * tf, "don": r["deeponet_p16"]["t50_norm"][i] * tf,
                         # a failed coarse solve is re-solved at production resolution: its t50 is the truth
                         "coarse": (cc["t50_norm"] * tf) if cc.get("accepted") else r["t50_true_norm"][i] * tf,
                         "nr_hgb": r["hgb_p16"]["nrmse_c"][i], "nr_don": r["deeponet_p16"]["nrmse_c"][i],
                         "nr_coarse": cc["nrmse_c"] if cc.get("accepted") else 0.0,
                         "coarse_cost": se_base if cc.get("accepted") else 1.0})
    mats = np.array([r["mat"] for r in rows]); conds = np.array([r["cond"] for r in rows])
    arr = {k: np.array([r[k] for r in rows], float) for k in rows[0] if k not in ("mat", "cond")}

    def metrics(idx):
        out = {}
        for arm in ("hgb", "don", "coarse"):
            sp, rc = [], []
            for c in np.unique(conds[idx]):
                j = idx[conds[idx] == c]
                sp.append(spearman(arr["t_true"][j], arr[arm][j])); rc.append(topk_recall(arr["t_true"][j], arr[arm][j]))
            out[arm] = (np.nanmean(sp), np.nanmean(rc))
        return out

    full = np.arange(len(rows))
    point = metrics(full)
    rng = np.random.default_rng(BOOT_SEED)
    by_mat = {m: np.where(mats == m)[0] for m in np.unique(mats)}
    um = np.array(list(by_mat))
    boots = []
    for _ in range(N_BOOT):
        idx = np.concatenate([by_mat[m] for m in rng.choice(um, size=len(um), replace=True)])
        boots.append(metrics(idx))
    q = lambda xs: [float(np.percentile(xs, 100 * ALPHA / 2)), float(np.percentile(xs, 100 * (1 - ALPHA / 2)))]
    out = {"_what": "PREREG_DD_ADDITIONS verdicts", "alpha": ALPHA, "n_boot": N_BOOT, "n_samples": len(rows),
           "n_materials": int(len(um)), "b1": {}}
    for arm in ("hgb", "don", "coarse"):
        sp_ci = q([b[arm][0] for b in boots]); rc_ci = q([b[arm][1] for b in boots])
        rec = {"spearman_mean": point[arm][0], "spearman_ci": sp_ci, "top10_recall_mean": point[arm][1],
               "top10_recall_ci": rc_ci, "screening_adequate": bool(sp_ci[0] >= 0.90 and rc_ci[0] >= 0.80)}
        if arm != "coarse":
            dsp = q([b["coarse"][0] - b[arm][0] for b in boots]); drc = q([b["coarse"][1] - b[arm][1] for b in boots])
            rec.update({"coarse_minus_arm_spearman_ci": dsp, "coarse_minus_arm_recall_ci": drc,
                        "ranks_worse_than_coarse": bool(dsp[0] > 0 or drc[0] > 0)})
        out["b1"][arm] = rec
    # paired field nRMSE, coarse vs each arm, over every sample (cluster bootstrap by material)
    from metrics import _cluster_bootstrap
    for arm, k in (("hgb", "nr_hgb"), ("don", "nr_don")):
        diff = arr[k] - arr["nr_coarse"]
        bs = _cluster_bootstrap(diff, mats, N_BOOT, np.random.default_rng(BOOT_SEED + 1))
        out["b1"][arm]["field_nrmse_mean"] = float(arr[k].mean())
        out["b1"][arm]["arm_minus_coarse_nrmse_ci"] = q(bs)
    out["b1"]["coarse"]["field_nrmse_mean"] = float(arr["nr_coarse"].mean())
    out["b1"]["coarse"]["mean_cost_solve_equivalents"] = float(arr["coarse_cost"].mean())
    # B2
    b2 = load_json(OUT_B2)
    if b2 and b2.get("fit"):
        p95 = {arm: float(np.percentile([np.mean(arr[k][mats == m]) for m in um], 95))
               for arm, k in (("hgb_p16", "nr_hgb"), ("deeponet_p16", "nr_don"))}
        out["b2"] = {"p95_heldout_material_nrmse": p95, "frameworks": {}}
        for name, fwp in b2["frameworks"].items():
            cs = [c for c in b2["cells"].values() if c["framework"] == name and c["ok"]]
            rec = {"outside_box": fwp["outside"], "n_conditions_ok": len(cs)}
            for arm in ("hgb_p16", "deeponet_p16"):
                if cs and f"{arm}_nrmse_c" in cs[0]:
                    mn = float(np.mean([c[f"{arm}_nrmse_c"] for c in cs]))
                    rec[arm] = {"nrmse_c": mn, "abs_t50_err_s": float(np.nanmean([abs(c[f"{arm}_t50_norm"] - c["t50_true_norm"]) * c["t_final"] for c in cs])),
                                "inside_heldout_distribution": bool(mn <= p95[arm])}
            co_ok = [c for c in cs if c.get("coarse_ok")]
            if co_ok:
                rec["coarse"] = {"nrmse_c": float(np.mean([c["coarse_nrmse_c"] for c in co_ok])), "n_failed": len(cs) - len(co_ok)}
            out["b2"]["frameworks"][name] = rec
        from scipy.stats import kendalltau
        taus = {}
        for arm in ("hgb_p16", "deeponet_p16"):
            tt = []
            for cond in sorted({c["cond"] for c in b2["cells"].values()}):
                cs = [c for c in b2["cells"].values() if c["cond"] == cond and c["ok"] and f"{arm}_t50_norm" in c]
                if len(cs) >= 3:
                    tt.append(kendalltau([c["t50_true_norm"] * c["t_final"] for c in cs],
                                         [c[f"{arm}_t50_norm"] * c["t_final"] for c in cs]).correlation)
            taus[arm] = float(np.nanmean(tt)) if tt else None
        out["b2"]["kendall_tau_framework_order"] = taus
    write_atomic(out, OUT_VERDICT)
    print(json.dumps(out, indent=1)[:3000])


if __name__ == "__main__":
    low_priority()
    os.makedirs(os.path.join("results", "dd_b2_fields"), exist_ok=True)
    {"coarse": phase_coarse, "b1": phase_b1, "b2solve": phase_b2solve,
     "b2fit": phase_b2fit, "analyse": phase_analyse}[sys.argv[1]]()
