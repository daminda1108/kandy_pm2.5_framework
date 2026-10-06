# The model {#ch-model}

The physics in this model is deliberately modest and the machine learning is entirely
conventional. Neither is the contribution. What is unusual is that the model states which
observations it is allowed to use, and that taking one of them away returns it exactly to the
simpler version rather than approximately. That is what makes {{ref:s-marginal-predictive-value-each}} a measurement rather than a
set of ablations, and everything else in {{this:ch-model}} exists to support it. The construction as a
whole was traced end to end in {{dia:pipeline}}; {{this:ch-model}} takes its parts in turn.
