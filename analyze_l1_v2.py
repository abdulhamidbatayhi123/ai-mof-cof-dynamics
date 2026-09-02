"""L1-v2 verdict: the data-driven arms on dataset v2, both designs.

Estimands and rules are frozen in PREREG_L1L2L7_v2.md §2(a). This script computes
them; it does not choose them. Nothing here is typed into a document by hand.

  manifest design   48 held-out materials, alpha from calibration_v2.json["v2"]
  fold design       240 held-out materials (every material once), alpha from
                    calibration_v2.json["v2_5fold"]

Per-sample scores are averaged over seeds, then compared with the paired,
cluster-robust-by-material bootstrap. Every null carries its MDE (mde.py).

    python analyze_l1_v2.py [--mde-trials 200]
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

from mde import mde_report
from metrics import ArmResult, compare, format_comparison
from v2_common import alpha_for

RES = "results/l1_v2_results.json"
OUT = "results/l1_v2_verdict.json"
MDE_EFFECTS = (0.0, 0.02, 0.05, 0.10, 0.20)


def seed_avg(recs, key):
    """Per-sample vector averaged over seeds; asserts identical sample order."""
    vals = [np.asarray(r[key], dtype=float) for r in recs]
    ids = [tuple(zip(r["material_ids"], r["condition_ids"])) for r in recs]
    if any(i != ids[0] for i in ids[1:]):
        raise AssertionError("seeds were scored on different samples or in a different order")
    return np.mean(vals, axis=0), np.asarray(recs[0]["material_ids"]), np.asarray(recs[0]["condition_ids"])


def pooled_folds(res, arm, key):
    """Concatenate the seed-averaged held-out vectors of every fold (each sample once)."""
    v, m, c = [], [], []
    for f in sorted(res["folds"], key=int):
        recs = [res["folds"][f]["arms"][arm][s]["test"] for s in sorted(res["folds"][f]["arms"][arm])]
        vv, mm, cc = seed_avg(recs, key)
        v.append(vv); m.append(mm); c.append(cc)
    return np.concatenate(v), np.concatenate(m), np.concatenate(c)


def pooled_floor(res, key):
    v, m = [], []
    for f in sorted(res["folds"], key=int):
        rec = res["folds"][f]["pod_floor_per_sample"]
        v.append(np.asarray(rec[key], dtype=float)); m.append(np.asarray(rec["material_ids"]))
    return np.concatenate(v), np.concatenate(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mde-trials", type=int, default=200)
    ap.add_argument("--no-mde", action="store_true")
    args = ap.parse_args()
    if not os.path.exists(RES):
        raise SystemExit(f"{RES} missing — run run_l1_v2.py first")
    res = json.load(open(RES))
    out = {"source": RES, "field_res": res["field_res"], "modes": res["modes"],
           "seeds": res["seeds"], "arms_skipped": res.get("arms_skipped", [])}
    print(f"L1-v2 — {res['field_shape'][0]}x{res['field_shape'][1]} encoding, "
          f"{res['modes']} POD modes/channel, seeds {res['seeds']}, skipped arms {res.get('arms_skipped', [])}")

    # ── manifest design ─────────────────────────────────────────────────────
    if "manifest" in res and res["manifest"].get("arms"):
        alpha, ncl = alpha_for("manifest")
        M = res["manifest"]
        arms = [a for a in M["arms"] if len(M["arms"][a]) >= 3]
        incomplete = [a for a in M["arms"] if a not in arms]
        print(f"\n{'=' * 92}\nMANIFEST SPLIT — {ncl} held-out materials, alpha {alpha}"
              + (f"   (INCOMPLETE arms excluded: {incomplete})" if incomplete else "") + f"\n{'=' * 92}")
        fl = M["pod_floor"]
        print(f"POD floor: " + "  ".join(f"{s}: c={fl[s]['c']:.3e} exit={fl[s]['exit_nrmse']:.3e}"
                                          for s in ("train", "novel_condition", "novel_material")))
        hdr = f"  {'arm':<6} {'split':<17} {'nRMSE c':>16} {'nRMSE q':>16} {'nRMSE T':>16} {'exit':>8} {'dt50 h':>7} {'x floor':>8}"
        print(hdr); print("  " + "-" * (len(hdr) - 2))
        table = {}
        for a in arms:
            table[a] = {}
            for s in ("train", "novel_condition", "novel_material"):
                cs = [M["arms"][a][k][s]["mean"]["c"] for k in M["arms"][a]]
                qs = [M["arms"][a][k][s]["mean"]["q"] for k in M["arms"][a]]
                Ts = [M["arms"][a][k][s]["mean"]["T"] for k in M["arms"][a]]
                ex = [M["arms"][a][k][s]["mean"]["exit_nrmse"] for k in M["arms"][a]]
                dt = [M["arms"][a][k][s]["mean"]["dt_bt50"] / 3600 for k in M["arms"][a]]
                table[a][s] = {"c": float(np.mean(cs)), "c_sd": float(np.std(cs)),
                               "q": float(np.mean(qs)), "T": float(np.mean(Ts)),
                               "exit": float(np.mean(ex)), "dt50_h": float(np.mean(dt)),
                               "x_floor": float(np.mean(cs) / fl[s]["c"])}
                print(f"  {a:<6} {s:<17} {np.mean(cs):>8.4f}+-{np.std(cs):<7.4f} "
                      f"{np.mean(qs):>8.4f}+-{np.std(qs):<7.4f} {np.mean(Ts):>8.4f}+-{np.std(Ts):<7.4f} "
                      f"{np.mean(ex):>8.4f} {np.mean(dt):>7.2f} {np.mean(cs) / fl[s]['c']:>7.1f}x")
        scores = {a: seed_avg([M["arms"][a][k]["novel_material"] for k in sorted(M["arms"][a])],
                              "per_sample_nrmse_c") for a in arms}
        best = min(arms, key=lambda a: scores[a][0].mean())
        print(f"\n  best arm on novel materials: {best} = {scores[best][0].mean():.4f}")
        comps = {}
        for a in arms:
            if a == best:
                continue
            r = compare(ArmResult(best, scores[best][1], scores[best][0]),
                        ArmResult(a, scores[a][1], scores[a][0]), alpha=alpha, n_boot=4000)
            comps[a] = r
            print("    " + format_comparison(r))
        ties = [a for a, r in comps.items() if not r["significant"]]
        print(f"  -> ties with the best arm (may not be ranked): {ties if ties else 'none'}")
        print("  novel-condition split: 2 clusters — descriptive only, no verdict (PREREG §3.3)")
        out["manifest"] = {"alpha": alpha, "n_clusters": ncl, "table": table, "best": best,
                           "comparisons": comps, "ties_with_best": ties, "arms_incomplete": incomplete}

    # ── fold design ─────────────────────────────────────────────────────────
    if "folds" in res:
        alpha, ncl = alpha_for("folds")
        done = [f for f in sorted(res["folds"], key=int)
                if all(len(res["folds"][f]["arms"].get(a, {})) >= 3
                       for a in res["arms_requested"] if a not in res.get("arms_skipped", []))]
        print(f"\n{'=' * 92}\n5-FOLD DESIGN — folds complete: {done} of {res['n_folds']}, alpha {alpha} "
              f"(calibrated for {ncl} clusters)\n{'=' * 92}")
        if len(done) < res["n_folds"]:
            print("  ⚠ INCOMPLETE. Numbers below are provisional and may not be reported.")
        sub = {"folds": {f: res["folds"][f] for f in done}}
        arms = [a for a in res["arms_requested"] if a not in res.get("arms_skipped", [])]
        if done:
            floor_c, floor_m = pooled_floor(sub, "per_sample_nrmse_c")
            floor_e, _ = pooled_floor(sub, "per_sample_exit_nrmse")
            print(f"  POD floor, pooled held-out: c={floor_c.mean():.4e}  exit={floor_e.mean():.4e}  "
                  f"({len(np.unique(floor_m))} materials, {floor_c.size} samples)")
            hdr = f"  {'arm':<6} {'nRMSE c':>16} {'nRMSE q':>9} {'nRMSE T':>9} {'exit':>8} {'dt50 h':>7} {'train c':>8} {'x floor':>8}"
            print(hdr); print("  " + "-" * (len(hdr) - 2))
            table, scores, exits = {}, {}, {}
            for a in arms:
                c, m, cid = pooled_folds(sub, a, "per_sample_nrmse_c")
                q, _, _ = pooled_folds(sub, a, "per_sample_nrmse_q")
                T, _, _ = pooled_folds(sub, a, "per_sample_nrmse_T")
                e, _, _ = pooled_folds(sub, a, "per_sample_exit_nrmse")
                dt, _, _ = pooled_folds(sub, a, "per_sample_dt_bt50")
                per_fold = [np.mean([res["folds"][f]["arms"][a][s]["test"]["mean"]["c"]
                                     for s in res["folds"][f]["arms"][a]]) for f in done]
                per_seed = [np.mean([res["folds"][f]["arms"][a][s]["test"]["mean"]["c"] for f in done])
                            for s in res["seeds"]] if all(str(s) in res["folds"][done[0]]["arms"][a] for s in res["seeds"]) else []
                trc = np.mean([res["folds"][f]["arms"][a][s]["train"]["mean"]["c"]
                               for f in done for s in res["folds"][f]["arms"][a]])
                scores[a], exits[a] = (c, m, cid), (e, m, cid)
                table[a] = {"c": float(c.mean()), "c_sd_seeds": float(np.std(per_seed)) if per_seed else None,
                            "c_per_fold": [float(v) for v in per_fold], "q": float(q.mean()),
                            "T": float(T.mean()), "exit": float(e.mean()),
                            "dt50_h": float(np.nanmean(dt) / 3600), "train_c": float(trc),
                            "x_floor": float(c.mean() / floor_c.mean()),
                            "x_floor_exit": float(e.mean() / floor_e.mean())}
                print(f"  {a:<6} {c.mean():>8.4f}+-{(np.std(per_seed) if per_seed else float('nan')):<7.4f} "
                      f"{q.mean():>9.4f} {T.mean():>9.4f} {e.mean():>8.4f} {np.nanmean(dt) / 3600:>7.2f} "
                      f"{trc:>8.4f} {c.mean() / floor_c.mean():>7.1f}x")
            best = min(arms, key=lambda a: scores[a][0].mean())
            print(f"\n  best arm, pooled out-of-fold: {best} = {scores[best][0].mean():.4f}")
            comps, mdes = {}, {}
            for a in arms:
                if a == best:
                    continue
                r = compare(ArmResult(best, scores[best][1], scores[best][0]),
                            ArmResult(a, scores[a][1], scores[a][0]), alpha=alpha, n_boot=4000)
                comps[a] = r
                print("    " + format_comparison(r))
                if not r["significant"] and not args.no_mde:
                    mdes[a] = mde_report(scores[a][0] - scores[best][0], scores[a][1],
                                         base=float(scores[best][0].mean()), alpha=alpha,
                                         effects=MDE_EFFECTS, trials=args.mde_trials,
                                         label=f"{best} vs {a}")
            ties = [a for a, r in comps.items() if not r["significant"]]
            # underfitting flag (defect B14): train error within 15 % of held-out error
            underfit = [a for a in arms if table[a]["train_c"] > 0.85 * table[a]["c"]]
            print(f"  -> ties with the best arm (may not be ranked): {ties if ties else 'none'}")
            print(f"  -> arms flagged as UNDERFITTING (train within 15 % of held-out, B14): "
                  f"{underfit if underfit else 'none'}")
            print(f"\n  VERDICT: best data-driven arm sits {table[best]['x_floor']:.1f}x above the POD floor "
                  f"on the field and {table[best]['x_floor_exit']:.1f}x on the exit curve, over "
                  f"{len(np.unique(floor_m))} held-out materials.")
            out["folds"] = {"alpha": alpha, "n_clusters_calibrated": ncl, "folds_done": done,
                            "complete": len(done) == res["n_folds"], "table": table, "best": best,
                            "comparisons": comps, "ties_with_best": ties, "mde": mdes,
                            "underfitting_flag": underfit,
                            "pod_floor_pooled": {"c": float(floor_c.mean()), "exit": float(floor_e.mean())}}
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
