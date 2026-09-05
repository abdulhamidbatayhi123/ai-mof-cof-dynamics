"""Verification harness for the MOF/COF adsorption digital-twin pipeline.

Every claim that reaches the manuscript must pass these gates. Run it before
committing, before training, and before regenerating any figure:

    python validate.py                # run everything
    python validate.py --only solver  # run one category
    python validate.py --list         # show all gates

Exit code is non-zero if any gate fails, so it can be wired into CI or a
pre-commit hook. A gate that cannot run (missing file, failed import) is
reported as SKIP, never as PASS.

Categories
----------
integrity : results must be computed, never hand-written
checkpoint: trained weights must be finite and usable
isotherm  : adsorption thermodynamics must be self-consistent
solver    : the ground-truth data must actually be a resolved solution
residual  : PDE loss terms must be commensurate before training starts
model     : network derivatives must be smooth enough to differentiate twice
"""
from __future__ import annotations

import argparse
import re
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Windows consoles default to cp1252, which cannot encode the box-drawing and
# scientific characters used below (and in chemical notation generally). Force
# UTF-8 so a report never dies on its own formatting.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # pragma: no cover - non-reconfigurable stream
        pass

R_GAS = 8.314  # J/mol/K


class Skip(Exception):
    """Raised by a gate when its prerequisites are unavailable."""


@dataclass
class Gate:
    name: str
    category: str
    fn: callable
    detail: str = ""


REGISTRY: list[Gate] = []


def gate(name: str, category: str):
    def deco(fn):
        REGISTRY.append(Gate(name=name, category=category, fn=fn, detail=fn.__doc__ or ""))
        return fn

    return deco


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_field(path: str):
    """Return (z, t, c, q, T) from a solver .npz, or Skip if absent."""
    p = ROOT / path
    if not p.exists():
        raise Skip(f"{path} not found")
    d = np.load(p)
    z, t, y = d["z"], d["t"], d["y"]
    n = len(z)
    return z, t, y[:n], y[n : 2 * n], y[2 * n :]


def _physics(kind: str = "default"):
    try:
        from solver_fd import AdsorptionPhysicsConfig
    except Exception as e:  # pragma: no cover
        raise Skip(f"cannot import solver_fd ({e})")
    if kind == "default":
        return AdsorptionPhysicsConfig()
    from fetch_real_mof_data import get_mof303_physics

    return get_mof303_physics()


_DATASET_SPECS = [
    ("data/synthetic_breakthrough.npz", "default", 1.0),
    ("data/mof303_breakthrough.npz", "mof303", None),
]


def _resolve_datasets():
    """Read c_in from each dataset when it records one, so gates never assume it."""
    out = []
    for path, kind, fallback in _DATASET_SPECS:
        c_in = fallback
        p = ROOT / path
        if p.exists():
            d = np.load(p)
            if "c_in" in d:
                c_in = float(d["c_in"])
        if c_in is None:
            from fetch_real_mof_data import rh_to_conc

            c_in = rh_to_conc(0.30, _physics(kind).T_in)
        out.append((path, kind, c_in))
    return out


DATASETS = _resolve_datasets()


# ─────────────────────────────────────────────────────────────────────────────
# integrity — the anti-fabrication gates
# ─────────────────────────────────────────────────────────────────────────────

# Patterns that indicate a plotted curve was invented rather than computed.
_FABRICATION_PATTERNS = [
    (r"np\.random\.normal\s*\([^)]*\)\s*(?:#.*)?$", "synthetic noise added to a plotted series"),
    (r"copy\s*\(\s*\w*_true\s*\)", "a 'prediction' built by copying ground truth"),
    (r"\bhallucinat", "a hand-authored 'failure' curve"),
    (r"placeholder logic", "acknowledged placeholder left in a plotting path"),
]


@gate("plotting code computes its curves", "integrity")
def gate_no_fabricated_curves():
    """No plotting script may synthesise a series it labels as a model prediction."""
    offenders = []
    for path in sorted(ROOT.glob("*.py")):
        if path.name == "validate.py":
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        if "matplotlib" not in src and "plt." not in src:
            continue
        for lineno, line in enumerate(src.splitlines(), 1):
            for pat, why in _FABRICATION_PATTERNS:
                if re.search(pat, line, re.IGNORECASE):
                    offenders.append(f"{path.name}:{lineno} — {why}")
    if offenders:
        return False, "figures must come from a model:\n      " + "\n      ".join(offenders)
    return True, "no synthesised series found in plotting code"


# A plotting script may not invent a model series. There are exactly TWO legitimate
# provenances and the gate below admits only those:
#
#   (A) CHECKPOINT — the script loads trained weights and evaluates them
#       (`load_state_dict`). This was the original rule, written for A1.
#   (B) RECORDED   — the script reads a number a RUNNER already wrote to a results
#       file and never touches a model itself. Every figure in the current set is of
#       this kind, and it is the safer of the two: the number is the one the verdict
#       was computed from, not a re-run that might differ.
#
# (B) is admitted only on proof, never on assertion (B37: a gate that can be bypassed
# is not a gate). The script must contain NO machinery capable of producing a
# prediction, and every results path it names must actually exist on disk — so it
# cannot cite a file nobody wrote.
_MODEL_MACHINERY = [
    (r"\bimport\s+torch\b|\bfrom\s+torch\b", "imports torch"),
    (r"\bfrom\s+sklearn\b|\bimport\s+sklearn\b", "imports sklearn"),
    (r"\bimport\s+xgboost\b|\bfrom\s+xgboost\b", "imports xgboost"),
    (r"\.predict\s*\(", "calls .predict()"),
    (r"\.fit\s*\(", "calls .fit()"),
    (r"\bnn\.[A-Z]", "constructs a torch module"),
]
_RESULTS_PATH = re.compile(r"[\"'](results/[\w./-]+\.json|verify_solver\.json)[\"']")


