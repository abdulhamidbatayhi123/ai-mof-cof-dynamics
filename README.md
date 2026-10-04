# What binds a surrogate?

A pre-registered falsification ladder for surrogate models of metal–organic-framework
water-adsorption columns.

Surrogates of adsorption columns are usually judged by how well they fit. This project
asks a different question: **when a surrogate must predict an adsorbent it has never
seen, what binds its error, and which of the standard interventions moves it?** Seven
candidate explanations were named in advance — more data, more capacity, a richer
edge basis (Kolmogorov–Arnold networks), a physics residual in the loss, operator
learning, structural identification of the kinetic and equilibrium objects, and
whether learning is needed at all — each with the evidence that would eliminate it,
and tested in order on a verified reference solver.

The answers, in the paper's pre-declared words, are in **`paper/manuscript.pdf`**
(built from `paper/manuscript.tex`). This README deliberately quotes no numbers: every
number in this project is a macro resolved from a results file by a script, and the
paper is where they are kept current.

---

## Where to look

| file | what it is |
|---|---|
| `paper/manuscript.pdf` | the paper. Start here. |
| `paper/si_ledger.pdf` | Supplementary S1: every withdrawn claim (A) and caught defect (B), generated from `RETRACTIONS.md` |
| `RETRACTIONS.md` | the correction ledger itself |
| `PREREG_*.md` | the pre-registrations, each frozen by a commit before its runs; amendments dated |
| `paper/numbers.py` | where every number in the paper comes from (file and path) |
| `audit_2026-10-04/` | the internal referee report and the revision plan answering it |
| `PREREG_P2_discoverability.md`, `paper2/` | Paper 2 (when can AI discover adsorption kinetics?), a Registered Report in preparation |

### On the pre-registrations, stated honestly

The original protocol (`03_LADDER_PROTOCOL.md`) is **self-attested**: the repository
was placed under version control after it was written, so its ordering cannot be
verified. Every later pre-registration (`PREREG_L6_v2.md`, `PREREG_L1L2L7_v2.md`,
`PREREG_L4b_v2.md`, `PREREG_L5_v2.md`, `PREREG_LASSITTER.md`, `PREREG_WARP_v2.md`,
`PREREG_BASELINES.md`) was committed before the runs it governs, and that ordering is
checkable in the git history. The paper says which is which.

---

## Reproducing

```bash
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
python validate.py               # the verification harness; every gate must pass
python build_paper.py --pdf      # resolves every number from its results file and compiles
```

`validate.py` is the entry point for trusting anything else here. Among its gates: the
solver against closed-form solutions, the isotherm against Clausius–Clapeyron, the
**training residual against the solver's own equation** (coefficient by coefficient),
every network's output head, and anti-fabrication rules for every plotting script.

`build_paper.py` refuses to build if any number in the manuscript is not a macro from
a results file, if an allowed literal appears in a new place, if a number written as a
word is unreviewed, if a citation lacks verified provenance, or if any results file
has no script that writes it.

Datasets (`data/*.npy`) are regenerable at the recorded seeds
(`gen_parametric_dataset.py`); the **manifests are tracked** because they carry the
splits, the rejection tally and the per-sample metadata.

---

## The rules this project runs on

Each was learned by getting it wrong; the ledger records each time.

1. **No number from a failing `validate.py` category** enters a manuscript, and no
   number enters it by hand.
2. **Matched training budget on both sides**, asserted rather than assumed.
3. **At least three seeds**, everywhere.
4. **Compare against the competitor's strongest configuration.** An optimum on the
   edge of a swept grid is extended before it is believed.
5. **Never normalise a metric by a quantity that can vanish.**
6. **A gate that cannot fire protects nothing** — every gate is tested by planting
   the defect it guards against.
7. **A model of the physics written separately from the solver is checked against
   the solver.** (The physics residual of one rung was not, for most of the project's
   life, and moved the gas at the wrong velocity: ledger B72.)
8. **A best-of-grid choice made on the test data carries its selection** into the
   interval that reports it.
9. **Errors made in the analysis are recorded on the same terms as errors in the code.**

## Licence and citation

Code: MIT (`LICENSE`). Please cite via `CITATION.cff`.
