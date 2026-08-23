"""Bootstrap CI on the v3 pooled LOMO R2, which has only ever been a single-run point estimate."""
import pandas as pd, numpy as np
d=pd.read_parquet('data/processed/stage1_v3/training/predictions_blend_v3.parquet')
# target is the RESIDUAL model reconstructed to absolute PM
y=d.pm25_observed.to_numpy(); yh=d.q50_blend.to_numpy()
m=np.isfinite(y)&np.isfinite(yh); y,yh=y[m],yh[m]
folds=d.fold.to_numpy()[m]
r2=lambda a,b: 1-((a-b)**2).sum()/((a-a.mean())**2).sum()
rmse=lambda a,b: float(np.sqrt(np.mean((a-b)**2)))
print(f'n={len(y)}  point R2={r2(y,yh):.4f}  RMSE={rmse(y,yh):.3f}')

rng=np.random.default_rng(20260823)
# CLUSTER bootstrap by fold: rows within a station-month fold are not independent
uf=np.unique(folds); B=2000
r2s=np.empty(B); rm=np.empty(B)
idx_by_fold={f:np.where(folds==f)[0] for f in uf}
for b in range(B):
    pick=rng.choice(uf,size=len(uf),replace=True)
    ii=np.concatenate([idx_by_fold[f] for f in pick])
    r2s[b]=r2(y[ii],yh[ii]); rm[b]=rmse(y[ii],yh[ii])
lo,hi=np.percentile(r2s,[2.5,97.5]); rlo,rhi=np.percentile(rm,[2.5,97.5])
print(f'cluster bootstrap over {len(uf)} folds, B={B}:')
print(f'  R2   {r2(y,yh):.4f}   95% CI [{lo:.4f}, {hi:.4f}]   width {hi-lo:.4f}')
print(f'  RMSE {rmse(y,yh):.3f}   95% CI [{rlo:.3f}, {rhi:.3f}]')
# naive iid bootstrap for contrast -- shows how much the clustering matters
r2i=np.array([r2(*(lambda ii:(y[ii],yh[ii]))(rng.integers(0,len(y),len(y)))) for _ in range(500)])
ilo,ihi=np.percentile(r2i,[2.5,97.5])
print(f'  (naive iid bootstrap would give [{ilo:.4f}, {ihi:.4f}] -- {(hi-lo)/(ihi-ilo):.1f}x narrower, i.e. overconfident)')
print(f"\nH3 gate was R2 >= 0.60; reported as an honest near-miss at 0.581.")
print(f"  does the CI include 0.60? {'YES' if lo<=0.60<=hi else 'NO'}")
