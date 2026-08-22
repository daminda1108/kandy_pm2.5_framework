import pandas as pd, numpy as np
from scipy.stats import spearmanr
L = pd.read_csv("data/processed/modular/ladder_all.csv")
for a,b in [("Bud0","Bud1"),("Bud1","Bud2"),("Bud2","Bud3")]:
    L[f"g_{b}"] = 100*(L[f"rmse_{a}"]-L[f"rmse_{b}"])/L[f"rmse_{a}"]
# n_held = stations withheld for scoring -> the network mean is over these
n = L.n_held
print(f"stations scored against (n_held): median {n.median():.0f}  range {n.min():.0f}-{n.max():.0f}\n")
print("If support error biased the ladder, gains should track how well the TARGET is estimated:")
for g in ["g_Bud1","g_Bud2","g_Bud3"]:
    s = L[[g,"n_held"]].dropna()
    rho,p = spearmanr(s.n_held, s[g])
    print(f"  {g:<7} vs n_held : rho={rho:+.3f}  p={p:.3f}  (n={len(s)})")
med = n.median(); hi, lo = L[n>=med], L[n<med]
print(f"\n  many stations (n>={med:.0f}, N={len(hi)})  vs  few (N={len(lo)}), median step gain:")
for g in ["g_Bud1","g_Bud2","g_Bud3"]:
    print(f"    {g:<7} many {hi[g].median():6.1f}%    few {lo[g].median():6.1f}%    diff {hi[g].median()-lo[g].median():+5.1f} pp")
# quadrature argument: a common support floor s compresses ALL fractional gains.
print("\nQuadrature check - what a common support floor does to a measured gain:")
print("  true RMSE a->b, observed sqrt(a^2+s^2)->sqrt(b^2+s^2)")
for true_gain in (0.30,0.50):
    a=10.0; b=a*(1-true_gain)
    for s in (0,2,4,6):
        obs=100*(np.hypot(a,s)-np.hypot(b,s))/np.hypot(a,s)
        print(f"    true {true_gain*100:.0f}%  s={s}: measured {obs:.1f}%")
