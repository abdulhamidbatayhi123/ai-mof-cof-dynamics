# prose

paper/manuscript.tex (1009 lines, identical to HEAD 3e6c960) is a well-organised but unfinished manuscript with one hard LaTeX build failure, at least four hand-typed numbers that contradict the macros beside them, a duplicated phrase and a duplicated sentence, and five figures plus one table that no sentence ever references. Structurally it has no Conclusions and no Discussion, and it never once states an inference cost, wall-clock time or amortised cost — the premise of a CMAME surrogate paper — despite the Introduction promising exactly that measure at line 82. Its most exposed claims are the abstract's "Six are eliminated" (rung L4 is literally "[SECTION PENDING]"), three headline verdicts computed on twelve clusters at a confidence level the paper never states, and two nulls that violate the paper's own rule that "every null reported below carries a minimum detectable effect".

## 1. [blocking] paper/manuscript.tex:457 (and paper/numbers.tex:52)

**What.** Line 457 uses \nLtwoBestFam, which numbers.tex defines as \newcommand{\nLtwoBestFam}{mlp_depth}. The raw underscore is expanded in text mode: "The best configuration anywhere is \nLtwoBestFam/\nLtwoBestCfg\ at \nLtwoBest".

**Why.** An unescaped `_` in text mode is a hard LaTeX error ("Missing $ inserted"). The document does not compile. build_paper.py checks for undefined macros, bare numerals and de-backslashed macros, but never checks that a macro's *value* is LaTeX-safe, so the gate reports success on a manuscript that cannot build.

**Fix.** Escape at generation time in paper/numbers.py: emit `mlp\_depth`, or better, map family identifiers to prose ("the depth sweep of the multilayer perceptron") and add a LaTeX-special-character check (`_ % & # $ ^ ~`) to the SPEC writer so any future string-valued macro is caught.

## 2. [blocking] paper/manuscript.tex:41 vs 513-515

**What.** The abstract asserts "Six are eliminated." Section 5.4 (L4) reads in full: "\textbf{[SECTION PENDING --- L4b-v2 is running. Its verdict text is \nLfourbVerdictMaterial\ on the material axis and \nLfourbVerdictTime\ on the time axis...]}", and both macros are defined as \textbf{[PENDING]} in numbers.tex.

**Why.** Seven candidates minus one not-eliminated (materials) = six, so the abstract's count necessarily includes L4, whose verdict the manuscript does not have and prints as [PENDING] on the page. A referee opening the PDF sees the abstract claim a result the body says is still running. This alone is a desk reject.

**Fix.** Either hold the submission until L4b-v2 lands, or restate the abstract as "Five of seven are eliminated; the physics-residual rung is reported as a design and an invalidation, not a verdict" and demote §5.4 to a design-and-scope subsection with no PENDING placeholder.

## 3. [blocking] paper/manuscript.tex:549 vs 566

**What.** Line 549: "At \(p = 128\) it sits fifty-five times above its own lower bound." Line 566 says of the same quantity: "DeepONet sits \(\nONetxFloor\times\)", and \nONetxFloor is 53 (0.0265 / 5.02e-04 = 52.8).

**Why.** Two different values for one quantity, seventeen lines apart, one of them hand-typed as an English word. The manuscript's own header comment (lines 5-9) declares "A bare numeral in the prose is a build failure", and B43 is cited as the reason. Spelling the number as a word defeats build_paper.py's NUMERAL regex (`\d+`) entirely, so the gate that exists to prevent exactly this passed it.

**Fix.** Replace "fifty-five times" with \(\nONetxFloor\times\). Then extend build_paper.py's check with a word-number scanner (one|two|...|ninety, hundred, thousand, half, third, twentieth, thousandths) so spelled-out results cannot bypass the numeral gate.

## 4. [blocking] paper/manuscript.tex:569-572

**What.** "At the highest mode count the Fourier operator is \emph{\nLfiveFNOwidth\ channels wide} and still matches the best DeepONet found anywhere, which has width 216. A nonlinear reconstruction with a twentieth of the channel count matches the best linear one." Two errors: (a) 28/216 is one seventh, not a twentieth; (b) \nLfiveFNOwidth is `fno_best.width` where results/l5_fno_verdict.json records fno_best.modes = 4, the LOWEST mode count swept (by_modes has 4, 8, 16), not the highest.

