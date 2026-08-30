"""Generate the parametric dataset the ladder trains on.

Design decisions, and why — these are frozen specs (protocol section 6).

Sampling structure
------------------
Materials and operating conditions are sampled SEPARATELY and nested:
`n_materials` frameworks, each run at `n_conditions` operating points. This is
not cosmetic. Hypothesis H1 is about transfer to held-out MATERIALS, and that
split only exists if materials are a real grouping in the data. Sampling one
flat cloud of (material x condition) vectors would make novel-material and
novel-condition indistinguishable and H1 untestable.

Storage resolution
------------------
Solved at N_z = 2000 (verified resolution, L0), stored at 512 x 256 float32.

    2000 x 500   12.00 MB/sim   front spans 21.4 cells   1000 sims = 12.0 GB
     512 x 256    1.57 MB/sim   front spans  5.5 cells   1000 sims = 1.6 GB
     128 x 128    0.20 MB/sim   front spans  1.4 cells   1000 sims = 0.2 GB

The "front spans" column above is the ISOTHERMAL MTZ estimate from
`AdsorptionPhysicsConfig.mtz_width`, and it is WRONG BY ~26x as a description of
the real front — corrected 2026-08-30, defect B31. That formula is isothermal;
the actual transition is far broader because the thermal wave runs ahead of the
mass front and shifts the isotherm. Measured directly on 30 stored fields, the
SHARPEST spatial front over an entire run spans **372 cells (median), minimum 29,
at 512 z** — i.e. 93 and 7 at 128 z, not 1.4.

So 512 x 256 is roughly 4x more resolution than the physics requires, and the
128 x 128 encoding L5 uses is adequate rather than degenerate. The oversampling
is harmless and is kept for the legacy dataset so prior comparisons stay valid;
design v2 stores at 256 x 256.

  !! The stored resolution is part of INFORMATION PARITY. Every arm in the
  !! ladder must see the same grid. Changing it invalidates every prior
  !! comparison -- record it in RETRACTIONS.md if it ever changes.

Time axis
---------
Each condition has its own stoichiometric time, so t_final differs per run.
Time is stored NORMALISED to [0,1] with `t_final` kept as a per-sample scalar.
Operators therefore learn on a common time axis, and t_final becomes a
predictable output rather than a hidden inconsistency.

Usage
-----
    python gen_parametric_dataset.py --materials 4 --conditions 3 --workers 4 --out data/probe
    python gen_parametric_dataset.py --materials 60 --conditions 17 --workers 8
"""
from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

from isotherm import calibrate_step, henry_constant, q_star_np
from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data

R_GAS = 8.314

# Storage resolution is read from the ENVIRONMENT, not from argparse, because
# multiprocessing on Windows uses spawn: each worker re-imports this module, so a
# value assigned in main() would never reach run_one() and every field would be
# silently written at the default resolution. Environment variables do propagate.
# The defaults reproduce the original 988-condition dataset exactly.
STORE_NZ = int(os.environ.get("ADS_STORE_NZ", 512))
STORE_NT = int(os.environ.get("ADS_STORE_NT", 256))
SOLVE_NZ = int(os.environ.get("ADS_SOLVE_NZ", 2000))
# How often the resume checkpoint is written, in completed runs. At ~4.4 s per
# run this bounds the work a sleeping laptop can destroy to a few minutes.
CHECKPOINT_EVERY = int(os.environ.get("ADS_CHECKPOINT_EVERY", 50))
HORIZON = 2.5          # multiples of stoichiometric time
# Ratio of cluster-site to Henry-site affinity, b_C0 / b_H0. FROZEN AT 20.
# Undeclared until the 2026-08-30 audit (defect B29); it sets the separation
# between the Henry wave and the cooperative shock and is therefore load-bearing
# for the two-wave analysis. Recorded in the manifest from now on.
B_H_RATIO = float(os.environ.get("ADS_B_H_RATIO", 20.0))


def p_sat_water(T):
    Tc = T - 273.15
    return 610.94 * np.exp(17.625 * Tc / (Tc + 243.04))


def rh_to_conc(rh, T):
    return rh * p_sat_water(T) / (R_GAS * T)


# ─────────────────────────────────────────────────────────────────────────────
# parameter space
# ─────────────────────────────────────────────────────────────────────────────

