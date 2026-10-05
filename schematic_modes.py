"""Owner of results/schematic_modes.json: the 'templates versus recipe' row of Figure 0.

Round-2/3 internal referees (clarity item 4) asked for one picture a materials chemist
can read before Section 5: a template model builds a field as a weighted sum of stored
shapes (proper-orthogonal-decomposition modes), and the weights come from a learned
"recipe" (a regressor from the material's numbers). Section 5 measures that the recipe,
not the templates, limits accuracy. This script records, for one held-out sample, the
same thing as pictures:

  - the first three templates (POD modes of the training fields);
  - the field rebuilt from P templates with the TRUE weights (perfect recipe);
  - the field rebuilt from the same templates with LEARNED weights (gradient boosting,
    the settings of l5_bottleneck.py), on a material the regressor never saw;
  - each rebuild's normalised error, and the same two errors averaged over every
    held-out sample, so the drawn sample can be read against the whole set.

Legacy dataset, legacy split, c channel at the L5 encoding (128 x 128), P = 8.
Selection rule (fixed here, not by eye): the held-out sample whose learned-weights error
is the MEDIAN over the held-out set -- a typical case, not the best or worst.

    python schematic_modes.py
"""
import json

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor

from comoving import load_c_light, nrmse

OUT = "results/schematic_modes.json"
P = 8
DRAW = 64          # templates and fields are recorded at 64 x 64 for drawing


def down(a):
    s = a.shape[-1] // DRAW
    return a.reshape(DRAW, s, DRAW, s).mean((1, 3))


def main():
    X, Pz, mat, split = load_c_light()
    tr, nm = np.where(split == "train")[0], np.where(split == "novel_material")[0]
    n, nz, nt = X.shape
    F = X.reshape(n, -1)
    pca = PCA(n_components=P).fit(F[tr])
    A = pca.transform(F)                                     # true weights, every sample
    Ah = np.empty_like(A)
    for k in range(P):
        m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                          early_stopping=True, random_state=0)
        m.fit(Pz[tr], A[tr, k])
        Ah[:, k] = m.predict(Pz)
    rec_true = pca.inverse_transform(A).reshape(n, nz, nt)
    rec_learn = pca.inverse_transform(Ah).reshape(n, nz, nt)
    e_true, e_learn = nrmse(rec_true, X), nrmse(rec_learn, X)

    order = nm[np.argsort(e_learn[nm])]
    i = int(order[len(order) // 2])                          # the median held-out case
    out = {
        "_what": __doc__.splitlines()[0],
        "P": P, "dataset": "legacy", "split": "novel_material", "n_heldout": int(len(nm)),
        "sample_index": i, "material_id": int(mat[i]),
        "templates": [down(pca.components_[k].reshape(nz, nt)).tolist() for k in range(3)],
        "field": down(X[i]).tolist(),
        "rebuilt_true_weights": down(rec_true[i]).tolist(),
        "rebuilt_learned_weights": down(rec_learn[i]).tolist(),
        "nrmse_true_weights": float(e_true[i]),
        "nrmse_learned_weights": float(e_learn[i]),
        "heldout_mean_nrmse_true_weights": float(e_true[nm].mean()),
        "heldout_mean_nrmse_learned_weights": float(e_learn[nm].mean()),
    }
    json.dump(out, open(OUT, "w"))
    print(f"sample {i} (material {out['material_id']}): true weights {e_true[i]:.4f}, "
          f"learned {e_learn[i]:.4f}; held-out means {out['heldout_mean_nrmse_true_weights']:.4f} "
          f"vs {out['heldout_mean_nrmse_learned_weights']:.4f}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
