"""Owner of results/l6_v2_mde_corrected.json -- which had none.

Five manuscript macros (L6's MDE, power at 2 % and 4 %, size at the null, the
between-cluster share) read that file. It was written around the A25 correction
(commit 1fd19df, 2026-09-02) by a call to mde.mde_report that no script records;
`mde.py --check-l6-v2` writes a DIFFERENT file (l6_v2_mde_check.json) from a
different input. This script re-derives it from the raw L6-v2 results through the
same function, and mde_report is seeded per trial, so a faithful reconstruction must
reproduce the stored file exactly.

Inputs are built exactly as analyze_l6_v2.py builds its primary paired comparison:
per-sample held-out nRMSE of the `separate` and `joint` arms, concatenated in the same
fold/seed order (flat()), difference separate - joint, base = the joint arm's mean.

    python analyze_l6_mde.py --inputs   # cheap: compare inputs with the stored file
    python analyze_l6_mde.py --check    # full Monte Carlo; diff against the stored file
    python analyze_l6_mde.py            # full Monte Carlo; write the file
"""
import json
import sys

import numpy as np

from analyze_l6_v2 import RES, flat
from mde import cluster_structure, mde_report

OUT = "results/l6_v2_mde_corrected.json"
EFFECTS = (0.0, 0.01, 0.02, 0.03, 0.04, 0.06, 0.10)
LABEL = "L6-v2 separate vs joint (corrected)"


def inputs():
    res = json.load(open(RES))
    vj, mj = flat(res, "joint")
    vs, ms = flat(res, "separate")
    vj, vs = np.asarray(vj, float), np.asarray(vs, float)
    assert list(mj) == list(ms), "joint and separate samples are not in the same order"
    return vs - vj, np.asarray(mj), float(vj.mean())


def main():
    delta, mats, base = inputs()
    old = json.load(open(OUT))
    if "--inputs" in sys.argv:
        cs = cluster_structure(delta, mats)
        for k, new in (("base", base), ("n_samples", delta.size), ("n_clusters", cs["n_clusters"]),
                       ("between_sd", cs["between_sd"]), ("within_sd", cs["within_sd"])):
            print(f"  {k:<12} stored {old[k]!r:<24} rebuilt {new!r}")
        return
    rep = mde_report(delta, mats, base, alpha=0.02, effects=EFFECTS, trials=400, n_boot=600,
                     verbose=False, label=LABEL)
    if "--check" in sys.argv:
        diffs = {k: (old.get(k), rep[k]) for k in rep if old.get(k) != rep[k]}
        print("identical to the stored file" if not diffs else f"DIFFERS: {diffs}")
        sys.exit(0 if not diffs else 1)
    json.dump(rep, open(OUT, "w"), indent=2)
    print(f"wrote {OUT}: MDE {rep['mde_80']}, power {rep['power']}")


if __name__ == "__main__":
    main()
