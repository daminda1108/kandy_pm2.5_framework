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

    # Only the unambiguous contractions. An earlier version matched any word + 's, which
    # flags every possessive: "Kandy's valley" and "the model's output" are correct English in
    # a thesis and there are hundreds of them. The 's ending is only a contraction in the
    # closed set below; everywhere else it is genitive.
    (ERROR, "contraction",
     r"\b\w+n(?:'|’)t\b|\b\w+(?:'|’)(?:re|ve|ll|d|m)\b"
     r"|\b(?:it|that|there|here|what|who|let|he|she|nothing|everything)(?:'|’)s\b",
     "contraction. Expand it. Possessive 's is fine."),

    # "rather than" is contrastive, not hedging, and it is the natural way to write a
    # sentence that says what something is instead of what it is not. Excluded explicitly.
    (WARN, "hedge",
     r"\b(?:arguably|somewhat|quite|fairly|relatively)\s+\w+|\brather\s+(?!than\b)\w+",
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


# A block may be exempted, but only with a stated reason, so that an exemption is a decision
# somebody made and can be argued with rather than a silent hole. The only legitimate use so
# far is a table whose entire purpose is to list values this project has retired.
BLOCK_OFF = re.compile(r"<!--\s*lint:off\s+([^>]+?)\s*-->(.*?)<!--\s*lint:on\s*-->", re.S)


def blank_exempt_blocks(text: str) -> tuple[str, list[str]]:
    reasons = []

    def sub(m):
        reasons.append(m.group(1))
        return " " * len(m.group())

    return BLOCK_OFF.sub(sub, text), reasons


def cited_spans(raw: str) -> list[tuple[int, int]]:
    """Character ranges of sentences that carry a citation.

    THE RULE THIS ENCODES. A number that looks computed is either generated by this project, in
    which case it must be a {{claim:}} token, or it belongs to somebody else, in which case it
    must carry a citation. There is no third category. A literature value in claims.json would
    falsely imply this project computed it, so exempting cited sentences is not a loophole in
    the rule; it is the other half of the rule.
    """
    # Sentence boundaries are terminal punctuation followed by whitespace or end of text.
    # NOT a bare [.!?]: the decimal point in "0.82" would end a sentence, so the very numbers
    # this rule exists to check could never be seen as sharing a sentence with their citation.
    bounds = [0] + [m.end() for m in re.finditer(r"[.!?]+(?=\s|$)", raw)] + [len(raw)]
    spans = []
    for a, b in zip(bounds, bounds[1:]):
        seg = raw[a:b]
        # THREE categories of number, and every number must be in one of them:
        #   generated   a {{claim:}} token, recomputed from a scored file at build time
        #   literature  someone else's measurement, carrying [@citation]
        #   recorded    this project's own archived result, carrying [ledger F.nn]
        # The third exists because runs from earlier in the project cannot be regenerated:
        # the models are gone and the inputs have moved. Marking them as recorded rather than
        # recomputed is the honest description, and it tells a reader which is which.
        if "[@" in seg or re.search(r"\[ledger [A-Za-z0-9.,\s#]+\]", seg):
            spans.append((a, b))
    return spans


def lint(path: Path) -> list[tuple[str, int, str, str, str]]:
    raw = io.open(path, encoding="utf-8", errors="replace").read()
    cited = cited_spans(raw)
    raw, block_reasons = blank_exempt_blocks(raw)
    text = blank_exempt(raw)
    if block_reasons:
        print(f"  note: {len(block_reasons)} exempted block(s) in {path.name}: "
              + "; ".join(block_reasons))
    lines = text.splitlines()
    starts, pos = [], 0
    for ln in lines:
        starts.append(pos)
        pos += len(ln) + 1

    out = []
    for level, name, pat, msg in RULES:
        for m in re.finditer(pat, text, re.I if name != "first-person" else 0):
            i = m.start()
            # a computed-looking number inside a cited sentence is attributed, not ours
            if name == "untokenised-number" and any(a <= i < b for a, b in cited):
                continue
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
                # The console is cp1252 on this machine, so a fragment holding any glyph outside
                # that codepage crashed the linter mid-report: it could not describe the very
                # lines most likely to need describing. The report is best-effort; the CHECK is
                # not, and an unprintable fragment must never suppress the error it belongs to.
                try:
                    print(f"                        | {frag}")
                except UnicodeEncodeError:
                    enc = sys.stdout.encoding or "ascii"
                    print("                        | "
                          + frag.encode(enc, "replace").decode(enc, "replace"))
        if len(issues) > 40:
            print(f"  ... and {len(issues) - 40} more")

    print(f"\n{'=' * 60}\n{total_err} errors, {total_warn} warnings across {len(paths)} file(s)")
    if total_err:
        print("BLOCKED. The docx build will not run while errors stand.")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
