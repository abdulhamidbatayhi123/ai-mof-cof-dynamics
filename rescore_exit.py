"""Re-score the best LEARNED arm on the exit curve, so L7's comparison is like-for-like.

L7's classical forms predict the exit breakthrough curve only. L1-L3 report full-
field nRMSE. Comparing 0.0485 (field) against 0.2307 (curve) would be meaningless
- the field metric averages over a mostly-smooth domain while the curve metric
concentrates on the hardest part of the solution.
"""
import gc, json
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import ladder_data
from run_l1 import fit_pod, project, CHANNELS
from metrics import breakthrough_times

d = ladder_data.load(verbose=False)
nz, nt = d.fields.shape[2:]
tr = d.idx("train")
bases, _ = fit_pod(d.fields, tr, 64, verbose=False)
C = project(d.fields, bases); gc.collect()
t_norm = np.linspace(0.0, 1.0, nt)
R = 64

def exit_scores(pred_coeffs, idx):
    out = []
    for k, gi in enumerate(idx):
        rec = bases["c"].inverse_transform(pred_coeffs[k, :R].reshape(1, -1)).reshape(nz, nt)
        pe, te = rec[-1, :], d.fields[gi, 0, -1, :]
        rng = te.max() - te.min()
        m = {"nrmse": float(np.sqrt(np.mean((pe - te) ** 2)) / (rng if rng > 0 else 1.0))}
        bp, bt = breakthrough_times(pe, t_norm), breakthrough_times(te, t_norm)
        a, b = bp[0.50], bt[0.50]
        m["dt50"] = abs(a - b) * d.t_final[gi] if np.isfinite(a) and np.isfinite(b) else np.nan
        out.append(m)
    return out

res = {}
print(f"{'arm':<24} {'split':<17} {'exit nRMSE':>12} {'dt50 (h)':>10}")
print("-" * 68)

# POD floor on the exit curve
for split in ladder_data.SPLITS:
    idx = d.idx(split)
    rows = exit_scores(C[idx], idx)
    res.setdefault("pod_floor", {})[split] = {
        "nrmse": float(np.nanmean([r["nrmse"] for r in rows])),
        "dt50": float(np.nanmean([r["dt50"] for r in rows]))}
    print(f"{'POD floor':<24} {split:<17} {res['pod_floor'][split]['nrmse']:>12.4f} "
          f"{res['pod_floor'][split]['dt50']/3600:>10.2f}")

for seed in (42, 43, 44):
    m = RandomForestRegressor(n_estimators=300, min_samples_leaf=1, random_state=seed, n_jobs=-1)
    m.fit(d.params_z[tr], C[tr])
    for split in ladder_data.SPLITS:
        idx = d.idx(split)
        rows = exit_scores(m.predict(d.params_z[idx]), idx)
        key = f"rf_seed{seed}"
        res.setdefault(key, {})[split] = {
            "nrmse": float(np.nanmean([r["nrmse"] for r in rows])),
            "dt50": float(np.nanmean([r["dt50"] for r in rows])),
            "per_sample_nrmse": [float(r["nrmse"]) for r in rows],
            "material_ids": d.material_ids[idx].tolist()}
    nm = res[f"rf_seed{seed}"]["novel_material"]
    print(f"{'rf (best L1/L2 arm)':<24} {'novel_material':<17} {nm['nrmse']:>12.4f} {nm['dt50']/3600:>10.2f}  seed {seed}")
    del m; gc.collect()

json.dump(res, open("results/exit_curve_rescore.json", "w"), indent=2)
nv = [res[f"rf_seed{s}"]["novel_material"]["nrmse"] for s in (42,43,44)]
print(f"\nrf novel-material exit nRMSE: {np.mean(nv):.4f} +- {np.std(nv):.4f}")
print("wrote results/exit_curve_rescore.json")
