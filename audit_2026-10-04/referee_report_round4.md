# Referee report, round 4: consistency check after the final runs

**What I reviewed**
- `paper/manuscript.tex` (2022 lines) at HEAD 2b3818d.
- Macros in `paper/numbers.tex`, with their sources in `paper/numbers.py`.
- Results files, read directly:
  - `results/l5_v2_verdict_24k.json`
  - `results/l4b_v3_verdict.json`
  - `results/l4b_v3_selection.json`
  - `results/coarse_solver_baseline.json`
  - `results/fitted_classical.json`
  - `results/gp_baseline_verdict.json`
- Also read: `l5_v2_analysis_24k.log`, `PREREG_L5_v2.md` (amendments A2 and A3), `RETRACTIONS.md` (A2, A3, A28 to A30), `paper/highlights.txt`, `coarse_solver_baseline.py` (summary code) and `figures/Fig1_ladder.png`.

Line numbers refer to `manuscript.tex` unless another file is named.

## The headline numbers check out

All of these match their JSON sources exactly:

- **L5-v2 (basis size):**
  - p = 8 gives 0.0109 and p = 128 gives 0.0096.
  - The per-pair interval is [0.00099, 0.00164]. The selection-adjusted interval is [0.00088, 0.00173], with q = 3.08 over 16 pairs.
  - The gain is 12.0 %. DeepONet sits 1.72x above the POD floor at p = 8 and 136x above it at p = 128.
- **L4b-v3 (physics as a loss):**
  - Material axis: 0.0231 to 0.0211, a gain of 8.7 %. The per-pair interval is [0.00141, 0.00271] and the selection-adjusted one is [0.00119, 0.00285].
  - Time axis: no difference, MDE 5 %.
  - Arm counts: 7 eligible arms worse and 3 better on the material axis; 3 abandoned on the time axis and 2 on the material axis.
  - Polishing: on the time axis the ordering flips; on the material axis polishing worsens both arms.
  - Refinement at inference: the twin goes 0.0231 to 0.0685 (2.96x) and the best physics arm 0.0211 to 0.0605. The seen-window error rises 394 %.
- **B-COARSE (coarse solver):** at N_z = 50 the error is 0.626 % against the surrogate's 3.06 %, at 0.126 solve-equivalents and 222 ms per solve. 7 of 240 coarse solves were unaccepted.
- **B-FIT (fitted Klinkenberg):** 2.44x worse than learning, interval [-0.0747, -0.0622].
- **B-GP (Gaussian process):** 0.0309 against the perceptron's 0.0306, interval [-0.0013, 0.0008], MDE 6 %.

**What is wrong is the text around these numbers.** The A29 retraction and the A30 cost revision were added where the new results are reported. They were not carried into the introduction, Section 5 (mechanism), the L5 caveat, the Fig. 5 caption, the corrections section's tally and error classes, the "What is scoped" conclusion, or the highlights. One new cross-reference sends the reader to the wrong ledger entries. Two claims about the coarse solver, in the abstract and the conclusions, break the paper's own rule against comparing absolute errors across rungs.

Recommendation: **minor revision.** Everything below is text only; no new computation is needed.

---

## MAJOR

### M1. The introduction still claims the retracted A29 result (l.200-203)
> "we show the plateau is invariant to basis size while the proper-orthogonal-decomposition floor beneath it falls \(\nFloorDrop\times\)"

This is listed as one of the paper's four extensions of Heinlein and Taraz. It is the exact claim A29 retracts:
- On the 240-material design, DeepONet improves 12 % from p = 8 to p = 128.
- The interval survives the selection adjustment: [0.00088, 0.00173].
- `\nFloorDrop` (28.7) is the legacy floor drop. The full-design figure is `\nLfiveVtwoFloorDrop` = 90.

**Fix:** "beyond a small basis the plateau barely moves (a 12 % gain, complete by p = 16) while the floor falls 90x".

### M2. Section 5 still calls DeepONet "flat in rank" (l.1316-1317)
> "Three independent function classes --- proper orthogonal decomposition plus random forest, plus gradient boosting, and DeepONet --- are all flat in rank while the floor falls by a factor of \nFloorDrop."

This is unqualified and stated as current. For DeepONet it is now false on the main design (A29). It is true only on the 12-material legacy set, where the verdict has been retracted.

