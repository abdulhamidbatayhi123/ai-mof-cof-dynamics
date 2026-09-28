# Results — running summary

Every number here is reproduced by a script in this repository and gated by
`validate.py`. Withdrawn numbers are in `RETRACTIONS.md`; the frozen experimental
design is in `03_LADDER_PROTOCOL.md`.

Last updated 2026-09-05.

---

## Where the ladder stands

| rung | hypothesis tested | verdict |
|---|---|---|
| **L0** | "the reference is trustworthy" | ✅ verified against 4 closed-form solutions |
| **L1** | "you just need more data" | ⚠️ **NOT ELIMINATED on v2** — the materials axis is still falling at 192 training materials (β = 0.22), and the basis needs none of that data: it is all coefficient map. Arms re-run on v2: the MLP is now the best fixed-basis arm, significantly |
| **L2** | "the model is too small" | ✅ every optimum bracketed on legacy **and on v2**; ⚠️ **but the optimum moves with the material count** — at 192 materials an 8-layer MLP beats the L1 setting by 21 % where legacy found 1 % (**A26**) |
| **L3** | "you need a better basis" | ✅ **FINAL** — re-run and fully re-tuned after **A19**/**B24**; MLP beats both KAN families at matched parameters, 6/6 significant, every KAN optimum bracketed over 8 learning rates spanning 3.5 decades; the MLP selects the bottom edge at every budget, saturated to 0.12–0.60 % (`l3_edges.py`) |
| **L4** | "add the PDE residual" | v2 (L4b, `PREREG_L4b_v2.md`): **time axis — NO DIFFERENCE** at the best weighting (w1e-5: 0.01323 vs twin 0.01310, CI spans zero, MDE 5 %); the interim "physics worse" reading was reversed by the pre-registered edge extension (B69). **Material axis — NOT YET A VERDICT**: w1e-5 is significantly better (0.02126 vs 0.02314) but sits on the unsaturated sweep edge; w1e-6 queued (autorun job 1b). Physics at inference destroys transfer on every arm (w1e-5 material: 0.0210 -> 0.1224). |
| **L5** | "you need an operator" | ✅ **FINAL** — eliminated *for linear-reconstruction operators*; n-width prediction **refuted** (**A17**). FNO **was** run (**B33** discharged) and is significantly better, 0.0216 vs 0.0265, but still 43× above the POD floor; legacy numbers superseded (**A20**) |
| **L6** | **"joint fitting is fine"** (H1, primary) | ✅ **RESOLVED on v2** — mechanism refuted (Da slope null), but separate **does** beat joint by 3.7 % (CI 1.0–6.5 %), reversing the legacy sign |
| **L7** | "deep learning is needed at all" | ✅ **eliminated on legacy and on v2** — the best closed form is 3.7× worse than the learned arm on the exit curve, paired over 240 materials |

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
`q ∝ c^n` at the origin, violating Henry's law. A **dual-term form in the spirit of
Do & Do** — a Langmuir primary-site term plus a cooperative Sips term — gives both:
1 inflection point, steepest uptake at **14 % RH**, a finite Henry constant, and
`q_st = -ΔH + RT` reproduced to **0.004 %** identically at 25/50/75 % loading.

> **Two corrections to how this used to be written.**
> **(B56)** It is *not* "the Do–Do form". Do & Do superpose an **n-layer BET**
> primary term with a Sips term; ours is a **Langmuir** primary term with a Sips
> term. What we take from them is the two-term construction and the fact that **only
> the primary term carries the Henry slope** — their Sips term, like ours, has slope
> exactly zero at the origin. Their cluster exponent is fixed (a = 5); ours is a
> sampled material parameter, closer to Do, Junpirom & Do (2009). "Type V" is our own
> IUPAC-grounded label — Buttersack calls this family Type IV.
> **(B57)** `K_H = 0.281` is **one configuration's** value. Across the 240 sampled
> materials K_H spans **0.032–2.52 mol/kg per mol/m³, 1.9 decades**, median 0.359.

**Henry's law holds for every one of the 240 materials, and the width of the region
where it dominates does not** (`isotherm_space.py`, `results/isotherm_space.json`,
gated). `isotherm_n > 1` strictly for every material (minimum 1.009), so the
cooperative term is `o(c)` at the origin and `K_H` is finite and positive everywhere.
But the concentration at which the cooperative term reaches 1 % of loading — the top
of the accessible Henry region — spans **508 decades**:

| | log₁₀(c_Henry / median feed c_in) |
|---|---|
| max (widest Henry region) | **−0.9** |
| median | **−2.0** |
| p05 | −15.8 |
| min | −509 |

**73 of 240 materials have no Henry region above 10⁻³ of the feed, and 34 none above
10⁻⁶.** For those the isotherm is effectively Sips-like at every concentration the
column visits. The design claim is therefore *thermodynamic validity by construction*,
which holds everywhere — not *an experimentally accessible linear regime*, which does
not. Report the distribution, never one configuration's number.

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

## L1 on the legacy dataset — data-driven interpolation does not transfer

> ⚠️ **Superseded on v2 in its ordering.** With four times the materials the MLP
> becomes the best arm and beats XGBoost significantly (0.0306 vs 0.0361); the
> "xgb, rf and mlp are indistinguishable" reading below is a 12-cluster result. See
> "L1-v2 — the arms" below. What survives unchanged is the *size* of the transfer
> gap relative to the POD floor, which grew from 33× to 109×.

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

## L2 on the legacy dataset — capacity is eliminated *at 48 training materials*

> ⚠️ **Scoped by retraction A26.** This section is the legacy (48-material) result and
> its "~1 %" conclusion holds only there. On dataset v2, with 192 training materials
> per fold, the same pre-registered sweep puts the depth optimum at **8 layers** and
> the gain at **21 %**. See "L2 on dataset v2" below; do not quote the ~1 % without
> the material count it was measured at.

26 configurations × 3 seeds. Every family **saturated** at its last step:
mlp_width (optimum w128), mlp_depth (d6), xgb_depth (md5), rf_leaf (at RF's
ceiling). Best configuration anywhere improves on L1 by **~1 %**.

The decisive evidence is decoupling: XGBoost from md2 → md10 drops **training
error 41×** (0.0450 → 0.0011) while novel-material error passes a minimum at md5
and then *worsens*. The models are already deep in the overfitting regime.

---

## L3 — architecture family is eliminated, and refuted

**Re-run and fully re-tuned, 2026-08-31**, after defect **B24** (11 of the original
54 runs reported the error of a random initialisation; the published
`cheby_kan`@200k cell was 3/3 untrained — retraction **A19**).

Corrected recipe: patience 400 → 2000 steps, `min_steps = 1000`, a hard failure on
`best_step == 0`, 12 000 steps, and a learning-rate grid extended in three passes
until **every** selected optimum was bracketed. **69 arms, 8 learning rates spanning
3e-5 to 1e-1 — three and a half decades**, 3 seeds each.
`results/l3_results.json` + `l3_bracket.json` + `l3_cheby_1e-1.json`.

Novel-material nRMSE on c, each family at **its own best learning rate**:

| budget | mlp | rbf_kan | cheby_kan |
|---|---|---|---|
| 50k | **0.0564** ± 0.0003 | 0.0768 ± 0.0041 | 0.1063 ± 0.0186 |
| 200k | **0.0570** ± 0.0023 | 0.0703 ± 0.0032 | 0.1120 ± 0.0150 |
| 800k | **0.0572** ± 0.0003 | 0.0702 ± 0.0013 | 0.1028 ± 0.0095 |

**6 of 6 pairwise comparisons against the MLP are significant** at the calibrated
α = 0.005, with the ordering identical at every budget:

```
 50k  mlp vs rbf_kan    diff -0.0204  CI [-0.0337, -0.0102]   SIGNIFICANT
 50k  mlp vs cheby_kan  diff -0.0499  CI [-0.0783, -0.0290]   SIGNIFICANT
200k  mlp vs rbf_kan    diff -0.0133  CI [-0.0249, -0.0037]   SIGNIFICANT
200k  mlp vs cheby_kan  diff -0.0550  CI [-0.0741, -0.0383]   SIGNIFICANT
800k  mlp vs rbf_kan    diff -0.0130  CI [-0.0255, -0.0034]   SIGNIFICANT
800k  mlp vs cheby_kan  diff -0.0456  CI [-0.0776, -0.0225]   SIGNIFICANT
```

### Every optimum is bracketed — the strawman objection is closed

This is the first rung in the project to satisfy protocol rule 4 *completely*, and
it is the one where it matters most, because the KANs are the arm being argued
against:

| | selected lr | status |
|---|---|---|
| `rbf_kan`, all three budgets | 3e-3 / 1e-2 / 3e-3 | **interior** — turns over on both sides |
| `cheby_kan`, all three budgets | 3e-2 / 3e-2 / 1e-2 | **interior** — turns over at 1e-1 |
| `mlp`, all three budgets | 3e-5 | edge, but **saturated to 0.1–0.6 %** |

An edge selection only matters if the metric is still moving there. The MLP's is
flat — 0.0564 vs 0.0566 across a 3× change — so extending downward cannot help it.
Both KAN families have genuine interior optima. **The KANs were given eight
learning rates over three and a half decades and their best configurations are
bracketed on both sides.**

### The tuning envelope is itself a result

The families want learning rates **three orders of magnitude apart**: `cheby_kan`
optimises at 1e-2–3e-2 while the MLP optimises at 3e-5, and `mlp`@200k *diverges*
at exactly the rate `cheby_kan`@200k needs. Three configurations failed on every
seed and four more on some (`analyze_l3_merged.py`, B70); all are excluded and listed, not averaged in.

That is **our measurement**, and it is reported rather than smoothed over. It sits in
a literature which says that optimisation treatment dominates accuracy for
physics-informed models, KANs included (Kiyani et al., *CMAME* 446:118308, 2025 — who
find that **both** PINNs and PIKANs improve by orders of magnitude under the **same**
self-scaled quasi-Newton schemes, not that KANs need different ones), and that deep
PIKANs are unstable without KAN-specific initialisation and architecture (Rigas et al.,
*CMAME* 452:118761, 2026). It also pre-empts the obvious attack: we did not tune the
MLP and leave the KANs at a default; we tuned both to their own interior optima and the
ordering held.

> **The literature is split, and this result is worth more because of it — B46.** An
> earlier version of this section cited Rigas and Kiyani for "the KAN literature's own
> central claim that KANs require different optimisation". **Neither paper says that**,
> and three of the four KAN papers we cite do not support a general "MLPs win":
> Wang et al.'s KINN (*CMAME* 433:117518) reports that *"KINN significantly outperforms
> MLP regarding accuracy and convergence speed"* on solid-mechanics PDEs; Rigas's
> Residual-Gated Adaptive KANs *"consistently outperform parameter-matched cPIKANs and
> PirateNets"*, and PirateNet is an MLP architecture; and Shukla et al.'s conclusion is
> two-tiered — original B-spline KANs lack accuracy and efficiency, while *modified*
> KANs on low-order orthogonal polynomials are **comparable** to PINNs and DeepONet but
> not robust. A matched-parameter, fully-bracketed measurement is worth **more** in a
> split literature than in a settled one. The honest sentence is that on **this**
> problem — transfer to unseen materials in a stiff two-wave adsorption column, at
> matched parameters, with every optimum bracketed over 3.5 decades of learning rate —
> the MLP wins 6/6, and the papers that disagree with us are cited so a reader can see
> the disagreement rather than discover it.

Seed robustness still favours the MLP by an order of magnitude
(sd 0.0003–0.0023 vs 0.0013–0.0041 and 0.0095–0.0186).

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

**Re-scored 2026-09-01 over every learning rate ever run** — 8 files, 76 arms,
learning rates 5e-5 to 1e-2, all at ~200 k parameters and 8000 steps on the same
128×128 encoding. Each family at **its own best learning rate** per basis size,
with `analyze_l5_merged.py`'s grid-boundary guard confirming each optimum is
interior or saturated. Retraction **A20** withdrew the original numbers.

Novel-material nRMSE on c:

| p | POD floor | DeepONet | × floor | DeepOKAN | × floor |
|---|---|---|---|---|---|
| 8 | 0.01440 | **0.0265** | 1.8× | 0.0392 | 2.7× |
| 16 | 0.00731 | **0.0265** | 3.6× | 0.0357 | 4.9× |
| 32 | 0.00331 | **0.0290** | 8.8× | 0.0498 | 15.1× |
| 64 | 0.00135 | **0.0284** | 21.0× | 0.0652 | 48.2× |
| 128 | 0.00050 | **0.0275** | **55×** | 0.0710 | 142× |

**The floor falls 28.7×. DeepONet moves 0.96×** — all four paired comparisons
against p = 8 return *no difference* at the calibrated α:

```
p= 16  diff -0.00001  CI [-0.00289, +0.00288]   NO DIFFERENCE
p= 32  diff -0.00258  CI [-0.00760, +0.00247]   NO DIFFERENCE
p= 64  diff -0.00197  CI [-0.00738, +0.00374]   NO DIFFERENCE
p=128  diff -0.00102  CI [-0.00585, +0.00491]   NO DIFFERENCE
```

The flat-in-p result **survives full re-tuning across three and a half decades of
learning rate**, and is flatter than originally reported.

---

### FNO: the arm the theory names, and it moves the wall — partly

Lanthaler, Molinaro, Hadorn & Mishra (ICLR 2023, **verified**) prove that operator
architectures with a **linear reconstruction** step — DeepONet, PCA-Net, and
POD-plus-regressor — are lower-bounded on advection-dominated problems, and that
**FNO escapes that bound** via nonlinear reconstruction. L5 originally tested only
the condemned family; the protocol named FNO and it was never run (**B33**).

The prediction was pre-registered in `run_l5_fno.py` before the run: *plateau near
0.028 → the wall belongs to the problem; break the plateau → L5 narrows to
linear-reconstruction operators.* Matched exactly — same encoding, budget, steps,
splits, seeds, and the same bounded output head.

| arm | best config | novel-material nRMSE | × POD floor (p=128) |
|---|---|---|---|
| DeepOKAN | p=16, lr 1e-3 | 0.0357 | 71× |
| DeepONet | p=8, lr 1e-2 | 0.0265 | 53× |
| **FNO** | **modes=4, lr 3e-3** | **0.0216** | **43×** |

```
DeepONet 0.0265 vs FNO 0.0216 | diff +0.0049 CI [+0.0004, +0.0098]  SIGNIFICANT
```

**Both halves of this matter, and neither may be reported without the other.**

**FNO wins, significantly — 23 % better than the best linear-reconstruction arm.**
That is the direction the theory predicts, and it is the first measurement of what
the escape is actually worth on a physical problem rather than in an approximation
bound. L5's conclusion narrows accordingly: *"you need an operator" is eliminated
for linear-reconstruction operators; for nonlinear reconstruction it is reduced,
not eliminated.*

**And FNO does not remove the wall.** It sits **43× above the POD floor** where
DeepONet sits 53×. A 1.23× improvement against a bound 43× below it is a dent, not
an escape. The obstruction measured in `l5_bottleneck.py` — the parameter →
coefficient map — survives the architecture the theory names as its remedy.

**The full FNO sweep** (each row at its own best learning rate, 3 seeds):

| modes | width | novel-material nRMSE |
|---|---|---|
| 4 | 28 | **0.0216** |
| 8 | 14 | 0.0246 |
| 16 | 7 | 0.0277 |

> **Caveat, stated because it is load-bearing.** FNO's `modes` sweep is confounded
> with width at a matched budget: the spectral weights cost ~16·w²·m², so width
> falls 28 → 14 → 7 as modes go 4 → 8 → 16. The monotone degradation therefore
> **cannot** be read as "more Fourier modes do not help" — it is modes traded
> against width, and by modes 16 the network is seven channels wide. The flat-in-p
> statement is made for DeepONet, where p and width are controlled separately, and
> is **not** claimed for FNO.

**One row is worth its own sentence.** At modes 16 the FNO is **seven channels
wide** and still reaches 0.0277 — statistically indistinguishable from the best
DeepONet anywhere (0.0265), which has width 216. A nonlinear reconstruction with a
twentieth of the channel count matches the best linear one. That is the clearest
single piece of evidence in the rung that the reconstruction, not the capacity, is
what separates these families.

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

## The two-wave warp — an established frame, applied where the standard one fails

> **Scope, and prior art (verified 2026-08-30).** Aligning multiple transports is
> **not new.** The two-transport case is the founding worked example of shifted POD
> (Reiss, Schulze, Sesterhenn & Mehrmann, *SIAM J. Sci. Comput.* 40:A1322, 2018),
> whose general formulation covers arbitrary Nₛ independent transports; multi-front
> variants follow in Nair & Balajewicz (2019), Mendible et al. (2020), Krah et al.
> (2025) and Zucatti & Zahr (2025). Shape–timescale decomposition of breakthrough
> curves specifically has been published with a *single* characteristic time (Lee,
> Lee & Kim, SSRN 6874257, 2026). **This section claims none of that.** What is
> ours is the measurement: the n-width in each frame for an inflected Type V
> system, the refutation of single-front alignment under an oracle control, and the
> localisation of the residual obstruction to front prediction. See `CITATIONS.md`.

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

### Monotonicity is violated constantly, and enforcing it does not help

`warp_monotone.py`. The obvious first attack on the front predictor is that it does
not know the two constraints the true trajectories satisfy exactly: `t_lo(z)` and
`t_hi(z)` are non-decreasing in z, and `t_hi > t_lo` everywhere. Nothing in a
POD-plus-regressor pipeline can enforce either — POD modes are not monotone, so a
reconstruction can double back. L4b measured that imposing a known physical bound
*architecturally* was worth 11.5× while the same bound as a penalty was worth
nothing, so this looked like the same lesson pointed at the warp.

**It is not.** Measured over 3 seeds on held-out materials:

| | true | predicted | after isotonic projection |
|---|---|---|---|
| non-monotone samples, `t_lo` | **0.0 %** | **52–58 %** | 0 % by construction |
| non-monotone samples, `t_hi` | 0.0 % | 1.3–1.4 % | 0 % |
| R² (`t_lo`) | — | +0.851…+0.881 | **+0.851…+0.881, unchanged to 3 dp** |
| novel-material nRMSE | — | 0.04770 | **0.04812** |

```
raw 0.04770 vs isotonic 0.04812 | diff -0.00041 CI [-0.00070, -0.00010]  SIGNIFICANT
```

The predictor violates monotonicity in more than half of all samples, the true
trajectories violate it in none — and projecting onto the constraint set changes R²
by *nothing* and makes the reconstruction **significantly worse**. The violations
are therefore frequent but negligible in magnitude: numerical wiggle that the warp
was absorbing, not gross backtracking.

**A monotone-by-construction front predictor is not worth building.** The remaining
2.17× is not a constraint-violation problem; it is raw predictive accuracy of
`t_lo(z)`. That points at material count, not architecture — the learning curve
measured R²(`t_lo`) rising **+0.390 → +0.781 → +0.888 → +0.895** as training
materials went 12 → 24 → 36 → 48, which is why the 240-material v2 dataset is the
next experiment rather than a better warp network.

> *Defect in this analysis, recorded on the same terms as the others.* The
> diagnostic "total backtrack ÷ the trajectory's own range" is **degenerate**: for
> a fast Henry wave that arrives almost simultaneously along the column, the range
> is ~0 and any wiggle gives a ratio of 1.0. Median 0.00000 with p95 1.00000 is
> that degeneracy, not a bimodal population. This is retraction **A15**'s error
> class — never normalise by a quantity that can vanish — committed again, in a
> diagnostic this time rather than a reported metric. The verdict does not depend
> on it: it rests on R² being unchanged and the paired reconstruction CI excluding
> zero. The diagnostic should be reported in absolute time units.

---

## L6-v2 — H1 resolved: the benefit is real, the mechanism is not

**Run 2026-09-02 on dataset v2.** Design frozen in `PREREG_L6_v2.md`, **committed to
git before the first arm trained** — the only rung in this project whose
pre-registration ordering is externally verifiable. 5-fold cross-validation over
all **240 materials** (every material held out exactly once), 3 arms × 3 seeds =
45 runs, α = 0.02 calibrated for this cluster count. `results/l6_v2_results.json`.

**Both invalidation checks passed before any verdict was computed:** the kinetic
object `d_p` is unrecoverable from the observable descriptors (**R² = −0.256**,
worse than the mean) while the equilibrium shape is recoverable (R² = 0.93–0.98);
and Damköhler **per material** — the median over each material's own samples, which is
the axis this slope test regresses on — spans **1.35 decades** (7.7 → 173), enough for a
slope test. The legacy dataset could not have supported this estimand at all: **98.9 % of
its samples** sat above Da 60 (reconstructed as `k_LDF × t_final`, **B63**).

### PRIMARY (pre-registered): the Damköhler mechanism is refuted

```
slope of (separate − joint) on log10(Da), 240 materials
  slope     +0.00140   CI [-0.00329, +0.00618]   NOT SIGNIFICANT
  Pearson r +0.040
```

**The separate-vs-joint difference does not vary with Damköhler.** Correlation is
essentially zero with a CI tight around it. H1-v2's mechanism — that separating the
kinetic object should pay most where kinetics dominate — **is not supported**, and
this time across the regime where it was supposed to work.

### SECONDARY: separate wins, and it is a sign reversal

| arm | mean nRMSE(c), 240 held-out materials |
|---|---|
| joint | 0.0562 |
| **separate** | **0.0541** |
| separate_noeq | 0.0557 |

```
joint 0.0562 vs separate 0.0541 | diff +0.00210  CI [+0.00056, +0.00363]  SIGNIFICANT
```

**Separate is 3.7 % better (CI 1.0 %–6.5 %).** In the legacy run it was **26 %
worse** with a CI spanning zero. The direction has flipped.

**Consistent across every fold and every seed** — not one cell driving it:

| fold | joint | separate | diff |
|---|---|---|---|
| 0 | 0.0555 | 0.0521 | −0.0034 |
| 1 | 0.0599 | 0.0566 | −0.0033 |
| 2 | 0.0526 | 0.0510 | −0.0016 |
| 3 | 0.0560 | 0.0549 | −0.0011 |
| 4 | 0.0561 | 0.0551 | −0.0009 |

seeds 42/43/44: −0.0008, −0.0026, −0.0029.

### Why the test has power now, and what its MDE is

The between-material sd of the arm difference fell from **0.0391 (69 % of the base
error)** in legacy to **0.0104 (18 %)** — a **3.8× noise reduction**. That, with 240
clusters instead of 12, is what turned an unanswerable question into an answerable
one. Design v2's Sobol sampling and physically-consistent Glueckauf kinetics removed
most of the material-to-material chaos.

**MDE (required by A22; never quote this null without it).** Corrected 2026-09-02
(retraction **A25**: the first table, 22 / 68 / 97 / 100 %, came from a simulation
that inflated the within-material noise by √2). From the real paired differences
with `mde.py`, 400 trials, 240 clusters, α = 0.02
(`results/l6_v2_mde_corrected.json`):

| true effect | power |
|---|---|
| 2 % | 26 % |
| 3 % | 55 % |
| **4 %** | **82 %** |
| 6 % | 99 % |
| 10 % | 100 % |

Size at the null 1.8 %; **minimum detectable effect at 80 % power: 4 %**. The
observed 3.7 % sits just under that, so the point estimate may still be optimistic
(winner's curse) even though the CI excludes zero — the lower bound, 1.0 %, is the
conservative reading.

### The verdict, in the pre-declared words

This is outcome four of the four `PREREG_L6_v2.md` §4 anticipated: **pooled
significant, slope null → a uniform benefit unrelated to Damköhler → the benefit is
not kinetic in origin.**

> **Structural decomposition of the equilibrium and kinetic objects gives a small
> but real and reproducible improvement in transfer to unseen materials (3.7 %,
> CI 1.0–6.5 %, consistent across five folds and three seeds). That improvement
> does not depend on Damköhler (slope CI [−0.0033, +0.0062], r = 0.04) across a
> range spanning kinetically-controlled to near-equilibrium operation. The
> structure therefore acts as an inductive bias rather than as a kinetic
> identifier — which is not what H1 predicted.**

That is a more precise statement than either the legacy null or a naive positive,
and it is only available because the mechanism was pre-registered as the primary
estimand and could therefore fail on its own terms.

---

## The ladder on dataset v2 — L1, the learning curve, and L7 (run 2026-09-03)

**Design frozen in `PREREG_L1L2L7_v2.md`, committed before any arm trained.** Every
rung reuses the L6-v2 fold map (`results/l6_v2_folds.json`), so L1, L2, L6 and L7
report over the **same 240 held-out materials in the same folds**. Encoding
128 × 128 on load, as L5 and L6-v2. α = 0.02, calibrated for 240 clusters (empirical
size 2.8 %). Per-sample scores averaged over 3 seeds, then the paired cluster-robust
bootstrap. **Every comparison below is significant, so no MDE is owed**; the nulls
this design was built to power did not occur. Headline comparisons were recomputed
by a second, independent code path (different bootstrap seed) and agree to the
fourth decimal.

### L1-v2 — the arms: the MLP is now the best fixed-basis arm

Pooled out-of-fold, 240 materials, 64 POD modes/channel (`results/l1_v2_results.json`,
`results/l1_v2_verdict.json`):

| arm | nRMSE c | nRMSE q | nRMSE T | exit nRMSE | dt50 (h) | train c | × POD floor |
|---|---|---|---|---|---|---|---|
| ridge | 0.0516 | 0.1832 | 0.1238 | 0.0782 | 0.73 | 0.0505 | 185× |
| rf | 0.0388 | 0.0900 | 0.0888 | 0.0578 | 0.46 | 0.0157 | 139× |
| xgb | 0.0361 | 0.0871 | 0.0752 | 0.0554 | 0.37 | 0.0193 | 129× |
| **mlp** | **0.0306** ± 0.0010 | 0.0922 | 0.0768 | **0.0474** | **0.34** | 0.0244 | **109×** |

```
mlp 0.0306 vs xgb   0.0361 | diff -0.00548 CI [-0.00675, -0.00426]  SIGNIFICANT
mlp 0.0306 vs rf    0.0388 | diff -0.00820 CI [-0.01061, -0.00597]  SIGNIFICANT
mlp 0.0306 vs ridge 0.0516 | diff -0.02102 CI [-0.02257, -0.01959]  SIGNIFICANT
```

The MLP is ahead in every one of the five folds (0.0291–0.0321 against 0.0337–0.0371
for XGBoost). The manifest split (48 held-out materials) gives the same ordering
with every comparison significant (mlp 0.0326, xgb 0.0353, rf 0.0385, ridge 0.0519).
Ridge carries the B14 flag (train ≈ held-out) as a *linear* model should; it is
not best, so the flag does not bind.

**This reverses legacy L1**, where xgb, rf and mlp were indistinguishable and the
MLP had the worst point estimate. With four times the materials the MLP wins by
15 % over XGBoost, significantly. The POD floor also moved: 2.8 × 10⁻⁴ on v2
against 1.5 × 10⁻³ on legacy (a different encoding and 4.6× the training samples),
while the best arm improved only from ~0.049 to 0.031 — the ratio above the floor
*grew* from 33× to 109×. The basis is even less the constraint than before.

### The materials learning curve — NOT ELIMINATED at 192 materials

c-channel, POD p = 32 + per-mode gradient boosting (legacy A18's function class),
5 folds × 3 seeds at every size, subsets drawn from each fold's own 192 training
materials (`results/learning_curve_v2.json`, `results/learning_curve_v2_verdict.json`,
`figures/FigS1_learning_curve`):

| training materials | 12 | 24 | 48 | 96 | 192 |
|---|---|---|---|---|---|
| field nRMSE, basis **refit** on the subset | 0.0654 | 0.0531 | 0.0465 | 0.0402 | **0.0348** |
| field nRMSE, basis **fixed** on all 192 | 0.0657 | 0.0533 | 0.0466 | 0.0403 | 0.0348 |
| sd over seeds | 0.0015 | 0.0011 | 0.0003 | 0.0009 | 0.0001 |
| coefficient-map modes with R² > 0.5 | 1 | 1 | 2 | 2 | 3 |
| coefficient-map modes with R² > 0.2 | 2 | 3 | 8 | 11 | 13 |
| R² of `t_hi(z)` (the shock) | 0.79 | 0.80 | 0.83 | 0.85 | 0.87 |

Every consecutive step is a significant improvement, including the last:

```
 96 -> 192   diff +0.00534  CI [+0.00439, +0.00637]   SIGNIFICANT
 48 ->  96   diff +0.00633  CI [+0.00508, +0.00760]
 24 ->  48   diff +0.00655  CI [+0.00508, +0.00795]
 12 ->  24   diff +0.01238  CI [+0.01007, +0.01487]
```

**Verdict, in the pre-declared words: the materials axis is NOT ELIMINATED at the
largest size available (192).** Error falls as **n^−0.222** (CI 0.205–0.239) over
12–192 materials, 1.88× end to end; no extrapolation beyond twice the measured
range is claimed. At that exponent, halving the error costs about **23× more
materials**. L1's verdict for the paper is therefore: *more materials does help,
slowly and without saturating in the range we can afford, and every "wall"
measured elsewhere in the ladder is scoped to the material count it was measured
at.*

**What more materials buy, and what they do not.** The fixed-basis curve is
*identical* to the refit curve at every size (0.0657 vs 0.0654 … 0.0348 vs 0.0348):
a basis fitted on 12 materials reconstructs held-out fields as well as one fitted
on 192, once the regressor sees the same data. **None of the gain is in the basis;
all of it is in the parameter → coefficient map.** That is retraction A21's
reading, now measured across five sizes instead of inferred from one: modes with
R² > 0.2 grow 2 → 13 and are still climbing at 192.

**The conditions axis** (fractions 0.25–1.0 of each material's conditions at the
full 192 materials): 0.0414 → 0.0377 → 0.0358 → 0.0348, every step significant
including the last (diff +0.00091, CI [+0.00050, +0.00128]), **β = 0.122** (CI
0.108–0.137). By the pre-declared rule this axis is also *not* eliminated — legacy
A18 had called it eliminated on a 12-cluster test — but its exponent is half the
material axis's, and the last step is a 2.6 % gain for a third more conditions.
Both axes are open; materials are the one that matters.

> **Rule-5 note (defect B41).** `R²(t_lo)` — the lower-front arrival time the
> two-wave warp uses — is **degenerate on v2** and is not reported: the 5 %
> crossing happens within 2 % of the run time in 97 % of all (sample, z) cells
> (mean 0.003, sd 0.012 in normalised time, against 0.014 / 0.038 on legacy), so its
> variance is too small for an R² to mean anything. The shock arrival `t_hi` and the
> span are well-posed (R² 0.87 at 192) and are what a v2 warp would have to predict.

### L7-v2 — the classical control is beaten 3.7×, paired over 240 materials

Exit-curve nRMSE on the 128-point grid, all 3947 samples; the learned reference is
the L1-v2 best arm's **out-of-fold** prediction (`results/l7_v2_results.json`,
`results/l7_v2_verdict.json`). The Glueckauf `k_LDF` rebuilt from the parameter
vector matched the manifest record to 0.0 relative over every sample before any
curve was scored.

| method | exit nRMSE | dt50 (h) | cost/curve | trained? |
|---|---|---|---|---|
| POD floor | 0.0009 | — | — | — |
| **mlp (learned, out-of-fold)** | **0.0474** | **0.34** | ~ms | yes |
| klinkenberg | 0.1769 | 1.27 | 0.38 ms | no |
| equilibrium_shock | 0.3146 | 1.35 | 0.19 ms | no |
| constant_pattern | 0.3878 | 1.00 | 0.83 ms | no |

```
mlp 0.0474 vs klinkenberg       0.1769 | diff -0.1295 CI [-0.1384, -0.1203]  SIGNIFICANT
mlp 0.0474 vs equilibrium_shock 0.3146 | diff -0.2672 CI [-0.2725, -0.2616]  SIGNIFICANT
mlp 0.0474 vs constant_pattern  0.3878 | diff -0.3404 CI [-0.3579, -0.3215]  SIGNIFICANT
```

**Learning is justified on v2**: the best closed form is **3.73× worse** on the
exit curve and 3.7× worse on the 50 % breakthrough time (legacy: 3.2× and 2.2×).
The order of the closed forms is unchanged; the reasoning — every closed form
linearises the physics the two-wave structure violates — carries over unchanged.

Run times on this machine: L7 80 s, L1 (both designs, 72 cells) 65 min, learning
curve (135 cells) 55 min; L2 (420 cells) ≈ 10 h, dominated by `xgb md8/md10`.

---

## L2 on dataset v2 — every optimum is bracketed, and the optimum moves with the material count (run 2026-09-03/04)

**Design frozen in `PREREG_L1L2L7_v2.md`.** The sweep is identical to legacy
(28 configurations, both directions around the L1 setting), on the same 64-mode POD
per fold, the same L6-v2 folds, 3 seeds — 420 cells, 10.6 h. Per-sample held-out
values averaged over seeds and pooled over the five folds (each sample once); paired
cluster bootstrap by material at α = 0.02 (240 clusters); every saturation null with
its MDE. `results/l2_v2_results.json`, `results/l2_v2_verdict.json`.

| family | optimum | held-out nRMSE(c) | train | last step (largest vs second-largest) | MDE at 80 % |
|---|---|---|---|---|---|
| `mlp_width` (depth 3) | **w64** (U-shaped) | 0.0298 | 0.0260 | w1024 vs w512: −0.0004, CI [−0.0009, +0.0001] → **saturated** | 5 % |
| `mlp_depth` (width 256) | **d8** (U-shaped) | **0.0241** | 0.0175 | d10 vs d8: +0.0006, CI [+0.0001, +0.0011] → **saturated** (past the optimum) | 5 % |
| `xgb_depth` | **md6** (U-shaped) | 0.0352 | 0.0133 | md10 vs md8: +0.0018, CI [+0.0014, +0.0022] → **saturated** (past the optimum; train 0.0009 vs held-out 0.0373 at md10, a 44× gap) | 2 % |
| `rf_leaf` | leaf1 (monotone) | 0.0381 | 0.0094 | leaf1 vs leaf2: −0.0007, CI [−0.0009, −0.0006] → **still improving**, 1.9 % | — |

**The pre-declared rule, applied literally:** three families have saturated with
interior optima; the random-forest family is still improving at its last step, so by
the letter of the rule L2 is *not eliminated* and the RF sweep "should be extended".
It cannot be: `min_samples_leaf = 1` with unlimited depth is a fully grown forest,
the ceiling of that family's capacity knob. Its last step is significant because 240
clusters resolve 1.9 %, and the family sits **37 % behind the best MLP**
(0.0381 vs 0.0241, CI [+0.0119, +0.0162]). The honest verdict is therefore:
**capacity as an unbounded lever is eliminated — every optimum that can be bracketed
is bracketed — but the optimum is not where the legacy sweep left it.**

**What moved, and by how much.** These five comparisons are **post-hoc and
descriptive** — the pre-registered rule is the per-family saturation test above, and
"how far the optimum moved" is a description of the sweep, not a test it was designed
for. They are labelled as such in the code and in the verdict file. Paired,
cluster-robust, α = 0.02, from `results/l2_v2_verdict.json` → `cross`:

```
mlp_depth/d8 0.0241 vs the L1 setting mlp_depth/d3 (256,256,256) 0.0306
                                   | diff -0.006507 CI [-0.007255, -0.005730]  +21.3 % [+18.7, +23.7]
mlp_width/w64 0.0298 vs w256 (the L1 width)  0.0306
                                   | diff -0.000851 CI [-0.001482, -0.000250]   +2.8 % [ +0.8,  +4.8]
mlp_depth/d8 vs mlp_width/w64      0.0298 | diff -0.005656 CI [-0.006394, -0.004881]  +19.0 % [+16.4, +21.5]
mlp_depth/d8 vs xgb_depth/md6      0.0352 | diff -0.011080 CI [-0.012440, -0.009764]  +31.5 % [+27.8, +35.4]
mlp_depth/d8 vs rf_leaf/leaf1      0.0381 | diff -0.013970 CI [-0.016190, -0.011880]  +36.7 % [+31.2, +42.5]
```

> **These four numbers had no script behind them until 2026-09-05 — defect B43**,
> B39's class, in the rung whose retraction (A26) rests on the first of them. They are
> now computed by `analyze_l2_v2.cross_comparisons` and stored in the verdict file;
> every quoted digit reproduced, so A26 stands, and the rest of the verdict file
> (MDEs included) is byte-identical.

**One identity, asserted rather than assumed (B44).** `mlp_width/w256`,
`mlp_depth/d3` and L1-v2's `mlp` arm are the *same* estimator — `(256, 256, 256)`
under a standardised target transform — trained by **two different runners** on the
same folds, the same per-fold POD and the same three seeds. Their per-sample held-out
scores agree to **0.00e+00**, means 0.030601 / 0.030601 / 0.030601. That is the
strongest available evidence that L1-v2, L2-v2, L6-v2 and L7-v2 really are reported
over one shared design, and the analyzer now raises if it ever stops being true.

On legacy (48 training materials) the best configuration anywhere improved on the
L1 setting by **~1 %** and the depth optimum was 6 layers; on v2 (192 training
materials per fold) the depth optimum is **8 layers and the gain is 21 %**. The
legacy sentence *"capacity is irrelevant"* was scoped to 48 materials without saying
so — retraction **A26**, the A18/A21 class again: a saturation measured at one sample
size stated as intrinsic. What survives unchanged: the shape of the evidence (every
family U-shaped or at its ceiling; XGBoost's training error falls 43× while its
held-out error passes through a minimum and rises), and the wall — the best
fixed-basis surrogate on v2, an 8-layer MLP, still sits **86× above the POD floor**.

Two consequences for the rest of the ladder. The L1-v2 arms table and the L7-v2
reference used the L1 setting (0.0306); a deeper MLP would only widen L7's margin
(the best closed form is already 3.7× worse). And the material learning curve's
slope (β = 0.22 for POD + gradient boosting) was measured at a fixed capacity; the
fact that the *optimal* capacity itself grows with the material count is the
standard signature of a data-limited, not a representation-limited, regime — the
same diagnosis the fixed-basis learning curve gave.

## The solver against a real MOF-303 bed — Lassitter et al. (2024) Fig. 10 (run 2026-09-03)

**Design frozen in `PREREG_LASSITTER.md`, committed before the run.** This is not a
rung and tests no surrogate: it asks whether the physics model that generated every
dataset here reproduces a published MOF-303 packed-bed breakthrough with **no
parameter fitted to the curve**. The experiment is the only MOF-303 breakthrough
whose conditions are fully on record (their SI Table S8): a **6.35 mm** bed in a
38.1 mm tube, 670.8 cm³/min of ambient air at **32.8 % RH**, 298.15 K, 3.11 g,
bulk density 429.6 kg/m³, porosity 0.4 (their estimate). Digitised in
`refs/Lassitter2024_fig10_digitised.csv`; results in
`results/lassitter_comparison.json`; figure `figures/Fig7_anchor`.

Inputs: the cited MOF-303 isotherm (`get_mof303_physics`, A4), the SI bed, and three
declared bands for what the source does not give — k_LDF ∈ {0.011, 0.05, 0.20} s⁻¹
from their CSFR Table S2, pellet size ∈ {1, 3, 5} mm (dispersion only), and thermal
coupling (isothermal, or the dataset's h_w = 10 with C_ps ∈ {900, 1000, 2400}).
Primary: k = 0.20, d_p = 3 mm, isothermal. Grid converged: max change in c/c_in
0.0005 (N_z 250 → 500) and 0.0003 (500 → 1000).

| curve | first leak t05 (min) | t50 | t95 | Henry plateau, 150–250 min (fraction of inlet) | nRMSE vs the 37 effluent points |
|---|---|---|---|---|---|
| **experiment** (digitised) | **86** | **287** | **354** | **0.267** | — |
| authors' COMSOL, 2-D, fitted CSFR kinetics | 128 | 300 | ~340 | 0.277 | 0.069 |
| **this solver, primary, no fitting** | 1.7 | **303** | 431 | **0.336** | 0.128 |
| band, isothermal members (k, d_p) | 0.4–2.4 | 295–312 | 390–462 | 0.30–0.36 | 0.108–0.144 |
| band, non-isothermal members (h_w = 10, any C_ps) | 0.3–1.6 | 179–223 | — | 0.48–0.52 | 0.235–0.256 |

**Under the pre-declared reading the primary run reproduces the experiment**: the
intermediate plateau is present, the 50 % arrival is **5.6 %** off (303 vs 287 min),
and the plateau level is within 1.26× (0.336 vs 0.267). The two-wave breakthrough of
§6c — a Henry-branch leak to a plateau near 0.3 of the feed, then a cooperative
shock — is what a real MOF-303 bed does, and the cited isotherm predicts it with
nothing tuned. The kinetic rate barely matters (Da = k·t_st is 160–3000: the bed is
near equilibrium, as in the legacy dataset); the thermal band is decisive in the
other direction — coupling the bed to the dataset's wall coefficient heats it 9 K
and breaks through 80–110 min early, so the thin bed is effectively isothermal, as
the authors also assumed.

**Two discrepancies, both attributable, both reported.**

1. **The first wave arrives ~80 min too early in the model** (t05 = 0.4–2.4 min for
   every band member against 86 min measured; the authors' fitted model gives 128).
   Nothing in the declared band moves it, and the post-hoc dispersion change below
   does not either. What sets it is the isotherm's **low-RH branch**: the Henry
   fraction of the cited Do–Do fit (0.06) was fitted to the step position and the
   capacity only (A4), and this is the first dynamic measurement that constrains
   it. Our fit holds too little water below the step. It is a measured limitation of
   the MOF-303 parameterisation, not of the solver, and the paper must say so.
2. **The shock is too dispersed** (t95 − t50 = 128 min against 67 measured). The
   cause is a closure, not the physics: the Ruthven correlation used for every
   dataset, D_L = 0.7 D_m + 0.5 d_p u, gives a Péclet number **vL/D_L ≈ 1** on a bed
   one or two pellets deep, where a packed-bed dispersion correlation does not
   apply. The authors use the Bruggeman closure D_e = ε^1.5 D_m (Pe ≈ 11).

> **Post-hoc sensitivity — labelled as such, chosen after seeing the result, not a
> fit and not the result** (`compare_lassitter_posthoc.py`,
> `results/lassitter_comparison_posthoc.json`, `figures/Fig7b_anchor_posthoc`).
> With the authors' Bruggeman closure and everything else unchanged: t50 313 min,
> t95 **329** min (experiment 354), plateau 0.234 (experiment 0.267), nRMSE
> **0.083** against the fitted COMSOL's 0.069. The shock width is recovered; the
> first-wave arrival is not (3.9 min), which is what isolates discrepancy 1 to the
> isotherm. On our 10 cm datasets the Ruthven closure is the appropriate one — the
> column is 50 pellets deep and Pe is in the hundreds — so this changes nothing
> upstream; it scopes the closure.

**What this establishes, and what it does not.** Solver-vs-experiment at one
condition, on a bed with an aspect ratio of 0.17 where a 1-D plug-flow model is at
the edge of its validity, with one isotherm parameter now known to be off in the
low-RH branch. Every surrogate number in this paper is surrogate-vs-solver, and the
error budget must separate the two in exactly those words.

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

**Verdict: H1 is not supported at this power.** Structural decomposition does not
produce a statistically significant improvement on novel materials in this system,
and the point estimate goes in the *wrong direction*.

> ⚠️ **This null excludes far less than first reported — retraction A22.** The
> design's power was recomputed with the material-level clustering preserved
> (`results/l6_power_corrected.json`). At 12 held-out materials and α = 0.005:
>
> | true improvement | power |
> |---|---|
> | 20 % | **7 %** |
> | 30 % | 16 % |
> | 50 % | 45 % |
> | 70 % | 77 % |
>
> The minimum detectable effect at 80 % power is roughly **70 %**. The difference
> between the arms is strongly clustered by material — between-material sd
> **0.0391, 69 % of the base error**, against a within-material sd of 0.0290 — and
> that is what makes the test hard.
>
> So this null is real but weak: it excludes only very large structural benefits.
> It is **not** evidence that a moderate one is absent, and it must never be quoted
> without its MDE. An earlier claim that this design had 96 % power at a 20 %
> effect is withdrawn; that figure came from a simulation that resampled residuals
> i.i.d. and destroyed the clustering.
>
> **Consequences.** (i) The v2 re-test at 48 held-out materials is *necessary*, not
> confirmatory. (ii) L6 should be estimated as an effect **as a function of
> Damköhler** rather than as one pooled mean difference — a regression uses the
> between-material structure instead of paying for it as noise, and the legacy
> dataset could not do this at all because **98.9 % of its samples** sat at Da > 60.

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

- **`validate.py`** — 24 gates, all passing. No number enters the manuscript from
  a failing category.
- **`RETRACTIONS.md`** — 26 Part-A, 64 Part-B caught before
  contamination. **31 of the 90 entries carry the words "our own error"** (counted by `ledger_counts.py`, never typed), and
  several more are self-attributed in other words (A22, A23, A25, B39, B41, B42,
  B43, B45-B53) — in the
  analysis, the validation gates, the power simulations, or the frozen protocol
  itself — recorded on the same terms as errors in the code. One Part-A
  retraction (**A17**) withdraws a claim the protocol had called its most
  important result; two (**A22**, **A25**) withdraw power statements, one in each
  direction.
- Figures are computed from data or loaded checkpoints; the harness forbids a
  plotting script from synthesising a series it labels as a model prediction.
- Comparisons use the **calibrated** α = 0.005, chosen because the percentile
  cluster bootstrap was measured to over-reject at these cluster counts.

---

## Open items before submission

1. Every MOF-303 parameter is a literature-range placeholder. Until replaced with
   cited values and the isotherm refitted to a published water isotherm, **no
   result may be described as "MOF-303"**.
2. ~~No experimental validation exists.~~ One solver-vs-experiment comparison now exists
   (Lassitter 2024 Fig. 10, pre-registered, no fitting); the error budget must still
   separate solver-vs-experiment from surrogate-vs-solver, in those words.
3. No COF case exists; the title claims one.
4. ~~`kaggle_run/` is a stale duplicate carrying the original defects.~~ **Closed 2026-09-25:** removed with `deploy_kaggle.py`, `build_kaggle_pkg.py` and the package zip; in git history at `81295d4`.
5. The speed claim needs an honest reference — our own solver runs one condition
   in 4.2 s (MOF-303 config, N_z = 2000).
6. **Closed 2026-09-25:** `sindy_discovery.py` removed (git `81295d4`; evidence kept in A7); `identify_kinetics.py` replaced it. Original item: SINDy needs something to discover: its library currently contains `q*`,
   computed from the law that generated the data.
