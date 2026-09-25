# RESEARCH PROGRAM — AI that explains MOF/COF water sorption, not only fits it

Written 2026-09-25, after the author set the scope: *use AI (equation discovery,
Kolmogorov–Arnold networks, neural operators, structure-preserving and liquid networks)
to understand the physics of MOF/COF atmospheric water harvesting, across as many
papers as the questions need.*

It rests on three fetched-source literature journals in `research/` (every source
opened, not searched — rule 8):

| journal | sources | question |
|---|---|---|
| `research/lit_equation_discovery.md` | 57 fetched | what equation discovery has done for adsorption, and where it cannot work |
| `research/lit_structure_preserving.md` | 50 fetched | which "physics-shaped" networks fit dissipative, non-isothermal sorption |
| `research/lit_water_harvesting_twins.md` | in progress | devices with reusable data, digital twins, material-transfer surrogates, water-isotherm databases, COFs |

Every paper below keeps the discipline paper 1 earned: a pre-registration frozen
before data, pre-declared verdict words, matched budgets, ≥3 seeds, the strongest
competitor configuration, a minimum detectable effect on every null, no number without
a script, a citation gate, and a correction ledger.

---

## 0. Where each exciting idea actually lands (the honest map)

| idea | verdict for THIS physics | evidence | where it goes |
|---|---|---|---|
| SINDy / weak-SINDy / PySR / KAN-symbolic | **Right question, one known failure regime.** Near local equilibrium the rate signal is ~1 % of the state (settled: `03_LADDER_PROTOCOL.md` identifiability section). Dataset v2 spans Da 3.8–689, so the informative regime is now covered | eq-discovery journal S1, S8, S29, S33, S36 | **Paper 2** |
| KAN (as an architecture) | Refuted on our data (L3, 6/6 for the MLP); external evidence agrees (S42–S44 in the structure journal) | paper 1, L3 | Only as symbolic extraction inside paper 2 (KANDy), never a headline |
| FNO / DeepONet / neural operators | FNO is significantly better than DeepONet; neither removes the wall | paper 1, L5 | Paper 1; the operator piece of paper 4 |
| Physics-informed DeepONet / DeepOKAN | Soft penalty only; DeepOKAN is published (A12); physics loss ties or hurts (L4) | paper 1, A12, L4 | Not a paper on its own |
| Hamiltonian / Lagrangian neural networks | **Wrong physics.** They conserve energy and are time-reversible; adsorption dissipates | structure journal, fit matrix | **Not pursued** — and the reason is written down |
| GENERIC / metriplectic / port-metriplectic / Onsager networks | **The right family** for dissipative, non-isothermal sorption; **no learned model of adsorption found** | structure journal, gap 1 | **Paper 3** |
| Liquid (LTC/CfC) networks | Generic continuous-time RNNs with no physics; the founding paper's only physics test is a robot benchmark. Neural ODE/CDE is the established process-control tool | structure journal S31–S34 | One baseline in **paper 4**, not a headline |
| Digital twin of a water harvester | Depends on device data being reusable | water-harvesting journal | **Paper 4** (pending the data audit) |

---

## Paper 1 — the falsification ladder (IN FLIGHT)

What binds a surrogate's error on unseen materials. CONTINUE_HERE.md owns its
state. Remaining: the L4b section once the follow-up lands, the L5 DeepONet bracket
(autorun job 2b), the three rungs still at 12 materials, 50 number-words owed. Venue
CMAME. **Newly found prior art it must cite and now does: MAPLE (B68).**

## Paper 2 — When can AI discover adsorption kinetics? A discoverability map

**Question.** For which regimes — Damköhler (Da), Péclet (Pe), measurement noise,
isotherm error, and observation model — can the adsorption rate LAW be discovered from
breakthrough data, and does discoverability fail at the same boundary as classical
parameter identifiability, or earlier?

**Why it is new (fetched evidence).** No paper maps rate-law discoverability over
these axes (gap G1); Santana et al. 2023 (S1) is a single point with an exact isotherm
at Da ≈ 0.9; Taylor et al. 2026 (S35) maps parameter sensitivity, not discovery.
Isotherm error has never been treated as an errors-in-variables problem in discovery
(G2), and discovery and profile-likelihood identifiability have never been compared on
one grid (G4). MOF water kinetics have no discovery study, and the MOF-303 rate drops
at the isotherm step (S39): a state-dependent k(q) is an untested target (G5).

**What is NOT new, and must be said so.** "Near local equilibrium the mass-transfer
coefficient is not identifiable from breakthrough data" is classical (S8, S29, S33,
S36, S37). Paper 2 turns it into a quantitative discoverability boundary with a
mechanism; it does not claim the phenomenon.

