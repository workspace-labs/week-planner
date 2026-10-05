"""Draws the PDF: page 1 is the Week Board, page 2 (when there is something to put on it) is the focus
page: the top goals, what is waiting on you, and what carried over or moves on.

Geometry for the board comes from layout.py; this file only paints it.
"""

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from . import VERSION, theme
from .layout import (BAR_W, MARGIN, MARK_ROOM, PAD_TOP, PAGE_H, PAGE_W, TEXT_LEFT, TEXT_RIGHT, board_top)
from .model import PlanError, day_name, hours_text

FOCUS_TOP = PAGE_H - 160.0
FOCUS_BOTTOM = 56.0
SECTION_GAP = 26.0
BELOW_GAP = 16.0                        # between the board and the focus lists drawn under it
SCORE_H = 26.0
ROW_LABEL_W = 54.0                      # "Done when" and its siblings, before the goal's own words
_logos = {}


# ------------------------------------------------------------------ the whole PDF

def build(plan, columns, brand, out_path):
    """Draws the PDF and returns how many pages it has: one when the focus fits under the board."""
    sections = focus_sections(plan)
    inline = bool(sections) and focus_fits_below(plan, columns)
    total = 2 if sections and not inline else 1
    c = canvas.Canvas(out_path, pagesize=(PAGE_W, PAGE_H))
    c.setTitle("%s - %s" % (plan.title, date_range(plan)))
    c.setAuthor(brand.name)
    c.setCreator("week-planner %s" % VERSION)
    _board_page(c, plan, columns, brand, total)
    if inline:
        top = columns[0].bottom - BELOW_GAP
        if plan.reviewed:
            _score(c, plan, top - SCORE_H)
            top -= SCORE_H + BELOW_GAP
        _sections(c, sections, focus_room(plan), top - 8.0)
    elif sections:
        c.showPage()
        _focus_page(c, plan, sections, brand, total)
    c.showPage()
    c.save()
    return total


def date_range(plan):
    first, last = plan.days[0].date, plan.days[-1].date
    if first == last:
        return "%s %d" % (day_name(first), first.year)
    return "%s – %s %d" % (day_name(first), day_name(last), last.year)


def summary_line(plan):
    work = plan.work
    planned = sum(day.planned for day in plan.days)     # buffer time included, as in every column total
    free = sum(d.free_hours for d in plan.days if not d.off)
    text = "%s  ·  %s planned of %s free" % (date_range(plan), hours_text(planned), hours_text(free))
    if plan.reviewed:
        text += "  ·  %d of %d done" % (sum(1 for i in work if i.done), len(work))
    return text


def tag_text(plan):
    if plan.reviewed:
        return "WEEK REVIEW"
    return "WEEKEND PLAN" if plan.mode == "weekend" else "WEEK PLAN"


# ------------------------------------------------------------------ page 1: the Week Board

def _board_page(c, plan, columns, brand, total):
    _rail(c, plan, brand)
    _title(c, plan.title, PAGE_H - 82.0)
    c.setFillColor(theme.INK_SOFT)
    c.setFont(theme.MEDIUM, 9.5)
    c.drawString(MARGIN, PAGE_H - 98.0, summary_line(plan))
    if plan.goals:
        _goal_band(c, plan.goals[0], board_top(plan) + 10.0)
    for column in columns:
        _column(c, column, plan.reviewed)
    _footer(c, plan, brand, 1, total)


def _goal_band(c, goal, y):
    h = 21.0
    c.setFillColor(theme.GOAL_BG)
    c.setStrokeColor(theme.TAG_LINE)
    c.setLineWidth(0.6)
    c.roundRect(MARGIN, y, PAGE_W - 2 * MARGIN, h, 8, stroke=1, fill=1)
    label_w = _tracked(c, "#1 GOAL", MARGIN + 12.0, y + 7.6, theme.BOLD, 6.8, theme.ACCENT, 1.2)
    c.setFillColor(theme.INK)
    c.setFont(theme.SEMIBOLD, 9.6)
    c.drawString(MARGIN + 12.0 + label_w + 10.0, y + 7.2, goal)


