"""The whole tool from the command line: drawn PDFs, their pages and their words."""

import io
import os
import re
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
        out = self.draw("week")
        self.assertEqual(pages(out), 2)
        if HAS_POPPLER:
            text = self.words(out)
            for word in ("This week", "WEEK PLAN", "#1 GOAL", "Choose the new", "Buffer", "WAITING ON YOU",
                         "CARRIED OVER", "Page 1 of 2", "13.5 h planned of 18.5 h free"):
                self.assertIn(word, text)

    def test_review_scores_and_moves_on(self):
        out = self.draw("week-reviewed")
        if HAS_POPPLER:
            text = self.words(out)
            for word in ("WEEK REVIEW", "7 of 10 done", "MOVES TO NEXT WEEK", "Update the weekly sales sheet"):
                self.assertIn(word, text)
            focus = text.split("How the week")[1]
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


class Command(unittest.TestCase):
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

    def test_missing_folder_exit_2(self):
        code, _, stderr = run(os.path.join(support.EXAMPLES, "week.json"), "-o", "/no/such/folder/x.pdf")
        self.assertEqual(code, 2)

    def test_no_cache_files_in_skill(self):
        found = [d for d, _, _ in os.walk(support.SKILL) if d.endswith("__pycache__")]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
