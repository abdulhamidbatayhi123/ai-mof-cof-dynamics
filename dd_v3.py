"""PREREG_DD_V3: design v3 (physically realistic isotherms) and DeepONet's own basis floor.

Every setting is fixed by PREREG_DD_V3.md (frozen 24e72e6, pushed before any run). The frozen
code paths are reused, pointed at v3 through ADS_DATA_ROOT / ADS_FOLDS_FILE / DD_TAG; nothing
in them changes for v2 when those are unset.

    python dd_v3.py folds                         # results/v3_folds.json (before any fit)
    python dd_v3.py deeponet --data v3 --p 16 --seed 42   # per fold: field, t50, own trunk floor
    python dd_v3.py hgb                           # v3: POD + boosting p16 per fold (screening arm)
    python dd_v3.py frameworks                    # v3 rule, production + coarse solves, refits
    python dd_v3.py analyse                       # shares, screening, baseline, frameworks
The coarse solve of every v3 sample and the screening analysis run through
dd_screening_frameworks.py with DD_TAG=_v3 (see run_dd_v3.sh). Eq. (split) on v3 runs through
l5_mapterm_v2.py --seeds 42 --out results/l5_mapterm_v3.json with ADS_DATA_ROOT set.
"""
from __future__ import annotations

import os
import sys

V3_ROOT, V3_FOLDS = "data/parametric_v3", "results/v3_folds.json"


def _data_arg():
    a = sys.argv
    return a[a.index("--data") + 1] if "--data" in a else "v3"


if sys.argv[1:2] != ["analyse"] and _data_arg() == "v3":
    # must happen before v2_common / dd_screening_frameworks are imported
    os.environ.setdefault("ADS_DATA_ROOT", V3_ROOT)
    os.environ.setdefault("ADS_FOLDS_FILE", V3_FOLDS)
    os.environ.setdefault("DD_TAG", "_v3")

import argparse  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

OUT_DON = "results/dd_v3_deeponet.json"
OUT_HGB = "results/dd_v3_hgb.json"
OUT = "results/dd_v3_verdict.json"
ALPHA, N_BOOT, BOOT_SEED = 0.02, 4000, 20261026


