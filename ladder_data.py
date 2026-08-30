"""Dataset loading and splitting for the ladder. ONE implementation, shared by every arm.

Split logic lives here and nowhere else. If each arm loaded its own data, the
splits would drift, and a drifted split is not a slow leak — it is the single
failure that invalidated the previous version of this project outright
(retraction A8: the physics arm saw the test window, the baselines did not).

`load()` returns the same object to every arm. Arms may not re-split, re-sample,
or re-normalise. `assert_parity()` checks that two arms were handed identical
conditions in identical order before any comparison is reported.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

import numpy as np

SPLITS = ("train", "novel_condition", "novel_material")

# Inputs the branch/parameter vector carries. Frozen: every arm sees exactly these,
# in this order. Adding one silently changes information parity.
PARAM_KEYS = (
    "q_max", "delta_H", "step_rh", "isotherm_n",
    "henry_fraction", "k_LDF", "rho_p", "eps_t",   # material
    "rh_feed", "v", "T_in",                        # operating
)


@dataclass
class LadderData:
    params: np.ndarray          # (N, 11) raw parameter vectors
    params_z: np.ndarray        # (N, 11) standardised using TRAIN statistics only
    fields: np.ndarray          # (N, 3, nz, nt) c/c_in, q/q_max, T/T_in
    material_ids: np.ndarray    # (N,)
    condition_ids: np.ndarray   # (N,)
    split: np.ndarray           # (N,) strings
    t_final: np.ndarray         # (N,) seconds
    mu: np.ndarray
    sigma: np.ndarray
    meta: dict

    def idx(self, split):
        return np.where(self.split == split)[0]

    def subset(self, split):
        i = self.idx(split)
        return (self.params_z[i], self.fields[i], self.material_ids[i], i)

    def summary(self):
        return {s: int((self.split == s).sum()) for s in SPLITS}


def load(root="data/parametric", verbose=True):
    man_path = os.path.join(root, "manifest.json")
    if not os.path.exists(man_path):
        raise FileNotFoundError(f"{man_path} missing — run gen_parametric_dataset.py")
    man = json.load(open(man_path))

    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}

    rows, fields = [], []
    for s in man["samples"]:
        f = os.path.join(root, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")
        if not os.path.exists(f):
            continue
        m, c = mats[s["mat"]], conds[s["cond"]]
        vec = [(m if k in m else c)[k] for k in PARAM_KEYS]
        rows.append((vec, s["mat"], s["cond"], s["split"], s["t_final"]))
        fields.append(np.load(f))

    if not rows:
        raise RuntimeError(f"no sample files found under {root}")

    params = np.array([r[0] for r in rows], dtype=np.float64)
    material_ids = np.array([r[1] for r in rows])
    condition_ids = np.array([r[2] for r in rows])
    split = np.array([r[3] for r in rows])
    t_final = np.array([r[4] for r in rows], dtype=np.float64)
    fields = np.stack(fields).astype(np.float32)

    # Standardise using TRAIN STATISTICS ONLY. Fitting the scaler on the full set
    # leaks held-out material properties into the normalisation, which is a real
    # (if small) train/test contamination and is trivially avoidable.
    tr = split == "train"
    mu = params[tr].mean(axis=0)
    sigma = params[tr].std(axis=0)
    sigma[sigma == 0] = 1.0
    params_z = (params - mu) / sigma

    d = LadderData(params, params_z, fields, material_ids, condition_ids,
                   split, t_final, mu, sigma, man)
    if verbose:
        print(f"loaded {len(rows)} samples from {root}")
        print(f"  fields {fields.shape}  params {params.shape}")
        print(f"  splits {d.summary()}")
        print(f"  materials: {len(np.unique(material_ids))} "
              f"({len(np.unique(material_ids[split == 'novel_material']))} held out)")
    return d


def load_slice(root="data/parametric", z_frac=0.5, verbose=True):
    """Load ONLY one z-slice per sample: (N, 3, nt), plus the same metadata.

    `load()` materialises (988, 3, 512, 256) float32 = 1.45 GB. Analyses that
    probe a single column position do not need it, and allocating it competes
    with whatever training run is in flight — which is how this was discovered
    (a MemoryError while a PINN sweep held the RAM).
    """
    man_path = os.path.join(root, "manifest.json")
    if not os.path.exists(man_path):
        raise FileNotFoundError(f"{man_path} missing — run gen_parametric_dataset.py")
    man = json.load(open(man_path))
    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}

    rows, slices = [], []
    for s in man["samples"]:
        f = os.path.join(root, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")
        if not os.path.exists(f):
            continue
        arr = np.load(f, mmap_mode="r")            # no full read
        zi = int(z_frac * (arr.shape[1] - 1))
        slices.append(np.array(arr[:, zi, :], dtype=np.float32))
        m, c = mats[s["mat"]], conds[s["cond"]]
        rows.append(([(m if k in m else c)[k] for k in PARAM_KEYS],
                     s["mat"], s["cond"], s["split"], s["t_final"]))

    params = np.array([r[0] for r in rows], dtype=np.float64)
    material_ids = np.array([r[1] for r in rows])
    condition_ids = np.array([r[2] for r in rows])
    split = np.array([r[3] for r in rows])
    t_final = np.array([r[4] for r in rows], dtype=np.float64)
    fields = np.stack(slices)                       # (N, 3, nt)

    tr = split == "train"
    mu, sd = params[tr].mean(axis=0), params[tr].std(axis=0)
    sd[sd == 0] = 1.0
    d = LadderData(params, (params - mu) / sd, fields, material_ids,
                   condition_ids, split, t_final, mu, sd, man)
    if verbose:
        print(f"loaded {len(rows)} samples (z-slice at {z_frac:.2f}L) from {root}")
        print(f"  slices {fields.shape}  ({fields.nbytes / 1e6:.0f} MB, vs "
              f"{fields.nbytes * 512 / 1e9:.2f} GB for the full field)")
    return d


def assert_parity(*arms):
    """Every arm must have been evaluated on identical conditions, in order."""
    ref = arms[0]
    for a in arms[1:]:
        if not np.array_equal(np.asarray(ref), np.asarray(a)):
            raise AssertionError(
                "information parity violated: arms were evaluated on different "
                "conditions or in different order — the comparison is invalid"
            )
    return True


if __name__ == "__main__":
    d = load()
    print()
    print("parameter ranges (train split):")
    tr = d.idx("train")
    for k, lo, hi in zip(PARAM_KEYS, d.params[tr].min(0), d.params[tr].max(0)):
        print(f"  {k:<16} [{lo:12.4g}, {hi:12.4g}]")
    print()
    print("field ranges:", {n: (float(d.fields[:, i].min()), float(d.fields[:, i].max()))
                            for i, n in enumerate(("c/c_in", "q/q_max", "T/T_in"))})
