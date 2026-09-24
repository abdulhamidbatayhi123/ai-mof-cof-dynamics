# followup

The follow-up chain does do all three pre-registered things — it extends w=1e-5 on BOTH axes (6 cells, ~4 h at the measured ~2300 s/cell), re-runs the analyser with MDEs, and runs the labelled POST_HOC refinement sweep — and it will not crash, will not retrain completed cells, and cannot lose the 66 sweep cells (the extension resumes cell-by-cell and write_atomic rewrites the whole dict; the sweep writes a different file). `parse_arm` handles `pi_fixed_w1e-5` correctly via `float()`, and the analyser does write `axes.{time,material}.verdict`, so paper/numbers.py's two dotted paths resolve. The damage is elsewhere and it is silent: `results/l4b_v2_verdict.json` is still declared PENDING in both paper/numbers.py and fig_ladder.py, so the moment the FIRST chain writes that file (a day before the follow-up starts) paper/numbers.py exits 1 and the manuscript stops building — and the follow-up's own `&& echo` masks that failure while still printing L4B_V2_FOLLOWUP_DONE.

## 1. [blocking] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\paper\numbers.py:43 (fires at 358-361)

**What.** PENDING still contains `"results/l4b_v2_verdict.json": "L4b-v2 is still running",` and resolve() treats a declared-PENDING file that EXISTS as a hard failure: `failures.append(f"{key}: {fname} is declared PENDING but EXISTS — remove it from PENDING and re-run")`, then `sys.exit(1)` at line 407 before numbers.tex is written.

**Why.** chain_l4b_v2.sh:18 (`analyze_l4b_v2.py --no-mde`) creates results/l4b_v2_verdict.json at the end of the FIRST chain, so paper/numbers.py starts failing a day before the follow-up runs. build_paper.py:171-173 exits 1 on that return code, so the manuscript cannot be built at all. Worse, chain_l4b_v2_followup.sh:54 invokes it as `"$P" -u paper/numbers.py && echo "NUM_EXIT=0"` with no `set -e`: the failure prints no NUM_EXIT marker, numbers.tex keeps `\newcommand{\nLfourbVerdictMaterial}{\textbf{[PENDING]}}` (paper/numbers.tex:183-184), and line 55 still prints L4B_V2_FOLLOWUP_DONE. The script's own comment at line 52 — "the PENDING placeholder cannot survive the run that resolves it" — is exactly inverted.

**Fix.** Delete the `"results/l4b_v2_verdict.json": ...` entry from PENDING in paper/numbers.py (leaving `PENDING = {}`) as part of the same commit that lands the verdict, and change chain_l4b_v2_followup.sh:53-54 to `; echo "FIG_EXIT=$?"` / `; echo "NUM_EXIT=$?"` so a non-zero exit is recorded instead of swallowed by `&&`.

## 2. [blocking] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\fig_ladder.py:140

**What.** `c = ax.get("best_pi_vs_data_only")` reads a key that analyze_l4b_v2.py never writes. The analyser writes `"comparisons_vs_data_only": comps` (a dict keyed by arm name) and `"best_pi": best_pi` at analyze_l4b_v2.py:115-117. Grep confirms `best_pi_vs_data_only` appears in exactly one place in the repo — this line.

**Why.** `c` is always None, so build_rows() takes the else branch at fig_ladder.py:150-155 and appends a row with `verdict="IN FLIGHT"`, note "the sweep is running, no verdict yet", and `e=None`. Figure 1 will draw the L4b rung as an in-flight tick mark forever, with no error and no CI, after the run has landed. It does not crash (panel_ladder handles e=None at line 213-217), so nothing in the follow-up reports it.

**Fix.** Either change fig_ladder.py:140 to `c = (ax.get("comparisons_vs_data_only") or {}).get(ax.get("best_pi"))`, or have analyze_l4b_v2.py additionally write `out["axes"][axis]["best_pi_vs_data_only"] = r_best` alongside line 116. The second is safer: it keeps the figure's contract explicit and gives the MDE lookup at fig_ladder.py:142-143 a matching partner.

## 3. [blocking] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\fig_ladder.py:61

**What.** `PENDING_RESULTS = ("results/l4b_v2_verdict.json",)` — validate.py:211-217 polices this both ways: `stale = [p for p in pending if (ROOT / p).exists()]` and, if non-empty, `bad.append(f"{path.name} — declares {...} as PENDING_RESULTS but the file exists: the run has landed and the figure must read it")`. fig_ladder.py matches `path.name.startswith("fig")` at validate.py:196, so the gate applies.

