from __future__ import annotations

# 图案积木的几何模型：统一边长多边形、面积换算与分页排版。

import math
from dataclasses import dataclass
from typing import Sequence

# 形状顺序：三角形族在前，正方形单独放在最后。
SHAPE_ORDER: tuple[str, ...] = (
    "triangle",
    "rhombus",
    "trapezoid",
    "hexagon",
    "square",
)

SHAPE_LABELS: dict[str, str] = {
    "triangle": "等边三角形",
    "rhombus": "菱形",
    "trapezoid": "梯形",
    "hexagon": "正六边形",
    "square": "正方形",
}

# 图形中心显示的简称，避免打印时字体缺失。
SHAPE_SHORT_LABELS: dict[str, str] = {
    "triangle": "三",
    "rhombus": "菱",
    "trapezoid": "梯",
    "hexagon": "六",
    "square": "方",
}

SIDE_MM: float = 30.0
MIN_SIDE_MM: float = 15.0
MAX_SIDE_MM: float = 60.0

PAGE_W_MM: float = 210.0
PAGE_H_MM: float = 297.0
MARGIN_MM: float = 12.0
GAP_MM: float = 4.0

# 打印安全余量：可用区域再收缩 2%，避免边角被打印机裁切。
SAFE_RATIO: float = 0.98

MIN_EACH: int = 1
MAX_EACH: int = 12

_LABEL_TO_NAME: dict[str, str] = {
    label: name for name, label in SHAPE_LABELS.items()
}

# 常见简称也视为合法中文名。
_NAME_ALIASES: dict[str, str] = {
    "三角形": "triangle",
    "六边形": "hexagon",
}


class PatternError(ValueError):
    """参数或几何数据不合法时抛出的错误。"""


def _validate_name(name: str) -> str:
    """校验形状名并返回规范英文名。"""
    if not isinstance(name, str):
        raise PatternError("形状名必须是字符串")
    key = name.strip()
    if key in SHAPE_ORDER:
        return key
    raise PatternError(
        "未知形状：" + key + "；可选：" + "、".join(SHAPE_LABELS[item] for item in SHAPE_ORDER)
    )


def validate_side(side_mm: float) -> float:
    """校验边长（15～60 mm）并返回浮点值。"""
    if isinstance(side_mm, bool) or not isinstance(side_mm, (int, float)):
        raise PatternError("边长必须是数字")
    value = float(side_mm)
    if not math.isfinite(value):
        raise PatternError("边长必须是有限数值")
    if value < MIN_SIDE_MM or value > MAX_SIDE_MM:
        raise PatternError(
            "边长必须在 {low:g}～{high:g} mm 之间".format(low=MIN_SIDE_MM, high=MAX_SIDE_MM)
        )
    return value


def validate_each(each: int) -> int:
    """校验每种形状的数量（1～12）。"""
    if isinstance(each, bool) or not isinstance(each, int):
        raise PatternError("每种形状的数量必须是整数")
    if each < MIN_EACH or each > MAX_EACH:
        raise PatternError(
            "每种形状的数量必须在 {low}～{high} 之间".format(low=MIN_EACH, high=MAX_EACH)
        )
    return each


def shape_vertices(name: str, side_mm: float = SIDE_MM) -> list[tuple[float, float]]:
    """返回以重心为原点、逆时针排列的多边形顶点（单位 mm）。"""
    shape = _validate_name(name)
    side = validate_side(side_mm)

    if shape == "triangle":
        # 等边三角形：重心与内心、外心重合，外接圆半径 = 边长 / √3。
        radius = side / math.sqrt(3.0)
        return [
            (
                radius * math.cos(math.radians(90.0 + 120.0 * index)),
                radius * math.sin(math.radians(90.0 + 120.0 * index)),
            )
            for index in range(3)
        ]

    height = math.sqrt(3.0) / 2.0 * side

    if shape == "rhombus":
        # 60°/120° 菱形，由两个等边三角形沿一条边拼成。
        return [
            (-0.75 * side, -height / 2.0),
            (0.25 * side, -height / 2.0),
            (0.75 * side, height / 2.0),
            (-0.25 * side, height / 2.0),
        ]

    if shape == "trapezoid":
        # 等腰梯形：下底 2s、上底 s、腰 s，由三个等边三角形拼成。
        return [
            (-side, -height / 2.0),
            (side, -height / 2.0),
            (0.5 * side, height / 2.0),
            (-0.5 * side, height / 2.0),
        ]

    if shape == "hexagon":
        # 正六边形：外接圆半径等于边长。
        return [
            (
                side * math.cos(math.radians(60.0 * index)),
                side * math.sin(math.radians(60.0 * index)),
            )
            for index in range(6)
        ]

    half = side / 2.0
    return [
        (-half, -half),
        (half, -half),
        (half, half),
        (-half, half),
    ]