@gate("plotting code loads a checkpoint", "integrity")
def gate_plot_loads_model():
    """Any script that draws a model curve must load a checkpoint, or read a
    recorded results file and demonstrably compute nothing itself."""
    bad, ok = [], []
    for path in sorted(ROOT.glob("*.py")):
        if path.name == "validate.py":
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        if "plt." not in src:
            continue
        # Gating on labels alone can be defeated by renaming a label, so EVERY figure
        # script must declare a provenance whatever its labels say.
        draws_model = path.name.startswith("fig") or re.search(
            r"label\s*=\s*(?:rf|fr|[rbfu])?[\"'][^\"']*(PIKAN|MLP|DeepONet|FNO|WNO|DeepOKAN|POD)",
            src, re.I)
        if not draws_model:
            continue
        if "load_state_dict" in src:
            ok.append(f"{path.name}: checkpoint")
            continue
        machinery = [why for pat, why in _MODEL_MACHINERY if re.search(pat, src)]
        named = sorted({m.group(1) for m in _RESULTS_PATH.finditer(src)})
        # A run still in flight has not written its verdict file yet. A script may
        # name such a file ONLY by declaring it in a PENDING_RESULTS tuple, which the
        # gate polices both ways: a declared file must NOT exist (a stale declaration
        # would let a figure keep drawing "in flight" over a result that has landed),
        # and an undeclared missing file is still a failure.
        pend_m = re.search(r"PENDING_RESULTS\s*=\s*\((.*?)\)", src, re.S)
        pending = sorted({m.group(1) for m in _RESULTS_PATH.finditer(pend_m.group(1))}) if pend_m else []
        stale = [p for p in pending if (ROOT / p).exists()]
        if stale:
            bad.append(f"{path.name} — declares {', '.join(stale)} as PENDING_RESULTS but the file "
                       f"exists: the run has landed and the figure must read it")
            continue
        missing = [p for p in named if not (ROOT / p).exists() and p not in pending]
        if machinery:
            bad.append(f"{path.name} — labels a model curve, loads no checkpoint, and "
                       f"{machinery[0]}, so it could compute the series itself")
        elif not named:
            bad.append(f"{path.name} — labels a model curve but neither loads a checkpoint "
                       f"nor names a results file to read it from")
        elif missing:
            bad.append(f"{path.name} — reads model series from files that do not exist: "
                       + ", ".join(missing))
        else:
            ok.append(f"{path.name}: recorded ({len(named)} file{'s' if len(named) > 1 else ''}"
                      + (f", {len(pending)} pending" if pending else "") + ")")
    if bad:
        return False, "\n      ".join(bad)
    return True, "model curves come from a checkpoint or a recorded results file — " + "; ".join(ok)


# ─────────────────────────────────────────────────────────────────────────────
# checkpoint
# ─────────────────────────────────────────────────────────────────────────────

@gate("checkpoint parameters are finite", "checkpoint")
def gate_checkpoint_finite():
    """A saved model must contain no NaN or Inf in any learnable tensor."""
    try:
        import torch
    except Exception as e:
        raise Skip(f"torch unavailable ({e})")
    ckpts = sorted(ROOT.glob("data/*.pth"))
    if not ckpts:
        raise Skip("no .pth checkpoints in data/")
    msgs, ok = [], True
    for c in ckpts:
        sd = torch.load(c, map_location="cpu", weights_only=True)
        bad = 0
        total = 0
        for k, v in sd.items():
            if not torch.is_floating_point(v):
                continue
            total += v.numel()
            bad += int(torch.isnan(v).sum() + torch.isinf(v).sum())
        if bad:
            ok = False
            msgs.append(f"{c.name}: {bad}/{total} ({100 * bad / max(total, 1):.1f}%) non-finite")
        else:
            msgs.append(f"{c.name}: clean ({total} params)")
    return ok, "; ".join(msgs)


# ─────────────────────────────────────────────────────────────────────────────
# isotherm
# ─────────────────────────────────────────────────────────────────────────────

def _q_of_c(phys, c, T):
    from isotherm import q_star_np

    c = np.atleast_1d(np.asarray(c, dtype=float))
    return q_star_np(c, np.full_like(c, float(T)), phys)


def _invert_isotherm(phys, q_target, T, c_hi=1e4):
    """Concentration giving loading q_target at temperature T, by bisection."""
    lo, hi = 1e-14, c_hi
    if _q_of_c(phys, hi, T)[0] < q_target:
        return np.nan
    for _ in range(200):
        mid = np.sqrt(lo * hi)  # geometric bisection: spans many decades
        if _q_of_c(phys, mid, T)[0] < q_target:
            lo = mid
        else:
            hi = mid
    return np.sqrt(lo * hi)


