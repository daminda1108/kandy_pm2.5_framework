# Chapter 10. Software, reproducibility, and the machinery that catches errors

This chapter documents how the work is built and how it defends itself against a specific class
of failure. It is included because that machinery is among the more defensible things the project
produced, and because Chapter 5 records nine occasions on which a number in a document had gone
stale against the file it came from without anyone noticing.

## 10.1 The problem this machinery solves

An analysis of this kind produces a document and a set of artefacts, and they drift apart.

The drift is not carelessness. It happens because a number is computed once, written into prose,
and then the input changes: a field is rebuilt, a defect is corrected, a frame is widened. The
prose still reads correctly. Nothing errors. The only way to notice is to recompute every number
and compare, and nobody does that by hand for a document of this length.

Chapter 5 lists what that cost. A panel size that was stale by one city and eleven per cent of
its city-days. A statistic describing instrument classes that had never been recomputed after the
run it described was replaced. A quantity stated three different ways in a single document. And,
found during preparation of this thesis, a result recorded in the project's own ledger as twice
as strong as it actually was.

## 10.2 Generated numbers

Every numeric claim in this thesis is a token that is resolved at build time.

{{dia:claimsgate}}

The generating script recomputes each claim from the scored file it derives from and records,
alongside the value, the statistic used, the sample size, the source file and a reference to the
project's dated record. The document carries `{{claim:tag}}` and never a typed number. At build
time the stored claims are recomputed and compared, and **the build refuses to produce a document
if any value has drifted**. It has refused, correctly, more than once.

There are {{claim:frame.cities}} cities in the panel and rather more than that many claims: the
current set numbers in the low hundreds, and the count is reported by the build rather than
stated here, because a number describing the machinery would otherwise be exactly the kind of
number the machinery exists to protect.

Three categories of number appear in this document and the distinction is enforced rather than
observed.

**Generated** numbers carry a claim token and are recomputed at build time.

**Literature** numbers belong to other people's measurements and carry a citation. They are
deliberately not claim tokens, because putting them in the generated set would falsely imply this
project computed them.

**Recorded** numbers are this project's own results from runs that can no longer be regenerated,
because the models are gone and the inputs have moved. They carry an explicit reference to the
project record. Marking them separately is the honest description and it tells a reader which is
which.

A style check enforces the partition: a number that looks computed, carries no token, and appears
in a sentence with neither a citation nor a record reference, blocks the build.

## 10.3 Figures are consumers too

A figure is generated from data exactly as prose is, and it can go stale in exactly the same way.
This is not hypothetical. A figure suite in this project was regenerated at one point and drew a
retired background file, rendering a partition value the project had already refuted, while every
prose gate stayed green because nothing reads pixels out of an image.

Two rules follow and both are implemented. Figures are resolved from the directory their
generating script writes to, never from a copy in the document tree, so a regenerated figure
reaches the document without anyone remembering to copy it. And the build reports any figure
whose file predates the most recent rebuild of the field it draws.

A third check was added after it caught something: the build compares the set of figure labels it
has assigned against the set of images it has actually placed, because a figure referenced in the
prose but never placed leaves a reader hunting for something that is not there. It found three.

## 10.4 Pre-registration as a working practice

{{dia:prereg}}

Six pre-registrations were lodged during this work, each stating its predictions and the
condition under which each would be abandoned, before the corresponding analysis ran. The sixth
is prospective: it registers a measurement campaign that has not been deployed, and its
detection limits demoted that campaign's original headline hypothesis before any money was
committed.

{{tbl:T7_5}}

Fourteen of thirty predictions were refuted, several of them headline predictions of the person
who registered them. A registration that never refutes anything is not testing a prediction; it
is recording a hope.

The practice matters most in the branch that distinguishes an honest amendment from a rescued
hypothesis. A defect found in the machinery **before** scoring may be corrected, provided the
amendment is dated and reported, and this happened once when a sampling design was found to alias
latitude band with monitoring network. A criterion changed **after** the result is known is not a
criterion. The distinction is procedural rather than moral, and it is the reason the registrations
are timestamped by a third party rather than by the author.

## 10.5 Admissibility, asserted in code

Chapter 6 described the information budget. Its enforcement is in code rather than in discipline,
and it checks three things, each of which exists because the corresponding failure occurred.

A tier may not use a stream it is not entitled to. This was implemented first and is the obvious
direction.

A tier must use every stream it **is** entitled to. This was missing, and Chapter 5 records what
its absence cost: a tier silently using one of three admitted streams, inflating every gain
measured above it.

And every scored unit must carry every stream its tier admits, because a single city missing a
stream is invisible in a pooled median and shifts it.

A deliberate omission is permitted but must be declared at the call site, so that it appears in
the code rather than in someone's memory.

## 10.6 Reproducing this work

The analysis code, the generating scripts for every claim, and the pre-registrations are held in
a version-controlled repository. The document is built by a chain of four steps: regenerate the
claims, generate the figures and tables, assemble the chapters with tokens resolved, and render.
Each step refuses to proceed if the step before it failed, which is a deliberate choice: a chain
that continues past a failed stage produces a document that looks finished.

Two limitations on reproducibility are stated rather than glossed.

The observational inputs are third-party and are not redistributed here. Their sources and
identifiers are given so they can be obtained, but obtaining them is not instantaneous and one of
them requires an institutional agreement.

And the earliest experiments described in Chapter 5 are not reproducible from this repository.
Their model checkpoints and input frames have been superseded, and the honest position is that
those results are recorded rather than reproducible. They are marked as such wherever they
appear.

## 10.7 What this machinery does not do

It does not check that a number is meaningful, only that it is current. A claim can be
regenerated faithfully from a file and still be the wrong statistic, computed on the wrong
subset, answering a question nobody asked. Chapter 5 records several errors of exactly that kind
and none of them would have been caught by any gate described here. They were caught by
recomputing a quantity a second way and finding two answers.

It does not check figures for their content, only for their currency and their placement.

And it does not remove the need for a reader. The most serious errors in this project were found
by a person deciding to check something, and the machinery's contribution is that it makes the
checking cheap enough to do repeatedly rather than once.

# References

::: {#refs}
:::
