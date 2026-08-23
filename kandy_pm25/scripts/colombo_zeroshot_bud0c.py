"""Colombo re-run against the spec-compliant Bud0c. Gates R-G6, per osf.io/g6hqb."""
import sys, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from pathlib import Path
REPO=Path("D:/ProjectCD/kandy_pm25"); sys.path.insert(0,str(REPO/"scripts"))
from sklearn.ensemble import HistGradientBoostingRegressor
from modular_validation_all import FEATS, build_frame
MOD=REPO/"data/processed/modular"
G1_LO,G1_HI,G2_MIN,G3_MAX=13.43,45.54,0.60,40.0

sample=pd.read_csv(MOD/"validation_sample.csv"); manifest=pd.read_csv(MOD/"openaq_manifest.csv")
_,pool=build_frame(sample,manifest)
doy=pool.date.dt.dayofyear
pool["doy_sin"]=np.sin(2*np.pi*doy/365.25); pool["doy_cos"]=np.cos(2*np.pi*doy/365.25)
met=[c for c in FEATS if c in pool.columns]
pool=pool.dropna(subset=met+["pm25_city"]); pool["city"]=pool.city.astype(str)
geo=pd.read_csv(MOD/"bud0_static_geo.csv"); geo["city"]=geo.city.astype(str)
sat=pd.read_csv(MOD/"bud0_satellite_level.csv"); sat["city"]=sat.city.astype(str)
geo_f=[c for c in geo.columns if c not in ("city","geo_n_stations")]
p=pool.merge(geo,on="city",how="left").merge(sat,on="city",how="left")
p=p.dropna(subset=geo_f+["sat_level"])
feats=met+geo_f+["sat_level"]
print(f"training pool {len(p)} city-days, {p.city.nunique()} cities, {len(feats)} features")

# Colombo drivers + obs
import glob
fr=[pd.read_csv(f) for f in sorted(glob.glob(str(REPO/"data/raw/era5_colombo/colombo_era5_*.csv")))]
d=pd.concat(fr,ignore_index=True)
d["date"]=pd.to_datetime(d.datetime,errors="coerce").dt.tz_localize(None).dt.normalize()
g=d.groupby("date").agg({c:"mean" for c in ["temperature_2m","u_component_of_wind_10m",
    "v_component_of_wind_10m","boundary_layer_height"]}).reset_index()
g["wind"]=np.hypot(g.u_component_of_wind_10m,g.v_component_of_wind_10m)
o=pd.read_parquet(REPO/"data/processed/stage1_v2/dataset_v2_colombo_daily.parquet",
                  columns=["date","pm25_observed"])
o["date"]=pd.to_datetime(o.date).dt.tz_localize(None).dt.normalize()
c=g.merge(o.dropna().groupby("date",as_index=False).pm25_observed.mean(),on="date")
dy=c.date.dt.dayofyear
c["doy_sin"]=np.sin(2*np.pi*dy/365.25); c["doy_cos"]=np.cos(2*np.pi*dy/365.25)

# Colombo's OWN static geo + satellite level, pulled the same way
import ee; ee.Initialize(project="kandypinn")
LAT,LON=6.9271,79.8612
pt=ee.Geometry.Point([LON,LAT]).buffer(5000)
lev=ee.ImageCollection("projects/sat-io/open-datasets/GHAP/GHAP_Y1K_PM25").filterDate(
    "2019-01-01","2023-01-01").mean().select("b1").reduceRegion(
    ee.Reducer.mean(),pt,scale=1000,maxPixels=1e9).getInfo()["b1"]
print(f"Colombo satellite level = {lev:.2f} ug/m3")
c["sat_level"]=float(lev)
# static geo: Colombo's REAL LUR predictors, pulled 2026-08-23 with the same gee_city/osm_city
# functions that built the panel's, at the US Embassy monitor (6.909 N, 79.875 E).
cl=pd.read_csv(MOD/"lur_predictors_colombo.csv")
_missing=[f_ for f_ in geo_f if f_ not in cl.columns]
assert not _missing, f"colombo LUR missing {_missing}"
for f_ in geo_f: c[f_]=float(cl.iloc[0][f_])
print("Colombo static geo: REAL predictors (67 cols)")

c=c.dropna(subset=feats+["pm25_observed"])
print(f"Colombo {len(c)} matched days")
preds=[]
for s in (0,1,2):
    m=HistGradientBoostingRegressor(max_iter=300,learning_rate=0.06,random_state=s)
    m.fit(p[feats],p.pm25_city); preds.append(m.predict(c[feats]))
yh=np.median(np.vstack(preds),axis=0); y=c.pm25_observed.to_numpy()
rmse=float(np.sqrt(np.mean((yh-y)**2))); bias=float((yh.mean()-y.mean())/y.mean()*100)
mm=pd.DataFrame({"m":c.date.dt.month,"o":y,"p":yh}).groupby("m").mean()
sr=float(np.corrcoef(mm.o,mm.p)[0,1])
clim=pd.Series(y).groupby(c.date.dt.dayofyear.values).transform("mean").to_numpy()
r2c=1-((y-yh)**2).sum()/((y-clim)**2).sum()
r2p=1-((y-yh)**2).sum()/((y-y.mean())**2).sum()
print(f"\n=== COLOMBO vs Bud0c (n={len(c)}) ===")
print(f"  observed mean {y.mean():.2f}   modelled {yh.mean():.2f}")
print(f"  C-G1 RMSE            {rmse:8.2f}  band[{G1_LO},{G1_HI}]  {'PASS' if G1_LO<=rmse<=G1_HI else 'FAIL'}")
print(f"  C-G2 seasonal r      {sr:8.3f}  >={G2_MIN}            {'PASS' if sr>=G2_MIN else 'FAIL'}")
print(f"  C-G3 level bias      {bias:+8.1f}% <={G3_MAX}%          {'PASS' if abs(bias)<=G3_MAX else 'FAIL'}")
print(f"  C-G4 R2 vs clim      {r2c:8.3f}  >0                  {'PASS' if r2c>0 else 'FAIL'}")
print(f"       (plain R2 {r2p:.3f})")
print(f"\n  PRIOR: bias falls from +31.3% to under 15%  -> {bias:+.1f}%  {'HELD' if abs(bias)<15 else 'REFUTED'}")
print(f"  PRIOR: R2 vs climatology turns positive     -> {r2c:.3f}  {'HELD' if r2c>0 else 'REFUTED'}")
pd.DataFrame([dict(n=len(c),obs=y.mean(),mod=yh.mean(),rmse=rmse,seasonal_r=sr,
    bias_pct=bias,r2_clim=r2c,r2_plain=r2p)]).to_csv(MOD/"colombo_zeroshot_bud0c_realgeo.csv",index=False)
