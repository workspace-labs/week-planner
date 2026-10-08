# Scope

## What it does

- Plans a person's **week** (up to 7 days, Sunday to Saturday by default) or **weekend** (at most 3 tasks
  plus a personal item only if the person wants one), and **reviews** the week at its end: a score, and what moves on.
- Works in every agent and app: Claude Code, the Claude app and website, Codex and other agents. It asks
  the person for their tasks everywhere, and reads a Backloop board only where one exists.
- Hands back a **Week Board** PDF in the WorkSpace Labs house look (owner's pick, concept A, 2026-10-05):
  the board, a **Top goals** page in the person's own words, and a page of the AI's **advice** (owner's
  booklet, 2026-10-09); or, on request, the same week as an **HTML page** to tick tasks off; or a table in
  the chat where code cannot run.

## What it will NOT do

- No board writes: never presses Commit, Accept or Reject, never changes a task's stage or file.
- No calendar events, messages, emails or reminders unless the person asks in their own words.
- No tasks, goals or personal items the person did not give. The AI's own ideas go only on the advice
  page, each quoting the person's words it came from, never on the board.
- No extra questions for the advice: it is written from what the person already said.
- No overfilled day, and no week without a buffer slot: the tool refuses them.
- No dashboards, number tiles or charts beyond the plain review score.
- No network access, no data collection: the tool reads one plan file and writes one PDF or one HTML page.
  The HTML page loads nothing from the internet; its ticks stay in that browser and in the plan file the
  person saves.
- No hard-coded paths from one machine.

## How good it must be

- **Clean or refused.** Every word fits its card, no card leaves its column, no day overflows; otherwise a
  numbered refusal says exactly what to change.
- **Plain words** in every refusal and every hand-over.
- **Same output everywhere.** Python 3.9+ and `reportlab` are the only needs; the font and logo travel
  inside the skill.
