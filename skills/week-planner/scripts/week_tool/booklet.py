"""The pages after the board: Top goals (each goal in the person's own words, its week counted from the
cards) and the advice page (the AI's tips, each showing the words it came from).

Measuring and painting share one path: every function takes a canvas, or None to measure only, so the
fit checks and the drawing can never disagree. A page that does not fit is refused, never squeezed.
"""

from . import pages, theme
from .layout import MARGIN, PAGE_H, PAGE_W
from .model import day_name, hours_text

TOP = PAGE_H - 118.0                    # under the title and summary line
BOTTOM = 56.0                           # above the footer
WIDTH = PAGE_W - 2 * MARGIN
GAP = 12.0
PAD = 14.0
HEAD_H = 40.0                           # the #1 goal's band
TASK_ROWS = 8                           # the #1 goal lists this many of its cards, then "and N more"
FIELDS = (("WHY", "why"), ("DONE WHEN", "done_when"), ("WHAT COULD STOP ME", "risk"), ("FIRST STEP", "first_step"))
RESULTS = {"reached": "REACHED", "close": "CLOSE", "not yet": "NOT YET"}
NOTICE = "Written from what you said while planning. Nothing here is on your board. Use what helps, skip the rest."


# ------------------------------------------------------------------ the pages

def goals_page(c, plan, brand, number, total):
    _head(c, plan, brand, "Top goals", "TOP GOALS")
    _goals(c, plan, [])
    pages._footer(c, plan, brand, number, total)


def advice_page(c, plan, brand, number, total):
    _head(c, plan, brand, "Advice for your week", "ADVICE")
    _advice(c, plan, [])
    pages._footer(c, plan, brand, number, total)


def check(plan):
    """Every word fits and each page holds what it is given."""
    problems = []
    for wanted, lay_out, name, hint in (
            (plan.goal_page, _goals, "Top goals", "Shorten a goal's why, done-when, risk or first step"),
            (plan.advice, _advice, "advice", "Keep fewer tips, or shorten them")):
        if not wanted:
            continue
        bad = []
        lowest = lay_out(None, plan, bad)
        for text in sorted(set(bad)):
            problems.append('A single word in "%s" is too wide for the %s page. Add a space or shorten it.' % (text, name))
        if lowest < BOTTOM:
            problems.append("The %s page is too full. %s." % (name, hint))
    return problems


def _head(c, plan, brand, title, tag):
    pages._rail(c, plan, brand, tag)
    pages._title(c, title, PAGE_H - 82.0)
    c.setFillColor(theme.INK_SOFT)
    c.setFont(theme.MEDIUM, 9.5)
    c.drawString(MARGIN, PAGE_H - 98.0, pages.summary_line(plan))


# ------------------------------------------------------------------ Top goals

def _goals(c, plan, bad):
    """The #1 goal across the page, then goals 2 and 3 side by side. Returns the lowest y reached."""
    goals = plan.goal_details
    y = TOP - _main_goal(c, plan, goals[0], TOP, bad)
    rest = list(enumerate(goals[1:], 2))
    if rest:
        y -= GAP
        w = (WIDTH - GAP) / 2.0
        h = max(_small_goal(None, plan, n, g, 0.0, y, w, bad) for n, g in rest)
        for i, (n, g) in enumerate(rest):
            _small_goal(c, plan, n, g, MARGIN + i * (w + GAP), y, w, bad, h)
        y -= h
    return y