def _column(c, column, reviewed):
    c.setFillColor(theme.SPACE)
    c.setStrokeColor(theme.LINE_SOFT)
    c.setLineWidth(0.6)
    c.roundRect(column.x, column.bottom, column.w, column.top - column.bottom, 10, stroke=1, fill=1)
    name = day_name(column.day.date).split()[0].upper()
    _tracked(c, name, column.x + 9.0, column.top - 14.0, theme.DAY_NAME[0], theme.DAY_NAME[1], theme.INK_FAINT, 1.4)
    c.setFillColor(theme.INK)
    c.setFont(*theme.DAY_NUMBER)
    number = str(column.day.date.day)
    c.drawString(column.x + 9.0, column.top - 33.0, number)
    c.setFillColor(theme.INK_FAINT)
    c.setFont(theme.MEDIUM, 7.4)
    c.drawString(column.x + 12.0 + theme.width(number, *theme.DAY_NUMBER), column.top - 33.0,
                 day_name(column.day.date).split()[2])
    for card in column.cards:
        _card(c, card, reviewed)
    if column.day.off and not column.cards:
        c.setFillColor(theme.INK_FAINT)
        c.setFont(theme.MEDIUM, 8.0)
        c.drawString(column.x + 9.0, column.top - 56.0, "Rest day")
    c.setFillColor(theme.INK_FAINT)
    c.setFont(theme.SEMIBOLD, 7.2)
    c.drawString(column.x + 9.0, column.bottom + 7.5, column.total_text)


def _card(c, card, reviewed):
    item = card.item
    if item.kind == "decision":
        fill, stroke = theme.RED_BG, theme.RED_LINE
    else:
        fill, stroke = theme.WHITE, theme.BOX_STROKE
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.6)
    if item.kind == "buffer":
        _hatched(c, card)
    else:
        c.roundRect(card.x, card.y, card.w, card.h, 6, stroke=1, fill=1)
        bar = theme.BAR["decision"] if item.kind == "decision" else \
            theme.BAR["personal"] if item.kind == "personal" else theme.BAR[item.stage]
        c.setFillColor(bar)
        c.roundRect(card.x, card.y + 5.0, BAR_W, card.h - 10.0, 1.5, stroke=0, fill=1)

    font, size, lead = theme.CARD_TITLE
    dfont, dsize, dlead = theme.CARD_DETAIL
    x, top = card.x + TEXT_LEFT, card.y + card.h - PAD_TOP
    c.setFillColor(theme.INK_SOFT if item.kind == "buffer" else theme.INK)
    c.setFont(font, size)
    for n, line in enumerate(card.title_lines):
        c.drawString(x, top - size * 0.78 - n * lead, line)
    top -= len(card.title_lines) * lead + 1.5
    c.setFillColor(theme.INK_SOFT)
    c.setFont(dfont, dsize)
    for n, line in enumerate(card.detail_lines):
        c.drawString(x, top - dsize * 0.78 - n * dlead, line)
    if reviewed and item.counts:
        _mark(c, card.x + card.w - TEXT_RIGHT - MARK_ROOM / 2.0 + 2.0, card.y + card.h - 10.5, item.done)


def _hatched(c, card):
    c.saveState()
    path = c.beginPath()
    path.roundRect(card.x, card.y, card.w, card.h, 6)
    c.clipPath(path, stroke=0, fill=0)
    c.setFillColor(theme.WHITE)
    c.rect(card.x, card.y, card.w, card.h, stroke=0, fill=1)
    c.setStrokeColor(theme.HATCH)
    c.setLineWidth(0.7)
    step = 5.0
    start = card.x - card.h
    while start < card.x + card.w:
        c.line(start, card.y, start + card.h, card.y + card.h)
        start += step
    c.restoreState()
    c.setStrokeColor(theme.BOX_STROKE)
    c.setDash(2.2, 1.8)
    c.setLineWidth(0.8)
    c.roundRect(card.x, card.y, card.w, card.h, 6, stroke=1, fill=0)
    c.setDash()


def _mark(c, cx, cy, done):
    """A blue tick in a circle for done; a pale empty ring for 'moves to next week'."""
    r = 4.4
    if done:
        c.setFillColor(theme.ACCENT)
        c.circle(cx, cy, r, stroke=0, fill=1)
        c.setStrokeColor(theme.WHITE)
        c.setLineWidth(1.1)
        c.setLineCap(1)
        path = c.beginPath()
        path.moveTo(cx - 2.0, cy + 0.1)
        path.lineTo(cx - 0.6, cy - 1.5)
        path.lineTo(cx + 2.1, cy + 1.6)
        c.drawPath(path, stroke=1, fill=0)
        c.setLineCap(0)
    else:
        c.setStrokeColor(theme.INK_FAINT)
        c.setLineWidth(0.9)
        c.circle(cx, cy, r, stroke=1, fill=0)


# ------------------------------------------------------------------ page 2: focus

