# Pre-registration — the two-wave coordinate change (warp) on dataset v2

**Written 2026-09-28, before the landmark screen or any v2 warp cell is run.** Frozen
by the commit that adds this file. Spec: `audit_2026-09-24/audit_risk.md` #14–#20.

## 1. Why
The warp verdict (NO DIFFERENCE under predicted fronts; a significant 2.27× under an
oracle) is measured on 12 held-out materials. On v2 the legacy landmarks are
degenerate: the 5 % level is crossed within 2 % of the run in 97 % of cells (B41), and
the 95 % level is never crossed in 13 615 cells, whose arrival times would be
fabricated at the end of the axis (audit_risk #15). The port must replace the
landmarks by a rule fixed before any reconstruction is scored.

## 2. Stage 1 — landmark screen (runs first; no reconstruction, no warp outcome)
Candidates: lower level L_lo ∈ {0.10, 0.20, 0.30, 0.40, 0.50}, upper level
L_hi ∈ {0.90, 0.95}. On the FIT materials of every fold, for every candidate:
- **G1 resolution:** sd over (sample, z) of t_L ≥ 4/(NT − 1).
- **G2 boundary mass:** fraction of cells with t_L ≤ 2/(NT − 1) < 0.20.
- **G3 no fabricated crossings:** n_bad = 0 for BOTH levels.
- **G4 span:** min (t_hi − t_lo) > 2/(NT − 1) with zero clamps; the clamp count reported.
- **G5 predictability ceiling (reported):** η², the between-material share of variance
  of each landmark curve.
**Selection rule:** the LOWEST L_lo passing G1–G4 on every fold, with the LOWEST L_hi
among {0.90, 0.95} that passes, so the window is as wide as possible. If no absolute
pair passes: Option B (self-normalised landmarks at c_p + 0.10(1 − c_p) and
c_p + 0.90(1 − c_p), c_p the Henry plateau), then Option C (derivative pair
t_peak ± w/2), each screened by the same guards and reported as a variant. If none
passes, the warp is NOT RUN on v2 and the paper says so. The screen's output is
committed before Stage 2.

## 3. Stage 2 — arms (one run, same folds, seeds 42/43/44)
Every arm computed in the same run, never from an imported constant (B28):
fixed frame; two-wave with the incumbent POD + HGB warp predictor; two-wave with the
**front-locating model** (below); oracle warp, labelled a bound and never quoted
against an arm that does not get the warp. Five folds of `results/l6_v2_folds.json`,
per-fold `standardise_params`, `assert_disjoint`. N_SIG 256, proven lossless by the
interpolation floor at 512 vs 256 on one fold (audit_risk #17).

**Front-locating model (declared here, the one family):** an MLP from the 11-dim
parameter vector to the two landmark curves on the 128-point z grid, emitting
non-negative increments (cumulative softplus in z) and a log-span, so monotonicity and
a positive span hold by construction. Hyperparameters from one grid declared in the
runner, selected on a nested 20 % holdout of the FIT materials, never the held-out
fold. **Pre-check that can stop it before training:** if η² < 0.94 for either curve
(G5), no parameter-only predictor can reach the R² the payoff curve needs; the runner
reports that bound instead of training.

## 4. Primary estimand and pre-declared words
Paired, cluster-robust-by-material bootstrap of per-sample nRMSE(c), model-warp
two-wave vs the same-run fixed frame, seed-averaged, pooled out of fold over 240
materials, at `alpha_for("folds")`:
- CI entirely below zero → "the two-wave frame with a learned front locator beats the
  fixed frame on v2" — a positive result.
- CI contains zero → "NO DIFFERENCE; front location remains the binding obstruction
  at 240 materials", with the MDE.
- CI above zero → "the front-locating model is worse than the fixed frame", reported.
The incumbent (POD + HGB warp) arm gets the same test and the same words; it carries
the legacy verdict's re-measurement.

**Secondary (non-verdict-bearing):** R² per landmark curve; pre-declared target
R² ≥ 0.94 on both. Reaching it WITHOUT beating the fixed frame withdraws the payoff
curve (`warp_predict.py`) as a guide.

## 5. Invalidation (any one → no verdict)
A landmark fails the screen on any fold; n_bad > 0 for either level; the interpolation
floor exceeds 10 % of the same-run fixed-frame error; `assert_disjoint` fires.

## 6. Compute
Screen < 10 min. Stage 2: ~10 h unloaded, ~30 h under contention (audit_risk #19),
queued in `autorun.sh`; peak memory must stay within the machine's free RAM (N_SIG
256, W_true freed before W_p).

## 7. Amendments
**A1, 2026-09-28 -- after the Stage-1 screen, before ANY Stage-2 reconstruction (so no warp outcome was seen).** (i) The screen ran (`results/warp_level_screen.json`): no absolute pair passes. Every L_lo in 0.10-0.50 fails G2 (50-93 % of cells cross within two grid steps -- the Henry wave lifts c early), 0.95 fails G3 (11 428 never-crossed cells on a fit set), and every pair fails G4. The pre-declared fallback therefore applies: Option B, then Option C. (ii) **The G5 pre-check is withdrawn as a stopping rule.** It was specified (following audit_risk #20) as the between-MATERIAL share of landmark variance, but the front locator's input includes the CONDITION parameters, which vary within a material; the between-material share is therefore not a ceiling on what the predictor can explain (the upper landmark's share is 0.017, i.e. almost all its variance is across conditions, which the predictor sees). G5 stays reported; it no longer stops the run. This is corrected before it could act, and would otherwise have cancelled the experiment for a wrong reason.

**Stage-1 OUTCOME, 2026-09-28 (under the frozen rule): the warp is NOT RUN on v2.** No absolute pair passes (above), and neither fallback passes (`results/warp_level_screen_bc.json`, after a disclosed off-by-one fix in the screen's own code that had marked 92 % of cells undefined; with it fixed, 253 cells are undefined and G2 still fails, 93-97 % boundary mass). The reason is physical and is itself a finding: on v2 the Henry wave crosses the whole column between the first two stored time samples (c jumps 0 -> 0.16 at mid-column), and the second front is mostly a gradual, dispersive rise (0.22 -> 0.94 over ~60 of 128 samples) rather than the sharp shock the two-wave warp aligns. Option B as specified assumes the steepest rise is the cooperative shock; on v2 it is the unresolved Henry jump, so its plateau collapses. **Not done:** redefining the landmark until one passes. A corrected plateau rule (the plateau located AFTER the Henry jump) may be run later ONLY as a labelled post-screen amendment, with any result reported as such.
