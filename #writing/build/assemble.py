"""Assemble one thesis from its composition file, resolving every token.

    python assemble.py --thesis a        reads theses/a/thesis.md, writes build/a/thesis.md

A thesis is a COMPOSITION FILE: headings, thesis-specific prose, and include lines that pull
labelled section fragments from pool/. Nothing in it carries a typed number. Everything numbered
is numbered here, from the order the composition gives, so the same fragment reads "Section 3.4"
in one thesis and "Section B.2" in the other without anyone editing it (plan:
kandy_pm25/docs/thesis_rescope_plan_2026-09-18.md).

Directives, each alone on a line:

    {{include:pool/ch06_the_model/01-s-decomposition-conserves.md}}
    {{include:... shift=1}}      demote every heading in the fragment by one level
    {{mainmatter}}               front matter ends; chapters number 1, 2, 3 from here
    {{appendices}}               chapters now number A, B, C
    {{toc}} {{listoffigures}} {{listoftables}}   Word fields, inserted by postprocess.py
    {{section:front}} {{section:body}}           page-numbering sections (roman, then Arabic)
    {{pagebreak}}

Tokens, anywhere in prose:

    {{claim:tag}}   a number from claims.json. The build FAILS if the stored claims disagree with
                    a fresh recomputation, or if the tag is missing.
    {{ref:label}}   "Chapter 3", "Section 3.2", "Appendix B" or "Section B.2", depending on what
                    the label is in THIS thesis. A label the thesis does not contain fails the
                    build: a reference into a section that was scoped out is a broken reference.
    {{fig:tag}} {{tbl:tag}} {{dia:tag}}   placed alone on a line, inline elsewhere; numbered by
                    chapter in order of first appearance, "Figure 3.2" or "Figure A.1".

Headings: level 1 is a chapter, 2 and 3 are numbered sections, 4 and below are unnumbered, which is
the departmental rule of at most three numbered levels. `{.front}` makes a front-matter heading
(DECLARATION, ABSTRACT, ...) that is set in the chapter-title style but kept out of the contents;
`{.unnumbered}` keeps a heading in the contents without a number (REFERENCES).

Out: build/<id>/thesis.md (input to pandoc; never edit it) and build/<id>/meta.json (captions for
the lists of figures and tables, the label map, the abstract word count, the source files).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import io
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from visuals import VISUALS  # noqa: E402

THESES = ROOT / "theses"
DIAGRAMS = ROOT / "thesis" / "diagrams"
TABLES = ROOT / "thesis" / "tables"
FIGURES = ROOT / "thesis" / "figures"

# Where a figure may live, in priority order. Resolved from the SOURCE directories, never from a
# copy, so a regenerated figure reaches the document without anyone remembering to copy it.
_ANALYSIS = Path("D:/ProjectCD/kandy_pm25/results/figures")
SEARCH = [DIAGRAMS, FIGURES, _ANALYSIS / "paper2026", _ANALYSIS / "paper_figures_v2",
          _ANALYSIS / "kandy_decomp"]

REPO = Path(r"D:\ProjectCD\kandy_pm25")
CLAIMS = REPO / "data" / "processed" / "modular" / "claims.json"
BUILD_CLAIMS = REPO / "scripts" / "build_claims.py"
VENV_PY = REPO / ".venv" / "Scripts" / "python.exe"

ABSTRACT_MAX_WORDS = 350          # departmental limit, single page

CLAIM_TOKEN = re.compile(r"\{\{claim:([A-Za-z0-9_.]+)\}\}")
VIS_TOKEN = re.compile(r"\{\{(fig|tbl|dia):([A-Za-z0-9_]+)\}\}")
REF_TOKEN = re.compile(r"\{\{ref:([A-Za-z0-9_\-]+)\}\}")
THIS_TOKEN = re.compile(r"\{\{([Tt])his:([A-Za-z0-9_\-]+)\}\}")
INCLUDE = re.compile(r"^\{\{include:([^}\s]+)(?:\s+shift=(-?\d+))?\}\}\s*$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*(\{[^{}]*\})?\s*$")
DRAFTING = re.compile(r"(?ms)^## Drafting notes.*?(?=^#{1,2} |\Z)")
FENCE = re.compile(r"^\s*```")

MARKER_WORDS = {"toc": "TOC", "listoffigures": "LOF", "listoftables": "LOT",
                "section:front": "SECTION-FRONT", "section:body": "SECTION-BODY"}


class AssemblyError(Exception):
    pass


