#!/bin/bash
# Everything L4b-v2 needs AFTER chain_l4b_v2.sh finishes. Never concurrently with it.
#
# BUDGET: roughly 20 hours, not the four the first version of this header claimed.
# The extension is ~6 cells at a measured ~2300 s each (~4 h); the post-hoc
# refinement sweep is 24 cells of comparable work (~15 h); refine and polish are
# no-ops unless best_pi moved, and several hours if it did.
#
# Five things, in this ORDER, and the order is load-bearing:
#
#   1. THE SWEEP EXTENSION (PREREG_L4b_v2.md §4.2). "A fixed weight whose optimum
#      sits on the sweep edge WITHOUT SATURATION: the sweep is extended one decade
#      in that direction before the verdict." Measured, not assumed: on the TIME
#      axis w=1e-4 (0.0146) is significantly worse than data_only (0.0131), CI
#      [-0.00202, -0.00106], so the family has NOT saturated at the bottom edge
#      and the rule binds. On the MATERIAL axis the same cell's CI spans zero, so
#      it HAS saturated and the rule does not bind there -- we run it on both
#      anyway, because declining an experiment on the strength of a re-reading of
#      the edge rule made after seeing the data is exactly what this project does
#      not do. `parse_arm` reads the weight with float(), so w1e-5 needs no code
#      change beyond being in ARMS.
#
#   2+3. REFINE AND POLISH, RE-RUN. Both were computed against whichever arm was
#      best when they ran -- pi_fixed_w1e-4. If w=1e-5 takes the minimum, the
#      analyser's best_pi moves and Q3's control and Q4's polish would then
#      describe a DIFFERENT arm from the one the verdict is about; the flip test
#      would take `before` from the new arm and `after` from the old one. Both
#      resume per (axis, arm, seed), so these are no-ops if best_pi is unchanged
#      and train exactly the missing cells if it moved. The analyser now REFUSES
#      to report Q4 across two different arms rather than silently reporting it,
#      so skipping these would cost the Q4 result, not corrupt it.
#
#   4. THE ANALYSER WITH ITS MDEs. chain_l4b_v2.sh ends with `--no-mde`. Rule 7
#      admits no null without its minimum detectable effect, and A22 exists
#      because one was quoted without one and the design turned out to have 7 %
#      power. Q1, Q2 and Q3 can each return a null -- and Q2 DID: "no difference
#      between the data-only twin and the best physics arm" -- so the verdict text
#      may not be written from the --no-mde output.
#
#   5. THE POST-HOC REFINEMENT SWEEP (defect B60). Q3 specifies one configuration
#      -- 300 Adam steps at lr 1e-4, all weights free -- and it degrades held-out
#      error four- to sevenfold while also destroying the seen window (+402 % to
#      +662 %). That is the signature of a badly-configured optimiser, not of a
#      refuted idea, and "physics at inference does not help" drawn from one
#      configuration is the claim shape this rung was re-run to eliminate. The
#      sweep is labelled POST_HOC in its own output and does not touch the
#      pre-registered verdict. NOTE it covers the MATERIAL axis only.
#
# NOT DONE HERE, and it is not optional: the manuscript's L4 section is prose, not
# a macro, so regenerating numbers.tex cannot resolve "[SECTION PENDING]". Rewrite
# paper/manuscript.tex §5.4 by hand after this lands.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=6 MKL_NUM_THREADS=6

# --- interlock -------------------------------------------------------------
# The log marker alone is not enough: chain_l4b_v2.sh echoes L4B_V2_DONE
# unconditionally (no `set -e`), resume.sh appends to that log, and once the
# marker lands it is permanent. Both runners load the whole results dict, mutate
# it in memory and write_atomic the WHOLE thing, so two live processes means
# last-writer-wins over all 66 cells. Ask Windows what is actually running.
if ! grep -q L4B_V2_DONE chain_l4b_v2_outer.log 2>/dev/null; then
  echo "chain_l4b_v2.sh has not finished (no L4B_V2_DONE in chain_l4b_v2_outer.log). Refusing."
  exit 1
fi
ALIVE=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -match 'run_l4b_v2|refine_l4b_v2|refine_sweep_l4b_v2' }).Count" 2>/dev/null | tr -d '\r ')
if [ "${ALIVE:-0}" -ne 0 ]; then
  echo "$ALIVE L4b runner process(es) already alive. Refusing: two writers to"
  echo "results/l4b_v2_results.json means last-writer-wins over all 66 cells."
  exit 1
fi

# Every step records its own exit code. `&& echo EXIT=0` masks a failure: the
# marker simply does not print and the chain carries on to announce DONE.
"$P" -u run_l4b_v2.py --stage sweep --arms pi_fixed_w1e-5 --axes time material --threads 6 \
     >> l4b_v2.log 2>&1;                                        echo "EXT_EXIT=$?"
"$P" -u refine_l4b_v2.py --axes material time --threads 6 \
     >> l4b_v2_refine.log 2>&1;                                 echo "REF_EXIT=$?"
"$P" -u run_l4b_v2.py --stage polish --axes time material --threads 6 \
     >> l4b_v2.log 2>&1;                                        echo "POL_EXIT=$?"
# Append, never truncate: the --no-mde analysis written by chain_l4b_v2.sh is the
# only record of what the verdict looked like BEFORE the sweep was extended, and
# that before/after is the whole point of the PREREG §4.2 extension rule.
"$P" -u analyze_l4b_v2.py --mde-trials 200 \
     >> l4b_v2_analysis.log 2>&1;                               echo "AN_EXIT=$?"
"$P" -u refine_sweep_l4b_v2.py --scope all --threads 6 \
     >> l4b_v2_refine_sweep.log 2>&1;                           echo "RSA_EXIT=$?"
"$P" -u refine_sweep_l4b_v2.py --scope last --threads 6 \
     >> l4b_v2_refine_sweep.log 2>&1;                           echo "RSL_EXIT=$?"

"$P" -u fig_ladder.py                                       >> l4b_v2_analysis.log 2>&1; echo "FIG_EXIT=$?"
"$P" -u paper/numbers.py                                    >> l4b_v2_analysis.log 2>&1; echo "NUM_EXIT=$?"
echo L4B_V2_FOLLOWUP_DONE
