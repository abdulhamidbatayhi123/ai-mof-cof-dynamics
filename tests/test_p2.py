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


from p2.analysis import boundary


def test_boundary_ci_has_nominal_coverage_and_no_bias():
    """A single 95 % CI misses one time in twenty, so one seed cannot test it:
    coverage over 60 simulated datasets must be near nominal, and the estimate
    unbiased (measured once at 100 datasets: coverage 0.94, bias +0.012 decade)."""
    import warnings
    warnings.filterwarnings("ignore")
    das = np.logspace(-1, 3, 9)
    tb = 1.3
    cover, ests = 0, []
    for seed in range(60):
        rng = np.random.default_rng(seed)
        succ = {float(d): list(rng.random(20) < 1 / (1 + np.exp(3 * (np.log10(d) - tb))))
                for d in das}
        e, lo, hi = boundary(succ, n_boot=200, seed=seed)
        cover += lo < 10 ** tb < hi
        ests.append(np.log10(e))
    assert cover / 60 >= 0.88, cover / 60
    assert abs(np.mean(ests) - tb) < 0.05, np.mean(ests)


def test_boundary_reports_none_when_no_crossing():
    succ = {float(d): [True] * 20 for d in np.logspace(-1, 3, 9)}
    est, lo, hi = boundary(succ, n_boot=100, seed=1)
    assert est is None


from p2.methods import slow_manifold
from p2.metric import success_manifold


def test_slow_manifold_finds_equilibrium_when_fast_and_not_when_slow():
    # "On the manifold" at the resolution the methods work at means the equilibrium
    # lag (1/k) dq/dt is below the 1e-3 floor. The ramp time here is ~30 s, so that
    # needs k * 30 >~ 1e3, i.e. k ~ 100. (k = 1 lags ~3 % during the ramp: M9 then
    # returns q* at 0.955 plus spurious c, c^2 -- correctly NOT the manifold.)
    fast = ldf_series(k=100.0, n=400)
    slow = ldf_series(k=0.002, n=400)     # k * t_end = 1.2: far from it
    for s, expect in ((fast, True), (slow, False)):
        F = lib_b(s["c"], s["q"], s["T"], s["qstar"])
        F_alg = {k: v for k, v in F.items() if k != "q" and "q" not in k.replace("qstar", "")}
        coefs = slow_manifold(F_alg, s["q"])
        assert success_manifold(coefs) == expect, (expect, coefs)


from p2.methods import sindy_pi


def test_sindy_pi_finds_implicit_langmuir_ldf_without_an_isotherm():
    """No q* supplied. dq/dt = k(qm b c/(1+bc) - q)  <=>
       dq/dt + b c dq/dt = k qm b c - k q - k b c q   (b=3, qm=5, k=0.02)."""
    s = ldf_series(k=0.02, n=400)
    c, q = s["c"], s["q"]
    dq = derivative(q, s["t"])
    F = {"1": np.ones_like(c), "c": c, "q": q, "c*q": c * q, "q^2": q ** 2, "c^2": c ** 2}
    lhs, coefs = sindy_pi(F, dq)
    # normalised to the dq/dt coefficient = 1
    assert set(coefs) == {"dq", "c*dq", "c", "q", "c*q"}, (lhs, coefs)
    # PREREG_P2 M6: b and k recovered within 5 % (measured 2026-10-04: 0.02 % and 0.07 %);
    # every coefficient held to the same relative 5 %, not the looser absolute bounds
    # this test first carried
    for key, true in (("c*dq", 3.0), ("c", -0.3), ("q", 0.02), ("c*q", 0.06)):
        assert abs(coefs[key] - true) <= 0.05 * abs(true), (key, coefs[key])


from p2.methods import kan_symbolic


import pytest


@pytest.mark.xfail(strict=True, reason=(
    "M8 fails its known-answer test at zero noise in every configuration tried "
    "(2026-09-28): polynomial library with lamb 1e-3/1e-2/1e-1 -> routes the law "
    "through q^2 or collapses to a constant; raw variables, single trajectory -> "
    "uses q alone (dq/dt is a function of q along one trajectory); raw variables, "
    "three trajectories -> {1, qstar, qstar^2}, q dropped. Reported as a documented "
    "negative (PREREG_P2 §3), consistent with L3 and S49. strict=True: if a pykan "
    "change makes this pass, the suite fails and says so."))
