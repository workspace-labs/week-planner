# Changelog

All notable changes to this project. The version is `VERSION` in
`skills/week-planner/scripts/week_tool/__init__.py`.

## [Unreleased]

### Docs

- README: a **Proof** section: the 66 tests by what they check, the second agent's review and its 7
  findings, the tries for real, and what is not tested yet. The skill itself is unchanged.

## [0.4.1] - 2026-10-09

### Fixed

- **The phone's bottom bar is solid.** It was 97% white, so the words scrolling under the score and Save plan
  showed through faintly; seen in the iPhone picture made for the README.

### Docs

- README: a picture of the HTML page on an iPhone (`media/week-planner-iphone.png`), drawn from the skill's
  own output for the example week: today first, Top goals, advice.

## [0.4.0] - 2026-10-09

The owner picked option A of three phone designs (`samples/mobile-demo`, outside the repository): today
first.

### Added

- **The HTML page on a phone** (640 px wide or less). The board gives way to one day at a time: tabs for the
  days along the top, with a dot per task that fills in when it is done; it opens on **today** (the first
  day before the week starts, the last after it ends). Today's tasks are big cards for a thumb, and the
  score with Save plan stays fixed at the bottom of the screen. The Top goals and advice pages follow
  below. A computer still shows the whole board; ticking a card in either view ticks it everywhere.

### Tests

- 101 tests (was 100): at a phone's width in a real headless Chrome, with "today" pinned to a Tuesday, the
  page opens on that Tuesday, a tick there moves the score and ticks the board's card and the day's dot, the
  bar stays fixed, another tab shows its own tasks, and nothing runs off the side of the screen.

## [0.3.0] - 2026-10-09

The owner's next step after his first real week: a week you tick off as you go, goals that look as serious
as they are, and the AI's own advice on a page of its own. Designed in conversation and approved from a
clickable demo (`samples/next-version-demo`, outside the repository) on 2026-10-09.

### Added

- **The HTML page** (`draw_week.py plan.json --html`). The same week as one file that needs no internet:
  click a task when it is done and the score, each day's total and the goals move at once. **Save plan**
  downloads the plan file under its own name, with `"done"` set on every task and nothing else changed; the
  review reads it. Ticks also stay in that browser between visits.
- **A Top goals page** in a week plan. The #1 goal across the page: **Why**, **Done when**, **What could
  stop me**, **First step**, and **This week** counted from its cards (tasks, hours, days, and the cards
  themselves, the first 8 then "and N more"). Goals 2 and 3 below it. In a review: a done bar and the
  person's verdict, **Reached**, **Close** or **Not yet**.
- **An advice page.** Up to 5 tips the AI writes from what the person already said, with no extra
  questions. Each shows "Because you said ..." with their own words, and the tool refuses a `because` that
  is not in the plan, so a tip can never claim a reason they did not give. A tip about real places or
  prices carries a "check before you book" note. Nothing on it goes on the board.
- Goal fields `risk`, `first_step` and (review only) `result`; plan field `advice`.

### Changed

- **The goals left page 1** of a week plan for their own page; page 1 keeps the #1 goal band, and what is
  waiting on you and what carried over stay under the board. A weekend plan is unchanged: one page, its goal
  under the board.
- **SKILL.md asks more about the #1 goal**, one question at a time: why (with a follow-up if the answer is
  short), how they will know it is done, what could stop them, and their first step. Goals 2 and 3 ask only
  why. Each answer is polished into one clear sentence and shown for a yes, never with a fact added. The
  plan puts the #1 goal's tasks early when time is the risk.
- The review asks each goal's verdict, and reads ticks already saved from the HTML page instead of asking
  again.

### Tests

- 100 tests (was 81): the new goal fields and the verdict (5), advice and its quote rule (5), the Top goals
  and advice pages fit or are refused by name and the long card list ends in "and N more" (4), the HTML page
  (5, one of them clicking the page in a real headless Chrome and pressing Save plan). Four tests that
  expected the goals under the board on one page now expect the booklet.

## [0.2.0] - 2026-10-05

The owner's first real week showed the board as six tall columns with two or three cards each, and a second
page holding one line.

### Changed

- **Columns end under the busiest day.** Every column now stops together just below the day with the most
  cards (never shorter than 150 pt, so a light week still reads as columns). A day that does not fit is
  still refused, never squeezed.
- **Your focus moves under the board when it fits.** The top goals, what is waiting on you, what carried
  over or moves on (and, in a review, the score) are drawn on page 1 under the board, so a usual week is one
  page. A packed week that leaves no room keeps them on page 2, as before.

