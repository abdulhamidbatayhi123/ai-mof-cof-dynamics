# Pre-registration: a physically realistic isotherm family (design v3) and DeepONet's own basis floor

Written 2026-10-25, BEFORE any of the runs below. The commit that adds this file is pushed to
GitHub at once, so the push event is an external timestamp. No v3 surrogate has been fitted,
no v3 field has been scored, and no DeepONet trunk floor has been computed.

## Why
Three internal referee reports for Digital Discovery (2026-10-25) converged on two points.

1. **The isotherm family is not that of real water MOFs.** In v2 the primary (Langmuir) sites
   are fixed at b_H = b_C/20, so they are weaker than the cooperative sites and hold about
   5 % of their capacity at the step. Real low-humidity sites (MOF-303, MIL-160,
   Co2Cl2(BTDD)) bind more strongly than the pore-filling ones. The step steepness also stops
   at n = 6, while the frozen B2 rule gives n ≈ 16 for aluminium fumarate and ≈ 30 for
   CAU-10-H. Steep steps make near-shocks, which is exactly where a reduced basis could bind.
   So "the map, not the basis" is shown only for smooth, weak-site isotherms.
2. **The decomposition was measured on the wrong model.** Eq. (split) was measured for POD
   with per-mode gradient boosting and ridge. The best surrogate, DeepONet, has a learned
   trunk seen through a sigmoid head. Its "floor" in the paper is the POD floor, not its own.

## Disclosed pilot (feasibility only)
On 2026-10-25, 16 v3 draws (seed 999, not the design seed) were solved to measure acceptance
(13 of 16) and solve time (13–209 s). No surrogate was fitted, and no field was scored or
inspected. The design ranges below were fixed before the pilot and are not changed after it.
The design size was reduced from 240 to 120 materials because of the pilot's solve times.

## A. Dataset v3
- **Code.** `gen_parametric_dataset.py --design v3` (MATERIAL_SPACE_V3) and
  `ladder_data.PARAM_KEYS_V3`, committed with this file.
- **Materials: 120, scrambled Sobol, seed 20260830.**
  - Ranges:
    - q_max 8–56 mol/kg;
    - ΔH −62 to −40 kJ/mol;
    - step RH 0.05–0.45;
    - n 1–32;
    - f_H 0.03–0.30;
    - **log10(b_H0/b_C0) from −1.3 to +1.5** (the v2 value is −1.3);
    - d_p, ρ_p, ε_t as in v2.
  - The ranges enclose all six named frameworks.
- **Conditions: the 17 v2 conditions exactly** (the same condition space and the same seed,
  20260830 + 7), so the operating conditions are identical to v2.
- **Physics, solver, N_z = 2000, the storage rule and the screening rule:** unchanged from v2.
  Run with ADS_STORE_NZ = 256, as in v2.
- **Folds: 5, by material.** The material ids 0–119 are permuted with
  `numpy.random.default_rng(20261026)` and split into 5 groups of 24 (results/v3_folds.json),
  written by `dd_v3.py folds` before any fit.

## B. Measurements (out of fold, five folds)
- **V1, eq. (split) on v3.** POD floor and map term at p ∈ {8, 16, 32, 64, 128}, for per-mode
  gradient boosting and ridge with the l5_mapterm_v2 settings and seed 42.
- **V2, DeepONet's own basis floor.**
  - On v3, DeepONet at p ∈ {8, 16, 128}, with the PREREG_DD_ADDITIONS settings (learning
    rate 3e-3, 24 000 steps, budget 200 000, depth 3) and seed 42; p = 16 also at seed 43.
  - The same on v2 at p ∈ {8, 128}, seed 42. On v2, p = 16 comes from dd_seed_robustness.py,
    seeds 43 and 44.
  - For every held-out sample, the own floor is min over a of ‖u − σ(T a + b0)‖ on the c
    channel. Here T is the trained trunk and σ the model's sigmoid head; a is fitted per sample
    (least-squares initialisation on logit u, then L-BFGS; dd_seed_robustness.trunk_floor).
- **V3, coarse solve.** N_z = 50 on every v3 sample, scored as in B1. A failed coarse solve is
  re-solved at production resolution and charged one production solve; the excluded variant
  is also reported.
- **V4, screening on v3.** The B1 metrics and thresholds unchanged (Spearman ≥ 0.90 and
  top-10 % recall ≥ 0.80 at the lower interval ends), for DeepONet p16, gradient boosting
  p16 and the coarse solve.
- **V5, zero-solve baseline (v2 and v3).** Ranking by the stoichiometric time
  t_st = ρ_b q*(c_in, T_in) L / (v c_in), from the isotherm alone. It is scored with the B1
  metrics.
- **V6, the six frameworks in the v3 box.**
  - The same rule as B2, with these changes:
    - f_H is the source's `henry_fraction_estimate` where the JSON gives one; otherwise the
      v3 median;
    - log10(b_H0/b_C0) is the v3 median;
    - n is from the rise interval where stated; otherwise the v3 median.
  - The arms are refit on all 120 materials, and the "inside the held-out error distribution"
    rule is the B2 rule.

## C. Statistics and verdict words, fixed now
- **Shares are of squared error**, the quantity eq. (split) adds up:
  share_map = mean(total²) − mean(floor²), over mean(total²). Ratios of mean nRMSE are reported
  beside them, labelled as such.
- **"The map dominates"** for a model and dataset if share_map ≥ 0.5 at every p ≥ 16, with the
  lower end of its cluster-bootstrap interval ≥ 0.5 (α = 0.02, 4000 draws, by material).
  **"The basis binds"** if share_map ≤ 0.5 at p = 16 with the upper end ≤ 0.5.
  Otherwise **"neither dominates"**.
  - This is applied to gradient boosting (V1) and to DeepONet with its own floor (V2), on
    v2 and on v3.
