# Independent first-hand findings (Claude, direct measurement)

## F1. The L5 DeepOKAN column in RESULTS.md and 03_LADDER_PROTOCOL.md is STALE and WRONG
CONTINUE_HERE.md sec.3 instructed: "If any DeepOKAN configuration at p=64 or 128 beats the
recorded 0.0818/0.0884, update the L5 DeepOKAN column."  results/l5_refine.json completed
(7557 s) and it DOES beat them, significantly:
  p=64  0.0818 (lr 1e-4) -> 0.0652 (lr 2e-4)   diff +0.0166 CI [+0.0116,+0.0233] SIGNIFICANT
  p=128 0.0884 (lr 1e-4) -> 0.0710 (lr 2e-4)   diff +0.0173 CI [+0.0128,+0.0238] SIGNIFICANT
The update was never made. Both governing documents currently overstate DeepOKAN's
degradation by ~20%. REQUIRED CORRECTION.
Qualitative conclusion survives: p16 0.0357 vs p128 0.0710, diff -0.0354 CI [-0.0428,-0.0273].

## F2. The L5 learning-rate grid did not bracket DeepONet's optimum either (B14 pattern, 5th time)
l5_fill1/l5_fill2 added lr=3e-3, ABOVE the previous top edge. DeepONet is better at 3e-3 at
EVERY p:  p8 0.0276, p16 0.0280, p32 0.0290, p64 0.0284, p128 0.0275
(recorded: 0.0281 0.0293 0.0291 0.0296 0.0296).
3e-3 is still the TOP EDGE -> optimum still unbracketed. Needs lr = 6e-3 / 1e-2.

## F3. BUT the L5 flagship conclusion SURVIVES and is STRENGTHENED
At the corrected best lr, paired vs p=8, project's own alpha=0.005:
  p16  diff -0.00039 CI [-0.00293,+0.00269]  NO DIFFERENCE
  p32  diff -0.00144 CI [-0.00363,+0.00023]  NO DIFFERENCE
  p64  diff -0.00083 CI [-0.00309,+0.00171]  NO DIFFERENCE
  p128 diff +0.00012 CI [-0.00164,+0.00315]  NO DIFFERENCE
0.0276 -> 0.0275 over p=8->128 while the POD floor falls 28.7x. Flatter than published.
At p=128 it now sits 55x above its own lower bound (0.02748/0.00050).
Family null also survives: DeepONet best 0.0275 vs DeepOKAN best 0.0357,
diff -0.0082 CI [-0.0190,+0.0017] NO DIFFERENCE.

## F4. L1's headline verdict "more data is eliminated" was never measured
run_l1.py has NO training-set-size sweep. audit_l1.py sweeps POD RANK, bootstrap
calibration and holdout SPLIT -- never data quantity. The project already caught this
itself: learning_curve.py's docstring says so verbatim. And learning_curve.log measures it:
in the SAME function class (POD+HGB) and SAME 128x128 encoding as L5,
  12 materials (173 conds) 0.09292
  24 materials (345)       0.06931
  36 materials (515)       0.05367
  48 materials (691)       0.05094
1.82x improvement, NOT saturated. The condition axis is much weaker (0.0642 -> 0.0512).
=> "L1: more data eliminated" must be NARROWED to "more CONDITIONS per material is
   eliminated; more MATERIALS is not." This is a required retraction (A18) AND it is the
   scientific justification for the 240-material scale-up.
learning_curve.py DIED before writing results/learning_curve.json -> must be re-run.

## F5. Protocol 6b's stated justification for the 512x256 storage grid is contradicted by
   the data it generated
6b: "The MTZ is ~1 mm in a 100 mm column; at 128 z-points the entire front sits inside
1.4 cells." Measured on 30 stored fields, sharpest spatial front over the whole run,
0.1-0.9 band:
  at 512 z: median 372 cells, min 29
  at 128 z: median  93 cells, min  7
Two orders of magnitude broader than the estimate. The Type V two-wave structure spreads
the Henry wave across most of the column. GOOD NEWS: it defends L5's 128x128 encoding.
But the written rationale is wrong and a referee who checks will find it.

## F6. Unfinished work found on disk
- results/l5_fill1b.json never produced (l5_fill1b.log is 0 bytes) -> DeepOKAN was never
  run at lr=3e-3 for p=8,16,32. Asymmetric grid vs DeepONet.
