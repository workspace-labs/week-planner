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
| `goals` | no | Up to 3 short sentences (70 characters each). The first is the #1 goal, shown in a band on the board. |
| `carried_over` | no | Up to 8 items carried from last week (70 characters each). |

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

## The rules the tool holds

- A day's items never add up to more than its `free_hours`.
- A week plan of 3 or more days has at least one buffer item.
- A weekend plan has at most 3 tasks or decisions, and at least one personal item.
- Every word fits its card, a title takes at most 3 lines, and a day's cards fit its column.
- English text only: characters the house font cannot draw (emoji, other scripts) are refused.

Each refusal is a numbered sentence saying exactly what to change.
