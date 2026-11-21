from __future__ import annotations

# 命令行入口：生成图案积木裁剪片 HTML。

import argparse
import sys
from pathlib import Path

from patternblocks.model import (
    MAX_EACH,
    MAX_SIDE_MM,
    MIN_EACH,
    MIN_SIDE_MM,
    SHAPE_LABELS,
    SHAPE_ORDER,
    PatternError,
    build_layout,
    validate_each,
    validate_shapes,
    validate_side,
)
from patternblocks.render import count_pages, render_blocks


def _build_parser() -> argparse.ArgumentParser:
    """构建参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="patternblocks",
        description="生成 A4 可打印的图案积木裁剪片与拼图挑战卡",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="patternblocks.html",
        help="输出 HTML 文件路径（默认 patternblocks.html）",
    )
    parser.add_argument(
        "--side",
        default="30",
        help="统一边长，单位 mm，范围 {low:g}～{high:g}（默认 30）".format(
            low=MIN_SIDE_MM, high=MAX_SIDE_MM
        ),
    )
    parser.add_argument(
        "--each",
        default="6",
        help="每种形状的数量，范围 {low}～{high}（默认 6）".format(
            low=MIN_EACH, high=MAX_EACH
        ),
    )
    parser.add_argument(
        "--shapes",
        default=None,
        help="逗号分隔的形状名，中英文均可（默认全部：{names}）".format(
            names="、".join(SHAPE_LABELS[name] for name in SHAPE_ORDER)
        ),
    )
    parser.add_argument(
        "--no-challenges",
        action="store_true",
        help="不生成拼图挑战卡与答案页",
    )
    parser.add_argument(
        "--title",
        default="图案积木裁剪片",
        help="文档标题（默认：图案积木裁剪片）",
    )
    return parser


def _parse_side(raw: str) -> float:
    """把命令行字符串解析为合法边长。"""
    if not isinstance(raw, str):
        raise PatternError("边长必须是数字")
    text = raw.strip()
    if not text:
        raise PatternError("边长不能为空")
    try:
        value = float(text)
    except ValueError as exc:
        raise PatternError("边长必须是数字：" + text) from exc
    return validate_side(value)


def _parse_each(raw: str) -> int:
    """把命令行字符串解析为合法数量。"""
    if not isinstance(raw, str):
        raise PatternError("每种形状的数量必须是整数")
    text = raw.strip()
    if not text:
        raise PatternError("每种形状的数量不能为空")
    try:
        value = int(text, 10)
    except ValueError as exc:
        raise PatternError("每种形状的数量必须是整数：" + text) from exc
    return validate_each(value)


def _resolve_shapes(raw: str | None) -> list[str]:
    """解析形状参数，缺省时返回全部形状。"""
    if raw is None:
        return list(SHAPE_ORDER)
    return validate_shapes(raw)


def main(argv: list[str] | None = None) -> int:
    """执行命令并返回退出码：0 成功，1 写文件失败，2 参数错误。"""
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 2

    try:
        side = _parse_side(args.side)
        each = _parse_each(args.each)
        names = _resolve_shapes(args.shapes)
        pages = build_layout(names, each, side_mm=side)
    except PatternError as exc:
        print("参数错误：" + str(exc), file=sys.stderr)
        return 2

    try:
        document = render_blocks(
            pages,
            side,
            title=args.title,
            show_challenges=not args.no_challenges,
        )
    except PatternError as exc:
        print("参数错误：" + str(exc), file=sys.stderr)
        return 2

    total_pages = count_pages(len(pages), not args.no_challenges)
    block_count = sum(len(page) for page in pages)

    try:
        target = Path(args.output)
        if str(target.parent) not in ("", "."):
            target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(document)
    except OSError as exc:
        print("写入文件失败：" + str(exc), file=sys.stderr)
        return 1

    print(
        "已生成 {path}（{pages} 页，{blocks} 片积木）".format(
            path=args.output, pages=total_pages, blocks=block_count
        )
    )
    return 0
