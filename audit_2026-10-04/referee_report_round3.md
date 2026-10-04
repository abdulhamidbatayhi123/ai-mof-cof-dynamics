# Referee report, round 3: "What binds a surrogate"

**What I reviewed**
- `paper/manuscript.tex`, 1917 lines, at HEAD 6956ee6.
- Macros resolved through `paper/numbers.tex`.
- Results files checked: `results/l5_fno_selection.json`, `results/l3_selection.json`, `results/l5_oracle_rank.json`, `results/l5_bottleneck_v2.json` and `results/l5_fno.json`, plus `analyze_l5_selection.py`.
- Figure checked: `figures/Fig1_ladder.png`.
- Ledger entry checked: `RETRACTIONS.md` B75.

Line numbers refer to `manuscript.tex` unless another file is named. "Verified" means I checked the claim against the named file. UNVERIFIED means I did not.

**Overall.** The round-2 revision is careful and mostly complete:
- The withdrawn L4 result no longer serves as evidence anywhere I could find.
- Fig. 1 now matches the text's verdicts.
- The FNO's "significantly" is withdrawn, and B75 pays for selection on both sides.

The main remaining defect repeats the pattern B75 fixed. The same selection correction cut L3 from 6/6 to 4/6, but the abstract, Section 4.3 and the conclusions still state L3 as unqualified 6/6 / "every comparison". A second, smaller contradiction runs through the conclusions: "architecture family is not the lever" sits next to "the learner lever is 2.4x". Neither problem needs new computation.

Recommendation: **minor revision** (text only, plus one figure label).

---

## 1. Status of round-2 items

### N-items

| Item | Status | Evidence (current lines) |
|---|---|---|
| N1(a) L4b drawn as a benefit in Fig. 1 | **RESOLVED** | The PNG shows the L4b row as "WITHDRAWN (B72) — re-run in flight" with no bar or interval. |
| N1(b) "the reading we defend ... weak regulariser" / "survives its own selection" | **RESOLVED** | grep finds neither phrase. l.1036-1039 now scopes the selection result to "the residual this rung used and ... the procedure". |
| N1(c) "pulls the prediction away from the data" | **RESOLVED** | The phrase is gone. l.1048-1050 now reads "no evidence about the right one". |
| N1(d) L4 as the worked case of selection correction | **RESOLVED** | l.1647-1651: "The worked case is L2". L4 appears only as a pending application. |
| N1(e) interpretive reading of polishing | **RESOLVED** | l.1010-1012: "with the residual this rung used, they carry no reading about physics". |
| N2 Fig. 1 labels (L2, title, warp) | **RESOLVED** | The PNG shows L2 "NOT ELIMINATED", the title "seven named candidates and what the evidence said", and "HEADROOM 2.27x over the fixed frame". |
| N3 "Two designs" | **RESOLVED** | l.477: "Three designs, their levels, all stated"; l.481: "L5's operator comparisons". l.1765-1767 still omits the 48-material split, which is acceptable now that L4 is withdrawn. A residual inconsistency is new item m3. |
| N4 "the one positive result that rests on such a choice" | **PARTIAL** | The sentence is gone. L5 and L3 are now adjusted (l.1098-1109, l.1652-1657). Three gaps remain: (i) the L3 best-KAN audit pair (l.915-921, "the better of two higher learning rates per seed") is still unadjusted, and it is the pair Fig. 1A draws for L3; (ii) the 2.4x / 1.9x "learner lever" ratios (abstract l.52-54, l.1819-1824) compare best-of-grid arms with no interval; (iii) the abstract and conclusions were not brought in line with the L3 adjustment (Major 1). |
| N5 cross-rung FNO vs oracle warp | **PARTIAL** | Licensed at l.1554-1558. Still unqualified: l.736 ("**Absolute errors are not comparable across rungs.**") and the Table 2 caption (l.744, "Absolute errors in different rows are not comparable"). l.1554 says "This is the one place we compare absolute errors across rungs", but l.1427-1428 makes the same comparison in Section 6. The exception should be footnoted in Table 2. |
| N6 "the reconstruction, not the capacity, separates" | **RESOLVED** | l.1122-1126: "Most of the learner lever is therefore training the basis and the coefficients together". The abstract gives DeepONet 1.9x (l.54). |
| N7 POD floor called a bound for the FNO | **RESOLVED** | l.1113-1115 and l.1826-1827: "a reference level it is not bound by". |
| N8 stale text | **RESOLVED** (one residue) | Fixed: l.1442-1444 "more training materials or a better learner"; "physical cause" is gone (grep); l.1524-1527 "The solver still finishes"; l.1070 heading "does an operator remove the wall?"; l.1580 "four" matches the l.1610 heading "Four". The residue is cosmetic item c1. |
| N9 numbers and definitions | **RESOLVED**, with a new defect exposed (Major 3) | 13 vs 17 is reconciled (l.1296-1299); 26 vs 28 (l.877-879); Damköhler glossary (l.121-124) and the scope note (l.1160-1163); "material" is no longer 11-D (l.169-171); sweep sign (l.1058-1059, "negative means the error fell"). |
| N10 notation | **MOSTLY RESOLVED** | Fixed: u defined (l.526, l.1672); ε_t is interparticle (l.542-544), so eqs. 3 and 5 are consistent with ρ_p as pellet density; R_f (l.257, l.266); N_mat, k, N_q. Still open: (i) eq. 11 (l.1480) introduces lowercase \(n_{\mathrm{train}}\), a fifth "n" (the number of training *simulations*); (ii) l.1317 writes the Ohlberger bound as "½ N^{-1/2}" with N as the mode count, where the text uses k; (iii) the inlet wording at l.550-552 ("the inlet face carries no dispersive or conductive flux") is unchanged next to an equation containing −D_L ∂c/∂z. That wording is defensible as a finite-volume face statement but reads as a contradiction (**PARTIAL**). |
| N11 chemistry | **RESOLVED** | (1) l.295-297 "small below a threshold" with the f_H range. (2) l.325-326: no IUPAC type asserted. (3) l.1737-1745: heat-range limitation. (4) l.637-641: n not placed, with the reason. (5) l.660-662 and l.1747-1753: re-anchored step. |
| N12 smaller items | **RESOLVED** | l.1098-1102: no "significantly ... marginal". Abstract labels the legacy set (l.49, l.52, l.58) and says "un-fitted" (l.56). Lab-notebook phrases are gone (grep for "hard way", "scar", "1982 bulletin": no hits). Fig. 1C labels each bar's error kind (PNG). |

