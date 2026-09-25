# PRE-REGISTRATION — Paper 2: when can AI discover adsorption kinetics?

**Status: DRAFT, NOT FROZEN.** Written 2026-09-25. It is frozen by a commit whose
message begins `FREEZE PREREG_P2` — after the generator pilot (§6) and before any
discovery method is run on any grid cell. Nothing in §2–§5 may change after the
freeze except through a dated, reasoned amendment appended in §9, and an amendment
made after results exist is reported as post hoc.

Evidence base: `research/lit_equation_discovery.md` (57 fetched sources). Codes
S1…S65 below refer to that journal.

---

## 1. Question

For which regimes can the adsorption **rate law** be discovered from data a column
experiment can produce — and does discoverability fail at the same boundary as
classical **practical identifiability** of the rate constant, or earlier?

What is **not** claimed as new: that the mass-transfer coefficient is poorly
determined near local equilibrium (S8, S29, S33, S36, S37). The paper measures where
the boundary lies for the strongest discovery methods, what sets it, and whether it
coincides with identifiability.

## 2. Hypotheses, each with its falsifier and pre-declared verdict words

Let δ be the realised driving-force fraction, `max |q*(c,T) − q| / q_max` over the run
(computed from ground truth), and ε_eff the combined relative error of the equilibrium
the method is given (isotherm error ε) and of the observations (noise σ).

**H2a — the boundary is a driving-force-versus-error boundary.** The probability of
successful discovery, P(success), collapses onto one curve when plotted against
R = δ / ε_eff, across Da, Pe, isotherm shape and observation model; the 50 % crossing
lies at R* with a spread of **less than half a decade** across conditions.
- *Falsifier:* R* spread ≥ one decade across conditions.
- *Words:* "R collapses the boundary" / "R does not collapse the boundary; the
  boundary depends additionally on {named axis}".

