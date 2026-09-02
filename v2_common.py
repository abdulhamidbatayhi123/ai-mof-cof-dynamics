"""Shared plumbing for the v2 re-runs of L1, L2 and L7. ONE implementation.

Design frozen in `PREREG_L1L2L7_v2.md`. This module holds what every v2 runner
needs identically — the fold map, the leakage assertion, the evaluation rows, the
per-fold POD cache and the resumable results file — so that the rungs cannot drift
apart in the way that produced retraction A8 (split drift between arms).

Three guards, each earned:

* `load_folds` refuses a fold map that does not cover every material in the data,
  or whose fold count / seed differ from what the results file was started with.
  L1, L2 and L6 must report over the SAME held-out materials in the SAME folds.
* `assert_disjoint` is called before every fit. A POD basis, scaler or regressor
  fitted on an index set that touches the held-out fold is the contamination that
  would flatter every arm equally and make the split meaningless.
* `exit_nrmse` raises if the reference exit curve's range vanishes (rule 5,
  retraction A15). It cannot vanish for a completed breakthrough; if it does, the
  sample is broken and the number must not be averaged in silently.
"""
from __future__ import annotations

import json
import os
import tempfile

import numpy as np

from metrics import breakthrough_times, per_variable_nrmse

ROOT_V2 = "data/parametric_v2"
FOLDS_FILE = "results/l6_v2_folds.json"
CALIBRATION_FILE = "results/calibration_v2.json"
FIELD_RES = 128                  # identical to L5 (run_l5.subsample) and L6-v2
CHANNELS = ("c", "q", "T")


# ─────────────────────────────────────────────────────────────────────────────
# folds and leakage
# ─────────────────────────────────────────────────────────────────────────────

def load_folds(material_ids, path=FOLDS_FILE):
    """The L6-v2 fold assignment, applied to THIS dataset's samples.

    Returns (fold_of_sample, n_folds, fold_seed). Raises if any material in the
    data has no fold, or if the file does not partition materials into the
    declared number of folds — a partial map would silently evaluate only some
    materials and report it as five-fold coverage.
    """
    rec = json.load(open(path))
    m2f = {int(k): int(v) for k, v in rec["material_to_fold"].items()}
    n_folds, seed = int(rec["n_folds"]), int(rec["fold_seed"])
    mats = np.unique(material_ids)
    missing = [int(m) for m in mats if int(m) not in m2f]
    if missing:
        raise RuntimeError(f"{path} has no fold for materials {missing[:10]}... — "
                           f"the fold map does not cover this dataset")
    if set(m2f.values()) != set(range(n_folds)):
        raise RuntimeError(f"{path} declares {n_folds} folds but assigns {sorted(set(m2f.values()))}")
    fold_of = np.array([m2f[int(m)] for m in material_ids])
    return fold_of, n_folds, seed


def assert_disjoint(fit_idx, held_idx, what):
    """No index used to fit anything may be in the held-out set."""
    inter = np.intersect1d(np.asarray(fit_idx), np.asarray(held_idx))
    if inter.size:
        raise AssertionError(f"LEAKAGE: {what} is fitted on {inter.size} held-out samples "
                             f"(e.g. index {int(inter[0])}). The comparison would be invalid.")


def alpha_for(design, path=CALIBRATION_FILE):
    """Calibrated bootstrap level for a design, read from the calibration file.

    `manifest` -> the 48-cluster level; `folds` -> the 240-cluster level. Raises
    if the level has not been calibrated: a verdict at an uncalibrated alpha is
    exactly what retraction A13 withdrew.
    """
    cal = json.load(open(path))
    key = {"manifest": "v2", "folds": "v2_5fold"}[design]
    if key not in cal or "alpha" not in cal[key]:
        raise RuntimeError(f"{path} has no calibrated alpha for design '{design}' ({key}). "
                           f"Run calibrate_v2.py{' --fivefold' if design == 'folds' else ''} first.")
    return float(cal[key]["alpha"]), int(cal[key]["n_clusters"])


def standardise_params(params, fit_idx):
    """z-score the parameter vector on the FIT indices only."""
    mu = params[fit_idx].mean(axis=0)
    sd = params[fit_idx].std(axis=0)
    sd[sd == 0] = 1.0
    return (params - mu) / sd


# ─────────────────────────────────────────────────────────────────────────────
# metrics per sample
# ─────────────────────────────────────────────────────────────────────────────

def exit_nrmse(pred_exit, true_exit):
    rng = float(true_exit.max() - true_exit.min())
    if rng < 0.05:
        raise ValueError(f"exit-curve range {rng:.3e} — the reference has no breakthrough; "
                         f"normalising by it would be rule-5 degenerate (A15)")
    return float(np.sqrt(np.mean((pred_exit - true_exit) ** 2)) / rng)


