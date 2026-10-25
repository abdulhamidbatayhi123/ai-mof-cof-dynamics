#!/usr/bin/env bash
# PREREG_DD_V3 chain (frozen 24e72e6). Waits for the v3 dataset, then runs every step in order.
# Each step is resumable; re-running the script skips finished work.
set -e
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY="${PY:-C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe}"
V3="ADS_DATA_ROOT=data/parametric_v3 ADS_FOLDS_FILE=results/v3_folds.json DD_TAG=_v3"

until [ -f data/parametric_v3/manifest.json ]; do sleep 60; done
echo "== $(date) v3 dataset ready"

"$PY" dd_v3.py folds
env $V3 "$PY" dd_screening_frameworks.py coarse                         # V3: every v3 sample, N_z = 50
env $V3 "$PY" l5_mapterm_v2.py --seeds 42 --out results/l5_mapterm_v3.json   # V1: eq. (split)
"$PY" dd_v3.py deeponet --data v3 --p 16 --seed 42                       # V2 (+ V4 arm 1)
"$PY" dd_v3.py hgb                                                       # V4 arm 2 + B1 layout
env $V3 "$PY" dd_screening_frameworks.py analyse                         # V4 verdicts (v3)
"$PY" dd_v3.py deeponet --data v3 --p 8 --seed 42
"$PY" dd_v3.py deeponet --data v3 --p 128 --seed 42
"$PY" dd_v3.py frameworks                                                # V6
env $V3 "$PY" dd_screening_frameworks.py analyse                         # V4 + V6 verdicts (v3)
"$PY" dd_v3.py deeponet --data v2 --p 8 --seed 42
"$PY" dd_v3.py deeponet --data v2 --p 128 --seed 42
"$PY" dd_v3.py deeponet --data v3 --p 16 --seed 43
"$PY" dd_v3.py analyse
echo "== $(date) PREREG_DD_V3 chain done"
