"""The board's geometry, judged with plain rectangle maths that never calls the tool's own helpers."""

import unittest

import support
from week_tool import layout, model, theme


def inside(inner, outer):
    ix, iy, iw, ih = inner
    ox, oy, ow, oh = outer
    return ix >= ox - 1e-6 and iy >= oy - 1e-6 and ix + iw <= ox + ow + 1e-6 and iy + ih <= oy + oh + 1e-6


def overlap(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


class Board(unittest.TestCase):
    def columns(self, path):
        theme.register_fonts()
        return layout.lay_out(model.load(path))

    def test_every_card_inside_its_column_and_page(self):
        for path in support.examples():
            for col in self.columns(path):
                col_box = (col.x, col.bottom + layout.TOTAL_H, col.w, col.top - col.bottom - layout.TOTAL_H)
                self.assertTrue(inside(col_box, (0, 0, layout.PAGE_W, layout.PAGE_H)))
                for card in col.cards:
                    with self.subTest(path=path, card=card.item.title):
                        self.assertTrue(inside((card.x, card.y, card.w, card.h), col_box))

    def test_nothing_overlaps(self):
        for path in support.examples():
            cols = self.columns(path)
            boxes = [(c.x, c.bottom, c.w, c.top - c.bottom) for c in cols]
            for i, a in enumerate(boxes):
                for b in boxes[i + 1:]:
                    self.assertFalse(overlap(a, b), path)
            for col in cols:
                cards = [(c.x, c.y, c.w, c.h) for c in col.cards]
                for i, a in enumerate(cards):
                    for b in cards[i + 1:]:
                        self.assertFalse(overlap(a, b), path)

    def test_every_line_fits_its_card(self):
        for path in support.examples():
            plan = model.load(path)
            room_less = layout.TEXT_LEFT + layout.TEXT_RIGHT + (layout.MARK_ROOM if plan.reviewed else 0)
            for col in layout.lay_out(plan):
                for card in col.cards:
                    for line in card.title_lines:
                        self.assertLessEqual(theme.width(line, *theme.CARD_TITLE[:2]), card.w - room_less + 1e-6)
                    for line in card.detail_lines:
                        self.assertLessEqual(theme.width(line, *theme.CARD_DETAIL[:2]), card.w - room_less + 1e-6)

    def test_hours_never_split(self):
        for path in support.examples():
            for col in self.columns(path):
                for card in col.cards:
                    for line in card.detail_lines:
                        self.assertFalse(line.rstrip().endswith((" 1", " 2", " 3", " 30")), line)

    def test_columns_end_together_under_the_busiest_day(self):
        cols = self.columns(support.EXAMPLES + "/week.json")
        self.assertEqual(len(set(c.bottom for c in cols)), 1)
        lowest_card = min(card.y for c in cols for card in c.cards)
        self.assertGreater(cols[0].bottom, layout.BOARD_BOTTOM + 100, "a light week leaves room below")
        self.assertLess(lowest_card - (cols[0].bottom + layout.TOTAL_H), 10, "no tall empty tail")

    def test_light_week_columns_keep_a_minimum_height(self):
        data = support.plan(days=[{"date": "2026-10-04", "free_hours": 1, "items": [{"title": "Read", "hours": 1}]}])
        col = layout.lay_out(model.parse(data))[0]
        self.assertGreaterEqual(col.top - col.bottom, layout.MIN_COL_H - 1e-6)

    def test_too_many_cards_refused(self):
        data = support.plan()
        data["days"][1]["free_hours"] = 16
        data["days"][1]["items"] = [{"title": "A task with a fairly long title %d" % n, "hours": 0.5} for n in range(14)]
        with self.assertRaises(model.PlanError) as caught:
            layout.lay_out(model.parse(data))
        self.assertIn("more than fits in its column", caught.exception.problems[0])

    def test_word_too_wide_refused(self):
        data = support.plan()
        data["days"][1]["items"][0]["title"] = "Supercalifragilisticexpialidociousandmorelettersx"[:48]
        with self.assertRaises(model.PlanError) as caught:
            layout.lay_out(model.parse(data))
        self.assertIn("too wide for its card", caught.exception.problems[0])

    def test_weekend_columns_stay_card_shaped(self):
        cols = self.columns(support.EXAMPLES + "/weekend.json")
        self.assertTrue(all(c.w <= layout.MAX_COL_W for c in cols))


if __name__ == "__main__":
    unittest.main()
