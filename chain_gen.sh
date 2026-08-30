#!/bin/bash
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export ADS_STORE_NZ=256 ADS_STORE_NT=256 ADS_CHECKPOINT_EVERY=50
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
# Retries so a resumed run continues automatically; each pass skips completed work.
for i in 1 2 3 4 5 6 7 8; do
  "$P" -u gen_parametric_dataset.py --materials 240 --conditions 17 --workers 7 \
       --seed 20260824 --out data/parametric_scale >> gen_scale.log 2>&1
  if [ -f data/parametric_scale/manifest.json ]; then echo GEN_COMPLETE; break; fi
  echo "pass $i ended without a manifest; retrying" >> gen_scale.log
  sleep 5
done
