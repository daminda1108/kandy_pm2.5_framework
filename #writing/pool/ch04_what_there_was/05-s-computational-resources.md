## Computational resources {#s-computational-resources}

The work runs on a single workstation with a consumer graphics processor, supplemented by a free
hosted notebook service for the neural network training described in {{ref:ch-eight-approaches-did-work}}. Total compute is
modest by the standards of the machine learning literature, and the reason is worth stating: the
binding constraint on this problem is the information content of the available observations, not
the capacity to fit a model to them. {{ref:ch-eight-approaches-did-work}} describes several attempts that consumed
substantial computation and produced no usable result, and none of them would have been rescued
by more.

The satellite and geographic data were extracted through a cloud-hosted earth observation
platform, which matters practically. A decade ago the terrain, land cover, night lights and
population extraction described here would itself have been a project. It is now a few hours of
scripting, and that shift is a large part of why a thesis of this kind is feasible at an
undergraduate scale at all.
