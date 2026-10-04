"""Owner of results/water_mofs.json: real water-harvesting MOFs placed in the design space.

Referee M10 asked where real water MOFs sit relative to the sampled parameter space.
The literature values live in research/water_mof_parameters.json (compiled
2026-10-04; every value with its DOI, location in the paper, a quote or a note on how
it was read, and a confidence; every DOI checked against Crossref; two spot-checked
against the full text). This script turns them into what the figure draws:

  per MOF and quantity, the [min, max] over the sources that report it -- the spread
  between sources is the uncertainty shown, never averaged away -- in the design's
  units (heat negative, capacity in mol/kg), plus the cited DOIs, and the Henry-site
  fraction estimated as uptake just below the step over uptake near saturation
  (a low-confidence figure reading for most MOFs, marked so).

Only the four intrinsic quantities are placed: the bed and pellet parameters belong
to the shaped body and the packing, not to the MOF.

    python water_mofs.py
"""
import json

SRC = "research/water_mof_parameters.json"
OUT = "results/water_mofs.json"
QTY = {"RH_step": "RH_step", "q_sat": "q_max", "heat_of_adsorption": "dH"}


def values(x):
    """A converted value, or a stated range 'a to b' (kept as both ends)."""
    if x is None:
        return []
    if isinstance(x, (int, float)):
        return [float(x)]
    a, b = str(x).split(" to ")
    return [float(a), float(b)]


def span(records):
    vals = [v for r in records for v in values(r.get("converted"))]
    dois = sorted({r["source_doi"] for r in records if r.get("converted") is not None})
    conf = sorted({r.get("confidence", "") for r in records if r.get("converted") is not None})
    return ({"lo": min(vals), "hi": max(vals), "n": len(vals), "dois": dois, "confidence": conf}
            if vals else None)


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    ranges = d["_meta"]["design_v2_ranges"]
    out = {"_what": __doc__.splitlines()[0], "source": SRC,
           "design": {"RH_step": ranges["RH_step"], "q_max": ranges["q_max_mol_per_kg"],
                      "dH": ranges["dH_ads_kJ_per_mol"], "henry_fraction": ranges["henry_fraction"]},
           "materials": {}}
    for name, m in d["materials"].items():
        row = {}
        for key, tag in QTY.items():
            row[tag] = span(m.get(key) or [])
        hb = m.get("uptake_below_step")
        hb = hb if isinstance(hb, list) else ([hb] if hb else [])
        hf = [r["henry_fraction_estimate"] for r in hb if r.get("henry_fraction_estimate") is not None]
        row["henry_fraction"] = ({"lo": min(hf), "hi": max(hf), "n": len(hf),
                                  "dois": sorted({r["source_doi"] for r in hb}),
                                  "confidence": sorted({r.get("confidence", "") for r in hb})} if hf else None)
        inside = {}
        for tag, v in row.items():
            if v is None:
                inside[tag] = None
                continue
            lo, hi = sorted(out["design"][tag])
            inside[tag] = ("inside" if lo <= v["lo"] and v["hi"] <= hi else
                           "outside" if v["hi"] < lo or v["lo"] > hi else "straddles the edge")
        row["placement"] = inside
        out["materials"][name] = row
        print(f"  {name:28s} " + "  ".join(f"{t}: {inside[t]}" for t in inside))
    out["n_inside_all"] = sum(all(p in ("inside", None) for p in r["placement"].values())
                              for r in out["materials"].values())
    out["n_materials"] = len(out["materials"])
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=2)
    print(f"{out['n_inside_all']} of {out['n_materials']} inside on every placed axis; wrote {OUT}")


if __name__ == "__main__":
    main()
