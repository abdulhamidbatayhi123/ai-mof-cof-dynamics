# Referee report, round 2: "What binds a surrogate" (revised manuscript)

Reviewed: `paper/manuscript.tex` (1819 lines), with macros resolved through `paper/numbers.tex`. I read the round-1 report and `REVISION_PLAN.md` and then judged the revision independently. Line numbers refer to `manuscript.tex` unless another file is named. Quotes are kept under 15 words.

"Verified" means I checked the claim against the named source file (results JSON, script or figure). "UNVERIFIED" means I did not.

Known items, not raised again:
- L5-v2 DeepONet 24k re-run (PREREG_L5_v2 A2)
- L4 verdicts withdrawn pending re-run (A28/B72)
- affiliation placeholder
- venue and length

**Overall.** The revision is substantial and mostly in good faith. The Methods section (l.490-752), the water-MOF placement, the selection-adjusted intervals, the refinement result and the two-wave scoping all fix real problems.

The revision has introduced a new class of defect: the withdrawn L4 result is still used as evidence in several places, and most visibly it is drawn as a significant benefit in the headline figure. Several round-1 fixes were also made in one place but not in the others that repeat the same claim.

Recommendation: minor-to-major revision. The changes needed are mostly text and one figure rebuild, plus one cheap analysis.

---

## 1. Round-1 MAJOR issues: status

| # | Status | Evidence (lines) |
|---|---|---|
| M1 mechanism vs operator numbers | **Partially resolved** | The four-learner comparison is now in the abstract, Section 5 and the conclusions (l.49-51, l.1212-1214, l.1722-1727). Two problems remain. (a) l.1198 still calls GB "a strong regressor". (b) l.1073-1076 claims "the reconstruction, not the capacity, separates these families". The paper's own numbers undercut (b): DeepONet (0.0265) beats POD+GB (0.0509) by 1.9x, and both use linear reconstruction. That gap is larger than DeepONet vs FNO (1.23x). See N6. |
| M2 warp "powered" / FNO matches oracle | **Partially resolved** | (a) "Nothing at all" is gone, and the interval is now stated in relative terms (l.1352-1355). But "powered" survives in the Fig. 6 caption (l.1266) and the subsection title (l.1319). (b) The FNO comparison is now made (l.1360-1361, l.1480-1484). However, it contradicts the new Methods rule "Absolute errors are not comparable across rungs" (l.700). See N5. |
| M3 selection on the test set | **Partially resolved** | A max-statistic interval is given for L4 and L2 (l.839-841, l.985-993, l.1559-1579). It is not given for the L5 FNO-vs-DeepONet comparison or for the L3 learning-rate choices, although REVISION_PLAN B1 says the L5 adjustment was done: there is no L5 selection macro in `numbers.tex`. Nested selection (C1) is still OPEN. l.1563 also misdescribes the scope (N4). |
| M4 refinement result unreported | **Resolved** | l.998-1019. The result is now inside the withdrawn rung, and l.1018-1019 over-reads it (N1). |
| M5 contradictions / stale prose | **Mostly resolved** | Fixed: the "eliminated" list (l.1471-1484); "five modes" (no occurrences left); "the one rung" (l.1088-1091); [PENDING] (l.877); the no-hand-typed claim, narrowed at l.1778-1787. Still hand-typed: results such as "all six pairwise comparisons significant" (l.859) and "\(6/6\)" (l.904). These are not covered by the stated exemptions. |
| M6 L6 Da null | **Resolved in text, not in the figure** | Text: l.1099-1109, l.1149-1153, l.1709-1712. But the Fig. 1B panel title still reads "the PRIMARY estimand, refuted: the benefit does not depend on Damköhler" (`fig_ladder.py`, verified in `figures/Fig1_ladder.png`). |
| M7 Methods | **Largely resolved** | l.490-752. Still missing: the L1/L2 perceptron architecture, learning rate, epochs and early-stopping rule. The only architecture statement is in the cost section, "three 256-unit layers" (l.1419-1420). The L1 "field subsampled" resolution is not given (l.718). The legacy dataset's ranges are given only as differences (l.586-590). |
| M8 three designs; L4/L7 in abstract | **Partially resolved** | Fixed: l.690 now says "Three evaluation designs", and the abstract names all three (l.43-44). But l.456 still says "Two designs, two levels, both stated", and l.458 assigns L5 to the legacy design, while Table 2 runs "L5 basis vs. map" on the five-fold design (l.736). |
| M9 L2 optimum moves | **Resolved in L2, reintroduced in the conclusions** | Fixed at l.849-853. Reintroduced at l.1699-1700: "with an optimum that moves with the number of training materials". |
| M10 framing / prior art / real MOFs | **Partially resolved** | Fixed: the title (l.29-31), the ROM/PSA prior art (l.156-167; bib keys verified present) and the water-MOF placement (l.592-622). Still open: "unseen materials" survives in the keywords (l.62), and "We find no operator-learning study ... held-out materials" (l.172-173) still rests on the relabelling. |
| M11 missing baselines | **Not resolved** | There is still no GP, no coarse solver and no fitted L7 (C2-C4 OPEN). The cost section now measures the query cost r (l.1424-1427), which answers round-1 minor 11 only. The abstract (l.53) still says "closed forms are 3.73 times worse than learning" without saying the closed forms are un-fitted. |
| M13 weak anchor | **Partially resolved** | The wording is fixed: "compared", "an anchor and not a validation" (l.41-42, l.202-205). The second anchor is blocked (C5). |
| M12 two-wave on v2 | **Resolved** | l.343-350, l.1676-1685. |
| M14 FNO margin fragile | **Partially resolved** | l.1059-1062 now calls the margin "marginal". But l.1063 still says "It is the direction the theory predicts", and Fig. 1A labels it "NARROWED, not removed" as a significant blue bar. No selection-adjusted interval is given. |