**Why.** The arithmetic is wrong by a factor of ~2.7 on the sentence the manuscript itself calls "the clearest single piece of evidence in the rung". Worse, the caveat at lines 576-581 states that width falls as modes rise (O(w^2 m^2)), so the width at the highest mode count is necessarily smaller than 28 — the sentence contradicts the caveat two paragraphs below it. "216" is also hand-typed and allow-listed in build_paper.py as "an architecture description" when it is plainly a result of the sweep.

**Fix.** Rewrite as "The best Fourier operator uses \nLfiveFNOmodes\ modes at \nLfiveFNOwidth\ channels and beats the best DeepONet found anywhere, whose width is a macro read from the L5 sweep", state the ratio as a derived macro, and move 216 out of ALLOWED into numbers.py SPEC.

## 5. [blocking] paper/manuscript.tex:672-673

**What.** "Training basis and coefficients together is worth a constant\na constant factor and nothing more." The phrase "a constant" is duplicated across the line break.

**Why.** A duplicated phrase in the concluding sentence of the mechanism section — the section that carries the paper's central claim. It reads as an unproofed draft.

**Fix.** Delete one "a constant": "...is worth a constant factor and nothing more."

## 6. [blocking] paper/manuscript.tex:605

**What.** "...The direction has flipped, and the earlier number is not quoted here because it belongs to a design that could not test the estimand at all. The direction has flipped." The clause "The direction has flipped" opens the sentence and is then repeated as a standalone sentence at the end.

**Why.** A sentence repeated verbatim inside a single line, in the paragraph reporting L6's sign reversal — the one place a referee will read most carefully, because a reversed sign against an earlier dataset invites the charge of selective reporting.

**Fix.** Delete the trailing "The direction has flipped." and keep only the opening clause.

## 7. [blocking] paper/manuscript.tex:n/a (whole document; sections listed at 70, 151, 212, 322, 385, 644, 696, 809, 865, 959)

**What.** The section list is: Introduction, The reference and its verification, The physics..., Dataset splits and statistics, The ladder, What binds the error, The coordinate change, Corrections and retractions, Limitations, Reproducibility, then unnumbered Data availability and Competing interest. There is no Conclusions section and no Discussion section.

**Why.** CMAME manuscripts are expected to close with conclusions. More substantively, the paper's central claim ("the error is bound by the parameter-to-coefficient map, not the representation; only more materials and a coordinate change move it") is stated once in MANUSCRIPT_OUTLINE.md line 18-22 and never assembled anywhere in the manuscript. A reader who finishes §9 Limitations and §10 Reproducibility has never been told, in one place, what the seven rungs jointly establish.

**Fix.** Add \section{Conclusions} after §8 Limitations (before Reproducibility) carrying: the one-sentence central claim from MANUSCRIPT_OUTLINE.md, the eliminated/not-eliminated tally as a list, the relocation of the obstruction from the coefficient map to the two front curves, and the two concrete next measurements (L3/L5/warp on 240 materials; a front-locating model held to the 2.17x prize).

## 8. [blocking] paper/manuscript.tex:81-82

**What.** The Introduction states: "so a synthetic study can only measure accuracy per unit inference cost, or accuracy from less information." Grepping the entire file for cost, speed, amortis*, wall-clock, runtime, throughput, seconds, GPU/CPU returns no measurement anywhere. The only other hits are "the spectral weights cost O(w^2 m^2)" (577) and "halving the error costs about 23x more materials" (428).

**Why.** This is the single strongest objection a CMAME referee will raise, and it is self-inflicted: the paper names accuracy-per-unit-inference-cost as one of only two admissible measures for a synthetic surrogate study, then measures the other one exclusively. A surrogate that is 109x above the POD floor (line 421) is only interesting if it is cheap; the paper never says how cheap. There is no solver wall-clock, no surrogate inference time, no break-even sample count, no statement of the screening scenario's economics — despite the Introduction opening (73-77) framing the entire paper as a screening case for "thousands" of curves.

**Fix.** Add a subsection to §2 (The reference and its verification) reporting: solver wall-clock per breakthrough curve at N_z = \nGridNz on the recorded hardware; surrogate inference time per curve; the ratio; and the number of curves at which the amortised cost of dataset generation + training is repaid. All four as macros from a new results file. Then add one abstract sentence giving the ratio, and one Limitations sentence bounding it to the recorded hardware.

