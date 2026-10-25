"""PREREG_DD_V3 amendment A1: the runs and analyses added after the second internal review.

Every setting is fixed in PREREG_DD_V3.md section "Amendment A1" (pushed before any run below).
The DeepONet runs (converged own floor, t90, saved models, the material-matched v2 control) are
`dd_v3.py deeponet`; this file holds the rest.

    python dd_v3a1.py hgb90     --data v2|v3   # POD + boosting p16 per fold: error, t50, t90
    python dd_v3a1.py coarse90  --data v2|v3   # N_z = 50 coarse solve of every sample: t50, t90
    python dd_v3a1.py fwsens                   # six frameworks, v3 rule, affinity -0.5 and +1.0
    python dd_v3a1.py fwfit     --seed S       # surrogates refit on all v3 materials (models saved);
                                               # predict v3-rule, v2-rule and sensitivity frameworks
    python dd_v3a1.py analyse                  # everything A1 reports -> results/dd_v3a1_verdict.json
"""
from __future__ import annotations

import os
import sys

V3_ROOT, V3_FOLDS = "data/parametric_v3", "results/v3_folds.json"
ENV = ("ADS_DATA_ROOT", "ADS_FOLDS_FILE", "DD_TAG")


def _data_arg():
    a = sys.argv
    return a[a.index("--data") + 1] if "--data" in a else "v3"


if sys.argv[1:2] not in (["analyse"],):
    if any(k in os.environ for k in ENV):
        raise SystemExit(f"dd_v3a1: unset {ENV} in the shell; this script sets them itself")
    if _data_arg() == "v3" or sys.argv[1:2] in (["fwsens"], ["fwfit"]):
        os.environ.update({"ADS_DATA_ROOT": V3_ROOT, "ADS_FOLDS_FILE": V3_FOLDS, "DD_TAG": "_v3"})

import argparse  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

OUT_HGB = "results/dd_v3a1_hgb.json"
OUT_SENS = "results/dd_v3a1_fwsens.json"
OUT_FW = "results/dd_v3a1_fwfit.json"
OUT = "results/dd_v3a1_verdict.json"
SENS_AFFINITY = (-0.5, 1.0)
ALPHA, N_BOOT, BOOT_SEED = 0.02, 4000, 20261027


def check_design(want):
    """Refuse to run if the loaded manifest is not the design asked for."""
    from v2_common import ROOT_V2
    got = json.load(open(os.path.join(ROOT_V2, "manifest.json"))).get("design")
    if got != want:
        raise SystemExit(f"dd_v3a1: asked for design {want}, but {ROOT_V2} holds design {got}")


# ─────────────────────────────── runs ─────────────────────────────────────────
def phase_hgb90(data):
    import dd_screening_frameworks as dd
    from v2_common import assert_disjoint, load_folds, standardise_params, write_atomic
    check_design(data)
    d, C, Ft = dd.load_v2()
    fold_of, n_folds, _ = load_folds(d.material_ids)
    X = d.fields[:, 0].reshape(len(d.fields), -1)
    res = dd.load_json(OUT_HGB, {"_what": "A1: POD + boosting p16, t50 and t90", "cells": {}})
    for f in range(n_folds):
        key = f"{data}|f{f}"
        if key in res["cells"]:
            continue
        tr, te = np.where(fold_of != f)[0], np.where(fold_of == f)[0]
        assert_disjoint(tr, te, key)
        Pz = standardise_params(d.params, tr)
        fields = dd.fit_hgb(X, Pz, tr)(Pz[te])
        nr, t50 = dd.score(fields, X[te])
        res["cells"][key] = {"material_ids": d.material_ids[te].tolist(), "condition_ids": d.condition_ids[te].tolist(),
                             "nrmse_c": nr.tolist(), "t50_norm": t50,
                             "t90_norm": [dd.t90_norm(x[-1]) for x in fields.reshape(-1, dd.FIELD_RES, dd.FIELD_RES)]}
        write_atomic(res, OUT_HGB)
        print(f"  hgb {key}: nRMSE {nr.mean():.4f}", flush=True)


