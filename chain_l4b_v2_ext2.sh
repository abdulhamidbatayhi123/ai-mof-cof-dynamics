#!/bin/bash
# The SECOND PREREG_L4b_v2 §4.2 extension: pi_fixed_w1e-6 on the MATERIAL axis.
#
# WHY. With w1e-5 added (the first extension), the material-axis verdict became
# "PHYSICS HELPS once correctly weighted": w1e-5 at 0.02126 against the data-only
# twin's 0.02314, CI [0.00125, 0.00263]. But w1e-5 is again the BOTTOM EDGE of the
# fixed-weight sweep, and it is significantly better than the twin -- so it is not
# saturated -- and the analyser raises edge_warning. PREREG §4.2 says the sweep "is
# extended one decade in that direction BEFORE the verdict". The verdict therefore
# waits. The time axis ties the twin at w1e-5 (saturated), so the rule does not bind
# there and it is not re-run.
#
# DIFFERENCE FROM chain_l4b_v2_followup.sh: that chain printed its done-marker even
# when stages failed (a full disk killed four of them on 2026-09-26 and the marker
# logic could not tell). This one prints L4B_V2_EXT2_DONE only if EVERY stage exits 0,
# so the autorun done-test cannot skip a broken run.
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=6 MKL_NUM_THREADS=6

ALIVE=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -match 'run_l4b_v2|refine_l4b_v2|refine_sweep_l4b_v2' }).Count" 2>/dev/null | tr -d '\r ')
if [ "${ALIVE:-0}" -ne 0 ]; then
  echo "$ALIVE L4b runner process(es) already alive. Refusing: two writers to the results file."
  exit 1
fi

FAIL=0
step() {   # $1 = label, rest = command
  local label="$1"; shift
  "$@"
  local rc=$?
  echo "${label}_EXIT=$rc"
  [ $rc -ne 0 ] && FAIL=1
}

step EXT2  "$P" -u run_l4b_v2.py --stage sweep --arms pi_fixed_w1e-6 --axes material --threads 6 >> l4b_v2.log 2>&1
# best_pi may change, so Q3 and Q4 must describe the arm the analyser selects
step REF   "$P" -u refine_l4b_v2.py --axes material time --threads 6 >> l4b_v2_refine.log 2>&1
step POL   "$P" -u run_l4b_v2.py --stage polish --axes time material --threads 6 >> l4b_v2.log 2>&1
step AN    "$P" -u analyze_l4b_v2.py --mde-trials 200 >> l4b_v2_analysis.log 2>&1
step RSA   "$P" -u refine_sweep_l4b_v2.py --scope all --threads 6 >> l4b_v2_refine_sweep.log 2>&1
step RSL   "$P" -u refine_sweep_l4b_v2.py --scope last --threads 6 >> l4b_v2_refine_sweep.log 2>&1
step FIG   "$P" -u fig_ladder.py >> l4b_v2_analysis.log 2>&1
step NUM   "$P" -u paper/numbers.py >> l4b_v2_analysis.log 2>&1

if [ $FAIL -eq 0 ]; then
  echo L4B_V2_EXT2_DONE
else
  echo "L4B_V2_EXT2_INCOMPLETE -- at least one stage failed; the queue will re-run this chain"
  exit 1
fi
