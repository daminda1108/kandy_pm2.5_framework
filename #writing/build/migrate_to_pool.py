"""One-time migration: split thesis/chapters/*.md into labelled section fragments in pool/.

WHY. Two theses are built from one body of work (plan: kandy_pm25/docs/thesis_rescope_plan_
2026-09-18.md). A section that appears in both must exist once, and a cross-reference inside it
cannot carry a typed number, because the same section is "Section 3.4" in one thesis and
"Section B.2" in the other. So:

  1. every heading loses its typed number and gains a stable label, {#label};
  2. every typed "Chapter N" / "Section N.N" / "Appendix X" in prose becomes {{ref:label}},
     which assemble.py renders against the manifest of the thesis being built;
  3. each H2 section (with its H3 children) becomes one file, so a thesis composes sections
     rather than copying them.

Any reference that cannot be mapped is REPORTED, never guessed. The old-number -> label map is
written to pool/labels.json as the record of what each label used to be called.

Front matter (ch00) is split by H2 into pool/front/ for reuse; each thesis writes its own title
page and abstract.

Usage: python migrate_to_pool.py [--dry-run]
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "thesis" / "chapters"
POOL = ROOT / "pool"

STOP = {"a", "an", "the", "of", "and", "or", "to", "in", "on", "for", "with", "at", "by", "is",
        "are", "it", "its", "what", "which", "that", "this", "does", "not", "from", "as", "be",
        "one", "how", "why", "where", "when", "there", "was", "were"}

H1 = re.compile(r"^#\s+(?:Chapter\s+(\d+)\.\s*|Appendix\s+([A-Z])\.\s*)(.+?)\s*$")
H2 = re.compile(r"^##\s+(?:(\d+\.\d+)\s+)?(.+?)\s*$")
H3 = re.compile(r"^###\s+(?:(\d+\.\d+\.\d+)\s+)?(.+?)\s*$")
REF = re.compile(r"\b(Chapter|Section|Appendix)\s+(\d+(?:\.\d+)*|[A-H])\b")


def slug(title: str, used: set[str], prefix: str) -> str:
    words = [w for w in re.sub(r"[^a-z0-9 ]", " ", title.lower()).split() if w not in STOP]
    base = prefix + "-".join(words[:4] or ["section"])
    s, n = base, 2
    while s in used:
        s, n = f"{base}-{n}", n + 1
    used.add(s)
    return s


def write_atomic(p: Path, text: str) -> None:
    """Temp file + os.replace (gotcha #81): a failed write must never leave a truncated file."""
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, p)


def main() -> int:
    dry = "--dry-run" in sys.argv
    used: set[str] = set()
    number_to_label: dict[str, str] = {}
    # (chapter_dir, [ (file_stem, [lines]) ])
    plan: list[tuple[str, list[tuple[str, list[str]]]]] = []

    for f in sorted(SRC.glob("ch*.md")):
        if f.name.startswith("ch00"):
            continue
        lines = io.open(f, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
        chapter_dir = f.stem
        pieces: list[tuple[str, list[str]]] = []
        cur_name, cur = None, []
        k = 0
        for ln in lines:
            m1, m2, m3 = H1.match(ln), H2.match(ln), H3.match(ln)
            if m1:
                num = m1.group(1) or m1.group(2)
                title = m1.group(3)
                lab = slug(title, used, "app-" if m1.group(2) else "ch-")
                number_to_label[num] = lab
                if cur_name is not None:
                    pieces.append((cur_name, cur))
                # ch11 holds several appendices: each H1 starts a new fragment
                cur_name = f"{k:02d}-{lab}"
                k += 1
                cur = [f"# {title} {{#{lab}}}"]
                continue
            if m2 and not ln.startswith("###"):
                if cur_name is not None:
                    pieces.append((cur_name, cur))
                num, title = m2.group(1), m2.group(2)
                lab = slug(title, used, "s-")
                if num:
                    number_to_label[num] = lab
                cur_name = f"{k:02d}-{lab}"
                k += 1
                cur = [f"## {title} {{#{lab}}}"]
                continue
            if m3:
                num, title = m3.group(1), m3.group(2)
                lab = slug(title, used, "s-")
                if num:
                    number_to_label[num] = lab
                cur.append(f"### {title} {{#{lab}}}")
                continue
            cur.append(ln)
        if cur_name is not None:
            pieces.append((cur_name, cur))
        plan.append((chapter_dir, pieces))

    # ── rewrite typed references ──────────────────────────────────────────────────────
    unmapped, replaced = [], 0

    def fix(text: str, where: str) -> str:
        nonlocal replaced

        def sub(m):
            nonlocal replaced
            kind, num = m.group(1), m.group(2)
            # "Appendix E" is a letter; "Chapter 7" a whole number; "Section 7.2" dotted.
            lab = number_to_label.get(num)
            ok = lab and ((kind == "Appendix") == bool(re.fullmatch(r"[A-H]", num)))
            if not ok:
                unmapped.append((where, m.group(0),
                                 text[max(0, m.start() - 50):m.end() + 50].replace("\n", " ")))
                return m.group(0)
            replaced += 1
            return f"{{{{ref:{lab}}}}}"

        # never touch inline code or claim tokens
        shields: list[str] = []

        def hide(m):
            shields.append(m.group(0))
            return f"\x00{len(shields) - 1}\x00"

        t = re.sub(r"`[^`]*`|\{\{[^}]*\}\}", hide, text)
        t = REF.sub(sub, t)
        for i, s in enumerate(shields):
            t = t.replace(f"\x00{i}\x00", s)
        return t

    outputs: dict[Path, str] = {}
    for chapter_dir, pieces in plan:
        for name, body in pieces:
            text = "\n".join(body).strip() + "\n"
            outputs[POOL / chapter_dir / f"{name}.md"] = fix(text, f"{chapter_dir}/{name}")

    # ── front matter: split by H2, references fixed the same way ──────────────────────
    front = io.open(SRC / "ch00_front.md", encoding="utf-8").read().replace("\r\n", "\n")
    parts = re.split(r"(?m)^(?=## )", front)
    for p in parts[1:]:
        title = p.splitlines()[0][3:].strip()
        name = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        outputs[POOL / "front" / f"{name}.md"] = fix(p.strip() + "\n", f"front/{name}")

    print(f"labels            {len(number_to_label)} numbered, {len(used)} total")
    print(f"fragments         {len(outputs)}")
    print(f"refs tokenised    {replaced}")
    print(f"refs UNMAPPED     {len(unmapped)}")
    for where, ref, ctx in unmapped:
        print(f"  {where:<55} {ref:<14} ...{ctx}...")

    if dry:
        print("dry run: nothing written")
        return 0
    if POOL.exists() and any(POOL.rglob("*.md")):
        print(f"{POOL} already holds fragments; refusing to overwrite a migration.")
        return 1
    for p, t in outputs.items():
        write_atomic(p, t)
    write_atomic(POOL / "labels.json",
                 json.dumps({"_note": "old typed number -> label, as migrated 2026-09-18",
                             "labels": dict(sorted(number_to_label.items(),
                                                   key=lambda kv: [(0, int(x)) if x.isdigit()
                                                                   else (1, x)
                                                                   for x in kv[0].split(".")]))},
                            indent=2))
    print(f"wrote {len(outputs)} fragments to {POOL.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
