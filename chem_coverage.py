"""Two questions a materials chemist asks of the sampled space (round-3 referee, §4.1-4.2).

Owner of results/chem_coverage.json.

1. How many accepted samples are fed BELOW their material's step humidity? Such a
   sample never reaches pore filling in the feed, so its breakthrough is the
   primary-site front alone, not the two-wave structure. A harvester is run above its
   step by design, so a chemist wants this fraction stated.
2. How many materials are only weakly cooperative (isotherm exponent n < 1.5)? Near
   n = 1 the cooperative term is nearly Langmuir and the isotherm is not visibly
   S-shaped.

Read from the dataset manifests (accepted samples only, `ok` true), for both designs.

    python chem_coverage.py
"""
import json

OUT = "results/chem_coverage.json"
DESIGNS = {"v2": "data/parametric_v2/manifest.json", "legacy": "data/parametric/manifest.json"}
WEAK_N = 1.5


def coverage(path):
    m = json.load(open(path))
    mats = {x["material_id"]: x for x in m["materials"]}
    conds = {x["condition_id"]: x for x in m["conditions"]}
    ok = [s for s in m["samples"] if s.get("ok")]
    below = [s for s in ok if conds[s["cond"]]["rh_feed"] < mats[s["mat"]]["step_rh"]]
    used = {s["mat"] for s in ok}
    weak = [k for k in used if mats[k]["isotherm_n"] < WEAK_N]
    return {"n_accepted": len(ok), "n_fed_below_step": len(below),
            "pct_fed_below_step": 100.0 * len(below) / len(ok),
            "n_materials": len(used), "n_weakly_cooperative": len(weak),
            "pct_weakly_cooperative": 100.0 * len(weak) / len(used), "weak_n_threshold": WEAK_N}


def main():
    out = {"_what": __doc__.splitlines()[0], **{d: coverage(p) for d, p in DESIGNS.items()}}
    json.dump(out, open(OUT, "w"), indent=1)
    for d in DESIGNS:
        c = out[d]
        print(f"{d}: {c['n_fed_below_step']}/{c['n_accepted']} accepted samples fed below the step "
              f"({c['pct_fed_below_step']:.1f} %); {c['n_weakly_cooperative']}/{c['n_materials']} "
              f"materials with n < {WEAK_N} ({c['pct_weakly_cooperative']:.1f} %)")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
