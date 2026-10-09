"""The whole tool from the command line: drawn PDFs, their pages and their words."""

import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

import support
import draw_week

HAS_POPPLER = shutil.which("pdftotext") is not None


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = draw_week.main(list(args))
    return code, out.getvalue(), err.getvalue()


def pages(path):
    with open(path, "rb") as handle:
        return len(re.findall(rb"/Type\s*/Page[^s]", handle.read()))


class Draws(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def draw(self, name):
        out = os.path.join(self.tmp, name + ".pdf")
        code, stdout, stderr = run(os.path.join(support.EXAMPLES, name + ".json"), "-o", out)
        self.assertEqual(code, 0, stderr)
        return out

    def words(self, path):
        return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, check=True).stdout

    def test_week_has_board_and_focus(self):
        # 0.3.0: the board with its focus lists, then Top goals, then the advice
        out = self.draw("week")
        self.assertEqual(pages(out), 3)
        if HAS_POPPLER:
            text = self.words(out)
            board, goals, advice = text.split("\f")[:3]
            for word in ("This week", "WEEK PLAN", "#1 GOAL", "Choose the new", "Buffer", "WAITING ON YOU",
                         "CARRIED OVER", "Page 1 of 3", "16 h planned of 18.5 h free"):
                self.assertIn(word, board)
            self.assertNotIn("TOP GOALS", board, "the goals have their own page now")
            for word in ("Top goals", "WHY", "DONE WHEN", "WHAT COULD STOP ME", "The client is slow to reply",
                         "FIRST STEP", "THIS WEEK", "Mon to Thu", "Draft the client report", "THIS WEEK'S #1",
                         "The old logo no longer fits the brand", "Page 2 of 3"):
                self.assertIn(word, goals)
            for word in ("Advice for your week", "FROM THE AI", "BECAUSE YOU SAID", '"Family dinner"',
                         "CHECK THE DINNER TIME WITH THE FAMILY", "Page 3 of 3"):
                self.assertIn(word, advice)

    def test_review_scores_and_moves_on(self):
        out = self.draw("week-reviewed")
        if HAS_POPPLER:
            text = self.words(out)
            for word in ("WEEK REVIEW", "7 of 10 done", "MOVES TO NEXT WEEK", "Update the weekly sales sheet",
                         "Book the dentist appointment", "REACHED", "3 of 3 done"):
                self.assertIn(word, text)
            self.assertNotIn("THIS WEEK'S #1", text, "a review shows the verdict instead")
            focus = text.split("SCORE")[1]
            self.assertNotIn("Choose the new logo", focus.split("MOVES")[0].split("WAITING ON YOU")[-1],
                             "a decision made this week is no longer waiting")

    def test_weekend(self):
        out = self.draw("weekend")
        if HAS_POPPLER:
            self.assertIn("WEEKEND PLAN", self.words(out))

    def test_one_page_when_nothing_to_focus_on(self):
        path = os.path.join(self.tmp, "bare.json")
        with open(path, "w") as handle:
            handle.write('{"days": [{"date": "2026-10-04", "free_hours": 1, "items": [{"title": "Read", "hours": 1}]}]}')
        code, stdout, _ = run(path)
        self.assertEqual(code, 0)
        self.assertIn("Drew 1 page:", stdout)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "Week Plan 2026-10-04.pdf")))


