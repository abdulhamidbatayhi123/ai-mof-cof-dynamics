#!/bin/bash
# L4b on dataset v2: the physics-weighting sweep, physics at inference, L-BFGS polish.
# Design frozen in PREREG_L4b_v2.md. Order per PREREG §3: data_only first (both axes),
# refinement of data_only, physics arms on the time axis, then the material axis,
# refinement of the best physics arm, then the polish. Every runner resumes.
# Never run concurrently with chain_v2_rungs.sh (shared 16 GB, one training job).
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=6 MKL_NUM_THREADS=6
PHYS="pi_fixed_w1e-4 pi_fixed_w1e-3 pi_fixed_w1e-2 pi_fixed_w1e-1 pi_fixed_w1 pi_gradnorm_t0.1 pi_gradnorm_t1.0 pi_gradnorm_t10 pi_ntk pi_sa"

"$P" -u run_l4b_v2.py --stage sweep --arms data_only --axes time material --threads 6 >> l4b_v2.log 2>&1; echo "D0_EXIT=$?"
"$P" -u refine_l4b_v2.py --arms data_only --axes material time --threads 6           >> l4b_v2_refine.log 2>&1; echo "R0_EXIT=$?"
"$P" -u run_l4b_v2.py --stage sweep --arms $PHYS --axes time --threads 6               >> l4b_v2.log 2>&1; echo "PT_EXIT=$?"
"$P" -u run_l4b_v2.py --stage sweep --arms $PHYS --axes material --threads 6           >> l4b_v2.log 2>&1; echo "PM_EXIT=$?"
"$P" -u refine_l4b_v2.py --axes material time --threads 6                              >> l4b_v2_refine.log 2>&1; echo "R1_EXIT=$?"
"$P" -u run_l4b_v2.py --stage polish --axes time material --threads 6                  >> l4b_v2.log 2>&1; echo "POL_EXIT=$?"
"$P" -u analyze_l4b_v2.py --no-mde                                                     >> l4b_v2_analysis.log 2>&1; echo "AN_EXIT=$?"
echo L4B_V2_DONE
