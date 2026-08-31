#!/bin/bash
# The FNO arm. Lanthaler et al. (ICLR 2023, VERIFIED) prove linear-reconstruction
# operators are lower-bounded on advection-dominated PDEs and that FNO escapes.
# L5 tested only DeepONet and DeepOKAN, both linear-reconstruction, so "the
# operator rung is eliminated" is not defensible until this runs (defect B33).
#
# Pre-registered in run_l5_fno.py's docstring BEFORE running:
#   plateau near ~0.028  -> the wall is a property of the PROBLEM, claim strengthens
#   breaks the plateau   -> L5 narrows honestly to linear-reconstruction operators
# Both outcomes publishable; the current state is not.
#
# 3 modes x 2 lrs x 3 seeds = 18 runs at ~1.8 h each.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=3 MKL_NUM_THREADS=3
"$P" -u run_l5_fno.py --modes 4 8 16 --lrs 3e-3 1e-3 --seeds 42 43 44 \
     --steps 8000 --budget 200000 --threads 3 \
     --out results/l5_fno.json > l5_fno.log 2>&1
echo "FNO_EXIT=$?"; echo FNO_DONE
