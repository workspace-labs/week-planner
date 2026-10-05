"""Reads a plan file and checks it. Every problem becomes one plain sentence saying what to change.

The format is in references/plan-format.md. Nothing here draws; layout.py and pages.py do.
"""

import datetime
import json
import math

from . import theme

KINDS = ("task", "decision", "personal", "buffer")
STAGES = ("idea", "plan", "checklist", "active", "review")
MODES = ("week", "weekend")
_PLAN_KEYS = {"title", "mode", "goals", "carried_over", "days"}
_DAY_KEYS = {"date", "free_hours", "off", "items"}
_ITEM_KEYS = {"title", "kind", "stage", "project", "hours", "done", "from_last_week"}
WEEKEND_MOST_TASKS = 3


class PlanError(Exception):
    def __init__(self, problems):
        Exception.__init__(self, "; ".join(problems))
        self.problems = problems


class Item(object):
    def __init__(self, title, kind, stage, project, hours, done, from_last_week=""):
        self.title, self.kind, self.stage, self.project = title, kind, stage, project
        self.hours = hours        # a multiple of a quarter hour
        self.done = done          # None until the week is reviewed, then True or False
        self.from_last_week = from_last_week   # the carried_over words this card plans, when its title differs

    @property
    def counts(self):
        """Buffer time is room, not work: it is never scored or carried over."""
        return self.kind != "buffer"


class Day(object):
    def __init__(self, date, free_hours, off, items):
        self.date, self.free_hours, self.off, self.items = date, free_hours, off, items

    @property
    def planned(self):
        return sum(item.hours for item in self.items)


class Plan(object):
    def __init__(self, title, mode, goals, carried_over, days):
        self.title, self.mode, self.goals, self.carried_over, self.days = title, mode, goals, carried_over, days

    @property
    def work(self):
        return [item for day in self.days for item in day.items if item.counts]

    @property
    def reviewed(self):
        return any(item.done is not None for item in self.work)

    @property
    def decisions(self):
        return [(day, item) for day in self.days for item in day.items if item.kind == "decision"]

    @property
    def unfinished(self):
        return [(day, item) for day in self.days for item in day.items if item.counts and item.done is False]

    @property
    def unplanned_carry_over(self):
        """Carried-over items no card plans this week."""
        taken = set(same_words(self.carry_source(item)) for item in self.work)
        return [text for text in self.carried_over if same_words(text) not in taken]

    def carry_source(self, item):
        """The one carried-over item a card plans: the one it names in "from_last_week", else the one its
        title repeats, else "". The link wins, so a linked card never also plans an item that happens to
        share its title. Buffer time plans nothing."""
        if not item.counts:
            return ""
        entries = dict((same_words(text), text) for text in self.carried_over)
        return entries.get(same_words(item.from_last_week or item.title), "")


def load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as err:
        raise PlanError(["The plan file could not be read: %s." % err])
    return parse(data)


def parse(data):
    problems = []
    if not isinstance(data, dict):
        raise PlanError(['The plan file must be one JSON object with "days" in it.'])
    _unknown(data, _PLAN_KEYS, "The plan", problems)

    mode = data.get("mode", "week")
    if mode not in MODES:
        problems.append('"mode" must be "week" or "weekend"; it is %s.' % describe(mode))
        mode = "week"
    title = _text(data, "title", 40, "The plan", problems) or ("This weekend" if mode == "weekend" else "This week")
    goals = _texts(data, "goals", 3, 70, problems)
    carried = _texts(data, "carried_over", 8, 70, problems)

    raw_days = data.get("days")
    if not isinstance(raw_days, list) or not raw_days:
        problems.append('"days" must list the days of the plan, from 1 to 7 of them.')
        raise PlanError(problems)
    most = 3 if mode == "weekend" else 7
    if len(raw_days) > most:
        problems.append("A %s plan has at most %d days; this one has %d." % (mode, most, len(raw_days)))

    days = [_day(raw, n, problems) for n, raw in enumerate(raw_days, 1)]
    days = [d for d in days if d]
    _check_dates(days, problems)
    plan = Plan(title, mode, goals, carried, days)
    _check_plan(plan, problems)
    if problems:
        raise PlanError(problems)
    return plan