## 9. [major] paper/manuscript.tex:373, 380-382 vs 545-546 and 770

**What.** §4.3 is titled "Every null carries its minimum detectable effect" and asserts (380-382) "Every null reported below carries a minimum detectable effect computed by a single, self-tested implementation from the real paired differences." Two nulls below carry none: L5's flat-in-p null (545-546, "interval [\nLfiveFlatLo, \nLfiveFlatHi], which spans zero") and the warp rung's null (Table 2 line 770, "no difference"). \nLtwoDepthMDE (5.0) and \nLtwoXgbMDE (2.0) are defined in numbers.tex and never used anywhere in the manuscript.

**Why.** The paper makes a compliance promise in a section heading and violates it twice, and the unused MDE macros are the evidence that the MDEs exist and were dropped. A22 is cited five lines earlier (376-378) as the retraction that resulted from exactly this omission. A referee who checks one thing will check this.

**Fix.** Report the MDE for L5's flat-in-p null and the warp predicted-vs-fixed null in the same form as L6 (\nLsixMDE), and use \nLtwoDepthMDE / \nLtwoXgbMDE in §5.2 where the capacity nulls are stated.

## 10. [major] paper/manuscript.tex:45-47 and 545-550

**What.** The abstract's third headline is "Linear-reconstruction operators are eliminated: DeepONet is flat in basis size". The supporting interval is [\nLfiveFlatLo, \nLfiveFlatHi] = [-0.00585, 0.00491] against a DeepONet base of \nLfiveONet = 0.0265. The interval therefore admits an improvement of up to 22.1 % from p = 8 to p = 128.

**Why.** The paper reports a 21.3 % gain (\nLtwoVsLonePct, line 458) as a real, decisive capacity effect. So "flat" is being claimed on an interval that admits an effect the paper elsewhere treats as material. Combined with the missing MDE, the headline elimination is an unpowered null stated as a positive finding — precisely the A22 error the paper says it corrected.

**Fix.** State the MDE and the interval in relative terms in the body ("the interval excludes improvements larger than 22 %, and the MDE at 80 % power is X %"), and soften the abstract to "DeepONet does not improve with basis size over a sixteenfold range; the test excludes improvements above 22 %".

## 11. [major] paper/manuscript.tex:367-371 vs 471, 481, 560-562, 771, 950-951

**What.** The only calibrated level in the paper is line 369: "\(\alpha = \nAlphaFolds\) at \nNclustFolds\ clusters" (0.02 at 240). Line 367 states the 12-cluster over-rejection (\nFprLegacyNominal = 8.5 % at nominal 5 %) and then never gives the remedy. L3 (471, 481), L5 (560-562) and the warp rung (771) are all on twelve clusters (stated at 950-951) and all report intervals called "significant", with no confidence level stated anywhere in the manuscript. results/calibration_v2.json records legacy.alpha = 0.01 and legacy.mde_at_80pct = 0.5; \nAlphaManifest and \nNclustManifest are defined in numbers.tex and never used.

**Why.** Three of the paper's headline results rest on a level the manuscript does not disclose, on the cluster count the manuscript itself flags as over-rejecting by 70 % relative. Worse, the calibration file says the 12-cluster design has an 80 %-power MDE of a 50 % effect — a fact nowhere in the manuscript, and one that makes L5's FNO interval [0.00035, 0.00978] (lower bound 0.7 % of base) look extremely fragile. A referee who requests the calibration file will find the number the paper omitted.

**Fix.** State the confidence level of every interval once in §4.2, add the legacy calibrated level (\alpha = 0.01 at 12 clusters, its empirical size) using the already-defined \nAlphaManifest/\nNclustManifest, and add the legacy 80 %-power MDE to the Limitations paragraph at 950-956.

## 12. [major] paper/manuscript.tex:779 and 57

**What.** Line 776-779: "The honest arm does \emph{not} beat the fixed frame. But the oracle gap is significant and large: given the true front trajectories, the same proper-orthogonal-decomposition-plus-regressor arm is \nWarpHeadroom{}\(\times\) better." \nWarpHeadroom = 2.17 is read from results/warp_verdict.json `headroom_to_oracle` = 2.1655, which is two_wave (predicted, 0.047704) / two_wave_oracle (0.022029) — the oracle against the PREDICTED arm. Against the fixed frame, the sentence's stated comparator, the ratio is 0.05005/0.02203 = 2.27.

