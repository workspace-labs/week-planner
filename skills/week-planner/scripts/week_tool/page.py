"""The week as one HTML page the person keeps open all week: they click a task when it is done, the
score, the day totals and the goals move with it, and "Save plan" hands back the plan file with the ticks
in it, for the review to read.

One self-contained file: the fonts and the logo are inside it, it never loads anything from the network,
and it shows every word of the plan as text, never as markup.
"""

import base64
import json
import os

from . import VERSION, pages, theme
from .model import day_name, hours_text

_WEIGHTS = ((400, "Regular"), (500, "Medium"), (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold"))


def write(plan, raw, plan_name, brand, out_path):
    """raw is the plan file as read, so a save keeps every field the person had and only adds the ticks."""
    html = _TEMPLATE
    for token, value in (("__FONTS__", _fonts()), ("__TITLE__", _escape(plan.title)),
                         ("__DATA__", _json(view(plan, raw, plan_name, brand)))):
        html = html.replace(token, value)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(html)


def view(plan, raw, plan_name, brand):
    """Everything the page shows, worked out here so the page and the PDF count the same way."""
    goals = []
    for n, goal in enumerate(plan.goal_details, 1):
        week = pages.goal_week(plan, goal)
        cards = [[plan.days.index(d), d.items.index(i)] for d, i in week["cards"]] if week else []
        goals.append({"n": n, "goal": goal.text, "why": goal.why, "done_when": goal.done_when, "risk": goal.risk,
                      "first_step": goal.first_step, "result": goal.result, "cards": cards,
                      "span": week["span"] if week else ""})
    days = []
    for day in plan.days:
        name, number, month = day_name(day.date).split()
        days.append({"name": name.upper(), "number": number, "month": month, "free": day.free_hours, "off": day.off,
                     "items": [{"title": i.title, "kind": i.kind, "stage": i.stage or "", "project": i.project,
                                "hours": i.hours, "time": hours_text(i.hours), "done": bool(i.done)} for i in day.items]})
    logo = ""
    if brand.logo:
        with open(brand.logo, "rb") as handle:
            logo = "data:image/png;base64," + base64.b64encode(handle.read()).decode("ascii")
    return {"title": plan.title, "range": pages.date_range(plan), "tag": pages.tag_text(plan), "mode": plan.mode,
            "goalPage": plan.goal_page, "goals": goals, "days": days, "reviewed": plan.reviewed,
            "advice": [{"title": a.title, "text": a.text, "because": a.because, "check": a.check} for a in plan.advice],
            "brand": {"name": brand.name, "accent": brand.accent, "website": brand.website, "logo": logo},
            "version": VERSION, "file": plan_name, "raw": raw}


def _fonts():
    faces = []
    for weight, cut in _WEIGHTS:
        with open(os.path.join(theme.ASSETS, "fonts", "PlusJakartaSans-%s.ttf" % cut), "rb") as handle:
            data = base64.b64encode(handle.read()).decode("ascii")
        faces.append('@font-face { font-family: "PJS"; font-weight: %d; src: url(data:font/ttf;base64,%s) format("truetype"); }'
                     % (weight, data))
    return "\n".join(faces)


def _json(value):
    """Safe inside a script tag: "</" can never close it early."""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
__FONTS__
:root {
  --space: #F2F5FF; --ink: #10182E; --ink-soft: #4A5478; --ink-faint: #8A93B2; --accent: #3E5BFF; --red: #E03131;
  --white: #FFFFFF; --line: #D6DCEF; --line-soft: #E3E8F7; --box-stroke: #C9D1EA; --tag-bg: #EEF1FF;
  --tag-line: #D2D9FF; --goal-bg: #EDF0FF; --red-bg: #FDF0F0; --red-line: #F7C4C4; --desk: #E4E7F0;
  --bar-review: #A6B4FF; --bar-checklist: #C5CEFF; --bar-plan: #C3C8DA; --bar-personal: #9AA3C0;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "PJS", system-ui, sans-serif; color: var(--ink); background: var(--desk); padding: 28px 16px 60px; }
button { font: inherit; color: inherit; }
.page { max-width: 1123px; min-height: 794px; margin: 0 auto 28px; background: var(--white); border-radius: 6px;
        box-shadow: 0 10px 40px rgba(16,24,46,.12); padding: 34px 48px 26px; display: flex; flex-direction: column; }
.top { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--line-soft); }
.brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 14px; }
.brand img { width: 22px; height: 22px; border-radius: 5px; }
.accent { color: var(--accent); }
.pill { font-size: 9.5px; font-weight: 700; letter-spacing: .16em; color: var(--accent); background: var(--tag-bg);
        border: 1px solid var(--tag-line); padding: 4px 11px; border-radius: 99px; white-space: nowrap; }
.pill.reached { background: var(--accent); border-color: var(--accent); color: var(--white); }
.pill.not-yet, .pill.check { background: var(--white); border-color: var(--box-stroke); color: var(--ink-soft); }
h1 { font-size: 34px; font-weight: 800; letter-spacing: -.02em; margin-top: 18px; line-height: 1.05; }
.sub { font-size: 12.5px; color: var(--ink-soft); margin-top: 6px; font-weight: 500; }
.footer { margin-top: auto; padding-top: 10px; border-top: 1px solid var(--line-soft); display: flex; justify-content: space-between;
          gap: 12px; font-size: 10px; color: var(--ink-faint); }
.eyebrow { font-size: 10px; font-weight: 700; letter-spacing: .16em; color: var(--accent); }
.band { margin-top: 14px; background: var(--goal-bg); border: 1px solid var(--tag-line); border-radius: 10px; padding: 9px 16px;
        display: flex; gap: 14px; align-items: center; font-size: 13px; font-weight: 600; }
.scroll { flex: 1; display: flex; overflow-x: auto; margin-top: 14px; }
.board { flex: 1; display: grid; gap: 10px; min-width: 0; }
.day { background: var(--space); border: 1px solid var(--line-soft); border-radius: 12px; padding: 12px 9px 10px; display: flex; flex-direction: column; min-height: 300px; }
.dname { font-size: 9.5px; font-weight: 700; letter-spacing: .16em; color: var(--ink-soft); }
.dnum { font-size: 22px; font-weight: 800; margin: 2px 0 10px; }
.dnum small { font-size: 10.5px; font-weight: 500; color: var(--ink-faint); margin-left: 3px; }
.rest { font-size: 11px; color: var(--ink-faint); font-weight: 500; }
.card { position: relative; display: block; width: 100%; text-align: left; background: var(--white); border: 1px solid var(--box-stroke);
        border-radius: 8px; padding: 8px 24px 8px 12px; margin-bottom: 8px; cursor: pointer; transition: border-color .15s; }
.card::before { content: ""; position: absolute; left: 0; top: 6px; bottom: 6px; width: 3.5px; border-radius: 3px; background: var(--bar-plan); }
.card.active::before { background: var(--accent); }
.card.review::before { background: var(--bar-review); }
.card.checklist::before { background: var(--bar-checklist); }
.card.personal::before { background: var(--bar-personal); }
.card.decision { background: var(--red-bg); border-color: var(--red-line); }
.card.decision::before { background: var(--red); }
.card:hover { border-color: var(--accent); }
.card:focus-visible, .save:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.card .t { display: block; font-size: 11.5px; font-weight: 700; line-height: 1.25; overflow-wrap: anywhere; }
.card .d { display: block; font-size: 9.5px; color: var(--ink-soft); margin-top: 3px; }
.tick { position: absolute; top: 8px; right: 7px; width: 14px; height: 14px; border-radius: 50%; border: 1.5px solid var(--ink-faint); background: var(--white); }
.done .tick, .row.done .tk { background: var(--accent); border-color: var(--accent); }
.done .tick::after, .row.done .tk::after { content: ""; position: absolute; left: 4px; top: 1.5px; width: 3px; height: 6.5px;
        border: solid #fff; border-width: 0 1.6px 1.6px 0; transform: rotate(45deg); }
.card.done .t { color: var(--ink-soft); }
.buffer { border: 1.5px dashed var(--box-stroke); border-radius: 8px; padding: 8px 12px; margin-bottom: 8px; font-size: 11px; font-weight: 600;
          color: var(--ink-soft); background: repeating-linear-gradient(135deg, #fff 0 6px, #EEF0F5 6px 7px); }
.buffer small { display: block; font-weight: 500; font-size: 9.5px; margin-top: 2px; }
.dtotal { margin-top: auto; padding-top: 8px; font-size: 9.5px; color: var(--ink-faint); font-weight: 600; }
.score { margin-top: 14px; background: var(--goal-bg); border: 1px solid var(--tag-line); border-radius: 10px; padding: 12px 18px;
         display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }
.score .big { font-size: 20px; font-weight: 800; min-width: 128px; }
.squares { display: flex; gap: 4px; flex-wrap: wrap; }
.squares i { width: 22px; height: 9px; border-radius: 3px; background: var(--line); transition: background .2s; }
.squares i.on { background: var(--accent); }
.save { margin-left: auto; font-size: 12px; font-weight: 700; color: var(--white); background: var(--accent); border: 0; border-radius: 8px; padding: 9px 16px; cursor: pointer; }
.saved { font-size: 11px; color: var(--ink-soft); }
.hint { margin: 10px 0 16px; font-size: 11px; color: var(--ink-soft); }
.g1 { margin-top: 18px; border: 1px solid var(--box-stroke); border-radius: 14px; overflow: hidden; }
.g1-head { display: flex; align-items: center; gap: 16px; padding: 14px 22px; background: var(--goal-bg); }
.g1-body { display: grid; border-top: 1px solid var(--tag-line); }
.num { font-size: 30px; font-weight: 800; color: var(--accent); line-height: 1; }
.gtitle { font-size: 20px; font-weight: 800; letter-spacing: -.01em; flex: 1; }
.cell { padding: 14px 20px; }
.stack { border-right: 1px solid var(--line-soft); }
.stack .cell + .cell { border-top: 1px solid var(--line-soft); }
.cell p, .gs p { font-size: 13.5px; line-height: 1.45; margin-top: 6px; font-weight: 500; }
.stats { display: flex; gap: 22px; margin-top: 8px; flex-wrap: wrap; }
.stat b { display: block; font-size: 24px; font-weight: 800; line-height: 1; }
.stat span { font-size: 10.5px; color: var(--ink-soft); font-weight: 600; }
.prog { margin-top: 14px; height: 8px; background: var(--line); border-radius: 99px; overflow: hidden; }
.prog i { display: block; height: 100%; width: 0; background: var(--accent); border-radius: 99px; transition: width .25s; }
.progtxt { font-size: 11px; color: var(--ink-soft); margin-top: 6px; font-weight: 600; }
.rows { margin-top: 12px; border-top: 1px solid var(--line-soft); list-style: none; }
.row { display: grid; grid-template-columns: 34px 1fr auto 16px; gap: 8px; align-items: center; font-size: 11.5px; padding: 6px 0; border-bottom: 1px solid var(--line-soft); }
.row .dd { font-size: 9.5px; font-weight: 700; letter-spacing: .1em; color: var(--ink-faint); }
.row .hh { color: var(--ink-soft); font-size: 10.5px; }
.row .tk { position: relative; width: 13px; height: 13px; border-radius: 50%; border: 1.5px solid var(--ink-faint); }
.row.done .tk::after { left: 3.5px; top: 1px; height: 6px; }
.row.done .tt { color: var(--ink-soft); }
.gsmall { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 14px; }
.gs { border: 1px solid var(--box-stroke); border-radius: 14px; padding: 16px 20px; display: grid; grid-template-columns: auto 1fr auto; gap: 6px 14px; align-items: start; }
.gs .num { font-size: 24px; }
.gs .gtitle { font-size: 16px; }
.gs .more { grid-column: 2 / 4; }
.gs .field { margin-top: 6px; }
.gs p { font-size: 12.5px; margin-top: 4px; }
.meta { font-size: 11px; color: var(--ink-soft); font-weight: 600; margin-top: 8px; }
.notice { margin-top: 16px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; padding: 10px 16px; border-radius: 10px;
          background: var(--space); border: 1px solid var(--line-soft); font-size: 12px; color: var(--ink-soft); font-weight: 500; }
.advice { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 16px; }
.tip { border: 1px solid var(--box-stroke); border-radius: 14px; padding: 16px 20px; display: flex; flex-direction: column; gap: 8px; }
.tip.wide { grid-column: 1 / -1; }
.tip-top { display: flex; align-items: baseline; gap: 12px; }
.tip-top .num { font-size: 20px; }
.tip h3 { font-size: 15px; font-weight: 800; }
.tip p { font-size: 12.5px; line-height: 1.5; font-weight: 500; }
.because { font-size: 11.5px; color: var(--ink-soft); border-left: 3px solid var(--tag-line); padding: 2px 0 2px 10px; }
.because b { display: block; color: var(--accent); font-weight: 700; letter-spacing: .1em; font-size: 9.5px; margin-bottom: 2px; }
.tip .pill { align-self: flex-start; }
@media (max-width: 800px) {
  body { padding: 16px 0 40px; }
  .page { padding: 20px 16px; border-radius: 0; min-height: 0; }
  .board { min-width: 860px; }
  .g1-body, .gsmall, .advice { grid-template-columns: 1fr !important; }
  .stack { border-right: 0; border-bottom: 1px solid var(--line-soft); }
  .tip.wide { grid-column: auto; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
@media print { body { background: #fff; padding: 0; } .save, .saved, .hint { display: none; }
  .page { box-shadow: none; border-radius: 0; break-after: page; margin: 0; } }
@page { size: A4 landscape; margin: 0; }
</style>
</head>
<body>
<main id="pages"></main>
<script type="application/json" id="plan">__DATA__</script>
<script>
(function () {
  "use strict";
  var V = JSON.parse(document.getElementById("plan").textContent);
  var KEY = "week-planner " + V.title + " " + V.range;
  var cards = [];                                 // every item that counts, in board order: {day, index, item}
  V.days.forEach(function (day, d) {
    day.items.forEach(function (item, i) { if (item.kind !== "buffer") cards.push({ day: d, index: i, item: item }); });
  });
  try {                                           // ticks made earlier in this browser come back
    var kept = JSON.parse(localStorage.getItem(KEY) || "null");
    if (kept && kept.length === cards.length) cards.forEach(function (c, n) { c.item.done = !!kept[n]; });
  } catch (e) { /* private window or blocked storage: the page still works, the Save button keeps the ticks */ }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }
  function add(parent) { for (var n = 1; n < arguments.length; n++) if (arguments[n]) parent.appendChild(arguments[n]); return parent; }
  function hours(h) { return h < 1 ? Math.round(h * 60) + " min" : h + " h"; }
  function short(h) { return h === 0 ? "0" : h < 1 ? Math.round(h * 60) + " min" : String(h); }
  function words(text, accent) {                  // one whole word in the accent colour
    var out = el("span");
    String(text).split(" ").forEach(function (word, n) {
      if (n) out.appendChild(document.createTextNode(" "));
      if (accent && word === accent) add(out, el("span", "accent", word)); else out.appendChild(document.createTextNode(word));
    });
    return out;
  }
  var root = document.getElementById("pages");
  var pageCount = 1 + (V.goalPage ? 1 : 0) + (V.advice.length ? 1 : 0);
  var watchers = [];

  function page(title, tag, number) {
    var p = el("section", "page");
    p.setAttribute("aria-label", "Page " + number + ": " + title);
    var brand = el("div", "brand");
    if (V.brand.logo) { var img = el("img"); img.src = V.brand.logo; img.alt = ""; add(brand, img); }
    add(brand, words(V.brand.name, V.brand.accent));
    add(p, add(el("div", "top"), brand, el("div", "pill", tag)));
    var parts = title.split(" ");
    add(p, add(el("h1"), words(title, parts.length > 1 ? parts[parts.length - 1] : "")));
    var sub = el("div", "sub");
    add(p, sub);
    watchers.push(function (done, total, planned, free) {
      sub.textContent = V.range + " · " + hours(planned) + " planned of " + hours(free) + " free · " + done + " of " + total + " done";
    });
    p.body = el("div");
    p.body.style.display = "contents";
    add(p, p.body);
    var site = V.brand.website ? " · " + V.brand.website : "";
    add(p, add(el("div", "footer"), el("span", "", V.title + " — " + V.range + " · week-planner " + V.version + site),
               el("span", "", "Page " + number + " of " + pageCount)));
    add(root, p);
    return p.body;
  }

  // ---- page 1: the board
  var body = page(V.title, V.tag, 1);
  if (V.goals.length) add(body, add(el("div", "band"), el("span", "eyebrow", "#1 GOAL"), el("span", "", V.goals[0].goal)));
  var board = el("div", "board");
  board.style.gridTemplateColumns = "repeat(" + V.days.length + ", minmax(0, 1fr))";
  if (V.days.length < 4) board.style.maxWidth = (V.days.length * 220) + "px";
  V.days.forEach(function (day) {
    var col = add(el("div", "day"), el("div", "dname", day.name), add(el("div", "dnum", day.number), el("small", "", day.month)));
    if (day.off && !day.items.length) add(col, el("div", "rest", "Rest day"));
    day.items.forEach(function (item) {
      if (item.kind === "buffer") { add(col, add(el("div", "buffer", item.title), el("small", "", item.time))); return; }
      var kind = item.kind === "decision" || item.kind === "personal" ? item.kind : (item.stage || "plan");
      var card = el("button", "card " + kind);
      card.type = "button";
      var detail = [item.project, item.kind === "decision" ? "your decision" : item.kind === "personal" ? "personal" : item.stage, item.time]
        .filter(Boolean).join(" · ");
      add(card, el("span", "t", item.title), el("span", "d", detail), el("span", "tick"));
      card.querySelector(".tick").setAttribute("aria-hidden", "true");
      card.addEventListener("click", function () { item.done = !item.done; update(); });
      watchers.push(function () { card.classList.toggle("done", item.done); card.setAttribute("aria-pressed", String(item.done)); });
      add(col, card);
    });
    var total = el("div", "dtotal", day.off ? "Day off" : short(day.items.reduce(function (a, i) { return a + i.hours; }, 0)) + " of " + hours(day.free));
    add(board, add(col, total));
  });
  add(body, add(el("div", "scroll"), board));
  var big = el("span", "big"), squares = el("span", "squares"), saved = el("span", "saved"), save = el("button", "save", "Save plan");
  save.type = "button";
  big.setAttribute("aria-live", "polite");
  saved.setAttribute("aria-live", "polite");
  add(body, add(el("div", "score"), el("span", "eyebrow", "SCORE"), big, squares, saved, save));
  add(body, el("p", "hint", "Click a task when it is done (or tab to it and press Enter). Save plan keeps your ticks in the plan file, for the review."));
  watchers.push(function (done, total) {
    big.textContent = done + " of " + total + " done";
    squares.textContent = "";
    for (var n = 0; n < total; n++) add(squares, el("i", n < done ? "on" : ""));
  });

  // ---- page 2: top goals
  function field(label, text, cls) { return text ? add(el("div", cls || "cell"), el("div", "eyebrow", label), el("p", "", text)) : null; }
  function badge(goal, main) {
    if (goal.result) return el("span", "pill " + goal.result.replace(" ", "-"), goal.result.toUpperCase());
    return main && !V.reviewed ? el("span", "pill", "THIS WEEK'S #1") : null;
  }
  function goalCards(goal) { return goal.cards.map(function (dc) { return V.days[dc[0]].items[dc[1]]; }); }
  if (V.goalPage) {
    body = page("Top goals", "TOP GOALS", 2);
    var g = V.goals[0];
    var g1 = add(el("article", "g1"), add(el("div", "g1-head"), el("span", "num", "1"), el("span", "gtitle", g.goal), badge(g, true)));
    var stacks = [[["WHY", g.why], ["DONE WHEN", g.done_when]], [["WHAT COULD STOP ME", g.risk], ["FIRST STEP", g.first_step]]]
      .map(function (s) { return s.filter(function (f) { return f[1]; }); }).filter(function (s) { return s.length; });
    var cols = stacks.map(function () { return "1fr"; });
    var gbody = el("div", "g1-body");
    stacks.forEach(function (s) { var st = el("div", "stack"); s.forEach(function (f) { add(st, field(f[0], f[1])); }); add(gbody, st); });
    if (g.cards.length) {
      cols.push("1.15fr");
      var tasksB = el("b"), hoursB = el("b"), bar = el("i"), progtxt = el("div", "progtxt"), rows = el("ul", "rows");
      add(gbody, add(el("div", "cell"), el("div", "eyebrow", "THIS WEEK"),
        add(el("div", "stats"), add(el("div", "stat"), tasksB, el("span", "", "tasks")), add(el("div", "stat"), hoursB, el("span", "", "hours")),
            add(el("div", "stat"), el("b", "", g.span), el("span", "", "days"))),
        add(el("div", "prog"), bar), progtxt, rows));
      var list = goalCards(g);
      tasksB.textContent = list.length;
      hoursB.textContent = list.reduce(function (a, i) { return a + i.hours; }, 0);
      g.cards.forEach(function (dc) {
        var item = V.days[dc[0]].items[dc[1]];
        var row = add(el("li", "row"), el("span", "dd", V.days[dc[0]].name), el("span", "tt", item.title), el("span", "hh", item.time), el("span", "tk"));
        add(rows, row);
        watchers.push(function () { row.classList.toggle("done", item.done); });
      });
      watchers.push(function () {
        var d = list.filter(function (i) { return i.done; }).length;
        bar.style.width = (100 * d / list.length) + "%";
        progtxt.textContent = d + " of " + list.length + " done";
      });
    }
    gbody.style.gridTemplateColumns = cols.join(" ");
    if (cols.length) add(g1, gbody);
    add(body, g1);
    if (V.goals.length > 1) {
      var small = el("div", "gsmall");
      V.goals.slice(1).forEach(function (goal) {
        var card = add(el("article", "gs"), el("span", "num", String(goal.n)), el("span", "gtitle", goal.goal), badge(goal, false) || el("span"));
        var more = el("div", "more");
        [["WHY", goal.why], ["DONE WHEN", goal.done_when], ["WHAT COULD STOP ME", goal.risk], ["FIRST STEP", goal.first_step]]
          .forEach(function (f) { add(more, field(f[0], f[1], "field")); });
        if (goal.cards.length) {
          var meta = el("div", "meta");
          var list2 = goalCards(goal);
          add(more, meta);
          watchers.push(function () {
            var d = list2.filter(function (i) { return i.done; }).length;
            meta.textContent = "This week · " + list2.length + (list2.length === 1 ? " task" : " tasks") + " · " +
              hours(list2.reduce(function (a, i) { return a + i.hours; }, 0)) + " · " + goal.span + " · " + d + " of " + list2.length + " done";
          });
        }
        add(small, add(card, more));
      });
      add(body, small);
    }
  }

  // ---- page 3: advice
  if (V.advice.length) {
    body = page("Advice for your week", "ADVICE", pageCount);
    add(body, add(el("div", "notice"), el("span", "eyebrow", "FROM THE AI"),
      el("span", "", "Written from what you said while planning. Nothing here is on your board. Use what helps, skip the rest.")));
    var grid = el("div", "advice");
    V.advice.forEach(function (tip, n) {
      var wide = n === V.advice.length - 1 && V.advice.length % 2 === 1;
      add(grid, add(el("article", "tip" + (wide ? " wide" : "")),
        add(el("div", "tip-top"), el("span", "num", String(n + 1)), el("h3", "", tip.title)), el("p", "", tip.text),
        add(el("div", "because"), el("b", "", "BECAUSE YOU SAID"), document.createTextNode('"' + tip.because + '"')),
        tip.check ? el("span", "pill check", tip.check.toUpperCase()) : null));
    });
    add(body, grid);
  }

  function update() {
    var done = cards.filter(function (c) { return c.item.done; }).length;
    var planned = 0, free = 0;
    V.days.forEach(function (d) { if (!d.off) free += d.free; d.items.forEach(function (i) { planned += i.hours; }); });
    watchers.forEach(function (w) { w(done, cards.length, planned, free); });
    saved.textContent = "";
    try { localStorage.setItem(KEY, JSON.stringify(cards.map(function (c) { return c.item.done; }))); } catch (e) { /* see above */ }
  }

  save.addEventListener("click", function () {
    // the plan file as it was, with "done" on every item that counts; buffers are never marked
    var plan = JSON.parse(JSON.stringify(V.raw));
    cards.forEach(function (c) { plan.days[c.day].items[c.index].done = c.item.done; });
    var blob = new Blob([JSON.stringify(plan, null, 2) + "\n"], { type: "application/json" });
    var link = el("a");
    link.href = URL.createObjectURL(blob);
    link.download = V.file;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(function () { URL.revokeObjectURL(link.href); }, 1000);
    saved.textContent = "Saved as " + V.file + " in your downloads. Keep it with your week plan: the review reads it.";
  });
  update();
})();
</script>
</body>
</html>
"""
