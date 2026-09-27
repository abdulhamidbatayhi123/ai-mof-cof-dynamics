import numpy as np

from p2.synthetic import ldf_series


def test_ldf_series_obeys_its_law():
    s = ldf_series(k=0.02, n=400, seed=0)
    dq = np.gradient(s["q"], s["t"])
    resid = dq - 0.02 * (s["qstar"] - s["q"])
    assert np.max(np.abs(resid[5:-5])) < 1e-3 * np.max(np.abs(dq))


from p2.features import derivative, lib_b
from p2.metric import success_L1, k_accuracy
from p2.methods import best_subset, stlsq, ensemble
from p2.identifiability import profile_interval


def test_derivative_exact_on_smooth_series():
    t = np.linspace(0, 10, 500); y = np.sin(t)
    assert np.max(np.abs(derivative(y, t)[10:-10] - np.cos(t)[10:-10])) < 1e-3


def test_lib_b_contains_measured_equilibrium_and_named_terms():
    s = ldf_series(k=0.02)
    F = lib_b(s["c"], s["q"], s["T"], s["qstar"])
    assert set(F) == {"1", "c", "q", "T", "c*q", "q^2", "c^2", "qstar"}
    assert np.allclose(F["qstar"], s["qstar"])


def test_success_requires_exact_support_signs_and_ratio():
    assert success_L1({"qstar": 0.02, "q": -0.02})
    assert not success_L1({"qstar": 0.02, "q": -0.02, "c": 1e-6})
    assert not success_L1({"qstar": -0.02, "q": 0.02})
    assert not success_L1({"qstar": 0.02, "q": -0.03})
    assert success_L1({"qstar": 0.02, "q": -0.0215})


def test_k_accuracy_is_relative_error_of_minus_q_coefficient():
    assert abs(k_accuracy({"qstar": 0.02, "q": -0.022}, 0.02) - 0.1) < 1e-12


def _fit_on(k, sigma=0.0, seed=0):
    s = ldf_series(k=k, seed=seed)
    q = s["q"] + np.random.default_rng(seed).normal(scale=sigma * np.ptp(s["q"]), size=s["q"].size)
    F = lib_b(s["c"], q, s["T"], s["qstar"])
    return F, derivative(q, s["t"])


def test_best_subset_recovers_ldf_at_zero_noise():
    F, y = _fit_on(0.02)
    coefs = best_subset(F, y, max_terms=4)
    assert success_L1(coefs) and k_accuracy(coefs, 0.02) < 0.02, coefs


def test_stlsq_and_ensemble_recover_ldf_at_zero_noise():
    F, y = _fit_on(0.02)
    for fit in (stlsq, ensemble):
        coefs = fit(F, y)
        assert success_L1(coefs), (fit.__name__, coefs)


def test_profile_interval_brackets_truth_and_is_narrow_at_low_noise():
    s = ldf_series(k=0.02)
    rng = np.random.default_rng(1)
    q_obs = s["q"] + rng.normal(scale=0.005 * np.ptp(s["q"]), size=s["q"].size)
    lo, hi = profile_interval(s["t"], s["c"], q_obs, lambda c: 5.0 * 3.0 * c / (1 + 3.0 * c),
                              sigma=0.005 * np.ptp(s["q"]))
    assert lo < 0.02 < hi and hi / lo < 1.5


from p2.weak import weak_system


def test_weak_form_recovers_ldf_at_zero_and_under_noise():
    for sigma in (0.0, 0.02):
        s = ldf_series(k=0.02, n=400)
        q = s["q"] + np.random.default_rng(3).normal(scale=sigma * np.ptp(s["q"]), size=s["q"].size)
        F = lib_b(s["c"], q, s["T"], s["qstar"])
        G, b = weak_system(F, q, s["t"])
        coefs = best_subset(G, b, max_terms=4)
        assert success_L1(coefs), (sigma, coefs)
        assert k_accuracy(coefs, 0.02) < 0.05, (sigma, coefs)


def test_strong_form_fails_where_weak_form_succeeds_under_noise():
    """The reason the weak form is in the competitor list: noisy derivatives."""
    s = ldf_series(k=0.02, n=400)
    q = s["q"] + np.random.default_rng(3).normal(scale=0.02 * np.ptp(s["q"]), size=s["q"].size)
    F = lib_b(s["c"], q, s["T"], s["qstar"])
    strong = best_subset(F, derivative(q, s["t"]), max_terms=4)
    G, b = weak_system(F, q, s["t"])
    weak = best_subset(G, b, max_terms=4)
    assert k_accuracy(weak, 0.02) < k_accuracy(strong, 0.02)
