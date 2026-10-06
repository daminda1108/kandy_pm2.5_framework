## Reproducing this work {#s-reproducing-work}

The analysis code, the generating scripts for every claim, and the pre-registrations are held in
a version-controlled repository. The document is built by a chain of four steps: regenerate the
claims, generate the figures and tables, assemble the chapters with tokens resolved, and render.
Each step refuses to proceed if the step before it failed, which is a deliberate choice: a chain
that continues past a failed stage produces a document that looks finished.

Two limitations on reproducibility are stated rather than glossed.

The observational inputs are third-party and are not redistributed here. Their sources and
identifiers are given so they can be obtained, but obtaining them is not instantaneous and one of
them requires an institutional agreement.

And the earliest experiments described in {{ref:ch-eight-approaches-did-work}} are not reproducible from this repository.
Their model checkpoints and input frames have been superseded, and the honest position is that
those results are recorded rather than reproducible. They are marked as such wherever they
appear.

The accurate summary of the whole is therefore that this work is **auditable, and reproducible
conditional on obtaining the source datasets**, which is not the same as self-contained. Every
step from those inputs to every number in this document can be re-run and checked by a reader who
holds them; the inputs themselves are third-party observations this project is not free to
redistribute, and one of them requires an institutional agreement to obtain at all. Claiming
self-contained reproducibility would be claiming something the data licences do not allow, and the
distinction is worth naming rather than leaving a reader to discover it.
