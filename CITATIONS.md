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

### How to differentiate from Lee, Lee & Kim (2026) — and why they *help* us

This is the closest prior art the review found, and it lands squarely on the
warp. **"Decompose a breakthrough curve into a normalised shape and a
characteristic timescale, predict each separately, recompose" is no longer a novel
idea and must not be claimed as one.** An adsorption referee will know this paper.

But read what they actually do, and the position is strong rather than weak:

| | Lee, Lee & Kim (2026) | this work |
|---|---|---|
| object predicted | the **exit curve**, 1-D in t | the full **field** c(z,t), 2-D |
| decomposition | shape + **one scalar** characteristic time | shape + **two trajectories** `t_lo(z)`, `t_hi(z)` |
| transfer axis | operating conditions / **scale-up** | held-out **materials**, cluster-robust |
| isotherm | not specified as inflected | **Type V**, which is why one timescale is not enough |
| what is measured | predictive accuracy | the **n-width** in each frame, and the basis/coefficient split |

**The decisive point is that we already tested their decomposition and refuted it
for this system.** A single characteristic timescale is exactly our *single-front*
co-moving frame, and `comoving.py` measured that it makes the representation
**worse**: modes for 99.9 % of training variance go **31 → 102** when aligning on
the 0.5 crossing, and it loses to the fixed frame even when handed the exact front
trajectory for free (0.0534 vs 0.0510). The reason was measured first, not
invoked: with a Type V isotherm the separation between the fast Henry wave and the
cooperative shock spans **40×** across the dataset, so one shift cannot straighten
two waves.

So the honest and much stronger claim is:

> Shape–timescale decomposition of breakthrough curves has been proposed for
> scale-up prediction with a single characteristic time (Lee, Lee & Kim, 2026). We
> show that for a **Type V (inflected) isotherm** that decomposition is
> insufficient — a single alignment *increases* the Kolmogorov n-width from 31 to
> 102 modes and loses to the unwarped frame even given an oracle trajectory — and
> that a **two-trajectory** warp, which removes both the arrival time and the
> transition width, instead collapses the n-width to 13–17 modes and cuts the
> oracle reconstruction error 2.27×.

That is a sharper contribution than "we propose a decomposition", and it is only
available *because* the prior art exists to be tested against.

**Still to do:** read the full 37-page PDF. Two things must be checked before the
warp section is written — (a) whether they consider inflected/Type V isotherms or
multi-wave breakthrough anywhere, and (b) whether the "scaling-based
reconstruction" is a single scalar or something z-dependent. If either answer
differs from the abstract's implication, this table changes.

---

## Queue — not yet verified

Priority order. Nothing below may be cited yet.

1. Abueidda, Pantidis & Mobasher, DeepOKAN, *CMAME* 436:117699 (retraction **A12** rests on this)
2. Shukla, Toscano, Wang, Zou & Karniadakis, *CMAME* 2024 (the KAN anchor, cited in the protocol)
3. McGreivy & Hakim, *Nature Machine Intelligence* 2024 (weak baselines in ML-for-PDE)
4. Li et al. 2025, *RSC Adv* — MOF-303 breakthrough, **the experimental anchor**; open access, geometry matches ours
5. Lassitter et al., *Chem. Eng. Sci.* 285:119430 (2024) — MOF-303 CSFR kinetics, LDF failure at the step
6. Bozbiyik et al. 2017 — Al-fumarate stepped breakthrough
7. Reiss, Schulze, Sesterhenn & Noack — shifted POD (the warp's prior-art lineage)
8. Krah et al., arXiv:2403.04313 — robust multi-transport sPOD
9. Zorawski et al. 2024 — neural sPOD
10. Taddei, *SISC* 2020 (arXiv:1906.11008) — registration ROM
11. Bartolucci et al., ReNO, NeurIPS 2023 — representation equivalence
12. Rohrer et al., *Perspectives on Psychological Science* 2021 — Loss-of-Confidence Project
13. van Genuchten & Alves (1982) — the L0 analytic reference (defect **B10**)
14. Do & Do — the Type V water isotherm form
15. Glueckauf — the LDF coefficient used in dataset design v2
16. … remainder of the ~268 candidates in `audit_2026-08-30/literature_review_raw.json`