def focus_sections(plan):
    """The focus page's sections as (heading, entries); each entry is (marker, text, small). Empty
    sections are left out, and no sections means no second page."""
    sections = []
    if plan.goals:
        sections.append(("TOP GOALS", [(str(n), g.text, goal_rows(plan, g)) for n, g in enumerate(plan.goal_details, 1)]))
    # A decision made this week is no longer waiting; one still open shows here once, not twice.
    waiting = [(d, i) for d, i in plan.decisions if not i.done]
    if waiting:
        later = " · moves to next week" if plan.reviewed else ""
        sections.append(("WAITING ON YOU", [("red", i.title, "%s · %s%s" % (day_name(d.date), hours_text(i.hours), later))
                                            for d, i in waiting]))
    if plan.reviewed:
        # Last week's carry-over that was never put on a day is still open: it moves on too. One that was
        # scheduled is already judged by its card (done, moving, or waiting), so it is not listed again.
        moving = [("ring", i.title, day_name(d.date)) for d, i in plan.unfinished if i.kind != "decision"]
        moving += [("ring", t, "from last week, not planned") for t in plan.unplanned_carry_over]
        if moving:
            sections.append(("MOVES TO NEXT WEEK", moving))
    elif plan.carried_over:
        sections.append(("CARRIED OVER", [("dot", t, "from last week") for t in plan.carried_over]))
    return sections


def goal_rows(plan, goal):
    """The labelled lines under a goal, each only when there is something for it. 'This week' is counted
    from the cards of the goal's project, never typed."""
    rows = [(label, text) for label, text in (("Why", goal.why), ("Done when", goal.done_when)) if text]
    cards = plan.goal_cards(goal)
    if cards:
        work = [i for _, i in cards]
        days = []
        for d, _ in cards:
            name = day_name(d.date).split()[0]
            if name not in days:
                days.append(name)
        if plan.reviewed:
            count = "%d of %d done" % (sum(1 for i in work if i.done), len(work))
        else:
            count = "%d task%s" % (len(work), "" if len(work) == 1 else "s")
        span = days[0] if len(days) == 1 else "%s to %s" % (days[0], days[-1])
        rows.append(("This week", "%s · %s · %s" % (count, hours_text(sum(i.hours for i in work)), span)))
    return rows


def _rows_wrapped(rows, room):
    """Each row's words wrapped beside its label; None when a single word cannot fit."""
    out = []
    for label, text in rows:
        lines = theme.wrap(text, theme.GOAL_ROW[0], theme.GOAL_ROW[1], room - ROW_LABEL_W)
        if lines is None:
            return None
        out.append((label, lines))
    return out


def focus_room(plan):
    n = max(len(focus_sections(plan)), 1)
    return (PAGE_W - 2 * MARGIN - SECTION_GAP * (n - 1)) / n


def check_focus(plan):
    """Every word on the focus page fits its column and every column fits the page."""
    problems = []
    room = focus_room(plan) - 26.0
    for heading, entries in focus_sections(plan):
        y = FOCUS_TOP - 24.0
        for _, text, small in entries:
            lines = theme.wrap(text, theme.LIST_TEXT[0], theme.LIST_TEXT[1], room)
            if lines is None or (isinstance(small, list) and _rows_wrapped(small, room) is None):
                problems.append('A single word in "%s" (or its why or done-when) is too wide for the focus page. '
                                'Add a space or shorten it.' % text)
                continue
            y -= _entry_height(lines, small, room)
        if y < FOCUS_BOTTOM:
            problems.append('The "%s" list is too long for the focus page. Keep fewer, or shorten them.'
                            % heading.capitalize())
    return problems


def focus_height(plan):
    """How tall the focus lists are (and the score, on a review), from the top of their headings."""
    room = focus_room(plan) - 26.0
    tallest = 0.0
    for _, entries in focus_sections(plan):
        h = 24.0
        for _, text, small in entries:
            h += _entry_height(theme.wrap(text, theme.LIST_TEXT[0], theme.LIST_TEXT[1], room) or [text], small, room)
        tallest = max(tallest, h - (10.0 if entries else 0.0))     # no gap is drawn after the last entry
    return tallest + (SCORE_H + BELOW_GAP if plan.reviewed else 0.0)


def focus_fits_below(plan, columns):
    """True when the focus lists fit between the board and the footer, so the plan is one page."""
    return columns[0].bottom - BELOW_GAP - 8.0 - focus_height(plan) >= FOCUS_BOTTOM


