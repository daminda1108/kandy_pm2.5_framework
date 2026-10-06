# Paper-writing workflow (both papers)

Established 2026-09-23, in response to the user being unsatisfied with earlier paper-writing
attempts (the old `docs/paper/` drafts and `#writing/` thesis pool). This is a clean restart in
`D:\ProjectCD\papers\` — not a rebuild of the old files. Facts, numbers and verified claims are
pulled FROM the ledger/thesis pool; prose is written fresh against the house style below.

## Directory layout

```
papers/
  WORKFLOW.md          <- this file
  paper1_information_budget/
    WRITING_LOG.md      <- dated session log, writing-specific (separate from SESLOG.md)
    manuscript/
      00_title_abstract.md
      01_introduction.md
      02_methods.md
      03_results.md
      04_discussion.md
      05_conclusions.md
    figures/
      FIGURE_PLAN.md    <- one spec per figure: data source, script, caption draft, status
    references/
      references.bib    <- seeded from kandy_pm25/docs/paper/references.bib, extend freely
  paper2_kandy_field/
    (same skeleton, lighter — built once Paper 1 is drafted)
```

Each manuscript file is self-contained and independently editable — no build step required to
read or edit a section. A compose/assemble script can be added later if we need single-document
output for submission; until then, edit files directly.

## House style (user-directed, 2026-09-23)

1. **Explain every figure in depth before it appears.** At least one full paragraph of body
   text must motivate and explain a figure — what the reader is about to see, why it's here,
   what to look for — before the figure reference. Never drop a bare "(see Figure 3)" with no
   lead-in.
2. **Every figure must be standalone-understandable.** A reader who flips straight to the
   figures (most reviewers do this first) must be able to understand axes, data source, method,
   and the headline finding from the caption ALONE, without reading the body text. Captions are
   therefore long — a paragraph, not a single-line label — and repeat enough context (sample
   size, city panel, what "gain" means) to stand alone.
3. **Err toward more references, not fewer.** Every non-obvious quantitative claim, every
   comparison to prior work, and every methodological choice that has a precedent in the
   literature gets a citation. Prefer over-citing established facts to under-citing.
4. **Write immersively.** Motivate before presenting; use concrete numbers and scenarios rather
   than abstract claims; connect sections and paragraphs with transitions, not isolated
   bullet-headers. This does not relax the formal-register rule from the thesis
   ([[feedback-thesis-formal-register]]) — immersive and rigorous are not in tension; avoid
   anecdote and rhetorical flourish, but do not write in the terse, list-heavy voice of a status
   report either.
5. **Apply the Gopen & Swan / Whitesides / hourglass rules** already established in this
   project's writing-craft playbook (`kandy_pm25/docs/paper/publication_strategy_2026-09-23.md`
   §7): subject-verb adjacency, one point per sentence, new information at sentence-end,
   introduction narrows to the gap, discussion widens back to the same scope it opened with.
6. **It is fine to leave a section incomplete or change it later.** Draft in whatever order is
   useful; mark incomplete sections `[STATUS: STUB]` or `[STATUS: DRAFT — needs X]` at the top
   of the file rather than leaving silent gaps. Do not let incompleteness block moving to
   another section.
7. **Every number in the manuscript must trace to a verified source.** While drafting, cite the
   internal F-code (e.g. `[F.97]`) or ledger location inline as a bracketed marker — this is NOT
   a final citation, it's a traceability breadcrumb. Before submission, every `[F.xx]` marker
   must be resolved to either (a) a proper external citation, (b) a supplementary-material
   pointer, or (c) removed if the claim doesn't survive into the final text. `grep -rn '\[F\.'
   manuscript/` should return zero hits at submission time.
8. **New figures get planned before they get built.** Add the spec to `FIGURE_PLAN.md` first
   (purpose, data source script, draft caption, status), then build. Don't build a figure that
   isn't in the plan; don't leave a planned figure unbuilt without a status note explaining why.

## De-AI-ifying the prose (added 2026-09-23)

The first full draft of the Introduction read as AI-generated on inspection — 47 em dashes
across two short sections, plus the usual cluster of tells that come with them. Fixing the
punctuation alone doesn't fix the underlying rhythm, so every section gets a full rewrite pass
against this checklist before it's considered done, not a find-and-replace:

1. **No em dashes.** Rewrite the sentence instead of substituting a comma or colon for the dash
   — that just relocates the tell. An em-dash-linked clause is almost always better as two
   sentences, a relative clause, or a parenthetical in actual parentheses.
2. **Cut connective-tissue filler**: "moreover," "furthermore," "it is worth noting that,"
   "importantly," "notably," "crucially," "fundamentally" used as bare intensifiers rather than
   because the word is load-bearing. If deleting the word changes nothing, delete it.
3. **Break up the "not X, but Y" and rule-of-three reflexes.** One well-placed contrast structure
   per section is fine; four in a row reads like a template. Vary sentence shape — some short,
   some long, not a metronome of identically-built compound sentences.
4. **No throat-clearing openers or closers.** Don't announce what a paragraph is about to do
   ("In this section, we will discuss...") or summarize what it just did ("In summary, we have
   shown that..."). Start with the actual content; end when the point is made.
5. **Prefer verbs to nominalizations.** "We used X to estimate Y," not "the utilization of X
   enabled the estimation of Y."
6. **Ground abstractions in a concrete number or example before generalizing from it**, the way
   a good science writer (Zimmer, Yong, the better parts of the Whitesides tradition) does —
   state the specific finding, then say what it means, not the reverse.
7. **Read it aloud (mentally) after drafting.** If a sentence only parses on a second read, or if
   the same rhetorical shape repeats three paragraphs running, rewrite it. This is the Gopen &
   Swan test (rule 5 above) applied specifically to catch machine-generated cadence.

Run `grep -c "—" <file>` on any drafted section before calling it done — nonzero is a signal to
do another pass, not just a strip-and-replace.

## Session workflow

At the start of a writing session: read `WRITING_LOG.md`'s most recent entries and the
manuscript files' `[STATUS: ...]` markers before drafting new material — don't re-derive what a
previous session already decided.

During a session: draft or revise sections, update figure specs, pull verified numbers from
`kandy_pm25/docs/model_reference/F_epistemic_ledger.md` / `CONTEXT.md` (never invent a number;
if a needed number doesn't exist yet, flag it in the log rather than approximating).

At the end of a session (or a natural stopping point): append an entry to `WRITING_LOG.md` —
what was drafted/changed, what's still open, what the next session should do first. This is
distinct from `SESLOG.md` (project-wide) and `kaggle_kernel_log.md` (Kaggle-specific) — this log
is ONLY for the writing process itself.

## Division of labor with the parallel spatial-curve work

The E8/E9 TabPFN spatial-learning-curve debugging is being handled in a separate session
("Workflow optimization tools"). Paper 1's Results section does not need that arm to finish —
it's scoped to the already-complete classical/tournament nulls (learned-pattern, LUR,
AlphaEarth, deliberate-siting, model-family tournament) per
`docs/paper/publication_strategy_2026-09-23.md` §2. If the spatial-curve arm finishes before
Paper 1's Discussion is drafted, it can be added as a forward-looking mention; it is not a
blocker for drafting to proceed now.
