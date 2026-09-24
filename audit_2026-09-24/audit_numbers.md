# numbers

Of the roughly 60 macros I traced back to their JSON sources, the arithmetic and formatting resolve correctly in almost every case — L1, L6, L7, the anchor, the calibration, the learning curve and Table tab:warp all check out to the digit — but four macros are attached to prose that describes a different quantity than the path measures (the FNO width sentence, the warp headroom, the n-width exponent, and the gate count), and one DERIVED formula string contradicts its own lambda. The larger structural problem is that the numerals gate is bypassed wholesale by spelling numbers as words: I found roughly forty measured quantities written as words or riding mis-declared allow-list literals, including one (\"more than five hundred per cent\") quoted from a run the same section declares PENDING, and one (\"a twentieth of the channel count\") that is wrong by a factor of 2.6. Twenty declared keys are unused, ten of which the paper ought to be quoting — including both L2 minimum detectable effects, whose absence breaks the paper's own stated rule that every null carries one.

## 1. [blocking] paper/manuscript.tex:568-573

**What.** "At the highest mode count the Fourier operator is \emph{\nLfiveFNOwidth\ channels wide} and still matches the best DeepONet found anywhere, which has width 216. A nonlinear reconstruction with a twentieth of the channel count matches the best linear one." Three claims, all contradicted by the declared source. \nLfiveFNOwidth reads results/l5_fno_verdict.json:fno_best.width = 28, which results/l5_fno.json shows is the width of the modes=4 arm — the LOWEST mode count and the best arm (0.021574). The arms are modes 4 -> width 28, modes 8 -> width 14, modes 16 -> width 7. At the highest mode count (16) the width is 7, and that arm scores 0.027710, which is WORSE than the best DeepONet (0.026457), so it does not "match" it. And 28/216 = 1/7.71, not "a twentieth" (7/216 would be a thirty-first).

**Why.** This is the paragraph the section calls "the clearest single piece of evidence in the rung that the reconstruction, not the capacity, separates these families", and every number in it is attached to the wrong arm. A referee who opens l5_fno.json sees the width-vs-modes table immediately; the sentence also contradicts the section's own caveat five lines later that width falls as modes rise.

**Fix.** Rewrite around the best arm: "The best Fourier operator uses \nLfiveFNOmodes\ modes at \nLfiveFNOwidth\ channels and beats the best DeepONet found anywhere, which has width 216." Drop "a twentieth" or replace it with a declared DERIVED ratio (216/28 = 7.7). If the intended claim really is about the highest-mode arm, declare a macro for its width (7) and its mean (0.02771) and state that it ties, not beats.

## 2. [blocking] paper/numbers.py:398-399

**What.** DERIVED entry NwidthHalving declares the formula string "modes needed to halve the error, 2^(1/|algebraic exponent|)" but the lambda computes `2.0 ** (1.0 / abs(r["NwidthExpC"] / 2.0))`. With NwidthExpC = -2.4543 the declared formula gives 1.33 and the code gives 1.76 (the value shipped as \nNwidthHalving).

**Why.** The formula string is the whole audit trail — numbers.py writes it into numbers.tex as a comment and into numbers.json as the provenance record, precisely so a ratio is "auditable rather than typed". A reader who checks the declared formula against the declared exponent gets a different number and concludes the ratio is wrong. The code is right and the declaration is wrong, which is the worst way round.

**Fix.** Change the formula string to "modes needed to halve the error, 2^(1/|algebraic exponent/2|) — the fitted exponent is on the residual ENERGY tail, so the error exponent is half of it".

## 3. [blocking] paper/manuscript.tex:682-685

**What.** "The Kolmogorov \(n\)-width of this snapshot family is algebraic, \(n^{\nNwidthExpC}\) with \(R^2 = \nNwidthRtwoC\) over \(n = 8\)--64, so halving the error requires \(\nNwidthHalving\times\) the modes permanently." \nNwidthExpC reads results/nwidth.json:c.algebraic_exponent = -2.4543, which nwidth.py:26-28 fits to the residual ENERGY tail (`tail = 1.0 - cum`, i.e. 1 minus cumulative explained variance), not to an error. The n-width is an L2 error and decays as the square root of that: n^-1.227. make_figures.py:251 knows this and plots `algebraic_exponent / 2`.

**Why.** The manuscript states the n-width decay rate as twice as fast as its own figure shows, and then quotes a halving factor (1.76) computed from the correct exponent (-1.23) — so the sentence contradicts itself: at n^-2.45 halving would cost 1.33x the modes, not 1.76x. Any referee who does 2^(1/2.45) catches it in ten seconds, in the paragraph that carries retraction A17.

**Fix.** Declare a new key, e.g. ("NwidthExpErr", "results/nwidth.json", "c.algebraic_exponent", lambda x: "%.2f" % (x/2)), and write \(n^{\nNwidthExpErr}\) here; keep the energy-tail exponent out of the prose or label it explicitly as the exponent of the residual energy.

## 4. [major] paper/manuscript.tex:775-778

**What.** "But the oracle gap is significant and large: given the true front trajectories, the same proper-orthogonal-decomposition-plus-regressor arm is \nWarpHeadroom{}\(\times\) better." \nWarpHeadroom reads results/warp_verdict.json:headroom_to_oracle = 2.1655, which is means.two_wave / means.two_wave_oracle (0.047704/0.022029) — the oracle relative to the PREDICTED-front two-wave arm. The sentence sits directly under Table~\ref{tab:warp}, whose only significant row is fixed_vs_oracle, so "better" reads as better than the fixed frame: 0.050051/0.022029 = 2.27x, not 2.17x. The abstract repeats it at line 57 ("buys a significant \nWarpHeadroom{}\(\times\) under an oracle").

**Why.** A significance statement taken from one comparison is paired with a ratio taken from a different one. The paper's own rule is that the oracle is reported only to size the headroom against the fixed frame, and 2.17 is not that number.

**Fix.** Either say what the ratio is a ratio of — "the oracle arm is \nWarpHeadroom{}\(\times\) better than the same frame with predicted fronts" — or add a DERIVED key for means.fixed/means.two_wave_oracle (2.27) and use that where the comparison is against the fixed frame. The abstract needs the same fix.

## 5. [major] paper/numbers.py:302-303, 306-309

**What.** \nMassClosure and \nGridConv are formatted with `pct` (one decimal). results/validation.json holds mass closure default = 0.000496726 (0.0497 %) and grid-convergence default err = 0.000549656 (0.0550 %), so the manuscript prints "closure improved to 0.0 %" (lines 176 and 198) and "grid convergence is 0.1 %" (line 198), while validation.json's own gate evidence strings read "default: closes to 0.050% OK" and "default: 0.055% change at N_z=2000". The same formatter turns MassClosureMof (0.0546 %) into "0.1". Table tab:l0 has it worse: \nLzeroRetarded is retarded_front.rel_err = 0.000271938 -> "0.0 %" and \nLzeroThermal is thermal_wave.rel_err = 0.000123328 -> "0.0 %".

**Why.** A verification table whose error column reads "0.0 %" claims exactness the solver does not have, and it disagrees with the harness output the same paper cites as evidence. It also throws away the paper's strongest verification numbers: 0.027 % and 0.012 % are impressive, 0.0 % is not believable.

**Fix.** Give these keys a two-significant-figure formatter instead of `pct` — e.g. `lambda x: sig(100*x, 2)` — so the table reads 0.027 %, 0.012 %, 0.050 %, 0.055 %.

## 6. [major] paper/manuscript.tex:548, 565

**What.** Line 548: "At \(p = 128\) it sits fifty-five times above its own lower bound." Line 565: "it sits \(\nFNOxFloor\times\) above the floor where DeepONet sits \(\nONetxFloor\times\)" = 53x. Both are correct for different quantities: DeepONet at p=128 (l5_merged.json selected.deeponet_p128.mean = 0.027476) over the p=128 floor is 54.78; \nONetxFloor is deeponet_best (which is the p=8 arm, 0.026457) over the p=128 floor = 52.75. The 55 is spelled in words and has no macro; the 53 divides a p=8 error by a p=128 floor without saying so.

**Why.** The same subsection gives two different multiples for "DeepONet above its floor" seventeen lines apart, one of them invisible to the numerals gate. The DERIVED description "the best DeepONet divided by the POD floor at p=128" does not warn that the numerator is the p=8 arm.

**Fix.** Declare ("LfiveONetP128", "results/l5_merged.json", "selected.deeponet_p128.mean", ...) and a DERIVED ONetP128xFloor for line 548; amend the ONetxFloor formula string to "the best DeepONet found anywhere (p=8) divided by the POD floor at p=128" and say so in the prose at line 565.

## 7. [major] paper/manuscript.tex:543-544

**What.** "At matched parameter counts and each family at its own best learning rate over three and a half decades, DeepONet is flat in basis size". The L5 learning-rate grid recorded in results/l5_merged.json (selected.*.grid) is [5e-05, 1e-04, 2e-04, 3e-04, 1e-03, 3e-03, 1e-02]: seven rates spanning 2.30 decades. "Three and a half decades" is L3's envelope, not L5's.

**Why.** The tuning envelope is the paper's own answer to the McGreivy and Hakim weak-baseline critique, so overstating it by more than a decade on the rung whose null ("DeepONet is flat") depends on the competitor being well tuned is exactly the failure the design brief is written against.

**Fix.** State L5's actual envelope: seven learning rates from 5e-5 to 1e-2, 2.3 decades — and make it macros from l5_merged.json's grid rather than words.

## 8. [major] paper/manuscript.tex:527

**What.** "It rose by more than five hundred per cent on all three seeds." This is a measured L4b-v2 quantity, spelled in words, with no macro and no results file: results/l4b_v2_verdict.json is listed in numbers.py PENDING, and the section's own verdict macros render as \textbf{[PENDING]} eleven lines above (line 512-514).

**Why.** The paper reports a number from a run it simultaneously declares unavailable. The PENDING mechanism exists so that "a manuscript can never be finalised while any remain" — and a number from that same run has walked past it by being written as words.

**Fix.** Either move the invalidation-condition measurement into a small results file the gate can read (e.g. results/l4b_v2_invalidation.json with seen_window_error_rise) and declare a macro, or cut the sentence until l4b_v2_verdict.json lands.

## 9. [major] paper/manuscript.tex:164, 175, 237, 286, 375-377, 415, 420, 435-436, 439, 441

**What.** Measured quantities written as words, invisible to the gate (build_paper.py NUMERAL only matches digits). Line 164 "an improvement of more than an order of magnitude" (verify_solver.json: 0.035219/0.0016855 = 20.9x; the Dirichlet error is in the file but not in SPEC). Line 175 "left global mass closure off by about one per cent". Line 237 "reproduced to four thousandths of a per cent" (validation.json Clausius-Clapeyron gate evidence: "0.004%") and "at a quarter, a half and three quarters of capacity". Line 286 caption "an intermediate plateau near a third of the feed" (\nAnchorPlateauExp = 0.267 already exists). Line 375-377 "at 96\,\% power against a 20\,\% effect" and "gave seven per cent". Line 415 "at a quarter of the materials". Line 420 "a ratio less than a third as large" (results/l1_audit.json split_sensitivity.ratios = 23.4-35.6 against \nLoneXfloor = 109; l1_audit.json is in no SPEC row) and "four times the materials". Line 435-436 "a basis fitted on twelve materials". Line 439 "clears a fifth of the variance" (the R^2 > 0.2 threshold). Line 441 "half the material exponent" (0.122/0.222 = 0.55).

**Why.** Rule 10 says no number without a script and rule 6 says a gate that can be bypassed is not a gate. Spelling a number in words is the bypass: the manuscript-numbers gate passed with "170 macros used, all resolved" while these went straight through. Line 420 is the sharpest case — the comparison ratio it rests on lives in a results file that numbers.py has never been told about.

**Fix.** Add SPEC rows for the ones with sources (l1_audit.json split_sensitivity.ratios; verify_solver.json max_abs_err_vs_dirichlet as a DERIVED ratio; validate's Clausius-Clapeyron 0.004 %; the pre-fix mass closure if it exists anywhere) and use the existing macros where they exist (\nAnchorPlateauExp at line 286, \nLCratio-style keys at 415/420). Then extend the gate: add a WORD_NUMERAL regex over the same body text (one|two|...|hundred|half|third|quarter|fifth|twentieth|orders? of magnitude) with its own declared allow-list, or the same defect recurs.

## 10. [major] paper/manuscript.tex:446, 452, 457, 458, 470-471, 482-484, 516-519

**What.** More words-as-numbers, L2 through L4. Line 446 "Twenty-eight configurations" (verified: mlp_width 7 + mlp_depth 8 + rf_leaf 6 + xgb_depth 7 = 28 rows in l2_v2_verdict.json). Line 452 "drops its training error by more than an order of magnitude" (xgb_depth train_c 0.03902 -> 0.00085, 45.8x). Line 457 "at 48 materials the same sweep found \(1\,\%\)" — a measured percentage that passes the gate only because build_paper.py allow-lists "1" as "ordinal / unity". Line 458 "put the depth optimum two layers lower". Line 470-471 "all six pairwise comparisons significant. \nLthreeArms\ arms were trained across eight learning rates spanning \(3\times10^{-5}\) to \(10^{-1}\), three and a half decades" — results/l3_merged.json's own `grid` is seven rates ending at 3e-2 (3.00 decades); the eighth exists only in results/l3_cheby_1e-1.json and only for one family. Line 482-484 "The families optimise three orders of magnitude apart" (0.03/3e-05 = 1000x) and "Six configurations failed to train entirely". Lines 516-519 "ten weighting schemes", "four decades", "three target ratios".

**Why.** Same bypass, and line 457 is worse than a bypass: a result is riding an exemption written for a different meaning of the digit. Line 471 additionally contradicts the very file \nLthreeArms is read from, and re-types 3e-5 as raw LaTeX when \nLthreeMlpLr already holds it.

**Fix.** Macros for the countables (n_arms already exists; add n_configs for L2, n_failed for L3, and the grid endpoints/decades from l3_merged.json:grid). At line 471 use \nLthreeMlpLr and a declared grid-span macro, and reconcile "eight rates / three and a half decades" with l3_merged.json:grid — if the 1e-1 arm counts, merge it into l3_merged.json so the file says eight.

## 11. [major] paper/manuscript.tex:537, 548-549, 570, 602-603, 609, 665, 669, 750, 783, 790, 819, 840-841, 874, 908-910

**What.** The remaining words-as-numbers, L5 to the end. Line 537 caption: "The floor falls by more than an order of magnitude" (\nFloorDrop = 28.7 exists and is used elsewhere), "a sixteenfold change in basis size", "beyond about the twenty-fourth the median is below zero". Line 548 "fifty-five times"; line 549 "buys it the accuracy of four". Line 570 "a twentieth of the channel count". Line 602-603 "consistent in all five folds and all three seeds". Line 609 "With 240 clusters instead of twelve" (\nNclustLegacy = 12 exists and is used at line 367). Line 665 "modes two to five partially, and beyond about mode 24". Line 669 "performs like a four-mode oracle". Line 750 "its interpolation floor reached almost a third of the signal". Line 783 "unlearnable beyond about five modes". Line 790 "It does violate them, in more than half of all samples" (warp_monotone.json nonmonotone_frac.lo = 0.526-0.580). Line 819 "three of them reversed headline verdicts". Line 840-841 "eleven of fifty-four runs in one rung reported the error of a random initialisation". Line 874 "an aspect ratio under a fifth" (6.35/38.1 = 0.167). Line 908-910 "measured over twelve held-out materials", "did not survive four times as many".

**Why.** Every one of these is a measured or countable quantity with no script behind it, and several have a macro sitting unused two hundred lines away (\nFloorDrop at 537, \nNclustLegacy at 609). "Eleven of fifty-four" (A19/B24, the undertrained-arms class) is a bare count in the correction ledger itself, which is the one section that must not contain an unscripted number.

**Fix.** Use the existing macros at 537 and 609; add SPEC rows for the oracle-equivalent mode count, the per-mode R^2 crossing index, the monotonicity violation fraction (warp_monotone.json per_seed[*].nonmonotone_frac.lo), the interpolation floor (comoving2.json pairs_detail['0.20-0.80'].interp_floor) and the 11/54 undertrained-run count; then reconcile line 665 ("beyond about mode 24") with line 783 ("beyond about five modes"), which state the same fact with different thresholds.

## 12. [major] paper/manuscript.tex:926

**What.** "A verification harness of \nGates\ gates runs before any number is reported". \nGates reads results/validation.json:n_pass — the number of gates that PASSED, not the number of gates. It currently equals 24 only because n_fail = 0 and n_skip = 0 (verified: by_gate has 24 entries, all PASS).

**Why.** If a gate ever fails or skips, the sentence silently reports a smaller harness rather than a failure — the count of the safety net is read from the net's success count. That is the shape of B37: a gate defeated by the absence of something.

**Fix.** Add n_gates (or len(by_gate)) to validation.json and point \nGates at it; if the pass count is also wanted, add a second macro and say "\nGatesPass of \nGates pass".

## 13. [major] paper/manuscript.tex:454-457

**What.** "\textbf{Verdict: capacity as an unbounded lever is eliminated}". results/l2_v2_verdict.json's own `verdict` field reads: "NOT ELIMINATED: families still improving at their last step: ['rf_leaf']. Extend their sweeps." The manuscript's verdict word for L2 is hand-written and is the opposite of the source file's, even though the verdict-string macro mechanism already exists and is used for L4b (\nLfourbVerdictMaterial, \nLfourbVerdictTime). The same is true of L1 (learning_curve_v2_verdict.json axes.materials.verdict), L6 (slope_verdict) and L7 (verdict), all of which carry verdict strings the manuscript retypes.

**Why.** The paper's headline claim for a whole rung is a hand-typed word that contradicts the machine verdict in the file it cites. The prose does explain the rf_leaf caveat at lines 449-450, so this is recoverable — but a referee who opens the verdict file first will not read it charitably.

**Fix.** Declare verdict-string macros for L1/L2/L6/L7 as was done for L4b, and either quote the file's verdict verbatim or state plainly in the text why the paper's verdict differs from the analyser's ("eliminated as an unbounded lever except for rf_leaf, whose last step is a fully grown forest").

## 14. [major] build_paper.py:162

**What.** `strip_structural` deletes every `\SI{...}{...}` before the numeral scan ("\SI carries its own units"). The anchor section therefore hand-types five numbers the gate can never see: manuscript.tex:294-296 \SI{6.35}{\milli\metre}, \SI{38.1}{\milli\metre}, \SI{32.8}{\percent}, \SI{298.15}{\kelvin}, \SI{429.6}{\kilo\gram\per\metre\cubed}. At least two of them are already in a results file: results/lassitter_comparison.json has rh_in = 0.328 and T_K = 298.15.

**Why.** Section~\ref{sec:reproducibility} line 933 asserts "No number in this manuscript is typed by hand. Every quantity above is a macro resolved at build time from a named results file." That claim is false, and it is false in the one place a referee will check hardest — the experimental anchor's conditions.

**Fix.** Either strip only the unit argument of \SI (keep the value in the scan) so these numerals must be declared, or declare macros from lassitter_comparison.json for rh_in and T_K and add the bed geometry to that file. Failing both, soften line 933 to name the exemption class explicitly.

## 15. [minor] paper/manuscript.tex:663

**What.** "The coefficient-map error, with a strong regressor, moves from \nLfiveCoefSmall\ to \nLfiveCoefLarge\ --- flat to four decimal places." The values are l5_bottleneck.json rows[0].coef_pred_novel = 0.0515010 and rows[4].coef_pred_novel = 0.0510459: they differ by 4.55e-4, i.e. AT the fourth decimal. As printed by the macros (0.0515 vs 0.0510) they visibly disagree in the digit the sentence claims they agree in.

**Why.** The sentence is refuted by the two numbers it quotes, in the paragraph that carries the paper's central mechanism claim.

**Fix.** "flat to three decimal places" (0.051 both), or better, quote the difference: "moves by 0.0005 across a sixteenfold change in basis size".

## 16. [minor] paper/manuscript.tex:750

**What.** "A third pair was excluded because a narrow window divides by a small span and its interpolation floor reached almost a third of the signal." The excluded pair is comoving2.json pairs_detail['0.20-0.80'], interp_floor = 0.014923 — 1.5 % of the signal. It is 29.8 % of the 0.05005 fixed-frame nRMSE, which is presumably where "almost a third" comes from (build_paper.py still allow-lists "29" as "an interpolation-floor percentage from a reported exclusion", though the numeral no longer appears anywhere in the manuscript).

**Why.** Wrong denominator: the floor is a third of the achievable error, not a third of the signal. The stale allow-list entry is itself evidence that the number moved from a declared literal into gate-invisible words.

**Fix.** "its interpolation floor reached almost a third of the fixed-frame error", with a macro for comoving2.json pairs_detail['0.20-0.80'].interp_floor and a DERIVED ratio against \nWarpFixed; then delete the dead "29" allow-list entry.

## 17. [minor] paper/manuscript.tex:602-603

**What.** "separate is better by \nLsixDiff, interval [\nLsixLo, \nLsixHi], consistent in all five folds and all three seeds." Nothing in results/l6_v2_verdict.json records per-fold or per-seed arm means (per_material has three keys: joint, separate, separate_noeq). Reading results/l6_v2_results.json directly: separate wins in 5/5 folds on the seed-averaged means and in 3/3 seeds on the fold-averaged means, but in only 11 of the 15 fold-by-seed cells — fold1/seed42 (0.06011 vs 0.06060), fold2/seed43 (0.05024 vs 0.05117), fold3/seed42 (0.05514 vs 0.05861) and fold4/seed44 (0.05533 vs 0.05645) reverse.

**Why.** The claim is true under the marginal reading and false under the cell-by-cell reading a reader is likely to take from "consistent in all five folds AND all three seeds", and no declared macro or small verdict file lets anyone check either way. The parallel L1 claim at line 415 ("ahead in every one of the five folds") is genuinely 5/5 and sets the stricter expectation.

**Fix.** Write the per-fold and per-seed win counts into l6_v2_verdict.json and declare macros: "separate is better in all five folds and for all three seeds (11 of 15 fold-by-seed cells)".

## 18. [minor] paper/manuscript.tex:434-436

**What.** "Refitting the basis on each subset changes nothing: \nLCsmallestFixed\ against \nLCsmallest\ at 12 materials, \nLClargestFixed\ against \nLClargest\ at 192." The second pair is rows[4].fixed and rows[4].refit in learning_curve_v2_verdict.json, and both are the identical float 0.034840433249133176 — at n=192 the "fixed on all 192" basis IS the refit basis.

**Why.** Quoting an identity as evidence is circular. A referee who notices the two printed values are byte-identical will assume a copy-paste error, or worse, that the whole fixed-vs-refit comparison is degenerate.

**Fix.** Say so: "...and identically at 192, where the fixed basis is the refit basis by construction". The real evidence is the 12/24/48/96 rows, which differ by less than 0.0003 each.

## 19. [minor] paper/numbers.py:166, 176-179, 313

**What.** Three SPEC paths index result lists by hard-coded position rather than by label: LtwoXfloor -> families.mlp_depth.rows[6].x_floor (row 6 is d8 today, verified against rows[i].label), LfiveBasisSmall/LfiveCoefSmall -> rows[0] and LfiveBasisLarge/LfiveCoefLarge -> rows[4] in l5_bottleneck.json, LCsmallest/LClargest -> axes.materials.rows[0] and rows[4].

**Why.** Insert a sweep row, extend a sweep, or reorder a merge and the macro silently resolves to a different configuration with no error — the resolver's contract is that a miss is a hard failure, and a positional hit that lands on the wrong row is exactly the silent miss the module was written to abolish.

**Fix.** Extend `dig` to accept a selector like `rows[label=d8]`, or have the analysers emit label-keyed dicts (families.mlp_depth.by_label.d8.x_floor) and point the SPEC rows at those.

## 20. [minor] paper/manuscript.tex:596-598

**What.** "over \nLsixDaDecades\ decades spanning kinetically-controlled to near-equilibrium operation". The declared source (l6_v2_checks.json da) is min 7.67, median 25.03, max 172.97, and dataset_summary.json puts the informative band at [5, 60] with 85 % of materials inside it. No material in the regression has Da below 7.7, so the low end of the range is inside the band, not in a kinetically controlled regime (Da of order 1 or below). The phrasing traces to l6_v2_verdict.json's slope_verdict string, which makes the same claim.

**Why.** The primary estimand's scope statement is the sentence a referee will test hardest, since the whole rung is a null on that axis. Overstating the low end invites the reply that the mechanism was never tested where it was supposed to act.

**Fix.** Quote the range instead of naming regimes: "over \nLsixDaDecades\ decades, Da \nLsixDaMin--\nLsixDaMax" (both macros exist and are unused), and describe the span relative to the declared informative band.

## 21. [minor] paper/manuscript.tex:253-255

**What.** "Measured across all \nIsoNmat\ sampled materials rather than at two named configurations: \(n > 1\) strictly for every material...". \nIsoNmat is isotherm_space.json:n_materials = 240, but the same file records n_representable = 239 (and log10_c_henry.min = -509, an underflow the corrections section itself describes at line 833-835).

**Why.** The paragraph's whole point is that a property must be measured over the space rather than at a configuration; if one of the 240 is not representable, "all 240" is the same overreach one scale down.

**Fix.** Check what n_representable excludes and either declare it as a macro and state the exception, or confirm it is an artefact of the underflow guard and say so.

## 22. [minor] paper/manuscript.tex:604, 671-672

**What.** Two duplicated fragments. Line 604: "...The direction has flipped, and the earlier number is not quoted here because it belongs to a design that could not test the estimand at all. The direction has flipped." Lines 671-672: "Training basis and coefficients together is worth a constant\na constant factor and nothing more."

**Why.** Not a number defect, but both sit in the two paragraphs a referee reads most closely (L6's sign reversal and the mechanism conclusion), and an editing artefact there reads as carelessness about the surrounding claims.

**Fix.** Delete the trailing "The direction has flipped." at line 604 and the repeated "a constant" at line 671.

## 23. [minor] paper/numbers.py:56-317

**What.** Twenty declared keys are never used in the manuscript (the brief said 21; the current count is 20). SHOULD BE USED: LtwoDepthMDE (5.0) and LtwoXgbMDE (2.0) — line 372 declares "Every null carries its minimum detectable effect" and the L2 subsection reports none, breaking the paper's own rule on the rung whose verdict is partly a null; LthreeMlpSmall/LthreeMlpLarge/LthreeRbfLarge/LthreeChebyLarge — L3 claims the perceptron wins at every budget and quotes not one per-budget number, and these four are exactly the cells; LfiveFNOmodes (4) — line 568 discusses mode count without ever giving the best arm's; LfiveOKAN (0.0357) — L5's third arm is never reported; LzeroTracerFront (0.0228 %) — Table tab:l0's tracer row reports the profile error only, while the L0 gate evidence reports both; MassClosureMof (0.055 %) — line 198 gives grid convergence for both configurations but mass closure only for the default; NclustManifest (48) and DataNheldout (48) — line 457 types "48 materials" as an allow-listed literal while two macros hold it. NOT DEAD, used as DERIVED inputs: LfiveFloor (FNOxFloor, ONetxFloor), LsixLegacyBetweenSD and LsixLegacyBase (LsixNoiseDrop, LsixLegacyBetweenOverBase). GENUINELY DEAD: AlphaManifest (duplicate of AlphaFolds, both 0.02); LtwoPodFloor (2.80e-04, the same floor as LonePodFloor); LsixDaMin/LsixDaMax/LsixDaMedian (duplicates of DaMatMin/Max/Median from a second file).

**Why.** An unused key is not harmless: LtwoDepthMDE and LtwoXgbMDE mean an announced protocol rule is unmet in the text, and the four L3 cells mean a headline claim is asserted with no quoted evidence. The genuinely dead ones cost nothing but should be labelled so the next audit does not re-derive this.

**Fix.** Use the ten SHOULD-BE-USED keys in the sentences named above; add a comment on the five dead ones saying they are retained as cross-file consistency checks (LsixDa* against DaMat*, LtwoPodFloor against LonePodFloor); and consider making numbers.py report unused keys on --check so the list stays honest.

