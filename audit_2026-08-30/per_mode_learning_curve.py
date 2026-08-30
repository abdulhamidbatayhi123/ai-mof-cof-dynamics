"""Is the params->coefficient ceiling FUNDAMENTAL or UNDER-SAMPLED?

l5_bottleneck measured per-mode R^2 at ONE training-set size (48 materials) and
concluded the map carries ~4-5 modes' worth of information. That is a claim about
the MAP. But an under-sampled map looks identical. Measure per-mode R^2 as a
function of the number of TRAINING MATERIALS: if R^2 for mode k is still climbing
at 48 materials, the ceiling is sample size, not the map.
"""
import sys, json, time
sys.path.insert(0, r"C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics")
import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor
from comoving import load_c_light, nrmse

t0 = time.time()
X, Pz, mat, split = load_c_light()
tr_all = np.where(split == "train")[0]
nm = np.where(split == "novel_material")[0]
mats_tr = np.unique(mat[tr_all])
print(f"train {len(tr_all)} conds / {len(mats_tr)} materials;  novel-material {len(nm)} conds")

P_MODES = 32
FRACS = [(12, 0.25), (24, 0.50), (36, 0.75), (48, 1.00)]
SEEDS = (42, 43, 44)
MODES_REPORT = [0, 1, 2, 3, 4, 7, 11, 15, 23, 31]

out = {}
for n_mat, frac in FRACS:
    r2_acc = np.zeros(P_MODES); fld = []
    for sd in SEEDS:
        rng = np.random.default_rng(sd)
        keep = set(rng.choice(mats_tr, size=n_mat, replace=False).tolist())
        sub = np.array([i for i in tr_all if mat[i] in keep])
        flat = X.reshape(len(X), -1)
        # POD on this subset only - no leakage
        pca = PCA(n_components=P_MODES, svd_solver="randomized", random_state=0).fit(flat[sub])
        A = pca.transform(flat)
        mu, s = A[sub].mean(0), A[sub].std(0); s[s == 0] = 1
        Az = (A - mu) / s
        Pr = np.empty_like(Az)
        for k in range(P_MODES):
            m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                              early_stopping=True, random_state=0)
            m.fit(Pz[sub], Az[sub, k]); Pr[:, k] = m.predict(Pz)
        for k in range(P_MODES):
            y, p = Az[nm, k], Pr[nm, k]
            r2_acc[k] += 1.0 - ((p - y) ** 2).sum() / max(((y - y.mean()) ** 2).sum(), 1e-30)
        rec = pca.inverse_transform(Pr * s + mu).reshape(X.shape)
        fld.append(nrmse(rec[nm], X[nm]))
    r2 = r2_acc / len(SEEDS)
    out[n_mat] = {"r2": r2.tolist(), "field_nrmse": float(np.mean(fld))}
    print(f"\n  n_materials = {n_mat:3d}   field nRMSE {np.mean(fld):.5f}   [{time.time()-t0:.0f}s]")
    print("    mode : " + " ".join(f"{k+1:>6d}" for k in MODES_REPORT))
    print("    R^2  : " + " ".join(f"{r2[k]:+6.3f}" for k in MODES_REPORT))
    print(f"    modes with R^2>0.5: {(r2>0.5).sum()}   >0.2: {(r2>0.2).sum()}   >0: {(r2>0).sum()}")

print("\n" + "="*78)
print("TREND PER MODE  (is R^2 still climbing at 48 materials?)")
print("  mode   12mat   24mat   36mat   48mat    delta(36->48)   verdict")
for k in MODES_REPORT:
    v = [out[n]["r2"][k] for n, _ in FRACS]
    d = v[3] - v[2]
    verdict = "STILL CLIMBING" if d > 0.02 else ("saturated" if abs(d) <= 0.02 else "degrading")
    print(f"  {k+1:4d}  {v[0]:+6.3f}  {v[1]:+6.3f}  {v[2]:+6.3f}  {v[3]:+6.3f}    {d:+.3f}      {verdict}")
n_climb = sum(1 for k in range(P_MODES)
              if out[48]["r2"][k] - out[36]["r2"][k] > 0.02)
print(f"\n  {n_climb} of {P_MODES} modes still climbing from 36 -> 48 materials")
json.dump(out, open(r"C:/Users/ABDULH~1/AppData/Local/Temp/claude/C--Users-abdulhamid-batayhi-Desktop-ai-mof-cof-dynamics/ae00ee7f-983e-4ff8-9a1d-62245728403c/scratchpad/per_mode_lc.json","w"))
print(f"\ndone [{time.time()-t0:.0f}s]")
