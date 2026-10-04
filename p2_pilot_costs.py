"""PREREG_P2 pre-freeze cost gate for M8 (KAN symbolic extraction) on its subgrid.

Owner of results/p2_cost_gates.json. Run on the KNOWN-ANSWER system only (never a grid
cell), at the grid's size: 20 probes x 200 times (p2_observe's N_PROBE, N_T).

Rule, written before this runs: M8 runs on its declared subgrid (216 fits: 9 Da x 2
sigma x 2 eps x 2 isotherms x 3 replicates) iff ONE fit takes <= 300 s on this machine,
i.e. the subgrid fits in <= 18 h of queue time; otherwise it is reported NOT RUN on the
grid, in those words, with this measurement as the reason. A machine limit, not a
judgement of the method.

    .venv/Scripts/python.exe p2_pilot_costs.py
"""
import json
import time

import numpy as np

from p2.features import derivative
from p2.methods import kan_symbolic
from p2.synthetic import ldf_series

OUT = "results/p2_cost_gates.json"
LIMIT_S = 300.0
N_PROBE, N_T = 20, 200


def main():
    chans = {"c": [], "q": [], "T": [], "qstar": []}
    for j in range(N_PROBE):
        s = ldf_series(k=0.02, n=N_T, t_end=600.0, seed=j)
        for k in chans:
            chans[k].append(s[k])
    t = np.linspace(0.0, 600.0, N_T)
    V = {k: np.concatenate(v) for k, v in chans.items()}
    y = np.concatenate([derivative(q, t) for q in chans["q"]])
    t0 = time.time()
    co = kan_symbolic(V, y, seed=0)
    sec = time.time() - t0
    out = {"_what": __doc__.splitlines()[0], "limit_s": LIMIT_S,
           "m8": {"sec_per_fit": sec, "run": sec <= LIMIT_S, "support_on_known_answer": sorted(co),
                  "fits_on_subgrid": 216, "projected_h": 216 * sec / 3600}}
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"M8: {sec:.0f} s per fit -> {'RUN on the subgrid' if out['m8']['run'] else 'NOT RUN'} "
          f"({out['m8']['projected_h']:.1f} h projected); wrote {OUT}")


if __name__ == "__main__":
    main()
