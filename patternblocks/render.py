from __future__ import annotations

# HTML/SVG 渲染：A4 裁剪页、面积对照表、拼图挑战卡与答案页。

import html
import math
from typing import Sequence

from patternblocks.model import (
    MARGIN_MM,
    PAGE_H_MM,
    PAGE_W_MM,
    SHAPE_LABELS,
    SHAPE_ORDER,
    SHAPE_SHORT_LABELS,
    PatternError,
    Placement,
    area_in_triangles,
    polygon_area,
    shape_bounds,
    shape_vertices,
    validate_side,
)

# 页面正文区域尺寸（扣除 12mm 页边距后恰好为 186mm × 273mm）。
_CONTENT_W: float = PAGE_W_MM - 2.0 * MARGIN_MM
_CONTENT_H: float = PAGE_H_MM - 2.0 * MARGIN_MM

_FILL = "#ffe4a3"
_STROKE = "#a87400"
_INK = "#5f4400"
_LINE = "#c9d2dc"

# 每道挑战题及其答案（答案用于答案页）。
_CHALLENGES: tuple[tuple[str, str], ...] = (
    ("用 2 个等边三角形拼成一个菱形。", "2 个等边三角形"),
    ("用 3 个等边三角形拼成一个梯形。", "3 个等边三角形"),
    ("用 6 个等边三角形拼成一个正六边形。", "6 个等边三角形"),
    ("用 4 个等边三角形拼成两个菱形。", "4 个等边三角形"),
    ("用 4 个等边三角形拼成一个边长翻倍的大等边三角形。", "4 个等边三角形"),
    ("用 2 个菱形拼成一个正六边形。", "2 个菱形"),
    ("用 2 个梯形拼成一个正六边形。", "2 个梯形"),
    ("用 3 个菱形拼成两个梯形。", "3 个菱形"),
    ("用 1 个正六边形拆成 3 个菱形。", "1 个正六边形"),
    ("用 2 个正六边形拆成 4 个梯形。", "2 个正六边形"),
)


