"""L5's operator verdict, from a script.

WHY THIS FILE EXISTS. `results/l5_fno_verdict.json` is read by four figures
(fig_ladder, fig_operators, fig_mechanism) and by eight macros in paper/numbers.py.
It carries L5's headline -- "the Fourier operator is significantly better and still
43x above the floor" -- and it is the file the abstract's third claim rests on.

Nothing in this repository wrote it. `grep -rn "deeponet_vs_fno\|fno_best" --include=*.py`
finds only readers. It is the B21/B43/B63 defect in its purest form: not a wrong
number, an UNOWNED one, and a reader cannot tell those apart. B63's entry says the
same thing about a Damkoehler summary that lived in a comment; this is larger,
because a retraction rests on it.

So: regenerate it, from the two runner outputs, with the comparison recomputed by
the same `metrics.compare` every other rung uses. If the regenerated numbers differ
from the ones that have been quoted, that is a finding and it is reported as one
rather than silently overwritten -- `--check` does exactly that and writes nothing.

    python analyze_l5_fno.py --check     # recompute, diff against the file, write nothing
    python analyze_l5_fno.py             # recompute and write

WHAT IT ADDS. The best DeepONet's WIDTH, which the manuscript quotes as a bare
"216" laundered through build_paper.py's ALLOWED list as "an architecture
description". It is not a description, it is the selected cell of a sweep, and the
sentence that uses it was wrong in three separate ways (see RETRACTIONS B65).
"""
from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np

from metrics import ArmResult, compare

FNO = "results/l5_fno.json"
MERGED = "results/l5_merged.json"
ONET_HI = "results/l5_onet_hi.json"
OUT = "results/l5_fno_verdict.json"
ALPHA = 0.005          # the legacy 12-cluster calibrated level (calibration_v2.legacy)
SPLIT = "novel_material"


def seed_mean_per_sample(arm, seeds, split=SPLIT):
    """Per-sample error averaged over seeds, with the sample order asserted equal."""
    recs = [arm["seeds"][str(s)][split] for s in seeds]
    ids = [tuple(r["material_ids"]) for r in recs]
    if any(i != ids[0] for i in ids[1:]):
        raise AssertionError("seeds scored on different samples")
    v = np.mean([np.asarray(r["per_sample_nrmse_c"], float) for r in recs], axis=0)
    return v, np.asarray(recs[0]["material_ids"])


def arm_mean(arm, seeds, split=SPLIT):
    return float(np.mean([arm["seeds"][str(s)][split]["c"] for s in seeds]))


