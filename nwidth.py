"""Empirical Kolmogorov n-width: does the POD spectrum decay exponentially or algebraically?

This decides whether a linear-reconstruction operator (POD+regressor, DeepONet)
is fundamentally limited on this problem, or merely under-trained.
"""
import json, numpy as np
from sklearn.decomposition import PCA
import ladder_data

d = ladder_data.load(verbose=False)
tr = d.idx("train")
R = 128
out = {}
print(f"{'ch':>3} {'n@90%':>6} {'n@99%':>6} {'n@99.9%':>8} {'n@99.99%':>9}   decay fit (n=8..64)")
print("-"*78)
for i, ch in enumerate(("c","q","T")):
    X = d.fields[tr, i].reshape(len(tr), -1).astype(np.float32)
    p = PCA(n_components=R, svd_solver="randomized", random_state=0).fit(X)
    sv = p.singular_values_
    ev = p.explained_variance_ratio_; cum = np.cumsum(ev)
    ns = [int(np.searchsorted(cum, t))+1 for t in (0.90,0.99,0.999,0.9999)]
    # residual energy after n modes = the n-width proxy
    tail = 1.0 - cum
    n = np.arange(1, R+1)
    m = (n>=8)&(n<=64)&(tail>1e-12)
    # algebraic: log(tail) ~ a*log(n)+b   |   exponential: log(tail) ~ -k*n+b
    alg = np.polyfit(np.log(n[m]), np.log(tail[m]), 1)
    exp = np.polyfit(n[m], np.log(tail[m]), 1)
    r2 = lambda x,y,f: 1-np.sum((y-np.polyval(f,x))**2)/np.sum((y-y.mean())**2)
    r2a = r2(np.log(n[m]), np.log(tail[m]), alg)
    r2e = r2(n[m], np.log(tail[m]), exp)
    print(f"{ch:>3} {ns[0]:>6} {ns[1]:>6} {ns[2]:>8} {ns[3]:>9}   "
          f"algebraic n^{alg[0]:+.2f} R2={r2a:.4f} | exponential e^({exp[0]:+.4f}n) R2={r2e:.4f}"
          f"  -> {'EXPONENTIAL' if r2e>r2a else 'ALGEBRAIC'}")
    out[ch] = {"singular_values": sv.tolist(), "explained_variance_ratio": ev.tolist(),
               "n_for": dict(zip(("90","99","999","9999"), ns)),
               "algebraic_exponent": float(alg[0]), "algebraic_r2": float(r2a),
               "exponential_rate": float(exp[0]), "exponential_r2": float(r2e)}
    del X
json.dump(out, open("results/nwidth.json","w"), indent=2)
print("\nwrote results/nwidth.json")
