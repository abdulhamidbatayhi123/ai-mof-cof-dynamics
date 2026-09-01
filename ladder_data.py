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

# DESIGN v2 (2026-08-30). Same length, same ordering convention, one substitution:
# `d_p` replaces `k_LDF`. In v2 the mass-transfer coefficient is DERIVED from the
# particle through Glueckauf rather than sampled independently of it, so k_LDF is
# no longer a material property — it is a function of (material, condition) and
# lives on the sample record, not the material record.
#
# This is a REPARAMETERISATION, not a change of information: k_LDF is a
# deterministic function of the eleven values below, so no arm loses anything it
# had before. It is also the better variable for L6: the hidden kinetic object
# becomes a true formulation constant that an experimentalist actually chooses,
# rather than a coefficient that already encodes the isotherm slope.
PARAM_KEYS_V2 = (
    "q_max", "delta_H", "step_rh", "isotherm_n",
    "henry_fraction", "d_p", "rho_p", "eps_t",     # material
    "rh_feed", "v", "T_in",                        # operating
)


def param_keys_for(man):
    """Which parameter vector this dataset uses. Read from the manifest, never guessed."""
    return PARAM_KEYS_V2 if man.get("design") == "v2" else PARAM_KEYS


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
    param_keys: tuple = PARAM_KEYS   # which vector THIS dataset uses; see pidx()

    def idx(self, split):
        return np.where(self.split == split)[0]

    def pidx(self, name):
        """Column of `name` in the parameter vector, or a loud failure.

        Never write `PARAM_KEYS.index("k_LDF")`. The legacy and v2 designs use
        DIFFERENT vectors at the same length: position 5 is `k_LDF` under legacy
        and `d_p` under v2. A hard-coded index would silently read one as the
        other, in a project whose entire premise is that silent substitutions are
        what destroy results. This raises instead.
        """
        try:
            return self.param_keys.index(name)
        except ValueError:
            raise KeyError(
                f"'{name}' is not in this dataset's parameter vector "
                f"({self.meta.get('design', 'legacy')} design: {list(self.param_keys)}). "
                f"Under design v2 the kinetic degree of freedom is 'd_p' and k_LDF is "
                f"derived per sample — read it from the manifest sample records, not "
                f"from the parameter vector."
            ) from None

    def subset(self, split):
        i = self.idx(split)
        return (self.params_z[i], self.fields[i], self.material_ids[i], i)

    def summary(self):
        return {s: int((self.split == s).sum()) for s in SPLITS}


def load(root="data/parametric", verbose=True, field_res=None):
    man_path = os.path.join(root, "manifest.json")
    if not os.path.exists(man_path):
        raise FileNotFoundError(f"{man_path} missing — run gen_parametric_dataset.py")
    man = json.load(open(man_path))

    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    keys = param_keys_for(man)

    # `field_res` subsamples each field AS IT IS READ. Doing it after the fact is
    # too late: dataset v2 is 3947 x 3 x 256 x 256 float32 = 3.1 GB, which on a
    # shared 16 GB machine thrashes or dies before any downsampling code runs.
    # The subsample is applied identically to every sample, so it is an encoding
    # choice made once — record it wherever the result is used.
    rows, fields = [], []
    zi = ti = None
    for s in man["samples"]:
        f = os.path.join(root, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")
        if not os.path.exists(f):
            continue
        m, c = mats[s["mat"]], conds[s["cond"]]
        vec = [(m if k in m else c)[k] for k in keys]
        rows.append((vec, s["mat"], s["cond"], s["split"], s["t_final"]))
        arr = np.load(f, mmap_mode="r" if field_res else None)
        if field_res:
            if zi is None:
                zi = np.linspace(0, arr.shape[1] - 1, field_res).astype(int)
                ti = np.linspace(0, arr.shape[2] - 1, field_res).astype(int)
            arr = np.array(arr[:, zi][:, :, ti], dtype=np.float32)
        fields.append(arr)

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
                   split, t_final, mu, sigma, man, tuple(keys))
    if verbose:
        print(f"loaded {len(rows)} samples from {root}")
        print(f"  fields {fields.shape}  params {params.shape}")
        print(f"  splits {d.summary()}")
        print(f"  materials: {len(np.unique(material_ids))} "
              f"({len(np.unique(material_ids[split == 'novel_material']))} held out)")
        print(f"  design: {man.get('design', 'legacy')}  params: {list(keys)}")
        if field_res:
            print(f"  fields subsampled to {field_res}x{field_res} on load "
                  f"({fields.nbytes / 1e9:.2f} GB resident)")
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
    keys = param_keys_for(man)

    rows, slices = [], []
    for s in man["samples"]:
        f = os.path.join(root, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")
        if not os.path.exists(f):
            continue
        arr = np.load(f, mmap_mode="r")            # no full read
        zi = int(z_frac * (arr.shape[1] - 1))
        slices.append(np.array(arr[:, zi, :], dtype=np.float32))
        m, c = mats[s["mat"]], conds[s["cond"]]
        rows.append(([(m if k in m else c)[k] for k in keys],
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
                   condition_ids, split, t_final, mu, sd, man, tuple(keys))
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
    for k, lo, hi in zip(d.param_keys, d.params[tr].min(0), d.params[tr].max(0)):
        print(f"  {k:<16} [{lo:12.4g}, {hi:12.4g}]")
    print()
    print("field ranges:", {n: (float(d.fields[:, i].min()), float(d.fields[:, i].max()))
                            for i, n in enumerate(("c/c_in", "q/q_max", "T/T_in"))})
