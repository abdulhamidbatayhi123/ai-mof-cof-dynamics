# risk

All three exposures — L5's flat-in-p claim, the two-wave warp verdict, and l5_bottleneck's coefficient-map table — run on the legacy 988-sample dataset through `ladder_data.load()` / `comoving.load_c_light()` with a hard-coded `split == "novel_material"` (12 held-out materials, one split, α = 0.005), while L1/L2/L6/L7 run 5-fold over 240 materials at α = 0.02; porting them is mechanical but touches four things per runner (load call, fold source, per-fold parameter standardisation, and the α/seed-pooling in the analyser), and two v2-specific degeneracies block the warp outright (B41's t_lo, plus 13,615 fabricated t_hi arrivals nobody has flagged). The cheapest experiment that most reduces risk is not the DeepONet re-run (26–39 h) or the warp verdict (10–30 h, 3 GB peak) but **l5_bottleneck on v2 in the same five folds (~1–2 h, <600 MB)**, which moves L5's load-bearing "the obstruction is the parameter → coefficient map" table from 12 clusters and one seed to 240 clusters and three seeds. The front-locating model is only reportable as a pre-declared arm inside the warp runner, with the reconstruction CI — not R² — as the primary estimand and a cheap between-material-variance pre-check that can kill it before any training.

## 1. [blocking] run_l5.py:228

**What.** The data-loading call is `d = ladder_data.load()` — no arguments, so `root="data/parametric"` (ladder_data.py:98) and `field_res=None`. Every L5 number in the paper is therefore measured on the legacy 988-sample / 60-material set (l5_run.log:1-4: `loaded 988 samples ... materials: 60 (12 held out)`).

**Why.** This is the single line that scopes the entire operator rung to 12 held-out materials while L1/L2/L6/L7 report over 240. RESULTS.md:405 already concedes it: "With 12 held-out materials this null cannot resolve a 21 % difference".

**Fix.** `d = ladder_data.load(args.root, field_res=args.field_res)` with `--root` defaulting to `v2_common.ROOT_V2` ("data/parametric_v2") and `--field-res` to `v2_common.FIELD_RES` (128), exactly as run_l1_v2.py:72. v2_common.py:33 already asserts in a comment that FIELD_RES=128 is "identical to L5 (run_l5.subsample)", so the encoding is unchanged and the cross-rung parity claim survives.

## 2. [blocking] run_l5.py:160, 231, 242

**What.** The split source is hard-coded three times: `tr, nm = d.idx("train"), d.idx("novel_material")` (line 160), `tr = d.idx("train")` (line 231), and `d.idx("novel_material")` inside the POD floor (line 242). `d.idx` reads the manifest string column (ladder_data.py:67-68), which on v2 gives the 2770/384/793 manifest split (48 held-out materials, l1_v2.log:3-4), not the folds.

**Why.** L1, L2, L6 and L7 all report over the SAME 240 materials in the SAME folds via `results/l6_v2_folds.json`. An L5 measured on v2's manifest split would be 48 materials, not 240, and would not be poolable with the rest of the ladder — the drift v2_common.py:11-13 exists to prevent.

**Fix.** Replace with the fold map: `fold_of, n_folds, fold_seed = load_folds(d.material_ids)` (v2_common.py:41), then per fold `te = np.where(fold_of == f)[0]`, `tr = np.where(fold_of != f)[0]`, as run_l1_v2.py:129-131. Keep the manifest design as a second, clearly-labelled design if you want the 48-cluster view, exactly as run_l1_v2.py:59 `--design {manifest,folds,both}`. Record `fold_file`, `fold_seed`, `n_folds` in the results header (run_l1_v2.py:82-83).

## 3. [blocking] run_l5.py:166

**What.** `Pz = torch.tensor(d.params_z, ...)` uses the standardisation computed in `ladder_data.load` at ladder_data.py:143-147, i.e. mean/sd over `split == "train"` — the MANIFEST train split.

**Why.** Under a fold design, a fold's held-out materials are mostly inside the manifest train split, so their parameter values enter the scaler the model is fitted with. That is the small-but-real normalisation leak ladder_data.py:141-142 explicitly warns about, and it would apply to L5 while L1/L2/L6/L7 avoid it.

**Fix.** Per fold, `Pz_np = standardise_params(d.params, tr)` (v2_common.py:86-91) and feed that to the model; do not touch `d.params_z`. Call `assert_disjoint(tr, te, "DeepONet parameter scaler")` (v2_common.py:63) before the fit, as every other v2 runner does.

## 4. [major] run_l5.py:141-154, 240-244

**What.** `pod_floor(F, tr_idx, p)` fits `PCA(n_components=p).fit(X[tr_idx])` for `ch in range(3)` but only ever assigns `errs`/`rng` when `ch == 0` (lines 151-153) — two thirds of the work is discarded. The floor is also computed once against `d.idx("train")` / `d.idx("novel_material")`, not per fold.

**Why.** On v2 each PCA is over (3158, 16384) instead of (691, 16384); running it three times per p per fold wastes roughly an hour across the sweep, and a single global floor is not comparable with L1-v2's per-fold `pod_floor_per_sample` (run_l1_v2.py:142-150) that the analysers pool.

**Fix.** Restrict the loop to `ch = 0` (the c channel is the only one scored, run_l5.py:190). Compute the floor per fold on `tr` with `assert_disjoint(tr, te, ...)`, and write the per-sample floor vector plus `material_ids`/`condition_ids` for the fold, mirroring run_l1_v2.py:146-150, so `analyze_*` can pool it out-of-fold.

## 5. [major] run_l5.py:185

**What.** The eval set construction is `for tag, idx in (("train", tr[:150]), ("novel_material", nm))`. `tr[:150]` is the first 150 rows of the train index in manifest order, not a random sample.

**Why.** On v2 the manifest is ordered by material id (files `m0000_c0000.npy` upward, ladder_data.py:116), so `tr[:150]` is roughly the first 13 materials — a biased train diagnostic, and the train error is the quantity the B14 underfitting flag is read from (analyze_l1_v2.py:32, 69-74).

**Fix.** Two changes. (1) Train leg: `rng = np.random.default_rng(f); tr_eval = np.sort(rng.choice(tr, size=min(600, len(tr)), replace=False))`, matching run_l1_v2.py:111-112 and 157-158. (2) Held-out leg: rename the tag from `novel_material` to `test` and pass the fold's `te`; the eval is forward-only over ~790 conditions per fold instead of 201, which is about 2 % of a cell's cost, so nothing else needs to change.

## 6. [blocking] analyze_l5_merged.py:223, 234, 250

**What.** The statistics call is `compare(base, other)` (line 234) and `compare(arm_result(...), arm_result(...))` (line 250), both with no `alpha`, so they take the default `alpha=ALPHA_CALIBRATED` = 0.005 (metrics.py:164, 167). The header at line 223 prints that α as the verdict's level.

**Why.** metrics.py:153-161 records that 0.005 was calibrated on the 12-material novel-material split. results/calibration_v2.json gives `v2_5fold` → α = 0.02 at 240 clusters. Running a 240-cluster comparison at the 12-cluster α is a verdict at an uncalibrated level — exactly what v2_common.alpha_for (v2_common.py:71-83) refuses for the other rungs and what retraction A13 withdrew.

**Fix.** `alpha, ncl = alpha_for("folds")` then `compare(a, b, alpha=alpha, n_boot=4000)`, identical to analyze_l1_v2.py:148-149 and 217-218. Print `alpha` and `n_clusters` in the header and write both into `results/l5_v2_verdict.json`.

## 7. [blocking] analyze_l5_merged.py:222-239

**What.** The flat-in-p verdict is four NULLS (`paired_vs_smallest_p`, all four `significant: false` in results/l5_merged.json), and the analyser computes no minimum detectable effect anywhere.

**Why.** Project rule 7 (mde.py:4-6) is "no null is reported without its minimum detectable effect", and retraction A22 exists because a null was quoted with a power figure from an i.i.d. resample. "DeepONet is flat in p" is the paper's central L5 claim and it is four unpowered nulls at 12 clusters.

**Fix.** For every non-significant comparison call `mde_report(scores[p][0] - scores[p8][0], material_ids, base=float(scores[p8][0].mean()), alpha=alpha, effects=(0.0,0.02,0.05,0.10,0.20), trials=200, label=...)` exactly as analyze_l1_v2.py:152-156, and write the MDE into the verdict file. Mark the verdict PROVISIONAL if `--no-mde` is passed (analyze_l1_v2.py:93).

## 8. [major] analyze_l5_merged.py:97-104

**What.** `arm_result` pools seeds by CONCATENATION: `values=np.concatenate(v)`, `material_ids=np.concatenate(m)` over the seeds, so each sample appears three times in the bootstrap.

**Why.** Every v2 rung does the opposite — `seed_avg` averages the per-sample vectors across seeds and then compares (analyze_l1_v2.py:35-41, 138-139, 199). Concatenation and averaging are different estimands; mixing them across rungs makes the L5 CI not comparable with the L1/L2/L6/L7 CIs the paper prints beside it.

**Fix.** Replace `arm_result` with a `seed_avg`-style helper that asserts identical `(material_ids, condition_ids)` ordering across seeds and returns the mean per-sample vector plus one copy of the ids, then pool across folds with a `pooled_folds` equivalent (analyze_l1_v2.py:44-51) so each of the 3947 samples appears exactly once.

## 9. [major] analyze_l5_merged.py:75, 78, 81-83, 153

**What.** The merge is keyed `(family, p, lr)` (line 81) and raises on duplicates (line 83); the parity check is `encodings.add((nz_s, nt_s, budget, steps))` (line 75); the floors and the selection both read the literal key `"novel_material"` (lines 78, 153, 161).

**Why.** With five folds every `(family, p, lr)` appears five times, so line 83 fires immediately; and the encoding tuple would happily merge a legacy file with a v2 file because it does not carry the dataset root or design.

**Fix.** Key by `(family, p, lr, fold)`. Extend the parity tuple to `(root, design_of_data, field_res, nz_s, nt_s, budget, steps)` — the runner should write `root` and `design_of_data` into the header as run_l1_v2.py:79-80 does. Replace the `"novel_material"` literals with `"test"` for the fold design and keep `"novel_material"` only under the manifest design.

## 10. [major] analyze_l5_merged.py:144-184

**What.** `select()`'s grid-boundary guard currently reports `deeponet p=8: best lr 1e-02 is the TOP of the swept grid [5e-05 ... 1e-02] and the metric is STILL MOVING there (4.3 % to the next point) — UNBRACKETED` and the same for p=16 at 5.7 % (results/l5_merged.json, `grid_boundary_warnings`).

**Why.** The two arms that are UNBRACKETED are p=8 and p=16 — the baseline the flatness claim is measured against. Their numbers are lower bounds, so "flat in p" is currently a comparison against an under-tuned anchor. Re-running on v2 with the same grid would reproduce the same defect at five times the cost.

**Fix.** The v2 learning-rate grid must extend above 1e-2. Minimum honest sweep: `--lrs 3e-3 1e-2 3e-2` (three points, the top one new). Keep `edge_is_binding` (line 111) unchanged so the guard can certify the v2 optima as interior or saturated before any table is written.

## 11. [major] run_l5.py:229, 168

**What.** `F, coords = subsample(d)` (line 229) fancy-indexes `d.fields` into a full copy (line 135), and `Ft = torch.tensor(F.reshape(...).transpose(0, 2, 1), device=DEVICE)` (line 168) makes a third full copy of every sample's field. On v2 at field_res=128 each copy is 3947 × 3 × 128 × 128 × 4 B = 776 MB.

**Why.** `d.fields` + `F` + `Ft` = ~2.3 GB resident before the model exists, on a 16 GB machine that l1_v2.log:6 already reports as "0.78 GB resident" for the load alone. This is the difference between the runner working and thrashing, and it is invisible on legacy where the same three copies are 194 MB each.

**Fix.** Make `subsample` a no-op when the field is already at (NZ_S, NT_S) — return `d.fields` and build `coords` from `d.fields.shape[2:]` — then `del d.fields`/reuse the same buffer for `Ft`. Building `Ft` once per RUN (not per cell) and reusing it across p/lr/seed is already the structure; just avoid the two extra materialisations.

## 12. [major] run_l5.py:265-268

**What.** Results are persisted with `json.dump(res, open(args.out, "w"), indent=2)` after each `(p, lr)` arm — a direct, non-atomic write, and there is no resume: a re-run recomputes every completed cell because nothing checks for one.

**Why.** CONTINUE_HERE.md:21-28 records twelve hours lost to a reboot mid-sweep, and v2_common.write_atomic (v2_common.py:194-201) exists precisely so a kill mid-write cannot truncate the file. A 26–39 h L5-v2 sweep without cell-level resume will be restarted from zero at least once.

**Fix.** Adopt the v2 pattern wholesale: `load_or_init(args.out, header, ("root","field_res","budget","steps","seeds","fold_seed","n_folds"))` (v2_common.py:204), `get_path(res, "folds", str(f), "arms", family, str(p), f"{lr:.0e}", str(seed)) is None` to build the todo list, `set_path` + `write_atomic` after every single (fold, family, p, lr, seed) cell — run_l1_v2.py:94-97 and 159-163 are the template.

## 13. [major] run_l5.py:170-180

**What.** Training is 8000 steps of batch 32 × 2048 sampled points, drawn from `tr` (line 172). The step budget was fixed against a 691-sample training split; on a v2 fold it is fixed against 3158 samples — 4.6× the data at the same number of gradient steps.

**Why.** Protocol §3 rule 6 (03_LADDER_PROTOCOL.md:78-88) says a shorter run is not a conservative proxy because "an undertrained model sits near its initialisation and flatters itself" — retractions A14 and A16. If DeepONet is undertrained on v2, error-vs-p would read flat for the wrong reason and the paper's headline L5 claim would be an artefact.

**Fix.** Declare, in the pre-registration and before the run, a step-count sensitivity arm: p ∈ {8, 128} at the selected lr, steps ∈ {8000, 24000}, 3 seeds, one fold. That is 12 extra cells (~2–4 h) and it converts "flat in p" from an assumption about budget adequacy into a measured one. If 24000 steps moves the p=128 number materially, the whole sweep must be re-budgeted before any table is written.

## 14. [blocking] warp_verdict.py:57, 114-117

**What.** `LEVELS = (0.05, 0.95)` (line 57); `t_lo, _ = arrival_time(X, u, lo)` (114), `t_hi, _ = arrival_time(X, u, hi)` (115), `span = np.maximum(t_hi - t_lo, 1e-3)` (116), `t_hi = t_lo + span` (117). `arrival_time` (comoving.py:90-111) returns the first upward crossing of the absolute level, linearly interpolated, and clamps a never-crossing cell to `u[-1]` (comoving.py:101). RETRACTIONS.md:139 (B41) measures the lower landmark on v2: the 5 % level is crossed within 2 % of the run in 97 % of (sample, z) cells, mean 0.003, sd 0.012, against 0.014 / 0.038 on legacy.

**Why.** sd 0.012 in normalised time is 1.5 grid steps at NT = 128 (1/127 = 0.0079). A target with 1.5 quanta of spread has no signal to predict; it is retraction A15's class for the third time. Any v2 warp built on the 0.05 level would report an R² and a reconstruction that are both arithmetic noise.

**Fix.** Do not port the levels. Add a LEVEL SCREEN stage that runs before any reconstruction and selects the pair, then freeze it. Concrete replacement (Option A, minimal change to the code): keep `arrival_time` and sweep candidate lower levels L_lo ∈ {0.10, 0.20, 0.30, 0.40, 0.50} against L_hi ∈ {0.90}; select the LOWEST L_lo that passes every guard below, so the window stays as wide as possible and the span cannot collapse. On v2, the physical reason 0.05 fails is that the fast Henry wave has already lifted c past 0.05 by t ≈ 0.003 everywhere, so the 0.05 landmark measures the Henry toe, not the shock the warp is meant to remove — which is why raising the level, not changing the regressor, is the fix.

## 15. [blocking] warp_verdict.py:114-115

**What.** Both calls discard `arrival_time`'s second return value with `_`. That value is `n_bad`, the count of (sample, z) cells that NEVER cross the level and are fabricated at `t = u[-1] = 1.0` (comoving.py:100-103). On v2 it is not zero: learning_curve_v2.log line 2 records `never-crossed cells lo=0 hi=13615 of 505216` at levels (0.05, 0.95) — 2.69 % of all cells, all on the UPPER landmark.

**Why.** This is a second, independent degeneracy that nobody has flagged: 13,615 upper-front arrival times on v2 are not measurements, they are the end of the time axis. They enter `span`, they enter the POD of the warp target, and they enter the R² denominator. B41 cleared `t_hi` as "well-posed (sd ≈ 0.25)" without accounting for them. A v2 warp verdict written today would silently absorb them.

**Fix.** Capture the counts (`t_lo, nb_lo = ...`, `t_hi, nb_hi = ...`), write them into the results header as learning_curve_v2.py:204-211 already does, and make `nb_lo == 0 and nb_hi == 0` a hard precondition of the run — not a warning. Under Option A above, L_hi = 0.90 rather than 0.95 is the candidate that has a chance of satisfying it; the screen must measure and report the count for every candidate level rather than assume it.

## 16. [blocking] warp_verdict.py:114-126

**What.** There is no guard anywhere that a chosen landmark is non-degenerate; the only existing check is the interpolation floor at line 125-126 (`floor > 0.1 * mean(oracle)` at line 190), which does not detect a landmark with no variance.

**Why.** Protocol §3 rule 7 (03_LADDER_PROTOCOL.md:96-101) forbids normalising by a quantity that can vanish; B34 and B41 are that rule broken in a diagnostic twice. A pre-declared, numeric screen is the only thing that turns "pick a better level" into a defensible choice rather than a level chosen after seeing which one gave the best answer.

**Fix.** Five guards, all computed on the FIT indices of each fold only, before any reconstruction is scored, all written to the results file for every candidate level: (G1) grid resolution — sd over all (sample, z) cells of t_L ≥ 4/(NT−1) = 0.0315 at NT = 128; v2's t_lo has sd 0.012 (1.5 quanta) and fails, legacy's 0.038 (4.8 quanta) passes. (G2) boundary mass — fraction of cells with t_L ≤ 2/(NT−1) = 0.0157 must be < 0.20; v2's t_lo is 0.97 and fails. (G3) no fabricated crossings — `n_bad == 0` for BOTH levels; v2 at 0.95 gives 13,615 and fails. (G4) span positivity — min over cells of (t_hi − t_lo) > 2/(NT−1) with ZERO clamps applied by comoving2.py:111-116, and the clamp count reported. (G5) predictability ceiling — η², the between-material share of the variance of t_L(z) on the fit folds; report it, and if η² is below the R² the payoff curve requires (0.94, see the front-locating finding) say so instead of training. A level that fails any guard on any fold may not be used, and the screen is run and frozen before the reconstruction arms. Fallbacks if no absolute level passes, in order: (Option B) a self-normalised landmark — per (sample, z) take the Henry plateau value c_p as c at the minimum |dc/dt| between the first crossing of 0.02 and the argmax of dc/dt, then use the crossings of c_p + 0.10(1 − c_p) and c_p + 0.90(1 − c_p), which measures the shock rather than the toe; (Option C) a derivative pair — t_peak = argmax_t dc/dt and w = (1 − c_p)/max(dc/dt), giving t_lo = t_peak − w/2, t_hi = t_peak + w/2, which plugs into `warp2`/`unwarp2` (comoving2.py:57-76) unchanged because they need only two curves with a positive gap, and cannot be degenerate while max dc/dt > 0. B and C are variants and must be reported as such, screened by the same G1–G5.

## 17. [major] comoving2.py:49

**What.** `N_SIG = 512`. `warp2` returns (N, NZ, N_SIG); on v2 that is 3947 × 128 × 512 × 4 B = 1.03 GB per warped array, and warp_verdict.py holds two of them simultaneously (`W_true` at line 124 and `W_p` at line 138) plus X (259 MB) plus the unwarp outputs.

**Why.** Peak resident is ~3 GB. CONTINUE_HERE.md and the machine memory note put free RAM at ~1.5 GB with a chain running; the warp verdict as written will not run on v2 without either exclusive use of the machine or a reduction.

**Fix.** Halve to `N_SIG = 256` and PROVE it lossless with the guard that already exists: the interpolation floor at warp_verdict.py:124-126 must stay under 10 % of the same-run fixed-frame error (the check at line 190). Report the floor at both 512 and 256 on one fold so the reduction is a measurement, not an assumption. Also free `W_true` before building `W_p` where the arms allow it.

## 18. [major] RESULTS.md:360-391

**What.** The "What binds instead" table (basis error vs coefficient-map error, 0.0515 / 0.0509 / 0.0510 flat to four decimals at p = 8/32/128, and the per-mode R² figures) comes from l5_bottleneck.py, which loads the legacy set (l5_bottleneck.py:48 `root="data/parametric"`, line 87 `load_c_light()`), scores `split == "novel_material"` (line 89), and runs at ONE seed — `random_state=0` hard-coded in both the PCA (line 100) and every HistGradientBoostingRegressor (line 120).

**Why.** This table is the load-bearing mechanism claim of the whole ladder — L5's Verdict, the co-moving section and the "the obstruction has moved" narrative all rest on it — and it is 12 held-out materials at a single seed, which protocol §3 rule 5 forbids from appearing in any table including appendices.

**Fix.** This is the cheapest, highest-value re-measurement in the project and it should be written first: `l5_bottleneck_v2.py`, built on learning_curve_v2.py's already-proven machinery (which loads the v2 c-channel at 128² for 259 MB, uses `load_folds`, and fits PCA + per-mode HGB per fold). Per (fold, seed): PCA(p) + p HGB fits for p ∈ {8,16,32,64,128} = 248 HGB fits + 5 PCAs; seeds (42,43,44); five folds; per-fold `standardise_params` and `assert_disjoint`; per-sample vectors + material ids written so the analyser can pool out-of-fold and compare at `alpha_for("folds")`. Cost, from the measured rate in learning_curve_v2.log (fold 0, materials 192, n_train 3150: 44–49 s for ~80 HGB fits + 2 PCA(32), i.e. ~0.55 s per HGB fit at 3150 rows): ~200 s per (fold, seed) × 15 = ~50 min, call it 1–2 h with the RidgeCV arm and the held-out reconstructions. Memory under 600 MB.

## 19. [minor] run_l5.py:170-196

**What.** Compute estimate for the L5-v2 DeepONet re-run, from the recorded per-cell wall times. Per-cell cost is independent of dataset size (line 172 samples batch=32 from `tr`, line 173 samples 2048 of 16384 coords, 8000 steps). Measured on legacy: DeepONet p=8 w216 222–298 s (l5_run.log), the same cell at lr 1e-2 434–455 s (l5_onet_hi.log), p=64 w178 667–1512 s, p=128 w146 846–1321 s (l5_onet_hi.log tail) — mean over DeepONet cells ≈ 600 s. Eval grows from 201 to ~790 held-out conditions per fold but is forward-only and ≈ 2 % of a cell.

**Why.** The parent session needs the number before committing the machine: this is the expensive option and it competes directly with the L4b-v2 chain that is running now.

**Fix.** 5 p × 3 lr (3e-3, 1e-2, 3e-2 — the third required by the unbracketed guard) × 3 seeds × 5 folds = 225 cells × ~600 s ≈ 37 h; at 2 lrs, 150 cells ≈ 25 h. Add POD floors: PCA(p ≤ 128) on (3158, 16384) × 5 p × 5 folds, ~20–40 min if the wasted channel loop at run_l5.py:145-154 is removed, ~1–2 h if not. Total 26–39 h, one job at a time, plus ~2–4 h if the step-count sensitivity arm is included. For comparison the two-wave warp on v2 is 10–30 h: warp_monotone.log seed 42 = 547 s on legacy for 80 HGB fits + 4 warp/unwarp pairs is the clean floor (warp_verdict.log's 4993/6736/7060 s per seed for comparable work is the same machine under contention — quote both); scaling ×4.6 for PCA/HGB rows (691 → 3158) and ×4.0 for the warp double loops (N·NZ 126,464 → 505,216) gives ~2500 s per (fold, seed) clean, × 5 folds × 3 seeds ≈ 10.5 h clean and ~30 h contended. `arrival_time` itself is cheap on v2: learning_curve_v2.log line 2 does both levels over 505,216 cells in 51 s including the load, so the level screen of finding 15 — which needs no reconstruction — costs under 10 minutes for six candidate levels and must be run first.

## 20. [major] warp_verdict.py:128-153, 183-188

**What.** Scope for the front-locating model — the experiment that would turn the 2.17× oracle headroom (line 183-184, results/warp_verdict.json `headroom_to_oracle` 2.1737) into a positive result rather than a bound. It has no runner today; `warp_predict.py` measured only the payoff curve.

**Why.** Without a pre-declared estimand and decision rule this is the fishing expedition the project's own protocol is built to prevent: the tempting move is to report R² going up, but the payoff curve (results/warp_predict.json) shows R² translates non-linearly into the thing that matters — R² 0.895/0.919 → 0.0508, 0.941/0.954 → 0.0427, 0.974/0.980 → 0.0345, 0.993/0.995 → 0.0269, oracle 0.0234, against a fixed frame of 0.0500. R² alone can rise while the reconstruction does not beat the baseline.

**Fix.** Build it as an ADDED ARM inside the v2 warp runner, not a separate script — one pass over the warp machinery serves all four arms. INPUTS: the 11-dim v2 parameter vector only, standardised per fold with `standardise_params(d.params, tr)` — the same information the fixed-frame arm gets, so information parity (03_LADDER_PROTOCOL.md:73-88) holds. TARGET: the two landmark curves on the 128-point z grid in the (start, log-span) parameterisation warp_predict.py:142-148 measured as better conditioned, with the lower landmark replaced by whatever passes the G1–G5 screen. SPLIT: the five `results/l6_v2_folds.json` folds, seeds 42/43/44, every stochastic component moved. ARMS, all computed in the same run and never from an imported constant (defect B28, warp_verdict.py:5-16): fixed frame; two-wave with the incumbent POD+HGB warp; two-wave with the model's warp; oracle, labelled as a bound and never quoted against an arm that does not get the warp. MODEL: one family declared in advance — a small MLP params → 2 × 128 emitting non-negative increments (cumulative softplus in z) and a log-span, so monotonicity and a positive span hold BY CONSTRUCTION. This is not a rerun of warp_monotone: that tested a post-hoc isotonic projection and found it significantly worse (RESULTS.md:547-593), whereas L4b's own result is that a physical bound imposed architecturally was worth 11.5× and the same bound as a penalty was worth nothing — the architectural version is the one never tested. HYPERPARAMETERS: one grid, declared before the run, selected on a nested 20 % holdout of the FIT materials, never on the held-out fold. PRIMARY ESTIMAND AND DECISION RULE, frozen before the first run: paired cluster-robust-by-material bootstrap of per-sample field nRMSE(c), model-warp two-wave arm vs the SAME-RUN fixed frame, seed-averaged, pooled out-of-fold over 240 materials, at `alpha_for("folds")` = 0.02 — CI entirely below zero → the two-wave frame is a positive result on v2; CI containing zero → NO DIFFERENCE in words plus the MDE from `mde_report`, and the reportable finding is "front location remains the binding obstruction at 240 materials", a strictly stronger statement than the current one, not a null; CI above zero → the model is worse than the incumbent and that is reported. SECONDARY, non-verdict-bearing: R² per curve, with the pre-declared target R² ≥ 0.94 on BOTH curves (the payoff curve's 0.941/0.954 row buys 0.0427 against 0.0500, a 15 % gain) and the pre-declared consequence that reaching R² ≥ 0.94 WITHOUT beating the fixed frame withdraws the payoff curve itself. INVALIDATION (any one fires → no verdict): a landmark fails the screen on any fold; `n_bad > 0` for either level; the interpolation floor exceeds 10 % of the same-run fixed-frame error; `assert_disjoint` fires anywhere. CHEAP PRE-CHECK that can kill the experiment before any training: η², the between-material share of variance of each landmark curve on the fit folds — if η² < 0.94 for either curve, no parameter-only predictor can reach the required R² and the runner reports that bound instead of training, the analogue of PREREG_L6_v2.md §5's invalidation checks.

