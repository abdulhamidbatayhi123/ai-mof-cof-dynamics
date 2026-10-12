"""Paper 2 verdicts: H2a-H2d from the grid result files, in the pre-declared words.

Owner of results/p2_verdicts.json. Reads (all written by freeze-guarded drivers):
  results/p2_o1.json         O1 sparse solvers (M2 weak, M2b strong, M3, M4)
  results/p2_o2.json         O2 (mass-balance inversion + the same solvers)
  results/p2_extra_m5.json   M5 EIV best-subset (O1, strong)
  results/p2_extra_m7.json   M7 PySR (O1 subgrid), if it ran
  results/p2_extra_l2.json   the L2 cells (H2d)
  results/p2_extra_o1ident.json   O1 identifiability (H2b, confirmatory)
  results/p2_rstats.json     delta, eps_rec per cell (ground truth)
and the ground-truth manifest. Every rule below is PREREG_P2 s.2 / s.4.3 / s.4.4 as amended
by A1 (s.9):

Replicates 0..N_SEL-1 (15) are the SELECTION set, N_SEL..N_REP-1 the ESTIMATION set (A1).
The best method of a slice is chosen on the selection set only (p2.analysis.select_best);
every boundary that enters a verdict is estimated on the estimation set, so the selection
does not bias the estimate. A method with too few replicates in a slice for both sets is
reported but takes no part in the selection.
H2b  per slice (sigma, eps, isotherm) on O1: Da*_disc of the best rate-law method vs
     Da*_ident (same logistic estimator on 'identifiable'); words by
     p2.analysis.disc_vs_ident at the decision threshold 0.25 decade; the hypothesis-level
     verdict by p2.analysis.aggregate_h2b (two-thirds rule, A1). O2 slices DESCRIPTIVE.
     Sensitivity (A1, descriptive): the same with success requiring k_hat in [k/2, 2k].
H2a  per slice (Pe, isotherm, observation in {O1, O2}), pooling sigma, eps and Da: the
     best method's P(success) against R = delta / sqrt(sigma^2 + eps^2 + eps_rec^2)
     (eps_rec = 0 on O1; R undefined at sigma = eps = 0 on O1 and excluded); words by
     p2.analysis.r_collapse.
H2c  per (isotherm, eps > 0) at sigma = 2 % on O1: shift = log10 Da*_disc(M5) - log10
     Da*_disc(best non-EIV method in the STRONG form); words by p2.analysis.h2c_verdict;
     H2c holds at an eps if the upward shift is >= 0.25 decade (A1).
H2d  descriptive: per L2 cell and (sigma, eps), the success rate of every method.
Positive control (A1): sigma = eps = 0, O1, lowest Da, per isotherm: the best method
     succeeds and k is identifiable in >= 90 % of estimation replicates; if not, verdict
     words for that isotherm are WITHHELD and the failure is reported.

The analysis is a pure function of the loaded rows (verdicts()), tested on simulated
grids with planted boundaries before any real result exists.

    python p2_analyze.py
"""
import json
import os
from collections import defaultdict

import numpy as np

from p2.analysis import (aggregate_h2b, boundary, disc_vs_ident, h2c_verdict, positive_control,
                         r_collapse, refine_levels, select_best)

MDE = 0.25                 # the decision threshold of H2b and H2c (PREREG_P2 s.4.4)
SIGMA_H2C = 0.02
EPS_REFINE = 0.02           # the H2c refinement grid is at sigma = eps = 2 % (PREREG_P2 s.4.4)
N_SEL = 15                 # A1: replicates 0..14 select the best method; 15..59 estimate
RATE_LAW_METHODS_EXCLUDED = {"slow_manifold"}       # M9 targets the algebraic law, not k
WITHHELD = "withheld: the positive control failed for this isotherm (A1)"


def _parse(key):
    name, sigma, eps, rep, method, form = key.split("|")
    return name, float(sigma), float(eps), int(rep), method, form


def _sel(rep):
    return rep < N_SEL


def _est(rep):
    return rep >= N_SEL