**Why.** The sentence's only antecedent is "the fixed frame" (776), so the number is attached to the wrong comparator, and the abstract repeats it (57: "buys a significant \nWarpHeadroom{}\(\times\) under an oracle and nothing at all under a predictor", where "buys" is necessarily relative to not applying the coordinate change, i.e. the fixed frame). This is a headline number in the abstract computed against a denominator the prose does not name.

**Fix.** Either name the comparator explicitly ("the oracle two-wave arm is \nWarpHeadroom{}x better than the predicted two-wave arm") or add a derived macro for fixed/oracle and use that in the abstract, where the comparator is the fixed frame.

## 13. [major] paper/manuscript.tex:664

**What.** "The coefficient-map error, with a strong regressor, moves from \nLfiveCoefSmall\ to \nLfiveCoefLarge\ --- flat to four decimal places." The two macros are 0.0515 and 0.0510. They differ at the third decimal place; they are equal only to two decimal places.

**Why.** A directly checkable false statement, sitting between the two numbers it misdescribes, in the paragraph that establishes the paper's central mechanism. A referee reads "0.0515 to 0.0510 --- flat to four decimal places" and stops trusting the arithmetic elsewhere.

**Fix.** "...moves from \nLfiveCoefSmall\ to \nLfiveCoefLarge --- a change of under one per cent across a sixteenfold change in basis size", with the one-per-cent figure as a derived macro.

## 14. [major] paper/manuscript.tex:428 vs 430-432

**What.** Line 428: "At that exponent, halving the error costs about \(\nLCmaterialsForHalving\times\) more materials" (23x). Lines 430-432: "\textbf{Verdict, in the pre-declared words: the materials axis is NOT ELIMINATED at the largest size available.} We claim no extrapolation beyond twice the measured range."

**Why.** The sentence immediately preceding the no-extrapolation pledge extrapolates 23-fold — from 192 materials to roughly 4,400. The disclaimer is falsified by the sentence it follows. Given that A18, A21 and A26 (listed at 828-831) are all "a property measured at one sample size, stated as intrinsic", this is the paper's own recurring error class committed in the paragraph that announces it.

**Fix.** Either move the halving statement inside the scope ("within the measured range, each doubling of materials buys X") or label it explicitly: "Extrapolated at the fitted exponent — outside the range we claim — halving the error would cost about 23x more materials."

## 15. [major] paper/manuscript.tex:176, 191, 192, 198

**What.** Line 176 "closure improved to \(\nMassClosure\,\%\)" and line 198 "Global mass balance closes to \(\nMassClosure\,\%\)" both render as "0.0 %". Table 1 rows 191 and 192 render "\nLzeroRetarded\,\%" and "\nLzeroThermal\,\%" as "0.0 %". The underlying values are 0.0497 % (results/validation.json, whose own evidence string reads "closes to 0.050%"), 0.0272 % and 0.0123 % (verify_solver.json).

**Why.** Two of the four rows in the solver verification table — the table the whole paper's credibility rests on — print an error of exactly "0.0 %", which reads either as a broken macro or as an implausible claim of exact agreement. The one-decimal `pct` format in numbers.py destroys the information at the exact place the paper needs it most.

**Fix.** Give the verification and mass-closure keys a format with enough significant figures (e.g. "{:.3f}" or a two-significant-figure formatter) in paper/numbers.py, so Table 1 reads 0.027 % and 0.012 % and the closure reads 0.050 %.

## 16. [major] paper/manuscript.tex:80-81

**What.** "A surrogate cannot beat its own reference on accuracy --- the reference is exact by construction ---"

**Why.** The reference is not exact by construction; it is a finite-difference solver whose errors §2 measures and tabulates (Table 1, grid convergence \nGridConv % at N_z = 2000, mass closure 0.050 %). The manuscript spends its second section establishing that the reference is verified rather than exact, and asserts the opposite in its second paragraph. A referee will quote this back.

**Fix.** "...the reference defines the target, so a surrogate can at best match it ---" or "...the reference is the definition of correctness in this study ---".

## 17. [major] paper/manuscript.tex:39-41 vs 302-311

**What.** Abstract: "tested on a reference solver verified against four closed-form solutions and against a published MOF-303 packed-bed breakthrough curve with nothing fitted." Body: nRMSE \nAnchorNrmse = 0.128 "against \nAnchorNrmseComsol" = 0.069 for the authors' own COMSOL model (304-305), and the first wave arrives at \nAnchorTfiveModel = 1.7 minutes against \nAnchorTfiveExp = 86 measured (310-311) — a fiftyfold error.

