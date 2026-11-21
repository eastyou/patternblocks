from __future__ import annotations

# patternblocks：图案积木裁剪片。

from patternblocks.model import (
    GAP_MM,
    MARGIN_MM,
    MAX_EACH,
    MAX_SIDE_MM,
    MIN_EACH,
    MIN_SIDE_MM,
    PAGE_H_MM,
    PAGE_W_MM,
    SHAPE_LABELS,
    SHAPE_ORDER,
    SHAPE_SHORT_LABELS,
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
from patternblocks.render import (
    count_pages,
    render_answer_page,
    render_blocks,
    render_challenge_page,
)

__version__ = "0.1.0"

__all__ = [
    "GAP_MM",
    "MARGIN_MM",
    "MAX_EACH",
    "MAX_SIDE_MM",
    "MIN_EACH",
    "MIN_SIDE_MM",
    "PAGE_H_MM",
    "PAGE_W_MM",
    "SHAPE_LABELS",
    "SHAPE_ORDER",
    "SHAPE_SHORT_LABELS",
    "SIDE_MM",
    "PatternError",
    "Placement",
    "area_in_triangles",
    "build_layout",
    "count_pages",
    "polygon_area",
    "render_answer_page",
    "render_blocks",
    "render_challenge_page",
    "shape_bounds",
    "shape_vertices",
    "validate_each",
    "validate_shapes",
    "validate_side",
]
