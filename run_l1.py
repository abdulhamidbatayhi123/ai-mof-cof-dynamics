"""L1 — the data-driven interpolation rung.

Hypothesis under test: *"you just need more data."* If purely data-driven
regression on 691 training conditions already transfers to held-out materials,
nothing further up the ladder is needed and the project has no thesis.

Method
------
Fields are reduced by POD (proper orthogonal decomposition) fitted on the TRAIN
SPLIT ONLY, and regressors map the 11-dimensional parameter vector to the POD
coefficients. This is the standard reduced-order-model baseline and the one a
competent practitioner would reach for first, so it is the honest thing to
compare against.

It also buys a second result for free. **The POD singular-value spectrum IS an
empirical estimate of the Kolmogorov n-width** of the solution manifold. Any
method whose output is a linear combination of a fixed basis -- POD-plus-
regressor here, and DeepONet at rung L5 -- is bounded below by that decay. If it
is slow, no amount of branch/trunk capacity fixes it, and we will have measured
the obstruction rather than argued it.

Arms (matched: same POD rank, same inputs, same splits, same seeds)
    ridge         linear map, the floor
    rf            random forest
    xgb           gradient boosting
    mlp           multilayer perceptron

Usage
    python run_l1.py --modes 64 --seeds 42 43 44
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import time

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.compose import TransformedTargetRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

import ladder_data
from metrics import ArmResult, breakthrough_times, compare, format_comparison, per_variable_nrmse

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

CHANNELS = ("c", "q", "T")


def fit_pod(fields, train_idx, n_modes, verbose=True):
    """Per-channel POD fitted on the training split only.

    Fitting on all samples would leak held-out material structure into the basis
    every arm reconstructs through — a subtle but real contamination that would
    flatter every arm equally and make the novel-material split meaningless.
    """
    bases, means, spectra = {}, {}, {}
    n, _, nz, nt = fields.shape
    for i, ch in enumerate(CHANNELS):
        X = fields[train_idx, i].reshape(len(train_idx), -1).astype(np.float32)
        pca = PCA(n_components=n_modes, svd_solver="randomized", random_state=0)
        pca.fit(X)
        bases[ch] = pca
        means[ch] = pca.mean_
        spectra[ch] = pca.explained_variance_ratio_
        if verbose:
            ev = pca.explained_variance_ratio_
            print(f"  {ch}: {n_modes} modes capture {100 * ev.sum():.4f}% of variance | "
                  f"modes for 90/99/99.9%: "
                  f"{np.searchsorted(np.cumsum(ev), 0.90) + 1}/"
                  f"{np.searchsorted(np.cumsum(ev), 0.99) + 1}/"
                  f"{np.searchsorted(np.cumsum(ev), 0.999) + 1}")
        del X
        gc.collect()
    return bases, spectra


def project(fields, bases, batch=64):
    """Project every sample onto the POD bases -> (N, 3*n_modes)."""
    n = fields.shape[0]
    out = []
    for i, ch in enumerate(CHANNELS):
        coeffs = np.empty((n, bases[ch].n_components_), dtype=np.float32)
        for s in range(0, n, batch):
            e = min(s + batch, n)
            coeffs[s:e] = bases[ch].transform(fields[s:e, i].reshape(e - s, -1))
        out.append(coeffs)
        gc.collect()
    return np.concatenate(out, axis=1)


def reconstruct(coeffs, bases, shape):
    """(3*n_modes,) -> (3, nz, nt) for ONE sample. Kept per-sample for memory."""
    nz, nt = shape
    r = bases["c"].n_components_
    fields = np.empty((3, nz, nt), dtype=np.float32)
    for i, ch in enumerate(CHANNELS):
        c = coeffs[i * r:(i + 1) * r].reshape(1, -1)
        fields[i] = bases[ch].inverse_transform(c).reshape(nz, nt)
    return fields


def make_arm(name, seed):
    if name == "ridge":
        return Ridge(alpha=1.0)
    if name == "rf":
        return RandomForestRegressor(n_estimators=300, min_samples_leaf=2,
                                     random_state=seed, n_jobs=-1)
    if name == "xgb":
        return XGBRegressor(n_estimators=400, max_depth=5, learning_rate=0.06,
                            subsample=0.85, colsample_bytree=0.85,
                            random_state=seed, n_jobs=-1, verbosity=0,
                            multi_strategy="multi_output_tree", tree_method="hist")
    if name == "mlp":
        # Targets MUST be standardised. POD coefficients span 309x between mode 1
        # and mode 64, and MLPRegressor does not scale targets, so an unscaled fit
        # optimises the leading modes and ignores the rest -- it UNDERFITS (train
        # error equal to test error) and lands 2x worse than it should. Reporting
        # that would be a strawman, which protocol section 3 forbids: arms are
        # compared against the strongest configuration of the competitor.
        #   unscaled            novel_material = 0.1205
        #   standardised        novel_material = 0.0592   <- this one
        #   standardised, wider = 0.0701 (train 0.0095, overfits) -> keep early stopping
        return TransformedTargetRegressor(
            regressor=MLPRegressor(hidden_layer_sizes=(256, 256, 256), max_iter=3000,
                                   early_stopping=True, n_iter_no_change=30,
                                   random_state=seed, learning_rate_init=1e-3),
            transformer=StandardScaler(),
        )
    raise ValueError(name)


def evaluate(pred_coeffs, true_fields, bases, shape, t_final, batch=48):
    """Per-sample metrics from reconstructed fields.

    Reconstruction is BATCHED. Calling `inverse_transform` one sample at a time
    dominated the cost of every rung (~150 s per configuration); batching cuts it
    by roughly an order of magnitude at ~300 MB peak, which matters because L2
    alone runs 25 configurations x 3 seeds.
    """
    rows = []
    nz, nt = shape
    r = bases["c"].n_components_
    t_norm = np.linspace(0.0, 1.0, nt)
    n = pred_coeffs.shape[0]

    for s0 in range(0, n, batch):
        e = min(s0 + batch, n)
        recon = np.empty((e - s0, 3, nz, nt), dtype=np.float32)
        for i, ch in enumerate(CHANNELS):
            block = pred_coeffs[s0:e, i * r:(i + 1) * r]
            recon[:, i] = bases[ch].inverse_transform(block).reshape(-1, nz, nt)
        for k in range(e - s0):
            _row(recon[k], true_fields[s0 + k], t_norm, t_final[s0 + k], rows)
        del recon
        gc.collect()
    return rows


def _row(pf, tf, t_norm, tf_scalar, rows):
    if True:
        m = per_variable_nrmse(pf, tf)
        bt_p = breakthrough_times(pf[0, -1, :], t_norm)
        bt_t = breakthrough_times(tf[0, -1, :], t_norm)
        for lev in (0.05, 0.50, 0.95):
            a, b = bt_p[lev], bt_t[lev]
            m[f"dt_bt{int(lev * 100):02d}"] = (
                abs(a - b) * tf_scalar if np.isfinite(a) and np.isfinite(b) else np.nan
            )
        m["dT_peak"] = float(abs(pf[2].max() - tf[2].max()))
        rows.append(m)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modes", type=int, default=64)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--arms", nargs="+", default=["ridge", "rf", "xgb", "mlp"])
    ap.add_argument("--out", default="results/l1_results.json")
    args = ap.parse_args()

    t0 = time.time()
    d = ladder_data.load()
    shape = d.fields.shape[2:]
    tr = d.idx("train")

    print(f"\nPOD (fitted on {len(tr)} training samples only), {args.modes} modes/channel:")
    bases, spectra = fit_pod(d.fields, tr, args.modes)

    print("\nprojecting all samples...")
    coeffs = project(d.fields, bases)
    print(f"  coefficients {coeffs.shape}")

    # POD reconstruction floor: the best ANY linear-basis method can do
    print("\nPOD reconstruction floor (perfect coefficient prediction):")
    floor = {}
    for split in ladder_data.SPLITS:
        idx = d.idx(split)
        rows = evaluate(coeffs[idx], d.fields[idx], bases, shape, d.t_final[idx])
        floor[split] = {k: float(np.nanmean([r[k] for r in rows])) for k in rows[0]}
        print(f"  {split:<16} nRMSE c={floor[split]['c']:.4e} q={floor[split]['q']:.4e} T={floor[split]['T']:.4e}")

    arms = [a for a in args.arms if a != "xgb" or HAS_XGB]
    results = {"modes": args.modes, "seeds": args.seeds, "pod_floor": floor,
               "spectrum": {c: spectra[c].tolist() for c in CHANNELS},
               "splits": d.summary(), "arms": {}}

    for arm in arms:
        results["arms"][arm] = {}
        for seed in args.seeds:
            t1 = time.time()
            model = make_arm(arm, seed)
            model.fit(d.params_z[tr], coeffs[tr])
            per_split = {}
            for split in ladder_data.SPLITS:
                idx = d.idx(split)
                pred = model.predict(d.params_z[idx])
                rows = evaluate(pred, d.fields[idx], bases, shape, d.t_final[idx])
                per_split[split] = {
                    "mean": {k: float(np.nanmean([r[k] for r in rows])) for k in rows[0]},
                    "per_sample_nrmse_c": [float(r["c"]) for r in rows],
                    "material_ids": d.material_ids[idx].tolist(),
                }
            results["arms"][arm][str(seed)] = per_split
            nm = per_split["novel_material"]["mean"]
            print(f"  {arm:<6} seed {seed}: novel-material nRMSE "
                  f"c={nm['c']:.4f} q={nm['q']:.4f} T={nm['T']:.4f}  "
                  f"dt_bt50={nm['dt_bt50'] / 3600:.2f}h  [{time.time() - t1:.0f}s]", flush=True)
            del model
            gc.collect()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nwrote {args.out}  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