# ── 1. composition ────────────────────────────────────────────────────────────────────────

def expand(path: Path, shift: int, stack: list[Path], sources: list[Path]) -> list[str]:
    """Expand include lines recursively, shifting heading levels on the way in."""
    if path in stack:
        raise AssemblyError(f"include cycle: {' -> '.join(p.name for p in stack + [path])}")
    if not path.exists():
        raise AssemblyError(f"include not found: {path.relative_to(ROOT)}")
    sources.append(path)
    text = io.open(path, encoding="utf-8").read().replace("\r\n", "\n")
    text = DRAFTING.sub("", text)                      # drafting notes never reach the output
    out: list[str] = []
    fenced = False
    for ln in text.split("\n"):
        if FENCE.match(ln):
            fenced = not fenced
        m = INCLUDE.match(ln.strip()) if not fenced else None
        if m:
            out.extend(expand(ROOT / m.group(1), shift + int(m.group(2) or 0),
                              stack + [path], sources))
            out.append("")
            continue
        h = HEADING.match(ln) if not fenced else None
        if h and shift:
            level = len(h.group(1)) + shift
            if not 1 <= level <= 6:
                raise AssemblyError(f"shift puts a heading at level {level}: {ln!r}")
            ln = "#" * level + ln[len(h.group(1)):]
        out.append(ln)
    return out


def sources_of(thesis: str) -> list[Path]:
    """Every file a thesis is built from, in order. build_docx lints exactly these."""
    sources: list[Path] = []
    expand(THESES / thesis / "thesis.md", 0, [], sources)
    return sources


# ── 2. numbering ──────────────────────────────────────────────────────────────────────────

def _attrs(raw: str | None) -> tuple[str | None, set[str]]:
    if not raw:
        return None, set()
    ident = re.search(r"#([A-Za-z0-9_\-]+)", raw)
    return (ident.group(1) if ident else None), set(re.findall(r"\.([A-Za-z0-9_\-]+)", raw))


def _upper(title: str) -> str:
    """Upper-case a title without touching tokens or inline code inside it."""
    return re.sub(r"(\{\{[^}]*\}\}|`[^`]*`)|([^{`]+)",
                  lambda m: m.group(1) or m.group(2).upper(), title)


def number(lines: list[str]) -> tuple[list[str], dict, list[dict]]:
    """Number chapters and sections; return the rewritten lines, the label map, the outline.

    Chapters in the main matter take 1, 2, 3; after {{appendices}} they take A, B, C. Levels 2
    and 3 are numbered under their chapter, level 4 and below are not, which is the rule of at
    most three numbered levels applied by construction rather than by checking.
    """
    phase = "front"
    ch_idx = app_idx = 0
    chap: str | None = None
    n2 = n3 = 0
    labels: dict[str, dict] = {}
    outline: list[dict] = []
    out: list[str] = []
    last_numbered = None
    fenced = False

    def register(ident, kind, num, title):
        if ident is None:
            return
        if ident in labels:
            raise AssemblyError(f"label used twice: {ident}")
        labels[ident] = {"kind": kind, "num": num, "title": title}

    for ln in lines:
        s = ln.strip()
        if FENCE.match(ln):
            fenced = not fenced
        if not fenced and s == "{{mainmatter}}":
            phase = "main"
            continue
        if not fenced and s == "{{appendices}}":
            phase = "app"
            continue
        h = HEADING.match(ln) if not fenced else None
        if not h:
            out.append(ln)
            continue

        level, title = len(h.group(1)), h.group(2).strip()
        ident, classes = _attrs(h.group(3))
        idattr = f" {{#{ident}}}" if ident else ""

        if "front" in classes or (phase == "front" and level == 1):
            register(ident, "front", None, title)
            out += ["", '::: {custom-style="Front Heading"}', _upper(title), ":::", ""]
            continue
        if "unnumbered" in classes:
            register(ident, "unnumbered", None, title)
            shown = _upper(title) if level == 1 else title
            out.append(f"{'#' * level} {shown} {{#{ident or ''} .unnumbered}}".replace("{# ", "{"))
            outline.append({"level": level, "num": None, "title": shown})
            continue
        if phase == "front":
            raise AssemblyError(f"numbered heading before {{{{mainmatter}}}}: {ln!r}")

        if level == 1:
            if phase == "main":
                ch_idx += 1
                chap = str(ch_idx)
                shown, kind = f"{chap}. {_upper(title)}", "chapter"
            else:
                chap = "ABCDEFGHIJKLMNOP"[app_idx]
                app_idx += 1
                shown, kind = f"APPENDIX {chap}: {_upper(title)}", "appendix"
            n2 = n3 = 0
            register(ident, kind, chap, title)
            last_numbered = chap
            out.append(f"# {shown}{idattr}")
            outline.append({"level": 1, "num": chap, "title": shown, "kind": kind})
            continue
        if chap is None:
            raise AssemblyError(f"section heading before any chapter: {ln!r}")
        if level == 2:
            n2, n3 = n2 + 1, 0
            num = f"{chap}.{n2}"
        elif level == 3:
            if n2 == 0:
                raise AssemblyError(f"level-3 heading directly under a chapter: {ln!r}")
            n3 += 1
            num = f"{chap}.{n2}.{n3}"
        else:
            # beyond three levels: no number, and a reference to it points at its parent
            register(ident, "section", last_numbered, title)
            out.append(f"{'#' * level} {title}{idattr}")
            continue
        register(ident, "section", num, title)
        last_numbered = num
        out.append(f"{'#' * level} {num} {title}{idattr}")
        outline.append({"level": level, "num": num, "title": title})
    return out, labels, outline


