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
import ast
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
    except ImportError as e:  # pragma: no cover -- ImportError only: a broken module must FAIL
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
    (r"copy\s*\(\s*\w*_true\s*\)", "a 'prediction' built by copying ground truth"),
    (r"\bhallucinat", "a hand-authored 'failure' curve"),
    (r"placeholder logic", "acknowledged placeholder left in a plotting path"),
]

# Noise generators (audit_hygiene #16). The old pattern was `np.random.normal(...)$`,
# anchored to end of line, so A1's actual shape `c_true + np.random.normal(0, 1e-3, n)`
# followed by anything -- or `np.random.normal(...) + c_true` -- escaped, and randn /
# rand / uniform / default_rng().normal() were not covered at all. No anchor now, and
# a Generator bound to a name (`rng = np.random.default_rng(s); rng.normal(...)`, the
# commonest idiom) is caught through that name. Only sampling methods that DRAW
# VALUES are listed; choice/permutation/integers index data and cannot fake a series.
_NOISE_METHODS = r"(?:randn|rand|uniform|normal|standard_normal|random)"
_NOISE_PATTERNS = [
    (r"np\.random\.(?:randn|rand|uniform|normal)\s*\(", "np.random noise draw"),
    (r"default_rng\s*\([^)]*\)\s*\.\s*" + _NOISE_METHODS + r"\s*\(", "default_rng(...) noise draw"),
]
_RNG_BINDING = re.compile(r"\b(\w+)\s*=\s*(?:np\.random\.)?(?:default_rng|RandomState|Generator)\s*\(")

# Directories the recursive scan does not enter, each with its reason. kaggle_run/
# (the "stale duplicate carrying every original defect", retraction A7) is NOT here:
# it was deleted from the tree, and if it ever reappears it is scanned.
_SCAN_SKIP_DIRS = {
    ".venv": "third-party virtualenv", ".git": "VCS metadata",
    "node_modules": "third-party", "site-packages": "third-party",
    "__pycache__": "bytecode",
    # tests/ build synthetic fixtures ON PURPOSE: test_p2.py and test_odr_bindy.py add
    # observation noise to a known truth to check that a method RECOVERS it. That is
    # the fabrication pattern by construction, produces no reported number and no
    # figure, and is the only way to test an estimator. Read 2026-09-28.
    "tests": "unit-test fixtures add noise to a known truth to test recovery",
}

# Per-file allow-list for noise draws: file -> (exact number of flagged lines, reason).
# The count is exact so that a NEW noise draw added to an allowed file is not waved
# through -- it changes the count and the gate asks for the file to be re-read.
# Every entry below was read line by line on 2026-09-28; none adds noise to a model
# or solver output that is then reported or plotted as a result.
_NOISE_ALLOWED = {
    "audit_l1.py": (3, "Monte-Carlo calibration of the L1 paired-CI procedure on SYNTHETIC "
                       "arms of known effect; it tests the statistic, reports no model number"),
    "calibrate_ci.py": (3, "coverage calibration of the paired CI on simulated arms of known "
                           "effect (the statistic is under test, not a model)"),
    "calibrate_v2.py": (3, "the same CI-coverage calibration for the v2 design: simulated arms "
                           "with a planted effect, to measure coverage"),
    "p2_pilot_m7.py": (2, "PREREG_P2 M7 inclusion gate: 0.5 % observation noise on a KNOWN-ANSWER "
                          "LDF system (q and the measured q*), to test whether PySR recovers the "
                          "planted law; never the confirmatory grid, reports no model result"),
    "mde.py": (2, "minimum-detectable-effect power simulation: draws synthetic between/within-"
                  "material variation to size the design, reports no model result"),
    "metrics.py": (3, "the module's self-test builds synthetic ArmResults of known ordering to "
                      "check the paired statistic; no model output is touched"),
    "cost_accounting.py": (4, "random INPUT tensors to time a forward pass (FLOP/latency "
                              "accounting); the values are never reported, only the wall time"),
    "gen_parametric_dataset.py": (2, "uniform sampling of the material/condition DESIGN space "
                                     "that the solver is then run on; inputs, not outputs"),
}


