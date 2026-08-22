# Novelty claim, figures, and loose ends — 2026-08-22

Companion to `rewrite_plan_2026-08-22.md` and `claims_audit_2026-08-22.md`.

---

## 1. The novelty claim

### 1.1 The proposed formulation, tested against the evidence

> *"Transferrable modular information-tiered ML and physics-infused grey-box decomposition model
> for PM2.5 estimation in data-sparse topographically complex global south cities"*

Five problems, three of them factual.

| | problem | evidence |
|---|---|---|
| 🔴 **"global south"** | **factually wrong about the validation frame.** The 47-city panel includes **Australia, France, Japan, Sweden, Slovakia, Malta and Singapore**. It is a *global* panel spanning income levels and four latitude bands — and that breadth is the point. Narrowing the title to "global south" both misdescribes the work and discards its generality. | `openaq_manifest.csv` country counts |
| 🔴 **"topographically complex"** | describes the **Kandy demonstration**, not the validation frame. The 47-city ladder spans terrain of every kind. It was true of the *old* 10-city panel (all valley/basin), which this paper supersedes. | panel census |
| 🔴 **"ML … infused"** | overstates the ML. The project's own measurements say `B`'s dilutive part and `P`'s shape are **unlearnable** (F.55–F.62), the dilution exponent is **0.054**, and the spatial pattern is *imposed* rather than learned. Leading with ML invites "where, exactly?" — and the honest answer is "in the temporal anchor, and not much else". | F.55–F.62 |
| 🟡 **nine stacked modifiers** | "transferrable modular information-tiered ML and physics-infused grey-box decomposition" is a queue of qualifiers. Reviewers read modifier-stacking as insecurity, and it buries the actual contribution. | — |
| 🟡 **"model for … estimation"** | positions the paper as *another model*. There are hundreds. The contribution is not the model. | — |

### 1.2 What is actually novel — four candidates, ranked

**① Bit-exact tier nesting (P3).** `Bud_i` reduces **byte-for-byte** to `Bud_{i-1}` when a data
stream is withheld. Multi-fidelity and data-fusion models normally degrade by *re-fitting*; this
one degrades *by construction*, and the property is asserted, tested and parameterised over every
adjacent tier pair. **I know of no urban PM2.5 model that makes or checks this claim.** It is
also the easiest thing in the paper for a referee to verify, which is worth a great deal.

**② The measured value of observation.** The marginal skill of each information increment,
across 47 cities, 32 countries, 4 latitude bands, 32,396 city-days, with gates registered before
running — and **three confounds caught by those gates** (country × latitude, driver completeness
× band, instrument class × band), each invisible in the pooled numbers. Value-of-information
analysis is old in hydrology and operations research; a *measured* VOI ladder for urban PM2.5
across a global panel is, as far as I can establish, new.

**③ The change-of-support limit on spatial skill.** Within-city contrast collapses monotonically
with averaging support — **85× → 4.0× → 3.0× → 1.23×** — measured from four independent campaigns
in one city. This says something about **every 1 km PM2.5 product ever scored against point
monitors**, not just ours. It may well be the most-cited result in the paper, and it is the one a
reader can take away and apply to their own work.

**④ The negative-result apparatus.** Five spatial nulls, five rejected background reformulations,
two refuted registered priors, one claim retracted when its own falsifier fired. Distinctive and
it builds trust — but it is *rigour*, not novelty, and it should not be sold as the contribution.

### 1.3 The claim I would defend

> **The information a city must supply before an urban PM2.5 field can be trusted is stated
> explicitly, guaranteed to nest exactly, and measured.**

Everything else — the decomposition, the physics, the ML — is machinery in service of that.
Framed this way the paper is not competing with the hundreds of existing PM2.5 models; it is
asking a question none of them answer, which is a far better place to be.

### 1.4 Title options

**A — contribution-first (recommended)**
> *Declared information budgets for urban PM2.5: exact tier nesting, the measured value of
> observation, and a change-of-support limit on spatial skill*

Leads with what is new, names all three contributions, no stacked modifiers. Long, but every
word is load-bearing. Fits GMD and ACP alike.

**B — question-first**
> *What does a PM2.5 field need to know? Measuring the value of observation across 47 cities*

More arresting and more readable; hides the nesting guarantee, which is the most verifiable
claim. Good if the target journal likes a hook.

**C — conservative**
> *An information-tiered grey-box decomposition for urban PM2.5 in data-scarce cities, with
> exact degradation between tiers and measured value of observation*

Closest to the project's existing internal phrasing and the safest with a traditional editor.
Least memorable.

**Recommendation: A**, with "data-scarce cities" added if the editor wants the application
signalled. Keep **"transferable"** out of the title — it is demonstrated in the body and reads as
a promise in a title.

⚠ **Do not** put "global south" or "topographically complex" in the title or abstract as
descriptions of the validation. Both belong in §6 as descriptions of the **demonstration city**.

---

## 2. Figures

### 2.1 How figures in strong journals are actually made

Almost never by hand, and almost never entirely in code either. The standard professional
workflow is **two-stage**:

1. **Data layers in code.** Python/matplotlib or R/ggplot2, exported as **vector PDF or SVG**.
   Everything quantitative is plotted programmatically so the figure regenerates from the data —
   which is also what GMD/ACP data-availability policies expect.
2. **Composition and annotation in a vector editor.** Illustrator or Inkscape for multi-panel
   assembly, panel letters, leader lines, callouts, and final typography.

Hand-drawing *data* is a serious integrity problem. Hand-*finishing* a figure is normal and
expected. What separates a strong figure from a default matplotlib plot is almost entirely
stage 2 plus deliberate choices in stage 1 — not the plotting library.

