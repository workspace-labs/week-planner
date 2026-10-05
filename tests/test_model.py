"""The plan file rules, and that every refusal names what to change."""

import os
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

    def test_carry_over_link_ignores_case_and_spacing(self):
        data = support.plan(carried_over=["Book the dentist", "Write the summary"])
        data["days"][1]["items"][0]["from_last_week"] = "book THE   dentist"
        self.assertEqual(model.parse(data).unplanned_carry_over, ["Write the summary"])

    def test_skill_explains_the_carry_over_link(self):
        # the link only helps if the agent that writes the plan file is told to use it
        for name in ("SKILL.md", os.path.join("references", "plan-format.md")):
            with open(os.path.join(support.SKILL, name), encoding="utf-8") as handle:
                self.assertIn("from_last_week", handle.read(), name)

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

    def test_weekend_personal_item_is_optional(self):
        # F02: the owner made personal items optional; a weekend of two tasks and no personal item is fine
        data = support.plan(mode="weekend")
        data["days"] = data["days"][:2]
        p = model.parse(data)
        self.assertFalse(any(i.kind == "personal" for d in p.days for i in d.items))

    def test_short_plan_needs_no_buffer(self):
        data = support.plan()
        data["days"] = data["days"][:2]
        model.parse(data)

    def test_weekend_at_most_three_tasks(self):
        data = support.plan(mode="weekend")
        data["days"] = data["days"][:2]
        data["days"][1]["items"].append({"title": "Third", "hours": 0.5})
        data["days"][0]["items"].append({"title": "Fourth", "hours": 0.5})
        self.refused(data, "at most 3 tasks")

    def test_non_finite_hours(self):
        # F04: NaN and Infinity are valid JSON to Python's reader; they must be refused, not crash
        for bad in (float("nan"), float("inf")):
            data = support.plan()
            data["days"][1]["free_hours"] = bad
            data["days"][1]["items"][0]["hours"] = bad
            self.refused(data, "must be a number of hours")

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

    def test_huge_whole_numbers(self):
        # F05: 10**400 is a valid JSON whole number; refused cleanly in both hour fields, either sign
        for field in ("free_hours", "hours"):
            for big in (10 ** 400, -10 ** 400):
                data = support.plan()
                if field == "free_hours":
                    data["days"][1]["free_hours"] = big
                else:
                    data["days"][1]["items"][0]["hours"] = big
                with self.subTest(field=field, sign=big > 0):
                    problems = self.refused(data, "must be between", "far too")
                    self.assertTrue(all(len(p) < 300 for p in problems))

    def test_from_last_week_must_name_a_carry_over(self):
        data = support.plan(carried_over=["Book the dentist"])
        data["days"][1]["items"][0]["from_last_week"] = "Book the doctor"
        self.refused(data, '"from_last_week"', "Book the doctor")

    def test_buffer_cannot_come_from_last_week(self):
        data = support.plan(carried_over=["Rest"])
        data["days"][2]["items"][0]["from_last_week"] = "Rest"
        self.refused(data, "buffer")

    def test_carry_over_listed_twice(self):
        self.refused(support.plan(carried_over=["Book the dentist", "book the  dentist"]), "twice")

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


