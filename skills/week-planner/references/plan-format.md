# The plan file

One JSON object. The drawing tool refuses any unknown field by name, so a typo never goes unnoticed.

## A complete small file

```json
{
  "title": "This week",
  "mode": "week",
  "goals": ["Deliver the client report"],
  "carried_over": ["Write the README"],
  "days": [
    {"date": "2026-10-04", "free_hours": 2, "items": [
      {"title": "Choose the new logo", "kind": "decision", "project": "Brand", "hours": 1}
    ]},
    {"date": "2026-10-05", "free_hours": 3, "items": [
      {"title": "Draft the client report", "stage": "active", "project": "Client work", "hours": 2},
      {"kind": "buffer", "hours": 1}
    ]},
    {"date": "2026-10-06", "free_hours": 0, "off": true}
  ]
}
```

## The plan

| Field | Needed | What it is |
|---|---|---|
| `days` | yes | 1 to 7 days (weekend: 1 to 3), one after another with none missing. |
| `mode` | no | `"week"` (default) or `"weekend"`. |
| `title` | no | Up to 40 characters; its last word is drawn in blue. Default "This week" or "This weekend". |
| `goals` | no | Up to 3 goals. Each is a short sentence (70 characters), or a goal object (below). The first is the #1 goal, shown in a band on the board. |
| `carried_over` | no | Up to 8 items carried from last week (70 characters each), in their exact words, each once. |

## A goal object

```json
{"goal": "Docker skill passes round 4", "why": "Proof the skill is professional",
 "done_when": "Codex says APPROVED", "project": "Docker skill"}
```

| Field | Needed | What it is |
|---|---|---|
| `goal` | yes | The goal, up to 70 characters. |
| `why` | no | Why it matters, in the person's words, up to 90 characters. |
| `done_when` | no | How they will know it is done, in their words, up to 90 characters. |
| `project` | no | The `project` of the cards that serve this goal (capital letters aside). The board counts those cards under the goal: "4 tasks · 6.5 h · Mon to Wed", or "3 of 4 done" in a review. A project no card has is refused. |

Under the goal, the PDF shows a labelled line for each one given: **Why**, **Done when**, **This week**.

## A day

| Field | Needed | What it is |
|---|---|---|
| `date` | yes | `YYYY-MM-DD`. The weekday is worked out from it. |
| `free_hours` | yes | Hours free that day, 0 to 16, in quarter hours. |
| `off` | no | `true` for a rest day: it must hold no items. |
| `items` | no | The cards, top to bottom. |

## An item

| Field | Needed | What it is |
|---|---|---|
| `title` | yes (not for a buffer) | A few words, verb first, up to 48 characters. |
| `hours` | yes | 0.25 to 16, in quarter hours. Shown as "30 min", "1 h", "1.5 h". |
| `kind` | no | `task` (default), `decision` (waiting on the person: red), `personal`, or `buffer` (hatched, title defaults to "Buffer"). |
| `stage` | no | For a task or decision from a board: `idea`, `plan`, `checklist`, `active`, `review`. It sets the colour of the card's bar. |
| `project` | no | Up to 24 characters, shown on the card's second line. |
| `done` | review only | `true` or `false`. Once any item has it, every item except buffers must have it. |
| `from_last_week` | no | When this card plans a carried-over item under a shorter or different title: that item's exact words from `carried_over`. Not for a buffer. |

## The rules the tool holds

- A day's items never add up to more than its `free_hours`. "Planned" always means all of a day's items,
  buffer time included (each column, both page headers, the tool's check line); the review's score counts
  only real work, never buffers.
- A week plan of 3 or more days has at least one buffer item.
- A weekend plan has at most 3 tasks or decisions. Personal items are optional and do not count.
- Every word fits its card, a title takes at most 3 lines, and a day's cards fit its column.
- English text only: characters the house font cannot draw (emoji, other scripts) are refused.
- `from_last_week` repeats one `carried_over` entry word for word (capital letters and spacing aside).
- One carried-over item goes on one card: two cards planning the same item are refused, whether by title,
  by `from_last_week` or one of each.

## Carried-over items in a review

Each card plans at most one carried-over item: the one it names in `from_last_week`, or, without that
field, the one its title repeats. The link wins, so a card linked to one item never also plans another item
that happens to share its title. Buffer time plans nothing. That card's own `done` then decides the item:
done is gone, open moves on once, and an open decision stays under "Waiting on you". A carried-over item no
card plans moves to next week as "from last week, not planned".

```json
{"carried_over": ["Review the proposed changes to the customer onboarding guide"],
 "days": [{"date": "2026-10-18", "free_hours": 1, "items": [
   {"title": "Review onboarding changes", "hours": 1, "done": true,
    "from_last_week": "Review the proposed changes to the customer onboarding guide"}]}]}
```

Each refusal is a numbered sentence saying exactly what to change.
