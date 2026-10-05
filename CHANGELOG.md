# Changelog

All notable changes to this project. The version is `VERSION` in
`skills/week-planner/scripts/week_tool/__init__.py`.

## [Unreleased]

### Docs

- README: a **Proof** section: the 66 tests by what they check, the second agent's review and its 7
  findings, the tries for real, and what is not tested yet. The skill itself is unchanged.

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
