"""Summary of the POST-HOC test-time refinement sweep (material axis, data-only arm).

Owner of results/l4b_v2_refine_sweep_summary.json. The pre-registered refinement
(steps 300, lr 1e-4, scope all) made held-out error several times worse on the
material axis. The labelled post-hoc sweep (refine_sweep_l4b_v2.py, B60) asks whether
that is a property of physics at inference or of one configuration: it tries scope
{last layer, all} x lr {1e-6 .. 1e-3} and reads every checkpoint in eval_at.

Reported per configuration: the seed-averaged held-out error at every checkpoint and
the best relative change from step 0 (negative = improvement). Overall: the single
best (configuration, step) anywhere -- the most generous reading for physics, and
itself selected on the held-out materials, which is stated next to it.

    python analyze_l4b_refine_sweep.py
"""
import json

import numpy as np

SRC = "results/l4b_v2_refine_sweep.json"
OUT = "results/l4b_v2_refine_sweep_summary.json"


def main():
    d = json.load(open(SRC))
    ev = d["eval_at"]
    cells, best = {}, None
    for name, by_seed in d["cells"].items():
        m = np.array([[by_seed[s]["means"][str(e)] for e in ev] for s in by_seed]).mean(0)
        rel = 100.0 * (m - m[0]) / m[0]
        i = int(np.argmin(rel[1:])) + 1            # best AFTER some refinement, not step 0
        cells[name] = {"n_seeds": len(by_seed), "means": dict(zip(map(str, ev), m.tolist())),
                       "best_rel_change_pct": float(rel[i]), "best_step": ev[i],
                       "final_rel_change_pct": float(rel[-1])}
        if best is None or rel[i] < best[1]:
            best = (name, float(rel[i]), ev[i])
    out = {"_note": "POST HOC (B60). Selected on held-out materials; the most generous reading.",
           "source": SRC, "axis": d["axis"], "arm": d["arm"], "eval_at": ev,
           "n_configs": len(cells), "n_checkpoints": len(ev) - 1, "cells": cells,
           "best_anywhere": {"config": best[0], "rel_change_pct": best[1], "step": best[2]},
           "n_configs_worse_at_final": sum(c["final_rel_change_pct"] > 0 for c in cells.values())}
    json.dump(out, open(OUT, "w"), indent=2)
    for k, c in cells.items():
        print(f"  {k:16s} best {c['best_rel_change_pct']:+7.2f}% (step {c['best_step']:>3})  "
              f"final {c['final_rel_change_pct']:+8.1f}%")
    print(f"best anywhere: {best[0]} {best[1]:+.2f}% at step {best[2]}; "
          f"{out['n_configs_worse_at_final']}/{len(cells)} worse at the last checkpoint")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