**H2b — discoverability versus identifiability.** For each slice (σ, ε, observation,
isotherm), compare Da*_disc (50 % crossing of P(success) for the best method) with
Da*_ident (largest Da at which k is practically identifiable given the TRUE law, §4.3).
- Three pre-declared outcomes, reported in these words:
  "discovery fails **before** identifiability" (Da*_disc < Da*_ident by ≥ the MDE),
  "discovery fails **with** identifiability" (|difference| < MDE),
  "discovery **outlives** identifiability" (Da*_disc > Da*_ident by ≥ MDE — the method
  finds the law's form where its coefficient is undetermined).

**H2c — errors-in-variables methods move the boundary.** The best EIV method (§3,
M5) shifts Da*_disc by at least a factor 2 relative to the best non-EIV method at
ε > 0.
- *Falsifier:* shift below the MDE at every ε > 0. *Words:* "EIV moves the
  boundary by {factor}" / "EIV does not move the boundary detectably (MDE {x})".

**H2d — the MOF case (exploratory, labelled so).** For a step (Type V) isotherm with a
rate that drops at the step (as reported for MOF-303, S39), is the state dependence
k(q) discoverable, and in which (σ, observation) cells? No directional prediction.

## 3. Methods compared — each in its strongest configuration (rule 4)

Two candidate libraries, both reported:
- **Lib-A (agnostic):** polynomials in (c, q, T) to degree 3, plus exp(−θ/T) factors.
- **Lib-B (equilibrium-informed):** Lib-A plus the **measured** equilibrium
  q*_meas(c,T) and its products with q. Including q* is legitimate here because it is
  the *measured* isotherm, carrying error ε — the defect of the original script (A7)
  was including the *exact* generating law.

| id | method | configuration rule |
|---|---|---|
| M1 | S1's pipeline reproduced (universal differential equation + sparse regression + symbolic regression) | at least S1's settings; stronger where S1's are weak |
| M2 | weak-form SINDy (S19, S54) | test-function support swept; best per cell by held-out integral error |
| M3 | ensemble / Bayesian SINDy (S14, S65) | inclusion probability of each term reported |
| M4 | **exact best-subset selection by enumeration** (the MIOSR objective, S55, solved exactly because the library is small), with sign constraints k > 0 and zero rate at q = q* | exhaustive over sparsity ≤ 4 |
| M5 | errors-in-variables: ODR-BINDy (S13) and WENDy-IRLS (S22) | if no reference implementation runs, implemented from the papers and verified on their own published examples before use |
| M6 | SINDy-PI (S21) for rational laws | |
| M7 | constrained symbolic regression (PySR, S23) | Julia installed in the isolated `.venv`, never the base environment |
| M8 | KAN + sparse regression (KANDy, S48) | secondary; not a headline (L3, S49) |
| M9 | slow-manifold discovery (S15) | expected to win at high Da by returning isotherm + apparent dispersion; reported as *what is discoverable there* |

A method that cannot be run in its strongest configuration is reported as such,
never silently replaced by a weaker one.

## 4. Design

### 4.1 Ground truth
The verified reference solver of paper 1 (`solver_fd.py`; L0 checks in
`verify_solver.py`). The rate law is `dq/dt = k(q*(c,T) − q)` (L1) or, for H2d,
`dq/dt = k(q)(q* − q)` with k dropping across the step (L2). Non-isothermal physics
as in paper 1 (primary); an isothermal control is secondary.

### 4.2 Axes
| axis | levels |
|---|---|
| **Da = k·t_stoich** (primary Damköhler: kinetic time constants per front passage; t_stoich from the solver's `stoichiometric_time`) | 9, log-spaced over the range the pilot shows feasible, targeted 10⁻¹–10³. The residence-time form k·L/u is reported alongside but is NOT the axis: the pilot measured it at 10⁻⁴–10⁻³ across the whole kinetic range (residence time 0.4 s against front passage ≈ 7200 s), so it cannot separate regimes here. S1's Da is recomputed in BOTH forms |
| Pe (via D_L multiplier) | 3: ×0.2, ×1, ×5 |
| noise σ, i.i.d. Gaussian, relative to channel range | 0, 0.5 %, 2 %, 5 % |
| isotherm error ε, smooth multiplicative perturbation of q* | 0, 0.5 %, 2 %, 5 % |
| observation | O1 interior c, q, T · O2 interior c, T (q latent) · O3 outlet c(t), T(t) only |
| isotherm | favourable Langmuir · MOF-303-like step |
| true law | L1 constant k · L2 k(q) (step isotherm only) |

Noise and isotherm error are applied **after** the solve, so ground truth needs only
the (Da, Pe, isotherm, law) solves — about 80, at ~17 worker-seconds each.
Replicates: 20 independent (σ, ε) realisations per cell for M2–M6, M8, M9; 3 for M1,
M7 (each needs a network or a Julia search per replicate), on a declared subgrid
(all Da × σ ∈ {0.5 %, 2 %} × ε ∈ {0, 2 %} × both isotherms × Pe ×1 × O2, O3).

### 4.3 Metrics
- **Success (primary):** the selected support equals the true law's support **and**
  every coefficient has the correct sign. For L1 in Lib-B: exactly {q*_meas, q} with
  coefficient ratio −1 within 10 %.
- **Accuracy (secondary):** |k̂ − k| / k ≤ 10 %.
- **P(success)** per cell over replicates; **Da*_disc** from a logistic fit in log Da,
  bootstrap CI over replicates.
- **Identifiability:** profile likelihood of k with the true law known, same
  σ, ε, observation. *Practically identifiable* ⇔ the 95 % profile interval lies
  within [k/2, 2k]. Da*_ident = the largest identifiable Da on the grid,
  interpolated.
- **Mechanistic predictors:** δ from ground truth; condition number of the library
  Gram matrix and its smallest eigenvalue (S11, S53) per cell.

### 4.4 Minimum detectable effects (rule 7)
- Boundary location: the Da grid spacing is half a decade; with 20 replicates the
  standard error of P(success) at 0.5 is ≈ 0.11. **MDE for a boundary shift or a
  disc/ident gap: half a decade**, stated with every null.
- H2c factor-2 shift is 0.3 decade — **below the MDE of the 9-level grid**, so H2c is
  tested on a refined Da grid (an extra 8 levels) around the boundary found for the
  best non-EIV method. That refinement is part of the design, not a post-hoc rescue.

## 5. External anchors
- **S1 on the map.** Recompute S1's Da under §4.2's definition; plot it. If it lands in
  our failure region, the contradiction is reported and diagnosed, not explained away.
- **Real MOF-303 data (exploratory).** Apply the best method per regime to published
  MOF-303 water-uptake kinetics (S39) and the digitised Lassitter breakthrough curve
  paper 1 already uses. Labelled exploratory; no hypothesis rests on it.

## 6. Pilot (declared, excluded from all confirmatory analysis)
`p2_pilot_generator.py` → `results/p2_pilot_generator.json`: **the generator only** —
for k on a log grid, residence and run Damköhler numbers, grid convergence
(N_z 400 vs 800), breakthrough, cost. It sets the feasible Da range and grid for §4.2.
No discovery method is run before the freeze.

**What the pilot has already changed (generator facts, not outcomes):**
1. The primary Damköhler is k·t_stoich, not k·L/u (§4.2).
2. At t_final = 1.5 t_stoich the default column reaches only c/c_in ≈ 0.75 at the
   outlet — not full breakthrough. Every ground-truth solve uses a horizon long enough
   that the exit reaches 0.95, checked per solve and recorded; a solve that does not
   is extended, never truncated silently.

## 7. Compute
~80 solves; M2–M6, M8, M9 at 20 replicates over ≈ 2600 cells are seconds each; M1 and
M7 on the subgrid are the cost (≈ 200 trainings or searches). CPU-feasible. Every job
is queued in `autorun.sh` with a done-test; one training job at a time.

## 8. What would make this paper wrong
- The competitor set is weak (answered by §3's rule, audited before freeze).
- Da is not the right axis (H2a tests exactly that; Pe and isotherm shape are axes).
- The synthetic observation model is optimistic (O3 is the realistic case and is
  reported first; S8 on non-plug flow is cited as a limitation).

## 9. Amendments
(none)
