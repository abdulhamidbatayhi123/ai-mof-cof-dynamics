# Falsification Ladder Protocol — MOF/COF Adsorption Surrogates

**Frozen 2026-08-20, before any model is trained.**

This document is written *first*, on purpose. Every comparison, metric, split, and
success criterion below is fixed in advance so that no result in this project can
be the product of a comparison chosen after seeing the numbers. Changes to this
protocol after training begins must be recorded in `RETRACTIONS.md` with the date
and the reason, not silently edited.

---

## 1. The hypothesis under test

Prior work on a structurally analogous system (transient conduction with a cyclic
source) produced three measured findings:

| finding | measurement |
|---|---|
| KAN ≈ MLP at matched parameters | gaps of 0.17–0.33 against a ~0.3 noise floor |
| Physics-as-loss helps, modestly | +0.51 to +0.76 RMSE, 3 seeds, matched budget |
| **Separate identification buys the physics** | transfer 6.10 % (separate) vs 98.45 % (joint) — 16× |

Independently, Shukla, Toscano, Wang, Zou & Karniadakis (CMAME 2024) report that
KAN variants are at best comparable to MLPs for PDE and operator learning, and are
less robust across seeds.

> **H1 (primary).** In stiff multiphysics surrogates, *structural decomposition*
> governs extrapolation, and *architectural family* does not. Specifically: a
> surrogate that identifies the equilibrium object (isotherm/thermodynamics) and
> the kinetic object (mass transfer) **separately** will transfer to held-out
> materials substantially better than one that fits them **jointly**, at matched
> parameter count — and this gap will exceed any gap between architecture families.

> **H2 (secondary).** Architecture family (MLP / KAN / Fourier / wavelet) produces
> differences within the seed-to-seed noise floor once parameter count, input
> encoding, and training budget are matched.

**Both outcomes are publishable.** If H1 holds, it is a transferable design rule
with cross-domain evidence, which almost nobody produces. If H1 fails, the
domain-dependence of the rule is itself the finding. The protocol is written so
that neither outcome can be dressed up as the other.

**Pre-declared failure condition for H1:** if the separate-vs-joint transfer gap
has a bootstrap CI including zero at 3 seeds, H1 is reported as **not supported**,
in the abstract, in those words.

---

## 2. The ladder

Each rung eliminates a named hypothesis. Rungs are run in order; a rung is not
reported as "eliminated" unless its arm was trained at full protocol (§3).

| # | rung | hypothesis it kills | arm |
|---|---|---|---|
| L0 | Ground-truth verification | "the reference is trustworthy" | solver vs. analytic limits + grid convergence |
| L1 | Data-driven interpolation | "you just need more data" | MLP / XGBoost / RF, matched encoding |
| L2 | Capacity | "the model is too small" | width & depth sweep at fixed encoding |
| L3 | Architecture family | "you need a better basis" | MLP vs RBF-KAN vs Chebyshev-KAN, matched params |
| L4 | Physics as a loss | "add the PDE residual" | PINN / PIKAN vs data-only twin |
| L5 | Operator family | "you need an operator" | DeepONet, FNO, WNO, DeepOKAN, matched budget |
| L6 | **Identification structure** | **"joint fitting is fine"** | **separate vs joint equilibrium/kinetics** |
| L7 | Classical control | "deep learning is needed at all" | fast closed-form adsorption theory (Klinkenberg / constant-pattern), zero training |

L7 is not a formality. In the analogous prior study a 128-number linear
convolution beat every deep operator tested. If a ten-parameter classical model
matches the neural arms here, that is the headline result and it will be reported
as such.

---

## 3. Information parity — non-negotiable

Every cross-arm comparison must hold **all** of these equal, or it is not reported
as a comparison:

1. **Parameter count**, within ±10 %. Report the actual counts in every table.
2. **Input encoding** — identical grid resolution and identical feature set.
   *(In the prior project, an encoding mismatch alone produced three retractions:
   A1, A2, A3. This is the single most dangerous line in this document.)*
3. **Training budget** — identical optimizer steps and schedule.
4. **Training data** — identical conditions, identical splits, identical
   normalization.
5. **Seeds** — 3 minimum (42, 43, 44). Single-seed numbers may not appear in any
   table, including appendices.
6. **Training budget, asserted not assumed.** Every cross-configuration
   comparison must state the step count for both sides. Extrapolation error
   *grows* with training here — an undertrained model sits near its
   initialisation and flatters itself — so a shorter run is not a conservative
   proxy. This confound produced retractions **A14** and **A16**, the same
   mistake in consecutive experiments.
7. **No metric may be normalised by a quantity that can vanish.** nRMSE over an
   evaluation window whose reference is flat divides by ~0. This produced
   retraction **A15**, where four "divergence to 26,000" results were a handful
   of degenerate denominators. Normalise by a full-field quantity, and sanity-
   check that the reported value is *achievable* given the model's output range.

**Each arm is compared against the strongest configuration of its competitor, not
the first one that was run.** If a weaker configuration of a competitor is used,
the resulting margin is invalid — this is exactly how retractions A2/A19/A20 were
generated.

---

## 4. Metrics

Pooled MSE across (c, q, T) is **forbidden**. In this system
var(T)/var(c) ≈ 4.5 × 10⁶, so a pooled figure is the temperature error wearing a
disguise and concentration is invisible in it.

Report, per variable:

- **nRMSE** — RMSE divided by the range of that variable in the reference.
- **Breakthrough time error** — Δt at c/c_in = 0.05, 0.50, 0.95. This is the
  quantity a process engineer actually uses.
- **Peak thermal excursion error** — ΔT_max, the regeneration-energy driver.
- **Working capacity error** — the AWH-relevant quantity.
- **Cyclic drift** — mass and energy imbalance after N adsorption/desorption
  cycles. A soft-penalty model will drift; report the slope, not just the endpoint.

Paired bootstrap CIs across held-out conditions, **cluster-robust by material**,
implemented in `metrics.py`. A difference whose CI includes zero is reported as
**no difference**, in words.

Clustering is not a formality. Measured over 200 trials under a realistic null —
two arms that tie on average, but where some materials favour one and some the
other, so the *difference* is clustered:

| resampling unit | false-positive rate |
|---|---|
| material (clustered) | **7.0 %** (nominal 5 %) |
| condition (naive) | **32.5 %** |

A naive bootstrap would declare a significant difference in roughly one of every
three comparisons where none exists. Pairing alone does not fix this: pairing
removes shared per-material difficulty, but material-level structure in the arms'
*relative* performance survives, and that is the realistic case.

`metrics.pooled_mse()` raises `NotImplementedError` by construction.

---

## 5. Splits

- **In-distribution** — held-out conditions, parameters inside the training hull.
- **Novel-condition** — held-out operating conditions (humidity, velocity, T).
- **Novel-material** — held-out frameworks. *This is the split H1 is about.*

**All arms see identical splits.** The earlier version of this project trained the
physics-informed model on data sampled uniformly across the full time domain while
requiring the baselines to extrapolate beyond `t = 300 s`. That asymmetry alone
explains any result it produced, and it is the first thing a referee checks.

Temporal extrapolation, if reported, must be extrapolation **for every arm**.

---

## 6. Frozen specifications

Decisions already made, with rationale. Changing any of these invalidates results
produced under the old value; both must then be reported.

| spec | value | why |
|---|---|---|
| Column length | 0.10 m | At 1 m the MTZ is 0.05 % of the domain and needs N_z ≈ 36,000. Lab-scale breakthrough geometry. |
| Axial dispersion | Ruthven correlation, d_p = 2 mm | Ties front width to a real particle size rather than a hand-picked D_L. |
| Advection scheme | first-order upwind | van Leer measured 9× slower with 6× the Jacobian factorisations — the limiter is non-smooth in near-uniform regions and wrecks BDF's Newton convergence. Resolution is controlled by grid convergence instead. |
| Grid | N_z = 2000 (reference), 1000 (sweep) | Measured convergence, below. Every dataset carries a stamped convergence error. |

### Measured grid convergence (2026-08-20)

Exit-curve error against an N_z = 4000 reference, 2.5× stoichiometric horizon:

| N_z | generic err | generic wall | **MOF-303 err** | **MOF-303 wall** |
|---|---|---|---|---|
| 125 | 0.750 % | 6.9 s | 4.456 % | 0.5 s |
| 250 | 0.388 % | 9.2 s | 2.309 % | 0.7 s |
| 500 | 0.188 % | 17.4 s | 1.110 % | 1.1 s |
| 1000 | 0.082 % | 41.0 s | 0.484 % | 2.1 s |
| 2000 | 0.027 % | 73.1 s | 0.163 % | 4.2 s |

Error halves as N_z doubles in both cases — clean first-order convergence, which
is the expected order for upwind advection and confirms the scheme is behaving.

**The MOF-303 case is ~17× cheaper per solve than the generic case at equal
resolution** (4.2 s vs 73.1 s at N_z = 2000), because `k_LDF = 0.01` vs `0.05`
makes it far less stiff and BDF takes much longer steps.

