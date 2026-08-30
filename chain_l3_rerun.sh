#!/bin/bash
# Re-run L3 after defect B24 (audit 2026-08-30).
#
# What was wrong with the original sweep:
#   * patience=400 steps with validation every 25 = 16 non-improving evaluations.
#     ALL 54 runs stopped between step 400 and 500 of a declared 6000, so the
#     cosine schedule (T_max=steps) never annealed and every arm was scored at
#     essentially its initial learning rate.
#   * 11 of 54 runs had best_step == 0 — the reported error was the RANDOM
#     INITIALISATION. Six were cheby_kan at the 200k budget at BOTH learning
#     rates, so the published 200k Chebyshev cell (0.1263) was untrained.
#   * The lr grid was {3e-3, 1e-3} and the best was 3e-3 — the top edge — for
#     rbf_kan at all three budgets. Unbracketed, so the KAN was under-tuned:
#     exactly the strawman the audit_l3 script exists to rule out.
#
# What changed (run_l3.py):
#   patience 400 -> 2000, min_steps=1000, and a hard RuntimeError if
#   best_step == 0. analyze_l3.assert_wellformed now refuses any file containing
#   such a run, so a never-trained number cannot reach a table again.
#
# The grid is widened to five learning rates spanning two decades so every
# family's optimum has a chance to be interior. steps raised to 12000 to give
# the KANs room to converge — the KAN literature's central rebuttal is that KANs
# optimise differently and need longer schedules, and at ~450 steps the original
# design could not distinguish "generalises worse" from "had not started".
#
# 3 families x 3 budgets x 5 lrs x 3 seeds = 135 runs.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=3 MKL_NUM_THREADS=3

"$P" -u run_l3.py \
     --seeds 42 43 44 \
     --budgets 50000 200000 800000 \
     --lrs 1e-2 3e-3 1e-3 3e-4 1e-4 \
     --steps 12000 \
     --out results/l3_results.json > l3_rerun_B24.log 2>&1
echo "L3_RERUN_EXIT=$?"
echo L3_RERUN_DONE
