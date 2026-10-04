# Pre-registration — L4b on dataset v2: the physics-weighting sweep, and physics at inference

**Written 2026-09-02, before any v2 L4b arm is trained.** Committed to git before the
runs. Frozen; changes after the first arm trains go in `RETRACTIONS.md`.

---

## 1. Why L4b is re-run

L4b's headline is an interaction: *"physics-as-a-loss helps only when the structure
is missing (unbounded head, time axis: 2.2× better) and hurts once the structure is
imposed (bounded head, time axis: 1.6× worse, CI excludes zero); on the material axis
it does not help under either head."* Three things make that claim weaker than it
reads:

1. **The arm being argued against never got a weighting sweep** — rule 4 turned
   inward (audit P7). Every physics number rests on one rule (gradient-norm
   balancing at `balance_target = 1.0`, which settled at `w_pde ≈ 2×10⁻⁴`), one
   optimiser (Adam), and 8 000 steps. "Physics hurts" is only defensible as
   "physics hurts at every weighting scheme tested".
2. **The time-axis CIs rest on ~7 clusters.** `run_l4b.py` scored `tr[:120]` —
   the first 120 training samples, i.e. about seven materials at 17 conditions
   each. A cluster bootstrap over seven clusters is close to meaningless, and the
   calibration (`metrics.py`) was never measured below 12.
3. **The mechanism argument was never turned into a measurement.** "A residual is
   evaluated only for training materials and never at inference" is true of the
   arm as built, not of physics-informed learning. Physics *at inference* — freeze
   the model, minimise the residual for the unseen material with zero data — is
   the only form that can act on the material axis at all, and it is the arm a
   referee will ask for (audit P8).

And, as for L1/L2/L7: every rung should report on the same dataset.

---

## 2. Questions and pre-declared decision rules

All arms use the **bounded head** (`apply_bounded_head`: sigmoid on c*, q*; the
initial condition as an explicit residual), because that is the configuration the
disputed claim is about. The unbounded head is settled and not re-run.

### Q1 — on the TIME axis, does any physics weighting beat, tie, or lose to the data-only twin?

Arms, matched architecture (`ParametricPINN`, width 192, depth 4, 114 435
parameters), matched 8 000 Adam steps, matched supervised budget (4 096
points/step), 3 seeds:

| arm | physics weighting |
|---|---|
| `data_only` | none (w → 0) |
| `pi_fixed_w1e-4`, `…1e-3`, `…1e-2`, `…1e-1`, `…1` | fixed `w_pde`, four decades |
| `pi_gradnorm_t0.1`, `…t1.0`, `…t10` | gradient-norm balancing (Wang, Teng & Perdikaris 2021), three target ratios; `t1.0` is the legacy configuration |
| `pi_ntk` | NTK weighting (Wang, Yu & Perdikaris, *JCP* 2022): per-term weights ∝ 1/trace of the term's empirical NTK, re-estimated every 50 steps from per-point gradient norms, EMA-smoothed |
| `pi_sa` | self-adaptive weights (McClenny & Braga-Neto, *JCP* 2023): a fixed collocation set with one trainable weight per point for the PDE and boundary terms, maximised by gradient ascent while the network minimises |

Every physics arm carries the interior PDE residual **and** the Danckwerts boundary
residuals (defect B20) under the same weight.

**Decision rule.** Let `best_pi` be the physics arm with the lowest mean held-out
error on the axis — chosen *on the held-out error*, which is the generous direction
for the arm being argued against (rule 4), and stated as such. Then, paired and
cluster-robust at α = 0.02:

| outcome | words to use |
|---|---|
| every physics arm significantly worse than `data_only` | "physics-as-a-loss is worse than its data-only twin at every weighting scheme tested (fixed over four decades, gradient-norm at three targets, NTK, self-adaptive)" — the legacy claim stands, now defended |
| `best_pi` ties `data_only` (CI includes zero) | "no difference at the best weighting found; MDE X %" — **the legacy 'hurts' claim is withdrawn** and replaced |
| `best_pi` significantly better | "physics helps once correctly weighted" — the legacy claim is **retracted** as a weighting artefact of exactly the kind B16 warned about |

### Q2 — the same on the MATERIAL axis. Same arms, same rule.

### Q3 — physics at inference (test-time refinement)

Take the trained `data_only` model (and, as a control, the trained `best_pi`).
For each held-out unit — each of the 48 held-out **materials** on the material
axis; each training material's t* > 0.5 window on the time axis — minimise, with
**no data**, the PDE + boundary + initial-condition residual for that unit's own
parameter vectors (all its conditions batched), 300 Adam steps at lr 10⁻⁴, all
weights free. On the time axis an anchor term (MSE to the frozen model's own
prediction on the seen window t* < 0.5, weight 1) prevents the seen region from
drifting; on the material axis no anchor exists, because nothing is known.

**Decision rule.** Paired before/after per sample, cluster-robust by material,
α = 0.02. HELPS iff after is significantly better; else "physics at inference does
not improve transfer at this configuration, MDE X %". A significant *worsening* is
reported in those words.

### Q4 — optimiser robustness (Rathore et al., ICML 2024)

After Adam, both `data_only` and `best_pi` (time axis and material axis) get an
identical L-BFGS polish on fixed batches (500 iterations, strong-Wolfe line
search, history 50). Rule: report whether the Q1/Q2 ordering **changes** under the
polish. It is a robustness check, not a new verdict; only if the ordering flips
does the verdict text change, and then the flip is the reported result.

