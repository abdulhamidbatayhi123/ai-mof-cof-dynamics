# Citation verification ledger

Every reference that may enter the manuscript, and its verification state. A
hallucinated citation in a paper whose selling point is rigour would be the worst
possible failure, so nothing is cited until it appears here as `VERIFIED`.

**States**
- `VERIFIED` — retrieved directly; title, authors, venue and the claim we make
  about it all confirmed against the source.
- `PARTIAL` — record confirmed to exist, but the specific claim we make about it
  has not been checked against the full text.
- `BLOCKED` — could not retrieve (paywall, bot check). Needs a human with
  institutional access. **May not be cited in this state.**
- `UNRESOLVED` — searched and not found. Treat as non-existent until proven
  otherwise. **May not be cited.**

Started 2026-08-30. Source pool: the 10-lens literature review in
`audit_2026-08-30/literature_review_raw.json` (~268 candidate references).

---

## Load-bearing — the argument depends on these

| ref | state | notes |
|---|---|---|
| **Lanthaler, Molinaro, Hadorn & Mishra**, *Nonlinear reconstruction for operator learning of PDEs with discontinuities*, **ICLR 2023** (arXiv:2210.01074; OpenReview `CrfhZAsJDsZ`) | ✅ **VERIFIED** | Confirmed verbatim: methods with a **linear reconstruction step** (DeepONet, PCA-Net) *"fail to efficiently approximate the solution operator"* of hyperbolic/advection-dominated PDEs, proved as lower approximation bounds; **FNO and shift-DeepONet** use non-linear reconstruction and *"overcome these fundamental lower bounds"*. **This is why running FNO is not optional** — L5 currently tests only the family the theory condemns. Cite in the L5 framing and in the Introduction. |
| **Heinlein & Taraz**, *The Error of Deep Operator Networks Is the Sum of Its Parts: Branch-Trunk and Mode Error Decompositions*, arXiv:**2602.21910**, v1 25 Feb 2026, v2 24 Aug 2026 | ✅ **VERIFIED** | **Partial priority on L5's mechanism — must be cited prominently.** Abstract confirms three of our findings independently: (i) *"the approximation error is dominated by the branch network when the internal dimension is sufficiently large"*; (ii) *"the learned trunk basis can often be replaced by classical basis functions without a significant impact"* (they substitute the left singular vectors of the training solution matrix — our `l5_bottleneck.py` move); (iii) *"a spectral bias in the branch network... coefficients of dominant, low-frequency modes learned more effectively"*. **Their scope, from the abstract: KdV and Burgers, and no mention of out-of-distribution or held-out-system evaluation.** See the differentiation note below. |
| **Lee, Lee & Kim**, *Scale-up prediction of breakthrough curves via shape–timescale decomposition in a hybrid deep learning framework*, SSRN preprint **10.2139/ssrn.6874257**, posted **3 Jun 2026**, 37 pp., 23 refs. Seung-Chan Lee & Song-Bae Kim (Seoul National University), Chang-Gu Lee (Ajou University) | ✅ **VERIFIED** (abstract read from the SSRN record 2026-08-30; **full text not yet read**) | **CLOSE PRIOR ART ON THE WARP — must be cited, and it changes how that section is framed.** Abstract: *"a hybrid deep learning framework based on explicit decomposition of BTCs into normalized shape and characteristic timescale components. The normalized BTC shape is learned using a bidirectional LSTM in a dimensionless time domain, while the characteristic breakthrough time is predicted using a multilayer perceptron. The full BTC is reconstructed through a scaling-based [recomposition]"*, validated on lab-scale datasets for scale-up. See the differentiation note below. |

### How to differentiate from Heinlein & Taraz — write this into the paper

Do **not** present branch-dominance or mode-wise spectral bias as new. Claim
instead, explicitly and up front:

> Heinlein & Taraz (2026) establish, for DeepONets on KdV and Burgers, that error
> is branch-dominated at large internal dimension, that the learned trunk is
> replaceable by a classical basis, and that the branch exhibits mode-wise
> spectral bias. We reproduce that signature independently in a different setting
> and extend it in four ways: **(i)** the inputs are a finite-dimensional
> parameter vector describing a *material*, not a discretised input function;
> **(ii)** evaluation is transfer to **held-out materials** under a
> cluster-robust, calibrated test, not in-distribution error; **(iii)** we show
> the plateau is invariant to basis size while the POD floor beneath it falls
> 28.7×, and calibrate the resulting error against an oracle to an equivalent
> mode count; **(iv)** we trace it to a measurable physical cause — the kinetic
> coefficient is not recoverable from observable descriptors (R² = −0.61) — and
> show the plateau survives a change of coordinates that collapses the n-width.

Two independent groups, different input types, different PDE families, same wall
is a **stronger** scientific statement than either result alone. Frame it that
way.

### Lee, Lee & Kim (2026) — full text read 2026-08-30, and the position is strong

SSRN preprint, https://ssrn.com/abstract=6874257, 37 pp. (a local copy was read; it is
not redistributed with this repository). This is the closest prior art the review
found and it lands on the warp. **"Decompose a breakthrough curve into a normalised
shape and a characteristic timescale, learn each, recompose" is published and must
not be claimed as new.** An adsorption referee will know it.

**Exactly what they do** (their Eqs. 1–5):

    theta      = t / EBCT                        dimensionless time
    theta*     = theta / theta_end               normalised to the run's own duration
    y_shape    = f_BiLSTM(theta*, [L/D, Re, C0]) the shape, on theta* in [0,1]
    theta_0.9  = f_MLP([L/D, Re, C0, EBCT])      ONE SCALAR: dimensionless time at C/C0 = 0.9
    alpha      = theta_0.9 / theta*_0.9
    theta      = alpha * theta*                  a SINGLE MULTIPLICATIVE DILATION

Their system is **Cu(II) onto functionalised cellulose adsorbents**, lab-to-pilot
scale-up, benchmarked against Thomas / Yoon–Nelson / Bohart–Adams / Clark — all
**single-sigmoid** BTC forms. They explicitly enforce *"monotonic increases in
normalized concentration and stable saturation"*. There is no isotherm-shape
discussion anywhere: no inflection, no Type IV/V, no multi-wave breakthrough.
Result: R² = 0.975 on unseen pilot-scale, 3–5× better than end-to-end baselines.

**The two differences that decide the framing:**

| | Lee, Lee & Kim (2026) | this work |
|---|---|---|
| object predicted | the **exit curve**, 1-D in t — no spatial dimension exists in their problem | the full **field** c(z,t) |
| the time map | **one scalar dilation** `alpha`, uniform over the whole curve | **two z-dependent trajectories** `t_lo(z)`, `t_hi(z)` — an affine map per column position |
| transfer axis | lab → pilot **scale-up** (geometry, flow, concentration) | held-out **materials**, cluster-robust |
| isotherm | not considered; single-step BTCs assumed and enforced | **Type V**, two-wave, separation varying **40×** |
| what is measured | predictive accuracy | the **n-width in each frame**, and the basis/coefficient error split |

**And we have already measured that their map cannot work here.** A single scalar
dilation is *weaker* than the single-front co-moving frame we tested and refuted:
ours was a z-dependent additive shift, theirs is a z-independent multiplicative
scale. `comoving.py` measured that even the stronger version makes the
representation worse — modes for 99.9 % of training variance go **31 → 102** — and
loses to the unwarped frame even when handed the exact front trajectory
(0.0534 vs 0.0510). Our refutation therefore applies *a fortiori*.

The mechanism is the point: **a pure dilation cannot change a curve's shape.** When
the separation between the fast Henry wave and the cooperative shock varies 40×
across the dataset, no single `alpha` can align both. That is exactly the failure
mode we measured before proposing the two-trajectory alternative.

**The sentence to write:**

> Shape–timescale decomposition has been proposed for breakthrough-curve scale-up,
> using a single characteristic time and a uniform rescaling of the time axis
> (Lee, Lee & Kim, 2026), and is effective for the single-step breakthrough of
> heavy-metal adsorption. We show that for an **inflected Type V isotherm** — where
> the breakthrough carries a fast Henry wave and a slow cooperative shock whose
> separation spans 40× across our parameter space — a one-parameter time map is
> structurally insufficient: it *increases* the Kolmogorov n-width from 31 to 102
> modes and loses to the unwarped frame even given an oracle trajectory. A
> **two-trajectory** warp, which removes the arrival time and the transition width
> independently and at every column position, instead collapses the n-width to
> 13–17 modes and cuts the oracle reconstruction error 2.27×.

That is a sharper claim than "we propose a decomposition", and it exists **only
because** their paper does. Cite them prominently and generously.

### ⚠ C2 — THE TWO-WAVE WARP IS NOT NOVEL. Verified 2026-08-30.

The differentiation table above was written against **Lee et al. alone** and is
correct as far as it goes. It is also **not the binding prior art.** Independent
verification found that multi-front alignment is the *founding worked example* of
shifted POD:

> Reiss, Schulze, Sesterhenn & **Mehrmann**, *The shifted proper orthogonal
> decomposition: a mode decomposition for multiple transport phenomena*,
> **SIAM J. Sci. Comput. 40(3), A1322–A1344 (2018)**, DOI 10.1137/17M1140571.

Their opening example is a pressure pulse splitting into **two** waves (c⁺ = +1,
c⁻ = −1), reconstructed with **two modes — one per co-moving frame — against 80+
POD modes**. The general formulation is written for arbitrary Nₛ independent
transports. Multi-front variants are further established by Nair & Balajewicz
(*IJNME* 117:1234–1262, 2019), Mendible et al. (*TCFD* 2020), Zorawski et al.
(arXiv:2407.17539, 2024), Krah et al. (*SISC* 47:A633–A656, 2025) and Zucatti &
Zahr (arXiv:2503.17463).

**Every sentence implying that aligning two waves is new must be deleted.**

