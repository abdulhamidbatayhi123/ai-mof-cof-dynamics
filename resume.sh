#!/bin/bash
# Resume after a shutdown. Safe to run any number of times.
#
# Nothing here is destructive and nothing recomputes work already on disk:
# every runner writes its results file after each completed arm, so a killed job
# loses at most the single configuration that was in flight.
#
#   ./resume.sh            show what is done and what is left, run nothing
#   ./resume.sh go         run whatever is missing
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8

echo "=============================================================="
echo " STATE"
echo "=============================================================="
"$P" - <<'PY'
import json, os
def n_arms(f, key="arms"):
    if not os.path.exists(f): return None
    d = json.load(open(f))
    a = d[key] if isinstance(d.get(key), list) else []
    return sum(1 for x in a if sum(1 for s in x.get("seeds", {})
                                   if "novel_material" in x["seeds"][s]) >= 3)

print(f"  dataset v2          : {'COMPLETE' if os.path.exists('data/parametric_v2/manifest.json') else 'MISSING'}"
      f"  ({len([f for f in os.listdir('data/parametric_v2') if f.endswith('.npy')]) if os.path.isdir('data/parametric_v2') else 0} sims)")
for label, f, want in (("L3 (merged)", "results/l3_results.json", 15),
                       ("L3 bracket", "results/l3_bracket.json", 6),
                       ("L3 cheby 1e-1", "results/l3_cheby_1e-1.json", 2),
                       ("L5 FNO", "results/l5_fno.json", 6)):
    n = n_arms(f)
    print(f"  {label:20s}: {'MISSING' if n is None else f'{n}/{want} arms complete'}")
def n_cells(f, walker):
    if not os.path.exists(f): return None
    try: return walker(json.load(open(f)))
    except Exception: return -1
def l1_cells(d):
    n = sum(1 for a in d.get("manifest", {}).get("arms", {}).values() for s in a)
    n += sum(1 for fo in d.get("folds", {}).values() for a in fo.get("arms", {}).values() for s in a)
    return n
def lc_cells(d):
    return sum(1 for fo in d.get("folds", {}).values() for ax in ("materials", "conditions")
               for g in fo.get(ax, {}).values() for s in g)
def l2_cells(d):
    return sum(1 for k in d.get("cells", {}).values() for fo in k.values() for s in fo)
for label, f, w, want in (("L1-v2 cells", "results/l1_v2_results.json", l1_cells, 12 + 60),
                          ("LC-v2 cells", "results/learning_curve_v2.json", lc_cells, 5 * 9 * 3),
                          ("L2-v2 cells", "results/l2_v2_results.json", l2_cells, 28 * 3 * 5)):
    n = n_cells(f, w)
    print(f"  {label:20s}: {'MISSING' if n is None else f'{n}/{want} cells complete'}")
print(f"  {'L7-v2':20s}: {'present' if os.path.exists('results/l7_v2_results.json') else 'missing'}")
for label, f in (("L6-v2 checks", "results/l6_v2_checks.json"),
                 ("L6-v2 folds", "results/l6_v2_folds.json"),
                 ("L6-v2 results", "results/l6_v2_results.json"),
                 ("calibration v2", "results/calibration_v2.json"),
                 ("warp verdict", "results/warp_verdict.json")):
    print(f"  {label:20s}: {'present' if os.path.exists(f) else 'missing'}")
PY

if [ "$1" != "go" ]; then
  echo
  echo "  (nothing run. use  ./resume.sh go  to continue the work)"
  exit 0
fi

echo
echo "=============================================================="
echo " RESUMING"
echo "=============================================================="

# 1. Finish the FNO sweep if modes=16 never completed. Low value -- at a matched
#    200k budget width collapses to ~7 channels -- but it completes the sweep and
#    the FNO conclusion does not depend on it.
if ! "$P" -c "
import json,sys
try: d=json.load(open('results/l5_fno.json'))
except Exception: sys.exit(1)
sys.exit(0 if any(a['modes']==16 and sum(1 for s in a['seeds'] if 'novel_material' in a['seeds'][s])>=3 for a in d['arms']) else 1)
"; then
  echo "-> FNO modes=16 missing; running (~3 h)"
  "$P" -u run_l5_fno.py --modes 16 --lrs 3e-3 1e-3 --seeds 42 43 44 \
       --steps 8000 --budget 200000 --threads 4 \
       --out results/l5_fno_m16.json >> l5_fno_m16.log 2>&1
else
  echo "-> FNO complete, skipping"
fi

# 2. L6-v2. Aborts by itself if the kinetic object is recoverable (defect B19).
#
#    Resumes FOLD BY FOLD. The first version of this script tested only whether
#    l6_v2_results.json existed, which would have refused to continue a run that
#    was killed after fold 0 — leaving four fifths of the primary hypothesis
#    undone while reporting "already has results". Ask which folds are complete,
#    and run exactly the ones that are not.
MISSING=$("$P" - <<'PY'
import json, os
want = {"joint", "separate", "separate_noeq"}
try:
    d = json.load(open("results/l6_v2_results.json"))
    folds, done = d.get("n_folds", 5), []
    for f, rec in d.get("folds", {}).items():
        arms = rec.get("arms", {})
        if set(arms) >= want and all(
            sum(1 for s in arms[a] if "per_sample_nrmse_c" in arms[a][s]) >= 3 for a in want):
            done.append(int(f))
except Exception:
    folds, done = 5, []
print(" ".join(str(f) for f in range(folds) if f not in done))
PY
)
if [ -n "$MISSING" ]; then
  echo "-> L6-v2: running folds [$MISSING] of 5 (the primary hypothesis)"
  "$P" -u run_l6_v2.py --folds 5 --seeds 42 43 44 --only-folds $MISSING >> l6_v2.log 2>&1
else
  echo "-> L6-v2 complete, all 5 folds"
fi

# 3. The verdict, once every fold is in.
if [ -f results/l6_v2_results.json ] && [ -z "$MISSING" ]; then
  echo "-> L6-v2 slope test"
  "$P" -u analyze_l6_v2.py 2>&1 | tee -a l6_v2_analysis.log
fi

# 4. L1, L2, L7 on dataset v2 (PREREG_L1L2L7_v2.md). Every runner resumes by
#    skipping completed cells, so each is simply invoked; nothing is recomputed.
echo "-> L1/L2/L7 on v2: running whatever is missing (see chain_v2_rungs.sh for the order)"
bash chain_v2_rungs.sh >> chain_v2_rungs_outer.log 2>&1

echo
echo "RESUME_DONE"
