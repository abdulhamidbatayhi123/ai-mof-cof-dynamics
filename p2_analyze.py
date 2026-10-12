"""Paper 2 verdicts: H2a-H2d from the grid result files, in the pre-declared words.

Owner of results/p2_verdicts.json. Reads (all written by freeze-guarded drivers):
  results/p2_o1.json         O1 sparse solvers (M2 weak, M2b strong, M3, M4)
  results/p2_o2.json         O2 (mass-balance inversion + the same solvers)
  results/p2_extra_m5.json   M5 EIV best-subset (O1, strong)
  results/p2_extra_m7.json   M7 PySR (O1 subgrid, Pe x1), if it ran
  results/p2_extra_l2.json   the L2 cells (H2d)
  results/p2_extra_o1ident.json   O1 identifiability (H2b, confirmatory)
  results/p2_rstats.json     delta, eps_rec per cell (ground truth)
and the ground-truth manifest. Every rule below is PREREG_P2 s.2 / s.4.3 / s.4.4 as amended
by A1 and A2 (s.9):

Replicates 0..N_SEL-1 (15) are the SELECTION set, N_SEL..N_REP-1 the ESTIMATION set (A1).
The best method of a slice is chosen on the selection set only (p2.analysis.select_best);
every boundary that enters a verdict is estimated on the estimation set. A method without
replicates in both sets at every Da level of a slice takes no part in the selection.
A row that raised an error counts as a FAILURE (success, identifiable = False), never
dropped (A2). M5 is given the true error levels, so it is an ORACLE for the purpose of
H2a/H2b and takes no part in their selection; it is used in H2c only (A2).
H2b  per slice (sigma, eps, isotherm, Pe) on O1 (Pe a slicing axis, A2): Da*_disc of the
     best rate-law method vs Da*_ident (same logistic estimator on 'identifiable'); words
     by p2.analysis.disc_vs_ident at the decision threshold 0.25 decade; every method's own
     Da*_disc reported; the hypothesis-level verdict by p2.analysis.aggregate_h2b
     (two-thirds rule, A1) over the slices of the isotherms whose positive control passed.
     O2 slices DESCRIPTIVE. Sensitivity (A1, descriptive): success also requiring
     k_hat in [k/2, 2k].
H2a  per slice (Pe, isotherm, observation in {O1, O2}), pooling sigma, eps and Da: the
     best method's P(success) against R = delta / sqrt(sigma^2 + eps^2 + eps_rec^2)
     (eps_rec = 0 on O1; R undefined at sigma = eps = 0 on O1 and excluded); words and the
     spread's bootstrap interval by p2.analysis.r_collapse.
H2c  per slice (isotherm, Pe, eps > 0) at sigma = 2 % on O1 (A2): shift = log10
     Da*_disc(M5) - log10 Da*_disc(best non-EIV method in the STRONG form), with a paired
     bootstrap interval; the shift against the best non-EIV method over BOTH forms reported
     descriptively. H2c holds at an eps if the shift is >= 0.25 decade in at least two
     thirds of that eps's slices with a verdict; it is falsified if the shift is below 0.25
     in every slice at every eps; the size is graded on the median shift (A2).
H2d  descriptive: per L2 cell and (sigma, eps), the success rate of every method.
Positive control (A1): sigma = eps = 0, O1, lowest Da, per isotherm (all Pe): the best
     non-oracle method succeeds and k is identifiable in >= 90 % of estimation replicates;
     if not, every verdict for that isotherm is WITHHELD (H2a, H2b, its sensitivity, H2c).

The analysis is a pure function of the loaded rows (verdicts(), h2c()), tested on simulated
grids with planted boundaries before any real result exists.

    python p2_analyze.py                  # verdicts -> results/p2_verdicts.json
    python p2_analyze.py --refine-levels  # H2c refinement levels (before p2_generate --refine)
"""
import json
import os
from collections import defaultdict

import numpy as np

from p2.analysis import (aggregate_h2b, boundary, disc_vs_ident, h2c_verdict, paired_shift,
                         positive_control, r_collapse, refine_levels, select_best)

