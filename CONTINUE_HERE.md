# CONTINUE HERE — session handoff

Rewritten 2026-09-02. Read this, then `RESULTS.md`, then `AUDIT_2026-08-30.md`.
`RETRACTIONS.md` is the record of everything withdrawn — **23 Part-A, 38 Part-B**.

---

## 1. First thing to do in a new session

```bash
cd "C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
./resume.sh          # shows what is done and what is missing, runs nothing
./resume.sh go       # continues only the missing work
```

`resume.sh go` finishes any incomplete FNO arm, then runs L6-v2 **fold by fold**,
then prints the L6-v2 verdict. Every runner writes after each completed arm, so a
shutdown loses at most one configuration.

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
| L1 | "more data" | ⚠️ **narrowed (A18)** — conditions axis eliminated, materials axis is **not** |
| L2 | "more capacity" | ✅ done (legacy data; not re-run on v2) |
| **L3** | **"better basis / KAN"** | ✅ **FINAL** — fully bracketed, 6/6 significant |
| L4/L4b | "physics as a loss" | ⚠️ needs a w_pde sweep and test-time refinement |
| **L5** | **"you need an operator"** | ✅ **FINAL** — narrowed by FNO |
| **L6** | **"separate identification"** (H1, primary) | 🔄 **RUNNING** — v2, fold 3 of 5 |
| L7 | "is learning needed" | ✅ done (legacy data; not re-run on v2) |

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

**Two-wave warp** — 3 seeds, both arms in one run, paired cluster bootstrap:
fixed 0.05005, predicted-warp 0.04770 (**no difference**), oracle 0.02203
(**significant, 2.27×**). The gain is entirely consumed by front-location error.
**2.17× headroom, established.** Monotonicity is *not* the lever (tested, B34).

**Dataset v2** — 3947 sims, 240 materials, Sobol, Glueckauf kinetics.
Da median **27.5** with **77.8 %** in the informative 5–60 band, against legacy's
626 and 1.1 %.

---

## 4. What is genuinely good — do not undo

1. **The retraction ledger.** 23 Part-A, 38 Part-B, 18 marked "our own error".
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
1. **L2, L7 have not been re-run on v2.** L1's material-axis learning curve has not
   either. Every rung should report on the same dataset.
2. **L4/L4b's "physics hurts once bounded" rests on one weighting rule.** The arm
   being argued against never got a `w_pde` sweep — this project's own rule 4,
   turned inward. Add NTK weighting and self-adaptive weights, or withdraw.
3. **~260 citations still unverified.** Two tranches done (≈90 refs).
4. **No experimental anchor yet.** Li et al. 2025 (*RSC Adv*, CC BY, on PMC,
   Fig. 11) is the target — 0.6 cm ID, ~10 cm bed, 298 K, 300 sccm, geometry
   matching ours. Digitising it is a submission-tier change.
5. **The figure set is built for the old narrative.** No figure exists for the
   two-wave warp or the coefficient-map bottleneck — the two strongest results.

**Known and scoped:**
- `C_ps = 1000 J/kg/K` has **no citable source**. Report as a 900–2400 J/kg/K
  sensitivity band, not a constant.
- **No COF breakthrough measurement exists anywhere** (searched, not found). The
  "no COF case" gap closes by saying so, not by inventing one.
- Novel-condition split has **2 clusters**. Descriptive only, no CIs.

---

## 6. Steps remaining — roughly 8–11 sessions

1. **Finish L6-v2** and analyse (`analyze_l6_v2.py`). — running
2. **L1 learning curve, L2, L7 on v2.** — 2 sessions
3. **L4b weighting sweep + test-time physics refinement.** — 1–2 sessions
4. **Citations tranche 3+, and digitise Li et al. 2025.** — 2 sessions
5. **Figure set rebuilt for the current narrative.** — 1–2 sessions
6. **Manuscript.** — 2–3 sessions

---

## 7. Rules carried forward

1. No number from a failing `validate.py` category. (22 gates, all passing.)
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