def complete(arms, seeds, split=SPLIT):
    ss = [str(s) for s in seeds]
    return [a for a in arms
            if all(s in a.get("seeds", {}) and split in a["seeds"][s] for s in ss)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="recompute and diff against the existing file; write nothing")
    args = ap.parse_args()

    fno = json.load(open(FNO))
    merged = json.load(open(MERGED))
    onet = json.load(open(ONET_HI))
    seeds = fno["seeds"]

    # ---- the best FNO cell, over the whole (modes, lr) sweep -----------------
    fno_arms = complete(fno["arms"], seeds)
    if not fno_arms:
        raise SystemExit("no complete FNO arm")
    best_fno = min(fno_arms, key=lambda a: arm_mean(a, seeds))

    by_modes = {}
    for a in fno_arms:
        m = str(a["modes"])
        v = arm_mean(a, seeds)
        if m not in by_modes or v < by_modes[m]:
            by_modes[m] = v

    # ---- the best DeepONet and DeepOKAN, from the merged selection -----------
    sel = merged["selected"]
    onet_cells = {k: v for k, v in sel.items() if k.startswith("deeponet_p")}
    okan_cells = {k: v for k, v in sel.items() if k.startswith("deepokan_p")}
    best_onet_key = min(onet_cells, key=lambda k: onet_cells[k]["mean"])
    best_okan_key = min(okan_cells, key=lambda k: okan_cells[k]["mean"])
    best_onet_p = int(best_onet_key.split("_p")[1])

    # the WIDTH of that cell, which the manuscript has been typing as "216"
    onet_arms = complete(onet["arms"], seeds)
    width_rows = {a["p"]: a["width"] for a in onet_arms if a["family"] == "deeponet"}
    if best_onet_p not in width_rows:
        raise SystemExit(f"no DeepONet arm at p={best_onet_p} in {ONET_HI}; "
                         "cannot report its width without inventing it")
    best_onet_width = int(width_rows[best_onet_p])

    # ---- the paired comparison, recomputed --------------------------------
    best_onet_arm = next(a for a in onet_arms
                         if a["family"] == "deeponet" and a["p"] == best_onet_p)
    v_onet, mats_o = seed_mean_per_sample(best_onet_arm, seeds)
    v_fno, mats_f = seed_mean_per_sample(best_fno, seeds)
    if not np.array_equal(mats_o, mats_f):
        raise AssertionError("DeepONet and FNO scored on different samples; "
                             "the paired comparison would be meaningless")
    cmp_ = compare(ArmResult("DeepONet", mats_o, v_onet),
                   ArmResult("FNO", mats_f, v_fno), alpha=ALPHA, n_boot=4000)

    floor = merged["pod_floor"]
    out = {
        "_what": "L5's operator verdict, recomputed by analyze_l5_fno.py from "
                 f"{FNO}, {MERGED} and {ONET_HI}.",
        "_alpha": ALPHA,
        "_n_clusters": int(len(np.unique(mats_o))),
        "_split": SPLIT,
        "fno_best": {"mean": arm_mean(best_fno, seeds), "modes": int(best_fno["modes"]),
                     "width": int(best_fno["width"]), "lr": float(best_fno["lr"]),
                     "n_params": int(best_fno["n_params"])},
        "by_modes": by_modes,
        "fno_width_by_modes": {str(a["modes"]): int(a["width"]) for a in fno_arms},
        "deeponet_best": float(onet_cells[best_onet_key]["mean"]),
        "deeponet_best_p": best_onet_p,
        "deeponet_best_width": best_onet_width,
        "deeponet_best_n_params": int(best_onet_arm["n_params"]),
        "deeponet_width_by_p": {str(p): int(w) for p, w in sorted(width_rows.items())},
        "deepokan_best": float(okan_cells[best_okan_key]["mean"]),
        "pod_floor_p128": float(floor["128"]),
        "deeponet_vs_fno": cmp_,
        "width_ratio_onet_over_fno": best_onet_width / int(best_fno["width"]),
    }

    if args.check and os.path.exists(OUT):
        old = json.load(open(OUT))
        drift = []
        def walk(a, b, path=""):
            if isinstance(a, dict) and isinstance(b, dict):
                for k in a:
                    if k.startswith("_"):
                        continue
                    if k not in b:
                        drift.append(f"{path}{k}: MISSING from the recomputation")
                    else:
                        walk(a[k], b[k], f"{path}{k}.")
            elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
                if not math.isclose(float(a), float(b), rel_tol=1e-6, abs_tol=1e-12):
                    drift.append(f"{path[:-1]}: file {a!r} vs recomputed {b!r}")
        walk(old, out)
        print(f"{len(drift)} difference(s) between {OUT} and the recomputation")
        for d in drift:
            print("  " + d)
        if not drift:
            print("  the unowned file reproduces exactly; it is now owned.")
        return

    json.dump(out, open(OUT, "w"), indent=1)
    f = out["fno_best"]
    print(f"FNO best: modes {f['modes']}, width {f['width']}, lr {f['lr']:g} "
          f"-> {f['mean']:.5f}  ({f['n_params']:,} params)")
    print(f"  by modes: " + ", ".join(f"m{k} w{out['fno_width_by_modes'][k]} {v:.5f}"
                                      for k, v in sorted(by_modes.items(), key=lambda kv: int(kv[0]))))
    print(f"DeepONet best: p={out['deeponet_best_p']}, width {out['deeponet_best_width']} "
          f"-> {out['deeponet_best']:.5f}  ({out['deeponet_best_n_params']:,} params)")
    print(f"  width ratio DeepONet/FNO = {out['width_ratio_onet_over_fno']:.1f}x")
    c = out["deeponet_vs_fno"]
    print(f"DeepONet vs FNO: diff {c['mean_diff']:+.5f} CI [{c['ci_low']:+.5f}, {c['ci_high']:+.5f}] "
          f"{'SIGNIFICANT' if c['significant'] else 'ns'}  (alpha {ALPHA}, "
          f"{out['_n_clusters']} clusters)")
    print(f"  floor at p=128 {out['pod_floor_p128']:.3e}; FNO sits "
          f"{f['mean'] / out['pod_floor_p128']:.0f}x above it")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
