"""Build the dataset deposit for Zenodo (Digital Discovery requires the training and test data).

Writes deposit/ with:
  ai-mof-ladder-v2-fields-128.zip   every accepted v2 sample, (3, 128, 128) float32 c/c_in, q/q_max,
                                    T/T_in on the grid every rung scores (z/L, t/t_final), one .npy each
  ai-mof-ladder-legacy-fields.zip   the legacy dataset at its stored resolution (rungs L3, first L5,
                                    coordinate change)
  manifests/                        the two manifest.json files and the five-fold map
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


def main():
    os.makedirs(os.path.join(OUT, "manifests"), exist_ok=True)
    n2, man2 = pack(ROOT_V2, os.path.join(OUT, "ai-mof-ladder-v2-fields-128.zip"), True)
    nl, manl = pack(ROOT_LEG, os.path.join(OUT, "ai-mof-ladder-legacy-fields.zip"), False)
    shutil.copy(os.path.join(ROOT_V2, "manifest.json"), os.path.join(OUT, "manifests", "manifest_v2.json"))
    shutil.copy(os.path.join(ROOT_LEG, "manifest.json"), os.path.join(OUT, "manifests", "manifest_legacy.json"))
    shutil.copy(FOLDS_FILE, os.path.join(OUT, "manifests", os.path.basename(FOLDS_FILE)))
    card = f"""# Data card: simulated water-adsorption breakthrough fields

Companion dataset of "The coefficient map, not the basis, limits how machine-learning surrogates of
metal-organic framework water-adsorption beds transfer to unseen materials". Code and every result:
https://github.com/abdulhamidbatayhi123/ai-mof-cof-dynamics (Zenodo concept DOI 10.5281/zenodo.23302586).

## Files
- `ai-mof-ladder-v2-fields-128.zip`: {n2} samples of the larger (v2) dataset, {man2.get('store_nz')}x{man2.get('store_nt')}
  stored fields subsampled to {FIELD_RES}x{FIELD_RES} by index rule linspace(0, N-1, {FIELD_RES}), exactly as every rung scores them.
- `ai-mof-ladder-legacy-fields.zip`: {nl} samples of the legacy dataset at their stored resolution.
- `manifests/manifest_v2.json`, `manifests/manifest_legacy.json`: every material, condition and
  sample, with the generator's seeds and settings; `manifests/{os.path.basename(FOLDS_FILE)}`: the five-fold map.

## Schema
Each `mMMMM_cCCCC.npy` is float32 with shape (3, N_z, N_t): channel 0 is c/c_in, 1 is q/q_max,
2 is T/T_in, on a uniform grid in z/L (axis 1, inlet first) and t/t_final (axis 2). MMMM is the
material id and CCCC the condition id in the manifest, whose `samples` entries also give t_final
(seconds), c_in, the horizon multiple, the Damkohler number and the split.

## Provenance
Produced by `gen_parametric_dataset.py --design v2` (finite-volume method of lines, 2000 cells,
SciPy BDF) from the parameters in the manifest; the fields are the solver output, not edited.
Licence: CC BY 4.0.
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
