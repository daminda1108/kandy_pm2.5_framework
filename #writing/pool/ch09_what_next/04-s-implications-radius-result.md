## Implications of the radius result {#s-implications-radius-result}

A predictor of within-city pattern has to be measured over some area around each point, and the
size of that area is a free choice that is usually made without comment. Testing it directly
produces the most surprising result in this thesis. The figure below scores the best single freely
available predictor at a range of buffer radii, from a few hundred metres up to several kilometres,
against held-out monitors. If sub-kilometre structure were the thing being recovered, skill would
be highest at the smallest radius and fall away as the buffer widened. It does the opposite. Skill
rises with radius and peaks at {{claim:phase1.best_radius_km}} kilometres, which is coarser than
the cell the model reports on, and {{ref:s-implications-radius-result}} draws the consequence for resolution.

{{fig:radius}}

Predictor skill rises with the radius of the buffer over which a predictor is measured, and peaks
at {{claim:phase1.best_radius_km}} kilometres, which is coarser than the kilometre cell the model
reports on. Read with
{{ref:s-reason-change-support}}'s finding that within-cell spread exceeds between-cell spread, the band of usable
spatial information is bounded from both sides.

The consequence for anyone building a product of this kind is uncomfortable and worth stating
plainly. Increasing resolution is not the improvement it appears to be. A finer grid does not
recover the sub-grid variation, because that variation is not encoded in any available covariate,
and it moves the reporting scale further from the scale at which the predictors carry
information. The registered refinement test of {{ref:s-resolution-tested-refuted}} measured exactly this and found a
tenfold refinement in area worth {{claim:s1.paired_delta_on_refinement}} on the paired-site
ratio.

A more useful direction is the opposite one: report the within-cell distribution rather than a
cell value, which {{ref:s-reason-change-support}} shows is both well-posed and the larger of the two quantities.
