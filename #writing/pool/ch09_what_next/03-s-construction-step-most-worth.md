## The construction step most worth revisiting {#s-construction-step-most-worth}

One finding in this thesis points at a specific line of code rather than at an instrument. It is
the result drawn in {{fig:dispersion}}, in {{ref:s-spatial-contrast-lost}}.

The dispersion solver was built to place the local increment by redistributing an emission
surface through terrain-steered flow. Scored against held-out stations it **removes** rank
correlation, taking the raw emission surface from {{claim:r2.rho_emission_surface}} down to
{{claim:r2.rho_with_atransport}} and improving only {{claim:r2.cities_improved}} of ten cities.
That result now holds on two independently selected sets of cities.

The implication is narrow and actionable. The benchmark for any replacement is not the delivered
field's {{claim:r2.rho_with_atransport}} but the undispersed surface's
{{claim:r2.rho_emission_surface}}, and a construction that simply declined to redistribute would
already be better than the one shipped. {{ref:ch-model-stops}} argues that the placement problem is
information-limited; this result says that the current construction is not even reaching the
limit that the information allows.
