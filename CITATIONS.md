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
| SSRN 10.2139/ssrn.6874257, reported title *"Scale-up prediction of breakthrough curves via shape-timescale decomposition in a hybrid deep learning framework"* | ⛔ **BLOCKED** | DOI resolves (302 → `ssrn.com/abstract=6874257`) but SSRN serves a Cloudflare bot check to both WebFetch (403) and the browser. A title search returns only unrelated generic time-series decomposition work — **no breakthrough-curve paper**. Given the title describes shape/timescale separation for breakthrough curves, this is potential **direct prior art on the two-wave warp** and must be read before that section is written. **ACTION FOR THE USER:** open <https://www.ssrn.com/abstract=6874257> in a normal browser and paste the title + abstract. 30 seconds of work; I cannot do it without defeating a bot check. |

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
