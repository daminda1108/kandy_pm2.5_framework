## The two correction terms {#s-two-correction-terms}

The elementary form fails in two specific and diagnosable ways. Each additional term repairs
exactly one of them.

**The increment split.** When the hourly total falls below the background, inc is negative, and
multiplying a core-high pattern by a negative number renders the city centre **cleaner** than the
countryside. The defect is obvious once seen and invisible in every aggregate statistic, because
it preserves the mean exactly. Against the unconstrained background it occurs in
{{claim:field.precap_excess_mean}} per cent of Kandy hours and, because ventilation peaks when
the boundary layer is deepest, in {{claim:field.precap_excess_midday}} per cent of midday hours.
The defect therefore concentrates in exactly the hours a daytime user would look at. The repair
is to structure only the accumulation above background and let ventilation below it apply
uniformly, which is the max(inc, 0) × *P* and min(inc, 0) pair. The basin mean is preserved
exactly and the midday inversion falls to {{claim:field.postcap_inversion_midday}} per cent.

**The floor on well-mixed hours.** On hours when the city is well ventilated and the total falls
to or below the background, the split above renders the map perfectly flat. Measurements from a
city with a dense network show that such hours are not flat. A bounded, mean-zero term
*e*(*t*)(*P* − 1) restores a small amount of structure on those hours. Being mean-zero, it leaves
conservation exact; being bounded below by zero and acting only on the accumulation side, it
cannot re-invert the core; and setting its scale to zero recovers the previous form exactly,
which is verified rather than asserted.