def test_kan_symbolic_recovers_ldf_at_zero_noise():
    """Several trajectories (different isotherms), as the grid's 20 probes give."""
    Vs, ys = [], []
    for b in (1.0, 3.0, 9.0):
        s = ldf_series(k=0.02, n=200, b=b)
        Vs.append(np.column_stack([s["c"], s["q"], s["T"], s["qstar"]]))
        ys.append(derivative(s["q"], s["t"]))
    V0 = np.vstack(Vs)
    V = {"c": V0[:, 0], "q": V0[:, 1], "T": V0[:, 2], "qstar": V0[:, 3]}
    coefs = kan_symbolic(V, np.concatenate(ys), seed=0)
    kept = {k: v for k, v in coefs.items() if abs(v) > 0.05 * max(abs(x) for x in coefs.values())}
    assert set(kept) == {"q", "qstar"}, coefs
    assert abs(-kept["q"] / kept["qstar"] - 1) < 0.1 and abs(-kept["q"] - 0.02) < 0.004, coefs


from p2.analysis import r_collapse, disc_vs_ident


def _curve(center, rng, xs):
    return {float(x): list(rng.random(20) < 1 / (1 + np.exp(3 * (np.log10(x) - center)))) for x in xs}


def test_r_collapse_words_follow_the_spread():
    # This test first fed FALLING curves, i.e. it encoded the bug that success falls with
    # R; success RISES with R = delta / eps_eff (see test_r_collapse_handles_success_
    # rising_with_R), so the curves are generated rising here.
    rng = np.random.default_rng(0)
    xs = np.logspace(-1, 3, 9)
    together = {f"cond{i}": _logistic_successes(xs, 1.0 + 0.05 * i, +4.0, 40, rng) for i in range(3)}
    apart = {"a": _logistic_successes(xs, 0.0, 4.0, 40, rng), "b": _logistic_successes(xs, 1.5, 4.0, 40, rng)}
    assert r_collapse(together, n_boot=100)["words"].startswith("R collapses")
    assert r_collapse(apart, n_boot=100)["words"].startswith("R does not collapse")


def test_disc_vs_ident_uses_the_declared_mde():
    mde = 0.25
    assert disc_vs_ident(10.0, 100.0, mde)["words"] == "discovery fails before identifiability"
    assert disc_vs_ident(100.0, 110.0, mde)["words"] == "discovery fails with identifiability"
    assert disc_vs_ident(100.0, 10.0, mde)["words"] == "discovery outlives identifiability"
    assert disc_vs_ident(None, 10.0, mde)["words"].startswith("no boundary")


def test_ode_profile_with_temperature_brackets_k_on_nonisothermal_probe():
    """O1 identifiability on a fresh non-isothermal solver run (not a grid cell)."""
    from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data
    from isotherm import q_star_np
    p = AdsorptionPhysicsConfig()
    p.k_LDF = 2e-4
    ts = p.stoichiometric_time(1.0, p.T_in)
    z, t, y = generate_breakthrough_data(p, N_z=100, t_final=4 * ts, n_snapshots=200, verbose=False)
    j = 50
    c, q, T = y[j], y[100 + j], y[200 + j]
    sig = 0.005 * np.ptp(q)
    q_obs = q + np.random.default_rng(2).normal(scale=sig, size=q.size)
    lo, hi = profile_interval(t, c, q_obs, lambda cc, TT: q_star_np(cc, TT, p), sigma=sig, T=T)
    # Sampling-resolution bias measured on noise-free data: +0.47 % at 200 snapshots
    # (the front crosses a probe in a few samples; PCHIP cut it from +0.61 %). A
    # 0.5 %-noise interval can therefore sit just beside the truth. The test checks
    # the PRE-REGISTERED criterion (identifiable: within [k/2, 2k]) and a 2 % bound.
    from p2.identifiability import identifiable
    assert identifiable(lo, hi, 2e-4), (lo, hi)
    assert lo > 2e-4 * 0.98 and hi < 2e-4 * 1.02, (lo, hi)



def test_success_L2_detects_a_rate_that_falls_with_loading():
    """PREREG_P2 §4.3 (L2, operational): k_hat(q) = -df/dq at fixed q*, binned in q/q_max,
    must fall (Spearman < -0.8) to <= 0.6 of its bottom-bin value, with q* and q selected."""
    from p2.metric import success_L2
    rng = np.random.default_rng(0)
    qmax = 5.0
    q = rng.uniform(0.0, qmax, 2000)
    c = rng.uniform(0.0, 1.0, 2000)
    # f = a q* + b q + e q^2  ->  k_hat = -(b + 2 e q): from 0.05 at q=0 to 0.01 at q=qmax
    falls = {"qstar": 0.03, "q": -0.05, "q^2": 0.004}
    assert success_L2(falls, c, q, qmax)
    # constant k (the L1 law): no state dependence
    assert not success_L2({"qstar": 0.02, "q": -0.02}, c, q, qmax)
    # a rate that RISES with loading is not the L2 law
    assert not success_L2({"qstar": 0.03, "q": -0.01, "q^2": -0.004}, c, q, qmax)
    # without q* the law cannot be the rate law at all
    assert not success_L2({"q": -0.05, "q^2": 0.004}, c, q, qmax)


