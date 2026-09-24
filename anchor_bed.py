r"""Record the anchor bed's operating conditions as data, so the manuscript can quote them.

The manuscript states the Lassitter et al. (2024) bed geometry and conditions inside
\SI{}{} commands. build_paper.py used to strip \SI wholesale, value and unit together,
so six experimental inputs reached the paper with no script behind them
(audit_hygiene #2 -- B21/B43 reproduced inside the fix for B21/B43).

This script owns them. It reads the values the comparison ACTUALLY RUNS WITH, from
compare_lassitter.physics() and its module constants, rather than retyping them, so
the paper and the solve cannot disagree. It solves nothing.

    python anchor_bed.py        # writes results/anchor_bed.json
"""
import json
import os

import compare_lassitter as cl

p = cl.physics(*cl.PRIMARY[:2], 1e4, 1000.0)
out = {
    "_source": "compare_lassitter.physics() and module constants; Lassitter et al. 2024 SI",
    "bed_length_mm": p.L * 1e3,
    "tube_diameter_mm": p.D_in * 1e3,
    "rh_percent": cl.RH_IN * 100.0,
    "T_K": cl.T_K,
    "bulk_density_kg_m3": p.rho_p * (1.0 - p.eps_t),
}
os.makedirs("results", exist_ok=True)
json.dump(out, open("results/anchor_bed.json", "w"), indent=2)
print(json.dumps(out, indent=2))