def _day(raw, number, problems):
    where = "Day %d" % number
    if not isinstance(raw, dict):
        problems.append('%s must be an object with "date", "free_hours" and "items".' % where)
        return None
    _unknown(raw, _DAY_KEYS, where, problems)
    date = None
    try:
        date = datetime.date.fromisoformat(raw.get("date", ""))
        where = day_name(date)
    except (TypeError, ValueError):
        problems.append('%s needs a "date" written YYYY-MM-DD; it is %s.' % (where, describe(raw.get("date"))))
    free = _hours(raw.get("free_hours"), '%s: "free_hours"' % where, problems, allow_zero=True)
    off = raw.get("off", False)
    if not isinstance(off, bool):
        problems.append('%s: "off" must be true or false.' % where)
        off = False
    raw_items = raw.get("items", [])
    if not isinstance(raw_items, list):
        problems.append('%s: "items" must be a list.' % where)
        raw_items = []
    items = [_item(r, "%s, item %d" % (where, n), problems) for n, r in enumerate(raw_items, 1)]
    items = [i for i in items if i]
    if off and items:
        problems.append("%s is a day off but has %d items on it. Move them, or take \"off\" away." % (where, len(items)))
    if free is not None and items and sum(i.hours for i in items) > free:
        problems.append("%s is overfilled: %s planned but only %s free. Move something to another day, "
                        "or raise its free hours." % (where, hours_text(sum(i.hours for i in items)), hours_text(free)))
    if date is None or free is None:
        return None
    return Day(date, free, off, items)


def _item(raw, where, problems):
    if not isinstance(raw, dict):
        problems.append('%s must be an object with a "title" and "hours".' % where)
        return None
    _unknown(raw, _ITEM_KEYS, where, problems)
    kind = raw.get("kind", "task")
    if kind not in KINDS:
        problems.append('%s: "kind" must be one of %s; it is %s.' % (where, ", ".join(KINDS), describe(kind)))
        kind = "task"
    title = _text(raw, "title", 48, where, problems)
    if kind == "buffer":
        title = title or "Buffer"
    elif not title:
        problems.append('%s needs a "title": a few words, verb first ("Send the report").' % where)
    stage = raw.get("stage")
    if stage is not None and (kind not in ("task", "decision") or stage not in STAGES):
        problems.append('%s: "stage" is only for a task or decision, and must be one of %s.' % (where, ", ".join(STAGES)))
        stage = None
    project = _text(raw, "project", 24, where, problems)
    hours = _hours(raw.get("hours"), '%s: "hours"' % where, problems)
    done = raw.get("done")
    if done is not None and (not isinstance(done, bool) or kind == "buffer"):
        problems.append('%s: "done" must be true or false, and buffer time is never marked.' % where)
        done = None
    carried = _text(raw, "from_last_week", 70, where, problems)
    if carried and kind == "buffer":
        problems.append('%s: buffer time is room, not work, so it never takes on "from_last_week".' % where)
        carried = ""
    if hours is None:
        return None
    return Item(title, kind, stage, project, hours, done, carried)


def _check_dates(days, problems):
    for before, after in zip(days, days[1:]):
        if (after.date - before.date).days != 1:
            problems.append("The days must follow one another with none missing or repeated: %s is followed by %s."
                            % (day_name(before.date), day_name(after.date)))
            return


