"""Audit L1 before building L2 on it. Three ways L1's conclusion could be wrong.

L1 concluded: "arms sit 33x above the POD floor, so the failure is a LEARNING
failure, not a representation failure — therefore test capacity next (L2)."

That conclusion is load-bearing. If it is wrong, L2 is the wrong experiment and
several weeks go into the wrong rung. Three independent ways it could be wrong:

  A. RANK SENSITIVITY. The 33x gap was measured at 64 POD modes, a number chosen
     without justification. If arm error falls as rank rises, the basis WAS
     partly binding and the diagnosis is wrong. If arm error is flat in rank,
     the regression is confirmed as the bottleneck.

  B. BOOTSTRAP CALIBRATION AT 12 CLUSTERS. Cluster-robust CIs were validated
     earlier at 20 materials. The novel-material split has only 12. Cluster
     bootstrap is known to under-cover with few clusters, so the "xgb and rf
     tie" verdict may rest on a CI that is too narrow to trust.

  C. SPLIT SENSITIVITY. Every number rests on ONE realisation of which 12
     materials were held out (seed 20260820). If a different holdout set gives a
     materially different answer, no single-split conclusion is safe.

Usage:  python audit_l1.py [--part A|B|C]
"""
from __future__ import annotations

import argparse
import gc
import json
import time

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor

import ladder_data
from metrics import ArmResult, compare

CH = ("c", "q", "T")


def _pod_and_scores(d, train_idx, eval_idx, n_modes, seed=42, arm="rf"):
    """Fit POD on train_idx, regress params->coeffs, return (floor, arm) nRMSE on c."""
    bases, coeffs = {}, []
    for i, ch in enumerate(CH):
        X = d.fields[train_idx, i].reshape(len(train_idx), -1).astype(np.float32)
        p = PCA(n_components=n_modes, svd_solver="randomized", random_state=0).fit(X)
        bases[ch] = p
        allc = np.empty((len(d.fields), n_modes), np.float32)
        for s in range(0, len(d.fields), 64):
            e = min(s + 64, len(d.fields))
            allc[s:e] = p.transform(d.fields[s:e, i].reshape(e - s, -1))
        coeffs.append(allc)
        del X
        gc.collect()
    C = np.concatenate(coeffs, 1)

    model = RandomForestRegressor(n_estimators=300, min_samples_leaf=2,
                                  random_state=seed, n_jobs=-1)
    model.fit(d.params_z[train_idx], C[train_idx])
    P = model.predict(d.params_z[eval_idx])

    nz, nt = d.fields.shape[2:]
    floor_e, arm_e = [], []
    for k, gi in enumerate(eval_idx):
        true_c = d.fields[gi, 0]
        rng = true_c.max() - true_c.min()
        rec_f = bases["c"].inverse_transform(C[gi, :n_modes].reshape(1, -1)).reshape(nz, nt)
        rec_a = bases["c"].inverse_transform(P[k, :n_modes].reshape(1, -1)).reshape(nz, nt)
        floor_e.append(np.sqrt(np.mean((rec_f - true_c) ** 2)) / rng)
        arm_e.append(np.sqrt(np.mean((rec_a - true_c) ** 2)) / rng)
    del C, coeffs, model
    gc.collect()
    return np.array(floor_e), np.array(arm_e)


def part_A(d):
    print("=" * 78)
    print("A. RANK SENSITIVITY — is 64 modes hiding a representation limit?")
    print("=" * 78)
    tr, nm = d.idx("train"), d.idx("novel_material")
    print(f"  {'modes':>6} {'POD floor':>12} {'rf novel-mat':>14} {'ratio':>8}")
    print("  " + "-" * 44)
    out = {}
    for r in (8, 16, 32, 64, 128):
        t0 = time.time()
        f, a = _pod_and_scores(d, tr, nm, r)
        out[r] = {"floor": float(f.mean()), "arm": float(a.mean())}
        print(f"  {r:>6} {f.mean():>12.4e} {a.mean():>14.4f} {a.mean() / f.mean():>7.1f}x"
              f"   [{time.time() - t0:.0f}s]", flush=True)
    fl = [out[r]["floor"] for r in out]
    ar = [out[r]["arm"] for r in out]
    print()
    print(f"  POD floor falls {fl[0] / fl[-1]:.1f}x from 8 to 128 modes (basis improves a lot)")
    print(f"  arm error falls {ar[0] / ar[-1]:.2f}x over the same range")
    if ar[0] / ar[-1] < 1.3:
        print("  => arm error is FLAT in rank. The basis is not the constraint.")
        print("     L1's diagnosis holds: it is a learning failure. L2 is the right next rung.")
    else:
        print("  => arm error improves with rank. The basis WAS partly binding;")
        print("     L1's diagnosis is wrong and L2 is the wrong experiment.")
    return out


