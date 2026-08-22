import pandas as pd, numpy as np
from scipy.stats import spearmanr

SITES = [
 # id, name, lat, lon, PM10 obs, censored?
 ("1.1","Kandy bus terminus",        7.2896,80.6338, 150, True),
 ("1.2","Girls' HS junction",        7.2870,80.6262, 150, True),
 ("1.4","Kandy Police Station",      7.2928,80.6337, 150, True),
 ("1.7","Sangaraja Mawatha",         7.2894,80.6463, 150, True),
 ("2.1","Girls' HS INSIDE grounds",  7.2870,80.6262, 32.5,False),
 ("2.2","Pushpadana Girls' College", 7.2940,80.6329, 32.5,False),
 ("2.3","Trinity College",           7.2999,80.6376, 32.5,False),
 ("3.1","Gatambe temple",            7.2676,80.6008, 230, False),
 ("3.2","Bot.Gardens ENTRANCE",      7.2682,80.5974, 110, False),
 ("4.2","Katugastota junction",      7.3221,80.6250, 340, False),
 ("5.1","Gannoruwa school",          7.2851,80.5895, 15,  False),
 ("5.5","Bot.Gardens 300m INSIDE",   7.2707,80.5963, 4,   False),
]

fr=[]
for y in range(2019,2024):
    d=pd.read_parquet(f"data/processed/decomp/kandy_decomp_predictions_{y}_additive_v3.parquet")
    d["t"]=pd.to_datetime(d.time); fr.append(d)
d=pd.concat(fr,ignore_index=True); d["pm25_q50"]=d.pm25_q50.clip(lower=0)
d["h"]=d.t.dt.hour
mid=d[d.h.between(11,13)]                      # the paper's 11:00-14:00 window
g=mid.groupby(["lat","lon"]).pm25_q50.mean()
lats=np.sort(d.lat.unique()); lons=np.sort(d.lon.unique())
dlat=np.diff(lats).mean()*111.0; dlon=np.diff(lons).mean()*110.2
print(f"grid {len(lats)}x{len(lons)}   pixel {dlat*1000:.0f} x {dlon*1000:.0f} m")
print(f"bbox lat {lats.min():.4f}-{lats.max():.4f}  lon {lons.min():.4f}-{lons.max():.4f}\n")

rows=[]
for sid,nm,la_,lo_,obs,cen in SITES:
    inside = lats.min()-dlat/222 <= la_ <= lats.max()+dlat/222 and lons.min()-dlon/220 <= lo_ <= lons.max()+dlon/220
    la=lats[np.abs(lats-la_).argmin()]; lo=lons[np.abs(lons-lo_).argmin()]
    rows.append(dict(id=sid,name=nm,lat=la_,lon=lo_,obs=obs,cens=cen,
                     px=(round(la,4),round(lo,4)), model=float(g.loc[(la,lo)]), inside=inside))
r=pd.DataFrame(rows)
print(f"{'id':<5}{'site':<28}{'obs PM10':>9}{'model PM2.5':>13}   pixel")
for x in r.itertuples():
    print(f"{x.id:<5}{x.name:<28}{('>'+str(int(x.obs))) if x.cens else f'{x.obs:g}':>9}{x.model:>13.2f}   {x.px}")

print("\n=== PAIRED-SITE TEST (same place, different microsite) ===")
for a,b in [("3.2","5.5"),("1.2","2.1")]:
    A=r[r.id==a].iloc[0]; B=r[r.id==b].iloc[0]
    sep=np.hypot((A.lat-B.lat)*111,(A.lon-B.lon)*110.2)*1000
    obs_r = A.obs/B.obs
    mod_r = A.model/B.model
    print(f"  {a} vs {b}: separation {sep:.0f} m | same pixel: {A.px==B.px}")
    print(f"     observed ratio {obs_r:6.2f}x     model ratio {mod_r:6.3f}x")

print("\n=== RANK CORRELATION ===")
for lab,sub in [("all 12 sites", r), ("9 uncensored", r[~r.cens])]:
    rho,p = spearmanr(sub.obs, sub.model)
    print(f"  {lab:<15} n={len(sub):2d}  Spearman rho = {rho:+.3f}  (p={p:.3f})")
print(f"\n  observed spread : {r.obs.min():g} - {r.obs.max():g}  = {r.obs.max()/r.obs.min():.0f}x")
print(f"  model    spread : {r.model.min():.2f} - {r.model.max():.2f}  = {r.model.max()/r.model.min():.2f}x")
r.to_csv("data/processed/decomp/elangasinghe_spatial_test.csv",index=False)
