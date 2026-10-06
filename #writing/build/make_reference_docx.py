"""Build the reference.docx that gives the thesis its typography.

Every style in pandoc's output comes from this reference document, so the departmental format
is set once here and nothing downstream has to know about fonts.

ENS4998 Final Report Format (Department of Environmental and Industrial Sciences, 2026-09-18):

    page       A4; margins left 1.25 in, right 1 in, top 1 in, bottom 1.25 in
    body       Times New Roman, justified, line spacing 1.5 (12 pt)
    chapters   14 pt bold, UPPERCASE, centred (upper-casing is done by assemble.py, so the
               contents list shows the same text the page does)
    headings   11 pt bold
    abstract   single spaced, justified ("Abstract Text")
    captions   12 pt italic, centred, single spaced (the 12 pt floor a previous instruction set
               for captions and tables is kept rather than quietly relaxed)

Custom styles used through pandoc's custom-style divs: Front Heading (DECLARATION, ABSTRACT, ...
set like a chapter title but kept out of the contents), Abstract Text, Marker (directive
paragraphs postprocess.py replaces), and the four title-page styles of the departmental template.

Page numbering, sections and the contents fields are NOT set here: pandoc cannot express them.
postprocess.py does that on the built document.

Usage: python make_reference_docx.py
Out:   build/reference.docx
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import docx
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

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
    # Theme font attributes OVERRIDE the explicit ones. Pandoc's default headings carry
    # w:asciiTheme="majorHAnsi", so without this the headings rendered in the theme's sans serif
    # while every style here claimed Times New Roman (seen in the first rendered build).
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(attr)) is not None:
            del rfonts.attrib[qn(attr)]


def _theme_fonts_to_body_font(path: Path) -> None:
    """Set the theme's major and minor Latin fonts to the body font.

    Stripping theme attributes from the styles this script touches is not enough: pandoc's
    reference document references the theme from docDefaults and from styles left untouched, and
    the theme names Aptos. Pointing the theme itself at Times New Roman means every theme
    reference, including any Word adds later, resolves to the required font.
    """
    import re as _re
    import shutil
    import zipfile

    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("word/theme/") and item.filename.endswith(".xml"):
                xml = data.decode("utf-8")
                xml = _re.sub(r'(<a:(?:major|minor)Font>\s*<a:latin typeface=")[^"]*(")',
                              rf"\g<1>{FONT}\g<2>", xml)
                data = xml.encode("utf-8")
            zout.writestr(item, data)
    shutil.move(str(tmp), str(path))


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
        s.left_margin = Inches(1.25)                # binding edge
        s.right_margin = Inches(1.0)
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.25)
        s.footer_distance = Cm(1.25)                # page number sits inside the bottom margin

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
    # Chapter titles 14 pt bold centred, on a new page; section headings 11 pt bold. Level 4
    # carries no number (departmental rule of three numbered levels), so it is set in italic
    # to stay distinguishable from level 3 at the same size.
    for name, pt, before, after, italic, centred in [
        ("Heading 1", 14, 0, 18, False, True),
        ("Heading 2", 11, 14, 6, False, False),
        ("Heading 3", 11, 12, 6, False, False),
        ("Heading 4", 11, 10, 4, True, False),
        ("Heading 5", 11, 10, 4, True, False),
    ]:
        try:
            st = d.styles[name]
        except KeyError:
            continue
        set_font(st, pt, bold=True, italic=italic)
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.alignment = (WD_ALIGN_PARAGRAPH.CENTER if centred
                                         else WD_ALIGN_PARAGRAPH.LEFT)
        st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.page_break_before = (name == "Heading 1")

    # ── departmental custom styles ───────────────────────────────────────────────────────
    def para_style(name, pt, *, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER,
                   spacing=WD_LINE_SPACING.SINGLE, before=0, after=0, page_break=False):
        try:
            st = d.styles[name]
        except KeyError:
            st = d.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        st.base_style = d.styles["Normal"]
        set_font(st, pt, bold=bold)
        pf = st.paragraph_format
        pf.alignment = align
        pf.line_spacing_rule = spacing
        pf.space_before, pf.space_after = Pt(before), Pt(after)
        pf.page_break_before = page_break
        pf.first_line_indent = Pt(0)
        return st

    # Front matter headings: chapter-title typography, own page, not in the contents.
    fh = para_style("Front Heading", 14, bold=True, after=18, page_break=True)
    fh.paragraph_format.keep_with_next = True
    para_style("Abstract Text", BODY_PT, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=6)
    para_style("Marker", 2)
    # Title page, after the departmental template: title 14 bold; name and registration 14;
    # submission lines 12; degree, university and year 12 bold.
    para_style("Title Page Title", 14, bold=True, before=0, after=36)
    para_style("Title Page Text", 12, after=6)
    para_style("Title Page Name", 14, after=6)
    para_style("Title Page Bold", 12, bold=True, after=6)

    # Reference list: single spaced with space between entries, so the list does not take
    # half as many pages again as it needs.
    try:
        bib = d.styles["Bibliography"]
        set_font(bib, BODY_PT)
        bib.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        bib.paragraph_format.space_after = Pt(6)
        bib.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    except KeyError:
        pass

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

    # Inline code is now only the odd identifier (a data-file variable name); the departmental
    # format requires Times New Roman throughout, so it is set in Times. Symbols are italic
    # mathematics (build/typeset_symbols.py), not code.
    try:
        set_font(d.styles["Verbatim Char"], BODY_PT)
    except KeyError:
        pass

    # Code BLOCKS stay monospace: a font that has to align by column is not Times. None remain
    # in the thesis after the equations became display mathematics.
    for name in ("Source Code",):
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
    _theme_fonts_to_body_font(OUT)

    print(f"wrote {OUT.relative_to(HERE.parent)}")
    print("  page      A4, margins L 1.25 in, R 1 in, T 1 in, B 1.25 in")
    print(f"  body      {FONT} {BODY_PT} pt, 1.5 spacing, justified")
    print(f"  headings  {FONT} bold: chapters 14 centred on a new page, sections 11")
    print(f"  captions  {FONT} {BODY_PT} pt italic, centred")
    return 0


if __name__ == "__main__":
    sys.exit(main())
