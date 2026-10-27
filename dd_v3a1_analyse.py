"""PREREG_DD_V3 amendment A1: every analysis the amendment registers -> results/dd_v3a1_verdict.json.

Reads only results files (and the two dataset manifests). Refuses, rather than skips, when a
registered cell is missing (the B37/B74 lesson: a gate whose input can go missing must fail).

    python dd_v3a1.py analyse
"""
from __future__ import annotations

import inspect
import json
import os

import numpy as np

import dd_screening_frameworks as dd
from v2_common import write_atomic

DON = "results/dd_v3a1_deeponet.json"
HGB = "results/dd_v3a1_hgb.json"
FW = "results/dd_v3a1_fwfit.json"
OUT = "results/dd_v3a1_verdict.json"
ROOTS = {"v2": "data/parametric_v2", "v3": "data/parametric_v3"}
ALPHA, N_BOOT, BOOT_SEED = 0.02, 4000, 20261027
REGISTERED = {"v2": (8, 16, 128), "v3": (8, 16, 128)}       # seed 42, five folds each
ROBUST = {"v2": (43, 44), "v3": (43,)}                       # extra seeds at p = 16


def _cells(res, prefix, need=5):
    cs = [c for k, c in res.items() if k.startswith(prefix + "|f")]
    if len(cs) != need:
        raise SystemExit(f"A1 analysis: registered cell set '{prefix}' has {len(cs)} of {need} folds")
    return cs


def _boot(stat, groups, rng, n=N_BOOT):
    um = np.array(list(groups))
    return [stat(np.concatenate([groups[m] for m in rng.choice(um, len(um), replace=True)]))
            for _ in range(n)]


def _q(xs):
    return [float(np.percentile(xs, 100 * ALPHA / 2)), float(np.percentile(xs, 100 * (1 - ALPHA / 2)))]


def share_record(floor, total, mats):
    f2, t2, mats = np.square(floor), np.square(total), np.asarray(mats)
    by = {m: np.where(mats == m)[0] for m in np.unique(mats)}
    bs = _boot(lambda i: 1 - f2[i].sum() / t2[i].sum(), by, np.random.default_rng(BOOT_SEED))
    per = 1 - f2 / np.maximum(t2, 1e-300)            # per-sample share (the pooled share weights large errors)
    return {"share_map": float(1 - f2.sum() / t2.sum()), "ci": _q(bs),
            "mean_floor": float(np.mean(floor)), "mean_total": float(np.mean(total)),
            "per_sample_median_share": float(np.median(per)),
            "frac_samples_floor_dominated": float(np.mean(per < 0.5))}


def verdict(by_p):
    hi = [p for p in by_p if p >= 16]
    if all(by_p[p]["share_map"] >= 0.5 and by_p[p]["ci"][0] >= 0.5 for p in hi):
        return "the map dominates"
    if by_p[16]["share_map"] <= 0.5 and by_p[16]["ci"][1] <= 0.5:
        return "the basis binds"
    return "neither dominates"


def split_a1(don):
    out = {}
    for data, ps in REGISTERED.items():
        by_p, diag = {}, {}
        for p in ps:
            cs = _cells(don, f"{data}|p{p}|s42")
            fl = np.concatenate([c["trunk_floor_c"] for c in cs])
            tot = np.concatenate([c["nrmse_c"] for c in cs])
            own = np.concatenate([c["own_coeff_nrmse_c"] for c in cs])
            conv = np.concatenate([c["floor_converged"] for c in cs])
            by_p[p] = share_record(fl, tot, np.concatenate([c["material_ids"] for c in cs]))
            diag[p] = {"frac_converged": float(conv.mean()), "frac_floor_le_total": float((fl <= tot + 1e-9).mean()),
                       "max_abs_own_minus_total": float(np.max(np.abs(own - tot)))}
        rob = {}
        for s in ROBUST[data]:
            cs = _cells(don, f"{data}|p16|s{s}")
            rob[str(s)] = share_record(np.concatenate([c["trunk_floor_c"] for c in cs]),
                                       np.concatenate([c["nrmse_c"] for c in cs]),
                                       np.concatenate([c["material_ids"] for c in cs]))
        out[data] = {"by_p": {str(p): v for p, v in by_p.items()}, "verdict": verdict(by_p),
                     "diagnostics": {str(p): v for p, v in diag.items()}, "seeds_p16": rob}
    return out