**Fix:** either drop DeepONet from the list, or scope the sentence to "on the legacy design" and add a pointer to the 12 % gain.

### M3. The L5 caveat still makes the retracted statement (l.1164-1166)
> "The flat-in-\(p\) statement is made for DeepONet, where \(p\) and width are controlled separately, and is not claimed for the Fourier operator."

This still presents "flat in p" as a statement the paper makes for DeepONet. A29 retracts it.

**Fix:** reword along the lines of "basis-size statements are made for DeepONet, where p and width are controlled separately (on the full design, a 12 % gain complete by p = 16)…".

### M4. Fig. 5 caption (l.1278-1280)
> "the floor falls \(\nFloorDrop\times\) while DeepONet and the pointwise regressors stay flat"

`fig_mechanism.py` reads only legacy files: `l5_merged.json`, `l5_fno_verdict.json` and `l5_bottleneck.json`. The caption never says "legacy", and it states "DeepONet … stay flat" as current. Fig. 4's caption was updated (l.1082, panel B points to A29); Fig. 5's was not.

**Fix:** add "legacy design" and "(on the full design DeepONet gains 12 %; A29)".

### M5. A29 points to the wrong ledger entries (l.1089-1090)
> "The pre-registered re-measurement … (Section~\ref{sec:corrections}, A2, A3) answers the rung's primary question"

In `RETRACTIONS.md` and SI S1:
- **A2** is "Publication-grade weights … Checkpoint void" (a NaN checkpoint).
- **A3** is "The datasets contained no breakthrough".

The A2 and A3 intended here are **amendments of PREREG_L5_v2**: the 24k-step re-budget and the selection adjustment. Every other A-code in the paper points into the ledger, so this misdirects the reader. The same ambiguity appears in the A29 row of `RETRACTIONS.md` ("at 24k steps (A2)", "(A3: [0.00088, 0.00173])").

**Fix:** write "PREREG_L5_v2 amendments A2 and A3" in both places, and cite B74, which is the ledger entry for the re-budget.

### M6. "A coarse solve is more accurate than every surrogate" breaks the paper's own comparability rule (abstract l.58; conclusions l.1920-1921)
> "A coarse numerical solve is more accurate than every surrogate and cheaper below about \nCoarseBreakEven\ queries." (l.58)
>
> "on this column it is more accurate than every surrogate here." (l.1921)

B-COARSE compares one target, `summary.target_l1_mlp` = 0.0306 (the L1 perceptron; the L2 best is 0.0241). It does not compare L5-v2 DeepONet (0.0096), the L4 time axis (0.0131) or the legacy FNO (0.0216). Each of those is on a different encoding, scored set or dataset.

l.748 says, in bold, "**Absolute errors are not comparable across rungs.**" l.1619 says the FNO-versus-warp comparison is "the one place we compare absolute errors across rungs". "Every surrogate" is a second, unlicensed cross-rung claim.

The comparison is also unpaired and has no interval:
- B-COARSE scores one randomly drawn condition per material (240 samples).
- The L1 mean is over all 3947 samples.

The 5x gap makes the conclusion very likely right for L1 and L2. As worded, though, it is an overclaim against the paper's own rule.

**Fix:** "more accurate than the L1 and L2 surrogates it was compared with".

### M7. The corrections tally and error classes ignore A29 and A30 (l.1645, l.1651-1656, l.1675-1688)
- l.1645: "four of them reversed headline verdicts".
- l.1675: "**Four that reversed a headline.**" The four are the physics-as-a-loss rung twice, A17 and A22.
  - A29 calls itself the retraction of "L5's headline". The paper's earlier text and the "basis size is not the lever" conclusion rested on it.
  - A30 reverses the cost section's central claim ("the surrogate is the cheaper option").
  - Neither is counted, and neither is named as excluded the way B75 is (l.1685-1688).
- l.1678-1680: A28 is still "the only one that voids a whole rung". The rung has been re-run with the corrected residual, and A28 is marked **Resolved 2026-10-11** in `RETRACTIONS.md`. Present-tense "voids" is stale; "voided … until the re-run" would be accurate.
- l.1653-1656: "A18, A21 and A26 are the same error three times". A29's own ledger text says "The same lesson as A18/A21/A26, a fourth time". Class 1 should list A29.