### Section 3 clarity items

| Item | Status | Evidence |
|---|---|---|
| 1 Abstract for a chemist | **RESOLVED** | l.44-52 give the absolute accuracy (3.5 %) and the plain-language "link from isotherm and pellet properties to the field". |
| 2 Henry region in humidity units | **RESOLVED** | l.342-346. |
| 3 What a "material" is | **RESOLVED** | Table 1 caption, l.656-665, with g/g. |
| 4 Plain-language opening of Section 5 | **PARTIAL** | The text is added (l.1246-1252). The schematic was not. |
| 5 Plain-language statistics | **RESOLVED** | l.457-463. |

### Section 4 priorities

| Priority | Status | Evidence |
|---|---|---|
| 1 Purge L4, rebuild Fig. 1 | **RESOLVED** | |
| 2 Consistency pass | **RESOLVED** except the items listed above | |
| 3 Selection gap and missing baselines | **PARTIAL** | Selection adjustment is done for L5 and L3, but L3's adjustment did not propagate (Major 1). GP-on-POD (C2) and coarse-solver (C3) baselines are still absent. l.1526-1527 says the coarse-solver baseline "is a baseline we report separately", but no such result is in the manuscript or in `results/` (no coarse-solver JSON found). |

---

## 2. New or remaining problems

### MAJOR

**Major 1. L3 is still stated as 6/6 / "every comparison" after its own selection correction left 4/6. This is the B75 pattern applied to one rung and not the other.**

Verified in `results/l3_selection.json`: `n_sig_per_pair = 6`, `n_sig_simultaneous = 4`. The two pairs that fail are both RBF-KAN at the larger budgets:
- 200k: sim interval [−0.00136, +0.02805];
- 800k: sim interval [−0.00293, +0.02903].

The text correctly reports 4/6 at l.901-902 and l.1655-1656. The following places still read as the unadjusted result:
- **Abstract, l.48-49:** "A perceptron beats Kolmogorov--Arnold networks at matched size in every comparison (legacy set)."
- **l.947-948:** "with every competitor optimum bracketed, the perceptron wins \(6/6\)". This is also a hand-typed result, which contradicts the l.1876 claim "No result in this manuscript is typed by hand".
- **l.1770:** "The architecture ordering of L3 is large and consistent across budgets". Against RBF-KAN at 200k and 800k, the gap is about 0.013 nRMSE and is not significant once selection is paid for.
- **Conclusions, l.1797-1799:** "a perceptron beats both Kolmogorov--Arnold families on held-out materials in every comparison, so the premise ... is refuted".

