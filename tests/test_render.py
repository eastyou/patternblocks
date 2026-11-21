from __future__ import annotations

# HTML/SVG 渲染的单元测试。

import re
import unittest

from patternblocks.model import (
    MARGIN_MM,
    SHAPE_ORDER,
    PatternError,
    Placement,
    build_layout,
    shape_vertices,
)
from patternblocks.render import (
    count_pages,
    render_answer_page,
    render_blocks,
    render_challenge_page,
)

POINT_PATTERN = re.compile(r"^-?\d+\.\d{2},-?\d+\.\d{2}$")


class RenderBlocksTests(unittest.TestCase):
    """裁剪页渲染测试。"""

    def setUp(self) -> None:
        self.pages = build_layout(list(SHAPE_ORDER), 3)
        self.html = render_blocks(self.pages, 30.0)

    def test_document_structure(self) -> None:
        self.assertTrue(self.html.startswith("<!DOCTYPE html>"))
        self.assertIn('<html lang="zh-CN">', self.html)
        self.assertIn('<meta charset="utf-8">', self.html)

    def test_polygon_count_matches_placements(self) -> None:
        expected = sum(len(page) for page in self.pages)
        self.assertEqual(self.html.count('class="polygon-block"'), expected)

    def test_page_count_matches_helper(self) -> None:
        total = count_pages(len(self.pages), True)
        self.assertEqual(self.html.count('<section class="page">'), total)

    def test_each_page_has_one_svg(self) -> None:
        self.assertEqual(
            self.html.count('<svg class="blocks"'), len(self.pages)
        )

    def test_cut_hint_present(self) -> None:
        self.assertIn("沿实线剪下", self.html)

    def test_page_numbers_present(self) -> None:
        total = count_pages(len(self.pages), True)
        self.assertIn("第 1 / {0} 页".format(total), self.html)
        self.assertIn(
            "第 {0} / {0} 页".format(total), self.html
        )

    def test_area_table_present(self) -> None:
        self.assertIn("面积对照表", self.html)
        self.assertIn("相当于几个三角形", self.html)
        self.assertIn("389.71 mm²", self.html)
        self.assertIn("900.00 mm²", self.html)

    def test_area_table_ratios(self) -> None:
        self.assertIn(">1<", self.html)
        self.assertIn(">2<", self.html)
        self.assertIn(">3<", self.html)
        self.assertIn(">6<", self.html)
        self.assertIn(">2.31<", self.html)

    def test_legend_has_five_shapes(self) -> None:
        self.assertEqual(self.html.count('class="polygon-legend"'), 5)
        self.assertIn("五种积木图例", self.html)

    def test_shape_labels_present(self) -> None:
        for label in ("三", "菱", "梯", "六", "方"):
            self.assertIn(">" + label + "</text>", self.html)

    def test_a4_css(self) -> None:
        self.assertIn("@page", self.html)
        self.assertIn("size: A4", self.html)
        self.assertIn("210mm", self.html)
        self.assertIn("297mm", self.html)

    def test_svg_uses_millimetres(self) -> None:
        self.assertIn('width="186.00mm"', self.html)
        self.assertIn('height="273.00mm"', self.html)
        self.assertIn('viewBox="0.00 0.00 186.00 273.00"', self.html)

    def test_polygon_coordinates_have_two_decimals(self) -> None:
        blocks = re.findall(r'<polygon class="polygon-block" points="([^"]+)"', self.html)
        self.assertTrue(blocks)
        for block in blocks:
            for token in block.split(" "):
                self.assertRegex(token, POINT_PATTERN)

    def test_challenge_page_included(self) -> None:
        self.assertIn("拼图挑战卡", self.html)
        self.assertGreaterEqual(self.html.count('class="answer-box"'), 8)

    def test_answer_page_included(self) -> None:
        self.assertIn("挑战答案", self.html)
        self.assertIn("2 个等边三角形", self.html)
        self.assertIn("3 个菱形", self.html)

    def test_challenge_questions_text(self) -> None:
        self.assertIn("用 2 个等边三角形拼成一个菱形。", self.html)
        self.assertIn("用 3 个等边三角形拼成一个梯形。", self.html)
        self.assertIn("用 6 个等边三角形拼成一个正六边形。", self.html)
        self.assertIn("用 4 个等边三角形拼成两个菱形。", self.html)

    def test_title_is_escaped(self) -> None:
        html = render_blocks(self.pages, 30.0, title='<em>"积木"</em>')
        self.assertIn("&lt;em&gt;&quot;积木&quot;&lt;/em&gt;", html)
        self.assertNotIn("<em>", html)

    def test_script_in_title_is_not_raw(self) -> None:
        html = render_blocks(self.pages, 30.0, title="<script>alert(1)</script>")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_no_challenges_option(self) -> None:
        html = render_blocks(self.pages, 30.0, show_challenges=False)
        self.assertNotIn("拼图挑战卡", html)
        self.assertNotIn('class="answer-box"', html)
        self.assertEqual(html.count('<section class="page">'), 1 + len(self.pages))

    def test_page_numbers_shift_without_challenges(self) -> None:
        html = render_blocks(self.pages, 30.0, show_challenges=False)
        total = 1 + len(self.pages)
        self.assertIn("第 {0} / {0} 页".format(total), html)

    def test_custom_side_is_used(self) -> None:
        html = render_blocks(self.pages, 45.0)
        self.assertIn("45 mm", html)
        self.assertIn("统一边长 45 mm", html)

    def test_invalid_side_raises(self) -> None:
        with self.assertRaises(PatternError):
            render_blocks(self.pages, 10.0)
        with self.assertRaises(PatternError):
            render_blocks(self.pages, "30")  # type: ignore[arg-type]

    def test_empty_title_raises(self) -> None:
        with self.assertRaises(PatternError):
            render_blocks(self.pages, 30.0, title="   ")
        with self.assertRaises(PatternError):
            render_blocks(self.pages, 30.0, title=None)  # type: ignore[arg-type]

    def test_unknown_placement_shape_raises(self) -> None:
        bad = [Placement(name="circle", x=0.0, y=0.0, vertices=shape_vertices("square"))]
        with self.assertRaises(PatternError):
            render_blocks([bad], 30.0)

    def test_non_placement_item_raises(self) -> None:
        with self.assertRaises(PatternError):
            render_blocks([[object()]], 30.0)  # type: ignore[list-item]

    def test_empty_pages_document(self) -> None:
        html = render_blocks([], 30.0)
        self.assertIn("面积对照表", html)
        self.assertEqual(html.count('<section class="page">'), 3)
        self.assertEqual(html.count('class="polygon-block"'), 0)

    def test_content_inside_page_margins(self) -> None:
        for page in self.pages:
            for placement in page:
                for x, y in placement.vertices:
                    self.assertGreaterEqual(x, MARGIN_MM - 1e-6)
                    self.assertGreaterEqual(y, MARGIN_MM - 1e-6)

    def test_count_pages_helper(self) -> None:
        self.assertEqual(count_pages(3, True), 6)
        self.assertEqual(count_pages(3, False), 4)
        self.assertEqual(count_pages(0, True), 3)

    def test_count_pages_rejects_negative(self) -> None:
        with self.assertRaises(PatternError):
            count_pages(-1, True)


class StandalonePageTests(unittest.TestCase):
    """挑战页与答案页独立渲染测试。"""

    def test_challenge_page_is_full_document(self) -> None:
        html = render_challenge_page(30.0)
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn("拼图挑战卡", html)
        self.assertGreaterEqual(html.count('class="answer-box"'), 8)

    def test_challenge_page_mentions_side(self) -> None:
        html = render_challenge_page(42.0)
        self.assertIn("42 mm", html)

    def test_challenge_page_invalid_side(self) -> None:
        with self.assertRaises(PatternError):
            render_challenge_page(5.0)

    def test_answer_page_is_full_document(self) -> None:
        html = render_answer_page()
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn("挑战答案", html)
        self.assertIn("1:2:3:6", html)

    def test_answer_page_lists_quantities(self) -> None:
        html = render_answer_page()
        self.assertIn("6 个等边三角形", html)
        self.assertIn("2 个菱形", html)
        self.assertIn("1 个正六边形", html)


if __name__ == "__main__":
    unittest.main()