def _k_ok(r, k_true):
    k_hat = r.get("k_hat")
    return k_hat is not None and 0.5 * k_true <= k_hat <= 2.0 * k_true


def _by_da(rows, cells, keep, reps=lambda rep: True, metric="success"):
    """{method_label: {Da: [outcomes]}} for the rows passing keep(cell, sigma, eps) and the
    replicate filter. metric 'success' or 'success_k' (success AND k_hat in [k/2, 2k])."""
    out = defaultdict(lambda: defaultdict(list))
    for key, r in rows.items():
        name, sigma, eps, rep, method, form = _parse(key)
        c = cells[name]
        if keep(c, sigma, eps) and reps(rep) and "error" not in r:
            v = bool(r["success"])
            if metric == "success_k":
                v = v and _k_ok(r, c.get("k_LDF", np.nan))
            out[f"{method}|{form}"][c["Da"]].append(float(v))
    return {m: dict(v) for m, v in out.items()}


def _complete(by_m_sel, by_m_est):
    """Methods with replicates in BOTH sets at every Da level of the slice (A1)."""
    ok = {}
    for m, s in by_m_sel.items():
        e = by_m_est.get(m, {})
        if s and e and set(s) == set(e) and all(len(v) for v in e.values()):
            ok[m] = s
    return ok


def _best_and_boundary(rows, cells, keep, n_boot, metric="success"):
    sel = _by_da(rows, cells, keep, _sel)
    est = _by_da(rows, cells, keep, _est, metric)
    best = select_best(_complete(sel, est))
    if best is None:
        return None, None, None, None
    b, lo, hi = boundary(est[best], n_boot=n_boot)
    return best, b, lo, hi


def _main_grid(rows, cells):
    """Rows of main-grid cells only: the H2c refinement cells (A1) enter H2c alone."""
    return {k: v for k, v in rows.items() if not cells[_parse(k)[0]].get("refined")}


