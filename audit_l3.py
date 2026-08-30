"""Did the KANs get their best shot? Protocol s3 before reporting a negative result.

L3 finds MLP significantly better than both KAN families at matched parameters,
consistently across three budgets. That contradicts the premise behind
PIKAN/DeepOKAN, so before reporting it the KAN hyperparameters must be shown to
have been chosen fairly -- otherwise the result is a strawman (cf. B14).

Swept, at matched parameter count throughout:
  rbf_kan   : num_grids 4..24, and learnable vs fixed centres/widths
  cheby_kan : degree 3..11
If ANY setting beats the MLP, the L3 conclusion is wrong.
"""
import numpy as np, torch, torch.nn as nn, gc, time, json
import ladder_data
from run_l1 import evaluate, fit_pod, project
from run_l3 import build, n_params, solve_width, train_one, RBFKANBlock

d = ladder_data.load(verbose=False)
shape = d.fields.shape[2:]; tr = d.idx("train"); nm = d.idx("novel_material")
bases, _ = fit_pod(d.fields, tr, 64, verbose=False)
C = project(d.fields, bases); gc.collect()
mu, sd = C[tr].mean(0), C[tr].std(0); sd[sd==0]=1.0
Y=(C-mu)/sd
BUDGET=200_000

def run(fam, seeds=(42,43,44), **kw):
    w,p = solve_width(fam, BUDGET, 3, 11, 192, **kw)
    nvs, trs = [], []
    for s in seeds:
        best=None
        for lr in (3e-3,1e-3):
            m,_ = train_one(fam, w, 3, d.params_z[tr], Y[tr], s, steps=6000, lr=lr, **kw)
            m.eval(); o={}
            with torch.no_grad():
                for tag,idx in (("train",tr),("novel",nm)):
                    P=m(torch.tensor(d.params_z[idx],dtype=torch.float32)).cpu().numpy()*sd+mu
                    o[tag]=float(np.nanmean([r["c"] for r in evaluate(P,d.fields[idx],bases,shape,d.t_final[idx])]))
            if best is None or o["novel"]<best["novel"]: best=o
            del m; gc.collect()
        nvs.append(best["novel"]); trs.append(best["train"])
    return w,p,np.mean(trs),np.mean(nvs),np.std(nvs)

print(f"budget ~{BUDGET:,}, depth 3, 3 seeds, best of lr in (3e-3, 1e-3)")
print(f"{'config':<26} {'width':>6} {'params':>9} {'train':>8} {'novel':>8} {'sd':>7}")
print("-"*70)
res={}
w,p,t,n,s = run("mlp"); res["mlp"]=n
print(f"{'mlp (reference)':<26} {w:>6} {p:>9,} {t:>8.4f} {n:>8.4f} {s:>7.4f}", flush=True)
for g in (4,8,12,16,24):
    w,p,t,n,s = run("rbf_kan", grids=g); res[f"rbf_g{g}"]=n
    print(f"{'rbf_kan grids=%d'%g:<26} {w:>6} {p:>9,} {t:>8.4f} {n:>8.4f} {s:>7.4f}", flush=True)
for dg in (3,5,7,9,11):
    w,p,t,n,s = run("cheby_kan", degree=dg); res[f"cheby_d{dg}"]=n
    print(f"{'cheby_kan degree=%d'%dg:<26} {w:>6} {p:>9,} {t:>8.4f} {n:>8.4f} {s:>7.4f}", flush=True)
best_kan=min((v,k) for k,v in res.items() if k!="mlp")
print()
print(f"best KAN anywhere : {best_kan[1]} = {best_kan[0]:.4f}")
print(f"mlp reference     : {res['mlp']:.4f}")
print(f"=> {'KAN WINS - L3 conclusion is WRONG' if best_kan[0]<res['mlp'] else 'MLP still ahead; L3 conclusion stands'}")
json.dump(res, open("results/l3_audit.json","w"), indent=2)
