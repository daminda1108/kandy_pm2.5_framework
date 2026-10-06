## Requirements for estimating the atmospheric state {#s-three-conditions-weather-forecasting}

Numerical weather prediction is the most developed example of estimating the state of the
atmosphere from observations and physical models, and its skill rests on three conditions
[@Bauer2015].

The first is a dense, global observing system. Surface stations, radiosondes, aircraft, buoys
and satellites report continuously, so that the analysis at any location is constrained by
observations made within a few hundred kilometres in the preceding hours [@Bauer2015]. Coverage
is uneven, but no large populated region is unobserved.

The second is well-established governing physics. The equations of motion for a compressible
fluid on a rotating sphere are known. Processes the model cannot resolve, such as convection and
turbulence, are represented by parameterisations that can be evaluated against observations, and
much of the remaining forecast error originates in these parameterisations and in the initial
state, both of which can be measured and improved.

The third is data assimilation. Established methods combine the model state with new
observations in a statistically consistent way, so that each observation corrects the state and
the correction is carried forward in time [@Bauer2015; @Bocquet2015].

Where any of these conditions is weakened, skill declines. For surface PM2.5 in a city without
monitors, all three are weaker, as {{ref:s-air-quality-satisfies-none}} shows.
