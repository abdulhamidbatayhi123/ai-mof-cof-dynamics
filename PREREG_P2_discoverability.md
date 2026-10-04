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

Let δ be the realised driving-force fraction, `max |q*(c,T) − q| / q_max` over the
observed points (computed from ground truth), and ε_eff the combined relative error of
the equilibrium the method is given (isotherm error ε), of the observations (noise σ)
and, on O2, of the uptake reconstruction (exact definitions in §4.2).

**H2a — the boundary is a driving-force-versus-error boundary.** The probability of
successful discovery, P(success), collapses onto one curve when plotted against
R = δ / ε_eff, across Da, Pe, isotherm shape and observation model (O1, O2; O3 has no
discovery method beyond M1's demonstration); the 50 % crossing
lies at R* with a spread of **less than half a decade** across conditions.
- *Falsifier:* R* spread ≥ one decade across conditions.
- *Words:* "R collapses the boundary" / "R does not collapse the boundary; the
  boundary depends additionally on {named axis}".

**H2b — discoverability versus identifiability.** For each slice (σ, ε, observation,
isotherm), compare Da*_disc (50 % crossing of P(success) for the best method) with
Da*_ident (50 % crossing of P(k practically identifiable) given the TRUE law, by the
same logistic estimator, §4.3). **Confirmatory on O1 only**, where both boundaries rest
on 20 replicates per level and the 0.25-decade MDE applies; on O2 and O3 identifiability
has 3 replicates on a subgrid, so those comparisons are reported descriptively, each
with its own bootstrap interval, and carry no verdict word.
- Three pre-declared outcomes, reported in these words:
  "discovery fails **before** identifiability" (Da*_disc < Da*_ident by ≥ the MDE),
  "discovery fails **with** identifiability" (|difference| < MDE),
  "discovery **outlives** identifiability" (Da*_disc > Da*_ident by ≥ MDE — the method
  finds the law's form where its coefficient is undetermined).

**H2c — errors-in-variables methods move the boundary.** The EIV method on the grid
(§3, M5) shifts Da*_disc by at least a factor 2 relative to the best non-EIV method at
ε > 0. Like for like: both in the strong form (M5 is strong-form only), on O1; the
best non-EIV method over both forms is reported alongside, descriptively.
- *Falsifier:* shift below the MDE at every ε > 0. *Words:* "EIV moves the
  boundary by {factor}" / "EIV does not move the boundary detectably (MDE {x})".

**H2d — the MOF case (exploratory, labelled so).** For a step (Type V) isotherm with a
rate that drops at the step (as reported for MOF-303, S39), is the state dependence
k(q) discoverable, and in which (σ, observation) cells? No directional prediction.

## 3. Methods compared — each in its strongest configuration (rule 4)

Two candidate libraries (fixed 2026-10-04, before the freeze, to the implemented and
known-answer-tested harness):
- **Lib-B (equilibrium-informed, primary):** {1, c, q, T, c·q, q², c², q*_meas}
  (`p2/features.py:lib_b`). Including q* is legitimate because it is the *measured*
  isotherm, carrying error ε — the defect of the original script (A7) was including the
  *exact* generating law. An earlier draft specified degree-3 polynomials, exp(−θ/T)
  factors and q*·q products; the tested harness uses the smaller library above. A
  smaller library makes discovery easier, so the boundaries measured here are
  **optimistic with respect to library size**, and the paper says so.
- **Lib-A (agnostic):** Lib-B without q*_meas. Under L1 the true law is not
  representable in Lib-A (q* is not polynomial), so Lib-A cannot succeed by the
  primary metric and is reported as held-out fidelity only. The agnostic route to the
  law's form is M6 (SINDy-PI) on the isothermal control, which finds the implicit
  Langmuir–LDF structure without any isotherm.

| id | method | configuration rule |
|---|---|---|
| M1 | S1's pipeline reproduced (universal differential equation + sparse regression + symbolic regression) | at least S1's settings; stronger where S1's are weak |
| M2 | weak-form SINDy (S19, S54); **M2b** is its strong-form counterpart (derivative-based regression, Savitzky–Golay dq/dt) | weak form: test-function support swept over {31, 61, 121} samples, chosen per cell by the held-out weak-system residual on every 5th probe (`p2/run_o1.py:choose_support`), then refitted on all probes. A support is admissible only if its training system has at least 3 equations per library term: on the known-answer test a long support left an under-determined weak system that fitted a wrong, dense law with zero residual, which a residual criterion would prefer. Both forms run every sparse solver (M2b, M3, M4) |
| M3 | ensemble / Bayesian SINDy (S14, S65) | inclusion probability of each term reported |
| M4 | **exact best-subset selection by enumeration** (the MIOSR objective, S55, solved exactly because the library is small) | exhaustive over sparsity ≤ 4, BIC with the declared residual floor, **unconstrained**. An earlier draft added sign constraints (k > 0, zero rate at q = q*); they are dropped before the freeze because "zero rate at q = q*" imposes the very coefficient ratio −1 the success metric tests, so M4 would succeed partly by construction. Signs are judged by the metric, as for every method |
| M5 | errors-in-variables. **On the grid: EIV best-subset** -- M4's exact enumeration with each support fitted by classical mixed LS-TLS (Golub, Hoffman & Stewart; TLS by SVD), every column weighted by its DECLARED error SD (σ × channel range; ε × q* plus its c-sensitivity; first-order propagation to products; the target's SD from the Savitzky-Golay filter's exact noise gain) -- `p2/eiv.py`, `p2_grid_extra.py m5`, full O1 grid, 20 replicates, strong form. ODR-BINDy (S13; the port reproduces the exact support on its authors' Lorenz example, accuracy pending the five-seed check below) and WENDy-IRLS (S22) are reported on their own published examples only: both learn AUTONOMOUS ODE systems (every state denoised and given its own equation), while the target here is one rate equation with exogenous c, T inside a PDE and the dominant error in a regressor (the measured isotherm); extending them would be new method development. Decided 2026-10-04, before the freeze. Known-answer tests: TLS removes the attenuation bias OLS suffers; at zero error EIV best-subset recovers L1 with M4's support |
| M6 | SINDy-PI (S21) for rational laws | run with Lib-A and NO measured isotherm, on the **isothermal control only** (exp(−ΔH/RT) is not polynomial); success = the implicit Langmuir–LDF structure {dq, c·dq, c, q, c·q} with correct signs; verified on the known-answer system (b, k recovered within 5 %) |
| M7 | constrained symbolic regression (PySR, S23) | Julia installed in the isolated `.venv`, never the base environment. **Inclusion gate (written 2026-10-04, before any M7 search):** `p2_pilot_m7.py` runs PySR (binary +, −, ×; maxsize 12; 40 iterations; PySR's own "best" model selection) on the known-answer LDF system (k = 0.02; 0.5 % noise on q AND on the measured q*) for 3 seeds. M7 runs on its subgrid iff success_L1 holds in ≥ 2 of 3 seeds AND every search finishes within 30 min AND peak memory stays under 3 GB; otherwise it is reported as NOT RUN with the pilot's numbers -- infeasible on this machine, or failing its known-answer test, in those words. The pilot is queued behind Paper 1's runs because Julia's first-import precompilation does not fit in the memory left beside them |
| M8 | KAN symbolic extraction (Liu et al.'s procedure, pykan 0.2.8; NOT a KANDy reimplementation -- its code was not opened) | secondary. **FAILS its known-answer test at zero noise in every configuration tried** (polynomial library at three sparsity penalties; raw variables on one and on three trajectories): it routes the law through q^2, uses q alone, or returns {1, q*, q*^2}. Its grid run (best configuration: raw variables, lamb 1e-3; on a subgrid of all Da × σ ∈ {0.5 %, 2 %} × ε ∈ {0, 2 %} × both isotherms × Pe ×1 × O1, 3 replicates = 216 fits) was gated on cost: it runs iff one fit at the grid's size takes ≤ 300 s (≤ 18 h for the subgrid), a rule written in `p2_pilot_costs.py` before that pilot ran. **Measured 1144 s: M8 is NOT RUN on the grid** (§10), a machine limit; it is reported on its known-answer tests, as a documented negative, never dropped |
| M9 | slow-manifold discovery (S15) | expected to win at high Da by returning isotherm + apparent dispersion; reported as *what is discoverable there* |

A method that cannot be run in its strongest configuration is reported as such,
never silently replaced by a weaker one.

**Phase A implemented and verified on a known-answer LDF system** (`p2/`,
`tests/test_p2.py`; plan `docs/superpowers/plans/2026-09-27-p2-harness-phase-a.md`):
M2b (strong-form STLSQ on standardised columns), M3 (bagged STLSQ, inclusion 0.6),
M4 (exact enumeration up to 4 terms), and the profile-likelihood tool. **Two design
facts the known-answer tests forced, declared here before the freeze:** (i) M4's BIC
carries a residual-variance floor at 2×10⁻³ × std(dq/dt), tied to the derivative
estimator's accuracy at the grid's sampling (RMS 8×10⁻⁴ at 200 times; first set at
10⁻³ from 400-sample tests, where M6 then bought a spurious q² term at zero noise on
200 samples; 2×10⁻³ is the smallest of {1, 2, 5}×10⁻³ that passes, calibrated
2026-10-04 on the known-answer system only) — because at zero noise plain BIC kept
terms of relative size 10⁻⁴ by fitting the estimator's own systematic error; (ii) the profile likelihood refines
adaptively between the coarse neighbours of its interval -- up to 6 passes of 41 points
(ODE profile) or 21 points (outlet/PDE profile), each pass narrowing to the new
neighbours (`p2/identifiability.py`) -- because at low noise the interval is narrower
than one coarse step, and a single fixed refinement collapsed onto one point below the
truth. (An earlier draft said a single 201-point refinement.) Phase B (M1, M2, M5–M9, the
cell runner, the analysis) follows its own plan.

**Which methods can see which observation model** (decided before the freeze; a
method is never run where its input does not exist):

| | O1 (c, q, T interior) | O2 (c, T interior; q latent) | O3 (outlet only) |
|---|---|---|---|
| M2, M2b, M3, M4, M6, M8 (regression on q and dq/dt) | ✔ | ✘ — q unobserved | ✘ |
| M5 EIV best-subset (mixed LS–TLS) | ✔ | ✘ | ✘ |
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
same Savitzky–Golay rule as O1 in t; in z, centred finite differences, because the
probe spacing is fixed by the observation model and no smoothing window in z may be
tuned to the answer (`p2/massbal.py`; an earlier draft said Savitzky–Golay in z too).

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
plus the adaptive refinement above only near the optimum, 3 replicates, on the §4.2
subgrid.

**Implementation audit (2026-09-25, search results — each repository must be opened
and its licence and language confirmed before the freeze):** WENDy — reference code
github.com/MathBioCU/WENDy (appears to be MATLAB) and a constrained variant
github.com/Moyi-Tian/WENDy-Constrained; ODR-BINDy — github.com/llfung/ODR-BINDy
(Zenodo release 16614238) with a Julia port github.com/jamestr4n/odr-bindy-julia;
MIOSR — github.com/wesg52/pysindy-miosr (needs a Gurobi licence, hence M4's exact
enumeration). A port to Python is acceptable only if it reproduces the original
paper's published example to the reported accuracy, recorded in a results file.

**ODR-BINDy port (2026-09-28, `p2/odr_bindy.py`, `results/odr_bindy_verification.json`).** On the authors' Lorenz example (500 points, 20 % noise) it recovers the exact 7-term support, but its relative coefficient error is 5.0e-3 against ~2.2e-3 read from the paper's Fig. 8 heatmap, and it runs ~26x slower (2385 s). Differences: Gauss-Newton with step-halving replaces lsqnonlin (SciPy least_squares, a trust-region copy and Levenberg-Marquardt all stalled on the ill-conditioned joint problem); only the default Hessian estimate is ported; the noise draw differs (MATLAB rng stream). **Status: NOT YET VERIFIED as the strongest configuration.** Before the freeze: run five noise seeds to separate single-run scatter from a real accuracy gap; if the multi-seed error still exceeds the reported figure, the PORT is reported as 'port, accuracy below the reference', with the gap stated (M5 on the grid is the EIV best-subset of §3, so this concerns the port's own verification only). The statistic compared is the MEAN relative coefficient error over the five seeds (the reported figure is itself a multi-run average), against 10^-2.65. **WENDy:** if no implementation is verified on its authors' own example before the freeze, WENDy is reported as NOT RUN, in those words; neither affects M5 on the grid.

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
| **Da = k·t_stoich** (primary Damköhler: kinetic time constants per front passage; t_stoich from the solver's `stoichiometric_time`) | 9, log-spaced over the range the pilot shows feasible, targeted 10⁻¹–10³. The residence-time form k·L/u is reported alongside but is NOT the axis: with a residence time of 0.4 s against a front passage of ≈ 7200 s, it is 0.4 s × k — 4×10⁻⁵ to 4 over the pilot's k = 10⁻⁴–10 s⁻¹ (`results/p2_pilot_generator.json`), and at most ~0.04 over the targeted kinetic range, so it cannot separate the regimes this study is about. (An earlier draft gave "10⁻⁴–10⁻³ across the whole kinetic range"; corrected before the freeze.) S1's Da is recomputed in BOTH forms |
| Pe (via D_L multiplier) | 3: ×0.2, ×1, ×5 |
| noise σ, i.i.d. Gaussian, relative to channel range | 0, 0.5 %, 2 %, 5 % |
| isotherm error ε, smooth multiplicative perturbation of q* | 0, 0.5 %, 2 %, 5 % |
| observation | O1 interior c, q, T · O2 interior c, T (q latent) · O3 outlet c(t), T(t) only |
| isotherm | favourable Langmuir · MOF-303-like step |
| true law | L1 constant k · L2 k(q) (step isotherm only) |

Noise and isotherm error are applied **after** the solve, so ground truth needs only
the (Da, Pe, isotherm, law) solves — 81, done (`p2_generate.log`: 3–7 s per solve at
the grid's k; the generator pilot measured up to ~300 s at k ≥ 0.03 s⁻¹; every solve
reached 95 % breakthrough, some after the horizon was extended). This is ground truth,
not a confirmatory result: no discovery method has seen it.
Replicates: 20 independent (σ, ε) realisations per cell for M2–M6, M9 (M8 is not run
on the grid: see its row in §3). M7 (a
Julia search per replicate, if its inclusion gate passes): 3 replicates on the subgrid
all Da × σ ∈ {0.5 %, 2 %} × ε ∈ {0, 2 %} × both isotherms × Pe ×1 × **O1** (the only
observation model M7 can see, per the applicability table). M1: the minimal
demonstration declared under "M1 feasibility — RESOLVED" below, nothing more.

**Observation model, exactly (`p2_observe.py`).** 20 equally spaced interior probes
(O1, O2) or the outlet (O3); 200 times uniform over the solved horizon. Noise:
i.i.d. Gaussian, SD = σ × the channel's range in that cell's ground truth. Isotherm
error: q*_meas = q*(c, T)·(1 + ε g(c/c_in)), g a smooth random function of 4 Fourier
modes on [0, 1] normalised to unit RMS, drawn once per replicate. Deterministic per
(cell, replicate, σ, ε, observation).

**Combined error and driving force (for H2a).** δ = max over the observed (z, t) of
|q*(c, T) − q| / q_max, computed from ground truth. ε_eff = √(σ² + ε² + ε_rec²), where
ε_rec = 0 for O1, and for O2 the RMS of (q̂ − q)/q_max of the mass-balance-inverted
uptake against ground truth on the same cell. R = δ / ε_eff per cell.

### 4.3 Metrics
- **Success (primary):** the selected support equals the true law's support **and**
  every coefficient has the correct sign. For L1 in Lib-B: exactly {q*_meas, q} with
  coefficient ratio −1 within 10 %.
- **Accuracy (secondary):** |k̂ − k| / k ≤ 10 %.
- **P(success)** per cell over replicates; **Da*_disc** from a logistic fit in log Da,
  bootstrap CI over replicates.
- **Identifiability:** profile likelihood of k with the true law known, same
  σ, ε, observation. *Practically identifiable* ⇔ the 95 % profile interval lies
  within [k/2, 2k]. Da*_ident = the 50 % crossing of P(identifiable)
  against log10 Da, by the logistic estimator of §4.4 (O1: 20 replicates per level,
  as for discovery).
- **Success for the other targets (fixed before the freeze).** M9: support {q*_meas} with
  coefficient 1 within 5 % (`p2/metric.py:success_manifold`). L2 (H2d): the operational rule
  below. Lib-A: held-out fidelity only (see §3). M9's features: {1, c, T, c², q*_meas}
  (q-free, the state q is the target). M6 on the isothermal control: library
  {1, c, q, c·q, q², c²} (Lib-A without T, which is constant there), every σ, ε = 0
  (M6 is given no isotherm, so isotherm error does not apply).
- **The 'best method' and its selection.** Da*_disc is estimated per method per slice.
  H2a and H2b use the method with the largest Da*_disc in the slice. Because that choice
  is made on the same replicates, its interval is a bootstrap that resamples replicates
  JOINTLY across methods and re-selects the best method inside every draw, so the
  interval carries the selection (the same correction as paper 1's selection-adjusted
  intervals). Every method's own Da*_disc is reported alongside.
- **R and its collapse (H2a).** R is computed per cell. Because σ and ε enter R itself,
  they are NOT slicing axes: a slice is one (Pe, isotherm, observation) combination,
  pooling every σ, ε and Da in it, and P(success) is fitted against log10 R by the same
  logistic estimator; R* is each slice's 50 % crossing; the spread is max − min of
  log10 R* over slices, with a bootstrap interval. O1 and O2 only: on O3 the sole
  discovery method is M1's single-replicate demonstration, which yields no R*.
- **ε_rec** (O2's reconstruction error inside ε_eff) is computed ONCE per cell, from the
  noise-free (σ = 0) O2 observation: it measures the inversion's structural error, the
  noise being already counted in σ.
- **L2 success, operationally.** With q*_meas held fixed, the fitted law's implied rate
  k̂(q) = −∂f/∂q is evaluated at the observed samples and averaged in 10 equal bins of
  q/q_max over the observed range. The state dependence is *discovered* iff the support
  contains q*_meas and q, k̂ decreases across the bins (Spearman ρ < −0.8), and k̂ in
  the top bin is at most 0.6 of k̂ in the bottom bin (the true k falls to 0.2).
- **Lib-A fidelity:** relative RMS error of the predicted dq/dt (strong form) on the
  held-out probes (every 5th), per cell.
- **H2c resolution.** H2c is decided at σ = 2 %: for ε = 2 % on the refined grid, for
  ε ∈ {0.5 %, 5 %} on the main grid. The 8 refinement levels lie strictly inside
  ±0.5 decade (the endpoints coincide with main-grid levels and are not repeated).
- **Isothermal control (M6).** 9 solves: the 9 Da levels × Pe ×1 × Langmuir, with the
  energy balance switched off (T held at the feed), same horizon rule; generated before
  the freeze is used, at ~seconds each.
- **Da*_ident, estimated exactly like Da*_disc.** Per replicate, k is identifiable or
  not (the [k/2, 2k] criterion); P(identifiable) is fitted against log10 Da by the same
  logistic estimator and Da*_ident is its 50 % crossing, so the two boundaries in H2b
  are measured by one estimator with the same resolution on O1 (MDE 0.25 decade, at
  20 replicates per level; O2/O3 identifiability has 3 and is descriptive).
- **Mechanistic predictors:** δ from ground truth; condition number of the library
  Gram matrix and its smallest eigenvalue (S11, S53) per cell.

### 4.4 Minimum detectable effects (rule 7)

**Estimator measured before the freeze (`p2/analysis.py`, 2026-09-28):** unpenalised
logistic ML in log₁₀ Da, 50 % crossing, percentile bootstrap within Da levels. On 100
simulated datasets with the design's grid (9 Da levels, 20 replicates) and a known
boundary: **coverage 0.94** (nominal 0.95), bias **+0.012 decade**, SD of the estimate
**0.089 decade**. A boundary
shift is resolvable at ≈ 2.8 × 0.089 ≈ **0.25 decade** (80 % power, two-sided 5 %).
The paper quotes 0.25 decade as the MDE, and the H2c refinement grid (§4.4, below)
stays as declared.

- **The MDE is 0.25 decade** (the measured estimator above), quoted with every null.
  The Da grid spacing is half a decade; the logistic estimator resolves the crossing
  well inside one grid step, which is what the measured SD shows. (An earlier draft
  also stated "MDE half a decade"; that was the grid spacing, not the estimator's
  resolution, and is withdrawn before the freeze.)
- H2c's factor-2 shift is 0.30 decade, close to the MDE, so H2c is tested on a refined
  Da grid: **8 extra levels, log-uniform within ±0.5 decade of the best non-EIV
  method's Da*_disc** at O1, σ = 2 %, ε = 2 %, for each isotherm. These need new
  ground-truth solves, made after the main grid and before any EIV method is run on
  them. The refinement is part of the design, not a post-hoc rescue.
- **Verdict words for the gaps between thresholds.** H2a: an R* spread of at least
  half a decade but less than one decade → "inconclusive: R narrows the boundary to a
  spread of {x} decades". H2c: a shift at or above the MDE but below 0.30 decade →
  "EIV moves the boundary by {factor}, detectably but by less than the predicted
  factor 2"; a shift DOWN of at least the MDE → "EIV moves the boundary DOWN by
  {factor}" (reported, a negative for H2c).

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
   (stiffness). The 81 ground-truth solves (done) took 3–7 s each at the grid's k.
5. **M1b verification (2026-09-28, a fresh solver run, not a grid cell).** From dense
   exact c (N_z = 200), the gas-balance inversion recovers q to ≤ 3 % of q_max (median
   error 0.013 against a median driving force 0.18; unchanged at N_z = 800, so not
   numerical diffusion). Fed the TRUE q, the weak-form pipeline recovers the law
   exactly at Da ≈ 14; fed the INVERTED q, it does not (it selects c², T). The inversion
   error concentrates at the front, where the kinetic signal is. Declared here because
   it bears on H2a: for O2, ε_eff must include the state-reconstruction error, and the
   analysis will report δ against it. No method or threshold was changed in response.
6. **Sampling-resolution bias of the ODE profile (2026-09-28).** On a fresh noise-free non-isothermal run, the profile's best k at an interior probe sits +0.61 % high with linear interpolation of c, T between 200 snapshots, +0.47 % with PCHIP (adopted), +0.17 % at 800 snapshots: the front crosses a probe in a few samples. Immaterial for the pre-registered identifiability criterion (interval within [k/2, 2k]); reported with the O1/O2 results, and the discovery methods face the same sampling.
7. Range: Da_run = k·t_final spans ~1 to ~10⁵ over k = 10⁻⁴–10 s⁻¹, so the targeted
   Da = k·t_stoich range 10⁻¹–10³ corresponds to k ≈ 10⁻⁵–10⁻¹ s⁻¹ at default
   physics; most of it is cheap (3–7 s per solve), but the pilot measured up to ~300 s
   per solve at k ≥ 0.03 s⁻¹, the upper end of the range.

## 7. Compute
81 ground-truth solves (done) plus the isothermal control and the H2c refinement solves;
M2–M6, M9 at 20 replicates (M8 NOT RUN on the grid, §3) over ≈ 2600 cells are seconds each; M1 and
M7 on the subgrid are the cost (≈ 200 trainings or searches). CPU-feasible. Every job
is queued in `autorun.sh` with a done-test; one training job at a time.

## 8. What would make this paper wrong
- The competitor set is weak (answered by §3's rule, audited before freeze).
- Da is not the right axis (H2a tests exactly that; Pe and isotherm shape are axes).
- The synthetic observation model is optimistic (O3 is the realistic case and is
  reported first; S8 on non-plug flow is cited as a limitation).

## 9. Amendments
(none — amendments are what changes AFTER the freeze)

## 10. Pre-freeze revisions, 2026-10-04 (before any discovery method has run on any grid cell)
Found by drafting the Registered-Report Stage-1 manuscript against this document and
the code; each fixed here, in the open, rather than silently:
1. MDE: one value, 0.25 decade (the measured estimator); "half a decade" was the grid.
2. M7/M1 subgrids made consistent with the applicability table (M7 on O1; M1 per its
   resolved minimal demonstration).
3. The residence-time Damköhler range corrected to the pilot file's 0.4 s × k.
4. Ground-truth cost corrected to the logged 3–7 s per solve; the 81 solves are done.
5. M2 (weak form) and M2b (strong form) named consistently; pilot items renumbered.
6. Lib-B fixed to the tested library (degree 2 + q*_meas), with the optimism it implies
   stated; Lib-A defined (no q*) and reported as fidelity only.
7. M4 runs unconstrained (the dropped constraint would impose the ratio the metric tests).
8. M1b's z-derivatives stated as centred differences (as implemented, and why).
9. The profile refinement stated as adaptive (as implemented, and why).
10. M6's test tightened to the stated 5 % on every coefficient (measured < 0.1 %).
11. M7's gate noise stated as applied to q and to q*_meas.
12. M2's support sweep IMPLEMENTED ({31, 61, 121}, held-out probes, with a well-posedness
    rule the known-answer test showed is needed), not dropped.
13. δ, ε_eff (including O2's reconstruction error) and R defined.
14. Success defined for M9, for L2 (H2d) and for Lib-A.
15. "Best method" defined, with a selection-carrying bootstrap; R-binning defined.
16. Da*_ident estimated by the same logistic estimator as Da*_disc.
17. Verdict words added for the gaps between thresholds (H2a, H2c).
18. H2c's 8 refinement levels placed by rule (±0.5 decade around the best non-EIV
    Da*_disc at O1, σ = ε = 2 %).
19. The observation model's exact settings written here (20 probes, 200 times, the
    4-mode isotherm error).
20. M5's five-seed statistic fixed (mean), and WENDy's NOT-RUN rule stated.
Third pass, same day (from the re-synced Stage-1 draft): the M5, M8 and L2 rules each
appeared in two versions after the second pass; the old ones removed (M5 = EIV
best-subset on the grid, the ODR-BINDy port and WENDy on their own examples only; M8's
subgrid and 300 s cost rule written into its row, and its NOT RUN outcome; one L2
rule). δ over the observed points; H2a's observation models named (O1, O2); H2c made
like-for-like (strong form, O1); M6's and M9's exact libraries and M6's ε = 0 stated;
the O1 restriction of the 0.25-decade MDE stated; stale cost numbers removed.
Second pass, same day (from the revised Stage-1 draft): one Da*_ident definition (the
logistic crossing); H2b confirmatory on O1 only, O2/O3 descriptive; H2a slices by (Pe,
isotherm, observation) with σ, ε inside R, O3 excluded; ε_rec defined; L2 success made
operational; Lib-A fidelity defined; H2c's resolution per ε and its level placement
made exact; the isothermal control given a grid; stale text removed.
**M8 cost gate, measured 2026-10-04 (`p2_pilot_costs.py`, `results/p2_cost_gates.json`):**
one fit at the grid's size took 1144 s against the declared 300 s limit (216 fits ~ 69 h),
so **M8 is NOT RUN on the grid**, a machine limit in those words. Measured while the
machine was shared with other long jobs, which the paper states; on the same
known-answer data the fit returned only a constant, consistent with M8's documented
known-answer failure. M8 is reported on its known-answer tests only.
**M5, decided 2026-10-04 before the freeze:** EIV best-subset on the grid (see §3 M5),
because ODR-BINDy and WENDy as published apply to autonomous ODE systems, not to a
single rate law with exogenous inputs and regressor error; H2c is tested with it.
**Verdict driver (2026-10-04):** `p2_analyze.py` computes H2a-H2d from the result files
exactly as §2/§4.3/§4.4 state (H2b per (σ, ε, isotherm) on O1, O2 descriptive; H2a
per (Pe, isotherm, observation) with R undefined at σ = ε = 0 on O1 and excluded; H2c
per (isotherm, ε > 0) at σ = 2 %, strong form; H2d descriptive), and is tested on a
simulated grid with planted boundaries before any real result exists.
**O1 identifiability (2026-10-04):** no driver computed it, though H2b's confirmatory
test is on O1. Now `p2_grid_extra.py o1ident`: the profile likelihood with the law
known over ALL 20 probes (information parity with discovery), the measured isotherm,
every non-isothermal L1 cell, every (σ, ε), 20 replicates. The ODE-solver likelihood
took ~540 s per replicate (~860 h for the design); it is evaluated instead by the exact
update of the linear LDF law between samples (q* piecewise linear on a 4x PCHIP
upsample), vectorised over k: 4.5 s per replicate, ~22 h. Tested: agreement with the
ODE likelihood (relative 1e-5 to 1e-3) and the known-answer interval contains k.
**Analysis code (2026-10-04):** `p2/analysis.py` now has the rising-curve rule for R
(a first version would have returned 'no crossing' for every H2a condition), the
selection-carrying best-method bootstrap, and the H2c words; H2c gains the pre-declared
words for a shift DOWN: "EIV moves the boundary DOWN by {factor}".
**Code owed before the freeze:** the O2 profile likelihood in `p2_grid_o23.py`
(listed in the table) -- DONE 2026-10-04 (`p2/identifiability.py:profile_interval_probes`,
`p2_grid_o23.py o2ident`, known-answer test). **Grid runners still owed** (found by
checking the drivers against §3: they run only M2/M2b, M3 and M4): M6 on the
isothermal control, M9, M8, M5, M7 and the L2 cells -- ALL WIRED 2026-10-04
(`p2_grid_extra.py` m5/m6/m7/m8/m9/l2; every runner refuses to start before the freeze):
M5 as EIV best-subset (no cost gate needed: linear algebra), M7 behind its inclusion
gate, M8 behind its cost gate (which it failed: NOT RUN on the grid). Done 2026-10-04: the
isothermal-control ground truth (9 cells in `data/p2`; isotherm at T_in identical to
the Langmuir cells, max |T - T_in| = 0, all reached 95 % breakthrough); the L2 success
metric and the Lib-A fidelity metric (`p2/metric.py`, tested).
