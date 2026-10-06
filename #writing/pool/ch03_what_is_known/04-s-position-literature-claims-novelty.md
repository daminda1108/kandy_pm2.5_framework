## Position in the literature, and claims to novelty {#s-position-literature-claims-novelty}

The question this thesis asks, what an observation is worth before it is bought, is old and has
been asked well by several fields. Stating what they established is a precondition for claiming
anything, and the honest position is that the central idea here is not new. What is new is
narrower, and it is easier to defend once the boundary is drawn.

**Decision-theoretic value of information** formalised the question in the 1960s. The value of an
observation is the reduction in expected loss from having it before deciding [@Howard1966]. This
is the definition the present work uses informally, with predictive error standing in for loss.

Bayesian optimal experimental design asks which experiment to run given a model and a
utility, and supplies the machinery for choosing among candidate observations
[@Chaloner1995]. It assumes a model in which the candidate observations can be simulated, which
is exactly what a city with no monitors and no validated field does not have.

Observing-system experiments are the closest methodological ancestor and the comparison most
worth making. Operational weather centres routinely measure the worth of an instrument by
withholding it and re-running the forecast, and report per-instrument impact from data-denial
runs [@Samrat2025]. **The idea of measuring an observation's value by removing it is therefore
standard practice and this thesis does not claim it.** Two differences matter. Such experiments
run inside a dense global observing system and score against an analysis that itself depends on
the observations being assessed, whereas the measurement here is made in order to advise a city
that has no observations and is scored against monitors physically withheld from the model. And a
denial run is a genuinely different model run, since the assimilation re-converges without the
observation, whereas the tiers here are nested by construction and reproduce one another exactly.
{{ref:s-guarantees-enforced-mechanisms-discharged}} explains why that exactness is what turns an ablation into a measurement.

Air quality monitoring network design is a developed field with its own review literature
[@Verghese2022], and the nearest published neighbour to this thesis applies value of information
directly to low-cost particulate networks [@Choi2026]. That work optimises **where** to place
sensors within a region, using an advection-diffusion model and a loss defined over misclassified
air quality categories weighted by population and vulnerability. It is a more sophisticated
treatment of the placement question than anything attempted here. It also differs in three ways
that determine what each can answer. It optimises placement within a fixed class of instrument,
where this thesis prices dissimilar streams against one another, so that free terrain data and a
rural monitor and a satellite retrieval are compared on one axis. It is applied in a region that
already has regulatory monitors, where the design here exists to serve cities that have none. And
it is demonstrated on one region over six weeks, where the measurement here is made across a
multi-city panel.

### Novelty, separated by kind {#s-novelty-separated-kind}

Four different things get called new in this sort of work and conflating them is how novelty
claims fail under examination.

**The idea is not new.** Measuring the value of an observation by withholding it, formalising
that value decision-theoretically, and applying it to air quality networks have all been done,
and the paragraphs above give the references. Nothing in {{ref:s-marginal-predictive-value-each}} should be read as claiming
otherwise.

The application is close to new, and is the weaker half of the claim. Running the measurement
in order to advise cities that cannot validate a model, and scoring it on a panel assembled to
stand in for such cities rather than on the data-rich systems where observation impact is usually
studied, is a use of the method this thesis has not found reported. That is a statement about a
search of the literature and not a proof of absence.

The implementation is new, and is the more defensible half. The tiers of {{ref:s-information-budget}} are nested
so that withholding a stream reproduces the lower tier exactly rather than approximately, which
follows from a conservation property of the decomposition, not from a training procedure.
Admissibility is asserted in code in both directions, so a tier can neither use a stream it is
not entitled to nor silently fail to use one it is. {{ref:s-defects-found-audit-rather}} records what the absence of the
second check cost, which is the argument for it.

Two of the empirical results are new as findings, independently of the framework that
produced them. That the ordering of acquisition priorities differs between latitude bands, and
that a monitor-trained covariate deflates the measured value of the rung above it rather than
inflating its own, are both statements about the world that a reader could act on, and neither
depends on accepting anything else in this thesis.

One further boundary belongs here because it is easy to overstate. Leakage from ground monitors
into satellite-derived products is a known hazard in this field, and careful work on model
evaluation already addresses it, including through spatial cross-validation designed to stop
nearby monitors inflating apparent skill [@Just2020]. What {{ref:s-effect-monitor-trained-covariate}} adds is not the
observation that leakage exists. It is that the same contamination behaves differently when the
quantity being measured is the marginal value of an observation rather than a model's accuracy,
because it displaces the effect onto a neighbouring term where a test aimed at the contaminated
stream will not find it.
