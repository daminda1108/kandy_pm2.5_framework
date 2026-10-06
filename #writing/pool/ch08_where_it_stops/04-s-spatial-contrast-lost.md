## Where the spatial contrast is lost {#s-spatial-contrast-lost}

The refutation also disposes of the premise that motivated it. Contrast is not destroyed by
coarsening. It is **relocated**. Tracking the spread through the build:

| stage | ratio of the ninetieth to the tenth percentile |
|---|---:|
| raw emission surface at {{claim:subgrid.fine_res_m}} m | {{claim:s1.contrast.raw_E_fine_94_m}} |
| after tempering | {{claim:s1.contrast.log1p_tempering}} |
| after dispersion at {{claim:subgrid.fine_res_m}} m | {{claim:s1.contrast.dispersion_94_m}} |
| after solving at {{claim:subgrid.production_res_m}} m | {{claim:s1.contrast.solve_at_238_m_production}} |
| reported at {{claim:subgrid.coarse_res_m}} m | {{claim:s1.contrast.report_at_998_m}} |

The dispersed field still spans {{claim:s1.contrast.report_at_998_m}} times at the delivered
resolution. There is no shortage of contrast. **It is in different places from where the survey
measured it**, which is a failure of placement rather than of dynamic range or of support.

An independent line agrees from the opposite direction, and it is the most actionable finding in
{{this:ch-model-stops}}. Scored across ten monitored cities, the raw emission surface ranks neighbourhoods
at {{claim:r2.rho_emission_surface}}. Passing it through the dispersion solver **lowers** that to
{{claim:r2.rho_with_atransport}}, improving only {{claim:r2.cities_improved}} of ten. The step
that redistributes contrast is the step that misplaces it.

{{fig:dispersion}}

That result now holds on two independently selected sets of cities, which is why {{ref:s-construction-step-most-worth}} treats
the dispersion step and not the source surface as the place to intervene.
