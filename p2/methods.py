"""Discovery methods, each fit(features, target) -> {term: coefficient}.

M4 best_subset: exhaustive enumeration of every support up to max_terms, least squares
on standardised columns, selection by BIC. Solves the MIOSR objective EXACTLY (the
library is small), without a Gurobi licence.
M2 stlsq: sequentially thresholded least squares on standardised columns.
M3 ensemble: bagged STLSQ (E-SINDy) with per-term inclusion probabilities."""
import itertools

import numpy as np


def _standardise(F):
    names = list(F)
    X = np.column_stack([F[n] for n in names]).astype(float)
    sd = X.std(0)
    sd[sd == 0] = 1.0            # the constant column keeps scale 1
    return names, X / sd, sd


def best_subset(F, y, max_terms=4, floor=1e-3):
    """BIC with a residual-variance FLOOR at `floor` x std(y). Found on the known-answer
    test: at zero noise plain BIC keeps terms of relative size ~1e-4 (c, q^2) because it
    rewards fitting the derivative estimator's own systematic error without limit. The
    floor is the Savitzky-Golay estimator's verified accuracy (test_derivative_...),
    so no support can be bought by fitting below what the derivative can resolve."""
    names, Xs, sd = _standardise(F)
    n = len(y)
    var_floor = (floor * float(np.std(y))) ** 2
    best, best_bic = None, np.inf
    for m in range(1, max_terms + 1):
        for S in itertools.combinations(range(len(names)), m):
            A = Xs[:, S]
            beta, *_ = np.linalg.lstsq(A, y, rcond=None)
            rss = float(np.sum((y - A @ beta) ** 2))
            bic = n * np.log(max(rss / n, var_floor)) + m * np.log(n)
            if bic < best_bic:
                best_bic, best = bic, (S, beta)
    S, beta = best
    return {names[j]: float(b / sd[j]) for j, b in zip(S, beta)}


def stlsq(F, y, threshold=0.05, alpha=1e-6):
    """Threshold is on standardised coefficients relative to the largest."""
    names, Xs, sd = _standardise(F)
    keep = np.ones(len(names), bool)
    beta = np.zeros(len(names))
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


def slow_manifold(F_alg, q, max_terms=3):
    """M9: regress the STATE q (not its rate) on q-free features. Near local
    equilibrium the bed lies on the slow manifold q = q*(c, T); what is discoverable
    there is that algebraic law, not k. Exact best-subset on the algebraic problem."""
    return best_subset(F_alg, np.asarray(q, float), max_terms=max_terms)


def sindy_pi(F, dq, max_terms=5):
    """M6, SINDy-PI (Kaheman, Kutz & Brunton 2020, S21): implicit discovery for RATIONAL
    laws, run with the agnostic library and NO measured isotherm (isothermal control
    only -- PREREG_P2 §3: exp(-dH/RT) is not polynomial). The library is augmented with
    dq/dt and its products with c and q; each dq-containing term is tried as the
    left-hand side, fitted by exact best-subset on the rest, and the candidate with the
    smallest relative residual wins. Returned normalised so the dq coefficient is 1:
    {term: coefficient} of the implicit relation  sum coef * term = 0."""
    aug = dict(F)
    aug["dq"] = dq
    aug["c*dq"] = F["c"] * dq
    aug["q*dq"] = F["q"] * dq
    best = None
    for lhs in ("dq", "c*dq", "q*dq"):
        rest = {k: v for k, v in aug.items() if k != lhs}
        co = best_subset(rest, aug[lhs], max_terms=max_terms)
        pred = sum(co[k] * rest[k] for k in co)
        rel = float(np.linalg.norm(aug[lhs] - pred) / np.linalg.norm(aug[lhs]))
        if best is None or rel < best[0]:
            best = (rel, lhs, co)
    _, lhs, co = best
    rel_coefs = {lhs: 1.0, **{k: -v for k, v in co.items()}}
    if "dq" not in rel_coefs:
        return lhs, rel_coefs                   # no dq term: not a rate law
    s = rel_coefs["dq"]
    return lhs, {k: v / s for k, v in rel_coefs.items()}


def kan_symbolic(V, y, seed=0, steps=100, lamb=1e-3):
    """M8: Kolmogorov-Arnold network + symbolic extraction (Liu et al.'s procedure,
    pykan 0.2.8). Takes the RAW variables V = {c, q, T, qstar}, not a pre-expanded
    polynomial library: a KAN edge learns any univariate function, so q^2 with a
    square-root edge IS q and an expanded library is redundant to it (found on the
    known-answer test: it routed the law through q^2). Fit [n -> 1] on standardised
    inputs with a sparsity penalty, snap every edge to {x, x^2, 0}, read the formula
    back in the original variables. Labelled as KAN symbolic extraction -- NOT a
    reimplementation of KANDy (S48), whose code was not opened. Secondary (L3, S49).
    Needs several distinct trajectories (the grid gives 20 probes per cell): along a
    single trajectory dq/dt is a function of q alone and nothing identifies q*."""
    import tempfile
    import sympy
    import torch
    from kan import KAN
    names = list(V)
    X0 = np.column_stack([V[n] for n in names]).astype(float)
    mu, sd = X0.mean(0), X0.std(0)
    sd[sd == 0] = 1.0
    ys = float(np.std(y)) or 1.0
    torch.manual_seed(seed)
    X = torch.tensor((X0 - mu) / sd, dtype=torch.float32)
    Y = torch.tensor((y / ys)[:, None], dtype=torch.float32)
    ds = {"train_input": X, "train_label": Y, "test_input": X, "test_label": Y}
    model = KAN(width=[len(names), 1], grid=5, k=3, seed=seed, auto_save=False,
                ckpt_path=tempfile.mkdtemp(prefix="p2kan_"), device="cpu")
    model.fit(ds, opt="LBFGS", steps=steps, lamb=lamb, log=steps + 1)
    model.auto_symbolic(lib=["x", "x^2", "0"], verbose=0)
    expr = model.symbolic_formula()[0][0]
    xs = [sympy.Symbol(f"x_{j + 1}") for j in range(len(names))]
    raw = [sympy.Symbol(n.replace("*", "_")) for n in names]
    expr = sympy.expand(ys * expr.subs({x: (r - m) / s for x, r, m, s in zip(xs, raw, mu, sd)}))
    out = {}
    for n, r in zip(names, raw):
        c1 = float(expr.coeff(r, 1).subs({rr: 0 for rr in raw}))
        if abs(c1) > 1e-9:
            out[n] = c1
        c2 = float(expr.coeff(r, 2).subs({rr: 0 for rr in raw}))
        if abs(c2) > 1e-9:
            out[n + "^2" if n != "q" else "q^2"] = c2
    const = float(expr.subs({rr: 0 for rr in raw}))
    if abs(const) > 1e-9:
        out["1"] = const
    return out