def polygon_area(points: Sequence[tuple[float, float]]) -> float:
    """用鞋带公式计算多边形面积（取绝对值，单位 mm²）。"""
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes)):
        raise PatternError("多边形顶点必须是坐标序列")
    if len(points) < 3:
        raise PatternError("多边形至少需要 3 个顶点")

    total = 0.0
    count = len(points)
    for index in range(count):
        try:
            x1, y1 = points[index]
            x2, y2 = points[(index + 1) % count]
        except (TypeError, ValueError) as exc:
            raise PatternError("每个顶点必须是两个数字构成的坐标") from exc

        for value in (x1, y1, x2, y2):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise PatternError("顶点坐标必须是数字")
            if not math.isfinite(float(value)):
                raise PatternError("顶点坐标必须是有限数值")

        total += float(x1) * float(y2) - float(x2) * float(y1)

    return abs(total) / 2.0


def area_in_triangles(name: str, side_mm: float = SIDE_MM) -> float:
    """返回该形状相当于几个等边三角形（统一边长）。"""
    shape = _validate_name(name)
    side = validate_side(side_mm)
    triangle_area = polygon_area(shape_vertices("triangle", side))
    return polygon_area(shape_vertices(shape, side)) / triangle_area


def shape_bounds(
    points: Sequence[tuple[float, float]],
) -> tuple[float, float, float, float]:
    """返回顶点包围盒 (min_x, min_y, max_x, max_y)。"""
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes)):
        raise PatternError("多边形顶点必须是坐标序列")
    if len(points) == 0:
        raise PatternError("多边形至少需要 1 个顶点")

    xs: list[float] = []
    ys: list[float] = []
    for point in points:
        try:
            x, y = point
        except (TypeError, ValueError) as exc:
            raise PatternError("每个顶点必须是两个数字构成的坐标") from exc
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise PatternError("顶点坐标必须是数字")
        if isinstance(y, bool) or not isinstance(y, (int, float)):
            raise PatternError("顶点坐标必须是数字")
        if not (math.isfinite(float(x)) and math.isfinite(float(y))):
            raise PatternError("顶点坐标必须是有限数值")
        xs.append(float(x))
        ys.append(float(y))

    return min(xs), min(ys), max(xs), max(ys)


def validate_shapes(raw: str) -> list[str]:
    """解析逗号分隔的形状名（中英文均可），去重并按 SHAPE_ORDER 排序。"""
    if not isinstance(raw, str):
        raise PatternError("形状列表必须是字符串")
    normalized = raw.replace("，", ",")
    if not normalized.strip():
        raise PatternError("形状列表不能为空")

    selected: set[str] = set()
    for chunk in normalized.split(","):
        token = chunk.strip()
        if not token:
            raise PatternError("形状列表中存在空项，请检查逗号")
        if token in SHAPE_ORDER:
            selected.add(token)
        elif token.lower() in SHAPE_ORDER:
            selected.add(token.lower())
        elif token in _LABEL_TO_NAME:
            selected.add(_LABEL_TO_NAME[token])
        elif token in _NAME_ALIASES:
            selected.add(_NAME_ALIASES[token])
        else:
            raise PatternError(
                "未知形状：" + token + "；可选：" + "、".join(SHAPE_LABELS[item] for item in SHAPE_ORDER)
            )

    return [name for name in SHAPE_ORDER if name in selected]


@dataclass(frozen=True)
class Placement:
    """一个积木在页面中的位置（页面左上角为原点，单位 mm）。"""

    name: str
    x: float
    y: float
    vertices: list[tuple[float, float]]


