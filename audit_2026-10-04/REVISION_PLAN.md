# Revision plan — response to the 2026-10-04 referee report

Source: `audit_2026-10-04/referee_report.md` (internal hostile review, recommendation:
major revision). Every item is re-verified by hand before it is acted on; a referee
point that does not survive verification is answered, not obeyed.

Status words: OPEN, DONE (commit), ANSWERED (not changed, reason given), BLOCKED (on what).

## Tier A — text that is wrong, stale or under-reported (no compute)
| # | Item | Status |
|---|---|---|
| A1 | M5 "eliminated" list (l.1069-1074) contradicts L2 NOT ELIMINATED and L4 material | OPEN |
| A2 | M5 "unlearnable beyond about five modes" stale vs A21 | OPEN |
| A3 | M5 "the one rung" with verifiable prereg ordering vs four listed | OPEN |
| A4 | M5 L3 [PENDING]: gate marker absent because the run was killed; re-run in queue | BLOCKED (L3 job, running) |
| A5 | M5 "No number typed by hand" is false; macro the listed numbers or narrow the claim | OPEN |
| A6 | M4 pre-registered test-time refinement result (5-7x WORSE) promised, never reported | OPEN |
| A7 | M8 third design (L4 single 48-material split); abstract omits L4, L7 | OPEN |
| A8 | M6 L6 Da null: state slope bound relative to effect, MDE, soften words | OPEN |
| A9 | M2a warp "nothing at all"/"powered" overclaim on 12 clusters | OPEN |
| A10 | M9 L2 "optimum moves with data" not supported (width moved down) | OPEN |
| A11 | M14 FNO>DeepONet margin marginal; say so | OPEN |
| A12 | minor 1 broken "accuracy of 4" sentence; oracle rank is p=8 not p=128 | OPEN |
| A13 | minor 2 abstract landmark pair 31->17 vs 13 | OPEN |
| A14 | minor 3 Fig 5 caption "every arm is flat" incl. FNO | OPEN |
| A15 | minor 4 eligible count is time-axis (7) not material (8) | OPEN |
| A16 | minor 5 L-BFGS WORSENED both arms on material axis | OPEN |
| A17 | minor 6-13, 17 | OPEN |

## Tier B — analysis on existing per-sample errors (cheap compute)
| # | Item | Status |
|---|---|---|
| B1 | M3 selection on the test set: max-statistic (selection-adjusted) bootstrap over all eligible arms for L4 material; same for L2 best-of-28, L5 FNO cell | OPEN |
| B2 | M6 MDE for the L6 Da slope | OPEN |
| B3 | M1/M2b one table, one encoding: POD+regressor, DeepONet, DeepOKAN, FNO, oracle warp (check encodings match) | OPEN |

## Tier C — new experiments (queued, one training job at a time)
| # | Item | Status |
|---|---|---|
| C1 | M3 nested selection (inner validation split on training materials) for L4 material axis | OPEN — cost first |
| C2 | M11b GP regression on POD coefficients (240 materials) | OPEN |
| C3 | M11a coarse-grid solver at matched accuracy, for the cost section | OPEN |
| C4 | M11c fitted per-material classical model for L7 | OPEN |
| C5 | M13 second experimental anchor (Al-fumarate stepped breakthrough, Bozbiyik) — needs digitised data | OPEN |
| C6 | M10 place real water MOFs (MOF-303, MOF-801, CAU-10, Al-fumarate) in the parameter space — needs cited isotherm/kinetic values | OPEN |

## Tier D — framing and structure
| # | Item | Status |
|---|---|---|
| D1 | M7 Methods section: equations, nRMSE, Da, parameter table, surrogates, encodings per rung, cross-rung non-comparability | OPEN |
| D2 | M10 retitle ("parameter sets", not "unseen MOFs"); parametric-ROM and PSA-surrogate prior art (each through the provenance gate) | OPEN |
| D3 | M1 restate "what binds": the map, as learned; learner class is a ~2x lever | OPEN — after B3 |
| D4 | M12 two-wave narrative scoped to the legacy design | OPEN |
| D5 | minor 14-16 length (corrections to SI), glossary box, schematic figure, venue | OPEN |