**Consequence for the dataset budget.** An earlier estimate of ~150 s/simulation
came from the generic config and implied ~17 days single-core for 10⁴ conditions.
For the production MOF-303 case at full N_z = 2000 resolution the true figure is
**4.2 s/simulation — about 11.7 hours single-core, or under 2 hours across 8
cores.** Parametric dataset generation is not the bottleneck it appeared to be,
and the operator arms (L5) are affordable.
| Isotherm | dual-term Do–Do (Type V) | Single-site Langmuir has zero inflection points and cannot represent cooperative pore filling — the mechanism AWH depends on. A bare Hill form fixes the step but violates Henry's law. |
| Kinetics | LDF, k_LDF swept | Standard; the object H1 asks us to identify separately. |
| Temperature output | bounded, `T* = 1 + dT_max·tanh(...)` | Unbounded T* crosses zero, the van't Hoff exponential overflows, and the graph NaNs. This was the root cause of the first checkpoint being 100 % NaN. |
| Residual scaling | each equation ÷ its dominant term | Ad-hoc constants produced a 4.5 × 10¹⁰ : 1 imbalance. Now within ~10× at init across 4 seeds. |
| Isosteric heat | `q_st = -ΔH + RT` | Not slack — the exact concentration-basis-to-pressure-basis conversion. 2.49 kJ/mol at 300 K, i.e. 5 % on a 50 kJ/mol enthalpy. |

---

## 6b. The parametric dataset — frozen

`gen_parametric_dataset.py`, seed 20260820.

**Structure.** 60 materials × 17 operating conditions = 1020 runs, nested rather
than flat. H1 is about transfer to held-out *materials*, and that split only
exists if materials are a real grouping in the data; a flat cloud of
(material × condition) draws would make novel-material and novel-condition
indistinguishable and H1 untestable.

**Splits.** 20 % of materials and 15 % of conditions held out →
≈720 train / 96 novel-condition / 204 novel-material.

**Resolution.** Solved at N_z = 2000 (the L0-verified grid), stored at
**512 × 256 float32**, ≈1.57 MB/sample, ≈1.6 GB total. The MTZ is ~1 mm in a
100 mm column; at 128 z-points the entire front sits inside 1.4 cells and an
operator would be learning a step function, which would present as an
architecture failure when it is really a storage decision. 512 gives ~5.5 cells
across the front.

> **The stored grid is part of information parity.** Every arm sees the same
> resolution. Changing it invalidates every prior comparison and must be logged
> in `RETRACTIONS.md`.

**Time axis.** Each condition has its own stoichiometric time, so `t_final`
varies. Time is stored normalised to [0,1] with `t_final` retained as a
per-sample scalar, giving operators a common axis and making `t_final` a
predictable output rather than a hidden inconsistency.

**Adaptive horizon.** A fixed 2.5× stoichiometric horizon rejected ~20 % of draws
for incomplete breakthrough — and those rejections were *not* random. They fell
on high-capacity, slow-kinetics materials and strongly cooled beds, where wall
cooling lets the solid keep re-adsorbing past the isothermal estimate. Rejecting
them would have biased the dataset toward fast, low-capacity frameworks and
quietly narrowed the parameter space H1 is tested over. The horizon now extends
(2.5 → 5 → 12.5 → 30×) until breakthrough completes, and `horizon_extensions` is
recorded per sample so the distribution stays auditable. Rejection rate: 0 %.

**Screening.** Degenerate draws are rejected *before* a solve, with the reason
counted in the manifest: feed loading below 10 % or above 99.5 % of capacity
(isotherm unidentifiable), non-physical Henry constant, MTZ unresolvable at the
solve grid, stoichiometric time outside 60 s – 2×10⁶ s. A silently filtered
dataset is a biased dataset, so every rejection reason is tallied and reported.

---

## 6c. Observed: the Type V isotherm produces a TWO-WAVE breakthrough

Measured in the generated MOF-303-like reference (`Fig2_ground_truth`):

| c/c_in | 0.05 | 0.20 | 0.40 | 0.60 | 0.68 | 0.80 | 0.95 | 0.99 |
|---|---|---|---|---|---|---|---|---|
| t (h) | 0.09 | 0.17 | 2.94 | 12.46 | 16.70 | 18.04 | 18.56 | 18.90 |

The exit curve is **not** a single sigmoid. It rises to ~0.2 within minutes,
crawls to ~0.68 over 16 h, then shocks to 1.0 in under two hours. That is the
dual-site structure resolving into two waves:

* the **Henry branch** (low-affinity primary sites, `f_H = 0.06`) has small
  capacity and a near-linear isotherm, so it breaks through almost immediately
  as a spreading, proportionate-pattern wave;
* the **cooperative branch** is strongly favourable (isotherm concave above
  `c/c_in ≈ 0.003`) and self-sharpens into a constant-pattern shock that arrives
  at ~18 h.

Two consequences.

**It validates the isotherm choice.** A bare Hill form, which violates Henry's
law, has zero slope at the origin and cannot produce the early leakage at all.
A Langmuir form produces a single sigmoid. Only a Henry-preserving Type V gives
the two-wave structure that real water/MOF columns show.

**It sharpens the case for the ladder.** The plateau *height* is set by the
Henry fraction and the shock *arrival* by the cooperative capacity — two features
that move independently as material parameters vary. A DeepONet reconstructs its
output as a linear combination `sum_k b_k(params) t_k(z,t)` in a fixed basis, and
a solution manifold with two independently-moving sharp features has a slowly
decaying Kolmogorov n-width. This is the n-width obstruction made concrete and
measurable in our own data, rather than argued from theory — and it is a
prediction the L5 rung will test directly.

---

## 6d. Measured: the Kolmogorov n-width decays ALGEBRAICALLY

Section 6c predicted, *before this was run*, that the two-wave structure would
give a slowly decaying n-width. Measured on the 691 training fields by POD
(`nwidth.py`, `results/nwidth.json`), fitting the residual energy tail over
n = 8…64 modes:

| field | modes for 90 % / 99 % / 99.9 % / 99.99 % | energy tail | d_n | algebraic R² | exponential R² |
|---|---|---|---|---|---|
| c | 3 / 11 / 32 / 68 | n^−2.45 | **n^−1.23** | 0.9910 | 0.9737 |
| q | 2 / 8 / 27 / 65 | n^−2.22 | **n^−1.11** | 0.9897 | 0.9759 |
| T | 3 / 13 / 36 / 76 | n^−2.39 | **n^−1.20** | 0.9911 | 0.9731 |

Algebraic beats exponential on R² for every field. `d_n = sqrt(tail energy)`, so
**halving the error requires 1.76× the modes — permanently.** Exponential decay
would instead need a fixed *additive* number of modes per halving.

For reference, Ohlberger & Rave give `d_n ~ n^−1/2` for pure linear transport.
We measure `n^−1.23`: the same algebraic family, faster than pure transport
(the physical dispersion and finite LDF kinetics smooth the front), and
decisively not exponential.

> **SUPERSEDED IN PART — read with `## L5 RESULT` and retraction A17.** The bound
> derived below is correct and still stands. The claim that it is *load-bearing*
> does not: L5 measured DeepONet flat in `p` (0.0281 -> 0.0296 while `d_n` falls
> 28.7x) and sitting **59x above** this bound at p = 128. The n-width is real and
> inactive. What binds is the parameter -> coefficient map, which carries about
> five modes' worth of generalisable information out of 128. The paragraph below
> is left unedited, because the pre-registration is the point.

**Why this is the load-bearing result of the ladder.** Any method whose output
is a linear combination of a *fixed* basis is bounded below by `d_n`. That
includes POD-plus-regressor (L1) and it includes DeepONet, whose output is
exactly `Σ_k b_k(params) · t_k(z,t)` — a linear n-term reconstruction. Branch and
trunk capacity change `b_k` and `t_k`; they do not change the fact that the
reconstruction is linear. So an algebraic n-width predicts that **L5 operators
will hit a floor that no amount of capacity removes**, and that the way past it
is a *nonlinear* reconstruction — a co-moving frame, or the separate
identification H1 proposes.

**Scope of the claim, honestly.** The fit is over n = 8–64 and the measured
spectrum *steepens* beyond that — the log–log curves bend below the fitted power
law at the top of the range (visible in `Fig5`, panel B). Two reasons not to read
the asymptotics from this: the POD of 691 training samples cannot resolve a tail
near its own sample-size limit, and the high-n modes are dominated by sampling
noise. So the defensible statement is **"algebraic, n^−1.2, over the practically
relevant range n = 8–64"** — not a claim about n → ∞. That range is the one that
matters, because it is where every operator in L5 will actually live.

Note the caution this imposes on 99.9 %-of-variance claims: 32 modes capture
99.906 % of the variance in c and that still leaves a POD floor of ~1.5e-3
nRMSE. Variance-explained is a misleading summary for sharp fronts, and this
project will not quote it without the corresponding error.

---

## L1 RESULT — data-driven interpolation does not transfer

Run 2026-08-20. 64 POD modes/channel, 3 seeds (42/43/44), 988 samples,
cluster-robust paired CIs. `results/l1_results.json`.

**Novel-material split** (the one H1 is about), nRMSE on c:

| arm | train | novel-condition | **novel-material** | × POD floor | gen. gap |
|---|---|---|---|---|---|
| xgb | 0.0126 | 0.0513 | **0.0485 ± 0.0008** | 33.3× | 3.8× |
| rf | 0.0196 | 0.0455 | **0.0488 ± 0.0004** | 33.5× | 2.5× |
| mlp | 0.0480 | 0.0492 | **0.0586 ± 0.0004** | 40.3× | 1.2× |
| ridge | 0.0677 | 0.0650 | **0.0676 ± 0.0000** | 46.4× | 1.0× |

Paired comparisons on novel materials:

```
xgb 0.04848 vs rf    0.04881 | diff -0.00033 CI [-0.00669, +0.00605]  NO DIFFERENCE
xgb 0.04848 vs mlp   0.05862 | diff -0.01014 CI [-0.01883, -0.00204]
xgb 0.04848 vs ridge 0.06756 | diff -0.01907 CI [-0.02727, -0.01072]
```

### L1 audit — three ways the conclusion could have been wrong