def resolve_refs(text: str, labels: dict) -> tuple[str, list[str]]:
    missing: list[str] = []

    def sub(m):
        lab = labels.get(m.group(1))
        if lab is None or lab["kind"] in ("front", "unnumbered") or lab["num"] is None:
            missing.append(f"ref:{m.group(1)}")
            return m.group(0)
        if lab["kind"] == "chapter":
            return f"Chapter {lab['num']}"
        if lab["kind"] == "appendix":
            return f"Appendix {lab['num']}"
        return f"Section {lab['num']}"

    def this(m):
        # "this chapter" inside a fragment means the unit the fragment came from, which is a
        # chapter in one thesis and a section or an appendix in the other.
        lab = labels.get(m.group(2))
        if lab is None:
            missing.append(f"this:{m.group(2)}")
            return m.group(0)
        noun = {"chapter": "chapter", "appendix": "appendix"}.get(lab["kind"], "section")
        return f"{'T' if m.group(1) == 'T' else 't'}his {noun}"

    def both(t):
        return THIS_TOKEN.sub(this, REF_TOKEN.sub(sub, t))

    return _outside_code(text, both), missing


def _outside_code(text: str, fn) -> str:
    """Apply fn to text outside inline code. Chapter 10 shows token syntax in order to explain
    it, and that must not be resolved or reported as a leftover."""
    shields: list[str] = []

    def hide(m):
        shields.append(m.group(0))
        return f"\x00SHIELD{len(shields) - 1}\x00"

    t = fn(re.sub(r"`[^`]*`", hide, text))
    for i, original in enumerate(shields):
        t = t.replace(f"\x00SHIELD{i}\x00", original)
    return t


# ── 3. claims ─────────────────────────────────────────────────────────────────────────────

def claims_fresh() -> bool:
    """Recompute the claims and refuse to build on drift. Same gate as the manuscript."""
    if not CLAIMS.exists():
        print("claims.json missing")
        return False
    r = subprocess.run([str(VENV_PY), str(BUILD_CLAIMS), "--check"],
                       cwd=str(REPO), capture_output=True, text=True)
    if r.returncode != 0:
        print("CLAIMS GATE FAILED. The stored claims disagree with a fresh recomputation:")
        print((r.stdout + r.stderr)[-1500:])
        return False
    return True


def load_claims() -> dict:
    return json.load(io.open(CLAIMS, encoding="utf-8"))["claims"]


def resolve_claims(text: str, claims: dict) -> tuple[str, list[str]]:
    missing: list[str] = []

    def sub(m):
        tag = m.group(1)
        if tag not in claims:
            missing.append(f"claim:{tag}")
            return m.group(0)
        return str(claims[tag]["value"])

    return _outside_code(text, lambda t: CLAIM_TOKEN.sub(sub, t)), missing


# ── 4. figures and tables ─────────────────────────────────────────────────────────────────

CHAPTER_LINE = re.compile(r"^#\s+(?:(\d+)\.\s|APPENDIX\s+([A-Z]):)")


def _short(caption: str) -> str:
    """First sentence of a caption, for the lists of figures and tables."""
    first = re.split(r"(?<=[a-z0-9)\]])\.\s", caption.strip(), maxsplit=1)[0].rstrip(".")
    return first if len(first) <= 110 else first[:107].rsplit(" ", 1)[0] + "..."


