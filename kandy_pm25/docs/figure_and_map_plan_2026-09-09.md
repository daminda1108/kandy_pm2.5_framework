# Plan: GIS-grade maps, six new figures, and the chapter titles

**Written 2026-09-09 after checking the libraries, the data and the existing figure code.**
Nothing below is proposed on the assumption that something exists. Every input was verified.

---

## 1. What the investigation found

### Libraries are already in place

| available | version | | missing | needed for |
|---|---|---|---|---|
| geopandas | 1.1.2 | | `mapclassify` | choropleth class intervals |
| cartopy | 0.25.0 | | `adjustText` | non-overlapping city labels |
| contextily | 1.7.0 | | | |
| rasterio | 1.4.4 | | | |
| shapely / pyproj | 2.1.2 / 3.7.2 | | | |
| osmnx | 2.1.0 | | | |
| matplotlib-scalebar | 0.9.0 | | | |

**Cartopy's Natural Earth cache is populated**: 65 shapefiles under
`~/.local/share/cartopy`, 55 physical and 10 cultural. Coastlines, land, borders and lakes can be
drawn offline. No download is required and no basemap tile service is needed.

Two packages should be installed rather than worked around: **`mapclassify`** and **`adjustText`**.
Both are small, both are the correct tool, and hand-rolling either would be the kind of degraded
substitute this project's rules forbid.

### The maps are not maps

Only `plot_sensor_design.py` imports a GIS library. The three map figures in the thesis body do not.

- **`obsdensity`** (Chapter 1) and **`panel`** (Chapter 4) are `scatter(lon, lat)` on bare axes
  labelled "longitude" and "latitude". **There is no coastline, no landmass, no projection and no
  graticule.** A reader is shown a cloud of dots and has to reconstruct the world from memory. For
  the figure that opens the thesis and carries its motivating claim, that is the single weakest
  visual decision in the document.
- **`valley`** (Chapter 2) is better. It computes a hillshade from the DEM by hand and lays a
  `gist_earth` ramp over it, with a reasoned comment about why `terrain` would make the valley
  floor read as water. What it lacks is the cartographic furniture: no projection, no scale bar,
  no north arrow, no contours, no place labels, no locator inset.

### The data for all six proposed figures already exists

| figure | source | rows |
|---|---|---|
| station-count curve | `modular/station_count_curve.csv` | 425 |
| model-family tournament | `modular/spatial_tournament.csv` + `embedding_spatial_test.csv` | 93 + 47 |
| loss sensitivity | `modular/loss_sensitivity_steps.csv` + `loss_sensitivity.csv` | 12 + 46 |
| partition sensitivity | `decomp/kandy_fmin_sweep.csv` + `kandy_partition_v2.json` | 35 + 5 years |
| paired versus unpaired | `modular/siting_experiment.csv` | 6,880 |
| cluster bootstrap | `modular/cluster_bootstrap.csv` | 30 |

**No new computation is needed for any of the six.** This is a plotting job, not an analysis job.

### House style the new work must match

From `thesisviz.py`: Times New Roman serif, 400 dpi, `lines.linewidth` 1.2, and a fixed palette.

```
ink #1a1a1a   muted #6b6b6b   line #4d4d4d   free #4393c3
local #d6604d   regional #f4a582   good #4d9221   bad #c51b7d
fill #f2f2f2   fill2 #e3eef6
```

The stated rule is that *a reader should not be able to tell which library drew which picture*.
Cartopy renders through matplotlib, so a projected map inherits the same fonts and palette and
that rule survives the change.

---

## 2. The three maps

### M1. `obsdensity`, Chapter 1 — the motivating figure

Rebuild the left panel as a **Robinson projection** with Natural Earth land in `fill`, coastlines
in `line` at 0.4 pt, and a 30-degree graticule. Keep the existing two-tone scatter for all
locations against reference-grade, keep the tropic lines, keep the Kandy star. Add a scale-free
inset showing Sri Lanka at country scale, because a single star at world scale tells a reader
nothing about the target. The right-hand latitude histogram is already correct and stays.

*Why Robinson:* the claim is about latitude, and an equal-area projection distorts the latitude
axis the argument rests on. Robinson keeps latitude bands readable, which is what this figure is
arguing about.

### M2. `panel`, Chapter 4 — where the validation comes from

Same projection and basemap as M1, so the two read as a pair and a reader can compare the panel
against the full population directly. Points sized by withheld monitors as now. Add `adjustText`
labels for the deep-tropical members only, since those are the ones the Kandy argument turns on
and they are currently indistinguishable dots. Keep the band histogram.

### M3. `valley`, Chapter 2 — the setting

Reproject the DEM to **UTM 44N**, which is what `kandy_dem_utm44n_90m.tif` already holds, so
distances on the page are true. Add: elevation contours at 100 m, a scale bar, a north arrow, the
domain boundary, labels for Hantana and the Mahaweli corridor, and the two sensor locations. Keep
the hand-computed hillshade and the `gist_earth` ramp, both of which are already right, and keep
the south-to-north section panel.