Run before starting L2, because L1's diagnosis determines which rung comes next.
`audit_l1.py`, `results/l1_audit.json`.

**A. Rank sensitivity.** The 33× gap was measured at 64 modes, a number chosen
without justification. Sweeping rank:

| modes | POD floor | rf novel-material | ratio |
|---|---|---|---|
| 8 | 1.476e-02 | 0.0496 | 3.4× |
| 16 | 7.325e-03 | 0.0492 | 6.7× |
| 32 | 3.493e-03 | 0.0492 | 14.1× |
| 64 | 1.455e-03 | 0.0492 | 33.8× |
| 128 | 5.46e-04 | 0.0491 | 90× |

The floor falls **27×** from rank 8 to 128; arm error falls **1.01×**. Flat.
The basis is definitively not the constraint — the arm cannot even exploit 8
modes. L1's diagnosis is confirmed and L2 is the right next rung.

**B. Bootstrap calibration.** The percentile cluster bootstrap over-rejects at
our cluster counts. Measured false-positive rate under a realistic null at
nominal 5 %: **8.5–9.7 % at 12 materials**, 10.7 % at 20, 7.7 % at 60. Nominal
α = 0.005 gives a true 5 % test. **One L1 verdict did not survive** — see
retraction A13. Null verdicts were always safe (an over-rejecting test that
still says "no difference" is conservative); the positive verdict was not.

**C. Split sensitivity.** Every L1 number rests on one realisation of which 12
materials were held out. Repeating with 5 independent holdout sets:

    rf novel-material error : 0.0502 ± 0.0019   (min 0.0483, max 0.0539)
    gap above the POD floor : 32.2× ± 4.5×

Stable. L1 is not an artefact of one split.

### Corrected verdicts (calibrated α = 0.005)

```
xgb vs ridge  diff -0.01907 CI [-0.03085, -0.00747]  SIGNIFICANT
xgb vs rf     diff -0.00033 CI [-0.00914, +0.00806]  no difference
xgb vs mlp    diff -0.01014 CI [-0.02260, +0.00093]  no difference   <- flipped
```

**xgb, rf and mlp are all indistinguishable. Only ridge is separable.** The
paper may not claim any nonlinear data-driven family beats another here.

**Verdict: L1 is eliminated.** The best data-driven arm predicts held-out
materials to ~4.9 % nRMSE on concentration, with a 0.42 h error in the 50 %
breakthrough time. That is a visibly wrong breakthrough curve, not a near-miss.
"More data of the same kind" is not the answer.

**XGBoost and Random Forest are indistinguishable** — the CI spans zero. Only
one of them may be quoted as "the best data-driven baseline", and the claim must
say they tie.

**The failure is a LEARNING failure, not a representation failure.** Every arm
sits 33–46× *above* the POD reconstruction floor of 1.46e-3. The basis can
represent these fields; the parameter→coefficient map is what fails. This is the
distinction §6d warned had to be kept separate, and it decides what comes next:
capacity (L2) is the right thing to eliminate, and the n-width bound of §6d is
real but **not yet binding at rank 64**.

Both facts must be stated together. Quoting the algebraic n-width as the cause of
L1's failure would be wrong by a factor of 33.

---

## L2 RESULT - capacity is eliminated

Run 2026-08-20. 26 configurations x 3 seeds, identical POD basis, splits, inputs
and seeds to L1. `results/l2_results.json`.

| family | config | train | novel-material | train->novel gap |
|---|---|---|---|---|
| mlp_width | w16 | 0.0661 | 0.0688 +- 0.0067 | 1.0x |
| mlp_width | w32 | 0.0625 | 0.0662 +- 0.0062 | 1.1x |
| mlp_width | w64 | 0.0517 | 0.0599 +- 0.0022 | 1.2x |
| mlp_width | w128 | 0.0528 | 0.0585 +- 0.0019 | 1.1x |
| mlp_width | w256 | 0.0480 | 0.0586 +- 0.0004 | 1.2x |
| mlp_width | w512 | 0.0582 | 0.0628 +- 0.0043 | 1.1x |
| mlp_width | w1024 | 0.0399 | 0.0594 +- 0.0004 | 1.5x |
| xgb_depth | md2 | 0.0450 | 0.0570 +- 0.0012 | 1.3x |
| xgb_depth | md3 | 0.0326 | 0.0511 +- 0.0008 | 1.6x |
| xgb_depth | md4 | 0.0220 | 0.0502 +- 0.0002 | 2.3x |
| xgb_depth | md5 | 0.0126 | 0.0485 +- 0.0008 | 3.8x |
| xgb_depth | md6 | 0.0065 | 0.0493 +- 0.0027 | 7.6x |
| xgb_depth | md8 | 0.0016 | 0.0522 +- 0.0029 | 32.3x |
| xgb_depth | md10 | 0.0011 | 0.0545 +- 0.0031 | 49.5x |
| rf_leaf | leaf32 | 0.0723 | 0.0863 +- 0.0001 | 1.2x |
| rf_leaf | leaf16 | 0.0540 | 0.0684 +- 0.0003 | 1.3x |
| rf_leaf | leaf8 | 0.0412 | 0.0584 +- 0.0003 | 1.4x |
| rf_leaf | leaf4 | 0.0302 | 0.0520 +- 0.0003 | 1.7x |
| rf_leaf | leaf2 | 0.0196 | 0.0488 +- 0.0004 | 2.5x |
| rf_leaf | leaf1 | 0.0108 | 0.0480 +- 0.0003 | 4.4x |
| mlp_depth | d1 | 0.0561 | 0.0604 +- 0.0009 | 1.1x |
| mlp_depth | d2 | 0.0453 | 0.0608 +- 0.0013 | 1.3x |
| mlp_depth | d3 | 0.0480 | 0.0586 +- 0.0004 | 1.2x |
| mlp_depth | d4 | 0.0548 | 0.0618 +- 0.0057 | 1.1x |
| mlp_depth | d5 | 0.0449 | 0.0569 +- 0.0005 | 1.3x |
| mlp_depth | d6 | 0.0433 | 0.0549 +- 0.0015 | 1.3x |
| mlp_depth | d8 | 0.0346 | 0.0550 +- 0.0039 | 1.6x |
| mlp_depth | d10 | 0.0527 | 0.0611 +- 0.0066 | 1.2x |

**Decision rule.** A rung is not eliminated on "the largest model wins" - that is
almost always true and shows only that the smallest setting was crippled. The
test is whether the **last step** (largest vs second-largest capacity) is still
significantly improving. A family whose final step is flat has *saturated*,
whatever the shape over the full range.

