# Pre-registration — L1, L2 and L7 on dataset v2

**Written 2026-09-02, before any v2 L1, L2 or L7 arm is trained.** Committed to git
before the runs, as `PREREG_L6_v2.md` was, so the ordering is verifiable.

This document is frozen. Changes after the first arm trains go in `RETRACTIONS.md`
with a date and a reason, not a silent edit. The one value that could not be
typed in before its script ran — the calibrated α for the 240-cluster design,
§3.5 — was produced by `calibrate_v2.py --fivefold` (log: `calibrate_v2_5fold.log`)
and entered before this document was committed and before any arm trained.

---

## 1. Why these rungs are re-run

L6 is resolved on dataset v2. L3 and L5 are final on the legacy dataset and are
not re-run. L1, L2 and L7 currently report on the legacy dataset (60 materials,
uniform sampling, Damköhler median 626), and three things make re-running them
necessary rather than cosmetic:

1. **L1's verdict is open.** Retraction **A18** narrowed "you just need more data"
   to *"more conditions per material is eliminated; more materials is not"*: the
   learning curve was still falling 1.82× at the largest size available, 48
   training materials. Retraction **A21** then showed the coefficient-map ceiling
   — "the map carries ~5 modes' worth of information" — is what 48 materials buy,
   not a property of the map, with 16 of 32 modes still climbing from 36 → 48
   materials. Dataset v2 has **192 training materials** in its manifest split and
   **240** in total: four to five times the legacy range. Whether the material
   axis closes is the single most consequential open measurement in the ladder,
   because every downstream rung's "wall" was measured at 48 materials.
2. **L2's verdict rests on 12 held-out clusters.** "Capacity is eliminated" was
   decided by a last-step test at α = 0.005 with 12 materials, a design whose
   MDE is about 50 % (`results/calibration_v2.json`, legacy). On v2 the same
   test has 240 clusters.
3. **L7's kinetic input changed.** Under v2 the mass-transfer coefficient is
   derived from the particle by Glueckauf, not sampled. The classical forms take
   `k_LDF` as an input, and the learned reference arm they are scored against
   must be one trained on v2.

The unifying reason: **every rung should report on the same dataset.** A referee
who finds L1/L2/L7 on one dataset and L6 on another will ask why, and the honest
answer — "we changed the dataset after finding its kinetics were unphysical
(§5B of the audit)" — is much stronger if the whole ladder is then shown on the
corrected data.

---

## 2. Questions, and the decision rule for each — fixed in advance

### L1-v2 (a) — the data-driven arms

*Which fixed-basis, data-driven family transfers best to unseen materials, and
how far above the representation floor does it sit?*

Arms, hyperparameters **identical to legacy `run_l1.py`**:

| arm | configuration |
|---|---|
| `ridge` | `Ridge(alpha=1.0)` |
| `rf` | `RandomForestRegressor(n_estimators=300, min_samples_leaf=2)` |
| `xgb` | `XGBRegressor(n_estimators=400, max_depth=5, learning_rate=0.06, subsample=0.85, colsample_bytree=0.85, multi_strategy="multi_output_tree", tree_method="hist")` |
| `mlp` | `MLPRegressor((256,256,256), max_iter=3000, early_stopping, n_iter_no_change=30, lr_init=1e-3)` on **standardised** targets (defect B14) |

Decision rule, as legacy: every arm is compared pairwise against the best arm
(lowest mean out-of-fold nRMSE on c) with the paired cluster-robust bootstrap at
the calibrated α. Arms whose CI includes zero **tie** and the paper may not rank
them. The gap above the per-fold POD floor is reported for every arm.

### L1-v2 (b) — the materials learning curve. **This is the load-bearing measurement.**

*Hypothesis H-data:* "more training materials closes the transfer gap."

Training-material counts **n ∈ {12, 24, 48, 96, 192}**, drawn from each fold's
own 192 training materials (the held-out fold is never subsampled). Every size
has **3 seeds** that move every stochastic component — the material subset, the
randomised SVD, and the regressor's early-stopping split. The full size is *not*
exempt: the legacy learning curve ran its full-size point once with
`random_state=0` throughout, which rule 3 forbids, and that is recorded in
`RETRACTIONS.md` when this document is committed.

Function class: **POD on the c-channel, p = 32, + per-mode gradient boosting**
(`HistGradientBoostingRegressor(max_iter=400, lr=0.06, early_stopping)`), the
same class and the same 128×128 encoding as `learning_curve.py`,
`l5_bottleneck.py` and `warp_verdict.py`, so the v2 curve is comparable to the
legacy A18 numbers and to L5's fixed-frame reference. **It is not comparable to
L1-(a)'s table** (three channels, 64 modes, different arms); it re-measures L1's
*hypothesis*, not L1's arms.

