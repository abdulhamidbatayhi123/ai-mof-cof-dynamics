#!/usr/bin/env bash
# Remaining amendment A1 cells after the session restart of 2026-10-27 (resumable: finished cells skipped).
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
unset ADS_DATA_ROOT ADS_FOLDS_FILE DD_TAG
PY="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
stream_a() {
  "$PY" dd_v3a1.py fwfit --seed 44
  "$PY" dd_v3.py deeponet --data v2 --p 16 --seed 42 --control
  "$PY" dd_v3.py deeponet --data v2 --p 16 --seed 44
  "$PY" dd_v3.py deeponet --data v2 --p 16 --seed 43
}
stream_b() {
  "$PY" dd_v3.py deeponet --data v2 --p 16 --seed 42
  "$PY" dd_v3.py deeponet --data v2 --p 8 --seed 42
  "$PY" dd_v3.py deeponet --data v2 --p 128 --seed 42
}
stream_a > dd_v3a1_finalA.log 2>&1 & A=$!
stream_b > dd_v3a1_finalB.log 2>&1 & B=$!
wait $A; wait $B
"$PY" dd_v3a1.py analyse > dd_v3a1_analyse.log 2>&1
echo "== $(date) amendment A1 done" >> dd_v3a1_final_chain.log
