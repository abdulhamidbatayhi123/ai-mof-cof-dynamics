"""Does a co-moving frame fix the coefficient map? A cheap, decisive test.

L5 measured the obstruction: the params -> POD-coefficient map carries about five
modes' worth of generalisable information out of 128, so every linear-
reconstruction method is stuck near 0.051 (POD + strong regressor) or 0.028
(DeepONet) regardless of basis size. The n-width bound is real and 59x below.

The standard diagnosis for that failure is TRANSPORT: a travelling front at a
sample-dependent position is not low-rank in a fixed basis, and its coefficients
depend on front location in a wildly oscillatory way. The standard fix is to
factor the position out before projecting.

The warp is defined per axial position rather than per time, because for a
breakthrough column c(z, .) is monotone in t at fixed z, so the local arrival time
is unique and cheap:

    t_L(z) = the time at which c(z, t) crosses level L    (linear interpolation)
    warped field  C(z, tau) = c(z, t_L(z) + tau)

For a pure travelling wave C is independent of z and the warped field is rank 1.
This system has TWO waves — a fast Henry wave and a slow cooperative shock (§6c) —
which one warp cannot align simultaneously, so the measurement is genuinely open.

The idea is given its strongest form before any conclusion is drawn, because
comparing against a weak version of a competitor is how retractions A2/A19/A20 and
defects B14/B22 were generated:

  * the interpolation floor is measured and driven down until it cannot
    contaminate the result (a lossy warp would manufacture the negative);
  * the shape basis is SWEPT, not fixed, exactly as L5 swept p;
  * the alignment level is SWEPT, since which wave you align on is a free choice;
  * the two-wave gap is MEASURED rather than invoked as an explanation.

Everything is computed at L5's frozen 128x128 encoding and scored with L5's
normalisation, so the comparison is within-rung and legitimate.

Output: results/comoving.json
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor

import ladder_data

NZ_S, NT_S = 128, 128          # identical to run_l5.subsample()
N_TAU = 512                    # 2x the source resolution, to keep the warp lossless
TAU_MAX = 1.0                  # normalised time; covers every reachable shift
LEVELS = (0.1, 0.5, 0.9)       # which wave to align on — swept, not assumed
PS = (8, 16, 32, 64, 128)      # shape basis size — swept, as L5 swept p
P_WARP = 8                     # modes for the smooth monotone curve t_L(z)
L5_FIXED_FRAME = 0.0510        # POD + strongest regressor, same encoding (l5_bottleneck)


def load_c_light(root="data/parametric"):
    """Channel c only, subsampled to (NZ_S, NT_S), via mmap."""
    man = json.load(open(os.path.join(root, "manifest.json")))
    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    rows, flds = [], []
    zi = ti = None
    for s in man["samples"]:
        f = os.path.join(root, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")
        if not os.path.exists(f):
            continue
        arr = np.load(f, mmap_mode="r")
        if zi is None:
            zi = np.linspace(0, arr.shape[1] - 1, NZ_S).astype(int)
            ti = np.linspace(0, arr.shape[2] - 1, NT_S).astype(int)
        flds.append(np.array(arr[0][np.ix_(zi, ti)], dtype=np.float32))
        m, c = mats[s["mat"]], conds[s["cond"]]
        rows.append(([(m if k in m else c)[k] for k in ladder_data.param_keys_for(man)],
                     s["mat"], s["split"]))
    params = np.array([r[0] for r in rows], dtype=np.float64)
    mat = np.array([r[1] for r in rows])
    split = np.array([r[2] for r in rows])
    tr = split == "train"
    mu, sd = params[tr].mean(0), params[tr].std(0)
    sd[sd == 0] = 1.0
    X = np.stack(flds)
    print(f"loaded c-channel {X.shape}  ({X.nbytes / 1e6:.0f} MB)")
    return X, (params - mu) / sd, mat, split


def arrival_time(X, u, level):
    """t_L(z) per sample: first upward crossing of `level`, linearly interpolated."""
    N, NZ, NT = X.shape
    tb = np.empty((N, NZ))
    above = X >= level
    first = np.argmax(above, axis=2)
    never = ~above.any(axis=2)
    n_bad = 0
    for n in range(N):
        for z in range(NZ):
            if never[n, z]:
                tb[n, z] = u[-1]
                n_bad += 1
                continue
            k = first[n, z]
            if k == 0:
                tb[n, z] = u[0]
                continue
            c0, c1 = X[n, z, k - 1], X[n, z, k]
            w = 0.0 if c1 == c0 else (level - c0) / (c1 - c0)
            tb[n, z] = u[k - 1] + w * (u[k] - u[k - 1])
    return tb, n_bad


def warp(X, u, tb, tau):
    """C(z, tau) = c(z, t_L(z) + tau), clamped at the ends (physically 0 / 1)."""
    N, NZ, _ = X.shape
    W = np.empty((N, NZ, len(tau)), dtype=np.float32)
    for n in range(N):
        for z in range(NZ):
            W[n, z] = np.interp(tb[n, z] + tau, u, X[n, z])
    return W


def unwarp(W, u, tb, tau):
    """Inverse: c(z, t) = C(z, t - t_L(z))."""
    N, NZ, _ = W.shape
    Y = np.empty((N, NZ, len(u)), dtype=np.float32)
    for n in range(N):
        for z in range(NZ):
            Y[n, z] = np.interp(u - tb[n, z], tau, W[n, z])
    return Y


def nrmse(rec, true):
    """L5's normalisation exactly: per-sample range over the FULL field."""
    a = rec.reshape(rec.shape[0], -1)
    b = true.reshape(true.shape[0], -1)
    rng = b.max(1) - b.min(1)
    return np.sqrt(((a - b) ** 2).mean(1)) / np.maximum(rng, 1e-12)


