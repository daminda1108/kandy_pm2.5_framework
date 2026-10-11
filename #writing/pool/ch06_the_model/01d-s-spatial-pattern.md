## The local pattern {#s-spatial-pattern}

The pattern *P*(*x*, *y*, *t*) decides where the local increment sits. In the delivered field it is
the product of two factors, renormalised to unit spatial mean at every hour, and neither is fitted
to concentrations measured in Kandy. This is the construction scored in the ten analogue cities
({{ref:s-model-across-ten-cities}}). A third factor, a transport calculation, was part of the
delivered pattern until it was shown to lower agreement with withheld stations; it is described
below and retained only as an alternative.

**A level surface.** The 2019 to 2023 mean of the one-kilometre satellite-derived surface over the
domain [@vanDonkelaar2021], normalised to unit mean. It gives the city a gentle core-high, ridge-low
shape (about ten per cent each way) and carries no daily information.

**Terrain confinement.** *M* = 1 + κ *w*(BLH) *c*(*x*, *y*), where *c* is a standardised index of
how far each cell lies below the surrounding terrain, computed from the elevation model
[@Farr2007], and *w* is a trapping weight that equals one when the boundary layer is far below the
ridges and falls to zero once it rises above them. Material accumulates in the valley floor at
night and is mixed out by day. The amplitude κ and the effective ridge height are physical priors
({{ref:app-constants-configuration}}). They could not be fitted at Kandy, because confinement and
the emission surface are both highest on the same valley floor and their effects cannot be
separated with the observations available.

**A transport calculation, no longer in the delivered field.** A road-traffic emission surface
was built from the street network [@OpenStreetMap]: estimated traffic volume from network
centrality (betweenness for through-traffic, closeness for trips that start and end in the city),
multiplied by an emission factor that rises under congestion [@Ntziachristos2000]. That surface was
carried through a steady advection and dispersion calculation on mass-consistent winds that follow
the terrain, computed by WindNinja [@Forthofer2014] for each wind sector, wind speed and day or night
stability class, and entered with an amplitude that scaled with an emission-timing profile for road
traffic [@Crippa2020] and inversely with the product of wind speed and boundary-layer height. On
identical held-out stations in ten cities the dispersion step lowered rank agreement
({{ref:s-spatial-contrast-lost}}), so the delivered field no longer uses it. At the one Kandy site
with an external record it matched the annual means more closely ({{ref:s-checks-kandy-carry-weight}}),
which is noted rather than used to choose, because one site cannot outweigh a ten-city test.

The two factors are proxies for **where** local material accumulates, not a source inventory. The
particulate level is carried by *T*(*t*), which is constrained by total observed concentration from
every source, so the pattern decides only how the local increment is spread. A source that does not
follow the surface, such as domestic biomass burning on the rural fringe, is placed in the wrong cell
rather than omitted ({{ref:s-excluded-processes-known-limits}}). In the ten analogue cities this
construction ranks withheld monitors with a median correlation of
{{claim:scorecard.spatial_rho_median}}, of the same order as a free built-up land-cover layer
({{claim:r2b.rho_BU}}) on a different selection of stations.