MDE = 0.25                 # the decision threshold of H2b and H2c (PREREG_P2 s.4.4, A1)
SIGMA_H2C = 0.02
EPS_REFINE = 0.02          # the H2c refinement grid is at sigma = eps = 2 % (PREREG_P2 s.4.4)
N_SEL = 15                 # A1: replicates 0..14 select the best method; 15..59 estimate
RATE_LAW_METHODS_EXCLUDED = {"slow_manifold"}       # M9 targets the algebraic law, not k
ORACLE = {"eiv_best_subset"}                         # A2: M5 knows sigma and eps
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


def _outcome(r, k_true, metric):
    """A2: an error row is a failure, never dropped (PREREG_P2 s.4.3)."""
    if "error" in r:
        return 0.0
    v = bool(r["success"])
    if metric == "success_k":
        v = v and _k_ok(r, k_true)
    return float(v)


def _by_da(rows, cells, keep, reps=lambda rep: True, metric="success"):
    """{method_label: {Da: [outcomes]}} for the rows passing keep(cell, sigma, eps) and the
    replicate filter. metric 'success' or 'success_k' (success AND k_hat in [k/2, 2k])."""
    out = defaultdict(lambda: defaultdict(list))
    for key, r in rows.items():
        name, sigma, eps, rep, method, form = _parse(key)
        c = cells[name]
        if keep(c, sigma, eps) and reps(rep):
            out[f"{method}|{form}"][c["Da"]].append(_outcome(r, c.get("k_LDF", np.nan), metric))
    return {m: dict(v) for m, v in out.items()}


def _complete(by_m_sel, by_m_est):
    """Methods with replicates in BOTH sets at every Da level of the slice (A1)."""
    ok = {}
    levels = set().union(*[set(s) for s in by_m_est.values()]) if by_m_est else set()
    for m, s in by_m_sel.items():
        e = by_m_est.get(m, {})
        if s and e and set(s) == set(e) == levels and all(len(v) for v in e.values()):
            ok[m] = s
    return ok


def _coverage(rows, cells, keep, reps):
    """{method_label: set of (cell, sigma, eps)} it was run on within the slice."""
    cov = defaultdict(set)
    for key in rows:
        name, sigma, eps, rep, method, form = _parse(key)
        if keep(cells[name], sigma, eps) and reps(rep):
            cov[f"{method}|{form}"].add((name, sigma, eps))
    return cov


def _best(rows, cells, keep, metric="success"):
    """The best method of a slice, chosen on the selection replicates with the analysis's
    own metric. Only methods run on EVERY (cell, sigma, eps) of the slice in both sets take
    part, so no method is compared on different cells (A2.2; e.g. M7, run on 4 of the 16
    (sigma, eps) pairs, cannot win an H2a slice that pools all 16)."""
    sel = _by_da(rows, cells, keep, _sel, metric)
    est = _by_da(rows, cells, keep, _est, metric)
    cs, ce = _coverage(rows, cells, keep, _sel), _coverage(rows, cells, keep, _est)
    full = set().union(*ce.values()) if ce else set()
    cand = {m: v for m, v in _complete(sel, est).items() if cs.get(m) == full and ce.get(m) == full}
    return select_best(cand)


def _best_and_boundary(rows, cells, keep, n_boot, metric="success"):
    best = _best(rows, cells, keep, metric)
    if best is None:
        return None, None, None, None
    est = _by_da(rows, cells, keep, _est, metric)
    b, lo, hi = boundary(est[best], n_boot=n_boot)
    return best, b, lo, hi


def _main_grid(rows, cells):
    """Rows of main-grid cells only: the H2c refinement cells (A1) enter H2c alone."""
    return {k: v for k, v in rows.items() if not cells[_parse(k)[0]].get("refined")}


def _no_oracle(rows):
    return {k: v for k, v in rows.items()
            if _parse(k)[4] not in RATE_LAW_METHODS_EXCLUDED | ORACLE}


