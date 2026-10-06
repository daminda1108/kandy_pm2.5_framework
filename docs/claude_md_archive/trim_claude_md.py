"""Move absorbed blocks of CLAUDE.md verbatim into an append-only archive.

Safe by construction (gotcha #81): read once, build both outputs in memory,
check that kept + moved == original line for line, write each via a temp
file and os.replace. Refuses if any range does not start where expected.
"""
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\ProjectCD")
SRC = ROOT / "CLAUDE.md"
ARCH = ROOT / "docs" / "claude_md_archive" / "CLAUDE_archived_blocks.md"
EXPECTED_SHA = "d00725e4d809d0b0df73b21a64444aa4e28542c65888cc1b2e7e4fe4ea2be69b"
DATE = "2026-10-05"

# (first, last) 1-indexed inclusive, with the text the first line must start with.
RANGES = [
    (130, 188, '## Current State (updated 2026-09-12'),
]

raw = SRC.read_bytes()
if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA:
    sys.exit("REFUSED: CLAUDE.md changed since the backup was taken")
lines = raw.decode("utf-8", errors="surrogateescape").splitlines(keepends=True)

drop = set()
moved_chunks = []
for a, b, head in RANGES:
    if not lines[a - 1].startswith(head):
        sys.exit(f"REFUSED: line {a} is {lines[a-1][:60]!r}, expected {head!r}")
    if drop & set(range(a, b + 1)):
        sys.exit(f"REFUSED: range {a}-{b} overlaps another")
    drop |= set(range(a, b + 1))
    moved_chunks.append((a, b, lines[a - 1 : b]))

kept = [ln for i, ln in enumerate(lines, 1) if i not in drop]
moved = [ln for _, _, chunk in moved_chunks for ln in chunk]
# Line-for-line conservation: re-interleave and compare with the original.
rebuilt, k, m = [], iter(kept), iter(moved)
for i in range(1, len(lines) + 1):
    rebuilt.append(next(m) if i in drop else next(k))
assert rebuilt == lines, "conservation check failed"

out = [f"\n\n# Archived from CLAUDE.md on {DATE}\n",
       f"Source: CLAUDE.md sha256 {EXPECTED_SHA[:12]} "
       f"(full copy: CLAUDE_{DATE}_pre-trim.md). Verbatim; line numbers are "
       f"those of that copy.\n"]
for a, b, chunk in moved_chunks:
    out.append(f"\n<!-- CLAUDE.md lines {a}-{b} -->\n")
    out.extend(chunk)

def write_atomic(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(text.encode("utf-8", errors="surrogateescape"))
    os.replace(tmp, path)

prior = ARCH.read_bytes().decode("utf-8", errors="surrogateescape") if ARCH.exists() else (
    "# CLAUDE.md archive — append-only\n\n"
    "Blocks moved out of `CLAUDE.md` when their conclusions were absorbed into\n"
    "`CONTEXT.md`, the gotchas, `PROJECT.md` or the ledger. Never edit; only append.\n")
write_atomic(ARCH, prior + "".join(out))
write_atomic(SRC, "".join(kept))
print(f"original {len(lines)} lines -> kept {len(kept)}, moved {len(moved)}")
