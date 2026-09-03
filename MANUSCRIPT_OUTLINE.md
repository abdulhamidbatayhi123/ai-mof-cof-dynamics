# Manuscript outline — for CMAME, one paper

Drafted 2026-09-03. Every number below points at a results file; nothing here may be
typed into the manuscript by hand (B21). Verdicts still pending: **L2-v2** (sweep
finishing) and **L4b-v2** (queued). The outline is written so that either outcome of
each slots in without changing the story.

## Working title

*What binds a surrogate: a pre-registered falsification ladder for transfer to unseen
materials in MOF adsorption columns*

(Alternatives: "The coefficient map, not the basis"; "Where physical knowledge
belongs in a surrogate".)

## The central claim, one sentence

> For a stiff two-wave adsorption column, the error of a surrogate on a material it
> has never seen is bound by the parameter-to-coefficient map, not by the
> representation; of the standard interventions, only more materials and a change
> of coordinates move it, and the coordinate change is limited by exactly the same
> map.

## Abstract skeleton (numbers from `RESULTS.md`, current)

1. Question: what binds transfer to unseen materials, and which interventions move it.
2. Method: a pre-registered ladder of seven named candidates on a verified reference
   (four closed forms, 0.05 % mass closure), 240 materials, cluster-robust inference
   calibrated at the real cluster count, every null with its MDE.
3. Eliminated: capacity (L2: every optimum bracketed), architecture family (L3: MLP
   beats both KAN families at matched parameters, 6/6), the PDE residual on the
   material axis (L4; L4b-v2 pending), linear-reconstruction operators (L5: DeepONet
   flat in p while the floor falls 28.7×; FNO better by 1.23× but 43× above the
   floor), the kinetic-identification mechanism (L6-v2: Damköhler slope null;
   separate beats joint by 3.7 %, CI 1.0–6.5 %, an inductive bias).
4. Not eliminated: more materials — error still falls as n^−0.22 at 192 materials
   with all of the gain in the coefficient map; and the two-wave coordinate change,
   whose 2.17× headroom is consumed entirely by front-location error.
5. The physics model reproduces a published MOF-303 bed's two-wave breakthrough
   with nothing fitted (t50 303 vs 287 min); two discrepancies named.
6. 25 withdrawn claims and 41 caught defects are reported as a numbered section.

## Sections

1. **Introduction** — the transfer problem, not the speed problem. McGreivy & Hakim
   (weak baselines), Grossmann et al. (PINNs vs FEM); a "design response" paragraph
   mapping each criticism to a feature of this study. Prior art stated up front:
   Poseidon / MPP (held-out physics), MOFSimBench (held-out materials, interatomic
   potentials), Heinlein & Taraz (branch-dominance), Reiss et al. (multi-transport
   sPOD), Lee, Lee & Kim (single-timescale decomposition). A23, A12, B36.
2. **The reference and its verification (L0)** — four closed forms (van Genuchten &
   Alves, not Ogata–Banks: B10), grid convergence, mass closure, the Danckwerts inlet
   (B8). *Fig3.*
3. **The physics that shapes everything** — Type V isotherm with Henry's law (A5,
   B4); the two-wave breakthrough (§6c), cited to Bozbiyik 2017 and Lassitter 2024 as
   established; the 40× separation range. *Fig2.* The solver against Lassitter's bed
   (`PREREG_LASSITTER.md`): reproduces the shape and t50 with nothing fitted; the
   early first wave (isotherm low-RH branch) and the shock width (dispersion closure
   on a 1–2-pellet bed) named. *Fig9, Fig9b.*
4. **Dataset v2 and the statistics** — Sobol, Glueckauf kinetics, Da 8–145 (77.8 %
   in band); why legacy could not test H1 (98.9 % above Da 60); the cluster bootstrap
   over-rejection measured and calibrated (7.0 % vs 32.5 %; α by cluster count);
   `mde.py` and the A22/A25 story; five-fold CV over materials shared by every rung.
   *Fig4 rebuilt.*