### M8. "What is scoped" contradicts the Limitations (l.1924-1926)
> "Three verdicts --- L3, L5 and the coordinate change --- were measured on \nNclustLegacy\ held-out materials rather than \nNclustFolds, and must be read at that material count until they are re-measured."

L5's basis verdict *has* been re-measured, and the result reversed. The Limitations section says so (l.1848-1850). The conclusions should say: "L3, L5's operator comparison (FNO vs DeepONet) and the coordinate change; L5's basis-size verdict was re-measured and reversed (A29)".

Related, minor:
- **l.1839-1841** heading and first sentence: "Three rungs are measured on the smaller dataset. L3, L5 and the coordinate change are measured over \nNclustLegacy …". This is qualified only later in the same paragraph.
- **l.491-493** ("L5's operator comparisons … run on the earlier … design") and **Table 2, l.782**: the L5 row is "legacy" only. Neither mentions that the DeepONet basis sweep now runs five-fold on 240 materials. Table 2 needs a row such as "L5 basis size (re-measured) | larger, five-fold | DeepONet over p, 24k steps".

### M9. Conclusions put a legacy number on a full-design floor (l.1878-1882)
> "while the proper-orthogonal-decomposition floor falls \(\nLfiveVtwoFloorDrop\times\) (A29); and a Fourier neural operator … still sits \(\nFNOxFloor\times\) above that floor."

"That floor" grammatically refers to the full-design floor, which falls 90x. But `\nFNOxFloor` = 43 is `LfiveFNO / LfiveFloor`: the legacy FNO over the legacy floor at p = 128. The FNO was never run on the 240-material design.

**Fix:** "above the legacy floor at p = 128".

### M10. The B-GP inference contradicts the rest of the paper (l.879-882)
> "Two very different function classes reach the same error from the same inputs, which is what a limit set by the information in the training materials, rather than by the regressor, predicts."

The same paper reports large regressor effects:
- L2 finds a perceptron configuration 21.3 % better than the L1 setting on the same folds (l.905).
- The conclusions call the learner lever "not small", 2.4x (l.1899-1905).
- The B-GP design's MDE is 6 %, so a null against one GP configuration (hyperparameters fitted on a subset, amendment A1) cannot carry "rather than by the regressor".

**Fix:** "is consistent with a limit set by the training materials; it does not exclude the configuration and learner effects of L2 and L5".

---

## MINOR

**m1. "Complete by p = 16" and "nothing after" are point-estimate readings, not tests** (l.1095-1096, l.1878-1879; A29 "p = 16-128 are level").
- `l5_v2_verdict_24k.json` contains only comparisons against p = 8. No p = 16 versus p ≥ 32 test exists.
- Point estimates are p16 0.00961, p32 0.00955, p64 0.00940, p128 0.00958. p = 64 is the best arm, with a 13.6 % gain.
- l.1878-1879 ("gains \nLfiveVtwoGainPct % from p = 8 to p = 16") attaches the p = 8 to p = 128 figure (12.0 %) to p = 16. The p = 16 gain is 11.7 %. This is harmless after rounding, but mislabelled.
- **Fix:** "level by point estimate (not tested)".

**m2. The step budget behind the L5-v2 verdict is not stated, and its convergence is untested** (l.1088-1099).
- The verdict is at 24k steps. The analyser's step check (8k vs 24k, fold 0) found p = 128 +18.8 % and p = 8 +0.5 % ("MATERIAL — RE-BUDGET THE SWEEP").
- The large-p arms are the budget-sensitive ones. Nothing tests whether 24k has converged, so the 12 % gain and "complete by p = 16" are conditional on the budget and could understate the large-p gain.
- **Fix:** state the budget and this direction of possible bias in the L5 paragraph. It is currently only in A29's "(A2)".

**m3. "Counted, not dropped" is not what the code does** (l.1581). `coarse_solver_baseline.py:97` computes `mean_nrmse_c` over `ok` (accepted only). The 7 unaccepted N_z = 50 solves (exit ratio 0.88-0.90) are **excluded from the mean**:
- Accepted-only mean: 0.006258.
- Mean over all 240: 0.006273.

