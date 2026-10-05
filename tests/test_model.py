"""The plan file rules, and that every refusal names what to change."""

import unittest

import support
from week_tool import model


class Accepts(unittest.TestCase):
    def test_small_plan(self):
        p = model.parse(support.plan())
        self.assertEqual(len(p.days), 3)
        self.assertEqual(p.title, "This week")
        self.assertFalse(p.reviewed)

    def test_examples(self):
        for path in support.examples():
            with self.subTest(path=path):
                model.load(path)

    def test_hours_text(self):
        self.assertEqual(model.hours_text(0.5), "30 min")
        self.assertEqual(model.hours_text(1), "1 h")
        self.assertEqual(model.hours_text(2.25), "2.25 h")

    def test_day_name_is_english(self):
        import datetime
        self.assertEqual(model.day_name(datetime.date(2026, 10, 4)), "Sun 4 Oct")


class Refuses(unittest.TestCase):
    def refused(self, data, *words):
        with self.assertRaises(model.PlanError) as caught:
            model.parse(data)
        text = " ".join(caught.exception.problems)
        for word in words:
            self.assertIn(word, text)
        return caught.exception.problems

    def test_overfilled_day(self):
        data = support.plan()
        data["days"][1]["items"].append({"title": "Another job", "hours": 2})
        self.refused(data, "Mon 5 Oct is overfilled", "4 h planned", "3 h free")

    def test_week_without_buffer(self):
        data = support.plan()
        data["days"][2]["items"] = []
        self.refused(data, "buffer")

    def test_short_plan_needs_no_buffer(self):
        data = support.plan()
        data["days"] = data["days"][:2]
        model.parse(data)

    def test_weekend_rules(self):
        data = support.plan(mode="weekend")
        data["days"] = data["days"][:2]
        data["days"][1]["items"].append({"title": "Third", "hours": 0.5})
        data["days"][0]["items"].append({"title": "Fourth", "hours": 0.5})
        self.refused(data, "at most 3 tasks", "personal")

    def test_weekend_at_most_three_days(self):
        data = support.plan(mode="weekend")
        data["days"].append({"date": "2026-10-07", "free_hours": 1})
        self.refused(data, "at most 3 days")

    def test_days_must_follow(self):
        data = support.plan()
        data["days"][2]["date"] = "2026-10-08"
        self.refused(data, "follow one another")

    def test_unknown_field(self):
        data = support.plan(colour="red")
        self.refused(data, 'unknown field "colour"')

    def test_partial_review(self):
        data = support.plan()
        data["days"][0]["items"][0]["done"] = True
        self.refused(data, "Not marked yet", "Run the checks")

    def test_buffer_cannot_be_marked(self):
        data = support.plan()
        data["days"][2]["items"][0]["done"] = True
        self.refused(data, "buffer time is never marked")

    def test_quarter_hours(self):
        data = support.plan()
        data["days"][1]["items"][0]["hours"] = 1.1
        self.refused(data, "quarter hours")

    def test_hours_not_text(self):
        data = support.plan()
        data["days"][1]["items"][0]["hours"] = "2"
        self.refused(data, "must be a number of hours")

    def test_off_day_with_items(self):
        data = support.plan()
        data["days"][1]["off"] = True
        self.refused(data, "is a day off")

    def test_emoji(self):
        data = support.plan()
        data["days"][1]["items"][0]["title"] = "Rest \U0001F33F"
        self.refused(data, "cannot be drawn")

    def test_stage_only_for_tasks(self):
        data = support.plan()
        data["days"][2]["items"][0]["stage"] = "active"
        self.refused(data, '"stage" is only for a task or decision')

    def test_bad_date(self):
        data = support.plan()
        data["days"][0]["date"] = "4/10/2026"
        self.refused(data, "YYYY-MM-DD")

    def test_task_needs_title(self):
        data = support.plan()
        del data["days"][1]["items"][0]["title"]
        self.refused(data, 'needs a "title"')

    def test_problems_are_all_listed(self):
        data = support.plan(colour="red", mode="month")
        self.assertGreaterEqual(len(self.refused(data)), 2)


if __name__ == "__main__":
    unittest.main()