def resolve_visuals(text: str):
    """Number figures, tables and diagrams by chapter, in order of first appearance.

    Numbers are never written in the source. A visual placed twice prints twice under one
    number, which happened four times before this check existed (gotcha #94): place once and
    refer inline elsewhere.
    """
    counters: dict[tuple[str, str], int] = {}
    assigned: dict[str, str] = {}
    sources: dict[str, Path] = {}
    placed_keys: set[str] = set()
    captions: list[dict] = []
    missing: list[str] = []
    chapter = "0"
    seq = {"fig": "fig", "dia": "fig", "tbl": "tbl"}

    def label_for(kind: str, tag: str) -> str:
        key = f"{seq[kind]}:{tag}"
        if key not in assigned:
            ck = (seq[kind], chapter)
            counters[ck] = counters.get(ck, 0) + 1
            word = "Table" if kind == "tbl" else "Figure"
            assigned[key] = f"{word} {chapter}.{counters[ck]}"
        return assigned[key]

    # Pass 1: number every visual where it is PLACED, not where it is first mentioned. A body
    # chapter may mention a figure that is printed in an appendix; numbering at first mention
    # would give it a Chapter 3 number on an Appendix A page.
    for line in text.splitlines():
        m = CHAPTER_LINE.match(line)
        if m:
            chapter = m.group(1) or m.group(2)
        placed = VIS_TOKEN.fullmatch(line.strip())
        if placed:
            label_for(placed.group(1), placed.group(2))
    chapter = "0"

    out_lines: list[str] = []
    for line in text.splitlines():
        m = CHAPTER_LINE.match(line)
        if m:
            chapter = m.group(1) or m.group(2)
        placed = VIS_TOKEN.fullmatch(line.strip())
        if placed:
            pk = f"{seq[placed.group(1)]}:{placed.group(2)}"
            if pk in placed_keys:
                missing.append(f"duplicate placement of {placed.group(1)}:{placed.group(2)} "
                               f"(place it once and refer to it inline elsewhere)")
                continue

        if placed and placed.group(1) == "tbl":
            tag = placed.group(2)
            lab = label_for("tbl", tag)
            frag = TABLES / f"{tag}.md"
            if not frag.exists():
                cand = sorted(TABLES.glob(f"{tag}*.md"))
                frag = cand[0] if cand else frag
            if not frag.exists():
                missing.append(f"tbl:{tag}")
                out_lines.append(lab)
                continue
            body = io.open(frag, encoding="utf-8").read().strip().splitlines()
            title = ""
            if body and body[0].startswith("Table:"):
                title = body[0][len("Table:"):].strip()
                body[0] = f"Table: {lab}. {title}"
            placed_keys.add(pk)
            captions.append({"kind": "tbl", "label": lab, "short": _short(title)})
            out_lines += [""] + body + [""]
            continue

        if placed and placed.group(1) in ("fig", "dia"):
            kind, tag = placed.group(1), placed.group(2)
            lab = label_for(kind, tag)
            if tag not in VISUALS:
                missing.append(f"{kind}:{tag}")
                out_lines.append(lab)
                continue
            stem, caption = VISUALS[tag]
            cands = [f for f in (d / f"{stem}.png" for d in SEARCH) if f.exists()]
            if not cands:
                missing.append(f"file for {kind}:{tag} ({stem}.png)")
                out_lines.append(lab)
                continue
            best = max(cands, key=lambda f: f.stat().st_mtime)
            sources[tag] = best
            placed_keys.add(pk)
            captions.append({"kind": "fig", "label": lab, "short": _short(caption)})
            out_lines.append(f"![{lab}. {caption}]({best.as_posix()})")
            out_lines.append("")
            continue

        out_lines.append(VIS_TOKEN.sub(lambda mm: label_for(mm.group(1), mm.group(2)), line))
    return "\n".join(out_lines), assigned, captions, missing, sources


# ── 5. markers and front matter ───────────────────────────────────────────────────────────

def markers(text: str) -> str:
    """Directives postprocess.py acts on, as paragraphs it can find in the .docx."""
    for word, tag in MARKER_WORDS.items():
        text = re.sub(rf"(?m)^\{{\{{{re.escape(word)}\}}\}}\s*$",
                      f'\n::: {{custom-style="Marker"}}\n[[{tag}]]\n:::\n', text)
    return re.sub(r"(?m)^\{\{pagebreak\}\}\s*$",
                  '\n```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n', text)