- **A goal says why, and when it is done.** A goal can now be an object: `goal`, and in the person's own
  words `why` and `done_when`, plus the `project` of the cards that serve it. Under the goal the PDF shows
  **Why**, **Done when** and **This week** ("4 tasks · 6.5 h · Mon to Wed", or "3 of 4 done" in a review),
  counted from the cards, never typed. A plain sentence still works. SKILL.md now asks "Why does it matter to
  you?" and "How will you know it's done?" after the goal, and reads them back. A goal naming a project no
  card has is refused. The examples' first goal shows it.

### Tests

- 81 tests (was 66): goal objects, their limits and refusals, the counted "This week" line in a plan and a
  review, and rows left out when not given (11); columns end together, a light week keeps a minimum height, the focus under the board
  never touches the board or the footer in every example, and a packed week keeps page 2 (4). With the old
  full-height columns put back, 3 of them fail.

## [0.1.1] - 2026-10-05

Fixes from Codex's review of 0.1.0 (candidate 16b33da), over five rounds.

### Added

- **`from_last_week` on a card.** A carried-over item can be up to 70 characters but a card title only 48, so
  the planner often shortens it. The card now names the carried-over words it plans, and the tool checks
  they repeat one `carried_over` entry. The tool also prints a note for each carried-over item no card takes
  on, so a forgotten link is caught at once (a note, never a refusal: leaving one unplanned is allowed).

### Fixed

- **F01: a review keeps last week's carry-over, once.** A reviewed week dropped anything carried over from last
  week that was never put on a day (the example lost "Book the dentist appointment"); it now moves on to next
  week. A carried-over item that was planned, under its own words or a shorter title linked by
  `from_last_week`, is judged by its card: done is gone, open moves on once, an open decision stays under
  "Waiting on you". Each card plans at most one carried-over item (its link wins over its title), and each
  item goes on at most one card: two cards for the same item are refused, so nothing is listed twice or
  silently lost. Words are matched ignoring capital letters and spacing; buffer time never plans one. The
  same entry listed twice in `carried_over` is refused.
- **F02: a weekend no longer demands a personal item.** Personal items are optional, as the owner decided;
  the tool refused a two-task weekend with no fun item. The 3-task limit stays.
- **F03: the footer never runs into the page number.** With a long title and a long website the footer
  overlapped "Page 1 of 1". When room is short the tool's version is left out first, then the website.
- **F04: NaN, Infinity and huge hours are refused.** They crashed the tool with a Python error; they now get the
  same numbered refusal as any other wrong number ("it is far too large" instead of a 400-digit number).

- **B04: looking at the pages never overwrites a file.** SKILL.md told the agent to render preview pictures as
  `page-1.png` in the current folder, which replaced any file of that name. They now go into a new
  temporary folder each time.

- **B06: "planned" means the same everywhere.** The page headers and the tool's check line counted only tasks
  (13.5 h in the example week) while each day's total also counted buffer time (16 h altogether). Every
  "planned" total now includes buffer time; the done score still counts only real work.

Each fix has a test that failed before it (66 tests now).

### Reviewed

- **Codex: APPROVED** on 2026-10-05, after an independent review over five rounds (findings F01 to F05, B04, B06).
- **Tests: 66/66 passed** (`python3 -B -m unittest discover -s tests`, Python 3.9.6, ReportLab 5.0.0).

## [0.1.0] - 2026-10-05

### Added

- **The week-planner skill.** "Plan my week", "plan my weekend" and "review my week": collect the real
  tasks (from the person, and from a Backloop board only where one exists, read only), ask a few click
  questions, fit the work into the free hours with a buffer slot, read it back, then hand it over.
- **The Week Board PDF** (the owner's pick, concept A): seven day columns, one card per task with a bar
  for its stage, red for decisions waiting on the person, a hatched buffer, the #1 goal in a band. Page 2
  holds the top goals, what is waiting on the person, and what carried over.
- **The review.** Mark each task done or not and the same PDF becomes a Week Review: ticks on the board, a
  score, and what moves to next week.
- **The plan file checks:** no overfilled day, a buffer in every week, at most 3 tasks in a weekend, every
  word fits its card; each refusal is a numbered sentence saying what to change.
- A chat table for apps where code cannot run, three examples, 36 tests, and the skill's own workflow
  PDF in `docs/workflow/`.
- The picture at the top of the README (`media/week-planner-hero.png`): the skill's own Week Plan and Week
  Review pages, drawn from the examples, which use made-up demo tasks.
