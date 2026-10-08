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

import support
import draw_week

CHROME = next((p for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                           shutil.which("google-chrome") or "", shutil.which("chromium") or "") if p and os.path.exists(p)), "")

# Run inside the page after it loads: click the first card, read what moved, then press Save plan and
# catch the file it would hand over. The answers land in a <pre id="probe"> for --dump-dom to read.
PROBE = r"""<script>
window.addEventListener("load", function () {
  var out = {};
  var savedText = null;
  URL.createObjectURL = function (blob) { blob.text().then(function (t) { savedText = t; finish(); }); return "#saved"; };
  HTMLAnchorElement.prototype.click = function () { out.downloadName = this.download; };   // no real download
  var cards = document.querySelectorAll("button.card");
  out.cards = cards.length;
  out.before = document.querySelector(".score .big").textContent;
  out.goalBefore = (document.querySelector(".progtxt") || {}).textContent || "";
  cards[0].click();
  out.after = document.querySelector(".score .big").textContent;
  out.pressed = cards[0].getAttribute("aria-pressed");
  out.goalAfter = (document.querySelector(".progtxt") || {}).textContent || "";
  out.pages = document.querySelectorAll("section.page").length;
  out.text = document.body.innerText;
  document.querySelector("button.save").click();
  out.savedNote = document.querySelector(".saved").textContent;
  function finish() {
    out.saved = savedText;
    var pre = document.createElement("pre"); pre.id = "probe"; pre.textContent = JSON.stringify(out);
    document.body.appendChild(pre);
  }
});
</script>"""


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
    def test_click_moves_the_score_and_save_keeps_the_ticks(self):
        data = self.example("week")
        out, html = self.write(data, "Week Plan 2026-10-04.json")
        with open(out, "w", encoding="utf-8") as handle:
            handle.write(html.replace("</body>", PROBE + "</body>"))
        dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--virtual-time-budget=4000",
                              "--user-data-dir=" + os.path.join(self.tmp, "chrome"), "--dump-dom", "file://" + out],
                             capture_output=True, text=True, timeout=60).stdout
        probe = re.search(r'<pre id="probe">(.*?)</pre>', dom, re.S)
        self.assertTrue(probe, "the page ran in Chrome")
        result = json.loads(probe.group(1).replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))
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


if __name__ == "__main__":
    unittest.main()