def verdicts(cells, o1_rows, o2_rows, ident_rows, rstats, n_boot=2000):
    o1_rows, o2_rows, ident_rows = (_main_grid(r, cells) for r in (o1_rows, o2_rows, ident_rows))
    o1 = {k: v for k, v in o1_rows.items() if _parse(k)[4] not in RATE_LAW_METHODS_EXCLUDED}
    sig_eps = sorted({(_parse(k)[1], _parse(k)[2]) for k in o1})
    isos = sorted({c["iso"] for c in cells.values() if c["law"] == "L1" and c["iso"] != "langmuir_iso"})
    out = {"H2b": {}, "H2b_k_sensitivity": {}, "H2b_O2_descriptive": {}, "H2a": {},
           "positive_control": {}}

    # Positive control (A1): sigma = eps = 0, O1, lowest Da, per isotherm
    failed = set()
    for iso in isos:
        das = sorted({c["Da"] for c in cells.values() if c["iso"] == iso and c["law"] == "L1"})
        if not das:
            continue
        keep = lambda c, ss, ee, iso=iso, d0=das[0]: (c["iso"] == iso and c["law"] == "L1"
                                                       and c["Da"] == d0 and ss == 0.0 and ee == 0.0)
        best = select_best(_complete(_by_da(o1, cells, keep, _sel), _by_da(o1, cells, keep, _est)))
        succ = _by_da(o1, cells, keep, _est).get(best, {}).get(das[0], []) if best else []
        idf = _by_da(ident_rows, cells, keep, _est).get("profile|o1", {}).get(das[0], [])
        if not succ and not idf:          # no zero-noise rows (e.g. a partial grid): not evaluated
            out["positive_control"][iso] = {"passed": None, "note": "no rows at sigma = eps = 0, lowest Da"}
            continue
        passed, detail = positive_control(succ, idf)
        out["positive_control"][iso] = {"passed": passed, "best_method": best, **detail}
        if not passed:
            failed.add(iso)

    # H2b, confirmatory on O1
    for (s, e) in sig_eps:
        for iso in isos:
            keep = lambda c, ss, ee, s=s, e=e, iso=iso: (c["iso"] == iso and c["law"] == "L1"
                                                          and ss == s and ee == e)
            best, est, lo, hi = _best_and_boundary(o1, cells, keep, n_boot)
            id_by_da = _by_da(ident_rows, cells, keep, _est).get("profile|o1", {})
            ident, ilo, ihi = boundary(id_by_da, n_boot=n_boot) if id_by_da else (None, None, None)
            v = disc_vs_ident(est, ident, MDE)
            if iso in failed:
                v = {**v, "words": WITHHELD}
            out["H2b"][f"sigma={s}|eps={e}|{iso}"] = {
                "best_method": best, "da_disc": est, "da_disc_ci": [lo, hi],
                "da_ident": ident, "da_ident_ci": [ilo, ihi], **v}
            kb, kest, klo, khi = _best_and_boundary(o1, cells, keep, n_boot, metric="success_k")
            out["H2b_k_sensitivity"][f"sigma={s}|eps={e}|{iso}"] = {
                "best_method": kb, "da_disc_k": kest, "da_disc_k_ci": [klo, khi],
                **disc_vs_ident(kest, ident, MDE)}
    out["H2b_overall"] = aggregate_h2b({k: v["words"] for k, v in out["H2b"].items()})
    out["H2b_k_sensitivity_overall"] = aggregate_h2b(
        {k: v["words"] for k, v in out["H2b_k_sensitivity"].items()})
    # H2b on O2: descriptive only
    for (s, e) in sorted({(_parse(k)[1], _parse(k)[2]) for k in o2_rows}):
        for iso in isos:
            keep = lambda c, ss, ee, s=s, e=e, iso=iso: (c["iso"] == iso and c["law"] == "L1"
                                                          and ss == s and ee == e)
            best, est, lo, hi = _best_and_boundary(o2_rows, cells, keep, n_boot)
            out["H2b_O2_descriptive"][f"sigma={s}|eps={e}|{iso}"] = {
                "best_method": best, "da_disc": est, "da_disc_ci": [lo, hi]}

    # H2a: slices (Pe, isotherm, observation), pooling sigma, eps, Da
    conds = {}
    for obs, rows in (("O1", o1), ("O2", o2_rows)):
        for iso in isos:
            if iso in failed:
                continue
            for pe in sorted({c["pe_mult"] for c in cells.values()}):
                keep = lambda c, ss, ee, iso=iso, pe=pe: (c["iso"] == iso and c["law"] == "L1"
                                                          and c["pe_mult"] == pe)
                best = select_best(_complete(_by_da(rows, cells, keep, _sel),
                                             _by_da(rows, cells, keep, _est)))
                if best is None:
                    continue
                by_r = defaultdict(list)
                for key, r in rows.items():
                    name, s, e, rep, method, form = _parse(key)
                    c = cells[name]
                    if f"{method}|{form}" != best or not keep(c, s, e) or "error" in r or not _est(rep):
                        continue
                    er = rstats[name]["eps_rec"] if obs == "O2" else 0.0
                    eff = float(np.sqrt(s ** 2 + e ** 2 + er ** 2))
                    if eff == 0:
                        continue                                   # R undefined
                    by_r[round(rstats[name]["delta"] / eff, 12)].append(float(r["success"]))
                if by_r:
                    conds[f"{obs}|{iso}|pe={pe}|{best}"] = dict(by_r)
    out["H2a"] = r_collapse(conds) if conds else {"words": "no verdict: no data"}
    if failed:
        out["H2a"]["isotherms_withheld"] = sorted(failed)
    return out