**Why.** Same trigger as the numbers.py PENDING entry: the file appears at the end of chain_l4b_v2.sh, and validate.py's figure-provenance gate then fails permanently. The follow-up never runs validate.py, so this is invisible until the manuscript is validated.

**Fix.** Remove the entry, leaving `PENDING_RESULTS = ()`, in the same commit as the numbers.py PENDING removal and the fig_ladder.py:140 key fix — all three must land together or validate.py and build_paper.py stay red.

## 4. [blocking] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\analyze_l4b_v2.py:104, 110, 112

**What.** Three of the four verdict branches interpolate arm names into the verdict string: line 104 `f"NO DIFFERENCE between data_only and the best physics arm {best_pi}; the legacy 'hurts' claim is WITHDRAWN."`, line 110 `f"PHYSICS HELPS once correctly weighted ({best_pi}); ..."`, line 112 `f"the best physics arm {best_pi} is significantly worse than data_only, ..."`. Every one contains raw underscores (`data_only`, `pi_fixed_w1e-4`, `pi_gradnorm_t0.1`). paper/numbers.py:286-287 pastes the string verbatim with formatter `"{}"` into `\newcommand{\nLfourbVerdictMaterial}{...}`, and paper/manuscript.tex:513 uses it in text mode.

**Why.** An unescaped `_` in LaTeX text mode is a hard error ("Missing $ inserted"). The material axis is the branch most likely to hit it: data_only held = 0.0231 vs pi_fixed_w1e-4 held = 0.0227, i.e. the fixed arm is already nominally ahead, so a NO DIFFERENCE or PHYSICS HELPS verdict on that axis is a live outcome. Only the `worse_all` string (lines 101-102) and "no eligible physics arm" (line 78) are underscore-free, so the build survives by luck of which branch fires.

**Fix.** In analyze_l4b_v2.py, render arm names for prose with a LaTeX-safe alias — e.g. define `def pretty(a): return a.replace("_", "-")` and use `pretty(best_pi)` / `"data-only"` inside the three f-strings — or add a `tex_escape` formatter in paper/numbers.py:286-287 in place of `"{}"` that replaces `_` with `\_`. Do not rely on the branch not firing.

## 5. [major] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\chain_l4b_v2_followup.sh:42

**What.** The extension trains `pi_fixed_w1e-5` AFTER chain_l4b_v2.sh has already consumed `best_pi`: chain_l4b_v2.sh:16 runs `refine_l4b_v2.py --axes material time` (which picks best_pi at refine_l4b_v2.py:129-131) and chain_l4b_v2.sh:17 runs `--stage polish` (which picks it at run_l4b_v2.py:409 and records it via `set_path(res, best_pi, "polish", axis, "best_pi")` at line 427). Nothing in the follow-up re-runs either stage.

**Why.** If w=1e-5 beats the incumbent — very likely on the time axis, where the fixed family is monotone and w1e-4 (0.0146) is the current best against data_only's 0.0131 — then the analyser's `best_pi` (analyze_l4b_v2.py:89) becomes pi_fixed_w1e-5 while Q3's physics-at-inference control and Q4's L-BFGS polish were computed for pi_fixed_w1e-4. analyze_l4b_v2.py:121-133 then reads `bp = P["best_pi"]` (the OLD arm) and at lines 127-129 compares `before_sign` from `r_best` (the NEW arm) against `after_sign` from `rp` (the OLD arm) to decide `ordering_flips`. That is a flip test across two different arms, and it is written into the verdict JSON as `polish.ordering_flips`.

**Fix.** Append two lines to chain_l4b_v2_followup.sh between the extension (line 42) and the analyser (line 44): `"$P" -u refine_l4b_v2.py --axes material time --threads 6 >> l4b_v2_refine.log 2>&1` and `"$P" -u run_l4b_v2.py --stage polish --axes time material --threads 6 >> l4b_v2.log 2>&1`. Both resume cell-by-cell and are no-ops if best_pi is unchanged; if it changed, they train exactly the cells the new best_pi needs. Alternatively make analyze_l4b_v2.py:121 refuse the Q4 block when `P["best_pi"] != best_pi` rather than silently comparing the wrong arm.

## 6. [major] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\analyze_l4b_v2.py:101-102

