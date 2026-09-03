# Reference audit — what is cited, and what is deliberately not

*Generated during the 2026-09 citation pass. Kept because an uncited entry in a bibliography is
either an oversight or a decision, and a reader cannot tell which without being told.*

⚠ **The standing rule this pass exists to enforce:** a previous version of this work cited a
paper that **does not exist**. Every key below was checked against `references.bib`, and no
citation was written for a claim without confirming the entry supports it.

## Deliberately uncited, with the reason

| key | why it is not cited |
|---|---|
| `Burnett2018`, `GBD2021Risk` | exposure–response and burden. The health block is **excised to the second paper**; citing them here would imply an analysis this paper does not contain. |
| `Raissi2019` | physics-informed neural networks. That workstream was **cut in 2026-05** and appears nowhere in the rewrite. |
| `Buchard2017`, `Provencal2017` | MERRA-2 evaluation. MERRA-2 was tested as a label and **rejected**; it is not a stream in any tier. |
| `Rao1994`, `Eskridge1997` | KZ-filter scale separation. The decomposition does not use a temporal filter. |
| `Huffman2020` | GPM IMERG precipitation. Rain enters the production model but plays no part in any claim in this paper. |
| `Mampitiya2023`, `Nandasena2010`, `Samaradiwakara2021`, `Dharmapriya2024` | Sri Lankan air-quality studies that do not bear on a specific claim made here. Retained in the bibliography for the second paper. |

## Where the remaining risk sits

- `Nirmani2025` and `Dhammapala2022` carry the **external checks in §6.2**, which are the only
  out-of-sample level evidence the paper has. Both were read directly; the values in the table
  were transcribed from their tables, not from secondary citation.
- `Wei2023` was added during this pass. §4.5 makes a substantive methodological claim about that
  product, and the claim rests on its stated training set (~9,500 stations including OpenAQ and
  CNEMC) — read from the paper's methods, not inferred.
- `Elangasinghe2008` carries §5 entirely. The 110 → 4 µg m⁻³ figures and the R² of 0.82 are that
  paper's, not ours, and are reported as literature values rather than claim tokens for exactly
  that reason.

## Still to do before submission

- Verify every page/volume field against the publisher record.
- `Priyankara2021` and `Senarathna2024` describe the **same 2019 KOALA record**; check that no
  passage treats them as independent corroboration. This error was made once before.