class OnePage(unittest.TestCase):
    """0.2.0: columns end under the busiest day and the focus lists go below the board when they fit.
    0.3.0: a week's goals and advice follow on pages of their own; a weekend keeps its goal under the board."""

    def draw(self, data):
        from week_tool import brand, layout, model, pages as tool_pages, theme
        theme.register_fonts()
        plan = model.parse(data)
        columns = layout.lay_out(plan)
        tmp = tempfile.mkdtemp()
        out = os.path.join(tmp, "p.pdf")
        try:
            tool_pages.build(plan, columns, brand.load(), out)
            html = subprocess.run(["pdftotext", "-bbox", out, "-"], capture_output=True, text=True,
                                  check=True).stdout if HAS_POPPLER else ""
            return columns, pages(out), html
        finally:
            shutil.rmtree(tmp)

    @unittest.skipUnless(HAS_POPPLER, "needs pdftotext")
    def test_focus_under_the_board_never_touches_it_or_the_footer(self):
        from week_tool import layout
        expected = {"week.json": 3, "week-reviewed.json": 3, "weekend.json": 1}
        for path in support.examples():
            with open(path) as handle:
                columns, count, html = self.draw(json.load(handle))
            self.assertEqual(count, expected[os.path.basename(path)], path)
            first = html.split("</page>")[0]
            heads = [float(y) for y, w in re.findall(r'yMin="([\d.]+)" xMax="[\d.]+" yMax="[\d.]+">([A-Z]+)</word>', first)
                     if w in ("TOP", "WAITING", "MOVES", "CARRIED", "SCORE")]
            board_bottom = layout.PAGE_H - columns[0].bottom
            with self.subTest(path=path):
                self.assertTrue(heads, "the focus lists are on page 1")
                self.assertTrue(all(y > board_bottom for y in heads), "below the board")
                self.assertTrue(all(y < layout.PAGE_H - 56 for y in heads), "above the footer")

    def test_packed_week_keeps_the_second_page(self):
        data = support.plan(goals=["Ship it"])
        data["days"][1]["free_hours"] = 8
        data["days"][1]["items"] = [{"title": "A task with a fairly long title that wraps %d" % n, "hours": 1}
                                    for n in range(8)]
        columns, count, html = self.draw(data)
        from week_tool import layout
        self.assertLess(columns[0].bottom, layout.BOARD_BOTTOM + 60)
        self.assertEqual(count, 3, "board, focus, top goals")
        if HAS_POPPLER:
            self.assertIn("focus", html.split("</page>")[1])


class GoalRows(unittest.TestCase):
    """0.2.0: under a goal, the person's why and done-when, and a 'This week' line counted from the cards."""

    def rows(self, data):
        from week_tool import model, pages
        p = model.parse(data)
        return pages.goal_rows(p, p.goal_details[0])

    def data(self, reviewed=False):
        data = support.plan(goals=[{"goal": "Ship the checks", "why": "It proves the work", "project": "Checks"}])
        data["days"][0]["items"][0]["project"] = "Checks"
        data["days"][1]["items"][0]["project"] = "Checks"
        if reviewed:
            data["days"][0]["items"][0]["done"] = True
            data["days"][1]["items"][0]["done"] = False
        return data

    def test_counted_from_the_cards(self):
        self.assertEqual(self.rows(self.data()), [("Why", "It proves the work"),
                                                  ("This week", "2 tasks · 3 h · Sun to Mon")])

    def test_review_counts_done(self):
        self.assertEqual(self.rows(self.data(True))[-1], ("This week", "1 of 2 done · 3 h · Sun to Mon"))

    def test_nothing_given_nothing_shown(self):
        self.assertEqual(self.rows(support.plan(goals=["Ship it"])), [])

    @unittest.skipUnless(HAS_POPPLER, "needs pdftotext")
    def test_rows_are_drawn(self):
        tmp = tempfile.mkdtemp()
        try:
            path, out = os.path.join(tmp, "p.json"), os.path.join(tmp, "p.pdf")
            with open(path, "w") as handle:
                json.dump(self.data(), handle)
            self.assertEqual(run(path, "-o", out)[0], 0)
            text = subprocess.run(["pdftotext", out, "-"], capture_output=True, text=True, check=True).stdout
            for words in ("WHY", "It proves the work", "THIS WEEK", "tasks", "Sun to Mon"):
                self.assertIn(words, text)
            self.assertNotIn("DONE WHEN", text, "a field the person did not give is left out")
            self.assertNotIn("FIRST STEP", text)
        finally:
            shutil.rmtree(tmp)