**Design (to be frozen in `PREREG_P2_discoverability.md` before any grid is run).**
- Ground truth from the verified solver (paper 1's L0 checks), CPU-cheap (~17
  worker-seconds per solve). Grid over Da (10⁻¹–10³), Pe, noise σ, isotherm error ε,
  observation {outlet only, interior profiles}, isotherm shape {favourable Langmuir,
  MOF-303-like step}, and true law {constant-k LDF, k(q) near the step}.
- Competitors, each in its strongest configuration (eq-discovery journal §d):
  S1's UDE+SINDy/SR pipeline reproduced; weak-form SINDy; ensemble/Bayesian SINDy
  (inclusion probability of the (q*−q) term and of its correct sign — the per-cell
  metric); MIOSR with sign constraints; errors-in-variables ODR-BINDy and WENDy;
  SINDy-PI for rational laws; constrained PySR; KANDy (secondary); slow-manifold
  discovery (the method expected to win at high Da by returning isotherm + apparent
  dispersion instead of k).
- Identifiability on the same grid: profile likelihood for k, D_L and the isotherm
  parameters; Fisher information and Gram-matrix conditioning as mechanistic
  predictors.
- Pre-declared hypotheses: (H2a) the discoverability boundary is predicted by the
  driving-force fraction relative to isotherm error; (H2b) discoverability is lost
  before identifiability; (H2c) errors-in-variables methods move the boundary.
  Each with its falsifier and MDE.
- External points: plot S1 on the map with its Da recomputed under our definition;
  if it lands in our failure region the contradiction is reported, not explained away.

**Risks (from the journal).** A straw-man competitor (answered by the list above); Da
may not be the single right axis (Pe and isotherm shape are axes); an EIV method may
rescue recovery (then the headline becomes a law about isotherm accuracy); scoop risk
is moderate (the Santana/Nogueira group, a differentiable-hybrid adsorption group).

**Venue.** Chem. Eng. Sci. / AIChE J. / Digital Discovery (choose at freeze time).

## Paper 3 — Thermodynamically consistent learned sorption

**Stage A (small, clean, first).** A learned adsorbed-phase potential whose
derivatives give the isotherm q*(p, T) and the isosteric heat, so Clausius–Clapeyron
consistency, the Henry limit and sign-correct (entropy-producing) LDF kinetics hold
**by construction**, not by penalty. Found done for vapour–liquid equilibrium (hard
Gibbs–Duhem), and only as penalties for sorption (98.6 % monotonicity, so violations
remain) — structure journal gap 4. Test on real multi-temperature water isotherms of
MOFs and COFs (datasets from the water-harvesting journal) against unconstrained and
penalty-constrained fits: extrapolation in temperature, isosteric-heat accuracy,
physical-violation counts.

**Stage B (ambitious).** A GENERIC / port-metriplectic latent model of the
non-isothermal column, with energy and entropy fixed from the known thermodynamics
(not learned — otherwise "respects the second law" is a statement about a surrogate
quantity), inlet/outlet/wall as ports. No learned structure-preserving model of
adsorption was found. **Pre-declared value test:** what structure is supposed to buy —
stability of long multi-cycle rollouts, data efficiency, zero unphysical outputs —
measured against the same model without structure. Paper 1's L4 result (physics as a
loss ties or hurts) is the standing warning that admissibility is not accuracy.

## Paper 4 — A digital twin of a MOF water harvester, across materials (DATA-GATED)

Cycle-level dynamics (uptake/release vs time, temperature, RH, productivity) as a
controlled low-dimensional system: neural ODE / neural CDE as the principal model,
liquid networks as one baseline, the Paper 3 constitutive layer inside, material
transfer tested as in paper 1. **Gated on the water-harvesting data audit**: it goes
ahead only if published device time series are reusable at the resolution a twin
needs. If they are not, the paper does not happen on invented data.

## COFs

The title of paper 1 claims only the frameworks it models, because no COF breakthrough
measurement exists (paper 1, Limitations). COFs enter the program where data exists:
COF-432 and any multi-temperature COF water isotherms go into Paper 3A as real
held-out materials. A standalone COF paper waits for data.

---

## Order, and why

1. **Paper 1 to submission** — it is nearly done and everything else cites it.
2. **Paper 2 pre-registration and pilot** — extends a settled result directly, uses
   the verified solver, runs on this CPU, and has the clearest fetched novelty.
3. **Paper 3A** — small, uses real data, gives the program its first real-material
   COF/MOF result.
4. **Paper 3B and Paper 4** — after 3A proves the constitutive layer, and after the
   data audit says whether a twin can be honest.

Compute: all four are CPU-feasible at the scales above; a GPU is a speed multiplier
for 3B and 4, not an enabler. One training job at a time stays the rule — new jobs go
into `autorun.sh` with a done-test.