- **Coarse against surrogate.** The paired cluster-bootstrap interval of the field nRMSE
  difference at α = 0.02. "More accurate" if it excludes zero.
- **Screening and frameworks:** the B1/B2 words, unchanged.
- **The title's claim** ("the coefficient map, not the basis, limits...") is kept only if "the
  map dominates" holds for DeepONet with its own floor on v3. Otherwise the title and abstract
  are rewritten to the verdict.

## What will not be done
- No tuning on v3; no change of ranges, settings or thresholds after any v3 result is seen.
- Any deviation goes in the correction ledger, with its date.

## Amendment A1 (2026-10-26, AFTER the first v3 results and a second internal review)
Everything above is unchanged. This amendment is written after the first PREREG_DD_V3 results
were seen (commit c1823b1) and after three second-round internal referee reports. It registers
corrections and additions before any of their runs. Each is in the correction ledger (B89).

**Why.**
1. **The own floor did not converge.** In the first runs, `trunk_floor` used L-BFGS: one shared
   line search over a batch of separable problems, 60 iterations. It returned "floors" above the
   model's own error for up to 20 % of v2 samples at p = 16, which is impossible for a minimum.
2. **The registered runs were incomplete.** The verdicts were computed while the chain was still
   running: v2 p = 128 and v3 p = 16 seed 43 were missing, and the analysis skipped missing cells
   silently.
3. **t50 often falls on the pre-step wave.** It can therefore rank materials by their weak sites,
   not their capacity.
4. **Two comparisons were confounded.** The v2-to-v3 comparison mixed training-set size, design
   and framework inputs. The named-framework criterion was relative to each design's own 95th
   percentile, which differs about fourfold between designs.

**Corrected method (replaces the trunk-floor solver of B, V2).**
- The floor is solved per sample by batched Levenberg-Marquardt with per-sample damping.
- It starts from (a) the model's own predicted coefficients, branch(Pz), and (b) least squares on
  logit(u), and keeps the better result.
- Only improving steps are accepted, so the floor never exceeds the model's own error.
- Convergence: relative gradient norm below 3e-5, a relative decrease below 1e-9, or damping at
  its cap; at most 200 iterations.
- Reported per cell: the converged fraction, the fraction with floor <= total, and the largest
  difference between the own-coefficient reconstruction and the model's error (a consistency
  check).
- Trained models are saved (`models/`), so floors can be recomputed.
- Code: `dd_seed_robustness.trunk_floor`, `dd_v3.py deeponet` (writes
  `results/dd_v3a1_deeponet.json`). The first-attempt file `results/dd_v3_deeponet.json` is kept
  as the record.

**Runs (all re-run with the corrected solver, settings otherwise as registered above).**
- **DeepONet.** v2 at p = 8, 16 and 128 (seed 42) and at p = 16 (seeds 43, 44); v3 at
  p = 8, 16 and 128 (seed 42) and at p = 16 (seed 43).
- **Material-matched v2 control** (`--control`): DeepONet p = 16, seed 42, on v2. Each fold's
  training materials are subsampled (rng 20261027 + fold) to the number of materials the same v3
  fold trains on; the held-out fold is unchanged.
- **POD + boosting p16** per fold on v2 and v3, now also recording t90 (`dd_v3a1.py hgb90`).
- **Coarse solve** of every sample of v2 and v3, now also recording t90 (`dd_v3a1.py coarse90`).
- **Affinity sensitivity of the frameworks** (`dd_v3a1.py fwsens`): the six frameworks under the
  v3 rule, re-solved with log10(b_H/b_C) = -0.5 and +1.0 instead of the median.
- **Framework refits** (`dd_v3a1.py fwfit`): both arms refit on all v3 materials at seeds 42, 43
  and 44, with models saved. Each refit predicts three sets:
  - the v3-rule frameworks;
  - the v2-rule frameworks, whose solver truth is unchanged (primary-site affinity
    log10(1/20)), so this separates design coverage from input changes;
  - the sensitivity frameworks.

**Analyses (`dd_v3a1_analyse.py`, `results/dd_v3a1_verdict.json`).**
- **The split verdicts of section C, recomputed from the A1 DeepONet cells at seed 42 for every
  registered p.** A missing registered cell stops the analysis. Seeds 43 and 44 at p = 16 are
  reported beside them.
- **Screening, with t90 (the first crossing of c/c_in = 0.9) as a second metric beside t50.**
  - Both metrics use the registered thresholds and words.
  - t50 remains the registered primary; t90 is an amendment and is labelled so.
  - Also reported: Spearman and recall within each fold, and the tie bias of the material
    bootstrap (bootstrap mean minus point estimate).
- **Coarse against surrogate, all samples, under both policies** (failed solves charged; failed
  solves excluded), on both designs.
- **Horizon-leak bound.** DeepONet's t50 ranking is re-scored with the horizon multiplier
  predicted out of fold (gradient-boosted classifier on log t_st and the condition, both
  solve-free) instead of the true horizon.
- **Frameworks: absolute errors and absolute and relative t50 errors** for every set and seed,
  beside the registered relative verdicts.
- **Physics checks.**
  - The Damkohler number on the stoichiometric clock, k_LDF t_st, per material.
  - The ratio of the adsorbed water's heat capacity at saturation to the solid's.
  - Acceptance of v3 cells by affinity quartile and by n >= 8 against n < 8.
  - The Monte Carlo standard error of the calibrated test size (400 null simulations).

**What will not be done.**
- No setting or threshold is tuned on these results.
- The registered verdicts of section C keep their wording.
- The t50 screening verdicts of B1 and V4 stand as registered.
- t90 is reported as an addition, not a replacement.