def test_lib_a_fidelity_is_relative_rms_on_held_out_probes():
    from p2.metric import heldout_fidelity
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert heldout_fidelity(y, y) == 0.0
    assert abs(heldout_fidelity(y + 0.1 * np.sqrt(np.mean(y ** 2)), y) - 0.1) < 1e-12


def test_probe_profile_likelihood_brackets_k_in_kinetic_regime():
    """O2 identifiability (PREREG_P2 §3 table): the whole column refitted to INTERIOR
    c(t), T(t) at a few probes, q latent. Same fresh low-Da run as the outlet test."""
    from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data
    from p2.identifiability import profile_interval_probes
    p = AdsorptionPhysicsConfig()
    k_true = 2e-4
    p.k_LDF = k_true
    ts = p.stoichiometric_time(1.0, p.T_in)
    n = 100
    z, t, y = generate_breakthrough_data(p, N_z=n, t_final=4 * ts, n_snapshots=120, verbose=False)
    iz = np.array([20, 50, 80])
    rng = np.random.default_rng(6)
    sT = 0.005 * np.ptp(y[2 * n:])
    c_obs = y[iz] + rng.normal(scale=0.005, size=(iz.size, t.size))
    T_obs = y[2 * n + iz] + rng.normal(scale=sT, size=(iz.size, t.size))
    lo, hi = profile_interval_probes(p, 1.0, t, z[iz], c_obs, T_obs, sigma_c=0.005,
                                     sigma_T=sT, n_z=n)
    assert lo < k_true < hi and hi / lo < 2.0, (lo, hi)


def test_success_M6_requires_the_implicit_langmuir_ldf_structure_and_signs():
    """PREREG_P2 M6: success = support {dq, c*dq, c, q, c*q} with correct signs
    (normalised to the dq coefficient = 1: c*dq > 0, c < 0, q > 0, c*q > 0)."""
    from p2.metric import success_M6
    good = {"dq": 1.0, "c*dq": 3.0, "c": -0.3, "q": 0.02, "c*q": 0.06}
    assert success_M6(good)
    assert not success_M6({**good, "q^2": 0.001})               # an extra term
    assert not success_M6({k: v for k, v in good.items() if k != "c*q"})   # a missing term
    assert not success_M6({**good, "c": 0.3})                   # a wrong sign


def test_grid_extra_m6_recovers_the_implicit_law_on_the_isothermal_system():
    """p2_grid_extra.fit_m6 on the known-answer ISOTHERMAL Langmuir-LDF system: M6 is
    given no isotherm and must find {dq, c*dq, c, q, c*q} with correct signs."""
    from p2_grid_extra import fit_m6
    co, ok = fit_m6(_synthetic_obs())
    assert ok, co


def test_grid_extra_m9_recovers_the_slow_manifold_near_equilibrium():
    """p2_grid_extra.fit_m9 at high k (q tracks q*): the algebraic law q = q*_meas."""
    from p2_grid_extra import fit_m9
    co, ok = fit_m9(_synthetic_obs(k=20.0))   # k = 2 is not near equilibrium on this system
    assert ok, co


def test_eiv_best_subset_recovers_ldf_and_matches_m4_at_zero_error():
    """M5 as run (p2/eiv.py): at (near-)zero declared error it must find the L1 law and
    agree with M4's exact enumeration on the support."""
    from p2.eiv import eiv_best_subset
    from p2.methods import best_subset
    s = ldf_series(k=0.02, n=200)
    F = lib_b(s["c"], s["q"], s["T"], s["qstar"])
    dq = derivative(s["q"], s["t"])
    sd = {k: 1e-6 * np.std(v) for k, v in F.items()}
    co = eiv_best_subset(F, dq, sd, 1e-6 * np.std(dq))
    assert success_L1(co), co
    assert set(co) == set(best_subset(F, dq)), (co, best_subset(F, dq))


