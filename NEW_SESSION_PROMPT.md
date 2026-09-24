# Prompt for a fresh session

Copy everything between the lines into the new session as your first message.

---

This is a research project aiming at the best possible paper for a top-tier journal.

THE STANDING RULE, above everything else: QUALITY OVER EVERYTHING, WHATEVER IT TAKES.
Time and compute are not constraints. Correctness and honesty are the only ones. If
something is good but could be better, make it better. If something is broken, fix it.
If the literature says there is a better way, use it. Never trade rigour for speed.
I want EVERYTHING that makes the work better — not only what blocks submission, but
the nice-to-have too. Work autonomously and keep going; you have permission to
continue without asking.

Start by reading, in this order:
  CONTINUE_HERE.md          status, the run in flight, what is open, what is settled
  audit_2026-09-24/         SIX AUDIT REPORTS, 133 findings, ~111 still open.
                            Read them. Do NOT re-derive them. Each carries file,
                            line, the offending text, why it matters, and the fix.
  RESULTS.md                every result, current
  RETRACTIONS.md            26 Part-A withdrawals, 64 Part-B defects
  CITATIONS.md              the citation gate, four tranches, the venue decision
  paper/manuscript.tex      the draft. Read paper/numbers.py before touching a number
  PREREG_L4b_v2.md          the rung in flight, and its pre-declared verdict words

Then run:  ./resume.sh      (reports state, runs nothing; it TELLS YOU if a chain is
                             incomplete and nothing is running — check this EVERY time,
                             the chain has died twice and once lost twelve hours)
And:       git log --oneline | head -20        (the messages carry the reasoning)

Use this python, not the one on PATH:
  "C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"

WHAT THIS PROJECT IS. A pre-registered falsification ladder for surrogate models of
MOF adsorption column dynamics. The question is not "can a network fit breakthrough
curves" — it is WHAT ACTUALLY BINDS THE ERROR when a surrogate must predict a
material it has never seen, and which standard interventions move it.

It is NOT an architecture paper. L3 refuted the KAN premise on our own data and L5
refuted our own n-width explanation. Do not re-frame it as one. The negative results
are the contribution, and the correction ledger is the paper's strongest asset.

COMPUTE IS RUNNING ITSELF. `autorun.sh` is a queue that survives this session
dying, a job being killed, and a reboot (a launcher in the Startup folder, which
removes itself when the queue completes). Check it, do not restart it:

    cat autorun_state.json     # heartbeat: what is running, since when
    tail -30 autorun.log       # per-job START/DONE/FAIL with exit codes
    ./resume.sh                # the project's own state report

The queue is: (1) chain_l4b_v2_followup.sh, ~20 h, five stages; (2)
l5_bottleneck_v2.py, ~1-2 h; (3) regenerate figures + numbers + build gate. It runs
ONE job at a time on purpose -- both L4b runners rewrite the whole results dict, so
two writers lose all 66 completed cells. DO NOT launch a training job by hand while
it is alive; add it to the queue in autorun.sh instead, with a done-test.
`AUTORUN_QUEUE_DONE` in autorun.log means the queue finished. Check every FAIL line.

THE IMMEDIATE JOB, in order (CONTINUE_HERE.md §4 has the full list):
  1. When the follow-up lands, write the manuscript's L4b section. It is PROSE, not
     a macro, so regenerating numbers.tex cannot resolve "[SECTION PENDING]". The
     time-axis verdict is probably CHANGING (w=1e-5 ties the data-only twin where
     w=1e-4 was clearly worse) — if it does, that is a retraction and it goes in
     RETRACTIONS.md on the same terms as a code defect. Then recount the abstract's
     "Six are eliminated".
  2. audit_citations.md #2 — B62 HAS RECURRED. Thirteen invented given names in
     references.bib. Working rule 11 ("NEVER EXPAND AN INITIAL") is currently broken.
  3. audit_hygiene.md — six solver gates PASS when their dataset is absent, proven
     empirically, and both ground-truth .npz files are gitignored, so that is the
     state of every clone. Rule 6: a gate that can be bypassed is not a gate.
  4. Add a Conclusions section. CMAME expects one and the central claim is never
     assembled in one place.
  5. The three rungs still on 12 materials (L3, L5, the warp) while L1/L2/L6/L7 use
     240 — the biggest structural risk, because retraction A26 exists precisely
     because a verdict measured at one material count did not survive four times as
     many. The cheapest of the three (l5_bottleneck on v2) is ALREADY QUEUED as
     autorun job 2 — do not launch it by hand, just read its result when it lands
     and write it up. The other two (DeepONet flat-in-p on v2, 26-39 h; the warp
     verdict, 10-30 h and needing a non-degenerate lower landmark because B41 makes
     t_lo rule-5 degenerate on v2) still need their runners PORTED, which is the
     real work. audit_risk.md scopes both, with file:line for every change.

ELEVEN WORKING RULES — each earned by getting it wrong once, all in CONTINUE_HERE.md
§6. The two that bite hardest: NO NULL WITHOUT ITS MINIMUM DETECTABLE EFFECT, and NO
NUMBER WITHOUT A SCRIPT (an unowned number is indistinguishable from a wrong one —
this has now happened four times, and all four times the number turned out to be
right, which is exactly why it is not a defence).

THE BUILD SYSTEM. Every quoted number is a macro resolved at build time from a named
results file through a declared path. Adding a number to the paper means adding a row
to paper/numbers.py FIRST. Run `python build_paper.py` and CHECK ITS EXIT CODE, not
its output — a pipe to `tail` reports tail's status and once let a commit through
with the gate red.

Report what you find, including when it contradicts something I or a previous session
believed — several headline verdicts have already been corrected that way. Every
commit message in this repository carries the reasoning; write yours the same way.

---
