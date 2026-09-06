# CONTINUE HERE — session handoff

Rewritten 2026-09-02; updated 2026-09-05 after the L1/L2/L7 v2 chain completed and L4b-v2 was launched. Read this, then `RESULTS.md`, then `AUDIT_2026-08-30.md`.
`RETRACTIONS.md` is the record of everything withdrawn — **26 Part-A, 64 Part-B**.

---

## 1. First thing to do in a new session

```bash
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
./resume.sh          # shows what is done and what is missing, runs nothing
./resume.sh go       # continues only the missing work
```

`resume.sh go` finishes any incomplete FNO arm, runs L6-v2 fold by fold, then runs
**whatever is missing of L1/L2/L7 on v2** (`chain_v2_rungs.sh`) and then **L4b on v2**
(`chain_l4b_v2.sh`). Every runner writes after each completed cell and skips completed
cells, so a shutdown loses at most one cell.

**The chain DIED once already. Check that it is alive before assuming progress.**
`./resume.sh` now says so at the top of its state report: it asks Windows for the
actual command line of every python process (Git Bash's `ps -ef` shows only the
interpreter path, so grepping it for a runner name always returns zero) and prints
how stale the results file is. On **2026-09-06 the machine rebooted at 22:54** with
the sweep at 41/66; nothing noticed until 00:23 the next day and **about twelve
hours were lost**. That is the second such loss. A stall looks exactly like progress
unless something checks.

**In flight as of 2026-09-05 00:57, relaunched 2026-09-07 00:24 (Istanbul): `chain_l4b_v2.sh`** (L4b on v2, ~50 h), launched
detached with `nohup`; logs `l4b_v2.log`, `l4b_v2_refine.log`, `l4b_v2_analysis.log`, step exit
codes `chain_l4b_v2_outer.log`. Design frozen in `PREREG_L4b_v2.md`, committed before any run.
The L1/L2/L7 v2 chain (`chain_v2_rungs.sh`) is **complete** (V2_RUNGS_DONE, 2026-09-03/04) and
written up in `RESULTS.md`. Never run two training chains concurrently on this 16 GB machine.

**Early L4b-v2 result already on disk (2026-09-05, stages D0 and R0 complete):** the
pre-registered test-time refinement (Q3: residual + BC + IC, 300 Adam steps at 1e-4,
zero data) makes transfer **much worse** — material axis 0.020 → 0.10–0.12, time axis
held-out 0.011 → 0.06–0.08, and the seen window degrades too despite the anchor
(`l4b_v2_refine.log`, `results/l4b_v2_refine.json`). This is a reportable pre-declared
outcome ("physics at inference makes transfer worse"). Before writing it, check the
B16-class diagnosis first: an unscaled residual overwhelming a good initialisation.
The loss trajectory per unit was **not saved** (`refine_unit` returns `hist` and the
runner drops it) — add that before any post-hoc, labelled sensitivity (e.g. lr 1e-5,
or a gradient-norm-balanced residual). Do not tune anything to rescue Q3.

**Two sessions touched this repository on 2026-09-05.** A parallel session (01:24–01:48)
added B43 (my L2 cross-comparisons had no script; now `analyze_l2_v2.cross_comparisons`,
post-hoc, labelled), B44 (the (256,256,256) estimator agrees to the bit across the L1
and L2 runners), hardened the plotting gate, drew Fig1 (`fig_ladder.py`) and fixed
three stale status rows; it ended without committing and its work was committed by
this session. The gate now accepts a results path a running chain has not written
only if the script declares it in `PENDING_RESULTS`, and fails once that file
exists: **remove the declaration in `fig_ladder.py` when L4b-v2 lands.**

**The repository is under git as of 2026-08-30.** Everything before that commit is
untracked history; everything after is timestamped and diffable. `git log --oneline`
is the fastest way to see what happened and why — the messages carry the reasoning.

---

## 2. What this project is

A **pre-registered falsification ladder** for surrogate models of MOF/COF
adsorption column dynamics. Not an architecture paper — L3 and L5 refuted that
premise long ago.

> **The question:** what actually binds the error when a surrogate is asked to
> predict a material it has never seen, and which standard interventions move it?

Seven candidates were named in advance with the evidence that would kill each.
Six are eliminated. The survivor is a change of coordinates, not of architecture.

