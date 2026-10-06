## A physics-informed network transferred between continents {#s-physics-informed-network-transferred}

**What was expected.** A neural network constrained to obey an advection-diffusion-deposition
equation [@Raissi2019] should learn a representation of transport that is a property of the
physics rather than of the city it was fitted in. If so, a network trained where data is plentiful could be
transferred to a city where it is not, and the physical constraint would carry the transfer.

What happened. A time-dependent formulation was fitted at Medellin, reaching a coefficient
of determination of 0.932, and transferred to Chiang Mai, where it reached 0.765 with a bias of
-0.59 [ledger stage 2, 76,261 parameters]. By the standards of the transfer literature that is a
good result. It was nonetheless abandoned.

What it cost. Several months, and the larger part of the project's computational budget.

What it established. The transferred quantity was not what the design assumed. What survives
transfer is the **form** of the physics, which was imposed rather than learned and would have
been imposed identically without any network. What does not survive is the fitted parameterisation,
because those parameters encode the emission field and the boundary-layer climatology of the
city they were fitted in, and those are exactly the things that differ between cities. The
constraint made the model physically plausible without making it transferable, and plausibility
was not the problem.

This is the first appearance of a distinction the rest of the thesis depends on. **Imposing
physics and learning physics are different operations, and only the first transfers.** {{ref:ch-model}}
imposes.