def _entry_height(lines, small, room):
    """small is a quiet line of text, or a goal's labelled rows."""
    if isinstance(small, list):
        rows = _rows_wrapped(small, room) or []
        extra = sum(len(r) for _, r in rows) * theme.GOAL_ROW[2] + (4.0 if rows else 0.0)
    else:
        extra = theme.LIST_SMALL[2] if small else 0
    return len(lines) * theme.LIST_TEXT[2] + extra + 10.0


def _focus_page(c, plan, sections, brand, total):
    _rail(c, plan, brand)
    _title(c, "Your focus" if not plan.reviewed else "How the week went", PAGE_H - 82.0)
    c.setFillColor(theme.INK_SOFT)
    c.setFont(theme.MEDIUM, 9.5)
    c.drawString(MARGIN, PAGE_H - 98.0, summary_line(plan))
    if plan.reviewed:
        _score(c, plan, PAGE_H - 140.0)
    _sections(c, sections, focus_room(plan), FOCUS_TOP)
    _footer(c, plan, brand, 2, total)


def _sections(c, sections, w, top):
    """The focus lists side by side, their headings' baseline at top."""
    for n, (heading, entries) in enumerate(sections):
        x = MARGIN + n * (w + SECTION_GAP)
        color = theme.RED if heading == "WAITING ON YOU" else theme.INK_FAINT
        _tracked(c, heading, x, top, theme.BOLD, 7.0, color, 1.4)
        c.setStrokeColor(theme.LINE)
        c.setLineWidth(0.6)
        c.line(x, top - 8.0, x + w, top - 8.0)
        y = top - 24.0
        for marker, text, small in entries:
            lines = theme.wrap(text, theme.LIST_TEXT[0], theme.LIST_TEXT[1], w - 26.0)
            _marker(c, marker, x + 7.0, y + 3.2)
            c.setFillColor(theme.INK)
            c.setFont(theme.LIST_TEXT[0], theme.LIST_TEXT[1])
            yy = y
            for line in lines:
                c.drawString(x + 26.0, yy, line)
                yy -= theme.LIST_TEXT[2]
            if isinstance(small, list):
                yy -= 4.0
                for label, row in _rows_wrapped(small, w - 26.0) or []:
                    c.setFillColor(theme.INK_FAINT)
                    c.setFont(*theme.GOAL_LABEL)
                    c.drawString(x + 26.0, yy + 2.0, label)
                    c.setFillColor(theme.INK_SOFT)
                    c.setFont(theme.GOAL_ROW[0], theme.GOAL_ROW[1])
                    for line in row:
                        c.drawString(x + 26.0 + ROW_LABEL_W, yy + 2.0, line)
                        yy -= theme.GOAL_ROW[2]
            elif small:
                c.setFillColor(theme.INK_FAINT)
                c.setFont(theme.LIST_SMALL[0], theme.LIST_SMALL[1])
                c.drawString(x + 26.0, yy + 2.0, small)
            y -= _entry_height(lines, small, w - 26.0)


def _score(c, plan, y):
    work = plan.work
    done = sum(1 for i in work if i.done)
    c.setFillColor(theme.GOAL_BG)
    c.setStrokeColor(theme.TAG_LINE)
    c.setLineWidth(0.6)
    c.roundRect(MARGIN, y, PAGE_W - 2 * MARGIN, SCORE_H, 9, stroke=1, fill=1)
    label_w = _tracked(c, "SCORE", MARGIN + 12.0, y + 10.0, theme.BOLD, 6.8, theme.ACCENT, 1.2)
    c.setFillColor(theme.INK)
    c.setFont(theme.EXTRABOLD, 12.0)
    text = "%d of %d done" % (done, len(work))
    c.drawString(MARGIN + 22.0 + label_w, y + 8.8, text)
    # a quiet bar beside it: one segment per item, blue when done
    x = MARGIN + 36.0 + label_w + theme.width(text, theme.EXTRABOLD, 12.0)
    seg = min(14.0, (PAGE_W - MARGIN - 12.0 - x) / max(len(work), 1) - 2.0)
    for i, item in enumerate(sorted(work, key=lambda it: not it.done)):
        c.setFillColor(theme.ACCENT if item.done else theme.LINE)
        c.roundRect(x + i * (seg + 2.0), y + 10.0, seg, 6.0, 2, stroke=0, fill=1)


