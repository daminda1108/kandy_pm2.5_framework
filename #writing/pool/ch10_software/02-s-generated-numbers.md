## Generated numbers {#s-generated-numbers}

Every numeric claim in this thesis is a token that is resolved at build time. No number is typed
into the prose, and none is copied from an earlier draft. The reason is a failure this project made
more than once: a value is computed, written into text, then superseded when the analysis is
re-run, and the text keeps the old number while every other check stays green. {{ref:app-changed-during-writing-thesis}} lists
eleven quantities that moved this way.

The figure below traces the path a single number takes, from the scored file where it is computed,
through the generator that records its value with its provenance, into the token in the text, and
past the gate that compares the two. The branch that matters is the one on the right, where the
stored value and a fresh recomputation disagree and the build refuses to produce a document at all.
That branch is not hypothetical. It has fired, correctly, more than once.

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

Literature numbers belong to other people's measurements and carry a citation. They are
deliberately not claim tokens, because putting them in the generated set would falsely imply this
project computed them.

Recorded numbers are this project's own results from runs that can no longer be regenerated,
because the models are gone and the inputs have moved. They carry an explicit reference to the
project record. Marking them separately is the honest description and it tells a reader which is
which.

A style check enforces the partition: a number that looks computed, carries no token, and appears
in a sentence with neither a citation nor a record reference, blocks the build.