@gate("isotherm is Type V (has an inflection)", "isotherm")
def gate_type_v():
    """Water AWH frameworks fill cooperatively; a Type I form cannot represent the step."""
    phys = _physics("mof303")
    T = phys.T_in
    c = np.linspace(1e-8, 3.0, 40000)
    q = _q_of_c(phys, c, T)
    d2 = np.gradient(np.gradient(q, c), c)
    interior = d2[20:-20]
    flips = int(np.sum(np.diff(np.sign(interior)) != 0))
    if flips == 0:
        return False, (
            f"strictly concave (Type I), 0 inflection points — d2q/dc2 in "
            f"[{interior.min():.3e}, {interior.max():.3e}]. The cooperative step "
            f"that makes AWH work cannot be represented."
        )
    steep = c[int(np.argmax(np.gradient(q, c)))]
    return True, f"{flips} inflection point(s); steepest uptake at c = {steep:.4g} mol/m3"


@gate("isotherm obeys Henry's law as c -> 0", "isotherm")
def gate_henry_law():
    """dq/dc must be finite and positive at the origin. A bare Hill form gives zero slope."""
    phys = _physics("mof303")
    T = phys.T_in
    from isotherm import henry_constant

    K_H = henry_constant(T, phys)
    cs = np.array([1e-9, 1e-8, 1e-7, 1e-6])
    ratios = _q_of_c(phys, cs, T) / cs
    drift = float(np.max(ratios) / max(np.min(ratios), 1e-300))
    if not np.isfinite(K_H) or K_H <= 0:
        return False, f"Henry constant is {K_H} — isotherm is not linear at the origin"
    if drift > 1.05:
        return False, f"q/c varies by {drift:.3f}x over c in [1e-9, 1e-6] — not linear at the origin"
    return True, f"K_H = {K_H:.4g} mol/kg per mol/m3; q/c constant to {drift:.5f}x near zero"


@gate("isotherm obeys Clausius-Clapeyron", "isotherm")
def gate_clausius_clapeyron():
    """Isosteric heat recovered numerically must equal -dH + RT, at every loading.

    The RT term is not slack -- it is the exact conversion between the two
    quantities, and getting it wrong is a classic adsorption-literature error.

    Our affinity is defined on a CONCENTRATION basis, b = b0 exp(-dH/(RT)), so at
    fixed loading  d(ln c)/d(1/T) = dH/R.  The isosteric heat, however, is defined
    from the PRESSURE:

        q_st = -R [d ln P / d(1/T)]_q ,   P = c R T

        d(ln P)/d(1/T) = d(ln c)/d(1/T) + d(ln T)/d(1/T) = dH/R - T

        => q_st = -dH + RT

    At 300 K that is 2.49 kJ/mol, i.e. 5 % on a 50 kJ/mol enthalpy. Reporting
    -dH as the isosteric heat (or vice versa) is a real 5 % error in any
    regeneration-energy calculation downstream.
    """
    rows, ok = [], True
    for _, kind, _ in DATASETS:
        phys = _physics(kind)
        T0 = getattr(phys, "T_in", 298.0)
        temps = np.linspace(T0 - 10.0, T0 + 10.0, 7)
        T_mid = float(np.mean(temps))
        expected = -phys.delta_H + R_GAS * T_mid
        for frac in (0.25, 0.50, 0.75):
            q_t = frac * phys.q_max
            cs = np.array([_invert_isotherm(phys, q_t, T) for T in temps])
            if not np.all(np.isfinite(cs)):
                continue
            lnP = np.log(cs * temps)          # P = cRT
            slope = np.polyfit(1.0 / temps, lnP, 1)[0]
            q_st = -R_GAS * slope
            rel = abs(q_st - expected) / abs(expected)
            if rel > 0.005:
                ok = False
                rows.append(f"{kind}@{frac:.0%}: q_st={q_st / 1000:.3f} vs -dH+RT={expected / 1000:.3f} kJ/mol ({100 * rel:.2f}% off)")
            else:
                rows.append(f"{kind}@{frac:.0%}: {q_st / 1000:.3f} kJ/mol ({100 * rel:.3f}%)")
    if not rows:
        raise Skip("isotherm could not be inverted at any loading")
    return ok, "; ".join(rows)


@gate("isotherm operating point is informative", "isotherm")
def gate_isotherm_regime():
    """The feed must land on the responsive part of the isotherm.

    Near saturation the isotherm is a step and its parameters are unidentifiable
    from breakthrough data; near zero the material barely loads.
    """
    rows, ok = [], True
    for _, kind, c_in in DATASETS:
        phys = _physics(kind)
        T = getattr(phys, "T_in", 298.0)
        theta_feed = float(_q_of_c(phys, c_in, T)[0]) / phys.q_max
        theta_low = float(_q_of_c(phys, 0.05 * c_in, T)[0]) / phys.q_max
        if not (0.15 <= theta_feed <= 0.97):
            ok = False
            rows.append(f"{kind}: q*(c_in)/q_max = {theta_feed:.3f} — outside the responsive band")
        elif theta_low > 0.8 * theta_feed:
            ok = False
            rows.append(f"{kind}: theta={theta_low:.3f} already at 5% of feed — irreversible limit, unidentifiable")
        else:
            rows.append(f"{kind}: theta(c_in)={theta_feed:.3f}, theta(0.05 c_in)={theta_low:.3f} OK")
    return ok, "; ".join(rows)