---

## 3. Design

- **Data.** `data/parametric_v2`, 128 × 128 on load, manifest split: 2 770 train /
  793 novel-material (48 materials). Inputs: the 11-vector (`d_p` in place of
  `k_LDF`), standardised on train. Physics groups via `physics_from_params(vec,
  d.param_keys)`; the Glueckauf `k_LDF` is asserted against the manifest record
  before training.
- **Time axis.** Train on t* ∈ [0, 0.5] of every training sample; score on
  t* ∈ [0.5, 1] of a **material-stratified** evaluation subset: 4 conditions from
  each of the 192 training materials (768 samples, 192 clusters), drawn once with
  seed 0 and identical for every arm. Normalisation by the full-field range
  (rule 5, A15).
- **Material axis.** Train on t* ∈ [0, 1]; score all 793 held-out samples (48
  clusters).
- **Steps, sampling.** 8 000 Adam steps, cosine schedule to 1 % of lr 10⁻³, 4 096
  supervised points/step, 1 024 collocation + 512 boundary points/step, gradient
  clipping at 1.0 — the legacy L4b settings, so the legacy numbers remain the
  reference for what changed.
- **Seeds.** 42, 43, 44.
- **Statistics.** Paired, cluster-robust by material; α = 0.02 (calibrated at 48
  clusters, and measured conservative at 240; the 192-cluster time axis sits
  between). Every null with its MDE (`mde.py`).
- **Checkpoints.** Every trained model's `state_dict` is saved
  (`data/l4b_v2_ckpt/`, gitignored) so the refinement and the polish load the
  trained weights rather than retraining, and so any figure can be regenerated from
  a checkpoint (standing rule 2).
- **Order of execution.** `data_only` on both axes → Q3 refinement of `data_only`
  → physics arms on the time axis → physics arms on the material axis → Q3
  refinement of `best_pi` → Q4 polish. The runners resume cell by cell.

## 4. What would invalidate the test

1. **A physics arm that fails to train** (non-finite loss, or a seen-window error
   more than 3× the data-only twin's — the B16 signature of an optimiser that
   abandoned the data fit). Reported as failed-to-train and **excluded from
   `best_pi` selection**, never averaged in.
2. **A fixed weight whose optimum sits on the sweep edge** without saturation
   (rule 4): the sweep is extended one decade in that direction before the
   verdict.
3. **Refinement that changes the seen-window prediction** on the time axis by more
   than the anchor tolerates (seen-window error rising > 10 %): the anchor is
   reported as insufficient and the refinement result on that axis is scoped.
4. **`k_LDF` mismatch** (B37's class): abort.

## 5. Compute

Legacy timings on this machine: data-only ≈ 6 min, physics ≈ 35 min per run at
8 000 steps. 10 physics arms × 2 axes × 3 seeds ≈ 35 h; data-only 6 runs ≈ 40 min;
refinement ≈ 2 h; polish ≈ 4 h. Runs after the L1/L2/L7 v2 chain; never
concurrently with it (shared 16 GB, one training job at a time).

## 6. Amendments

**A-B72, 2026-10-04 -- after every v2 L4b result, before any cell of the corrected re-run.**
The residual this rung used advected gas at v instead of v/eps_t (ledger B72; proof:
`results/l4_residual_check.json`), so every verdict above measured a mis-specified
prior and is withdrawn as a statement about physics (A28). The rung is re-run with
the corrected residual, which is now gated against the solver (`validate.py`, "the
training residual is the solver's equation"). Nothing about the design changes except
what the defect forces and what was already demanded:

1. **Code.** `run_l4.pde_residual` / `boundary_residual` as of commit d29eb9c; the
   gate must PASS before the first cell.
2. **Arms.** `data_only` and every physics arm of §2 at the grid the edge rule had
   already reached: fixed weights 1e-6 ... 1 (seven), gradient-norm at 0.1, 1.0, 10,
   NTK, self-adaptive. Same axes, seeds 42/43/44, steps, widths, budgets, split.
   `data_only` is re-trained too (its refinement uses the residual, and a fresh twin
   removes any doubt about checkpoint provenance).
3. **Rules unchanged.** The §2 words, the §4 invalidations, the edge rule (an
   unsaturated optimum at 1e-6 extends the sweep to 1e-7 before any verdict), Q3
   refinement and Q4 polish as declared.
4. **Added before the run, not after it:** the selected-arm comparison is also
   reported with the studentised max-statistic interval over all eligible arms
   (`selection_adjust.py`, `analyze_l4b_selection.py`), because the referee review
   showed best-arm selection on the test materials is anti-conservative for a
   positive verdict. If the per-pair and adjusted intervals disagree, the adjusted
   one decides the word.
5. **Outputs.** `results/l4b_v3_results.json`, `results/l4b_v3_refine.json`,
   `results/l4b_v3_verdict.json`, checkpoints in `data/l4b_v3_ckpt/`. The withdrawn
   run's files and checkpoints are kept unchanged as its evidence.
6. **Compute.** 12 physics arms x 2 axes x 3 seeds at ~35 min, plus refinement and
   polish: about 2-2.5 days, queued after the L5-v2 24k sweep, one job at a time.
