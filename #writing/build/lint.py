"""Style lint for the thesis.

WHY THIS IS A SCRIPT AND NOT A RESOLUTION. Every rule below is one I would otherwise break by
accident across thirty thousand words, because each violation looks fine in isolation and only
becomes a pattern in aggregate. A reader who has seen fifty machine-drafted documents recognises
the pattern faster than the author does.

The rules come from two places: the explicit instruction that the thesis contain no em dashes
and no machine-writing tells, and the ordinary requirements of a thesis, which is written in the
third person and does not editorialise.

Exit code is 1 if any error-level rule fires, so the build chain can refuse to produce a .docx
that violates them.

Usage: python lint.py [path ...]        default: thesis/chapters/*.md
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "thesis" / "chapters"

# ── rules ─────────────────────────────────────────────────────────────────────────────────
# (level, name, pattern, message). ERROR fails the build; WARN is reported and allowed.

ERROR = "ERROR"
WARN = "WARN"

RULES: list[tuple[str, str, str, str]] = [
    (ERROR, "em-dash", r"[—–]",
     "em or en dash. Use a comma, a colon, a full stop, or restructure the sentence."),

    # Vocabulary that marks machine drafting. Each of these is a real word; the objection is
    # that they cluster in generated prose and almost never in a thesis written by hand.
    (ERROR, "tell-vocab",
     r"\b(delve|delves|delving|tapestry|testament to|realm of|landscape of|"
     r"navigat\w+ the complexit\w+|underscore[sd]?|underscoring|"
     r"pivotal|crucial(?:ly)?|vital(?:ly)?|myriad|plethora|robustly|seamless\w*|"
     r"holistic\w*|multifaceted|paradigm shift|game.?chang\w+|"
     r"it is (?:worth|important) (?:noting|to note)|"
     r"in the (?:realm|world|context) of|"
     r"leverag\w+|harness\w+ the power)\b",
     "vocabulary that marks machine drafting."),

    # [ \t]* and not \s*: \s crosses the newline of a preceding blank line, so the match
    # starts one line early and the reported line number points at nothing.
    (ERROR, "tell-opener",
     r"(?m)^[ \t]*(?:Importantly|Notably|Crucially|Moreover|Furthermore|Additionally|"
     r"In conclusion|In summary|Overall|Ultimately)\s*,",
     "sentence opener that marks machine drafting. Start with the subject."),

    (ERROR, "first-person", r"\b(?:I|we|our|us|my)\b(?![\w'])",
     "first person. The thesis is written in the third person."),

    (ERROR, "contraction",
     r"\b\w+(?:'|’)(?:s|t|re|ve|ll|d|m)\b(?<!\bit's)",
     "contraction. Expand it, unless it is a possessive."),

    (WARN, "hedge",
     r"\b(?:arguably|somewhat|rather|quite|fairly|relatively)\s+\w+",
     "hedge. Either the claim is supported or it is not."),

    (WARN, "rule-of-three",
     r"\b\w+,\s+\w+,?\s+and\s+\w+\b(?=[\s,.;])",
     "possible decorative triple. Keep it only if all three earn their place."),

    (WARN, "long-sentence", r"(?<=[.!?])\s+[^.!?]{320,}[.!?]",
     "sentence over 320 characters. Consider splitting."),

    (ERROR, "untokenised-number",
     r"(?<![\w.$#\-])(?:0\.\d{2,}|\d{1,3}\.\d{1,2}\s*(?:%|per cent))(?![\w])",
     "a number that looks computed but is not a {{claim:}} token."),
]

# Text inside these is exempt: code, tokens, tables of literature values, and quoted material.
EXEMPT = [
    (re.compile(r"```.*?```", re.S), "code block"),
    (re.compile(r"`[^`]*`"), "inline code"),
    (re.compile(r"\{\{[^}]*\}\}"), "token"),
    (re.compile(r"(?m)^\s*>.*$"), "block quote"),
    (re.compile(r"(?m)^<!--.*?-->", re.S), "comment"),
    (re.compile(r"\[@[^\]]+\]"), "citation"),
]


def blank_exempt(text: str) -> str:
    """Replace exempt spans with spaces so offsets and line numbers are preserved."""
    for pat, _ in EXEMPT:
        text = pat.sub(lambda m: " " * len(m.group()), text)
    return text


def lint(path: Path) -> list[tuple[str, int, str, str, str]]:
    raw = io.open(path, encoding="utf-8", errors="replace").read()
    text = blank_exempt(raw)
    lines = text.splitlines()
    starts, pos = [], 0
    for ln in lines:
        starts.append(pos)
        pos += len(ln) + 1

    out = []
    for level, name, pat, msg in RULES:
        for m in re.finditer(pat, text, re.I if name != "first-person" else 0):
            i = m.start()
            lineno = max(1, sum(1 for s in starts if s <= i))
            frag = lines[lineno - 1].strip() if lineno - 1 < len(lines) else ""
            out.append((level, lineno, name, msg, frag[:90]))
    return sorted(out, key=lambda r: r[1])


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv[1:]] or sorted(CHAPTERS.glob("*.md"))
    if not paths:
        print(f"no chapters yet in {CHAPTERS.relative_to(ROOT)}")
        return 0

    total_err = total_warn = 0
    for p in paths:
        issues = lint(p)
        errs = [i for i in issues if i[0] == ERROR]
        warns = [i for i in issues if i[0] == WARN]
        total_err += len(errs)
        total_warn += len(warns)
        flag = "FAIL" if errs else ("warn" if warns else "ok")
        print(f"\n{p.name}  [{flag}]  {len(errs)} error, {len(warns)} warn")
        for level, ln, name, msg, frag in issues[:40]:
            print(f"  {level:<5} line {ln:>4}  {name:<18} {msg}")
            if frag:
                print(f"                        | {frag}")
        if len(issues) > 40:
            print(f"  ... and {len(issues) - 40} more")

    print(f"\n{'=' * 60}\n{total_err} errors, {total_warn} warnings across {len(paths)} file(s)")
    if total_err:
        print("BLOCKED. The docx build will not run while errors stand.")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
