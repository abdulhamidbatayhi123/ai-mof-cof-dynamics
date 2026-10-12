"""Operating characteristics of Paper 2's FROZEN decision rules, by simulation.

The verdicts of PREREG_P2 (frozen at d562f19) are threshold rules on point estimates of
logistic 50 % crossings, not significance tests. A reviewer's power question is therefore
answered by how often each rule returns each verdict when the truth is known. This script
simulates exactly that, with the frozen ingredients only:

  * planted boundaries as in the frozen calibration (tests/test_p2.py): P(success) =
    1 / (1 + exp(a (log10 Da - b))), slope a = 3 per decade (1.5 and 6 as sensitivity),
    9 Da levels logspace(-1, 3), 20 replicates per level (the frozen design) and 45
    (the estimation set of amendment A1, PREREG_P2 s.9);
  * the frozen estimator p2.analysis._fit (unpenalised logistic ML, no crossing -> None);
  * the frozen thresholds: H2b gap +-0.25 decade (the MDE); H2c shift >= log10 2 for
    "moves by {factor}", >= 0.25 for "detectably but by less", <= -0.25 for "DOWN";
    H2a spread < 0.5 "collapses", >= 1.0 "does not collapse".

H2b and H2c compare two boundaries estimated from different outcome sets; they are
simulated here as INDEPENDENT (conservative if, as expected, the two estimates on the same
replicates are positively correlated). H2c's eps = 2 % comparison uses the frozen refined
grid: 8 extra levels strictly inside +-0.5 decade of the non-EIV boundary, added to the 9.
H2a is approximated: each slice pools many cells, simulated as 144 cells (9 Da x 16 (sigma,
eps)) with log10 R spread uniformly over 3 decades, 20 replicates each, 12 slices (3 Pe x 2
isotherms x 2 observation models). No grid cell, no discovery method and no ground truth
is used: this is a property of the estimator and the rules.

    python p2_operating_characteristics.py   -> results/p2_operating_characteristics.json
"""
import json
import time
import warnings

import numpy as np

from p2.analysis import _fit

warnings.filterwarnings("ignore")
OUT = "results/p2_operating_characteristics.json"
DAS = np.log10(np.logspace(-1, 3, 9))
MDE, F2 = 0.25, float(np.log10(2.0))
N_SIM = 1000
B0 = 1.3                       # planted boundary, as in the frozen calibration


def sim_boundary(rng, b, n_rep, slope=3.0, levels=DAS, rising=False):
    x = np.repeat(levels, n_rep)
    sgn = -1.0 if rising else 1.0
    p = 1.0 / (1.0 + np.exp(sgn * slope * (x - b)))
    y = rng.random(x.size) < p
    return _fit(x, y.astype(float), rising)


def single(n_rep, slope):
    rng = np.random.default_rng(1000 + n_rep + int(10 * slope))
    est = [sim_boundary(rng, B0, n_rep, slope) for _ in range(N_SIM)]
    ok = np.array([e for e in est if e is not None])
    return {"n_rep": n_rep, "slope": slope, "sd": round(float(ok.std(ddof=1)), 4),
            "bias": round(float(ok.mean() - B0), 4),
            "p_no_crossing": round(1 - ok.size / N_SIM, 4)}


def h2b(n_rep, gap, slope=3.0):
    rng = np.random.default_rng(2000 + n_rep + int(1000 * gap))
    words = {"before": 0, "with": 0, "outlives": 0, "no_verdict": 0}
    for _ in range(N_SIM):
        d = sim_boundary(rng, B0 + gap / 2, n_rep, slope)   # disc boundary
        i = sim_boundary(rng, B0 - gap / 2, n_rep, slope)   # ident boundary
        if d is None or i is None:
            words["no_verdict"] += 1
            continue
        g = d - i
        words["before" if g <= -MDE else "outlives" if g >= MDE else "with"] += 1
    return {k: round(v / N_SIM, 4) for k, v in words.items()}


