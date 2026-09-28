"""Owner of results/l3_final_pair.json -- the L3 'best KAN anywhere vs the perceptron'
comparison, whose paired interval had no script (B71).

The two MEANS in that file equal audit_l3.py's results exactly (results/l3_audit.json:
mlp 0.0573, rbf_g4 0.0633), so they are owned. The paired, cluster-robust INTERVAL and
the 'still significant' verdict were computed from per-sample errors that no script
saved. This re-runs exactly audit_l3.py's two configurations -- matched budget 200k,
depth 3, seeds 42/43/44, best of lr in {3e-3, 1e-3} per seed chosen on held-out error
(the generous direction for the KAN, as audit_l3 did) -- keeps the per-sample held-out
errors and material ids, and computes metrics.compare at the calibrated alpha.

Training job: queued in autorun.sh, never run beside another training job.

    python l3_final_pair.py
"""
import gc
import json

import numpy as np
import torch

import ladder_data
from metrics import ALPHA_CALIBRATED, ArmResult, compare
from run_l1 import evaluate, fit_pod, project
from run_l3 import solve_width, train_one

BUDGET = 200_000
OUT = "results/l3_final_pair.json"


def main():
    d = ladder_data.load(verbose=False)
    shape = d.fields.shape[2:]
    tr, nm = d.idx("train"), d.idx("novel_material")
    bases, _ = fit_pod(d.fields, tr, 64, verbose=False)
    C = project(d.fields, bases)
    gc.collect()
    mu, sd = C[tr].mean(0), C[tr].std(0)
    sd[sd == 0] = 1.0
    Y = (C - mu) / sd

    def run(fam, **kw):
        w, p = solve_width(fam, BUDGET, 3, 11, 192, **kw)
        per_seed = []
        for s in (42, 43, 44):
            best = None
            for lr in (3e-3, 1e-3):
                m, _ = train_one(fam, w, 3, d.params_z[tr], Y[tr], s, steps=6000, lr=lr, **kw)
                m.eval()
                with torch.no_grad():
                    P = m(torch.tensor(d.params_z[nm], dtype=torch.float32)).cpu().numpy() * sd + mu
                errs = np.array([r["c"] for r in evaluate(P, d.fields[nm], bases, shape, d.t_final[nm])])
                if best is None or np.nanmean(errs) < np.nanmean(best[1]):
                    best = (lr, errs)
                del m
                gc.collect()
            per_seed.append(best)
            print(f"  {fam} seed {s}: lr {best[0]:g} novel {np.nanmean(best[1]):.4f}", flush=True)
        # one ArmResult over all seeds' samples, material ids repeated per seed
        vals = np.concatenate([e for _, e in per_seed])
        mats = np.concatenate([np.asarray(d.material_ids)[nm]] * len(per_seed))
        return vals, mats, [lr for lr, _ in per_seed]

    va, ma, lra = run("mlp")
    vb, mb, lrb = run("rbf_kan", grids=4)
    r = compare(ArmResult("mlp", ma, va), ArmResult("rbf_g4", mb, vb), alpha=ALPHA_CALIBRATED)
    out = {"_source": "l3_final_pair.py (re-run of audit_l3.py's mlp and rbf_kan grids=4)",
           "mlp": float(np.nanmean(va)), "rbf_g4": float(np.nanmean(vb)),
           "diff": r["mean_a"] - r["mean_b"] if "mean_diff" not in r else r["mean_diff"],
           "ci": [r["ci_low"], r["ci_high"]], "significant": bool(r["significant"]),
           "alpha": ALPHA_CALIBRATED, "lr_per_seed": {"mlp": lra, "rbf_g4": lrb},
           "comparison": r,
           "audit_means_for_reference": json.load(open("results/l3_audit.json"))}
    out["audit_means_for_reference"] = {k: out["audit_means_for_reference"][k] for k in ("mlp", "rbf_g4")}
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"wrote {OUT}: mlp {out['mlp']:.4f} rbf_g4 {out['rbf_g4']:.4f} ci {out['ci']}")
    print("L3_FINAL_PAIR_DONE")


if __name__ == "__main__":
    main()