def sample_row(pred, true, t_norm, t_final):
    """Every per-sample metric the v2 rungs report, from one (3, nz, nt) pair."""
    m = per_variable_nrmse(pred, true)
    for k in ("c", "q", "T"):
        if not np.isfinite(m[k]):
            raise ValueError(f"nRMSE({k}) is not finite — a reference field with zero range")
    pe, te = pred[0, -1, :], true[0, -1, :]
    m["exit_nrmse"] = exit_nrmse(pe, te)
    bp, bt = breakthrough_times(pe, t_norm), breakthrough_times(te, t_norm)
    for lev in (0.05, 0.50, 0.95):
        a, b = bp[lev], bt[lev]
        m[f"dt_bt{int(lev * 100):02d}"] = (abs(a - b) * t_final
                                           if np.isfinite(a) and np.isfinite(b) else np.nan)
    m["dT_peak"] = float(abs(pred[2].max() - true[2].max()))
    return m


def evaluate_coeffs(pred_coeffs, true_fields, bases, t_final, batch=48):
    """Rows of per-sample metrics from POD coefficients -> reconstructed fields.

    `bases` is {channel: fitted PCA}; `pred_coeffs` is (n, 3*r) in channel-major
    blocks, exactly as `run_l1.project` lays them out.
    """
    n, _, nz, nt = true_fields.shape
    r = bases["c"].n_components_
    t_norm = np.linspace(0.0, 1.0, nt)
    rows = []
    for s0 in range(0, n, batch):
        e = min(s0 + batch, n)
        recon = np.empty((e - s0, 3, nz, nt), dtype=np.float32)
        for i, ch in enumerate(CHANNELS):
            block = pred_coeffs[s0:e, i * r:(i + 1) * r]
            recon[:, i] = bases[ch].inverse_transform(block).reshape(-1, nz, nt)
        for k in range(e - s0):
            rows.append(sample_row(recon[k], true_fields[s0 + k], t_norm, t_final[s0 + k]))
        del recon
    return rows


def summarise_rows(rows):
    return {k: float(np.nanmean([r[k] for r in rows])) for k in rows[0]}


def per_sample_lists(rows, d, idx):
    """The per-sample vectors every analysis needs, with sample identity."""
    return {
        "per_sample_nrmse_c": [float(r["c"]) for r in rows],
        "per_sample_nrmse_q": [float(r["q"]) for r in rows],
        "per_sample_nrmse_T": [float(r["T"]) for r in rows],
        "per_sample_exit_nrmse": [float(r["exit_nrmse"]) for r in rows],
        "per_sample_dt_bt50": [float(r["dt_bt50"]) for r in rows],
        "material_ids": d.material_ids[idx].tolist(),
        "condition_ids": d.condition_ids[idx].tolist(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# per-fold POD cache
# ─────────────────────────────────────────────────────────────────────────────

class FoldPOD:
    """POD bases, coefficients and floors for ONE fit index set.

    Fitting the basis is the expensive part and is identical for every arm and
    configuration within a fold, so it is done once and shared. The basis sees
    only `fit_idx`; `assert_disjoint` is called against `held_idx` before the fit.
    """

    def __init__(self, d, fit_idx, held_idx, n_modes, label, verbose=True):
        from run_l1 import fit_pod, project
        assert_disjoint(fit_idx, held_idx, f"POD basis ({label})")
        self.fit_idx, self.held_idx, self.n_modes, self.label = fit_idx, held_idx, n_modes, label
        self.bases, self.spectra = fit_pod(d.fields, fit_idx, n_modes, verbose=verbose)
        self.coeffs = project(d.fields, self.bases)          # (N, 3*n_modes)
        self.params_z = standardise_params(d.params, fit_idx)

    def floor(self, d, idx):
        rows = evaluate_coeffs(self.coeffs[idx], d.fields[idx], self.bases, d.t_final[idx])
        return summarise_rows(rows), rows

    def spectrum_json(self):
        return {c: self.spectra[c].tolist() for c in CHANNELS}


# ─────────────────────────────────────────────────────────────────────────────
# resumable results file
# ─────────────────────────────────────────────────────────────────────────────

def write_atomic(obj, path):
    """Write JSON via a temp file + rename so a kill mid-write cannot leave a
    truncated results file (defect B15's neighbourhood)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, path)


def load_or_init(path, header, match_keys):
    """Resume an existing results file if its configuration matches, else start.

    A mismatch on any of `match_keys` aborts: merging cells produced under a
    different encoding, seed set or fold seed would break information parity
    across the very comparison the rung is.
    """
    if os.path.exists(path):
        try:
            prev = json.load(open(path))
        except Exception:
            prev = None
        if prev:
            for k in match_keys:
                if prev.get(k) != header.get(k):
                    raise SystemExit(
                        f"ABORT: {path} was produced with {k}={prev.get(k)!r} but this run "
                        f"uses {k}={header.get(k)!r}. Move the old file aside or match the config.")
            return prev, True
    return dict(header), False


def get_path(obj, *keys):
    for k in keys:
        if not isinstance(obj, dict) or k not in obj:
            return None
        obj = obj[k]
    return obj


def set_path(obj, value, *keys):
    for k in keys[:-1]:
        obj = obj.setdefault(k, {})
    obj[keys[-1]] = value