def _marker(c, marker, cx, cy):
    if marker == "red":
        c.setFillColor(theme.RED)
        c.circle(cx, cy, 3.4, stroke=0, fill=1)
    elif marker == "ring":
        _mark(c, cx, cy, False)
    elif marker == "dot":
        c.setFillColor(theme.INK_FAINT)
        c.circle(cx, cy, 2.6, stroke=0, fill=1)
    else:                                               # a goal's number
        c.setFillColor(theme.ACCENT)
        c.setFont(theme.EXTRABOLD, 15.0)
        c.drawCentredString(cx, cy - 4.6, marker)


# ------------------------------------------------------------------ page furniture

def _rail(c, plan, brand):
    y, tile = PAGE_H - 30.0, 16.0
    x = MARGIN
    if brand.logo:
        if brand.logo not in _logos:
            _logos[brand.logo] = ImageReader(brand.logo)
        c.setFillColor(theme.WHITE)
        c.setStrokeColor(theme.LINE)
        c.setLineWidth(0.6)
        c.roundRect(x, y - tile / 2.0, tile, tile, tile * 0.24, stroke=1, fill=1)
        inset = tile * 0.08
        c.drawImage(_logos[brand.logo], x + inset, y - tile / 2.0 + inset, tile - 2 * inset, tile - 2 * inset,
                    mask="auto", preserveAspectRatio=True, anchor="c")
        x += tile + 8.0
    _accent_line(c, brand.name, brand.accent, x, y - 3.4, theme.BOLD, 9.6)
    tag = tag_text(plan)
    font, size, tracking = theme.BOLD, 6.2, 1.2
    w = theme.tracked_width(tag, font, size, tracking) + 16.0
    c.setFillColor(theme.TAG_BG)
    c.setStrokeColor(theme.TAG_LINE)
    c.setLineWidth(0.6)
    c.roundRect(PAGE_W - MARGIN - w, y - 7.5, w, 15.0, 7.5, stroke=1, fill=1)
    _tracked(c, tag, PAGE_W - MARGIN - w + 8.0, y - 2.3, font, size, theme.ACCENT, tracking)
    c.setStrokeColor(theme.LINE_SOFT)
    c.line(MARGIN, PAGE_H - 46.0, PAGE_W - MARGIN, PAGE_H - 46.0)


def _title(c, text, y):
    words = text.split()
    _accent_line(c, text, words[-1] if len(words) > 1 else "", MARGIN, y, theme.EXTRABOLD, 24.0)


def _footer(c, plan, brand, page, total):
    c.setStrokeColor(theme.LINE_SOFT)
    c.setLineWidth(0.6)
    c.line(MARGIN, 40.0, PAGE_W - MARGIN, 40.0)
    c.setFillColor(theme.INK_FAINT)
    c.setFont(theme.REGULAR, 7)
    number = "Page %d of %d" % (page, total)
    room = PAGE_W - 2 * MARGIN - theme.width(number, theme.REGULAR, 7) - 16.0
    c.drawString(MARGIN, 28.0, footer_left(plan, brand, room))
    c.drawRightString(PAGE_W - MARGIN, 28.0, number)


def footer_left(plan, brand, room):
    """The footer's left words, never running into the page number: the tool's version is dropped first,
    then the website. The title (40 characters at most) and the dates always fit."""
    base = "%s — %s" % (plan.title, date_range(plan))
    version = "  ·  week-planner %s" % VERSION
    site = "  ·  %s" % brand.website if brand.website else ""
    for text in (base + version + site, base + site, base):
        if theme.width(text, theme.REGULAR, 7) <= room:
            return text
    return base


def _tracked(c, text, x, y, font, size, color, tracking):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, text, charSpace=tracking)
    return theme.tracked_width(text, font, size, tracking)


def _accent_line(c, text, accent, x, y, font, size):
    """One line with one whole word in the accent colour."""
    c.setFont(font, size)
    for n, word in enumerate(text.split(" ")):
        piece = word if n == 0 else " " + word
        c.setFillColor(theme.ACCENT if accent and word == accent else theme.INK)
        c.drawString(x, y, piece)
        x += theme.width(piece, font, size)


def preflight(plan, brand):
    """Words that would not fit the fixed places: the goal band, the title, the footer."""
    problems = check_focus(plan)
    room = PAGE_W - 2 * MARGIN
    if plan.goals and theme.width(plan.goals[0], theme.SEMIBOLD, 9.6) > room - 90.0:
        problems.append("The #1 goal is too long for its band. Shorten it.")
    if theme.width(plan.title, theme.EXTRABOLD, 24.0) > room:
        problems.append("The title is too long for the page. Shorten it.")
    return problems
