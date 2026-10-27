#!/usr/bin/env bash
# Stream B of run_dd_v3a1.sh, restarted after the pool-worker guard fix (resumable).
set -e
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
unset ADS_DATA_ROOT ADS_FOLDS_FILE DD_TAG
PY="${PY:-python}"
"$PY" dd_v3a1.py coarse90 --data v3
"$PY" dd_v3a1.py hgb90 --data v2
"$PY" dd_v3a1.py hgb90 --data v3
"$PY" dd_v3.py deeponet --data v2 --p 16 --seed 42
"$PY" dd_v3.py deeponet --data v2 --p 8 --seed 42
"$PY" dd_v3.py deeponet --data v2 --p 128 --seed 42
"$PY" dd_v3.py deeponet --data v2 --p 16 --seed 43
"$PY" dd_v3.py deeponet --data v2 --p 16 --seed 44
echo "== $(date) stream B done"