def _isotherms(cells):
    return sorted({c["iso"] for c in cells.values() if c["law"] == "L1" and c["iso"] != "langmuir_iso"})


def _pes(cells):
    return sorted({c["pe_mult"] for c in cells.values() if c["iso"] != "langmuir_iso"})


def positive_controls(cells, o1, ident_rows):
    """A1: per isotherm, sigma = eps = 0, O1, lowest Da (all Pe), estimation replicates."""
    out, failed = {}, set()
    for iso in _isotherms(cells):
        das = sorted({c["Da"] for c in cells.values() if c["iso"] == iso and c["law"] == "L1"
                      and not c.get("refined")})
        keep = lambda c, ss, ee, iso=iso, d0=das[0]: (c["iso"] == iso and c["law"] == "L1"
                                                       and c["Da"] == d0 and ss == 0.0 and ee == 0.0)
        best = _best(o1, cells, keep)
        succ = _by_da(o1, cells, keep, _est).get(best, {}).get(das[0], []) if best else []
        idf = _by_da(ident_rows, cells, keep, _est).get("profile|o1", {}).get(das[0], [])
        if not succ and not idf:          # no zero-noise rows (e.g. a partial grid): not evaluated
            out[iso] = {"passed": None, "note": "no rows at sigma = eps = 0, lowest Da"}
            continue
        passed, detail = positive_control(succ, idf)
        out[iso] = {"passed": passed, "best_method": best, **detail}
        if not passed:
            failed.add(iso)
    return out, failed


