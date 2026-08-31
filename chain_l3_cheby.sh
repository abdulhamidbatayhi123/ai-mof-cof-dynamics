#!/bin/bash
# Final L3 bracketing: cheby_kan at 1e-1, budgets 50k and 200k only.
#
# After merging the 5-point and bracket sweeps (7 lrs, 3e-5 .. 3e-2), the tuning
# envelope shows only TWO cells are still improving at the grid edge:
#   cheby_kan@50k   1e-2:0.1189 -> 3e-2:0.1063   (11.9%% better, still moving)
#   cheby_kan@200k  1e-2:0.1212 -> 3e-2:0.1120   ( 8.2%% better, still moving)
# Every other selected arm is either interior or demonstrably flat:
#   rbf_kan turns over on BOTH sides at all three budgets  -> interior
#   cheby_kan@800k turns over (3e-2:0.1206 worse than 1e-2:0.1028) -> interior
#   mlp sits at the bottom edge but is SATURATED there: 0.0564 vs 0.0566 across a
#     3x lr change (0.1-0.4%%). An edge selection only matters if the metric is
#     still changing at it, and the MLP's is not.
# 2 budgets x 1 lr x 3 seeds = 6 runs.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
"$P" -u run_l3.py --seeds 42 43 44 --budgets 50000 200000 \
     --lrs 1e-1 --steps 12000 --out results/l3_cheby_1e-1.json > l3_cheby.log 2>&1
echo "L3_CHEBY_EXIT=$?"; echo L3_CHEBY_DONE
