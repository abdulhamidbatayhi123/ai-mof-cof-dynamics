"""L3: 'the perceptron beats both KAN families at every budget, all six comparisons
significant' -- owned, and adjusted for choosing both arms of each pair.

Owner of results/l3_selection.json. The manuscript's "all six pairwise comparisons
significant" had no script (audit 2026-09-24 #10 flagged the words around it; the
round-2 referee, N4, the selection). Each of the six comparisons (three budgets x two
KAN families) pits the perceptron at its best learning rate against the KAN family at
its best learning rate, both chosen on the held-out materials the comparison is
scored on. Selection runs on both sides, so this computes:

  per_pair       metrics.compare on the six selected pairs, at the calibrated alpha --
                 the comparison as it was made;
  simultaneous   one studentised max-statistic cluster bootstrap
                 (selection_adjust.simultaneous) over EVERY (KAN cell, perceptron cell)
                 pair at the same budget, all budgets and both families in one family,
                 differences KAN - MLP (positive = the perceptron is better). The
                 interval it gives each selected pair holds however both were chosen.

Cells, and the 'best learning rate' rule, are analyze_l3_merged.py's: a configuration
counts only if every seed trained; per-sample errors are the seed mean, with the
sample order asserted equal.

    python analyze_l3_selection.py
"""
import json
from collections import defaultdict

import numpy as np

from analyze_l3_merged import FILES
from metrics import ALPHA_CALIBRATED, ArmResult, compare
from selection_adjust import simultaneous

OUT = "results/l3_selection.json"
MERGED = "results/l3_merged.json"
SPLIT = "novel_material"


def cells():
    out = defaultdict(dict)                          # budget -> {(family, lr): (v, mats)}
    for f in FILES:
        for a in json.load(open(f))["arms"]:
            recs = [s[SPLIT] for s in a["seeds"].values() if SPLIT in s]
            if len(recs) != len(a["seeds"]) or len(recs) < 3:
                continue                             # any failed seed: excluded, never averaged
            ids = [tuple(r["material_ids"]) for r in recs]
            if any(i != ids[0] for i in ids[1:]):
                raise AssertionError("seeds scored on different samples")
            v = np.mean([np.asarray(r["per_sample_nrmse_c"], float) for r in recs], axis=0)
            key = (a["family"], float(a["lr"]))
            if key in out[a["budget"]]:
                raise SystemExit(f"duplicate cell {a['budget']} {key}")
            out[a["budget"]][key] = (v, np.asarray(recs[0]["material_ids"]))
    return out


def main():
    table = json.load(open(MERGED))["table"]
    by_b = cells()
    mats = next(iter(next(iter(by_b.values())).values()))[1]
    diffs, selected = {}, {}
    for b, cs in sorted(by_b.items()):
        for (fam, lr), (_, m) in cs.items():
            if not np.array_equal(m, mats):
                raise AssertionError(f"{b} {fam} {lr} scored on different samples")
        mlp = {lr: v for (fam, lr), (v, _) in cs.items() if fam == "mlp"}
        for kan in sorted({fam for fam, _ in cs if fam != "mlp"}):
            kc = {lr: v for (fam, lr), (v, _) in cs.items() if fam == kan}
            for lk, vk in kc.items():
                for lm, vm in mlp.items():
                    diffs[f"{b}|{kan}@{lk:g}|mlp@{lm:g}"] = vk - vm
            bk = min(kc, key=lambda lr: kc[lr].mean())
            bm = min(mlp, key=lambda lr: mlp[lr].mean())
            # the selection must be the one the manuscript's table reports
            assert np.isclose(table[f"{b}_{kan}"]["lr"], bk) and np.isclose(table[f"{b}_mlp"]["lr"], bm)
            selected[f"{b}|{kan}"] = (f"{b}|{kan}@{bk:g}|mlp@{bm:g}", kc[bk], mlp[bm])

    sim, q = simultaneous(diffs, mats, ALPHA_CALIBRATED)
    rows = {}
    for name, (key, vk, vm) in selected.items():
        c = compare(ArmResult("kan", mats, vk), ArmResult("mlp", mats, vm), alpha=ALPHA_CALIBRATED)
        rows[name] = {"pair": key, "per_pair": c, "simultaneous": sim[key]}
    out = {
        "_what": "L3 selected MLP-vs-KAN pairs: per-pair and simultaneous over every "
                 "(KAN cell, MLP cell) pair at the same budget; written by analyze_l3_selection.py",
        "_alpha": ALPHA_CALIBRATED,
        "_n_clusters": int(len(np.unique(mats))),
        "k": len(diffs),
        "q": q,
        "n_pairs": len(rows),
        "n_sig_per_pair": sum(r["per_pair"]["significant"] for r in rows.values()),
        "n_sig_simultaneous": sum(r["simultaneous"]["significant_simultaneous"] for r in rows.values()),
        "n_mlp_better_simultaneous": sum(r["simultaneous"]["sim_lo"] > 0 for r in rows.values()),
        "pairs": rows,
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"{len(diffs)} pairs in the family; q = {q:.2f} SE ({out['_n_clusters']} clusters, "
          f"alpha {ALPHA_CALIBRATED})")
    for name, r in rows.items():
        p, s = r["per_pair"], r["simultaneous"]
        print(f"  {r['pair']:42s} KAN-MLP {s['mean_diff']:+.5f}  per-pair "
              f"[{p['ci_low']:+.5f}, {p['ci_high']:+.5f}] {'S' if p['significant'] else 'ns'}  "
              f"simult. [{s['sim_lo']:+.5f}, {s['sim_hi']:+.5f}] "
              f"{'S' if s['significant_simultaneous'] else 'ns'}")
    print(f"significant: {out['n_sig_per_pair']}/{len(rows)} per pair, "
          f"{out['n_sig_simultaneous']}/{len(rows)} simultaneous "
          f"({out['n_mlp_better_simultaneous']} with the perceptron better)")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
