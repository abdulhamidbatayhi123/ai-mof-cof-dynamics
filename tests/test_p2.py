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


def test_o1_exact_ldf_likelihood_matches_the_ode_reference():
    """identifiability.loglik_o1 (exact piecewise-linear LDF update, vectorised) must agree
    with the solver-based _loglik it replaces for speed (~120x): same model, PCHIP drivers."""
    from p2.identifiability import _loglik, loglik_o1
    rng = np.random.default_rng(0)
    s = ldf_series(k=0.02, n=200, seed=0)
    qsf = lambda c: 5.0 * 3.0 * np.asarray(c) / (1 + 3.0 * np.asarray(c))
    qo = s["q"] + rng.normal(0, 0.002, 200)
    for k in (0.005, 0.02, 0.05):
        a = _loglik(k, s["t"], s["c"], qo, qsf, 0.002)
        b = loglik_o1(k, s["t"], [s["c"]], [qo], qsf, 0.002)[0]
        assert abs(a - b) <= 2e-3 * abs(a) + 0.2, (k, a, b)


def test_o1_profile_over_all_probes_brackets_k():
    from p2.identifiability import identifiable, profile_interval_o1
    rng = np.random.default_rng(1)
    qsf = lambda c: 5.0 * 3.0 * np.asarray(c) / (1 + 3.0 * np.asarray(c))
    cs, qs = [], []
    for j in range(20):
        s = ldf_series(k=0.02, n=200, seed=j)
        cs.append(s["c"])
        qs.append(s["q"] + rng.normal(0, 0.02 * np.ptp(s["q"]), 200))
    lo, hi = profile_interval_o1(s["t"], cs, qs, qsf, 0.02 * np.ptp(qs[0]))
    assert lo <= 0.02 <= hi * (1 + 1e-9) and identifiable(lo, hi, 0.02), (lo, hi)


def _planted_grid(rng, n_rep=20):
    """A simulated O1 grid with KNOWN boundaries: methods A (Da* = 10) and B (Da* = 30),
    M5 (Da* = 90, i.e. 3x B), identifiability at Da* = 300; one isotherm, one Pe."""
    Da = np.logspace(-1, 3, 9)
    cells = {f"lang_{d:.3g}": {"iso": "langmuir", "law": "L1", "pe_mult": 1.0, "Da": float(d)} for d in Da}
    P = lambda d, b: 1.0 / (1.0 + np.exp(4.0 * (np.log10(d) - np.log10(b))))
    o1, m5, ident = {}, {}, {}
    for nm, c in cells.items():
        for rep in range(n_rep):
            u = rng.uniform(size=4)
            o1[f"{nm}|0.02|0.02|{rep}|A|strong"] = {"success": bool(u[0] < P(c["Da"], 10))}
            o1[f"{nm}|0.02|0.02|{rep}|B|strong"] = {"success": bool(u[1] < P(c["Da"], 30))}
            m5[f"{nm}|0.02|0.02|{rep}|eiv_best_subset|strong"] = {"success": bool(u[2] < P(c["Da"], 90))}
            ident[f"{nm}|0.02|0.02|{rep}|profile|o1"] = {"success": bool(u[3] < P(c["Da"], 300))}
    rstats = {nm: {"delta": 1.0 / c["Da"], "eps_rec": 0.0} for nm, c in cells.items()}
    return cells, o1, m5, ident, rstats


def test_p2_analyze_recovers_planted_verdicts():
    """The verdict driver on a simulated grid with planted boundaries: H2b must pick B and
    say 'fails before identifiability' (30 vs 300); H2c must see EIV move it up ~3x.
    A1: the grid has N_REP replicates, split into selection and estimation sets."""
    from p2_analyze import h2c, verdicts
    from p2_grid_o1 import N_REP
    cells, o1, m5, ident, rstats = _planted_grid(np.random.default_rng(4), n_rep=N_REP)
    out = verdicts(cells, o1, {}, ident, rstats, n_boot=200)
    s = out["H2b"]["sigma=0.02|eps=0.02|langmuir|pe=1.0"]
    assert s["best_method"] == "B|strong", s
    assert s["words"] == "discovery fails before identifiability", s
    assert abs(np.log10(s["da_disc"]) - np.log10(30)) < 0.3 and abs(np.log10(s["da_ident"]) - np.log10(300)) < 0.3
    hc = h2c(cells, o1, m5, n_boot=200)
    sl = hc["slices"]["langmuir|pe=1.0|eps=0.02"]
    assert sl["words"].startswith("EIV moves the boundary by"), hc
    assert hc["h2c_holds"] and sl["shift_ci"][0] is not None and sl["shift_ci"][0] < sl["shift"] < sl["shift_ci"][1]
    assert isinstance(out["H2a"]["words"], str)