# ─────────────────────────────── screening, t50 and t90 ─────────────────────
def _rank_metrics(rows, arm, which, idx, within_fold=False):
    sp, rc = [], []
    for c in np.unique(rows["cond"][idx]):
        j = idx[rows["cond"][idx] == c]
        groups = [j] if not within_fold else [j[rows["fold"][j] == f] for f in np.unique(rows["fold"][j])]
        for g in groups:
            if len(g) < 3:
                continue
            sp.append(dd.spearman(rows[f"true_{which}"][g], rows[f"{arm}_{which}"][g]))
            rc.append(dd.topk_recall(rows[f"true_{which}"][g], rows[f"{arm}_{which}"][g]))
    return float(np.nanmean(sp)), float(np.nanmean(rc))


def screening_rows(data, don):
    man = json.load(open(os.path.join(ROOTS[data], "manifest.json")))
    samp = {(s["mat"], s["cond"]): s for s in man["samples"] if s.get("ok", True)}
    co = json.load(open(f"results/dd_v3a1_coarse_{data}.json"))["cells"]
    hg = json.load(open(HGB))["cells"]
    cols = {k: [] for k in ("mat", "cond", "fold", "tf", "tst", "mult", "true_t50", "true_t90", "don_t50", "don_t90",
                            "hgb_t50", "hgb_t90", "coarse_t50", "coarse_t90", "nr_don", "nr_hgb", "nr_coarse",
                            "coarse_ok", "don_t50_norm")}
    for c in _cells(don, f"{data}|p16|s42"):
        h = hg[f"{data}|f{c['fold']}"]
        assert h["material_ids"] == c["material_ids"]
        for i, (m, k) in enumerate(zip(c["material_ids"], c["condition_ids"])):
            s, tf = samp[(m, k)], c["t_final"][i]
            cc = co[f"m{m:04d}_c{k:04d}"]
            ok = bool(cc.get("accepted"))
            vals = {"mat": m, "cond": k, "fold": c["fold"], "tf": tf, "tst": s["t_stoich"], "mult": s["horizon_mult"],
                    "true_t50": c["t50_true_norm"][i] * tf, "true_t90": c["t90_true_norm"][i] * tf,
                    "don_t50": c["t50_norm"][i] * tf, "don_t90": c["t90_norm"][i] * tf,
                    "hgb_t50": h["t50_norm"][i] * tf, "hgb_t90": h["t90_norm"][i] * tf,
                    "coarse_t50": (cc["t50_norm"] if ok else c["t50_true_norm"][i]) * tf,
                    "coarse_t90": (cc.get("t90_norm") if ok else c["t90_true_norm"][i]) * tf,
                    "nr_don": c["nrmse_c"][i], "nr_hgb": h["nrmse_c"][i],
                    "nr_coarse": cc["nrmse_c"] if ok else 0.0, "coarse_ok": ok, "don_t50_norm": c["t50_norm"][i]}
            for kk, v in vals.items():
                cols[kk].append(v)
    return {k: np.array(v, dtype=float) for k, v in cols.items()}


