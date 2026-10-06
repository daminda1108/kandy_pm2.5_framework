## Figures are consumers too {#s-figures-consumers-too}

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