---

## 2. New issues introduced or exposed by the revision

### N1. The withdrawn L4 results are still used as evidence (verified)
This is the most serious new problem.

**(a) Fig. 1A, the headline figure, draws L4b as a significant benefit.**
- What the figure shows: a blue bar at about +8 %, labelled "PHYSICS HELPS once correctly weighte[d]" (truncated), in `figures/Fig1_ladder.png`.
- Why: `fig_ladder.py:138-153` gates only on the `L4B_V2_EXT2_DONE` marker. That marker is present in `chain_l4b_v2_ext2_outer.log` (count 1). The script has no A28 or withdrawal handling.
- Timing: the PNG/PDF are timestamped 13:40 on 2026-10-04, which is after the A28 commit (18123e7, 12:55). So the figure was rebuilt after the withdrawal and still draws the result.
- Fix: draw the L4b row as "WITHDRAWN (A28), re-run pending", with no bar. Add a test that fails if any withdrawn rung draws a bar.

**(b) l.994-996 still interprets the withdrawn result.**
- Quote: "the reading we defend is the modest one --- the residual is a weak regulariser".
- l.993 also says "the effect survives its own selection".
- Both contradict l.926-928 ("none of it may be read as physics helps").
- Fix: delete both sentences, or restate them as "the residual this rung used".

**(c) l.1018-1019 generalises beyond the withdrawn residual.**
- Quote: "pulls the prediction away from the data rather than towards the physics".
- Two lines earlier the text says the result is "no evidence about the right one".
- Fix: delete the sentence.

**(d) l.1563-1574 uses L4 as the showcase for the selection correction.**
- l.1563-1564: "For the one positive result that rests on such a choice".
- l.1573: "The L4 result survives it".
- Fix: lead with L2 as the worked case, and mention L4 only as a pending application of the procedure.

**(e) l.961-968: interpretive reading of the withdrawn polishing result.**
- Quote, l.968: "under the optimiser the physics arm needs, the data-only arm gains more".
- Fix: report the polished numbers without the reading.

