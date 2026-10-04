"""L4b-v2: the best-physics-arm verdict, adjusted for choosing that arm on the test set.

Owner of results/l4b_v2_selection.json. analyze_l4b_v2.py picks best_pi as the
eligible physics arm with the lowest HELD-OUT error and then tests it against the
data-only twin with a per-pair interval (referee M3). Here every eligible arm on each
axis enters one max-statistic cluster bootstrap (selection_adjust.simultaneous), at
the same alpha, so the interval for the selected arm is valid whatever selected it.

Also reported: a sanity check that the per-pair interval is reproduced for the
selected arm (same seed path as metrics.compare is NOT required; the per-pair numbers
quoted in the paper come from l4b_v2_verdict.json).

    python analyze_l4b_selection.py
"""
import json

import numpy as np

from analyze_l4b_v2 import ALPHA, SWEEP, seed_avg
from selection_adjust import simultaneous
from v2_common import eligible_physics_arms

OUT = "results/l4b_v2_selection.json"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", default=SWEEP)
    ap.add_argument("--verdict", default="results/l4b_v2_verdict.json")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    sw = json.load(open(args.sweep))
    seeds = sw["seeds"]
    verdict = json.load(open(args.verdict))
    out = {"_what": __doc__.splitlines()[0], "alpha": ALPHA, "n_boot": 4000, "axes": {}}
    for axis in ("time", "material"):
        S = sw["sweep"][axis]
        eligible, _, _ = eligible_physics_arms(S, seeds)
        d0, mats = seed_avg(S["data_only"], seeds, "per_sample_held")
        diffs = {}
        for a in eligible:
            v, m = seed_avg(S[a], seeds, "per_sample_held")
            assert np.array_equal(m, mats)
            diffs[a] = d0 - v                                   # positive = physics better
        res, q = simultaneous(diffs, mats, ALPHA)
        best = verdict["axes"][axis]["best_pi"]
        per_pair = verdict["axes"][axis]["best_pi_vs_data_only"]
        out["axes"][axis] = {"eligible": eligible, "k": len(eligible), "q": q,
                             "selected": best, "selected_simultaneous": res[best],
                             "selected_per_pair": {"ci_low": per_pair["ci_low"], "ci_high": per_pair["ci_high"]},
                             "all": res,
                             "survives_selection": res[best]["significant_simultaneous"]}
        r = res[best]
        print(f"[{axis}] K={len(eligible)} selected {best}: diff {r['mean_diff']:+.5f}  "
              f"per-pair [{per_pair['ci_low']:+.5f}, {per_pair['ci_high']:+.5f}]  "
              f"simultaneous [{r['sim_lo']:+.5f}, {r['sim_hi']:+.5f}]  "
              f"{'SURVIVES' if r['significant_simultaneous'] else 'does NOT survive'} selection")
    json.dump(out, open(args.out, "w"), indent=2)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
