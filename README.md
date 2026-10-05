# week-planner

![Plan Sunday, review Saturday: the skill's own Week Plan and Week Review pages, fanned out, with the score 7 of 10 done](media/week-planner-hero.png)

**Plan your week, or your weekend, in one calm page. Then see how it went.**

An agent skill that turns "plan my week" into a realistic plan: your real tasks fitted into the free hours
of each day, never overfilled, with a buffer slot for when things take longer. You get a **Week Board**
PDF: seven day columns, one card per task, red for the decisions waiting on you. At the end of the week,
"review my week" scores what got done and carries the rest over.

It works in every agent and app: Claude Code, the Claude app and website, Codex and others. It asks you
for your tasks everywhere, and also reads your Backloop board (read only) where one exists.

**Version 0.1.1** · **66 tests, all passing** · **reviewed by a second agent: APPROVED** · [the proof](#proof-how-we-know-it-works)

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

## Proof: how we know it works

We do not call it built until it is proven. Everything below can be checked.

### 66 automated tests, all passing

Run them yourself (Python 3.9+ and `reportlab`; `poppler` for the checks that read the PDFs back):

```bash
python3 -B -m unittest discover -s tests
```

On version 0.1.1 (Python 3.9.6, ReportLab 5.0.0): **66 passed, 0 skipped, 0 failed.**

| What is tested | Tests |
|---|---:|
| The plan rules and their plain-language refusals: an overfilled day, no buffer, too much for a weekend, a half-marked review, emoji, wrong dates, NaN or huge hours, carried-over tasks and their links | 36 |
| The board's geometry, judged by independent rectangle maths: every card inside its column, nothing overlapping, every line fits, "1 h" never split | 7 |
| The whole tool, end to end: drawn PDFs read back word by word with `pdftotext`, the command line and its exit codes, the footer, the planned totals, a page preview that never overwrites a file | 23 |
| **Total** | **66** |

### Reviewed by a second agent

A second AI agent, Codex, reviewed the skill in a fresh session: it had not watched the build and checked
everything from the repository itself. Over five rounds it found **7 real problems**. Each was fixed with a
test that failed before the fix and passes after it, and on 5 October 2026 its verdict was **APPROVED**.

| Finding | What was wrong | Closed in round |
|---|---|---:|
| F01 | A carried-over task could be lost, listed twice, or come back after it was done | 4 |
| F02 | A weekend demanded a personal item, though personal items are optional | 2 |
| F03 | A long title and website could run into the page number | 2 |
| F04 | NaN or infinite hours crashed the tool instead of being refused | 2 |
| F05 | A huge number of hours crashed the tool instead of being refused | 3 |
| B04 | Previewing the pages could overwrite a file named `page-1.png` | 4 |
| B06 | "Planned" left out buffer time in some places but not others | 5 |

On top of the tests, the reviewer ran its own stress checks; it reported, for example, 7,056 carried-over
combinations and 1,050 footer combinations with no failures. Every finding and its fix is in
[CHANGELOG.md](CHANGELOG.md).

### Tried for real

The final version was also used the way a person uses it. A fresh agent (once Claude, once Codex) got only
the skill's instructions and a scripted person: "plan my week" with a carried-over task too long for a card,
then "review my week". Each time it asked its questions first, read the plan back and waited for a yes,
linked the shortened task on its own, and drew a review with the right totals and score.

### Not tested yet

So you know exactly what the proof covers:

- The skill being picked up on its own inside the native Claude and Codex apps, and their clickable answers.
- Uploading the zip to the Claude app.
- The chat-only table, where code cannot run.
- A real Backloop board (a made-up board was used).

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