### N2. Fig. 1 labels contradict the text on three rungs (verified in the PNG)
- **L2.** The figure says "ELIMINATED as an unbounded lever". l.828 says "capacity is NOT ELIMINATED".
- **Title.** "seven named candidates, the one survivor": l.1475 and l.1697 list at least two levers that are not eliminated.
- **Warp.** The figure says "HEADROOM 2.17x" (`\nWarpHeadroom`, against predicted fronts). The text's headline is 2.27x against the fixed frame. l.1347-1349 says explicitly that 2.27x is the quantity the reader wants.

Fix: regenerate the labels from the same pre-declared verdict strings the text uses, and plot 2.27x.

### N3. "Two designs" survives next to "Three evaluation designs" (verified)
- l.456: "Two designs, two levels, both stated".
- l.690: "Three evaluation designs are used".
- l.458 puts L5 on the legacy design; Table 2 l.736 runs "L5 basis vs. map" on the five-fold design.
- l.1668-1670 ("Three rungs ... smaller dataset") omits the 48-material split.

Fix: rename the paragraph at l.456 to "Three designs, their levels"; add the single split; say "L5 operators" at l.458.

### N4. "The one positive result that rests on such a choice" is false (l.1563)
Other positive results also rest on best-of-grid selection on the held-out materials:
- the FNO "significantly better" (l.1057; both arms are grid minima, `analyze_l5_fno.py`);
- the L3 6/6 (each family at its best learning rate);
- the L3 best-KAN audit pair, where "the better of two higher learning rates per seed" (l.873) is again test-set selection (UNVERIFIED in code).

Fix: apply the same studentised max-statistic bootstrap to FNO vs DeepONet over the full grid of both arms. This is cheap and runs on the existing per-sample errors. Then rewrite l.1563 to list every affected comparison.

### N5. Cross-rung comparison against the new Methods rule (l.700 vs l.1360-1361, l.1480-1484)
- l.700 says "Absolute errors are not comparable across rungs", and Table 2 lists L5 and Warp as different rows.
- l.1360 and l.1480 then compare FNO 0.0216 with the oracle warp 0.0220.

I checked the code. The comparison appears legitimate:
- `warp_verdict.py` and `run_l5.py` both use the 128x128 subsample of c (`comoving.py:51`: "identical to run_l5.subsample()").
- Both use the legacy split.
- Whether the `nrmse` functions are identical is UNVERIFIED.

The paper does not say any of this. Fix: add a footnote to Table 2: "L5 and Warp share one encoding (128x128 c, same split); their absolute errors are directly comparable". Or remove the comparison.

### N6. "The reconstruction, not the capacity, separates these families" is undercut by the paper's own table (l.1073-1076 vs l.1722-1727)
- Two linear-reconstruction methods, POD+GB (0.0509) and DeepONet (0.0265), differ by 1.9x.
- Linear vs nonlinear reconstruction (DeepONet vs FNO) differs by 1.23x.
- So most of the 2.4x "learner lever" is a property of jointly trained versus per-mode regression, not of nonlinear reconstruction.

This also changes the abstract's framing at l.50-51, which credits the 2.4x to the FNO.

Fix:
- Rephrase l.1073-1076 as "at matched parameters, with a fraction of the channels".
- In the abstract, state that DeepONet already captures 1.9x of the 2.4x.

### N7. The POD floor is called a "bound" for the FNO (l.1066, l.1704-1706, l.1728-1729)
- Quotes: "a bound 43x below it is a dent" (l.1066); "still sits 43x above what the basis could represent" (l.1729).
- l.1052-1053 itself says the FNO "escapes that bound through nonlinear reconstruction". The p=128 POD floor is therefore a reference level for the FNO, not a lower bound.

Fix: say "43x above the p=128 linear-reconstruction floor, a reference level the FNO is not bound by".

