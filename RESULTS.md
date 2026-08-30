# Results — running summary

Every number here is reproduced by a script in this repository and gated by
`validate.py`. Withdrawn numbers are in `RETRACTIONS.md`; the frozen experimental
design is in `03_LADDER_PROTOCOL.md`.

Last updated 2026-08-24.

---

## Where the ladder stands

| rung | hypothesis tested | verdict |
|---|---|---|
| **L0** | "the reference is trustworthy" | ✅ verified against 4 closed-form solutions |
| **L1** | "you just need more data" | ⚠️ **NARROWED — see A18.** Conditions axis eliminated; **materials axis is NOT** (1.82×, unsaturated) |
| **L2** | "the model is too small" | ✅ **eliminated** |
| **L3** | "you need a better basis" | ✅ eliminated for RBF-KAN; ⚠️ the Chebyshev 200k cell is **withdrawn** (**A19**, **B24**) and the rung is being re-run |
| **L4** | "add the PDE residual" | ✅ **no difference** on the material axis |
| **L5** | "you need an operator" | ✅ eliminated *for linear-reconstruction operators*; n-width prediction **refuted**. ⚠️ FNO/WNO never run (**B33**); numbers superseded (**A20**) |
| **L6** | **"joint fitting is fine"** | ✅ **H1 NOT SUPPORTED** — separate does not beat joint |
| **L7** | "deep learning is needed at all" | ✅ **eliminated — learning is justified** |

---

## L0 — the ground truth is verified, not asserted

| check | tests | error |
|---|---|---|
| Inert tracer vs van Genuchten third-type | advection, dispersion, Danckwerts BC | **1.69e-3** abs; front **0.023 %** |
| Retarded front, R = 901 | isotherm coupling, equilibrium limit | **0.027 %** |
| Thermal wave, adsorption off | energy equation | **0.012 %** |
| LDF vs Anzelius–Schumann J-function | kinetics | **3.0e-4** abs |

Global mass balance closes to **0.050 %**; grid convergence 0.055 % (generic) and
0.323 % (MOF-303-like) at N_z = 2000.

---

## The physics that shapes everything downstream

**The isotherm must be Type V with Henry's law intact.** Single-site Langmuir has
zero inflection points and predicts the largest uptake gradient at RH → 0 — the
opposite of the mechanism AWH depends on. A bare Hill form gives the step but
`q ∝ c^n` at the origin, violating Henry's law. The dual-term Do–Do form gives
both: 1 inflection point, steepest uptake at **14 % RH**, finite
`K_H = 0.281 mol/kg per mol/m³`, and `q_st = -ΔH + RT` reproduced to **0.004 %**
identically at 25/50/75 % loading.

**The Type V isotherm produces a two-wave breakthrough**, not a sigmoid:

| c/c_in | 0.05 | 0.20 | 0.40 | 0.60 | 0.68 | 0.95 | 0.99 |
|---|---|---|---|---|---|---|---|
| t (h) | 0.09 | 0.17 | 2.94 | 12.46 | 16.70 | 18.56 | 18.90 |

A fast, spreading Henry wave, then a slow self-sharpening cooperative shock. Two
sharp features whose positions move *independently* with material parameters.

---

## The Kolmogorov n-width is algebraic

Measured by POD on the 691 training fields, fitted over n = 8–64:

| field | modes for 90/99/99.9/99.99 % | energy tail | d_n | alg. R² | exp. R² |
|---|---|---|---|---|---|
| c | 3 / 11 / 32 / 68 | n^−2.45 | **n^−1.23** | 0.9910 | 0.9737 |
| q | 2 / 8 / 27 / 65 | n^−2.22 | **n^−1.11** | 0.9897 | 0.9759 |
| T | 3 / 13 / 36 / 76 | n^−2.39 | **n^−1.20** | 0.9911 | 0.9731 |

Halving the error requires **1.76× the modes, permanently**. Any method whose
output is a linear combination of a fixed basis — POD-plus-regressor, and
DeepONet — is bounded below by this. Scoped to n = 8–64: the spectrum steepens
beyond, and 691 samples cannot resolve a tail at their own limit.

