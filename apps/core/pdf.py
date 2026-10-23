"""
pdf.py - Shared PDF font (Atkinson Hyperlegible) for certificates, receipts and reports
=====================================================================================

Owner: Dinesh Upreti. The built-in PDF fonts cannot print Māori macrons (ā, ē, ī, ō, ū),
so names like "Hēmi" would break. Atkinson Hyperlegible (SIL Open Font License,
see fonts/OFL.txt) has them and is easy to read.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent / "fonts"
REGULAR, BOLD = "Atkinson", "Atkinson-Bold"


@lru_cache(maxsize=1)
def register_fonts() -> tuple[str, str]:
    """Register the fonts once; return (regular, bold) font names."""
    # pylint: disable=import-outside-toplevel
    from reportlab.lib.fonts import addMapping
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont(REGULAR, str(FONT_DIR / "AtkinsonHyperlegible-Regular.ttf")))
    pdfmetrics.registerFont(TTFont(BOLD, str(FONT_DIR / "AtkinsonHyperlegible-Bold.ttf")))
    addMapping(REGULAR, 0, 0, REGULAR)
    addMapping(REGULAR, 1, 0, BOLD)
    addMapping(REGULAR, 0, 1, REGULAR)
    addMapping(REGULAR, 1, 1, BOLD)
    return REGULAR, BOLD


def styles():
    """reportlab sample styles switched to the Atkinson font."""
    from reportlab.lib.styles import getSampleStyleSheet  # pylint: disable=import-outside-toplevel
    regular, bold = register_fonts()
    sheet = getSampleStyleSheet()
    for name in ("Normal", "Italic", "BodyText"):
        sheet[name].fontName = regular
    for name in ("Title", "Heading1", "Heading2", "Heading3"):
        sheet[name].fontName = bold
    return sheet