def screening(data, don):
    rows = screening_rows(data, don)
    idx_all = np.arange(len(rows["mat"]))
    by = {m: np.where(rows["mat"] == m)[0] for m in np.unique(rows["mat"])}
    out = {}
    for which in ("t50", "t90"):
        rec = {}
        for arm in ("don", "hgb", "coarse"):
            sp, rc = _rank_metrics(rows, arm, which, idx_all)
            bs = _boot(lambda i: np.array(_rank_metrics(rows, arm, which, i)), by,
                       np.random.default_rng(BOOT_SEED), n=1000)
            bs = np.array(bs)
            r = {"spearman": sp, "spearman_ci": _q(bs[:, 0]), "recall": rc, "recall_ci": _q(bs[:, 1]),
                 "tie_bias_spearman": float(bs[:, 0].mean() - sp), "tie_bias_recall": float(bs[:, 1].mean() - rc)}
            r["screening_adequate"] = bool(r["spearman_ci"][0] >= 0.90 and r["recall_ci"][0] >= 0.80)
            per_sp, per_rc = [], []                    # one value per condition, for the figure
            for cnd in np.unique(rows["cond"]):
                j = idx_all[rows["cond"] == cnd]
                per_sp.append(dd.spearman(rows[f"true_{which}"][j], rows[f"{arm}_{which}"][j]))
                per_rc.append(dd.topk_recall(rows[f"true_{which}"][j], rows[f"{arm}_{which}"][j]))
            r["per_condition_spearman"], r["per_condition_recall"] = per_sp, per_rc
            if arm != "coarse":
                r["within_fold_spearman"], r["within_fold_recall"] = _rank_metrics(rows, arm, which, idx_all, True)
            rec[arm] = r
        sp_b, rc_b = [], []                            # zero-solve baseline: rank by t_st
        for cnd in np.unique(rows["cond"]):
            j = idx_all[rows["cond"] == cnd]
            sp_b.append(dd.spearman(rows[f"true_{which}"][j], rows["tst"][j]))
            rc_b.append(dd.topk_recall(rows[f"true_{which}"][j], rows["tst"][j]))
        rec["baseline_tstoich"] = {"spearman": float(np.nanmean(sp_b)), "recall": float(np.nanmean(rc_b))}
        out[which] = rec
    ok = rows["coarse_ok"] > 0.5
    out["field"] = {"don": float(rows["nr_don"].mean()), "hgb": float(rows["nr_hgb"].mean()),
                    "coarse_policy": float(rows["nr_coarse"].mean()),
                    "ratio_policy": float(rows["nr_don"].mean() / rows["nr_coarse"].mean()),
                    "ratio_excluded": float(rows["nr_don"][ok].mean() / rows["nr_coarse"][ok].mean()),
                    "n_coarse_failed": int((~ok).sum()), "n": int(len(ok))}
    out["leak_bound"] = leak_bound(rows)
    # Family-wise check (added after the third internal review, ledger B91): the eight surrogate
    # adequacy verdicts (2 arms x 2 designs x 2 times) at a Bonferroni level alpha / 8, with 4000
    # draws so the 0.125 % tails are resolved; the verdict rule is otherwise the registered one.
    a_bonf = ALPHA / 8
    out["bonferroni"] = {}
    for which in ("t50", "t90"):
        for arm in ("don", "hgb"):
            bs = np.array(_boot(lambda i: np.array(_rank_metrics(rows, arm, which, i)), by,
                                np.random.default_rng(BOOT_SEED + 7), n=N_BOOT))
            lo_sp = float(np.percentile(bs[:, 0], 100 * a_bonf / 2))
            lo_rc = float(np.percentile(bs[:, 1], 100 * a_bonf / 2))
            out["bonferroni"][f"{which}|{arm}"] = {"spearman_lo": lo_sp, "recall_lo": lo_rc,
                                                  "screening_adequate": bool(lo_sp >= 0.90 and lo_rc >= 0.80)}
    return out