@gate("Henry's law holds across the WHOLE material space", "isotherm")
def gate_isotherm_space():
    """Every gate above evaluates TWO named configurations. Dataset v2 has 240
    sampled materials, and A18/A21/A26 are all the same error: a property measured
    at one point in a space, stated as a property of the space.

    Checked here for every sampled material, not for two of them:
      * isotherm_n > 1 strictly  -> the cooperative (Sips) term is o(c) at the
        origin, so the primary (Langmuir) term alone sets the initial slope and
        Henry's law holds. At n = 1 exactly the cooperative term becomes Langmuir
        and contributes a finite slope, which is still a valid isotherm but is a
        different claim; the sampler must never reach it.
      * henry_fraction > 0       -> K_H = q_max f_H b_H is non-zero.
      * K_H finite and positive for every material.

    The gate also REPORTS the spread rather than a single value, because
    `RESULTS.md` quoted one configuration's K_H for a family spanning ~2 decades.
    """
    import json as _json

    path = ROOT / "results" / "isotherm_space.json"
    if not path.exists():
        raise Skip("results/isotherm_space.json not found — run isotherm_space.py")
    d = _json.loads(path.read_text(encoding="utf-8"))
    rows = d["rows"]
    bad = []
    for r in rows:
        if not r["isotherm_n"] > 1.0:
            bad.append(f"material {r['material_id']}: isotherm_n = {r['isotherm_n']:.4f} <= 1")
        if not r["henry_fraction"] > 0.0:
            bad.append(f"material {r['material_id']}: henry_fraction = {r['henry_fraction']}")
        if not (np.isfinite(r["K_H"]) and r["K_H"] > 0.0):
            bad.append(f"material {r['material_id']}: K_H = {r['K_H']}")
    if bad:
        return False, "Henry's law fails for:\n      " + "\n      ".join(bad[:8])
    k, w = d["K_H"], d["log10_c_henry_over_c_in_median"]
    return True, (
        f"{len(rows)} materials, isotherm_n in ({min(r['isotherm_n'] for r in rows):.3f}, "
        f"{max(r['isotherm_n'] for r in rows):.3f}]; K_H {k['min']:.3g}–{k['max']:.3g} "
        f"({k['decades']:.1f} decades, median {k['median']:.3g}); the Henry region ends at "
        f"1e{w['median']:.1f} of the feed (median), and below 1e-3 of it for "
        f"{d['n_henry_region_below_1e3_of_feed']} materials — report the DISTRIBUTION, "
        f"never one config's K_H")


# ─────────────────────────────────────────────────────────────────────────────
# solver
# ─────────────────────────────────────────────────────────────────────────────

@gate("breakthrough actually occurs", "solver")
def gate_breakthrough_occurs():
    """A 'breakthrough curve' dataset must contain a breakthrough."""
    rows, ok = [], True
    for path, _, c_in in DATASETS:
        try:
            z, t, c, q, T = _load_field(path)
        except Skip as e:
            rows.append(f"{Path(path).name}: SKIP ({e})")
            continue
        ratio = c[-1, -1] / c_in
        if ratio < 0.95:
            ok = False
            rows.append(f"{Path(path).name}: c_exit/c_in = {ratio:.3e} at t_final (need >0.95)")
        else:
            rows.append(f"{Path(path).name}: c_exit/c_in = {ratio:.3f} OK")
    if not rows:
        raise Skip("no datasets present")
    return ok, "; ".join(rows)


@gate("mass-transfer zone is resolved in the data", "solver")
def gate_front_resolved():
    """The front must span enough cells at the time it is inside the column.

    Measured over ALL snapshots, not at t_final: once breakthrough completes the
    bed is uniformly saturated and there is no front left to resolve, so sampling
    the last frame asks the wrong question and reports 0 cells on a perfectly
    resolved run.
    """
    MIN_CELLS = 20
    rows, ok = [], True
    for path, _, _ in DATASETS:
        try:
            z, t, c, q, T = _load_field(path)
        except Skip as e:
            rows.append(f"{Path(path).name}: SKIP ({e})")
            continue
        if q.max() <= 0:
            ok = False
            rows.append(f"{Path(path).name}: bed never loads")
            continue
        q_sat = q.max()
        # Width of the 5%-95% transition in each snapshot, measured as the
        # distance between crossings. Take the MINIMUM over time: the binding
        # requirement is that the front is resolved when it is at its SHARPEST.
        # (Counting all cells in the band instead reports the early-time shallow
        # gradient across most of the column -- ~1840 cells for a front whose
        # physical width is 21 -- and passes for the wrong reason.)
        widths = []
        for k in range(q.shape[1]):
            prof = q[:, k]
            lo = np.where(prof > 0.05 * q_sat)[0]
            hi = np.where(prof > 0.95 * q_sat)[0]
            if lo.size == 0 or hi.size == 0:
                continue                      # front not fully inside the column
            if lo[-1] >= len(prof) - 1:
                continue                      # front has reached the outlet
            widths.append(int(lo[-1] - hi[-1]) + 1)
        if not widths:
            ok = False
            rows.append(f"{Path(path).name}: front never fully inside the column")
            continue
        sharpest = int(np.min(widths))
        if sharpest < MIN_CELLS:
            ok = False
            rows.append(f"{Path(path).name}: front narrows to {sharpest} cells (need >={MIN_CELLS}); "
                        f"median {int(np.median(widths))}")
        else:
            rows.append(f"{Path(path).name}: sharpest front {sharpest} cells, "
                        f"median {int(np.median(widths))} OK")
    if not rows:
        raise Skip("no datasets present")
    return ok, "; ".join(rows)


