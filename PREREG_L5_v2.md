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
(none)