**Venue decision: CMAME.** Free to publish (subscription route, green OA to arXiv
— the author is a student without APC funding), IF ≈ 7, and the best topical fit
in the candidate set: every paper L3 argues with is in CMAME (Shukla 431, Abueidda
436, Wang 433, Kiyani 446, Rigas 452). Fallbacks: Separation & Purification
Technology, then TMLR. Reasoning in `CITATIONS.md`. **One paper, not two.**

---

## 3. Status

| rung | verdict | state |
|---|---|---|
| L0 | reference verified vs 4 closed forms | ✅ done |
| L1 | "more data" | ⚠️ **NOT ELIMINATED on v2** — still falling at 192 materials (β = 0.22), all of it in the coefficient map; the **MLP is now the best arm**, significantly |
| L2 | "more capacity" | ✅ **done on v2** — every optimum bracketed, but it **moved**: 8-layer MLP beats the L1 setting by 21 % at 192 materials (legacy: 1 %). **A26** |
| **L3** | **"better basis / KAN"** | ✅ **FINAL** — fully bracketed, 6/6 significant |
| L4/L4b | "physics as a loss" | ⏳ **RUNNING on v2** since 2026-09-05 00:57 (`PREREG_L4b_v2.md`: fixed-w sweep, gradient-norm targets, NTK, self-adaptive, test-time refinement, L-BFGS polish; ~50 h) |
| **L5** | **"you need an operator"** | ✅ **FINAL** — narrowed by FNO |
| **L6** | **"separate identification"** (H1, primary) | ✅ **RESOLVED on v2** — mechanism refuted, but separate beats joint 3.7 % |
| L7 | "is learning needed" | ✅ **eliminated on v2 too** — best closed form 3.7× worse, paired over 240 materials |

### The headline numbers, current

**L3** — 69 arms, 8 learning rates over 3.5 decades, every optimum bracketed:

| budget | mlp | rbf_kan | cheby_kan |
|---|---|---|---|
| 50k | **0.0564** | 0.0768 | 0.1063 |
| 200k | **0.0570** | 0.0703 | 0.1120 |
| 800k | **0.0572** | 0.0702 | 0.1028 |

6/6 significant. The families optimise **three orders of magnitude apart** in
learning rate, which is itself a finding and pre-empts the strawman objection.

**L5** — matched ~200k params, 8000 steps, 128×128:

| arm | best | × POD floor |
|---|---|---|
| DeepOKAN | 0.0357 | 71× |
| DeepONet | 0.0265 | 53× |
| **FNO** | **0.0216** | **43×** |

`DeepONet vs FNO: diff +0.00488, CI [+0.00035, +0.00978] SIGNIFICANT`.
DeepONet is **flat in p** (0.0265 → 0.0275 over p = 8→128, all four CIs span zero)
while the POD floor falls 28.7×. **A seven-channel FNO matches the best DeepONet
(width 216)** — the reconstruction, not the capacity, separates the families.

**L6-v2 (the primary hypothesis, resolved)** — 45 runs, 5-fold CV over all 240
materials, pre-registration committed to git *before* the first arm trained:

- **PRIMARY, refuted:** the separate-vs-joint difference does **not** vary with
  Damköhler. slope +0.00140, CI [−0.00329, +0.00618], r = 0.040, over 1.35 decades.
- **SECONDARY, significant:** joint 0.0562 vs separate **0.0541** — separate is
  **3.7 % better** (CI 1.0–6.5 %), consistent in all 5 folds and all 3 seeds.
  Legacy had separate **26 % worse**. The sign reversed.
- MDE (corrected, A25): 82 % power at 4 %, 99 % at 6 %; MDE 4 %. Quote the **1.0 % lower bound** as the
  conservative reading — the observed effect sits near the resolution limit.
- Why it became answerable: between-material noise fell 0.0391 → **0.0104**
  (69 % → 18 % of base), a 3.8× reduction from v2's Sobol sampling and
  physically consistent kinetics.
- **Verdict:** the structure acts as an **inductive bias, not a kinetic
  identifier**. Outcome four of the four the pre-registration anticipated.

**Two-wave warp** — 3 seeds, both arms in one run, paired cluster bootstrap:
fixed 0.05005, predicted-warp 0.04770 (**no difference**), oracle 0.02203
(**significant, 2.27×**). The gain is entirely consumed by front-location error.
**2.17× headroom, established.** Monotonicity is *not* the lever (tested, B34).

**L1 / learning curve / L7 on v2 (2026-09-03)** — `PREREG_L1L2L7_v2.md`, same folds as
L6-v2, 240 held-out materials, every comparison significant:

