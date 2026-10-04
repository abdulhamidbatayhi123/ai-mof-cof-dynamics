"""M7 (PREREG_P2 §3): constrained symbolic regression with PySR, as a support-returning method.

PySR returns an expression, the paper's metric (p2/metric.py) a coefficient dict over
named features. The bridge is deliberately strict: the chosen expression is expanded
by SymPy; every monomial that is a single feature to the first power contributes its
coefficient under that feature's name, and ANY other monomial (a constant, a product,
a power, a quotient) is recorded under its own string as extra support -- so a law
found only up to a spurious term counts as a failure, as for every other method.

Selection among PySR's Pareto front uses PySR's own default ("best": the score-based
knee), fixed here before any confirmatory run. Binary operators only (+, -, *), no
unary functions: the true law is linear in Lib-B's features, and the prereg gives
every method the same features.
"""
from __future__ import annotations

import numpy as np


def pysr_sr(features: dict, y, seed=0, niterations=40, maxsize=12, timeout_s=1800, procs=2):
    from pysr import PySRRegressor
    import sympy as sp

    names = list(features)
    X = np.column_stack([np.asarray(features[n], float) for n in names])
    model = PySRRegressor(
        binary_operators=["+", "-", "*"], unary_operators=[],
        niterations=niterations, maxsize=maxsize, random_state=seed,
        deterministic=True, parallelism="serial" if procs <= 1 else "multithreading",
        timeout_in_seconds=timeout_s, model_selection="best", progress=False, verbosity=0,
        temp_equation_file=True)
    model.fit(X, np.asarray(y, float), variable_names=names)
    expr = sp.expand(model.sympy())
    syms = {sp.Symbol(n): n for n in names}
    coefs = {n: 0.0 for n in names}
    for term in sp.Add.make_args(expr):
        c, rest = term.as_coeff_Mul()
        if rest in syms and rest.is_Symbol:
            coefs[syms[rest]] += float(c)
        else:
            key = str(term if rest == 1 else rest)
            coefs[key] = coefs.get(key, 0.0) + float(c if rest != 1 else term)
    return coefs, str(expr)