Targets at every size, all on the held-out fold:

| target | what it measures |
|---|---|
| **field nRMSE(c)**, basis refit on the subset | what a practitioner with n materials actually gets — the honest curve |
| field nRMSE(c), basis **fixed** on the fold's full 192 training materials, regressor trained on the subset | separates "the basis needs more data" from "the coefficient map needs more data" — the clean version the audit (§4A) asked for |
| per-mode R² of the coefficient map, fixed basis, modes 1–32 | A21's measurement at five sizes instead of one |
| R² of `t_lo(z)` and `t_hi(z)` at levels (0.05, 0.95) | the two-wave warp's bottleneck (the 2.17× headroom depends on it) |

**Decision rule (the L2 rule, applied to data):** the materials axis is
**eliminated** iff the last step, **96 → 192**, is *not* a significant
improvement in the honest field nRMSE at the calibrated α — reported with its
MDE. It is **not eliminated** if the last step is significant; in that case the
power-law exponent β in `err ∝ n^−β` over the five sizes is reported with a
bootstrap-over-materials CI, and **no extrapolation beyond twice the measured
range is claimed** in any document.

Pre-declared outcomes, all reportable:

| outcome | reading |
|---|---|
| last step null, curve flat by 96 | the wall is intrinsic to this function class at this information; L1 is eliminated on both axes and the ladder's diagnosis stands |
| last step significant, β reported | the axis is open at 192 materials; L1's verdict becomes "not eliminated at the largest size available", in those words, and every downstream "wall" is scoped to the material count it was measured at |
| warp R² saturates while field error still falls, or the reverse | reported as-is; it decides which target the two-wave headroom actually depends on |
| fixed-basis curve flat while refit-basis curve falls | the basis, not the map, is what more materials buy — this would *contradict* A21's reading and is reported in those words |

### L1-v2 (c) — the conditions axis

At the full 192 training materials, keep a fraction **f ∈ {0.25, 0.50, 0.75,
1.00}** of each material's conditions, 3 seeds each. Same targets, same rule on
the last step (0.75 → 1.00). Legacy found this axis much weaker than the
material axis (0.0642 → 0.0512); the prediction is that this replicates.

### L2-v2 — capacity

The sweep is **identical to legacy `run_l2.py`**: `mlp_width` w ∈ {16, 32, 64,
128, 256, 512, 1024} at depth 3; `mlp_depth` d ∈ {1, 2, 3, 4, 5, 6, 8, 10} at
width 256; `xgb_depth` md ∈ {2, 3, 4, 5, 6, 8, 10}; `rf_leaf` leaf ∈ {1, 2, 4,
8, 16, 32}. Same POD (64 modes/channel, fold-train only), same inputs, same
seeds. Train error reported alongside held-out error so underfitting is ruled
out rather than assumed.

Decision rule, as legacy: a family has **saturated** iff its largest capacity is
not significantly better than its second-largest at the calibrated α. L2 is
**eliminated** iff every family has saturated; any family still improving has
its sweep extended before a verdict is given. Each saturation null carries its
MDE.

### L7-v2 — the classical control

