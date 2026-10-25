#!/usr/bin/env bash
# PREREG_DD_V3 amendment A1, two parallel streams. Resumable: re-running skips finished cells.
set -e
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
unset ADS_DATA_ROOT ADS_FOLDS_FILE DD_TAG
PY="${PY:-python}"

stream_a() {
  "$PY" dd_v3.py deeponet --data v3 --p 16 --seed 42
  "$PY" dd_v3.py deeponet --data v3 --p 8 --seed 42
  "$PY" dd_v3.py deeponet --data v3 --p 128 --seed 42
  "$PY" dd_v3.py deeponet --data v3 --p 16 --seed 43
  "$PY" dd_v3a1.py fwsens
  for s in 42 43 44; do "$PY" dd_v3a1.py fwfit --seed $s; done
  "$PY" dd_v3.py deeponet --data v2 --p 16 --seed 42 --control
}
stream_b() {
  "$PY" dd_v3a1.py coarse90 --data v2
  "$PY" dd_v3a1.py coarse90 --data v3
  "$PY" dd_v3a1.py hgb90 --data v2
  "$PY" dd_v3a1.py hgb90 --data v3
  "$PY" dd_v3.py deeponet --data v2 --p 16 --seed 42
  "$PY" dd_v3.py deeponet --data v2 --p 8 --seed 42
  "$PY" dd_v3.py deeponet --data v2 --p 128 --seed 42
  "$PY" dd_v3.py deeponet --data v2 --p 16 --seed 43
  "$PY" dd_v3.py deeponet --data v2 --p 16 --seed 44
}
stream_a > dd_v3a1_streamA.log 2>&1 &
A=$!
stream_b > dd_v3a1_streamB.log 2>&1 &
B=$!
wait $A; wait $B
"$PY" dd_v3a1.py analyse > dd_v3a1_analyse.log 2>&1
echo "== $(date) amendment A1 done"