The L5 FNO lost "significantly" for the same reason. Consistency requires the same treatment here.

Fix: say "beats both families in every comparison by point estimate; 4 of 6 survive paying for the learning-rate choice, all Chebyshev comparisons and the smallest RBF budget". Replace "6/6" with the macros. Soften l.1770 to "large against the Chebyshev family; against the Gaussian-RBF family at the two larger budgets, not significant once selection is paid for". The refutation of the premise still stands: no comparison reverses.

**Major 2. "Architecture family is not the lever" contradicts "the learner lever is not small" in the same Conclusions section and in Section 7.**

- l.1796-1797: "Architecture family is not the lever either".
- l.1818-1819: "How well the map is learned also depends on the learner, and that lever is not small" (2.4x, l.1823).
- l.1543-1544: "Architecture family and the basis size of a linear-reconstruction operator cost fit time and nothing else".
- l.1550: "The choice of operator moves the accuracy without moving the data cost".

The FNO, DeepONet and POD+GB are architecture families, so read literally these sentences contradict each other. The text means the *per-edge basis* (KAN vs MLP at matched size), as it says precisely at l.145-146 ("a richer per-edge basis").

Fix: replace "Architecture family" with "A richer per-edge basis (Kolmogorov--Arnold vs perceptron)" at l.1543 and l.1796.

**Major 3. "Only the first 5 modes are predicted at all (R²>0.2)" disagrees with the results file, and the 5 and the 17 it is set against are different statistics.**

The text:
- l.1066 (Fig. 4 caption) and l.1264-1266: "only the first \nLfiveLeadModes\ modes are predicted at all (\(R^2 > 0.2\)), and the median \(R^2\) of the remaining \nLfiveTailModes ...".
- `\nLfiveLeadModes` = 5 is read from `mode_r2_p128.leading_predictable_run` (`paper/numbers.py:255`). That is the length of the leading *contiguous* run.

The same JSON (`results/l5_oracle_rank.json`) shows:
- modes with R² > 0.5: [1, 3, 4];
- modes with 0.2 < R² < 0.5: [2, 5, 9, 13, 18, 60].

So **9** modes clear R² > 0.2, not 5, and modes 9, 13, 18 and 60 are inside the "remaining 123" whose median is quoted.

The v2 figure is a different statistic:
- `\nLfiveVtwoModes` = 17 (l.1289) is a *count* (`summary.128.modes_r2_gt_0.2` in `l5_bottleneck_v2.json`).
- `\nLCmodesLarge` = 13 is also a count (`modes_r2_gt_0.2`).

The reader is therefore shown 5 (a run), 13 (a count) and 17 (a count) as like quantities. The reconciliation at l.1296-1299 names the learner and basis but not this definitional difference.

The conclusion, that a small leading set is predictable and the tail is not, survives. The sentence as written is factually wrong.

Fix: "the leading 5 modes, and 4 isolated later ones, clear R² > 0.2; the median of the rest is ...". Alternatively, report the legacy count (9) next to the v2 count (17).

### MINOR

**m1. Fig. 1A's L3 row is unadjusted and comes from a selected pair. B75 says otherwise.**
- What the figure draws: the PNG's L3 row is "strongest KAN vs MLP, matched parameters" at about −10 %, CI about [−20, −1.6] %. This is `\nLthreeBestKanDiff` with interval [−0.0115, −0.0009], i.e. the audit pair of l.915-921.
- Why it is a selected pair: its arms are "the better of two higher learning rates per seed", chosen on the test materials.
- The ledger: `RETRACTIONS.md` B75 says "Figure 1 now draws the selection-adjusted interval for L2, L3's note and L5". No L3 selection note is visible in the PNG.
- Fix: draw the matched-budget selection-adjusted result, or annotate the row "per-pair; 4/6 matched pairs survive selection".

**m2. The Fig. 1 caption (l.799-800) says "Nulls carry their minimum detectable effect".**
- In the PNG the MDE ticks sit on L2 and L6, both *significant* results.
- The nulls (L5 basis, L5 FNO-once-selected, warp predicted) carry none.
- The caption also does not mention the withdrawn L4b row.
- Fix: either the caption or the figure.

**m3. The design of the L5 basis-vs-map decomposition is stated two ways.**
- l.477-479: "L5's basis-versus-map decomposition run on the 240-material folds". Table 2's "L5 basis vs. map" row says "larger, five-fold" (l.772).
- Section 5's main numbers, however, are legacy: l.1279-1281 says "The numbers above were measured on the legacy held-out set". These include the 28.7x floor drop, 0.0515 → 0.0510, the oracle ranks, the 5 lead modes, and the POD+GB 0.0509 used for the 2.4x/1.9x levers.
- The legacy decomposition has no row in Table 2.
- Fix: add it, and say "both designs" at l.478.

