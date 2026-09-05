# Where does physical knowledge belong in a surrogate?

A pre-registered falsification ladder for surrogate models of MOF/COF adsorption
column dynamics.

The question is not "can a neural network fit breakthrough curves" — it can. The
question is **what actually binds the error when a surrogate is asked to predict a
material it has never seen**, and which of the standard interventions moves it.

Seven candidate answers were named in advance, each with the evidence that would
kill it, and then tested in order. Six were eliminated. The one that survives is a
change of coordinates, not a change of architecture.

---

## Read these, in this order

| file | what it is |
|---|---|
| **`RESULTS.md`** | every result, current. Start here. |
| **`03_LADDER_PROTOCOL.md`** | the pre-registered design, plus each rung's detail |
| **`RETRACTIONS.md`** | every claim withdrawn, why, and what replaced it |
| **`AUDIT_2026-08-30.md`** | external audit: literature position, defects, plan |
| **`CONTINUE_HERE.md`** | session handoff and open items |

`_WITHDRAWN_*.md` are superseded manuscript drafts, kept as provenance and
banner-marked with the retraction that killed each claim. **Do not cite them.**

### On the pre-registration claim, stated honestly

`03_LADDER_PROTOCOL.md` says it was frozen 2026-08-20, before any model was
trained. **That ordering is self-attested and cannot be verified**: this
repository was placed under version control on 2026-08-30, and results were
appended into the protocol file, so its timestamps do not establish it. Every
change from the baseline commit onward *is* timestamped and diffable. Follow-up
work will be registered externally before it is run. A reader should weight the
pre-registration accordingly.

---

## Reproducing

```bash
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
python validate.py                    # 22 gates; all must pass
```

`validate.py` is the entry point for trusting anything else here. It checks the
solver against four closed-form solutions, the isotherm against Clausius–Clapeyron,
the residual scaling, every architecture's output head, and the anti-fabrication
rules on the plotting code.

Then, in dependency order:

```bash
python verify_solver.py                        # L0: solver vs analytic limits
python gen_parametric_dataset.py               # ~1.6 GB, several hours on 8 cores
python run_l1.py && python analyze_l1.py       # ... through run_l7.py
python analyze_l5_merged.py                    # L5 across every lr file, with the
                                               #   grid-boundary guard
python make_figures.py
```

`data/*.npy` is gitignored and regenerable at the recorded seed. The **manifests
are tracked** — they carry the splits, the rejection tally and per-sample metadata
that cannot be recovered from the arrays.

---

## The rules this project runs on

These exist because each one was learned by getting it wrong. See `RETRACTIONS.md`.

1. **No number from a failing `validate.py` category** enters a manuscript.
2. **Matched training budget on both sides**, asserted rather than assumed.
   Extrapolation error *grows* with training here, so a shorter run flatters
   itself (retractions A14, A16).
3. **≥ 3 seeds.** Single-seed numbers may not appear anywhere, appendices included.
4. **Compare against the competitor's strongest configuration**, never the first
   one run. A selected hyperparameter sitting on the edge of its swept grid means
   the search did not bracket the optimum, and the margin is invalid (B14, B22,
   B23, A20 — five recurrences; `analyze_l5_merged.py` now guards it mechanically).
5. **Never normalise a metric by a quantity that can vanish**, and sanity-check
   that a reported value is *achievable* given the model's output range (A15).
6. **A gate that skips protects nothing.** Verify each one fires.
7. **Stop hypothesising, measure the term** (B10, B21).
8. **Errors made by the analysis are recorded on the same terms as errors in the
   code.** Most of the Part-B ledger is our own.

---

## Status

All eight rungs have run on the legacy dataset; L1, L2, L6 and L7 have been re-run
on dataset v2 under pre-registrations committed before each run
(`PREREG_L6_v2.md`, `PREREG_L1L2L7_v2.md`). On v2, "more materials" is **not**
eliminated (error still falls as n^−0.22 at 192 training materials, all of it in the
coefficient map), the MLP is the best fixed-basis arm, its optimal depth grows with the material
count (8 layers, 21 % better than the L1 setting: A26), and learning beats every
closed form 3.7×. One solver-vs-experiment comparison exists
(`PREREG_LASSITTER.md`, no parameter fitted). L4b on v2 is pre-registered
(`PREREG_L4b_v2.md`) and queued. See `CONTINUE_HERE.md` for the current state and
`RETRACTIONS.md` for everything withdrawn (26 Part-A, 44 Part-B).

## Licence

Code MIT (`LICENSE`). Please cite via `CITATION.cff` if you use any of it.
