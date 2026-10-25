# Pre-registration: screening and named-framework tests (Digital Discovery revision)

Written and committed 2026-10-25, BEFORE any of the runs below. The commit that adds this file
is pushed to GitHub at once, so the push event is an external timestamp. Nothing below was
looked at in advance: no screening metric and no named-framework field had been computed.

## Why
A desk rejection (CMAME, 2026-10-17) and three simulated reviews for Digital Discovery asked
the same questions:
- What does a materials chemist learn from field errors, rather than from rankings?
- Do the surrogates work on real, named frameworks, rather than on random points of the
  sampled box?

Two pre-specified additions answer them. Both are exploratory with respect to the original
ladder, and the paper labels them as additions made after the CMAME review.

## Arms (all fixed now)
1. **POD + per-mode gradient boosting**, p = 16. These are the l5_bottleneck_v2 settings:
   HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06, early stopping) per
   standardised mode.
2. **DeepONet**, p = 16, learning rate 3e-3, 24 000 steps, budget 200 000, depth 3. These are the
   selected L5-v2 settings (results/l5_v2_verdict_24k.json), with one seed (42).
3. **The coarse finite-volume solve** at N_z = 50, the B-COARSE matching grid, on every sample.

The production solve (N_z = 2000) is the reference. Every learned arm is fit on training
materials only, with parameters standardised on the fit set, and assert_disjoint is checked.

## B1: screening on the 240-material five-fold design (out of fold)
- **Quantity.** t50: the time at which the outlet concentration first reaches 0.5 c_in. It is
  read from the c field at the frozen 128 × 128 encoding (outlet row, linear interpolation in
  time) and taken in units of t_final.
- **Truth.** Read the same way from the stored production field, so truth and prediction share
  their discretisation.
- **Metrics, per condition** (17 conditions, ranking the held-out materials within each):
  - Spearman rank correlation between predicted and true t50;
  - top-10 % recall: the fraction of the materials with the longest true t50 that the arm
    also puts in its top 10 %.
- **Summary.**
  - The mean over conditions.
  - A paired cluster-bootstrap interval by material at the v2 calibrated level
    (alpha = 0.02, 4000 draws), resampling materials and recomputing every per-condition
    metric.
  - Each surrogate compared with the coarse solve.
- **Verdict words, fixed now.** A surrogate is "screening-adequate" when the lower end of its
  interval is at least 0.90 for mean Spearman and at least 0.80 for mean top-10 % recall. It is
  "ranks worse than a coarse solve" when its paired difference against the coarse solve is
  significant and unfavourable.
- **Also reported.**
  - The coarse solve's paired field nRMSE against every surrogate on all samples. This
    replaces the one-sample-per-material comparison.
  - Failed coarse solves counted at the cost of one production solve, never excluded.

## B2: named frameworks
- **The six frameworks** of research/water_mof_parameters.json: MOF-303, MOF-801, CAU-10-H,
  aluminium fumarate, MIL-160(Al) and Co2Cl2(BTDD).
- **Their model parameters, fixed by rule now:**
  - **step_rh:** the mean of the stated inflection or midpoint values.
  - **q_max:** the mean of the stated saturation values in mol/kg. Values stated at
    intermediate RH ("at 20 % RH") are not used.
  - **delta_H:** minus the mean stated magnitude.
  - **isotherm_n:** n = ln 81 / ln(p90/p10) where the source states the rise interval
    (p10, p90 taken as its ends); otherwise the dataset median.
  - **henry_fraction, d_p, rho_p, eps_t:** the dataset medians, because they are not framework
    properties in this model (see the f_H correction in the revision).
- **Conditions.** The dataset's 17 conditions.
- **Truth.** The production solver.
- **In or out of the box.** "In the box" means every parameter lies inside the sampled ranges.
  The frameworks outside it (MOF-801 step, Co2Cl2(BTDD) capacity) are reported as extrapolation
  and never pooled with the in-box ones.
- **Surrogates.** The arms are refit once on all 240 materials. Each framework then gets:
  - field nRMSE (c);
  - |t50 error|;
  - whether the order of the six frameworks by t50, within each condition, is preserved
    (Kendall tau).
- **Verdict words.** A framework is "inside the held-out error distribution" when its mean nRMSE
  is at or below the 95th percentile of the same arm's per-material out-of-fold errors in B1.

## Amendment 1 (2026-10-25, before any run)
- **t50 is ranked in seconds, not in units of t_final.** The original text said "in units of
  t_final". But t_final is material-dependent: it is the run horizon, a multiple of the
  stoichiometric time. A ranking in normalised time would compare materials on different
  clocks.
- **How it is computed.** t50 [s] is the normalised crossing time multiplied by the sample's
  t_final. Prediction and truth both use the sample's stored t_final, as every rung's
  normalised-time scoring already does.
- **A known small leak, stated.** t_final carries the solver's horizon extensions for the
  7 % of runs that were extended, so the surrogate is handed the true horizon for those
  samples. The same is done for the coarse solve.

## What will not be done
- No tuning on these test sets.
- No change of arms, settings or thresholds after any result is seen.
- Any deviation goes in the correction ledger with its date.