def _scan_py_files():
    """All tracked-tree .py files under ROOT, recursively, minus _SCAN_SKIP_DIRS."""
    out = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if any(part in _SCAN_SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if rel.as_posix() == "validate.py":
            continue
        out.append(path)
    return out


def _noise_lines(src):
    """Line numbers of every noise draw in `src` (see _NOISE_PATTERNS)."""
    names = sorted({m.group(1) for m in _RNG_BINDING.finditer(src)})
    pats = [p for p, _ in _NOISE_PATTERNS]
    if names:
        pats.append(r"\b(?:" + "|".join(map(re.escape, names)) + r")\s*\.\s*"
                    + _NOISE_METHODS + r"\s*\(")
    hits = []
    for lineno, line in enumerate(src.splitlines(), 1):
        code = line.split("#", 1)[0]
        if any(re.search(p, code) for p in pats):
            hits.append(lineno)
    return hits


@gate("plotting code computes its curves", "integrity")
def gate_no_fabricated_curves():
    """No script may synthesise a series it reports as a model prediction.

    The scan is recursive and covers every script, not only plotting ones: A7's
    fabricated SINDy input was never plotted -- it was regressed on. Noise draws are
    admitted only through _NOISE_ALLOWED, per file, with a reason and an exact count.
    """
    offenders, allowed_seen = [], []
    for path in _scan_py_files():
        rel = path.relative_to(ROOT).as_posix()
        src = path.read_text(encoding="utf-8", errors="replace")
        if "matplotlib" in src or "plt." in src:
            for lineno, line in enumerate(src.splitlines(), 1):
                for pat, why in _FABRICATION_PATTERNS:
                    if re.search(pat, line, re.IGNORECASE):
                        offenders.append(f"{rel}:{lineno} — {why}")
        noise = _noise_lines(src)
        if not noise:
            continue
        allowed = _NOISE_ALLOWED.get(rel)
        if allowed and allowed[0] == len(noise):
            allowed_seen.append(rel)
            continue
        where = ", ".join(map(str, noise[:8]))
        if allowed:
            offenders.append(f"{rel}: {len(noise)} noise draw(s) at lines {where}, but the allow-list "
                             f"reviewed {allowed[0]} — re-read the file and update _NOISE_ALLOWED")
        else:
            offenders.append(f"{rel}: noise draw(s) at lines {where} — synthetic noise can fake a "
                             f"series; justify in _NOISE_ALLOWED or remove")
    stale = sorted(set(_NOISE_ALLOWED) - set(allowed_seen)
                   - {o.split(":", 1)[0] for o in offenders})
    if stale:
        offenders.append("stale _NOISE_ALLOWED entries (file gone or no longer draws noise): "
                         + ", ".join(stale))
    if offenders:
        return False, "figures must come from a model:\n      " + "\n      ".join(offenders)
    return True, (f"no synthesised series found ({len(allowed_seen)} files draw noise under a "
                  f"reviewed allow-list entry)")


# A plotting script may not invent a model series. There are FOUR legitimate
# provenances (A, B here; C SOLVER and D DIGITISED in the gate body) and it admits only those:
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
_RESULTS_LIT = re.compile(r"^(results/[\w./-]+\.json|verify_solver\.json)$")

# Calls that READ a file. A results path counts as provenance only if it reaches one
# of these (audit_hygiene #10): a quoted filename in a docstring or comment, or in an
# unused variable, is an assertion, not proof.
_READ_CALLS = {"open", "load", "loads", "read_text", "read_bytes", "fromfile", "loadtxt",
               "genfromtxt", "read_csv", "read_json", "read_parquet", "read_pickle",
               "read_table", "read_excel"}


def _ast_parse(src):
    """ast.parse without echoing the parsed file's own SyntaxWarnings (e.g. '\\|')."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        return ast.parse(src)


def _call_name(node):
    f = node.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


def _is_write_open(call):
    """open(p, "w") / open(p, mode="a") / Path.open("w") writes; it proves nothing read."""
    mode = None
    if _call_name(call) == "open":
        args = call.args[1:] if isinstance(call.func, ast.Name) else call.args[:1]
        if args and isinstance(args[0], ast.Constant):
            mode = args[0].value
        for kw in call.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                mode = kw.value.value
    return isinstance(mode, str) and any(ch in mode for ch in "wax")


def _loaded_results_paths(src):
    """Results paths in `src` that provably reach a file-reading call whose value is used.

    Flow-insensitive taint over NAMES: a literal assigned to a name (directly or inside
    a list/tuple/join/f-string) taints that name, and a for-loop over a tainted iterable
    taints its target. A path counts once a read call -- or a function defined in the
    same file whose body contains a read call (fig_ladder's `load` helper) -- takes the
    literal or a tainted name among its arguments, and that call is not a bare
    expression statement (its result is used). Returns None if the file does not parse.
    """
    try:
        tree = _ast_parse(src)
    except SyntaxError:
        return None
    parent = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            parent[ch] = node

    def lits(node):
        return {n.value for n in ast.walk(node)
                if isinstance(n, ast.Constant) and isinstance(n.value, str) and _RESULTS_LIT.match(n.value)}

    def names(node):
        return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}

    reader_funcs = set(_READ_CALLS)
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(isinstance(c, ast.Call) and _call_name(c) in _READ_CALLS and not _is_write_open(c)
                   for c in ast.walk(fn)):
                reader_funcs.add(fn.name)

    taint = {}  # name -> set of results paths it may carry
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and node.value is not None:
                carried = lits(node.value).union(*[taint.get(n, set()) for n in names(node.value)])
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            elif isinstance(node, (ast.For, ast.comprehension)):
                carried = lits(node.iter).union(*[taint.get(n, set()) for n in names(node.iter)])
                targets = [node.target]
            else:
                continue
            if not carried:
                continue
            for t in targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name) and not carried <= taint.get(n.id, set()):
                        taint.setdefault(n.id, set()).update(carried)
                        changed = True

    loaded = set()
    for call in ast.walk(tree):
        if not (isinstance(call, ast.Call) and _call_name(call) in reader_funcs) or _is_write_open(call):
            continue
        # the result must be used: climb to the outermost enclosing call chain and
        # reject a bare expression statement such as `open("results/x.json")`.
        top = call
        while isinstance(parent.get(top), (ast.Call, ast.Attribute, ast.Subscript, ast.keyword)):
            top = parent[top]
        if isinstance(parent.get(top), ast.Expr):
            continue
        argnodes = list(call.args) + [k.value for k in call.keywords]
        if isinstance(call.func, ast.Attribute):
            argnodes.append(call.func.value)   # Path("results/x.json").read_text()
        for a in argnodes:
            loaded |= lits(a)
            for n in names(a):
                loaded |= taint.get(n, set())
    return loaded


def _calls_load_state_dict(src):
    """True iff `load_state_dict` is a real ast.Call, not a word in a comment or docstring."""
    try:
        tree = _ast_parse(src)
    except SyntaxError:
        return False
    return any(isinstance(n, ast.Call) and _call_name(n) == "load_state_dict" for n in ast.walk(tree))


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
        # "EVERY" used to be implemented as a filename prefix plus a label keyword
        # list, which the anchor figure's own script escaped (audit_hygiene #9). The
        # trigger is now what the rule says: any script that SAVES a figure.
        draws_model = path.name.startswith("fig") or re.search(
            r"label\s*=\s*(?:rf|fr|[rbfu])?[\"'][^\"']*(PIKAN|MLP|DeepONet|FNO|WNO|DeepOKAN|POD)",
            src, re.I)
        if not (draws_model or "savefig" in src):
            continue
        if _calls_load_state_dict(src):   # a CALL, not a substring (audit_hygiene #10)
            ok.append(f"{path.name}: checkpoint")
            continue
        learned = [why for pat, why in _MODEL_MACHINERY if re.search(pat, src)]
        if not draws_model and not learned:
            # Two further provenances, admitted only for a script that draws no model
            # curve and holds no learning machinery: (C) SOLVER -- it runs the verified
            # reference solver itself; (D) DIGITISED -- it plots a published figure's
            # digitised points from refs/.
            if re.search(r"\bgenerate_breakthrough_data\s*\(", src):
                ok.append(f"{path.name}: solver")
                continue
            if re.search(r"[\"']refs/[\w./-]+\.(csv|png)[\"']", src):
                ok.append(f"{path.name}: digitised")
                continue
        machinery = [why for pat, why in _MODEL_MACHINERY if re.search(pat, src)]
        # Only paths that provably reach a read call count (audit_hygiene #10); a
        # path merely quoted somewhere in the file is an assertion.
        loaded = _loaded_results_paths(src)
        if loaded is None:
            bad.append(f"{path.name} — does not parse, so its provenance cannot be proven")
            continue
        named = sorted(loaded)
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
                       f"nor reads a results file (a path must reach open/json.load/np.load/..., "
                       f"not merely be quoted)")
        elif missing:
            bad.append(f"{path.name} — reads model series from files that do not exist: "
                       + ", ".join(missing))
        else:
            ok.append(f"{path.name}: recorded ({len(named)} file{'s' if len(named) > 1 else ''}"
                      + (f", {len(pending)} pending" if pending else "") + ")")
    if bad:
        return False, "\n      ".join(bad)
    return True, "model curves come from a checkpoint or a recorded results file — " + "; ".join(ok)


@gate("the manuscript contains no hand-typed number", "integrity")
def gate_manuscript_numbers():
    """Every numeral in the manuscript must be a macro resolved from a results file,
    or a literal declared in build_paper.ALLOWED with a written reason.

    B21 and B43 are the same defect at two scales: a number reached a document with
    no script behind it. B43's was the quantitative basis of a retraction. This gate
    makes the manuscript the one document where that cannot happen silently.
    """
    tex = ROOT / "paper" / "manuscript.tex"
    if not tex.exists():
        raise Skip("paper/manuscript.tex not written yet")
    try:
        sys.path.insert(0, str(ROOT))
        import build_paper as bp
        import importlib
        importlib.reload(bp)
    except ImportError as e:  # a broken module must FAIL, not SKIP (audit_hygiene #14)
        raise Skip(f"cannot import build_paper ({e})")
    nums = ROOT / "paper" / "numbers.tex"
    if not nums.exists():
        raise Skip("paper/numbers.tex not built — run python paper/numbers.py")
    # numbers.json is read BEFORE the verdict (audit_hygiene #26): it used to be read
    # after the pass decision, unguarded, so an absent file became a raw-traceback
    # FAIL and a non-empty `pending` list became a suffix on a PASS -- a manuscript
    # with visible [PENDING] markers went green. numbers.py:39-40 says a manuscript
    # can never be finalised while any remain; this gate now enforces it.
    import json as _json
    nums_json = ROOT / "paper" / "numbers.json"
    if not nums_json.exists():
        raise Skip("paper/numbers.json not built — run python paper/numbers.py")
    pend = _json.loads(nums_json.read_text(encoding="utf-8")).get("pending", [])
    body =bp.body(tex.read_text(encoding="utf-8"))
    defined = set(bp.MACRO.findall(nums.read_text(encoding="utf-8")))
    used = set(bp.MACRO.findall(body))
    undefined = sorted(used - defined)
    hits = []
    for i, line in enumerate(body.splitlines(), 1):
        for m in bp.NUMERAL.finditer(bp.strip_structural(line)):
            if m.group(1) not in bp.ALLOWED:
                hits.append(f"line {i}: {m.group(1)}")
    # build_paper's third check (B64). It lived only in build_paper.main(), so this
    # gate -- the one rule 1 sends people to -- passed a manuscript of mangled macros.
    broken = bp.mangled(body, defined)
    # build_paper's fourth check: numbers written as words (paper/number_words.py).
    sys.path.insert(0, str(ROOT / "paper"))
    import number_words
    nw_unreviewed, nw_owed, _ = number_words.check(body, bp.strip_structural)
    if undefined or hits or broken or nw_unreviewed or pend:
        msg = []
        if pend:
            msg.append(f"{len(pend)} value(s) PENDING a run still in flight — the manuscript "
                       f"prints [PENDING] and cannot pass: " + ", ".join(
                           (p.get("key", "?") + " <- " + p.get("file", "?")) if isinstance(p, dict)
                           else str(p) for p in pend[:6]))
        if nw_unreviewed:
            msg.append(f"{len(nw_unreviewed)} unreviewed number-word(s): "
                       + "; ".join(k for _, _, k in nw_unreviewed[:4]))
        if broken:
            msg.append(f"{len(broken)} mangled macro(s): " + "; ".join(map(str, broken[:6])))
        if undefined:
            msg.append("undefined macros: " + ", ".join("\n" + u for u in undefined[:6]))
        if hits:
            msg.append(f"{len(hits)} undeclared numeral(s): " + "; ".join(hits[:6]))
        return False, " | ".join(msg)
    return True, (f"{len(used)} macros used, all resolved from results files; "
                  f"{len(bp.ALLOWED)} literals declared with reasons; 0 pending; "
                  f"{len(nw_owed)} measured quantities still OWED as words")


# ─────────────────────────────────────────────────────────────────────────────
# checkpoint
# ─────────────────────────────────────────────────────────────────────────────

@gate("checkpoint parameters are finite", "checkpoint")
def gate_checkpoint_finite():
    """A saved model must contain no NaN or Inf in any learnable tensor."""
    try:
        import torch
    except ImportError as e:  # a broken module must FAIL, not SKIP (audit_hygiene #14)
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


@gate("isotherm is S-shaped (has an inflection)", "isotherm")
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
    rows, ok, vals = [], True, {}
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
                # audit_hygiene #25: this used to `continue` silently, so a loading the
                # gate could not check still counted as a pass.
                ok = False
                rows.append(f"{kind}@{frac:.0%}: NOT INVERTIBLE -- loading unchecked")
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
            vals[f"{kind}@{frac:.2f}"] = float(rel)
    if not rows:
        raise Skip("isotherm could not be inverted at any loading")
    # structured, so the manuscript's "reproduced to 0.004 %" reads a number, not a string
    vals["max_rel_err"] = max(v for k, v in vals.items() if "@" in k) if vals else None
    return ok, "; ".join(rows), vals


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

def _missing_datasets(skipped, ok):
    """Rule 6: a gate whose data is absent has not passed.

    All datasets absent -> SKIP (the gate could not run). Some absent -> FAIL (a
    partial check must not report a whole PASS). Before 2026-09-25 each solver gate
    appended a 'SKIP' row and returned PASS, which on every fresh clone (the .npz
    files are gitignored) printed six green lines about data that was not there.
    """
    if skipped and len(skipped) == len(DATASETS):
        raise Skip("no dataset present: " + ", ".join(Path(p).name for p in skipped))
    return ok and not skipped

@gate("breakthrough actually occurs", "solver")
def gate_breakthrough_occurs():
    """A 'breakthrough curve' dataset must contain a breakthrough."""
    rows, ok, skipped = [], True, []
    for path, _, c_in in DATASETS:
        try:
            z, t, c, q, T = _load_field(path)
        except Skip as e:
            rows.append(f"{Path(path).name}: SKIP ({e})")
            skipped.append(path)
            continue
        ratio = c[-1, -1] / c_in
        if ratio < 0.95:
            ok = False
            rows.append(f"{Path(path).name}: c_exit/c_in = {ratio:.3e} at t_final (need >0.95)")
        else:
            rows.append(f"{Path(path).name}: c_exit/c_in = {ratio:.3f} OK")
    ok = _missing_datasets(skipped, ok)
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
    rows, ok, skipped = [], True, []
    for path, _, _ in DATASETS:
        try:
            z, t, c, q, T = _load_field(path)
        except Skip as e:
            rows.append(f"{Path(path).name}: SKIP ({e})")
            skipped.append(path)
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
    ok = _missing_datasets(skipped, ok)
    return ok, "; ".join(rows)


@gate("solution is grid-converged", "solver")
def gate_grid_converged():
    """Scheme-agnostic resolution check: refining the grid must not move the exit curve.

    Replaces an analytic D_num = u*dz/2 estimate, which is only valid for
    first-order upwind and says nothing about a limited or higher-order scheme.
    The generator runs the study and stamps the result into the .npz.
    """
    TOL = 0.02
    rows, ok, vals, skipped = [], True, {}, []
    for path, kind, _ in DATASETS:
        p = ROOT / path
        if not p.exists():
            rows.append(f"{Path(path).name}: SKIP (absent)")
            skipped.append(path)
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
        vals[kind] = {"err": float(err), "N_z": nz}
    ok = _missing_datasets(skipped, ok)
    return ok, "; ".join(rows), vals


@gate("mass-transfer zone is resolvable at the chosen grid", "solver")
def gate_mtz_resolvable():
    """The MTZ width is a property of the parameters; the grid must be able to see it."""
    rows, ok, skipped = [], True, []
    for path, kind, c_in in DATASETS:
        phys = _physics(kind)
        p = ROOT / path
        nz = int(np.load(p)["N_z"]) if (p.exists() and "N_z" in np.load(p)) else None
        T = getattr(phys, "T_in", 298.0)
        width, need = phys.mtz_width(c_in, T)
        cells = (width / (phys.L / nz)) if nz else float("nan")
        if nz is None:
            rows.append(f"{kind}: MTZ {width * 1e3:.3f} mm needs N_z>={need} (no dataset)")
            skipped.append(path)
        elif cells < 10:
            ok = False
            rows.append(f"{kind}: MTZ {width * 1e3:.3f} mm spans {cells:.1f} cells at N_z={nz} (need >=10; use N_z>={need})")
        else:
            rows.append(f"{kind}: MTZ {width * 1e3:.3f} mm spans {cells:.0f} cells at N_z={nz} OK")
    ok = _missing_datasets(skipped, ok)
    return ok, "; ".join(rows)


@gate("global mass balance closes", "solver")
def gate_mass_closure():
    """Accumulated adsorbate must equal net influx to within 1%."""
    rows, ok, vals, skipped = [], True, {}, []
    for path, kind, c_in in DATASETS:
        try:
            z, t, c, q, T = _load_field(path)
        except Skip as e:
            rows.append(f"{Path(path).name}: SKIP ({e})")
            skipped.append(path)
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
        vals[kind] = float(err)
    ok = _missing_datasets(skipped, ok)
    return ok, "; ".join(rows), vals


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
    rows, ok, skipped = [], True, []
    for path, kind, c_in in DATASETS:
        try:
            z, t, c, q, T = _load_field(path)
        except Skip as e:
            rows.append(f"{Path(path).name}: SKIP ({e})")
            skipped.append(path)
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
    ok = _missing_datasets(skipped, ok)
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
    except ImportError as e:  # a broken module must FAIL, not SKIP (audit_hygiene #14)
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
    except ImportError as e:  # a broken module must FAIL, not SKIP (audit_hygiene #14)
        raise Skip(f"import failed ({e})")

    # `checks` is a list of per-equation booleans, not a verdict. all([]) is True, so an
    # empty list used to PASS with an affirmative claim about zero equations
    # (audit_hygiene #24); it is now a SKIP.
    rows, checks = [], []
    for _, kind, c_in in DATASETS:
        phys = _physics(kind)
        nd = NondimConfig(phys, t_final=1.5 * phys.stoichiometric_time(c_in), c_in=c_in)
        coeffs = term_coefficients(nd, phys)
        nrm = _normalisers(nd, phys)
        for eq, terms in coeffs.items():
            scaled = {k: v / nrm[eq] for k, v in terms.items()}
            top = max(abs(v) for v in scaled.values())
            checks.append(abs(top - 1.0) < 1e-9)
            rng = f"[{min(abs(v) for v in scaled.values()):.1e}, {top:.1f}]"
            rows.append(f"{kind}/{eq}: {rng}")
    if not checks:
        raise Skip("no equations to check")
    if not all(checks):
        return False, "some equation is not normalised: " + "; ".join(rows)
    return True, (f"dominant coefficient = 1 in all {len(checks)} equations | "
                  + "; ".join(rows[:3]) + " ...")


@gate("the training residual is the solver's equation", "residual")
def gate_residual_matches_solver():
    """The physics residual L4 trains on must be the PDE the data were generated by.

    B72: for the life of the project the gas-mass residual advected at v instead of
    v/eps_t (and its inlet flux used 1/Pe instead of eps/Pe), so every physics-informed
    arm trained and refined against a front eps_t times too slow. The velocity gate
    above checked the SOLVER's convention; nothing checked the RESIDUAL against it.

    This probes the actual torch functions with fields whose derivatives are known
    (c = z, c = z^2/2, c = t, q = t), reads off each coefficient, and compares ratios
    with solver_fd.gas_coefficients on real v2 physics rows. Ratios make the check
    independent of how each equation is normalised.
    """
    try:
        import json as _json
        import torch
        from ladder_data import param_keys_for
        from run_l4 import boundary_residual, build_phys_table, pde_residual, physics_from_params
        from solver_fd import gas_coefficients
    except ImportError as e:  # a broken module must FAIL, not SKIP (audit_hygiene #14)
        raise Skip(f"import failed ({e})")
    man_path = ROOT / "data" / "parametric_v2" / "manifest.json"
    if not man_path.exists():
        raise Skip("dataset v2 manifest absent")
    man = _json.load(open(man_path))
    keys = param_keys_for(man)
    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    rows = man["samples"][:: max(1, len(man["samples"]) // 16)][:16]
    raw = np.array([[(mats[s["mat"]] if k in mats[s["mat"]] else conds[s["cond"]])[k] for k in keys]
                    for s in rows], float)
    t_final = np.array([s["t_final"] for s in rows], float)
    table = build_phys_table(raw, "cpu", keys)
    tau = torch.tensor(t_final, dtype=torch.float32).unsqueeze(1) / table["t_ref"]
    n = len(rows)

    class Probe(torch.nn.Module):
        def __init__(self, fc, fq, fT=None):
            super().__init__()
            self.fc, self.fq, self.fT = fc, fq, fT

        def forward(self, pz, z, t):
            # a zero-valued term in z and t keeps every input in the autograd graph
            # (a probe that ignores t would make d/dt undefined, not zero)
            g = 0.0 * (z * z * t * t)
            T = (self.fT(z, t) if self.fT else 1.0) + g
            return torch.cat([self.fc(z, t) + g, self.fq(z, t) + g, T], dim=1)

    zero = lambda z, t: 0.0 * z
    pz = torch.zeros(n, 11)
    z = torch.full((n, 1), 0.5)
    t = torch.full((n, 1), 0.5)

    def mass(fc, fq, zz=z):
        r, _, _ = pde_residual(Probe(fc, fq), pz, table, zz.clone(), t.clone(), tau)
        return r.detach().double().numpy().ravel()

    a_code = mass(lambda z, t: z, zero)                             # coef of dc/dz
    d_code = -mass(lambda z, t: 0.5 * z * z, zero, torch.zeros(n, 1))   # coef of d2c/dz2
    s_code = mass(lambda z, t: t, zero)                             # coef of dc/dt
    q_code = mass(zero, lambda z, t: t)                             # coef of dq/dt
    b0, _, _, _ = boundary_residual(Probe(lambda z, t: z, zero), pz, table, t.clone(), tau)
    bc_code = -(b0.detach().double().numpy().ravel() + 1.0)         # coef of dc/dz at the inlet
    _, bT, _, _ = boundary_residual(Probe(zero, zero, lambda z, t: z), pz, table, t.clone(), tau)
    bcT_code = -(bT.detach().double().numpy().ravel() + 1.0)        # coef of dT/dz at the inlet

    bad = []
    for i in range(n):
        p = physics_from_params(raw[i], keys)
        u_gas, src = gas_coefficients(p)
        c_in, qm = float(table["c_in"][i]), float(table["q_max"][i])
        sink = src * qm / t_final[i]                                  # dq/dt scale, per unit c
        want = {"advection/sink": u_gas * c_in / p.L / sink,
                "dispersion/sink": p.D_L * c_in / p.L ** 2 / sink,
                "accumulation/sink": c_in / t_final[i] / sink,
                "inlet dispersion": p.D_L / (u_gas * p.L),
                # solver: alpha_T = k_z/C_term, u_th = v rho_g C_pg/C_term, zero-flux inlet face
                "inlet conduction": p.k_z / (p.v * p.rho_g * p.C_pg * p.L)}
        got = {"advection/sink": a_code[i] / q_code[i], "dispersion/sink": d_code[i] / q_code[i],
               "accumulation/sink": s_code[i] / q_code[i], "inlet dispersion": bc_code[i],
               "inlet conduction": bcT_code[i]}
        for k in want:
            rel = abs(got[k] - want[k]) / abs(want[k])
            if rel > 1e-3:
                bad.append(f"row {i} {k}: residual {got[k]:.4g} vs solver {want[k]:.4g} ({100 * rel:.0f}% off)")
    if bad:
        return False, f"{len(bad)} coefficient(s) disagree with the solver: " + "; ".join(bad[:4])
    return True, (f"advection, dispersion, accumulation and both inlet-flux coefficients match "
                  f"solver_fd on {n} v2 physics rows (rel tol 1e-3)")


@gate("residuals are finite across seeds", "residual")
def gate_residual_finite():
    """No initialisation may produce NaN/Inf residuals — the van't Hoff term can overflow."""
    try:
        import torch
        from pde_adsorption import NondimConfig, compute_adsorption_pde_residuals
        from kan_model import PIKAN_Adsorption
    except ImportError as e:  # a broken module must FAIL, not SKIP (audit_hygiene #14)
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


_RESIDUAL_NAMES = {"pde": {"pde_residual", "compute_adsorption_pde_residuals"},
                   "bc": {"boundary_residual", "boundary_residuals"}}
_AST_CACHE = {}


def _parse_root_module(stem):
    """ast of ROOT/<stem>.py, or None if absent or unparsable (cached)."""
    if stem not in _AST_CACHE:
        p = ROOT / f"{stem}.py"
        try:
            _AST_CACHE[stem] = _ast_parse(p.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError):
            _AST_CACHE[stem] = None
    return _AST_CACHE[stem]


def _live_calls(node):
    """Every ast.Call under `node`, skipping bodies of constant-false `if`/`while`
    (`if False:` / `if 0:`), which are dead code however they read."""
    out, stack = [], [node]
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.If, ast.While)) and isinstance(n.test, ast.Constant) and not n.test.value:
            stack.extend(n.orelse)
            continue
        if isinstance(n, ast.Call):
            out.append(n)
        stack.extend(ast.iter_child_nodes(n))
    return out


