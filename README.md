# week-planner

![Plan Sunday, review Saturday: the skill's own Week Plan and Week Review pages, fanned out, with the score 7 of 10 done](media/week-planner-hero.png)

**Plan your week, or your weekend, in one calm page. Then see how it went.**

An agent skill that turns "plan my week" into a realistic plan: your real tasks fitted into the free hours
of each day, never overfilled, with a buffer slot for when things take longer. You get a **Week Board**
PDF: seven day columns, one card per task, red for the decisions waiting on you. At the end of the week,
"review my week" scores what got done and carries the rest over.

It works in every agent and app: Claude Code, the Claude app and website, Codex and others. It asks you
for your tasks everywhere, and also reads your Backloop board (read only) where one exists.

**Version 0.1.1**

---

## What you say

| You say | You get |
|---|---|
| "plan my week" | A few click questions (free hours, free days, your #1 goal), a read-back, then the Week Plan PDF |
| "plan my weekend" | Your weekend days, at most 3 tasks, plus a fun or personal item if you want one |
| "review my week" | Tick what got done: a Week Review PDF with the score and what moves to next week |

Where the app cannot run code, the same plan comes back as a table in the chat.

## What the PDF holds

1. **The Week Board**: the #1 goal in a band, then one column per day. Each card has a bar for its stage
   (active, review, plan), red for a decision waiting on you, hatched for buffer time, and each day shows
   hours planned of hours free.
2. **Your focus** (when there is something for it): the top goals, what is waiting on you, and what carried
   over from last week. In a review: the score, and what moves to next week.

The look is the WorkSpace Labs house look, the same family as the workflow-project PDF: Plus Jakarta Sans,
a light ground, one blue accent, red only for "waiting on you".

## Install

The drawing tool needs Python 3.9 or newer and `reportlab` (already in Claude's and ChatGPT's sandboxes;
elsewhere `python3 -m pip install reportlab`).

**Claude Code, Codex and other agents**, in one line:

```bash
npx skills add workspace-labs/week-planner -g
```

Or by hand, for Claude Code:

```bash
git clone https://github.com/workspace-labs/week-planner.git
mkdir -p ~/.claude/skills
cp -R week-planner/skills/week-planner ~/.claude/skills/
```

**Claude app (chat and Cowork)**: make the zip, then upload it in **Customize → Skills**.

```bash
cd week-planner
rm -f dist/week-planner.zip && mkdir -p dist
(cd skills && zip -r -X ../dist/week-planner.zip week-planner -x '*/__pycache__/*' '*.pyc' '*.DS_Store')
```

Then start a fresh session and say "plan my week".

## Run the drawing tool yourself

```bash
python3 skills/week-planner/scripts/draw_week.py skills/week-planner/examples/week.json -o "Week Plan.pdf"
python3 skills/week-planner/scripts/draw_week.py my-plan.json --check      # checks only
```

The plan file format is in `skills/week-planner/references/plan-format.md`.

## Test

```bash
python3 -B -m unittest discover -s tests
```

66 checks: the plan rules and their plain refusals (overfilled day, no buffer, too much for a weekend, a
half-marked review, emoji, wrong dates and hours, carried-over items and their links); the board geometry judged by independent rectangle maths
(every card inside its column, nothing overlapping, every line fits, "1 h" never split); and the drawn PDFs
read back with `pdftotext` (skipped where poppler is missing).

## Limits

- English text only; emoji are refused in the PDF.
- A4 landscape, 1 to 7 days (weekend 1 to 3), about 6 to 8 cards a day.
- Task titles up to 48 characters, 3 lines in their card.

## Layout

```
skills/week-planner/        the skill (what gets installed)
  SKILL.md                  what the agent does
  references/               the plan file format, and the chat table
  scripts/draw_week.py      the drawing tool
  scripts/week_tool/        its parts: model (rules), layout (geometry), pages (painting), theme, brand
  examples/                 a week, a weekend and a reviewed week
  assets/                   the fonts (SIL Open Font License), brand.json and the logo
tests/                      the checks (not shipped with the skill)
docs/                       scope, the decision record, and the skill's own workflow PDF
media/                      the picture at the top of this page
```

## Credits and licence

The code is under the MIT licence (`LICENSE`). Plus Jakarta Sans is by Tokotype under the SIL Open Font
License 1.1 (see `CREDITS.md`). The logo and the WorkSpace Labs name are WorkSpace Labs' own; replace them
with yours through `assets/brand.json`.

---

<sub>by Workspace Labs</sub>
