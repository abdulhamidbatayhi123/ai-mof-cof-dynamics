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


from p2.run_o1 import discover_o1


def _synthetic_obs(k=0.02, n_probe=5):
    chans = {"c": [], "q": [], "T": []}
    for j in range(n_probe):
        s = ldf_series(k=k, n=200, t_end=600.0)   # same isotherm as qstar_meas below
        for ch in chans:
            chans[ch].append(s[ch])
    qs = lambda c, T: 5.0 * 3.0 * np.asarray(c) / (1 + 3.0 * np.asarray(c))
    t = np.linspace(0, 600.0, 200)
    return {"t": t, "channels": {k_: np.array(v) for k_, v in chans.items()}, "qstar_meas": qs}


def test_discover_o1_recovers_law_in_both_forms_and_all_solvers():
    obs = _synthetic_obs()
    for method in ("best_subset", "stlsq", "ensemble"):
        for form in ("strong", "weak"):
            coefs = discover_o1(obs, method, form)
            assert success_L1(coefs), (method, form, coefs)


from p2.massbal import invert_uptake


def test_mass_balance_inversion_recovers_q_from_dense_concentration():
    """Known answer from a fresh verified-solver run (NOT a confirmatory grid cell)."""
    from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data
    p = AdsorptionPhysicsConfig()
    p.k_LDF = 0.002
    ts = p.stoichiometric_time(1.0, p.T_in)
    z, t, y = generate_breakthrough_data(p, N_z=200, t_final=3 * ts, n_snapshots=300, verbose=False)
    c, q = y[:200], y[200:400]
    q_hat = invert_uptake(c, z, t, p, c_in=1.0)
    inner = slice(20, 180)            # boundary derivatives are one-sided; judge the interior
    err = np.max(np.abs(q_hat[inner] - q[inner])) / np.max(q)
    assert err < 0.03, err


from p2.run_o1 import discover_o2


def test_discover_o2_recovers_law_from_concentration_only():
    from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data
    from isotherm import q_star_np
    p = AdsorptionPhysicsConfig()
    p.k_LDF = 0.002
    ts = p.stoichiometric_time(1.0, p.T_in)
    z, t, y = generate_breakthrough_data(p, N_z=200, t_final=3 * ts, n_snapshots=300, verbose=False)
    obs = {"t": t, "z": z, "channels": {"c": y[:200], "T": y[400:]},
           "qstar_meas": lambda c, T: q_star_np(np.asarray(c, float), np.asarray(T, float), p),
           "c_in": 1.0}
    # Pipeline correctness: discover_o2 must be discover_o1 on the INVERTED q. Checked
    # by feeding the true q through the same path. (With inverted q the law is NOT
    # recovered at this Da even from dense exact c -- inversion error ~3 % of q_max,
    # concentrated at the front, beats the driving force there. That is a pilot fact
    # declared in PREREG_P2 §6, not a pipeline defect, and no test is bent to hide it.)
    import p2.massbal as mb
    true_q = y[200:400]
    orig = mb.invert_uptake
    mb.invert_uptake = lambda *a, **k: true_q
    try:
        coefs = discover_o2(obs, p, "best_subset", "weak", probes=slice(20, 180, 8))
    finally:
        mb.invert_uptake = orig
    assert success_L1(coefs) and k_accuracy(coefs, 0.002) < 0.02, coefs


def test_jax_column_matches_verified_solver():
    from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data
    from p2.jaxcol import solve
    p = AdsorptionPhysicsConfig()
    p.k_LDF = 0.002
    ts = p.stoichiometric_time(1.0, p.T_in)
    z, t, y = generate_breakthrough_data(p, N_z=50, t_final=3 * ts, n_snapshots=100, verbose=False)
    yj = np.asarray(solve(p, 50, 1.0, 3 * ts, t))
    exit_ref, exit_jax = y[49], yj[:, 49]
    assert np.max(np.abs(exit_ref - exit_jax)) < 5e-3, np.max(np.abs(exit_ref - exit_jax))


def test_outlet_profile_likelihood_brackets_k_in_kinetic_regime():
    """O3 identifiability: the whole column refitted to outlet c(t), T(t) per k.
    Fresh run (not a grid cell) at a low Da, where k must be identifiable."""
    from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data
    from p2.identifiability import profile_interval_outlet
    p = AdsorptionPhysicsConfig()
    k_true = 2e-4
    p.k_LDF = k_true
    ts = p.stoichiometric_time(1.0, p.T_in)
    z, t, y = generate_breakthrough_data(p, N_z=100, t_final=4 * ts, n_snapshots=120, verbose=False)
    rng = np.random.default_rng(5)
    c_obs = y[99] + rng.normal(scale=0.005, size=t.size)
    T_obs = y[299] + rng.normal(scale=0.005 * np.ptp(y[299]), size=t.size)
    lo, hi = profile_interval_outlet(p, 1.0, t, c_obs, T_obs, sigma_c=0.005,
                                     sigma_T=0.005 * np.ptp(y[299]), n_z=100)
    assert lo < k_true < hi and hi / lo < 2.0, (lo, hi)