def _check_plan(plan, problems):
    if plan.mode == "week" and len(plan.days) >= 3 and not any(i.kind == "buffer" for d in plan.days for i in d.items):
        problems.append("A week plan keeps at least one buffer slot, because things take longer. "
                        'Add an item with "kind": "buffer" to a day with room.')
    if plan.mode == "weekend":
        tasks = [i for d in plan.days for i in d.items if i.kind in ("task", "decision")]
        if len(tasks) > WEEKEND_MOST_TASKS:
            problems.append("A weekend plan holds at most %d tasks; this one has %d. Keep the most important."
                            % (WEEKEND_MOST_TASKS, len(tasks)))
    seen = set()
    for text in plan.carried_over:
        if same_words(text) in seen:
            problems.append('"carried_over" lists "%s" twice. Keep it once.' % text)
        seen.add(same_words(text))
    for item in plan.work:
        if item.from_last_week and same_words(item.from_last_week) not in seen:
            problems.append('"%s": "from_last_week" must repeat one "carried_over" entry word for word; '
                            '"%s" is not one of them.' % (item.title, item.from_last_week))
    cards = {}
    for item in plan.work:
        source = plan.carry_source(item)
        if source:
            cards.setdefault(same_words(source), (source, []))[1].append(item.title)
    for source, titles in cards.values():
        if len(titles) > 1:
            problems.append('Carried-over "%s" is on %d cards: %s. One carried-over item goes on one card; give the '
                            'others a title of their own and no "from_last_week" to it.'
                            % (source, len(titles), ", ".join('"%s"' % t for t in titles)))
    if plan.reviewed:
        unmarked = [i.title for i in plan.work if i.done is None]
        if unmarked:
            problems.append('The week is being reviewed, so every item needs "done": true or false. Not marked yet: %s.'
                            % "; ".join(unmarked))
    texts = [plan.title] + plan.goals + plan.carried_over
    texts += [t for d in plan.days for i in d.items for t in (i.title, i.project, i.from_last_week) if t]
    missing = sorted(set(ch for t in texts for ch in theme.missing_characters(t)))
    if missing:
        problems.append("These characters cannot be drawn by the house font (English text only, no emoji): %s."
                        % " ".join(missing))


def _unknown(data, allowed, where, problems):
    for key in sorted(data):
        if key not in allowed:
            problems.append('%s has an unknown field "%s" (allowed: %s).' % (where, key, ", ".join(sorted(allowed))))


def _text(data, key, limit, where, problems):
    value = data.get(key)
    if value is None:
        return ""
    if not isinstance(value, str):
        problems.append('%s: "%s" must be text in quotes; it is %s.' % (where, key, describe(value)))
        return ""
    value = " ".join(value.split())
    if len(value) > limit:
        problems.append('%s: "%s" is too long (%d characters; keep it to %d): "%s".' % (where, key, len(value), limit, value))
        return value[:limit]
    return value


def _texts(data, key, most, limit, problems):
    value = data.get(key, [])
    if not isinstance(value, list):
        problems.append('"%s" must be a list of short sentences.' % key)
        return []
    if len(value) > most:
        problems.append('"%s" holds at most %d; it has %d.' % (key, most, len(value)))
    out = []
    for n, entry in enumerate(value[:most], 1):
        text = _text({key: entry}, key, limit, "%s %d" % (key.replace("_", " ").capitalize(), n), problems)
        if text:
            out.append(text)
    return out


def _hours(value, where, problems, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or (isinstance(value, float) and not math.isfinite(value)):
        problems.append("%s must be a number of hours (0.5 is half an hour); it is %s." % (where, describe(value)))
        return None
    if value < 0 or (value == 0 and not allow_zero) or value > 16 or abs(value * 4 - round(value * 4)) > 1e-9:
        shown = value if abs(value) <= 1000 else "far too %s" % ("large" if value > 0 else "small")
        problems.append("%s must be between %s and 16, in quarter hours (0.25, 0.5, 0.75 ...); it is %s."
                        % (where, "0" if allow_zero else "0.25", shown))
        return None
    return round(value * 4) / 4.0


def same_words(text):
    """Two texts are the same item when only capital letters or spacing differ."""
    return " ".join(text.split()).casefold()


def describe(value):
    if value is None:
        return "missing"
    if isinstance(value, str):
        return '"%s"' % value
    return json.dumps(value)


def day_name(date):
    """'Sun 4 Oct', always in English whatever the computer's language."""
    return "%s %d %s" % (("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[date.weekday()], date.day,
                         ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")[date.month - 1])


def hours_text(hours):
    """30 min, 1 h, 1.5 h, 2.25 h."""
    if hours < 1:
        return "%d min" % round(hours * 60)
    return ("%g h" % hours)