**What.** The `worse_all` verdict string is hard-coded: "PHYSICS IS WORSE AT EVERY WEIGHTING SCHEME TESTED (fixed over four decades, gradient-norm at three targets, NTK, self-adaptive) — the legacy claim stands, now defended." But `worse_all` is accumulated at line 88 only over `eligible`, and `eligible` (line 62) excludes both failed arms and arms flagged `abandoned`. On the time axis the current data already excludes four of the ten: d0_seen = 0.0145, so the 3x threshold is 0.0435, and pi_fixed_w1e-1 (seen 0.0563), pi_fixed_w1 (0.0842), pi_gradnorm_t10 (0.0633) and pi_sa (0.1679) all exceed it. Separately, `complete` at line 55 silently drops any arm with fewer than 3 seeds, with no assertion that the full arm set is present.

**Why.** The sentence goes verbatim into the manuscript through paper/numbers.py:287 and asserts a comparison against ten schemes when six were compared. After the follow-up the fixed family also spans FIVE decades (1e-5..1), so "four decades" is wrong in the verdict string, in fig_ladder.py:147 ("fixed over four decades, gradient-norm x3, NTK, self-adaptive") and in paper/manuscript.tex:518. And because chain_l4b_v2.sh:19 echoes L4B_V2_DONE unconditionally, a chain that died mid-material-axis would still let the follow-up run and write this sentence from a 4-arm sweep.

**Fix.** Build the parenthetical from the data rather than typing it: enumerate `eligible` (and state `abandoned` explicitly as failed-to-train per PREREG §4.1) inside the verdict string, and count the fixed-weight decades from `len(fixed)`. Add a guard before the verdict that raises unless `set(complete) >= set(sw["arms_all"]) | {"pi_fixed_w1e-5"}`, so an incomplete sweep cannot produce a verdict. Update fig_ladder.py:147 and paper/manuscript.tex:518 to five decades.

## 7. [major] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\refine_l4b_v2.py:129-131

**What.** best_pi is selected in three places with two different rules. analyze_l4b_v2.py:58-62 implements the PREREG §4.1 failed-to-train guard (`abandoned = [a for a in usable if a != "data_only" and np.mean([...]["seen"]) > 3 * d0_seen]`). refine_l4b_v2.py:129-131 (`ok = {a: v for a, v in S.items() if a != "data_only" and len(v) >= len(args.seeds) and all(v[str(s)].get("failed") is None ...)}`) and run_l4b_v2.py:404-405 (identical filter for the polish) apply only the non-finite-loss `failed` flag and no seen-window criterion.

**Why.** The pre-registration excludes an arm whose seen-window error exceeds 3x the data-only twin's from best_pi selection entirely. On the time axis four arms are in that class today. If any of them had had the lowest held-out error, Q3's physics-at-inference control and Q4's polish would have been run on an arm the analyser simultaneously reports as failed-to-train — the two halves of the paper would disagree about which arm is the best physics arm. It does not bite on the current numbers, but the follow-up adds an arm and re-opens the selection.

**Fix.** Factor the eligibility rule into one function (e.g. `eligible_arms(sweep_axis, seeds)` in v2_common.py or run_l4b_v2.py) implementing both criteria — non-finite `failed`, and seed-mean `seen` > 3x data_only's — and call it from all three sites: analyze_l4b_v2.py:58-62, refine_l4b_v2.py:129-131, run_l4b_v2.py:404-405.

## 8. [major] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\analyze_l4b_v2.py:158-160

**What.** In the Q3 null branch the MDE is computed and thrown away: `mde_report(a - b, mats, base=float(b.mean()), alpha=ALPHA, effects=MDE_EFFECTS, trials=args.mde_trials, label=f"Q3 [{axis}] {arm}")` — the return value is not assigned, and `out["refine"][f"{axis}/{arm}"]` at lines 162-163 stores only `comparison`, `seen_before`, `seen_after`, `verdict`. Contrast lines 106-108, where the Q1/Q2 MDE is captured into `mdes[best_pi]` and reaches the JSON.

**Why.** The whole point of running the analyser again without `--no-mde` (follow-up item 2, citing rule 7 and retraction A22) is that a null may not be reported without its MDE. Q3's verdict string is "physics at inference does not improve transfer at this configuration" — a null — and its MDE will exist only in l4b_v2_analysis.log, which the follow-up truncates with `>` at line 45. Quoting that percentage in the manuscript would require typing it by hand, which is exactly defect B21/B43.

