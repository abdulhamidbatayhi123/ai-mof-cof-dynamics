"""Evaluation metrics for the ladder. Every arm is scored through this module.

Two rules are enforced here rather than left to discipline, because both have
already caused a retraction in this project (A8) or in the prior one.

1. POOLED MSE IS FORBIDDEN.
   In this system var(T)/var(c) is about 4.5e6. An unweighted mean squared error
   over (c, q, T) is the temperature error wearing a disguise -- concentration
   contributes ~0.0000% of it. `pooled_mse` exists only to raise an error and
   point here.

2. A DIFFERENCE WHOSE CI INCLUDES ZERO IS NO DIFFERENCE.
   `compare` returns the CI and an explicit `significant` flag. Report the flag,
   in words, not a point estimate that happens to favour one arm.

Bootstrap resampling is CLUSTER-ROBUST BY MATERIAL. Conditions sharing a
material are not independent -- they share q_max, dH, kinetics and isotherm
shape -- so resampling individual conditions understates the variance and
manufactures significance.

That is measured, not assumed. Under a realistic null (two arms that tie on
average, but where some materials favour one and some the other, so the
DIFFERENCE is clustered), over 200 trials at 20 materials x 5 conditions:

    false-positive rate, clustered by material :   7.0 %   (nominal 5 %)
    false-positive rate, naive per-condition   :  32.5 %

A naive bootstrap would report a significant difference in roughly one of every
three comparisons where none exists. Materials are the resampling unit.

Note that pairing alone does NOT fix this. When both arms are evaluated on the
same conditions, pairing removes the shared per-material difficulty, but any
material-level structure in the arms' RELATIVE performance survives -- and that
is precisely the realistic case.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def pooled_mse(*_args, **_kwargs):
    raise NotImplementedError(
        "Pooled MSE across (c, q, T) is forbidden — var(T)/var(c) ~ 4.5e6, so it "
        "reports temperature error and nothing else. Use per_variable_nrmse()."
    )


# ─────────────────────────────────────────────────────────────────────────────
# per-sample metrics
# ─────────────────────────────────────────────────────────────────────────────

def per_variable_nrmse(pred, true):
    """RMSE per field, normalised by that field's range in the reference.

    pred, true: (3, N_z, N_t) arrays of (c, q, T) in the stored normalised units.
    Returns {"c": .., "q": .., "T": ..}.
    """
    out = {}
    for i, name in enumerate(("c", "q", "T")):
        t = true[i]
        rng = float(t.max() - t.min())
        rmse = float(np.sqrt(np.mean((pred[i] - t) ** 2)))
        out[name] = rmse / rng if rng > 0 else np.nan
    return out


def breakthrough_times(curve, t, levels=(0.05, 0.50, 0.95)):
    """First crossing time of each level in a monotone-ish exit curve.

    Uses the FIRST upcrossing rather than np.interp over the whole series: a
    breakthrough curve with a thermal overshoot is not monotone, and interpolating
    against a non-monotone x-array silently returns nonsense.
    """
    out = {}
    for lev in levels:
        idx = np.argmax(curve >= lev)
        if curve[idx] < lev:
            out[lev] = np.nan
            continue
        if idx == 0:
            out[lev] = float(t[0])
            continue
        c0, c1 = curve[idx - 1], curve[idx]
        f = 0.0 if c1 == c0 else (lev - c0) / (c1 - c0)
        out[lev] = float(t[idx - 1] + f * (t[idx] - t[idx - 1]))
    return out


def engineering_metrics(pred, true, t_norm, t_final):
    """Quantities a process engineer actually uses, not just field error."""
    c_pred, c_true = pred[0, -1, :], true[0, -1, :]     # exit concentration
    T_pred, T_true = pred[2], true[2]
    q_pred, q_true = pred[1], true[1]

    bt_p = breakthrough_times(c_pred, t_norm)
    bt_t = breakthrough_times(c_true, t_norm)

    m = {}
    for lev in (0.05, 0.50, 0.95):
        a, b = bt_p[lev], bt_t[lev]
        m[f"dt_bt_{int(lev * 100):02d}_s"] = (a - b) * t_final if np.isfinite(a) and np.isfinite(b) else np.nan

    m["dT_peak_err_K"] = float((T_pred.max() - T_true.max()) * 1.0)  # in T_ref units
    # working capacity: mean solid loading at the end of the run
    m["working_capacity_err"] = float(q_pred[:, -1].mean() - q_true[:, -1].mean())
    return m


# ─────────────────────────────────────────────────────────────────────────────
# aggregation with cluster-robust bootstrap
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ArmResult:
    """Per-condition scores for one arm, tagged by material for clustering."""
    name: str
    material_ids: np.ndarray
    values: np.ndarray            # one scalar score per condition
    metric: str = "nrmse_c"

    def __post_init__(self):
        self.material_ids = np.asarray(self.material_ids)
        self.values = np.asarray(self.values, dtype=float)
        if self.material_ids.shape != self.values.shape:
            raise ValueError("material_ids and values must be the same length")


def _cluster_bootstrap(values, material_ids, n_boot, rng, stat=np.mean):
    """Resample MATERIALS (with replacement), then take all their conditions."""
    mats = np.unique(material_ids)
    idx_by_mat = {m: np.where(material_ids == m)[0] for m in mats}
    out = np.empty(n_boot)
    for b in range(n_boot):
        drawn = rng.choice(mats, size=len(mats), replace=True)
        take = np.concatenate([idx_by_mat[m] for m in drawn])
        out[b] = stat(values[take])
    return out


def summarise(arm: ArmResult, n_boot=2000, seed=0, alpha=0.05):
    rng = np.random.default_rng(seed)
    boots = _cluster_bootstrap(arm.values, arm.material_ids, n_boot, rng)
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "arm": arm.name, "metric": arm.metric,
        "mean": float(arm.values.mean()),
        "ci_low": float(lo), "ci_high": float(hi),
        "n_conditions": int(arm.values.size),
        "n_materials": int(np.unique(arm.material_ids).size),
    }


# Percentile cluster bootstrap OVER-REJECTS at the cluster counts we have.
# Measured false-positive rate under a realistic null, nominal 5 %:
#     12 materials -> 8.5-9.7 %,  20 -> 10.7 %,  30 -> 9.7 %,  60 -> 7.7 %
# Calibrating on the 12-material novel-material split (see calibrate_ci.py):
#     nominal alpha 0.050 -> 8.5 % actual
#     nominal alpha 0.010 -> 5.8 % actual
#     nominal alpha 0.005 -> 4.2 % actual   <- use this for a true 5 % test
# Null verdicts are conservative under an over-rejecting test, so "no difference"
# was always safe; POSITIVE claims at nominal 0.05 were not.
ALPHA_CALIBRATED = 0.005


def compare(a: ArmResult, b: ArmResult, n_boot=2000, seed=0, alpha=ALPHA_CALIBRATED):
    """PAIRED comparison of two arms on the same conditions.

    Pairing matters: arms are evaluated on identical conditions, so the
    condition-to-condition variance is shared and an unpaired test would be far
    less powerful while also being wrong about the null.
    """
    if not np.array_equal(a.material_ids, b.material_ids):
        raise ValueError("arms must be evaluated on the same conditions, in the same order")

    diff = a.values - b.values
    rng = np.random.default_rng(seed)
    boots = _cluster_bootstrap(diff, a.material_ids, n_boot, rng)
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    significant = bool(lo > 0 or hi < 0)

    if significant:
        better = b.name if diff.mean() > 0 else a.name
        verdict = f"{better} is better (lower {a.metric})"
    else:
        verdict = f"no difference between {a.name} and {b.name}"

    return {
        "arm_a": a.name, "arm_b": b.name, "metric": a.metric,
        "mean_a": float(a.values.mean()), "mean_b": float(b.values.mean()),
        "mean_diff": float(diff.mean()),
        "ci_low": float(lo), "ci_high": float(hi),
        "significant": significant,
        "verdict": verdict,
        "n_materials": int(np.unique(a.material_ids).size),
    }


def format_comparison(res):
    """One line, stating the conclusion in words rather than implying it."""
    ci = f"[{res['ci_low']:+.4g}, {res['ci_high']:+.4g}]"
    flag = "" if res["significant"] else "  (CI includes zero — NO DIFFERENCE)"
    return (f"{res['arm_a']} {res['mean_a']:.4g} vs {res['arm_b']} {res['mean_b']:.4g} | "
            f"diff {res['mean_diff']:+.4g} CI {ci}{flag}")


if __name__ == "__main__":
    # self-test: two arms that genuinely differ, and two that do not
    rng = np.random.default_rng(0)
    mats = np.repeat(np.arange(20), 5)
    base = rng.normal(0.10, 0.02, size=mats.size)
    print("A vs B where B is genuinely better by 0.03:")
    a = ArmResult("A", mats, base)
    b = ArmResult("B", mats, base - 0.03 + rng.normal(0, 0.005, mats.size))
    print("   ", format_comparison(compare(a, b)))

    print("A vs C where C differs only by noise:")
    c = ArmResult("C", mats, base + rng.normal(0, 0.005, mats.size))
    print("   ", format_comparison(compare(a, c)))

    print("\nPooled MSE guard:")
    try:
        pooled_mse()
    except NotImplementedError as e:
        print("    raises:", str(e)[:70], "...")
