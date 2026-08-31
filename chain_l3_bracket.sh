#!/bin/bash
# Extend the L3 learning-rate grid until every selected optimum is INTERIOR.
#
# The B24 re-run (5 lrs: 1e-4 ... 1e-2) is clean -- every cell has a trained arm,
# and MLP beats both KAN families at all three budgets, 6 of 6 significant. But
# SIX of the nine selected arms sit on a grid EDGE:
#
#   cheby_kan picks lr = 1e-2, the TOP edge, at all three budgets
#   rbf_kan   picks lr = 1e-2, the TOP edge, at 200k
#   mlp       picks lr = 1e-4, the BOTTOM edge, at 50k and 800k
#
# That is the B14/B22/B23/A20 pattern again, and here it matters more than usual:
# L3's conclusion is "the MLP beats the KANs", and the KANs are the arm being
# argued AGAINST. If they are pinned at the top of the grid they are under-tuned,
# and protocol rule 4 (compare against the competitor's STRONGEST configuration)
# is not satisfied. This is the single most predictable referee attack on L3.
#
# Note the finding this already produced: the two families want learning rates an
# order of magnitude apart -- the KANs pinned high, the MLP pinned low, and
# mlp@200k DIVERGED at 1e-2 where cheby_kan@200k needs it. That is consistent with
# the KAN literature's central claim that KANs require different optimisation
# (Rigas et al., CMAME 452:118761, 2026; Kiyani et al., CMAME 446:118308, 2025),
# and it is worth reporting rather than smoothing over.
#
# Extending in BOTH directions: 3e-2 above, 3e-5 below.
# 3 families x 3 budgets x 2 lrs x 3 seeds = 54 runs.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=3 MKL_NUM_THREADS=3

"$P" -u run_l3.py \
     --seeds 42 43 44 \
     --budgets 50000 200000 800000 \
     --lrs 3e-2 3e-5 \
     --steps 12000 \
     --out results/l3_bracket.json > l3_bracket.log 2>&1
echo "L3_BRACKET_EXIT=$?"
echo L3_BRACKET_DONE