class Focus(unittest.TestCase):
    """F01: in a review, last week's unscheduled carry-over must still be shown."""

    def sections(self, data):
        from week_tool import model, pages
        return dict((h, [t for _, t, _ in e]) for h, e in pages.focus_sections(model.parse(data)))

    def reviewed(self, carried):
        data = support.plan(carried_over=carried)
        data["days"][0]["items"][0]["done"] = False          # the decision stays open
        data["days"][1]["items"][0]["done"] = True
        data["days"][1]["items"].append({"title": "Write notes", "hours": 1, "done": False})
        return data

    def test_unscheduled_carry_over_survives_review(self):
        s = self.sections(self.reviewed(["Book the dentist"]))
        moving = s.get("MOVES TO NEXT WEEK", []) + s.get("CARRIED OVER", [])
        self.assertIn("Book the dentist", moving)
        self.assertIn("Write notes", moving)

    def test_carry_over_never_duplicates_or_revives(self):
        # scheduled and done, scheduled and open, and a still-open decision: none shown a second time
        s = self.sections(self.reviewed(["Run the checks", "Write notes", "Pick a direction"]))
        everything = [t for entries in s.values() for t in entries]
        self.assertNotIn("Run the checks", everything)
        self.assertEqual(everything.count("Write notes"), 1)
        self.assertEqual(everything.count("Pick a direction"), 1)


    # F01, round 3: last week's long title, planned this week under a shorter name (Codex's repro)
    LONG = "Review the proposed changes to the customer onboarding guide"

    def shortened(self, kind="task", done=True):
        item = {"title": "Review onboarding changes", "hours": 1, "done": done, "from_last_week": self.LONG}
        if kind == "decision":
            item["kind"] = "decision"
        return {"carried_over": [self.LONG], "days": [{"date": "2026-10-18", "free_hours": 1, "items": [item]}]}

    def everything(self, data):
        return [t for entries in self.sections(data).values() for t in entries]

    def test_shortened_carry_over_done_stays_gone(self):
        shown = self.everything(self.shortened(done=True))
        self.assertNotIn(self.LONG, shown)
        self.assertNotIn("Review onboarding changes", shown)

    def test_shortened_carry_over_open_appears_once(self):
        data = self.shortened(done=False)
        self.assertEqual(self.sections(data).get("MOVES TO NEXT WEEK"), ["Review onboarding changes"])
        self.assertNotIn(self.LONG, self.everything(data))

    def test_shortened_open_decision_appears_once(self):
        s = self.sections(self.shortened(kind="decision", done=False))
        self.assertEqual(s.get("WAITING ON YOU"), ["Review onboarding changes"])
        self.assertNotIn("MOVES TO NEXT WEEK", s)

    def test_buffer_never_claims_carry_over(self):
        # buffer time is room, not work: a carry-over that happens to be called "Buffer" is still open
        self.assertIn("Buffer", self.sections(self.reviewed(["Buffer"])).get("MOVES TO NEXT WEEK", []))

    @unittest.skipUnless(HAS_POPPLER, "needs pdftotext")
    def test_shortened_carry_over_pdf(self):
        tmp = tempfile.mkdtemp()
        try:
            path, out = os.path.join(tmp, "repro.json"), os.path.join(tmp, "repro.pdf")
            with open(path, "w") as handle:
                json.dump(self.shortened(done=True), handle)
            code, _, stderr = run(path, "-o", out)
            self.assertEqual(code, 0, stderr)
            text = subprocess.run(["pdftotext", out, "-"], capture_output=True, text=True, check=True).stdout
            self.assertIn("1 of 1 done", text)
            self.assertNotIn("customer onboarding guide", text)
        finally:
            shutil.rmtree(tmp)


    def test_conflicting_title_and_link_keeps_both_honest(self):
        # done card titled like one carried item but linked to another: the linked one is done, the other moves on
        data = {"carried_over": ["Write the summary", self.LONG],
                "days": [{"date": "2026-10-18", "free_hours": 1, "items": [
                    {"title": "Write the summary", "hours": 1, "done": True, "from_last_week": self.LONG}]}]}
        s = self.sections(data)
        self.assertEqual(s.get("MOVES TO NEXT WEEK"), ["Write the summary"])
        self.assertNotIn(self.LONG, self.everything(data))

    def test_open_personal_item_linked_appears_once(self):
        data = {"carried_over": ["Gym"], "days": [{"date": "2026-10-18", "free_hours": 1, "items": [
            {"title": "Gym session", "kind": "personal", "hours": 1, "done": False, "from_last_week": "gym"}]}]}
        self.assertEqual(self.everything(data), ["Gym session"])