*One real distinction survives, and it is worth stating precisely rather than
overclaiming.* sPOD is an **additive** decomposition — a sum of co-moving fields,
one per wave, each with its own frame. Our map is **compositional**: a single
reparameterisation `σ = (t − t_lo(z))/(t_hi(z) − t_lo(z))` that normalises the
*interval between* two fronts rather than summing two transported fields. That
places it in the registration/calibration family (Taddei, *SISC* 42:A997, 2020 —
**note an erratum exists, DOI 10.1137/24M1639579, unread**) rather than the sPOD
family. But registration ROM is itself established, so this distinction narrows the
claim; it does not restore novelty.

**What we may actually claim** — the measurement, not the map:

1. The **n-width measured in each frame** for a Type V adsorption system: original
   31 modes → single-front warp **102** → two-wave warp **13–17**, for 99.9 % of
   training variance. Nobody has reported this for inflected-isotherm breakthrough.
2. The **refutation of single-alignment under an oracle control** — it loses to the
   unwarped frame *even given the exact front trajectory* (0.0534 vs 0.0510), with
   the mechanism measured first (40× separation spread), not invoked afterwards.
3. The **localisation of the obstruction**: oracle 0.02203 vs predicted 0.04770 vs
   fixed 0.05005, so the entire gain is consumed by front-location error, with a
   powered CI. That converts a representation question into a 1-D regression target.
4. **Application** to MOF/COF water-adsorption breakthrough and to transfer across
   held-out *materials*.

Write the section as *"we apply an established transformation-based reduction to a
system where its single-front form provably fails, and measure what it buys and
what limits it"* — never as *"we propose a two-wave warp."*

*One methodological note, for our own use rather than criticism of theirs:*
their `theta* = theta/theta_end` normalises by the **observation window**, so the
representation depends on when the experiment was stopped. Our normalisation uses
`t_final` from the stoichiometric time with a recorded adaptive horizon, which is a
property of the physics rather than of the operator. Worth a sentence in Methods,
since a referee comparing the two frames will ask.

---

## Queue — not yet verified

Priority order. Nothing below may be cited yet.

1. Abueidda, Pantidis & Mobasher, DeepOKAN, *CMAME* 436:117699 (retraction **A12** rests on this)
2. Shukla, Toscano, Wang, Zou & Karniadakis, *CMAME* 2024 (the KAN anchor, cited in the protocol)
3. McGreivy & Hakim, *Nature Machine Intelligence* 2024 (weak baselines in ML-for-PDE)
4. Li et al. 2025, *RSC Adv* — MOF-303 breakthrough, **the experimental anchor**; open access, geometry matches ours
5. Lassitter et al., *Chem. Eng. Sci.* 285:119430 (2024) — MOF-303 CSFR kinetics, LDF failure at the step
6. Bozbiyik et al. 2017 — Al-fumarate stepped breakthrough
7. ~~Reiss, Schulze, Sesterhenn & Noack~~ → **Reiss, Schulze, Sesterhenn & MEHRMANN** — see C1
8. Krah et al., arXiv:2403.04313 — robust multi-transport sPOD
9. Zorawski et al. 2024 — neural sPOD
10. Taddei, *SISC* 2020 (arXiv:1906.11008) — registration ROM
11. Bartolucci et al., ReNO, NeurIPS 2023 — representation equivalence
12. Rohrer et al., *Perspectives on Psychological Science* 2021 — Loss-of-Confidence Project
13. van Genuchten & Alves (1982) — the L0 analytic reference (defect **B10**)
14. Do & Do — the Type V water isotherm form
15. Glueckauf — the LDF coefficient used in dataset design v2
16. … remainder of the ~268 candidates in `audit_2026-08-30/literature_review_raw.json`

---

## Venue decision (2026-08-31)

**Primary: Computer Methods in Applied Mechanics and Engineering (CMAME), Elsevier.**

Chosen on three grounds, in this order:

1. **Cost.** Subscription journal — publishing costs **nothing** if the optional
   open-access upgrade is declined. The accepted manuscript may be posted to arXiv
   (green OA), so the work stays freely readable. The author is a student without
   APC funding, which rules out npj Computational Materials (~$3.5k),
   Communications Engineering (~$3.5k) and MLST (~$2k) unless an institutional
   read-and-publish agreement exists. **Action: confirm with the library.**
2. **Topical fit — the strongest in the candidate set.** Every paper L3 argues with
   is in CMAME: Shukla et al. **431**:117290, Abueidda et al. (DeepOKAN)
   **436**:117699, Wang et al. (KINN) **433**:117518, Kiyani et al. **446**:118308,
   Rigas et al. **452**:118761. A matched-parameter KAN result is a direct
   contribution to an argument this journal is actively curating. CMAME also
   publishes n-width analysis, registration ROM and operator-learning limits.
3. **Scope.** Methods contribution with a domain application is CMAME's centre of
   gravity, and it is what the evidence actually supports.

**Sequence:** arXiv preprint first (free, establishes priority) → CMAME.
**Fallbacks:** Separation and Purification Technology (Elsevier, IF ~8.6, also free
to publish, domain framing) → TMLR (free, fully OA; its stated criteria forbid
rejection for lack of novelty and require only that claims match evidence, which
this paper satisfies unusually well).

**Not pursued:** Nature Computational Science and Nature Machine Intelligence are
out of reach without experimental data — unchanged since the audit.

**Scope: ONE paper.** The falsification ladder is the story. With multi-front
alignment established as prior art (B36), the warp is a section, not a paper.

---

## Experimental anchor — status 2026-09-02

**Li, Li, Yin, Shan, Tao & Wang, *RSC Adv.* 15:8867 (2025), PMC11931415, CC BY 3.0 —
read in full from PMC.** The audit called this "the experimental anchor, with
matching geometry", and the geometry does match: inner diameter **0.6 cm**, bed
height **≈ 10 cm**, **298 K**, nitrogen carrier at **300 sccm**, MOF-303 formed
into **2–5 mm cylindrical granules**. But three things the audit assumed are
**not in the paper**, and they decide what the curve can be used for:

| needed for a quantitative comparison | reported? |
|---|---|
| inlet water-vapour concentration / RH of the feed | **no** — not stated anywhere in the dynamic section |
| mass of adsorbent in the column (or bulk density) | **no** — only the bed height |
| bed void fraction, pellet density | **no** |
| outlet signal definition | on-line mass spectrometer; m/z and calibration not given |
| the plotted quantity in Fig. 11 | **"breakthrough adsorption capacity" in mg g⁻¹ vs time** — a cumulative uptake, not c/c_in; its formula is not given |

Numbers the text does give (Table 3): MOF-303 granules (A0) breakthrough capacity
**248.6 mg g⁻¹**, breakthrough time **134.3 min**; composites A1–A4 277–301 mg g⁻¹;
13X 151.2 mg g⁻¹ / 80.8 min; silica gel 207.0 mg g⁻¹ / 110.0 min. Static uptake:
powder 445 mg g⁻¹, granules 416 mg g⁻¹ at 298 K.

**Consequence.** Without the feed concentration and the bed mass the
stoichiometric time is undetermined, so a digitised Fig. 11 cannot fix the solver's
absolute time axis; it can only be compared in **shape** (single-step vs stepped,
and the ratio of the early leak to the main front) and in **breakthrough time
relative to the capacity-derived stoichiometric estimate**. The honest use is a
qualitative shape anchor with a stated one-parameter fit (feed concentration
inferred from the reported capacity and the cited isotherm), never a
solver-vs-experiment error budget. Whether this changes the venue tier as the
audit hoped is doubtful; it must be written as a limitation, not a validation.

Figure image (CC BY 3.0): `https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9f9d/11931415/47ad8d5d2b89/d4ra08282f-f11.jpg`.
Not yet downloaded or digitised.

**Alternatives checked:** Lassitter et al. 2024 (CSFR kinetics, PDF at
yaghi.berkeley.edu) — see the note that follows once read; Bozbiyik et al. 2017
(Al-fumarate, three feed humidities, single-step → stepped transition; Springer,
access not yet confirmed).

**Lassitter, Hanikel, Coyle, … Yaghi & Glover, *Chem. Eng. Sci.* 285:119430 (2024) —
main text read in full 2026-09-02 from the author-hosted PDF
(`yaghi.berkeley.edu/pdfPublications/24MassTransfer.pdf`, text extracted with PyMuPDF).**

The paper does contain a MOF-303 packed-bed breakthrough curve, **Fig. 10**
("Experimental Breakthrough Curve (points) and COMSOL model (line)"): *"MOF-303
was pressed into pellets, without a binder, and ambient air was pulled through
the MOF-303 adsorption bed … This breakthrough test was conducted on 3.11 g of
MOF-303 in a tube that was 1.5 in. in diameter with additional details in the
SI."* The flow rate, inlet humidity, temperature, pellet size and bed length are
**in the supplementary information, not the main text**; the SI is on
ScienceDirect (10.1016/j.ces.2023.119430) and its accessibility is recorded
below. The physics sentence we need is verbatim: *"the unique shape of the
breakthrough curve shown in Fig. 10 occurs not because of mass transfer effects,
but rather because of the shape of the adsorption isotherm … transitions from
favorable to unfavorable adsorption that results in changes in the breakthrough
curve from a more shock-like curve to a more dispersed curve (LeVan and Carta,
2008)"*, with Bozbiyik et al. 2017 cited for the same behaviour on aluminium
fumarate. **That is direct experimental support for §6c's two-wave
mechanism**, and it should be cited for exactly that.

Also confirmed: the LDF-vs-micropore comparison is on the CSFR data (LDF
"fits the data reasonably well until the humidity approaches 20 %" for MOF-333,
with deviations at high frequency near the step); **no solid heat capacity
value** is given (Cs appears only as a symbol in the energy balance, Eq. 16), so
the C_ps gap stands; the density/porosity numbers in the text (183.2 kg m⁻³,
0.584, skeletal 440 kg m⁻³) refer to the **polymer composite coating**, not to
MOF-303 pellets, and must not be used as pellet values.

