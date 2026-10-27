#!/usr/bin/env bash
# The rest of amendment A1 after the pool-guard fix: two streams, resumable, then the analysis.
set -e
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
unset ADS_DATA_ROOT ADS_FOLDS_FILE DD_TAG
PY="${PY:-python}"
stream_a() {
  "$PY" dd_v3a1.py fwsens
  for s in 42 43 44; do "$PY" dd_v3a1.py fwfit --seed $s; done
  "$PY" dd_v3.py deeponet --data v2 --p 16 --seed 42 --control
  "$PY" dd_v3.py deeponet --data v2 --p 16 --seed 44
}
stream_b() {
  "$PY" dd_v3a1.py coarse90 --data v3
  "$PY" dd_v3a1.py hgb90 --data v2
  "$PY" dd_v3a1.py hgb90 --data v3
  "$PY" dd_v3.py deeponet --data v2 --p 16 --seed 42
  "$PY" dd_v3.py deeponet --data v2 --p 8 --seed 42
  "$PY" dd_v3.py deeponet --data v2 --p 128 --seed 42
  "$PY" dd_v3.py deeponet --data v2 --p 16 --seed 43
}
stream_a > dd_v3a1_restA.log 2>&1 & A=$!
stream_b > dd_v3a1_restB.log 2>&1 & B=$!
ea=0; eb=0; wait $A || ea=$?; wait $B || eb=$?
echo "streams exited: A=$ea B=$eb"
"$PY" dd_v3a1.py analyse > dd_v3a1_analyse.log 2>&1
echo "== $(date) amendment A1 done"
