# Prompt for a new session

Paste the block below. It is written to be self-contained: a session with no prior
context should be able to continue without losing standards or repeating settled work.

Rewritten 2026-09-07, after the session that built the manuscript and its build gates.

---

```
This is a research project aiming at the best possible paper for a top-tier journal.

THE STANDING RULE, above everything else: QUALITY OVER EVERYTHING, WHATEVER IT TAKES.
Time and compute are not constraints. Correctness and honesty are the only ones. If
something is good but could be better, make it better. If something is broken, fix it.
If the literature says there is a better way, use it. Never trade rigour for speed.
I want EVERYTHING that makes the work better — not only what blocks submission, but
the nice-to-have too. Work autonomously and keep going; you have permission to
continue without asking.

Start by reading, in this order:
  CONTINUE_HERE.md        current status, every headline number, what to protect
  RESULTS.md              every result, current
  RETRACTIONS.md          26 Part-A withdrawals, 64 Part-B defects caught pre-contamination
  CITATIONS.md            the citation gate, four tranches, the venue decision
  paper/manuscript.tex    the draft. Read paper/numbers.py before touching a number
  AUDIT_2026-08-30.md     the external audit and its evidence tags
  PREREG_L4b_v2.md        the rung in flight, and its pre-declared verdict words

Then run:  ./resume.sh          (reports state, runs nothing; it will TELL YOU if a
                                 chain is incomplete and nothing is running)
And:       git log --oneline    (the messages carry the reasoning)

WHAT THIS PROJECT IS. A pre-registered falsification ladder for surrogate models of
MOF adsorption column dynamics. The question is not "can a network fit breakthrough
curves" — it is WHAT ACTUALLY BINDS THE ERROR when a surrogate must predict a
material it has never seen, and which standard interventions move it.

It is NOT an architecture paper. L3 refuted the KAN premise on our own data and L5
refuted our own n-width explanation. Do not re-frame it as one.

WHAT IS SETTLED — do not redo, do not re-litigate:
  L0  reference verified against 4 closed-form solutions; van Genuchten & Alves is
      the right reference and B10 is confirmed by its own text
  L1  NOT ELIMINATED on v2. 0.0654 -> 0.0348 at 12 -> 192 materials, every step
      significant including the last, beta 0.222 [0.205, 0.239]. The fixed-basis
      curve is IDENTICAL, so all of the gain is the coefficient map. MLP is the best
      fixed-basis arm (0.0306), significant in every fold, 109x the POD floor
  L2  on v2: every optimum bracketed, but the optimum MOVED — an 8-layer MLP
      (0.0241) beats the L1 setting by 21.3 % [18.7, 23.7] where legacy found 1 %.
      Retraction A26. Wall stands at 86x the floor
  L3  FINAL. MLP beats both KAN families at matched parameters, 6/6 significant,
      every optimum bracketed across 8 learning rates over 3.5 decades
  L5  FINAL. DeepONet flat in basis size (4/4 paired intervals span zero) while its
      own bound falls 28.7x; FNO significantly better (0.0216 vs 0.0265) and STILL
      43x above the floor — the wall survives nonlinear reconstruction
  L6  RESOLVED on v2. The Damkohler mechanism is REFUTED (slope null, r = 0.04) but
      separate identification beats joint by 3.7 % (CI 1.0–6.5 %), reversing the
      legacy sign. Structure is an INDUCTIVE BIAS, not a kinetic identifier
  L7  eliminated on v2: the best closed form is 3.7x worse, paired over 240 materials
  Dataset v2  3947 sims, 240 materials, 17 conditions, Sobol, Glueckauf kinetics
  Anchor: the solver with the cited MOF-303 isotherm reproduces Lassitter 2024
      Fig. 10 with nothing fitted (t50 303 vs 287 min). Two named discrepancies.
  MDE: mde.py is the only implementation; use it for every null.

THE PAPER NOW EXISTS, AND SO DOES ITS BUILD SYSTEM. Read this before writing a number.
  paper/manuscript.tex   full CMAME draft, ten sections. Only the L4b subsection is a
                         placeholder, and it resolves itself when the run lands
  paper/numbers.py       EVERY quoted number, declared as (key, results file, dotted
                         path, formatter) and resolved at build time. 161 keys from
                         24 results files plus 9 derived ratios that carry their
                         formula. A missing file, a bad path or a non-finite value is
                         a HARD FAILURE. Adding a number to the paper means adding a
                         row here FIRST
  build_paper.py         refuses a manuscript containing an undefined macro, a
                         MANGLED macro (one that lost its backslash and became a
                         word), or a numeral that is neither a macro nor a declared
                         literal-with-a-reason. First run caught 57 hand-typed
                         numerals. Run it and CHECK ITS EXIT CODE, not its output —
                         a pipe to `tail` reports tail's status and once let a commit
                         through with the gate red
  paper/references.py    generates references.bib. Only VERIFIED entries are emitted;
                         a PARTIAL only when explicitly marked citable through a
                         NAMED secondary source; one entry is refused on every run.
                         47 keys are wired and every one resolves
  validate.py            24 gates. --json writes results/validation.json, and two
                         gates emit STRUCTURED values so the paper can read mass
                         closure and grid convergence instead of parsing a sentence
  ledger_counts.py, dataset_summary.py, isotherm_space.py — three more numbers that
                         used to be typed and are now counted

ELEVEN WORKING RULES. Each was earned by getting it wrong once; the retraction is named.
  1. No number from a failing validate.py category. (24 gates, all passing.)
  2. Matched training budget, ASSERTED not assumed. (A14, A16)
  3. >=3 seeds. Single-seed numbers appear nowhere, appendices included.
  4. Compare against the competitor's STRONGEST configuration. A selected
     hyperparameter on a grid edge is acceptable only if the metric has SATURATED
     there — measure it, never assume it. (B14, B22, B23, A20, and B60 where the
     rule was turned inward AGAIN inside the rung created to fix it)
  5. Never normalise by a quantity that can vanish. (A15, B34, B41, and again in
     isotherm_space.py's first version, which printed "inf decades")
  6. A gate that can be bypassed is not a gate. (B37; and B64, where the build gate
     could not see a break in the document it guards)
  7. NO NULL WITHOUT ITS MINIMUM DETECTABLE EFFECT. (A22: 7 % power)
  8. Nothing is cited until it has been FETCHED, not searched. (B35, A23, B42)
  9. Errors in the analysis are recorded on the same terms as errors in the code.
 10. NO NUMBER WITHOUT A SCRIPT. B21, B43 and B63 are the same defect three times,
     and all three ended in "the number was right" — these are not wrong numbers,
     they are UNOWNED ones, and a reader cannot tell them apart from wrong ones.
 11. NEVER EXPAND AN INITIAL. An author recorded as "E. Glueckauf" is written as
     "E. Glueckauf". B62: the bibliography generator invented eleven given names and
     a third author for a two-author paper — B35 by a different mechanism.

THINGS THAT WOULD DAMAGE THE PAPER — never do these:
  * Do not claim the two-wave warp is novel. Multi-front alignment is the founding
    example of shifted POD (Reiss, Schulze, Sesterhenn & MEHRMANN, SISC 40:A1322,
    2018), AND the map itself is textbook landmark registration whose two-landmark
    linear case IS our sigma. Claim the MEASUREMENT, not the map. (C2, B50)
  * Do not quote the oracle-warp number against any arm not also handed the warp.
  * Do not present DeepONet branch-dominance as new — Heinlein & Taraz got there
    first. Cite them and differentiate on the four axes in CITATIONS.md.
  * Do not cite Rigas or Kiyani for "KANs need different optimisation" — neither
    says it, and the KAN literature is SPLIT (KINN reports KAN beating MLP). B46.
  * Do not call our isotherm "the Do–Do form": theirs has an n-layer BET primary
    term, ours a Langmuir. "In the spirit of Do & Do". B56.
  * Do not attribute D_L = 0.7 D_m + 0.5 d_p u to Ruthven — it is Wakao & Funazkri,
    for NONPOROUS particles, and Perry's calls it a LOWER bound. B53.
  * Do not describe results as "MOF-303" beyond the cited parameters. C_ps has no
    citable source and is a 900–2400 J/kg/K band.

VENUE: CMAME. Free to publish (subscription route, green OA to arXiv). Fallbacks:
Separation & Purification Technology, then TMLR. ONE paper, not two.

STATE OF THE RUN, 2026-09-07 05:25 Istanbul:
  chain_l4b_v2.sh is IN FLIGHT at 44/66 sweep cells. It DIED ONCE — the machine
  rebooted 2026-09-06 22:54 and about twelve hours were lost before anyone noticed;
  that is the second such loss. ./resume.sh now says so at the top of its report.
  CHECK IT EVERY TIME. Do not run anything CPU-heavy alongside it.

  Already decided on the time axis, 11 arms complete: data_only (0.0131) beats every
  physics arm, monotonically with weight, +11.6 % at w=1e-4 to +754 % at w=1. That is
  PREREG Q1's first pre-declared outcome. Material axis in progress; the arms so far
  sit inside the seed spread.

NEXT ACTIONS, in order:
  1. WHEN THE CHAIN FINISHES (chain_l4b_v2_outer.log ends with L4B_V2_DONE), run
     ./chain_l4b_v2_followup.sh. It refuses to start otherwise. It does three things
     the pre-registration REQUIRES, not optional extras:
       (a) extends the fixed-weight sweep to w=1e-5. PREREG §4.2 binds because the
           time-axis optimum sits at the bottom edge (0.0146) and is NOT saturated
           against data_only (0.0131);
       (b) re-runs the analyser WITH its MDEs — the chain ends with --no-mde and
           rule 7 admits no null without one;
       (c) runs refine_sweep_l4b_v2.py, the labelled POST-HOC sweep for defect B60.
     Then write the verdict in PREREG_L4b_v2.md's pre-declared words, and regenerate
     fig_ladder.py and paper/numbers.py so the [PENDING] placeholder resolves.
     NOTE: a pre-declared invalidation condition has ALREADY FIRED (B61) — the
     time-axis anchor moved 643 % against a 10 % tolerance, so that axis is scoped
     and the MATERIAL axis carries the reportable Q3 verdict.
  2. Draft the manuscript's L4b subsection for all three pre-declared outcomes now,
     so landing the run is a substitution rather than a writing task.
  3. THE BIGGEST UNADDRESSED RISK: three rungs are still on the SMALL dataset.
     L3, L5 and the two-wave warp are measured over 12 held-out materials while L1,
     L2, L6 and L7 use 240. A26 exists precisely because a verdict measured at one
     material count did not survive four times as many. Re-measure at least L5's
     flat-in-p on v2 — it is the most load-bearing legacy number — and the warp,
     whose "no difference" is the weakest inference in the paper. Note B41: t_lo is
     degenerate on v2, so a v2 warp needs a non-degenerate lower landmark.
  4. Build the front-locating model. The warp's 2.17x headroom is a target nobody has
     shot at, and it would convert the paper's best negative into a positive.
  5. Remaining citations: verify everything the drafted bibliography actually cites.
     FIVE primaries cannot be retrieved electronically and need library access —
     B54 is LIVE on a reported result (which Klinkenberg paper carries L7's erf
     formula, 1948 or 1954), plus Glueckauf 1955, Do & Do Carbon 2000, Danckwerts
     1953, Anzelius/Schumann. Ask the author for these.
  6. Remaining housekeeping: run the C_ps 900–2400 band as an actual sensitivity;
     check the dataset's particle Peclet range against Edwards & Richardson (B53);
     write the amortised cost accounting (CMAME's premise); remove kaggle_run/ and
     SINDy; decide the COF framing.

Work autonomously. Report what you find, including when it contradicts something I or
a previous session believed — three headline verdicts have already been corrected that
way, and the correction ledger is the paper's strongest asset. Every commit message in
this repository carries the reasoning; write yours the same way.
```