**Why.** "Verified against" is doing work the numbers do not support. The model is 1.9x worse than the reference publication's own model and mislocates the first breakthrough by a factor of 50; §9 (933-938) concedes "The isotherm's low-humidity branch is wrong". The abstract's word choice invites the reviewer to check, and the check fails. Line 306-307 compounds it: "the cited isotherm predicts it" — quantitatively it does not.

**Fix.** Abstract: "...and compared, with nothing fitted, against a published MOF-303 packed-bed breakthrough curve, which it reproduces in shape and 50 % arrival time but not in first-wave timing." Line 306-307: "the cited isotherm produces the two-wave structure, though not its first-wave timing".

## 18. [major] paper/manuscript.tex:684-686

**What.** "The Kolmogorov \(n\)-width of this snapshot family is algebraic, \(n^{\nNwidthExpC}\) with \(R^2 = \nNwidthRtwoC\) over \(n = 8\)--64, so halving the error requires \(\nNwidthHalving\times\) the modes permanently." This renders as n^{-2.45} and 1.76x. But 2^(1/2.45) = 1.33, not 1.76. paper/numbers.py line 305-306 computes NwidthHalving as 2**(1/abs(NwidthExpC/2)) = 2^(1/1.225) = 1.76, while its own docstring says "2^(1/|algebraic exponent|)".

**Why.** The exponent quoted in the prose and the halving factor quoted in the same sentence are inconsistent by a factor of two in the exponent — the -2.45 is evidently an energy/singular-value-squared decay, not the error decay, but the sentence labels it "the Kolmogorov n-width", which IS the error. The code comment and the code also disagree. Any referee who recomputes 2^(1/2.45) finds the mismatch immediately.

**Fix.** Say which quantity decays as n^{-2.45} ("the POD energy spectrum decays as n^{-2.45}, so the n-width decays as n^{-1.23}"), and correct the DERIVED docstring in paper/numbers.py to match the code.

## 19. [major] paper/manuscript.tex:690-693

**What.** "For transport-dominated problems the slow decay is established --- Ohlberger and Rave prove a \emph{lower} bound of \(\tfrac12 N^{-1/2}\) for linear advection with jump discontinuities, which is a bound and not a rate, and we state it that way." This is placed immediately after the paper's own measured decay (n^{-2.45}, or n^{-1.23} on the corrected reading).

**Why.** Both readings of the measured exponent decay strictly faster than the cited N^{-1/2} lower bound. Juxtaposed with no reconciliation, this reads as either a violated theorem or an incomparable quantity smuggled in as support. The reconciliation is straightforward — dispersion smooths the fronts, so the jump-discontinuity hypothesis does not hold here — but the paper does not say it, and this is the exact mechanism the paper needs to explain why the n-width bound is "real and inactive" (689).

**Fix.** Add one sentence: "Our fields are dispersion-smoothed rather than discontinuous, which is why the measured decay is faster than the jump-discontinuity bound and why the bound, though real, is inactive here."

## 20. [major] paper/manuscript.tex:597-598

**What.** "over \nLsixDaDecades\ decades spanning kinetically-controlled to near-equilibrium operation". \nLsixDaDecades = 1.35, and the per-material Damköhler range is \nDaMatMin--\nDaMatMax = 7.7 to 173 (line 348).

**Why.** Kinetic control means Da well below 1. The dataset never goes below Da = 7.7; the entire 1.35-decade range sits on the fast-kinetics side. The primary pre-registered hypothesis — that separating the kinetic object pays most where kinetics dominate — is therefore refuted over a range that arguably never enters the regime where the effect was predicted. This is the strongest attack on L6's central negative result and the manuscript does not pre-empt it at all.

**Fix.** Replace with "over \nLsixDaDecades\ decades of the informative band (Da \nDaMatMin--\nDaMatMax)", and add a sentence to §5.6 or §9 conceding that Da < 1 was not sampled and that the refutation is scoped to Da above the informative band's lower edge.

## 21. [major] paper/manuscript.tex:793-794 vs 770

