#!/bin/bash
# Generate the design-v2 parametric dataset. This is the long pole: every rung
# re-runs on it.
#
# What v2 changes, and why (full rationale in gen_parametric_dataset.py):
#   * k_LDF is DERIVED from a sampled particle diameter through Glueckauf,
#     instead of being sampled independently of d_p. The legacy dataset's k_LDF
#     was a median 10x (p95 37x) faster than a 2 mm pellet can physically
#     support, and the consequence was Da median 626 with only 1.1 % of samples
#     in the kinetically-informative band -- which is why L6 could not test H1.
#     Measured on the v2 probe: Da median 31, min 4.4, 59 % in the 5-60 band.
#   * scrambled Sobol instead of independent uniforms (L2-star discrepancy
#     0.0930 -> 0.0191 at the same cost).
#
# 240 materials x 17 conditions = 4080 runs, 5x the material count of the legacy
# dataset. The learning curve measured 1.82x improvement from 12 -> 48 training
# materials WITH NO SATURATION, so material count is the axis that was still
# paying and this is the experiment that finds where it stops.
#
# Stored at 256x256: the audit measured the real front to be ~372 cells wide at
# 512 z (the protocol's 1.4-cell figure was the isothermal estimate and wrong by
# 26x, defect B31), so 256 is ample and halves the disk.
#
# workers=4, not 7: this machine is also running unrelated jobs.
# The generator now runs in chunks with a fresh pool each, and retries a broken
# pool, so the WinError 87 that killed the previous 4080-run attempt is handled
# in-process rather than by relaunching from bash.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export ADS_STORE_NZ=256 ADS_STORE_NT=256 ADS_CHECKPOINT_EVERY=50
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1

"$P" -u gen_parametric_dataset.py \
     --design v2 \
     --materials 240 --conditions 17 \
     --workers 4 \
     --seed 20260830 \
     --out data/parametric_v2 >> gen_v2.log 2>&1
echo "GEN_V2_EXIT=$?"
if [ -f data/parametric_v2/manifest.json ]; then echo GEN_V2_COMPLETE; else echo GEN_V2_INCOMPLETE; fi
