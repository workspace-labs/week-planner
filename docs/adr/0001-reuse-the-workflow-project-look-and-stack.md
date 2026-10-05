# 0001. Reuse workflow-project's look and stack

Date: 2026-10-05 · Status: accepted (owner chose concept A, the Week Board, and the PDF result)

## Context

The owner wants week-planner to look like one family with workflow-project and to run in every agent.

## Decision

Python 3.9+ with `reportlab`, the same Plus Jakarta Sans files, the same colour values and the same
`brand.json`, copied into this skill so it installs on its own. The page is drawn directly on a canvas
(fixed layout), with geometry in `layout.py` kept apart from painting in `pages.py` so tests can check it.

## Consequences

- Works in Claude's and ChatGPT's sandboxes with no install, like workflow-project.
- The look is duplicated, not shared: a change to workflow-project's theme must be copied here by hand.
  Accepted, because a shared package would make each skill unable to install alone.
