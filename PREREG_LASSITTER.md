# Pre-registration — the solver against a published MOF-303 breakthrough curve

**Written 2026-09-03, before the comparison is run.** Committed to git before the
run. Frozen; changes go in `RETRACTIONS.md`.

## 1. What is being compared, and what is not

**The reference solver (L0) with the cited MOF-303 parameters, against Fig. 10 of
Lassitter et al., *Chem. Eng. Sci.* 285:119430 (2024)** — the only published
MOF-303 packed-bed breakthrough curve whose conditions are fully on record (their
SI Table S8; digitised in `refs/Lassitter2024_fig10_digitised.csv`, see
`CITATIONS.md`). This is **not a rung of the ladder** and it tests **no
surrogate**. It asks one thing: does the physics model that generated every
dataset in this project reproduce a real MOF-303 bed's two-wave breakthrough, with
**no parameter fitted to the curve**?

**No parameter is fitted.** Every input is either cited (isotherm capacity, heat,
step position — `fetch_real_mof_data.get_mof303_physics`), taken from the SI
(bed geometry, flow, humidity, temperature, bulk density, porosity), or swept over
a **declared band** because the source does not give it. Anything else would be a
fit, and would be reported as one.

## 2. Inputs

| quantity | value | source |
|---|---|---|
| bed height L | 0.00635 m | SI Table S8 |
| tube diameter D_in | 0.0381 m | SI Table S8 (R = 0.01905 m) |
| superficial velocity v | 0.0098062 m s⁻¹ | SI Table S8 (Q / A_c) |
| temperature T_in = T_w | 298.15 K | SI Table S8 |
| feed | 32.8 % RH → c_in by our Tetens `rh_to_conc` (≈ 0.418 mol m⁻³; the SI's 0.42212 uses P_sat 3190 Pa, 0.9 % apart) | SI Table S8 |
| bulk density (1 − ε_t) ρ_p | 429.58 kg m⁻³ | SI Table S8 |
| bed porosity ε_t | 0.4 → ρ_p = 716.0 kg m⁻³ | SI Table S8 (marked "estimated" by the authors) |
| isotherm | cited MOF-303 form: q_max 25.0 mol kg⁻¹, ΔH −50.5 kJ mol⁻¹, step at 15 % RH, n = 4, Henry fraction 0.06 | `get_mof303_physics` (A4 discharge; the two shape parameters are fitted to the step and capacity, **not** to any breakthrough curve) |
| horizon | 600 min, 1200 snapshots | the figure's axis |

**Declared bands** (the source gives none of these):

| quantity | band | primary | why |
|---|---|---|---|
| k_LDF (s⁻¹) | {0.011, 0.05, 0.20} | **0.20** | SI Table S2: 0.24 at 26 % RH, 0.18 at 40 % RH bracket the feed; 0.011 is the minimum at the step |
| pellet diameter d_p (mm), enters only the Ruthven dispersion | {1, 3, 5} | **3** | pressed binder-free pellets, size not given |
| thermal | isothermal (h_w = 10⁴ W m⁻² K⁻¹) vs the dataset's h_w = 10 with C_ps ∈ {900, 1000, 2400} J kg⁻¹ K⁻¹ | **isothermal** | their own model is isothermal ("trace adsorbate"); a 6 mm bed in a metal tube is close to it; C_ps has no citable value (A4) |

Grid: N_z = 500 (dz = 12.7 µm); convergence checked at 250 / 500 / 1000 for the
primary configuration and reported as the max change in exit RH.

## 3. What is reported — descriptive, no verdict on the ladder

For the primary configuration and every band member, against the 37 digitised
effluent points (the four on the axis line at RH 0 included):

1. **shape**: is there an intermediate plateau (effluent between 15 % and 45 % of
   the inlet for at least 60 min before the shock)? The experiment has one at
   0.27–0.32 of the inlet from 146 to 250 min.
2. **plateau level**: mean effluent over 150–250 min, as a fraction of the inlet.
   This is a *prediction* of the fitted Henry fraction (0.06), which was never fitted
   to a dynamic measurement.
3. **arrival times** at 5 %, 50 % and 95 % of the inlet, model vs experiment
   (experiment: 83 / ≈ 300 / ≈ 350 min from the digitised points).
4. **nRMSE** of the model's exit RH at the experimental times, normalised by the
   inlet RH; and the same number for the authors' COMSOL line, so the reader can
   see how a fitted 2-D model with CSFR kinetics does on the same points.

**Pre-declared reading.** The solver "reproduces the experiment" only if the primary
configuration shows the plateau (1), puts the 50 % arrival within ±20 % of the
observed time, and puts the plateau level within a factor of 1.5 of the observed
one — with no parameter moved. Anything else is reported as a discrepancy, with
the band member that comes closest named as a *sensitivity*, never as a fit.
Whatever the outcome, the paper's error budget must say that this is
solver-vs-experiment at one condition on a 6.35 mm bed with an aspect ratio of
0.17, where a 1-D plug-flow model is at the edge of its validity, and that every
surrogate number in the paper is surrogate-vs-solver.