def _imports(tree):
    """(from-imports {local: (module, original)}, module imports {local: module})."""
    names, mods = {}, {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            for a in n.names:
                names[a.asname or a.name] = (n.module, a.name)
        elif isinstance(n, ast.Import):
            for a in n.names:
                mods[a.asname or a.name.split(".")[0]] = a.name
    return names, mods


def _calls_resolve_to(stem, calls, kind, seen):
    """True if any call in `calls` (inside module `stem`) resolves to a `kind` residual,
    directly, through an import alias, or through a helper defined in `stem` or in
    another root module (followed transitively, cycle-safe)."""
    tree = _parse_root_module(stem)
    if tree is None:
        return False
    names, mods = _imports(tree)
    local_defs = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for c in calls:
        f = c.func
        if isinstance(f, ast.Name):
            orig = names.get(f.id, (None, f.id))[1]
            if orig in _RESIDUAL_NAMES[kind] or f.id in _RESIDUAL_NAMES[kind]:
                return True
            if f.id in local_defs and _func_calls(stem, f.id, kind, seen):
                return True
            if f.id in names and _func_calls(names[f.id][0], names[f.id][1], kind, seen):
                return True
        elif isinstance(f, ast.Attribute):
            if f.attr in _RESIDUAL_NAMES[kind]:
                return True
            if isinstance(f.value, ast.Name) and f.value.id in mods \
                    and _func_calls(mods[f.value.id], f.attr, kind, seen):
                return True
    return False


def _func_calls(stem, fname, kind, seen):
    """Does function `fname` defined at top level of root module `stem` call a `kind` residual?"""
    key = (stem, fname)
    if key in seen or "." in stem:
        return False
    seen = seen | {key}
    tree = _parse_root_module(stem)
    if tree is None:
        return False
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == fname:
            return _calls_resolve_to(stem, _live_calls(n), kind, seen)
    return False


def _module_calls(stem, kind):
    """Does root module `stem` contain a live call that resolves to a `kind` residual?"""
    tree = _parse_root_module(stem)
    return tree is not None and _calls_resolve_to(stem, _live_calls(tree), kind, frozenset())


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
    # Selection is by BEHAVIOUR, not filename (audit_hygiene #15): the old glob
    # `run_*.py + train_pikan.py` never saw refine_*/sweep scripts, which train with a
    # PDE residual exactly where B20 would recur. Every root script that trains
    # (an ast call to .backward() or .step()) is examined; residual calls are resolved
    # through ast, so `from pde_adsorption import compute_adsorption_pde_residuals as r`
    # and helpers imported from other root modules (refine_* call run_l4b_v2's
    # physics_terms, which calls both residuals) are followed.
    offenders, checked = [], []
    for path in sorted(ROOT.glob("*.py")):
        if path.name == "validate.py":
            continue
        tree = _parse_root_module(path.stem)
        if tree is None or not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                                   and n.func.attr in ("backward", "step") for n in ast.walk(tree)):
            continue
        uses_pde = _module_calls(path.stem, "pde")
        if not uses_pde:
            continue
        checked.append(path.name)
        # A definition alone does not count - require a live CALL (not under a
        # constant-false branch). run_l4.py once DEFINED boundary_residual without
        # its own trainer ever calling it, which is exactly how B20 survived.
        if not _module_calls(path.stem, "bc"):
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
    except ImportError as e:  # a broken module must FAIL, not SKIP (audit_hygiene #14)
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
    except ImportError as e:  # a broken module must FAIL, not SKIP (audit_hygiene #14)
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
    except ImportError as e:  # a broken module must FAIL, not SKIP (audit_hygiene #14)
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
    ap.add_argument("--json", nargs="?", const="results/validation.json", default=None,
                    help="write every gate's verdict AND its evidence string to JSON. "
                         "The manuscript reads numbers like the mass-closure and "
                         "grid-convergence percentages from here; before this existed "
                         "they were quoted from a terminal log, which is B43's defect.")
    args = ap.parse_args()

    if args.no_color or not sys.stdout.isatty():
        global C_PASS, C_FAIL, C_SKIP, C_OFF
        C_PASS = C_FAIL = C_SKIP = C_OFF = ""

    cats = sorted({g.category for g in REGISTRY})
    if args.only and args.only not in cats:
        # A typo used to select zero gates and exit 0: a green hook that ran nothing.
        print(f"--only {args.only!r} is not a category; valid: {', '.join(cats)}")
        return 2
    if args.only and args.json == "results/validation.json":
        # The authoritative record is a FULL run. A partial run written there made
        # nGates report a third of the harness (audit_hygiene #8).
        args.json = f"results/validation_{args.only}.json"
    gates = [g for g in REGISTRY if not args.only or g.category == args.only]

    if args.list:
        for g in gates:
            print(f"  [{g.category:<10}] {g.name}")
        return 0

    print("=" * 78)
    print("VERIFICATION HARNESS — ai-mof-cof-dynamics")
    print("=" * 78)

    n_pass = n_fail = n_skip = 0
    records = []
    current = None
    for g in gates:
        if g.category != current:
            current = g.category
            print(f"\n── {current} " + "─" * (74 - len(current)))
        try:
            res = g.fn()
            ok, msg, vals = (res if len(res) == 3 else (res[0], res[1], None))
            rec = {"gate": g.name, "category": g.category,
                   "state": "PASS" if ok else "FAIL", "evidence": msg}
            if vals:
                # Structured values for paper/numbers.py. Parsing them back out of the
                # evidence STRING would be exactly the fragility this project keeps
                # finding, so a gate that carries a manuscript number emits it as data.
                rec["values"] = vals
            records.append(rec)
            if ok:
                n_pass += 1
                print(f"  {C_PASS}PASS{C_OFF}  {g.name}")
                print(f"        {msg}")
            else:
                n_fail += 1
                print(f"  {C_FAIL}FAIL{C_OFF}  {g.name}")
                print(f"        {msg}")
        except Skip as e:
            records.append({"gate": g.name, "category": g.category,
                            "state": "SKIP", "evidence": str(e)})
            n_skip += 1
            print(f"  {C_SKIP}SKIP{C_OFF}  {g.name}")
            print(f"        {e}")
        except Exception:
            records.append({"gate": g.name, "category": g.category,
                            "state": "FAIL", "evidence": traceback.format_exc().strip()})
            n_fail += 1
            print(f"  {C_FAIL}FAIL{C_OFF}  {g.name}  (gate raised)")
            print("        " + traceback.format_exc().strip().replace("\n", "\n        "))

    print("\n" + "=" * 78)
    verdict = f"{n_pass} passed, {n_fail} failed, {n_skip} skipped"
    print(f"{C_FAIL if n_fail else C_PASS}{verdict}{C_OFF}")
    print("=" * 78)
    if args.json:
        import json as _json

        out = {"n_gates": len(records), "n_pass": n_pass, "n_fail": n_fail, "n_skip": n_skip,
               "only": args.only, "gates": records,
               "by_gate": {r["gate"]: r for r in records}}
        path = ROOT / args.json
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_json.dumps(out, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}  ({len(records)} gates"
              + (f", {args.only} only — NOT a full record" if args.only else "") + ")")
    if n_fail:
        print("\nNo result from a failing category may enter the manuscript.")
    if n_pass == 0:
        print("\nNo gate passed -- a run that verified nothing is not a success.")
        return 1
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
