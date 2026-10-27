"""Owner of results/workflow_example_v3.json: the worked example in Figure 1 (B-E).

Figure 1 shows the study's question on one real held-out field of the MOF-like design (v3):
a reduced-basis surrogate writes the field as a weighted sum of basis modes; with the best
coefficients the error is the basis floor, with predicted coefficients it is the floor plus
the map error. Recorded here, nothing drawn:

  - one held-out concentration field (c/c_in, 128 x 128, stored solver output);
  - the first three POD modes of the training fields;
  - that field rebuilt from P = 16 modes with its best (projected) coefficients, and with
    the coefficients gradient boosting predicts from the material's parameters;
  - each rebuild's nRMSE, and both errors averaged over every held-out sample of the fold.

Settings are those of the POD + boosting arm (dd_screening_frameworks.fit_hgb: randomized
PCA with random_state 0, standardised coefficients, HistGradientBoostingRegressor with 400
iterations, learning rate 0.06, early stopping, seed 42), the v3 five-fold map, fold 0 held
out, inputs standardised on the training folds. Selection rule (fixed here, not by eye): the
held-out sample whose predicted-coefficient error is the MEDIAN of the fold, a typical case.

    python workflow_example.py
"""
import json
import os

os.environ.setdefault("ADS_DATA_ROOT", "data/parametric_v3")     # before v2_common is imported
os.environ.setdefault("ADS_FOLDS_FILE", "results/v3_folds.json")

import numpy as np  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.ensemble import HistGradientBoostingRegressor  # noqa: E402

import ladder_data  # noqa: E402
from v2_common import FIELD_RES, ROOT_V2, load_folds, standardise_params, write_atomic  # noqa: E402

OUT = "results/workflow_example_v3.json"
P, FOLD, SEED = 16, 0, 42
DRAW = 64          # fields and modes are recorded at 64 x 64 for drawing


def down(a):
    s = a.shape[-1] // DRAW
    return a.reshape(DRAW, s, DRAW, s).mean((1, 3))


def nrmse(pred, truth):
    rng = truth.max(1) - truth.min(1)
    return np.sqrt(((pred - truth) ** 2).mean(1)) / np.maximum(rng, 1e-12)


def main():
    assert ROOT_V2.endswith("parametric_v3"), ROOT_V2
    d = ladder_data.load(ROOT_V2, field_res=FIELD_RES)
    fold_of, _, _ = load_folds(d.material_ids)
    tr, te = np.where(fold_of != FOLD)[0], np.where(fold_of == FOLD)[0]
    assert not set(d.material_ids[tr]) & set(d.material_ids[te])
    X = d.fields[:, 0].reshape(len(d.fields), -1)
    Pz = standardise_params(d.params, tr)

    pca = PCA(n_components=P, svd_solver="randomized", random_state=0).fit(X[tr])
    A = pca.transform(X[tr])
    amu, asd = A.mean(0), A.std(0)
    asd[asd == 0] = 1.0
    Azp = np.stack([HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06, early_stopping=True,
                                                  random_state=SEED).fit(Pz[tr], ((A - amu) / asd)[:, k])
                    .predict(Pz[te]) for k in range(P)], 1)
    rec_best = pca.inverse_transform(pca.transform(X[te]))       # best coefficients: the basis floor
    rec_pred = pca.inverse_transform(Azp * asd + amu)            # predicted coefficients
    e_best, e_pred = nrmse(rec_best, X[te]), nrmse(rec_pred, X[te])

    j = int(np.argsort(e_pred)[len(te) // 2])                    # the median held-out case
    i = int(te[j])
    shape = (FIELD_RES, FIELD_RES)
    out = {
        "_what": __doc__.splitlines()[0],
        "design": "v3", "P": P, "fold": FOLD, "n_heldout_samples": int(len(te)),
        "sample_index": i, "material_id": int(d.material_ids[i]), "condition_id": int(d.condition_ids[i]),
        "modes": [down(pca.components_[k].reshape(shape)).tolist() for k in range(3)],
        "field": down(X[i].reshape(shape)).tolist(),
        "rebuilt_best": down(rec_best[j].reshape(shape)).tolist(),
        "rebuilt_predicted": down(rec_pred[j].reshape(shape)).tolist(),
        "nrmse_best": float(e_best[j]), "nrmse_predicted": float(e_pred[j]),
        "fold_mean_nrmse_best": float(e_best.mean()), "fold_mean_nrmse_predicted": float(e_pred.mean()),
    }
    write_atomic(out, OUT)
    print(f"sample {i} (material {out['material_id']}, condition {out['condition_id']}): best "
          f"{e_best[j]:.4f}, predicted {e_pred[j]:.4f}; fold means {e_best.mean():.4f} vs {e_pred.mean():.4f}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
