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
