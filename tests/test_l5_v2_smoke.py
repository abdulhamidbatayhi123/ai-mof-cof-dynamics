"""Smoke test for run_l5_v2.py / analyze_l5_v2.py on a TINY copy of dataset v2.

Builds a throwaway root with 3 materials x 6 conditions from each of folds 0 and 1
(36 samples, ~28 MB on disk, ~7 MB resident at 128x128), runs 2 folds x 1 family x
2 p x 1 lr x 1 seed x 30 steps, then the step arm and the analyzer. Minutes, not hours.
Never touches results/ except READING the fold map and calibration file.
"""
from __future__ import annotations

import json
import os
import shutil
import sys

import numpy as np
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
os.chdir(REPO)

import run_l5_v2  # noqa: E402
import analyze_l5_v2  # noqa: E402
import v2_common  # noqa: E402

SMOKE = ["--only-folds", "0", "1", "--families", "deeponet", "--ps", "8", "16",
         "--lrs", "1e-2", "--seeds", "42", "--steps", "30", "--batch", "4",
         "--n-pts", "256", "--train-eval-cap", "8", "--threads", "2"]


@pytest.fixture(scope="module")
def tiny_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("pv2")
    man = json.load(open(os.path.join(v2_common.ROOT_V2, "manifest.json")))
    m2f = {int(k): int(v) for k, v in json.load(open(v2_common.FOLDS_FILE))["material_to_fold"].items()}
    keep_mats = [m for f in (0, 1) for m in sorted(k for k, v in m2f.items() if v == f)[:3]]
    samples = []
    for m in keep_mats:
        samples += [s for s in man["samples"] if s["mat"] == m][:6]
    man["samples"] = samples
    json.dump(man, open(root / "manifest.json", "w"))
    for s in samples:
        name = f"m{s['mat']:04d}_c{s['cond']:04d}.npy"
        shutil.copy(os.path.join(v2_common.ROOT_V2, name), root / name)
    return str(root)


@pytest.fixture(scope="module")
def smoke_run(tiny_root, tmp_path_factory):
    out = str(tmp_path_factory.mktemp("res") / "l5_smoke.json")
    calls = []
    orig = run_l5_v2.assert_disjoint

    def spy(a, b, what):
        calls.append((np.asarray(a).copy(), np.asarray(b).copy(), what))
        return orig(a, b, what)

    run_l5_v2.assert_disjoint = spy
    try:
        run_l5_v2.main(["--root", tiny_root, "--out", out] + SMOKE)
    finally:
        run_l5_v2.assert_disjoint = orig
    return out, calls, tiny_root


def test_results_nested_keys(smoke_run):
    out, _, _ = smoke_run
    r = json.load(open(out))
    assert r["n_folds"] == 5 and "fold_seed" in r and r["fold_file"] == v2_common.FOLDS_FILE
    assert r["design"] == "folds" and r["root"].endswith("pv2") or "pv2" in r["root"]
    for f in ("0", "1"):
        F = r["folds"][f]
        for p in ("8", "16"):
            cell = F["arms"]["deeponet"][p]["1e-02"]["42"]
            assert set(cell) >= {"train", "test", "width", "n_params", "steps"}
            t = cell["test"]
            assert len(t["per_sample_nrmse_c"]) == len(t["material_ids"]) == len(t["condition_ids"]) == 18
            fl = F["pod_floor_per_sample"][p]
            assert fl["material_ids"] == t["material_ids"] and fl["condition_ids"] == t["condition_ids"]
            assert np.isfinite(t["c"]) and "per_sample_nrmse_c" not in cell["train"]


def test_scalers_never_see_held_out(smoke_run):
    _, calls, _ = smoke_run
    scaler = [c for c in calls if "parameter scaler" in c[2]]
    floor = [c for c in calls if "POD floor" in c[2]]
    assert len(scaler) == 2 and len(floor) == 4
    for tr, te, what in calls:
        v2_common.assert_disjoint(tr, te, what)          # raises on any overlap
        assert np.intersect1d(tr, te).size == 0


def test_resume_skips_completed(smoke_run, monkeypatch):
    out, _, root = smoke_run
    before = open(out).read()

    def boom(*a, **k):
        raise AssertionError("resume re-ran a completed cell")

    monkeypatch.setattr(run_l5_v2, "train_eval", boom)
    monkeypatch.setattr(run_l5_v2, "pod_floor_c", boom)
    run_l5_v2.main(["--root", root, "--out", out] + SMOKE)
    assert json.load(open(out)) == json.loads(before)


def test_step_arm_and_analyzer(smoke_run, tmp_path):
    out, _, root = smoke_run
    steps_out = str(tmp_path / "l5_steps.json")
    run_l5_v2.main(["--root", root, "--out", steps_out, "--arm", "steps", "--steps-lr", "1e-2",
                    "--steps-fold", "0", "--steps-grid", "20", "40", "--steps-ps", "8",
                    "--seeds", "42", "--batch", "4", "--n-pts", "256", "--train-eval-cap", "8"])
    s = json.load(open(steps_out))
    assert set(s["folds"]["0"]["arms"]["deeponet"]["8"]["1e-02"]) == {"20", "40"}

    verdict = str(tmp_path / "l5_v2_verdict.json")
    v = analyze_l5_v2.main(["--res", out, "--steps-res", steps_out, "--out", verdict,
                            "--min-seeds", "1", "--mde-trials", "5"])
    assert os.path.exists(verdict)
    assert v["provisional"] and not v["complete"]
    assert v["folds_used"] == [0, 1] and v["n_boot"] == 4000
    assert v["alpha"] == v2_common.alpha_for("folds")[0]
    assert "deeponet_p16" in v["paired_vs_smallest_p"]
    if not v["paired_vs_smallest_p"]["deeponet_p16"]["significant"]:
        assert "deeponet_p16" in v["mde"]
    assert isinstance(v["step_sensitivity"], dict)