def _main_goal(c, plan, goal, top, bad):
    """One wide card: the goal in a band, then its fields in two stacks and its week on the right."""
    week = pages.goal_week(plan, goal)
    stacks = [s for s in ([f for f in FIELDS[:2] if getattr(goal, f[1])],
                          [f for f in FIELDS[2:] if getattr(goal, f[1])]) if s]
    shares = [1.0] * len(stacks) + ([1.15] if week else [])
    unit = WIDTH / sum(shares) if shares else 0.0
    heights = [sum(_field(None, goal, f, 0.0, 0.0, unit, bad) for f in s) for s in stacks]
    if week:
        heights.append(_week(None, plan, week, 0.0, 0.0, unit * 1.15, bad))
    body = max(heights) if heights else 0.0
    h = HEAD_H + body
    badge = _badge_text(plan, goal, True)
    room = WIDTH - 46.0 - PAD - (_badge_w(badge) + 10.0 if badge else 0.0)
    if theme.width(goal.text, *theme.GOAL_TITLE) > room:
        bad.append(goal.text)
    if c is None:
        return h

    x, bottom = MARGIN, top - h
    _card(c, x, bottom, WIDTH, h)
    c.saveState()
    path = c.beginPath()
    path.roundRect(x, bottom, WIDTH, h, 10)
    c.clipPath(path, stroke=0, fill=0)
    c.setFillColor(theme.GOAL_BG)
    c.rect(x, top - HEAD_H, WIDTH, HEAD_H, stroke=0, fill=1)
    c.restoreState()
    _card(c, x, bottom, WIDTH, h, fill=False)
    if body:
        c.setStrokeColor(theme.TAG_LINE)
        c.line(x, top - HEAD_H, x + WIDTH, top - HEAD_H)
    c.setFillColor(theme.ACCENT)
    c.setFont(*theme.GOAL_NUMBER)
    c.drawString(x + 18.0, top - 28.5, "1")
    c.setFillColor(theme.INK)
    c.setFont(*theme.GOAL_TITLE)
    c.drawString(x + 46.0, top - 25.0, goal.text)
    if badge:
        _badge(c, badge, x + WIDTH - PAD - _badge_w(badge), top - HEAD_H / 2.0 - 7.5, goal.result)

    cx = x
    for n, stack in enumerate(stacks):
        y = top - HEAD_H
        for i, field in enumerate(stack):
            if i:
                c.setStrokeColor(theme.LINE_SOFT)
                c.line(cx, y, cx + unit, y)
            y -= _field(c, goal, field, cx, y, unit, bad)
        cx += unit
        c.setStrokeColor(theme.LINE_SOFT)
        if n < len(stacks) - 1 or week:
            c.line(cx, top - HEAD_H, cx, bottom)
    if week:
        _week(c, plan, week, cx, top - HEAD_H, unit * 1.15, bad)
    return h


def _field(c, goal, field, x, top, w, bad):
    """A label in small blue capitals and the person's words under it."""
    label, key = field
    font, size, lead = theme.BOOK_FIELD
    lines = _lines(getattr(goal, key), font, size, w - 2 * PAD, bad)
    h = 12.0 + 7.0 + 6.0 + len(lines) * lead + 8.0
    if c is not None:
        pages._tracked(c, label, x + PAD, top - 19.0, theme.BOOK_LABEL[0], theme.BOOK_LABEL[1], theme.ACCENT, 1.2)
        c.setFillColor(theme.INK)
        c.setFont(font, size)
        for n, line in enumerate(lines):
            c.drawString(x + PAD, top - 34.0 - n * lead, line)
    return h


def _week(c, plan, week, x, top, w, bad):
    """THIS WEEK: tasks, hours and days counted from the cards; in a review, a done bar; then the cards."""
    font, size, lead = theme.TASK_ROW
    hours_w = 34.0
    mark = 12.0 if plan.reviewed else 0.0
    room = w - 2 * PAD - 30.0 - hours_w - mark
    shown = week["cards"][:TASK_ROWS]
    rows = [(d, i, _lines(i.title, font, size, room, bad)) for d, i in shown]
    more = len(week["cards"]) - len(shown)
    y = top - 19.0                                   # the label's baseline
    stats_y = y - 25.0
    bar_y = stats_y - 24.0
    list_top = (bar_y - 22.0) if plan.reviewed else (stats_y - 18.0)
    h = (top - list_top) + sum(len(r) * lead + 5.0 for _, _, r in rows) + (lead + 4.0 if more else 0.0) + 10.0
    if c is None:
        return h

    pages._tracked(c, "THIS WEEK", x + PAD, y, theme.BOOK_LABEL[0], theme.BOOK_LABEL[1], theme.ACCENT, 1.2)
    sx = x + PAD
    for value, label in ((str(week["tasks"]), "task" if week["tasks"] == 1 else "tasks"),
                         (hours_text(week["hours"]).replace(" h", ""), "hours" if week["hours"] >= 1 else "time"),
                         (week["span"], "days")):
        c.setFillColor(theme.INK)
        c.setFont(*theme.STAT)
        c.drawString(sx, stats_y, value)
        c.setFillColor(theme.INK_SOFT)
        c.setFont(*theme.STAT_LABEL)
        c.drawString(sx, stats_y - 10.0, label)
        sx += max(theme.width(value, *theme.STAT), 24.0) + 18.0
    if plan.reviewed:
        bw = w - 2 * PAD
        c.setFillColor(theme.LINE)
        c.roundRect(x + PAD, bar_y, bw, 6.0, 3.0, stroke=0, fill=1)
        if week["done"]:
            c.setFillColor(theme.ACCENT)
            c.roundRect(x + PAD, bar_y, bw * week["done"] / week["tasks"], 6.0, 3.0, stroke=0, fill=1)
        c.setFillColor(theme.INK_SOFT)
        c.setFont(*theme.STAT_LABEL)
        c.drawString(x + PAD, bar_y - 11.0, "%d of %d done" % (week["done"], week["tasks"]))
    y = list_top
    c.setStrokeColor(theme.LINE_SOFT)
    c.line(x + PAD, y, x + w - PAD, y)
    for day, item, lines in rows:
        row_h = len(lines) * lead + 5.0
        base = y - 4.0 - size * 0.8
        pages._tracked(c, day_name(day.date).split()[0].upper(), x + PAD, base, theme.BOLD, 6.4, theme.INK_FAINT, 1.0)
        c.setFillColor(theme.INK_SOFT if item.done else theme.INK)
        c.setFont(font, size)
        for n, line in enumerate(lines):
            c.drawString(x + PAD + 30.0, base - n * lead, line)
        c.setFillColor(theme.INK_SOFT)
        c.drawRightString(x + w - PAD - mark, base, hours_text(item.hours))
        if plan.reviewed:
            pages._mark(c, x + w - PAD - 4.4, base + 2.8, item.done)
        y -= row_h
        c.setStrokeColor(theme.LINE_SOFT)
        c.line(x + PAD, y, x + w - PAD, y)
    if more:
        c.setFillColor(theme.INK_FAINT)
        c.setFont(*theme.META)
        c.drawString(x + PAD + 30.0, y - 4.0 - size * 0.8, "and %d more" % more)
    return h