**Fix.** Assign it — `q3_mde = mde_report(...)` — and add `"mde": q3_mde` to the dict written at analyze_l4b_v2.py:162-163, then declare a key for it in paper/numbers.py SPEC (path `refine.material/data_only.mde.mde_80`) if the prose quotes it.

## 9. [minor] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\analyze_l4b_v2.py:93-99

**What.** The sweep-edge check tests position only: `bf = min(fixed, key=lambda a: table[a]["held"])` then `if bf in (fixed[0], fixed[-1]): edge = bf` and prints "fixed-weight optimum {bf} sits on the sweep edge — extend before a verdict (PREREG §4.2)". PREREG_L4b_v2.md:136-138 conditions the rule on the edge being reached "without saturation".

**Why.** After the follow-up adds w=1e-5, that arm is very likely the new fixed-weight minimum (w -> 0 is data_only by construction, and data_only 0.0131 already beats w1e-4's 0.0146 on the time axis). The check will then fire again on the new bottom edge even though the family has plainly saturated, and its message says to extend before writing a verdict — an instruction that recurses forever. Note also that `edge` is only recorded as `edge_warning` and does not actually block the verdict, so the message is advisory in one direction and misleading in the other.

**Fix.** Add the saturation test the pre-registration names: treat the edge as satisfied when the edge cell's held-out error is within noise of the data_only twin's (e.g. `abs(table[bf]["held"] - table["data_only"]["held"]) < table["data_only"]["held_sd"]`, or the CI of that comparison includes zero), and set `edge = None` in that case. Record the saturation evidence next to `edge_warning`.

## 10. [minor] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\chain_l4b_v2_followup.sh:36-40

**What.** The only interlock is `if ! grep -q L4B_V2_DONE chain_l4b_v2_outer.log 2>/dev/null; then ... exit 1; fi`. chain_l4b_v2.sh:19 echoes L4B_V2_DONE unconditionally (no `set -e`; exit codes are only echoed as D0_EXIT/PT_EXIT/... markers), and resume.sh:183 invokes `bash chain_l4b_v2.sh >> chain_l4b_v2_outer.log 2>&1` unconditionally and with append, so once the marker lands it is permanent.

**Why.** This is the only route by which the 66 completed cells can be lost. Both run_l4b_v2.py invocations do `load_or_init` -> mutate in memory -> `write_atomic` the WHOLE dict; two processes holding the file concurrently means last-writer-wins over the entire results file. A `./resume.sh go` typed while the follow-up's extension is training would start a second run_l4b_v2.py against results/l4b_v2_results.json, and would also re-run analyze_l4b_v2.py with `--no-mde`, overwriting the MDE verdict the follow-up just produced. The follow-up alone is safe; the pair is not.

**Fix.** Replace the log grep with a live-process check plus a completeness check — reuse the `Get-CimInstance Win32_Process ... -match 'run_l4b_v2|refine_l4b_v2'` probe from resume.sh:79 and refuse to start if the count is non-zero, and count cells in results/l4b_v2_results.json (as resume.sh:82-93 does) rather than trusting the marker. Add the mirror-image guard to chain_l4b_v2.sh so it refuses to start while the follow-up is alive, and make resume.sh:183 conditional on the follow-up not running.

## 11. [minor] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\run_l4b_v2.py:57-60 and 366

**What.** `ARMS` does not include `pi_fixed_w1e-5`, and `load_or_init` returns the PREVIOUS header on resume (v2_common.py:222 `return prev, True`), so `arms_all` in results/l4b_v2_results.json stays the 11-arm list after the extension adds a twelfth. analyze_l4b_v2.py:63 then prints `f"[{axis}] {len(complete)}/{len(sw['arms_all'])} arms complete"`, i.e. "12/11 arms complete".

**Why.** Cosmetic in the log, but `arms_all` is the only machine-readable record of what the sweep was supposed to contain, and any future completeness assertion built on it (see the fix for the verdict-text finding) would be wrong. Confirmed against the live file: `arms_all` currently lists exactly the 11 pre-registered arms.

**Fix.** Add `"pi_fixed_w1e-5"` to the ARMS list at run_l4b_v2.py:57-60 (it belongs there once the extension is pre-registered under PREREG §4.2), and have load_or_init or the caller union `header["arms_all"]` into the resumed record rather than discarding it — e.g. after line 366, `res["arms_all"] = sorted(set(res.get("arms_all", [])) | set(args.arms))`.

## 12. [minor] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\chain_l4b_v2_followup.sh:46-49

**What.** The two refine_sweep invocations use every default: refine_sweep_l4b_v2.py:136 `--lrs` defaults to `[1e-6, 1e-5, 1e-4, 1e-3]`, :135 `--seeds` to `[42, 43, 44]`, :138 `--eval-at` to `[0, 25, 50, 100, 200, 300]`, over 48 held-out materials. That is 12 cells per scope, 24 cells total, each cell being 48 units x 300 Adam steps plus six full-field evaluations per unit.

**Why.** The header comment budgets the follow-up only for the extension ("Six cells, roughly four hours" — accurate; measured cells in l4b_v2.log run 1750-4100 s, median ~2300 s). The pre-registered single-configuration refinement took 2106/2324/2087 s per seed on the material axis (l4b_v2_refine.log), so 24 cells of comparable or greater work is roughly 15 hours, making the real follow-up about 19-20 hours rather than four. Nothing breaks; the operator's plan does.

**Fix.** Either state the true budget in the header comment, or narrow the grid — e.g. `--lrs 1e-6 1e-5 1e-4` for `--scope last` — and note that the sweep covers the MATERIAL axis only (refine_sweep_l4b_v2.py:151,162 hard-code `nm` and `"axis": "material"`), so the PREREG §4.3 seen-window blow-up on the TIME axis (0.0127 -> 0.0945) is never swept despite being cited at refine_sweep_l4b_v2.py:15-17 as a motivation.

## 13. [minor] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\chain_l4b_v2_followup.sh:45

**What.** The analyser step redirects with a single `>`: `"$P" -u analyze_l4b_v2.py --mde-trials 200 >  l4b_v2_analysis.log 2>&1`, truncating the file, whereas every other step in both chains appends with `>>`.

**Why.** It destroys the `--no-mde` analysis output written by chain_l4b_v2.sh:18 — the only record of what the verdict looked like before the sweep was extended, which is exactly the before/after that PREREG §4.2's extension rule exists to document. It also destroys the Q3 MDE printout if the run is repeated, and that printout is currently the ONLY place the Q3 MDE exists (see the discarded-return finding).

**Fix.** Change to `>>`, and if a clean file is wanted for the final verdict, write it to a distinct name (e.g. `l4b_v2_analysis_final.log`) so the pre-extension analysis survives.

## 14. [minor] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\paper\manuscript.tex:512-514

**What.** The L4 section body is a hand-written placeholder: `\textbf{[SECTION PENDING --- L4b-v2 is running. Its verdict text is \nLfourbVerdictMaterial\ on the material axis and \nLfourbVerdictTime\ on the time axis, and will be reported in the words pre-declared in the pre-registration.]}`.

**Why.** chain_l4b_v2_followup.sh:51-54 claims regenerating the figure and numbers means "the PENDING placeholder cannot survive the run that resolves it". It cannot touch this one: it is prose in manuscript.tex, not a macro value. Even with every other fix applied, the resolved verdict sentences would be printed inside a paragraph that still announces the run as pending.

**Fix.** Treat the L4 section rewrite as a required manual step after the follow-up lands, and add it to the follow-up's header comment alongside the three automated items so it is not mistaken for something the chain does.

## 15. [minor] C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\analyze_l4b_v2.py:69

**What.** `seen = np.mean([complete[a][str(s)]["seen"] for s in seeds if not complete[a][str(s)].get("failed")] or [np.nan])`, then line 72 stores `"seen": float(seen)` and line 72-73 store `"held": None, "held_sd": None` for the same case.

**Why.** For an arm where every seed hit a non-finite loss, the table entry carries a bare `NaN` into results/l4b_v2_verdict.json via `json.dump` at line 164. Python's json writes `NaN` unquoted, which is invalid JSON for any strict consumer, and paper/numbers.py:367-369 has a finiteness gate precisely because non-finite values reaching a document is a known failure mode. No arm has failed so far, so this is latent rather than active.

**Fix.** Store `None` instead of NaN — `"seen": float(seen) if np.isfinite(seen) else None` — matching how `held`/`held_sd` are already handled two lines down, and pass `allow_nan=False` to the `json.dump` at line 164 so the condition surfaces as an error rather than as an unparseable file.