def abstract_words(text: str) -> int | None:
    m = re.search(r'::: \{custom-style="Abstract Text"\}\n(.*?)\n:::', text, re.S)
    if not m:
        return None
    return len(re.sub(r"[^\w\s.\-]", " ", m.group(1)).split())


# ── main ──────────────────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--thesis", required=True, help="a or b: theses/<id>/thesis.md")
    a = ap.parse_args()
    comp = THESES / a.thesis / "thesis.md"
    outdir = HERE / a.thesis
    outdir.mkdir(exist_ok=True)

    print(f"assembling thesis {a.thesis}")
    if not claims_fresh():
        return 1
    claims = load_claims()
    print(f"  claims.json fresh, {len(claims)} claims")

    try:
        srcs: list[Path] = []
        lines = expand(comp, 0, [], srcs)
        lines, labels, outline = number(lines)
    except AssemblyError as e:
        print(f"\nASSEMBLY FAILED: {e}")
        return 1
    text = "\n".join(lines)

    problems: list[str] = []
    # Captions live in visuals.py, which the prose lint never sees. Four typed references
    # survived there after the chapters were tokenised, so the same two rules run here.
    for tag, (_, cap) in VISUALS.items():
        bare = re.sub(r"\{\{[^}]*\}\}", " ", cap)
        if re.search(r"\b(?:Chapter|Section|Appendix)[ \t]+(?:\d+(?:\.\d+)*|[A-H])\b", bare) \
                or re.search(r"\b[Tt]his[ \t]+(?:chapter|appendix)\b", bare):
            problems.append(f"caption {tag}: typed section reference; use {{{{ref:label}}}}")
    # ORDER MATTERS. Visuals first: a table fragment carries its own {{claim:}} tokens, and
    # figure captions may too, so claims resolve after insertion.
    text, assigned, captions, vis_missing, fig_sources = resolve_visuals(text)
    problems += vis_missing
    text, missing = resolve_refs(text, labels)
    problems += missing
    text, missing = resolve_claims(text, claims)
    problems += missing
    for c in captions:
        c["short"], _ = resolve_claims(c["short"], claims)
    text = markers(text)

    leftover = re.findall(r"\{\{[^}]+\}\}", re.sub(r"`[^`]*`", " ", text))
    n_abs = abstract_words(text)
    if n_abs is not None and n_abs > ABSTRACT_MAX_WORDS:
        problems.append(f"abstract is {n_abs} words; the limit is {ABSTRACT_MAX_WORDS}")

    if problems or leftover:
        print("\nNOT WRITING OUTPUT.")
        for t in sorted(set(problems)):
            print(f"  {t}")
        for t in sorted(set(leftover))[:30]:
            print(f"  unresolved: {t}")
        return 1

    out = outdir / "thesis.md"
    out.write_text(text, encoding="utf-8")
    meta = {
        "thesis": a.thesis,
        "built": _dt.datetime.now().isoformat(timespec="seconds"),
        "abstract_words": n_abs,
        "captions": captions,
        "outline": outline,
        "labels": labels,
        "sources": [str(p.relative_to(ROOT)) for p in srcs],
    }
    (outdir / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")

    words = len(re.sub(r"[^\w\s]", " ", text).split())
    figs = sum(1 for c in captions if c["kind"] == "fig")
    tbls = sum(1 for c in captions if c["kind"] == "tbl")
    chapters = [o for o in outline if o["level"] == 1 and o.get("kind") == "chapter"]
    apps = [o for o in outline if o["level"] == 1 and o.get("kind") == "appendix"]
    print(f"  sources  {len(srcs)} files")
    print(f"  chapters {len(chapters)}   appendices {len(apps)}")
    print(f"  words    {words:,}")
    print(f"  figures  {figs}   tables {tbls}")
    if n_abs is not None:
        print(f"  abstract {n_abs} words (limit {ABSTRACT_MAX_WORDS})")
    else:
        print("  WARNING: no Abstract Text block found")

    placed_tags = set(fig_sources)
    labelled = {k.split(":", 1)[1] for k in assigned if k.startswith("fig:")}
    for t in sorted(labelled - placed_tags):
        print(f"  WARNING: {assigned.get('fig:' + t)} ({t}) is referenced but never placed")
    stale = [(t, p) for t, p in fig_sources.items()
             if _dt.date.fromtimestamp(p.stat().st_mtime) < _dt.date(2026, 8, 18)]
    for t, p in sorted(stale):
        print(f"  WARNING: {t} is older than the 2026-08-18 field rebuild ({p.name})")
    print(f"  wrote    {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
