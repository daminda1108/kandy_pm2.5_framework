# Reproducing this work {#app-reproducing-work}

The analysis code, the generating script for every numeric claim, the figure and table scripts,
and the pre-registration documents are held in a version-controlled repository.

The document is produced by four steps, each of which refuses to proceed if the one before it
failed:

1. regenerate every claim from the scored files, and compare against the stored values
2. generate the figures and tables
3. assemble the chapters, resolving claim, figure and table tokens and numbering by chapter
4. render to the output format against a reference document that carries the typography

Two limitations are stated rather than glossed.

The observational inputs are third-party and are not redistributed here. Their sources and
identifiers are given in {{ref:ch-available-data-deliberate-constraint}} so that they can be obtained, but one of them requires an
institutional agreement and none of them is instantaneous.

The earliest experiments described in {{ref:ch-eight-approaches-did-work}} are not reproducible from this repository. Their
model checkpoints and input frames have been superseded, and the honest position is that those
results are recorded rather than reproducible. They are marked as such wherever they appear.