def test_mixed_ls_tls_removes_the_attenuation_bias_ols_suffers():
    """The classical EIV property M5 relies on: with error in the regressor, OLS slopes
    are attenuated; TLS with the declared error SDs is not (here y = 2 x + 1, x noisy)."""
    from p2.eiv import mixed_ls_tls
    rng = np.random.default_rng(0)
    x = rng.uniform(0, 1, 20000)
    y = 2.0 * x + 1.0 + rng.normal(0, 0.05, x.size)
    xn = x + rng.normal(0, 0.15, x.size)
    X = np.column_stack([xn, np.ones_like(xn)])
    ols = np.linalg.lstsq(X, y, rcond=None)[0]
    tls = mixed_ls_tls(X, y, [0.15, 0.0], 0.05)
    assert abs(ols[0] - 2.0) > 0.2          # attenuated
    assert abs(tls[0] - 2.0) < 0.05, tls    # corrected
    assert abs(tls[1] - 1.0) < 0.05, tls


def test_grid_extra_m5_matches_m4_at_zero_noise_through_the_grid_wrapper():
    """p2_grid_extra.fit_m5 end to end (declared SDs, derivative gain, finite-difference
    dq*/dc) at zero noise: recovers L1 and agrees with M4. NOT asserted: recovery under
    noise -- at 0.1 % noise on this 5-probe, 200-sample system both M4 and M5 fail in
    the strong form (measured 2026-10-04), which is the boundary the grid maps, not a
    defect a unit test should hide."""
    from p2_grid_extra import fit_m5
    obs = _synthetic_obs()
    co, ok = fit_m5(obs, 0.0, 0.0)
    assert ok, co
    assert set(co) == set(discover_o1(obs, "best_subset", "strong")), co


def _logistic_successes(levels, b_log10, slope, n_rep, rng):
    """Replicate outcomes with P(success) = sigma(slope (log10 x - b)); slope < 0 falls."""
    out = {}
    for x in levels:
        p = 1.0 / (1.0 + np.exp(-slope * (np.log10(x) - b_log10)))
        out[float(x)] = (rng.uniform(size=n_rep) < p).astype(float)
    return out


def test_r_collapse_handles_success_rising_with_R():
    """H2a: success RISES with R = delta / eps_eff. A first version reused the Da boundary,
    which only accepts a falling curve, and would have returned 'no crossing' for every
    condition -- no H2a verdict could ever be reached."""
    from p2.analysis import r_collapse
    rng = np.random.default_rng(0)
    R = np.logspace(-1, 3, 9)
    conds = {f"c{i}": _logistic_successes(R, 1.0 + 0.1 * i, +4.0, 40, rng) for i in range(3)}
    out = r_collapse(conds)
    assert not out["no_crossing"], out
    assert out["spread_decades"] < 0.5 and out["words"].startswith("R collapses the boundary"), out
    wide = {"a": _logistic_successes(R, 0.0, 4.0, 40, rng), "b": _logistic_successes(R, 1.7, 4.0, 40, rng)}
    assert r_collapse(wide)["words"].startswith("R does not collapse the boundary")
    mid = {"a": _logistic_successes(R, 0.0, 4.0, 60, rng), "b": _logistic_successes(R, 0.75, 4.0, 60, rng)}
    assert r_collapse(mid)["words"].startswith("inconclusive: R narrows the boundary to a spread of")


def test_best_method_boundary_carries_the_selection():
    """H2a/H2b: the best method is chosen on the same replicates, so its interval comes
    from a bootstrap that resamples replicates JOINTLY across methods and re-selects the
    best in every draw (PREREG_P2 §4.3)."""
    from p2.analysis import best_method_boundary
    rng = np.random.default_rng(1)
    Da = np.logspace(-1, 3, 9)
    by_m = {"A": _logistic_successes(Da, 1.0, -4.0, 20, rng),
            "B": _logistic_successes(Da, 1.8, -4.0, 20, rng)}
    best, est, lo, hi = best_method_boundary(by_m, n_boot=300)
    assert best == "B" and lo <= est <= hi
    assert abs(np.log10(est) - 1.8) < 0.3


def test_h2c_words_cover_every_outcome():
    from p2.analysis import h2c_verdict
    mde = 0.25
    assert h2c_verdict({0.02: 0.40}, mde)["words"].startswith("EIV moves the boundary by")
    assert "less than the predicted factor 2" in h2c_verdict({0.02: 0.27}, mde)["words"]
    assert h2c_verdict({0.005: 0.1, 0.02: -0.1}, mde)["words"].startswith(
        "EIV does not move the boundary detectably")
    assert h2c_verdict({0.02: -0.40}, mde)["words"].startswith("EIV moves the boundary DOWN by")
