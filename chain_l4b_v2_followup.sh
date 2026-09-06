#!/bin/bash
# Everything L4b-v2 needs AFTER chain_l4b_v2.sh finishes. Run it only when
# chain_l4b_v2_outer.log ends with L4B_V2_DONE. Never concurrently with it.
#
# Three things, in order, and the first two are REQUIRED by the pre-registration
# rather than optional extras:
#
#   1. THE SWEEP EXTENSION (PREREG_L4b_v2.md §4.2). "A fixed weight whose optimum
#      sits on the sweep edge WITHOUT SATURATION: the sweep is extended one decade
#      in that direction before the verdict." On the time axis the fixed-weight
#      family is monotone in w and its best cell is w = 1e-4, the bottom of the
#      grid, at ~0.0146 against data_only's ~0.0131 -- a gap of order ten per cent,
#      so it is NOT saturated and the rule binds. `parse_arm` reads the weight out
#      of the arm name with float(), so w1e-5 needs no code change.
#      Six cells, roughly four hours.
#
#   2. THE ANALYSER WITH ITS MDEs. chain_l4b_v2.sh ends with `--no-mde`. Rule 7
#      admits no null without its minimum detectable effect, and A22 exists
#      because one was quoted without one and the design turned out to have 7 %
#      power. Q1, Q2 and Q3 can each return a null, so the verdict text may not be
#      written from the --no-mde output.
#
#   3. THE POST-HOC REFINEMENT SWEEP (defect B60). Q3 specifies one configuration
#      -- 300 Adam steps at lr 1e-4, all weights free -- and it degrades held-out
#      error about fivefold while also destroying the seen window. That is the
#      signature of a badly-configured optimiser, not of a refuted idea, and
#      "physics at inference does not help" drawn from one configuration is the
#      claim shape this rung was re-run to eliminate. The sweep is labelled
#      POST_HOC in its own output and does not touch the pre-registered verdict.
#
# The verdict text is written only after all three have run.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=6 MKL_NUM_THREADS=6

if ! grep -q L4B_V2_DONE chain_l4b_v2_outer.log 2>/dev/null; then
  echo "chain_l4b_v2.sh has not finished (no L4B_V2_DONE in chain_l4b_v2_outer.log)."
  echo "Refusing to start: two training chains must never run at once on this machine."
  exit 1
fi

"$P" -u run_l4b_v2.py --stage sweep --arms pi_fixed_w1e-5 --axes time material --threads 6 \
     >> l4b_v2.log 2>&1;                                        echo "EXT_EXIT=$?"
"$P" -u analyze_l4b_v2.py --mde-trials 200 \
     >  l4b_v2_analysis.log 2>&1;                               echo "AN_EXIT=$?"
"$P" -u refine_sweep_l4b_v2.py --scope all --threads 6 \
     >> l4b_v2_refine_sweep.log 2>&1;                           echo "RSA_EXIT=$?"
"$P" -u refine_sweep_l4b_v2.py --scope last --threads 6 \
     >> l4b_v2_refine_sweep.log 2>&1;                           echo "RSL_EXIT=$?"

# The figure and the manuscript both read the verdict file; regenerate them so the
# PENDING placeholder cannot survive the run that resolves it.
"$P" -u fig_ladder.py                                        && echo "FIG_EXIT=0"
"$P" -u paper/numbers.py                                     && echo "NUM_EXIT=0"
echo L4B_V2_FOLLOWUP_DONE
