# CONTINUE HERE — session handoff

Written 2026-08-24. Read this first, then `RESULTS.md`, then
`03_LADDER_PROTOCOL.md`. `RETRACTIONS.md` is the record of everything withdrawn.

---

## 1. What this project is now

It began as *"Foundation Digital Twins for MOFs and COFs"* — PIKAN + DeepOKAN +
neural operators + SINDy. **The evidence has moved it somewhere else**, and the
new position is stronger and better supported:

> **Where should physical knowledge enter a surrogate — as structure, or as a
> penalty — and when does structure actually pay?**

Adsorption in MOF/COF columns is the testbed. The answer is specific and
measured: **hard structural constraints pay; soft physics penalties pay only in a
narrow regime; structural decomposition pays only when the structure is
non-degenerate; and richer function bases do not pay at all, because the binding
constraint is elsewhere.**

Do not re-frame this as an architecture paper. L3 refuted the KAN premise on our
own data, and L5 refuted our own n-width explanation.

---

## 2. Status at handoff

```
22 validate.py gates passing, 0 failing
21 Part-A retractions (claims withdrawn) · 33 Part-B defects (caught pre-contamination)
15 of the Part-B defects are our own errors — in analysis, gates, or the protocol
ALL 8 RUNGS COMPLETE
```

| rung | question | verdict |
|---|---|---|
| L0 | is the reference trustworthy? | ✅ verified vs 4 closed-form solutions |
| L1 | more data? | ✅ eliminated |
| L2 | more capacity? | ✅ eliminated |
| L3 | better basis (KAN)? | ✅ eliminated — **refuted**, not null |
| L4 / L4b | physics as a loss? | ✅ axis-specific; **hurts** once bounds exist |
| L5 | operators / n-width? | ✅ eliminated — **our own prediction refuted** |
| L6 | separate identification (H1)? | ✅ **NOT SUPPORTED** |
| L7 | is learning needed at all? | ✅ eliminated — learning wins 3.2× |

### Headline numbers (novel-material split unless noted)

| finding | number |
|---|---|
| best data-driven arm (L1) | 0.0485 nRMSE(c), 33× above the POD floor |
| KAN vs MLP at matched params (L3) | MLP better at **every** budget, 8/9 significant |
| physics-as-loss, time axis (L4b) | 0.1425 → 0.0639 — **helps** |
| physics-as-loss, once bounds exist | 0.0124 → 0.0194 — **hurts** |
| hard output bounds (L4b) | 11.5× on time, +25% on materials — best single intervention |
| **DeepONet vs basis size (L5)** | **0.0281 → 0.0296 while the floor falls 28.7×** |
| **DeepONet's effective rank (L5)** | **~4 modes, whether given 8 basis functions or 128** |
| **coefficient map R² (L5)** | **0.946 on mode 1; median −0.014 beyond mode 24** |
| DeepOKAN training collapse (L5) | 10/45 runs; DeepONet 0/45 |
| classical closed-form (L7) | 0.2307 vs learned 0.0725 — learning justified |
| H1, joint vs separate (L6) | diff −0.0155, CI [−0.045, +0.014] — **not supported** |
| Kolmogorov n-width | algebraic, d_n ~ n^−1.23 — real, and **inactive** |
| Damköhler over the run | median **626** → near local equilibrium |

---

## 3. THE FIRST THING TO DO

**A confirmation run may still be in flight.** Check it:

```bash
tail -20 l5_refine.log
```

It sweeps two extra learning rates (`2e-4`, `5e-5`) at p = 64 and 128 only, 24
runs, ~4 h, writing `results/l5_refine.json` and touching nothing else. Its
purpose is narrow: to confirm that **DeepOKAN's degradation at large p is real and
not an artefact of a 3-point learning-rate grid.** Everything else in L5 is
already settled and does not depend on it.

When it finishes:

```bash
python analyze_l5.py results/l5_refine.json
```

If any DeepOKAN configuration at p = 64 or 128 beats the recorded 0.0818 / 0.0884,
update the L5 DeepOKAN column in `03_LADDER_PROTOCOL.md` and `RESULTS.md`. **The
DeepONet result and the whole bottleneck analysis are unaffected either way** —
DeepONet's optimum is `lr = 1e-3` and the trend below it is strictly monotone
(p = 64: 0.0296 → 0.0370 → 0.0446 → 0.0504 as lr falls 1e-3 → 3e-4 → 2e-4 → 1e-4).