def h2c(cells, o1_rows, m5_rows, n_boot=2000, withheld=()):
    """H2c per (isotherm, eps > 0) at sigma = 2 % on O1, like for like (strong form); the
    best non-EIV method chosen on the selection set, both boundaries on the estimation set."""
    shifts, detail = {}, {}
    for iso in sorted({c["iso"] for c in cells.values() if c["iso"] != "langmuir_iso"}):
        if iso in withheld:
            continue
        for e in sorted({_parse(k)[2] for k in m5_rows if _parse(k)[2] > 0}):
            keep = lambda c, s, ee, iso=iso, e=e: (c["iso"] == iso and c["law"] == "L1"
                                                   and s == SIGMA_H2C and ee == e
                                                   and (not c.get("refined") or e == EPS_REFINE))
            strong = {k: v for k, v in o1_rows.items() if _parse(k)[5] == "strong"
                      and _parse(k)[4] not in RATE_LAW_METHODS_EXCLUDED}
            best, base, _, _ = _best_and_boundary(strong, cells, keep, n_boot)
            m5 = _by_da(m5_rows, cells, keep, _est)
            eiv = boundary(next(iter(m5.values())), n_boot=n_boot)[0] if m5 else None
            s = None if (base is None or eiv is None) else float(np.log10(eiv) - np.log10(base))
            shifts[f"{iso}|eps={e}"] = s
            detail[f"{iso}|eps={e}"] = {"da_disc_eiv": eiv, "da_disc_best_strong": base,
                                        "best_strong_method": best}
    return {**h2c_verdict(shifts, MDE), "detail": detail}


def h2c_refine_levels(cells, o1_rows):
    """The H2c refinement levels (PREREG_P2 s.4.4, exact by A1): per isotherm, 8 levels
    strictly inside +-0.5 decade of the best STRONG-form non-EIV method's Da*_disc at O1,
    sigma = eps = 2 %, main grid; the method chosen on the selection set and its boundary
    estimated on the estimation set. No EIV result is read."""
    o1_rows = _main_grid(o1_rows, cells)
    out = {}
    for iso in sorted({c["iso"] for c in cells.values() if c["iso"] != "langmuir_iso"}):
        keep = lambda c, s, e, iso=iso: (c["iso"] == iso and c["law"] == "L1"
                                         and s == SIGMA_H2C and e == EPS_REFINE)
        strong = {k: v for k, v in o1_rows.items() if _parse(k)[5] == "strong"
                  and _parse(k)[4] not in RATE_LAW_METHODS_EXCLUDED | {"eiv_best_subset"}}
        best, est, _, _ = _best_and_boundary(strong, cells, keep, n_boot=0 or 1)
        out[iso] = {"best_strong_method": best, "da_disc": est, "levels": refine_levels(est)}
    return out


def main():
    import sys
    load = lambda p: json.load(open(p))["rows"] if os.path.exists(p) else {}
    if "--refine-levels" in sys.argv:
        cells = json.load(open("data/p2/manifest.json"))["cells"]
        lv = h2c_refine_levels(cells, load("results/p2_o1.json"))
        json.dump(lv, open("results/p2_h2c_refine_levels.json", "w"), indent=1)
        print(json.dumps(lv, indent=1))
        return
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    rstats = json.load(open("results/p2_rstats.json"))["cells"]
    o1 = load("results/p2_o1.json")
    o1.update({k: v for k, v in load("results/p2_extra_m7.json").items()})
    m5 = load("results/p2_extra_m5.json")
    out = verdicts(cells, {**o1, **m5}, load("results/p2_o2.json"),
                   load("results/p2_extra_o1ident.json"), rstats)
    failed = [iso for iso, v in out["positive_control"].items() if v["passed"] is False]
    out["H2c"] = h2c(cells, o1, m5, withheld=failed)
    l2 = load("results/p2_extra_l2.json")
    rates = defaultdict(list)
    for key, r in l2.items():
        name, s, e, rep, method, form = _parse(key)
        rates[f"{name}|{s}|{e}|{method}|{form}"].append(float(r.get("success", False)))
    out["H2d_descriptive"] = {k: float(np.mean(v)) for k, v in rates.items()}
    json.dump(out, open("results/p2_verdicts.json", "w"), indent=2, default=str)
    print("positive control:", {k: v["passed"] for k, v in out["positive_control"].items()})
    print("H2b:", out["H2b_overall"]["words"])
    print("H2a:", out["H2a"]["words"])
    print("H2c:", out["H2c"]["words"])
    print("wrote results/p2_verdicts.json")


if __name__ == "__main__":
    main()