def phase_coarse90(data, workers=5):
    """Re-run of the coarse phase into its own file, recording t90 as well (A1)."""
    from multiprocessing import Pool
    import dd_screening_frameworks as dd
    from v2_common import ROOT_V2, write_atomic
    check_design(data)
    out = f"results/dd_v3a1_coarse_{data}.json"
    man = json.load(open(os.path.join(ROOT_V2, "manifest.json")))
    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    res = dd.load_json(out, {"_what": f"A1: N_z=50 coarse solve of every {data} sample, t50 and t90", "cells": {}})
    samples = [s for s in man["samples"] if s.get("ok", True)
               and os.path.exists(os.path.join(ROOT_V2, f"m{s['mat']:04d}_c{s['cond']:04d}.npy"))]
    todo = [(s, mats[s["mat"]], conds[s["cond"]], man["store_nz"], man["store_nt"]) for s in samples
            if f"m{s['mat']:04d}_c{s['cond']:04d}" not in res["cells"]]
    print(f"  coarse90 {data}: {len(todo)} to go", flush=True)
    with Pool(workers) as pool:
        for k, (key, cell) in enumerate(pool.imap_unordered(dd._coarse_one, todo, chunksize=4)):
            res["cells"][key] = cell
            if k % 100 == 0:
                write_atomic(res, out)
    write_atomic(res, out)


def _sens_one(args):
    import gen_parametric_dataset as gen
    import dd_screening_frameworks as dd
    from coarse_solver_baseline import sub
    name, mat, cond, aff = args
    m = dict(mat, material_id=-1, henry_affinity_log10=aff)
    r = gen.run_one((m, cond))
    cell = {"framework": name, "cond": cond["condition_id"], "affinity": aff, "ok": bool(r["ok"])}
    if r["ok"]:
        truth = sub(r["fields"], dd.FIELD_RES)
        cell.update({"t_final": r["t_final"], "t50_true_norm": dd.t50_norm(truth[0, -1]),
                     "t90_true_norm": dd.t90_norm(truth[0, -1]), "truth_c": truth[0].ravel().round(6).tolist()})
    else:
        cell["reason"] = r["reason"]
    return f"{name}|a{aff:+.1f}|c{cond['condition_id']:04d}", cell


def phase_fwsens(workers=4):
    from multiprocessing import Pool
    import dd_v3
    import dd_screening_frameworks as dd
    from v2_common import write_atomic
    dd_v3._B2_RULE = dd.framework_params
    fw, man = dd_v3.framework_params_v3()
    res = dd.load_json(OUT_SENS, {"_what": "A1: six frameworks (v3 rule) at primary-site affinity -0.5 and +1.0",
                                  "cells": {}})
    todo = [(n, {k: v for k, v in m.items() if k != "outside"}, c, a) for a in SENS_AFFINITY
            for n, m in fw.items() for c in man["conditions"]
            if f"{n}|a{a:+.1f}|c{c['condition_id']:04d}" not in res["cells"]]
    print(f"  fwsens: {len(todo)} solves", flush=True)
    with Pool(workers) as pool:
        for key, cell in pool.imap_unordered(_sens_one, todo):
            res["cells"][key] = cell
            write_atomic(res, OUT_SENS)
            print(f"  fwsens {key}: {'ok' if cell['ok'] else cell['reason']}", flush=True)