If it died, re-launch:

```bash
python run_l5.py --ps 64 128 --seeds 42 43 44 --lrs 2e-4 5e-5 --steps 8000 --budget 200000 --out results/l5_refine.json
```

**Never analyse `results/l5_singlelr_WITHDRAWN.json`** — one learning rate for
both families, KAN stack saturated (defect B22).

---

## 4. What L5 found, and why it is the strongest result in the project

The protocol's §6d called the Kolmogorov n-width **"the load-bearing result of the
ladder"** and pre-registered the prediction that DeepONet error would fall
algebraically with basis size `p`, tracking the POD floor.

**It does not move at all.** 0.0281 → 0.0296 over p = 8 → 128, all four paired CIs
including zero, while the floor falls 28.7×. At p = 128 DeepONet sits **59× above
its own lower bound**. Train error is flat too, so it is not a generalisation
artefact — the model cannot use the extra modes on data it has already seen.

**The reason was then measured, not inferred** (`l5_bottleneck.py`). Splitting the
error of a linear reconstruction into its two terms, in the *optimal* basis:

- basis error with true coefficients falls 28.7× (it is the floor, by definition)
- **coefficient-map error is flat at 0.051** across the same range

Per mode, the params → coefficient map scores R² = 0.946 on mode 1, 0.39–0.58 on
modes 2–5, and a **median of −0.014 beyond mode 24** — worse than predicting the
mean. Calibrated against an oracle given true coefficients for its first k modes,
**DeepONet at any p performs like a 4-mode reconstruction.**

Three independent function classes — POD+rf (the L1 audit), POD+HGB, and
DeepONet — are all flat in rank against a floor that falls ~28×. The L1 audit had
already shown this signature and it was read as an L1-specific result. It was the
general diagnosis all along. See retraction **A17**.

**Where this points.** Every remaining lever inside the linear-reconstruction
family is now eliminated: data (L1), capacity (L2), edge basis (L3), basis size
(L5). The obstruction is that the parameter → coefficient map carries about five
modes' worth of generalisable information.

The obvious remedy — a **co-moving frame** — has now been tested and **refuted**
(`comoving.py`, protocol section "CO-MOVING FRAME"). It makes the n-width *worse*
(31 → 102 modes for 99.9 % when aligning on the 0.5 crossing) and loses to the
fixed frame even when handed the exact front trajectory for free (0.0534 vs
0.0510). The reason was measured, not assumed: the separation between the fast
Henry wave and the cooperative shock varies **40-fold** across the dataset
([0.025, 0.992] normalised time), so one shift cannot straighten two waves.

**What remains open** is a *two-parameter* warp that aligns both waves
independently. That is what the gap measurement points at, and it has not been
tried.

---

## 5. Traps — every one of these was hit at least once

1. **Matched training budget, always.** Extrapolation error *grows* with training,
   so a shorter run flatters itself. Produced **A14** and **A16** — the same
   confound in consecutive experiments.
2. **Never normalise a metric by something that can vanish.** Produced **A15**:
   four "divergence to nRMSE 26,000" results that were arithmetically impossible
   for a bounded model. Sanity-check that a reported value is *achievable*.
3. **Compare against the STRONGEST competitor config**, never the first one run.
   This has now happened FOUR times: `MLPRegressor` on unscaled POD coefficients
   (**B14**), KAN hyperparameters in L3 (audited in time), one learning rate
   across two operator families (**B22**), and a 3-point lr grid that may not
   bracket DeepOKAN's optimum at large p (the run in §3 exists to close that).
4. **Check the scoring rule against the WRITTEN protocol, not against its own
   rationale.** **B23**: a 2-surviving-seed rule was chosen specifically to be
   generous to the arm being argued against — and still violated the frozen
   3-seed minimum, understating the effect by ~35 % while feeling conservative.
5. **A gate that skips protects nothing.** Verify each gate *fires* by planting a
   violating file.
6. **Background runs can clobber each other's output files.** Produced **B15**.
   Every rung's analyzer now has `assert_wellformed`, and figures call it too.
7. **Stop hypothesising, measure the term.** **B10** and **B21** burned multiple
   wrong hypotheses before a direct measurement found the cause in one step.
   L5's bottleneck analysis is the positive version of this lesson.
8. **Do not compare absolute numbers across rungs.** Different function classes,
   supervision and encodings. `l5_bottleneck.py` deliberately recomputes the POD
   baseline at L5's own 128×128 encoding so that comparison is within-rung.