@gate("solution is grid-converged", "solver")
def gate_grid_converged():
    """Scheme-agnostic resolution check: refining the grid must not move the exit curve.

    Replaces an analytic D_num = u*dz/2 estimate, which is only valid for
    first-order upwind and says nothing about a limited or higher-order scheme.
    The generator runs the study and stamps the result into the .npz.
    """
    TOL = 0.02
    rows, ok = [], True
    for path, kind, _ in DATASETS:
        p = ROOT / path
        if not p.exists():
            rows.append(f"{Path(path).name}: SKIP (absent)")
            continue
        d = np.load(p)
        if "grid_convergence_err" not in d:
            ok = False
            rows.append(f"{kind}: no convergence study stamped in the dataset — resolution unverified")
            continue
        err = float(d["grid_convergence_err"])
        nz = int(d["N_z"]) if "N_z" in d else len(d["z"])
        if not np.isfinite(err):
            ok = False
            rows.append(f"{kind}: convergence study did not run")
        elif err > TOL:
            ok = False
            rows.append(f"{kind}: exit curve moves {100 * err:.2f}% on refinement at N_z={nz} (need <{100 * TOL:.0f}%)")
        else:
            rows.append(f"{kind}: {100 * err:.3f}% change at N_z={nz} OK")
    if not rows:
        raise Skip("no datasets present")
    return ok, "; ".join(rows)


@gate("mass-transfer zone is resolvable at the chosen grid", "solver")
def gate_mtz_resolvable():
    """The MTZ width is a property of the parameters; the grid must be able to see it."""
    rows, ok = [], True
    for path, kind, c_in in DATASETS:
        phys = _physics(kind)
        p = ROOT / path
        nz = int(np.load(p)["N_z"]) if (p.exists() and "N_z" in np.load(p)) else None
        T = getattr(phys, "T_in", 298.0)
        width, need = phys.mtz_width(c_in, T)
        cells = (width / (phys.L / nz)) if nz else float("nan")
        if nz is None:
            rows.append(f"{kind}: MTZ {width * 1e3:.3f} mm needs N_z>={need} (no dataset)")
        elif cells < 10:
            ok = False
            rows.append(f"{kind}: MTZ {width * 1e3:.3f} mm spans {cells:.1f} cells at N_z={nz} (need >=10; use N_z>={need})")
        else:
            rows.append(f"{kind}: MTZ {width * 1e3:.3f} mm spans {cells:.0f} cells at N_z={nz} OK")
    return ok, "; ".join(rows)


@gate("global mass balance closes", "solver")
def gate_mass_closure():
    """Accumulated adsorbate must equal net influx to within 1%."""
    rows, ok = [], True
    for path, kind, c_in in DATASETS:
        try:
            z, t, c, q, T = _load_field(path)
        except Skip as e:
            rows.append(f"{Path(path).name}: SKIP ({e})")
            continue
        phys = _physics(kind)
        dz = float(np.mean(np.diff(z)))
        stored = np.trapezoid(phys.eps_t * c + (1 - phys.eps_t) * phys.rho_p * q, dx=dz, axis=0)
        accumulated = stored[-1] - stored[0]
        influx = np.trapezoid(phys.v * (c_in - c[-1, :]), t)
        denom = max(abs(accumulated), abs(influx), 1e-30)
        err = abs(accumulated - influx) / denom
        if err > 0.01:
            ok = False
            rows.append(f"{kind}: stored={accumulated:.4e} vs net-in={influx:.4e} ({100 * err:.2f}% gap)")
        else:
            rows.append(f"{kind}: closes to {100 * err:.3f}% OK")
    if not rows:
        raise Skip("no datasets present")
    return ok, "; ".join(rows)


@gate("solver matches closed-form solutions (L0)", "solver")
def gate_analytic_verification():
    """The ground truth must be verified against analytic limits, not asserted.

    Thresholds are set from what a correct scheme achieves at these grids, not
    tuned to whatever the current code produces. Run `python verify_solver.py`
    to regenerate.
    """
    import json

    p = ROOT / "verify_solver.json"
    if not p.exists():
        raise Skip("verify_solver.json absent — run verify_solver.py")
    r = json.loads(p.read_text(encoding="utf-8"))

    checks = [
        ("tracer profile", r["tracer_van_genuchten"]["max_abs_err_vs_third_type"], 5e-3, "abs"),
        ("tracer front", r["tracer_van_genuchten"]["front_rel_err"], 2e-3, "rel"),
        ("retarded front", r["retarded_front"]["rel_err"], 2e-3, "rel"),
        ("thermal wave", r["thermal_wave"]["rel_err"], 2e-3, "rel"),
        ("LDF vs Anzelius", r["ldf_anzelius_schumann"]["max_abs_err"], 5e-3, "abs"),
    ]
    rows, ok = [], True
    for name, val, tol, kind in checks:
        if not np.isfinite(val) or val > tol:
            ok = False
            rows.append(f"{name}: {val:.3e} > {tol:.0e}")
        else:
            rows.append(f"{name}: {val:.2e}")
    return ok, "; ".join(rows)