- deeponet_lc.log stops after the header -> the operator learning-curve never ran.
- data/parametric_scale: 1457 of 4080 .npy files, no manifest.json. gen_scale.log shows
  a Windows multiprocessing failure: OSError [WinError 87] in spawn_main OpenProcess.
- results/learning_curve.json never written.

## F7. warp_predict.py's "beats the fixed frame" is not supported at the project's own standard
warp_predict.py: no seeds (every random_state=0), no bootstrap, no CI, single split.
It compares its 0.0508 against `L5_FIXED_FRAME = 0.0510`, a HARD-CODED LITERAL imported
from comoving.py line 57, and writes `"beats_fixed_frame": true` into
results/warp_predict.json on a 0.4% margin.
Violates protocol sec.3 rule 5 (3-seed minimum, "single-seed numbers may not appear in any
table, including appendices") and sec.4 (a difference whose CI includes zero is reported as
no difference). Not yet in RESULTS.md -> still a Part-B catch. Fix: 3 seeds both sides,
recompute the fixed-frame arm in the same run, paired cluster bootstrap at alpha=0.005.

## F8. b_H0 = b0/20.0 is an undeclared ninth material parameter
gen_parametric_dataset.py:136 and fetch_real_mof_data.py:71 hard-code the ratio of the
Henry-site affinity to the cluster-site affinity at exactly 20. It appears NOWHERE in
03_LADDER_PROTOCOL.md or RESULTS.md, and it is not in MATERIAL_SPACE.
It is the parameter that sets the SEPARATION BETWEEN THE TWO WAVES -- the structure the
project's best positive result (the two-wave warp) is built on. So the 40x separation range
and the whole two-wave finding are scoped to b_C0/b_H0 = 20, silently.
Protocol sec.6: "Decisions already made, with rationale. Changing any of these invalidates
results produced under the old value." This one was never recorded.

## F9. Material sampling is plain uniform, not space-filling  (MEASURED)
gen_parametric_dataset.sample_material uses independent rng.uniform on 8 parameters.
L2-star discrepancy of the actual 60-material draw : 0.0930
  same-size Latin hypercube                        : 0.0283   (3.3x better)
  same-size scrambled Sobol                        : 0.0191   (4.9x better)
  mean of 20 random uniform draws                  : 0.0655 +- 0.0115  (this draw was unlucky)
min pairwise distance (unit cube): actual 0.273, LHS 0.394, Sobol 0.505.
The novel-material split asks the model to generalise into the holes this sampler left.
The 240-material scale-up now generating uses the SAME sampler.
Also: no correlation structure between q_max / delta_H / step_rh, which are correlated in
real MOFs. Candidate confound for the flagship L5 result -- the params->coefficient map may
be hard because the material manifold is an unphysically wide uncorrelated hypercube.
TESTABLE and not yet tested.

## F10. Damkohler coverage (MEASURED, Da = k_LDF * t_final, the project's definition)
p05 122, median 626, p95 3312, max 15107.  Only 0.30% of samples have Da < 50.
To reach Da=10 at the median t_final needs k_LDF = 3.9e-4 1/s, vs the current
MATERIAL_SPACE lower bound of 0.002. Extending the range down one decade is required.
NOTE: lowering k_LDF lengthens t_final through the adaptive horizon, so Da falls
SUB-LINEARLY in k -- the sweep needs the horizon and the t_st < 2e6 s screen re-checked,
not just a smaller lower bound.

## F11. POWER OF THE L6 NULL — MEASURED, and it DEFENDS the paper
The single most likely referee attack on this project is "your nulls are just underpowered."
I measured it: resample the 12 held-out materials with replacement, inject a known
improvement into the separate arm while preserving the REAL between-arm noise structure,
and re-run the project's own compare() at alpha = 0.005.

  true improvement of separate over joint     power
                                       0 %      4 %   <- type-I rate; matches the
                                       5 %     24 %      calibrated 4.2% exactly
                                      10 %     60 %
                                      20 %     96 %
                                      30 %     98 %

So the design has 96% power at a 20% effect and 98% at 30%. The prior conduction project's
H1 effect was 16x (a 94% improvement) — this design would detect that with certainty.
The observed point estimate goes the WRONG way (separate is 26% worse).