def h2c(n_rep, shift, refined, slope=3.0):
    rng = np.random.default_rng(3000 + n_rep + int(1000 * shift) + 7 * refined)
    base = B0
    levels = DAS
    if refined:   # 8 levels strictly inside +-0.5 decade of the non-EIV boundary
        extra = np.linspace(base - 0.5, base + 0.5, 10)[1:-1]
        levels = np.sort(np.concatenate([DAS, extra]))
    words = {"moves_by_factor": 0, "detectably_less_than_2": 0, "not_detectable": 0,
             "down": 0, "no_verdict": 0}
    for _ in range(N_SIM):
        ref = sim_boundary(rng, base, n_rep, slope, levels)
        m5 = sim_boundary(rng, base + shift, n_rep, slope, levels)
        if ref is None or m5 is None:
            words["no_verdict"] += 1
            continue
        s = m5 - ref
        if s >= F2:
            words["moves_by_factor"] += 1
        elif s >= MDE:
            words["detectably_less_than_2"] += 1
        elif s <= -MDE:
            words["down"] += 1
        else:
            words["not_detectable"] += 1
    return {k: round(v / N_SIM, 4) for k, v in words.items()}


def h2a(n_rep, true_spread, n_slices=12, slope=3.0, n_sim=300):
    """True R* identical in all slices (true_spread = 0), or split into two groups
    true_spread apart. Returns the probability of each verdict."""
    rng = np.random.default_rng(4000 + n_rep + int(100 * true_spread))
    words = {"collapses": 0, "inconclusive": 0, "does_not_collapse": 0, "no_verdict": 0}
    for _ in range(n_sim):
        rs = []
        for s in range(n_slices):
            b = 0.0 + (true_spread if s % 2 else 0.0)
            levels = rng.uniform(b - 1.5, b + 1.5, 144)      # 144 cells' log10 R values
            e = sim_boundary(rng, b, n_rep, slope, levels, rising=True)
            if e is not None:
                rs.append(e)
        if len(rs) < 2:
            words["no_verdict"] += 1
            continue
        sp = max(rs) - min(rs)
        words["collapses" if sp < 0.5 else "does_not_collapse" if sp >= 1.0 else "inconclusive"] += 1
    return {k: round(v / n_sim, 4) for k, v in words.items()}


def selection_bias(n_methods=6, n_sel=20, n_est=40, n_sim=500, slope=3.0):
    """Best-of-K selection (PREREG_P2 s.4.3) with K methods whose TRUE boundaries are equal.
    'same': select the largest Da* and report it from the same replicates (frozen rule).
    'split': select on n_sel replicates, report the chosen method's boundary from n_est
    independent replicates (amendment A1). Methods are simulated independently, which
    maximises the bias of 'same' (methods sharing replicates are positively correlated)."""
    rng = np.random.default_rng(5000 + n_methods)
    same, split = [], []
    for _ in range(n_sim):
        sel = [sim_boundary(rng, B0, n_sel + n_est, slope) for _ in range(n_methods)]
        sel = [b for b in sel if b is not None]
        if sel:
            same.append(max(sel) - B0)
        pick = [sim_boundary(rng, B0, n_sel, slope) for _ in range(n_methods)]
        if any(p is not None for p in pick):
            est = sim_boundary(rng, B0, n_est, slope)     # chosen method, fresh replicates
            if est is not None:
                split.append(est - B0)
    return {"n_methods": n_methods, "n_sel": n_sel, "n_est": n_est,
            "bias_same_replicates_decade": round(float(np.mean(same)), 4),
            "sd_same": round(float(np.std(same, ddof=1)), 4),
            "bias_split_decade": round(float(np.mean(split)), 4),
            "sd_split": round(float(np.std(split, ddof=1)), 4)}