def verdicts(cells, o1_rows, o2_rows, ident_rows, rstats, n_boot=2000):
    o1_rows, o2_rows, ident_rows = (_main_grid(r, cells) for r in (o1_rows, o2_rows, ident_rows))
    o1, o2 = _no_oracle(o1_rows), _no_oracle(o2_rows)
    sig_eps = sorted({(_parse(k)[1], _parse(k)[2]) for k in o1})
    isos, pes = _isotherms(cells), _pes(cells)
    out = {"H2b": {}, "H2b_k_sensitivity": {}, "H2b_O2_descriptive": {}, "H2a": {}}
    out["positive_control"], failed = positive_controls(cells, o1, ident_rows)

    # H2b, confirmatory on O1; slices (sigma, eps, isotherm, Pe)
    for (s, e) in sig_eps:
        for iso in isos:
            for pe in pes:
                key = f"sigma={s}|eps={e}|{iso}|pe={pe}"
                keep = lambda c, ss, ee, s=s, e=e, iso=iso, pe=pe: (
                    c["iso"] == iso and c["law"] == "L1" and c["pe_mult"] == pe and ss == s and ee == e)
                best, est, lo, hi = _best_and_boundary(o1, cells, keep, n_boot)
                id_by_da = _by_da(ident_rows, cells, keep, _est).get("profile|o1", {})
                ident, ilo, ihi = boundary(id_by_da, n_boot=n_boot) if id_by_da else (None, None, None)
                per_method = {m: boundary(v, n_boot=0)[0]
                              for m, v in _by_da(o1, cells, keep, _est).items()}
                v = disc_vs_ident(est, ident, MDE)
                kb, kest, klo, khi = _best_and_boundary(o1, cells, keep, n_boot, metric="success_k")
                kv = disc_vs_ident(kest, ident, MDE)
                if iso in failed:
                    v, kv = {**v, "words": WITHHELD}, {**kv, "words": WITHHELD}
                out["H2b"][key] = {"best_method": best, "da_disc": est, "da_disc_ci": [lo, hi],
                                   "da_ident": ident, "da_ident_ci": [ilo, ihi],
                                   "da_disc_by_method": per_method, **v}
                out["H2b_k_sensitivity"][key] = {"best_method": kb, "da_disc_k": kest,
                                                 "da_disc_k_ci": [klo, khi], **kv}
    passing = lambda d: {k: v["words"] for k, v in d.items() if v["words"] != WITHHELD}
    out["H2b_overall"] = {**aggregate_h2b(passing(out["H2b"])), "isotherms_withheld": sorted(failed)}
    out["H2b_k_sensitivity_overall"] = {**aggregate_h2b(passing(out["H2b_k_sensitivity"])),
                                        "isotherms_withheld": sorted(failed)}
    if failed and len(failed) == len(isos):
        out["H2b_overall"]["words"] = out["H2b_k_sensitivity_overall"]["words"] = WITHHELD
    # H2b on O2: descriptive only
    for (s, e) in sorted({(_parse(k)[1], _parse(k)[2]) for k in o2}):
        for iso in isos:
            for pe in pes:
                keep = lambda c, ss, ee, s=s, e=e, iso=iso, pe=pe: (
                    c["iso"] == iso and c["law"] == "L1" and c["pe_mult"] == pe and ss == s and ee == e)
                best, est, lo, hi = _best_and_boundary(o2, cells, keep, n_boot)
                out["H2b_O2_descriptive"][f"sigma={s}|eps={e}|{iso}|pe={pe}"] = {
                    "best_method": best, "da_disc": est, "da_disc_ci": [lo, hi]}

    # H2a: slices (Pe, isotherm, observation), pooling sigma, eps, Da
    conds = {}
    for obs, rows in (("O1", o1), ("O2", o2)):
        for iso in isos:
            if iso in failed:
                continue
            for pe in pes:
                keep = lambda c, ss, ee, iso=iso, pe=pe, obs=obs: (
                    c["iso"] == iso and c["law"] == "L1" and c["pe_mult"] == pe
                    and not (obs == "O1" and ss == 0.0 and ee == 0.0))   # R undefined there
                best = _best(rows, cells, keep)
                if best is None:
                    continue
                by_r = defaultdict(list)
                for key, r in rows.items():
                    name, s, e, rep, method, form = _parse(key)
                    c = cells[name]
                    if f"{method}|{form}" != best or not keep(c, s, e) or not _est(rep):
                        continue
                    er = rstats[name]["eps_rec"] if obs == "O2" else 0.0
                    eff = float(np.sqrt(s ** 2 + e ** 2 + er ** 2))
                    if eff == 0:
                        continue                                   # R undefined
                    by_r[round(rstats[name]["delta"] / eff, 12)].append(_outcome(r, np.nan, "success"))
                if by_r:
                    conds[f"{obs}|{iso}|pe={pe}|{best}"] = dict(by_r)
    out["H2a"] = r_collapse(conds, n_boot=n_boot) if conds else {"words": "no verdict: no data"}
    if failed:
        out["H2a"]["isotherms_withheld"] = sorted(failed)
        if len(failed) == len(isos):
            out["H2a"]["words"] = WITHHELD
    return out


