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

`refs/Lee2026_shape_timescale.pdf`, 37 pp. This is the closest prior art the review
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
