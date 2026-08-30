"""What nominal alpha gives 5% ACTUAL false-positive rate at our cluster counts?

The percentile cluster bootstrap over-rejects at these cluster counts (measured:
~10% at nominal 5%). Rather than assert the CIs are fine, calibrate: find the
nominal level whose empirical rejection rate is the 5% we actually want.
"""
import numpy as np
from metrics import ArmResult, compare

def fpr(n_mat, n_cond, alpha, trials=400, seed0=0):
    fp = 0
    for s in range(trials):
        rng = np.random.default_rng(seed0 + s)
        mats = np.repeat(np.arange(n_mat), n_cond)
        adv = rng.normal(0, 0.02, n_mat)[mats]
        A = 0.05 + rng.normal(0, 0.003, mats.size)
        B = 0.05 + adv + rng.normal(0, 0.003, mats.size)
        fp += compare(ArmResult("A",mats,A), ArmResult("B",mats,B),
                      n_boot=600, seed=s, alpha=alpha)["significant"]
    return 100*fp/trials

print("Empirical false-positive rate vs nominal alpha (12 materials x 17 conditions)")
print(f"  {'nominal alpha':>14} {'nominal CI':>12} {'empirical FPR':>15}")
print("  " + "-"*44)
best=None
for a in (0.05, 0.02, 0.01, 0.005, 0.002):
    f = fpr(12, 17, a)
    print(f"  {a:>14.3f} {100*(1-a):>11.1f}% {f:>14.1f} %")
    if best is None and f <= 5.0: best=(a,f)
print()
if best:
    print(f"  => use alpha = {best[0]} (a {100*(1-best[0]):.1f}% CI) for a true 5% test on this split.")
else:
    print("  => even alpha=0.002 over-rejects; report effects only when far from the boundary.")
