# Reproducibility, data and computation {#ch-reproducibility-machinery-catches-errors}

## Generated numbers {#s-generated-numbers}

Every numeric result in this thesis is a token resolved when the document is built, and no result
is typed into the prose. A generating script recomputes each value from the scored file it derives
from and records, beside the value, the statistic, the sample size and the source file. At build
time the stored values are recomputed and compared, and the build refuses to produce a document if
any value has drifted. Numbers taken from the literature carry a citation instead of a token, and
configuration values are listed in {{ref:app-constants-configuration}}. The figures and tables are
regenerated from the same files on every build, so a table cannot fall behind its data.

## Pre-registration {#s-pre-registration-working-practice}

The cross-city tests of {{ref:a-app-panel}} and the spatial tests of {{ref:a-app-spatial}} were
registered on the Open Science Framework before they were scored, with the hypotheses, the
estimators, the summaries and the pass conditions fixed in advance. Deviations were lodged as
dated amendments. {{ref:app-registered-predictions-their-outcomes}} lists every registered
prediction and its outcome, including those that were refuted. Analyses added after scoring, such
as the re-analysis of {{ref:s-like-for-like}} and the deployed-model rung of
{{ref:s-kandy-model-rung}}, are labelled as exploratory wherever they appear; the latter's design was
committed to the version-control record before it was scored.

## Reproducing this work {#app-reproducing-work}

The analysis code, the generating scripts for every claim, the figure and table scripts, the
document build and the registration documents are held in a public version-controlled repository,
<https://github.com/daminda1108/kandy_pm2.5_framework>. The document is produced in
four steps, each of which refuses to proceed if the one before it failed: regenerate and check every
claim, generate the figures and tables, assemble the chapters with every token resolved, and render
against a reference document that carries the typography. The observational inputs are third-party
and are not redistributed; their sources are given in {{ref:ch-available-data-deliberate-constraint}}.
The work is therefore auditable, and reproducible conditional on obtaining the source datasets.
It has not yet been reproduced by anyone outside the project, and this thesis claims a documented
workflow rather than a demonstrated independent reproduction.

## Data requested but not obtained {#s-data-requested-but-obtained}

Three local records would have changed what this thesis could establish. The national regulatory
authority's Kandy station holds an hourly record of particulate matter, gases and meteorology from
2019, with a gap of about fifteen months; access was granted in principle for academic use, subject
to a formal request and a signed agreement, and the record was not obtained within the period of
this work. The regional stations of the national research organisation supply the external check
of {{ref:s-checks-kandy-carry-weight}} through a published paper; a direct request would provide a
genuine regional background series. The university's own sensor network was identified late and not
pursued. The reference monitor that anchored earlier published Kandy records is no longer operating.

## Computational resources {#s-computational-resources}

The work ran on a single workstation, supplemented by a free hosted notebook service for the
heaviest cross-city runs. Satellite, reanalysis and geographic data were extracted through a
cloud-hosted earth observation platform. The binding constraint on the problem is the information
content of the available observations, not computing capacity.
