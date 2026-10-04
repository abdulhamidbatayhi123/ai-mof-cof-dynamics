#!/bin/bash
# AUTONOMOUS COMPUTE QUEUE. Runs the remaining work, in order, unattended.
#
# WHY THIS EXISTS. This project has lost roughly twenty-four hours in two
# incidents, both the same shape: a chain stopped -- once because the machine
# rebooted at 22:54 -- and nothing noticed until somebody happened to look. A stall
# is indistinguishable from progress unless something checks, and until now the
# only thing that checked was a person reading ./resume.sh.
#
# WHAT IT GUARANTEES
#   * ONE training job at a time. Both L4b runners load the whole results dict,
#     mutate it in memory and write_atomic the WHOLE thing, so two live writers
#     means last-writer-wins over every completed cell. Every job here waits for
#     the previous one to exit.
#   * Survives this terminal closing: launch it detached (see LAUNCH below).
#   * Survives a REBOOT: install_autorun.sh drops a one-line launcher in the user's
#     Startup folder, so the queue resumes at next logon. It removes itself when
#     the queue completes, so it cannot outlive its purpose.
#   * Survives a killed job: every runner in the queue is resumable cell-by-cell,
#     so a job that dies mid-way loses at most the one cell in flight. The queue
#     re-runs it and the runner skips what is already on disk.
#   * NEVER repeats completed work: each job declares a `done` test, and a job
#     whose test passes is skipped, not re-run.
#
# WHAT IT DOES NOT DO. It does not decide anything. Every job here is either
# pre-registered or a mechanical re-measurement of a result the paper already
# reports on a smaller design. Nothing in this queue chooses a hyperparameter,
# selects an arm, or writes a verdict.
#
# LAUNCH
#     nohup bash autorun.sh >> autorun_outer.log 2>&1 &
#     bash install_autorun.sh        # and survive reboots
#
# WATCH
#     tail -f autorun.log            # per-job progress
#     cat autorun_state.json         # heartbeat: what is running, since when
#     ./resume.sh                    # the project's own state report

cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics" || exit 1
P="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=6 MKL_NUM_THREADS=6

LOG=autorun.log
STATE=autorun_state.json
LOCK=autorun.lock

now() { date '+%Y-%m-%d %H:%M:%S'; }
say() { echo "[$(now)] $*" | tee -a "$LOG"; }

# ---------------------------------------------------------------- single instance
# Two copies of this queue would be exactly the disaster the queue exists to
# prevent. The lock carries a PID and is ignored if that process is gone, so a
# hard kill or a power cut cannot wedge the queue permanently.
if [ -f "$LOCK" ]; then
  OLD=$(cat "$LOCK" 2>/dev/null)
  if [ -n "$OLD" ] && ps -p "$OLD" >/dev/null 2>&1; then
    say "autorun already running as PID $OLD; this instance exits."
    exit 0
  fi
  say "stale lock from PID $OLD (not running); taking over."
fi
echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT

# ------------------------------------------------------- any training job alive?
runners_alive() {
  powershell -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -match 'run_l4b_v2|refine_l4b_v2|refine_sweep_l4b_v2|l5_bottleneck_v2|run_l5|run_l6_v2|run_l1_v2|run_l2_v2|l3_final_pair' }).Count" 2>/dev/null | tr -d '\r '
}

