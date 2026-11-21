from __future__ import annotations

# 几何模型与排版逻辑的单元测试。

import math
import unittest
from typing import Sequence

from patternblocks.model import (
    GAP_MM,
    MARGIN_MM,
    MAX_EACH,
    MAX_SIDE_MM,
    MIN_EACH,
    MIN_SIDE_MM,
    PAGE_H_MM,
    PAGE_W_MM,
    SAFE_RATIO,
    SHAPE_LABELS,
    SHAPE_ORDER,
    SIDE_MM,
    PatternError,
    Placement,
    area_in_triangles,
    build_layout,
    polygon_area,
    shape_bounds,
    shape_vertices,
    validate_each,
    validate_shapes,
    validate_side,
)

SIDE: float = 30.0
DELTA: float = 1e-6


def edge_lengths(points: Sequence[tuple[float, float]]) -> list[float]:
    """返回多边形每条边的长度。"""
    total = len(points)
    return [
        math.dist(points[index], points[(index + 1) % total])
        for index in range(total)
    ]


def signed_area(points: Sequence[tuple[float, float]]) -> float:
    """返回带符号面积（逆时针为正）。"""
    total = 0.0
    count = len(points)
    for index in range(count):
        x1, y1 = points[index]
        x2, y2 = points[(index + 1) % count]
        total += x1 * y2 - x2 * y1
    return total / 2.0


def centroid(points: Sequence[tuple[float, float]]) -> tuple[float, float]:
    """返回顶点平均值（重心）。"""
    count = float(len(points))
    return (
        sum(point[0] for point in points) / count,
        sum(point[1] for point in points) / count,
    )


def bbox(points: Sequence[tuple[float, float]]) -> tuple[float, float, float, float]:
    """返回包围盒。"""
    return shape_bounds(points)