class Preview(unittest.TestCase):
    """B04: the preview command SKILL.md gives never overwrites the person's files."""

    @unittest.skipUnless(shutil.which("pdftoppm"), "needs pdftoppm")
    def test_documented_preview_keeps_existing_files(self):
        with open(os.path.join(support.SKILL, "SKILL.md"), encoding="utf-8") as handle:
            line = next(l for l in handle if "pdftoppm" in l)
        command = line.split("`")[1] if "`" in line else line.strip()
        tmp = tempfile.mkdtemp()
        try:
            pdf = os.path.join(tmp, "plan.pdf")
            code, _, stderr = run(os.path.join(support.EXAMPLES, "weekend.json"), "-o", pdf)
            self.assertEqual(code, 0, stderr)
            work = os.path.join(tmp, "project")
            os.mkdir(work)
            mine = os.path.join(work, "page-1.png")
            with open(mine, "wb") as handle:
                handle.write(b"the person's own file")
            shown = []
            for _ in range(2):
                args = shlex.split(command.replace("<file>.pdf", pdf))
                args[0] = sys.executable
                done = subprocess.run(args, cwd=work, capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(done.returncode, 0, done.stderr)
                shown.append(done.stdout.strip())
            with open(mine, "rb") as handle:
                self.assertEqual(handle.read(), b"the person's own file")
            self.assertEqual(os.listdir(work), ["page-1.png"])
            self.assertNotEqual(shown[0], shown[1])
            for folder in shown:
                self.assertTrue(os.path.exists(os.path.join(folder, "page-1.png")), folder)
                shutil.rmtree(folder)
        finally:
            shutil.rmtree(tmp)


class PlannedHours(unittest.TestCase):
    """B06: "planned" counts buffer time everywhere (both page headers, every column, the check line);
    the done score never counts it. Expected totals come from the plan file itself, not the tool."""

    def plan(self, reviewed=False, buffer=True):
        days = [("2026-10-18", 4, [{"title": "Review the sample", "hours": 2}]),
                ("2026-10-19", 4, [{"title": "Call the supplier", "hours": 1}])]
        if buffer:   # a third day; a week of 3 or more days must keep a buffer
            days.append(("2026-10-20", 2, [{"title": "Write the notes", "hours": 1}, {"kind": "buffer", "hours": 1}]))
        if reviewed:
            for _, _, items in days:
                for item in items:
                    if item.get("kind") != "buffer":
                        item["done"] = item["title"] != "Call the supplier"
        return {"goals": ["Finish the sample work"],
                "days": [{"date": d, "free_hours": f, "items": i} for d, f, i in days]}

    def drawn(self, data):
        tmp = tempfile.mkdtemp()
        try:
            path, out = os.path.join(tmp, "p.json"), os.path.join(tmp, "p.pdf")
            with open(path, "w") as handle:
                json.dump(data, handle)
            code, stdout, stderr = run(path, "-o", out)
            self.assertEqual(code, 0, stderr)
            text = subprocess.run(["pdftotext", out, "-"], capture_output=True, text=True, check=True).stdout
            return stdout, text, pages(out)
        finally:
            shutil.rmtree(tmp)

    @unittest.skipUnless(HAS_POPPLER, "needs pdftotext")
    def test_planned_agrees_with_the_days(self):
        from week_tool import model
        for buffer in (True, False):
            for reviewed in (False, True):
                data = self.plan(reviewed, buffer)
                planned = sum(i["hours"] for d in data["days"] for i in d["items"])
                free = sum(d["free_hours"] for d in data["days"])
                expect = "%s planned of %s free" % (model.hours_text(planned), model.hours_text(free))
                with self.subTest(buffer=buffer, reviewed=reviewed):
                    stdout, text, count = self.drawn(data)
                    self.assertIn(expect, stdout)
                    self.assertEqual(text.count(expect), count, "every page header")
                    if reviewed:
                        work = [i for d in data["days"] for i in d["items"] if i.get("kind") != "buffer"]
                        self.assertIn("%d of %d done" % (sum(i["done"] for i in work), len(work)), text)

    @unittest.skipUnless(HAS_POPPLER, "needs pdftotext")
    def test_codex_reproduction(self):
        # 4 h of tasks and a 1 h buffer in 10 h free: 5 h planned, and the review still scores 2 of 3
        stdout, text, _ = self.drawn(self.plan(reviewed=True))
        self.assertIn("5 h planned of 10 h free", stdout)
        self.assertIn("5 h planned of 10 h free", text)
        self.assertIn("2 of 3 done", text)
        self.assertNotIn("4 h planned", text + stdout)


class Footer(unittest.TestCase):
    """F03: a long title and website never run into the page number."""

    @unittest.skipUnless(HAS_POPPLER, "needs pdftotext")
    def test_footer_never_reaches_page_number(self):
        from week_tool import brand, layout, model, pages, theme
        theme.register_fonts()
        owner = brand.load()
        owner.website = "W" * 60
        plan = model.parse({"title": "W" * 28 + " " + "I" * 10,
                            "days": [{"date": "2026-10-11", "free_hours": 1, "items": [{"title": "Read", "hours": 1}]}]})
        tmp = tempfile.mkdtemp()
        try:
            out = os.path.join(tmp, "f.pdf")
            pages.build(plan, layout.lay_out(plan), owner, out)
            html = subprocess.run(["pdftotext", "-bbox", out, "-"], capture_output=True, text=True, check=True).stdout
            words = [(float(a), float(b), float(c), w) for a, b, c, w in
                     re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="[\d.]+">([^<]*)</word>', html)]
            footer = [w for w in words if w[1] > layout.PAGE_H - 45]
            page_x = min(w[0] for w in footer if w[3] == "Page")
            left_end = max(w[2] for w in footer if w[0] < page_x)
            self.assertLess(left_end, page_x - 6.0)
        finally:
            shutil.rmtree(tmp)


class Booklet(unittest.TestCase):
    """0.3.0: the Top goals and advice pages fit, or are refused by name; nothing is squeezed."""

    def check(self, data):
        from week_tool import booklet, model, theme
        theme.register_fonts()
        return booklet.check(model.parse(data))

    def full_goal(self, n):
        return {"goal": "Goal %d with a fairly long name that still fits its line" % n,
                "why": "A reason long enough to wrap onto a second line in its narrow column, and more",
                "done_when": "A finish line long enough to wrap onto a second line in its column, and then more",
                "risk": "A risk long enough to wrap onto a second line in its narrow column too, and then more",
                "first_step": "A first step long enough to wrap onto a second line in its column, and then more"}

    def test_examples_fit(self):
        for path in support.examples():
            with open(path) as handle:
                self.assertEqual(self.check(json.load(handle)), [], path)

    def test_too_full_is_refused(self):
        data = support.plan(goals=[self.full_goal(n) for n in (1, 2, 3)])
        data["days"][1]["free_hours"] = 16
        data["days"][1]["items"] = [{"title": "Task %d with a title long enough to wrap" % n, "hours": 1,
                                     "project": "Checks"} for n in range(12)]
        data["goals"][0]["project"] = "Checks"
        self.assertIn("The Top goals page is too full", " ".join(self.check(data)))

    def test_long_word_is_refused(self):
        tip = {"title": "W" * 48, "text": "Short.", "because": "Pick a direction"}
        data = support.plan(advice=[tip, dict(tip, title="Fine")])      # two tips share a row, half width each
        self.assertIn('is too wide for the advice page', " ".join(self.check(data)))

    def test_many_cards_list_ends_with_and_more(self):
        if not HAS_POPPLER:
            self.skipTest("needs pdftotext")
        data = support.plan(goals=[{"goal": "Ship the checks", "project": "Checks"}])
        for day, numbers in ((0, range(5)), (1, range(5, 10))):
            data["days"][day]["free_hours"] = 6
            data["days"][day]["items"] = [{"title": "Check %d" % n, "hours": 1, "project": "Checks"} for n in numbers]
        tmp = tempfile.mkdtemp()
        try:
            path, out = os.path.join(tmp, "p.json"), os.path.join(tmp, "p.pdf")
            with open(path, "w") as handle:
                json.dump(data, handle)
            code, _, stderr = run(path, "-o", out)
            self.assertEqual(code, 0, stderr)
            goals = subprocess.run(["pdftotext", out, "-"], capture_output=True, text=True, check=True).stdout.split("\f")[-2]
            self.assertIn("and 2 more", goals)
            self.assertIn("10", goals, "the count is every card, not only the ones listed")
        finally:
            shutil.rmtree(tmp)


class Command(unittest.TestCase):
    def test_output_cannot_replace_the_plan_file(self):
        for html in (False, True):
            with self.subTest(html=html), tempfile.TemporaryDirectory() as tmp:
                path = os.path.join(tmp, "plan.json")
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump(support.plan(), handle)
                with open(path, "rb") as handle:
                    original = handle.read()
                code, _, stderr = run(path, "-o", path, *(["--html"] if html else []))
                self.assertEqual(code, 2)
                self.assertIn("plan file", stderr)
                with open(path, "rb") as handle:
                    self.assertEqual(handle.read(), original, "the JSON source is never an output file")

    def test_output_cannot_replace_a_hard_link_to_the_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, output = os.path.join(tmp, "plan.json"), os.path.join(tmp, "alias.pdf")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(support.plan(), handle)
            os.link(path, output)
            code, _, stderr = run(path, "-o", output)
            self.assertEqual(code, 2)
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(json.load(handle), support.plan())

    def test_utf8_bom_plan_works_for_pdf_and_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "plan.json")
            with open(path, "w", encoding="utf-8-sig") as handle:
                json.dump(support.plan(), handle)
            for ext, flags in (("pdf", []), ("html", ["--html"])):
                with self.subTest(ext=ext):
                    output = os.path.join(tmp, "plan." + ext)
                    code, _, stderr = run(path, "-o", output, *flags)
                    self.assertEqual(code, 0, stderr)
                    self.assertTrue(os.path.isfile(output))

    def test_unwritable_output_is_a_plain_command_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            for flags in ([], ["--html"]):
                with self.subTest(flags=flags):
                    code, _, stderr = run(os.path.join(support.EXAMPLES, "weekend.json"), "-o", tmp, *flags)
                    self.assertEqual(code, 2)
                    self.assertIn("could not be written", stderr)

    def test_check_writes_nothing(self):
        code, stdout, _ = run(os.path.join(support.EXAMPLES, "week.json"), "--check")
        self.assertEqual(code, 0)
        self.assertIn("Ready to draw.", stdout)

    def test_refusal_is_numbered_and_exit_1(self):
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "bad.json")
            with open(path, "w") as handle:
                handle.write('{"days": [{"date": "2026-10-04", "free_hours": 1, "items": [{"title": "Big", "hours": 3}]}]}')
            code, _, stderr = run(path)
            self.assertEqual(code, 1)
            self.assertIn("  1. Sun 4 Oct is overfilled", stderr)
            self.assertEqual(os.listdir(tmp), ["bad.json"])
        finally:
            shutil.rmtree(tmp)

    def test_huge_number_in_file_is_refused(self):
        # F05: a 401-digit whole number in the file is a numbered refusal, never a Python error
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "big.json")
            with open(path, "w") as handle:
                handle.write('{"days": [{"date": "2026-10-11", "free_hours": 1%s, "items": [{"title": "Read", "hours": 1}]}]}'
                             % ("0" * 400))
            code, _, stderr = run(path)
            self.assertEqual(code, 1)
            self.assertIn("  1. Sun 11 Oct", stderr)
            self.assertLess(len(stderr), 400)
        finally:
            shutil.rmtree(tmp)

    def test_unlinked_carry_over_is_named(self):
        # the planner shortened a carried-over title but forgot the link: the tool says so, without refusing
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "p.json")
            long = "Review the proposed changes to the customer onboarding guide"
            item = {"title": "Review onboarding changes", "hours": 1}
            for linked in (False, True):
                if linked:
                    item["from_last_week"] = long
                with open(path, "w") as handle:
                    json.dump({"carried_over": [long], "days": [{"date": "2026-10-18", "free_hours": 1, "items": [item]}]},
                              handle)
                code, stdout, _ = run(path, "--check")
                self.assertEqual(code, 0)
                self.assertEqual("Carried over but on no day" in stdout, not linked)
        finally:
            shutil.rmtree(tmp)

    def test_missing_folder_exit_2(self):
        code, _, stderr = run(os.path.join(support.EXAMPLES, "week.json"), "-o", "/no/such/folder/x.pdf")
        self.assertEqual(code, 2)

    def test_no_cache_files_in_skill(self):
        found = [d for d, _, _ in os.walk(support.SKILL) if d.endswith("__pycache__")]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
