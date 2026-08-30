import json, numpy as np, sys
sys.path.insert(0, r"C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics")
from metrics import ArmResult, compare

d=json.load(open(r"C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics/results/l6_results.json"))
def AR(name):
    v=[];m=[]
    for s in sorted(d["arms"][name]):
        nm=d["arms"][name][s]["novel_material"]
        v.append(np.asarray(nm["per_sample_nrmse_c"])); m.append(np.asarray(nm["material_ids"]))
    return ArmResult(name=name, values=np.concatenate(v), material_ids=np.concatenate(m))

J,S_=AR("joint"),AR("separate")
r=compare(J,S_)
print(f"L6 reproduced: joint {r['mean_a']:.4f} vs separate {r['mean_b']:.4f} "
      f"diff {r['mean_diff']:+.4f} CI [{r['ci_low']:+.4f},{r['ci_high']:+.4f}] "
      f"sig={r['significant']} n_mat={r['n_materials']}\n")

rng=np.random.default_rng(0)
mats=np.unique(J.material_ids)
idx_by={m:np.where(J.material_ids==m)[0] for m in mats}
resid=S_.values-J.values
resid=resid-resid.mean()

# vectorised cluster bootstrap
def sig(base, alt, mids, nboot=300, alpha=0.005, seed=0):
    rr=np.random.default_rng(seed)
    um=np.unique(mids); ib={m:np.where(mids==m)[0] for m in um}
    diff=base-alt
    b=np.empty(nboot)
    for k in range(nboot):
        dr=rr.choice(um,size=len(um),replace=True)
        b[k]=diff[np.concatenate([ib[m] for m in dr])].mean()
    lo,hi=np.percentile(b,[100*alpha/2,100*(1-alpha/2)])
    return lo>0 or hi<0

def power(effect, n_trials=200):
    hits=0
    for t in range(n_trials):
        dr=rng.choice(mats,size=len(mats),replace=True)
        take=np.concatenate([idx_by[m] for m in dr])
        base=J.values[take]
        noise=resid[rng.choice(len(resid),size=len(take))]
        alt=base*(1-effect)+noise
        if sig(base,alt,J.material_ids[take],seed=t): hits+=1
    return hits/n_trials

print("POWER of the L6 design (12 held-out materials, 3 seeds, cluster bootstrap, alpha=0.005)")
print(f"{'true improvement of separate over joint':>42s}   {'power':>7s}")
for eff in (0.0,0.05,0.10,0.20,0.30,0.40,0.50,0.60,0.70):
    print(f"{eff*100:39.0f} %   {power(eff)*100:5.0f} %")
print("\nContext: prior conduction project's H1 effect was 16x (=94% improvement).")
print("L6 observed point estimate: separate is 26% WORSE.")
