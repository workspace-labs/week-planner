---
name: week-planner
description: Plans a person's week or weekend and hands back a Week Board PDF (seven day columns, every task in its day, a buffer slot, what is waiting on them, a page for their top goals and one of advice), or an HTML page they tick tasks off on all week, then reviews the week at the end. Use when someone says "plan my week", "plan my weekend", "what should I do this week", "make my weekly plan", "help me fit my tasks into the week", or "review my week" / "how did my week go". Works in any agent or app; reads a Backloop task board only when one is there. Not for one-off reminders, timed cloud jobs or recurring agent runs, calendar invites, or a project's build plan.
---

# week-planner

Turns "plan my week" into a calm, realistic week: the real tasks, fitted into the free hours of each day,
never overfilled, with room to breathe. At the end of the week it scores what got done and carries the
rest over. The result is a **Week Board** PDF in the WorkSpace Labs house look (the same family as the
workflow-project PDF): the board, then a **Top goals** page in the person's own words, then a page of
**advice**. On request, the same week comes as an **HTML page** they keep open and tick tasks off on. Where
code cannot run, it is a table in the chat.

Its own workflow (how it works from A to Z) is drawn in the repository's `docs/workflow/`.

## Three flows

| The person says | Flow |
|---|---|
| "plan my week" | **Week**: up to 7 days, Sunday to Saturday unless they say their week starts another day |
| "plan my weekend" | **Weekend**: their weekend days (ask which), at most 3 tasks, plus a fun or personal item if they want one |
| "review my week" | **Review**: mark what got done, score it, move the rest to next week |

## 1. Collect the tasks

Never invent a task. Gather them from what is really there:

1. **Last week's plan.** If a saved plan file from last week is in reach (see step 5), everything still open
   in it carries over: its review's "Moves to next week" list and any decision still waiting. Put each one
   in `carried_over` in its exact words. Never reviewed? Offer to review it first (step 6). In a fresh chat,
   ask whether they have one to paste.
2. **A Backloop board, only if one exists.** If the working folder or the person's Workspace has Backloop
   task files (`<project>/.pipeline/*.md`), read each open card's title, project and status (idea, plan,
   checklist, active, review). Cards waiting for the person's own press or answer are **decisions**.
   **Read only**: never edit a task file, never run a command that moves a card, never press a gate.
   No board? Skip this quietly.
3. **Ask them.** "What else is on this week?" They can type, paste a list or upload a file. Personal items
   (gym, family, study) are welcome but optional; never add one they did not mention.

## 2. Ask a few questions

Ask with clickable choices where the app has them, always with a way to type their own answer. Ask only
what you do not already know.

1. **Free time:** how many hours, and which days are free or off? (Per day if they know it.)
2. **The #1 goal:** offer their real projects to click. Up to two more goals are optional.
   **Then understand each goal, one question at a time.** For the **#1 goal** ask four:
   - *"Why does it matter to you?"* If the answer is a word or two, ask one gentle follow-up.
   - *"How will you know it's done?"* Help them make it something they can check on Saturday.
   - *"What could stop you this week?"*
   - *"What's the very first step?"* You may offer two or three likely first steps from what you know of
     their work, always with a way to type their own.

   For **goals 2 and 3** ask only *"Why does it matter to you?"*, so it stays quick.

   After each answer, **polish their words into one clear sentence and show it**: "Here's how I'd write it:
   ... Right?" Keep their meaning and their facts; never add one they did not give. They say yes or change
   it. A question they skip is left out, and its line never appears. The answers go in the goal's `why`,
   `done_when`, `risk` and `first_step`. Give the goal the `project` of the cards that serve it, so the
   pages count its tasks and hours ("This week: 4 tasks · 6.5 h · Mon to Wed").
3. **Personal items:** add some, or skip?
4. Weekend flow only: **which days are your weekend?**

## 3. Build the plan

- **Rank:** decisions waiting on them first (they block other work), then active and review work, then
  plan and idea work. Personal items go where they asked.
- **Use what could stop them.** If the #1 goal's risk is time or other work crowding in, put its tasks
  early in the week and keep a buffer near them.
- **Fit:** put each task in a day. A day's tasks must not add up to more than its free hours; the tool
  refuses an overfilled day. Times are in quarter hours (0.25, 0.5, 1, 1.5 ...).
- **Leave room:** a week plan keeps **at least one buffer slot** (`"kind": "buffer"`), because things take
  longer than planned. Put it mid-week or near the hardest work.
- **Too much work?** Do not squeeze. Ask which tasks wait for next week, then fit again.
- Write task titles short, verb first: "Send the report for review", not a paragraph.
- **Carried-over work:** when you put a carried-over item on a day, keep its exact words as the title if
  they fit (48 characters). If you shorten or reword it, give that card `"from_last_week"` with its exact
  words from `carried_over`. That link is how the review knows it was planned: done work stays gone and
  open work moves on once. One carried-over item goes on one card; the tool refuses two cards for the same
  one. A carried-over item left off every day shows as "not planned".

## 4. Read it back

Say the goal with its why, done-when, risk and first step, then the plan day by day in plain words ("Sunday: choose the new logo, 1 hour. Monday: ...") and the
total hours. Wait for their yes. Change what they ask and read it back again. Never draw before the yes.

**Then write the advice yourself, without asking anything more.** Up to five short tips for their week
(three is usual), drawn on its own page after the goals. Each tip is a `title`, a sentence or two of
`text`, and `because`: **their own words, copied from the plan file** (a goal, its why, done-when, risk or
first step, or a card title), so they see what the tip came from. The tool refuses a `because` that is not
in the plan. Base every tip on what they told you. A tip may name real places, hotels or opening times when
it helps (a trip, an event); give it a `check` such as "Check opening hours and prices before you book",
because those facts change and you can be wrong. Advice never adds a card to the board, and they never have
to answer it. No advice that fits? Leave `advice` out; the page is then not drawn.

