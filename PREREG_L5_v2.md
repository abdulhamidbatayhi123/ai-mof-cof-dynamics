# Pre-registration — L5 (linear-reconstruction operators) on dataset v2

**Written 2026-09-28, before any v2 L5 cell is run.** Frozen by the commit that adds
this file; changes after it are dated amendments in §7, reported as post hoc if made
after any result.

## 1. Why
L5's verdict — DeepONet is flat in basis size p while the POD floor falls — is measured
on the legacy design: 12 held-out materials, one split, α = 0.005. L1, L2, L6 and L7
report over 240 materials in five folds at α = 0.02. Retraction A26 exists because a
verdict taken at one material count did not survive four times as many. This rung is
re-measured on the design the rest of the ladder uses (`audit_2026-09-24/audit_risk.md`
#1–#13 specify the port).

## 2. Design (identical to legacy L5 except where stated)
- Data: `data/parametric_v2`, field_res 128 (v2_common), the same five material folds
  as L1/L2/L6/L7 (`results/l6_v2_folds.json`), parameters standardised **per fold** on
  the fold's training materials only.
- Arms: DeepONet at p ∈ {8, 16, 32, 64, 128}, the legacy budget, depth and steps.
- Learning rates: {3e-3, 1e-2, 3e-2} — extended one point above the legacy top because
  the legacy p = 8 and p = 16 optima sat on that edge, unbracketed (B67). The
  `edge_is_binding` guard certifies every selected optimum interior or saturated
  before any table is written; an unbracketed optimum extends the grid one point in
  that direction, per rule 4, before the verdict.
- Seeds 42, 43, 44; per-sample errors seed-averaged, pooled out of fold (each of the
  3947 samples once).
- Statistics: paired, cluster-robust by material, α from `alpha_for("folds")`
  (calibrated 0.02 at 240 clusters), n_boot 4000; every null carries its MDE
  (`mde_report`).

## 3. Question and pre-declared words
**Q-L5 (primary):** is DeepONet's held-out error flat in p on v2?
- p = 128 vs p = 8 not significant, MDE stated → "DeepONet is flat in basis size on the
  240-material design; a sixteenfold increase cannot have improved it by more than X %
  (MDE)" — the legacy verdict **stands at 240 materials**.
- p = 128 significantly better → "basis size helps DeepONet on the 240-material
  design" — the legacy flat-in-p verdict is **retracted as a small-design artefact**,
  on the same terms as A26.
- p = 128 significantly worse → reported in those words, with the same scoping.

**Secondary:** the POD floor per fold at each p, and the ratio best-DeepONet / floor at
p = 128 — the "wall" statement is re-quoted from v2 numbers only.

## 4. Step-budget sensitivity (declared, runs first)
On v2 a fold trains on ~3158 samples against 691 on legacy, at the same 8000 steps.
Rule 6: an undertrained model sits near its initialisation and flatters flatness.
**Arm:** p ∈ {8, 128} at each p's selected lr, steps ∈ {8000, 24000}, 3 seeds, fold 0.
**Rule:** if 24000 steps changes the p = 128 error by more than the fold-0 MDE, the
whole sweep is re-budgeted at 24000 steps before any L5-v2 verdict is written; the
change is reported either way.

## 5. What would invalidate the test
- A selected optimum unbracketed after one extension → the verdict is reported as
  provisional in those words.
- Any fold's scaler touching held-out materials (asserted, never assumed).
- A seed that fails to train (B24 signature: best validation at step 0) → excluded and
  listed, never averaged in.

## 6. Compute
~26–39 h at normal load (audit_risk); queued in `autorun.sh`, one training job at a
time. The step-sensitivity arm (~2–4 h) runs first.

## 7. Amendments
**2026-09-28, before any v2 L5 cell ran (not post hoc).** §4 said the step arm "runs first" and uses "each p's selected lr" -- inconsistent, because only the sweep selects an lr. Resolved: the step arm runs first at the **legacy-selected** rates, p = 8 at 1e-2 and p = 128 at 3e-3 (`results/l5_merged.json`), as two invocations with separate outputs (`results/l5_v2_steps_p8.json`, `results/l5_v2_steps_p128.json`). The sweep runs `--families deeponet` only, as §2 declares (the runner's default also includes DeepOKAN).


**A2, 2026-10-04 -- after the 8000-step sweep and the step arm, before any L5-v2 verdict was written.** Both triggers below are rules frozen in §2 and §4, applied as written; nothing is chosen after seeing a p-comparison. (i) **§4 fired.** At fold 0, p = 128 (lr 3e-3) moves 0.0115 -> 0.0094 from 8000 to 24000 steps (+18.8 %, significant; threshold 5 %), while p = 8 does not move (+0.5 %). The 8000-step sweep is therefore under-budgeted exactly in the direction rule 6 warns of -- it flatters flatness -- and is NOT used for the verdict. (ii) **§2 fired.** At 8000 steps p = 32, 64, 128 select lr 3e-3, the bottom of the grid, still moving. (iii) **Action:** the sweep is re-run at 24000 steps on lr {1e-3, 3e-3, 1e-2, 3e-2} for every p (the grid extended one point down for all p, so the selection rule is the same for every arm), 5 folds, seeds 42/43/44, output `results/l5_v2_results_24k.json`. The 8000-step results stay on disk and are reported as the under-budgeted run. (iv) **Disclosed defect:** the analyser read the pre-A1 single step-arm filename, found nothing, and reported the gate as "NOT RUN" while both files existed; fixed (it now reads every declared file and refuses a partial set) before this amendment was written.

**A3, 2026-10-05 -- before any 24k L5-v2 verdict existed (24k sweep at 27/300 trainings; no p-comparison of the 24k run has been computed or looked at).** Prompted by B75 (the legacy FNO-vs-DeepONet "significant" did not survive paying for the selection of both arms on the test materials), not by any L5-v2 number. Q-L5 compares p = 128 and p = 8, each at its own best of the four learning rates, both chosen on the held-out folds. **The §3 verdict and its words are unchanged and remain per-pair.** Added alongside it: one studentised max-statistic cluster bootstrap (`selection_adjust.simultaneous`) over every (lr at p = 8, lr at p = 128) pair, at the same alpha, with the interval for the selected pair and these words, written by `analyze_l5_v2.py` into `q_l5_selection_adjusted`: per-pair significant and simultaneous not → "significant as a pair, NOT after paying for both learning-rate choices; reported as no detectable difference once selected"; both significant → "the per-pair verdict survives the selection"; per-pair null → "per-pair null; the selection can only widen it". The manuscript reports both. The code was exercised on the voided 8000-step results only, to a scratch file.