def phase_fwfit(seed):
    """Refit both arms on all v3 materials (seed `seed`), save the models, and predict every
    framework set: the v3 rule (dd_b2_frameworks_v3), the v2 rule (dd_b2_frameworks, whose
    primary-site affinity is the v2 constant, log10(1/20)), and the affinity sensitivity."""
    import pickle
    import torch
    import ladder_data
    import dd_screening_frameworks as dd
    from v2_common import ROOT_V2, write_atomic
    check_design("v3")
    d, C, Ft = dd.load_v2()
    man = json.load(open(os.path.join(ROOT_V2, "manifest.json")))
    keys = list(ladder_data.param_keys_for(man))
    conds = {c["condition_id"]: c for c in man["conditions"]}
    all_idx = np.arange(len(d.params))
    mu, sd = d.params.mean(0), d.params.std(0)
    sd[sd == 0] = 1.0
    X = d.fields[:, 0].reshape(len(d.fields), -1)
    res = dd.load_json(OUT_FW, {"_what": "A1: v3 surrogates refit on all materials, framework predictions",
                                "cells": {}})
    sets = {"v3rule": json.load(open("results/dd_b2_frameworks_v3.json")),
            "v2rule": json.load(open("results/dd_b2_frameworks.json")),
            "sens": json.load(open(OUT_SENS))}
    rows = []
    for sname, src in sets.items():
        for ck, c in src["cells"].items():
            if not c["ok"]:
                continue
            if sname == "sens":
                fwp = dict(src.get("frameworks", {}).get(c["framework"], {}))
            else:
                fwp = dict(src["frameworks"][c["framework"]])
            if sname == "sens":
                import dd_v3
                dd_v3._B2_RULE = dd.framework_params
                fwp = {k: v for k, v in dd_v3.framework_params_v3()[0][c["framework"]].items() if k != "outside"}
                fwp["henry_affinity_log10"] = c["affinity"]
            if sname == "v2rule":
                fwp["henry_affinity_log10"] = float(np.log10(1.0 / 20.0))
            raw = [(fwp[kk] if kk in fwp else conds[c["cond"]][kk]) for kk in keys]
            rows.append((sname, ck, c, raw))
    Pz_new = (np.array([r[3] for r in rows], float) - mu) / sd
    truth = np.array([r[2]["truth_c"] for r in rows], float)
    os.makedirs("models", exist_ok=True)
    for arm in ("hgb_p16", "deeponet_p16"):
        key = f"{arm}|s{seed}"
        if any(k.startswith(key + "|") for k in res["cells"]):
            continue
        t1 = time.time()
        if arm == "hgb_p16":
            pred = dd.fit_hgb(X, (d.params - mu) / sd, all_idx, seed=seed)
        else:
            pred = dd.fit_deeponet(Ft, C, (d.params - mu) / sd, all_idx, seed=seed)
            torch.save(pred.model.state_dict(), os.path.join("models", f"fwfit_v3_deeponet_p16_s{seed}.pt"))
        fields = pred(Pz_new)
        nr, t50 = dd.score(fields, truth)
        t90 = [dd.t90_norm(x[-1]) for x in fields.reshape(-1, dd.FIELD_RES, dd.FIELD_RES)]
        for (sname, ck, c, _), a, b, e in zip(rows, nr, t50, t90):
            res["cells"][f"{key}|{sname}|{ck}"] = {"set": sname, "framework": c["framework"], "cond": c["cond"],
                                                    "nrmse_c": float(a), "t50_norm": b, "t90_norm": e,
                                                    "t50_true_norm": c["t50_true_norm"], "t_final": c["t_final"],
                                                    "affinity": c.get("affinity")}
        write_atomic(res, OUT_FW)
        print(f"  fwfit {key}: mean nRMSE {nr.mean():.4f} [{time.time() - t1:.0f}s]", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["hgb90", "coarse90", "fwsens", "fwfit", "analyse"])
    ap.add_argument("--data", default="v3", choices=["v2", "v3"])
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    if a.phase == "hgb90":
        phase_hgb90(a.data)
    elif a.phase == "coarse90":
        phase_coarse90(a.data)
    elif a.phase == "fwsens":
        phase_fwsens()
    elif a.phase == "fwfit":
        phase_fwfit(a.seed)
    else:
        import dd_v3a1_analyse
        dd_v3a1_analyse.main()