=> "H1 is not supported" is a POWERED null, not an underpowered one, and the paper can say
   so with a number. RECOMMENDATION: publish a power curve for every null verdict in the
   ladder (L4 material axis, L5 flat-in-p, L5 DeepONet vs DeepOKAN, L6 H1). That converts
   "no difference detected" into "improvements larger than ~15% are excluded at 90% power",
   which is a far stronger and more publishable statement, and it is cheap.
   It also lets the L5 family null be stated as a proper equivalence result (TOST) rather
   than an absence of evidence.

## F12. The L4b "physics hurts once bounds exist" result has two open referee attacks
(a) The physics arm's w_pde is set by gradient-norm balancing -- ONE choice, never swept.
    Protocol rule: "Each arm is compared against the STRONGEST configuration of its
    competitor." Here the physics arm is the arm being argued against, so it must be given
    a w_pde sweep or the 1.6x-worse result is a strawman by the project's own rule.
    This is the B14/B22/B23 pattern applied to L4b -- it has not been checked there.
(b) The stated reason physics cannot help on the material axis is "a residual is evaluated
    only at collocation points for materials in the training set, and never at inference."
    That is true of the arm as built, but NOT of physics-informed learning in general.
    TEST-TIME PHYSICS REFINEMENT -- freeze the trained model, then for each NOVEL material
    minimise the PDE residual at inference with zero data -- removes exactly that
    limitation. It is cheap, it is the arm a modern referee will ask for, and it is the
    only version of "physics as a loss" that can act on the material axis at all.
    If it still fails, the L4 conclusion becomes MUCH stronger and generalises.

## F13. Figure defects seen by direct inspection
Fig5 panel A: a BAR CHART on a LOG y-axis. Bar length is meaningless when the baseline is
  arbitrary; all four arms look identical and the "33x/40x/46x floor" text labels are doing
  the work the bars should. Referees and production editors object to this specifically.
  Fix: points with CI whiskers on a linear axis, or a dot-and-error-bar plot with the POD
  floor as a horizontal reference.
Fig7: no error bars or CI bands anywhere, on a figure whose entire argument is "these
  differences are not significant". A flat line with no uncertainty band cannot make that
  argument visually. Add +-1 sd (3 seeds) or the bootstrap CI.
Fig7 panel A/B/D: built from the STALE DeepOKAN numbers (0.0818/0.0884) and the stale
  DeepONet lr grid. Panel A's "59x" annotation becomes 55x. Panel D's collapse rates were
  computed on the old lr grid and must be recomputed with lr=2e-4 included.
Fig2_ground_truth.pdf is 39.2 MB against a 340 KB PNG -> an unrasterised pcolormesh with
  ~10^5-10^6 vector quads. Most journals reject or mangle this. Fix:
  pcolormesh(..., rasterized=True) with dpi=600, or imshow.

## F14. *** THE BIGGEST FINDING *** The pre-registration claim is UNVERIFIABLE
03_LADDER_PROTOCOL.md line 3: "**Frozen 2026-08-20, before any model is trained.**"
That single sentence is the paper's strongest asset. It is currently unfalsifiable:

  - There is NO git repository (`Is a git repository: false`).
  - There is no OSF registration, no Zenodo DOI, no arXiv preprint, no .ots timestamp,
    no external immutable record of ANY kind.
  - 03_LADDER_PROTOCOL.md's own mtime is 2026-08-24, four days AFTER the claimed freeze,
    because results were appended into the same file. The file cannot distinguish
    "frozen on the 20th and appended to" from "written on the 24th".

A referee who is sympathetic to a pre-registered falsification ladder is EXACTLY the
referee who will ask to see the registration. There is nothing to show them.

FIX (cheap, do it today):
  1. git init; commit everything now; every future change is timestamped and diffable.
  2. SPLIT the frozen protocol from the results log. 03_LADDER_PROTOCOL.md currently
     mixes a pre-registration with 1100 lines of post-hoc results. A pre-registration
     that is edited is not a pre-registration. Freeze `PROTOCOL_v1.md` verbatim, move
     every result into RESULTS.md, and record protocol amendments as dated entries.
  3. Register the follow-up work (the low-Da H1 re-test, the two-wave warp) on OSF or
     as a Zenodo-DOI'd preprint BEFORE running it. Then at least part of the paper has a
     verifiable pre-registration.
  4. In the manuscript, state honestly that the L0-L7 pre-registration is self-attested
     and the follow-up is externally registered. That is more credible than silence and
     it is the kind of candour that already characterises this project.

