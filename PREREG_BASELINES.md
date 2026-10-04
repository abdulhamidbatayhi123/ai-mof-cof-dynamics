# Pre-registration — three baselines a referee asked for

**Written 2026-10-04, before any of these baselines is run.** Frozen by the commit
that adds this file; changes after it are dated amendments in §6. Source: the internal
referee report `audit_2026-10-04/referee_report.md`, items M11a-c. Every baseline runs
on dataset v2 (`data/parametric_v2`, field_res 128), the five folds of
`results/l6_v2_folds.json`, and is compared with `metrics.compare` (paired,
cluster-robust by material) at `alpha_for("folds")`, n_boot 4000; every null carries its
MDE. None of these baselines changes a pre-registered ladder verdict; each is reported
as a baseline, in the words below.

## 1. B-GP — Gaussian-process regression on POD coefficients (M11b)
**Why.** With ~3150 training samples in 11 dimensions, a GP on the POD coefficients is
the standard non-intrusive reduced-order-model regressor, and the referee notes the
learner is a ~2x lever (M1). Omitting it would leave the strongest classical regressor
untested.
**Config (one, declared here).** `run_l1_v2.py --design folds --arms gp`, identical to
L1-v2 in every other respect (64 POD modes per channel, per-fold parameter
standardisation, seeds 42/43/44, out-of-fold pooling). The arm: scikit-learn
`GaussianProcessRegressor`, kernel `ConstantKernel * Matern(nu=2.5, length_scale=ones(11),
bounds 1e-2..1e3) + WhiteKernel(1e-3, bounds 1e-8..1e0)`, `normalize_y=False` inside a
`TransformedTargetRegressor(StandardScaler)` (the targets are standardised exactly as
for the MLP arm), `n_restarts_optimizer=2`, `random_state=seed`. One shared kernel for
all outputs (scikit-learn's multi-output GP).
**Comparison and words.** GP vs the L1-v2 MLP arm (the best L1 arm), out of fold:
- GP significantly better → "a Gaussian process on POD coefficients beats the
  perceptron on held-out materials"; the paper's L1 arm is then not the strongest
  pointwise regressor and the L1/L2 text is revised to say so.
- not significant → "no difference between a Gaussian process and the perceptron", MDE.
- GP significantly worse → "the perceptron beats a Gaussian process", reported.
**Invalidation.** A fold whose GP fit fails to converge (kernel at a bound on every
length scale) is reported, not averaged in silently.

## 2. B-COARSE — the same solver on a coarser grid (M11a)
**Why.** The cost section compares the surrogate only with the full-resolution solve.
The decision-relevant competitor is a cheaper numerical solve at matched accuracy.
**Config.** For one sample per material (240 samples; the condition drawn per material
with `numpy.random.default_rng(20261004)`), re-solve with `gen_parametric_dataset`'s
own physics (`build_physics`, the recorded `t_final`, the same integrator settings and
600 snapshots) at N_z ∈ {50, 100, 200, 400, 800}; resample to the stored grid with the
generator's `resample`, subsample to 128x128 with `ladder_data`'s rule, and score
`metrics.per_variable_nrmse` against the stored field. Wall time per solve is measured
in the same process, and the N_z = 2000 production solve is timed on the first 24 of
the same samples so the cost is in solve-equivalents measured on one machine.
**Reported.** The accuracy-cost curve (mean c-channel nRMSE vs solve-equivalents), and
the smallest N_z whose mean error is at or below (a) the L1-v2 MLP's held-out error and
(b) the best L2 configuration's. Words: "a coarse solve at N_z = X matches the
surrogate's held-out accuracy at Y solve-equivalents per query", or "no tested grid
matches it" (then the coarsest grid's error is stated). The surrogate's per-query cost
r (cost_accounting.py --time) is set beside it.
**Invalidation.** A coarse solve that fails or does not reach 90 % breakthrough is
counted and reported per N_z, never dropped silently.

## 3. B-FIT — the Klinkenberg form with fitted corrections (M11c)
**Why.** L7's closed forms are scored with nothing fitted. The fair classical
competitor is the same form with its two physically interpretable inputs corrected by
fitting on the training materials.
**Config.** `klinkenberg` of `classical.py` with the chord Henry slope K and k_LDF each
multiplied by a constant, exp(a) and exp(b), fitted per fold by Nelder-Mead from (0,0)
on the fold's TRAINING samples (minimising mean exit-curve nRMSE, `v2_common.exit_nrmse`),
then applied unchanged to that fold's held-out samples. Two parameters per fold, no
per-material fitting (a per-material fit would need the held-out material's own curve).
**Comparison and words.** Fitted Klinkenberg vs the learned arm's out-of-fold exit
curve, exactly as `analyze_l7_v2.py` pairs them:
- learned arm still significantly better → "learning remains justified against a
  fitted classical form", with the ratio.
- not significant → "a two-parameter fitted Klinkenberg form matches the learned
  arm on the exit curve", MDE — this would weaken L7 and is reported in L7.
- fitted form significantly better → reported in those words, in L7.

## 4. Order and compute
After the L5-v2 24k sweep and the P2 ODR check in `autorun.sh`, one at a time:
B-FIT (minutes), B-GP (an hour or two), B-COARSE (a few hours, mostly the 24 production
solves).

## 5. What this does not do
It does not add a baseline after seeing which would win: all three are declared here
with their words before any is run. It does not re-select the ladder's arms.

## 6. Amendments
(none)
