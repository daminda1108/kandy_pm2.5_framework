## A rigid physical form fitted across cities {#s-rigid-physical-form-fitted}

**What was expected.** If a single parameterised form for valley confinement, taken from the
mountain meteorology literature [@DeWekker2015; @Stull1988], could be fitted jointly across
several cities, the fitted parameters would characterise valley behaviour in general and could be applied to a new valley.

What happened. Two of the form's six parameters, a trapping depth and a valley shape
exponent, were driven onto their bound constraints by the fit. Cross-validated skill was uneven:
correlation of 0.863 at one city and 0.323 at another [ledger stage 3 LOOCV].

{{fig:bound}}

What it cost. Less than the previous attempt, because the failure was legible early.

What it established. Parameters that saturate their bounds are not estimates. The data does
not contain the information needed to identify them, and a fit that reports them anyway is
reporting the boundary of the search space in place of a property of the atmosphere. This is
identifiability failure, and the useful response is not a better optimiser but a declaration:
those parameters are imposed, not estimated, and the model should say so. That declaration
became the fourth of the properties set out in {{ref:s-guarantees-enforced-mechanisms-discharged}}.

An unexpected consequence, and it belongs here rather than in a footnote. For most of this
project's history the outcome was recorded as **all six** parameters saturating rather than two.
The correction came from regenerating the figure during preparation of this thesis, not from
anyone questioning the claim, and the project's own epistemic ledger still carried the
overstatement until that point. A number that makes an argument stronger is the least likely
number to be checked. {{ref:s-defects-found-audit-rather}} is about errors of that kind, and this one is an instance of
the class it describes.
