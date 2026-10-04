"""L2-v2: the 'best configuration vs the L1 setting' gain, adjusted for choosing it.

Owner of results/l2_v2_selection.json. analyze_l2_v2.py reports the best of the
capacity sweep against the L1 setting (+21 %) with a per-pair interval; the best was
chosen on the same held-out materials (referee M3, B1). Here every sweep configuration
enters one studentised max-statistic cluster bootstrap against the L1 setting
(selection_adjust.simultaneous), at the five-fold design's alpha, so the interval for
the selected configuration is valid however it was selected.

The L1 setting appears in the sweep twice (mlp_depth/d3 and mlp_width/w256 are the
same configuration); both are the reference, not candidates.

    python analyze_l2_selection.py
"""
import json

import numpy as np

from analyze_l2_v2 import pooled
from selection_adjust import simultaneous
from v2_common import alpha_for

RES = "results/l2_v2_results.json"
VER = "results/l2_v2_verdict.json"
OUT = "results/l2_v2_selection.json"
REF = "mlp_depth/d3"
SAME_AS_REF = {"mlp_depth/d3", "mlp_width/w256"}


def main():
    res = json.load(open(RES))
    folds = [str(f) for f in range(res["n_folds"])]
    keys = [k for k, v in res["cells"].items() if all(f in v for f in folds)]
    vals = {k: pooled(res, k, folds) for k in keys}
    ref_v, mats = vals[REF]
    for k, (v, m) in vals.items():
        assert np.array_equal(m, mats), k
    diffs = {k: ref_v - v for k, (v, _) in vals.items() if k not in SAME_AS_REF}
    alpha, _ = alpha_for("folds")
    out_all, q = simultaneous(diffs, mats, alpha)
    best = max(diffs, key=lambda k: diffs[k].mean())
    ver_best = "/".join(json.load(open(VER))["best_overall"][1:])
    if best != ver_best:
        raise SystemExit(f"selected {best} differs from the verdict's {ver_best}")
    r = out_all[best]
    base = float(ref_v.mean())
    out = {"_what": __doc__.splitlines()[0], "alpha": alpha, "k": len(diffs), "q": q,
           "reference": REF, "selected": best, "selected_simultaneous": r,
           "pct": 100 * r["mean_diff"] / base, "pct_sim_lo": 100 * r["sim_lo"] / base,
           "pct_sim_hi": 100 * r["sim_hi"] / base,
           "survives_selection": r["significant_simultaneous"], "all": out_all}
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"K={len(diffs)}, q={q:.2f}: {best} vs {REF}: {out['pct']:+.1f} %, simultaneous "
          f"[{out['pct_sim_lo']:+.1f}, {out['pct_sim_hi']:+.1f}] % -> "
          f"{'SURVIVES' if r['significant_simultaneous'] else 'does NOT survive'} selection")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
