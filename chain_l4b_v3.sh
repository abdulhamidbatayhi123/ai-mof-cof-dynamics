#!/bin/bash
# L4b re-run with the CORRECTED residual (B72; PREREG_L4b_v2.md §6 amendment A-B72).
# Same arms, axes, seeds and stages as chain_l4b_v2.sh + both edge extensions; new
# output files and a new checkpoint directory, so the withdrawn run stays intact.
# The residual gate must PASS first: a re-run of a physics rung against an unchecked
# residual would repeat the defect it exists to correct.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=6 MKL_NUM_THREADS=6
export L4B_CKPT_DIR="data/l4b_v3_ckpt"
LOG=l4b_v3.log

"$P" -u validate.py --only residual >> $LOG 2>&1
if ! grep -q "PASS  the training residual is the solver's equation" <(tail -40 $LOG); then
  echo "REFUSED: the residual gate did not pass; no L4b-v3 cell is trained" | tee -a $LOG
  exit 1
fi

PHYS="pi_fixed_w1e-6 pi_fixed_w1e-5 pi_fixed_w1e-4 pi_fixed_w1e-3 pi_fixed_w1e-2 pi_fixed_w1e-1 pi_fixed_w1 pi_gradnorm_t0.1 pi_gradnorm_t1.0 pi_gradnorm_t10 pi_ntk pi_sa"
OUT=results/l4b_v3_results.json
REF=results/l4b_v3_refine.json
rc=0
"$P" -u run_l4b_v2.py --stage sweep --arms data_only --axes time material --threads 6 --out $OUT >> $LOG 2>&1 || rc=1
"$P" -u refine_l4b_v2.py --sweep $OUT --out $REF --arms data_only --axes material time --threads 6 >> $LOG 2>&1 || rc=1
"$P" -u run_l4b_v2.py --stage sweep --arms $PHYS --axes time --threads 6 --out $OUT >> $LOG 2>&1 || rc=1
"$P" -u run_l4b_v2.py --stage sweep --arms $PHYS --axes material --threads 6 --out $OUT >> $LOG 2>&1 || rc=1
"$P" -u refine_l4b_v2.py --sweep $OUT --out $REF --axes material time --threads 6 >> $LOG 2>&1 || rc=1
"$P" -u run_l4b_v2.py --stage polish --axes time material --threads 6 --out $OUT >> $LOG 2>&1 || rc=1
"$P" -u analyze_l4b_v2.py --sweep $OUT --refine $REF --out results/l4b_v3_verdict.json >> l4b_v3_analysis.log 2>&1 || rc=1
"$P" -u analyze_l4b_selection.py --sweep $OUT --verdict results/l4b_v3_verdict.json --out results/l4b_v3_selection.json >> l4b_v3_analysis.log 2>&1 || rc=1
if [ $rc -eq 0 ]; then echo L4B_V3_DONE >> $LOG; else echo "L4B_V3_FAILED (a stage exited non-zero)" >> $LOG; exit 1; fi
