## The local pattern {#s-spatial-pattern}

The pattern *P*(*x*, *y*, *t*) decides where the local increment sits. It is the product of three
factors, renormalised to unit spatial mean at every hour, and none of them is fitted to
concentrations measured in Kandy.

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

**Transport of local emissions.** A road-traffic emission surface is built from the street
network [@OpenStreetMap]: estimated traffic volume from network centrality (betweenness for
through-traffic, closeness for trips that start and end in the city), multiplied by an emission
factor that rises under congestion [@Ntziachristos2000]. That surface is carried through a steady
advection and dispersion calculation on mass-consistent winds that follow the terrain, computed
by WindNinja [@Forthofer2014] for each wind sector, wind speed and day or night stability class.
The resulting shape enters with an amplitude that scales with an emission-timing profile for road
traffic [@Crippa2020] and inversely with the product of wind speed and boundary-layer height,
so the pattern sharpens in still, shallow rush hours and relaxes in windy, deep afternoons.

The traffic surface is a proxy for **where** local combustion happens, not a source inventory.
The particulate level is carried by *T*(*t*), which is constrained by total observed concentration
from every source, so the proxy decides only how the local increment is spread. Its weakness is
known and measured: a source that does not follow the road network, such as domestic biomass
burning on the rural fringe, is placed in the wrong cell rather than omitted
({{ref:s-excluded-processes-known-limits}}). The pattern is scored against monitors withheld in
the ten analogue cities ({{ref:s-model-across-ten-cities}}), and {{ref:s-spatial-contrast-lost}}
reports that the transport factor lowers, rather than raises, its agreement with them.
