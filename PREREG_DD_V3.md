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
