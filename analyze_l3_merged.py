"""Owner of results/l3_merged.json -- which had none.

The file was written on 2026-08-31 (commit 4d9e6e3) by no script; seven manuscript
macros read it (the L3 winner table, both optimal learning rates, the arm count).
This script reconstructs it from the three raw L3 files and, per rule 10, makes it
reproducible. Selection rule (recovered by reproducing the old table EXACTLY): for each
(budget, family) the learning rate with the lowest mean held-out error among
configurations where EVERY seed trained. A configuration with any failed seed is
excluded, never averaged in.

Two counts in the old file / manuscript were wrong and are corrected here (B70):
  * n_arms was 63 -- the six configurations of l3_cheby_1e-1.json were left out, while
    the manuscript says the arms were trained "across eight learning rates", the
    eighth being exactly that file. The count over all three files is 69.
  * the manuscript's "Six configurations failed to train entirely" matches nothing:
    3 configurations failed on every seed, 4 more on some. Both are recorded.

    python analyze_l3_merged.py           # write results/l3_merged.json
    python analyze_l3_merged.py --check   # diff against the file on disk, write nothing
"""
import json
import sys

FILES = ("results/l3_results.json", "results/l3_bracket.json", "results/l3_cheby_1e-1.json")
OUT = "results/l3_merged.json"


def build():
    arms = [a for f in FILES for a in json.load(open(f))["arms"]]

    def trained(a):
        return [s["novel_material"]["c"] for s in a["seeds"].values() if "novel_material" in s]
    full = [a for a in arms if len(trained(a)) == len(a["seeds"]) >= 3]
    table = {}
    for a in full:
        key = f"{a['budget']}_{a['family']}"
        mu = sum(trained(a)) / len(trained(a))
        if key not in table or mu < table[key]["novel"]:
            table[key] = {"lr": a["lr"], "novel": mu}
    all_failed = [f"{a['budget']}_{a['family']}@{a['lr']:g}" for a in arms if not trained(a)]
    some_failed = [f"{a['budget']}_{a['family']}@{a['lr']:g}" for a in arms
                   if trained(a) and len(trained(a)) < len(a["seeds"])]
    grid = sorted({a["lr"] for a in full})
    return {
        "_source": "analyze_l3_merged.py from " + ", ".join(FILES),
        "grid": grid,
        "grid_all_tried": sorted({a["lr"] for a in arms}),
        "n_arms": len(arms),
        "n_arms_fully_trained": len(full),
        "failed_all_seeds": all_failed,
        "failed_some_seeds": some_failed,
        "table": dict(sorted(table.items(), key=lambda kv: (int(kv[0].split("_")[0]), kv[0]))),
    }


def main():
    new = build()
    if "--check" in sys.argv:
        old = json.load(open(OUT))
        same = all(abs(new["table"][k]["novel"] - v["novel"]) < 1e-15 and new["table"][k]["lr"] == v["lr"]
                   for k, v in old["table"].items()) and set(old["table"]) == set(new["table"])
        print("winner table reproduced exactly:", same)
        print(f"n_arms: file {old.get('n_arms')} -> recomputed {new['n_arms']} "
              f"({new['n_arms_fully_trained']} fully trained)")
        print("failed on every seed:", new["failed_all_seeds"])
        print("failed on some seeds:", new["failed_some_seeds"])
        sys.exit(0 if same else 1)
    json.dump(new, open(OUT, "w"), indent=2)
    print(f"wrote {OUT}: {new['n_arms']} arms, {len(new['failed_all_seeds'])} failed on every "
          f"seed, {len(new['failed_some_seeds'])} on some")


if __name__ == "__main__":
    main()
