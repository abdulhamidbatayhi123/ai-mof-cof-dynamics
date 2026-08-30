#!/bin/bash
# Close the L5 learning-rate grid so no selected optimum sits on a boundary.
#
# analyze_l5_merged.py's guard reports 7 of 10 selected arms UNBRACKETED:
#   deeponet p=8,16,32,64,128 all pick lr=3e-3, the top of the grid
#   deepokan p=8,16           pick lr=1e-3, the top of ITS grid
# A search whose optimum is on the edge is not a search (defects B14/B22/B23,
# and this is the fifth recurrence). Until the selected lr is interior, every
# "X is eliminated" verdict that depends on the grid is contestable.
#
# Two jobs, run concurrently at 3 threads each on a 12-core box:
#   A. lr = 1e-2 for BOTH families at every p           -> l5_lr1e-2.json
#   B. the DeepOKAN half of fill1 that never completed  -> l5_fill1b.json
#      (l5_fill1b.log is 0 bytes; the chain died. deepokan was never run at
#       3e-3 for p=8,16,32, so the two families' grids are asymmetric.)
#
# Neither job touches an existing results file. analyze_l5_merged.py picks both
# up automatically and refuses duplicate (family, p, lr) keys.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8

"$P" -u run_l5.py --ps 8 16 32 64 128 --seeds 42 43 44 --lrs 1e-2 \
     --steps 8000 --budget 200000 --threads 3 \
     --out results/l5_lr1e-2.json > l5_lr1e-2.log 2>&1 &
PID_A=$!

"$P" -u run_l5.py --ps 8 16 32 --seeds 42 43 44 --lrs 3e-3 2e-4 --families deepokan \
     --steps 8000 --budget 200000 --threads 3 \
     --out results/l5_fill1b.json > l5_fill1b.log 2>&1 &
PID_B=$!

wait $PID_A; echo "A (lr=1e-2, both families) exited $?"
wait $PID_B; echo "B (deepokan fill1b) exited $?"
echo L5_GRID_CLOSED
