# Pre-registration — L6 on dataset v2: does structural decomposition pay, and where?

**Written 2026-09-01, before any v2 L6 arm is trained.** Committed to git before the
run so the ordering is verifiable, which the L0–L7 pre-registration was not
(`README.md` states that limitation honestly).

This document is frozen. Changes after the first arm trains go in `RETRACTIONS.md`
with a date and a reason, not a silent edit.

---

## 1. Why L6 is being re-run at all

The legacy L6 reported **"H1 NOT SUPPORTED"**. That verdict stands, but retraction
**A22** established that it excludes far less than was claimed: with 12 held-out
materials the design had **7 % power at a 20 % effect** and a minimum detectable
effect near **70 %**. It is a real null and a weak one.

Two things also made the legacy test close to unanswerable in principle:

1. **The kinetic regime was degenerate.** Da = k·t_final had median **626**, with
   only **1.1 %** of samples in the kinetically-informative band 5–60. At local
   equilibrium there is no kinetic object to identify, so a decomposition into
   equilibrium and kinetic parts has almost nothing to decompose.
2. **The kinetic object was entangled with the equilibrium one.** `k_LDF` is
   partly determined by the isotherm slope (k ∝ 1/K, K = q*/c), so asking whether
   an isotherm fingerprint predicts `k_LDF` was partly asking whether it predicts
   itself.

Design v2 fixes both: Da median **27.5** with **77.8 %** in band (p05 8.3, p95 145),
and the hidden kinetic object is now **`d_p`**, the particle diameter, which is
thermodynamically independent of the isotherm.

---

## 2. The hypothesis, restated so it is answerable

The original H1 asked a **pooled** question: *does separate identification beat
joint fitting on held-out materials, on average?* Measured power says that question
cannot be answered well even at 48 clusters (MDE 50 %).

It is also the wrong question. The mechanism the project measured says the benefit
of separating the kinetic object should **depend on how much the kinetics matter**,
which is exactly what Damköhler measures. So:

> **H1-v2 (primary).** The transfer advantage of separate equilibrium/kinetic
> identification over joint fitting **increases as Damköhler falls**. Formally, in
> a regression of the per-material paired difference `Δ_m = err_separate,m −
> err_joint,m` on `log10 Da_m`, the slope is **positive** (the advantage grows as
> log Da decreases, i.e. Δ becomes more negative at low Da).

> **H1-v2 (secondary, the legacy question).** The pooled mean difference `E[Δ]`,
> reported **with its minimum detectable effect**, never alone.

A slope test uses the between-material variance instead of paying for it as noise.
That variance is the whole problem: measured at **0.0391, 69 % of the base error**.

---

## 3. Design

**Data.** `data/parametric_v2` — 3947 samples, 240 materials, 17 conditions,
design v2 (Sobol, Glueckauf kinetics). Splits from the manifest, unchanged.

**Cross-validation over materials.** Five folds over all 240 materials, each fold
holding out 48 and training on 192. This yields **240 held-out materials in total**
rather than 48, at 5× the compute of a single run. Power scales roughly as
√(n_clusters), so the expected MDE improves from 50 % to **≈ 23 %**.

*Every arm sees identical folds.* Fold assignment is by material id, seeded, written
to `results/l6_v2_folds.json` before training, and asserted identical across arms.

**Arms**, at matched ~120 000 parameters, matched steps, matched optimiser,
3 seeds — unchanged from legacy so the two are comparable:

| arm | description |
|---|---|
| `joint` | one network, descriptors → fields |
| `separate` | equilibrium head + kinetic head, composed through the Duhamel integrator |
| `separate_noeq` | ablation: kinetic head only |

**Inputs.** Observable descriptors from `descriptors.build` — isotherm fingerprint
at 12 humidities × 4 temperature offsets, plus `rho_p`, `eps_t`, `v`, `T_in`,
`rh_feed`. **Withheld:** `q_max`, `delta_H`, `step_rh`, `isotherm_n`,
`henry_fraction`, **`d_p`**.

**Statistics.** α = **0.02**, the level calibrated for 48 clusters
(`results/calibration_v2.json`; empirical FPR 5.0 %). Paired, cluster-robust by
material. The slope test bootstraps materials and refits.

---

## 4. Pre-declared outcomes — all four are reportable

| outcome | what it means | how it is reported |
|---|---|---|
| **slope > 0, CI excludes 0** | H1 holds, and the mechanism is confirmed: structure pays when kinetics matter | *"Separate identification pays, and the benefit is a measured function of Damköhler."* This is a positive result. |
| **slope CI includes 0, pooled CI includes 0** | H1 fails across the whole informative regime, not just at equilibrium | *"H1 is not supported at Da 8–145, with MDE X %"* — a far stronger negative than legacy, because the regime it was supposed to work in is now covered |
| **slope < 0, CI excludes 0** | separation gets *worse* as kinetics matter more | Reported as-is. It would refute the mechanism as well as the hypothesis. |
| **pooled significant but slope null** | a uniform benefit unrelated to Da | Reported as-is; would suggest the benefit is not kinetic in origin |

**Failure condition, in the words to be used.** If the slope CI includes zero at
α = 0.02 with 240 held-out materials, the abstract will say: **"structural
decomposition of the equilibrium and kinetic objects does not improve transfer to
unseen materials, across a Damköhler range of 8–145 spanning kinetically-controlled
to near-equilibrium operation, with a minimum detectable effect of X %."**

No outcome may be reported without its MDE (retraction **A22**).

---

## 5. What would invalidate this test, checked before the verdict

1. **`d_p` recoverable from the descriptors.** If a strong regressor recovers `d_p`
   with R² > 0.7 on held-out materials, the kinetic object is not actually hidden
   and the rung is degenerate again (defect **B19**). `descriptors.check_non_degenerate`
   runs first and the result is reported either way.
2. **Da not actually varying within folds.** Each fold's held-out Da range is
   reported; if a fold spans less than a decade the slope estimate for it is not
   used.
3. **Fold imbalance.** Cluster sizes per fold are reported; the bootstrap uses the
   real, unbalanced sizes.
4. **The Duhamel composition handicap.** Legacy found the `separate` arm's error
   amplified through the integrator (`separate_noeq` q-nRMSE 0.4564). If that
   recurs, the negative result is about **this composition**, not about
   decomposition in general, and will be scoped in those words.

---

## 6. Compute

5 folds × 3 arms × 3 seeds = 45 runs at ~120 k parameters. Comparable to the legacy
L6 run × 5.
