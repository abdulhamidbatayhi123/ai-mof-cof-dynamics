# Prompt for a new session

Paste the block below. It is written to be self-contained: a session with no prior
context should be able to continue without losing standards or repeating settled work.

---

```
This is a research project aiming at the best possible paper for a top-tier journal.

THE STANDING RULE, above everything else: QUALITY OVER EVERYTHING, WHATEVER IT TAKES.
Time and compute are not constraints. Correctness and honesty are the only ones. If
something is good but could be better, make it better. If something is broken, fix it.
If the literature says there is a better way, use it. Never trade rigour for speed.

Start by reading, in this order:
  CONTINUE_HERE.md        current status, every headline number, what to protect
  RESULTS.md              every result, current
  RETRACTIONS.md          26 Part-A withdrawals, 44 Part-B defects caught pre-contamination
  AUDIT_2026-08-30.md     the external audit and its evidence tags
  CITATIONS.md            the citation gate and the venue decision
  PREREG_L6_v2.md         a pre-registration committed to git before its run

Then run:  ./resume.sh          (reports state, runs nothing)
And:       git log --oneline    (the messages carry the reasoning)

WHAT THIS PROJECT IS. A pre-registered falsification ladder for surrogate models of
MOF/COF adsorption column dynamics. The question is not "can a network fit
breakthrough curves" — it is WHAT ACTUALLY BINDS THE ERROR when a surrogate must
predict a material it has never seen, and which standard interventions move it.

It is NOT an architecture paper. L3 refuted the KAN premise on our own data and L5
refuted our own n-width explanation. Do not re-frame it as one.

WHAT IS SETTLED — do not redo, do not re-litigate:
  L0  reference verified against 4 closed-form solutions
  L3  FINAL. MLP beats both KAN families at matched parameters, 6/6 significant,
      every optimum bracketed across 8 learning rates over 3.5 decades
  L5  FINAL. DeepONet flat in basis size; FNO significantly better (0.0216 vs
      0.0265) but still 43x above the POD floor — the wall survives nonlinear
      reconstruction
  L6  RESOLVED on dataset v2. The Damkohler mechanism is REFUTED (slope null,
      r=0.04) but separate identification does beat joint by 3.7% (CI 1.0-6.5%),
      reversing the legacy sign. Structure acts as an INDUCTIVE BIAS, not a
      kinetic identifier
  Dataset v2  3947 sims, 240 materials, Sobol sampling, Glueckauf kinetics
  L1/LC/L7 on v2 (2026-09-03, PREREG_L1L2L7_v2.md, same folds as L6-v2): the
      materials axis is NOT ELIMINATED at 192 materials (0.0654 -> 0.0348 at
      12 -> 192, every step significant, beta 0.222 [0.205, 0.239]); the fixed-basis
      curve is identical, so ALL of the gain is the coefficient map (A21 confirmed);
      the MLP is now the best fixed-basis arm (0.0306, significant in every fold);
      learning beats the best closed form 3.7x. Do not re-run.
  Anchor: the solver with the cited MOF-303 isotherm reproduces Lassitter 2024
      Fig. 10 (6.35 mm bed) with nothing fitted: t50 303 vs 287 min, plateau 0.34 vs
      0.27. Two named discrepancies (early first wave = isotherm low-RH branch; shock
      too dispersed = Ruthven closure on a 1-2-pellet bed). PREREG_LASSITTER.md.
  MDE: A25 corrected the power simulation (sqrt 2 noise inflation); L6-v2 has 82 %
      power at 4 %. mde.py is the only implementation; use it for every null.
  L2 on v2 (2026-09-04, 420 cells): every optimum bracketed (w64, d8, md6; the forest
      at its ceiling), but the optimum MOVED: an 8-layer MLP (0.0241) beats the L1
      setting by 21 % (CI 19-24 %) where legacy found 1 % -- retraction A26 scopes
      "capacity is irrelevant" to 48 materials. Wall stands: 86x the POD floor.

NINE WORKING RULES. Each was earned by getting it wrong once; the retraction is named.
  1. No number from a failing validate.py category. (22 gates, all passing.)
  2. Matched training budget, ASSERTED not assumed. (A14, A16)
  3. >=3 seeds. Single-seed numbers appear nowhere, appendices included.
  4. Compare against the competitor's STRONGEST configuration. A selected
     hyperparameter on a grid edge is acceptable only if the metric has SATURATED
     there — measure it, never assume it. (B14, B22, B23, A20)
  5. Never normalise by a quantity that can vanish. (A15, and again in B34)
  6. A gate that can be bypassed is not a gate. (B37: a keyword default defeated one)
  7. NO NULL WITHOUT ITS MINIMUM DETECTABLE EFFECT. (A22 exists because one was
     quoted without one and the design turned out to have 7% power)
  8. Nothing is cited until it has been FETCHED, not searched. (B35, A23)
  9. Errors in the analysis are recorded on the same terms as errors in the code.

THINGS THAT WOULD DAMAGE THE PAPER — never do these:
  * Do not claim the two-wave warp is novel. Multi-front alignment is the founding
    example of shifted POD (Reiss, Schulze, Sesterhenn & MEHRMANN, SIAM J. Sci.
    Comput. 40:A1322, 2018). Claim the MEASUREMENT, not the map. See A23.
  * Do not quote the oracle-warp number (0.0203) against any arm not also handed
    the warp. It leaks the answer.
  * Do not present DeepONet branch-dominance as new — Heinlein & Taraz (arXiv:
    2602.21910, Feb 2026) got there first. Cite them and differentiate on the four
    axes written in CITATIONS.md.
  * Do not describe results as "MOF-303" beyond the cited parameters. rho_p, eps_t
    and C_ps are NOT MOF-303 measurements; C_ps has no citable source at all and
    must be reported as a 900-2400 J/kg/K sensitivity band.

VENUE: CMAME. Free to publish (subscription route, green OA to arXiv — the author is
a student with no APC funding), IF ~7, and every paper L3 argues with is in CMAME.
Fallbacks: Separation & Purification Technology, then TMLR. ONE paper, not two.

NEXT ACTIONS, in order:
  1. L4b on v2 is RUNNING (launched 2026-09-05 00:57 Istanbul; ~50 h; chain_l4b_v2.sh,
     resumable with ./resume.sh go). When it finishes, read l4b_v2_analysis.log and write
     the verdict in PREREG_L4b_v2.md's pre-declared words. Do not run anything else
     CPU-heavy while it runs.
  2. While L4b runs (I/O only): citation verification tranche 4 (see the list in
     MANUSCRIPT_OUTLINE.md), the ladder schematic figure (F1), and the manuscript
     draft from MANUSCRIPT_OUTLINE.md, in the voice of RESULTS.md.
  3. Citation verification, tranche 3 onward (~225 remain). The anchor is done;
     the Henry-branch discrepancy it exposed is a limitation to write, not to fix by
     tuning.
  4. Figures: Fig8 (learning curve), Fig9/9b (anchor), Fig10 (mechanism) and Fig11
     (two-wave warp) exist, every series from results files. Still to do: the ladder
     schematic (F1, after L2/L4b) and re-authoring Fig1-7 to column width.
  5. Draft the manuscript as a falsification ladder. The negative results are the
     contribution, not gaps.

Work autonomously. Report what you find, including when it contradicts something I or
a previous session believed — three headline verdicts have already been corrected that
way, and the correction ledger is the paper's strongest asset.
```