def test_pysr_safe_names_are_valid_identifiers():
    """B76: PySR refuses names like 'c*q'; the placeholders must be plain identifiers,
    one per feature, in order, and must not collide with each other."""
    from p2.pysr_method import safe_names
    names = ["c", "q", "T", "c*q", "q^2", "c^2", "qstar"]
    ph = safe_names(names)
    assert len(ph) == len(names) and len(set(ph)) == len(ph)
    assert all(p.isidentifier() and p.replace("_", "").isalnum() for p in ph)


# ---- Amendment A1 (PREREG_P2 s.9): selection split, aggregation, positive control, k-aware

def test_select_best_uses_only_what_it_is_given():
    """A1: the best method is chosen from the selection replicates; the largest crossing
    wins, and with no crossing anywhere the highest mean success wins."""
    from p2.analysis import select_best
    rng = np.random.default_rng(2)
    Da = np.logspace(-1, 3, 9)
    by_m = {"A": _logistic_successes(Da, 1.0, -4.0, 20, rng),
            "B": _logistic_successes(Da, 2.0, -4.0, 20, rng)}
    assert select_best(by_m) == "B"
    flat = {"A": {float(d): [1.0] * 20 for d in Da}, "B": {float(d): [0.0] * 20 for d in Da}}
    assert select_best(flat) == "A"
    assert select_best({}) is None


def test_aggregate_h2b_two_thirds_rule():
    from p2.analysis import aggregate_h2b
    w = "discovery fails before identifiability"
    o = "discovery outlives identifiability"
    assert aggregate_h2b({"a": w, "b": w, "c": o})["words"] == w
    assert aggregate_h2b({"a": w, "b": o})["words"].startswith("mixed")
    r = aggregate_h2b({"a": w, "b": "no boundary on the grid for one of the two; reported as the range tested"})
    assert r["words"] == w and r["no_verdict"] == ["b"]
    assert aggregate_h2b({"a": "no boundary"})["words"].startswith("no verdict")


def test_positive_control_threshold():
    from p2.analysis import positive_control
    assert positive_control([1.0] * 36 + [0.0] * 4, [1.0] * 40)[0]
    assert not positive_control([1.0] * 35 + [0.0] * 5, [1.0] * 40)[0]
    assert not positive_control([], [1.0] * 40)[0]


def test_h2c_holds_on_a_detectable_upward_shift():
    """A1: H2c holds at an eps if the upward shift reaches the decision threshold."""
    from p2.analysis import h2c_verdict
    r = h2c_verdict({0.02: 0.27, 0.05: 0.1}, 0.25)
    assert r["h2c_holds"] and r["holds_by_eps"] == {0.02: True, 0.05: False} and not r["h2c_falsified"]
    r = h2c_verdict({0.02: 0.1, 0.05: -0.3}, 0.25)
    assert not r["h2c_holds"] and r["h2c_falsified"]


