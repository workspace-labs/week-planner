"""0.3.0: the HTML page to tick off. Its words, its safety, and (where Chrome is installed) a real browser
clicking a task and pressing Save plan."""

import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import support
import draw_week

CHROME = next((p for p in (
    os.environ.get("CHROME_BIN", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    shutil.which("google-chrome") or "", shutil.which("chromium") or "",
    os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
    os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
) if p and os.path.isfile(p)), "")

# Run inside the page after it loads: click the first card, read what moved, then press Save plan and
# catch the file it would hand over. The answers land in a <pre id="probe"> for --dump-dom to read.
PROBE = r"""<script>
window.addEventListener("load", function () {
  var out = {};
  var savedText = null;
  URL.createObjectURL = function (blob) { blob.text().then(function (t) { savedText = t; finish(); }); return "#saved"; };
  HTMLAnchorElement.prototype.click = function () { out.downloadName = this.download; };   // no real download
  var cards = document.querySelectorAll(".board button.card");
  out.cards = cards.length;
  out.before = document.querySelector(".score .big").textContent;
  out.goalBefore = (document.querySelector(".progtxt") || {}).textContent || "";
  cards[0].click();
  out.after = document.querySelector(".score .big").textContent;
  out.pressed = cards[0].getAttribute("aria-pressed");
  out.goalAfter = (document.querySelector(".progtxt") || {}).textContent || "";
  out.pages = document.querySelectorAll("section.page").length;
  out.text = document.body.innerText;
  out.focus = (document.querySelector(".focus") || {}).innerText || "";
  document.querySelector("button.save").click();
  out.savedNote = document.querySelector(".saved").textContent;
  function finish() {
    out.saved = savedText;
    var pre = document.createElement("pre"); pre.id = "probe"; pre.textContent = JSON.stringify(out);
    document.body.appendChild(pre);
  }
});
</script>"""


# The phone view (0.4.0), at a phone's width with "today" pinned to Tue 6 Oct.
PHONE_PROBE = r"""<script>
window.addEventListener("load", function () {
  var out = {}, style = function (sel) { return getComputedStyle(document.querySelector(sel)); };
  var titles = function () { return Array.prototype.map.call(document.querySelectorAll(".panel .card .t"), function (n) { return n.textContent; }); };
  out.board = style(".scroll").display;
  out.phone = style(".phone-week").display;
  out.bar = style(".score").position;
  var tabs = document.querySelectorAll(".tab");
  out.tabs = tabs.length;
  out.selected = Array.prototype.indexOf.call(tabs, document.querySelector(".tab.sel"));
  out.head = document.querySelector(".dayhead").textContent;
  out.today = titles();
  document.querySelector(".panel .card").click();
  out.after = document.querySelector(".score .big").textContent;
  out.boardTwin = document.querySelectorAll(".board .card.done").length;
  out.dots = document.querySelectorAll(".tab.sel .dots i.done").length;
  tabs[3].click();
  out.wed = titles();
  out.overflow = document.documentElement.scrollWidth - window.innerWidth;
  var pre = document.createElement("pre"); pre.id = "probe"; pre.textContent = JSON.stringify(out);
  document.body.appendChild(pre);
});
</script>"""


def chrome(page, html, tmp, size="800,600", before=""):
    """Runs the page in headless Chrome with a probe; returns what the probe found."""
    with open(page, "w", encoding="utf-8") as handle:
        handle.write(html.replace("<body>", "<body>" + before, 1))
    dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--virtual-time-budget=4000",
                          "--window-size=" + size, "--user-data-dir=" + os.path.join(tmp, "chrome-" + size),
                          "--dump-dom", Path(page).resolve().as_uri()], capture_output=True,
                         text=True, encoding="utf-8", timeout=60).stdout
    probe = re.search(r'<pre id="probe">(.*?)</pre>', dom, re.S)
    if not probe:
        return None
    return json.loads(probe.group(1).replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = draw_week.main(list(args))
    return code, out.getvalue(), err.getvalue()


class Page(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, data, name="plan.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w") as handle:
            json.dump(data, handle)
        code, stdout, stderr = run(path, "--html")
        self.assertEqual(code, 0, stderr)
        out = re.search(r"Wrote the page to tick off: (.+)", stdout).group(1)
        with open(out, encoding="utf-8") as handle:
            return out, handle.read()

    def example(self, name):
        with open(os.path.join(support.EXAMPLES, name + ".json")) as handle:
            return json.load(handle)

    def test_default_name_beside_the_plan(self):
        out, _ = self.write(self.example("week"))
        self.assertEqual(os.path.basename(out), "Week Plan 2026-10-04.html")
        self.assertEqual(sorted(os.listdir(self.tmp)), ["Week Plan 2026-10-04.html", "plan.json"], "no PDF as well")

    def test_never_reaches_the_network(self):
        _, html = self.write(self.example("week"))
        self.assertIsNone(re.search(r"(src|href)=[\"']?https?:|url\(https?:|@import|fetch\(|XMLHttpRequest", html))
        self.assertIn("data:font/ttf;base64,", html)

    def test_words_are_text_never_markup(self):
        data = support.plan(title="Fish </script> & chips", goals=[{"goal": "Ship <b>it</b>", "why": "</script><i>x"}])
        _, html = self.write(data)
        self.assertEqual(html.count("</script>"), 2, "the plan's words can never close a script early")
        self.assertIn("<title>Fish &lt;/script&gt; &amp; chips</title>", html)
        self.assertNotIn("innerHTML", html)

    def test_refused_plan_writes_no_page(self):
        path = os.path.join(self.tmp, "bad.json")
        with open(path, "w") as handle:
            json.dump(support.plan(advice=[{"title": "Rest", "text": "Sleep early.", "because": "You said you are tired"}]),
                      handle)
        code, _, stderr = run(path, "--html")
        self.assertEqual(code, 1)
        self.assertIn('"because" must repeat', stderr)
        self.assertEqual(os.listdir(self.tmp), ["bad.json"])

    @unittest.skipUnless(CHROME, "needs Chrome")
    def test_edited_plan_does_not_inherit_another_tasks_ticks(self):
        data = support.plan()
        out, html = self.write(data)
        first = chrome(out, html.replace("</body>", PROBE + "</body>"), self.tmp)
        self.assertEqual(first["after"], "1 of 2 done")
        # Regenerate the same file, title, dates and card count with different work.
        data["days"][0]["items"][0]["title"] = "Choose another direction"
        out, html = self.write(data)
        second = chrome(out, html.replace("</body>", PROBE + "</body>"), self.tmp)
        self.assertEqual(second["before"], "0 of 2 done", "new work must not start checked")

    @unittest.skipUnless(CHROME, "needs Chrome")
    def test_unchanged_plan_keeps_its_ticks_on_reopen(self):
        out, html = self.write(support.plan())
        first = chrome(out, html.replace("</body>", PROBE + "</body>"), self.tmp)
        second = chrome(out, html.replace("</body>", PROBE + "</body>"), self.tmp)
        self.assertEqual((first["after"], second["before"]), ("1 of 2 done", "1 of 2 done"))

    @unittest.skipUnless(CHROME, "needs Chrome")
    def test_new_review_marks_are_not_replaced_by_old_browser_ticks(self):
        data = support.plan()
        out, html = self.write(data)
        chrome(out, html.replace("</body>", PROBE + "</body>"), self.tmp)
        for day in data["days"]:
            for item in day["items"]:
                if item.get("kind") != "buffer":
                    item["done"] = True
        out, html = self.write(data)
        review = chrome(out, html.replace("</body>", PROBE + "</body>"), self.tmp)
        self.assertEqual(review["before"], "2 of 2 done", "the updated source marks take precedence")

    @unittest.skipUnless(CHROME, "needs Chrome")
    def test_focus_keeps_unplanned_carry_and_updates_decisions(self):
        data = support.plan(carried_over=["Book the dentist appointment"])
        out, html = self.write(data)
        result = chrome(out, html.replace("</body>", PROBE + "</body>"), self.tmp)
        self.assertIn("Book the dentist appointment", result["text"])
        self.assertIn("MOVES TO NEXT WEEK", result["text"])
        self.assertIn("Run the checks", result["text"])
        # The first card is the decision the probe just completed.
        self.assertNotIn("Pick a direction", result["focus"])

    @unittest.skipUnless(CHROME, "needs Chrome")
    def test_weekend_shows_its_goal_details(self):
        data = {"mode": "weekend", "goals": [{"goal": "Fix the bicycle", "why": "Cycle to work",
                "done_when": "The bicycle is ready", "project": "Bicycle"}],
                "days": [{"date": "2026-10-16", "free_hours": 2,
                          "items": [{"title": "Repair the tyre", "hours": 1, "project": "Bicycle"}]}]}
        out, html = self.write(data)
        result = chrome(out, html.replace("</body>", PROBE + "</body>"), self.tmp)
        self.assertIn("Cycle to work", result["text"])
        self.assertIn("The bicycle is ready", result["text"])
        self.assertIn("This week", result["text"])

    @unittest.skipUnless(CHROME, "needs Chrome")
    def test_phone_wraps_long_titles_that_fit_the_pdf(self):
        data = support.plan(title="W" * 28, goals=[{"goal": "W" * 35, "why": "Make room for next week"}])
        out, html = self.write(data)
        probe = '''<script>window.addEventListener("load", function () {
          var p = document.createElement("pre"); p.id = "probe";
          p.textContent = JSON.stringify({overflow: document.documentElement.scrollWidth - window.innerWidth,
                                         width: window.innerWidth}); document.body.appendChild(p);
        });</script>'''
        result = chrome(out, html.replace("</body>", probe + "</body>"), self.tmp, size="360,800")
        self.assertLessEqual(result["width"], 640, "the phone layout is active")
        self.assertLessEqual(result["overflow"], 0, "valid plan text stays on the phone screen")

    @unittest.skipUnless(CHROME, "needs Chrome")
    def test_click_moves_the_score_and_save_keeps_the_ticks(self):
        data = self.example("week")
        out, html = self.write(data, "Week Plan 2026-10-04.json")
        result = chrome(out, html.replace("</body>", PROBE + "</body>"), self.tmp)
        self.assertTrue(result, "the page ran in Chrome")
        work = [i for d in data["days"] for i in d["items"] if i.get("kind") != "buffer"]
        self.assertEqual(result["cards"], len(work))
        self.assertEqual(result["pages"], 3, "board, top goals, advice")
        self.assertEqual(result["before"], "0 of %d done" % len(work))
        self.assertEqual(result["after"], "1 of %d done" % len(work))
        self.assertEqual(result["pressed"], "true")
        self.assertEqual((result["goalBefore"], result["goalAfter"]), ("0 of 3 done", "0 of 3 done"),
                         "the first card (a Brand decision) does not serve goal 1")
        for words in ("WHAT COULD STOP ME", "The client is slow to reply", "BECAUSE YOU SAID", "Advice for your week"):
            self.assertIn(words, result["text"])
        self.assertIn("Week Plan 2026-10-04.json", result["savedNote"])
        self.assertEqual(result["downloadName"], "Week Plan 2026-10-04.json", "saved under the plan file's own name")
        saved = json.loads(result["saved"])
        marks = [i.get("done") for d in saved["days"] for i in d["items"] if i.get("kind") != "buffer"]
        self.assertEqual(marks, [True] + [False] * (len(work) - 1))
        self.assertTrue(all("done" not in i for d in saved["days"] for i in d["items"] if i.get("kind") == "buffer"))
        saved_plain = json.loads(result["saved"])
        for day in saved_plain["days"]:
            for item in day["items"]:
                item.pop("done", None)
        self.assertEqual(saved_plain, data, "the save changes nothing but the ticks")
        path = os.path.join(self.tmp, "saved.json")
        with open(path, "w") as handle:
            handle.write(result["saved"])
        self.assertEqual(run(path, "--check")[0], 0, "the saved plan draws again, as a review")

    @unittest.skipUnless(CHROME, "needs Chrome")
    def test_phone_shows_today_first(self):
        out, html = self.write(self.example("week"))
        result = chrome(out, html.replace("</body>", PHONE_PROBE + "</body>"), self.tmp, size="500,900",
                        before='<script>window.WEEK_PLANNER_TODAY = "2026-10-06";</script>')
        self.assertTrue(result, "the page ran in Chrome")
        self.assertEqual((result["board"], result["phone"]), ("none", "block"), "one day at a time, not the board")
        self.assertEqual(result["bar"], "fixed", "the score and Save stay at the bottom")
        self.assertEqual((result["tabs"], result["selected"]), (7, 2), "opens on today, Tuesday")
        self.assertIn("TODAY", result["head"])
        self.assertEqual(result["today"], ["Send the report for review", "Gym"])
        self.assertEqual(result["after"], "1 of 10 done")
        self.assertEqual((result["boardTwin"], result["dots"]), (1, 1), "the board's card and the day's dot tick too")
        self.assertEqual(result["wed"], ["Review the new website", "Approve the budget: yes or no"])
        self.assertLessEqual(result["overflow"], 0, "nothing runs off the side of the screen")


if __name__ == "__main__":
    unittest.main()