def amendment():
    """Evidence for amendment A1: replicate counts and the selection split."""
    t0 = time.time()
    res = {"h2b_gap_0.40": {str(n): h2b(n, 0.40) for n in (40, 45, 50)},
           "h2b_gap_0": {str(n): h2b(n, 0.0) for n in (40, 45, 50)},
           "h2b_gap_0.40_slope_1.5": {str(n): h2b(n, 0.40, slope=1.5) for n in (40, 50)},
           "h2c_main_grid_n40": {f"{s:.2f}": h2c(40, s, False) for s in (0.0, 0.40)},
           "selection": [selection_bias(6, 20, 40), selection_bias(6, 10, 50)]}
    res["runtime_s"] = round(time.time() - t0, 1)
    json.dump(res, open("results/p2_operating_characteristics_a1.json", "w", encoding="utf-8"), indent=1)
    print(json.dumps(res, indent=1))


def h2a_cells(n_rep, true_spread, n_cells, n_slices=12, slope=3.0, n_sim=300):
    """h2a() with a chosen number of cells per slice (O1 slices have 135: 9 Da x 15 (sigma,
    eps) once sigma = eps = 0 is excluded; O2 slices 144)."""
    rng = np.random.default_rng(6000 + n_rep + int(100 * true_spread) + n_cells)
    words = {"collapses": 0, "inconclusive": 0, "does_not_collapse": 0, "no_verdict": 0}
    for _ in range(n_sim):
        rs = []
        for s in range(n_slices):
            b = true_spread if s % 2 else 0.0
            e = sim_boundary(rng, b, n_rep, slope, rng.uniform(b - 1.5, b + 1.5, n_cells), rising=True)
            if e is not None:
                rs.append(e)
        if len(rs) < 2:
            words["no_verdict"] += 1
            continue
        sp = max(rs) - min(rs)
        words["collapses" if sp < 0.5 else "does_not_collapse" if sp >= 1.0 else "inconclusive"] += 1
    return {k: round(v / n_sim, 4) for k, v in words.items()}


def amendment2():
    """Evidence for amendment A2: H2a just below its threshold with O1's 135 cells, the
    selection bias with a pool of 9 methods, and H2b at 0.35 decade."""
    t0 = time.time()
    res = {"h2a_135_cells_n45": {f"{t:.2f}": h2a_cells(45, t, 135) for t in (0.0, 0.25, 0.40, 0.5, 1.0)},
           "selection_9_methods": selection_bias(9, 15, 45),
           "h2b_n45_gap_0.35": h2b(45, 0.35)}
    res["runtime_s"] = round(time.time() - t0, 1)
    json.dump(res, open("results/p2_operating_characteristics_a2.json", "w", encoding="utf-8"), indent=1)
    print(json.dumps(res, indent=1))


def main():
    import sys
    if "--amendment" in sys.argv:
        return amendment()
    if "--amendment2" in sys.argv:
        return amendment2()
    t0 = time.time()
    res = {"model": "frozen planted logistic, 9 Da levels logspace(-1,3), b = 1.3, slope 3/decade",
           "n_sim": N_SIM, "thresholds": {"mde": MDE, "factor2": round(F2, 4),
                                          "h2a": [0.5, 1.0]},
           "single_boundary": [single(n, a) for n in (20, 45) for a in (1.5, 3.0, 6.0)],
           "h2b": {str(n): {f"{g:.2f}": h2b(n, g) for g in (0.0, 0.25, 0.30, 0.40, 0.50, 0.75, 1.0)}
                   for n in (20, 45)},
           "h2c_refined_grid": {str(n): {f"{s:.2f}": h2c(n, s, True) for s in (0.0, 0.25, F2, 0.40, 0.50, 0.75, 1.0)}
                                for n in (20, 45)},
           "h2c_main_grid": {str(n): {f"{s:.2f}": h2c(n, s, False) for s in (0.0, F2, 0.40, 0.50, 1.0)}
                             for n in (20, 45)},
           "h2a_12_slices": {str(n): {f"{t:.1f}": h2a(n, t) for t in (0.0, 0.5, 1.0, 1.5)} for n in (20, 45)},
           "h2b_slope_1.5_n45": {f"{g:.2f}": h2b(45, g, slope=1.5) for g in (0.0, 0.40, 0.50, 0.75)},
           "selection": [selection_bias(6, 15, 45)]}
    res["runtime_s"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