heartbeat() {   # $1 = job name, $2 = status
  "$P" - "$1" "$2" <<'PY' 2>/dev/null
import json, sys, time, os
job, status = sys.argv[1], sys.argv[2]
prev = {}
if os.path.exists("autorun_state.json"):
    try: prev = json.load(open("autorun_state.json"))
    except Exception: prev = {}
prev["job"] = job
prev["status"] = status
prev["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
prev.setdefault("history", []).append({"job": job, "status": status,
                                       "at": prev["updated"]})
prev["history"] = prev["history"][-200:]
json.dump(prev, open("autorun_state.json", "w"), indent=1)
PY
}

# ------------------------------------------------------------------- the queue
# Each job: NAME | DONE-TEST (shell, exit 0 == already done) | COMMAND
# The DONE-TEST is what stops completed work being repeated after a restart.
run_job() {
  local name="$1" donetest="$2" cmd="$3"
  if eval "$donetest" >/dev/null 2>&1; then
    say "SKIP  $name  (already complete)"
    return 0
  fi
  # never start beside a live training job
  local waited=0
  while [ "$(runners_alive)" != "0" ]; do
    if [ "$waited" -eq 0 ]; then
      say "WAIT  $name  -- a training job is alive; holding"
      heartbeat "$name" "waiting for a live runner"
    fi
    waited=$((waited + 1))
    sleep 120
  done
  # RE-TEST after the wait. The job we waited for may BE this job -- launched by
  # hand before the queue existed, or by the reboot launcher. Testing only before
  # the wait would hold until the follow-up finished and then start it again.
  if [ "$waited" -gt 0 ] && eval "$donetest" >/dev/null 2>&1; then
    say "SKIP  $name  (completed while we waited)"
    return 0
  fi
  say "START $name"
  heartbeat "$name" "running"
  local t0=$(date +%s)
  eval "$cmd"
  local rc=$?
  local dt=$(( $(date +%s) - t0 ))
  if [ $rc -eq 0 ]; then
    say "DONE  $name  (${dt}s)"
    heartbeat "$name" "done in ${dt}s"
  else
    say "FAIL  $name  exit=$rc after ${dt}s -- the queue CONTINUES; fix and re-run"
    heartbeat "$name" "FAILED exit=$rc after ${dt}s"
  fi
  return 0
}

say "=============================================================="
say "autorun starting (PID $$)"
say "=============================================================="

# --- 1. the L4b-v2 follow-up (pre-registered; may already be running) --------
# If it is alive, run_job's wait loop holds until it exits and the done-test then
# skips it. If a reboot killed it, this restarts it and every runner inside
# resumes cell-by-cell.
run_job "l4b-v2 follow-up (PREREG 4.2 extension, MDEs, B60 post-hoc)" \
  'grep -q L4B_V2_FOLLOWUP_DONE chain_l4b_v2_followup_outer.log 2>/dev/null' \
  'bash chain_l4b_v2_followup.sh >> chain_l4b_v2_followup_outer.log 2>&1'

# --- 1b. second PREREG 4.2 extension: w1e-6 on the material axis ------------
# Added 2026-09-27 AFTER job 1 (only bytes after the live read position changed).
# w1e-5 made the material verdict "physics helps" but sits on the sweep edge,
# unsaturated -- the rule says extend before the verdict. The chain prints its
# marker only if every stage exits 0. ~8-10 h.
run_job "l4b-v2 second extension (w1e-6, material axis)"   'grep -q L4B_V2_EXT2_DONE chain_l4b_v2_ext2_outer.log 2>/dev/null'   'bash chain_l4b_v2_ext2.sh >> chain_l4b_v2_ext2_outer.log 2>&1'

# --- 2. L5's mechanism table on v2 -------------------------------------------
# The cheapest experiment that most reduces the paper's risk (audit_risk.md):
# moves the load-bearing "the coefficient map is what binds" table from 12
# clusters and one seed to 240 clusters and three seeds. ~1-2 h.
run_job "l5_bottleneck on v2 (240 materials, 5 folds, 3 seeds)" \
  '"$P" -c "
import json,sys
d=json.load(open(\"results/l5_bottleneck_v2.json\"))
sys.exit(0 if len(d.get(\"cells\",{}))>=75 and \"summary\" in d else 1)"' \
  '"$P" -u l5_bottleneck_v2.py >> l5_bottleneck_v2.log 2>&1'

# --- 2b. close L5's DeepONet learning-rate bracket (rule 4) -------------------
# analyze_l5_merged.py flags deeponet p=8 and p=16 UNBRACKETED: best lr 1e-2 is the
# top of the grid and still moving 4.3 / 5.7 %. DeepONet is the arm the FNO is
# said to beat, so an under-tuned DeepONet would inflate that result. One more
# rate up, three seeds, same budget and steps as l5_onet_hi. ~1.5 h. Added
# 2026-09-25, AFTER job 2 so the bytes bash has already read are unchanged.
run_job "L5 DeepONet bracket at 3e-2 (p=8,16)"   '"$P" -c "
import json,sys
d=json.load(open(\"results/l5_onet_3e2.json\"))
n=sum(1 for a in d[\"arms\"] for s in a[\"seeds\"].values())
sys.exit(0 if n>=6 else 1)"'   '"$P" -u run_l5.py --ps 8 16 --seeds 42 43 44 --lrs 3e-2 --families deeponet --steps 8000 --budget 200000 --threads 6 --out results/l5_onet_3e2.json >> l5_onet_3e2.log 2>&1 && "$P" -u analyze_l5_merged.py >> l5_onet_3e2.log 2>&1 && "$P" -u analyze_l5_fno.py >> l5_onet_3e2.log 2>&1 && "$P" -u fig_operators.py >> l5_onet_3e2.log 2>&1'

# --- 2c. B71: re-derive the L3 best-KAN-vs-MLP interval (no script had saved it) --
# Re-runs audit_l3.py's two configurations with per-sample errors kept. ~2-4 h.
run_job "L3 final pair re-run (B71)" 'grep -q L3_FINAL_PAIR_DONE l3_final_pair.log 2>/dev/null' '"$P" -u l3_final_pair.py >> l3_final_pair.log 2>&1'

# --- 2d-2f. L5 on v2 (PREREG_L5_v2.md): step-budget arm first, then the sweep ---
run_job "L5-v2 step arm p=8 (lr 1e-2)" 'grep -q L5V2_STEPS_P8_DONE l5_v2_steps.log 2>/dev/null' '"$P" -u run_l5_v2.py --arm steps --steps-ps 8 --steps-lr 1e-2 --steps-fold 0 --families deeponet --threads 6 --out results/l5_v2_steps_p8.json >> l5_v2_steps.log 2>&1 && echo L5V2_STEPS_P8_DONE >> l5_v2_steps.log'
run_job "L5-v2 step arm p=128 (lr 3e-3)" 'grep -q L5V2_STEPS_P128_DONE l5_v2_steps.log 2>/dev/null' '"$P" -u run_l5_v2.py --arm steps --steps-ps 128 --steps-lr 3e-3 --steps-fold 0 --families deeponet --threads 6 --out results/l5_v2_steps_p128.json >> l5_v2_steps.log 2>&1 && echo L5V2_STEPS_P128_DONE >> l5_v2_steps.log'
run_job "L5-v2 sweep (DeepONet, 5 folds, 240 materials)" 'grep -q L5V2_SWEEP_DONE l5_v2.log 2>/dev/null' '"$P" -u run_l5_v2.py --families deeponet --threads 6 >> l5_v2.log 2>&1 && echo L5V2_SWEEP_DONE >> l5_v2.log'

# --- 3. regenerate everything the above feeds --------------------------------
run_job "figures + numbers + build gate" \
  'false' \
  '"$P" -u fig_ladder.py >> autorun.log 2>&1; "$P" -u paper/numbers.py >> autorun.log 2>&1; "$P" -u build_paper.py >> autorun.log 2>&1'

# referee minor 11: measure the per-query cost r the cost section only bounds (idle machine, minutes)
run_job "cost accounting: time the surrogate query (r)" 'grep -q COST_TIME_DONE cost_time.log 2>/dev/null' '"$P" -u cost_accounting.py --time >> cost_time.log 2>&1 && echo COST_TIME_DONE >> cost_time.log'

# PREREG_L5_v2 A2: the frozen step rule fired; the verdict sweep is re-run at 24k steps
run_job "L5-v2 sweep at 24k steps (A2)" 'grep -q L5V2_SWEEP24K_DONE l5_v2_24k.log 2>/dev/null' '"$P" -u run_l5_v2.py --families deeponet --steps 24000 --lrs 1e-3 3e-3 1e-2 3e-2 --threads 6 --out results/l5_v2_results_24k.json >> l5_v2_24k.log 2>&1 && echo L5V2_SWEEP24K_DONE >> l5_v2_24k.log'
run_job "L5-v2 analysis (24k)" 'grep -q L5V2_ANALYSIS24K_DONE l5_v2_analysis_24k.log 2>/dev/null' '"$P" -u analyze_l5_v2.py --res results/l5_v2_results_24k.json --out results/l5_v2_verdict_24k.json > l5_v2_analysis_24k.log 2>&1 && echo L5V2_ANALYSIS24K_DONE >> l5_v2_analysis_24k.log'

# B72 / PREREG_L4b_v2 A-B72: L4b re-run with the corrected residual (~2-2.5 days)
run_job "L4b re-run, corrected residual (B72)" 'grep -q L4B_V3_DONE l4b_v3.log 2>/dev/null' 'bash chain_l4b_v3.sh >> chain_l4b_v3_outer.log 2>&1'

# PREREG_P2 §3 pre-freeze: ODR-BINDy port, five noise seeds (~3.5 h, light RAM)
run_job "P2 ODR-BINDy five-seed check" 'grep -q ODR_SEEDS_DONE p2_odr_seeds.log 2>/dev/null' '"$P" -u p2_odr_seeds.py >> p2_odr_seeds.log 2>&1'

# PREREG_BASELINES (referee M11a-c), in the declared order, one at a time
run_job "B-FIT fitted Klinkenberg" 'grep -q BFIT_DONE bfit.log 2>/dev/null' '"$P" -u fitted_classical.py >> bfit.log 2>&1'
run_job "B-GP Gaussian process on POD (5 folds)" 'grep -q BGP_RUN_DONE bgp.log 2>/dev/null' '"$P" -u run_l1_v2.py --design folds --arms gp --out results/l1_v2_gp.json >> bgp.log 2>&1 && echo BGP_RUN_DONE >> bgp.log'
run_job "B-GP analysis" 'grep -q BGP_ANALYSIS_DONE bgp_analysis.log 2>/dev/null' '"$P" -u analyze_gp_baseline.py >> bgp_analysis.log 2>&1'
run_job "B-COARSE coarse-grid solver" 'grep -q BCOARSE_DONE bcoarse.log 2>/dev/null' '"$P" -u coarse_solver_baseline.py >> bcoarse.log 2>&1'

# PREREG_P2 §3 M7 inclusion gate: PySR known-answer pilot (Julia precompile needs free RAM)
run_job "P2 M7 PySR pilot (inclusion gate)" 'grep -q P2_PILOT_M7_DONE p2_pilot_m7.log 2>/dev/null' '.venv/Scripts/python.exe -u p2_pilot_m7.py >> p2_pilot_m7.log 2>&1'

say "=============================================================="
say "AUTORUN_QUEUE_DONE"
say "=============================================================="
heartbeat "queue" "AUTORUN_QUEUE_DONE"

# The reboot launcher has done its job; take it out of Startup so it cannot
# outlive the work. install_autorun.sh can always put it back.
bash uninstall_autorun.sh >> "$LOG" 2>&1 || true