def h2c(cells, o1_rows, m5_rows, n_boot=2000, withheld=()):
    """H2c per slice (isotherm, Pe, eps > 0) at sigma = 2 % on O1, like for like (strong
    form); the best non-EIV method chosen on the selection set, both boundaries and their
    paired-bootstrap shift on the estimation set; refined cells only at eps = 2 % (A1, A2)."""
    o1_rows = _no_oracle(o1_rows)
    slices, by_eps = {}, defaultdict(dict)
    for iso in _isotherms(cells):
        if iso in withheld:
            continue
        for pe in _pes(cells):
            for e in sorted({_parse(k)[2] for k in m5_rows if _parse(k)[2] > 0}):
                keep = lambda c, s, ee, iso=iso, pe=pe, e=e: (
                    c["iso"] == iso and c["law"] == "L1" and c["pe_mult"] == pe
                    and s == SIGMA_H2C and ee == e and (not c.get("refined") or e == EPS_REFINE))
                strong = {k: v for k, v in o1_rows.items() if _parse(k)[5] == "strong"}
                best = _best(strong, cells, keep)
                both = _best(o1_rows, cells, keep)
                sh = (paired_shift(_pairs(m5_rows, o1_rows, best, cells, keep), n_boot)
                      if best else (None, None, None))
                sh_both = (paired_shift(_pairs(m5_rows, o1_rows, both, cells, keep), n_boot=0)[0]
                           if both else None)
                k = f"{iso}|pe={pe}|eps={e}"
                slices[k] = {"best_strong_method": best, "shift": sh[0], "shift_ci": [sh[1], sh[2]],
                             "best_any_form_method": both, "shift_vs_best_any_form": sh_both,
                             "words": h2c_verdict({k: sh[0]}, MDE)["words"]}
                by_eps[e][k] = sh[0]
    per_eps = {}
    for e, d in by_eps.items():
        vals = [v for v in d.values() if v is not None]
        holds = bool(vals) and sum(v >= MDE for v in vals) >= (2.0 / 3.0) * len(vals)
        med = float(np.median(vals)) if vals else None
        per_eps[e] = {"n_slices_with_verdict": len(vals), "n_detectable": int(sum(v >= MDE for v in vals)),
                      "holds": holds, "median_shift": med,
                      "words": h2c_verdict({e: med}, MDE)["words"] if med is not None else "no verdict"}
    every = [v for d in by_eps.values() for v in d.values()]
    out = {"slices": slices, "per_eps": per_eps,
           "h2c_holds": any(p["holds"] for p in per_eps.values()),
           # falsified only if EVERY slice has a verdict and all are below the threshold
           "h2c_falsified": bool(every) and all(v is not None and v < MDE for v in every),
           "isotherms_withheld": sorted(withheld)}
    if withheld and len(withheld) == len(_isotherms(cells)):          # A2.6
        out.update({"h2c_holds": None, "h2c_falsified": None, "words": WITHHELD})
    return out


def _pairs(m5_rows, rows, method, cells, keep):
    """{Da: [(M5 outcome, method outcome)]} over the estimation replicates both were run on
    (same cell, sigma, eps, replicate: the same observation)."""
    m5 = {}
    for key, r in m5_rows.items():
        name, s, e, rep, meth, form = _parse(key)
        c = cells[name]
        if keep(c, s, e) and _est(rep):
            m5[(name, s, e, rep)] = _outcome(r, c.get("k_LDF", np.nan), "success")
    out = defaultdict(list)
    for key, r in rows.items():
        name, s, e, rep, meth, form = _parse(key)
        c = cells[name]
        if f"{meth}|{form}" == method and keep(c, s, e) and (name, s, e, rep) in m5:
            out[c["Da"]].append((m5[(name, s, e, rep)], _outcome(r, c.get("k_LDF", np.nan), "success")))
    return dict(out)


def descriptive_o23(cells, o2_rows, o2_ident, o3_ident, n_boot=2000):
    """H2b on O2 and O3, DESCRIPTIVE (PREREG_P2 s.2): on the identifiability subgrid
    (sigma in {0.5, 2 %}, eps in {0, 2 %}, Pe x1, both isotherms), the O2 discovery boundary
    (best non-oracle method, estimation set) against the O2 identifiability boundary, and the
    O3 identifiability boundary, each with its interval. Identifiability there has 3
    replicates, all used; an error counts as not identifiable."""
    def ident_by_da(rows, iso, s, e):
        out = defaultdict(list)
        for key, r in rows.items():
            name, ss, ee, rep = key.split("|")
            c = cells[name]
            if c["iso"] == iso and c["pe_mult"] == 1.0 and float(ss) == s and float(ee) == e:
                out[c["Da"]].append(0.0 if "error" in r else float(r.get("identifiable", False)))
        return dict(out)
    o2 = _no_oracle(_main_grid(o2_rows, cells))
    res = {}
    for iso in _isotherms(cells):
        for s in (0.005, 0.02):
            for e in (0.0, 0.02):
                keep = lambda c, ss, ee, iso=iso, s=s, e=e: (c["iso"] == iso and c["law"] == "L1"
                                                              and c["pe_mult"] == 1.0 and ss == s and ee == e)
                best, d, dlo, dhi = _best_and_boundary(o2, cells, keep, n_boot)
                i2 = ident_by_da(o2_ident, iso, s, e)
                i3 = ident_by_da(o3_ident, iso, s, e)
                b2 = boundary(i2, n_boot=n_boot) if i2 else (None, None, None)
                b3 = boundary(i3, n_boot=n_boot) if i3 else (None, None, None)
                gap = float(np.log10(d) - np.log10(b2[0])) if (d and b2[0]) else None
                res[f"sigma={s}|eps={e}|{iso}|pe=1.0"] = {
                    "O2_best_method": best, "O2_da_disc": d, "O2_da_disc_ci": [dlo, dhi],
                    "O2_da_ident": b2[0], "O2_da_ident_ci": [b2[1], b2[2]], "O2_gap_decades": gap,
                    "O3_da_ident": b3[0], "O3_da_ident_ci": [b3[1], b3[2]]}
    return res