def test_p2_analyze_selection_split_and_k_sensitivity():
    """A1 on a planted grid: selection uses replicates < N_SEL only (a method that is best
    ONLY on the estimation replicates is not chosen); the k-aware sensitivity counts a
    success only if k_hat is within [k/2, 2k]; the positive control is reported."""
    from p2_analyze import N_SEL, verdicts
    from p2_grid_o1 import N_REP
    cells, o1, m5, ident, rstats = _planted_grid(np.random.default_rng(5), n_rep=N_REP)
    for nm, c in cells.items():
        c["k_LDF"] = 0.01
        for rep in range(N_REP):
            # C: never succeeds on the selection set, always on the estimation set
            o1[f"{nm}|0.02|0.02|{rep}|C|strong"] = {"success": rep >= N_SEL, "k_hat": 0.01}
            # B keeps its successes but its k is off by 10x: k-aware success never holds
            o1[f"{nm}|0.02|0.02|{rep}|B|strong"]["k_hat"] = 0.1
            o1[f"{nm}|0.02|0.02|{rep}|A|strong"]["k_hat"] = 0.01
    out = verdicts(cells, o1, {}, ident, rstats, n_boot=100)
    s = out["H2b"]["sigma=0.02|eps=0.02|langmuir|pe=1.0"]
    assert s["best_method"] == "B|strong", s
    k = out["H2b_k_sensitivity"]["sigma=0.02|eps=0.02|langmuir|pe=1.0"]
    assert abs(np.log10(k["da_disc_k"] or 1e9) - np.log10(30)) > 0.3   # B's successes no longer count
    assert "H2b_overall" in out and "positive_control" in out


def test_refine_levels_are_strictly_inside_half_a_decade():
    """A1: 8 levels, equally spaced in log10 Da, strictly inside +-0.5 decade."""
    from p2.analysis import refine_levels
    lv = np.log10(refine_levels(30.0))
    assert len(lv) == 8 and np.all(np.abs(lv - np.log10(30.0)) < 0.5)
    assert np.allclose(np.diff(lv), 1.0 / 9.0)
    assert refine_levels(None) == []


def test_refined_cells_enter_h2c_only():
    """A1: refinement cells (flag 'refined') never enter H2a/H2b; in H2c they join the main
    grid at eps = 2 % only. The generator lists them for every Pe multiplier."""
    from p2_analyze import h2c, h2c_refine_levels, verdicts
    from p2_generate import refined_cells
    from p2_grid_o1 import N_REP
    cells, o1, m5, ident, rstats = _planted_grid(np.random.default_rng(6), n_rep=N_REP)
    lv = h2c_refine_levels(cells, o1)
    assert len(lv["langmuir|pe=1.0"]["levels"]) == 8
    assert len(refined_cells(lv)) == 8 * len(lv) and all(c[2] == 1.0 for c in refined_cells(lv))
    # a refined cell where every method always FAILS: it would distort H2b if it leaked in
    cells["lang_ref"] = {"iso": "langmuir", "law": "L1", "pe_mult": 1.0, "Da": 0.2, "refined": True}
    for rep in range(N_REP):
        for m in ("A", "B"):
            o1[f"lang_ref|0.02|0.02|{rep}|{m}|strong"] = {"success": False}
        ident[f"lang_ref|0.02|0.02|{rep}|profile|o1"] = {"success": False}
    rstats["lang_ref"] = {"delta": 1.0, "eps_rec": 0.0}
    out = verdicts(cells, o1, {}, ident, rstats, n_boot=100)
    s = out["H2b"]["sigma=0.02|eps=0.02|langmuir|pe=1.0"]
    assert abs(np.log10(s["da_disc"]) - np.log10(30)) < 0.3, s
    hc = h2c(cells, o1, m5, n_boot=100)
    assert hc["slices"]["langmuir|pe=1.0|eps=0.02"]["shift"] is not None

# ---- Amendment A2: errors as failures, M5 out of H2a/H2b, robust intervals

def test_error_rows_count_as_failures_never_dropped():
    from p2_analyze import _by_da
    cells = {"x": {"iso": "langmuir", "law": "L1", "pe_mult": 1.0, "Da": 1.0, "k_LDF": 0.01}}
    rows = {"x|0.02|0.02|0|A|strong": {"success": True},
            "x|0.02|0.02|1|A|strong": {"success": True, "error": "ValueError: boom"}}
    got = _by_da(rows, cells, lambda c, s, e: True)
    assert got["A|strong"][1.0] == [1.0, 0.0]


def test_m5_oracle_never_becomes_the_h2b_best_method():
    """A2: M5 knows sigma and eps; even when it is the strongest method it is excluded
    from H2a/H2b's selection and used in H2c only."""
    from p2_analyze import verdicts
    from p2_grid_o1 import N_REP
    cells, o1, m5, ident, rstats = _planted_grid(np.random.default_rng(7), n_rep=N_REP)
    out = verdicts(cells, {**o1, **m5}, {}, ident, rstats, n_boot=50)
    s = out["H2b"]["sigma=0.02|eps=0.02|langmuir|pe=1.0"]
    assert s["best_method"] == "B|strong", s
    assert "eiv_best_subset|strong" not in s["da_disc_by_method"]