**Anchor status, honestly:** two published MOF-303 breakthrough curves exist
(Li 2025 Fig. 11; Lassitter 2024 Fig. 10). Neither reports, in its main text,
the full set {feed humidity, bed mass or bulk density, void fraction} a
quantitative solver-vs-experiment comparison needs. Lassitter's SI may; until
it is read, the experimental section of the paper is a **shape comparison**
with the stated missing parameters, not an error budget.

**Lassitter 2024 — supplementary information READ 2026-09-02** (Elsevier SI,
`1-s2.0-S0009250923009867-mmc1.docx`, text extracted from the docx archive; the
tables are embedded EMF images, converted and read). **This changes the anchor
decision: the packed-bed test is fully specified.**

Section S4: pellets pressed from NovoMOF MOF-303 at 2 US tons for ~30 s (BET
839 → 814 m² g⁻¹, ~3 % loss); degassed 15 h at 120 °C; loaded under nitrogen;
*"ambient air was drawn across the bed at 670.8 cm³/min"*; inlet and effluent RH by
Honeywell HIH-4021-001 sensors. Table S8 (packed-bed COMSOL parameters), verbatim:

| symbol | value | description |
|---|---|---|
| R | 0.01905 m | radius of tube |
| **L** | **0.00635 m** | **height of bed** |
| Q | 1.118 × 10⁻⁵ m³ s⁻¹ | volumetric flow rate of air, inlet |
| v | 0.0098062 m s⁻¹ | inlet velocity of air |
| A_c | 0.0011401 m² | cross-sectional area of bed |
| D_H2O,air | 2.19 × 10⁻⁵ m² s⁻¹ | diffusivity of water in air |
| T | 298.15 K | temperature |
| **RH** | **32.8 %** | relative humidity |
| C₀ | 0.42212 mol m⁻³ | inlet water concentration |
| V_b | 7.2396 × 10⁻⁶ m³ | volume of bed |
| M_b | 0.00311 kg | mass of bed |
| **ρ_b** | **429.58 kg m⁻³** | MOF bulk density |
| **ε_b** | **0.4** | porosity of bed (**estimated**) |
| P_sat | 3190.1 Pa | saturation pressure of water |

Model: 2-D axisymmetric porous domain, Brinkman flow, **isothermal** ("trace"
adsorbate), LDF with k_LDF from CSFR (micropore rate; **no macropore resistance
and no pellet size enters their model**), Bruggeman tortuosity, Eq. S1–S6.

Table S2 (CSFR, MOF-303 powder, 25 °C), verbatim — the kinetic object as a
function of humidity, **with its minimum at the isotherm step**:

| RH % | η = D/r_s² (s⁻¹) | k_LDF (s⁻¹) |
|---|---|---|
| 5 | 1.09e-2 | 1.46e-1 |
| 7 | 3.45e-3 | 5.22e-2 |
| 10 | 8.16e-4 | 1.34e-2 |
| **12** | **4.24e-4** | **1.14e-2** |
| 15 | 3.23e-3 | 3.67e-2 |
| 26 | 1.42e-2 | 2.44e-1 |
| 40 | 1.44e-2 | 1.83e-1 |
| 60 | 1.14e-2 | 1.43e-1 |
| 80 | 1.82e-2 | 2.20e-1 |

**What this buys, stated carefully.** Every input a 1-D solver-vs-experiment
comparison needs is now on record for Fig. 10: L, v, T, RH, ρ_b, ε_b, M_b and the
rate. Three caveats must be written next to any such comparison: (i) the bed is
**6.35 mm tall in a 38.1 mm tube** — an aspect ratio of 0.17, far from the
100 mm column of our dataset; axial dispersion, entrance effects and maldistribution
are not small, and their own model is 2-D axisymmetric for that reason; (ii) the
feed at 32.8 % RH sits **above** MOF-303's step (13–15 % RH), so the whole run is on
the cooperative branch — the two-wave shape the main text attributes to the
isotherm is exactly §6c's mechanism and is what to compare; (iii) ε_b is an
estimate and the pellet size is not given, so the dispersion term is a
sensitivity band, and C_ps remains uncited (their model is isothermal, so they
did not need it). Fig. 10 is in the main-text PDF (points + COMSOL line) and is
the curve to digitise; Li 2025 Fig. 11 is demoted to a qualitative
shape comparison.

**Fig. 10 digitised 2026-09-02** — `digitise_lassitter.py` → `refs/Lassitter2024_fig10_digitised.csv`
(committed) from the figure image extracted from the main-text PDF (page 10,
kept locally as `refs/Lassitter2024_fig10.png`, gitignored as copyrighted). QA
overlay: `figures/qa_lassitter_fig10_digitised.png`. The frame corners are the
axis limits (0–600 min, 0–35 % RH); markers are classified square (inlet) vs
circle (effluent) by corner ink; the legend region is excluded by position.