def phase_folds():
    man = json.load(open(os.path.join(V3_ROOT, "manifest.json")))
    ids = sorted(m["material_id"] for m in man["materials"])
    perm = np.random.default_rng(20261026).permutation(ids)
    m2f = {int(m): int(i // (len(ids) // 5)) for i, m in enumerate(perm)}
    rec = {"_what": "PREREG_DD_V3 fold map: rng(20261026) permutation of material ids, 5 groups",
           "fold_seed": 20261026, "n_folds": 5, "material_to_fold": {str(k): v for k, v in m2f.items()}}
    if os.path.exists(V3_FOLDS) and json.load(open(V3_FOLDS))["material_to_fold"] != rec["material_to_fold"]:
        raise SystemExit(f"{V3_FOLDS} exists and differs; refusing to overwrite a fold map")
    json.dump(rec, open(V3_FOLDS, "w"), indent=1)
    print(f"wrote {V3_FOLDS}: {len(ids)} materials, sizes "
          f"{np.bincount(list(m2f.values())).tolist()}")


def phase_deeponet(data, p, seed):
    import dd_screening_frameworks as dd
    from dd_seed_robustness import trunk_floor
    from v2_common import assert_disjoint, load_folds, standardise_params, write_atomic
    dd.P = p                                       # basis size of fit_deeponet (module constant)
    d, C, Ft = dd.load_v2()                        # reads ADS_DATA_ROOT
    fold_of, n_folds, _ = load_folds(d.material_ids)
    X = d.fields[:, 0].reshape(len(d.fields), -1)
    res = dd.load_json(OUT_DON, {"_what": "PREREG_DD_V3 V2: DeepONet field error and own trunk floor",
                                 "cells": {}})
    for f in range(n_folds):
        key = f"{data}|p{p}|s{seed}|f{f}"
        if key in res["cells"]:
            continue
        tr, te = np.where(fold_of != f)[0], np.where(fold_of == f)[0]
        assert_disjoint(tr, te, key)
        Pz = standardise_params(d.params, tr)
        t1 = time.time()
        pred = dd.fit_deeponet(Ft, C, Pz, tr, seed=seed)
        nr, t50 = dd.score(pred(Pz[te]), X[te])
        floor = trunk_floor(pred.model, C, X[te])
        res["cells"][key] = {"data": data, "p": p, "seed": seed, "fold": f,
                             "material_ids": d.material_ids[te].tolist(),
                             "condition_ids": d.condition_ids[te].tolist(),
                             "t_final": d.t_final[te].tolist(),
                             "t50_true_norm": [dd.t50_norm(x[0, -1]) for x in d.fields[te]],
                             "nrmse_c": nr.tolist(), "t50_norm": t50, "trunk_floor_c": floor.tolist(),
                             "secs": time.time() - t1}
        write_atomic(res, OUT_DON)
        print(f"  {key}: nRMSE {nr.mean():.4f}, own floor {floor.mean():.5f} [{time.time() - t1:.0f}s]",
              flush=True)


def phase_hgb():
    """v3 screening arm 2 (POD + boosting, p16), then the B1 file in the frozen layout."""
    import dd_screening_frameworks as dd
    from v2_common import assert_disjoint, load_folds, standardise_params, write_atomic
    d, C, Ft = dd.load_v2()
    fold_of, n_folds, _ = load_folds(d.material_ids)
    X = d.fields[:, 0].reshape(len(d.fields), -1)
    res = dd.load_json(OUT_HGB, {"_what": "PREREG_DD_V3 V4: POD + boosting p16 on v3", "folds": {}})
    for f in range(n_folds):
        if str(f) in res["folds"]:
            continue
        tr, te = np.where(fold_of != f)[0], np.where(fold_of == f)[0]
        assert_disjoint(tr, te, f"v3 hgb fold {f}")
        Pz = standardise_params(d.params, tr)
        nr, t50 = dd.score(dd.fit_hgb(X, Pz, tr)(Pz[te]), X[te])
        res["folds"][str(f)] = {"material_ids": d.material_ids[te].tolist(), "nrmse_c": nr.tolist(),
                                "t50_norm": t50}
        write_atomic(res, OUT_HGB)
        print(f"  v3 hgb fold {f}: nRMSE {nr.mean():.4f}", flush=True)
    # assemble dd's B1 layout (OUT_B1 is tagged _v3), so dd.phase_analyse runs unchanged
    don = json.load(open(OUT_DON))["cells"]
    b1 = {"_what": "B1 layout for v3 (PREREG_DD_V3 V4), assembled by dd_v3.py hgb", "folds": {}}
    for f in range(n_folds):
        dc = don[f"v3|p16|s42|f{f}"]
        h = res["folds"][str(f)]
        assert dc["material_ids"] == h["material_ids"]
        b1["folds"][str(f)] = {"material_ids": dc["material_ids"], "condition_ids": dc["condition_ids"],
                               "t_final": dc["t_final"], "t50_true_norm": dc["t50_true_norm"],
                               "hgb_p16": {"nrmse_c": h["nrmse_c"], "t50_norm": h["t50_norm"]},
                               "deeponet_p16": {"nrmse_c": dc["nrmse_c"], "t50_norm": dc["t50_norm"]}}
    write_atomic(b1, dd.OUT_B1)
    print(f"wrote {dd.OUT_B1}")


def framework_params_v3():
    """PREREG_DD_V3 V6: the B2 rule with f_H from the sources' estimates and the v3 medians."""
    import dd_screening_frameworks as dd
    src = json.load(open("research/water_mof_parameters.json", encoding="utf-8"))["materials"]
    man = json.load(open(os.path.join(V3_ROOT, "manifest.json")))
    keys = ("isotherm_n", "henry_fraction", "henry_affinity_log10", "d_p", "rho_p", "eps_t")
    med = {k: float(np.median([m[k] for m in man["materials"]])) for k in keys}
    base, _ = _B2_RULE()                           # q_max, delta_H, step_rh, n by the B2 rule
    rise_stated = {"MOF-303", "MOF-801", "CAU-10-H", "Al-fumarate (Basolite A520)"}
    out = {}
    for name, m in base.items():
        est = (src[name].get("uptake_below_step") or {}).get("henry_fraction_estimate")
        out[name] = {"q_max": m["q_max"], "delta_H": m["delta_H"], "step_rh": m["step_rh"],
                     "isotherm_n": m["isotherm_n"] if name in rise_stated else med["isotherm_n"],
                     "henry_fraction": float(est) if est is not None else med["henry_fraction"],
                     "henry_affinity_log10": med["henry_affinity_log10"],
                     "d_p": med["d_p"], "rho_p": med["rho_p"], "eps_t": med["eps_t"]}
    ranges = {k: tuple(man["material_space"][k]) for k in ("q_max", "delta_H", "step_rh", "isotherm_n",
                                                            "henry_fraction")}
    for name, m in out.items():
        m["outside"] = [k for k, (lo, hi) in ranges.items() if not lo <= m[k] <= hi]
    return out, man


_B2_RULE = None


def phase_frameworks():
    global _B2_RULE
    import dd_screening_frameworks as dd
    _B2_RULE = dd.framework_params                 # the frozen B2 rule, kept before patching
    dd.framework_params = framework_params_v3
    os.makedirs(os.path.join("results", f"dd_b2_fields{dd._TAG}"), exist_ok=True)
    dd.phase_b2solve()
    dd.phase_b2fit()


# ─────────────────────────────── analysis ────────────────────────────────────
def _share_ci(floor2, total2, mats):
    """share of squared error carried by the map, 1 - sum(floor^2)/sum(total^2), with a
    cluster bootstrap over materials (percentile, alpha = 0.02)."""
    floor2, total2, mats = map(np.asarray, (floor2, total2, mats))
    point = 1.0 - floor2.sum() / total2.sum()
    by = {m: np.where(mats == m)[0] for m in np.unique(mats)}
    um = np.array(list(by))
    rng = np.random.default_rng(BOOT_SEED)
    bs = []
    for _ in range(N_BOOT):
        idx = np.concatenate([by[m] for m in rng.choice(um, len(um), replace=True)])
        bs.append(1.0 - floor2[idx].sum() / total2[idx].sum())
    lo, hi = np.percentile(bs, [100 * ALPHA / 2, 100 * (1 - ALPHA / 2)])
    return {"share_map": float(point), "ci": [float(lo), float(hi)],
            "mean_floor": float(np.sqrt(floor2).mean()), "mean_total": float(np.sqrt(total2).mean())}


def _verdict(rows):
    """PREREG_DD_V3 C: rows = {p: share record}."""
    hi_ps = [p for p in rows if p >= 16]
    if hi_ps and all(rows[p]["share_map"] >= 0.5 and rows[p]["ci"][0] >= 0.5 for p in hi_ps):
        return "the map dominates"
    if 16 in rows and rows[16]["share_map"] <= 0.5 and rows[16]["ci"][1] <= 0.5:
        return "the basis binds"
    return "neither dominates"


def _mapterm_shares(path):
    res = json.load(open(path))
    out = {}
    for p in sorted({c["p"] for c in res["cells"].values()}):
        cs = [c for c in res["cells"].values() if c["p"] == p and c["seed"] == 42]
        if len(cs) < 5:
            continue
        f2 = np.concatenate([np.square(c["floor"]) for c in cs])
        t2 = np.concatenate([np.square(c["total_hgb"]) for c in cs])
        mats = np.concatenate([c["material_ids"] for c in cs])
        out[p] = _share_ci(f2, t2, mats)
    return out


def _don_shares(data):
    cells = json.load(open(OUT_DON))["cells"] if os.path.exists(OUT_DON) else {}
    seeds_v2 = json.load(open("results/dd_seed_robustness.json"))["b1"] if os.path.exists(
        "results/dd_seed_robustness.json") else {}
    out = {}
    for p in (8, 16, 128):
        recs = [c for k, c in cells.items() if k.startswith(f"{data}|p{p}|s42|")]
        if data == "v2" and p == 16:      # v2 p16 own floors come from the seed-robustness runs
            recs = [c for k, c in seeds_v2.items()
                    if k.split("|")[:2] in (["deeponet_p16", "43"], ["deeponet_p16", "44"])
                    and "trunk_floor_c" in c]
        if len(recs) < 5:
            continue
        f2 = np.concatenate([np.square(c["trunk_floor_c"]) for c in recs])
        t2 = np.concatenate([np.square(c["nrmse_c"]) for c in recs])
        mats = np.concatenate([c["material_ids"] for c in recs])
        out[p] = _share_ci(f2, t2, mats)
    return out


def _baseline(root, b1_path):
    """V5: rank by the stoichiometric time t_st (manifest), scored with the B1 metrics."""
    import dd_screening_frameworks as dd
    man = json.load(open(os.path.join(root, "manifest.json")))
    tst = {(s["mat"], s["cond"]): s["t_stoich"] for s in man["samples"] if s.get("ok", True)}
    b1 = json.load(open(b1_path))
    rows = [(c, r["t50_true_norm"][i] * r["t_final"][i], tst[(m, c)], r["t_final"][i])
            for r in b1["folds"].values()
            for i, (m, c) in enumerate(zip(r["material_ids"], r["condition_ids"]))]
    a = np.array(rows, float)
    out = {}
    # col 2: t_st, the zero-solve baseline (V5). col 3: t_final alone, which measures the size of
    # the horizon leak of amendment 1 (the stored horizon is 2.5 t_st, extended when breakthrough
    # was incomplete; a ranking by it uses no surrogate at all)
    for name, col in (("t_stoich", 2), ("t_final_leak_check", 3)):
        sp, rc = [], []
        for c in np.unique(a[:, 0]):
            j = a[:, 0] == c
            sp.append(dd.spearman(a[j, 1], a[j, col])); rc.append(dd.topk_recall(a[j, 1], a[j, col]))
        out[name] = {"spearman_mean": float(np.nanmean(sp)), "top10_recall_mean": float(np.nanmean(rc)),
                     "n_conditions": int(len(sp))}
    out["frac_horizon_extended"] = float(np.mean([s.get("horizon_extensions", 0) > 0
                                                  for s in man["samples"] if s.get("ok", True)]))
    return out


def _cost_v2():
    """Absolute costs on v2 (reviewers asked for them), all read from results files.

    Break-even of DeepONet p16 against the N_z = 50 coarse solve, counting the training set at
    production cost AND the fit (B1's measured training time, per fold), against the coarse
    solve's per-query cost (B-COARSE single-process timing); the surrogate's own query time is
    neglected, which favours the surrogate.
    """
    cb = json.load(open("results/coarse_solver_baseline.json"))["summary"]
    b1 = json.load(open("results/dd_b1_predictions.json"))["folds"]
    cv = json.load(open("results/coarse_vs_surrogates.json"))
    t_prod = float(cb["t_prod_s"])
    se50, se100 = cb["per_nz"]["50"]["solve_equivalents"], cb["per_nz"]["100"]["solve_equivalents"]
    fit_s = float(np.mean([r["deeponet_p16"]["secs"] for r in b1.values()]))
    n_train = float(cv["n_train_sims"]) if not isinstance(cv["n_train_sims"], (list, dict)) else \
        float(np.mean(list(cv["n_train_sims"].values()) if isinstance(cv["n_train_sims"], dict) else cv["n_train_sims"]))
    train_solves = n_train + fit_s / t_prod
    return {"t_prod_s": t_prod, "t_coarse50_s": float(cb["per_nz"]["50"]["mean_wall_s"]),
            "t_coarse100_s": float(cb["per_nz"]["100"]["mean_wall_s"]),
            "nrmse_coarse50": float(cb["per_nz"]["50"]["mean_nrmse_c"]),
            "nrmse_coarse100": float(cb["per_nz"]["100"]["mean_nrmse_c"]),
            "deeponet_fit_s": fit_s, "deeponet_fit_in_solves": fit_s / t_prod, "n_train_sims": n_train,
            "training_cpu_h": train_solves * t_prod / 3600.0,
            "break_even_with_fit": train_solves / se50}


def phase_analyse():
    out = {"_what": "PREREG_DD_V3 verdicts", "alpha": ALPHA, "n_boot": N_BOOT, "split": {}}
    for data, mt in (("v2", "results/l5_mapterm_v2.json"), ("v3", "results/l5_mapterm_v3.json")):
        rec = {}
        if os.path.exists(mt):
            hg = _mapterm_shares(mt)
            rec["hgb"] = {"by_p": {str(p): v for p, v in hg.items()}, "verdict": _verdict(hg)}
        dn = _don_shares(data)
        if dn:
            rec["deeponet_own_floor"] = {"by_p": {str(p): v for p, v in dn.items()}, "verdict": _verdict(dn)}
        out["split"][data] = rec
    out["baseline_tstoich"] = {}
    for data, root, b1 in (("v2", "data/parametric_v2", "results/dd_b1_predictions.json"),
                           ("v3", V3_ROOT, "results/dd_b1_predictions_v3.json")):
        if os.path.exists(b1) and os.path.exists(os.path.join(root, "manifest.json")):
            out["baseline_tstoich"][data] = _baseline(root, b1)
    out["cost_v2"] = _cost_v2()
    if os.path.exists(os.path.join(V3_ROOT, "manifest.json")):     # quoted in the text: the v3 design box
        out["design_v3"] = json.load(open(os.path.join(V3_ROOT, "manifest.json")))["material_space"]
    v3 = out["split"].get("v3", {}).get("deeponet_own_floor", {}).get("verdict")
    out["title_condition"] = {"deeponet_own_floor_v3": v3, "title_kept": v3 == "the map dominates"}
    from v2_common import write_atomic
    write_atomic(out, OUT)
    print(json.dumps(out, indent=1)[:4000])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["folds", "deeponet", "hgb", "frameworks", "analyse"])
    ap.add_argument("--data", default="v3", choices=["v2", "v3"])
    ap.add_argument("--p", type=int, default=16)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    if a.phase == "folds":
        phase_folds()
    elif a.phase == "deeponet":
        phase_deeponet(a.data, a.p, a.seed)
    elif a.phase == "hgb":
        phase_hgb()
    elif a.phase == "frameworks":
        phase_frameworks()
    else:
        phase_analyse()
