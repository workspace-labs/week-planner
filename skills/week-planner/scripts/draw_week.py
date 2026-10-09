#!/usr/bin/env python3
"""Draws a Week Board PDF from a plan file, or the same week as an HTML page to tick off.

    python3 draw_week.py plan.json -o "Week Plan 2026-10-04.pdf"
    python3 draw_week.py plan.json --html          (the HTML page, "Week Plan 2026-10-04.html")
    python3 draw_week.py plan.json --check         (checks only, writes nothing)

Needs Python 3.9+ and the reportlab package. The file format is in references/plan-format.md.
Whose name, logo and website the PDF carries comes from assets/brand.json.
Exit codes: 0 drawn or checked, 1 the plan needs changes (each one is listed), 2 bad command,
3 reportlab is missing.
"""

import argparse
import json
import os
import sys

sys.dont_write_bytecode = True          # keep the skill folder free of cache files
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Draw a Week Board PDF from a plan file.")
    parser.add_argument("plan", nargs="?", help="the plan file (JSON)")
    parser.add_argument("-o", "--output", help='where to write it (default: "Week Plan <first date>.pdf" beside the plan)')
    parser.add_argument("--html", action="store_true", help="write the HTML page to tick tasks off, instead of the PDF")
    parser.add_argument("--check", action="store_true", help="check the plan and its layout without drawing")
    parser.add_argument("--version", action="store_true", help="print the tool's version")
    args = parser.parse_args(argv)

    try:
        import reportlab  # noqa: F401
    except ImportError:
        print("The drawing tool needs the Python package reportlab. Install it with:  pip install reportlab",
              file=sys.stderr)
        return 3

    from week_tool import VERSION, brand, layout, model, page, pages, theme

    if args.version:
        print("week-planner drawing tool %s" % VERSION)
        return 0
    if not args.plan:
        parser.print_usage(sys.stderr)
        return 2

    theme.register_fonts()
    try:
        owner = brand.load()
        plan = model.load(args.plan)
        columns = layout.lay_out(plan)
    except model.PlanError as err:
        return _refuse(err.problems)
    problems = pages.preflight(plan, owner)
    if problems:
        return _refuse(problems)

    work = plan.work
    print("Checked: %d days, %d items, %s planned of %s free." % (
        len(plan.days), len(work), model.hours_text(sum(d.planned for d in plan.days)),
        model.hours_text(sum(d.free_hours for d in plan.days if not d.off))))
    print("No day is overfilled, and every word fits its card.")
    for text in plan.unplanned_carry_over:
        print('Carried over but on no day: "%s". If a card is this item under a shorter title, '
              'give that card "from_last_week": "%s".' % (text, text))
    if args.check:
        print("Ready to draw.")
        return 0

    kind = "Weekend Plan" if plan.mode == "weekend" else "Week Plan"
    if plan.reviewed:
        kind = "Week Review"
    output = args.output or os.path.join(os.path.dirname(os.path.abspath(args.plan)), "%s %s.%s" % (
        kind, plan.days[0].date.isoformat(), "html" if args.html else "pdf"))
    # A typo in -o must never replace the JSON needed for the review, even via an alias.
    same_path = os.path.normcase(os.path.realpath(output)) == os.path.normcase(os.path.realpath(args.plan))
    try:
        same_path = same_path or os.path.samefile(output, args.plan)
    except OSError:
        pass                                    # a new output file has no identity yet
    if same_path:
        print("The output would overwrite the plan file. Choose a different PDF or HTML filename.", file=sys.stderr)
        return 2
    folder = os.path.dirname(os.path.abspath(output))
    if not os.path.isdir(folder):
        print("The folder for the output does not exist: %s" % folder, file=sys.stderr)
        return 2
    try:
        if args.html:
            with open(args.plan, encoding="utf-8-sig") as handle:
                raw = json.load(handle)
            page.write(plan, raw, os.path.basename(args.plan), owner, output)
            print("Wrote the page to tick off: %s" % os.path.abspath(output))
            return 0
        total = pages.build(plan, columns, owner, output)
    except OSError as err:
        print("The output could not be written: %s. Choose a writable file in an existing folder." % err,
              file=sys.stderr)
        return 2
    print("Drew %d page%s: %s" % (total, "" if total == 1 else "s", os.path.abspath(output)))
    return 0


def _refuse(problems):
    print("Not drawn yet. Change these in the plan file, then run again:", file=sys.stderr)
    for number, problem in enumerate(problems, 1):
        print("  %d. %s" % (number, problem), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
