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
| M6 | SINDy-PI (S21) for rational laws | run with Lib-A and NO measured isotherm, on the **isothermal control only** (exp(−ΔH/RT) is not polynomial); success = the implicit Langmuir–LDF structure {dq, c·dq, c, q, c·q} with correct signs; verified on the known-answer system (b, k recovered within 5 %) |
| M7 | constrained symbolic regression (PySR, S23) | Julia installed in the isolated `.venv`, never the base environment |
| M8 | KAN + sparse regression (KANDy, S48) | secondary; not a headline (L3, S49) |
| M9 | slow-manifold discovery (S15) | expected to win at high Da by returning isotherm + apparent dispersion; reported as *what is discoverable there* |

A method that cannot be run in its strongest configuration is reported as such,
never silently replaced by a weaker one.

**Phase A implemented and verified on a known-answer LDF system** (`p2/`,
`tests/test_p2.py`, 8 tests; plan `docs/superpowers/plans/2026-09-27-p2-harness-phase-a.md`):
M2 (strong-form STLSQ on standardised columns), M3 (bagged STLSQ, inclusion 0.6),
M4 (exact enumeration up to 4 terms), and the profile-likelihood tool. **Two design
facts the known-answer tests forced, declared here before the freeze:** (i) M4's BIC
carries a residual-variance floor at 10⁻³ × std(dq/dt) — the derivative estimator's
verified accuracy — because at zero noise plain BIC kept terms of relative size 10⁻⁴
by fitting the estimator's own systematic error; (ii) the profile likelihood refines
on a 201-point grid between the coarse neighbours of its interval, because at low
noise the interval is narrower than one coarse step. Phase B (M1, M2-weak, M5–M9, the
cell runner, the analysis) follows its own plan.

**Which methods can see which observation model** (decided before the freeze; a
method is never run where its input does not exist):

| | O1 (c, q, T interior) | O2 (c, T interior; q latent) | O3 (outlet only) |
|---|---|---|---|
| M2, M2b, M3, M4, M6, M8 (regression on q and dq/dt) | ✔ | ✘ — q unobserved | ✘ |
| M5 EIV (ODR-BINDy, WENDy) | ✔ | ✘ | ✘ |
| M7 PySR on (features → dq/dt) | ✔ | ✘ | ✘ |
| M9 slow-manifold | ✔ | ✘ | ✘ |
| M1 UDE (network in the uptake term, trained through the PDE) + sparse/symbolic readout | ✔ | ✔ | ✔ |
| profile likelihood (law known) | ✔ ODE per probe | ✔ PDE forward solve | ✔ PDE forward solve |

**Added 2026-09-28 — M1b, mass-balance inversion (O2).** From interior c(z,t) the
uptake rate follows from the gas-phase balance,
`∂q/∂t = −ε/((1−ε)ρ_p) · (∂c/∂t + u ∂c/∂z − D_L ∂²c/∂z²)`, with q recovered by time
integration from q(z,0) = 0. That is how an experimentalist with interior probes gets
uptake, it needs no training, and every O1 method then runs on it; it is therefore the
strongest O2 competitor and must be included. Its derivatives are estimated with the
same Savitzky–Golay rule as O1, in both z and t.

**M1 feasibility (declared, not yet resolved).** A network inside the column model
trained through the PDE needs a differentiable solve over ~4 t_stoich (≈ 8 h of
process time); an explicit scheme is CFL-bound at ~4 ms, so ~10⁶–10⁷ steps per epoch
— infeasible on this CPU. The route is an implicit differentiable solver (JAX +
diffrax, Kvaerno5, in `.venv`), whose cost is measured by a timing pilot on one cell
before the freeze. If one training cannot finish in ≤ 2 h at N_z = 50 (grid
convergence checked against N_z = 400 on the same cell), M1 runs on a declared
reduced subgrid, or is reported NOT RUN on O3 — the realistic observation model then
rests on profile likelihood alone, and the paper says so.

**M1 feasibility — RESOLVED by the pilot (`p2_pilot_m1.py`, `results/p2_pilot_m1.json`,
2026-09-28).** The JAX column (`p2/jaxcol.py`) matches `solver_fd` to < 5×10⁻³ on the
exit curve; N_z = 50 differs from N_z = 400 by 0.55 %. Cost on this CPU: forward
solve 22 s, gradient w.r.t. k 101 s, gradient w.r.t. a 2×32 MLP rate **145 s** — i.e.
~50 training steps in the 2 h budget, where a UDE needs hundreds to thousands. By
the rule declared above, **M1 is NOT RUN at the declared scale.** It runs only as a
labelled demonstration on a minimal subgrid (Langmuir, Pe ×1, σ = 2 %, ε = 0, O3,
the 9 Da levels, one replicate, L-BFGS, ≤ 50 steps), and **the O3 comparison rests
on profile likelihood**. The paper states this, and states that it is a compute
limit, not a finding about UDEs: on a GPU the same code is expected to be feasible.

So the O2/O3 comparison is M1 against identifiability, and it is where the
experimentally realistic answer lives; O1 is the optimistic ceiling for everything
else. In O2/O3 the profile likelihood needs a PDE solve per k: coarse 25-point k grid
plus the 201-point refinement only near the optimum, 3 replicates, on the §4.2
subgrid.

