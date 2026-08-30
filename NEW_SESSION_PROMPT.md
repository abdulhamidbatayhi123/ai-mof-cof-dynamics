# Prompt for a new session

Copy everything inside the block below into a fresh Claude Code session opened in
`C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics`.

Last refreshed 2026-08-24, after L5 completed.

---

```
We are continuing a computational adsorption-science project aimed at a top-tier
journal paper. Please start by reading CONTINUE_HERE.md in full, then RESULTS.md,
then 03_LADDER_PROTOCOL.md. RETRACTIONS.md is the ledger of every claim we have
withdrawn — read it too, because it encodes the mistakes you must not repeat.

THE GOAL
A falsification-ladder study of physics-informed surrogates for MOF/COF adsorption
column dynamics, at a standard that survives hostile peer review. The thesis the
evidence produced is: "Where should physical knowledge enter a surrogate — as
structure, or as a penalty — and when does structure actually pay?" Do NOT
re-frame this as an architecture paper; we refuted the PIKAN/DeepOKAN premise on
our own matched-parameter data (L3), and we refuted our own n-width explanation
on our own operator data (L5, retraction A17).

THE RULE, above everything else
Quality over speed, always. Specifically, and this is not negotiable because
violating it has already cost us 17 retracted claims:

  VERIFY FIRST, REPORT SECOND. Before you state any number to me, it must have:
  (1) matched training budget on both sides of every comparison,
  (2) a metric whose reported value is ACHIEVABLE given the model's output range,
  (3) at least 3 seeds — the frozen protocol minimum, checked against the WRITTEN
      rule and not against your own rationale for departing from it (defect B23),
  (4) a paired, cluster-robust CI at the calibrated alpha = 0.005,
  (5) the competitor at its STRONGEST configuration, not its first.

  When something looks wrong, stop hypothesising and measure the term directly.

  Record every withdrawn claim in RETRACTIONS.md, including your own analysis
  errors, on the same terms as errors in the code. 15 of our 36 Part-B 
  are our own errors. That ledger is the project's main credibility asset.

STATUS
All 8 rungs are complete. 22/22 validate.py gates pass. The headline result is
L5: the Kolmogorov n-width bound we had called "the load-bearing result of the
ladder" is real and completely INACTIVE — DeepONet sits 59x above it and does not
move as the bound falls 28.7x. We then measured what actually binds: the
parameter -> POD-coefficient map carries about five modes' worth of generalisable
information out of 128, so DeepONet at any basis size performs like a 4-mode
reconstruction.

IMMEDIATE ACTION
One narrow confirmation run may still be in flight — check `tail -20
l5_refine.log`. CONTINUE_HERE.md section 3 says exactly what it tests, what to do
if it died, and why nothing else depends on it.

ENVIRONMENT
Use this interpreter for everything; the default `python` on PATH lacks numpy:
  "C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
Prefix long-output commands with PYTHONIOENCODING=utf-8 or em-dashes corrupt.
Do NOT write Python files with bash heredocs — two attempts corrupted the file.
Run `python validate.py` — 22 gates must pass. No number from a failing category
may enter the manuscript.

Compute is CPU-only here plus Kaggle GPU (I can run things on Kaggle if useful —
just tell me what to upload). Put long jobs in the background so we can work in
parallel, and give each one its OWN output path (a stale background process once
clobbered a results file — defect B15).

WHAT COMES NEXT
CONTINUE_HERE.md section 8 has the ordered list. The scientifically highest-value
item is the co-moving frame experiment: it is the ONLY intervention the ladder has
not eliminated, and L5 says precisely why it should work. It would turn a paper of
six negative results into one with a positive result that the negatives motivate.

Please confirm you have read the four documents and give me your own summary of
where the project stands before doing anything else.
```