The effect is negligible, but the sentence is wrong. **Fix:** "counted in the tally and excluded from the mean (including them changes it from 0.626 % to 0.627 %)".

**m4. Two numbers for "the surrogate's error"** (abstract l.47 vs l.1579).
- The abstract quotes the perceptron at `\nLClargestPct` = 3.5 % (the learning-curve point at 192 materials, 0.0348).
- The cost and coarse comparison uses `\nCoarseTargetPct` = 3.1 % (the L1 pooled perceptron, 0.0306).
- Table 4's 192-material row prices 0.0348, but B-COARSE prices against 0.0306.
- **Fix:** one sentence saying which arm each number is.

**m5. The break-even mixes cost bases; say it is a lower bound** (l.1582-1586; numbers.py `CoarseBreakEven`).
- Training simulations are priced at 1 solve-equivalent each on the in-process 1.77 s base.
- The generation actually cost 16.6 worker-seconds per solve (`\nCostSolveSec`), about 9.4x more.
- With the generation cost, the coarse-versus-surrogate break-even is roughly 9x larger.
- This only strengthens the A30 conclusion, but "about 25 400 queries" should be called a lower bound, and the reason for the 9.4x gap given.

**m6. The abstract overstates B-FIT and leaves L4 unscoped** (l.55-58).
- "Fitted closed forms are \nBfitRatio times worse": only the Klinkenberg form was fitted. **Fix:** "a fitted closed form".
- "a small weight improves transfer by 9 %" omits that this holds on the material axis only, at a searched weight. The time axis shows no difference.

**m7. Neighbouring L4 weights and the selection adjustment** (l.1044-1046; RETRACTIONS A28 "Resolved").
- Per pair, w = 1e-6 and w = 1e-4 are both better than the twin.
- After selection adjustment, w = 1e-4 is **not**: simultaneous interval [-0.00021, 0.00170]. w = 1e-6 is: [0.00008, 0.00139].
- A28's "neighbouring decades also better, surviving selection: [0.00119, 0.00285]" can be read as both neighbours surviving. **Fix:** say that one does and one does not.

**m8. The "eliminated rungs" paragraph and the highlights are stale.**
- l.1605-1609: "every rung that was *eliminated* … beyond a small basis, a larger linear-reconstruction basis cost fit time and nothing else". L5's basis row is now "HELPS A LITTLE", not eliminated. The wording works if "beyond a small basis" carries the weight, but L5-basis should not sit in the "eliminated" list.
- `paper/highlights.txt` line 3: "Learning the parameter-to-field map binds the error; the basis does not". At p = 8 the basis binds (l.1097-1098). The highlights also never mention the coarse-solver result, which is now the paper's main practical message.

**m9. Contributions and "What binds" lack the small-basis qualifier** (l.221-224, l.1895).
- "the parameter-to-coefficient map, not the representation" and "not the basis it is expressed in" need "beyond a small basis". The abstract has that qualifier.
- The contributions list (l.210-229) also has no item for the pre-registered baselines (B-COARSE, B-FIT, B-GP), which the revised cost argument now depends on.

**m10. The reproducibility section undercounts verifiable pre-registrations** (l.1946-1950).
- Listed: L6, L1/L2/L7, L4b and the anchor.
- `PREREG_L5_v2.md` (commit 4ecc5d9, 2026-09-28) and `PREREG_BASELINES.md` (commit 073ad4d, 2026-10-04) were also committed before their runs. Git history confirms they predate `results/*_24k.json` and `coarse_solver_baseline.json`, which first appear in 54d73f3.
- That the B72 amendment to PREREG_L4b_v2 predates the v3 run is UNVERIFIED (not checked).

**m11. Fig. 1 verdict labels are hand-typed, not the pre-declared words** (`fig_ladder.py`).
- "HELPS AT SMALL WEIGHTS (B72 fixed)" and "HELPS A LITTLE (A29)" are literals in the figure script.
- The declared words are "PHYSICS HELPS once correctly weighted" and "basis size helps DeepONet on the 240-material design".
- The text says each verdict is reported "in pre-declared words" (abstract l.44). Either use the declared strings, abbreviated, or say in the caption that the labels are summaries.

---

## COSMETIC

