# Changelog

All notable changes to this project. The version is `VERSION` in
`skills/week-planner/scripts/week_tool/__init__.py`.

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