def test_boundary_without_bootstrap_draws_does_not_crash():
    from p2.analysis import boundary, select_best
    rng = np.random.default_rng(3)
    Da = np.logspace(-1, 3, 9)
    succ = _logistic_successes(Da, 2.9, -4.0, 15, rng)      # boundary near the top edge
    b, lo, hi = boundary(succ, n_boot=0)
    assert lo is None and hi is None
    select_best({"A": succ})                                 # must not raise (A2)


def test_shift_interval_and_spread_interval():
    from p2.analysis import r_collapse
    rng = np.random.default_rng(4)
    R = np.logspace(-1, 3, 9)
    conds = {f"c{i}": _logistic_successes(R, 1.0 + 0.1 * i, 4.0, 45, rng) for i in range(3)}
    r = r_collapse(conds, n_boot=100)
    assert r["spread_ci"][0] is not None and r["spread_ci"][0] <= r["spread_ci"][1]

# ---- B83: the analysis code conforms to the A1/A2 text

def test_a_method_run_on_part_of_a_slice_cannot_be_selected():
    """A2.2 as written: a method run on only some (cell, sigma, eps) of a slice (like M7 on
    4 of 16 noise pairs) takes no part in the selection, however well it does there."""
    from p2_analyze import _best
    from p2_grid_o1 import N_REP
    cells = {f"c{d:.3g}": {"iso": "langmuir", "law": "L1", "pe_mult": 1.0, "Da": float(d)}
             for d in np.logspace(-1, 3, 9)}
    P = lambda d, b: 1.0 / (1.0 + np.exp(4.0 * (np.log10(d) - np.log10(b))))
    rng = np.random.default_rng(8)
    rows = {}
    for nm, c in cells.items():
        for s in (0.005, 0.02):
            for rep in range(N_REP):
                rows[f"{nm}|{s}|0.0|{rep}|A|strong"] = {"success": bool(rng.uniform() < P(c["Da"], 10))}
            # M7-like: only at sigma = 0.005, and much better there
        for rep in range(N_REP):
            rows[f"{nm}|0.005|0.0|{rep}|M7|strong"] = {"success": bool(rng.uniform() < P(c["Da"], 300))}
    assert _best(rows, cells, lambda c, s, e: True) == "A|strong"


def test_paired_shift_keeps_the_pairing():
    from p2.analysis import paired_shift
    rng = np.random.default_rng(9)
    Da = np.logspace(-1, 3, 9)
    P = lambda d, b: 1.0 / (1.0 + np.exp(4.0 * (np.log10(d) - b)))
    pairs = {float(d): [(float(u < P(d, 1.8)), float(u < P(d, 1.2))) for u in rng.uniform(size=45)]
             for d in Da}
    sh, lo, hi = paired_shift(pairs, n_boot=200)
    assert lo < sh < hi and abs(sh - 0.6) < 0.25
    assert paired_shift({}, n_boot=10) == (None, None, None)


def test_h2b_counts_by_axis():
    from p2.analysis import aggregate_h2b
    w = "discovery fails before identifiability"
    r = aggregate_h2b({"sigma=0.02|eps=0.0|langmuir|pe=1.0": w,
                       "sigma=0.02|eps=0.02|step|pe=1.0": w})
    assert r["counts_by_axis"]["sigma=0.02"][w] == 2 and r["counts_by_axis"]["step"][w] == 1


def test_h2c_withheld_and_strict_falsification():
    """A2.6: with every isotherm withheld there is no H2c verdict; A2.3: falsified only if
    EVERY slice has a verdict below the threshold."""
    from p2_analyze import h2c
    from p2_grid_o1 import N_REP
    cells, o1, m5, ident, rstats = _planted_grid(np.random.default_rng(10), n_rep=N_REP)
    r = h2c(cells, o1, m5, n_boot=20, withheld=("langmuir",))
    assert r["words"].startswith("withheld") and r["h2c_holds"] is None
    flat = {k: {"success": True} for k in m5}              # no crossing -> no verdict
    r = h2c(cells, o1, flat, n_boot=20)
    assert r["h2c_falsified"] is False