### N8. Stale text that contradicts the revised conclusions
- **l.1376-1377.** "the remaining headroom is raw predictive accuracy, which points at material count rather than at architecture". The revised l.1480-1484 and l.1736-1738 now say the learner is a lever as large as materials. Fix: "...points at the front predictor: more materials or a better learner".
- **l.188-189.** "we trace it to a measurable physical cause". The n-width cause is withdrawn (A17, l.1248), and the two-wave cause is scoped to legacy (l.347-350). Fix: delete the phrase, or name the cause and its scope.
- **l.1506 vs l.1536.** "three of them reversed headline verdicts" against the heading "Four that reversed a headline", which then lists five items (B69, B72/A28, A17, A22, A25). Fix: count once and use one number.
- **l.1455-1457.** "the surrogate is the only option that finishes". This is unsupported on the paper's own numbers: 16.6 worker-s per solve (`\nCostSolveSec`) means 10^5 solves is about 460 core-hours, which is feasible. Fix: "the option that finishes soonest, at 3.5 % nRMSE", until the coarse-solver baseline (M11a) exists.
- **l.1028.** The heading "L5 --- you need an operator" reads as a finding, while the rung's result is that operators dent but do not escape. Fix: "L5 --- does an operator remove the wall?".

### N9. Number and definition mismatches
- **13 vs 17 modes at 192 training materials** (l.812 / l.1233 vs l.1227).
  - The learning curve says 13 modes clear R^2 > 0.2 at 192 materials.
  - The v2 bottleneck says "about 17" at the same 192 training materials per fold.
  - The difference is regressor and basis (MLP at 64 modes vs GB at p=128), but no sentence reconciles them.
  - Fix: one sentence naming the regressor and basis for each.
- **"Best of 26 configurations" (l.840) vs "28 configurations" (l.819).**
  - `l2_v2_selection.json` has k = 26, reference mlp_depth/d3; the gap is presumably the duplicated L1 configuration (l.1791). Fix: say so.
- **Damköhler definition clash.**
  - Glossary l.117-118: "ratio of the adsorption-kinetics rate to the time scale". This is dimensionally confused (a rate times a time is not a ratio of these), and it says large Da means near-equilibrium.
  - Methods l.572-577: Da = k_LDF t_final, which carries the horizon-extension factor for 52 % of runs. So a large Da can mean a long horizon rather than fast kinetics.
  - Fix: glossary "product of the kinetic rate constant and the simulated duration (Section 4)", and note the extension caveat in the L6 scope paragraph (l.1111-1128).
- **"Material" defined as 11-D** (l.163-164).
  - Quote: "a 'material' is a point in an eleven-dimensional space of isotherm, kinetic and bed parameters".
  - Table 1 (l.635-648) has 8 material plus 3 operating parameters; kinetics are derived, not sampled (l.417-419, l.542-548); and l.582-584 crosses materials with conditions.
  - Fix: "a material is a point in an eight-dimensional space (Table 1); a sample adds three operating conditions".
- **L4 refinement sweep sign** (l.1015). The quote "best change found ... is -0.2 %" has no sign convention: is -0.2 % an improvement or a degradation? (UNVERIFIED which.) Fix: say "a 0.2 % reduction" or "increase".

### N10. Notation clashes
- **`n` has four meanings:**
  - cooperativity exponent (eq. 1, Table 1);
  - number of training materials (n^-0.222, l.45, l.797);
  - mode count (n-width, n^-2.45, l.1239);
  - number of screening queries (eq. 10, l.1409).

  Fix: n for the Sips exponent; N_mat, k (modes) and N_q.
- **ε_t is called both "bed porosity" (Table 1, l.643) and "total porosity" (l.1658).**
  - This is not cosmetic. If ε_t is total porosity (including intraparticle porosity), then the solid term (1-ε_t)ρ_p in eqs. 3 and 5, with ρ_p the *particle* density, double-counts the pellet void.
  - Fix: define ε_t once (interbed vs total) and check eqs. 3-5 against it.
- **Velocity.** v is superficial in Methods (l.502), but Limitations writes D_L = 0.7 D_m + 0.5 d_p u (l.1593) with u undefined; Methods uses v/ε_t (l.541). Fix: define u = v/ε_t once.
- **R** is both the retardation factor (Table l.258) and the gas constant (l.305). Use R_f for the retardation factor.
- **Inlet condition wording (l.524-528).** The prose says "the inlet face carries no dispersive ... flux", but the displayed equation contains -D_L ∂c/∂z. Fix: "the total flux entering equals the feed's advective flux".

