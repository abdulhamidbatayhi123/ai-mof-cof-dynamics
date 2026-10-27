"""Build the dataset deposit for Zenodo (Digital Discovery requires the training and test data).

Writes deposit/ with:
  ai-mof-ladder-v2-fields-128.zip   every accepted v2 sample, (3, 128, 128) float32 c/c_in, q/q_max,
                                    T/T_in on the grid every rung scores (z/L, t/t_final), one .npy each
  ai-mof-ladder-v3-fields-128.zip   design v3 (PREREG_DD_V3), same layout
  named-frameworks-*.zip            the six named frameworks under the v2 and v3 rules
  ai-mof-ladder-legacy-fields.zip   the legacy dataset at its stored resolution (rungs L3, first L5,
                                    coordinate change)
  manifests/                        the three manifest.json files and the two five-fold maps
  sha256sums.txt                    a checksum per file
  DATA_CARD.md                      schema, units, normalisation, how the files map to the paper

Streams one sample at a time (low memory). Nothing is computed; the arrays are the stored solver
fields, subsampled by the same rule as ladder_data.load(field_res=128).

    python make_dataset_deposit.py
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import zipfile

import numpy as np

from coarse_solver_baseline import sub
from v2_common import FIELD_RES, FOLDS_FILE, ROOT_V2

ROOT_LEG = "data/parametric"
ROOT_V3, FOLDS_V3 = "data/parametric_v3", "results/v3_folds.json"   # PREREG_DD_V3
MODELS = "models"                     # trained DeepONet checkpoints of PREREG_DD_V3 amendment A1
OUT = "deposit"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pack(root, zpath, resample):
    man = json.load(open(os.path.join(root, "manifest.json")))
    n = 0
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for s in man["samples"]:
            f = os.path.join(root, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")
            if not (s.get("ok", True) and os.path.exists(f)):
                continue
            arr = np.load(f, mmap_mode="r")
            arr = sub(np.asarray(arr), FIELD_RES) if resample else np.asarray(arr)
            buf = io.BytesIO()
            np.save(buf, arr.astype(np.float32))
            z.writestr(os.path.basename(f), buf.getvalue())
            n += 1
    return n, man


def pack_once(root, zpath, resample):
    """Re-use a zip already built from the same manifest (the arrays are fixed solver output)."""
    man = json.load(open(os.path.join(root, "manifest.json")))
    if os.path.exists(zpath):
        with zipfile.ZipFile(zpath) as z:
            n = len(z.namelist())
        n_ok = sum(1 for s in man["samples"] if s.get("ok", True) and os.path.exists(
            os.path.join(root, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")))
        if n == n_ok:
            return n, man
    return pack(root, zpath, resample)


def pack_dir(src, zpath, ext=".npy"):
    """A directory of files with one extension: the named-framework truth fields (B2, and V6 on
    v3, already at 128 x 128), or the DeepONet checkpoints (.pt)."""
    n = 0
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for fn in sorted(os.listdir(src)):
            if fn.endswith(ext):
                z.write(os.path.join(src, fn), fn)
                n += 1
    return n


def main():
    os.makedirs(os.path.join(OUT, "manifests"), exist_ok=True)
    n2, man2 = pack_once(ROOT_V2, os.path.join(OUT, "ai-mof-ladder-v2-fields-128.zip"), True)
    nl, manl = pack_once(ROOT_LEG, os.path.join(OUT, "ai-mof-ladder-legacy-fields.zip"), False)
    n3, man3 = pack_once(ROOT_V3, os.path.join(OUT, "ai-mof-ladder-v3-fields-128.zip"), True)
    nf2 = pack_dir("results/dd_b2_fields", os.path.join(OUT, "named-frameworks-v2-fields-128.zip"))
    nf3 = pack_dir("results/dd_b2_fields_v3", os.path.join(OUT, "named-frameworks-v3-fields-128.zip"))
    nm = pack_dir(MODELS, os.path.join(OUT, "deeponet-checkpoints.zip"), ext=".pt")
    shutil.copy(os.path.join(ROOT_V3, "manifest.json"), os.path.join(OUT, "manifests", "manifest_v3.json"))
    shutil.copy(FOLDS_V3, os.path.join(OUT, "manifests", os.path.basename(FOLDS_V3)))
    shutil.copy(os.path.join(ROOT_V2, "manifest.json"), os.path.join(OUT, "manifests", "manifest_v2.json"))
    shutil.copy(os.path.join(ROOT_LEG, "manifest.json"), os.path.join(OUT, "manifests", "manifest_legacy.json"))
    shutil.copy(FOLDS_FILE, os.path.join(OUT, "manifests", os.path.basename(FOLDS_FILE)))
    card = f"""# Data card: simulated water-adsorption breakthrough fields

