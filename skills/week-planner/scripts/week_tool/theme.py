"""The WorkSpace Labs look, in one place.

The same light ground, Plus Jakarta Sans and one blue accent as the workflow-project PDF, so the two
skills read as one family. Red is only for "waiting on you". Every colour, font and size is read from here.
"""

import os

from reportlab.lib.colors import Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont, TTFontFile

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(SKILL_ROOT, "assets")

# Colours (the workflow-project values)
SPACE = HexColor("#F2F5FF")        # the pale ground: day columns, bands
INK = HexColor("#10182E")
INK_SOFT = HexColor("#4A5478")
INK_FAINT = HexColor("#8A93B2")
ACCENT = HexColor("#3E5BFF")       # one emphasis word, active work, the goal band
RED = HexColor("#E03131")          # only for "waiting on you"
WHITE = HexColor("#FFFFFF")
LINE = HexColor("#D6DCEF")
LINE_SOFT = HexColor("#E3E8F7")
BOX_STROKE = HexColor("#C9D1EA")


def mix(base, tint, amount):
    """A solid colour that looks like `tint` laid over `base` at `amount` opacity."""
    return Color(base.red + (tint.red - base.red) * amount,
                 base.green + (tint.green - base.green) * amount,
                 base.blue + (tint.blue - base.blue) * amount)


TAG_BG = mix(WHITE, ACCENT, 0.08)
TAG_LINE = mix(WHITE, ACCENT, 0.22)
GOAL_BG = mix(WHITE, ACCENT, 0.09)
RED_BG = mix(WHITE, RED, 0.07)
RED_LINE = mix(WHITE, RED, 0.28)
HATCH = mix(WHITE, INK, 0.10)

# The thin bar on the left of every card says what kind of work it is.
BAR = {
    "active": ACCENT,
    "review": mix(WHITE, ACCENT, 0.45),
    "checklist": mix(WHITE, ACCENT, 0.30),
    "plan": HexColor("#C3C8DA"),
    "idea": HexColor("#C3C8DA"),
    None: HexColor("#C3C8DA"),
    "personal": HexColor("#9AA3C0"),
    "decision": RED,
}

# Fonts (static cuts of Plus Jakarta Sans, SIL Open Font License, see assets/fonts/OFL.txt)
REGULAR = "PJS-Regular"
MEDIUM = "PJS-Medium"
SEMIBOLD = "PJS-SemiBold"
BOLD = "PJS-Bold"
EXTRABOLD = "PJS-ExtraBold"
_FONT_FILES = {
    REGULAR: "PlusJakartaSans-Regular.ttf",
    MEDIUM: "PlusJakartaSans-Medium.ttf",
    SEMIBOLD: "PlusJakartaSans-SemiBold.ttf",
    BOLD: "PlusJakartaSans-Bold.ttf",
    EXTRABOLD: "PlusJakartaSans-ExtraBold.ttf",
}
_cmap = None


def register_fonts():
    """Makes the house fonts available to measuring and drawing. Safe to call twice."""
    global _cmap
    registered = pdfmetrics.getRegisteredFontNames()
    for name, filename in _FONT_FILES.items():
        if name not in registered:
            pdfmetrics.registerFont(TTFont(name, os.path.join(ASSETS, "fonts", filename)))
    if _cmap is None:
        _cmap = TTFontFile(os.path.join(ASSETS, "fonts", _FONT_FILES[REGULAR])).charToGlyph


def missing_characters(text):
    """Characters the house font cannot draw (they would print as empty boxes)."""
    register_fonts()
    return sorted({ch for ch in text if not ch.isspace() and ord(ch) not in _cmap})


def width(text, font, size):
    register_fonts()
    return pdfmetrics.stringWidth(text, font, size)


def tracked_width(text, font, size, tracking):
    """Width of letter-spaced text (small capital labels)."""
    return width(text, font, size) + tracking * max(len(text) - 1, 0)


def wrap(text, font, size, room):
    """Splits text into lines no wider than `room`. Returns None when one word alone is too wide:
    words are never cut, the caller refuses instead. Only plain spaces break a line, so a no-break
    space keeps "1 h" together."""
    lines, current = [], ""
    for word in [w for w in text.split(" ") if w]:
        if width(word, font, size) > room:
            return None
        candidate = word if not current else current + " " + word
        if width(candidate, font, size) <= room:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# Text styles: (font, size, line height)
CARD_TITLE = (BOLD, 8.0, 9.8)
CARD_DETAIL = (REGULAR, 6.8, 8.4)
DAY_NAME = (BOLD, 6.6)
DAY_NUMBER = (EXTRABOLD, 16.0)
LIST_TEXT = (MEDIUM, 9.6, 12.6)
LIST_SMALL = (REGULAR, 7.6, 9.6)
GOAL_LABEL = (SEMIBOLD, 7.2)
GOAL_ROW = (REGULAR, 8.2, 10.6)

# The Top goals and advice pages (booklet.py)
BOOK_LABEL = (BOLD, 6.6)                # WHY, DONE WHEN ... tracked, in the accent
BOOK_FIELD = (MEDIUM, 9.4, 12.8)        # the person's own words under each label
GOAL_NUMBER = (EXTRABOLD, 22.0)
GOAL_TITLE = (EXTRABOLD, 14.0)
SMALL_NUMBER = (EXTRABOLD, 17.0)
SMALL_TITLE = (EXTRABOLD, 11.5, 14.0)
STAT = (EXTRABOLD, 17.0)
STAT_LABEL = (SEMIBOLD, 6.8)
TASK_ROW = (REGULAR, 8.2, 10.4)
META = (SEMIBOLD, 7.6)
TIP_TITLE = (BOLD, 10.5, 13.0)
TIP_TEXT = (MEDIUM, 8.8, 12.2)
TIP_QUOTE = (REGULAR, 8.2, 11.0)
