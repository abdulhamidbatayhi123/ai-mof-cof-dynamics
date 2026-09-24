"""Which L3 optima are interior, which sit on the grid edge, and whether the edge ones
have saturated there -- the evidence rule 4 asks for, owned by a script.

RESULTS.md carried "MLP at 3e-5, edge but saturated to 0.1-0.6 %" as typed text, and
the manuscript went further and said "every selected optimum was bracketed", which is
false for the perceptron: it selects the bottom edge at every budget. Rule 4 accepts
an edge only when the metric has saturated there, so the saturation must be measured,
not asserted. Reads the three L3 results files the grid is spread across.

    python l3_edges.py      # writes results/l3_edges.json
"""
import json
import math
from collections import defaultdict

FILES = ["results/l3_results.json", "results/l3_bracket.json", "results/l3_cheby_1e-1.json"]
cells = defaultdict(list)     # trained seeds' held-out error
tried = defaultdict(int)      # every seed attempted, trained or not
for f in FILES:
    for a in json.load(open(f))["arms"]:
        for s in a["seeds"].values():
            tried[(a["budget"], a["family"], a["lr"])] += 1
            if "novel_material" in s and math.isfinite(s["novel_material"]["c"]):
                cells[(a["budget"], a["family"], a["lr"])].append(s["novel_material"]["c"])

grid = sorted({k[2] for k in tried})
out = {"grid": grid, "n_rates": len(grid),
       "decades": math.log10(grid[-1] / grid[0]), "selections": {}}
for b, fam in sorted({(k[0], k[1]) for k in cells}):
    # a cell counts only if all three seeds trained (failed-to-train cells are excluded)
    means = {lr: sum(v) / len(v) for (bb, ff, lr), v in cells.items()
             if bb == b and ff == fam and len(v) >= 3}
    lrs = sorted(means)
    best = min(means, key=means.get)
    i = lrs.index(best)
    edge = "bottom" if i == 0 else "top" if i == len(lrs) - 1 else None
    # An edge among FULLY-trained cells is still bracketed if the next rate out was
    # attempted and is worse on the seeds that trained, or failed to train at all:
    # both say the optimum has been passed. Recorded, not silently assumed.
    beyond = [lr for lr in sorted({k[2] for k in tried if k[:2] == (b, fam)})
              if (edge == "top" and lr > best) or (edge == "bottom" and lr < best)]
    if edge and beyond:
        nxt = beyond[0] if edge == "top" else beyond[-1]
        v = cells.get((b, fam, nxt), [])
        worse = (not v) or (sum(v) / len(v) > means[best])
        rec_beyond = {"lr": nxt, "trained": len(v), "tried": tried[(b, fam, nxt)],
                      "mean_trained": (sum(v) / len(v)) if v else None, "turns_over": worse}
        if worse:
            edge = None
    else:
        rec_beyond = None
    rec = {"lr": best, "mean": means[best], "tried": lrs, "edge": edge, "beyond": rec_beyond}
    if edge:
        nb = lrs[1] if edge == "bottom" else lrs[-2]
        rec["neighbour_lr"] = nb
        rec["rel_change_to_neighbour"] = means[nb] / means[best] - 1.0
    out["selections"][f"{b}_{fam}"] = rec
edges = {k: v for k, v in out["selections"].items() if v["edge"]}
out["edge_selections"] = sorted(edges)
out["edge_saturation_max"] = max((v["rel_change_to_neighbour"] for v in edges.values()), default=0.0)
out["edge_saturation_min"] = min((v["rel_change_to_neighbour"] for v in edges.values()), default=0.0)
json.dump(out, open("results/l3_edges.json", "w"), indent=2)
for k, v in out["selections"].items():
    print(f"{k:<22} lr={v['lr']:<8g} edge={v['edge']} "
          + (f"neighbour +{100 * v['rel_change_to_neighbour']:.2f}%" if v["edge"] else ""))
print(f"grid: {len(grid)} rates, {out['decades']:.2f} decades")