9. **Heredocs corrupt Python files.** Two attempts to write scripts via bash
   heredoc failed (one silently injected a byte into a regex — trap 5's origin).
   Use the file-writing tools.

---

## 6. Repository map

**Governing documents** — `03_LADDER_PROTOCOL.md` (frozen design + every result),
`RESULTS.md` (running summary), `RETRACTIONS.md` (withdrawn claims).

**Core physics** — `isotherm.py` (Type V Do–Do, batch-aware, single source of
truth for solver *and* residual), `solver_fd.py` (sparse-Jacobian MOL, Danckwerts
inlet), `verify_solver.py` (L0), `classical.py` (L7 closed forms).

**Data** — `gen_parametric_dataset.py` → `data/parametric/` (988 conditions,
1.5 GB), `ladder_data.py` (**splits live here and nowhere else**; `load_slice()`
for memory-light analyses), `descriptors.py` (observable descriptors for L6).

**Shared infrastructure** — `metrics.py` (pooled MSE raises by construction;
cluster-robust bootstrap; `ALPHA_CALIBRATED = 0.005`), `output_head.py` (**one**
definition of the output parameterisation), `validate.py` (22 gates).

**Rungs** — `run_l1.py` … `run_l7.py`, `run_l4b.py`, with `analyze_l*.py`
counterparts. `audit_l1.py`, `audit_l3.py` are the post-hoc audits.
`l5_bottleneck.py` is the basis-vs-coefficient decomposition.
`identify_kinetics.py` + `identifiability.py` replaced the original SINDy.

**Figures** — `make_figures.py`, Fig1–Fig7 in `figures/`. Every series is computed
from data or a loaded checkpoint; the harness forbids synthesising one.

---

## 7. Open items before submission

1. **Every MOF-303 parameter is an uncited literature-range placeholder.** Until
   replaced with cited values and the isotherm refitted to a published water
   isotherm, **no result may be described as "MOF-303"** (retraction A4).
2. **No experimental validation.** The error budget must separate
   solver-vs-experiment from surrogate-vs-solver. One digitised published
   breakthrough curve would change the venue tier.
3. **No COF case exists** — the title claims one. Add it or drop it.
4. **`kaggle_run/` is a stale duplicate** carrying every original defect. Deleting
   it is destructive, so it is left for the user to decide.
5. **Speed claim needs an honest reference.** Frame as amortised screening
   throughput, not per-simulation speedup (retraction A6).
6. **`k_LDF` range under-samples the informative regime.** Sampled Da 155–3885,
   all near-equilibrium; the informative regime is Da ~ 1–50. This is also the
   pre-declared re-test of H1.

---

## 8. Recommended order from here

1. **Close the L5 refinement** (§3). Fast, and it is the last open number.
2. **Re-test H1 at low Damköhler** — the one follow-up the evidence specifically
   asks for. New dataset with `k_LDF` extended down to ~1e-4. H1 was NOT
   SUPPORTED, but we measured *why*: at median Da 626 the equilibrium/kinetic
   decomposition is nearly degenerate. **If the gap is still absent at low Da, H1
   is wrong rather than untested** — either outcome is publishable.
3. **The two-wave warp.** Single-front alignment is refuted (§4). The measurement
   that killed it also names its successor: align the Henry wave and the
   cooperative shock with *two* independent shifts, since their separation varies
   40-fold. This is the one remaining intervention the ladder has not eliminated,
   and it is the only realistic route to a positive result that the six negatives
   would motivate. Reuse `comoving.py` — the warp/unwarp machinery, the
   interpolation-floor self-check and the oracle 2×2 all generalise.
4. Replace the MOF-303 parameters with cited values; re-run affected figures.
5. Draft the manuscript as the falsification ladder. The negative results are
   contributions, not gaps.

**Venue realism:** npj Computational Materials is a reasonable stretch; JCP or
CMAME fit the methods contribution; a domain journal fits if the framing stays on
adsorption. Nature Computational Science is not reachable without experimental
data — that assessment has not changed.

---

## 9. Working agreement carried forward

Before any number is reported: matched training budget on both sides, a metric
whose value is *achievable* given the model's output range, ≥3 seeds, a paired CI
at the calibrated α, and the competitor at its strongest configuration. Verify
first, report second — the reverse order caused three retractions in one
experiment. Record your own analysis errors on the same terms as errors in the
code; that ledger is the project's main credibility asset.
