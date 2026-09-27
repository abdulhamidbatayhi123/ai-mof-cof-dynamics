# CONTINUE HERE — session handoff

Rewritten **2026-09-24**, after the session that landed L4b-v2, launched its
pre-registered follow-up, ran a six-agent audit of the whole manuscript, and fixed
the twenty-two defects that audit found which were verifiable on the spot.
Read this, then `RESULTS.md`, then `audit_2026-09-24/` (the open findings).
`RETRACTIONS.md` is the record of everything withdrawn — **26 Part-A, 67 Part-B** (counted by `ledger_counts.py`; B65–B67 added 2026-09-25).

---

## 1. First thing to do, every time

```bash
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
./resume.sh                    # state only, runs nothing
git log --oneline | head -20   # the messages carry the reasoning
```

**A chain is in flight. Check it is alive before assuming progress.**
`./resume.sh` prints, at the top, whether a chain is incomplete *and* nothing is
running. It has died twice: a reboot on 2026-09-06 lost twelve hours, and nothing
noticed. A stall looks exactly like progress unless something checks.

To watch the follow-up specifically:

```bash
powershell -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -match 'run_l4b_v2|refine_l4b_v2|refine_sweep' }).Count"
```

---

## 2. STATE OF THE RUN — read this before anything else

**`chain_l4b_v2.sh` is COMPLETE** (66/66 cells, both axes, polish and Q3
refinement done, `L4B_V2_DONE` in `chain_l4b_v2_outer.log`).

**`chain_l4b_v2_followup.sh` is IN FLIGHT**, launched 2026-09-24. Five stages:

| # | stage | state |
|---|---|---|
| 1 | `pi_fixed_w1e-5` extension, both axes (PREREG §4.2) | time axis **DONE** (3/3), material axis not started |
| 2 | `refine_l4b_v2.py` re-run (Q3 must describe the current `best_pi`) | pending |
| 3 | `run_l4b_v2.py --stage polish` re-run (same reason, Q4) | pending |
| 4 | `analyze_l4b_v2.py` **with** MDEs | pending |
| 5 | `refine_sweep_l4b_v2.py` ×2, the labelled post-hoc for B60 | pending |

Budget ≈ **20 h**, not the four the old header claimed. Logs: `l4b_v2.log`,
`l4b_v2_refine.log`, `l4b_v2_analysis.log`, `l4b_v2_refine_sweep.log`; step exit
codes in `chain_l4b_v2_followup_outer.log`. **Never run a second training job
beside it** — both runners rewrite the whole results dict, so two writers means
last-writer-wins over all 66 cells. The follow-up now refuses to start if a runner
is alive.

### UPDATE 2026-09-27 — the extension landed; read this first

- **Time axis: NO DIFFERENCE (final)** — w1e-5 0.01323 vs twin 0.01310, CI spans
  zero, MDE 5 % at 99.5 % power. The interim "physics worse" below is REVERSED (B69).
- **Material axis: NOT FINAL.** w1e-5 is significantly BETTER (0.02126 vs 0.02314,
  CI [0.00125, 0.00263]) but is the unsaturated bottom edge again; PREREG §4.2 says
  extend before the verdict. `chain_l4b_v2_ext2.sh` (autorun job 1b) runs w1e-6 on
  the material axis, then refine/polish/analysis/sweeps, and prints its marker ONLY
  if every stage exits 0. Do NOT write "physics helps" before it lands.
- A **full disk** killed four follow-up stages on 2026-09-26 (ENOSPC). `write_atomic`
  now waits for space; `resume.sh` reports free disk.

### The verdicts as they stand (NOT final — the extension is still landing)

| axis | verdict from the completed sweep | what the extension is doing to it |
|---|---|---|
| **time** | physics is **worse** than its data-only twin at every weighting scheme that trained (`data_only` 0.0131, best physics `w1e-4` 0.0146, CI [−0.00202, −0.00106]) | **w1e-5 = 0.0116/0.0141/0.0141, mean 0.0133 vs 0.0131 — a TIE.** The verdict is likely to become **NO DIFFERENCE** |
| **material** | **NO DIFFERENCE** (`data_only` 0.0231 vs `w1e-4` 0.0227, CI spans zero). **The legacy "physics hurts" claim is WITHDRAWN** — pre-declared outcome two | w1e-5 not started |

