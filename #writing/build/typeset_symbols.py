"""One-time pass: set mathematical symbols as mathematics rather than as code.

The departmental format requires Times New Roman, and the style guide it cites sets variables in
italic. The pool wrote every symbol as inline code (`T(t)`, `b_k`), which renders in a
monospace face, and the two central equations as code blocks. This pass:

  - maps each symbol-like inline code span to italic Times with pandoc subscripts
    (variables and indices italic, descriptive labels such as "rep" and "min" roman);
  - turns the two equation code blocks into display mathematics;
  - removes the warning glyph, which rendered in a symbol font; every sentence it opened stands
    without it.

Genuine identifiers (a variable name in a data file, the token syntax) stay as code. Any code
span NOT in the mapping is reported and left alone, never guessed.

Writes with temp file + os.replace (gotcha #81).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SYMBOLS = {
    "B": "*B*",
    "B'": "*B*′",
    "B(t)": "*B*(*t*)",
    "F_min": "*F*~min~",
    "(1 - F_min)": "(1 − *F*~min~)",
    "H_k": "*H*~*k*~",
    "P": "*P*",
    "P' = (C − B') / (T − B')": "*P*′ = (*C* − *B*′) / (*T* − *B*′)",
    "P(x, y, t)": "*P*(*x*, *y*, *t*)",
    "T": "*T*",
    "T - B": "*T* − *B*",
    "T(t)": "*T*(*t*)",
    "T(t) - B(t)": "*T*(*t*) − *B*(*t*)",
    "b_k": "*b*~*k*~",
    "e(t)(P - 1)": "*e*(*t*)(*P* − 1)",
    "f": "*f*",
    "inc": "inc",
    "inc(t)": "inc(*t*)",
    "inc(t) = T(t) - B(t)": "inc(*t*) = *T*(*t*) − *B*(*t*)",
    "k": "*k*",
    "max(inc, 0) * P": "max(inc, 0) × *P*",
    "min(inc, 0)": "min(inc, 0)",
    "rho": "*ρ*",
    "s_rep": "*s*~rep~",
    "t": "*t*",
}
KEEP_AS_CODE = {"total_precipitation_sum", "{{claim:tag}}"}

EQUATIONS = {
    "PM(x, y, t) = B(t) + max(inc, 0) * P(x, y, t) + min(inc, 0) + e(t) * (P - 1)":
        r"$$\mathrm{PM}(x,y,t) = B(t) + \max(\mathrm{inc},0)\,P(x,y,t) + \min(\mathrm{inc},0)"
        r" + e(t)\,\bigl(P-1\bigr)$$",
    "y_k(t) = H_k[C](t) + b_k + e_k,      e_k ~ N(0, s_meas,k^2 + s_rep,k^2)":
        r"$$y_k(t) = H_k[C](t) + b_k + e_k, \qquad e_k \sim \mathcal{N}\!\left(0,\;"
        r" s_{\mathrm{meas},k}^2 + s_{\mathrm{rep},k}^2\right)$$",
}


def convert(text: str, where: str, unknown: list[str]) -> str:
    def block(m):
        body = m.group(1).strip()
        if body in EQUATIONS:
            return EQUATIONS[body]
        unknown.append(f"{where}: code block {body[:60]!r}")
        return m.group(0)

    text = re.sub(r"```\s*\n(.*?)\n```", block, text, flags=re.S)

    def inline(m):
        s = m.group(1)
        if s in SYMBOLS:
            return SYMBOLS[s]
        if s not in KEEP_AS_CODE:
            unknown.append(f"{where}: `{s}`")
        return m.group(0)

    text = re.sub(r"`([^`\n]+)`", inline, text)
    text = re.sub("⚠️?[ \t]*", "", text)
    return text


def main() -> int:
    unknown: list[str] = []
    changed = 0
    for p in sorted(list((ROOT / "pool").rglob("*.md")) + list((ROOT / "theses").rglob("*.md"))):
        s = p.read_text(encoding="utf-8")
        t = convert(s, str(p.relative_to(ROOT)), unknown)
        if t != s:
            tmp = p.with_suffix(".md.tmp")
            tmp.write_text(t, encoding="utf-8", newline="\n")
            os.replace(tmp, p)
            changed += 1
    print(f"files changed {changed}")
    for u in unknown:
        print(f"  NOT MAPPED  {u}")
    return 1 if unknown else 0


if __name__ == "__main__":
    sys.exit(main())