def _small_goal(c, plan, number, goal, x, top, w, bad, h=None):
    """Goals 2 and 3: the goal, its fields stacked, and its week in one counted line."""
    tfont, tsize, tlead = theme.SMALL_TITLE
    font, size, lead = theme.BOOK_FIELD
    indent = PAD + 26.0
    badge = _badge_text(plan, goal, False)
    room = w - indent - PAD - (_badge_w(badge) + 8.0 if badge else 0.0)
    title = _lines(goal.text, tfont, tsize, room, bad)
    fields = [(label, _lines(getattr(goal, key), font, size, w - indent - PAD, bad))
              for label, key in FIELDS if getattr(goal, key)]
    week = [text for label, text in pages.goal_rows(plan, goal) if label == "This week"]
    need = PAD + len(title) * tlead + sum(14.0 + len(lines) * lead for _, lines in fields) \
        + (16.0 if week else 0.0) + PAD
    if c is None:
        return need
    h = h or need
    _card(c, x, top - h, w, h)
    c.setFillColor(theme.ACCENT)
    c.setFont(*theme.SMALL_NUMBER)
    c.drawString(x + PAD, top - PAD - 13.0, str(number))
    if badge:
        _badge(c, badge, x + w - PAD - _badge_w(badge), top - PAD - 12.0, goal.result)
    c.setFillColor(theme.INK)
    c.setFont(tfont, tsize)
    y = top - PAD - 10.5
    for line in title:
        c.drawString(x + indent, y, line)
        y -= tlead
    for label, lines in fields:
        y -= 4.0
        pages._tracked(c, label, x + indent, y, theme.BOOK_LABEL[0], theme.BOOK_LABEL[1], theme.ACCENT, 1.2)
        y -= 10.0 + size * 0.2
        c.setFillColor(theme.INK)
        c.setFont(font, size)
        for line in lines:
            c.drawString(x + indent, y, line)
            y -= lead
    if week:
        c.setFillColor(theme.INK_SOFT)
        c.setFont(*theme.META)
        c.drawString(x + indent, y - 6.0, "This week  ·  " + week[0])
    return h


def _badge_text(plan, goal, main):
    """The person's own verdict in a review; on the #1 goal of a plan, a quiet marker of its rank."""
    if goal.result:
        return RESULTS[goal.result]
    return "THIS WEEK'S #1" if main and not plan.reviewed else ""


def _badge_w(text):
    return theme.tracked_width(text, theme.BOLD, 6.2, 1.2) + 16.0