MATERIAL_SPACE = {
    "q_max":          (8.0, 30.0),      # mol/kg
    "delta_H":        (-60000.0, -38000.0),   # J/mol
    "step_rh":        (0.08, 0.45),     # cooperative step position
    "isotherm_n":     (1.0, 6.0),       # 1 = Type I, >1 = Type V
    "henry_fraction": (0.03, 0.25),
    "k_LDF":          (0.002, 0.05),    # 1/s
    "rho_p":          (700.0, 1400.0),  # kg/m3
    "eps_t":          (0.30, 0.48),
}

CONDITION_SPACE = {
    "rh_feed": (0.15, 0.85),
    "v":       (0.03, 0.30),     # superficial, m/s
    "T_in":    (288.15, 313.15), # K
}


# ─────────────────────────────────────────────────────────────────────────────
# DESIGN v2 (2026-08-30) — physically consistent kinetics, space-filling sampling
#
# Two defects in the legacy design, both found by the 2026-08-30 audit, both
# fixed here. `--design legacy` reproduces the original 988-run dataset exactly.
#
# (1) k_LDF WAS SAMPLED INDEPENDENTLY OF PARTICLE SIZE (defect: physical
#     inconsistency, and the cause of the Damkohler-coverage gap). For a
#     bidisperse adsorbent the mass-transfer coefficient is DETERMINED by the
#     pellet, through Glueckauf:
#
#         k_LDF = 15 eps_p D_p / (R_p^2 rho_p K),    D_p = D_m / tau,  K = q*/c
#
#     Measured over the legacy draws, the sampled k_LDF is a **median 10x** (p95
#     37x) faster than a 2 mm pellet can physically support. The consequence was
#     Da = k*t_final with median 626 and only **1.1 %** of samples in the
#     kinetically-informative band Da ~ 5-60 — which is precisely why L6's H1
#     was untestable: at local equilibrium there is no kinetic object to identify.
#
#     Deriving k_LDF from a sampled d_p instead puts **~90 %** of the dataset in
#     that band (measured: d_p = 3 mm -> Da median 28; 5 mm -> median 10) while
#     making every material physically realisable. One change, three defects.
#
#     K is the CHORD slope q*(c_in)/c_in, not the local derivative: the chord is
#     the slope the front actually travels along, it stays finite at the
#     cooperative step where the derivative does not, and it keeps k_LDF one
#     constant per (material, condition) so the solver and its Anzelius-Schumann
#     verification remain valid. Lassitter et al. (Chem. Eng. Sci. 285:119430,
#     2024) measure that the true transport rate DIPS at the isotherm step,
#     because rate = corrected diffusivity / isotherm slope; that loading
#     dependence is not modelled here and is a stated limitation.
#
# (2) SAMPLING WAS PLAIN rng.uniform, NOT SPACE-FILLING. Measured L2-star
#     discrepancy of the legacy 60-material draw: 0.0930, against 0.0191 for
#     same-size scrambled Sobol — 4.9x worse, and worse than the average random
#     draw (0.0655 +- 0.0115), so that particular draw was also unlucky. The
#     novel-material split asks a model to generalise into the holes the sampler
#     left. Scrambled Sobol is a drop-in fix at identical cost.
# ─────────────────────────────────────────────────────────────────────────────

D_M_WATER = 2.6e-5     # molecular diffusivity of water vapour in air, m2/s (~298 K)
TORTUOSITY = 3.0       # macropore tortuosity, typical packed pellet
EPS_PELLET = 0.35      # pellet macroporosity

MATERIAL_SPACE_V2 = {
    "q_max":          (8.0, 30.0),
    "delta_H":        (-60000.0, -38000.0),
    "step_rh":        (0.08, 0.45),
    "isotherm_n":     (1.0, 6.0),
    "henry_fraction": (0.03, 0.25),
    # d_p REPLACES k_LDF as the sampled kinetic degree of freedom. It is a real
    # formulation choice, it is what an experimentalist actually controls, and it
    # makes the kinetics follow from it rather than contradict it. 1.5-5 mm spans
    # the classical packed-bed range (Ruthven) up to the large pellets that reach
    # Da ~ 10.
    "d_p":            (0.0015, 0.0050),
    "rho_p":          (700.0, 1400.0),
    "eps_t":          (0.30, 0.48),
}


def _sobol_unit(n, dim, seed):
    """n points in [0,1]^dim from a scrambled Sobol sequence.

    Sobol is generated in powers of two; `random_base2` refuses anything else, so
    draw the next power of two and truncate. Truncating a scrambled Sobol
    sequence preserves its low-discrepancy property.
    """
    from scipy.stats import qmc
    m = int(np.ceil(np.log2(max(n, 2))))
    return qmc.Sobol(d=dim, scramble=True, seed=seed).random_base2(m=m)[:n]


