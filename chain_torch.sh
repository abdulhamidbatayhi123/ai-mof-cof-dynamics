#!/bin/bash
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONIOENCODING=utf-8
# 1. finish the lr grid at p=64,128 (both families, lr=3e-3 tests above the old top edge)
"$P" -u run_l5.py --ps 64 128 --seeds 42 43 44 --lrs 3e-3 --steps 8000 \
     --budget 200000 --threads 4 --out results/l5_fill2.json > l5_fill2.log 2>&1
# 2. the DeepOKAN half of fill1 (its DeepONet half is already saved)
"$P" -u run_l5.py --ps 8 16 32 --seeds 42 43 44 --lrs 3e-3 2e-4 --families deepokan \
     --steps 8000 --budget 200000 --threads 4 --out results/l5_fill1b.json > l5_fill1b.log 2>&1
# 3. does the operator improve with material count too?
"$P" -u deeponet_lc.py > deeponet_lc.log 2>&1
echo CHAIN_TORCH_DONE
