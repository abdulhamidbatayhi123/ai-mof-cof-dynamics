#!/bin/bash
# L6-v2: the primary hypothesis, 5-fold CV over 240 materials.
# Design frozen in PREREG_L6_v2.md, committed before this ran.
# Writes after every (fold, arm), so a shutdown loses at most one arm.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=5 MKL_NUM_THREADS=5
"$P" -u run_l6_v2.py --folds 5 --seeds 42 43 44 >> l6_v2.log 2>&1
echo "L6V2_EXIT=$?"; echo L6V2_DONE