Companion dataset of "The coefficient map, not the basis, limits machine-learning surrogates of MOF water-adsorption beds on unseen materials". Code and every result:
https://github.com/abdulhamidbatayhi123/ai-mof-cof-dynamics (Zenodo concept DOI 10.5281/zenodo.23302586).

## Files
- `ai-mof-ladder-v2-fields-128.zip`: {n2} samples of the larger (v2) dataset, {man2.get('store_nz')}x{man2.get('store_nt')}
  stored fields subsampled to {FIELD_RES}x{FIELD_RES} by index rule linspace(0, N-1, {FIELD_RES}), exactly as every rung scores them.
- `ai-mof-ladder-v3-fields-128.zip`: {n3} samples of design v3 (PREREG_DD_V3: sampled primary-site
  affinity, step steepness up to n = 32), subsampled by the same rule.
- `ai-mof-ladder-legacy-fields.zip`: {nl} samples of the legacy dataset at their stored resolution.
- `named-frameworks-v2-fields-128.zip`, `named-frameworks-v3-fields-128.zip`: {nf2} and {nf3} production
  fields of the six named frameworks (MOF-303, MOF-801, CAU-10-H, aluminium fumarate, MIL-160(Al),
  Co2Cl2(BTDD)) under the v2 and v3 parameter rules, named `<framework>_cCCCC.npy`.
- `deeponet-checkpoints.zip`: {nm} trained DeepONet state dictionaries (PyTorch) of PREREG_DD_V3
  amendment A1, named `<design>_p<basis size>_s<seed>_f<fold>.pt` (out-of-fold models) and
  `fwfit_v3_deeponet_p16_s<seed>.pt` (refit on all v3 materials); `dd_v3._load_model` rebuilds
  one (`run_l5.DeepONet` with the width rule and settings of `dd_screening_frameworks.py`). The
  inputs are the manifest's material and condition parameters, standardised with the mean and
  standard deviation of the training folds for an out-of-fold model
  (`v2_common.standardise_params`) and of all v3 samples for a refit model
  (`dd_v3a1.phase_fwfit`); a parameter with zero spread is divided by one.
- `manifests/manifest_v2.json`, `manifest_v3.json`, `manifest_legacy.json`: every material, condition
  and sample, with the generator's seeds and settings; `manifests/{os.path.basename(FOLDS_FILE)}` and
  `v3_folds.json`: the five-fold maps.

## Schema
Each `mMMMM_cCCCC.npy` is float32 with shape (3, N_z, N_t): channel 0 is c/c_in, 1 is q/q_max,
2 is T/T_in; axis 1 is z/L (inlet first), axis 2 is t/t_final. The stored solver grid is uniform
(N points from 0 to 1); the 128-point files keep the stored points with indices
linspace(0, N-1, 128) cast to int; for N = 256 that is 126 steps of two stored points and one
step of three, so the coordinates are index / (N-1), not a uniform 128-point grid. MMMM is the
material id and CCCC the condition id in the manifest, whose `samples` entries also give t_final
(seconds), c_in, the horizon multiple, the Damkohler number and the split.

## Provenance
Produced by `gen_parametric_dataset.py --design v2` and `--design v3` (finite-volume method of lines, 2000 cells,
SciPy BDF) from the parameters in the manifest; the fields are the solver output, not edited.
Licence: CC BY 4.0 (data). The code is under the MIT licence in the repository.
"""
    open(os.path.join(OUT, "DATA_CARD.md"), "w", encoding="utf-8").write(card)
    with open(os.path.join(OUT, "sha256sums.txt"), "w") as f:
        for dirpath, _, files in os.walk(OUT):
            for fn in sorted(files):
                if fn == "sha256sums.txt":
                    continue
                p = os.path.join(dirpath, fn)
                f.write(f"{sha256(p)}  {os.path.relpath(p, OUT).replace(os.sep, '/')}\n")
    for dirpath, _, files in os.walk(OUT):
        for fn in files:
            p = os.path.join(dirpath, fn)
            print(f"  {os.path.relpath(p, OUT):45s} {os.path.getsize(p) / 1e6:9.1f} MB")


if __name__ == "__main__":
    main()
