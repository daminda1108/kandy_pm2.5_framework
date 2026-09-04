"""Build the reference.docx that gives the thesis its typography.

WHY A REFERENCE DOCUMENT. Pandoc's default .docx is Calibri 11 pt. Every style in the output
comes from a reference document, so setting the typography once here is the difference between
a thesis that looks like a thesis and one that looks like a converted markdown file. Nothing
downstream has to know about fonts.

Standard practice, since no departmental template was issued:

    page       A4, 2.5 cm margins, 3.5 cm left for binding
    body       Times New Roman 12 pt, 1.5 line spacing, justified
    headings   Times New Roman bold, 14 / 13 / 12 pt, not blue and not sans serif
    captions   Times New Roman 12 pt, italic, centred
    tables     Times New Roman 12 pt

⚠ The 12 pt minimum applies to captions and table text as well, which is larger than
typographic convention would choose and lengthens the document. It is what was asked for and it
is applied consistently rather than quietly relaxed where it is inconvenient.

Run once. Re-run only if the typography changes.

Usage: python make_reference_docx.py
Out:   build/reference.docx
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import docx
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
OUT = HERE / "reference.docx"

FONT = "Times New Roman"
BODY_PT = 12
INK = RGBColor(0x00, 0x00, 0x00)


def set_font(style, size_pt: float, *, bold=False, italic=False, color=INK) -> None:
    """Set a style's font on every script, not only Latin.

    python-docx sets w:ascii only. Word falls back to a different face for anything it
    classifies as complex script or East Asian, which is how a document ends up with two fonts
    in one line without anyone choosing it.
    """
    f = style.font
    f.name = FONT
    f.size = Pt(size_pt)
    f.bold = bold
    f.italic = italic
    f.color.rgb = color
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), FONT)


def main() -> int:
    # Start from pandoc's own reference document so every style pandoc emits exists, then
    # override typography. Building from a blank document instead leaves styles like
    # "Source Code" and "Table Caption" undefined, and pandoc silently falls back.
    seed = HERE / "_pandoc_default.docx"
    try:
        with open(seed, "wb") as fh:
            subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"],
                           stdout=fh, check=True)
    except Exception as e:                                                  # noqa: BLE001
        print(f"could not get pandoc's default reference: {e}")
        return 1

    d = docx.Document(str(seed))

    # ── page ─────────────────────────────────────────────────────────────────────────────
    for s in d.sections:
        s.page_width, s.page_height = Cm(21.0), Cm(29.7)
        s.top_margin = s.bottom_margin = s.right_margin = Cm(2.5)
        s.left_margin = Cm(3.5)                     # binding edge

    # ── body ─────────────────────────────────────────────────────────────────────────────
    normal = d.styles["Normal"]
    set_font(normal, BODY_PT)
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_after = Pt(6)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # ── headings ─────────────────────────────────────────────────────────────────────────
    # Word's defaults are blue and sans serif, which is the single clearest sign of a
    # converted document.
    for name, pt, before, after in [
        ("Heading 1", 14, 18, 10),
        ("Heading 2", 13, 14, 8),
        ("Heading 3", 12, 12, 6),
        ("Heading 4", 12, 10, 6),
    ]:
        try:
            st = d.styles[name]
        except KeyError:
            continue
        set_font(st, pt, bold=True)
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        st.paragraph_format.keep_with_next = True

    # ── captions, tables, code, quotes ───────────────────────────────────────────────────
    for name, pt, italic, align in [
        ("Caption", BODY_PT, True, WD_ALIGN_PARAGRAPH.CENTER),
        ("Image Caption", BODY_PT, True, WD_ALIGN_PARAGRAPH.CENTER),
        ("Table Caption", BODY_PT, True, WD_ALIGN_PARAGRAPH.CENTER),
        ("Compact", BODY_PT, False, WD_ALIGN_PARAGRAPH.LEFT),
        ("Block Text", BODY_PT, False, WD_ALIGN_PARAGRAPH.JUSTIFY),
    ]:
        try:
            st = d.styles[name]
        except KeyError:
            continue
        set_font(st, pt, italic=italic)
        st.paragraph_format.alignment = align
        st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        st.paragraph_format.space_after = Pt(10 if "Caption" in name else 6)

    # Monospace stays monospace: a font that has to align by column is not Times.
    for name in ("Source Code", "Verbatim Char"):
        try:
            st = d.styles[name]
        except KeyError:
            continue
        st.font.name = "Consolas"
        st.font.size = Pt(BODY_PT - 2)
        rpr = st.element.get_or_add_rPr()
        rfonts = rpr.get_or_add_rFonts()
        for attr in ("w:ascii", "w:hAnsi", "w:cs"):
            rfonts.set(qn(attr), "Consolas")

    # Table text at body size, per the 12 pt minimum.
    for name in ("Table", "Table Grid", "Compact Table"):
        try:
            set_font(d.styles[name], BODY_PT)
        except KeyError:
            continue

    d.save(str(OUT))
    seed.unlink(missing_ok=True)

    print(f"wrote {OUT.relative_to(HERE.parent)}")
    print(f"  page      A4, {2.5} cm margins, 3.5 cm binding edge")
    print(f"  body      {FONT} {BODY_PT} pt, 1.5 spacing, justified")
    print(f"  headings  {FONT} bold 14 / 13 / 12 / 12")
    print(f"  captions  {FONT} {BODY_PT} pt italic, centred")
    return 0


if __name__ == "__main__":
    sys.exit(main())
