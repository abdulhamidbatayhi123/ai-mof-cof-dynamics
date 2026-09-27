# Paper 2 Harness — Phase A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A tested core for Paper 2 — derivative estimation, the Lib-B feature library, the pre-registered success metric, three discovery methods (exact best-subset M4, STLSQ/weak-form SINDy M2, ensemble SINDy M3) and profile-likelihood identifiability — each verified on a case with a known answer, before the prereg freeze.

**Architecture:** One package `p2/` with one responsibility per file. Every method has the signature `fit(features: dict[str, ndarray], target: ndarray) -> dict[str, float]` (term name → coefficient; absent = not selected), so the metric and the cell runner never depend on the method. Data enter only through `p2_observe.observe()` (already selftested). Tests use a synthetic LDF ODE whose law is exact, so a correct method must recover it at zero noise.

**Tech Stack:** Python 3.12 in `.venv` (inherits numpy 2.4, scipy 1.17, scikit-learn 1.8; adds pysindy 2.1), pytest.

**Spec:** `PREREG_P2_discoverability.md` §3 (methods), §4.3 (metrics). Phase B (M1 UDE, M5 EIV ports, M6 SINDy-PI, M7 PySR, M8 KANDy, M9 slow-manifold, the cell runner, the analysis) gets its own plan after Phase A passes.

**Hard rule:** no test or script in this plan reads `data/p2/` through a discovery method. The confirmatory grid is touched only after the `FREEZE PREREG_P2` commit.

---

## File structure

| file | responsibility |
|---|---|
| `p2/__init__.py` | empty package marker |
| `p2/synthetic.py` | a known-answer LDF system for tests (never used on the grid) |
| `p2/features.py` | derivative estimation; Lib-B construction from an observation |
| `p2/metric.py` | the pre-registered success and accuracy definitions |
| `p2/methods.py` | M4 exact best-subset, M2 STLSQ + weak-form, M3 ensemble |
| `p2/identifiability.py` | profile likelihood of k with the true law known |
| `tests/test_p2.py` | all Phase A tests |

---

### Task 1: Known-answer system

**Files:** Create `p2/__init__.py`, `p2/synthetic.py`, `tests/test_p2.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_p2.py
import numpy as np
from p2.synthetic import ldf_series

def test_ldf_series_obeys_its_law():
    s = ldf_series(k=0.02, n=400, seed=0)
    dq = np.gradient(s["q"], s["t"])
    resid = dq - 0.02 * (s["qstar"] - s["q"])
    assert np.max(np.abs(resid[5:-5])) < 1e-3 * np.max(np.abs(dq))
```

- [ ] **Step 2: Run to verify it fails**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_p2.py::test_ldf_series_obeys_its_law -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'p2'`

- [ ] **Step 3: Implement**

```python
# p2/__init__.py
```

```python
# p2/synthetic.py
"""A known-answer LDF system: dq/dt = k (q*(c) - q), c(t) a smooth breakthrough ramp,
q*(c) Langmuir. Used ONLY by tests, never on the confirmatory grid."""
import numpy as np
from scipy.integrate import solve_ivp


def ldf_series(k, n=400, seed=0, t_end=600.0, qmax=5.0, b=3.0):
    t = np.linspace(0.0, t_end, n)
    c_of = lambda tt: 1.0 / (1.0 + np.exp(-(tt - 0.4 * t_end) / (0.05 * t_end)))
    qs_of = lambda cc: qmax * b * cc / (1.0 + b * cc)
    sol = solve_ivp(lambda tt, q: k * (qs_of(c_of(tt)) - q), (0, t_end), [0.0],
                    t_eval=t, rtol=1e-10, atol=1e-12)
    c = c_of(t)
    return {"t": t, "c": c, "q": sol.y[0], "T": np.full(n, 298.0), "qstar": qs_of(c)}