def test_descriptive_o23_runs_on_planted_rows():
    from p2_analyze import descriptive_o23
    from p2_grid_o1 import N_REP
    cells, o1, m5, ident, rstats = _planted_grid(np.random.default_rng(11), n_rep=N_REP)
    o2 = {k.replace("|0.02|0.02|", "|0.02|0.02|"): v for k, v in o1.items()}
    o2i = {f"{nm}|0.02|0.02|{r}": {"identifiable": bool(np.random.default_rng(r).uniform() < 0.5)}
           for nm in cells for r in range(3)}
    res = descriptive_o23(cells, o2, o2i, {}, n_boot=20)
    s = res["sigma=0.02|eps=0.02|langmuir|pe=1.0"]
    assert s["O2_best_method"] == "B|strong" and s["O3_da_ident"] is None

# ---- B84: words follow the rules; design-cell coverage; not-evaluated positive control

def test_h2c_words_follow_the_hold_and_falsify_rules():
    """Graded 'moves' words only where H2c holds at that eps; otherwise say it does not hold,
    with the count; 'does not move detectably' only if every slice is below threshold."""
    import p2_analyze as pa
    from p2_grid_o1 import N_REP
    cells, o1, m5, ident, rstats = _planted_grid(np.random.default_rng(12), n_rep=N_REP)
    r = pa.h2c(cells, o1, m5, n_boot=20)
    pe = r["per_eps"][0.02]
    assert pe["holds"] and pe["words"].startswith("EIV moves the boundary by")
    # the referee's case: 3 of 6 detectable -> does not hold, and neither graded words
    r = pa.h2c_eps_rule([0.1, 0.1, 0.2, 0.4, 0.4, 0.4])
    assert not r["holds"] and r["words"].startswith("H2c does not hold at this eps (3 of 6")
    # every slice below the threshold -> the 'does not move detectably' words
    assert pa.h2c_eps_rule([0.1, 0.0, -0.1])["words"].startswith("EIV does not move the boundary detectably")
    # a slice without a verdict blocks the falsifier words
    assert pa.h2c_eps_rule([0.1, None])["words"].startswith("H2c does not hold")
    assert pa.h2c_eps_rule([0.4, 0.4, 0.1])["holds"]


def test_extra_rows_of_one_method_do_not_exclude_the_others():
    """Coverage is checked against the slice's design cells, not the union of what exists:
    a method with rows on cells outside the slice's design keeps nobody out."""
    from p2_analyze import _best
    from p2_grid_o1 import N_REP
    cells = {f"c{d:.3g}": {"iso": "langmuir", "law": "L1", "pe_mult": 1.0, "Da": float(d)}
             for d in np.logspace(-1, 3, 9)}
    P = lambda d, b: 1.0 / (1.0 + np.exp(4.0 * (np.log10(d) - np.log10(b))))
    rng = np.random.default_rng(13)
    rows = {}
    for nm, c in cells.items():
        for rep in range(N_REP):
            u = rng.uniform(size=2)
            rows[f"{nm}|0.02|0.02|{rep}|A|strong"] = {"success": bool(u[0] < P(c["Da"], 30))}
            rows[f"{nm}|0.02|0.02|{rep}|B|strong"] = {"success": bool(u[1] < P(c["Da"], 10))}
    keep = lambda c, s, e: s == 0.02 and e == 0.02
    assert _best(rows, cells, keep) == "A|strong"
    # B also has rows at another (sigma, eps) that the slice excludes: no effect
    for nm in cells:
        for rep in range(N_REP):
            rows[f"{nm}|0.005|0.0|{rep}|B|strong"] = {"success": True}
    assert _best(rows, cells, keep) == "A|strong"


def test_positive_control_without_discovery_rows_is_not_evaluated():
    from p2_analyze import positive_controls
    cells = {"x": {"iso": "langmuir", "law": "L1", "pe_mult": 1.0, "Da": 0.1}}
    ident = {f"x|0.0|0.0|{r}|profile|o1": {"success": True} for r in range(60)}
    out, failed = positive_controls(cells, {}, ident)
    assert out["langmuir"]["passed"] is None and not failed