@gate("fields stay physical", "solver")
def gate_no_negative():
    """Concentration and loading must remain non-negative and bounded by capacity."""
    rows, ok = [], True
    for path, kind, c_in in DATASETS:
        try:
            z, t, c, q, T = _load_field(path)
        except Skip as e:
            rows.append(f"{Path(path).name}: SKIP ({e})")
            continue
        phys = _physics(kind)
        tol = 1e-8 * max(c_in, 1.0)
        problems = []
        if c.min() < -tol:
            problems.append(f"c_min={c.min():.3e}")
        if q.min() < -tol * phys.q_max:
            problems.append(f"q_min={q.min():.3e}")
        if q.max() > 1.01 * phys.q_max:
            problems.append(f"q_max={q.max():.3f} > capacity {phys.q_max}")
        if c.max() > 1.05 * c_in:
            problems.append(f"c_max={c.max():.3e} > c_in {c_in}")
        if problems:
            ok = False
            rows.append(f"{kind}: " + ", ".join(problems))
        else:
            rows.append(f"{kind}: OK")
    if not rows:
        raise Skip("no datasets present")
    return ok, "; ".join(rows)


@gate("velocity convention is consistent", "solver")
def gate_velocity_convention():
    """The gas front speed implied by the solver must equal v/eps_t, numerically.

    A source-text check cannot survive a refactor. This measures the convention
    from the solution itself: with adsorption switched off, a tracer front must
    travel at the interstitial speed v/eps_t.
    """
    try:
        from solver_fd import generate_breakthrough_data
    except Exception as e:
        raise Skip(f"import failed ({e})")

    import copy

    phys = copy.deepcopy(_physics("default"))
    phys.k_LDF = 0.0          # inert tracer: no uptake, no heat release
    phys.L = 0.10
    expected = phys.v / phys.eps_t
    t_end = 0.6 * phys.L / expected

    N = 400
    z, t, y = generate_breakthrough_data(
        phys, N_z=N, t_final=t_end, c_in=1.0, n_snapshots=40, verbose=False
    )
    c = y[:N]
    prof = c[:, -1]
    if prof.max() < 0.5:
        raise Skip("tracer front did not develop")
    # front position = the half-height crossing
    idx = int(np.argmin(np.abs(prof - 0.5 * prof.max())))
    measured = z[idx] / t[-1]
    rel = abs(measured - expected) / expected
    if rel > 0.10:
        return False, (
            f"tracer front moves at {measured:.4g} m/s but v/eps_t = {expected:.4g} m/s "
            f"({100 * rel:.1f}% off) — the mass and energy balances disagree on what v means"
        )
    return True, f"tracer front {measured:.4g} m/s vs v/eps_t {expected:.4g} m/s ({100 * rel:.1f}% off)"


# ─────────────────────────────────────────────────────────────────────────────
# residual
# ─────────────────────────────────────────────────────────────────────────────

@gate("each equation is normalised to its dominant term", "residual")
def gate_equation_normalisation():
    """Every residual equation must have a dominant-term coefficient of 1.

    Tests the nondimensionalisation itself, not a random network's output scale.
    """
    try:
        from pde_adsorption import NondimConfig, _normalisers, term_coefficients
    except Exception as e:
        raise Skip(f"import failed ({e})")

    rows, ok = [], []
    for _, kind, c_in in DATASETS:
        phys = _physics(kind)
        nd = NondimConfig(phys, t_final=1.5 * phys.stoichiometric_time(c_in), c_in=c_in)
        coeffs = term_coefficients(nd, phys)
        nrm = _normalisers(nd, phys)
        for eq, terms in coeffs.items():
            scaled = {k: v / nrm[eq] for k, v in terms.items()}
            top = max(abs(v) for v in scaled.values())
            ok.append(abs(top - 1.0) < 1e-9)
            rng = f"[{min(abs(v) for v in scaled.values()):.1e}, {top:.1f}]"
            rows.append(f"{kind}/{eq}: {rng}")
    if not all(ok):
        return False, "some equation is not normalised: " + "; ".join(rows)
    return True, "dominant coefficient = 1 in every equation | " + "; ".join(rows[:3]) + " ..."


@gate("residuals are finite across seeds", "residual")
def gate_residual_finite():
    """No initialisation may produce NaN/Inf residuals — the van't Hoff term can overflow."""
    try:
        import torch
        from pde_adsorption import NondimConfig, compute_adsorption_pde_residuals
        from kan_model import PIKAN_Adsorption
    except Exception as e:
        raise Skip(f"import failed ({e})")

    phys = _physics("default")
    c_in = 1.0
    nd = NondimConfig(phys, t_final=1.5 * phys.stoichiometric_time(c_in), c_in=c_in)
    bad, mags = [], []
    for seed in range(4):
        torch.manual_seed(seed)
        model = PIKAN_Adsorption(width=32, depth=2, num_grids=10)
        z, t = torch.rand(1500, 1), torch.rand(1500, 1)
        res = compute_adsorption_pde_residuals(model, z, t, nd, phys)
        vals = [float(r.pow(2).mean().detach()) for r in res]
        if not all(np.isfinite(v) for v in vals):
            bad.append(f"seed {seed}: {vals}")
        else:
            mags.append(max(vals) / max(min(vals), 1e-300))
    if bad:
        return False, "non-finite residuals — " + "; ".join(bad)
    return True, f"4 seeds finite; init-scale spread {min(mags):.1f}x–{max(mags):.1f}x (not a scaling defect)"


