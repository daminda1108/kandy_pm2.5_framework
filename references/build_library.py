"""build_library.py -- one organised reference library for the thesis and Paper 1 (2026-10-07).

1. Reads both bibliographies (thesis/preprint `kandy_pm25/docs/paper/references.bib`, Paper 1
   `papers/paper1_information_budget/references/references.bib`) and merges them by DOI (else by key).
2. Matches the PDFs already in `references/papers/` to entries by the DOI printed on their first pages.
3. For entries still without a PDF, asks OpenAlex (no account needed) for LEGAL open-access locations and downloads
   the first one that is really a PDF. Paywalled works are listed for retrieval through the university library.
4. Writes `references/library/<citekey>.pdf`, `INDEX.csv`, `library.bib` (Zotero-importable, with `file` fields) and
   `README.md`. Originals in `references/papers/` are left untouched. Re-runnable: existing files are kept.

Usage: python references/build_library.py
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "references" / "library"
OLD = ROOT / "references" / "papers"
BIBS = {"thesis": ROOT / "kandy_pm25" / "docs" / "paper" / "references.bib",
        "paper1": ROOT / "papers" / "paper1_information_budget" / "references" / "references.bib"}
UA = {"User-Agent": "kandy-pm25-reference-library/1.0 (academic research; open-access only)"}
MATCHED: set[str] = set()
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>{}]+", re.I)


# ── bib parsing (entries are simple and well-formed: one field per line or wrapped) ──────────────
def parse_bib(path: Path) -> list[dict]:
    text = io.open(path, encoding="utf-8").read()
    out = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        typ, key, start = m.group(1).lower(), m.group(2), m.end()
        depth, i = 1, start
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0); i += 1
        body = text[start:i - 1]
        fields, j = {}, 0
        for fm in re.finditer(r"(\w+)\s*=\s*", body):
            if fm.start() < j:
                continue
            k, p = fm.group(1).lower(), fm.end()
            if p < len(body) and body[p] == "{":
                d, q = 1, p + 1
                while q < len(body) and d:
                    d += {"{": 1, "}": -1}.get(body[q], 0); q += 1
                val, j = body[p + 1:q - 1], q
            elif p < len(body) and body[p] == '"':
                q = body.index('"', p + 1); val, j = body[p + 1:q], q + 1
            else:
                q = re.search(r"[,\n]", body[p:]); q = p + (q.start() if q else len(body) - p)
                val, j = body[p:q], q
            fields[k] = " ".join(val.split())
        out.append({"type": typ, "key": key, "raw": text[m.start():i], **fields})
    return out


def clean_doi(d: str | None) -> str | None:
    if not d:
        return None
    m = DOI_RE.search(d)
    return m.group(0).rstrip(".,;)").lower() if m else None


# ── existing PDFs: find the DOI on the first two pages ──────────────────────────────────────────
def pdf_dois(path: Path) -> set[str]:
    try:
        import fitz
        doc = fitz.open(path)
        txt = " ".join(doc[i].get_text() for i in range(min(2, len(doc))))
        return {clean_doi(m.group(0)) for m in DOI_RE.finditer(txt)}
    except Exception:                                                   # noqa: BLE001
        return set()


def is_pdf(b: bytes) -> bool:
    return b[:5] == b"%PDF-"


def fetch_oa(doi: str) -> tuple[str | None, str]:
    """Return (pdf_url_that_worked, status)."""
    try:
        r = requests.get(f"https://api.openalex.org/works/doi:{doi}", headers=UA, timeout=30)
    except Exception as e:                                              # noqa: BLE001
        return None, f"openalex error {type(e).__name__}"
    if r.status_code != 200:
        return None, f"openalex {r.status_code}"
    w = r.json()
    if not w.get("open_access", {}).get("is_oa"):
        return None, "closed access"
    urls = []
    for loc in ([w.get("best_oa_location")] + (w.get("locations") or [])):
        if loc and loc.get("pdf_url") and loc["pdf_url"] not in urls:
            urls.append(loc["pdf_url"])
    if w.get("open_access", {}).get("oa_url") and w["open_access"]["oa_url"] not in urls:
        urls.append(w["open_access"]["oa_url"])
    # fallbacks: the PDF that each landing page declares for indexers (citation_pdf_url), and Europe PMC's copy
    for loc in ([w.get("best_oa_location")] + (w.get("locations") or [])):
        lp = (loc or {}).get("landing_page_url")
        if lp:
            pdf = landing_pdf(lp)
            if pdf and pdf not in urls:
                urls.append(pdf)
    pmcid = (w.get("ids") or {}).get("pmcid")
    if pmcid:
        pid = pmcid.rstrip("/").split("/")[-1]
        urls.append(f"https://europepmc.org/articles/{pid}?pdf=render")
    return (urls, "oa") if urls else (None, "oa but no pdf link")


BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/126.0 Safari/537.36 (academic reference library; open access only)",
           "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.8"}


def landing_pdf(url: str) -> str | None:
    try:
        r = requests.get(url, headers=BROWSER, timeout=30, allow_redirects=True)
    except Exception:                                                   # noqa: BLE001
        return None
    if r.status_code != 200:
        return None
    if is_pdf(r.content):
        return r.url
    m = re.search(r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)', r.text, re.I) or \
        re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url', r.text, re.I)
    if m:
        return requests.compat.urljoin(r.url, m.group(1).replace("&amp;", "&"))
    return None


def download(urls: list[str], dest: Path) -> str | None:
    for u in urls:
        try:
            r = requests.get(u, headers=BROWSER, timeout=60, allow_redirects=True)
        except Exception:                                               # noqa: BLE001
            continue
        if r.status_code == 200 and is_pdf(r.content) and len(r.content) > 20_000:
            tmp = dest.with_suffix(".part"); tmp.write_bytes(r.content); os.replace(tmp, dest)
            return u
        time.sleep(0.5)
    return None


def main() -> int:
    LIB.mkdir(parents=True, exist_ok=True)
    merged: dict[str, dict] = {}
    for src, path in BIBS.items():
        for e in parse_bib(path):
            doi = clean_doi(e.get("doi")) or clean_doi(e.get("url"))
            k = doi or f"key:{e['key'].lower()}"
            if k in merged:
                merged[k]["cited_by"].add(src); merged[k]["keys"].add(e["key"])
            else:
                merged[k] = {**e, "doi": doi, "cited_by": {src}, "keys": {e["key"]}}
    print(f"{len(merged)} unique works from {', '.join(BIBS)}", flush=True)

    # match existing PDFs
    by_doi = {v["doi"]: v for v in merged.values() if v["doi"]}
    for f in sorted(OLD.glob("*.pdf")):
        for d in pdf_dois(f):
            if d in by_doi:
                dest = LIB / f"{by_doi[d]['key']}.pdf"
                if not dest.exists():
                    dest.write_bytes(f.read_bytes())
                by_doi[d]["status"] = f"held (from references/papers/{f.name})"
                MATCHED.add(f.name)
                break

    rows = []
    for n, v in enumerate(sorted(merged.values(), key=lambda x: x["key"].lower()), 1):
        dest = LIB / f"{v['key']}.pdf"
        if dest.exists():
            v.setdefault("status", "held")
        elif v["doi"]:
            urls, st = fetch_oa(v["doi"])
            if urls:
                got = download(urls, dest)
                v["status"] = f"downloaded (open access: {got})" if got else "open access, but no link served a PDF"
            else:
                v["status"] = st
            time.sleep(0.2)
        else:
            v["status"] = "no DOI (book, report, dataset or web page)"
        held = dest.exists()
        rows.append({"key": v["key"], "also_keys": ";".join(sorted(v["keys"] - {v["key"]})),
                     "year": v.get("year", ""), "authors": v.get("author", "")[:120],
                     "title": v.get("title", "").replace("{", "").replace("}", ""),
                     "venue": v.get("journal", v.get("booktitle", v.get("publisher", ""))),
                     "doi": v["doi"] or "", "cited_by": ";".join(sorted(v["cited_by"])),
                     "pdf": f"{v['key']}.pdf" if held else "", "status": v["status"]})
        if n % 20 == 0:
            print(f"  {n}/{len(merged)}", flush=True)

    with open(LIB / "INDEX.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    # Zotero-importable bib with file fields
    bib = []
    for v in sorted(merged.values(), key=lambda x: x["key"].lower()):
        raw = v["raw"].rstrip()
        if (LIB / f"{v['key']}.pdf").exists() and "file" not in raw.lower().split("=")[0]:
            raw = raw[:-1].rstrip().rstrip(",") + f",\n  file = {{{v['key']}.pdf}}\n}}"
        bib.append(raw)
    (LIB / "library.bib").write_text("\n\n".join(bib) + "\n", encoding="utf-8")

    held = sum(1 for r in rows if r["pdf"])
    need = [r for r in rows if not r["pdf"] and r["doi"]]
    nodoi = [r for r in rows if not r["doi"]]
    md = [
        "# Reference library",
        "",
        "Built by `references/build_library.py` from the thesis/preprint bibliography "
        "(`kandy_pm25/docs/paper/references.bib`) and the Paper 1 bibliography "
        "(`papers/paper1_information_budget/references/references.bib`), merged by DOI. "
        "Re-run the script after adding references; existing PDFs are kept.",
        "",
        f"- **{len(rows)} unique works**; **{held} PDFs held** as `<citekey>.pdf`; "
        f"**{len(need)} to fetch through the university library** (closed access or no PDF link); "
        f"**{len(nodoi)} without a DOI** (books, reports, datasets, web pages).",
        "- Only legal open-access copies were downloaded (OpenAlex locations: publisher, arXiv, repositories).",
        "- `INDEX.csv`: key, year, authors, title, venue, DOI, which document cites it, PDF file, status.",
        "- `library.bib`: both bibliographies merged, with `file = {<citekey>.pdf}` for Zotero "
        "(File > Import, then point the linked-file base directory at this folder).",
        "- The original downloads in `references/papers/` are left as they were; matched ones are copied here.",
        "",
        "## Other papers in references/papers/ (not cited in either bibliography, or no DOI on their first pages)",
        "",
        *[f"- `{f.name}`" for f in sorted(OLD.iterdir()) if f.is_file() and f.name not in MATCHED],
        "",
        "## To fetch through the university library",
        "",
        "| key | year | title | DOI |", "|---|---|---|---|",
        *[f"| {r['key']} | {r['year']} | {r['title'][:90]} | {r['doi']} |" for r in need],
        "",
        "## Without a DOI",
        "",
        "| key | year | title | venue |", "|---|---|---|---|",
        *[f"| {r['key']} | {r['year']} | {r['title'][:90]} | {r['venue'][:50]} |" for r in nodoi],
    ]
    (LIB / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"works {len(rows)} | held {held} | to fetch {len(need)} | no DOI {len(nodoi)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