def part_B(d):
    print("=" * 78)
    print("B. BOOTSTRAP CALIBRATION AT 12 CLUSTERS — are the L1 CIs trustworthy?")
    print("=" * 78)
    print("  Realistic null: two arms tie on average, per-material advantages differ.")
    print("  Any 'significant' verdict is a false positive. Nominal rate 5 %.\n")
    print(f"  {'n materials':>12} {'conditions each':>16} {'false-positive rate':>21}")
    print("  " + "-" * 52)
    res = {}
    for n_mat, n_cond in ((12, 17), (20, 5), (30, 5), (60, 17)):
        fp = 0
        TRIALS = 300
        for s in range(TRIALS):
            rng = np.random.default_rng(7000 + s)
            mats = np.repeat(np.arange(n_mat), n_cond)
            adv = rng.normal(0, 0.02, n_mat)[mats]
            A = 0.05 + rng.normal(0, 0.003, mats.size)
            B = 0.05 + adv + rng.normal(0, 0.003, mats.size)
            r = compare(ArmResult("A", mats, A), ArmResult("B", mats, B), n_boot=600, seed=s)
            fp += r["significant"]
        res[n_mat] = 100 * fp / TRIALS
        flag = "  <-- L1 novel-material split" if n_mat == 12 else ""
        print(f"  {n_mat:>12} {n_cond:>16} {res[n_mat]:>20.1f} %{flag}")
    print()
    if res[12] > 12:
        print(f"  => at 12 clusters the test over-rejects ({res[12]:.1f} % vs 5 % nominal).")
        print("     'xgb and rf tie' is SAFE (a null verdict from an over-rejecting test")
        print("     is conservative), but any POSITIVE claim on this split needs widening.")
    else:
        print(f"  => 12 clusters is adequately calibrated ({res[12]:.1f} %).")
    return res


def part_C(d, n_repeats=5):
    print("=" * 78)
    print("C. SPLIT SENSITIVITY — does the answer depend on WHICH materials are held out?")
    print("=" * 78)
    all_mats = np.unique(d.material_ids)
    n_hold = 12
    print(f"  {'repeat':>7} {'held-out materials':>22} {'POD floor':>11} {'rf error':>10} {'ratio':>7}")
    print("  " + "-" * 62)
    ratios, arms = [], []
    for rep in range(n_repeats):
        rng = np.random.default_rng(9000 + rep)
        hold = set(rng.choice(all_mats, n_hold, replace=False).tolist())
        tr = np.array([i for i, m in enumerate(d.material_ids) if m not in hold])
        nm = np.array([i for i, m in enumerate(d.material_ids) if m in hold])
        f, a = _pod_and_scores(d, tr, nm, 64)
        ratios.append(a.mean() / f.mean())
        arms.append(a.mean())
        print(f"  {rep:>7} {str(sorted(hold)[:4])[:-1] + ', ...]':>22} "
              f"{f.mean():>11.3e} {a.mean():>10.4f} {ratios[-1]:>6.1f}x", flush=True)
    print()
    print(f"  rf novel-material error across splits: {np.mean(arms):.4f} +- {np.std(arms):.4f}"
          f"  (min {min(arms):.4f}, max {max(arms):.4f})")
    print(f"  gap above floor:                       {np.mean(ratios):.1f}x +- {np.std(ratios):.1f}x")
    if np.std(arms) / np.mean(arms) < 0.25 and min(ratios) > 5:
        print("  => the conclusion is stable across holdout sets. L1 is not a fluke of one split.")
    else:
        print("  => the conclusion MOVES with the split. Single-split numbers are unsafe;")
        print("     L1 must be re-reported as a mean over repeated splits.")
    return {"arms": arms, "ratios": ratios}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["A", "B", "C"], nargs="*", default=["A", "B", "C"])
    a = ap.parse_args()
    d = ladder_data.load(verbose=False)
    print(f"988 samples, {len(np.unique(d.material_ids))} materials, "
          f"novel-material split holds out {len(np.unique(d.material_ids[d.split == 'novel_material']))}\n")
    out = {}
    if "A" in a.part:
        out["rank_sensitivity"] = part_A(d); print()
    if "B" in a.part:
        out["bootstrap_calibration"] = part_B(d); print()
    if "C" in a.part:
        out["split_sensitivity"] = part_C(d); print()
    json.dump(out, open("results/l1_audit.json", "w"), indent=2, default=float)
    print("wrote results/l1_audit.json")