- **c1.** l.1030-1031, "The legacy statement that physics as a loss hurts is withdrawn": B69 already withdrew it. Say "remains withdrawn".
- **c2.** l.1572, "the solver is both cheaper *and* exact": the reference has its own grid error (`\nGridConv`). Suggest "the reference".
- **c3.** l.1111 and l.1314, "The best DeepONet found anywhere": there are now two DeepONet designs. Add "on the legacy design".
- **c4.** Abstract l.59, "\nLedgerA withdrawn claims": the count of 30 now includes A30 ("Revised") and A28 ("Resolved"). Consider "withdrawn or revised".
- **c5.** The analyser's verdict string `\nLfourcVerdictMat` / `\nLfourbVerdictMaterial` ends "the legacy claim is RETRACTED as a weighting artefact". A28 attributes that withdrawal to the wrong residual (B72), not to weighting. The macro is not used in the manuscript, but it sits in `numbers.tex` and `results/l4b_v3_verdict.json`. `l4b_v3_selection.json`'s `_what` field still says "L4b-v2".

---

## C. Figure 1 (`figures/Fig1_ladder.png`) against the text

| Check | Result |
|---|---|
| L4b row | Point about 8.7 % with a bar of about 5.1-12.3 %. This matches the selection-adjusted interval [0.00119, 0.00285] / 0.0231. Labelled 48 clusters, material axis, selection-adjusted. The caption (l.818-819) says so. **OK** |
| L5 "a bigger basis" row | Point about 12 % with a bar of about 8.1-15.9 %. This matches [0.00088, 0.00173] / 0.01088. Labelled 240 clusters, selection-adjusted. **OK** |
| L4 time axis and refinement | Not drawn. They appear only in the row note ("no difference on the time axis" is in `fig_ladder.py`, but the rendered note shows only "best weight vs data-only twin…"). The text carries them. Acceptable, but the "larger or adaptive weights hurt; no difference on the time axis" note from `fig_ladder.py` does not appear in the PNG. Check that the note renders. |
| Caption "both L5 rows" selection-paid | Consistent with the PNG. |
| L7 label "CLOSED FORMS ELIMINATED" | The declared words are "LEARNING IS JUSTIFIED" (l.1249). B-FIT is not shown. Minor (see m11). |
| B-COARSE | Not in Fig. 1. That is defensible, since it is not a rung, but the abstract now leads with it. Consider a one-line note in the caption or a separate panel. |

---

## D. What a reticular or adsorption chemist would query

1. **The fitted Klinkenberg corrections are never reported in physical terms.** l.1255-1256 says the two multipliers are "physically interpretable", but their values are never given. In `fitted_classical.json` the fitted `log_mult_k` is about -1.64 to -1.68 on every fold: the rate constant is cut about 5x if natural log, about 45x if log10. `log_mult_K` is about +0.05. A chemist will read this as the Glueckauf LDF rate being far too fast for the Klinkenberg form. That is a physical finding about the dataset and should be stated with the log base.
2. **The coarse-solve accuracy is a whole-field nRMSE.** A 50-cell grid smears the cooperative pore-filling shock through numerical dispersion. That shock is the feature a harvester designer cares about. Quote the breakthrough-time (t50, t95) error of the N_z = 50 solves alongside 0.6 %, or state that nRMSE may hide front-position error. 7 of 240 coarse solves did not reach 0.9 c_in within the horizon; a chemist will ask whether the coarse grid shifts breakthrough.
3. **A residual weight of 1e-5 has no transferable meaning** unless the residual's scaling is stated. A reader cannot reuse "weight 1e-5" on another column. Say what the residual is normalised by, or present the result as "about 3 decades below the scale-balanced weight".
4. **"Materials" are parameter sets.** The new text says "a small weight improves transfer to unseen materials" and "coarse solve … every surrogate". Elsewhere the paper says "unseen adsorbent parameter sets" (title, l.1916). Use one term consistently in the new sentences; a chemist reads "unseen materials" as real frameworks.
5. **"The surrogate breaks even only after ~25 400 queries."** Screening libraries of hypothetical MOFs run to 10^4-10^5 entries, so this lands exactly in the regime chemists care about. Say so concretely (e.g. a CoRE-MOF-sized screen). That is the reader-useful version of "tens of thousands of candidates" (l.1587).