**m4. The learner lever is called "comparable" to the learning curve's lever in one place and "larger than" it in another.**
- l.1275-1276 calls 2.4x "a lever comparable to the learning curve's"; l.1823-1824 calls it "larger than the 1.88x".
- The 2.4x is legacy (12 held-out materials, best-of-grid on both ends, no interval); the 1.88x is v2. Comparing them is a cross-design ratio comparison that the l.736 rule discourages.
- Fix: pick one word, and say the two ratios come from different designs.

**m5. "The best learner of all" (l.1252) and "the best of them" (l.1825) name the FNO.**
- After B75 the FNO is not distinguishable from DeepONet.
- Fix: "the most accurate learner by point estimate".

**m6. l.1260 still reads "with a strong regressor".** This is round-1 M1(a), never addressed. Name it: gradient boosting.

**m7. "Four that reversed a headline" (l.1610) is ambiguous after B75.**
- The paragraph counts B69, B72/A28, A17 and A22, says A25 is "not ... a fifth".
- It then adds B75, which removed a significance claim from a headline comparison.
- Fix: say explicitly whether B75 counts.

**m8. The coarse-solver sentence at l.1526-1527 implies a result exists.** It says "is a baseline we report separately". Nothing is reported in the manuscript, and I found no coarse-solver result in `results/`. Fix: "is a baseline not yet run".

**m9. Abstract and practitioner paragraph: "For a framework it has never seen" (l.44-45) and "unseen frameworks" (l.1834).**
- The held-out units are idealised eight-number parameter sets, not real frameworks. The title, Table 1 caption and l.169-171 say so correctly.
- A chemist will read "framework" as a synthesised MOF.
- The keyword "transfer to unseen materials" (l.66, round-1 M10) is also unchanged.
- Fix: "for an adsorbent parameter set it has never seen".

**m10. Hand-typed result numerals despite l.1876 ("No result in this manuscript is typed by hand").**
- l.948 "6/6" is a result (Major 1).
- Design-count numerals are covered by the stated exemption and are acceptable: "240" (l.466, l.810, l.816, l.1767), "12 → 192", "96 → 192" (l.830-832), "48" (l.822, l.1768).

### COSMETIC

**c1.** l.1001-1003 still calls L4 "the clearest case in this paper of a pre-registered rule changing a result". This is about the procedure and is acceptable, but the changed result (B69) was itself measured with the wrong residual. Add "on the residual then in use".

**c2.** Fig. 1C: the white in-bar labels for the tracer and retarded-front bars ("advection, dispersion, the Danckwerts inlet"; "isotherm coupling, the equilibrium limit") overflow the short bars and are unreadable against the white background. Fig. 1B: the slope annotation overprints data points.

**c3.** Fig. 1A: L7 is labelled "ELIMINATED — learning is justified". The double negative (the candidate "a closed form suffices" is eliminated) is correct but reads oddly next to a blue "reduces the error" bar. Consider "CLOSED FORMS ELIMINATED".

**c4.** l.1015 "In the pre-declared words the analyser reports that physics helps". Even with the scope that follows, quoting "physics helps" for a withdrawn rung invites selective quotation. Consider "the analyser's pre-declared positive verdict".

---

## 3. Checks that came out clean (verified)

**L5 selection numbers.** `l5_fno_selection.json` matches the text:
- k = 204 = 34 × 6;
- q = 3.72 (text \nLfiveSelQ = 3.7);
- simultaneous interval [−0.00176, +0.01152], which includes zero;
- per-pair interval [+0.00015, +0.00984];
- FNO 0.02157, DeepONet 0.02646.

The Fig. 1A L5 row (about +18 %, about [−6.6, +43.6] %) matches `selected_rel_lo/hi_pct`. The text does not overstate the JSON. "Excludes zero by a small fraction of either error" (l.1101-1102) is accurate.

**L3 selection.** `l3_selection.json`: k = 281, q = 3.76, 4/6 simultaneous, and no reversal (all mean differences favour the MLP). l.901-902 and l.1655-1656 match.