Four arms (`w1e-1`, `w1`, `gradnorm_t10`, `pi_sa`) **abandoned the data fit** —
seen-window error 3–12× the twin's, the B16 signature — and are excluded as
failed-to-train per PREREG §4.1, never averaged in.

Q3 (physics at inference) makes transfer **worse** on all four arm/axis
combinations, and destroys the seen window (+402 % to +662 %). PREREG §4.3's
invalidation fired on the time axis, so that axis is scoped; **the material axis
carries the reportable Q3 verdict.** Whether that is a property of physics at
inference or of one optimiser configuration is exactly what stage 5 tests.

Q4: the L-BFGS polish **flips the ordering on the material axis** (data_only
0.0273 vs physics 0.0253 after polish — but *both arms got worse*, and the
data-only arm got worse faster). PREREG Q4 says a flip is the reported result.
Report the degradation of both arms alongside it or the flip reads as "physics
helps", which is not what happened.

**When the follow-up finishes**, `chain_l4b_v2_followup_outer.log` ends with
`L4B_V2_FOLLOWUP_DONE`. Check **every** `*_EXIT=` marker is 0 — the script now
records them instead of masking them with `&& echo`.

---

## 3. What this session changed (2026-09-24)

Commits `b40443b`, `36a788a`, and `4f5b415` / `0d9e135` from the same working day.

**Five defects sitting between the finished run and the manuscript**, all of which
would have shipped:

1. **A macro value that does not compile.** `\nLtwoBestFam` resolves to the literal
   string `mlp_depth`; an unescaped underscore in LaTeX text mode is a hard error.
   The build gate checked undefined macros, mangled macros and bare numerals and
   **never looked at what a macro expanded to**. Worse, three of the four L4b
   verdict branches interpolate an arm name and every arm name has an underscore —
   the document compiled only because the branch that fired was the one hard-coded
   string without one. `paper/numbers.py` now runs every value through `tex_safe()`.
2. **A figure reading a key nothing writes.** `fig_ladder.py` asked for
   `best_pi_vs_data_only`; the analyser writes `comparisons_vs_data_only`. The L4b
   rung would have drawn as "IN FLIGHT" for ever after the run landed, silently.
3. **The edge rule had only half its test.** PREREG §4.2 says "on the sweep edge
   **without saturation**"; the code tested position only, and since `w → 0` *is*
   the data-only twin, the bottom edge is always the family minimum — it would
   demand another decade for ever. Saturation now means "indistinguishable from the
   twin". Measured: the time axis is **not** saturated (rule binds), the material
   axis **is**. **The extension was run on both anyway** — declining an experiment
   on a re-reading of a pre-registered rule made *after* seeing the data is the one
   move this project exists to refuse. It is already paying: the time-axis verdict
   is moving.
4. **`best_pi` was selected in three places under two different rules**, so Q3/Q4
   could have described an arm the analyser simultaneously calls failed-to-train.
   One rule now (`v2_common.eligible_physics_arms`), verified to reproduce the
   analyser's own lists. The analyser refuses Q4 across two different arms.
5. **The follow-up masked its own failures** (`&& echo EXIT=0` prints nothing on
   failure) and **truncated the log** holding the only pre-extension analysis.

**The build had been red since 2026-09-08 and nothing said so** —
`l4b_v2_verdict.json` was declared PENDING in both `numbers.py` and `fig_ladder.py`
while the first chain had already created it.

**An unowned file carrying L5's headline.** `results/l5_fno_verdict.json` had **no
script**: four figures and eight macros read it, and it carries the abstract's
third claim. `analyze_l5_fno.py` now writes it; `--check` diffs rather than
overwrites. **It reproduced to the bit** — the number was right, and nobody could
have known. B21/B43/B63, a fourth time.

**And what that uncovered:** `metrics.compare` defaults to `n_boot = 2000`, never
justified. `bootstrap_convergence.py` measures the cost: L5's published lower bound
+0.00035 is ~18 % below the converged +0.000429 ± 0.000008. **No verdict moves** —
significance is stable across every setting and twelve independent resamplers —
but the *precision* was being quoted from an unconverged Monte Carlo. A
project-wide re-run at a converged `n_boot` is **owed work**.

