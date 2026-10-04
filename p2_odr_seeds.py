"""PREREG_P2 §3, before the freeze: is the ODR-BINDy port's accuracy gap real or one draw?

The single verification run (noise seed 12) recovered the exact Lorenz support but a
relative coefficient error of 5.0e-3 against ~2.2e-3 read from Fung et al.'s Fig. 8,
which is a MULTI-RUN average. One draw cannot separate scatter from a real gap. The
prereg's rule, written before this runs: run five noise seeds; if the multi-seed mean
error still exceeds the reported figure, M5 is run and reported as "port, accuracy
below the reference", with the gap stated.

Seeds 1-5 (seed 12 is the existing record and is not reused). Identical setup to
tests/test_odr_bindy.run_lorenz_example. Resumable: each finished seed is written at
once. ~40 min per seed on this machine. Output: results/odr_bindy_seeds.json

    python p2_odr_seeds.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests"))
from test_odr_bindy import REPORTED_REL_ERR, run_lorenz_example  # noqa: E402

SEEDS = [1, 2, 3, 4, 5]
OUT = "results/odr_bindy_seeds.json"


def main():
    res = json.load(open(OUT)) if os.path.exists(OUT) else {"runs": {}}
    for s in SEEDS:
        if str(s) in res["runs"]:
            print(f"seed {s}: done, skipping")
            continue
        r = run_lorenz_example(seed=s, write=False)["reproduced"]
        res["runs"][str(s)] = {k: r[k] for k in ("support_correct", "n_terms_found", "missing_terms",
                                                 "extra_terms", "rel_frobenius_error", "runtime_s")}
        print(f"seed {s}: support {r['support_correct']}  rel err {r['rel_frobenius_error']:.2e}  "
              f"[{r['runtime_s']:.0f}s]", flush=True)
        tmp = OUT + ".tmp"
        json.dump(res, open(tmp, "w"), indent=2)
        os.replace(tmp, OUT)
    errs = np.array([v["rel_frobenius_error"] for v in res["runs"].values()])
    res["summary"] = {
        "n_seeds": len(errs), "support_rate": float(np.mean([v["support_correct"] for v in res["runs"].values()])),
        "rel_err_mean": float(errs.mean()), "rel_err_median": float(np.median(errs)),
        "reported_rel_err": REPORTED_REL_ERR, "reported_success_rate": 0.79,
        "gap_ratio_mean": float(errs.mean() / REPORTED_REL_ERR),
        "verdict": ("port matches the reported accuracy" if errs.mean() <= REPORTED_REL_ERR else
                    "port, accuracy below the reference (PREREG_P2 §3): gap stated as gap_ratio_mean"),
    }
    json.dump(res, open(OUT, "w"), indent=2)
    print(json.dumps(res["summary"], indent=1))
    print("ODR_SEEDS_DONE")


if __name__ == "__main__":
    main()
