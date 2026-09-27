"""Paper 2 PILOT for M1 (declared in PREREG_P2 §3): is training a rate network THROUGH
the column feasible on this CPU? Generator facts only -- no discovery is run.

Measures, on the default physics at k = 0.002 s^-1 (Da ~ 14, a fresh run, not a grid
cell): wall time of one forward solve, one reverse-mode gradient w.r.t. k, and one
gradient w.r.t. a 2x32 tanh MLP rate; and the exit-curve change N_z 50 -> 400 (the
grid the UDE would train on, against the grid the ground truth uses).
Output: results/p2_pilot_m1.json
"""
import json
import time

import jax
import jax.numpy as jnp
import numpy as np

from p2.jaxcol import solve
from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data


def mlp_rate(c, q, T, qs, args):
    x = jnp.stack([c, q / 20.0, (T - 298.0) / 10.0, qs / 20.0], -1)
    h = jnp.tanh(x @ args["W1"] + args["b1"])
    h = jnp.tanh(h @ args["W2"] + args["b2"])
    return (h @ args["W3"])[..., 0] * args["scale"]


def main():
    p = AdsorptionPhysicsConfig()
    p.k_LDF = 0.002
    t_st = p.stoichiometric_time(1.0, p.T_in)
    tf = 4 * t_st
    ts = np.linspace(0, tf, 100)
    out = {"_pilot": True, "k": p.k_LDF, "Da": p.k_LDF * t_st}

    t0 = time.time(); y = solve(p, 50, 1.0, tf, ts); y.block_until_ready()
    out["forward_s_first_incl_compile"] = time.time() - t0
    t0 = time.time(); y = solve(p, 50, 1.0, tf, ts); y.block_until_ready()
    out["forward_s"] = time.time() - t0
    target = y[:, 49]

    def loss_k(k):
        return jnp.mean((solve(p, 50, 1.0, tf, ts, args={"k": k})[:, 49] - target) ** 2)
    g = jax.grad(loss_k)
    t0 = time.time(); g(0.003).block_until_ready(); out["grad_k_s_first"] = time.time() - t0
    t0 = time.time(); g(0.003).block_until_ready(); out["grad_k_s"] = time.time() - t0

    key = jax.random.PRNGKey(0)
    k1, k2, k3 = jax.random.split(key, 3)
    params = {"W1": 0.3 * jax.random.normal(k1, (4, 32)), "b1": jnp.zeros(32),
              "W2": 0.3 * jax.random.normal(k2, (32, 32)), "b2": jnp.zeros(32),
              "W3": 0.3 * jax.random.normal(k3, (32, 1)), "scale": 0.01}

    def loss_nn(prm):
        return jnp.mean((solve(p, 50, 1.0, tf, ts, rate=mlp_rate, args=prm)[:, 49] - target) ** 2)
    gn = jax.grad(loss_nn)
    t0 = time.time(); jax.block_until_ready(gn(params)); out["grad_nn_s_first"] = time.time() - t0
    t0 = time.time(); jax.block_until_ready(gn(params)); out["grad_nn_s"] = time.time() - t0

    curves = {}
    for n in (50, 400):
        z, t, yy = generate_breakthrough_data(p, N_z=n, t_final=tf, n_snapshots=100, verbose=False)
        curves[n] = yy[n - 1]
    out["exit_change_50_vs_400"] = float(np.max(np.abs(curves[50] - curves[400])))
    out["epochs_in_2h_at_grad_nn"] = 7200.0 / out["grad_nn_s"]
    json.dump(out, open("results/p2_pilot_m1.json", "w"), indent=2)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
