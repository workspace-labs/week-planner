"""Where everything on the Week Board page goes: one column per day, one card per item.

Pure geometry: it measures text but never draws, so tests can check the boxes without a PDF.
Coordinates are PDF points, y grows upward. A day with more than fits is refused, never squeezed.
"""

from . import theme
from .model import PlanError, day_name, hours_text

PAGE_W, PAGE_H = 841.89, 595.28        # A4 landscape
MARGIN = 30.0
GAP = 8.0                              # between day columns
MAX_COL_W = 200.0                      # a weekend's 2 columns stay card-shaped, centred
BOARD_BOTTOM = 52.0                    # the footer sits below this
COL_PAD = 6.0
HEADER_H = 42.0                        # weekday + date number at the top of a column
TOTAL_H = 18.0                         # "2.5 of 3 h" at the bottom of a column
CARD_GAP = 6.0
BAR_W = 3.0
TEXT_LEFT = 10.0                       # from the card's left edge, past the bar
TEXT_RIGHT = 6.0
MARK_ROOM = 10.0                       # the done tick or open ring, only on a reviewed plan
PAD_TOP, PAD_BOTTOM = 7.0, 6.5
TITLE_MOST_LINES = 3


class Card(object):
    def __init__(self, item, x, y, w, h, title_lines, detail_lines):
        self.item, self.x, self.y, self.w, self.h = item, x, y, w, h     # (x, y) is the bottom-left corner
        self.title_lines, self.detail_lines = title_lines, detail_lines


class Column(object):
    def __init__(self, day, x, w, top, bottom, cards, total_text):
        self.day, self.x, self.w, self.top, self.bottom = day, x, w, top, bottom
        self.cards, self.total_text = cards, total_text


def board_top(plan):
    """The goal band takes a row under the title when there is a #1 goal."""
    return PAGE_H - (136.0 if plan.goals else 110.0)


def lay_out(plan):
    """Returns the columns. Raises PlanError listing every day or word that does not fit."""
    n = len(plan.days)
    col_w = min(MAX_COL_W, (PAGE_W - 2 * MARGIN - GAP * (n - 1)) / n)
    left = (PAGE_W - (col_w * n + GAP * (n - 1))) / 2.0
    top, problems, columns = board_top(plan), [], []
    for i, day in enumerate(plan.days):
        x = left + i * (col_w + GAP)
        cards = _cards(day, x + COL_PAD, top - HEADER_H, col_w - 2 * COL_PAD, plan.reviewed, problems)
        lowest = cards[-1].y if cards else top - HEADER_H
        if lowest < BOARD_BOTTOM + TOTAL_H:
            problems.append("%s has more than fits in its column. Move an item to another day, or shorten titles."
                            % day_name(day.date))
        total = "Day off" if day.off else "%s of %s" % (_short(day.planned), hours_text(day.free_hours))
        columns.append(Column(day, x, col_w, top, BOARD_BOTTOM, cards, total))
    if problems:
        raise PlanError(problems)
    return columns


def detail_text(item):
    """The quiet second line of a card: project · stage or kind · time."""
    parts = [item.project] if item.project else []
    if item.kind == "decision":
        parts.append("your decision")
    elif item.kind == "personal":
        parts.append("personal")
    elif item.stage:
        parts.append(item.stage)
    parts.append(hours_text(item.hours).replace(" ", "\u00a0"))
    return " · ".join(parts)


def _cards(day, x, y_top, w, reviewed, problems):
    room = w - TEXT_LEFT - TEXT_RIGHT - (MARK_ROOM if reviewed else 0)
    font, size, lead = theme.CARD_TITLE
    dfont, dsize, dlead = theme.CARD_DETAIL
    cards, y = [], y_top
    for item in day.items:
        title = theme.wrap(item.title, font, size, room)
        detail = theme.wrap(detail_text(item), dfont, dsize, room)
        if title is None or detail is None:
            problems.append('%s: a single word in "%s" is too wide for its card. Add a space or shorten it.'
                            % (day_name(day.date), item.title))
            continue
        if len(title) > TITLE_MOST_LINES:
            problems.append('%s: "%s" needs %d lines in its card (at most %d). Shorten the title.'
                            % (day_name(day.date), item.title, len(title), TITLE_MOST_LINES))
            continue
        h = PAD_TOP + len(title) * lead + 1.5 + len(detail) * dlead + PAD_BOTTOM
        cards.append(Card(item, x, y - h, w, h, title, detail))
        y -= h + CARD_GAP
    return cards


def _short(hours):
    """'2.5' for the column total, so '2.5 of 3 h' reads once."""
    return "0" if hours == 0 else hours_text(hours).replace(" h", "") if hours >= 1 else hours_text(hours)