def _usable_size(
    page_w_mm: float, page_h_mm: float, margin_mm: float
) -> tuple[float, float]:
    """计算扣除页边距与安全余量后的可用区域尺寸。"""
    for value, label in (
        (page_w_mm, "页面宽度"),
        (page_h_mm, "页面高度"),
        (margin_mm, "页边距"),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise PatternError(label + "必须是数字")
        if not math.isfinite(float(value)):
            raise PatternError(label + "必须是有限数值")
    if float(page_w_mm) <= 0.0 or float(page_h_mm) <= 0.0:
        raise PatternError("页面尺寸必须大于 0")
    if float(margin_mm) < 0.0:
        raise PatternError("页边距不能为负数")
    if float(margin_mm) * 2.0 >= float(page_w_mm) or float(margin_mm) * 2.0 >= float(
        page_h_mm
    ):
        raise PatternError("页边距过大，页面没有可用区域")

    usable_w = (float(page_w_mm) - 2.0 * float(margin_mm)) * SAFE_RATIO
    usable_h = (float(page_h_mm) - 2.0 * float(margin_mm)) * SAFE_RATIO
    if usable_w <= 0.0 or usable_h <= 0.0:
        raise PatternError("页面可用区域必须大于 0")
    return usable_w, usable_h


def build_layout(
    names: list[str],
    each: int,
    page_w_mm: float = PAGE_W_MM,
    page_h_mm: float = PAGE_H_MM,
    margin_mm: float = MARGIN_MM,
    gap_mm: float = GAP_MM,
    side_mm: float = SIDE_MM,
) -> list[list[Placement]]:
    """按行排版积木，返回按页分组的摆放结果。"""
    if not isinstance(names, Sequence) or isinstance(names, (str, bytes)):
        raise PatternError("形状列表必须是形状名序列")
    if len(names) == 0:
        raise PatternError("至少需要一种形状")
    if isinstance(gap_mm, bool) or not isinstance(gap_mm, (int, float)):
        raise PatternError("间距必须是数字")
    if not math.isfinite(float(gap_mm)) or float(gap_mm) < 0.0:
        raise PatternError("间距必须是非负的有限数值")

    count = validate_each(each)
    side = validate_side(side_mm)
    usable_w, usable_h = _usable_size(page_w_mm, page_h_mm, margin_mm)
    gap = float(gap_mm)

    # 先按宽度切成行，每个元素记录形状、相对顶点与包围盒尺寸。
    rows: list[list[tuple[str, list[tuple[float, float]], float, float]]] = []
    current_row: list[tuple[str, list[tuple[float, float]], float, float]] = []
    row_width = 0.0

    for name in names:
        shape = _validate_name(name)
        vertices = shape_vertices(shape, side)
        min_x, min_y, max_x, max_y = shape_bounds(vertices)
        width = max_x - min_x
        height = max_y - min_y
        if width > usable_w or height > usable_h:
            raise PatternError(
                "形状 {label} 在边长 {side:g} mm 时超出页面可用区域".format(
                    label=SHAPE_LABELS[shape], side=side
                )
            )

        for _ in range(count):
            extra = width if not current_row else gap + width
            if current_row and row_width + extra > usable_w + 1e-9:
                rows.append(current_row)
                current_row = []
                row_width = 0.0
                extra = width
            current_row.append((shape, vertices, width, height))
            row_width += extra

    if current_row:
        rows.append(current_row)

    pages: list[list[Placement]] = []
    page: list[Placement] = []
    cursor_y = float(margin_mm)
    bottom = float(margin_mm) + usable_h
    left = float(margin_mm)

    for row in rows:
        row_height = max(item[3] for item in row)
        needed = row_height if not page else row_height + gap
        if page and cursor_y + needed > bottom + 1e-9:
            pages.append(page)
            page = []
            cursor_y = float(margin_mm)
            needed = row_height

        cursor_x = left
        for shape, vertices, width, height in row:
            min_x, min_y, _, _ = shape_bounds(vertices)
            offset_x = cursor_x - min_x
            offset_y = cursor_y + (row_height - height) / 2.0 - min_y
            placed = [
                (vertex[0] + offset_x, vertex[1] + offset_y) for vertex in vertices
            ]
            page.append(
                Placement(name=shape, x=offset_x, y=offset_y, vertices=placed)
            )
            cursor_x += width + gap

        cursor_y += row_height + gap

    if page:
        pages.append(page)

    return pages