**Sixteen manuscript defects**, each verified before it was touched — three numbers
that contradicted the macro beside them; the *n*-width exponent (the fitted −2.45 is
the residual **energy** exponent; the *n*-width is the **norm**, −1.23); a
verification table printing "0.0 %" three times; the warp headroom's denominator;
two overclaims against our own record; L6's Damköhler scope. Details in `36a788a`.

**Two things the paper did not have:**

* **B53 closed.** `dispersion_check.py`: our closure is the high-particle-Péclet
  *limit* of Edwards & Richardson. The dataset sits at Pe_p 4.6–190 where the two
  forms differ by a median 1.19× — but the **anchor bed sits at Pe_p 2.9, and the
  disagreement peaks at 3.8 (2.06×)**. Re-solving the anchor without the truncation
  (a labelled post-hoc) moves t95 431 → 384 min against 354 measured and nRMSE
  0.128 → 0.105. **61 % of the arrival-time excess is one term evaluated at a limit
  this bed does not satisfy.**
* **The cost accounting** (`cost_accounting.py`, §"What the surrogate costs"). One
  solve-equivalent = 16.6 worker-seconds; the training set = 18 core-hours; fitting
  the arm = 1.3 solve-equivalents. **Break-even ≥ 3159 screening queries**, and that
  is a *bound* needing no timing at all. The learning curve becomes a price list:
  16× the data for 1.88× the accuracy.

---

## 4. OPEN WORK — `audit_2026-09-24/` holds 133 findings, ~111 still open

The six audit reports are in the repo. **Read them; do not re-derive them.**
Each finding carries file, line, the offending text, why it matters, and the fix.

| file | findings | headline |
|---|---|---|
| `audit_prose.md` | 34 | no Conclusions section; five uncited floats; numbers spelled as words bypass the gate |
| `audit_numbers.md` | 23 | ~40 measured quantities written as English words; 20 declared-but-unused keys, 10 of which should be quoted |
| `audit_citations.md` | 13 | **B62 HAS RECURRED**: 13 invented given names in `references.bib` |
| `audit_followup.md` | 15 | mostly fixed; the rest are noted in the file |
| `audit_hygiene.md` | 28 | **six solver gates PASS when their dataset is absent** (proven empirically) |
| `audit_risk.md` | 20 | scoping for the three rungs still on 12 materials |

### Priority order

1. **When the follow-up lands** — write the L4b section. It is *prose*, not a macro,
   so regenerating `numbers.tex` cannot resolve `[SECTION PENDING]`. Write the
   verdict in the pre-declared words, note the Q4 flip honestly (both arms
   degraded), and record the time-axis verdict change as a **retraction** if the
   extension moves it. Then the abstract's "Six are eliminated" must be recounted.
2. ~~B62 recurrence~~ **DONE 2026-09-25 (B65)** — every given name now gated against
   `paper/author_provenance.md` (fetched by `paper/fetch_author_provenance.py`);
   the build runs the citation gate. Heinlein's co-author is **Johannes** Taraz.
3. ~~Solver gates pass on absent data~~ **DONE (B66)**. Still open from that audit:
   decide whether to TRACK the two ground-truth `.npz` files — a clone now SKIPs,
   and `numbers.py` then refuses to build, which is correct but means no clone
   can build the paper without regenerating them. Document the command or track.
4. ~~Conclusions~~ **DONE** (`\section{Conclusions}`). Its L4 sentence reads the
   verdict macros; re-read it once the L4b section is written.
4b. **NEW, from B67: autorun job 2b** closes L5's DeepONet learning-rate bracket
   (p=8,16 at 3e-2). When it lands: `analyze_l5_merged.py` and `analyze_l5_fno.py`
   re-run inside the job. Then REWRITE the caveat in the L5 section that ends
   "the grid is being extended to close it" into the result — and if DeepONet's
   best improves, the FNO margin, the abstract's FNO sentence and `\nFNOgain`
   move. Check `grid_boundary_warnings` in `results/l5_merged.json` is empty.
4c. **`audit_2026-09-24/STATUS.md`** records which of the 133 findings are closed.
   Update it as you close things; do not re-derive.
5. **The three rungs still on 12 materials** — the biggest structural risk.
   `audit_risk.md` says the cheapest high-value experiment is **`l5_bottleneck` on
   v2 in the same five folds (~1–2 h, <600 MB)**, which moves L5's load-bearing
   "the obstruction is the parameter→coefficient map" table from 12 clusters and one
   seed to 240 clusters and three seeds. Do that one first. DeepONet flat-in-p on
   v2 is 26–39 h; the warp verdict 10–30 h and needs a non-degenerate lower
   landmark (B41: `t_lo` is rule-5 degenerate on v2).
