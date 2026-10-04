"""Paper 2 verdicts: H2a-H2d from the grid result files, in the pre-declared words.

Owner of results/p2_verdicts.json. Reads (all written by freeze-guarded drivers):
  results/p2_o1.json         O1 sparse solvers (M2 weak, M2b strong, M3, M4)
  results/p2_o2.json         O2 (mass-balance inversion + the same solvers)
  results/p2_extra_m5.json   M5 EIV best-subset (O1, strong)
  results/p2_extra_m7.json   M7 PySR (O1 subgrid), if it ran
  results/p2_extra_l2.json   the L2 cells (H2d)
  results/p2_extra_o1ident.json   O1 identifiability (H2b, confirmatory)
  results/p2_rstats.json     delta, eps_rec per cell (ground truth)
and the ground-truth manifest. Every rule below is PREREG_P2 §2 / §4.3 / §4.4:

H2b  per slice (sigma, eps, isotherm) on O1: Da*_disc of the best rate-law method (the
     largest Da*_disc; interval carries the selection) vs Da*_ident (same logistic
     estimator on 'identifiable'); words by p2.analysis.disc_vs_ident at MDE 0.25.
     O2 slices are computed the same way and labelled DESCRIPTIVE (no verdict word).
H2a  per slice (Pe, isotherm, observation in {O1, O2}), pooling sigma, eps and Da: the
     best method's P(success) against R = delta / sqrt(sigma^2 + eps^2 + eps_rec^2)
     (eps_rec = 0 on O1; R undefined at sigma = eps = 0 on O1 and excluded); words by
     p2.analysis.r_collapse.
H2c  per (isotherm, eps > 0) at sigma = 2 % on O1: shift = log10 Da*_disc(M5) - log10
     Da*_disc(best non-EIV method in the STRONG form); words by p2.analysis.h2c_verdict.
H2d  descriptive: per L2 cell and (sigma, eps), the success rate of every method.

The analysis is a pure function of the loaded rows (verdicts()), tested on simulated
grids with planted boundaries before any real result exists.

    python p2_analyze.py
"""
import json
import os
from collections import defaultdict

import numpy as np

from p2.analysis import best_method_boundary, boundary, disc_vs_ident, h2c_verdict, r_collapse

MDE = 0.25
SIGMA_H2C = 0.02
RATE_LAW_METHODS_EXCLUDED = {"slow_manifold"}       # M9 targets the algebraic law, not k


def _parse(key):
    name, sigma, eps, rep, method, form = key.split("|")
    return name, float(sigma), float(eps), int(rep), method, form


def _by_da(rows, cells, keep):
    """{method_label: {Da: [successes]}} for the rows passing keep(cell, sigma, eps)."""
    out = defaultdict(lambda: defaultdict(list))
    for key, r in rows.items():
        name, sigma, eps, rep, method, form = _parse(key)
        c = cells[name]
        if keep(c, sigma, eps) and "error" not in r:
            out[f"{method}|{form}"][c["Da"]].append(float(r["success"]))
    return {m: dict(v) for m, v in out.items()}