def _badge(c, text, x, y, result):
    """Reached is solid blue; close is pale blue; not yet is quiet grey. Red stays for waiting on you."""
    w = _badge_w(text)
    fill, stroke, ink = {"reached": (theme.ACCENT, theme.ACCENT, theme.WHITE),
                         "not yet": (theme.WHITE, theme.BOX_STROKE, theme.INK_SOFT)}.get(
        result, (theme.TAG_BG, theme.TAG_LINE, theme.ACCENT))
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.6)
    c.roundRect(x, y, w, 15.0, 7.5, stroke=1, fill=1)
    pages._tracked(c, text, x + 8.0, y + 5.2, theme.BOLD, 6.2, ink, 1.2)


# ------------------------------------------------------------------ advice

def _advice(c, plan, bad):
    """A notice that this page is the AI's, then the tips two by two; an odd last tip spans the page."""
    y = TOP
    if c is not None:
        c.setFillColor(theme.SPACE)
        c.setStrokeColor(theme.LINE_SOFT)
        c.setLineWidth(0.6)
        c.roundRect(MARGIN, y - 24.0, WIDTH, 24.0, 8, stroke=1, fill=1)
        label_w = pages._tracked(c, "FROM THE AI", MARGIN + 12.0, y - 15.0, theme.BOLD, 6.6, theme.ACCENT, 1.2)
        c.setFillColor(theme.INK_SOFT)
        c.setFont(theme.MEDIUM, 8.4)
        c.drawString(MARGIN + 24.0 + label_w, y - 15.2, NOTICE)
    y -= 24.0 + GAP
    tips = plan.advice
    half = (WIDTH - GAP) / 2.0
    i = 0
    while i < len(tips):
        row = [(tips[i], WIDTH)] if i == len(tips) - 1 else [(tips[i], half), (tips[i + 1], half)]
        h = max(_tip(None, t, i + n + 1, 0.0, y, w, bad) for n, (t, w) in enumerate(row))
        for n, (tip, w) in enumerate(row):
            _tip(c, tip, i + n + 1, MARGIN + n * (half + GAP), y, w, bad, h)
        y -= h + GAP
        i += len(row)
    return y + GAP


def _tip(c, tip, number, x, top, w, bad, h=None):
    tfont, tsize, tlead = theme.TIP_TITLE
    font, size, lead = theme.TIP_TEXT
    qfont, qsize, qlead = theme.TIP_QUOTE
    title = _lines(tip.title, tfont, tsize, w - 2 * PAD - 20.0, bad)
    text = _lines(tip.text, font, size, w - 2 * PAD, bad)
    quote = _lines('"%s"' % tip.because, qfont, qsize, w - 2 * PAD - 10.0, bad)
    check = tip.check.upper()
    if check and _badge_w(check) > w - 2 * PAD:
        bad.append(tip.check)
    need = PAD + len(title) * tlead + 4.0 + len(text) * lead + 6.0 + 10.0 + len(quote) * qlead + 4.0 \
        + (21.0 if check else 0.0) + PAD - 4.0
    if c is None:
        return need
    h = h or need
    _card(c, x, top - h, w, h)
    c.setFillColor(theme.ACCENT)
    c.setFont(theme.EXTRABOLD, 13.0)
    c.drawString(x + PAD, top - PAD - 9.5, str(number))
    y = top - PAD - 9.0
    c.setFillColor(theme.INK)
    c.setFont(tfont, tsize)
    for line in title:
        c.drawString(x + PAD + 20.0, y, line)
        y -= tlead
    y -= 4.0
    c.setFont(font, size)
    for line in text:
        c.drawString(x + PAD, y, line)
        y -= lead
    y -= 6.0
    block = 10.0 + len(quote) * qlead
    c.setFillColor(theme.TAG_LINE)
    c.rect(x + PAD, y - block + 7.0, 2.0, block, stroke=0, fill=1)
    pages._tracked(c, "BECAUSE YOU SAID", x + PAD + 10.0, y, theme.BOLD, 6.0, theme.ACCENT, 1.1)
    y -= 11.0
    c.setFillColor(theme.INK_SOFT)
    c.setFont(qfont, qsize)
    for line in quote:
        c.drawString(x + PAD + 10.0, y, line)
        y -= qlead
    if check:
        _badge(c, check, x + PAD, y - 13.0, "not yet")
    return h


# ------------------------------------------------------------------ shared

def _card(c, x, y, w, h, fill=True):
    c.setFillColor(theme.WHITE)
    c.setStrokeColor(theme.BOX_STROKE)
    c.setLineWidth(0.7)
    c.roundRect(x, y, w, h, 10, stroke=1, fill=1 if fill else 0)


def _lines(text, font, size, room, bad):
    lines = theme.wrap(text, font, size, room)
    if lines is None:
        bad.append(text)
        return [text]
    return lines