> **…and it turned out not to matter.** L5 tested this bound and found it
> completely inactive: DeepONet sits **59× above** it at p = 128 and does not move
> as the bound falls 28.7×. The mathematics is right; the prediction built on it
> was wrong. See L5 below and retraction **A17**.

---

## L1 — data-driven interpolation does not transfer

nRMSE on c, novel-material split, 64 POD modes, 3 seeds:

| arm | train | novel-material | × POD floor |
|---|---|---|---|
| xgb | 0.0126 | **0.0485 ± 0.0008** | 33× |
| rf | 0.0196 | **0.0488 ± 0.0004** | 34× |
| mlp | 0.0480 | **0.0586 ± 0.0004** | 40× |
| ridge | 0.0677 | **0.0676 ± 0.0000** | 46× |

At the calibrated α = 0.005, **xgb, rf and mlp are mutually indistinguishable**;
only ridge separates. Best arm: 4.9 % nRMSE and a **0.42 h error in the 50 %
breakthrough time** — a visibly wrong curve, not a near-miss.

**Audited three ways.** Rank: the gap is flat in POD rank (arm error changes
1.01× from 8 to 128 modes while the floor falls 27×). Calibration: the cluster
bootstrap over-rejects (8.5 % at nominal 5 %), so α = 0.005 is used — one verdict
did not survive (A13). Splits: 0.0502 ± 0.0019 across 5 independent holdout sets.

---

## L2 — capacity is eliminated

26 configurations × 3 seeds. Every family **saturated** at its last step:
mlp_width (optimum w128), mlp_depth (d6), xgb_depth (md5), rf_leaf (at RF's
ceiling). Best configuration anywhere improves on L1 by **~1 %**.

The decisive evidence is decoupling: XGBoost from md2 → md10 drops **training
error 41×** (0.0450 → 0.0011) while novel-material error passes a minimum at md5
and then *worsens*. The models are already deep in the overfitting regime.

---

## L3 — architecture family is eliminated, and refuted

At matched parameter count (MLP width 269 vs KAN 98/103 for the same 200k
budget), novel-material nRMSE:

| budget | mlp | rbf_kan | cheby_kan |
|---|---|---|---|
| 50k | **0.0585** | 0.0768 | 0.1220 |
| 200k | **0.0573** | 0.0771 | 0.1263 |
| 800k | **0.0599** | 0.0709 | 0.1120 |

**8 of 9 pairwise comparisons significant**, ordering identical at every budget.
Seed robustness also favours the MLP (sd 0.0019 vs 0.0032 / 0.0041).

The KAN hyperparameters were audited so this is not a strawman. The trend is
**monotone in the KAN-ness of the edge**: rbf_kan 0.0633 → 0.1013 as grids go
4 → 24; cheby_kan 0.0889 → 0.1250 as degree goes 3 → 11. The best KAN found
anywhere is the *least* KAN-like (grids = 4, 0.0633), and it is still
significantly behind the MLP (diff −0.0060, CI [−0.0120, −0.0008]).