## F15. No reproducibility infrastructure at all
Missing: requirements.txt, environment.yml, pyproject.toml, README, LICENSE, CITATION.cff,
Makefile/Dockerfile, and any single command that reproduces RESULTS.md.
Installed versions are all very recent and unpinned:
  numpy 2.4.6  scipy 1.17.1  scikit-learn 1.8.0  torch 2.12.0+cpu  xgboost 3.2.0
  matplotlib 3.10.9  pandas 3.0.3
npj Computational Materials, the Nature family, JCP and CMAME all have code-availability
requirements this repository cannot currently meet. This is a submission blocker, not a
nicety, and it is a few hours of work.

## F5 CORRECTION — the project already caught the MTZ discrepancy
solver_fd.py:119-129 documents it explicitly: "CAVEAT, measured: this estimate is
ISOTHERMAL and underestimates the real front... 555 cells at its sharpest where this
formula predicts 21 -- a factor of ~26... Do not quote it as the physical front width."
That is exactly right, with the mechanism (the thermal wave running ahead of the mass
front) and the direction of the error. Excellent work; withdraw my F5 as a defect.

What REMAINS from F5 is narrower but still real:
  03_LADDER_PROTOCOL.md sec.6b still says "The MTZ is ~1 mm in a 100 mm column; at 128
  z-points the entire front sits inside 1.4 cells" and uses that to justify the 512x256
  storage grid -- a spec the protocol itself declares part of information parity.
  The code's own docstring contradicts the protocol's number by 26x. Two governing
  documents disagree, and the one a referee reads is the protocol.
  Fix: correct sec.6b to the measured front width and restate the storage-grid rationale.
  (Consequence: 512 was 4x more than needed. Harmless, but the 240-material scale-up is
  already storing at 256, which is the right call and should be said out loud.)
  Also verified: the MTZ screen NEVER FIRED -- 0 of 32 rejections. All 32 were
  "low feed loading". So nothing was wrongly discarded.

## F16. The one active screen biases against the AWH-relevant regime
The only filter that fires is theta(c_in) < 0.10 -> "feed loads only X of capacity"
(32 of 1020 draws, 3.1%). It rejects HIGH-capacity materials at LOW feed humidity --
which is precisely the arid-condition, high-q_max corner that atmospheric water
harvesting exists to serve. The paper's motivation is AWH below 30% RH; the dataset
systematically thins exactly there. Small effect (3.1%) but a referee in the MOF/AWH
community will notice it immediately. Either justify it explicitly or lower the threshold
and report the sensitivity.

## F17. The temperature bound contradicts the project's own best result — free win available
validate.py reproduces 22 PASS / 0 FAIL / 0 SKIP independently. But its model gate prints:
  PIKAN [182,406] K   PI_DeepOKAN [197,446] K   DeepONet_base [209,321] K
output_head.py: DT_MAX_DEFAULT = 0.5 in units of T_ref, symmetric tanh
  -> T in roughly [150, 450] K, i.e. water frozen solid to superheated steam.
The docstring says this is deliberate: "generous next to the adiabatic rise (beta ~ 3), so
it NEVER BINDS on a physical solution -- it only prevents the pathological one."

That was the right call when the head existed only to stop the van't Hoff overflow (A2/B3).
It is the WRONG call now, because L4b subsequently measured that HARD BOUNDS ARE THE SINGLE
BEST INTERVENTION IN THE WHOLE PROJECT: 11.5x on the time axis, +25% on materials. Those
bounds were applied to c and q ONLY. Temperature was deliberately left loose.

The physical envelope is known and narrow:
  T_in in [288.15, 313.15] K (CONDITION_SPACE)
  peak excursion is ONE-SIDED and reaches +66 K (defect B21 measured this)
  -> physical bound is about [T_in - 5 K, T_in + 80 K], and ASYMMETRIC.
The head is symmetric tanh. B21 explicitly learned "the excursion is one-sided and reaches
+66 K, so the symmetric window was genuinely wrong" -- about the isotherm fingerprint --
and that lesson was never carried across to the output head.

ARM TO RUN (cheap, one afternoon, high expected value):
  re-run the L4b 2x2 with a tightened, one-sided temperature head
  (T* = 1 + dT_hi*sigmoid(raw_T) - small, dT_hi ~ 0.27, dT_lo ~ 0.02).
  The project's own strongest measured effect predicts this helps, and if it does it
  strengthens the paper's central claim -- "the value of physical knowledge lies in HOW it
  is imposed" -- from two variables to three, on the variable with the largest dynamic
  range. If it does NOT help, that is an informative boundary on the claim.