**What.** Line 792-794: "projecting onto the constraint set changes \(R^2\) by nothing to three decimal places and makes the reconstruction significantly \emph{worse}: \nMonoRawNrmse\ against \nMonoProjNrmse" — 0.04770 against 0.04812, a difference of 0.00042, reported with NO confidence interval. Table 2 line 770 reports a difference of \nWarpPredDiff = 0.00235, 5.6 times larger, as "no difference" with CI [-0.00812, 0.01183].

**Why.** The paper calls a 0.00042 difference significant while calling a 0.00235 difference no difference, on the same dataset and the same twelve clusters, and gives an interval only for the second. As written the significance claim is unsupported and directly contradicted by the neighbouring table.

**Fix.** Report the monotonicity comparison's interval and test in the same form as Table 2, or drop the word "significantly" and state only the point difference and its sign.

## 22. [major] paper/manuscript.tex:45-48 and 56-58 vs 950-956

**What.** The abstract states three results unconditionally: "Architecture family is eliminated" (L3), "Linear-reconstruction operators are eliminated... A Fourier neural operator... is significantly better" (L5), and "a change of coordinates which collapses the \(n\)-width... buys a significant \nWarpHeadroom{}\(\times\) under an oracle" (warp). §9 line 950-954 says: "L3, L5 and the coordinate change are measured over twelve held-out materials... those three verdicts must be read as scoped to the material count at which they were taken."

**Why.** The Limitations section walks back exactly the three verdicts the abstract states without qualification — and does so citing A26, the paper's own retraction of a verdict that did not survive four times the materials. This is the abstract/limitations inconsistency a referee will name first, because the paper hands them the argument.

**Fix.** Carry the scope into the abstract in one clause: "...eliminated on the smaller twelve-material design", or move the L3/L5/warp scope statement forward into §5's opening paragraph so it governs every verdict that follows rather than appearing 400 lines later.

## 23. [major] paper/manuscript.tex:812-813 vs 979-980

**What.** Line 812-813: "\nLedgerB\ further defects were caught before they contaminated a reported number." Line 979-980: "defect B43 found three quoted comparisons --- one of them the basis of a retraction --- that had no script behind them at all." Line 498-499 records B46 as an earlier draft citing two papers for a consensus that does not exist; line 328 records B27 as a published figure that "showed no training points at all".

**Why.** The framing claim about the Part-B ledger is contradicted three times by the manuscript's own descriptions of Part-B entries. B43's numbers reached a document and were the quantitative basis of a retraction — that is contamination by any reading. Since the correction ledger is presented as an evidential asset (819-824), an overstatement inside it costs more than it saves.

**Fix.** "...\nLedgerB\ further defects were caught and corrected, most of them before they reached a reported number" — and name B43 as the exception in the same sentence.

## 24. [major] paper/manuscript.tex:636-638

**What.** "In a previous project on cyclic heat conduction --- linear and time-invariant, so a Green's function is the exact solution operator --- a 128-number linear convolution beat every deep operator." No citation, no data, no reference to any repository or results file; "128" is hand-typed and allow-listed in build_paper.py.

**Why.** This unpublished, unciteable anecdote is the sole evidence offered for the paper's stated "transferable statement" — "a classical model wins exactly when the physics it assumes is the physics that is there" (634-636). A CMAME referee cannot check it and will ask that it be removed or cited. In a manuscript whose §10 says "Nothing is cited until it has been retrieved", an uncited private result carrying a generalisation is conspicuous.

**Fix.** Either cite the previous project (preprint, repository, or dataset DOI) or delete the sentence and let the L7 numbers carry the claim without it.

## 25. [major] paper/manuscript.tex:n/a (labels at 329, 405, 654, 705, 764)

**What.** Five floats are labelled but never referenced by any \ref: fig:dataset (Fig2_dataset, line 329), fig:rungs (Fig3_rungs, 405), fig:mechanism (Fig5_mechanism, 654), fig:warp (Fig6_warp, 705), tab:warp (Table 2, 764). Only fig:anchor, fig:ladder, fig:operators and fig:anchorposthoc are cited in the text. figures/FigS1_learning_curve.pdf exists on disk and is not included at all.

**Why.** Five of seven figures and one of two tables float free of the prose. Elsevier production and most referees treat an uncited float as an error; more practically, the reader is never told when to look at the learning-curve panel, the mechanism panel or the warp panel, so the figures do no work. Table 2 in particular carries the warp rung's entire quantitative result and no sentence points at it.