## 5. Deliver

**Where code can run** (coding agents, and chat apps with code execution):

1. Write the plan file as JSON. Format: [references/plan-format.md](references/plan-format.md); examples in
   `examples/`.
2. Draw it:
   ```bash
   python3 <this skill's folder>/scripts/draw_week.py plan.json -o "Week Plan 2026-10-04.pdf"
   ```
   A week with goals is a booklet: page 1 the board (with what is waiting on them and what carried over
   under it, or on a page of its own when the board is full), then **Top goals**, then **advice** when
   there is some. A weekend keeps its goal under the board, on one page.

   **When they ask for an HTML page** (to tick tasks off during the week), add `--html`:
   ```bash
   python3 <this skill's folder>/scripts/draw_week.py plan.json --html -o "Week Plan 2026-10-04.html"
   ```
   One file, no internet needed. They click a task when it is done; the score, the day totals and the
   goals move with it. On a phone it opens on **today**: day tabs along the top, today's tasks as big
   cards, and the score with Save plan fixed at the bottom; a computer shows the whole board. **Save plan** downloads the plan file with their ticks in it, under the plan file's
   own name. Tell them to keep it with the week's PDF: the review reads it.
   It needs Python 3.9+ and `reportlab` (already in Claude's and ChatGPT's sandboxes; elsewhere
   `pip install reportlab`, asking first if your rules say installs need approval).
3. It checks everything first. If it refuses, it lists numbered reasons: **change exactly those in the
   plan file and run it again.** Never draw the PDF another way to get around a refusal, and never edit
   the tool to silence one. It also names each carried-over item no card takes on: if you did plan one
   under a shorter title, add the `"from_last_week"` link to that card.
4. Look at the pages if you can. Render them into a new empty folder, so no file of the person's is ever
   overwritten; the pictures are only for your check, not part of the result:
   ```bash
   preview="$(mktemp -d)" && pdftoppm -r 70 -png "<file>.pdf" "$preview/page" && echo "$preview"
   ```
   No `mktemp`? Make any new empty folder and render into it. If you cannot render pages, say so.
5. Save the PDF **and the plan file next to it**, so the review can reopen it: where the person's own
   instructions say; else a `week-plans/` folder in the current working folder; in a chat sandbox, its
   outputs folder. Never hard-code a path from another machine.

**Where code cannot run:** give the same plan as a table in the chat, one row per day, and offer the plan
file as a code block so a later session can draw it. The table is in
[references/chat-table.md](references/chat-table.md).

Hand over in two to four plain sentences: the #1 goal, hours planned of hours free (planned includes buffer
time, as on the PDF), what is waiting on them, and where the file is. Then stop.

## 6. Review the week

1. Open last week's plan file (or ask them to paste it, or the table). If they ticked tasks on the HTML
   page and pressed **Save plan**, the saved file (usually in their Downloads) already holds the ticks:
   use it.
2. Ask which items got done, as one click list. Ticks already saved from the HTML page are read back for a
   quick "still right?", not asked again. Every item except buffers gets `"done": true` or `false`; the
   tool refuses a review with an item left unmarked.
3. For each goal, ask their verdict: *"Did you reach it? Done when: ..."* with three clicks, **Reached**,
   **Close**, **Not yet**. It goes in the goal's `result` and shows as a badge on the Top goals page.
4. Draw it the same way; the PDF becomes a **Week Review**: ticks on the board, a score
   ("7 of 10 done"), what is still waiting on them, what moves to next week, and each goal's verdict.
5. Say the score plainly and kindly; no lecture. Offer to plan next week: its `carried_over` is, word for
   word, everything still open (the "Moves to next week" list and any decision still waiting).

## Never

- Never press a board gate (Commit, Accept, Reject) or change a task's stage. The board is read only.
- Never create calendar events, send messages or emails, or set reminders unless the person asks for that
  in their own words, and then hand over to the tool that does it.
- Never add tasks, personal items or goals they did not give you. Advice is the one place for your own
  ideas, and it stays on its own page, never on the board.
- Never restyle the PDF, swap its fonts or colours, or add charts or dashboards.

## Limits

Say these when they matter:

- English text only; emoji are refused (the house font cannot draw them).
- A4 landscape, 1 to 7 days (weekend: 1 to 3). About 6 to 8 cards fit in one day's column; more is refused.
- The Top goals page lists the #1 goal's first 8 cards, then "and N more". Three goals with every answer
  near its limit can overfill the page; the tool refuses it and says to shorten.
- Task titles up to 48 characters and 3 lines in their card.

## Files

| File | What it is |
|---|---|
| `scripts/draw_week.py` | the drawing tool (plan file in, Week Board PDF or, with `--html`, the page to tick off) |
| `references/plan-format.md` | the plan file format and its rules |
| `references/chat-table.md` | the table to give where code cannot run |
| `examples/` | a week, a weekend and a reviewed week |
| `assets/` | the Plus Jakarta Sans font (SIL Open Font License, `assets/fonts/OFL.txt`), `brand.json` and the logo |

## Your own brand

Whose name, logo and website the PDF carries comes from `assets/brand.json` (WorkSpace Labs by default):
`{"name": "...", "accent": "<one word of the name>", "website": "...", "logo": "<png beside it>"}`.
Change it only when the person asks for their own brand.
