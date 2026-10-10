## The assumptions of the decomposition {#s-decomposition-assumptions}

### The uniform background assumption {#s-uniform-background-assumption}

Taking *B*(*t*) uniform over the domain looks like a strong physical assumption and is mostly a
definition. The decomposition splits concentration into a part with no horizontal structure at
this scale and a part with all of it, so anything varying across fifteen kilometres is assigned
to the increment by construction. The assumption is not that regional air is truly uniform. It is
that the split is useful, which requires the uniform part to be large and the residual structure
in it to be small beside the increment's.

Three lines support that, and one of them is a measurement made for this thesis.

Regional air arriving over the basin has travelled hundreds of kilometres and is well mixed
through the depth of the boundary layer, so its horizontal gradient across fifteen kilometres is
small compared with a local increment whose sources sit inside the domain.

If the background were behaving as a locally accumulating quantity it would dilute as the
boundary layer grows through the day. Fitting the exponent that would express that gives
{{claim:dilution.exponent}} against a value of one for pure inverse-height dilution, so the
component is close to inert to the diurnal cycle. That is the behaviour of air already mixed
rather than air accumulating in place.

{{ref:s-independent-chemical-check}} adds a model-based consistency check: in the composition model, air
classified by back-trajectory arrival sector as continental is more secondary-rich, and therefore
more aged, than air arriving from the ocean. A background composed of aged air is what the decomposition requires.

The assumption is nonetheless the one a denser network would test first, and {{ref:s-marginal-predictive-value-each}} is
explicit that the proxy standing in for *B* is the weakest link in the chain.

### The imposed pattern is not an arbitrary prior {#s-imposed-pattern-arbitrary-prior}

If *P* were chosen freely it would carry no information and the conservation property would
merely make it harmless. Three things stop it being arbitrary, and the third matters most.

It is constructed from measured quantities rather than fitted parameters. The surface combines
an emission proxy built from the road network [@Ntziachristos2000] with a confinement term
built from the digital elevation model, and neither is tuned to concentration data in the city where it is applied.

It is falsifiable and has been scored. Across the ten cities of {{ref:s-model-across-ten-cities}} the pattern's rank
against held-out monitors is reported rather than assumed, with a median of
{{claim:scorecard.spatial_rho_median}}.

**And it has been partly refuted, which an arbitrary prior cannot be.** {{ref:s-spatial-contrast-lost}} reports that
the dispersion step, which is the part of the model that redistributes the emission
surface through terrain-steered flow, **lowers** rank from {{claim:r2.rho_emission_surface}} to
{{claim:r2.rho_with_atransport}}. A prior that cannot fail would not have produced that result,
and the appropriate response is {{ref:s-construction-step-most-worth}}'s rather than a defence of the model.
