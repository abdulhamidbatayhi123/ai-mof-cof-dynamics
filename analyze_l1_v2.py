"""L1-v2 verdict: the data-driven arms on dataset v2, both designs.

Estimands and rules are frozen in PREREG_L1L2L7_v2.md §2(a). This script computes
them; it does not choose them. Nothing here is typed into a document by hand.

  manifest design   48 held-out materials, alpha from calibration_v2.json["v2"]
  fold design       240 held-out materials (every material once), alpha from
                    calibration_v2.json["v2_5fold"]

Per-sample scores are averaged over seeds, then compared with the paired,
cluster-robust-by-material bootstrap. Every null carries its MDE (mde.py); when
the MDE is skipped (--no-mde) the verdict is written as PROVISIONAL and may not be
reported. The B14 underfitting flag is enforced: a flagged arm cannot be "best".

    python analyze_l1_v2.py [--mde-trials 200] [--no-mde]
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
UNDERFIT_RATIO = 0.85          # train error within 15 % of held-out error (defect B14)


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


def select_best(arms, mean_of, train_of):
    """Best = lowest held-out error, but a B14-flagged best is refused (PREREG §4.3).

    A linear arm (ridge) has train ≈ held-out by construction — that is low
    capacity, not under-training — so the flag matters only when the flagged arm
    would otherwise be reported as the rung's best.
    """
    flagged = [a for a in arms if train_of[a] > UNDERFIT_RATIO * mean_of[a]]
    best = min(arms, key=mean_of.get)
    if best in flagged:
        raise SystemExit(f"ABORT: the best arm '{best}' has train error {train_of[best]:.4f} within 15 % of its "
                         f"held-out error {mean_of[best]:.4f} — the B14 underfitting signature. It may not be "
                         f"reported as the best data-driven arm until its configuration is fixed and re-run.")
    return best, flagged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mde-trials", type=int, default=200)
    ap.add_argument("--no-mde", action="store_true")
    ap.add_argument("--res", default=RES)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    res_path, out_path = args.res, args.out
    if not os.path.exists(res_path):
        raise SystemExit(f"{res_path} missing — run run_l1_v2.py first")
    res = json.load(open(res_path))
    seeds = [str(s) for s in res["seeds"]]
    out = {"source": res_path, "field_res": res["field_res"], "modes": res["modes"],
           "seeds": res["seeds"], "arms_skipped": res.get("arms_skipped", []),
           "mde_computed": not args.no_mde}
    tag = "" if not args.no_mde else "PROVISIONAL (no MDE) — "
    print(f"L1-v2 — {res['field_shape'][0]}x{res['field_shape'][1]} encoding, "
          f"{res['modes']} POD modes/channel, seeds {res['seeds']}, skipped arms {res.get('arms_skipped', [])}"
          + ("\n  ⚠ --no-mde: every null below is PROVISIONAL and may not be reported" if args.no_mde else ""))

    def dump():
        json.dump(out, open(out_path, "w"), indent=2)

    # ── manifest design ─────────────────────────────────────────────────────
    arms = None
    if "manifest" in res and res["manifest"].get("arms"):
        alpha, ncl = alpha_for("manifest")
        M = res["manifest"]
        arms = [a for a in M["arms"] if all(s in M["arms"][a] for s in seeds)]
        incomplete = [a for a in M["arms"] if a not in arms]
        print(f"\n{'=' * 92}\nMANIFEST SPLIT — {ncl} held-out materials, alpha {alpha}"
              + (f"   (INCOMPLETE arms excluded: {incomplete})" if incomplete else "") + f"\n{'=' * 92}")
        if not arms:
            print("  no arm has all seeds yet — nothing to report")
            out["manifest"] = {"alpha": alpha, "n_clusters": ncl, "arms_incomplete": incomplete,
                               "provisional": True}
            arms = None
    if arms:
        fl = M["pod_floor"]
        print("POD floor: " + "  ".join(f"{s}: c={fl[s]['c']:.3e} exit={fl[s]['exit_nrmse']:.3e}"
                                        for s in ("train", "novel_condition", "novel_material")))
        hdr = (f"  {'arm':<6} {'split':<17} {'nRMSE c':>16} {'nRMSE q':>16} {'nRMSE T':>16} "
               f"{'exit':>8} {'dt50 h':>7} {'x floor':>8}")
        print(hdr); print("  " + "-" * (len(hdr) - 2))
        table = {}
        for a in arms:
            table[a] = {}
            for s in ("train", "novel_condition", "novel_material"):
                cs = [M["arms"][a][k][s]["mean"]["c"] for k in seeds]
                qs = [M["arms"][a][k][s]["mean"]["q"] for k in seeds]
                Ts = [M["arms"][a][k][s]["mean"]["T"] for k in seeds]
                ex = [M["arms"][a][k][s]["mean"]["exit_nrmse"] for k in seeds]
                dt = [M["arms"][a][k][s]["mean"]["dt_bt50"] / 3600 for k in seeds]
                table[a][s] = {"c": float(np.mean(cs)), "c_sd": float(np.std(cs)),
                               "q": float(np.mean(qs)), "T": float(np.mean(Ts)),
                               "exit": float(np.mean(ex)), "dt50_h": float(np.mean(dt)),
                               "x_floor": float(np.mean(cs) / fl[s]["c"])}
                print(f"  {a:<6} {s:<17} {np.mean(cs):>8.4f}+-{np.std(cs):<7.4f} "
                      f"{np.mean(qs):>8.4f}+-{np.std(qs):<7.4f} {np.mean(Ts):>8.4f}+-{np.std(Ts):<7.4f} "
                      f"{np.mean(ex):>8.4f} {np.mean(dt):>7.2f} {np.mean(cs) / fl[s]['c']:>7.1f}x")
        scores = {a: seed_avg([M["arms"][a][k]["novel_material"] for k in seeds], "per_sample_nrmse_c")
                  for a in arms}
        best, flagged = select_best(arms, {a: float(scores[a][0].mean()) for a in arms},
                                    {a: table[a]["train"]["c"] for a in arms})
        print(f"\n  best arm on novel materials: {best} = {scores[best][0].mean():.4f}"
              + (f"   (train ≈ held-out, low-capacity or under-trained: {flagged})" if flagged else ""))
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
                                     label=f"manifest {best} vs {a}")
        ties = [a for a, r in comps.items() if not r["significant"]]
        print(f"  -> {tag}ties with the best arm (may not be ranked): {ties if ties else 'none'}")
        print("  novel-condition split: 2 clusters — descriptive only, no verdict (PREREG §3.3)")
        out["manifest"] = {"alpha": alpha, "n_clusters": ncl, "table": table, "best": best,
                           "comparisons": comps, "ties_with_best": ties, "arms_incomplete": incomplete,
                           "underfitting_flag": flagged, "mde": mdes if not args.no_mde else "PENDING",
                           "provisional": bool(args.no_mde and ties)}
        dump()

    # ── fold design ─────────────────────────────────────────────────────────
    if "folds" in res:
        alpha, ncl = alpha_for("folds")
        arms_all = [a for a in res["arms_requested"] if a not in res.get("arms_skipped", [])]
        done = [f for f in sorted(res["folds"], key=int)
                if all(all(s in res["folds"][f]["arms"].get(a, {}) for s in seeds) for a in arms_all)]
        complete = len(done) == res["n_folds"]
        print(f"\n{'=' * 92}\n5-FOLD DESIGN — folds complete: {done} of {res['n_folds']}, alpha {alpha} "
              f"(calibrated for {ncl} clusters)\n{'=' * 92}")
        if not complete:
            print("  ⚠ INCOMPLETE. Numbers below are provisional and may not be reported.")
        if done:
            sub = {"folds": {f: res["folds"][f] for f in done}}
            floor_c, floor_m = pooled_floor(sub, "per_sample_nrmse_c")
            floor_e, _ = pooled_floor(sub, "per_sample_exit_nrmse")
            print(f"  POD floor, pooled held-out: c={floor_c.mean():.4e}  exit={floor_e.mean():.4e}  "
                  f"({len(np.unique(floor_m))} materials, {floor_c.size} samples)")
            hdr = (f"  {'arm':<6} {'nRMSE c':>16} {'nRMSE q':>9} {'nRMSE T':>9} {'exit':>8} "
                   f"{'dt50 h':>7} {'train c':>8} {'x floor':>8}")
            print(hdr); print("  " + "-" * (len(hdr) - 2))
            table, scores = {}, {}
            for a in arms_all:
                c, m, cid = pooled_folds(sub, a, "per_sample_nrmse_c")
                q, _, _ = pooled_folds(sub, a, "per_sample_nrmse_q")
                T, _, _ = pooled_folds(sub, a, "per_sample_nrmse_T")
                e, _, _ = pooled_folds(sub, a, "per_sample_exit_nrmse")
                dt, _, _ = pooled_folds(sub, a, "per_sample_dt_bt50")
                per_fold = [np.mean([res["folds"][f]["arms"][a][s]["test"]["mean"]["c"] for s in seeds])
                            for f in done]
                per_seed = [np.mean([res["folds"][f]["arms"][a][s]["test"]["mean"]["c"] for f in done])
                            for s in seeds]
                trc = float(np.mean([res["folds"][f]["arms"][a][s]["train"]["mean"]["c"]
                                     for f in done for s in seeds]))
                scores[a] = (c, m, cid)
                table[a] = {"c": float(c.mean()), "c_sd_seeds": float(np.std(per_seed)),
                            "c_per_fold": [float(v) for v in per_fold], "q": float(q.mean()),
                            "T": float(T.mean()), "exit": float(e.mean()),
                            "dt50_h": float(np.nanmean(dt) / 3600), "train_c": trc,
                            "x_floor": float(c.mean() / floor_c.mean()),
                            "x_floor_exit": float(e.mean() / floor_e.mean())}
                print(f"  {a:<6} {c.mean():>8.4f}+-{np.std(per_seed):<7.4f} {q.mean():>9.4f} {T.mean():>9.4f} "
                      f"{e.mean():>8.4f} {np.nanmean(dt) / 3600:>7.2f} {trc:>8.4f} "
                      f"{c.mean() / floor_c.mean():>7.1f}x")
            best, flagged = select_best(arms_all, {a: table[a]["c"] for a in arms_all},
                                        {a: table[a]["train_c"] for a in arms_all})
            print(f"\n  best arm, pooled out-of-fold: {best} = {table[best]['c']:.4f}"
                  + (f"   (train ≈ held-out, low-capacity or under-trained: {flagged})" if flagged else ""))
            comps, mdes = {}, {}
            for a in arms_all:
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
                                         label=f"folds {best} vs {a}")
            ties = [a for a, r in comps.items() if not r["significant"]]
            print(f"  -> {tag}ties with the best arm (may not be ranked): {ties if ties else 'none'}")
            print(f"\n  VERDICT{' (PROVISIONAL)' if not complete or args.no_mde else ''}: best data-driven arm sits "
                  f"{table[best]['x_floor']:.1f}x above the POD floor on the field and "
                  f"{table[best]['x_floor_exit']:.1f}x on the exit curve, over "
                  f"{len(np.unique(floor_m))} held-out materials.")
            out["folds"] = {"alpha": alpha, "n_clusters_calibrated": ncl, "folds_done": done,
                            "complete": complete, "table": table, "best": best,
                            "comparisons": comps, "ties_with_best": ties,
                            "mde": mdes if not args.no_mde else "PENDING",
                            "underfitting_flag": flagged,
                            "provisional": bool(not complete or (args.no_mde and ties)),
                            "pod_floor_pooled": {"c": float(floor_c.mean()), "exit": float(floor_e.mean())}}
            dump()
    dump()
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