5. **The ladder** — one subsection per rung, each with its pre-declared rule, verdict
   in the pre-declared words, CI, and MDE where a null occurred:
   - L1: arms on v2 (MLP best, significant in every fold); the learning curve
     (NOT eliminated; β = 0.222; fixed-basis = refit-basis). *Fig8.*
   - L2: legacy (eliminated, 1 % gain) and v2 (pending; provisional: optimum
     bracketed but depth worth 21 % → capacity's optimum scales with data).
   - L3: final, 6/6, three orders of magnitude apart in learning rate. *Fig6.*
   - L4/L4b: legacy 2×2 (bounded head 11.5×; physics-as-loss hurts once bounded)
     and L4b-v2 (pending: sweep, NTK, SA, refinement, polish).
   - L5: DeepONet flat, DeepOKAN collapses (10/45), FNO 1.23× better and 43× above
     the floor; the seven-channel FNO. *Fig7 rebuilt.*
   - L6: legacy null with its MDE (~70 %); v2 (mechanism refuted, 3.7 % uniform
     benefit, MDE 4 %).
   - L7: classical forms beaten 3.7× on v2 (3.2× legacy); "a classical model wins
     exactly when the physics it assumes is the physics that is there".
6. **The mechanism** — basis vs coefficient-map error in the optimal basis, the
   oracle-rank calibration, per-mode R², and its sample-size scoping (A21; the v2
   curve). Heinlein & Taraz differentiated on the four axes in `CITATIONS.md`. *Fig10.*
7. **The coordinate change** — single-front alignment refuted under an oracle;
   two-wave alignment (an established transformation, sPOD/registration family:
   B36) collapses the n-width 31 → 13; the honest arm ties the fixed frame; the
   oracle sizes the 2.17× headroom; monotonicity is not the lever (B34); B41 on
   why the 0.05 level is degenerate on v2. *Fig11.*
8. **Corrections and retractions** — numbered section, not an appendix: the
   25 Part-A and 41 Part-B entries, grouped by class (split drift, normalisation
   by a vanishing quantity, undertrained arms scored, power simulations, citation
   errors), with the three that reversed headline verdicts (A17, A18, A25) told
   in full. Rohrer et al. 2021 on disclosed self-correction.
9. **Limitations** — one PDE family; the isotherm's low-RH branch; C_ps uncited
   (band); the Ruthven closure's validity range; the 12-cluster legacy CIs; no COF
   measurement exists (say so; do not invent one); the solver-vs-experiment vs
   surrogate-vs-solver error budget in those words.
10. **Reproducibility** — git-timestamped pre-registrations (which ones are
    verifiable and which are self-attested), `validate.py`, pinned versions, the
    resume protocol.

## Figure list (target: 10, column width, Type 42 fonts)

| # | content | status |
|---|---|---|
| F1 | the ladder as a schematic: rung, hypothesis, verdict, CI, MDE | to draw after L2/L4b |
| F2 | the two-wave physics and the 40× separation | rebuild from Fig2 |
| F3 | L0 verification | exists (Fig3) |
| F4 | dataset v2 coverage and Da distribution | rebuild (B27) |
| F5 | L1–L3 eliminations with CIs | rebuild from Fig5/6 |
| F6 | the mechanism | **Fig10, done** |
| F7 | L5 flat-in-p with FNO | rebuild from Fig7 |
| F8 | the learning curve on v2 | **Fig8, done** |
| F9 | the two-wave warp | **Fig11, done** |
| F10 | the solver against Lassitter's bed | **Fig9/9b, done** |

## Citations to verify before drafting (beyond the 41 already verified)

Kneip & Gasser 1992 (landmark registration — B38); Ohlberger & Rave 2016 (n-width
of transport; the 2013 note is verified PARTIAL); Nair & Balajewicz 2019; Mendible
et al. 2020; Zucatti & Zahr 2025; Taddei 2020 erratum; Rohrer et al. 2021;
Poseidon (Herde et al. 2024) and MPP (McCabe et al. 2024); MOFSimBench; Ruthven's
dispersion correlation (original source); Bruggeman (for the post-hoc closure);
Glueckauf 1955 (PARTIAL → full); Do & Do 2000 (PARTIAL → full); LeVan & Carta
(Perry's, verified); Lanthaler et al. 2023 (verified); Heinlein & Taraz (verified).
