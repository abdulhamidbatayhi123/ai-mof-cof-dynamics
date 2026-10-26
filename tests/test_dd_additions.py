"""Tests for the Digital Discovery additions: crossing times, the own-floor solver, the share
statistic and the verdict rule (PREREG_DD_V3 and amendment A1).

    python -m pytest tests/test_dd_additions.py -q
"""
from __future__ import annotations

import numpy as np
import pytest
import torch

import dd_screening_frameworks as dd
from dd_seed_robustness import trunk_floor
from run_l5 import DeepONet


def test_crossing_times_interpolate_on_the_stored_grid():
    t = dd.T_GRID
    outlet = np.clip((t - 0.2) / 0.6, 0, 1)            # linear ramp from t = 0.2 to 0.8
    assert dd.t50_norm(outlet) == pytest.approx(0.5, abs=2e-3)
    assert dd.t90_norm(outlet) == pytest.approx(0.74, abs=2e-3)
    assert dd.t_cross_norm(outlet, 0.5) == dd.t50_norm(outlet)


def test_crossing_time_is_nan_when_never_reached():
    assert np.isnan(dd.t90_norm(np.full(dd.FIELD_RES, 0.5)))


def _model_and_grid(p, seed=0):
    torch.manual_seed(seed)
    m = DeepONet(12, p=p, width=32, depth=3)
    zz, tt = np.meshgrid(np.linspace(0, 1, 48), np.linspace(0, 1, 48), indexing="ij")
    C = torch.tensor(np.stack([zz.ravel(), tt.ravel()], 1), dtype=torch.float32)
    return m, C


@pytest.mark.parametrize("p", [8, 32])
def test_own_floor_recovers_fields_in_the_span(p):
    m, C = _model_and_grid(p)
    with torch.no_grad():
        T = m.trunk(C).view(len(C), 3, p)[:, 0, :]
        U = torch.sigmoid(torch.randn(6, p) * 2 @ T.T + m.bias[0]).numpy()
    floor, conv, _ = trunk_floor(m, C, U)
    assert conv.all()
    assert floor.max() < 1e-4


def test_own_floor_never_exceeds_the_models_own_error():
    m, C = _model_and_grid(16, seed=1)
    rng = np.random.default_rng(0)
    Pz = rng.standard_normal((10, 12)).astype(np.float32)
    U = np.clip(rng.random((10, len(C))), 0, 1)       # fields far from the span
    floor, conv, own = trunk_floor(m, C, U, Pz=Pz)
    assert (floor <= own + 1e-12).all()
    with torch.no_grad():                              # own = the model's prediction, scored the same way
        pred = m(torch.as_tensor(Pz), C)[..., 0].numpy()
    rng_u = U.max(1) - U.min(1)
    model_err = np.sqrt(((pred - U) ** 2).mean(1)) / rng_u
    assert own == pytest.approx(model_err, rel=1e-5)


def test_share_and_verdict_rules():
    import dd_v3a1_analyse as a
    rng = np.random.default_rng(0)
    mats = np.repeat(np.arange(40), 5)
    total = rng.uniform(0.02, 0.04, 200)
    rec_map = a.share_record(0.1 * total, total, mats)       # floor carries 1 % of squared error
    assert rec_map["share_map"] == pytest.approx(0.99, abs=1e-9)
    rec_basis = a.share_record(0.9 * total, total, mats)     # floor carries 81 %
    assert a.verdict({8: rec_map, 16: rec_map, 128: rec_map}) == "the map dominates"
    assert a.verdict({8: rec_basis, 16: rec_basis, 128: rec_basis}) == "the basis binds"
    assert a.verdict({8: rec_map, 16: rec_basis, 128: rec_map}) == "the basis binds"


def test_missing_registered_cells_stop_the_analysis():
    import dd_v3a1_analyse as a
    cells = {f"v2|p16|s42|f{f}": {} for f in range(4)}       # one fold missing
    with pytest.raises(SystemExit):
        a._cells(cells, "v2|p16|s42")