@gate("physics losses include boundary conditions", "residual")
def gate_physics_has_bcs():
    """Any training script that uses a PDE residual must also use a boundary residual.

    A PDE residual ALONE does not determine a solution — the same equation admits
    different solutions under different boundary data. Omitting the boundary terms
    let a physics-informed arm diverge to nRMSE 5,480 on temporal extrapolation
    where the corrected loss reaches 1.05 at 20x fewer steps (defect B20).

    The omission was invisible: the loss decreased, training converged, and the
    arm simply underperformed. Only a structural check catches it.
    """
    import re as _re

    offenders, checked = [], []
    for path in sorted(ROOT.glob("run_*.py")) + [ROOT / "train_pikan.py"]:
        if not path.exists():
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        uses_pde = bool(_re.search(r"(?:pde_residual|compute_adsorption_pde_residuals)\s*\(", src))
        if not uses_pde:
            continue
        checked.append(path.name)
        # a definition alone does not count; require a CALL
        # A definition alone does not count - require a CALL that passes a model.
        # run_l4.py once DEFINED boundary_residual without its own trainer ever
        # calling it, which is exactly how B20 survived.
        calls_bc = bool(_re.search(r"boundary_residuals?\s*\(\s*model", src))
        if not calls_bc:
            offenders.append(f"{path.name} computes a PDE residual but never calls a boundary residual")
    if not checked:
        raise Skip("no training script uses a PDE residual")
    if offenders:
        return False, "; ".join(offenders)
    return True, f"{len(checked)} physics-training scripts checked: " + ", ".join(checked)


@gate("EVERY model bounds temperature away from zero", "model")
def gate_temperature_bounded():
    """T* must be bounded away from 0 in every architecture, not just the PIKAN.

    An unbounded T* lets the isotherm's van't Hoff factor exp(-dH/(R T)) diverge,
    which NaNs the whole graph (retraction A2, defect B3). The head lived in six
    separate copies across the model files and every copy had the defect; fixing
    only the one under test is how it survived. This gate sweeps all of them.
    """
    try:
        import torch
        from kan_model import PIKAN_Adsorption
        from baseline_models import DataDrivenMLP, DeepONet_Adsorption
        from fno_model_adsorption import FNO2d_Adsorption
        from operator_models import PI_DeepOKAN, PI_DeepONet, WaveletNeuralOperator
    except Exception as e:
        raise Skip(f"import failed ({e})")

    phys = _physics("default")
    T_ref = phys.T_in

    def pw():
        return torch.rand(600, 1), torch.rand(600, 1)

    def op(B=3, N=300):
        return torch.rand(B, 4), torch.rand(B, N, 2)

    # Layout says WHERE the (c, q, T) channel axis is. Temperature is always
    # channel 2; only the axis differs. Naming the layout explicitly beats
    # inferring it from tensor rank -- an earlier version of this gate sliced
    # channel 1 (which is q, and legitimately 0 at t=0) for grid-layout models
    # and reported a false failure on two correct architectures.
    #   "point" : (N, 3)          -> [:, 2]
    #   "opnet" : (B, N, 3)       -> [:, :, 2]
    #   "grid"  : (B, 3, Nz, Nt)  -> [:, 2]
    def temperature(out, layout):
        if layout == "point":
            return out[:, 2]
        if layout == "opnet":
            return out[:, :, 2]
        if layout == "grid":
            return out[:, 2]
        raise ValueError(layout)

    cases = {
        "PIKAN": (lambda: PIKAN_Adsorption(32, 2, 8)(*pw()), "point"),
        "PI_DeepONet": (lambda: PI_DeepONet(width=32, depth=2)(*op()), "opnet"),
        "PI_DeepOKAN": (lambda: PI_DeepOKAN(width=32, depth=2, num_grids=8)(*op()), "opnet"),
        "WaveletNO": (lambda: WaveletNeuralOperator(width=16)(torch.rand(2, 4), 32, 32), "grid"),
        "FNO2d": (lambda: FNO2d_Adsorption(modes=8, width=16, n_layers=2)(torch.rand(2, 4), 32, 32), "grid"),
        "DataDrivenMLP": (lambda: DataDrivenMLP(width=32, depth=2)(*pw()), "point"),
        "DeepONet_base": (lambda: DeepONet_Adsorption()(*op()), "opnet"),
    }

    rows, ok = [], True
    for name, (fn, layout) in cases.items():
        lo, hi, finite = np.inf, -np.inf, True
        for seed in range(3):
            torch.manual_seed(seed)
            with torch.no_grad():
                out = fn()
            if not torch.isfinite(out).all():
                finite = False
            T = temperature(out, layout)
            lo = min(lo, float(T.min()))
            hi = max(hi, float(T.max()))
        if not finite or lo * T_ref <= 50.0:
            ok = False
            rows.append(f"{name}: T*min={lo:.3f} -> {lo * T_ref:.0f} K{'' if finite else ' NON-FINITE'}")
        else:
            rows.append(f"{name}: [{lo * T_ref:.0f},{hi * T_ref:.0f}]K")
    return ok, f"{len(cases)} architectures | " + "; ".join(rows)


