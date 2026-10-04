"""Owner of results/design_constants.json: the design constants the Methods section quotes.

Referee item M7 asked for a Methods section: governing equations, parameter ranges,
numerics. Those are design constants, not results -- but a constant typed into a
manuscript drifts from the code exactly as a result does (the solver docstring's
mass balance had drifted from rhs(), B72). So every constant the Methods quote is read
here from the place the computation actually takes it:

  * the dataset MANIFESTS (what the generator recorded it used -- e.g. v2 is stored at
    256 x 256 although the module default is 512: the default is not the design);
  * the physics object `gen_parametric_dataset.build_physics` constructs for a real
    v2 sample (bed and transport properties, the dispersion correlation's D_m);
  * the solver's own signature (integrator tolerances) and the generator's call
    (number of output snapshots).

    python design_constants.py
"""
import inspect
import json
import re

import gen_parametric_dataset as gen
import solver_fd

OUT = "results/design_constants.json"


def main():
    v2 = json.load(open("data/parametric_v2/manifest.json"))
    leg = json.load(open("data/parametric/manifest.json"))
    mats = {m["material_id"]: m for m in v2["materials"]}
    conds = {c["condition_id"]: c for c in v2["conditions"]}
    s0 = v2["samples"][0]
    p = gen.build_physics(mats[s0["mat"]], conds[s0["cond"]])

    # the dispersion correlation D_L = 0.7 D_m + 0.5 d_p v/eps_t, inverted for D_m
    d_m_disp = (p.D_L - 0.5 * p.d_p * p.v / p.eps_t) / 0.7
    sig = inspect.signature(solver_fd.generate_breakthrough_data).parameters
    m = re.search(r"n_snapshots=(\d+)", inspect.getsource(gen.run_one))
    mult = re.search(r"for attempt, mult in enumerate\(\(([^)]*)\)\)", inspect.getsource(gen.run_one))
    mults = [eval(x.strip(), {"HORIZON": v2["horizon"]}) for x in mult.group(1).split(",")]

    ok = [s for s in v2["samples"] if s.get("ok", True)]
    out = {
        "_what": __doc__.splitlines()[0],
        "v2": {
            "n_materials": len(v2["materials"]), "n_conditions": len(v2["conditions"]),
            "n_accepted": sum(v2["counts"].values()), "n_rejected": v2["n_rejected"],
            "seed_materials": v2["seed"], "seed_conditions": v2["seed"] + 7,
            "solve_nz": v2["solve_nz"], "store_nz": v2["store_nz"], "store_nt": v2["store_nt"],
            "horizon": v2["horizon"], "horizon_multipliers": mults,
            "frac_horizon_extended_pct": 100.0 * sum(s["horizon_extensions"] > 0 for s in ok) / len(ok),
            "material_space": v2["material_space"], "condition_space": v2["condition_space"],
            "b_H_ratio": v2["b_H_ratio"], "glueckauf": v2["glueckauf"],
        },
        "legacy": {"n_materials": len(leg["materials"]), "n_conditions": len(leg["conditions"]),
                   "n_accepted": sum(leg["counts"].values()), "store_nz": leg["store_nz"],
                   "store_nt": leg["store_nt"], "k_LDF_range": leg["material_space"]["k_LDF"]},
        "physics": {"L": p.L, "D_in": p.D_in, "rho_g": p.rho_g, "C_pg": p.C_pg, "C_ps": p.C_ps,
                    "k_z": p.k_z, "h_w": p.h_w, "D_m_dispersion": d_m_disp},
        "numerics": {"rtol": sig["rtol"].default, "atol": sig["atol"].default,
                     "n_snapshots": int(m.group(1))},
    }
    json.dump(out, open(OUT, "w"), indent=2)
    print(json.dumps({k: (v if k != "v2" else {a: b for a, b in v.items() if "space" not in a}) for k, v in out.items() if k != "_what"}, indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