**Fix.** Add \ref calls at the natural points: fig:dataset in §4.1 (line 334), fig:rungs in §5.1/§5.2/§5.3, fig:mechanism at line 662, fig:warp at line 748, and Table~\ref{tab:warp} at line 756-757 where the table is introduced.

## 26. [major] paper/manuscript.tex:420-421 vs 547-548

**What.** "the proper-orthogonal-decomposition floor" names two different numbers. Line 420: "The proper-orthogonal-decomposition floor is \nLonePodFloor" = 2.80e-04 (v2, 240 materials, 64 modes/channel). Line 547-548: "its own proper-orthogonal-decomposition floor falls from \nLfiveFloorSmall\ to \nLfiveFloorLarge" = 1.44e-02 to 5.02e-04 (legacy, 12 materials, p=128). The derived ratios 109x and 86x use the first; 43x and 53x use the second.

**Why.** A floor at 128 modes (5.02e-04) that is higher than a floor at 64 modes (2.80e-04) is impossible on the same data, so the two are different datasets — but the manuscript uses the same definite phrase "the floor" for both and never says so. §6 "What binds the error" then mixes them, quoting \nFloorDrop (legacy, 672) alongside \nLCmodesSmall/\nLCmodesLarge (v2 learning curve, 678-679). A reader cannot reconcile 109x with 53x.

**Fix.** Qualify every use: "the v2 floor at 64 modes per channel" vs "the legacy floor at p = 128", and add one sentence in §6 stating which dataset each quantity in that section comes from.

## 27. [major] paper/manuscript.tex:927-929

**What.** "\textbf{So roughly half of the anchor's second named discrepancy is not the solver and not the bed geometry, but one term evaluated at its limit.}" The paragraph's own numbers: nRMSE 0.128 -> 0.105 (an 18 % reduction); 95 % arrival 431 -> 384 against 354 measured (a 61 % reduction of the excess).

**Why.** Neither number is "roughly half": one is 18 %, the other 61 %. This is a hedge doing work a number should do, in a bolded sentence, in a limitations paragraph whose entire purpose is to quantify rather than attribute — and line 317-319 forward-references it as "about half" too.

**Fix.** Replace with the actual quantity and say which metric it is measured on: "So the untruncated form removes X % of the 95 % arrival-time excess and Y % of the nRMSE", both as derived macros, and align line 318 to the same figure.

## 28. [minor] paper/manuscript.tex:486-487

**What.** "Six configurations failed to train entirely and are excluded and listed, never averaged in. We did not tune the perceptron and leave the Kolmogorov--Arnold arms at a default." No list of the six configurations appears anywhere in the manuscript. The second sentence mixes tenses ("did not... and leave") and, read literally, contradicts line 469 ("each family at its own best learning rate") and 483-485 ("the perceptron at \nLthreeMlpLr").

**Why.** A dangling promise ("listed" — where?) plus a sentence that says the opposite of what it means. The intended meaning is presumably "we did not tune the perceptron while leaving the KAN arms at a default", i.e. a denial of an unfair comparison; as written it asserts the perceptron was untuned, which the tuning-envelope paragraph refutes two lines above.

**Fix.** "...never averaged in; the six are listed in the supplementary material. We did not tune the perceptron while leaving the Kolmogorov--Arnold arms at a default: every family was swept over the same eight learning rates." And add the list, or drop "and listed".

## 29. [minor] paper/manuscript.tex:448-449

**What.** "Three families are U-shaped with interior optima (\nLtwoWidthShape; \nLtwoDepthShape; \nLtwoXgbShape)" renders as "Three families are U-shaped with interior optima (U-SHAPED, optimum at w64; U-SHAPED, optimum at d8; U-SHAPED, optimum at md6)". Line 457 renders \nLtwoBestFam/\nLtwoBestCfg as "mlp_depth/d8".

**Why.** Machine verdict strings in all caps, redundant with the sentence that introduces them, plus code identifiers (w64, d8, md6, mlp_depth) appearing as prose. This is the raw output of the analysis script pasted into the manuscript.

**Fix.** Change the SPEC formats in paper/numbers.py to emit prose-ready values ("width 64", "depth 8", "max depth 6"), or restructure the sentence to "Three families are U-shaped, with optima at \nLtwoWidthShape, \nLtwoDepthShape and \nLtwoXgbShape" where those macros carry only the configuration name.