def leak_bound(rows):
    """Re-score DeepONet's t50 ranking with a horizon predicted out of fold from the parameters
    (a gradient-boosted classifier of the extension multiplier), instead of the true horizon."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    mult = np.round(rows["mult"], 2)                 # the horizon is one of a few fixed multiples
    classes, lab = np.unique(mult, return_inverse=True)
    pred_mult = np.empty_like(mult)
    # parameters are not in the rows; the classifier sees log t_st and the condition, both solve-free
    X = np.column_stack([np.log(rows["tst"]), rows["cond"]])
    for f in np.unique(rows["fold"]):
        tr, te = rows["fold"] != f, rows["fold"] == f
        clf = HistGradientBoostingClassifier(max_iter=200, random_state=0).fit(X[tr], lab[tr])
        pred_mult[te] = classes[clf.predict(X[te])]
    t50_free = rows["don_t50_norm"] * pred_mult * rows["tst"]
    sp_true, rc_true = _rank_metrics(rows, "don", "t50", np.arange(len(mult)))
    r2 = dict(rows, don_t50=t50_free)
    sp_free, rc_free = _rank_metrics(r2, "don", "t50", np.arange(len(mult)))
    out = {"spearman_true_horizon": sp_true, "spearman_predicted_horizon": sp_free,
           "recall_true_horizon": rc_true, "recall_predicted_horizon": rc_free,
           "multiplier_accuracy": float((pred_mult == mult).mean()),
           "majority_class_accuracy": float(np.bincount(lab).max() / len(lab))}
    # A second solve-free horizon, added after the third internal review (ledger B91): one fixed
    # multiple of the stoichiometric time for every sample. Within a condition the multiple drops
    # out of the ranking, so this ranks by predicted t50/t_final times t_st, with no classifier.
    by = {m: np.where(rows["mat"] == m)[0] for m in np.unique(rows["mat"])}
    for arm in ("don", "hgb"):
        r3 = dict(rows, **{f"{arm}_t50": rows[f"{arm}_t50"] / rows["tf"] * rows["tst"]})
        sp, rc = _rank_metrics(r3, arm, "t50", np.arange(len(mult)))
        bs = np.array(_boot(lambda i: np.array(_rank_metrics(r3, arm, "t50", i)), by,
                            np.random.default_rng(BOOT_SEED), n=1000))
        out[f"{arm}_fixed_multiple"] = {"spearman": sp, "spearman_ci": _q(bs[:, 0]), "recall": rc,
                                        "recall_ci": _q(bs[:, 1]),
                                        "screening_adequate": bool(_q(bs[:, 0])[0] >= 0.90 and _q(bs[:, 1])[0] >= 0.80)}
    return out


# ─────────────────────────────── control, frameworks, physics checks ─────────
def control(don):
    out = {}
    for tag in ("v2|p16|s42", "v2ctl|p16|s42", "v3|p16|s42"):
        cs = _cells(don, tag)
        out[tag.split("|")[0]] = {"nrmse": float(np.mean(np.concatenate([c["nrmse_c"] for c in cs]))),
                                  "n_train_materials": [c["n_train_materials"] for c in cs]}
    out["v3_over_v2ctl"] = out["v3"]["nrmse"] / out["v2ctl"]["nrmse"]
    out["v2ctl_over_v2"] = out["v2ctl"]["nrmse"] / out["v2"]["nrmse"]
    return out


def frameworks():
    res = json.load(open(FW))["cells"]
    v3 = json.load(open("results/dd_additions_verdict_v3.json"))["b2"]
    v2 = json.load(open("results/dd_additions_verdict.json"))["b2"]
    out = {"p95": {"v2": v2["p95_heldout_material_nrmse"], "v3": v3["p95_heldout_material_nrmse"]}, "by": {}}
    for k, c in res.items():
        arm, seed, sname = k.split("|")[:3]
        aff = c.get("affinity")
        tag = f"{arm}|{sname}" + (f"|a{aff:+.1f}" if sname == "sens" else "")
        rec = out["by"].setdefault(tag, {}).setdefault(c["framework"], {}).setdefault(seed, {"nr": [], "dt": [], "rel": []})
        rec["nr"].append(c["nrmse_c"])
        tt, tp = c["t50_true_norm"] * c["t_final"], c["t50_norm"] * c["t_final"]
        rec["dt"].append(abs(tp - tt) / 60.0)
        rec["rel"].append(abs(tp - tt) / tt)
    for tag, fws in out["by"].items():
        for fw, seeds in fws.items():
            for s, r in seeds.items():
                seeds[s] = {"nrmse": float(np.mean(r["nr"])), "abs_t50_err_min": float(np.nanmean(r["dt"])),
                            "rel_t50_err": float(np.nanmean(r["rel"])), "n_conditions": len(r["nr"])}
            vals = [v["nrmse"] for v in seeds.values()]
            # how many accepted conditions each number rests on (ledger B91: at affinity +1.0 the
            # feed saturates most isotherms, and a mean over one or two conditions is not comparable)
            fws[fw] = {"per_seed": seeds, "min": min(vals), "max": max(vals),
                       "n_conditions": min(v["n_conditions"] for v in seeds.values())}
    return out


def physics_checks():
    out = {}
    calib = inspect.signature(__import__("calibrate_v2").simulate).parameters["trials"].default
    fpr = json.load(open("results/calibration_v2.json"))["v2_5fold"]["fpr_by_alpha"]
    out["alpha_calibration"] = {"trials": int(calib), "size_at_002_pct": fpr["0.02"],
                                "mc_se_pct": float(100 * np.sqrt(fpr["0.02"] / 100 * (1 - fpr["0.02"] / 100) / calib)),
                                "size_at_005_pct": fpr["0.05"],
                                "mc_se_005_pct": float(100 * np.sqrt(fpr["0.05"] / 100 * (1 - fpr["0.05"] / 100) / calib))}
    cps = json.load(open("results/design_constants.json"))["physics"]["C_ps"]
    for data, root in ROOTS.items():
        man = json.load(open(os.path.join(root, "manifest.json")))
        ok = [s for s in man["samples"] if s.get("ok", True)]
        da_st = {}
        for s in ok:
            da_st.setdefault(s["mat"], []).append(s["k_LDF"] * s["t_stoich"])
        per_mat = np.array([np.median(v) for v in da_st.values()])
        q = np.array([m["q_max"] for m in man["materials"]])
        ratio = q * 0.018015 * 4180.0 / cps                   # adsorbed water heat capacity at saturation / C_ps
        n_all = len(man["materials"]) * len(man["conditions"])
        rec = {"da_stoich_per_material_min": float(per_mat.min()), "da_stoich_per_material_median": float(np.median(per_mat)),
               "adsorbed_cp_over_solid_median": float(np.median(ratio)), "adsorbed_cp_over_solid_max": float(ratio.max()),
               "acceptance": float(len(ok) / n_all)}
        if data == "v3":
            mats = {m["material_id"]: m for m in man["materials"]}
            acc = {(s["mat"], s["cond"]) for s in ok}
            aff = np.array([mats[m]["henry_affinity_log10"] for m in mats])
            qs = np.quantile(aff, [0.25, 0.5, 0.75])
            by_q = []
            for lo, hi in zip([-np.inf, *qs], [*qs, np.inf]):
                ms = [m for m in mats if lo <= mats[m]["henry_affinity_log10"] < hi]
                by_q.append(float(np.mean([(m, c["condition_id"]) in acc for m in ms for c in man["conditions"]])))
            steep = [m for m in mats if mats[m]["isotherm_n"] >= 8]
            mild = [m for m in mats if mats[m]["isotherm_n"] < 8]
            rec["acceptance_by_affinity_quartile"] = by_q
            rec["acceptance_n_ge_8"] = float(np.mean([(m, c["condition_id"]) in acc for m in steep for c in man["conditions"]]))
            rec["acceptance_n_lt_8"] = float(np.mean([(m, c["condition_id"]) in acc for m in mild for c in man["conditions"]]))
            rec["materials_without_samples"] = int(len(mats) - len({m for m, _ in acc}))
        out[data] = rec
    return out


def main():
    don = json.load(open(DON))["cells"]
    out = {"_what": "PREREG_DD_V3 amendment A1 verdicts and checks", "alpha": ALPHA, "n_boot": N_BOOT,
           "split_deeponet_own_floor": split_a1(don),
           "screening": {d: screening(d, don) for d in ("v2", "v3")},
           "control": control(don), "frameworks": frameworks(), "physics": physics_checks()}
    write_atomic(out, OUT)
    s = out["split_deeponet_own_floor"]
    for d in s:
        print(d, s[d]["verdict"], {p: round(v["share_map"], 4) for p, v in s[d]["by_p"].items()}, s[d]["diagnostics"])
    print(json.dumps({d: {w: {a: (round(r["spearman"], 3), round(r["recall"], 3), r.get("screening_adequate"))
                              for a, r in out["screening"][d][w].items()} for w in ("t50", "t90")}
                      for d in out["screening"]}, indent=1))
    print("control", out["control"])


if __name__ == "__main__":
    main()