def sample_material(rng, idx):
    m = {k: float(rng.uniform(*v)) for k, v in MATERIAL_SPACE.items()}
    m["material_id"] = idx
    return m


def sample_condition(rng, idx):
    c = {k: float(rng.uniform(*v)) for k, v in CONDITION_SPACE.items()}
    c["condition_id"] = idx
    return c


def sample_design(n, space, seed, key):
    """A scrambled-Sobol design over `space`, one dict per point."""
    keys = list(space)
    U = _sobol_unit(n, len(keys), seed)
    out = []
    for i in range(n):
        d = {k: float(space[k][0] + U[i, j] * (space[k][1] - space[k][0]))
             for j, k in enumerate(keys)}
        d[key] = i
        out.append(d)
    return out


def k_ldf_glueckauf(p, c_in, T, d_p):
    """Macropore-controlled LDF coefficient — kinetics DERIVED from the pellet."""
    R_p = d_p / 2.0
    D_p = D_M_WATER / TORTUOSITY
    q_in = float(q_star_np(np.array([c_in]), np.array([T]), p)[0])
    K = max(q_in / max(c_in, 1e-12), 1e-9)          # chord slope, m3/kg
    return 15.0 * EPS_PELLET * D_p / (R_p ** 2 * p.rho_p * K)


def build_physics(mat, cond):
    p = AdsorptionPhysicsConfig()
    p.q_max = mat["q_max"]
    p.delta_H = mat["delta_H"]
    p.isotherm_n = mat["isotherm_n"]
    p.henry_fraction = mat["henry_fraction"]
    p.rho_p = mat["rho_p"]
    p.eps_t = mat["eps_t"]

    p.T_in = cond["T_in"]
    p.T_w = cond["T_in"]
    p.v = cond["v"]
    p.L = 0.10
    # d_p is sampled in design v2 and fixed at 2 mm in the legacy design.
    p.d_p = float(mat.get("d_p", 0.002))
    p.D_L = 0.7 * 2.5e-5 + 0.5 * p.d_p * (p.v / p.eps_t)

    # place the cooperative step at the material's step_rh, at its own T_in
    c_step = rh_to_conc(mat["step_rh"], cond["T_in"])
    p.b0 = calibrate_step(p, c_step, cond["T_in"])
    # RATIO OF HENRY-SITE TO CLUSTER-SITE AFFINITY. Fixed at 20 throughout. This
    # was an undeclared spec until the 2026-08-30 audit (defect B29) and it is
    # load-bearing: it sets the SEPARATION BETWEEN THE TWO WAVES, which is the
    # structure the co-moving/two-wave analysis is built on. Recorded here, in
    # the manifest, and in the protocol so the 40x separation range is properly
    # scoped to it.
    p.b_H_ratio = B_H_RATIO
    p.b_H0 = p.b0 / B_H_RATIO

    # KINETICS. Legacy: k_LDF sampled independently of d_p (physically
    # inconsistent — median 10x faster than the pellet supports). v2: derived
    # from the pellet through Glueckauf, which is both consistent and lands ~90 %
    # of the dataset in the informative Damkohler band. See the design note above.
    if "k_LDF" in mat:
        p.k_LDF = mat["k_LDF"]
    else:
        c_in = rh_to_conc(cond["rh_feed"], cond["T_in"])
        p.k_LDF = k_ldf_glueckauf(p, c_in, cond["T_in"], p.d_p)
    return p


def screen(p, c_in):
    """Reject degenerate conditions BEFORE spending a solve on them.

    Returns None if acceptable, else a string reason. Rejections are logged and
    counted -- a silently filtered dataset is a biased dataset.
    """
    T = p.T_in
    theta = float(q_star_np(np.array([c_in]), np.array([T]), p)[0]) / p.q_max
    if theta < 0.10:
        return f"feed loads only {theta:.3f} of capacity"
    if theta > 0.995:
        return f"feed saturates ({theta:.4f}) — isotherm unidentifiable"
    if not np.isfinite(henry_constant(T, p)) or henry_constant(T, p) <= 0:
        return "non-physical Henry constant"
    width, _ = p.mtz_width(c_in, T)
    if width / (p.L / SOLVE_NZ) < 5.0:
        return f"MTZ {width * 1e3:.3f} mm unresolvable at N_z={SOLVE_NZ}"
    t_st = p.stoichiometric_time(c_in, T)
    if not (60.0 < t_st < 2.0e6):
        return f"stoichiometric time {t_st:.3g}s outside practical range"
    return None


