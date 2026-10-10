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
{{this:ch-model-stops}}. Three surfaces were scored on exactly the same held-out stations in
{{claim:r2b.cities}} monitored cities: the raw road-traffic emission surface, the same surface after
the dispersion solver (the step the delivered field uses), and the simplest free alternative, the
built-up fraction of land cover within one kilometre of each station, which involves no model. The
median rank correlations are {{claim:r2b.rho_S}} for the raw surface, {{claim:r2b.rho_C}} after
dispersion and {{claim:r2b.rho_BU}} for the built-up fraction. Dispersion improves on the raw surface
in only {{claim:r2b.C_minus_S_wins}} of the {{claim:r2b.cities}} cities, and the built-up fraction
ranks above the dispersed surface in {{claim:r2b.BU_minus_C_wins}} of them. The magnitudes are
also wrong in the same direction: the station means span a ratio of {{claim:r2b.contrast_obs}}
between their ninetieth and tenth percentiles, while the raw and dispersed surfaces span
{{claim:r2b.contrast_S}} and {{claim:r2b.contrast_C}}, so the dispersion step widens a contrast that
is already too wide. (In the delivered field the surface shapes only the local increment, which is
why the field's own contrast is far smaller.)

**The dispersion step has therefore not earned its place.** It is physically motivated, and it
remains in the delivered field as a declared modelling choice, but it is not a validated
improvement: on every comparison made, a simpler surface places concentration at least as well.
Physical sophistication and predictive skill did not improve together here.

{{fig:dispersion}}

The first comparison, without the built-up arm, was registered in advance; the three-way comparison
on identical sites was added after the second external review and is exploratory. The direction
holds on two independently selected sets of cities, which is why {{ref:s-construction-step-most-worth}}
treats the dispersion step, not the source surface, as the place to intervene.
