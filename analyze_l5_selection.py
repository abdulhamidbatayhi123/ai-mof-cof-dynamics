"""L5: 'the Fourier operator is significantly better than DeepONet', adjusted for choosing both.

Owner of results/l5_fno_selection.json. analyze_l5_fno.py compares the best FNO cell
(over modes x learning rate) with the best DeepONet cell (over basis size x learning
rate), both chosen on the same held-out materials the comparison is scored on
(round-2 referee, N4). Selection happened on BOTH sides, so a family over FNO cells
against one fixed DeepONet would not pay for it. Here the family is every
(DeepONet cell, FNO cell) pair: one studentised max-statistic cluster bootstrap
(selection_adjust.simultaneous) over all pairwise per-sample differences
DeepONet - FNO, at the legacy design's alpha. The interval it gives the selected pair
holds however either half of the pair was chosen.

DeepONet cells come from every source the L5 merge reads (results/l5_merged.json
"sources"); a (p, lr) cell present in more than one source must agree, or the script
refuses. Each cell is the seed mean per sample, as in analyze_l5_fno.

    python analyze_l5_selection.py
"""
import json

import numpy as np

from analyze_l5_fno import ALPHA, FNO, MERGED, arm_mean, complete, seed_mean_per_sample
from selection_adjust import simultaneous

OUT = "results/l5_fno_selection.json"
VERDICT = "results/l5_fno_verdict.json"


def main():
    fno = json.load(open(FNO))
    seeds = fno["seeds"]
    merged = json.load(open(MERGED))

    onet = {}
    for src in merged["sources"]:
        for a in complete(json.load(open("results/" + src)).get("arms", []), seeds):
            if a.get("family") != "deeponet":
                continue
            key = f"deeponet_p{a['p']}_lr{a['lr']:g}"
            v, m = seed_mean_per_sample(a, seeds)
            if key in onet and not np.allclose(onet[key][0], v):
                raise SystemExit(f"{key} differs between sources; refusing to pick one")
            onet[key] = (v, m)
    fcells = {f"fno_m{a['modes']}_lr{a['lr']:g}": seed_mean_per_sample(a, seeds)
              for a in complete(fno["arms"], seeds)}

    mats = next(iter(fcells.values()))[1]
    for k, (_, m) in {**onet, **fcells}.items():
        if not np.array_equal(m, mats):
            raise AssertionError(f"{k} scored on different samples")

    diffs = {f"{o}|{f}": onet[o][0] - fcells[f][0] for o in onet for f in fcells}
    res, q = simultaneous(diffs, mats, ALPHA)

    best_f = min(fcells, key=lambda k: fcells[k][0].mean())
    best_o = min(onet, key=lambda k: onet[k][0].mean())
    ver = json.load(open(VERDICT))
    assert np.isclose(fcells[best_f][0].mean(), ver["fno_best"]["mean"]), "FNO best disagrees with the verdict file"
    assert np.isclose(onet[best_o][0].mean(), ver["deeponet_best"]), "DeepONet best disagrees with the verdict file"
    sel = res[f"{best_o}|{best_f}"]

    out = {
        "_what": "DeepONet - FNO for the selected pair, simultaneous over every "
                 "(DeepONet cell, FNO cell) pair; written by analyze_l5_selection.py",
        "_alpha": ALPHA,
        "_n_clusters": int(len(np.unique(mats))),
        "n_deeponet_cells": len(onet),
        "n_fno_cells": len(fcells),
        "k": len(diffs),
        "q": q,
        "selected_pair": [best_o, best_f],
        "selected": sel,
        "selected_rel_lo_pct": 100 * sel["sim_lo"] / onet[best_o][0].mean(),
        "selected_rel_hi_pct": 100 * sel["sim_hi"] / onet[best_o][0].mean(),
        "per_pair": ver["deeponet_vs_fno"],
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"{len(onet)} DeepONet x {len(fcells)} FNO cells = {len(diffs)} pairs; q = {q:.2f} SE "
          f"({out['_n_clusters']} clusters, alpha {ALPHA})")
    print(f"selected {best_o} vs {best_f}: diff {sel['mean_diff']:+.5f}, simultaneous "
          f"[{sel['sim_lo']:+.5f}, {sel['sim_hi']:+.5f}] "
          f"({'excludes' if sel['significant_simultaneous'] else 'includes'} zero)")
    print(f"per-pair interval was [{ver['deeponet_vs_fno']['ci_low']:+.5f}, "
          f"{ver['deeponet_vs_fno']['ci_high']:+.5f}]")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