def pca_regress(Pz, Y, tr, n_comp):
    """PCA-compress, regress coefficients from params. Returns (oracle, predicted)."""
    flat = Y.reshape(Y.shape[0], -1)
    pca = PCA(n_components=n_comp, svd_solver="randomized", random_state=0).fit(flat[tr])
    A = pca.transform(flat)
    amu, asd = A[tr].mean(0), A[tr].std(0)
    asd[asd == 0] = 1.0
    Az = (A - amu) / asd                                  # standardise (defect B14)
    P = np.empty_like(Az)
    for k in range(n_comp):
        m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                          early_stopping=True, random_state=0)
        m.fit(Pz[tr], Az[tr, k])
        P[:, k] = m.predict(Pz)
    return (pca.inverse_transform(A * asd + amu).reshape(Y.shape),
            pca.inverse_transform(P * asd + amu).reshape(Y.shape))


def spectrum(F, tr):
    flat = F.reshape(F.shape[0], -1)
    pca = PCA(n_components=128, svd_solver="randomized", random_state=0).fit(flat[tr])
    cum = np.cumsum(pca.explained_variance_ratio_)
    return {str(q): int(np.searchsorted(cum, q) + 1) for q in (0.9, 0.99, 0.999, 0.9999)}


def main():
    t0 = time.time()
    X, Pz, mat, split = load_c_light()
    tr = np.where(split == "train")[0]
    nm = np.where(split == "novel_material")[0]
    N, NZ, NT = X.shape
    u = np.linspace(0.0, 1.0, NT)
    tau = np.linspace(-TAU_MAX, TAU_MAX, N_TAU)

    out = {"nz_s": NZ_S, "nt_s": NT_S, "n_tau": N_TAU, "levels": list(LEVELS),
           "ps": list(PS), "p_warp": P_WARP,
           "l5_fixed_frame_reference": L5_FIXED_FRAME,
           "material_ids_novel": mat[nm].tolist(), "levels_detail": {}}

    # ── is one warp even capable of aligning this system? ────────────────────
    print("\n1. THE TWO-WAVE GAP — measured, not invoked")
    out_z = NZ - 1
    t10, _ = arrival_time(X, u, 0.1)
    t50, _ = arrival_time(X, u, 0.5)
    t90, _ = arrival_time(X, u, 0.9)
    gap = t90[:, out_z] - t10[:, out_z]
    print(f"   at the outlet, t(0.9) - t(0.1) spans "
          f"[{gap.min():.3f}, {gap.max():.3f}] normalised time, "
          f"median {np.median(gap):.3f}")
    print(f"   relative spread across samples: {gap.std() / max(gap.mean(), 1e-12):.2f}")
    print("   A single-level warp aligns ONE level exactly; the others move by this"
          " much.")
    out["two_wave_gap"] = {"min": float(gap.min()), "max": float(gap.max()),
                           "median": float(np.median(gap)), "mean": float(gap.mean()),
                           "std": float(gap.std())}

    print(f"\n2. n-width, original frame:  "
          f"{spectrum(X, tr)}")
    out["spectrum_original"] = spectrum(X, tr)

    best = None
    for level in LEVELS:
        print(f"\n{'=' * 74}\n3. ALIGNMENT LEVEL c = {level}\n{'=' * 74}")
        tb, n_bad = arrival_time(X, u, level)
        W = warp(X, u, tb, tau)

        rt = nrmse(unwarp(W, u, tb, tau), X)[nm].mean()
        print(f"   interpolation floor (oracle warp + oracle shape): {rt:.6f}")
        if rt > 0.1 * L5_FIXED_FRAME:
            print("   WARNING: floor is >10 % of the reference — result contaminated")
        sp = spectrum(W, tr)
        print(f"   n-width in this frame: {sp}   (original: {out['spectrum_original']})")

        _, tb_pred = pca_regress(Pz, tb[:, :, None], tr, P_WARP)
        tb_pred = tb_pred[:, :, 0]
        r2 = float(1.0 - ((tb_pred[nm] - tb[nm]) ** 2).sum()
                   / max(((tb[nm] - tb[nm].mean()) ** 2).sum(), 1e-30))
        print(f"   R² of the warp t_L(z) on novel materials: {r2:+.3f}")

        rows = []
        print(f"   {'p':>5} {'oracle warp':>13} {'pred warp':>11}   (novel materials)")
        for p in PS:
            shp_o, shp_p = pca_regress(Pz, W, tr, p)
            e_ow = nrmse(unwarp(shp_p, u, tb, tau), X)[nm]
            e_pw = nrmse(unwarp(shp_p, u, tb_pred, tau), X)[nm]
            rows.append({"p": p, "oracle_warp_pred_shape": float(e_ow.mean()),
                         "pred_warp_pred_shape": float(e_pw.mean()),
                         "per_sample_novel": [float(v) for v in e_pw]})
            print(f"   {p:>5} {e_ow.mean():>13.5f} {e_pw.mean():>11.5f}")
            if best is None or e_pw.mean() < best[0]:
                best = (float(e_pw.mean()), level, p)

        out["levels_detail"][str(level)] = {
            "interp_floor": float(rt), "n_never_crossed": int(n_bad),
            "spectrum": sp, "warp_r2_novel": r2, "rows": rows}

    print(f"\n{'=' * 74}\n4. VERDICT\n{'=' * 74}")
    print(f"   best co-moving anywhere: {best[0]:.4f}  (level {best[1]}, p = {best[2]})")
    print(f"   L5 fixed frame, same encoding, same regressor: {L5_FIXED_FRAME:.4f}")
    ratio = L5_FIXED_FRAME / best[0]
    print(f"   co-moving is {ratio:.2f}x the fixed frame — "
          f"{'BETTER' if ratio > 1 else 'WORSE OR EQUAL'}")
    out["best"] = {"nrmse": best[0], "level": best[1], "p": best[2],
                   "ratio_vs_fixed_frame": ratio}

    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/comoving.json", "w"), indent=2)
    print(f"\nwrote results/comoving.json  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