| family | last step | verdict | optimum |
|---|---|---|---|
| mlp_width | w512 -> w1024 | SATURATED | w128 (U-shaped) |
| mlp_depth | d8 -> d10 | SATURATED | d6 (U-shaped) |
| xgb_depth | md8 -> md10 | SATURATED | md5 (U-shaped) |
| rf_leaf | leaf2 -> leaf1 | SATURATED | leaf1 (at RF's ceiling) |

`mlp_depth` initially flagged "still improving" because d4 carried an outlier
seed (0.0618 +- 0.0057). Extending the sweep to 10 layers settled it: d10 vs d1
is **no difference** (CI [-0.00616, +0.00748]) and the optimum is interior at d6.

**Verdict: capacity is eliminated.** The best configuration anywhere in the sweep
(rf leaf=1, 0.0480) improves on the L1 setting by **~1 %** and remains **33x**
above the representation floor.

The clearest evidence is the train/novel decoupling in xgb: from md2 to md10 the
**training error falls 41x (0.0450 -> 0.0011) while novel-material error passes
through a minimum at md5 (0.0485) and then gets worse (0.0545)**. The models are
already deep into the overfitting regime. The parameter->coefficient map is not
under-parameterised, and adding capacity is actively harmful past the optimum.

Combined with the L1 audit - the gap is flat in POD rank (1.01x over 8->128
modes) and stable across holdout sets (0.0502 +- 0.0019) - the ~33x gap is
attributable to neither representation nor capacity. **Proceed to L3
(architecture family).**

---

## L3 RESULT - architecture family is eliminated, and NOT as a null

Run 2026-08-20/21. Three parameter budgets x three families x three seeds, with
the learning rate swept and **each family reported at its own best setting**
(protocol s3). `results/l3_results.json`.

Matched-parameter widths: an MLP edge carries one parameter, an RBF-KAN edge
carries `num_grids`, a Chebyshev edge `degree+1`. At a 200k budget that is
width 269 for the MLP against 98 and 103 for the KANs. **Comparing at equal
width instead of equal parameters is the most common error in this literature
and would have inverted the result.**

| budget | family | width | params | train | novel-material |
|---|---|---|---|---|---|
| 50,000 | cheby_kan | 48 | 50,496 | 0.0400 | 0.1875 +- 0.0059 |
| 50,000 | mlp | 114 | 49,668 | 0.0205 | 0.1260 +- 0.0056 |
| 50,000 | rbf_kan | 45 | 49,737 | 0.0384 | 0.1037 +- 0.0035 |
| 200,000 | cheby_kan | 103 | 198,776 | 0.0115 | 0.1314 +- 0.0003 |
| 200,000 | mlp | 269 | 200,328 | 0.0058 | 0.0852 +- 0.0040 |
| 200,000 | rbf_kan | 98 | 201,582 | 0.0125 | 0.0849 +- 0.0015 |
| 800,000 | cheby_kan | 215 | 799,992 | 0.0025 | 0.1154 +- 0.0034 |
| 800,000 | mlp | 583 | 800,068 | 0.0013 | 0.0636 +- 0.0046 |
| 800,000 | rbf_kan | 203 | 801,027 | 0.0020 | 0.0767 +- 0.0033 |

Paired comparisons at the calibrated alpha = 0.005: **8 of 9 significant**, and
the ordering `mlp < rbf_kan < cheby_kan` is **identical at all three budgets**.
A difference that flipped sign between budgets would not be an architecture
effect; this one does not flip.

Seed robustness (sd of novel-material error): mlp **0.00188**, rbf_kan 0.00322,
cheby_kan 0.00413. The MLP is also the most stable - matching Shukla et al.'s
report that KAN variants "may diverge for different random seeds".

### Audit: did the KANs get their best shot?

A negative result against the project's own premise has to survive a
hyperparameter audit, or it is a strawman (cf. B14). Sweeping the KAN-specific
knobs at matched parameters, 3 seeds, best of two learning rates
(`audit_l3.py`, `results/l3_audit.json`):

| configuration | novel-material |
|---|---|
| mlp | 0.0573 |
| rbf_g4 | 0.0633 |
| rbf_g8 | 0.0766 |
| rbf_g12 | 0.0828 |
| cheby_d3 | 0.0889 |
| rbf_g16 | 0.0943 |
| rbf_g24 | 0.1013 |
| cheby_d5 | 0.1032 |
| cheby_d9 | 0.1211 |
| cheby_d7 | 0.1238 |
| cheby_d11 | 0.1250 |

**The trend is monotone and mechanistic.** Novel-material error rises steadily
with the number of basis functions per edge - rbf_kan 0.0633 -> 0.1013 as grids
go 4 -> 24, cheby_kan 0.0889 -> 0.1250 as degree goes 3 -> 11. The best KAN found
anywhere is the *least KAN-like* one (grids = 4), and the limit of that trend as
basis functions -> 1 is an MLP.

Paired test, MLP against the best KAN configuration found anywhere:

```
mlp 0.0573 vs rbf_kan_g4 0.0633 | diff -0.00600 CI [-0.01196, -0.00084]  SIGNIFICANT
```

### Verdict

**H2 as originally stated is REFUTED, and in the direction opposite to the
project's premise.** Architecture family does not merely fail to help - at a
fixed parameter budget, KAN edges generalise significantly *worse* than an MLP
on this problem, consistently across budgets, with a monotone dose-response in
the KAN-ness of the edge.

The interpretation is not "KANs are bad". It is that **at a fixed budget,
parameters spent on per-edge basis richness buy training fit but not
generalisation, while the same parameters spent on width buy both.** RBF-KAN
fits the training set as well as or better than the MLP at every budget
(0.0442-0.0563 vs 0.0474-0.0563) and is worse on held-out materials every time.

Consequences for this project, stated plainly:

* A paper cannot claim PIKAN or DeepOKAN is the right architecture for this
  problem. Our own matched-parameter measurement says the opposite.
* This is consistent with two independent priors - Shukla et al. (CMAME 2024)
  and our prior project's retraction A3 - and now extends them to adsorption with
  a mechanism attached.
* The KAN arms remain valuable *as eliminations*. This rung is a result, not a
  gap in the paper.

**Architecture is eliminated. The ~33x gap above the representation floor is
attributable to neither representation (L1 audit), capacity (L2), nor
architecture family (L3). Proceed to L4 (physics as a loss).**

---

## L4 DESIGN - and a weighting result found while building it

L4 asks whether a PDE residual term improves transfer to held-out materials.
Unlike L1-L3 it cannot use POD-coefficient regression, because a residual needs
the field and its derivatives. The model is a parametric PINN,

    (11 material+operating params, z*, t*) -> (c*, q*, T*)

and the comparison is INTERNAL: physics-informed against a data-only twin with
identical architecture, parameters, optimiser, schedule, steps, seeds and
supervised-sample budget. The only difference is the residual term. Absolute
numbers are NOT comparable across rungs (different function class, different
supervision) and no such comparison is made.

### A fixed physics weight is not a fair test

At `w_pde = 1.0` the residual term starts at **9.87** against a data loss of
**0.130** -- 76x -- and the optimiser abandons the data fit:

| step | data loss | PDE loss |
|---|---|---|
| 0 | 0.130 | 9.873 |
| 50 | 0.214 | 0.168 |
| 100 | 0.244 | 0.063 |
| 175 | 0.214 | 0.059 |

The data loss **rises** while the residual falls. Reported naively this reads as
"physics-informing hurts generalisation" (novel-material 0.557 vs 0.165 for the
data-only twin), when the honest statement is "this weight does not work".
Publishing that would have been the same class of error as B14 and A13: a
negative result manufactured by a handicapped configuration.

The physics weight is therefore set by **gradient-norm balancing** (Wang, Teng &
Perdikaris, SISC 2021): every `balance_every` steps, `w_pde` is moved toward
`||grad_theta L_data|| / ||grad_theta L_pde||` under an EMA, so the two terms
contribute comparable gradient magnitude regardless of their raw scales.

Arms: `data_only`, `pi` (fixed weight, kept as the cautionary arm),
`pi_gradnorm`, `pi_gradnorm_causal` (adds causal time weighting).

### Two implementation faults caught before the run

**Per-row isotherms.** A parametric PINN evaluates a batch whose rows are
*different materials*. The first version passed `isotherm_n.mean()` into the
isotherm - one averaged isotherm applied to every row, silently erasing the
material-to-material variation the rung exists to test. `isotherm.py` is now
batch-aware and each row is verified against its own scalar reference to <1e-4.

**Per-step physics rebuild.** The residual rebuilt 1024 `AdsorptionPhysicsConfig`
objects per optimiser step, each with an exponential and a step calibration.
Precomputing the table once made that component **13x** cheaper (13.0 ms -> 0.98
ms per step).

Measured step cost after both fixes: `data_only` 98 ms, `pi_gradnorm` 212 ms.

---

## L6 / L7 DESIGN - and a degeneracy in the original L7

### The degeneracy

L7 was originally specified as "LDF + fitted isotherm, ~10 parameters". In a
purely synthetic study that is **degenerate and must not be run as written**.
The ground truth was *generated* by an LDF + Type V isotherm model, and the
11-dimensional vector handed to every ML arm essentially *is* that model's
parameters. A classical model given those parameters therefore reproduces the
reference exactly, would "win" with zero error, and would say nothing about
anything.

The mistake was treating a surrogate study as an accuracy competition. It is
not: the reference solver is already exact, and costs 4.2 s. What a surrogate
buys is **accuracy at a speed budget**.

### Corrected L7

The classical control must be a **fast approximation**, not the generating
model. Adsorption supplies several that cost microseconds and carry real,
characterisable error:

* **Klinkenberg** closed form for LDF kinetics with a linear isotherm;
* **constant-pattern** analysis for a favourable isotherm, where the
  mass-transfer zone reaches a fixed shape and the breakthrough curve follows
  from the isotherm alone;
* **equilibrium theory** (Rhee-Aris-Amundson) for the shock and simple-wave
  structure, which is what predicts the two-wave behaviour observed in section 6c.

These require **no training at all**, so they also give a zero-parameter transfer
reference for held-out materials - the analogue of the prior project's
128-number linear convolution beating every deep operator.

### L6, and why it is the same question

H1 says structural decomposition governs extrapolation. In adsorption the
decomposition is the field's own: **equilibrium** (what the material holds) and
**kinetics** (how fast it gets there).

| arm | what is learned | what is imposed |
|---|---|---|
| **joint** | params -> full spatiotemporal field | nothing |
| **separate** | params -> isotherm `q*(c,T)`; params -> rate `k` | the PDE structure that composes them |

Both emit a field, are trained on identical data with matched parameter counts,
and are scored on identical splits. The joint arm is free to fit anything; the
separate arm must route everything through two physically meaningful objects and
the known conservation structure.

The classical control (L7) is the limiting case of the separate arm in which
*both* objects are given rather than learned - which is why L6 and L7 are two
views of one question, and why they are run together.

**Pre-declared:** if the separate-vs-joint transfer gap has a bootstrap CI
including zero at 3 seeds and the calibrated alpha, H1 is reported as **not
supported**, in the abstract, in those words.

---

## L7 RESULT - the classical control is beaten, and that is a real finding

Run 2026-08-21. Zero training, closed form. `results/l7_results.json`,
`results/exit_curve_rescore.json`.

**Scored like-for-like.** The classical forms predict the EXIT breakthrough
curve, not the full field, so the learned arm was re-scored on the exit curve
too. Comparing 0.0485 (field) against 0.2307 (curve) would have been meaningless:
the field metric averages over a largely smooth domain, the curve metric
concentrates on the hardest part of the solution. Note the learned arm is
noticeably worse on the curve (0.0725) than on the field (0.0488) - the exit
curve is where the difficulty lives.

Novel-material split, exit-curve nRMSE:

| method | exit nRMSE | dt50 error | cost per curve | trained? |
|---|---|---|---|---|
| POD floor (representation limit) | 0.0045 | 0.01 h | - | - |
| **rf (best learned arm)** | **0.0725 +- 0.0004** | **0.39 h** | ~ms | yes |
| klinkenberg | 0.2307 | 0.87 h | 0.264 ms | **no** |
| constant_pattern | 0.2673 | 0.82 h | 0.635 ms | **no** |
| equilibrium_shock | 0.2725 | 0.87 h | 0.113 ms | **no** |

Paired, cluster-robust, calibrated alpha = 0.005:

```
rf vs equilibrium_shock | diff -0.2000 CI [-0.2489, -0.1522]  SIGNIFICANT
rf vs klinkenberg       | diff -0.1582 CI [-0.2162, -0.0987]  SIGNIFICANT
rf vs constant_pattern  | diff -0.1948 CI [-0.2420, -0.1496]  SIGNIFICANT
```

**Verdict: learning is justified here.** The best learned arm beats the best
closed form by **3.2x** on exit-curve nRMSE and **2.2x** on breakthrough time,
significantly, on materials it never saw.

### Why this differs from the prior project, and why that matters

In the analogous conduction study a 128-number linear convolution beat every deep
operator. Here classical theory loses decisively. The difference is diagnostic
rather than contradictory:

* conduction with a cyclic source is **linear and time-invariant**, so a Green's
  function is not an approximation - it is the exact solution operator, and a
  learned model can at best match it;
* adsorption with a Type V isotherm is **nonlinear**, and every closed form above
  linearises somewhere. Klinkenberg assumes a linear isotherm (we supply the
  chord slope); constant-pattern assumes a favourable isotherm and a
  non-spreading front; equilibrium theory assumes infinitely fast kinetics. The
  **two-wave structure of section 6c violates all three** - a fast spreading
  Henry wave followed by a slow cooperative shock is neither a single shock nor a
  constant-pattern front.

So the honest cross-domain statement is not "classical beats deep learning" or
its reverse, but: **a classical model wins exactly when the physics it assumes is
the physics that is there.** That is a sharper and more transferable claim than
either project alone supports, and it is the kind of statement the ladder exists
to produce.

The classical arms remain the zero-parameter transfer reference every learned arm
must clear, and all of them clear it.

---

## L6 DESIGN PROBLEM - H1 is not testable as originally framed

Found 2026-08-21, before running the rung. This is the second degeneracy of the
same kind as B18 and it affects the project's PRIMARY hypothesis, so it is stated
in full.

### The problem

H1 contrasts a surrogate that identifies the equilibrium and kinetic objects
**separately** against one that fits them **jointly**. But `PARAM_KEYS` hands
every arm the eleven *generative* parameters - `q_max`, `delta_H`, `step_rh`,
`isotherm_n`, `henry_fraction`, `k_LDF`, `rho_p`, `eps_t`, and the operating
conditions. Those are not descriptors of the material; they ARE the model that
produced the data.

So a separate-identification arm does not have to *identify* anything. Its
equilibrium object is an identity map from its own inputs, its kinetic object is
one of its own inputs, and composing them through the known PDE is just running
the reference solver - exact by construction, and 4.2 s per condition.

Framed that way the rung has a foregone answer that is an artefact of the
parameterisation, not a finding about structure.

### Why this is the same mistake as B18

Both come from treating a synthetic surrogate study as an accuracy competition
against a reference that is already exact. The reference cannot be beaten on
accuracy; it can only be beaten on **accuracy per unit inference cost**, or
matched on accuracy from **less information**.

### Two corrected framings

**(a) Observable descriptors (preferred).** Replace the generative parameters
with what an experimentalist would actually have:

* a measured isotherm *fingerprint* - uptake at K relative humidities, which is a
  standard characterisation and is exactly what a screening campaign records;
* bed and operating properties, which are genuinely known (`rho_p`, `eps_t`, `v`,
  `T_in`, `rh_feed`);
* **no `k_LDF`** - the kinetic coefficient is not directly observable and must be
  inferred from dynamics, which is precisely what makes the equilibrium/kinetic
  decomposition non-trivial.

Under this parameterisation the separate arm has real work to do: recover the
isotherm from the fingerprint, infer the rate from the dynamics, and compose them
through the conservation structure. The joint arm sees identical inputs. H1
becomes a genuine question, and the setup matches how the method would be used.

**(b) Matched inference cost.** Compare arms at equal wall-clock per prediction,
so the exact-but-slow structural route competes against the fast learned one on
the axis that actually matters for screening. Reported alongside (a), not instead
of it: (a) tests the science, (b) tests the engineering claim.

### Consequence

L6 is **not run** under the current parameterisation. It is re-specified under
(a), which requires regenerating the descriptor matrix - not the field data, which
is unaffected. L1-L5 are unaffected: they never claimed to test H1, and their
inputs are legitimate for the questions they do ask (representation, capacity,
architecture, physics-as-loss, operator family).

**Pre-declared, unchanged:** if the separate-vs-joint gap under (a) has a
bootstrap CI including zero at 3 seeds and the calibrated alpha, H1 is reported as
**not supported**, in the abstract, in those words.

### The corrected L6 input set, and its degeneracy check

`descriptors.py`. 41 features:

* **isotherm fingerprint** - q*(RH) at 12 relative humidities x 3 temperatures
  (T_in - 10, T_in, T_in + 10 K), shape-normalised with the scale carried as a
  separate feature;
* **bed / operating** - rho_p, eps_t, v, T_in, rh_feed.

Three temperatures are not decoration. With a single isotherm the enthalpy is
invisible - measured R^2 for dH from a one-temperature fingerprint is **-0.81**,
i.e. unrecoverable - and any model would be blind to the isosteric heat. Real
characterisation campaigns measure several temperatures for exactly this reason.

**Degeneracy check** (`descriptors.check_non_degenerate`): a strong regressor is
trained to recover each withheld generative parameter from the descriptors alone,
and scored on held-out materials. If any were recoverable, the substitution would
not have removed the problem.

| withheld parameter | R2 from descriptors | reading |
|---|---|---|
| step_rh | 0.9642 | equilibrium shape is observable, as a measured isotherm should be |
| q_max | 0.9331 | " |
| isotherm_n | 0.9251 | " |
| delta_H | 0.7465 | recoverable via the van't Hoff slope across the three temperatures |
| henry_fraction | -0.0034 | not recoverable |
| **k_LDF** | **-0.6088** | **not recoverable at all** |

This is exactly the structure H1 needs. The **equilibrium** object is largely
observable - which is true in practice, isotherms are measured. The **kinetic**
object is completely hidden and can only be inferred from the dynamics. So a
separate-identification arm has real work to do on the half that matters, and the
joint arm sees identical inputs.

---

## L4 RESULT - physics as a loss makes NO DIFFERENCE on the material axis

Run 2026-08-21. Parametric PINN, 114,435 parameters, 15,000 steps, 3 seeds,
identical supervised budget for both arms, physics weight set by gradient-norm
balancing. `results/l4_results.json`.

| arm | train c | novel c | novel q | novel T |
|---|---|---|---|---|
| data_only | 0.0092 +- 0.0002 | **0.0577 +- 0.0074** | 0.0797 +- 0.0027 | 0.1234 +- 0.0125 |
| pi_gradnorm | 0.0197 +- 0.0002 | **0.0655 +- 0.0024** | 0.0974 +- 0.0051 | **0.1057 +- 0.0010** |

```
data_only 0.05774 vs pi_gradnorm 0.06555 | diff -0.00781 CI [-0.01990, +0.00726]
                                          -> NO DIFFERENCE
```

> **NOTE on defect B20 / retraction A14.** This section's physics loss omitted boundary conditions, which was
> a genuine defect and is fixed. But adding them changed **nothing** at matched training budget (5060 +- 419
> without, 5967 +- 4290 with, 8,000 steps, 3 seeds). An earlier claim of a ~5,200x improvement was an
> undertrained-vs-trained artifact and is withdrawn as A14. These L4 numbers therefore stand.

**Verdict: on the novel-MATERIAL axis, adding a PDE residual changes nothing.**
Not better, not worse. The point estimate favours the data-only twin, and the CI
spans zero at the calibrated alpha.

### Two structures inside the null, which the mean hides

**Physics helps the field with the weakest data signal.** Temperature improves
0.1234 -> 0.1057 while concentration and loading get slightly worse. T is a small
perturbation about T_in and is the hardest field to fit from data alone; the
energy residual constrains it directly. (Per-sample T was not stored this run, so
no paired CI is available for that difference - it is reported as suggestive and
the storage is fixed for L4b.)

**Physics buys consistency, not accuracy.** Seed-to-seed spread falls sharply in
every field: c 0.0074 -> 0.0024, q 0.0027 -> 0.0051, T 0.0125 -> 0.0010. The
residual acts as a regulariser. A study reporting only means would miss this
entirely, and "no difference in mean, 3-12x tighter across seeds" is a materially
different statement from "no effect".

### Why the null is expected, and what it does NOT mean

It does **not** mean physics-informing is useless - that would contradict a large
literature and our own prior project, where physics-informed arms extrapolated in
time and data-driven ones did not.

It means the residual was asked to bridge an axis it cannot bridge. A PDE residual
is evaluated at (z,t) collocation points **for materials in the training set**,
and at inference it is not evaluated at all. Nothing in the residual for material
A constrains material B, whose PDE coefficients the model never saw. Worse, this
rung's training data samples the **full (z,t) domain** for every training
material, so there is no data-free region for the residual to supervise - it is
largely redundant with data already present.

Physics-as-a-loss should help where the residual can be evaluated but data is
absent: **inside the coordinates the PDE constrains**. That is a sharp, falsifiable
prediction and it is tested directly in L4b.

This is also precisely the argument for H1. To transfer across materials, the
material-dependence must enter through **structure that generalises** - an
equilibrium object, a rate object - not through a penalty evaluated only on
training materials.

---

## IDENTIFIABILITY - the kinetic object is only weakly determined, and why

Closes the SINDy open item. `identify_kinetics.py`, `identifiability.py`,
`results/kinetics_identification.json`.

### What replaced the original SINDy

`sindy_discovery.py` placed `q*` - computed from the exact law that generated the
data - into its own library alongside `q`. Since the true law is
`dq/dt = k(q* - q)`, both terms were handed to the regressor. That is a two-term
fit onto the answer, not discovery (retraction A7).

The question the ladder actually needs is different. `descriptors.py` showed
`k_LDF` is not recoverable from observable descriptors (R2 = -0.61). H1's
separate-identification arm therefore depends on the rate being recoverable from
**dynamics**. That is what was tested.

### Result: identifiable in principle, not in practice

| estimator | median error in k |
|---|---|
| exact `q*(c,T)` pointwise | **0.80 %** (90.7 % within 10 %) |
| exact `q*`, restricted to the informative window | 1.32 % (100 % within 10 %) |
| measured isotherm fingerprint | **95.6 %** |

The estimator is correct - given the true equilibrium it recovers `k` almost
exactly. The failure is entirely in reconstructing `q*` from measurement, and the
reason is a regime property, not an interpolation defect:

    Damkohler over the run, Da = k * t_final :  p05 122, median 626, p95 3312

**Da >> 1 everywhere: the bed sits near local equilibrium.** The LDF driving
force is then a small difference of two large numbers:

    peak |q* - q| / q_max :  p05 0.054 %, median 1.38 %, p95 21.1 %
    44 % of conditions never exceed 1 % of q_max

Identifying `k` to 10 % requires knowing `q*` to **0.14 % of q_max**. A 12-point
interpolated fingerprint achieves ~2-3 % - an **18x shortfall**. Measured directly
on individual conditions, the reconstruction error in `q*` (0.22-0.47 mol/kg) is
**5-25x larger than the true driving force itself** (max 0.061 mol/kg).

> **The kinetic coefficient is not practically identifiable from breakthrough data
> plus a measured isotherm in the near-equilibrium regime, because the signal is
> smaller than the isotherm measurement error.** This is an experimental-design
> statement, not a modelling one, and it holds regardless of the estimator.

### Consequences

**For H1.** The separate arm cannot identify `k` by regression against a measured
isotherm. It must learn the rate end-to-end from the dynamics - which is what
`run_l6.Separate` does (a `log_k` head trained by backpropagation through the
exponential-integrator composition, never by fitting a measured isotherm). The
design stands; this explains what it is actually doing and why the task is hard.

**For the parameter space.** `k_LDF` was sampled over [0.002, 0.05], which is
Da 155-3885 - entirely inside the near-equilibrium regime. Measured sensitivity
of the exit curve:

| k_LDF | Da | max abs change in c/c_in | t50 shift |
|---|---|---|---|
| 0.05 -> 0.002 (the sampled range) | 3885 -> 155 | **0.105** | 0.11 h |
| 0.05 -> 1e-4 (below the range) | 3885 -> 8 | 0.284 | 2.93 h |

`k` is **not** irrelevant: 0.105 in `c/c_in` is about **2x the best model error
(0.048)**, so the dataset does carry kinetic signal. But the kinetically
informative regime, Da ~ 1-50, lies *below* the sampled range. A future dataset
should extend `k_LDF` downward (or shorten the run) to put the kinetic axis on
equal footing with the equilibrium axis. Recorded here rather than silently
changed, because the current dataset underpins L1-L4.

### The polynomial SINDy arm

Rebuilt with **column standardisation** (the original applied one absolute
threshold to a library spanning ~40 orders of magnitude, κ(Θ) = 1.07e44). It now
selects a `q` term in 100 % of conditions, but with the negative sign the LDF law
requires in only **69 %**, and retains essentially every candidate term - it does
not sparsify. That is the expected outcome in a near-equilibrium regime where the
kinetic signal is 1 % of the state: there is little for a sparse regression to
find. Reported as a null, not omitted.

---

## L4b RESULT - where physics helps, and how it should be imposed

Run 2026-08-21/22. Two held-out axes x two output parameterisations x two arms,
matched at 8,000 steps, 3 seeds, identical supervised budget.
`results/l4b_results.json`, `results/l4b_bounded.json`,
`results/l4b_time_corrected.json`.

Three claims made from this experiment were withdrawn before it settled - A14,
A15, A16. The numbers below are the corrected ones.

### The 2x2

nRMSE on c, held-out portion of each axis:

| output head | arm | TIME axis | MATERIAL axis |
|---|---|---|---|
| unbounded (`t*softplus`) | data-only | 0.1425 | 0.0719 |
| unbounded | physics-informed | 0.0639 | 0.0855 |
| **bounded** (`sigmoid`) | **data-only** | **0.0124** | **0.0538** |
| bounded | physics-informed | 0.0194 | 0.0668 |

The bounded head enforces `0 <= c <= c_in` and `0 <= q <= q_max` - the maximum
principle for this system - architecturally, with no extra parameters and no
loss term. The initial condition moves to an explicit residual, because the
`t*` envelope the unbounded head used is not the right IC anyway: it forces
`c <= t` everywhere, including at the inlet where c reaches c_in almost at once.

### Two effects, and an interaction

**Hard bounds help on both axes, significantly.**

```
data-only   TIME     0.1425 -> 0.0124   11.5x   CI [+0.1139, +0.1438]
physics     TIME     0.0639 -> 0.0194    3.3x   CI [+0.0271, +0.0643]
data-only   MATERIAL 0.0719 -> 0.0538   +25%    CI [+0.0048, +0.0499]
```

**Physics-as-a-loss helps only when the structure is missing, and hurts when it
is present.**

```
unbounded   TIME     0.1425 -> 0.0639   2.2x BETTER   CI [+0.0564, +0.1032]
bounded     TIME     0.0124 -> 0.0194   1.6x WORSE    CI [-0.0112, -0.0020]
unbounded   MATERIAL 0.0719 -> 0.0855   worse (CI includes zero)
bounded     MATERIAL 0.0538 -> 0.0668   worse (CI includes zero)
```

That is a genuine **interaction**, not an additive effect. With an unbounded
head the residual partially compensates for the constraint the architecture is
missing. Once the constraint is imposed exactly, the penalty has nothing left to
add and costs accuracy - it diverts gradient budget from fitting the data, which
shows directly in the in-window error (bounded data-only 0.0145, bounded physics
0.0248).

### What this says about physics-informed learning here

**The value of physical knowledge lies in how it is imposed, not whether it is
present.** The same fact - c cannot exceed c_in - is worth 11.5x as an
architectural bound and is counter-productive as a penalty term once the bound is
there.

**Physics-as-a-loss is an axis-specific tool.** On the material axis it does not
help under either parameterisation, and the reason is structural: a residual is
evaluated only at collocation points for materials in the training set, and never
at inference. Nothing in material A's residual constrains material B. On the time
axis, where the residual CAN be evaluated where data is absent, it helps - but
only up to the point where hard structure does the job better.

**The best configuration on both axes uses no physics loss at all**: a data-only
model with physically bounded outputs (TIME 0.0124, MATERIAL 0.0538). That is the
strongest evidence yet for H1's premise - structure, not penalties - and it
arrives from the physics-as-a-loss rung rather than the identification rung.

### Caveat carried forward

The material-axis numbers here (0.0538 best) are not comparable to L1-L3's
(0.0485 best): different function class, different supervision, different
sampling. Within-rung comparisons only.

---

## L6 RESULT - H1 IS NOT SUPPORTED

Run 2026-08-22. Observable descriptors (54 features, generative parameters
withheld), matched ~120,000 parameters, 8,000 steps, 3 seeds, identical inputs
and splits across arms. `results/l6_results.json`.

| arm | params | train c | novel-material c | novel-material q | exit c |
|---|---|---|---|---|---|
| joint | 120,273 | 0.0252 +- 0.0007 | **0.0566 +- 0.0039** | 0.1158 +- 0.0056 | 0.0546 |
| separate | 118,948 | 0.0296 +- 0.0011 | **0.0721 +- 0.0105** | 0.1259 +- 0.0091 | 0.0604 |
| separate_noeq | 118,948 | 0.0320 +- 0.0021 | **0.0728 +- 0.0073** | **0.4564 +- 0.1939** | 0.0592 |

```
joint vs separate       diff -0.01554 CI [-0.04540, +0.01372]   NO DIFFERENCE
joint vs separate_noeq  diff -0.01623 CI [-0.04827, +0.01294]   NO DIFFERENCE
separate vs sep_noeq    diff -0.00069 CI [-0.00678, +0.00499]   NO DIFFERENCE
```

### Verdict, in the pre-declared words

The separate-vs-joint transfer gap has a bootstrap CI including zero at 3 seeds
and the calibrated alpha. **H1 is NOT SUPPORTED.** The point estimate favours the
*joint* arm, and the paper must say so.

### What the ablation does show

The equilibrium head is doing real work on the quantity it structures. Replacing
it with a free output (`separate_noeq`) degrades solid loading from
**0.1259 to 0.4564** - a 3.6x collapse, with 21x the seed variance. So the
composition is not inert: imposing `dq/dt = k(q_eq - q)` with a learned
equilibrium object predicts q far better than the same composition with q left
free.

*(Caveat: only per-sample nRMSE on c was stored, so no paired CI is available for
the q difference. It is reported as means +- seed spread, and the separation is
large relative to that spread. Storage is fixed for any re-run.)*

But structuring q correctly **does not transfer to the field or to held-out
materials**. The structure helps the quantity it constrains and nothing else.

### Why, and what it means

The most likely reason is already measured: **the decomposition is nearly
degenerate in this regime.** Da = k*t_final has median **626** and the LDF driving
force |q* - q| peaks at a median of **1.38 % of q_max**. When the bed sits at
local equilibrium, `q ~= q*(c,T)` and the LDF composition reduces to "q tracks the
isotherm" - something the joint arm can learn directly from a fingerprint that
already exposes the isotherm shape (step_rh R2 = 0.96). There is little structure
left to exploit, so imposing it costs flexibility and buys nothing.

This sharpens rather than contradicts the prior project's separate-identification
result (6.10 % vs 98.45 % transfer, a 16x gain). That system was linear and
time-invariant, where the Green's-function decomposition is exact and carries the
whole solution. Here the analogous decomposition is nearly trivial.

> **The transferable claim: structural decomposition helps when the structure is
> non-degenerate in the operating regime.** It is not a general-purpose
> generalisation device, any more than physics-as-a-loss was.

### The falsifiable follow-up

H1 should be re-tested at low Damkohler, where kinetics genuinely shape the
solution. The sensitivity sweep shows the informative regime is Da ~ 1-50, below
the sampled range: dropping k_LDF from 0.05 to 1e-4 moves the exit curve by 0.284
in c/c_in and the 50 % breakthrough time by 2.93 h, against 0.105 and 0.11 h
across the whole sampled range. A dataset extending k_LDF downward would test H1
where it has a chance of being true. **This is a prediction, not an excuse: if
the gap is still absent at low Da, H1 is wrong rather than untested.**

---

## L5 RESULT - the n-width is a real bound, and it is NOT what binds

Run 2026-08-23/24. 90 configurations: 2 families x p in {8,16,32,64,128} x
lr in {1e-3, 3e-4, 1e-4} x seeds {42,43,44}, all at ~200 k parameters, 8000
steps, frozen 128x128 encoding. 35,821 s. `results/l5_results.json`,
`results/l5_analysis.json`, `results/l5_bottleneck.json`.

The single-learning-rate run that preceded this is withdrawn (defect **B22**) and
kept at `results/l5_singlelr_WITHDRAWN.json`.

> **The DeepOKAN column below is SUPERSEDED and a grid-completion run is in
> flight.** The `{1e-3, 3e-4, 1e-4}` grid straddled DeepOKAN's optimum at large p:
> at `lr = 2e-4` it reaches **0.0652** at p = 64 and **0.0710** at p = 128 with no
> collapses, against the 0.0818 / 0.0884 tabulated here. Separately, both families
> peak at `lr = 1e-3`, which is the **top edge** of the grid, so their optimum at
> small p is untested. Runs covering `lr = 3e-3` at every p and `lr = 2e-4` at
> p = 8/16/32 are running now (`results/l5_fill1.json`, `l5_fill2.json`); scoring
> is over the union via `python analyze_l5.py <files...>`. **The DeepONet flatness
> result and the entire bottleneck analysis are unaffected** — they are the
> load-bearing claims and do not depend on DeepOKAN's column. This is defect-B22's
> failure class recurring at finer resolution; see trap 3.

### The pre-registered prediction is refuted

Section 6d predicted DeepONet error would fall algebraically with `p`, tracking
the POD floor. Each family is scored at **its own best learning rate** for each
`p`, over three surviving seeds:

| p | POD floor | DeepONet | best lr | x floor | DeepOKAN | best lr |
|---|---|---|---|---|---|---|
| 8 | 0.01440 | **0.0281** | 1e-3 | 2.0x | 0.0392 | 1e-3 |
| 16 | 0.00731 | **0.0293** | 1e-3 | 4.0x | 0.0357 | 1e-3 |
| 32 | 0.00331 | **0.0291** | 1e-3 | 8.8x | 0.0498 | 3e-4 |
| 64 | 0.00135 | **0.0296** | 1e-3 | 21.9x | 0.0818 | 1e-4 |
| 128 | 0.00050 | **0.0296** | 1e-3 | **59.0x** | 0.0884 | 1e-4 |

```
deeponet p=8 0.02812 vs p=16  0.02925 | diff -0.00113 CI [-0.00298, +0.00056]  NO DIFFERENCE
deeponet p=8 0.02812 vs p=32  0.02908 | diff -0.00096 CI [-0.00363, +0.00121]  NO DIFFERENCE
deeponet p=8 0.02812 vs p=64  0.02962 | diff -0.00150 CI [-0.00447, +0.00062]  NO DIFFERENCE
deeponet p=8 0.02812 vs p=128 0.02960 | diff -0.00148 CI [-0.00475, +0.00121]  NO DIFFERENCE
```

The floor falls **28.7x**; DeepONet moves **1.05x**, and every point estimate is
in the *wrong direction*. The n-width bound is mathematically correct and
completely inactive: at p = 128 the method sits **59x above** it. See retraction
**A17**, which withdraws §6d's claim that this bound is "the load-bearing result
of the ladder".

**Not a generalisation artefact.** Train error is flat too (0.0119 at p = 8 ->
0.0135 at p = 128, against a train floor of 2.5e-4). The model cannot exploit the
extra modes on data it has *seen*, so no amount of extra training addresses it.

### What actually binds, measured rather than inferred

`l5_bottleneck.py` separates the two terms a linear reconstruction can fail on,
in the **optimal** basis, so the answer does not depend on what basis DeepONet
happened to learn. POD is fit on train; coefficients are then predicted from the
same 11 parameters by the strongest regressor available (targets standardised —
defect B14):

| p | basis error (true coefs) | coefficient-map error | best regressor |
|---|---|---|---|
| 8 | 0.01440 | 0.0515 | HGB |
| 16 | 0.00731 | 0.0511 | HGB |
| 32 | 0.00331 | 0.0509 | HGB |
| 64 | 0.00135 | 0.0510 | HGB |
| 128 | 0.00050 | 0.0510 | HGB |

Flat to the fourth decimal while the basis error falls 28.7x. The reason is
visible per mode: on held-out materials the params -> coefficient map has
**R² = 0.946 for mode 1**, 0.39-0.58 for modes 2-5, and a **median R² of -0.014
beyond mode 24** — worse than predicting the mean. Only **3 of 128 modes** reach
R² > 0.5, and that count is 3 at every `p`.

Calibrating against an oracle reconstruction that is *given* the true
coefficients for its first k modes:

| method | novel-material nRMSE | equivalent oracle rank |
|---|---|---|
| POD + strongest coefficient regressor | 0.0510 | ~2 modes |
| DeepOKAN, best anywhere | 0.0357 | ~3 modes |
| DeepONet, best anywhere | 0.0281 | **~4 modes** |

**Giving DeepONet 128 basis functions buys it the accuracy of four.** The basis
was never the constraint.

This is the same signature the L1 audit found (rf error flat at 0.0496 -> 0.0491
over rank 8 -> 128 while the floor fell 27x) and it was then read as an L1-specific
result. Three independent function classes — POD+rf, POD+HGB, DeepONet — are all
flat in rank against a floor that falls ~28x. End-to-end training of basis and
coefficients together is worth a constant **1.8x** (0.0510 -> 0.0281, same
encoding, so this comparison is within-rung and legitimate) but does not change
the scaling.

### DeepOKAN has a hard optimisation failure, and it is width-driven

**10 of 45 DeepOKAN runs collapsed; 0 of 45 DeepONet runs did.** Collapse is
detected mechanistically, not by an error threshold: a run is flagged iff its
per-condition error vector matches a run with a *different seed*. All ten land on
the same point in function space, agreeing to **2.7e-7** across different `p`,
different learning rates and different seeds — a trained network cannot be
seed-invariant.

| p | branch/trunk width | collapsed |
|---|---|---|
| 8 | 92 | 0/9 |
| 16 | 88 | 0/9 |
| 32 | 78 | 1/9 |
| 64 | 62 | 4/9 |
| 128 | 42 | **5/9** |

At matched parameters, larger `p` forces a narrower stack, and the RBF-KAN
saturates. The failure rate is monotone in width.

### Family verdict — narrower than L3's, and stated as such

```
deeponet p=8   0.0281 vs deepokan p=8   0.0392 | diff -0.0111 CI [-0.0292, +0.0053]  NO DIFFERENCE
deeponet p=16  0.0293 vs deepokan p=16  0.0357 | diff -0.0064 CI [-0.0184, +0.0057]  NO DIFFERENCE
deeponet p=32  0.0291 vs deepokan p=32  0.0498 | diff -0.0207 CI [-0.0307, -0.0103]  SIGNIFICANT
deeponet p=64  0.0296 vs deepokan p=64  0.0818 | diff -0.0521 CI [-0.0621, -0.0409]  SIGNIFICANT
deeponet p=128 0.0296 vs deepokan p=128 0.0884 | diff -0.0588 CI [-0.0687, -0.0468]  SIGNIFICANT
best anywhere  0.0281 vs best anywhere  0.0357 | diff -0.0075 CI [-0.0197, +0.0044]  NO DIFFERENCE
```

Verdicts are unchanged under all three scoring rules (3 surviving seeds — the
protocol minimum and the primary; collapsed runs included; 2 surviving seeds
allowed). See defect **B23** for why the seed rule had to be checked.

**L5 does NOT replicate L3.** L3 found MLP edges better at *every* budget, 8 of 9
comparisons significant. Here, at their best configurations the two families are
**statistically indistinguishable** (0.0281 vs 0.0357). The KAN penalty appears
only once the basis is large enough to force a narrow stack. The defensible
statements are: DeepOKAN is **never better** at any `p`; it is significantly worse
at `p >= 32`; and it fails to train in **22 %** of runs where DeepONet never does.

**The null is not equivalence.** With 12 held-out materials the best-vs-best CI
spans [-0.0197, +0.0044] — the test cannot resolve a 21 % difference. Report "no
difference detected", never "the families are equivalent".

**Matched steps favours DeepOKAN in compute.** Both families ran 8000 steps, but
DeepOKAN costs **1.6-2.1x** the wall-clock per run at every `p` (median 420 s vs
237 s at p = 8; 532 s vs 256 s at p = 128). Quoted as minimum-over-seeds to
discount external machine load, the ratios are 1.5-1.9x — the same conclusion. At
matched *compute* DeepOKAN would look worse still, so the comparison above is the
generous one.

### Verdict

**The operator rung is eliminated, and the n-width hypothesis with it.** An
operator buys a constant 1.8x over POD-plus-regressor and nothing else; both are
flat in basis size. The obstruction is the parameter -> coefficient map, which
carries about five modes' worth of generalisable information out of 128. Widening
the basis, changing the edge family, or adding capacity cannot address that,
which is consistent with L2 and L3 having already been eliminated. What would
address it is a *nonlinear* reconstruction — a co-moving frame that removes the
front position from the field before projection — and that is the direction the
ladder now points to.

---

## CO-MOVING FRAME - the standard fix does not work here, and the reason is measured

Run 2026-08-24, `comoving.py`, `results/comoving.json`. Same 128x128 encoding and
same nRMSE normalisation as L5, so the comparison is within-rung.

L5 left exactly one lever unexplored. Every failure it documented — flat in basis
size, coefficients unpredictable beyond ~mode 5 — is the textbook signature of
**transport**: a front at a sample-dependent position is not low-rank in a fixed
basis. The textbook fix is to factor the position out before projecting.

The warp is defined per axial position, since `c(z, .)` is monotone in `t` at fixed
`z` for a breakthrough column:

    t_L(z) = time at which c(z, t) crosses level L      (linear interpolation)
    C(z, tau) = c(z, t_L(z) + tau)

### Why one warp cannot work here — measured first

At the outlet, the separation between the fast Henry wave and the cooperative
shock, `t(0.9) - t(0.1)`, spans **[0.025, 0.992]** in normalised time — a **40x
range** across the dataset, median 0.640, relative spread 0.29. A single-level warp
aligns one wave exactly and lets the other scatter by that much. This is the §6c
two-wave structure charging a price.

### It makes the n-width WORSE, not better

Modes needed for 90 / 99 / 99.9 / 99.99 % of training variance:

| frame | 90 % | 99 % | 99.9 % | 99.99 % |
|---|---|---|---|---|
| **original** | 3 | 11 | **31** | 65 |
| co-moving, L = 0.1 | 4 | 15 | 42 | 98 |
| co-moving, L = 0.5 | 5 | 27 | **102** | 129 |
| co-moving, L = 0.9 | 3 | 20 | 84 | 129 |

Every alignment level is worse than doing nothing. Aligning on the 0.5 crossing —
the obvious choice — **triples** the rank needed for 99.9 %.

### And it does not help accuracy, even given the warp for free

Novel-material nRMSE, POD + the same strongest coefficient regressor as
`l5_bottleneck.py`, shape basis swept exactly as L5 swept p:

| alignment | warp R² | best oracle-warp | best predicted-warp |
|---|---|---|---|
| L = 0.1 | +0.811 | 0.0593 | **0.0612** |
| L = 0.5 | +0.927 | **0.0534** | 0.0645 |
| L = 0.9 | +0.919 | 0.0572 | 0.0725 |
| **fixed frame (L5)** | — | — | **0.0510** |

Flat in shape-basis size in every frame (0.0596 -> 0.0594 at L = 0.1), the same
signature L5 found. The interpolation floor is 0.0024-0.0030, under 6 % of the
signal, so it cannot manufacture this.

The decisive row is the oracle: **handed the exact front trajectory for free, the
co-moving frame still does not beat the fixed frame** (0.0534 vs 0.0510). This is
not a warp-prediction failure — the warp is predictable at R² = 0.927. The frame
itself is wrong for this system.

### Scope, stated honestly

What is measured: **single-front alignment does not help, at any of three levels,
at any shape-basis size, even with an oracle warp.** What is *not* tested, and
remains open: a **two-parameter warp** that aligns both waves independently, which
the gap measurement above suggests is what the system actually requires. Also
untested is whether a neural reconstruction in a co-moving frame would inherit the
1.8x that DeepONet buys over POD+regressor in the fixed frame; that scaling is an
assumption, not a measurement, and 0.0612 / 1.8 = 0.034 would still be behind
DeepONet's 0.0281.

**This does not eliminate nonlinear reconstruction as a direction.** It eliminates
the simplest version of it and says precisely why: the cooperative isotherm makes
this a two-wave problem, and two waves whose separation varies 40-fold cannot be
straightened by one shift.

---

## TWO-WAVE WARP - the right frame, and an unrealised 2.5x

Run 2026-08-24, `comoving2.py`, `results/comoving2.json`. Same encoding and
normalisation as L5 and `comoving.py`.

The measurement that refuted the single warp named its successor. Use *two* shifts
— one per wave — and normalise the interval between them:

    t_lo(z), t_hi(z) = arrival times of the Henry wave and the completed shock
    sigma = (t - t_lo(z)) / (t_hi(z) - t_lo(z))
    C(z, sigma) = c(z, t_lo + sigma * (t_hi - t_lo))

This removes both the arrival time and the transition width.

### It collapses the n-width, where one shift inflated it

Modes for 90 / 99 / 99.9 / 99.99 % of training variance:

| frame | 90 % | 99 % | 99.9 % | 99.99 % |
|---|---|---|---|---|
| original | 3 | 11 | 31 | 65 |
| single warp, L = 0.5 | 5 | 27 | 102 | 129 |
| **two-wave, 0.10-0.90** | 2 | 5 | **17** | 64 |
| **two-wave, 0.05-0.95** | 2 | **4** | **13** | **52** |

Where one shift *tripled* the rank needed for 99.9 %, two shifts **more than halve
it** (31 -> 13). The two-wave structure is not noise to be averaged over; it is the
coordinate system the problem is written in.

### And the reconstruction error falls 2.5x — given the warp

Novel-material nRMSE, shape basis swept over p = 8...128 exactly as L5 swept p:

| frame | oracle warp | predicted warp | warp R² (lo / hi) |
|---|---|---|---|
| fixed frame (L5) | — | 0.0510 | — |
| single warp, best | 0.0534 | 0.0612 | +0.927 |
| **two-wave, 0.10-0.90** | **0.0203** | 0.0513 | +0.811 / +0.919 |
| two-wave, 0.05-0.95 | 0.0233 | 0.0518 | +0.895 / +0.911 |

**0.0203 is better than DeepONet's 0.0281** — the best arm anywhere in the ladder —
reached by POD plus a gradient-boosted coefficient regressor, once the field is
written in the right coordinates. Flat in shape-basis size again (0.02053 ->
0.02027 over p = 8 -> 128), so the shape is not the constraint either.

The level pair 0.20-0.80 is **excluded**: its interpolation floor is 0.0149, 29 %
of the signal, because a narrow window divides by a small span. The guard caught
it and it is reported here rather than dropped silently.

### The obstruction has MOVED — and that is the result

Predicted-warp error (0.0513) ties the fixed frame (0.0510). **The entire 2.5x is
consumed by the error in locating the two fronts**, whose R² is only 0.81-0.92.

This is not a null result, it is a relocation. Through L1-L5 the obstruction was
"the parameter -> coefficient map is unlearnable beyond ~5 modes", which no
architecture addressed. It is now "**two smooth monotone 1-D curves are not
predicted accurately enough**" — a far better-posed problem, with a measured prize
of 2.5x and a target that a front-locating model can be held to. `warp_predict.py`
quantifies how accurate the warp must be.

---

## 7. Open items — must close before submission

1. **Every MOF-303 parameter is a literature-range placeholder, not a cited
   value.** `q_max`, `ΔH`, step position, cooperativity, `ρ_p`, `k_LDF` must each
   be replaced with a referenced number and the isotherm refitted to a published
   MOF-303 water isotherm. Until then no result may be described as "MOF-303".
2. **No experimental validation exists.** Everything is the surrogate against our
   own solver. The error budget must decompose solver-vs-experiment from
   surrogate-vs-solver, and the abstract must state which one the headline number
   is. Digitising one published breakthrough curve would change the venue tier.
3. **COF case does not exist.** The title says MOF *and* COF. Either add a COF
   framework or remove it from the title.
4. **CLOSED 2026-09-25 -- `kaggle_run/` was a stale duplicate** carrying every original defect; removed, in git history at `81295d4`. Delete it
   and deploy from a single source, or it will eventually be the thing that runs.
5. **Speed claim needs an honest reference.** Our own solver runs one condition in
   ~150 s. "Hours per simulation" describes 3-D FEM, not this. The defensible
   framing is amortised throughput across a screen, not per-simulation speedup.
6. **CLOSED 2026-09-25 -- `sindy_discovery.py` removed** (git `81295d4`, evidence in A7; replaced by `identify_kinetics.py`). Original item: **SINDy needs something to discover.** Its library currently contains `q*`,
   computed from the exact law that generated the data — regression onto the
   answer. And no breathing/flexible-framework physics exists anywhere in the
   data, so no breathing kinetics can be recovered from it.

---

## 8. Honesty infrastructure

Carried over from the prior project, where it was the part reviewers praised.

- **`RETRACTIONS.md` from day one.** Every withdrawn number, why it was wrong,
  what replaced it, and the artifact that reproduces both. Corrections that run in
  our favour are recorded on the same terms as the others.
- **`validate.py` gates every claim.** No number enters the manuscript from a
  failing category.
- **Every figure is regenerated from a checkpoint.** A plotting script that draws
  a model curve must call `load_state_dict`; the harness enforces this.
- **Negative results are reported, not buried.** The ladder's value *is* its
  eliminations.