**Implementation audit (2026-09-25, search results — each repository must be opened
and its licence and language confirmed before the freeze):** WENDy — reference code
github.com/MathBioCU/WENDy (appears to be MATLAB) and a constrained variant
github.com/Moyi-Tian/WENDy-Constrained; ODR-BINDy — github.com/llfung/ODR-BINDy
(Zenodo release 16614238) with a Julia port github.com/jamestr4n/odr-bindy-julia;
MIOSR — github.com/wesg52/pysindy-miosr (needs a Gurobi licence, hence M4's exact
enumeration). A port to Python is acceptable only if it reproduces the original
paper's published example to the reported accuracy, recorded in a results file.

**Opened 2026-09-27:** ODR-BINDy (llfung) is MATLAB, requires R2024a+, ships
Lorenz / Rössler / Van der Pol / nonlinear-oscillator examples and a LICENSE file;
the authors state a Python/Julia package does not yet exist. WENDy (MathBioCU) is
MATLAB; its README says Figures 3–7 reproduce from `wendy_script.m`; no licence was
visible on the page (to be checked in the file listing before use). **MATLAB is not
installed on this machine** (a stale PATH entry only). Route, in order: (1) the Julia
port of ODR-BINDy via `juliacall` in `.venv`, verified on the Lorenz example; (2) a
Python port of each, verified on the authors' own example to the paper's reported
accuracy; (3) if neither can be verified, the method is reported as NOT RUN in its
strongest form — never replaced silently.

## 4. Design

### 4.1 Ground truth
The verified reference solver of paper 1 (`solver_fd.py`; L0 checks in
`verify_solver.py`). The rate law is `dq/dt = k(q*(c,T) − q)` (L1) or, for H2d,
`dq/dt = k(q)(q* − q)` with k dropping across the step (L2). Non-isothermal physics
as in paper 1 (primary); an isothermal control is secondary.

**L2 exactly:** `k(q) = k0 · [1 − 0.8 · σ((q/q_max − θ) / 0.05)]`, σ the logistic
function, θ the fractional loading at the isotherm's step midpoint (computed from the
isotherm at the feed temperature, recorded per solve). The rate falls to 20 % of k0
across the step. Implemented through `solver_fd`'s `k_of_q` hook, whose default path
is verified unchanged. **Isotherms:** "Langmuir" = default physics (`isotherm_n = 1`);
"step" = `fetch_real_mof_data.get_mof303_physics()` (cited MOF-303 step position and
capacity), with column geometry and flow held at the default so only the isotherm
changes. Ground truth is written to `data/p2/` (gitignored) with a manifest recording
every parameter, t_stoich, horizon, and the per-solve breakthrough check.

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

**Estimator measured before the freeze (`p2/analysis.py`, 2026-09-28):** unpenalised
logistic ML in log₁₀ Da, 50 % crossing, percentile bootstrap within Da levels. On 100
simulated datasets with the design's grid (9 Da levels, 20 replicates) and a known
boundary: **coverage 0.94** (nominal 0.95), bias **+0.012 decade**, SD of the estimate
**0.089 decade**. The half-decade MDE below is therefore conservative; a boundary
shift is resolvable at ≈ 2.8 × 0.089 ≈ **0.25 decade** (80 % power, two-sided 5 %).
The paper quotes 0.25 decade as the MDE, and the H2c refinement grid (§4.4, below)
stays as declared.

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
3. Why 1.5 t_stoich stops at 0.76: the **thermal wave** — the outlet is still ~9 K
   above feed at 1.5 t_stoich. At k = 0.01 s⁻¹ the 95 % crossing is at 2.2 t_stoich
   and a 4 t_stoich horizon reaches c/c_in = 1.00. **Default horizon: 4 t_stoich**,
   subject to the per-solve 0.95 check. (The thermal delay is itself a reason H2a
   carries T: the rate law's driving force depends on q*(c,T).)
4. Grid: the exit curve changes ≤ 0.11 % between N_z 400 and 800 at every k tested
   (10⁻⁴–10 s⁻¹), so N_z = 400 is adequate; the harness's 2 % tolerance is met with
   margin. Cost at N_z 400: 2–20 s for k ≤ 10⁻², rising to ~15 min at k = 3–10 s⁻¹
   (stiffness). The ~80 ground-truth solves are therefore ≲ 10 h worst case.
6. **M1b verification (2026-09-28, a fresh solver run, not a grid cell).** From dense
   exact c (N_z = 200), the gas-balance inversion recovers q to ≤ 3 % of q_max (median
   error 0.013 against a median driving force 0.18; unchanged at N_z = 800, so not
   numerical diffusion). Fed the TRUE q, the weak-form pipeline recovers the law
   exactly at Da ≈ 14; fed the INVERTED q, it does not (it selects c², T). The inversion
   error concentrates at the front, where the kinetic signal is. Declared here because
   it bears on H2a: for O2, ε_eff must include the state-reconstruction error, and the
   analysis will report δ against it. No method or threshold was changed in response.
7. Range: Da_run = k·t_final spans ~1 to ~10⁵ over k = 10⁻⁴–10 s⁻¹, so the targeted
   Da = k·t_stoich range 10⁻¹–10³ corresponds to k ≈ 10⁻⁵–10⁻¹ s⁻¹ at default
   physics — inside the cheap part of the cost curve.

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