The three closed forms in `classical.py` (`equilibrium_shock`, `klinkenberg`,
`constant_pattern`), zero training, evaluated on **every** sample, since a
zero-parameter model holds nothing out. `k_LDF` is the Glueckauf value
reconstructed by `physics_from_params` and **asserted equal** to the manifest's
per-sample `k_LDF` before scoring (defect B37's class).

Scored **like-for-like on the exit curve** at the 128-point time grid, paired
sample by sample with the **out-of-fold** exit-curve prediction of the best
L1-v2 arm. "Best" is the L1-(a) arm with the lowest mean out-of-fold nRMSE(c);
if the top arms tie under L1-(a)'s rule, the comparison is repeated for every
tied arm and all are reported.

Decision rule: learning is **justified** iff every classical form is
significantly worse than the learned arm on exit-curve nRMSE. If any classical
form ties or wins, **that is the headline of the rung**, as the frozen protocol
(§2) already says.

---

## 3. Design

### 3.1 Data
`data/parametric_v2` — 3947 samples, 240 materials, 17 conditions, design v2
(Sobol, Glueckauf kinetics). Manifest splits unchanged.

### 3.2 Encoding
Fields are subsampled to **128 × 128 on load** (`ladder_data.load(field_res=128)`),
exactly as L5 and L6-v2 — the same `linspace` index selection, so every v2 rung
and the warp analyses share one encoding. All three channels for L1-(a) and L2;
the c-channel only for the learning curve. POD rank **64 per channel** for
L1-(a)/L2 (legacy) and **32** for the learning curve (legacy). The encoding is
recorded in every results file. Absolute numbers are therefore comparable to
L5, L6-v2 and the legacy learning curve, and **not** to legacy L1/L2's
512 × 256 tables.

### 3.3 Held-out design — the L6-v2 folds, reused
**5-fold cross-validation over materials using the fold assignment already on
disk**, `results/l6_v2_folds.json` (seed 20260901), asserted identical at load.
Every material is held out exactly once, giving **240 held-out clusters**, and
L1, L2 and L6 then report over the *same* held-out materials in the *same*
folds. POD bases, target scalers and input scalers are fitted on **fold-train
only** — the code asserts that no held-out index enters any fit.

For L1-(a) only, the **manifest split** (192 train / 48 novel materials, plus
the 2-condition novel-condition split) is *also* run, as the single-split,
legacy-shaped view at the 48-cluster calibration (α = 0.02). The
novel-condition split has two clusters and is reported descriptively, with no
interval and no verdict (audit B19-of-the-audit / §3B).

### 3.4 Seeds
42, 43, 44 for every stochastic component. No single-seed number anywhere,
including the full-size learning-curve point and including appendices.

### 3.5 Statistics
Per-sample scores are **averaged over the three seeds**, then compared with the
paired, cluster-robust-by-material bootstrap of `metrics.compare` (4000
resamples). Calibrated levels:

| design | clusters | α | source |
|---|---|---|---|
| manifest split | 48 | **0.02** | `results/calibration_v2.json["v2"]`, FPR 5.0 % |
| 5-fold pooled | 240 | **0.02** | `results/calibration_v2.json["v2_5fold"]` — calibrated 2026-09-02 before any arm trained: empirical FPR **2.8 %** at nominal 0.02 (6.5 % at 0.05), so the level is conservative, and it is the same level L6-v2 used on this design. Generic-null MDE at 80 % power: 10 % |

Every null carries its **minimum detectable effect** from `mde.py`, computed
from the *measured* between- and within-material sd of the actual paired
difference (retraction A22). `mde.py` was checked against the L6-v2 power table
before this document was committed (`results/l6_v2_mde_check.json`).

### 3.6 What is written, and when
Every runner writes its results file after each completed (fold, configuration,
seed) cell and resumes by skipping completed cells, so a shutdown loses at most
one cell. `resume.sh go` runs whatever is missing. Results go to **new files**
(`results/l1_v2_results.json`, `results/learning_curve_v2.json`,
`results/l2_v2_results.json`, `results/l7_v2_results.json`); the legacy files are
not overwritten.

---

## 4. What would invalidate the test, checked before any verdict

1. **Fold mismatch.** The fold map read from disk must contain all 240 materials
   in 5 folds and match the L6-v2 file byte-for-byte in content. Asserted.
2. **Leakage into a fit.** Any POD, scaler or regressor fitted on an index set
   that intersects the held-out fold. Asserted in code at every fit.
3. **An underfitting arm** (train ≈ held-out error, defect B14). The arm's
   number is reported, flagged, and may not be used as "the best data-driven
   arm" until its configuration is fixed and re-run.
4. **XGBoost unavailable** → the arm is skipped and listed as skipped, never
   silently absent.
5. **A learning-curve subset that draws from the held-out fold.** Asserted.
6. **Degenerate normalisation** (rule 5): nRMSE is normalised by the full-field
   range of the reference; exit-curve nRMSE by the full exit-curve range. Neither
   can vanish for a completed breakthrough, and the code raises if either does.
7. **`k_LDF` reconstruction mismatch** for L7 (B37's class): the Glueckauf
   coefficient rebuilt from the parameter vector must equal the manifest's
   per-sample value to 1e-9 relative, or the rung aborts.

---

## 5. Compute

| piece | fits | note |
|---|---|---|
| L1-(a), manifest split | 4 arms × 3 seeds | minutes to ~1 h |
| L1-(a), 5-fold | 4 × 3 × 5 = 60 | RF and MLP dominate |
| learning curve | 5 folds × (5 sizes + 4 fractions) × 3 seeds = 135 | ~1–2 min each |
| L2-v2 | 28 configs × 3 seeds × 5 folds = 420 | `xgb md8/md10` dominate; run last, cheap families first |
| L7-v2 | 3 forms × 3947 curves | seconds |

Order of execution: **L7 → L1-(a) → learning curve → L2**, so the cheapest and
most decisive results land first and a shutdown costs the least.
