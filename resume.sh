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
def l4b_cells(d):
    return sum(1 for ax in d.get("sweep", {}).values() for a in ax.values() for s in a)
n = n_cells("results/l4b_v2_results.json", l4b_cells)
print(f"  {'L4b-v2 sweep cells':20s}: {'MISSING' if n is None else f'{n}/{11 * 2 * 3} cells complete'}")
print(f"  {'L4b-v2 refine':20s}: {'present' if os.path.exists('results/l4b_v2_refine.json') else 'missing'}")
for label, f in (("L6-v2 checks", "results/l6_v2_checks.json"),
                 ("L6-v2 folds", "results/l6_v2_folds.json"),
                 ("L6-v2 results", "results/l6_v2_results.json"),
                 ("calibration v2", "results/calibration_v2.json"),
                 ("warp verdict", "results/warp_verdict.json")):
    print(f"  {label:20s}: {'present' if os.path.exists(f) else 'missing'}")
PY

# ---------------------------------------------------------------------------
# Is a chain incomplete AND not running? That combination has cost this project
# real time twice: two idle days once, and twelve hours to an overnight reboot on
# 2026-09-06 while the L4b-v2 sweep sat at 41/66. Both times the state report said
# "41/66 cells complete" and said nothing about the fact that nothing was working
# on the remaining 25. A stall that looks identical to progress is the problem, so
# say it loudly, at the top of every state report, whether or not "go" was passed.
# ---------------------------------------------------------------------------
# `ps -ef` under Git Bash shows only the interpreter path, never the script, so
# grepping it for a runner name always returns zero and the check would cry wolf on
# a perfectly healthy chain -- it did, the first time this was written. Ask Windows
# for the actual command line instead, and report how stale the results file is as
# corroboration.
RUNNING=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -match 'run_l4b_v2|refine_l4b_v2|run_l6_v2|run_l1_v2|run_l2_v2|run_l5_fno' }).Count" 2>/dev/null | tr -d '\r ')
RUNNING=${RUNNING:-0}
STALE=$(powershell -NoProfile -Command "if (Test-Path 'results\l4b_v2_results.json') { [int]((Get-Date) - (Get-Item 'results\l4b_v2_results.json').LastWriteTime).TotalMinutes } else { -1 }" 2>/dev/null | tr -d '\r ')
INCOMPLETE=$("$P" - <<'PY'
import json, os
def cells(path, want):
    if not os.path.exists(path):
        return 0, want
    d = json.load(open(path))
    n = sum(1 for axis in d.get("sweep", {}).values()
            for arm in axis.values() for s in arm.values() if "held" in s)
    return n, want
n, want = cells("results/l4b_v2_results.json", 66)
print("1" if n < want else "0")
PY
)
if [ "$INCOMPLETE" = "1" ] && [ "$RUNNING" -eq 0 ]; then
  echo
  echo "  ############################################################"
  echo "  #  A CHAIN IS INCOMPLETE AND NOTHING IS RUNNING."
  echo "  #  Nothing is working on the missing cells. This is what a"
  echo "  #  reboot or a killed process looks like, and it is"
  echo "  #  indistinguishable from progress unless you look here."
  echo "  #     ./resume.sh go        continues where it stopped"
  echo "  #  last results write was ${STALE} minutes ago."
  echo "  ############################################################"
elif [ "$INCOMPLETE" = "1" ]; then
  echo
  echo "  (incomplete, and $RUNNING runner process(es) alive — in flight;"
  echo "   last results write ${STALE} min ago, cells take roughly 50)"
fi

# The check above tests ONE artefact, the 66-cell sweep. Since 2026-09-24 the work in
# flight is the autorun QUEUE (follow-up chain, l5_bottleneck-v2, build), and the
# sweep reads 69/66 -- "complete" -- so the banner above could never fire for it: a
# dead queue would have been reported as nothing at all (found 2026-09-25). Test the
# queue itself: not finished, and neither its own PID nor any runner is alive.
QDONE=0; grep -q "AUTORUN_QUEUE_DONE" autorun.log 2>/dev/null && QDONE=1
QPID=$(cat autorun.lock 2>/dev/null)
QALIVE=0; [ -n "$QPID" ] && ps -p "$QPID" >/dev/null 2>&1 && QALIVE=1
ANYPY=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -match '(run|refine|refine_sweep|analyze|learning_curve)_\w*v2|run_l5_fno|l5_bottleneck' }).Count" 2>/dev/null | tr -d '\r ')
ANYPY=${ANYPY:-0}
if [ -f autorun.log ] && [ "$QDONE" = "0" ]; then
  if [ "$QALIVE" = "0" ] && [ "$ANYPY" -eq 0 ]; then
    echo
    echo "  ############################################################"
    echo "  #  THE AUTORUN QUEUE IS UNFINISHED AND NOTHING IS RUNNING."
    echo "  #  No AUTORUN_QUEUE_DONE in autorun.log, the queue's PID"
    echo "  #  (${QPID:-none}) is gone, and no runner is alive."
    echo "  #     tail -30 autorun.log                    what it last did"
    echo "  #     nohup bash autorun.sh >> autorun_outer.log 2>&1 &"
    echo "  ############################################################"
  else
    echo
    echo "  (autorun queue in flight: queue PID ${QPID:-?} alive=$QALIVE, $ANYPY runner(s) alive;"
    echo "   $(tail -1 autorun.log 2>/dev/null | cut -c1-100))"
  fi
fi

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

# 5. L4b on v2 (PREREG_L4b_v2.md): the weighting sweep, physics at inference, the
#    L-BFGS polish. Runs only after the v2 rungs above, never concurrently.
echo "-> L4b-v2: running whatever is missing (see chain_l4b_v2.sh for the order)"
bash chain_l4b_v2.sh >> chain_l4b_v2_outer.log 2>&1

echo
echo "RESUME_DONE"