### N11. Claims about MOF chemistry that a reticular chemist would dispute
1. **l.287-288.** "Water uptake ... is negligible until a threshold relative humidity".
   - This contradicts the paper's own f_H range of 0.03-0.25 (Table 1) and the MOF-303 Henry plateau at 0.267 of feed (l.379).
   - It also contradicts the anchor finding that the model holds *too little* water below the step (l.1653-1654).
   - Fix: "small below a threshold RH (up to a quarter of capacity in some frameworks), then...".
2. **l.316-317.** "``Type~V'' is likewise our own label on IUPAC grounds; the modelling literature calls this family Type~IV."
   - "Type V" appears nowhere else in the manuscript (grep), so "likewise" refers to nothing.
   - The Type IV attribution is uncited.
   - Most MOF water papers describe MOF-303/MOF-801/CAU-10 isotherms as S-shaped, Type V (IUPAC 2015); Type IV is used for mesoporous frameworks (e.g. MIL-100/101).
   - Fix: "S-shaped (IUPAC Type V) isotherm, as for MOF-303 [cite]", and drop the Type IV clause.
3. **Table 1, ΔH from -60 to -38 kJ/mol.**
   - With q_st = -ΔH + RT (l.306), the upper end gives q_st of about 40.5 kJ/mol, which is below water's enthalpy of vaporisation (about 44 kJ/mol at 298 K).
   - Physisorptive pore filling of water in these frameworks is reported at or above the latent heat (roughly 45-60 kJ/mol).
   - Fix: either justify the lower edge or note that part of the sampled space is unphysical for water (reviewer judgement; the literature values were not checked here).
4. **l.594-595: placement on four axes omits the cooperativity exponent n.**
   - n (step steepness) is the single most diagnostic framework property for a harvester.
   - Fix: add n from the cited isotherms, or say why it was not placed.
5. **l.520-521 vs l.305 and l.1655-1656: what a "material" is.**
   - The cluster affinity is "set per run so that the cooperative step sits at the material's step humidity at the feed temperature".
   - So the same "material" has a different b_C0 at each feed temperature. Its isotherm family is not a fixed object across conditions, which a chemist will read as "one material" in Table 1.
   - Fix: state this explicitly in the Methods and in Table 1's caption, and in the l.1655 limitation (the step RH is invariant across T_in by construction).

### N12. Smaller items
- **l.1059 vs l.1057.** "The margin is marginal" immediately follows "significantly better". Fix: "is better (interval excludes zero by a margin that is small next to either error)".
- **Abstract l.43-44.** It promises "with the design it rests on" for each verdict, but L3, the FNO 2.4x and the warp 2.27x (all legacy) are not labelled, while the 90x floor drop next to them is v2. Fix: add "(12-material legacy design)" after the L3, FNO and warp clauses.
- **Abstract l.53.** Fix: "un-fitted closed forms are 3.73 times worse".
- **l.243, l.481, l.985, l.1229.** Lab-notebook register remains: "A 1982 bulletin predicted the defect", "has the scar to prove it", "rather than leave for a referee", "which we learned the hard way". Fix: cut.
- **Fig. 1C.** It mixes absolute errors and fractional errors on one log axis (the tracer is "abs", the others are %). Fix: label units per bar.

---

## 3. Clarity for a materials-chemistry reader (e.g. the Yaghi group): the five places most likely to lose them

1. **Abstract, l.45-51.** "the basis floor falls 90x with basis size while the parameter-to-coefficient map moves 0.9 %: the map binds, not the basis" means nothing to a chemist, and no absolute accuracy is ever stated.

   *Rewrite:* "The surrogate predicts a breakthrough field to about 3 % (nRMSE) for a framework it has not seen. Its error is limited by how well it learns the link from isotherm and pellet properties to the shape of the breakthrough, not by its ability to draw that shape: improving the drawing ninety-fold changes the error by under 1 %."