```

- [ ] **Step 4: Run to verify it passes** — same command. Expected: PASS
- [ ] **Step 5: Commit** — `git add p2/ tests/test_p2.py && git commit -m "p2: known-answer LDF system for harness tests"`

### Task 2: Features — derivative and Lib-B

**Files:** Create `p2/features.py`; Modify `tests/test_p2.py`

- [ ] **Step 1: Failing test**

```python
from p2.features import derivative, lib_b

def test_derivative_exact_on_smooth_series():
    t = np.linspace(0, 10, 500); y = np.sin(t)
    assert np.max(np.abs(derivative(y, t)[10:-10] - np.cos(t)[10:-10])) < 1e-3

def test_lib_b_contains_measured_equilibrium_and_named_terms():
    s = ldf_series(k=0.02)
    F = lib_b(s["c"], s["q"], s["T"], s["qstar"])
    assert set(F) == {"1", "c", "q", "T", "c*q", "q^2", "c^2", "qstar"}
    assert np.allclose(F["qstar"], s["qstar"])
```

- [ ] **Step 2: Run** — Expected FAIL (no module `p2.features`)
- [ ] **Step 3: Implement**

```python
# p2/features.py
"""Derivative estimation and the equilibrium-informed library Lib-B (PREREG §3).
q* here is ALWAYS the measured equilibrium the method is given, never the truth."""
import numpy as np
from scipy.signal import savgol_filter