def verdicts(cells, o1_rows, o2_rows, ident_rows, rstats, n_boot=2000):
    o1 = {k: v for k, v in o1_rows.items() if _parse(k)[4] not in RATE_LAW_METHODS_EXCLUDED}
    sig_eps = sorted({(_parse(k)[1], _parse(k)[2]) for k in o1})
    isos = sorted({c["iso"] for c in cells.values() if c["law"] == "L1" and c["iso"] != "langmuir_iso"})
    out = {"H2b": {}, "H2b_O2_descriptive": {}, "H2a": {}, "H2c": {}}

    # H2b, confirmatory on O1
    for (s, e) in sig_eps:
        for iso in isos:
            keep = lambda c, ss, ee: c["iso"] == iso and c["law"] == "L1" and ss == s and ee == e
            by_m = _by_da(o1, cells, keep)
            id_by_da = _by_da(ident_rows, cells, keep).get("profile|o1", {})
            best, est, lo, hi = best_method_boundary(by_m, n_boot=n_boot) if by_m else (None,) * 4
            ident, ilo, ihi = boundary(id_by_da, n_boot=n_boot) if id_by_da else (None, None, None)
            out["H2b"][f"sigma={s}|eps={e}|{iso}"] = {
                "best_method": best, "da_disc": est, "da_disc_ci": [lo, hi],
                "da_ident": ident, "da_ident_ci": [ilo, ihi], **disc_vs_ident(est, ident, MDE)}
    # H2b on O2: descriptive only
    for (s, e) in sorted({(_parse(k)[1], _parse(k)[2]) for k in o2_rows}):
        for iso in isos:
            keep = lambda c, ss, ee: c["iso"] == iso and c["law"] == "L1" and ss == s and ee == e
            by_m = _by_da(o2_rows, cells, keep)
            best, est, lo, hi = best_method_boundary(by_m, n_boot=n_boot) if by_m else (None,) * 4
            out["H2b_O2_descriptive"][f"sigma={s}|eps={e}|{iso}"] = {
                "best_method": best, "da_disc": est, "da_disc_ci": [lo, hi]}

    # H2a: slices (Pe, isotherm, observation), pooling sigma, eps, Da
    conds = {}
    for obs, rows in (("O1", o1), ("O2", o2_rows)):
        for iso in isos:
            for pe in sorted({c["pe_mult"] for c in cells.values()}):
                keep = lambda c, ss, ee: c["iso"] == iso and c["law"] == "L1" and c["pe_mult"] == pe
                by_m = _by_da(rows, cells, keep)
                if not by_m:
                    continue
                best = best_method_boundary(by_m, n_boot=0 or 1)[0] or max(
                    by_m, key=lambda m: np.mean([np.mean(v) for v in by_m[m].values()]))
                by_r = defaultdict(list)
                for key, r in rows.items():
                    name, s, e, rep, method, form = _parse(key)
                    c = cells[name]
                    if f"{method}|{form}" != best or not keep(c, s, e) or "error" in r:
                        continue
                    er = rstats[name]["eps_rec"] if obs == "O2" else 0.0
                    eff = float(np.sqrt(s ** 2 + e ** 2 + er ** 2))
                    if eff == 0:
                        continue                                   # R undefined
                    by_r[round(rstats[name]["delta"] / eff, 12)].append(float(r["success"]))
                if by_r:
                    conds[f"{obs}|{iso}|pe={pe}|{best}"] = dict(by_r)
    out["H2a"] = r_collapse(conds) if conds else {"words": "no verdict: no data"}
    return out


def h2c(cells, o1_rows, m5_rows, n_boot=2000):
    """H2c per (isotherm, eps > 0) at sigma = 2 % on O1, like for like (strong form)."""
    shifts, detail = {}, {}
    for iso in sorted({c["iso"] for c in cells.values() if c["iso"] != "langmuir_iso"}):
        for e in sorted({_parse(k)[2] for k in m5_rows if _parse(k)[2] > 0}):
            keep = lambda c, s, ee: c["iso"] == iso and c["law"] == "L1" and s == SIGMA_H2C and ee == e
            strong = {k: v for k, v in o1_rows.items() if _parse(k)[5] == "strong"
                      and _parse(k)[4] not in RATE_LAW_METHODS_EXCLUDED}
            _, base, _, _ = best_method_boundary(_by_da(strong, cells, keep), n_boot=n_boot)
            m5 = _by_da(m5_rows, cells, keep)
            eiv = boundary(next(iter(m5.values())), n_boot=n_boot)[0] if m5 else None
            s = None if (base is None or eiv is None) else float(np.log10(eiv) - np.log10(base))
            shifts[f"{iso}|eps={e}"] = s
            detail[f"{iso}|eps={e}"] = {"da_disc_eiv": eiv, "da_disc_best_strong": base}
    return {**h2c_verdict(shifts, MDE), "detail": detail}


def main():
    load = lambda p: json.load(open(p))["rows"] if os.path.exists(p) else {}
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    rstats = json.load(open("results/p2_rstats.json"))["cells"]
    o1 = load("results/p2_o1.json")
    o1.update({k: v for k, v in load("results/p2_extra_m7.json").items()})
    m5 = load("results/p2_extra_m5.json")
    out = verdicts(cells, {**o1, **m5}, load("results/p2_o2.json"),
                   load("results/p2_extra_o1ident.json"), rstats)
    out["H2c"] = h2c(cells, o1, m5)
    l2 = load("results/p2_extra_l2.json")
    rates = defaultdict(list)
    for key, r in l2.items():
        name, s, e, rep, method, form = _parse(key)
        rates[f"{name}|{s}|{e}|{method}|{form}"].append(float(r.get("success", False)))
    out["H2d_descriptive"] = {k: float(np.mean(v)) for k, v in rates.items()}
    json.dump(out, open("results/p2_verdicts.json", "w"), indent=2, default=str)
    print("H2a:", out["H2a"]["words"])
    print("H2c:", out["H2c"]["words"])
    print("wrote results/p2_verdicts.json")


if __name__ == "__main__":
    main()