**Non-negotiables for submission:**

- **Vector throughout** (PDF/EPS/SVG); raster only for genuine imagery (satellite, DEM hillshade),
  and then at ≥300 dpi (maps ≥400).
- **Fonts embedded**, one family, sized so the *smallest* text is ≥6–7 pt **at final printed
  width**. The commonest referee complaint about figures is unreadable axis labels.
- **Colourblind-safe.** ~8% of male readers have a red–green deficiency. Check every categorical
  palette; never encode a result in red-vs-green alone.
- **Sized to the journal column** from the start (single ≈ 84 mm, double ≈ 174 mm typical). Never
  design at arbitrary size and scale down — that is what shrinks text below legibility.
- **One message per figure.** If you need two sentences to say what a panel shows, it is two
  panels or one fewer.
- **Direct labelling** beats a legend wherever the plot has room.

### 2.2 What this project already has, and should keep

The infrastructure is genuinely good and the conventions are locked: `pubfig.py` style,
`paperfig.py` helpers, SciencePlots + STIX, **YlOrRd** on a shared `PowerNorm(γ=1.3)` 10–40 scale
for PM, **inferno** reserved for pure emission surfaces, RdBu for signed fields, magma for UQ,
square heatmaps, opaque legends (framealpha 0.92), pins on F1 only, A4 sizing.

**Keep all of it.** ⚠ Two things to change for this paper: figures should be sized to the
**journal column**, not A4; and the palette set needs a **colourblind check**, which does not
appear to have been run.

### 2.3 The figures this paper needs

**🔴 Fig. 1 — the support-scaling ladder. The money figure, and it does not exist.**
Log-scaled contrast on the y-axis against averaging support on the x-axis, four points with
error/range bars, annotated with the measurement that produced each. Inset: the botanical garden
— two markers 300 m apart reading 110 and 4, with the 1 km pixel drawn around both. *A reader
should understand the paper's hardest result in five seconds.* This single figure carries §5.

**🔴 Fig. 2 — the budget ladder.** Step gain per tier, stratified by latitude band and by
instrument class. Must show the LCS/reference split, since "more in-city stations buy nothing" is
a reference-network result and stating it unconditionally would be wrong.

**🟡 Fig. 3 — the three confounds.** Pooled number beside the stratified number, for each of the
three. This is the paper's evidence that the registered gates did real work.

**🟡 Fig. 4 — the formulation schematic.** The decomposition, the observation operator, and the
budget tiers in one diagram. Hand-composed in vector; no data.

**🟢 Fig. 5–7 — Kandy demonstration.** Field, the four external records against the model, the
paired-site panel. Reuse existing code.

**Cut:** exposure weighting and burden figures, with the health block.

### 2.4 The visual abstract

Worth doing, and increasingly expected. One panel, readable at thumbnail size, no more than
~15 words of text. Suggested composition — a left-to-right narrative in three beats:

1. **the problem** — a city with two sensors and a question mark over the map
2. **the apparatus** — the budget ladder as literal rungs, `Bud0` → `Bud3`, with the measured
   gain written on each rung
3. **the limit** — the garden inset: 110 and 4, three hundred metres apart, inside one pixel

with a single bottom line: *"how much observation does a PM2.5 map need? we measured it."*

Build it in Inkscape or Illustrator over vector exports of Figs 1 and 2. ⚠ Check the target
journal's spec before building — Elsevier titles usually require a specific pixel size and
aspect; EGU journals allow but do not require one.

---

## 3. Loose ends register

Carried forward so nothing is silently dropped.

| | item | state |
|---|---|---|
| 🔴 **P4 identifiability** | **RUNNING** — `scripts/p4_identifiability.py`, Medellín first. Result determines whether P4 is a property or a withdrawn claim (F.74) |
| 🔴 **Webapp re-export + deploy** | QA-passed at 0.0014 µg/m³, **still not deployed**. Separate repo; bump `?v=`; verify with `git -C … rev-list --count origin/main..HEAD` (gotcha #77) |
| 🔴 **CEA letter** | the **only** route to a Kandy reference monitor now the Torrington Park BAM is defunct. Settles W11 and W6 together |
| 🟡 **`emix`** | `vehic = 0.85` refuted. Wire the burning sector (~0.5–0.6 / 0.3–0.4) or declare it a timing prior. **No skill gain expected — do not sell it as one** |
| 🟡 **NBRO URLs** | domain moved `nbro.gov.lk` → **`nbri.gov.lk`**; update notes and the drafted letter |
| 🟡 **Premasiri 5-site pixel test** | small; Overpass was down. Would add a fifth point to the support ladder |
| 🟡 **Colourblind check** | never run on the locked palette set |
| 🟢 **Elangasinghe Fig. 1 data** | 13 of 25 sites have no stated value. Authors are at Peradeniya — a cheap internal ask that would complete the transect |
| 🟢 **Seneviratne 2011** | the Colombo PMF companion, still unread; shows how the method behaves where factors sum to 100% |
| 🟢 **`stage_c_data_dictionary.md`** | still documents the v11 schema |
| 🟢 **Bootstrap CI on v3-extended R²** | still a single-run point estimate (0.581) |

---

## 4. Immediate order

1. **P4 finishes** → F.74 resolves either way; the property list in §2 depends on it.
2. **Novelty and title fixed** (§1.4) → determines abstract, and journal.
3. **Fig. 1 built** → it is the paper's spine and everything in §5 is written around it.
4. Then the phased rewrite in `rewrite_plan_2026-08-22.md`.