def overlaps(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> bool:
    """判断两个包围盒是否有正面积重叠。"""
    return (
        first[0] < second[2] - DELTA
        and second[0] < first[2] - DELTA
        and first[1] < second[3] - DELTA
        and second[1] < first[3] - DELTA
    )


class ConstantTests(unittest.TestCase):
    """常量与中文名称测试。"""

    def test_shape_order_is_stable(self) -> None:
        self.assertEqual(
            SHAPE_ORDER,
            ("triangle", "rhombus", "trapezoid", "hexagon", "square"),
        )

    def test_shape_labels_cover_all_shapes(self) -> None:
        self.assertEqual(set(SHAPE_LABELS), set(SHAPE_ORDER))

    def test_shape_labels_are_chinese(self) -> None:
        self.assertEqual(SHAPE_LABELS["triangle"], "等边三角形")
        self.assertEqual(SHAPE_LABELS["rhombus"], "菱形")
        self.assertEqual(SHAPE_LABELS["trapezoid"], "梯形")
        self.assertEqual(SHAPE_LABELS["hexagon"], "正六边形")
        self.assertEqual(SHAPE_LABELS["square"], "正方形")

    def test_default_side_is_30(self) -> None:
        self.assertEqual(SIDE_MM, 30.0)

    def test_page_constants(self) -> None:
        self.assertEqual(PAGE_W_MM, 210.0)
        self.assertEqual(PAGE_H_MM, 297.0)
        self.assertEqual(MARGIN_MM, 12.0)
        self.assertEqual(GAP_MM, 4.0)
        self.assertTrue(0.98 <= SAFE_RATIO < 1.0)


class VertexTests(unittest.TestCase):
    """顶点数量、重心与边长测试。"""

    def test_triangle_vertex_count(self) -> None:
        self.assertEqual(len(shape_vertices("triangle", SIDE)), 3)

    def test_rhombus_vertex_count(self) -> None:
        self.assertEqual(len(shape_vertices("rhombus", SIDE)), 4)

    def test_trapezoid_vertex_count(self) -> None:
        self.assertEqual(len(shape_vertices("trapezoid", SIDE)), 4)

    def test_hexagon_vertex_count(self) -> None:
        self.assertEqual(len(shape_vertices("hexagon", SIDE)), 6)

    def test_square_vertex_count(self) -> None:
        self.assertEqual(len(shape_vertices("square", SIDE)), 4)

    def test_triangle_centroid_at_origin(self) -> None:
        center = centroid(shape_vertices("triangle", SIDE))
        self.assertAlmostEqual(center[0], 0.0, delta=1e-9)
        self.assertAlmostEqual(center[1], 0.0, delta=1e-9)

    def test_rhombus_centroid_at_origin(self) -> None:
        center = centroid(shape_vertices("rhombus", SIDE))
        self.assertAlmostEqual(center[0], 0.0, delta=1e-9)
        self.assertAlmostEqual(center[1], 0.0, delta=1e-9)

    def test_trapezoid_centroid_at_origin(self) -> None:
        center = centroid(shape_vertices("trapezoid", SIDE))
        self.assertAlmostEqual(center[0], 0.0, delta=1e-9)
        self.assertAlmostEqual(center[1], 0.0, delta=1e-9)

    def test_hexagon_centroid_at_origin(self) -> None:
        center = centroid(shape_vertices("hexagon", SIDE))
        self.assertAlmostEqual(center[0], 0.0, delta=1e-9)
        self.assertAlmostEqual(center[1], 0.0, delta=1e-9)

    def test_square_centroid_at_origin(self) -> None:
        center = centroid(shape_vertices("square", SIDE))
        self.assertAlmostEqual(center[0], 0.0, delta=1e-9)
        self.assertAlmostEqual(center[1], 0.0, delta=1e-9)

    def test_triangle_edges_equal_side(self) -> None:
        for length in edge_lengths(shape_vertices("triangle", SIDE)):
            self.assertAlmostEqual(length, SIDE, delta=1e-9)

    def test_rhombus_edges_equal_side(self) -> None:
        for length in edge_lengths(shape_vertices("rhombus", SIDE)):
            self.assertAlmostEqual(length, SIDE, delta=1e-9)

    def test_trapezoid_edges_equal_side(self) -> None:
        lengths = edge_lengths(shape_vertices("trapezoid", SIDE))
        self.assertEqual(len(lengths), 4)
        self.assertAlmostEqual(lengths[0], 2.0 * SIDE, delta=1e-9)
        for length in lengths[1:]:
            self.assertAlmostEqual(length, SIDE, delta=1e-9)

    def test_hexagon_edges_equal_side(self) -> None:
        lengths = edge_lengths(shape_vertices("hexagon", SIDE))
        self.assertEqual(len(lengths), 6)
        for length in lengths:
            self.assertAlmostEqual(length, SIDE, delta=1e-9)

    def test_square_edges_equal_side(self) -> None:
        lengths = edge_lengths(shape_vertices("square", SIDE))
        self.assertEqual(len(lengths), 4)
        for length in lengths:
            self.assertAlmostEqual(length, SIDE, delta=1e-9)

    def test_all_shapes_are_counter_clockwise(self) -> None:
        for name in SHAPE_ORDER:
            self.assertGreater(signed_area(shape_vertices(name, SIDE)), 0.0)

    def test_side_scales_edges(self) -> None:
        for name in SHAPE_ORDER:
            for length in edge_lengths(shape_vertices(name, 60.0)):
                valid = abs(length - 60.0) < 1e-9
                if name == "trapezoid":
                    valid = valid or abs(length - 120.0) < 1e-9
                self.assertTrue(valid, "{0} 的边长为 {1}".format(name, length))

    def test_triangle_wraps_in_its_bounding_box(self) -> None:
        min_x, min_y, max_x, max_y = shape_bounds(shape_vertices("triangle", SIDE))
        self.assertAlmostEqual(max_x - min_x, SIDE, delta=1e-9)
        self.assertAlmostEqual(max_y - min_y, math.sqrt(3.0) / 2.0 * SIDE, delta=1e-9)

    def test_hexagon_bounding_box(self) -> None:
        min_x, min_y, max_x, max_y = shape_bounds(shape_vertices("hexagon", SIDE))
        self.assertAlmostEqual(max_x - min_x, 2.0 * SIDE, delta=1e-9)
        self.assertAlmostEqual(max_y - min_y, math.sqrt(3.0) * SIDE, delta=1e-9)


class AreaTests(unittest.TestCase):
    """鞋带公式与面积倍率测试。"""

    def test_triangle_area_formula(self) -> None:
        area = polygon_area(shape_vertices("triangle", SIDE))
        self.assertAlmostEqual(area, math.sqrt(3.0) / 4.0 * SIDE * SIDE, delta=DELTA)

    def test_square_area_is_side_squared(self) -> None:
        area = polygon_area(shape_vertices("square", SIDE))
        self.assertAlmostEqual(area, SIDE * SIDE, delta=DELTA)

    def test_rhombus_area_is_two_triangles(self) -> None:
        base = area_in_triangles("triangle", SIDE)
        self.assertAlmostEqual(area_in_triangles("rhombus", SIDE) / base, 2.0, delta=DELTA)

    def test_trapezoid_area_is_three_triangles(self) -> None:
        base = area_in_triangles("triangle", SIDE)
        self.assertAlmostEqual(area_in_triangles("trapezoid", SIDE) / base, 3.0, delta=DELTA)

    def test_hexagon_area_is_six_triangles(self) -> None:
        base = area_in_triangles("triangle", SIDE)
        self.assertAlmostEqual(area_in_triangles("hexagon", SIDE) / base, 6.0, delta=DELTA)

    def test_area_ratio_sequence(self) -> None:
        ratios = [
            area_in_triangles(name, SIDE)
            for name in ("triangle", "rhombus", "trapezoid", "hexagon")
        ]
        for ratio, expected in zip(ratios, (1, 2, 3, 6)):
            self.assertAlmostEqual(ratio, float(expected), delta=DELTA)

    def test_area_ratio_is_side_independent(self) -> None:
        for side in (15.0, 42.0, 60.0):
            values = [
                area_in_triangles(name, side)
                for name in ("triangle", "rhombus", "trapezoid", "hexagon")
            ]
            for value, expected in zip(values, (1, 2, 3, 6)):
                self.assertAlmostEqual(value, float(expected), delta=DELTA)

    def test_square_area_in_triangles(self) -> None:
        ratio = area_in_triangles("square", SIDE)
        self.assertAlmostEqual(ratio, 4.0 / math.sqrt(3.0), delta=DELTA)
        self.assertAlmostEqual(ratio, 900.0 / (math.sqrt(3.0) / 4.0 * 900.0), delta=DELTA)

    def test_area_in_triangles_matches_shoelace(self) -> None:
        triangle = polygon_area(shape_vertices("triangle", 45.0))
        for name in SHAPE_ORDER:
            expected = polygon_area(shape_vertices(name, 45.0)) / triangle
            self.assertAlmostEqual(area_in_triangles(name, 45.0), expected, delta=DELTA)

    def test_polygon_area_ignores_direction(self) -> None:
        points = shape_vertices("square", SIDE)
        self.assertAlmostEqual(
            polygon_area(list(reversed(points))), polygon_area(points), delta=DELTA
        )

    def test_polygon_area_requires_three_points(self) -> None:
        with self.assertRaises(PatternError):
            polygon_area([(0.0, 0.0), (1.0, 1.0)])

    def test_polygon_area_rejects_text_coordinates(self) -> None:
        with self.assertRaises(PatternError):
            polygon_area([(0.0, 0.0), ("1", 0.0), (0.0, 1.0)])

    def test_polygon_area_rejects_infinite(self) -> None:
        with self.assertRaises(PatternError):
            polygon_area([(0.0, 0.0), (math.inf, 0.0), (0.0, 1.0)])


class ValidationTests(unittest.TestCase):
    """形状名与边长校验测试。"""

    def test_unknown_shape_raises(self) -> None:
        with self.assertRaises(PatternError):
            shape_vertices("circle", SIDE)

    def test_side_below_minimum_raises(self) -> None:
        with self.assertRaises(PatternError):
            shape_vertices("triangle", MIN_SIDE_MM - 0.1)

    def test_side_above_maximum_raises(self) -> None:
        with self.assertRaises(PatternError):
            shape_vertices("triangle", MAX_SIDE_MM + 0.1)

    def test_side_must_be_number(self) -> None:
        with self.assertRaises(PatternError):
            shape_vertices("triangle", "30")  # type: ignore[arg-type]

    def test_side_must_be_finite(self) -> None:
        with self.assertRaises(PatternError):
            shape_vertices("triangle", math.nan)
        with self.assertRaises(PatternError):
            shape_vertices("triangle", math.inf)

    def test_boundary_sides_are_accepted(self) -> None:
        self.assertEqual(validate_side(MIN_SIDE_MM), MIN_SIDE_MM)
        self.assertEqual(validate_side(MAX_SIDE_MM), MAX_SIDE_MM)

    def test_validate_each_rejects_out_of_range(self) -> None:
        with self.assertRaises(PatternError):
            validate_each(MIN_EACH - 1)
        with self.assertRaises(PatternError):
            validate_each(MAX_EACH + 1)

    def test_validate_each_rejects_non_integer(self) -> None:
        with self.assertRaises(PatternError):
            validate_each(3.0)  # type: ignore[arg-type]

    def test_validate_shapes_english_order(self) -> None:
        self.assertEqual(
            validate_shapes("square,triangle,hexagon"),
            ["triangle", "hexagon", "square"],
        )

    def test_validate_shapes_chinese(self) -> None:
        self.assertEqual(
            validate_shapes("正方形，等边三角形"),
            ["triangle", "square"],
        )

    def test_validate_shapes_aliases(self) -> None:
        self.assertEqual(validate_shapes("三角形,六边形"), ["triangle", "hexagon"])

    def test_validate_shapes_deduplicates(self) -> None:
        self.assertEqual(
            validate_shapes("triangle,等边三角形,TRIANGLE,triangle"),
            ["triangle"],
        )

    def test_validate_shapes_unknown_name(self) -> None:
        with self.assertRaises(PatternError) as context:
            validate_shapes("circle")
        self.assertIn("未知形状", str(context.exception))

    def test_validate_shapes_empty_string(self) -> None:
        with self.assertRaises(PatternError):
            validate_shapes("")

    def test_validate_shapes_blank_items(self) -> None:
        with self.assertRaises(PatternError):
            validate_shapes("triangle,,square")

    def test_shape_bounds_values(self) -> None:
        min_x, min_y, max_x, max_y = shape_bounds(shape_vertices("square", SIDE))
        self.assertAlmostEqual(min_x, -15.0, delta=1e-9)
        self.assertAlmostEqual(min_y, -15.0, delta=1e-9)
        self.assertAlmostEqual(max_x, 15.0, delta=1e-9)
        self.assertAlmostEqual(max_y, 15.0, delta=1e-9)

    def test_shape_bounds_empty_points(self) -> None:
        with self.assertRaises(PatternError):
            shape_bounds([])


class LayoutTests(unittest.TestCase):
    """分页排版测试。"""

    def setUp(self) -> None:
        self.usable_w = (PAGE_W_MM - 2.0 * MARGIN_MM) * SAFE_RATIO
        self.usable_h = (PAGE_H_MM - 2.0 * MARGIN_MM) * SAFE_RATIO

    def test_layout_contains_all_blocks(self) -> None:
        pages = build_layout(list(SHAPE_ORDER), 3, side_mm=SIDE)
        self.assertEqual(sum(len(page) for page in pages), 5 * 3)

    def test_layout_returns_placements_with_vertices(self) -> None:
        pages = build_layout(["triangle"], 2, side_mm=SIDE)
        self.assertEqual(len(pages), 1)
        for placement in pages[0]:
            self.assertIsInstance(placement, Placement)
            self.assertEqual(placement.name, "triangle")
            self.assertEqual(len(placement.vertices), 3)

    def test_layout_boxes_do_not_overlap(self) -> None:
        pages = build_layout(list(SHAPE_ORDER), 6, side_mm=SIDE)
        for page in pages:
            boxes = [bbox(placement.vertices) for placement in page]
            for first in range(len(boxes)):
                for second in range(first + 1, len(boxes)):
                    self.assertFalse(
                        overlaps(boxes[first], boxes[second]),
                        "同一页内积木重叠：{0} 与 {1}".format(first, second),
                    )

    def test_layout_stays_inside_printable_area(self) -> None:
        pages = build_layout(list(SHAPE_ORDER), 6, side_mm=SIDE)
        for page in pages:
            for placement in page:
                for x, y in placement.vertices:
                    self.assertGreaterEqual(x, MARGIN_MM - 1e-6)
                    self.assertGreaterEqual(y, MARGIN_MM - 1e-6)
                    self.assertLessEqual(x, MARGIN_MM + self.usable_w + 1e-6)
                    self.assertLessEqual(y, MARGIN_MM + self.usable_h + 1e-6)

    def test_layout_paginates_when_full(self) -> None:
        pages = build_layout(list(SHAPE_ORDER), 12, side_mm=SIDE)
        self.assertGreater(len(pages), 1)
        self.assertLessEqual(sum(len(page) for page in pages), 5 * 12)

    def test_layout_each_page_not_empty(self) -> None:
        pages = build_layout(list(SHAPE_ORDER), 4, side_mm=SIDE)
        for page in pages:
            self.assertGreater(len(page), 0)

    def test_layout_each_below_minimum_raises(self) -> None:
        with self.assertRaises(PatternError):
            build_layout(["triangle"], 0)

    def test_layout_each_above_maximum_raises(self) -> None:
        with self.assertRaises(PatternError):
            build_layout(["triangle"], 13)

    def test_layout_rejects_empty_names(self) -> None:
        with self.assertRaises(PatternError):
            build_layout([], 1)

    def test_layout_rejects_unknown_shape(self) -> None:
        with self.assertRaises(PatternError):
            build_layout(["circle"], 1)

    def test_layout_rejects_bad_margin(self) -> None:
        with self.assertRaises(PatternError):
            build_layout(["triangle"], 1, margin_mm=120.0)

    def test_layout_rejects_negative_gap(self) -> None:
        with self.assertRaises(PatternError):
            build_layout(["triangle"], 1, gap_mm=-1.0)

    def test_layout_respects_large_side(self) -> None:
        pages = build_layout(list(SHAPE_ORDER), 2, side_mm=60.0)
        for page in pages:
            for placement in page:
                for _, y in placement.vertices:
                    self.assertLessEqual(y, MARGIN_MM + self.usable_h + 1e-6)

    def test_layout_places_single_shape_once(self) -> None:
        pages = build_layout(["square"], 1, side_mm=SIDE)
        self.assertEqual(len(pages), 1)
        self.assertEqual(len(pages[0]), 1)

    def test_placement_is_immutable(self) -> None:
        placement = build_layout(["square"], 1, side_mm=SIDE)[0][0]
        with self.assertRaises(AttributeError):
            placement.x = 1.0  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
