#!/bin/bash
# Close the L5 grid where the refined guard says it actually matters.
#
# The guard now separates "on the edge and still moving" from "on the edge but
# saturated". Applied to the merged L5 sweep:
#
#   deepokan p=8    top edge 1e-3, STILL MOVING 30.2%%   <-- under-tuned
#   deepokan p=16   top edge 1e-3, STILL MOVING 35.4%%   <-- under-tuned
#   deeponet p=16   top edge 3e-3, still moving  4.5%%
#   deeponet p=64   top edge 3e-3, still moving  4.2%%
#   deeponet p=128  top edge 3e-3, still moving  7.7%%
#   deeponet p=8    top edge 3e-3, SATURATED     1.9%%   -- benign
#   deeponet p=32   top edge 3e-3, SATURATED     0.2%%   -- benign
#
# DeepOKAN being 30-35%% off matters more than the rest combined. Its best is
# currently 0.0357 against DeepONet's 0.0275; a 30%% improvement would put it at
# ~0.025 and FLIP the family verdict. Reporting "no difference detected" while
# holding evidence that one arm is a third under-tuned would be indefensible, and
# it is the arm being argued against -- protocol rule 4 exactly.
#
# deepokan gets 3e-3 AND 1e-2 (it has never been run above 1e-3);
# deeponet gets 1e-2. Two processes, 3 threads each.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8

"$P" -u run_l5.py --ps 8 16 32 64 128 --seeds 42 43 44 --lrs 3e-3 1e-2 \
     --families deepokan --steps 8000 --budget 200000 --threads 3 \
     --out results/l5_okan_hi.json > l5_okan_hi.log 2>&1 &
A=$!
"$P" -u run_l5.py --ps 8 16 32 64 128 --seeds 42 43 44 --lrs 1e-2 \
     --families deeponet --steps 8000 --budget 200000 --threads 3 \
     --out results/l5_onet_hi.json > l5_onet_hi.log 2>&1 &
B=$!
wait $A; echo "deepokan exit $?"
wait $B; echo "deeponet exit $?"
echo L5_BRACKET2_DONE