| series | points | notes |
|---|---|---|
| inlet squares | 39 | 31.5 → 33.3 % RH over the run (the ambient feed drifts ~2 %; Table S8's 32.8 % is the mean) |
| effluent circles | 37 | 4 sit on the axis line at t = 18–67 min and are recorded at RH 0 (flagged); markers overlap the inlet series after ~330 min (flagged) |
| COMSOL line | 625 columns | first rise at ≈ 128 min, plateau ≈ 9–10 % RH from 150 to 280 min, shock 300–330 min, 32.7 % after |

Effluent, digitised: first leak at **83 min (1.2 % RH)**, plateau **7.4–10.5 %
RH from 146 to 250 min** (≈ 0.25–0.32 of the inlet), rise through 11.9 (267 min),
14.5 (283), 20.9 (296), 28.0 (319), 29.8 (333), 31.1 (350), then 32.1–32.3 %
from 400 min. **A two-wave breakthrough with a Henry-branch plateau at roughly
30 % of the feed and a cooperative shock ~150 min later** — §6c in a real MOF-303
bed, at conditions that are fully on record. The comparison was pre-registered
(`PREREG_LASSITTER.md`) and run 2026-09-03: see `RESULTS.md`, "The solver against a
real MOF-303 bed". Reproduces the shape and the 50 % arrival with no fitting; the
first-wave arrival and the shock width are the two named discrepancies.

---

## Tranche 3 (2026-09-03) — the weighting schemes cited in `PREREG_L4b_v2.md`

| ref | state | notes |
|---|---|---|
| **Wang, Teng & Perdikaris**, *Understanding and mitigating gradient flow pathologies in physics-informed neural networks*, **SIAM J. Sci. Comput. 43(5), A3055–A3081 (2021)**, DOI 10.1137/20M1318043; arXiv:2001.04536 | ✅ **VERIFIED** (Crossref record + arXiv abstract) | The gradient-norm balancing rule L4 and L4b use: *"a learning rate annealing algorithm that utilizes gradient statistics during model training to balance the interplay between different terms in composite loss functions."* |
| **Wang, Yu & Perdikaris**, *When and why PINNs fail to train: A neural tangent kernel perspective*, **J. Comput. Phys. 449, 110768 (2022)**, DOI 10.1016/j.jcp.2021.110768; arXiv:2007.14527 | ✅ **VERIFIED** (Crossref record + arXiv abstract; ScienceDirect page 403) | The NTK weighting arm: adaptive weights from the NTK eigenvalues to *"calibrate the convergence rate"* of the loss components. Our implementation uses per-point gradient norms as the diagonal (trace) estimate, per term, EMA-smoothed — a stated approximation, not their full eigen-decomposition. |
| **McClenny & Braga-Neto**, *Self-adaptive physics-informed neural networks using a soft attention mechanism*, **J. Comput. Phys. 474, 111722 (2023)**, DOI 10.1016/j.jcp.2022.111722; arXiv:2009.04544 v5 (2024) | ✅ **VERIFIED** (arXiv record with the journal reference) | The self-adaptive arm: *"trainable weights applied to each training point individually"*, minimised in the network and maximised in the weights. Ours: softplus-parameterised per-point weights on a fixed collocation pool, minibatched. |
| **Rathore, Lei, Frangella, Lu & Udell**, *Challenges in training PINNs: a loss landscape perspective*, **ICML 2024** (oral), arXiv:2402.01868 v2 | ✅ **VERIFIED** (arXiv record) | The optimiser robustness check: they *"compare gradient-based optimizers Adam, L-BFGS, and their combination Adam+L-BFGS, showing the superiority of Adam+L-BFGS"* and tie PINN ill-conditioning to the differential operator. Our Q4 polish is Adam → L-BFGS on both arms of a pair. |

### Tranche 3, continued (2026-09-03) — prior art the Introduction and the warp section cite

| ref | state | notes |
|---|---|---|
| **Herde, Raonić, Rohner, Käppeli, Molinaro, de Bézenac & Mishra**, *Poseidon: Efficient Foundation Models for PDEs*, **arXiv:2405.19101** (2024) | ✅ **VERIFIED** (arXiv record) | *"Poseidon also generalizes very well to new physics that is not seen during pretraining"*; 15 downstream tasks. **A23's identifier for this paper was wrong (B42).** NeurIPS 2024 acceptance not stated on the arXiv page — cite the arXiv record unless the proceedings entry is fetched. |
| **McCabe et al.** (14 authors), *Multiple Physics Pretraining for Physical Surrogate Models*, **arXiv:2310.02994** (2023) | ✅ **VERIFIED** (arXiv record) | *"more accurate predictions … on systems with previously unseen physical components"*. This is the identifier A23 had attached to Poseidon. |
| **Kraß, Huang & Moosavi**, *MOFSimBench: evaluating universal machine learning interatomic potentials in metal–organic framework molecular modeling*, **npj Comput. Mater. 12:4 (2025)**, DOI 10.1038/s41524-025-01872-3; arXiv:2507.11806 | ✅ **VERIFIED** (Crossref record: volume 12, article 4, published online 11 Dec 2025) | Held-out **materials** for uMLIPs on MOFs, 20 models; the "held-out materials is established for interatomic potentials" half of A23's residue. |
| **Kneip & Gasser**, *Statistical tools to analyze data representing a sample of curves*, **Ann. Statist. 20(3) (1992)**, DOI 10.1214/aos/1176348769 | ✅ **VERIFIED** (Crossref) | The landmark-registration ancestor (B38: not Ramsay & Li). |
| **Nair & Balajewicz**, *Transported snapshot model order reduction approach for parametric, steady-state fluid flows containing parameter-dependent shocks*, **IJNME 117(12):1234–1262 (2019)**, DOI 10.1002/nme.5998 | ✅ **VERIFIED** (Crossref) | Multi-front transported snapshots; prior art on aligning shocks (B36). |
| **Mendible, Brunton, Aravkin, Lowrie & Kutz**, *Dimensionality reduction and reduced-order modeling for traveling wave physics*, **Theor. Comput. Fluid Dyn. 34(4):385–400 (2020)**, DOI 10.1007/s00162-020-00529-9 | ✅ **VERIFIED** (Crossref) | Traveling-wave ROM; prior art (B36). |
| **Zucatti & Zahr**, *Model reduction of convection-dominated viscous conservation laws using implicit feature tracking and landmark image registration*, **arXiv:2503.17463** (2025) | ✅ **VERIFIED** (arXiv record) | **Landmark image registration with RBF interpolation, landmarks from shock detection + clustering** — the closest methodological relative of our two-landmark warp; must be cited in the warp section alongside Kneip & Gasser, not only in the sPOD list. |
| **Taddei**, *Erratum: A registration method for model order reduction: data compression and geometry reduction*, **SIAM J. Sci. Comput. 48(3):A1839–A1842 (2026)**, DOI 10.1137/24M1639579 | ✅ **VERIFIED** (Crossref) | *"corrected versions of Proposition 2.1 and its proof"* of the 2020 paper. Cite the erratum next to the original; nothing we use depends on Proposition 2.1. |
| **Rohrer, Tierney, Uhlmann et al.** (17 authors), *Putting the self in self-correction: findings from the Loss-of-Confidence Project*, **Perspect. Psychol. Sci. 16(6):1255–1269 (2021)**, DOI 10.1177/1745691620964106 | ✅ **VERIFIED** (Crossref) | For the corrections section: disclosed self-correction is received well. |

---

## Tranche 4 (2026-09-05) — the KAN cluster, the critique literature, the registration family, MOF-303 and the closures

Fetched by five parallel verification passes, each instructed to try to **falsify** what
the project believed rather than confirm it. Four passes returned; the fifth (the
classical adsorption references) **died on an account session limit and must be re-run**
— those seven remain unverified and uncitable (list at the end of this tranche).

This tranche found **more real defects than any previous one**, including two references
that do not say what we cite them for. They are recorded as **B45–B53**.

### 4a — the KAN cluster (rung L3, and the Introduction)

| ref | state | notes |
|---|---|---|
| **Abueidda, Pantidis & Mobasher**, *DeepOKAN: Deep operator network based on Kolmogorov Arnold networks for mechanics problems*, **CMAME 436:117699 (2025)**, DOI **10.1016/j.cma.2024.117699**, arXiv:2405.19143 | VERIFIED | Gaussian-RBF basis confirmed verbatim: *"uses Gaussian radial basis functions (RBFs) rather than the B-splines"*. Three authors, no substitution. **DOI trap: the year segment is 2024, not 2025.** ⚠️ **Their DeepOKAN is NOT physics-informed** — a purely data-driven neural operator benchmarked against DeepONet. It pre-empts the *name* and the *basis*, not a physics-informed variant. See **B45**. |
| **Shukla, Toscano, Wang, Zou & Karniadakis**, *A comprehensive and FAIR comparison between MLP and KAN representations for differential equations and operator networks*, **CMAME 431:117290 (2024)**, DOI 10.1016/j.cma.2024.117290, arXiv:2406.02917 | VERIFIED | Confirmed: KANs *"still lack robustness as they may diverge for different random seeds"*; sensitive to initialisation, need a tanh composition and float64. **Their conclusion is two-tiered, not "MLPs beat KANs"**: original B-spline KANs lack accuracy and efficiency, while *modified* KANs on low-order orthogonal polynomials reach performance **comparable** to PINNs/DeepONet but are not robust. They **do** build physics-informed DeepOKANs, so they — not Abueidda — are the prior art for that. A duplicate SSRN record exists (10.2139/ssrn.4858126); cite the CMAME DOI. |
| **Wang, Sun, Bai, Anitescu, Eshaghi, Zhuang, Rabczuk & Liu**, *Kolmogorov–Arnold-Informed neural network: a physics-informed deep learning framework for solving forward and inverse problems based on Kolmogorov–Arnold Networks* (KINN), **CMAME 433:117518 (2025)**, DOI **10.1016/j.cma.2024.117518**, arXiv:2406.11045 | VERIFIED | Eight authors — the short form hides seven. **DOI year segment is 2024.** ⚠️ **This paper cuts against us**: *"KINN significantly outperforms MLP regarding accuracy and convergence speed"* on solid-mechanics PDEs, the opposite direction from Shukla. The literature is **split**, and L3 must say so. See **B46**. |
| **Kiyani, Shukla, Urbán, Darbon & Karniadakis**, *Optimizing the optimizer for physics-informed neural networks and Kolmogorov–Arnold networks*, **CMAME 446:118308 (2025)**, DOI 10.1016/j.cma.2025.118308, arXiv:2501.16371 | VERIFIED, ⚠️ **our claim was overstated** | It does **not** find that KANs need a *different* optimiser from MLPs. It finds that **both** PINNs and PIKANs are under-served by Adam/L-BFGS and **both** improve by orders of magnitude under the *same* self-scaled quasi-Newton schemes (SSBFGS, SSBroyden), and calls PIKANs *"effective and comparable in accuracy with PINNs"*. Cite for "optimiser choice dominates accuracy for physics-informed models, KANs included". See **B46**. |
| **Rigas, Anagnostopoulos, Papachristou & Alexandridis**, *Training deep physics-informed Kolmogorov–Arnold networks*, **CMAME 452:118761 (2026)**, DOI 10.1016/j.cma.2026.118761, arXiv:2510.23501 | VERIFIED, ⚠️ **claim mismatch** | About **initialisation and architecture**, not optimisers and not adaptivity: a Glorot-like basis-agnostic initialisation and a Residual-Gated Adaptive KAN block. *"cPIKANs face significant challenges when scaled to depth."* Use **2026** (Semantic Scholar says 2025; Crossref and the arXiv journal-ref say 2026). An SSRN preprint carries a **different title** (*Towards Deep…*). Also cuts against us: RGA-KANs *"consistently outperform parameter-matched cPIKANs and PirateNets"*, and PirateNet is an MLP architecture. |
| **Rigas, Papachristou, Papadopoulos, Anagnostopoulos & Alexandridis**, *Adaptive Training of Grid-Dependent Physics-Informed Kolmogorov–Arnold Networks*, **IEEE Access 12:176982–176998 (2024)**, DOI 10.1109/ACCESS.2024.3504962, arXiv:2407.17611 | PARTIAL | A **different paper with a different author list** from the CMAME one — five authors, adding Theofilos Papadopoulos, and Anagnostopoulos carries a middle initial here. This is the one whose subject really is *adaptivity*. Abstract retrieved only as an inverted-index reconstruction, so the claim is unverified; one more fetch before it may be cited. |

### 4b — the critique literature and operator-learning theory

| ref | state | notes |
|---|---|---|
| **McGreivy & Hakim**, *Weak baselines and reporting biases lead to overoptimism in machine learning for fluid-related partial differential equations*, **Nature Machine Intelligence 6(10):1256–1269 (2024)**, DOI 10.1038/s42256-024-00897-5, arXiv:2407.07218 | VERIFIED | *"we determine that 79 % (60/76) compare to a weak baseline"*. **Scope the number**: the denominator is articles that solve a fluid-related PDE **and claim to outperform a standard numerical method** — not all ML-for-PDE papers. The reporting-bias half is qualitative; **do not attach 79 % to it**. |
| **Grossmann, Komorowska, Latz & Schönlieb**, *Can physics-informed neural networks beat the finite element method?*, **IMA J. Appl. Math. 89(1):143–174 (2024)**, DOI 10.1093/imamat/hxae011, arXiv:2302.04107 | VERIFIED | *"physics-informed neural networks have not been able to outperform the finite element method"* — but explicitly *"in our study"*, over Poisson 1/2/3-D, Allen–Cahn 1-D and semilinear Schrödinger 1/2-D: low-dimensional, FEM-friendly problems, not a theorem. The abstract also concedes *"In some experiments, they were faster at evaluating the solved PDE."* Scope it or a referee will. |
| **Bartolucci, de Bézenac, Raonić, Molinaro, Mishra & Alaifari**, *Representation Equivalent Neural Operators: a Framework for Alias-free Operator Learning* (ReNO), **NeurIPS 2023** (Advances in NeurIPS 36), arXiv:2305.19913 | VERIFIED | Six-author list survived character-by-character checking against arXiv, DBLP and the NeurIPS proceedings page. *"operator aliasing, which measures inconsistency between neural operators and their discrete representations."* The framework is diagnostic and *"potentially"* constructive — **do not cite ReNO as a solved problem**. No page numbers exist for NeurIPS; cite volume 36. |
| **Ohlberger & Rave**, *Nonlinear reduced basis approximation of parameterized evolution equations via the method of freezing*, **C. R. Math. 351(23–24):901–906 (2013)**, DOI 10.1016/j.crma.2013.10.028 | VERIFIED — **and the claim is REFUTED** | **The full open-access text at Numdam contains the strings "Kolmogorov", "n-width" and "N-width" nowhere, and states no decay rate.** It is a *method* paper (freezing; group + shape decomposition). It may be cited for nonlinear/transformed reduced bases for moving discontinuities — **never for slow n-width decay**. Our `PARTIAL` status was masking a substantive mismatch, not merely an unchecked abstract. See **B47**. The arXiv preprint (1304.4513) carries a different title; cite the published one. |
| **Ohlberger & Rave**, *Reduced Basis Methods: Success, Limitations and Future Challenges*, **Proceedings of ALGORITMY 2016, 1–12**, arXiv:1511.02021 | VERIFIED | **This** is the citation for the slow n-width: *"A slow decay of the Kolmogorov N-widths can already be observed"*, and §5 proves **d_N(M) ≥ ½·N^(−1/2)** for a linear advection problem with jump discontinuities. ⚠️ **It is a LOWER bound.** Write *"decays no faster than N^(−1/2)"*, never *"decays like N^(−1/2)"* or *"is O(N^(−1/2))"*, which asserts an upper bound they do not prove. The bound uses Pinkus (*n-widths in Approximation Theory*, Springer 1985) Cor. IV.2.11 as a general tool — **Pinkus is not an alternative citation for the transport claim**. An earlier automated read attributed the rate to "Cohen & DeVore 2014"; the passage cites Pinkus. **Do not propagate that attribution.** For contrast they prove (Thm 3.1) that affinely decomposed coercive problems satisfy d_N ≤ C exp(−c N^(1/Q)). |
| **Greif & Urban**, *Decay of the Kolmogorov N-width for wave problems*, **Appl. Math. Lett. 96:216–222 (2019)**, DOI 10.1016/j.aml.2019.05.013, arXiv:1903.08488 | VERIFIED — not the source we were looking for | Checked as a candidate *earlier* canonical source: it is **later** (2019), and for the transport statement it cites *"the known slow decay of d_N(M) for the linear transport problem"* to **Ohlberger & Rave 2016** — so the chain terminates there and no earlier canonical paper exists. Their own N^(−1/2) theorem is for the **hyperbolic wave equation** with discontinuous initial data: a companion result, not a substitute. Cite only if wave problems are discussed. |

### 4c — the registration / sPOD family (§7, the warp)

| ref | state | notes |
|---|---|---|
| **Reiss, Schulze, Sesterhenn & Mehrmann**, *The shifted proper orthogonal decomposition: a mode decomposition for multiple transport phenomena*, **SIAM J. Sci. Comput. 40(3):A1322–A1344 (2018)**, DOI 10.1137/17M1140571 | VERIFIED | **B35 definitively refuted**: the fourth author is Volker **Mehrmann**; no Noack anywhere on the record. Note the umlaut: **Jörn** Sesterhenn. The two-wave example and *"more than 80 POD modes are required"* against *"the full information is described by just two modes"* confirmed **from the arXiv/ar5iv full text (§2.2), not the typeset SISC pages — do not cite a journal section number.** Semantic Scholar reports 2015 (inheriting the arXiv posting date); **2018** is correct. |
| **Krah, Marmin, Zorawski, Reiss & Schneider**, *A robust shifted proper orthogonal decomposition: proximal methods for decomposing flows with multiple transports*, **SIAM J. Sci. Comput. 47(2):A633–A656 (2025)**, DOI **10.1137/24M164392X**, arXiv:2403.04313 | VERIFIED | Five authors; the project held only "Krah and co-authors". Preprint and paper are the same work (arXiv carries the journal-ref; v2 is the accepted version). ⚠️ **The DOI ends in the letter X** and is one character from the Taddei erratum's 10.1137/24M1639579, which we also cite. Do not transpose them. |
| **Zorawski, Burela, Krah, Marmin & Schneider**, *Automated transport separation using the neural shifted proper orthogonal decomposition*, **arXiv:2407.17539 (2024)**, ECCOMAS 2024 proceedings | VERIFIED, with a trap | ⚠️ **Do not copy arXiv's Related DOI 10.23967/eccomas.2024.066** — resolved twice against Crossref, it belongs to *"Zooming into Kinetic Equations using the Characteristic Mapping Method"* by Krah, Yin, Bergmann, Nave & Schneider. Overlapping authors, same proceedings: **B42's exact pattern**. Cite the arXiv id alone. Also **Shubhaditya Burela** was missing from our author list entirely, and arXiv's comments say *"Proceedings not peer-reviewed yet"* — describe it as a non-peer-reviewed proceedings item. See **B48**. |
| **Taddei**, *A registration method for model order reduction: data compression and geometry reduction*, **SIAM J. Sci. Comput. 42(2):A997–A1027 (2020)**, DOI 10.1137/19M1271270, arXiv:1906.11008 | VERIFIED | Record exactly as believed. ⚠️ **Wording**: it is a *"parameter-independent registration method"* that **produces** a parameter-dependent bijective mapping — do not call the method parameter-dependent. His mappings act on the **spatial** domain and are found by optimisation over a mapping ansatz, not written in closed form from identified fronts: a real distinction of construction, **not of kind**. Cite the 2026 erratum alongside. |
| **Zucatti & Zahr**, *Model reduction of convection-dominated viscous conservation laws using implicit feature tracking and landmark image registration*, **J. Comput. Phys. 561:114958 (2026)**, DOI 10.1016/j.jcp.2026.114958, arXiv:2503.17463 | VERIFIED — **our tranche-3 record is now STALE** | Published since; citing it as a preprint would be a defect. ⚠️ **This is the closest prior art in the group and §7 must name it as such**: *"a novel landmark-based registration procedure tailored for ROMs of convection-dominated problems"* — the same primitive as our two fronts. Our defensible distinctions: their landmarks are detected shock features **in space**, RBF-interpolated into a mesh warp and coupled to implicit feature tracking; ours are two fronts **in time** giving a closed-form affine interval map. If we do not name it, a referee will, and it will look like we hid it. See **B49**. |
| **Ramsay & Li**, *Curve registration*, **J. R. Statist. Soc. B 60(2):351–363 (1998)**, DOI **10.1111/1467-9868.00129** | VERIFIED — **and we should cite it after all** | *"registration or alignment of salient curve features by suitable monotone transformations"*, with analyses carried out on **x_i{h_i(t)}** — composition with a monotone warp, exactly our structure; the abstract notes engineers call it dynamic time warping. **B38 remains correct** that their *method* is the landmark-free branch, and B38 itself already allowed citing them as the landmark-free contrast — but omitting them is the likeliest ambush in §7. ⚠️ **Identifier trap caught**: DOI …00115 is a *different* JRSS-B 1998 paper (Wang, *Mixed Effects Smoothing Spline ANOVA*, 60(1):159–174). Semantic Scholar conflates this record with a 2018 Oxford handbook chapter; Crossref is authoritative. |
| **Krah, Büchholz, Häringer & Reiss**, *Front transport reduction for complex moving fronts: nonlinear model reduction for an advection–reaction–diffusion equation with a Kolmogorov–Petrovsky–Piskunov reaction term*, **J. Sci. Comput. 96(1):28 (2023)**, DOI 10.1007/s10915-023-02210-9 | VERIFIED — **and it narrows our distinction** | Reduces **advection–reaction–diffusion** fronts, the equation class a breakthrough front belongs to — closer to our physics than the acoustic and vortex sPOD examples. It parameterises the field as a nonlinear activation **composed** with a level-set function: a *compositional* construction from inside the sPOD school. **Our "sPOD is additive, ours is compositional" line is therefore too clean** and must be narrowed to: *our map composes on the **time** argument between two identified fronts, whereas front-transport reduction composes an activation with a level set in **space***. See **B50**. Umlauts: Büchholz, Häringer. |
| **Papapicco, Demo, Girfoglio, Stabile & Rozza**, *The neural network shifted-proper orthogonal decomposition: a machine learning approach for non-linear reduction of hyperbolic equations*, **CMAME (2022)**, DOI 10.1016/j.cma.2022.114687 | PARTIAL — **priority flag** | **Predates Zorawski et al. by two years**, so "the neural sPOD" must not be attributed to Zorawski. Retrieved only from a Crossref *query listing*, not a direct `works/<DOI>` fetch; volume, pages and article number unconfirmed. **Do not put it in the bibliography until fetched directly.** The same query surfaced Kovárnová, Krah, Reiss & Isoz, *Topical Problems of Fluid Mechanics 2022*, DOI 10.14311/tpfm.2022.016 — another earlier sPOD-plus-network combination, likewise unverified. |
| **Gowrachari, Stabile & Rozza**, *Model reduction for transport-dominated problems via cross-correlation based snapshot registration*, **arXiv:2501.01299 (2025)** | VERIFIED — **a negative result in our favour** | Searched because a **search-engine summary** claimed this line of work targets chromatography. **It does not**: the retrieved abstract lists only 1-D travelling waves and a 2-D isentropic convective vortex. Registration ROM has **not** been taken into separation-process column fields. A reminder that a search summary is never evidence — this one would have manufactured a false "we are scooped". |

#### The falsification question, asked and answered

> **Has anyone published a two-landmark or interval-normalising TIME reparameterisation
> applied to adsorption breakthrough curves or packed-column fields?**

**No publication found.** The *application* appears genuinely unclaimed. But the answer
is **split**, and the second half matters more.

**The map itself is textbook.** Piecewise landmark registration — a monotone warp built
by interpolating between identified landmark times — is the standard alignment method in
functional data analysis, shipping in `R fda::landmarkreg` and `scikit-fda`'s
`landmark_registration`. **The two-landmark linear case reduces exactly to
σ = (t − t_lo)/(t_hi − t_lo).** A referee who knows FDA will recognise it on sight.
Frame the contribution as *"we identify the two fronts that make the classical landmark
reparameterisation work for breakthrough fields, and measure what it buys and what limits
it"* — **never as a new map**. This is **C2's conclusion reached a second time from a
different direction**, and it tightens it.

Near-misses, all with fetched identifiers, all to be cited:

- **Knox, Ebner, LeVan, Coker & Ritter**, *Limitations of Breakthrough Curve Analysis in
  Fixed-Bed Adsorption*, **Ind. Eng. Chem. Res. 55(16):4734–4748 (2016)**,
  DOI 10.1021/acs.iecr.6b00516. **The referee risk to pre-empt**: constant-pattern
  behaviour — a front propagating without changing shape — is long established in
  fixed-bed adsorption, and a referee can say our map merely re-derives constant-pattern
  scaling. Say plainly what it adds **when the pattern is not constant**, i.e. when the
  two fronts move at different rates, which is exactly what one scale factor cannot do.
- **Emami-Meibodi**, *A generalized dimensionless form of the break-through curve for
  adsorption processes*, **Chem. Eng. Sci. 282:119343 (2023)**,
  DOI 10.1016/j.ces.2023.119343 — single-parameter dimensionless-time collapse, the
  closest thing in our own domain (Crossref record fetched; abstract not retrieved).
- **Roy & Moharir**, *Modeling the Generic Breakthrough Curve for Adsorption Process*,
  arXiv:1907.00195 — likewise one scale factor.
- **Standridge, Livescu & Cizmas**, *Trajectory-Optimized Time Reparameterization for
  Learning-Compatible Reduced-Order Modeling of Stiff Dynamical Systems*,
  **arXiv:2603.16583 (2026)** — warps **time** for ROM, by arc-length/stiffness
  optimisation rather than landmarks, and not for adsorption. Cite it so we are not
  accused of missing that time-warping ROM is a live topic. (Abstract returned truncated;
  confirm before quoting anything from it.)
- **Long, Barnett, Jefferson-Loveday, Stabile & Icardi**, *A reduced-order model for
  advection-dominated problems based on Radon Cumulative Distribution Transform*,
  arXiv:2304.14883 — another nonlinear-transform-before-POD approach.

### 4d — MOF-303, the experimental anchor, and the closures

| ref | state | notes |
|---|---|---|
| **Hanikel, Pei, Chheda, Lyu, Jeong, Sauer, Gagliardi & Yaghi**, *Evolution of water structures in metal–organic frameworks for improved atmospheric water harvesting*, **Science 374(6566):454–459 (2021)**, DOI 10.1126/science.abj0890 | VERIFIED, ⚠️ **our figure attribution is wrong** | *"corresponded to a total uptake of 0.45 g g⁻¹"* — correct, and tied to **Fig. 1A**. But the **≈53 kJ/mol does not come from Fig. 1A**; Fig. 1A is only the 25 °C isotherm plus the crystal structure. The enthalpy is in the **multivariate-series section (text S10 / Fig. 4)**, from isotherms at 15/35/45 °C by Clausius–Clapeyron, running **−53 → −50 kJ/mol** across the PZDC→FDC series, with −53 the parent MOF-303 end. The paper calls it the **differential adsorption enthalpy Δh_ads** and reports it **negative**; it does not call it the isosteric heat. **25.0 mol/kg is our own conversion** (0.45/0.018), arithmetically right but never stated by the paper. See **B51**. |
| **Fathieh, Kalmutzki, Kapustin, Waller, Yang & Yaghi**, *Practical water production from desert air*, **Sci. Adv. 4(6):eaat3198 (2018)**, DOI 10.1126/sciadv.aat3198 | VERIFIED | *"inflection point at P/P0 = 0.15, a plateau is reached at P/P0 = 0.3"*, explicitly for MOF-303. Two context points: the headline **desert device used MOF-801**, not MOF-303 — do not attribute that data to MOF-303; and this paper gives MOF-303 a maximum capacity of **0.48 g/g** against Hanikel's 0.45. **Reconcile, or state which measurement each is.** |
| **Bozbiyik, Van Assche, Lannoeye, De Vos, Baron & Denayer**, *Stepped water isotherm and breakthrough curves on aluminium fumarate metal–organic framework: experimental and modelling study*, **Adsorption 23(1):185–192 (2017)**, DOI 10.1007/s10450-016-9847-0 | VERIFIED, ⚠️ **two defects in what we believed** | (1) **A missing author**: **Tom Van Assche** is the second author and had been dropped — B35's class again, confirmed by four independent sources. (2) **Wrong venue**: the journal is *Adsorption*, not PCCP or Chem. Eng. Sci. ⚠️ **Scope the claim**: at *low* water partial pressure a **single** breakthrough step is seen; *"a stepped profile is observed at higher partial pressure of water"*. It is feed-condition dependent, not a property of the material. The two-step type-IV isotherm, and the deliberate study of isotherm shape on column dynamics, **are** exactly our attribution. See **B52**. |
| **Hastings, Lassitter, Zheng, Chheda, Siepmann, Gagliardi, Yaghi & Glover**, *High-Temperature Water Adsorption Isotherms and Ambient Temperature Water Diffusion Rates on Water Harvesting Metal–Organic Frameworks*, **J. Phys. Chem. C 128(27):11328–11339 (2024)**, DOI 10.1021/acs.jpcc.4c01733 | VERIFIED | ⚠️ **Do not confuse with Lassitter et al. 2024** (*Chem. Eng. Sci.* 285:119430, fourteen authors, Lassitter first) — Lassitter is *second* author here. It is **this** paper whose ref. 47 is Bozbiyik. It gives **no** MOF-303 capacity and **no** MOF-303 isosteric heat, so it cannot back 0.45 g/g or 53 kJ/mol; its 54 kJ/mol is **MOF-LA2-1**, a different material, and letting that transcribe as MOF-303's 53 is exactly the slip that produced B42. One relevant result: the MOF-303 isotherm step **shifts toward 15 % RH from 25 → 45 °C** — the step position is temperature dependent, worth acknowledging since our isotherm places it at 13.2 % RH. It cites Ruthven 1984 only for transport diffusion, not for axial dispersion. |
| **Lassitter, Hanikel, Coyle, Hossain, Lipinski, O'Brien, Hall, Hastings, Borja, O'Neil, Neumann, Moore, Yaghi & Glover**, *Mass transfer in atmospheric water harvesting systems*, **Chem. Eng. Sci. 285:119430 (2024)**, DOI 10.1016/j.ces.2023.119430 | VERIFIED | Fourteen authors, confirmed against Crossref and against ref. 40 of the Hastings paper. |
| **Ruthven**, *Principles of Adsorption and Adsorption Processes*, Wiley-Interscience, New York, 1984, ISBN 0-471-86606-7, xxiv + 433 pp | PARTIAL — **and the attribution looks WRONG** | Ruthven's own text is **BLOCKED** (archive.org lending-restricted; Google Books rate-limited), so the original statement and any validity range could not be read. **Perry's Sec. 16 Table 16-10 attributes the 0.7 / 0.5 coefficient pair to Wakao & Funazkri (1978), for nonporous particles** — not to Ruthven, who appears there only for the range γ₁ = 0.64–0.73 following from Wicke's γ₁ = 0.45 + 0.55ε. ⚠️ **And it contradicts our use of it**: Perry's presents these correlations as a **lower bound** on axial dispersion, notes γ₁ rises from 0.7 for nonporous particles to as much as **20/ε** depending on the intraparticle mass-transfer mechanism, and states that for **strongly adsorbed species** the effective axial dispersion is **much larger** than the nonporous non-adsorbing estimate. Our beds are porous, strongly adsorbing MOF particles taking up water — precisely the case Perry's says this form **underestimates**. **No Reynolds range verified**: 0.008 < Re < 50 appeared in a search snippet only and may not be used. Knox et al.'s "1984; p 433" is the **total page count** in ACS style, not a page locator. See **B53**. |
| **Wakao & Funazkri**, *Effect of fluid dispersion coefficients on particle-to-fluid mass transfer coefficients in packed beds: correlation of Sherwood numbers*, **Chem. Eng. Sci. 33(10):1375–1384 (1978)**, DOI 10.1016/0009-2509(78)85120-3 | VERIFIED | The primary source of the 0.7 / 0.5 coefficients per Perry's Table 16-10, **for nonporous particles**. This is what we should be citing for the closure, alongside or instead of Ruthven. |
| **Edwards & Richardson**, *Gas dispersion in packed beds*, **Chem. Eng. Sci. 23(2):109–123 (1968)**, DOI 10.1016/0009-2509(68)87056-3 | VERIFIED | Perry's gives γ₁ = 0.73 with γ₂ = 0.5/(1 + 9.7 D_m/(d_p v)) — a form that reduces to 0.5 only at **high** particle Péclet number. **If our beds sit at low d_p·u/D_m the plain 0.5 d_p u term is not the right limit**, and this is the better correlation. Check the project's actual Péclet range against this before finalising the limitations. |
| **Bruggeman**, *Berechnung verschiedener physikalischer Konstanten von heterogenen Substanzen. I. Dielektrizitätskonstanten und Leitfähigkeiten der Mischkörper aus isotropen Substanzen*, **Ann. Phys. 416(7):636–664 (1935)**, DOI 10.1002/andp.19354160705 | PARTIAL | Record exactly right (older literature cites the same paper as Ann. Phys. (5. Folge) **24**, 636 — pre-continuous numbering; ours is the modern form). **Claim unchecked**: Wiley paywalls the 1935 text. ⚠️ The title establishes the subject as **dielectric constants and conductivities of mixtures of isotropic substances** — an electrostatics/conduction paper, explicitly Part I. **It does not state D_eff = ε^1.5 D_m**; that is the later conductivity–diffusivity analogy applied to porous media. Say *"the closure follows the Bruggeman effective-medium relation"*, never that the 1935 paper writes it for diffusion. Retrieved evidence on real porous media reports Bruggeman **underestimates tortuosity**, so ε^1.5 tends to **over**estimate effective diffusivity; Perry's gives measured adsorbent tortuosities of **2–6** (recommending 4) against ε^(−0.5) ≈ 1.4–1.7 — though Perry's figure is intraparticle and ours is a bed/macropore closure, so the two are not strictly the same quantity. |
| **LeVan & Carta**, *Adsorption and Ion Exchange*, Section 16 in **Perry's Chemical Engineers' Handbook, 9th ed.** (Green & Southard, eds.), McGraw-Hill Education, New York, 2019 | VERIFIED (claim), ⚠️ **edition and byline** | Claim confirmed verbatim from a fetched full text: *"a simple wave occurs for an unfavorable dimensionless isotherm"* because low concentrations travel faster than high; for a favourable isotherm the simple-wave solution is impossible and the correct solution is a **shock**; with mass-transfer resistance or axial dispersion the transition approaches a **constant pattern** and self-sharpens; asymptotically, proportionate-pattern spreading for R > 1, constant pattern for R < 1, √t spreading for R = 1. ⚠️ **The text read was the SEVENTH edition (1997)** — a widely mirrored file whose *filename* says "8th Edition" has a title page reading SEVENTH EDITION. ⚠️ **The byline changes by edition**: the 7th lists **three** contributors (LeVan, Carta **and Carmen M. Yon**); the 9th lists two. "LeVan & Carta" is therefore wrong for the 7th. The 8th-edition byline could not be verified from an authoritative source (WorldCat and Google Books both rate-limited). **Cite the 9th (2019)** — the only edition whose authorship was confirmed from a publisher document, and the current one. |

### Still unverified, and therefore uncitable

The fifth pass died on an account session limit. These remain **UNVERIFIED** and must be
re-run before the Methods, L0 and L7 sections can be written:

**van Genuchten & Alves (1982)** — the third-type inlet, B10's replacement reference;
**Ogata & Banks (1961)**; **Glueckauf (1955)** — the k = 15 D/r² factor;
**Klinkenberg (1948)** — L7's control, and its linear-isotherm assumption;
**Danckwerts (1953)**; **Anzelius (1926) / Schumann (1929)** — L0's J-function and the
correct attribution convention; and **Do & Do (2000)**.

The last carries the highest stakes: **the entire isotherm design (A5, B4) rests on the
published Do–Do form having a finite Henry slope at the origin**, and that has not been
checked against the source. If it does not, the form we use is ours rather than theirs
and must be described that way.

### 4e (2026-09-05) — the classical adsorption and transport references

The pass that died on a session limit, re-run. **Two of these seven turned out to
carry live attribution risks (B54, B55), one showed that our isotherm is not the form
we name it after (B56), and one supplied a textual argument for a boundary condition
we had only defended numerically (B59).** Four primaries could not be read at all;
they are cited through verified corroboration and marked `PARTIAL`, which in this
ledger means *the record is confirmed and the claim is not*.

| ref | state | notes |
|---|---|---|
| **van Genuchten & Alves**, *Analytical Solutions of the One-Dimensional Convective-Dispersive Solute Transport Equation*, **USDA ARS Technical Bulletin No. 1661**, U.S. Government Printing Office, Washington DC, 1982, 151 pp. | VERIFIED | **B10 confirmed, and stronger than we stated.** Eqn [9a] `c(0,t) = g(t)` is the *"first- or concentration-type"* inlet; eqn [9b] `−D ∂c/∂x + vc = v g(t)` is *"a third- or flux-type boundary condition of the form"* — and the bulletin cites **Ogata & Banks (1961)**, with Lapidus & Amundson (1952), for the first-type semi-infinite solution, exactly as B10 diagnosed. ⚠️ **It never uses the name "Danckwerts"** for [9b] — that eponym is from the reactor literature, and the only occurrence in the bulletin is inside the *title* of Pearson (1959) in its reference list. **And it hands us an argument we did not have**: the bulletin states [9b] conserves mass inside a column whereas [9a] causes mass-balance errors that grow with D/v — the same phenomenon as our own defect **B8**. Two lower boundary conditions are offered ([10a] semi-infinite, [10b] zero gradient at the column end) and the bulletin **explicitly declines to endorse one over the other**. Full text retrieved via AgEcon Search after `pubs.usgs.gov`, NALDC and direct PDF fetches all returned 403/404. |
| **Ogata & Banks**, *A Solution of the Differential Equation of Longitudinal Dispersion in Porous Media*, **USGS Professional Paper 411-A**, 1961, pp. A1–A7 | VERIFIED | Unambiguously a **first-type** inlet: *"its surface is maintained at concentration unity"*, with `C(∞,t) = 0`. ⚠️ **The page range in our source is wrong**: van Genuchten & Alves cite "A1–A9"; the report itself runs **A-1 to A-7**. Copying vGA's citation would propagate their error. Author is **R. B. Banks** (title page: "By AKIO OGATA and R. B. BANKS"; OpenAlex expands to Robert B. Banks). Their own novelty claim is narrower than "it solves the Dirichlet problem": they avoid the (x − ut) transformation and so obtain an **asymmetrical** distribution, converging on the symmetric-boundary result only for small D and away from the source — worth one clause if L0 uses them as a foil. Public-domain USGS document. |
| **Glueckauf**, *Theory of chromatography. Part 10.—Formulæ for diffusion into spheres and their application to chromatography*, **Trans. Faraday Soc. 51:1540–1551 (1955)**, DOI 10.1039/TF9555101540 (corrected 2026-09-25: the earlier ledger string TF9551501540 returns 404 on Crossref; TF9555101540 resolves to this title, vol. 51, pp. 1540–1551, author "E. Glueckauf") | PARTIAL | **BLOCKED on the primary**: RSC returns a Cloudflare 403, and Crossref, OpenAlex, Semantic Scholar and OSTI all carry the record with **no abstract**. The factor 15 has never been read from Glueckauf's own text. ⚠️ **Attribution risk (B55)**: Cruz, Magalhães & Mendes (*Chem. Eng. Sci.* 61:3519–3531, 2006) attribute the plain `dq/dτ = 15(q_s − q)` (their Eq. 44) to **Glueckauf & Coates (1947)**, and label as *"the result derived by Glueckauf (1955)"* a different expression (their Eq. 46) carrying an extra `dq_s/dτ` term. Perry's §16 does attribute the LDF to the 1955 paper "under linear equilibrium conditions" with time constant `r_s²/(15 D_s)`. **Cite both years.** Note the ligature *Formulæ* and the em dash — a `.bib` entry must not mangle them. |
| **Glueckauf & Coates**, *241. Theory of chromatography. Part IV. The influence of incomplete equilibrium on the front boundary of chromatograms and on the effectiveness of separation*, **J. Chem. Soc. 1947, 1315**, DOI 10.1039/jr9470001315 | VERIFIED | The companion citation wherever the manuscript writes `k = 15 D/r²`. Roman part number **IV**, leading serial **241.**, no volume (continuous pagination). **Coates is the co-author most often dropped when this reference is copied** — B35's failure mode, pre-empted. |
| **Klinkenberg**, *Numerical Evaluation of Equations Describing Transient Heat and Mass Transfer in Packed Solids*, **Ind. Eng. Chem. 40(10):1992–1994 (1948)**, DOI 10.1021/ie50466a034 | PARTIAL | ⚠️ **READ B54 FIRST — a live B42-class risk on L7's control.** The record is verified and internally consistent everywhere. But the erf expression L7 actually uses is attributed by **Seader, Henley & Roper** (*Separation Process Principles*, 3rd ed.) to **Klinkenberg (1954)**, *Heat Transfer in Cross-Flow Heat Exchangers and Packed Beds*, **Ind. Eng. Chem. 46(11):2285–2289**, DOI 10.1021/ie50539a021 — a different paper. **Neither is retrievable** (ACS closed, no abstracts anywhere), so which contains the formula is **unresolved**. Cite *"(Klinkenberg 1948, 1954)"* or attribute the equation to the secondary source until a primary is in hand. ⚠️ **Near-duplicate trap**: Crossref also holds `10.1021/ie50539a438`, same title and issue, paginated 43–43 — a one-page industrial-edition abstract. The **linear-isotherm assumption is confirmed** from an open-access application paper (Al-Anber, *Appl. Water Sci.* 3:77–84, 2013), which fits `q = Kc` and states the solution assumes constant velocity, negligible axial dispersion and LDF. |
| **Klinkenberg**, *Heat Transfer in Cross-Flow Heat Exchangers and Packed Beds*, **Ind. Eng. Chem. 46(11):2285–2289 (1954)**, DOI 10.1021/ie50539a021 | VERIFIED (record) | The candidate replacement or companion for L7's reference. Existence, author, journal, volume, issue, pages and year all confirmed; **which of the two years carries the equation is not**. |
| **Danckwerts**, *Continuous flow systems: Distribution of residence times*, **Chem. Eng. Sci. 2(1):1–13 (1953)**, DOI 10.1016/0009-2509(53)80001-1 | PARTIAL | **BLOCKED on the primary**: Elsevier closed, and Semantic Scholar explicitly reports the abstract *"elided by the publisher"*. The flux-inlet / zero-gradient-outlet claim was **not read from Danckwerts**. ⚠️ **Title trap**: Crossref, OpenAlex **and** Semantic Scholar all return the bare *"Continuous flow systems"*, silently dropping the subtitle — any `.bib` auto-generated from a DOI lookup will be wrong. The subtitle is real (Elsevier's own article page and the ISI Citation Classic both carry it). ⚠️ **Precedence**: Wehner & Wilhelm's Citation Classic commentary records that **Langmuir obtained the same solution in 1908** and was overlooked. Do not assert that Danckwerts originated the conditions. |
| **Pearson**, *A note on the "Danckwerts" boundary conditions for continuous flow reactors*, **Chem. Eng. Sci. 10(4):281–284 (1959)**, DOI 10.1016/0009-2509(59)80063-4 | VERIFIED | The companion to cite wherever the manuscript asserts *what* the boundary conditions are, given that the 1953 primary is unreadable: modern transport work routinely cites Pearson for the asymmetry between inlet and outlet, and **van Genuchten & Alves cite it too**, so it is already inside L0's citation neighbourhood. Note the scare quotes around "Danckwerts" are **part of the published title**. |
| **Anzelius**, *Über Erwärmung vermittels durchströmender Medien*, **ZAMM 6(4):291–294 (1926)** | PARTIAL | Closed at Wiley, no abstract anywhere — **the J-function was not read from Anzelius**. Three fixes to our string: the page range is **291–294**, not a bare start page; the paper is **in German** and the circulating English title *"Heating by means of percolating media"* is a **translation**, not the published title; and the attribution convention is **priority to Anzelius (1926), the name to Schumann (1929)** — write *"the Anzelius–Schumann solution"* and cite both. Convention confirmed from a CC-BY source (Rabi', Radulovic & Buick, *Thermo* 4:295–314, 2024). ⚠️ Perry's attributes the **J(s,t) integral definition** to **Hiester & Vermeulen, *Chem. Eng. Prog.* 48:505 (1952)** — that journal is not in Crossref, the reference is **UNVERIFIED, and it may not be cited**. |
| **Schumann**, *Heat transfer: A liquid flowing through a porous prism*, **J. Franklin Inst. 208(3):405–416 (1929)**, DOI 10.1016/S0016-0032(29)91186-8 | PARTIAL | Volume, issue, pages and year confirmed and matching our belief; **our entry carried no title at all** — supply it. Use **T. E. W. Schumann** (Crossref; OpenAlex normalises to "Thomas Schumann") and the full journal name *Journal of the Franklin Institute*. Closed at Elsevier with no abstract, so the closed form was not read from Schumann either. If L0's verification rests on the exact functional form of J, one of the two originals must be obtained; otherwise phrase as *"the classical Anzelius–Schumann solution"* without quoting equation numbers. |
| **Do & Do**, *A model for water adsorption in activated carbon*, **Carbon 38(5):767–773 (2000)**, DOI 10.1016/S0008-6223(99)00159-1 | PARTIAL | **The claim survives, with a caveat A5/B4 must absorb — see B56.** The Do–Do model is a **sum of two terms and only the first carries the finite Henry slope**: term 1 is an **n-layer-BET-like primary-site** term `f·K_f·Σ(n xⁿ)/(1 + K_f Σ xⁿ)` → `f·K_f·x` as x → 0; term 2 is a **Sips** term whose slope at the origin is **exactly zero** — *"regarded to fail because the slope at x = 0 is zero"* is the standard objection to that form. ⚠️ **Our primary term is a single-site Langmuir, not an n-layer BET**, so our equation is *in the spirit of* Do & Do, not their form (B56). ⚠️ **Do & Do (2000) fixes the cluster size (a = 5, m = 6)**; ours is a sampled material parameter, which is closer to the **2009** model. ⚠️ **Title trap**: several citing works render this as *"A **new** model…"* — the word "new" belongs to the 2009 paper; Crossref, OpenAlex and Buttersack all give the 2000 title without it. ⚠️ **Type IV vs V**: Buttersack repeatedly calls the Do–Do model a **type IV** model. Water on a hydrophobic surface is canonically Type V under IUPAC, so our label is defensible **in our own voice** — do not attribute "Type V" to Do & Do. **PARTIAL because the Carbon 2000 paper itself was not retrievable** (Elsevier closed; null abstract on Crossref, OpenAlex and Semantic Scholar); the functional form was verified from Buttersack's open-access reproduction. |
| **Do, Junpirom & Do**, *A new adsorption–desorption model for water adsorption in activated carbon*, **Carbon 47(6):1466–1473 (2009)**, DOI 10.1016/j.carbon.2009.01.039 | VERIFIED (record) | Relevant because **our cluster exponent is a free parameter and theirs is not**: the 2000 paper fixes a = 5 and m = 6, the 2009 paper lets them float. If our implementation treats the cluster size as an adjustable quantity — it does, as a *sampled* material parameter — the 2009 model is the closer relative and must be cited. **Three authors — do not drop Junpirom.** |
| **Buttersack**, *Modeling of type IV and V sigmoidal adsorption isotherms*, **PCCP 21(10):5614–5626 (2019)**, DOI 10.1039/C8CP07751G, CC BY-NC | VERIFIED | The document that carries the load for the Do–Do Henry-slope verification, and therefore one that must appear in the reference list if that claim is made: *"a hybrid one, essentially consisting of a superposition of the n-layer BET and the Sips equation"*, with the Do–Do isotherm transcribed at his eqns (29)–(30) and his ref. 34 being exactly Carbon 38:767–773. ⚠️ **Mildly adversarial to Do–Do**: he argues additive superposition of two independent terms is strictly applicable only when the terms describe **distinct sites**, and proposes his own single-term (Klotz-based) isotherm as theoretically preferable, while conceding Do–Do may fit some data better. **Citing him for the Henry-slope property must not imply he endorses the form.** |

**What remains genuinely open after this tranche**, and cannot be closed without
library access: which Klinkenberg paper carries L7's erf expression (**B54**); the
factor 15 in Glueckauf's own words (**B55**); the boundary-condition statement in
Danckwerts's own words (**B58**); the J-function in Anzelius's or Schumann's own words
(**B58**); and the Do–Do functional form from *Carbon* rather than through Buttersack
(**B56**). Every one of these is currently cited through a **verified secondary
source**, and the manuscript must say which, rather than implying the primaries were
read.

---

## Tranche 5 (2026-09-25) — material-as-input adsorption surrogates (B68)

Found by the research-program literature pass (`research/lit_water_harvesting_twins.md`,
S22/S23/S29). Records fetched from Crossref and the arXiv API; claims confirmed from the
OpenAlex abstract of the IECR paper, the OpenAlex abstract of the chemRxiv preprint of the
SPT paper (10.26434/chemrxiv-2021-26xgh), and the arXiv abstract.

| ref | state | notes |
|---|---|---|
| **Pai, Prasad & Rajendran**, *Generalized, Adsorbent-Agnostic, Artificial Neural Network Framework for Rapid Simulation, Optimization, and Adsorbent Screening of Adsorption Processes*, **Ind. Eng. Chem. Res. 59(38):16730–16740 (2020)**, DOI 10.1021/acs.iecr.0c02339 | VERIFIED | MAPLE: the Langmuir isotherm parameters are INPUTS; outputs are cyclic-steady-state KPIs (purity, recovery, energy, productivity) "for any arbitrary adsorbent"; test R²adj ≥ 0.995; CO2 capture. **Scalar KPIs at CSS, not transient fields; Langmuir only.** |
| **Pai, Nguyen, Prasad & Rajendran**, *Experimental validation of an adsorbent-agnostic artificial neural network (ANN) framework for the design and optimization of cyclic adsorption processes*, **Sep. Purif. Technol. 290:120783 (2022)**, DOI 10.1016/j.seppur.2022.120783 | VERIFIED | Trained on 20,000 detailed-model runs over hypothetical Langmuir parameters; used with measured N2/O2 isotherms of 13X and LiX that "were not a part of the dataset used to train the model"; nine Pareto points run on a two-column rig, mean |error| 3 / 5 / 9 % (purity / recovery / productivity). **Material transfer of an adsorption surrogate is established at the KPI level.** Caveat: "unseen" is unseen isotherm inside the sampled Langmuir box. |
| **Ceccanti, Galanti, Roghair & van Sint Annaland**, *Deep Operator Networks for Surrogate Modeling of Cyclic Adsorption Processes with Varying Initial Conditions*, **arXiv:2601.09491 (2026)** | VERIFIED | DeepONets for TVSA; generalisation tested "across a wide range of initial conditions" — the out-of-distribution axis is initial conditions, **not materials**. |

---

## Papapicco et al. 2022 promoted (2026-09-28, audit_citations #13)

Fetched directly: Crossref works/10.1016/j.cma.2022.114687 -> *The Neural Network shifted-proper orthogonal decomposition: A machine learning approach for non-linear reduction of hyperbolic equations*, CMAME **392**:114687 (March 2022); authors Davide Papapicco, Nicola Demo, Michele Girfoglio, Giovanni Stabile, Gianluigi Rozza. VERIFIED for existence, authorship and date only -- the claim cited is that a neural-network shifted-POD predates Zorawski et al. (2024).

---

## Author strings as fetched (B62 recurrence, closed 2026-09-25)

`paper/references.py` refuses to emit any spelled-out given name that does not occur
in this file or in `audit_2026-08-30/citation_verification.md`. Each row below is the
`given | family` list returned by `https://api.crossref.org/works/<DOI>` on 2026-09-25.

| key | DOI | Crossref author list |
|---|---|---|
| wang2025kinn | 10.1016/j.cma.2024.117518 | Yizheng Wang; Jia Sun; Jinshuai Bai; Cosmin Anitescu; Mohammad Sadegh Eshaghi; Xiaoying Zhuang; Timon Rabczuk; Yinghua Liu |
| mendible2020dimensionality | 10.1007/s00162-020-00529-9 | Ariana Mendible; Steven L. Brunton; Aleksandr Y. Aravkin; Wes Lowrie; J. Nathan Kutz |
| knox2016limitations | 10.1021/acs.iecr.6b00516 | James C. Knox; Armin D. Ebner; M. Douglas LeVan; Robert F. Coker; James A. Ritter |
| hastings2024high | 10.1021/acs.jpcc.4c01733 | Jon Hastings; Thomas Lassitter; Zhiling Zheng; Saumil Chheda; J. Ilja Siepmann; Laura Gagliardi; Omar M. Yaghi; T. Grant Glover |
| dodo2000model | 10.1016/S0008-6223(99)00159-1 | D.D. Do; H.D. Do — **initials only**; the bib's "Duong"/"Ha" were expansions (B62) and are removed |
| dodo2009new | 10.1016/j.carbon.2009.01.039 | D.D. Do; S. Junpirom; H.D. Do — same |
| levan2019adsorption | (no DOI; Perry's 9th ed.) | no fetchable byline record; reduced to surnames "LeVan and Carta", the form recorded above |
