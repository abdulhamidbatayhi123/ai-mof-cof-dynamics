"""Paper 2 confirmatory grid, observation model O1 (PREREG_P2 §4).

REFUSES TO RUN until the pre-registration is frozen: git history must contain a commit
whose subject starts "FREEZE PREREG_P2", and PREREG_P2_discoverability.md must be
unchanged since that commit (an unfrozen edit after the freeze is an amendment and
must be committed as one). A gate that can be bypassed is not a gate (rule 6), so
there is no --force.

For every ground-truth cell x sigma x eps x replicate x solver x form, records
success (primary), k accuracy (secondary) and the selected support. Resumable:
results/p2_o1.json is rewritten atomically after every cell.

    python p2_grid_o1.py
"""
import itertools
import json
import os
import subprocess
import sys
import time

from p2.metric import k_accuracy, success_L1
from p2.run_o1 import SOLVERS, discover_o1
from p2_observe import observe
from v2_common import write_atomic

SIGMAS = (0.0, 0.005, 0.02, 0.05)
EPSS = (0.0, 0.005, 0.02, 0.05)
N_REP = 20
FORMS = ("strong", "weak")
OUT = "results/p2_o1.json"
PREREG = "PREREG_P2_discoverability.md"


def frozen():
    log = subprocess.run(["git", "log", "--format=%H %s"], capture_output=True, text=True).stdout
    frz = [ln.split(" ", 1)[0] for ln in log.splitlines() if " FREEZE PREREG_P2" in " " + ln.split(" ", 1)[1]]
    if not frz:
        return False, "no 'FREEZE PREREG_P2' commit in history"
    diff = subprocess.run(["git", "diff", "--quiet", frz[0], "--", PREREG]).returncode
    if diff != 0:
        return False, f"{PREREG} changed since the freeze commit {frz[0][:8]} -- commit it as an amendment"
    return True, frz[0]


def main():
    ok, why = frozen()
    if not ok:
        sys.exit(f"REFUSED: the pre-registration is not frozen ({why}).")
    man = json.load(open("data/p2/manifest.json"))["cells"]
    res = json.load(open(OUT)) if os.path.exists(OUT) else {"freeze_commit": why, "rows": {}}
    for name, rec in sorted(man.items()):
        if rec["law"] != "L1":
            continue   # L2 (k(q)) has its own success definition: p2_grid_o1_l2, exploratory (H2d)
        t0 = time.time()
        for sigma, eps, rep, solver, form in itertools.product(SIGMAS, EPSS, range(N_REP), SOLVERS, FORMS):
            key = f"{name}|{sigma}|{eps}|{rep}|{solver}|{form}"
            if key in res["rows"]:
                continue
            obs = observe(name, rep, sigma, eps, "O1")
            try:
                co = discover_o1(obs, solver, form)
                res["rows"][key] = {"success": bool(success_L1(co)),
                                    "k_acc": float(k_accuracy(co, rec["k_LDF"])),
                                    "support": sorted(co)}
            except Exception as e:   # recorded, never dropped
                res["rows"][key] = {"success": False, "error": f"{type(e).__name__}: {e}"}
        write_atomic(res, OUT)
        print(f"{name:<34} done [{time.time() - t0:.0f}s]", flush=True)


if __name__ == "__main__":
    main()