**Ratios.**
- 0.0509 / 0.0216 = 2.36, consistent with \nOperatorLever 2.4.
- 0.0509 / 0.0265 = 1.92, consistent with \nONetLever 1.9.
- 2^(1/1.23) = 1.76, consistent with \nNwidthHalving.
- L4 material gain: (0.0231 − 0.0213) / 0.0231 = 7.8 %, consistent with "8 %".
- Capacity conversion: 8 and 30 mol/kg × 18.015 g/mol = 0.14 and 0.54 g/g. Co₂Cl₂(BTDD) 54 mol/kg = 0.97 g/g, 1.8 × 30.

**Fig. 1A bars.**
- L1: 0.00534 / 0.0402 = 13 %.
- L6: 0.0021 / 0.0562 = 3.7 %.
- L7: 0.1295 / 0.1769 = 73 %.
- Oracle warp: 0.02802 / 0.05005 = 56 %.
- Warp label 2.27x.
- Fig. 1B title "no detectable dependence ... (a weak null)" matches l.1150.

**Section references.** l.1109 (sec:corrections), l.1537 (sec:mechanism), l.1654 (sec:ladder) and l.1660 all point to the right sections.

**The ε_t fix.** Eqs. 3 and 5 with interparticle ε_t and pellet ρ_p are self-consistent. The Glueckauf group ρ_p K is dimensionless.

**The q_st identity.** q_st = −ΔH + RT holds at every loading: both terms need b·c constant on an isostere, and c = p/RT.

---

## 4. For a reticular-chemistry reader (e.g. the Yaghi group)

1. **The feed humidity can sit below the step (UNVERIFIED how often).**
   - Feed RH spans 0.15-0.85 and step RH 0.08-0.45 (`\nDcRH*`, `\nDcStep*`). A sample with, say, feed 0.20 and step 0.40 never reaches pore filling, so its breakthrough is a single Henry/primary-site front, not the two-wave structure the paper builds on.
   - The rejection screen ("feed loads too little ... of capacity", l.589) may remove most of these, but the paper does not say how many accepted samples have feed RH < step RH.
   - A chemist will ask, because a harvester is operated above its step by design. State the fraction, or confirm the screen excludes them.
2. **Steepness near n = 1 is not a step.** Table 1 samples n from 1 to 6 (l.675), and l.333 says "n > 1 strictly". For n close to 1 the cooperative term is nearly Langmuir, and the isotherm is not S-shaped in any sense a chemist recognises, yet the paper calls the family "S-shaped, or stepped" (l.325-326). Say what fraction of materials has n below about 1.5, or describe the lower end as "weakly cooperative".
3. **Refusing the IUPAC type label (l.325-326).** It is defensible under the paper's citation rule, but a MOF reader expects "Type V" for MOF-303/CAU-10/Al-fumarate water isotherms. One clause would help: "commonly described as Type V in the MOF water literature". This needs a retrieved citation, e.g. the Thommes et al. 2015 IUPAC report, which the commit message says could not be fetched (UNVERIFIED).
4. **"Henry-branch leak" (l.377, l.392).** The early effluent plateau in MOF-303 is uptake on the low-RH (primary/defect) sites. Calling it the "Henry branch" is the paper's model language, not a chemist's. The glossary (l.125-127) defines it, but Fig. 7's caption should say "low-humidity (primary-site) uptake".
5. **"For a framework it has never seen" / "unseen frameworks"** (m9). This is the sentence most likely to be read as a claim about real MOFs. No real framework's isotherm was ever a held-out test case.
6. **Temperature behaviour.** Re-anchoring the step per feed temperature (l.546-547, l.1747-1753) is now disclosed. A chemist will add that for most of the placed MOFs the step position in RH is nearly temperature-invariant over 288-313 K (the characteristic-curve behaviour), so the re-anchoring may be *closer* to real behaviour than the Limitations paragraph implies. Literature values were not checked (UNVERIFIED). The paragraph currently says "In a real framework it shifts" without a magnitude; cite one.

---

## 5. Summary of required changes, in priority order

1. Propagate the L3 4/6 result to the abstract (l.48-49), l.947-948, l.1770 and the conclusions (l.1797-1799), and make "6/6" a macro (Major 1, m10).
2. Replace "architecture family" with "a richer per-edge basis" at l.1543 and l.1796 (Major 2).
3. Correct "only the first 5 modes are predicted at all", or relabel the macro as a leading run, and reconcile it with the counts 13 and 17 (Major 3).
4. Bring the Fig. 1 L3 row and the Fig. 1 caption in line with B75 and with what the figure draws (m1, m2).
5. Make the Table 2 / l.736 comparability rule carry its stated exception, and add the legacy decomposition row (N5, m3).
6. Make the remaining wording fixes: m4-m9 and the chemistry items 1, 2 and 5.