| | result |
|---|---|
| L1 arms (5-fold) | **mlp 0.0306** < xgb 0.0361 < rf 0.0388 < ridge 0.0516, all significant; MLP ahead in every fold. Reverses legacy (trees ≥ MLP). 109× above the POD floor |
| L2 sweep (5-fold) | optima w64 / **d8 = 0.0241** / md6 / leaf1; d8 vs the L1 setting −21.3 % (CI 18.7–23.7 %); three families saturated, the forest at its ceiling; best fixed-basis arm on v2 is 86× the floor |
| learning curve | 0.0654 → 0.0531 → 0.0465 → 0.0402 → **0.0348** at 12/24/48/96/192 materials, **every step significant, last step included**; β = 0.222 [0.205, 0.239]. **NOT ELIMINATED.** Fixed-basis curve identical → all of the gain is the coefficient map (A21 confirmed) |
| conditions axis | β = 0.122, last step significant but 2.6 %; not eliminated by the rule, half the material exponent |
| L7 | mlp exit 0.0474 vs klinkenberg 0.1769 (3.7×), all three closed forms significantly worse |
| B41 | `R²(t_lo)` is rule-5 degenerate on v2 (97 % of cells cross 5 % within 2 % of the run); only `t_hi` is a valid warp target there |
| anchor | solver vs Lassitter 2024 Fig. 10: t50 303 vs 287 min, plateau 0.34 vs 0.27, no fitting; first wave ~80 min early (isotherm low-RH branch), shock too dispersed under Ruthven on a 1–2-pellet bed (Pe ≈ 1; Bruggeman post-hoc gives nRMSE 0.083 vs the fitted COMSOL's 0.069) |

**Dataset v2** — 3947 sims, 240 materials, Sobol, Glueckauf kinetics.
Da **per sample** (n = 3947): median **27.5**, **77.8 %** in the informative 5–60 band,
range 3.8–689. Da **per material** (n = 240, a median of medians — the axis L6's slope
test uses): median **25.0**, **85.0 %** in band, 1.35 decades. Legacy per sample: median
**625.6**, **98.9 %** ABOVE the band. Name the denominator (**B63**); `dataset_summary.py`.

---

## 4. What is genuinely good — do not undo

1. **The retraction ledger.** 26 Part-A, 64 Part-B; 31 entries carry the words
   "our own error" and several more are self-attributed in other words.
   Several corrections *weaken* headline claims that nobody would have questioned.
   This is the paper's strongest asset; make it a numbered section, not an appendix.
2. **Guards that make recurring failures impossible**, each earned from a real
   defect: the never-trained guard (`best_step == 0`), the grid-boundary guard
   with binding-vs-saturated classification, `pidx()` refusing wrong columns,
   `physics_from_params` requiring keys with no default, `pooled_mse()` raising.
3. **`l5_bottleneck.py`** — the basis-vs-coefficient decomposition in the *optimal*
   basis. Independently corroborated by Heinlein & Taraz (2026), which is
   corroboration, not loss.
4. **Verified citations.** `CITATIONS.md` is a gate: nothing is cited until fetched.
   It has already caught a fabricated co-author and a falsified novelty claim.
5. **Pre-registration in git.** `PREREG_L6_v2.md` was committed before L6-v2 ran —
   verifiable in a way the original L0–L7 pre-registration is not, and the README
   says so plainly.

---

## 5. What is not good yet

**Blocking:**
1. **L4b-v2 is RUNNING** — launched 2026-09-05 00:57 (Istanbul), detached: `chain_l4b_v2.sh`,
   logs `l4b_v2.log`, `l4b_v2_refine.log`, exit codes `chain_l4b_v2_outer.log`; ~50 h.
   Order: data_only both axes → refinement → physics arms (time, then material) →
   refinement of the best physics arm → L-BFGS polish → `analyze_l4b_v2.py`. Resumable;
   `./resume.sh go` continues it. When done: read `l4b_v2_analysis.log` and write the
   verdict in the pre-declared words of `PREREG_L4b_v2.md` (defended / withdrawn /
   retracted). **Two idle days were lost** between the v2 chain finishing (09-03 ~13:00)
   and this launch — the session that was to launch it had ended.
2. **L4b-v2 is pre-registered and smoke-tested but not run.** `chain_l4b_v2.sh`
   after the v2 chain (~50 h). Its verdict decides whether "physics hurts once
   bounded" is defended, withdrawn, or retracted — all three outcomes are written
   in `PREREG_L4b_v2.md`.
3. **~260 citations still unverified.** Two tranches done (≈90 refs).
4. **Experimental anchor: done, pre-registered, no fitting.** Lassitter et al. 2024
   (*Chem. Eng. Sci.* 285:119430) Fig. 10 — a 6.35 mm MOF-303 bed at 32.8 % RH, fully
   specified in its SI — digitised and compared (`PREREG_LASSITTER.md`,
   `compare_lassitter.py`, `results/lassitter_comparison.json`, Fig9). The cited
   isotherm reproduces the two-wave shape and the 50 % arrival (303 vs 287 min) with
   nothing tuned. Two named discrepancies: the first wave arrives ~80 min too early
   (the isotherm's low-RH branch — the Henry fraction was never fitted to dynamics),
   and the shock is too dispersed under the Ruthven closure on a 1–2-pellet bed
   (Pe ≈ 1); the authors' Bruggeman closure fixes the second as a labelled post-hoc
   sensitivity (Fig9b). Li 2025 is only a shape comparison. What remains: write the
   error budget in the paper as solver-vs-experiment (this) and surrogate-vs-solver
   (everything else).
5. **Figures for the current narrative — partly done.** New this session, every series
   read from results files: Fig8 (v2 learning curve), Fig9/9b (solver vs Lassitter),
   Fig10 (the mechanism: floor vs arms, basis vs coefficient-map error, per-mode R²),
   Fig11 (two-wave warp: n-width per frame, the powered verdict). Still to do: a
   ladder schematic with each rung's verdict and power (F1), and re-authoring Fig1–7
   to column width for the falsification-ladder story.

**Known and scoped:**
- `C_ps = 1000 J/kg/K` has **no citable source**. Report as a 900–2400 J/kg/K
  sensitivity band, not a constant.
- **No COF breakthrough measurement exists anywhere** (searched, not found). The
  "no COF case" gap closes by saying so, not by inventing one.
- Novel-condition split has **2 clusters**. Descriptive only, no CIs.

---

## 6. Steps remaining — roughly 7–10 sessions

1. ~~Finish L6-v2~~ — ✅ **done 2026-09-02**
2. **L1 learning curve, L2, L7 on v2.** — ✅ launched 2026-09-03; report when done
3. **L4b weighting sweep + test-time physics refinement.** — pre-registered; run next
4. **Citations tranche 3+.** The Lassitter comparison is done (2026-09-03). — 1–2 sessions
5. **Figure set rebuilt for the current narrative.** — 1–2 sessions
6. **Manuscript.** — 2–3 sessions

---

## 6b. What this session (2026-09-02/03) changed — read before trusting older text

- **A25** (in our favour): the MDE simulation inflated within-material noise by √2;
  L6-v2 has **82 % power at 4 %**, MDE 4 % (was 68 % / ~5 %). `mde.py` is now the single
  MDE implementation, self-tested.
- **A24**: the legacy learning curve's 48-material endpoint was a single deterministic
  run; flagged, superseded by the v2 curve.
- **B39/B40**: the L6-v2 MDE table had no script; the B37 fix had shadowed the key list
  it threaded through (every PINN run would have crashed). Both fixed.
- **Experimental anchor changed**: Lassitter 2024 Fig. 10 (fully specified in its SI,
  digitised) replaces Li 2025 (under-specified). See §5 item 4.
- Ledger counts: 26 Part-A, 59 Part-B (B43/B44 figure pass, B45-B53 citation tranche 4,
  B54-B59 tranche 4b, all 2026-09-05). B54 is the first entry left OPEN: which
  Klinkenberg paper carries L7's control formula needs a library copy.

## 7. Rules carried forward

1. No number from a failing `validate.py` category. (24 gates, all passing.)
2. Matched training budget, **asserted** not assumed.
3. ≥3 seeds. Single-seed numbers appear nowhere, appendices included.
4. Compare against the competitor's **strongest** configuration. A selected
   hyperparameter on a grid edge is only acceptable if the metric has **saturated**
   there — measure it, do not assume it.
5. Never normalise by a quantity that can vanish. (A15, and again in B34.)
6. A gate that can be bypassed is not a gate. (B37: a keyword default defeated one.)
7. **No null without its minimum detectable effect.** (A22 exists because one was
   quoted without one, and the design turned out to have 7 % power.)
8. Nothing is cited until it has been **fetched**, not searched. (B35, A23.)
9. Errors in the analysis are recorded on the same terms as errors in the code.
