"""writing_audit.py -- a read-only audit of Thesis A's prose for the damage that repeated patching leaves and that the
mechanical gates (claims, lint, assembly) cannot see (2026-10-12). It edits nothing.

Runs on the SOURCE files the thesis is assembled from (theses/a/thesis.md include tree), so every finding carries a file
and line the author can open. Claim tokens are replaced by "N" so wording, not values, is compared.

Checks
  1. review traces       sentences that narrate the review process ("an external review asked", "added after")
  2. repeated caveats    near-duplicate sentences in different sections (word 4-gram Jaccard), and how often each
                         standing caveat is restated across the document
  3. terminology         competing names for one concept, with counts and first locations
  4. patch seams         markers of text added after the fact (parenthetical stacks, "now", "since", "before the")
  5. density             sentences carrying many numbers or very long sentences

Out: #writing/WRITING_AUDIT_thesis_a.md
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

WR = Path(__file__).resolve().parents[1]
INC = re.compile(r"^\{\{include:([^}\s]+)(?:\s+shift=(-?\d+))?\}\}\s*$")
NUMTOK = re.compile(r"\bN\b")


def nnum(t):
    return len(NUMTOK.findall(t))


TOK = re.compile(r"\{\{(claim|ref|fig|tbl|this|This|include)[^}]*\}\}")


def expand(path: Path, part: str, out: list):
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = INC.match(line.strip())
        if m:
            sub = WR / m.group(1)
            expand(sub, "appendix" if ("appendices" in path.name or part == "appendix") else part, out)
        else:
            out.append((path.relative_to(WR).as_posix(), i, line, part))


def lines_to_sentences(lines):
    """paragraphs from consecutive prose lines; sentences keep the (file, line) where they start."""
    paras, cur = [], []
    for f, i, text, part in lines:
        t = text.strip()
        prose = t and not t.startswith(("#", "|", "{{fig", "{{tbl", "```", "<", "!", "---", ":::")) and not INC.match(t)
        if prose:
            cur.append((f, i, TOK.sub("N", t), part))      # tokens out BEFORE sentence splitting (their keys hold dots)
        elif cur:
            paras.append(cur); cur = []
    if cur:
        paras.append(cur)
    sents = []
    for p in paras:
        # rebuild the paragraph with a char -> (file, line) map
        buf, where = "", []
        for f, i, t, part in p:
            if buf:
                buf += " "; where.append(where[-1])
            for ch in t:
                buf += ch; where.append((f, i, part))
        for m in re.finditer(r"[^.!?]+(?:[.!?]+(?=\s|$)|$)", buf):
            s = m.group(0).strip()
            if len(s.split()) >= 5:
                f, i, part = where[m.start() + (len(m.group(0)) - len(m.group(0).lstrip()))]
                sents.append(dict(file=f, line=i, part=part, raw=s, text=TOK.sub("N", s)))
    return sents


def section_of(f):
    return f.rsplit("/", 1)[0] if f.startswith("pool/") else f


def ngrams(s, n=4):
    w = re.findall(r"[a-z]+|N", s.lower())
    return {tuple(w[k:k + n]) for k in range(len(w) - n + 1)}


REVIEW = re.compile(r"\b(external review(er)?s?|a review (asked|pointed|found|raised)|reviewers?|asked for it|"
                    r"(was|were) added after|added after (an?|the)|in response to|was made after the other)\b", re.I)
SEAM = {
    "\"before/after the refit|correction|re-anchoring\"": re.compile(r"\b(before|after) (the|its|this) (refit|re-?anchoring|correction|widening|rebuild)\b", re.I),
    "\"now\" describing a model change": re.compile(r"\b(is|are|was|were) now\b|\bnow (rests?|reads?|carries|contains|sets?)\b", re.I),
    "\"as first delivered / earlier version\"": re.compile(r"\b(as first delivered|first delivered|an earlier version|earlier drafts?)\b", re.I),
    "\"since\" + model step": re.compile(r"\bsince (the|it was|its) (re-?anchor|refit|cap|widen)", re.I),
}
CAVEATS = {
    "one station / single station": r"\bone (regulatory )?station\b|\bsingle station\b|\bone city-centre station\b",
    "spatial pattern is a hypothesis": r"\bhypothesis\b",
    "not a source apportionment": r"source apportionment",
    "property of the decomposition": r"property of the decomposition",
    "calibration, not validation": r"calibration,? not validation|cannot (be used|serve) as (a )?(check|validation)|not (count|counted) as validation",
    "provisional": r"\bprovisional\b",
    "exploratory": r"\bexploratory\b",
    "held out / later record checks": r"\bheld[- ]out\b|\blater record\b",
    "not established / not resolvable improvement": r"not an established|no resolvable",
    "humidity correction": r"humidity correction|constant[- ]humidity|hourly[- ]humidity",
    "point vs cell / change of support": r"change of support|point (and|with|like) a (kilometre )?cell|area mean",
    "registered before scoring": r"(written|registered|specified|fixed) (down )?(before|in advance)",
}
TERMS = {
    "the CEA monitor": [r"regulatory station", r"regulatory monitor", r"reference station", r"CEA station",
                        r"city-centre station", r"\bAAQMS\b", r"Central Environmental Authority('s)? (Kandy )?(station|monitor)"],
    "the two FECT units": [r"low-cost sensors?", r"FECT sensors?", r"Kandy sensors?", r"the two sensors", r"sensor record"],
    "T(t)": [r"temporal anchor", r"\banchor\b(?! station)", r"\bT\(t\)|\*T\*\(\*t\*\)", r"temporal model", r"temporal estimate"],
    "B(t)": [r"regional background", r"background", r"regional-background estimate", r"\*B\*\(\*t\*\)"],
    "f": [r"local fraction", r"local share", r"local increment'?s? share", r"\bf\b"],
    "daily cycle": [r"daily cycle", r"diurnal cycle", r"diurnal (shape|profile)", r"hour-of-day (cycle|shape|profile)"],
    "the product": [r"\bthe field\b", r"\breconstruction\b", r"\bthe map\b", r"delivered field", r"delivered series"],
    "withheld data": [r"held[- ]out", r"withheld"],
    "unit spelling": [r"micrograms per cubic metre", r"µg/m³|µg m⁻³|ug/m3"],
    "percent spelling": [r"per cent", r"\bpercent\b", r"\d ?%"],
    "monsoon spelling": [r"south-west monsoon", r"southwest monsoon", r"SW monsoon", r"north-east monsoon", r"northeast monsoon"],
}


def main():
    lines = []
    expand(WR / "theses/a/thesis.md", "body", lines)
    S = lines_to_sentences(lines)
    body = [s for s in S if s["part"] == "body"]
    out = ["# Writing audit, Thesis A", "",
           f"Generated by `#writing/build/writing_audit.py` from the source tree of `theses/a/thesis.md` "
           f"({len(set(s['file'] for s in S))} files, {len(S)} sentences of five words or more; {len(body)} in the main "
           "text, the rest in appendices). The script itself edits nothing. Claim tokens are shown as N. Locations are "
           "`file:line` of the sentence's first line.", "",
           "Each section lists what to look at, not what to write; the rewrite is the author's.", ""]

    # 1. review traces
    rv = [s for s in S if REVIEW.search(s["text"])]
    out += ["## 1. Traces of the review process", "",
            f"{len(rv)} sentences narrate how the thesis was revised (who asked, what was added after). A thesis states "
            "what was tested and how; the history belongs in `CHANGELOG_thesis.md`. Candidates to reword or drop:", ""]
    out += [f"- `{s['file']}:{s['line']}` ({s['part']}): {s['text'][:230]}" for s in rv] or ["- none"]
    out.append("")

    # 2a. standing caveats: how often each is restated, by chapter-level location
    out += ["## 2. Repeated caveats", "",
            "### 2a. How often each standing caveat is stated", "",
            "Counts of sentences carrying the caveat, main text and appendices. A caveat stated once where the result is "
            "reported and once in the conclusions is usually enough; high counts in the main text are the candidates.", "",
            "| caveat | main text | appendices | files (main text) |", "|---|---|---|---|"]
    for name, pat in CAVEATS.items():
        r = re.compile(pat, re.I)
        b = [s for s in body if r.search(s["text"])]
        a = [s for s in S if s["part"] != "body" and r.search(s["text"])]
        out.append(f"| {name} | {len(b)} | {len(a)} | {len(set(s['file'] for s in b))} |")
    out.append("")

    # 2b. near-duplicate sentences across different sections
    grams = [ngrams(s["text"]) for s in S]
    pairs = []
    for i in range(len(S)):
        if len(grams[i]) < 6:
            continue
        for j in range(i + 1, len(S)):
            if len(grams[j]) < 6 or section_of(S[i]["file"]) == section_of(S[j]["file"]) and abs(S[i]["line"] - S[j]["line"]) < 40:
                continue
            inter = len(grams[i] & grams[j])
            if inter < 5:
                continue
            jac = inter / len(grams[i] | grams[j])
            if jac >= 0.30:
                pairs.append((jac, S[i], S[j]))
    pairs.sort(key=lambda x: -x[0])
    out += ["### 2b. Near-duplicate sentences in different places", "",
            f"{len(pairs)} pairs share at least 30 % of their four-word sequences. Some repetition is deliberate (the "
            "abstract, conclusions and summary restate results); repeated wording between two results sections, or "
            "between the results and the discussion, usually is not.", ""]
    for jac, a, b in pairs[:60]:
        out.append(f"- **{jac:.2f}** `{a['file']}:{a['line']}` ↔ `{b['file']}:{b['line']}`  \n  "
                   f"A: {a['text'][:200]}  \n  B: {b['text'][:200]}")
    if len(pairs) > 60:
        out.append(f"- … and {len(pairs) - 60} weaker pairs")
    out.append("")

    # 3. terminology
    out += ["## 3. Terminology: competing names for one thing", "",
            "Counts of each variant in the main text. Where a concept has several names, pick one for the main text "
            "(defined at first use) and keep the others only where they mean something different.", ""]
    for concept, variants in TERMS.items():
        rows = []
        for v in variants:
            r = re.compile(v, re.I if concept not in ("f",) else 0)
            hits = [s for s in body if r.search(s["raw"])]
            if hits:
                rows.append(f"{v.replace('|', '/')} ×{len(hits)} (first `{hits[0]['file']}:{hits[0]['line']}`)")
        out.append(f"- **{concept}**: " + "; ".join(rows) if rows else f"- **{concept}**: none")
    out.append("")

    # 4. patch seams
    out += ["## 4. Patch seams", "",
            "Wording that describes the model's history rather than the model (\"as first delivered\", \"before the "
            "refit\", \"is now\"). In the results this is sometimes needed (a before/after comparison); elsewhere it reads "
            "as a patch. Also paragraphs where many such markers cluster.", ""]
    for name, r in SEAM.items():
        hits = [s for s in body if r.search(s["text"])]
        out.append(f"- **{name}**: {len(hits)} sentences" + (" — " + "; ".join(f"`{s['file']}:{s['line']}`" for s in hits[:12]) if hits else ""))
    out.append("")

    # 5. density
    dense = sorted(body, key=lambda s: -(nnum(s["text"])))[:25]
    longs = sorted(body, key=lambda s: -len(s["text"]))[:15]
    out += ["## 5. Density", "",
            "### 5a. Sentences carrying the most numbers (main text)", "",
            "Six or more numbers in one sentence is hard to read aloud; a table or two sentences may serve better.", ""]
    out += [f"- {(nnum(s['text']))} numbers, `{s['file']}:{s['line']}`: {s['text'][:180]}" for s in dense if (nnum(s["text"])) >= 6]
    out += ["", "### 5b. Longest sentences (main text)", ""]
    out += [f"- {len(s['text'].split())} words, `{s['file']}:{s['line']}`: {s['text'][:160]}…" for s in longs]
    out.append("")

    # 6. connective tics (per 1,000 words of main text)
    words = sum(len(s["text"].split()) for s in body)
    out += ["## 6. Recurring connectives (main text)", "", f"Per 1,000 words over {words:,} words. Not errors; a "
            "high rate of one connective is a sign of sentences built to the same pattern.", ""]
    for w in ("therefore", "rather than", "which is", "not ", "only", "itself", "however"):
        n = sum(len(re.findall(r"\b" + re.escape(w.strip()) + r"\b", s["text"], re.I)) for s in body)
        out.append(f"- **{w.strip()}**: {n} ({1000 * n / words:.1f} per 1,000 words)")
    out.append("")

    # summary
    out.insert(6, "")
    out.insert(6, f"**At a glance:** {len(rv)} review-process sentences; {len(pairs)} near-duplicate pairs; "
                  f"{sum(1 for s in body if (nnum(s['text'])) >= 6)} main-text sentences with six or more numbers; "
                  f"{sum(1 for s in body if len(s['text'].split()) > 60)} main-text sentences over 60 words.")
    notes = WR / "build" / "writing_audit_notes.md"          # the author-facing reading, written by hand
    if notes.exists():
        out[7:7] = ["", notes.read_text(encoding="utf-8").rstrip(), "", "---", "", "# Measured lists", ""]
    p = WR / "WRITING_AUDIT_thesis_a.md"
    p.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(out[6]); print("wrote", p)


if __name__ == "__main__":
    main()