class Goals(unittest.TestCase):
    """0.2.0: a goal can carry the person's why, their done-when, and the project whose cards serve it."""

    def goal(self, **fields):
        data = support.plan(goals=[dict({"goal": "Ship the checks"}, **fields)])
        data["days"][1]["items"][0]["project"] = "Checks"
        return data

    def refused(self, data):
        with self.assertRaises(model.PlanError) as caught:
            model.parse(data)
        return " ".join(caught.exception.problems)

    def test_goal_with_details(self):
        p = model.parse(self.goal(why="It proves the work", done_when="All pass", project="checks"))
        self.assertEqual(p.goals, ["Ship the checks"])
        g = p.goal_details[0]
        self.assertEqual((g.why, g.done_when), ("It proves the work", "All pass"))
        self.assertEqual([i.title for _, i in p.goal_cards(g)], ["Run the checks"], "project matched ignoring case")

    def test_plain_goal_still_works(self):
        p = model.parse(support.plan(goals=["Ship it"]))
        self.assertEqual((p.goals, p.goal_details[0].why, p.goal_cards(p.goal_details[0])), (["Ship it"], "", []))

    def test_project_with_no_cards(self):
        self.assertIn('names the project "Brand", but no card', self.refused(self.goal(project="Brand")))

    def test_goal_words_needed(self):
        self.assertIn('Goal 1 needs its words in "goal"', self.refused(support.plan(goals=[{"why": "Because"}])))

    def test_unknown_goal_field(self):
        self.assertIn('unknown field "reason"', self.refused(self.goal(reason="x")))

    def test_why_too_long(self):
        self.assertIn('"why" is too long', self.refused(self.goal(why="w" * 91)))

    def test_emoji_in_why(self):
        self.assertIn("cannot be drawn", self.refused(self.goal(why="Because \U0001F600")))


class CarryClaims(unittest.TestCase):
    """F01, round 4: each card plans at most one carried-over item, and each item is on at most one card."""

    LONG = "Review the proposed changes to the customer onboarding guide"

    def plan(self, items, carried):
        return {"carried_over": carried, "days": [{"date": "2026-10-18", "free_hours": 4, "items": items}]}

    def card(self, title, link=None, kind="task", done=None):
        out = {"title": title, "hours": 0.5, "kind": kind}
        if link is not None:
            out["from_last_week"] = link
        if done is not None:
            out["done"] = done
        return out

    def refused(self, data, *words):
        with self.assertRaises(model.PlanError) as caught:
            model.parse(data)
        text = " ".join(caught.exception.problems)
        for word in words:
            self.assertIn(word, text)

    def test_two_links_to_one_item(self):
        self.refused(self.plan([self.card("Review onboarding changes", self.LONG),
                                self.card("Finish onboarding review", self.LONG.upper())], [self.LONG]),
                     "on 2 cards", "Review onboarding changes", "Finish onboarding review")

    def test_two_decisions_linked_to_one_item(self):
        self.refused(self.plan([self.card("Approve the guide", self.LONG, "decision"),
                                self.card("Sign off the guide", self.LONG, "decision")], [self.LONG]), "on 2 cards")

    def test_title_and_link_to_one_item(self):
        self.refused(self.plan([self.card("Write the summary"), self.card("Write summary", "write THE  summary")],
                               ["Write the summary"]), "on 2 cards")

    def test_two_titles_for_one_item(self):
        self.refused(self.plan([self.card("Gym", kind="personal"), self.card("gym", kind="personal")], ["Gym"]),
                     "on 2 cards")

    def test_link_wins_over_title(self):
        # a card linked to one item never also plans another item that happens to share its title
        done = self.card("WRITE the summary", self.LONG, done=True)
        p = model.parse(self.plan([done], ["Write the summary", self.LONG]))
        self.assertEqual(p.unplanned_carry_over, ["Write the summary"])

    def test_buffers_plan_nothing(self):
        data = self.plan([{"kind": "buffer", "hours": 0.5}, {"kind": "buffer", "hours": 0.5},
                          self.card("Tidy up", "Buffer")], ["Buffer"])
        self.assertEqual(model.parse(data).unplanned_carry_over, [])
        data = self.plan([{"kind": "buffer", "hours": 0.5}, {"kind": "buffer", "hours": 0.5}], ["Buffer"])
        self.assertEqual(model.parse(data).unplanned_carry_over, ["Buffer"])

    def test_personal_item_can_plan_one(self):
        p = model.parse(self.plan([self.card("Gym", kind="personal")], ["gym"]))
        self.assertEqual(p.unplanned_carry_over, [])


if __name__ == "__main__":
    unittest.main()