def _fmt(value: float) -> str:
    """把坐标格式化为两位小数，并去掉负零。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PatternError("坐标必须是数字")
    number = float(value)
    if not math.isfinite(number):
        raise PatternError("坐标必须是有限数值")
    rounded = round(number, 2)
    if rounded == 0.0:
        rounded = 0.0
    return "{0:.2f}".format(rounded)


def _ratio_text(ratio: float) -> str:
    """面积倍率文本：整数倍直接显示整数，否则保留两位小数。"""
    if abs(ratio - round(ratio)) < 1e-9:
        return "{0:.0f}".format(ratio)
    return "{0:.2f}".format(ratio)


def _css() -> str:
    """返回完整样式表。"""
    return (
        "@page {{ size: A4; margin: 0 }}\n"
        "* {{ box-sizing: border-box }}\n"
        "html, body {{ margin: 0; padding: 0 }}\n"
        "body {{ background: #eceff2; color: #1f2933; "
        'font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", '
        '"Noto Sans CJK SC", sans-serif; }}\n'
        ".page {{ position: relative; width: {page_w}mm; min-height: {page_h}mm; "
        "padding: {margin}mm; box-sizing: border-box; overflow: hidden; "
        "background: #ffffff; margin: 0 auto 6mm; page-break-after: always; }}\n"
        ".page:last-child {{ page-break-after: auto }}\n"
        ".page-header {{ position: absolute; top: 4mm; left: {margin}mm; "
        "right: {margin}mm; height: 5mm; display: flex; align-items: center; "
        "justify-content: space-between; font-size: 9pt; color: #52606d; }}\n"
        ".page-footer {{ position: absolute; bottom: 4mm; left: {margin}mm; "
        "right: {margin}mm; height: 5mm; display: flex; align-items: center; "
        "justify-content: space-between; font-size: 8.5pt; color: #7b8794; }}\n"
        ".blocks {{ display: block; width: {content_w}mm; height: {content_h}mm; }}\n"
        ".polygon-block {{ fill: {fill}; stroke: {stroke}; stroke-width: 0.6; "
        "stroke-linejoin: round; }}\n"
        ".polygon-legend {{ fill: {fill}; stroke: {stroke}; stroke-width: 0.5; "
        "stroke-linejoin: round; }}\n"
        ".shape-label {{ fill: {ink}; font-size: 6px; font-weight: 600; "
        "text-anchor: middle; dominant-baseline: central; }}\n"
        ".legend {{ display: block; width: 100%; height: auto; margin: 4mm 0 6mm; }}\n"
        ".legend-label {{ fill: #52606d; font-size: 3.2px; text-anchor: middle; }}\n"
        "h1 {{ margin: 0 0 2mm; font-size: 22pt; letter-spacing: 0.04em; }}\n"
        "h2 {{ margin: 0 0 3mm; font-size: 15pt; }}\n"
        "p {{ margin: 0 0 2mm; line-height: 1.55; }}\n"
        ".subtitle {{ color: #52606d; font-size: 10.5pt; margin-bottom: 6mm; }}\n"
        ".section-title {{ font-size: 11pt; font-weight: 600; margin: 6mm 0 2mm; "
        "color: #323f4b; }}\n"
        "table.area-table {{ width: 100%; border-collapse: collapse; "
        "font-size: 9.5pt; }}\n"
        "table.area-table caption {{ text-align: left; font-size: 9pt; "
        "color: #7b8794; padding-bottom: 1.5mm; }}\n"
        "table.area-table th, table.area-table td {{ border: 0.3mm solid {line}; "
        "padding: 1.6mm 2mm; text-align: left; }}\n"
        "table.area-table th {{ background: #f5f7fa; font-weight: 600; }}\n"
        "table.area-table td.num {{ text-align: right; font-variant-numeric: "
        "tabular-nums; }}\n"
        "ul.tips {{ margin: 0; padding-left: 5mm; font-size: 9.5pt; "
        "line-height: 1.7; color: #3e4c59; }}\n"
        "ol.challenges {{ margin: 0; padding-left: 6mm; }}\n"
        "ol.challenges li {{ margin-bottom: 3mm; font-size: 10pt; }}\n"
        ".answer-box {{ margin-top: 1.5mm; height: 14mm; border: 0.3mm dashed "
        "#9aa5b1; border-radius: 1.5mm; color: #b0b8c1; font-size: 8pt; "
        "padding: 1.5mm 2mm; }}\n"
        "ol.answers {{ margin: 0; padding-left: 6mm; font-size: 10pt; "
        "line-height: 1.8; }}\n"
        ".note {{ margin-top: 5mm; font-size: 9pt; color: #616e7c; "
        "border-left: 1mm solid #cbd2d9; padding-left: 3mm; }}\n"
        "@media print {{ body {{ background: #ffffff }} "
        ".page {{ margin: 0 }} }}\n"
    ).format(
        page_w="{0:g}".format(PAGE_W_MM),
        page_h="{0:g}".format(PAGE_H_MM),
        margin="{0:g}".format(MARGIN_MM),
        content_w="{0:g}".format(_CONTENT_W),
        content_h="{0:g}".format(_CONTENT_H),
        fill=_FILL,
        stroke=_STROKE,
        ink=_INK,
        line=_LINE,
    )


def _document(title: str, body: str) -> str:
    """包装为完整 HTML 文档。"""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>{title}</title>\n"
        "<style>\n{css}</style>\n"
        "</head>\n"
        "<body>\n{body}\n</body>\n"
        "</html>\n"
    ).format(title=html.escape(title), css=_css(), body=body)


def _page(content: str, header: str, footer: str) -> str:
    """生成单页结构，页眉页脚位于页边距内。"""
    return (
        '<section class="page">\n'
        '<div class="page-header">{header}</div>\n'
        "{content}\n"
        '<div class="page-footer">{footer}</div>\n'
        "</section>"
    ).format(header=header, content=content, footer=footer)


def _polygon_points(points: Sequence[tuple[float, float]]) -> str:
    """把顶点序列转换为 SVG points 属性值。"""
    if len(points) < 3:
        raise PatternError("多边形至少需要 3 个顶点")
    return " ".join(
        "{0},{1}".format(_fmt(x), _fmt(y)) for x, y in points
    )


def _shape_svg(
    points: Sequence[tuple[float, float]],
    side_mm: float,
    label: str | None = None,
    css_class: str = "polygon-block",
) -> str:
    """绘制单个多边形（可带中心简称）。"""
    parts = [
        '<polygon class="{cls}" points="{pts}" />'.format(
            cls=html.escape(css_class, quote=True),
            pts=_polygon_points(points),
        )
    ]
    if label:
        center_x = sum(point[0] for point in points) / len(points)
        center_y = sum(point[1] for point in points) / len(points)
        size = max(2.2, min(side_mm * 0.22, 8.0))
        parts.append(
            '<text class="shape-label" x="{x}" y="{y}" font-size="{size}px">{text}</text>'.format(
                x=_fmt(center_x),
                y=_fmt(center_y),
                size=_fmt(size),
                text=html.escape(label),
            )
        )
    return "".join(parts)


def _area_table(side_mm: float) -> str:
    """面积对照表：形状、边长、面积、相当于几个三角形。"""
    rows: list[str] = []
    for name in SHAPE_ORDER:
        area = polygon_area(shape_vertices(name, side_mm))
        ratio = area_in_triangles(name, side_mm)
        rows.append(
            "<tr>"
            "<td>{label}</td>"
            '<td class="num">{side}</td>'
            '<td class="num">{area}</td>'
            '<td class="num">{ratio}</td>'
            "</tr>".format(
                label=html.escape(SHAPE_LABELS[name]),
                side="{0:g} mm".format(side_mm),
                area="{0:.2f} mm²".format(area),
                ratio=_ratio_text(ratio),
            )
        )
    return (
        '<table class="area-table">\n'
        "<caption>面积对照表（统一边长 {side:g} mm，三角形族面积比 1:2:3:6）</caption>\n"
        "<thead><tr><th>形状</th><th>边长</th><th>面积</th><th>相当于几个三角形</th></tr></thead>\n"
        "<tbody>\n{rows}\n</tbody>\n"
        "</table>"
    ).format(side=side_mm, rows="\n".join(rows))


def _legend_svg() -> str:
    """封面用的五种积木图例。"""
    cell = _CONTENT_W / float(len(SHAPE_ORDER))
    parts: list[str] = []
    for index, name in enumerate(SHAPE_ORDER):
        vertices = shape_vertices(name, 16.0)
        min_x, min_y, max_x, max_y = shape_bounds(vertices)
        center_x = cell * (index + 0.5)
        offset_x = center_x - (min_x + max_x) / 2.0
        offset_y = 14.5 - (min_y + max_y) / 2.0
        points = [(x + offset_x, y + offset_y) for x, y in vertices]
        parts.append(_shape_svg(points, 16.0, SHAPE_SHORT_LABELS[name], "polygon-legend"))
        parts.append(
            '<text class="legend-label" x="{x}" y="{y}">{text}</text>'.format(
                x=_fmt(center_x), y=_fmt(36.0), text=html.escape(SHAPE_LABELS[name])
            )
        )
    return (
        '<svg class="legend" xmlns="http://www.w3.org/2000/svg" '
        'viewBox="0 0 {w} 40" role="img" aria-label="五种积木图例" '
        'preserveAspectRatio="xMidYMid meet">\n{parts}\n</svg>'
    ).format(w=_fmt(_CONTENT_W), parts="\n".join(parts))


def _cutout_svg(placements: Sequence[Placement], side_mm: float) -> str:
    """生成一页积木的 SVG，坐标以正文区域左上角为原点。"""
    parts: list[str] = []
    for placement in placements:
        points = [
            (x - MARGIN_MM, y - MARGIN_MM) for x, y in placement.vertices
        ]
        parts.append(
            _shape_svg(points, side_mm, SHAPE_SHORT_LABELS[placement.name], "polygon-block")
        )
    return (
        '<svg class="blocks" xmlns="http://www.w3.org/2000/svg" '
        'viewBox="0.00 0.00 {w} {h}" width="{w}mm" height="{h}mm" '
        'preserveAspectRatio="xMidYMid meet" role="img" '
        'aria-label="图案积木裁剪页">\n{parts}\n</svg>'
    ).format(
        w=_fmt(_CONTENT_W),
        h=_fmt(_CONTENT_H),
        parts="\n".join(parts),
    )


def _cover_page(
    side_mm: float, title: str, total_pages: int, show_challenges: bool
) -> str:
    """封面页：标题、面积对照表、图例与使用说明。"""
    tips = [
        "<li>打印：A4 纸、缩放 100%（1:1），不要选择「适合页面」。</li>",
        "<li>剪裁：沿每个图形的实线轮廓剪下，图形中心的小字仅作分类提示。</li>",
        "<li>分类：三角形的边长与菱形、梯形、正六边形一致，可以无缝拼合。</li>",
    ]
    if show_challenges:
        tips.append(
            "<li>挑战：裁剪页之后附有拼图挑战卡与答案页，答案页可先折叠收起。</li>"
        )
    content = (
        "<h1>{title}</h1>\n"
        '<p class="subtitle">统一边长 {side:g} mm · 五种图案积木 · A4 1:1 打印</p>\n'
        "{legend}\n"
        '<div class="section-title">面积对照</div>\n'
        "{table}\n"
        '<div class="section-title">使用说明</div>\n'
        '<ul class="tips">\n{tips}\n</ul>'
    ).format(
        title=html.escape(title),
        side=side_mm,
        legend=_legend_svg(),
        table=_area_table(side_mm),
        tips="\n".join(tips),
    )
    header = "<span>{title}</span><span>A4 · 1:1 打印</span>".format(
        title=html.escape(title)
    )
    footer = "<span>图案积木 · 统一边长 {side:g} mm</span><span>第 1 / {total} 页</span>".format(
        side=side_mm, total=total_pages
    )
    return _page(content, header, footer)


def _cutout_page(
    placements: Sequence[Placement],
    side_mm: float,
    title: str,
    page_no: int,
    total_pages: int,
) -> str:
    """一页裁剪页。"""
    header = "<span>{title}</span><span>边长 {side:g} mm · 共 {count} 片</span>".format(
        title=html.escape(title), side=side_mm, count=len(placements)
    )
    footer = "<span>沿实线剪下</span><span>第 {no} / {total} 页</span>".format(
        no=page_no, total=total_pages
    )
    return _page(_cutout_svg(placements, side_mm), header, footer)


def _challenge_section() -> str:
    """挑战卡正文（共 10 题，每题带作答框）。"""
    items: list[str] = []
    for index, (question, _) in enumerate(_CHALLENGES, start=1):
        items.append(
            "<li>"
            '<div class="challenge-title">第 {no} 题：{question}</div>\n'
            '<div class="answer-box">作答区（可在框内画出拼法，并写出所用积木数量）</div>'
            "</li>".format(no=index, question=html.escape(question))
        )
    return (
        "<h2>拼图挑战卡</h2>\n"
        '<p class="subtitle">用裁剪好的积木完成下列任务，并在作答框内画出拼法。</p>\n'
        '<ol class="challenges">\n{items}\n</ol>'
    ).format(items="\n".join(items))


def _answer_section() -> str:
    """答案页正文。"""
    items: list[str] = []
    for index, (question, answer) in enumerate(_CHALLENGES, start=1):
        items.append(
            "<li>第 {no} 题：{answer}（题目：{question}）</li>".format(
                no=index,
                answer=html.escape(answer),
                question=html.escape(question),
            )
        )
    return (
        "<h2>挑战答案</h2>\n"
        '<p class="subtitle">参考答案：每题的积木种类与数量。</p>\n'
        '<ol class="answers">\n{items}\n</ol>\n'
        '<p class="note">等边三角形、菱形、梯形、正六边形的面积比为 1:2:3:6；'
        "正方形边长同样是统一边长，但面积为边长的平方，不计入该比例。</p>"
    ).format(items="\n".join(items))


def count_pages(block_pages: int, show_challenges: bool = True) -> int:
    """统计完整文档的总页数（封面 + 裁剪页 + 可选挑战页与答案页）。"""
    if isinstance(block_pages, bool) or not isinstance(block_pages, int):
        raise PatternError("裁剪页数量必须是整数")
    if block_pages < 0:
        raise PatternError("裁剪页数量不能为负数")
    return 1 + block_pages + (2 if show_challenges else 0)


def render_blocks(
    pages: Sequence[Sequence[Placement]],
    side_mm: float,
    title: str = "图案积木裁剪片",
    show_challenges: bool = True,
) -> str:
    """渲染完整的 A4 打印文档，返回 HTML 字符串。"""
    if not isinstance(title, str) or not title.strip():
        raise PatternError("标题不能为空")
    side = validate_side(side_mm)
    if not isinstance(pages, Sequence) or isinstance(pages, (str, bytes)):
        raise PatternError("页面数据必须是按页分组的摆放列表")

    for page in pages:
        if not isinstance(page, Sequence) or isinstance(page, (str, bytes)):
            raise PatternError("页面数据必须是摆放列表")
        for placement in page:
            if not isinstance(placement, Placement):
                raise PatternError("页面中的每一项都必须是 Placement")
            if placement.name not in SHAPE_ORDER:
                raise PatternError("出现未知形状：" + str(placement.name))

    total_pages = count_pages(len(pages), show_challenges)
    sections: list[str] = [
        _cover_page(side, title, total_pages, show_challenges)
    ]

    for index, page in enumerate(pages, start=2):
        sections.append(_cutout_page(page, side, title, index, total_pages))

    if show_challenges:
        challenge_no = 2 + len(pages)
        sections.append(
            _page(
                _challenge_section(),
                "<span>拼图挑战卡</span><span>共 {count} 题</span>".format(
                    count=len(_CHALLENGES)
                ),
                "<span>画出你的拼法</span><span>第 {no} / {total} 页</span>".format(
                    no=challenge_no, total=total_pages
                ),
            )
        )
        sections.append(
            _page(
                _answer_section(),
                "<span>挑战答案</span><span>参考答案</span>",
                "<span>对照检查拼法</span><span>第 {no} / {total} 页</span>".format(
                    no=total_pages, total=total_pages
                ),
            )
        )

    return _document(title, "\n".join(sections))


def render_challenge_page(side_mm: float) -> str:
    """单独渲染挑战卡页（完整 HTML 文档）。"""
    side = validate_side(side_mm)
    content = (
        _challenge_section()
        + '\n<p class="note">提示：所有积木边长均为 {side:g} mm，'
        "可以任意旋转、翻面后拼接。</p>".format(side=side)
    )
    return _document(
        "拼图挑战卡",
        _page(
            content,
            "<span>拼图挑战卡</span><span>边长 {side:g} mm</span>".format(side=side),
            "<span>画出你的拼法</span><span>第 1 / 1 页</span>",
        ),
    )


def render_answer_page() -> str:
    """单独渲染答案页（完整 HTML 文档）。"""
    return _document(
        "挑战答案",
        _page(
            _answer_section(),
            "<span>挑战答案</span><span>参考答案</span>",
            "<span>对照检查拼法</span><span>第 1 / 1 页</span>",
        ),
    )