> **Consequence for this project.** A paper cannot claim PIKAN or DeepOKAN is the
> right architecture here — our own matched-parameter measurement says the
> opposite. The interpretation is not "KANs are bad" but that **at a fixed
> budget, parameters spent on per-edge basis richness buy training fit and not
> generalisation, while the same parameters spent on width buy both.** RBF-KAN
> fits the training set as well as or better than the MLP at every budget and is
> worse on held-out materials every time.
>
> This is consistent with two independent priors (Shukla et al., CMAME 2024; the
> prior project's retraction A3) and extends them to adsorption with a mechanism.
> The KAN arms remain valuable **as eliminations**.

---

## L5 — the operator rung, and the strongest mechanism in the project

90 configurations (2 families × 5 basis sizes × 3 learning rates × 3 seeds), all
at ~200 k parameters and 8000 steps. Each family scored at **its own best
learning rate** per basis size. Novel-material nRMSE on c:

| p | POD floor | DeepONet | × floor | DeepOKAN |
|---|---|---|---|---|
| 8 | 0.01440 | **0.0281** | 2.0× | 0.0392 |
| 16 | 0.00731 | **0.0293** | 4.0× | 0.0357 |
| 32 | 0.00331 | **0.0291** | 8.8× | 0.0498 |
| 64 | 0.00135 | **0.0296** | 21.9× | 0.0818 |
| 128 | 0.00050 | **0.0296** | **59.0×** | 0.0884 |

**The floor falls 28.7×. DeepONet moves 1.05×** — all four paired comparisons
against p = 8 return *no difference* at the calibrated α. Train error is flat too
(0.0119 → 0.0135), so this is not a generalisation artefact: the model cannot use
the extra modes on data it has already seen.

### What binds instead — measured, not inferred

Separating the two terms a linear reconstruction can fail on, in the **optimal**
basis so the answer cannot depend on what basis DeepONet happened to learn:

| p | basis error (true coefficients) | coefficient-map error |
|---|---|---|
| 8 | 0.01440 | 0.0515 |
| 32 | 0.00331 | 0.0509 |
| 128 | 0.00050 | 0.0510 |

Flat to four decimals. The per-mode reason: on held-out materials the
params → coefficient map scores **R² = 0.946 on mode 1**, 0.39–0.58 on modes 2–5,
and a **median R² of −0.014 beyond mode 24** — worse than predicting the mean.
Only 3 of 128 modes clear R² > 0.5, and that count is 3 at *every* p.

Against an oracle reconstruction handed the true coefficients for its first k
modes:

| method | novel-material nRMSE | equivalent oracle rank |
|---|---|---|
| POD + strongest coefficient regressor | 0.0510 | ~2 modes |
| DeepOKAN, best anywhere | 0.0357 | ~3 modes |
| **DeepONet, best anywhere** | **0.0281** | **~4 modes** |

**Giving DeepONet 128 basis functions buys it the accuracy of four.**

This is the same signature the L1 audit found and mis-attributed to L1. **Three
independent function classes — POD+rf, POD+HGB, DeepONet — are all flat in rank
while the floor falls ~28×.** Training basis and coefficients together is worth a
constant **1.8×** and nothing more.

### DeepOKAN's failure is optimisation, not accuracy

**10 of 45 DeepOKAN runs collapsed; 0 of 45 DeepONet runs did.** All ten land on
the same point in function space, agreeing to **2.7e-7** across different p,
learning rates *and* seeds — detected by seed-invariance, which a trained network
cannot exhibit. The rate is monotone in stack width: 0/9 at p = 8 and 16, 1/9 at
32, 4/9 at 64, **5/9 at 128**.

**L5 does not replicate L3.** At their best configurations the two families are
statistically **indistinguishable** (0.0281 vs 0.0357, CI [−0.0197, +0.0044]).
DeepOKAN is never better, is significantly worse at p ≥ 32, and fails to train
22 % of the time. With 12 held-out materials this null cannot resolve a 21 %
difference — "no difference detected", never "equivalent".

### Verdict

**The operator rung is eliminated and the n-width hypothesis with it.** The
obstruction is the parameter → coefficient map, which carries about five modes'
worth of generalisable information out of 128. No amount of basis, capacity or
edge richness addresses that — consistent with L2 and L3 already being eliminated.
What would address it is a **nonlinear** reconstruction: a co-moving frame that
removes the front position before projection.

---

## The co-moving frame — the standard fix, tested and refuted

L5 left one lever unexplored. Its whole signature — flat in basis size,
coefficients unpredictable past ~mode 5 — is the textbook fingerprint of
**transport**, whose textbook remedy is to factor the front position out before
projecting. We warped each field onto its own local arrival time,
`C(z, τ) = c(z, t_L(z) + τ)`, and swept the alignment level and the shape basis.

**Measured first, before invoking any explanation:** at the outlet the separation
between the fast Henry wave and the cooperative shock, `t(0.9) − t(0.1)`, spans
**[0.025, 0.992]** in normalised time — a **40× range** across the dataset. One
shift cannot align two waves whose separation varies that much.

**The warp makes the n-width worse.** Modes needed for 99.9 % of training variance:

| frame | original | L = 0.1 | L = 0.5 | L = 0.9 |
|---|---|---|---|---|
| modes for 99.9 % | **31** | 42 | **102** | 84 |

Aligning on the 0.5 crossing — the obvious choice — *triples* the required rank.

**And it does not help accuracy, even given the warp for free:**

| alignment | warp R² | best oracle-warp | best predicted-warp |
|---|---|---|---|
| L = 0.1 | +0.811 | 0.0593 | **0.0612** |
| L = 0.5 | +0.927 | **0.0534** | 0.0645 |
| **fixed frame (L5)** | — | — | **0.0510** |

The decisive row is the oracle: **handed the exact front trajectory for free, the
co-moving frame still loses to the fixed frame.** The warp is predictable
(R² = 0.927); the frame itself is simply wrong for this system. The interpolation
floor is 0.0024–0.0030, under 6 % of the signal, so it cannot manufacture this.

**Scope.** What is refuted is *single-front* alignment. The measurement that killed
it named its successor — and that successor works.

---

## The two-wave warp — the right frame, and an unrealised 2.5×

Use *two* shifts, one per wave, normalising the interval between them:
`σ = (t − t_lo(z)) / (t_hi(z) − t_lo(z))`. This removes both the arrival time and
the transition width.

**It collapses the n-width where one shift inflated it.** Modes for 99.9 % of
training variance:

| frame | original | single warp (L=0.5) | two-wave 0.10–0.90 | two-wave 0.05–0.95 |
|---|---|---|---|---|
| modes for 99.9 % | 31 | **102** | 17 | **13** |

**And the reconstruction error falls 2.5× — given the warp:**

| frame | oracle warp | predicted warp | warp R² (lo / hi) |
|---|---|---|---|
| fixed frame (L5) | — | 0.0510 | — |
| single warp, best | 0.0534 | 0.0612 | +0.927 |
| **two-wave, 0.10–0.90** | **0.0203** | 0.0513 | +0.811 / +0.919 |
| two-wave, 0.05–0.95 | 0.0233 | 0.0518 | +0.895 / +0.911 |

The oracle-warp arm reaches **0.0203**, below DeepONet's best (0.0276), using only
POD plus a gradient-boosted regressor once the field is written in the right
coordinates. Flat in shape-basis size again (0.02053 → 0.02027 over p = 8 → 128),
so the shape is not the constraint either. The 0.20–0.80 pair is **excluded**: a
narrow window divides by a small span and its interpolation floor reaches 29 % of
the signal. The guard caught it; it is reported rather than dropped silently.

> ⚠️ **The oracle arm is handed the true front trajectories, and DeepONet is not.**
> This is not a like-for-like comparison and it may not be presented as one — a
> reviewer reads a leaked-label comparison in one line, and this project's
> credibility is the thing it cannot afford to spend. The comparable arm is the
> **predicted** warp, and the powered verdict on it is below: no difference from
> the fixed frame, with a significant 2.17× still on the table.

### The obstruction has moved — and that is the result

Run to full protocol 2026-08-30 in `warp_verdict.py`: **3 seeds across every
stochastic component, both arms computed in the same run** (the earlier comparison
imported the fixed-frame number as a hard-coded literal), paired cluster bootstrap
by material at the calibrated α = 0.005. `results/warp_verdict.json`.

| arm | novel-material nRMSE(c) | sd (3 seeds) |
|---|---|---|
| fixed frame | 0.05005 | 0.00034 |
| two-wave, **predicted** warp | **0.04770** | 0.00159 |
| two-wave, **oracle** warp | **0.02203** | 0.00029 |

```
fixed vs two-wave (predicted) : diff +0.00235  CI [-0.00812, +0.01183]  NO DIFFERENCE
fixed vs two-wave (oracle)    : diff +0.02802  CI [+0.01990, +0.03668]  SIGNIFICANT
```

**Two statements, and both are needed.** The honest arm does *not* beat the fixed
frame — the 4.7 % improvement in the mean is inside the noise, and the earlier
"two-wave now beats the fixed frame" line, computed from one seed and a 0.4 %
margin, is withdrawn as defect **B28** before it reached this document. But the
oracle gap **is** significant and large: given the true front trajectories, the
same POD-plus-regressor arm is **2.27× better**, with a CI far from zero.

So: **the entire gain is consumed by the error in locating the two fronts**, and
that is now a measured, powered statement rather than an impression.

This is a relocation, not a null. Through L1–L5 the obstruction was "the
parameter → coefficient map is unlearnable beyond ~5 modes", which no architecture
touched. It is now "**two smooth monotone 1-D curves are not located accurately
enough**" — a far better-posed problem, with a **statistically established prize of
2.17×** and a target a front-locating model can be held to. The current predictor
reaches R² ≈ 0.85–0.88 on the lower trajectory and 0.91–0.92 on the upper; the
payoff curve in `warp_predict.py` says R² ≈ 0.97 would already recover most of the
gap. Two smooth monotone 1-D curves are a far easier object to attack than a 2-D
field, which is the point.

> **Do not quote the oracle number against any arm that is not also handed the
> warp.** It leaks the answer. It is an upper bound on what a perfect
> front-locating model could buy, and it is reported here only to size the
> remaining headroom.

---

## L7 — the classical control is beaten, and that is a real finding

Scored like-for-like on the **exit curve** (the classical forms predict the curve,
not the field; comparing 0.0485 field against 0.2307 curve would be meaningless).
Novel-material split:

| method | exit nRMSE | dt50 error | cost/curve | trained? |
|---|---|---|---|---|
| POD floor | 0.0045 | 0.01 h | — | — |
| **rf (best learned)** | **0.0725 ± 0.0004** | **0.39 h** | ~ms | yes |
| klinkenberg | 0.2307 | 0.87 h | 0.26 ms | **no** |
| constant_pattern | 0.2673 | 0.82 h | 0.64 ms | **no** |
| equilibrium_shock | 0.2725 | 0.87 h | 0.11 ms | **no** |

All three differences significant at the calibrated α. The best learned arm beats
the best closed form by **3.2×** on nRMSE and **2.2×** on breakthrough time.

**Why this differs from the prior conduction project**, where a 128-number linear
convolution beat every deep operator: conduction with a cyclic source is *linear
and time-invariant*, so a Green's function is the exact solution operator — a
learned model can at best match it. Adsorption with a Type V isotherm is
nonlinear, and every closed form linearises somewhere; the **two-wave structure
violates all three assumptions** (Klinkenberg assumes a linear isotherm,
constant-pattern a non-spreading favourable front, equilibrium theory infinitely
fast kinetics).

The transferable statement is neither "classical wins" nor its reverse, but:
**a classical model wins exactly when the physics it assumes is the physics that
is there.**

---

## Two design degeneracies found and corrected before running

Both from the same root cause — treating a synthetic surrogate study as an
accuracy contest against a reference that is already exact. It cannot be beaten
on accuracy, only on **accuracy per unit inference cost**, or matched **from less
information**.

**B18 — L7 as originally specified was vacuous.** "LDF + fitted isotherm" is the
model that *generated* the data, handed the parameters that generated it. It
would have reproduced the reference exactly. Corrected to fast closed-form theory.

**B19 — L6 could not test H1.** Every arm was handed the eleven generative
parameters, so a separate-identification arm had nothing to identify. Re-specified
over **observable descriptors**: an isotherm fingerprint measured at 12 humidities
× 3 temperatures, plus bed/operating properties, with `k_LDF` withheld.

The substitution is verified rather than assumed — a strong regressor is trained
to recover each withheld parameter from the descriptors alone:

| withheld | R² on held-out materials | reading |
|---|---|---|
| step_rh / q_max / isotherm_n | 0.96 / 0.93 / 0.93 | equilibrium shape observable, as a measured isotherm should be |
| delta_H | 0.75 | recoverable via the van't Hoff slope across three temperatures |
| henry_fraction | −0.00 | not recoverable |
| **k_LDF** | **−0.61** | **not recoverable at all** |

Three temperatures are not decoration: with one, ΔH is unrecoverable (R² = −0.81)
and any model would be blind to the isosteric heat. This is exactly the structure
H1 needs — the equilibrium object observable, the kinetic object hidden.

---

## L6 — H1 is NOT SUPPORTED

Run 2026-08-22. Three arms, 3 seeds, observable descriptors (54 features, generative
parameters withheld). `results/l6_results.json`.

**Pre-declared failure condition** (protocol §L6, line 700–702): "if the
separate-vs-joint transfer gap has a bootstrap CI including zero at 3 seeds and
the calibrated alpha, H1 is reported as not supported, in the abstract, in those
words."

Novel-material nRMSE at matched ~120,000 parameters:

| arm | width | params | c (novel) | q (novel) | exit nRMSE | dt50 |
|---|---|---|---|---|---|---|
| **joint** | 190 | 120,273 | **0.0566 ± 0.0039** | **0.1158 ± 0.0056** | **0.0546 ± 0.0027** | **0.33 ± 0.05 h** |
| separate | 168 | 118,948 | 0.0721 ± 0.0105 | 0.1259 ± 0.0091 | 0.0604 ± 0.0066 | 0.37 ± 0.09 h |
| separate_noeq | 168 | 118,948 | 0.0728 ± 0.0073 | 0.4564 ± 0.1939 | 0.0592 ± 0.0056 | 0.36 ± 0.09 h |

Cluster bootstrap, calibrated α = 0.005:

```
separate − joint (c, novel-material):
  observed mean diff: +0.0147  (separate is WORSE)
  99.5 % CI: [−0.0155, +0.0450]  → CI INCLUDES ZERO → NOT SIGNIFICANT
```

**Verdict: H1 is not supported.** Structural decomposition does not produce a
statistically significant improvement on novel materials in this system. The
point estimate goes in the *wrong direction*.

### Why the separate arm does not help here

1. **The kinetic coefficient is unrecoverable** from the observable descriptors
   (R² = −0.61, identifiability study). The `kin_head` must infer a parameter it
   has no information about.
2. **Error amplification through hard structure.** The Duhamel integrator in the
   separate arm composes q from the equilibrium and kinetic heads. Small errors
   in the equilibrium head produce large errors in q, especially at early times.
   The `separate_noeq` ablation confirms this catastrophically: q nRMSE 0.4564.
3. **Variance cost.** The separate arm's seed-to-seed spread is 2.7× higher
   (sd 0.0105 vs 0.0039), consistent with L3's finding that structural richness
   costs robustness.

### What this means for the paper

The paper that was planned — "structural decomposition is the answer" — is not
supported by the evidence. The paper these results do support is: **five standard
ML interventions for closing the transfer gap in stiff multiphysics surrogates
were tested. None closed it.** That negative result, together with the
methodology that produced it, is the contribution.

---

## Honesty infrastructure

- **`validate.py`** — 22 gates, all passing. No number enters the manuscript from
  a failing category.
- **`RETRACTIONS.md`** — 21 Part-A withdrawals, 33 Part-B defects caught before
  contamination. **15 of the Part-B defects are our own errors** — in the
  analysis, the validation gates, or the frozen protocol itself — recorded on the
  same terms as errors in the code. One Part-A retraction (**A17**) withdraws a
  claim the protocol had called its most important result.
- Figures are computed from data or loaded checkpoints; the harness forbids a
  plotting script from synthesising a series it labels as a model prediction.
- Comparisons use the **calibrated** α = 0.005, chosen because the percentile
  cluster bootstrap was measured to over-reject at these cluster counts.

---

## Open items before submission

1. Every MOF-303 parameter is a literature-range placeholder. Until replaced with
   cited values and the isotherm refitted to a published water isotherm, **no
   result may be described as "MOF-303"**.
2. No experimental validation exists. The error budget must separate
   solver-vs-experiment from surrogate-vs-solver.
3. No COF case exists; the title claims one.
4. `kaggle_run/` is a stale duplicate carrying the original defects.
5. The speed claim needs an honest reference — our own solver runs one condition
   in 4.2 s (MOF-303 config, N_z = 2000).
6. SINDy needs something to discover: its library currently contains `q*`,
   computed from the law that generated the data.