def resample(z, t, field, nz_out, nt_out, L, t_final):
    """Bilinear resample a (N_z, N_t) field onto a uniform (nz_out, nt_out) grid."""
    z_out = np.linspace(0.0, L, nz_out)
    t_out = np.linspace(0.0, t_final, nt_out)
    tmp = np.empty((field.shape[0], nt_out))
    for i in range(field.shape[0]):
        tmp[i] = np.interp(t_out, t, field[i])
    out = np.empty((nz_out, nt_out))
    for j in range(nt_out):
        out[:, j] = np.interp(z_out, z, tmp[:, j])
    return out.astype(np.float32)


def run_one(task):
    mat, cond = task
    try:
        p = build_physics(mat, cond)
        c_in = rh_to_conc(cond["rh_feed"], cond["T_in"])
        why = screen(p, c_in)
        if why:
            return {"ok": False, "reason": why, "mat": mat["material_id"], "cond": cond["condition_id"]}

        # ADAPTIVE HORIZON. A fixed 2.5x stoichiometric multiple rejected ~20% of
        # draws for incomplete breakthrough -- and those rejections are not
        # random. They fall on high-capacity, slow-kinetics materials and on
        # strongly cooled beds, where wall cooling lets the solid keep re-
        # adsorbing past the isothermal stoichiometric estimate. Dropping them
        # would bias the dataset toward fast, low-capacity frameworks and quietly
        # narrow the very parameter space H1 is tested over.
        #
        # Extend instead of reject, and record how many extensions were needed.
        t_st = p.stoichiometric_time(c_in, p.T_in)
        n = None
        for attempt, mult in enumerate((HORIZON, 2 * HORIZON, 5 * HORIZON, 12 * HORIZON)):
            t_final = mult * t_st
            z, t, y = generate_breakthrough_data(
                p, N_z=SOLVE_NZ, t_final=t_final, c_in=c_in, T_in=p.T_in,
                n_snapshots=600, verbose=False,
            )
            if not np.all(np.isfinite(y)):
                return {"ok": False, "reason": "non-finite solution",
                        "mat": mat["material_id"], "cond": cond["condition_id"]}
            n = len(z)
            c, q, T = y[:n], y[n:2 * n], y[2 * n:]
            exit_ratio = float(c[-1, -1] / c_in)
            if exit_ratio >= 0.90:
                break
        if exit_ratio < 0.90:
            return {"ok": False, "reason": f"incomplete breakthrough at {12 * HORIZON:g}x stoich ({exit_ratio:.3f})",
                    "mat": mat["material_id"], "cond": cond["condition_id"]}

        fields = np.stack([
            resample(z, t, c / c_in, STORE_NZ, STORE_NT, p.L, t_final),
            resample(z, t, q / p.q_max, STORE_NZ, STORE_NT, p.L, t_final),
            resample(z, t, T / p.T_in, STORE_NZ, STORE_NT, p.L, t_final),
        ])
        return {
            "ok": True, "fields": fields,
            "mat": mat["material_id"], "cond": cond["condition_id"],
            "t_final": t_final, "t_stoich": t_st, "c_in": c_in,
            "exit_ratio": exit_ratio,
            "horizon_mult": t_final / t_st,
            "horizon_extensions": attempt,
            "T_peak_rise": float(T.max() - p.T_in),
            # Kinetic regime, recorded PER SAMPLE so the Damkohler coverage of a
            # dataset is auditable without re-deriving it. The audit found the
            # legacy dataset had Da median 626 with only 1.1 % in the informative
            # band, and nothing in the manifest said so.
            "k_LDF": float(p.k_LDF),
            "d_p": float(p.d_p),
            "Da": float(p.k_LDF * t_final),
        }
    except Exception as e:  # a failed draw must not kill the sweep
        return {"ok": False, "reason": f"{type(e).__name__}: {e}",
                "mat": mat["material_id"], "cond": cond["condition_id"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--materials", type=int, default=60)
    ap.add_argument("--conditions", type=int, default=17)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--seed", type=int, default=20260820)
    ap.add_argument("--out", default="data/parametric")
    ap.add_argument("--holdout-materials", type=float, default=0.20)
    ap.add_argument("--holdout-conditions", type=float, default=0.15)
    ap.add_argument("--design", choices=["legacy", "v2"], default="legacy",
                    help="legacy reproduces the original 988-run dataset exactly "
                         "(uniform sampling, k_LDF sampled independently of d_p). "
                         "v2 uses scrambled Sobol and derives k_LDF from a sampled "
                         "d_p via Glueckauf — see the design note in this file.")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    if args.design == "v2":
        materials = sample_design(args.materials, MATERIAL_SPACE_V2,
                                  args.seed, "material_id")
        conditions = sample_design(args.conditions, CONDITION_SPACE,
                                   args.seed + 7, "condition_id")
        print(f"design v2: scrambled Sobol; k_LDF derived from d_p (Glueckauf)")
    else:
        materials = [sample_material(rng, i) for i in range(args.materials)]
        conditions = [sample_condition(rng, j) for j in range(args.conditions)]
    tasks = [(m, c) for m in materials for c in conditions]

    print(f"{len(materials)} materials x {len(conditions)} conditions = {len(tasks)} runs")
    print(f"store {STORE_NZ}x{STORE_NT} float32 -> {STORE_NZ * STORE_NT * 3 * 4 / 1e6:.2f} MB/sim, "
          f"{len(tasks) * STORE_NZ * STORE_NT * 3 * 4 / 1e9:.2f} GB total")
    print(f"workers={args.workers}")

    os.makedirs(args.out, exist_ok=True)
    t0 = time.time()
    kept, rejected = [], []

    # CHECKPOINT / RESUME.
    # A multi-hour generation that writes its manifest only on success loses
    # everything to a laptop lid. `_partial.json` is written periodically and
    # holds the per-sample metadata (t_final, exit_ratio, ...) that CANNOT be
    # recovered from the .npy files afterwards. `manifest.json` is still written
    # only on completion, because the train/novel splits are assigned from the
    # final kept set and a half-populated split would be silently wrong.
    part_path = os.path.join(args.out, "_partial.json")
    if os.path.exists(part_path):
        prev = json.load(open(part_path))
        if prev.get("seed") == args.seed and prev.get("store_nz") == STORE_NZ:
            kept = [r for r in prev["kept"]
                    if os.path.exists(os.path.join(
                        args.out, f"m{r['mat']:04d}_c{r['cond']:04d}.npy"))]
            rejected = prev.get("rejected", [])
            seen = {(r["mat"], r["cond"]) for r in kept} | \
                   {(r["mat"], r["cond"]) for r in rejected}
            before = len(tasks)
            tasks = [(m, c) for m, c in tasks
                     if (m["material_id"], c["condition_id"]) not in seen]
            print(f"RESUMING: {len(kept)} kept + {len(rejected)} rejected already on "
                  f"disk; {len(tasks)} of {before} runs remain")
        else:
            print(f"ignoring {part_path}: different seed or store resolution")

    def save_partial():
        tmp = part_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"seed": args.seed, "store_nz": STORE_NZ, "store_nt": STORE_NT,
                       "kept": kept, "rejected": rejected}, f)
        os.replace(tmp, part_path)          # atomic: never a half-written checkpoint

    # POOL RESILIENCE (2026-08-30). The previous 4080-run generation died with
    #
    #     OSError: [WinError 87] The parameter is incorrect
    #       File "multiprocessing/spawn.py", line 108, in spawn_main
    #         source_process = _winapi.OpenProcess(...)
    #
    # A worker could not open a handle to its parent. On Windows this happens
    # when a long-lived pool goes stale — a recycled handle, a sleep/resume, or a
    # worker dying and its replacement spawning against an invalid parent handle.
    # Submitting all ~4000 futures to ONE pool that must survive many hours makes
    # it near-certain, and it also pins every completed-but-unconsumed 0.79 MB
    # result in memory.
    #
    # The previous workaround was a bash loop that re-launched the whole process
    # and let the resume logic pick up. That works but discards the in-flight
    # chunk and needs a human to notice. Instead: run in CHUNKS, each with a
    # fresh pool, and catch a broken pool so the chunk is retried rather than
    # losing the run. The checkpoint means a retried chunk skips what is already
    # on disk.
    n_prev = len(kept) + len(rejected)
    total = n_prev + len(tasks)
    done = 0
    CHUNK = max(args.workers * 8, 32)

    def consume(r):
        nonlocal done
        done += 1
        if r["ok"]:
            np.save(os.path.join(args.out, f"m{r['mat']:04d}_c{r['cond']:04d}.npy"),
                    r.pop("fields"))
            kept.append(r)
        else:
            rejected.append(r)
        if done % CHECKPOINT_EVERY == 0:
            save_partial()
        if done % 25 == 0 or done == len(tasks):
            el = time.time() - t0
            print(f"  {n_prev + done}/{total}  kept={len(kept)} "
                  f"rejected={len(rejected)}  {el:.0f}s elapsed, "
                  f"{el / max(done, 1) * (len(tasks) - done):.0f}s left", flush=True)

    i = 0
    while i < len(tasks):
        chunk = tasks[i:i + CHUNK]
        for attempt in range(3):
            try:
                with ProcessPoolExecutor(max_workers=args.workers) as ex:
                    futs = [ex.submit(run_one, t) for t in chunk]
                    for fut in as_completed(futs):
                        consume(fut.result())
                break
            except Exception as e:                      # BrokenProcessPool, OSError, ...
                print(f"  ! pool failed on chunk {i}-{i+len(chunk)} "
                      f"({type(e).__name__}: {e}); attempt {attempt + 1}/3", flush=True)
                save_partial()
                already = {(r["mat"], r["cond"]) for r in kept} | \
                          {(r["mat"], r["cond"]) for r in rejected}
                chunk = [(m, c) for m, c in chunk
                         if (m["material_id"], c["condition_id"]) not in already]
                if not chunk:
                    break
                time.sleep(5)
        else:
            raise RuntimeError(f"chunk {i} failed three times; aborting rather than "
                               f"silently producing a partial dataset")
        i += CHUNK
        save_partial()
    save_partial()

    # splits — by material first, so novel-material is a real holdout
    mat_ids = sorted({k["mat"] for k in kept})
    rng2 = np.random.default_rng(args.seed + 1)
    rng2.shuffle(mat_ids)
    n_hold_m = max(1, int(args.holdout_materials * len(mat_ids)))
    novel_materials = set(mat_ids[:n_hold_m])
    train_materials = set(mat_ids[n_hold_m:])

    cond_ids = sorted({k["cond"] for k in kept})
    rng2.shuffle(cond_ids)
    n_hold_c = max(1, int(args.holdout_conditions * len(cond_ids)))
    novel_conditions = set(cond_ids[:n_hold_c])

    def split_of(r):
        if r["mat"] in novel_materials:
            return "novel_material"
        if r["cond"] in novel_conditions:
            return "novel_condition"
        return "train"

    for r in kept:
        r["split"] = split_of(r)

    counts = {s: sum(1 for r in kept if r["split"] == s) for s in
              ("train", "novel_condition", "novel_material")}
    reasons = {}
    for r in rejected:
        key = r["reason"].split("(")[0].strip()
        reasons[key] = reasons.get(key, 0) + 1

    manifest = {
        "seed": args.seed,
        "store_nz": STORE_NZ, "store_nt": STORE_NT, "solve_nz": SOLVE_NZ, "horizon": HORIZON,
        "design": args.design,
        "material_space": (MATERIAL_SPACE_V2 if args.design == "v2" else MATERIAL_SPACE),
        "condition_space": CONDITION_SPACE,
        # Frozen specs that were previously implicit in the code only (B29, B31).
        "b_H_ratio": B_H_RATIO,
        "kinetics": ("glueckauf: k_LDF = 15 eps_p (D_m/tau) / (R_p^2 rho_p K), "
                     "K = q*(c_in)/c_in" if args.design == "v2"
                     else "k_LDF sampled independently of d_p (legacy)"),
        "glueckauf": {"D_m": D_M_WATER, "tau": TORTUOSITY, "eps_p": EPS_PELLET},
        "materials": materials, "conditions": conditions,
        "samples": kept,
        "counts": counts,
        "n_rejected": len(rejected), "rejection_reasons": reasons,
        "novel_materials": sorted(novel_materials),
        "novel_conditions": sorted(novel_conditions),
        "elapsed_s": time.time() - t0,
    }
    with open(os.path.join(args.out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    if os.path.exists(part_path):
        os.remove(part_path)               # the real manifest supersedes the checkpoint

    print(f"\nkept {len(kept)}  rejected {len(rejected)}")
    print(f"  splits: " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    if reasons:
        print("  rejections:")
        for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
            print(f"    {v:5d}  {k}")
    print(f"wrote {args.out}/manifest.json  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