## 30. [minor] paper/manuscript.tex:237

**What.** "Both affinities carry the same \(\Delta H\), so \(q_{st} = -\Delta H + RT\) holds at every loading; it is reproduced to four thousandths of a per cent identically at a quarter, a half and three quarters of capacity."

**Why.** The sentence does not parse: "reproduced to four thousandths of a per cent identically" leaves "identically" dangling with no referent, and "four thousandths of a per cent" is a hand-typed result that the numeral gate cannot see because it is spelled out.

**Fix.** "...holds at every loading; it is reproduced to \nIsoQstErr\,\% at a quarter, a half and three quarters of capacity", with a new macro read from results/isotherm_space.json.

## 31. [minor] paper/manuscript.tex:175, 237, 378, 421, 528, 549, 571, 751, 841-842, 927

**What.** Results spelled out as English words, invisible to build_paper.py's NUMERAL regex: "about one per cent" (175), "four thousandths of a per cent" (237), "seven per cent" (378), "less than a third as large" (421), "more than five hundred per cent" (528), "fifty-five times" (549), "a twentieth" (571), "almost a third of the signal" (751), "eleven of fifty-four runs" (841-842), "roughly half" (927). build_paper.py's ALLOWED list also launders four literals that its own docstring says do not belong there: "216" (the best DeepONet's width), "29" (an interpolation-floor percentage), "7" (a power figure), and "1" (which admits "at 48 materials the same sweep found \(1\,\%\)", line 458 — a reported effect size).

**Why.** The manuscript's central process claim, stated twice (header lines 5-9 and §10 line 976: "No number in this manuscript is typed by hand"), is false at ten sites, and the gate that enforces it has a systematic blind spot that one of those sites (fifty-five vs 53) has already exploited into a self-contradiction. §10 is where a referee checks whether the reproducibility claims are literal.

**Fix.** Add a word-number scanner to build_paper.py's numeral check; convert each of the ten sites into a macro or an ALLOWED entry with a written reason; and move "216", "29", "7" and "1" out of ALLOWED into paper/numbers.py SPEC.

## 32. [minor] paper/manuscript.tex:969 (and paper/numbers.py:233)

**What.** "A verification harness of \nGates\ gates runs before any number is reported". numbers.py line 233 defines Gates as results/validation.json path "n_pass" — the number of gates that PASSED, not the number that exist. Currently both are 24, so the sentence happens to be true.

**Why.** If any gate ever fails, the sentence silently reports a smaller harness rather than a failure — the same silent-degradation shape the file's own `mangled()` docstring warns about. A reproducibility section that asserts a gate count should not read it from the pass count.

**Fix.** Point Gates at the total gate count (len of by_gate, or an explicit n_total field), and add a separate assertion that n_pass == n_total or the build fails.

## 33. [minor] paper/manuscript.tex:31-32

**What.** The frontmatter has \author{Abdulhamid Batayhi} and \ead{abdulbatayhi@gmail.com} with no \address{} block, which elsarticle expects between them.

**Why.** Elsevier's submission system and the elsarticle class both expect an affiliation. The manuscript as it stands has no institutional address at all.

**Fix.** Add \address{...} (or \affiliation{organization=...}) after \author, or state "Independent researcher" with a city and country if there is no institutional affiliation.

## 34. [minor] paper/references.bib:n/a

**What.** Five entries are in the bibliography and cited nowhere in the manuscript: abueidda2025deepokan, gowrachari2025cross, greif2019decay, kiyani2025optimizing, ohlberger2013nonlinear. Relatedly, \nLfiveOKAN (0.0357) is defined in numbers.tex and never used — §5.5 never mentions the DeepOKAN arm at all, although abueidda2025deepokan is the DeepOKAN reference and MANUSCRIPT_OUTLINE.md line 74 records "DeepOKAN collapses (10/45)".

**Why.** With elsarticle-num these entries do not print, so they are harmless in the PDF but signal that a planned result (the DeepOKAN arm of L5) was dropped without a word. The outline promised it; the manuscript is silent; the macro sits unused as evidence.

**Fix.** Either report the DeepOKAN arm in §5.5 using \nLfiveOKAN and cite abueidda2025deepokan, or say in one sentence why it is excluded. Remove the four genuinely unused entries or cite them where they belong (ohlberger2013nonlinear alongside ohlberger2016reduced at line 690).