*Not proposed:* a satellite basemap under the terrain. `contextily` would need a tile service,
the licence terms would need checking for a published thesis, and the DEM already carries the
information the figure exists to show.

### Two smaller additions

`transect` and `withinpixel` are profile plots, not maps, and should stay that way. Each gains a
**small locator inset** showing where in the domain the sites sit, which is currently left to the
reader.

---

## 3. The six new figures

Each covers a finding that currently exists only as prose or a table. Ordered by how much the
thesis needs it.

**N1. Station-count curve** — Section 7.2, beside the existing ladder figure.
Median RMSE reduction against station count from one to eight, with the paired bootstrap interval,
and a marked annotation at k=1. Band-stratified curves as thin lines behind the pooled one.
*Why it earns a place:* saturation at one station is among the cleanest findings in the thesis and
it currently has no figure at all.

**N2. Model-family tournament** — Section 8.5, replacing part of the prose.
A horizontal dot-plot: seven admissible families plus foundation-model embeddings, each showing
paired improvement over the benchmark with its interval, against a vertical line at the registered
detection limit of 0.130. Oracle families below a separator, clearly labelled as inadmissible.
*Why:* turns "we tried everything and nothing beat a single free raster" from a claim a reader
must take on trust into one image they can check.

**N3. Loss sensitivity and the sign flip** — Section 7.2.1.
Two panels. Left: the three ladder steps under four losses, as grouped bars. Right: the
deep-tropical paired advantage under each loss, with the sign change from positive on daily error
to negative on exceedance shown across a zero line.
*Why:* this is the most consequential qualification in the thesis and it is currently a table.

**N4. Partition sensitivity, three axes** — Section 6.6.
Three small panels sharing a y-axis: `f` across anchored years, `f` across the `F_min` sweep, and
`f` across the three background-window forms. A shaded band marks the full range.
*Why:* conflating these three axes is exactly the error that reached the abstract and had to be
corrected as F.108. A figure makes them impossible to confuse again.

**N5. Paired versus unpaired** — Section 7.2 or Chapter 10.
The siting experiment shown both ways: the medians per method side by side, then the within-city
paired differences as a distribution straddling zero.
*Why:* the difference-of-medians trap has now caught this project four separate times. One picture
would teach it better than the four paragraphs currently spent on it.

**N6. Cluster bootstrap intervals** — Section 7.2.
A forest plot: three ladder steps, each with the city-level interval and the network-level interval
drawn together so the widening and the survival are visible at once.
*Why:* answers a reviewer objection visually, and shows that widening every interval by half again
changes no conclusion.

**Deliberately not proposed:** figures for the precipitation null, the campaign costing, or the
chemistry bounds. All three are table-shaped and a figure would be decoration.

---

## 4. Chapter titles

The current set mixes registers. Five chapters open with a conversational phrase, which reads
oddly against a formal abstract, while Chapter 7 in particular understates what it does.

| | current | proposed |
|---|---|---|
| 1 | Why the weather is known and the air is not | **Why weather is forecast and air quality is not** |
| 2 | Kandy: the setting, the record and the stakes | *(unchanged, revised this session)* |
| 3 | What is already known about Kandy's air | **Prior measurement, and the gap it leaves** |
| 4 | What there was to work with | **The available data, and a deliberate constraint** |
| 5 | What was tried and did not work | **Eight approaches that did not work** |
| 6 | The model | *(unchanged)* |
| 7 | Making sure it works | **Validation without local ground truth** |
| 8 | Where the model stops | *(unchanged)* |
| 9 | What to build next | **What to measure next** |
| 10 | Software, reproducibility, and the machinery that catches errors | **Reproducibility, and the machinery that catches errors** |

The two that matter most are 5 and 7. **"Eight approaches that did not work"** names a number and
is therefore a claim rather than a mood. **"Validation without local ground truth"** states the
thesis's hardest problem in the contents page, where "Making sure it works" states nothing.

---

## 5. Order, and what could go wrong

1. **Install `mapclassify` and `adjustText`.** Minutes.
2. **Chapter titles.** Ten lines, no risk, and it improves the contents page immediately.
3. **N1, N4, N6** — the three simplest figures, all reading a single small file.
4. **N2, N3, N5** — need two files each or a distribution rather than a summary.
5. **M3 `valley`** — one city, one DEM already in the right projection, no network access.
6. **M1 and M2** — the world maps, done together so they read as a pair.
7. **Lead-in paragraphs** for all six new figures, to the standard set this session.

⚠ **Risks worth stating in advance.** Cartopy's Natural Earth cache is populated for the features
checked, but a feature at a scale not yet cached will attempt a download and fail silently on a
machine without access; every new map should assert its features loaded before saving.
⚠ Adding six figures makes the thesis 41 figures, and the figure numbering is generated by order
of first appearance, so every insertion renumbers what follows. That is handled by the build, but
any prose that names a figure number rather than using a token would break. A check for that
should run before the first insertion.
