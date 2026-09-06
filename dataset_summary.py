"""Descriptive statistics of a generated dataset, with every denominator named.

Written because the project reports the Damkohler distribution twice, under one
name, with two different denominators:

    per SAMPLE    n = 3947   median 27.5   77.8 % in the 5-60 band   range 3.8-689
    per MATERIAL  n = 240    median 25.0   85.0 % in band            range 7.7-173

Both are correct. The first describes the dataset; the second is the axis rung L6's
primary estimand is regressed on, and it is a median of medians. But `RESULTS.md`
quoted the first in its dataset section and the second in its L6 section without
saying which was which, so the two ranges cannot be reconciled by a reader -- and a
referee reading "3.8 to 689" in one section and "7.7 to 173" in another will ask.

Nothing here is new measurement. It records what was already true, once, with the
denominator attached, so that neither number can be typed into a document again.

    python dataset_summary.py                      # writes results/dataset_summary.json
    python dataset_summary.py --root data/parametric   # the legacy design, for contrast
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

BAND = (5.0, 60.0)   # the informative Damkohler band, fixed by the design


def summarise(root):
    man = json.load(open(os.path.join(root, "manifest.json")))
    samples = man["samples"]
    ok = [s for s in samples if s.get("ok", True)]
    with_da = [s for s in ok if "Da" in s]

    # The legacy manifest records no per-sample Damkohler -- the field was added in
    # v2. It is RECONSTRUCTIBLE, because v2 defines Da = k_LDF * t_final
    # (gen_parametric_dataset.py) and the legacy manifest carries t_final per sample
    # and k_LDF per material. Reconstructing it is the point of this branch: the
    # claim that "98.9 % of the legacy dataset sat above Da 60" -- the stated
    # justification for building v2, quoted in RESULTS.md and in retraction A22 --
    # lived only in a COMMENT in the generator and had no script behind it (B63).
    da_source = "recorded per sample in the manifest"
    if not with_da:
        k_by_mat = {m["material_id"]: m.get("k_LDF") for m in man["materials"]}
        if any(v is None for v in k_by_mat.values()):
            return {"root": root, "design": man.get("design", "legacy"),
                    "n_samples": len(ok), "n_materials": len(man["materials"]),
                    "damkohler": "UNAVAILABLE and not reconstructible: no per-sample Da "
                                 "and no per-material k_LDF."}
        with_da = [dict(s, Da=k_by_mat[s["mat"]] * s["t_final"]) for s in ok
                   if "t_final" in s and s["mat"] in k_by_mat]
        da_source = ("RECONSTRUCTED as k_LDF * t_final, the definition v2 uses "
                     "(gen_parametric_dataset.py). Not recorded in this manifest.")

    da_sample = np.array([s["Da"] for s in with_da], float)
    by = {}
    for s in with_da:
        by.setdefault(s["mat"], []).append(s["Da"])
    da_material = np.array([np.median(v) for v in by.values()], float)

    def dist(x, what):
        return {
            "denominator": what, "n": int(x.size),
            "min": float(x.min()), "median": float(np.median(x)), "max": float(x.max()),
            "decades": float(np.log10(x.max() / x.min())),
            "frac_in_band": float(((x >= BAND[0]) & (x <= BAND[1])).mean()),
        }

    counts = man.get("counts", {})
    out = {
        "root": root, "design": man.get("design", "legacy"),
        "n_samples": len(ok), "n_materials": len(man["materials"]),
        "n_conditions": len(man["conditions"]),
        "n_rejected": man.get("n_rejected"),
        "n_held_out_materials": len(man.get("novel_materials", [])),
        "split_counts": counts,
        "band": list(BAND), "damkohler_source": da_source,
        "frac_above_band_per_sample": float((da_sample > BAND[1]).mean()),
        "damkohler_per_sample": dist(da_sample, "one value per SAMPLE"),
        "damkohler_per_material": dist(da_material, "the MEDIAN over each material's own "
                                                    "samples, one value per MATERIAL -- this is "
                                                    "the axis L6's slope test regresses on"),
        "note": "The two Damkohler summaries are different quantities, not a discrepancy. "
                "Any document quoting either must name its denominator.",
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/parametric_v2")
    ap.add_argument("--out", default="results/dataset_summary.json")
    args = ap.parse_args()

    out = summarise(args.root)
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(args.out, "w"), indent=2)

    print(f"{out['design']}: {out['n_samples']} accepted samples, {out['n_materials']} materials "
          f"x {out['n_conditions']} conditions, {out['n_rejected']} rejected, "
          f"{out['n_held_out_materials']} materials held out")
    for key in [k for k in ("damkohler_per_sample", "damkohler_per_material") if k in out]:
        d = out[key]
        print(f"  Da {key.split('_', 1)[1]:<22} n={d['n']:>5}  median {d['median']:6.2f}  "
              f"{100 * d['frac_in_band']:5.1f} % in [{BAND[0]:.0f}, {BAND[1]:.0f}]  "
              f"range {d['min']:.2f}-{d['max']:.0f}  ({d['decades']:.2f} decades)")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