def derivative(y, t, window=21, order=3):
    """Savitzky-Golay derivative on a uniform grid (p2_observe samples uniformly)."""
    dt = float(t[1] - t[0])
    w = min(window, (len(y) // 2) * 2 - 1)
    return savgol_filter(y, w, min(order, w - 1), deriv=1, delta=dt)


def lib_b(c, q, T, qstar):
    return {"1": np.ones_like(c), "c": c, "q": q, "T": T, "c*q": c * q,
            "q^2": q ** 2, "c^2": c ** 2, "qstar": qstar}
```

- [ ] **Step 4: Run** — Expected PASS
- [ ] **Step 5: Commit** — `git commit -am "p2: derivative estimation and Lib-B"` (add the new file first)

### Task 3: The pre-registered metric

**Files:** Create `p2/metric.py`; Modify `tests/test_p2.py`

- [ ] **Step 1: Failing test**

```python
from p2.metric import success_L1, k_accuracy

def test_success_requires_exact_support_signs_and_ratio():
    assert success_L1({"qstar": 0.02, "q": -0.02})
    assert not success_L1({"qstar": 0.02, "q": -0.02, "c": 1e-6})   # extra term
    assert not success_L1({"qstar": -0.02, "q": 0.02})             # wrong signs
    assert not success_L1({"qstar": 0.02, "q": -0.03})             # ratio off by 50 %
    assert success_L1({"qstar": 0.02, "q": -0.0215})               # ratio within 10 %

def test_k_accuracy_is_relative_error_of_minus_q_coefficient():
    assert abs(k_accuracy({"qstar": 0.02, "q": -0.022}, 0.02) - 0.1) < 1e-12
```

- [ ] **Step 2: Run** — Expected FAIL
- [ ] **Step 3: Implement**

```python
# p2/metric.py
"""PREREG_P2 §4.3. Success (primary): support == {qstar, q} exactly, qstar coefficient
> 0, q coefficient < 0, and -coef(q)/coef(qstar) within 10 % of 1.
Accuracy (secondary): |k_hat - k| / k with k_hat = -coef(q)."""


def success_L1(coefs, ratio_tol=0.10):
    sel = {k for k, v in coefs.items() if v != 0.0}
    if sel != {"qstar", "q"}:
        return False
    a, b = coefs["qstar"], coefs["q"]
    return a > 0 and b < 0 and abs(-b / a - 1.0) <= ratio_tol


def k_accuracy(coefs, k_true):
    return abs(-coefs.get("q", 0.0) - k_true) / k_true
```

- [ ] **Step 4: Run** — PASS
- [ ] **Step 5: Commit** — `git commit -m "p2: pre-registered success and accuracy metrics"`

### Task 4: M4 exact best-subset with constraints

**Files:** Create `p2/methods.py`; Modify `tests/test_p2.py`

- [ ] **Step 1: Failing test**

```python
from p2.methods import best_subset

def _fit_on(k, sigma=0.0, seed=0):
    s = ldf_series(k=k, seed=seed)
    q = s["q"] + np.random.default_rng(seed).normal(scale=sigma * np.ptp(s["q"]), size=s["q"].size)
    F = lib_b(s["c"], q, s["T"], s["qstar"])
    return F, derivative(q, s["t"])

def test_best_subset_recovers_ldf_at_zero_noise():
    F, y = _fit_on(0.02)
    coefs = best_subset(F, y, max_terms=4)
    assert success_L1(coefs) and k_accuracy(coefs, 0.02) < 0.02
```

- [ ] **Step 2: Run** — FAIL
- [ ] **Step 3: Implement**

```python
# p2/methods.py
"""Discovery methods, each fit(features, target) -> {term: coefficient}.

M4 best_subset: exhaustive enumeration of every support up to max_terms, least
squares on standardised columns, selection by BIC. This solves the MIOSR objective
EXACTLY (the library is small), without a Gurobi licence."""
import itertools
import numpy as np


def _standardise(F):
    names = list(F)
    X = np.column_stack([F[n] for n in names]).astype(float)
    sd = X.std(0)
    sd[sd == 0] = 1.0            # the constant column keeps scale 1
    return names, X / sd, sd


def best_subset(F, y, max_terms=4):
    names, Xs, sd = _standardise(F)
    n = len(y)
    best, best_bic = None, np.inf
    for m in range(1, max_terms + 1):
        for S in itertools.combinations(range(len(names)), m):
            A = Xs[:, S]
            beta, *_ = np.linalg.lstsq(A, y, rcond=None)
            rss = float(np.sum((y - A @ beta) ** 2))
            bic = n * np.log(max(rss, 1e-300) / n) + m * np.log(n)
            if bic < best_bic:
                best_bic, best = bic, (S, beta)
    S, beta = best
    return {names[j]: float(b / sd[j]) for j, b in zip(S, beta)}
```

- [ ] **Step 4: Run** — PASS. If it FAILS at zero noise, the derivative estimator or library is wrong — fix those, never loosen the test.
- [ ] **Step 5: Commit** — `git commit -m "p2: M4 exact best-subset (MIOSR objective solved by enumeration)"`

### Task 5: M2 (STLSQ and weak-form) and M3 (ensemble) via pysindy

**Files:** Modify `p2/methods.py`, `tests/test_p2.py`

- [ ] **Step 1: Failing test**

```python
from p2.methods import stlsq, ensemble

def test_stlsq_and_ensemble_recover_ldf_at_zero_noise():
    F, y = _fit_on(0.02)
    for fit in (stlsq, ensemble):
        coefs = fit(F, y)
        assert success_L1(coefs), (fit.__name__, coefs)
```

- [ ] **Step 2: Run** — FAIL
- [ ] **Step 3: Implement** (append to `p2/methods.py`)

```python
def stlsq(F, y, threshold=0.05, alpha=1e-6):
    """M2 strong-form: sequentially thresholded least squares on standardised columns
    (the column standardisation the original script lacked -- 03_LADDER_PROTOCOL.md).
    Threshold is on standardised coefficients relative to the largest."""
    names, Xs, sd = _standardise(F)
    keep = np.ones(len(names), bool)
    for _ in range(20):
        beta = np.zeros(len(names))
        A = Xs[:, keep]
        beta[keep] = np.linalg.solve(A.T @ A + alpha * np.eye(A.shape[1]), A.T @ y)
        new = np.abs(beta) >= threshold * np.abs(beta).max()
        if (new == keep).all():
            break
        keep = new
    return {names[j]: float(beta[j] / sd[j]) for j in range(len(names)) if keep[j]}


def ensemble(F, y, n_models=100, frac=0.6, threshold=0.05, inclusion=0.6, seed=0):
    """M3 bagged STLSQ (E-SINDy): terms kept if selected in >= `inclusion` of bootstrap
    fits; coefficients are medians over the fits that selected them. The inclusion
    probability of each term is the per-cell uncertainty metric PREREG §3 names."""
    rng = np.random.default_rng(seed)
    n = len(y)
    fits = []
    for _ in range(n_models):
        idx = rng.choice(n, int(frac * n), replace=True)
        fits.append(stlsq({k: v[idx] for k, v in F.items()}, y[idx], threshold))
    out = {}
    for name in F:
        vals = [f[name] for f in fits if name in f]
        if len(vals) / n_models >= inclusion:
            out[name] = float(np.median(vals))
    return out
```

The weak-form variant (M2b) uses `pysindy.WeakPDELibrary`; it is added in Phase B with its own known-answer test, because its interface takes the raw time series rather than a precomputed derivative.

- [ ] **Step 4: Run** — PASS
- [ ] **Step 5: Commit** — `git commit -m "p2: M2 STLSQ and M3 ensemble, known-answer verified"`

### Task 6: Profile-likelihood identifiability

**Files:** Create `p2/identifiability.py`; Modify `tests/test_p2.py`

- [ ] **Step 1: Failing test**

```python
from p2.identifiability import profile_interval

def test_profile_interval_brackets_truth_and_is_narrow_at_low_noise():
    s = ldf_series(k=0.02)
    rng = np.random.default_rng(1)
    q_obs = s["q"] + rng.normal(scale=0.005 * np.ptp(s["q"]), size=s["q"].size)
    lo, hi = profile_interval(s["t"], s["c"], q_obs, lambda c: 5.0 * 3.0 * c / (1 + 3.0 * c),
                              sigma=0.005 * np.ptp(s["q"]))
    assert lo < 0.02 < hi and hi / lo < 1.5
```

- [ ] **Step 2: Run** — FAIL
- [ ] **Step 3: Implement**

```python
# p2/identifiability.py
"""Profile likelihood of k with the LDF law KNOWN (PREREG §4.3): the classical
practical-identifiability test the discovery boundary is compared against. For each k
on a log grid, integrate dq/dt = k (q*(c(t)) - q) with c(t) interpolated from data,
Gaussian log-likelihood against observed q; the 95 % interval is where
2 * (max loglik - loglik) <= 3.84. 'Practically identifiable' iff the interval lies
within [k/2, 2k]."""
import numpy as np
from scipy.integrate import solve_ivp


def _loglik(k, t, c, q_obs, qstar_fn, sigma):
    sol = solve_ivp(lambda tt, q: k * (qstar_fn(np.interp(tt, t, c)) - q), (t[0], t[-1]),
                    [q_obs[0]], t_eval=t, rtol=1e-8, atol=1e-10)
    if not sol.success:
        return -np.inf
    return -0.5 * np.sum((sol.y[0] - q_obs) ** 2) / sigma ** 2


def profile_interval(t, c, q_obs, qstar_fn, sigma, k_grid=None):
    k_grid = np.logspace(-5, 1, 241) if k_grid is None else k_grid
    ll = np.array([_loglik(k, t, c, q_obs, qstar_fn, sigma) for k in k_grid])
    ok = 2.0 * (ll.max() - ll) <= 3.84
    return float(k_grid[ok].min()), float(k_grid[ok].max())


def identifiable(lo, hi, k_true):
    return lo >= k_true / 2 and hi <= 2 * k_true
```

- [ ] **Step 4: Run** — PASS
- [ ] **Step 5: Commit** — `git commit -m "p2: profile-likelihood identifiability, known-answer verified"`

### Task 7: Phase A gate

- [ ] **Step 1:** Run all: `./.venv/Scripts/python.exe -m pytest tests/test_p2.py -v` — Expected: 8 passed.
- [ ] **Step 2:** Add to `PREREG_P2_discoverability.md` §3 a line recording that M2 (strong form), M3, M4 and the identifiability tool are implemented and pass known-answer tests (commit hash), and that Phase B remains.
- [ ] **Step 3:** Commit — `git commit -am "p2 phase A complete: harness core verified on known answers"`
