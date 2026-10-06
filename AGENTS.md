# AGENTS.md: working on week-planner

For coding agents changing this repository. What the skill does is in `README.md`; what it must never do
is in `docs/scope.md`.

## Test

```bash
python3 -B -m unittest discover -s tests
```

The layout tests judge the board with their own rectangle maths, never the tool's helpers. Look at the
drawn pages too:

```bash
for ex in week weekend week-reviewed; do
  python3 skills/week-planner/scripts/draw_week.py skills/week-planner/examples/$ex.json -o "/tmp/$ex.pdf"
done
```

## Rules for this repository

- Keep `skills/week-planner/` clean: no `__pycache__`, no drawn PDFs, no test files. It is installed and
  uploaded as it is.
- The look lives in `skills/week-planner/scripts/week_tool/theme.py` and copies workflow-project's values; it is the owner's decision.
- Geometry (`skills/week-planner/scripts/week_tool/layout.py`) never imports drawing code.
- Every change to the skill (`skills/week-planner/`) bumps `VERSION` in `skills/week-planner/scripts/week_tool/__init__.py` and adds a
  dated `CHANGELOG.md` entry. A README or docs-only change goes under `[Unreleased]` in `CHANGELOG.md`.
- After a change, rebuild `dist/week-planner.zip` (command in `README.md`).
- Never commit or push without the owner's word.