2. **Section 3.2, l.321-334, Henry region in concentration fractions.** The quotes "reaches 10^-0.9 of the feed at best" and "K_H ... mol/kg per mol/m^3" use units a chemist does not use.

   *Rewrite* in relative humidity and g/g: "For a median material the near-linear uptake regime ends at about 1 % of the feed humidity; for a third of materials it ends below 10^-6 of it, so in practice they show no linear region at all."

3. **Methods, l.519-522 and Table 1: what a "material" is.** A chemist reads "material" as a framework. Here it is eight numbers, one of which (the step) is re-anchored per operating temperature, and capacity is given in mol/kg.

   *Rewrite* the Table 1 caption: "A 'material' here is a set of eight numbers describing an idealised framework pellet (the isotherm's capacity, step position, steepness, low-humidity fraction and heat, plus pellet size, density and packing). Capacity 8-30 mol/kg corresponds to 0.14-0.54 g water per g. The step is re-anchored at each feed temperature so that it sits at the stated relative humidity."

4. **Sections 4.5 and 5, l.1028-1256: DeepONet, FNO, oracle rank, n-width.** These are four new concepts in two pages with no picture.

   *Rewrite:* open Section 5 with a three-sentence plain-language summary and one schematic.

   > "Every model here builds a breakthrough field either as a sum of stored template shapes (DeepONet, POD + regressor) or by learning the field directly (FNO). We ask whether the templates or the recipe for mixing them limits accuracy. The recipe does: perfect templates would be fifty times better than any recipe we can learn."

5. **Statistics, l.448-487 and l.673-686: "calibrated α", "empirical size", "percentile cluster bootstrap", "MDE".**

   *Rewrite:* add one boxed paragraph.

   > "Several breakthroughs share one material, so they are not independent. We therefore resample whole materials. We set the significance threshold so that, in simulations where no real effect exists, we falsely claim one at most 2-5 % of the time. For each 'no difference' we state the smallest effect the test could have detected."

---

## 4. The three highest-value remaining changes before a preprint

1. **Purge the withdrawn L4 from evidence, and rebuild Fig. 1 from the text's own verdicts.**
   - Fix N1(a)-(e) and N2.
   - Add a figure-level gate: a withdrawn rung draws no bar, labels come from the pre-declared verdict strings, and the Fig. 1B title is softened to match l.1099-1109.
   - As it stands, the first figure a reader sees displays a withdrawn positive result, a capacity verdict opposite to the text's, and a refuted Damköhler dependence. A referee who opens the PDF at Fig. 1 will stop trusting the paper there.

2. **One consistency pass on every claim the revision changed in only one place.** This is text only, about a day's work:
   - "Two designs" (l.456)
   - "powered" (l.1266, l.1319)
   - the L2 optimum in the conclusions (l.1699)
   - "points at material count" (l.1376)
   - "physical cause" (l.188)
   - three vs four reversals (l.1506/l.1536)
   - 13 vs 17 modes
   - 26 vs 28 configurations
   - "material = 11-D" (l.163)
   - the Damköhler glossary
   - ε_t and n notation
   - "the reconstruction, not the capacity" (N6)
   - the POD floor called a bound for the FNO (N7)
   - "only option that finishes" (l.1455)
   - the Type V sentence and "negligible below the step" (N11)
   - the L5/warp shared-encoding footnote (N5)

3. **Close the selection gap on the remaining positive results, and run the cheapest missing baseline.**
   - Apply the existing max-statistic bootstrap to FNO vs DeepONet and to the L3 learning-rate selections (N4). This uses existing per-sample errors and is minutes of CPU.
   - Queue the already-implemented GP-on-POD regressor (C2). It directly tests whether the 1.9x gap between POD+GB and DeepONet is a property of the per-mode regressor, which is now the paper's central mechanistic claim (N6).
   - If CPU allows, a coarse-grid solve at matched nRMSE (C3) would replace the near-tautological break-even with a decision-relevant one.