def h2c_refine_levels(cells, o1_rows):
    """The H2c refinement levels (PREREG_P2 s.4.4, exact by A1, per (isotherm, Pe) by A2):
    8 levels strictly inside +-0.5 decade of the best STRONG-form non-EIV method's Da*_disc
    at O1, sigma = eps = 2 %, main grid; the method chosen on the selection set and its
    boundary estimated on the estimation set. No EIV result is read."""
    rows = _no_oracle(_main_grid(o1_rows, cells))
    strong = {k: v for k, v in rows.items() if _parse(k)[5] == "strong"}
    out = {}
    for iso in _isotherms(cells):
        for pe in _pes(cells):
            keep = lambda c, s, e, iso=iso, pe=pe: (c["iso"] == iso and c["law"] == "L1"
                                                    and c["pe_mult"] == pe
                                                    and s == SIGMA_H2C and e == EPS_REFINE)
            best, est, _, _ = _best_and_boundary(strong, cells, keep, n_boot=0)
            out[f"{iso}|pe={pe}"] = {"iso": iso, "pe": pe, "best_strong_method": best,
                                     "da_disc": est, "levels": refine_levels(est)}
    return out


def main():
    import sys
    load = lambda p: json.load(open(p))["rows"] if os.path.exists(p) else {}
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    o1 = load("results/p2_o1.json")
    o1.update(load("results/p2_extra_m7.json"))
    if "--refine-levels" in sys.argv:
        lv = h2c_refine_levels(cells, o1)
        json.dump(lv, open("results/p2_h2c_refine_levels.json", "w"), indent=1)
        print(json.dumps(lv, indent=1))
        return
    rstats = json.load(open("results/p2_rstats.json"))["cells"]
    m5 = load("results/p2_extra_m5.json")
    out = verdicts(cells, o1, load("results/p2_o2.json"), load("results/p2_extra_o1ident.json"), rstats)
    failed = [iso for iso, v in out["positive_control"].items() if v["passed"] is False]
    out["H2c"] = h2c(cells, o1, m5, withheld=failed)
    out["H2b_O2_O3_descriptive"] = descriptive_o23(cells, load("results/p2_o2.json"),
                                                   load("results/p2_o2_ident.json"),
                                                   load("results/p2_o3_ident.json"))
    l2 = load("results/p2_extra_l2.json")
    rates = defaultdict(list)
    for key, r in l2.items():
        name, s, e, rep, method, form = _parse(key)
        rates[f"{name}|{s}|{e}|{method}|{form}"].append(_outcome(r, np.nan, "success"))
    out["H2d_descriptive"] = {k: float(np.mean(v)) for k, v in rates.items()}
    json.dump(out, open("results/p2_verdicts.json", "w"), indent=2, default=str)
    print("positive control:", {k: v["passed"] for k, v in out["positive_control"].items()})
    print("H2b:", out["H2b_overall"]["words"])
    print("H2a:", out["H2a"]["words"])
    print("H2c holds:", out["H2c"]["h2c_holds"], "| falsified:", out["H2c"]["h2c_falsified"])
    print("wrote results/p2_verdicts.json")


if __name__ == "__main__":
    main()