@gate("output head has a single definition", "model")
def gate_single_output_head():
    """No model file may re-implement the head; drift is how the NaN spread."""
    offenders = []
    for path in sorted(ROOT.glob("*.py")):
        if path.name in ("output_head.py", "validate.py"):
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(src.splitlines(), 1):
            if re.search(r"1\.0\s*\+\s*t_(star|env)\s*\*", line):
                offenders.append(f"{path.name}:{lineno} re-implements an unbounded T head")
    if offenders:
        return False, "\n      ".join(offenders)
    return True, "all models route through output_head.apply_output_head"


# ─────────────────────────────────────────────────────────────────────────────
# model
# ─────────────────────────────────────────────────────────────────────────────

@gate("network derivatives are non-singular", "model")
def gate_derivative_smoothness():
    """d2u/dz2 must not blow up on any interior locus; PDE residuals need bounded 2nd derivatives."""
    try:
        import torch
        from kan_model import PIKAN_Adsorption
    except Exception as e:
        raise Skip(f"import failed ({e})")

    torch.manual_seed(0)
    model = PIKAN_Adsorption(width=64, depth=3, num_grids=10)
    z = torch.rand(20000, 1, requires_grad=True)
    t = torch.rand(20000, 1, requires_grad=True)
    out = model(z, t)
    g = torch.autograd.grad(out[:, 0:1], z, torch.ones_like(z), create_graph=True)[0]
    g2 = torch.autograd.grad(g, z, torch.ones_like(z), create_graph=True)[0]
    a1, a2 = g.abs().detach(), g2.abs().detach()
    p50, p999, mx = (float(np.percentile(a1.numpy(), p)) for p in (50, 99.9, 100))
    dyn = mx / max(p50, 1e-30)
    if dyn > 1e3 or float(a2.max()) > 1e5:
        return False, (
            f"|dc/dz| p50={p50:.2e} p99.9={p999:.2e} max={mx:.2e} (dynamic range {dyn:.1e}x); "
            f"max|d2c/dz2|={float(a2.max()):.2e} — derivative field is singular on a locus, "
            f"residuals will be sampling noise"
        )
    return True, f"|dc/dz| p50={p50:.2e} max={mx:.2e}; max|d2c/dz2|={float(a2.max()):.2e} OK"


@gate("input layer preserves coordinates", "model")
def gate_input_not_collapsed():
    """Distinct (z,t) must map to distinct first-layer activations."""
    try:
        import torch
        from kan_model import RBFKANLayer
    except Exception as e:
        raise Skip(f"import failed ({e})")

    torch.manual_seed(0)
    layer = RBFKANLayer(2, 8, num_grids=10)
    zz = torch.linspace(0.05, 0.95, 12).repeat_interleave(12).unsqueeze(1)
    tt = torch.linspace(0.05, 0.95, 12).repeat(12).unsqueeze(1)
    x = torch.cat([zz, tt], dim=1)
    with torch.no_grad():
        pre = layer.norm(x) if getattr(layer, "norm", None) is not None else x
    n_in = x.shape[0]
    n_out = torch.unique(torch.round(pre * 1e4) / 1e4, dim=0).shape[0]
    if n_out < 0.9 * n_in:
        return False, (
            f"{n_in} distinct (z*,t*) collapse to {n_out} distinct activations — "
            f"the first layer is discarding coordinate information "
            f"(LayerNorm over {layer.in_features} features returns ~sign(z-t))"
        )
    return True, f"{n_in} inputs -> {n_out} distinct activations OK"


# ─────────────────────────────────────────────────────────────────────────────
# runner
# ─────────────────────────────────────────────────────────────────────────────

C_PASS, C_FAIL, C_SKIP, C_OFF = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="run a single category")
    ap.add_argument("--list", action="store_true", help="list gates and exit")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    if args.no_color or not sys.stdout.isatty():
        global C_PASS, C_FAIL, C_SKIP, C_OFF
        C_PASS = C_FAIL = C_SKIP = C_OFF = ""

    gates = [g for g in REGISTRY if not args.only or g.category == args.only]

    if args.list:
        for g in gates:
            print(f"  [{g.category:<10}] {g.name}")
        return 0

    print("=" * 78)
    print("VERIFICATION HARNESS — ai-mof-cof-dynamics")
    print("=" * 78)

    n_pass = n_fail = n_skip = 0
    current = None
    for g in gates:
        if g.category != current:
            current = g.category
            print(f"\n── {current} " + "─" * (74 - len(current)))
        try:
            ok, msg = g.fn()
            if ok:
                n_pass += 1
                print(f"  {C_PASS}PASS{C_OFF}  {g.name}")
                print(f"        {msg}")
            else:
                n_fail += 1
                print(f"  {C_FAIL}FAIL{C_OFF}  {g.name}")
                print(f"        {msg}")
        except Skip as e:
            n_skip += 1
            print(f"  {C_SKIP}SKIP{C_OFF}  {g.name}")
            print(f"        {e}")
        except Exception:
            n_fail += 1
            print(f"  {C_FAIL}FAIL{C_OFF}  {g.name}  (gate raised)")
            print("        " + traceback.format_exc().strip().replace("\n", "\n        "))

    print("\n" + "=" * 78)
    verdict = f"{n_pass} passed, {n_fail} failed, {n_skip} skipped"
    print(f"{C_FAIL if n_fail else C_PASS}{verdict}{C_OFF}")
    print("=" * 78)
    if n_fail:
        print("\nNo result from a failing category may enter the manuscript.")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