6. **Project-wide bootstrap re-run** at a converged `n_boot`, with
   `bootstrap_convergence.py` extended to the rungs whose per-sample arrays live in
   the large results files.
7. **The front-locating model** — the warp's 2.27× oracle headroom is a target
   nobody has shot at. `audit_risk.md` #4 gives the minimal honest design: it is
   only reportable as a **pre-declared arm inside the warp runner**, with the
   reconstruction CI (not R²) as the primary estimand.
8. Housekeeping: `C_ps` 900–2400 J/kg/K as a real sensitivity; remove `kaggle_run/`
   and SINDy (`audit_hygiene.md` #3 lists what breaks); decide the COF framing;
   `\address{}` in the frontmatter.

---

## 5. What needs the outside world

**Compute:** nothing is blocked. Everything runs CPU-only on this 16 GB / 12-core
machine. A **GPU would be a speed multiplier, not an enabler** — it would collapse
the ~20 h follow-up and the ~40 h of v2 re-measurements into hours and make the
front-locating model cheap to iterate on. Nothing in the paper *requires* one.

**Money:** none. CMAME's subscription route is free to publish, green OA to arXiv.

**The one genuine external dependency: library access.** Five primaries cannot be
retrieved electronically and **B54 is LIVE on a reported result** — which
Klinkenberg paper carries L7's erf formula, 1948 or 1954. Also Glueckauf 1955,
Do & Do (*Carbon* 2000), Danckwerts 1953, Anzelius 1926 / Schumann 1929. All are
currently cited through *named* secondary sources, which is honest but weaker. A
university library or an inter-library loan resolves all five. **Ask the author to
request them.**

---

## 6. Rules carried forward — each earned by getting it wrong once

1. No number from a failing `validate.py` category.
2. Matched training budget, **asserted** not assumed.
3. ≥3 seeds. Single-seed numbers appear nowhere.
4. Compare against the competitor's **strongest** configuration. A selected
   hyperparameter on a grid edge is acceptable only if the metric has **saturated**
   there — measure it, never assume it.
5. Never normalise by a quantity that can vanish.
6. A gate that can be bypassed is not a gate.
7. **No null without its minimum detectable effect.**
8. Nothing is cited until it has been **fetched**, not searched.
9. Errors in the analysis are recorded on the same terms as errors in the code.
10. **No number without a script.** An unowned number is indistinguishable from a
    wrong one.
11. **Never expand an initial.** (Currently violated — see §4 item 2.)

**New, from this session:** a gate must check what a macro *expands to*, not only
that it resolves. And a Monte Carlo interval must be run to convergence before its
endpoints are quoted.

---

## 7. Things that would damage the paper — never do these

* Do not claim the two-wave warp is novel. Multi-front alignment is the founding
  example of shifted POD (Reiss, Schulze, Sesterhenn & **Mehrmann**, SISC 40:A1322,
  2018), and the map is textbook landmark registration whose two-landmark linear
  case **is** our σ. Claim the **measurement**, not the map.
* Do not quote the oracle-warp number against any arm not also handed the warp.
* Do not present DeepONet branch-dominance as new — Heinlein & Taraz got there
  first. Cite them and differentiate on the four axes in `CITATIONS.md`.
* Do not cite Rigas or Kiyani for "KANs need different optimisation" — neither says
  it, and the KAN literature is **split** (KINN reports KAN beating MLP).
* Do not call our isotherm "the Do–Do form" — theirs has an *n*-layer BET primary
  term, ours a Langmuir. "In the spirit of Do & Do".
* Do not attribute `D_L = 0.7 D_m + 0.5 d_p u` to Ruthven — it is Wakao & Funazkri,
  for **nonporous** particles, and Perry's calls it a **lower** bound.
* Do not describe results as "MOF-303" beyond the cited parameters.
* **It is not an architecture paper.** L3 refuted the KAN premise on our own data
  and L5 refuted our own *n*-width explanation. The negative results are the
  contribution.

**Venue: CMAME.** Fallbacks: Separation & Purification Technology, then TMLR.
**One paper, not two.**
