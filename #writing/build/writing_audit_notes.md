## Reading (by hand, 2026-10-12): what to fix, in order

The measured lists below say *where*; this section says *what matters*. Nothing here has been rewritten except the
items under "already fixed", which were errors of fact rather than of style.

### Already fixed during this audit (stale after release r18)

The daily cycle was refitted to the regulatory station in r18, but four passages still described the sensor-shaped
anchor as the delivered field. Corrected: the humidity-scenario section (`theses/a/rh_scenario.md`, first and last
paragraphs, and the title and column header of its table), conclusion 2 (it compared the humidity scenario's 0.486,
computed on the old anchor, with the new baseline 0.505), the discussion ("the field's nights are too high"), the summary
(the peaks' depth "depends on the humidity correction") and the results lead. Thesis and summary rebuilt; summary still
two pages.

### A. Correctness and consistency (do first)

1. **Table 4.1, "Value of daily observations"** compares *one* station read daily (42.1 per cent) with *two* used only to
   calibrate (11.0 per cent). The abstract compares two with two (53.3 against 11.0). Use like with like
   (`src/t_tables.py:576`).
2. **How numbers print.** Trailing zeros are dropped and the minus sign is a hyphen: "daily correlation 0.6, 0.73"
   (abstract), "1.95 observed, 1.8 modelled" (Table 4.1), "within -1 per cent", "-2.79 to 25.8". Precision is
   also mixed in the abstract (4.83 beside 53.3 and 11.0). This is one rule in the claim renderer (a fixed number of
   decimals per claim, a typographic minus), not a hand edit. It is mechanical and can be done for you.
3. **Conclusion 1**: "departs from the anchor by at most 0.0 per cent" reads as a slip; say the city mean equals the
   anchor exactly (to rounding), or quote the small value with its unit.
4. **Seven sentences narrate the review process** ("added after an external review asked for them", "identified by an
   external review"). A thesis says what was tested and when the test was fixed; who asked belongs in
   `CHANGELOG_thesis.md`. List in section 1 below.

### B. Structure and repetition

5. **The correction history is told in too many places.** "As first delivered", "before the refit" and similar appear
   in the methods (`01b`), the CEA section, the interval section, the field description, the discussion, the conclusions
   and the summary. Suggested division: the methods describe the model as delivered; the before-and-after is reported
   once, in the CEA section (level and daily cycle) and the interval section (width), where the tests are; the
   discussion and conclusions state the current result with at most one clause of history.
6. **Standing caveats are restated more than they need to be** (section 2a): "one station" 13 times in 8 main-text
   files; the humidity correction 16 times in 11 files; point against cell 11 times; "fixed before scoring" 12 times.
   The humidity story is now secondary (the delivered daily shape no longer comes from the sensors): it could live in
   its own section and one sentence of the known limits.
7. **Near-duplicates** (section 2b): the guideline-exceedance sentence appears almost verbatim in the field
   description, the discussion and the conclusions; the interval's missing uncertainty sources twice (§2.3.2 and the
   interval section); the constant-humidity Barkjohn sentence twice (data streams, known limits); the radius result
   twice (chapters 8 and 9).
8. **A defensive register.** "Not" occurs 8.4 times per 1,000 words, "rather than" 3.1 and "only" 3.3. Many results are
   stated by what they are not. Table 4.1 already carries the permitted interpretation of each quantity, so the abstract
   and the conclusions can state the positive result and let the table hold the limits.
9. **Number-dense sentences** (section 5a): 19 main-text sentences carry six or more numbers; the worst are the
   before-and-after paragraph of the CEA section (11), the station-count sentence of the measurement priorities (11), the
   held-out level sentence (10) and conclusion 3's level item (10). Conclusions in particular read better with few
   numbers, since Table 4.1 holds them.
10. **Long sentences** (section 5b): 18 main-text sentences exceed 60 words; the results lead (86 words) and the
    network-design sentence of the continuation programme (85) are the first to split.

### C. Terminology: pick one name per thing

11. **"Anchor" has two meanings.** It is the temporal estimate *T*(*t*) (about 125 uses as "anchor", "temporal anchor")
    and, in the ten-city sections, the two **anchor stations** (23 uses). A reader meets "the anchor stations' own
    climatology" next to "the temporal anchor". Consider "calibration stations" for the ten-city pair.
12. **The product** is "the field" (76), "the delivered field" (24), "the reconstruction" (12), "the map" (7) and "the
    delivered series" (5). "Field" for the product, "delivered field" only when contrasting it with a variant, and
    "reconstruction" for the framing in the title and abstract would be enough.
13. **"Held-out" (26) and "withheld" (23)** mean the same thing. Either unify or keep a stated rule (held-out for time
    splits, withheld for stations).
14. **"Kandy sensors"** (6) is now ambiguous, because the regulatory station is also a Kandy instrument; "the two
    low-cost sensors" is already the majority term (32).
15. "Daily cycle" (35) against "diurnal cycle" (5), and "regulatory station" (40) against "regulatory monitor" (5):
    small, but unify.

### What I would leave alone

The abstract's order (what was built, what holds against the station, the level, the guideline, the ten cities, the
ladder, the limits) is sound, and Table 4.1 is the most useful single object in the thesis for an examiner. The
continuation chapter reads as a plan rather than a defence, which is right.
