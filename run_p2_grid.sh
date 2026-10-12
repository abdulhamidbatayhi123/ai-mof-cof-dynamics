#!/bin/bash
# Paper 2 confirmatory grid, in order, one job at a time (PREREG_P2 s.3-s.4, amendments A1-A4).
#
# Every driver refuses to run unless PREREG_P2 matches its latest FREEZE commit, and every
# driver is resumable cell by cell, so a killed job loses at most the cell in flight and a
# re-run skips what is on disk. A step whose marker exists is skipped. A failing step is
# retried twice, then the chain stops and says so. Nothing here chooses or decides anything.
#
#   bash run_p2_grid.sh            # run what is missing (log: p2_grid_chain.log)
#   bash run_p2_grid.sh status     # show which steps are done
cd "$(dirname "$0")" || exit 1
PY="C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics/.venv/Scripts/python.exe"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=2
MARK=results/.p2_grid_done
mkdir -p "$MARK"
log() { echo "[$(date '+%F %T')] $*"; }

STEPS=(
  "o1           | p2_grid_o1.py"
  "m5           | p2_grid_extra.py m5"
  "m9           | p2_grid_extra.py m9"
  "m6           | p2_grid_extra.py m6"
  "l2           | p2_grid_extra.py l2"
  "o2           | p2_grid_o23.py o2"
  "o1ident      | p2_grid_extra.py o1ident"
  "o2ident      | p2_grid_o23.py o2ident"
  "o3           | p2_grid_o23.py o3"
  "m7           | p2_grid_extra.py m7"
  "m1           | p2_grid_extra.py m1"
  "refinelevels | p2_analyze.py --refine-levels"
  "generate_ref | p2_generate.py --refine"
  "o1_ref       | p2_grid_o1.py"
  "m5_ref       | p2_grid_extra.py m5"
  "m7_ref       | p2_grid_extra.py m7"
  "analyze      | p2_analyze.py"
)

if [ "$1" = "status" ]; then
  for s in "${STEPS[@]}"; do n="$(echo "${s%%|*}" | xargs)"
    [ -f "$MARK/$n" ] && echo "done     $n  ($(cat "$MARK/$n"))" || echo "pending  $n"; done
  exit 0
fi

log "=== Paper 2 grid chain start; freeze: $("$PY" -c 'import p2_grid_o1;print(p2_grid_o1.frozen())')"
for s in "${STEPS[@]}"; do
  n="$(echo "${s%%|*}" | xargs)"; cmd="$(echo "${s#*|}" | xargs)"
  if [ -f "$MARK/$n" ]; then log "skip  $n (done)"; continue; fi
  ok=0
  for attempt in 1 2 3; do
    log "START $n: $cmd (attempt $attempt)"
    t0=$(date +%s)
    if "$PY" -X utf8 $cmd; then ok=1; break; fi
    log "FAIL  $n (attempt $attempt)"
  done
  if [ $ok = 1 ]; then
    echo "$(date '+%F %T') $(( $(date +%s) - t0 ))s" > "$MARK/$n"
    log "DONE  $n ($(( $(date +%s) - t0 ))s)"
  else
    log "STOP  chain halted at $n after 3 attempts"; exit 1
  fi
done
log "=== P2_GRID_CHAIN_DONE"
