# -*- coding: utf-8 -*-
"""
Unified MathFigure Specification Builder & Standalone Vector Exporter.
Adheres to rules/03_stem.md: Semantic Educational Diagrams.

Supports:
1. 2D Euclidean Geometry:
   - Polygons (Rectangles, Triangles, Quadrilaterals)
   - Circles and Arcs
   - Exact Right Angle Markers (arbitrary angle/rotation)
   - Directed Angle Arc Markers
   - KaTeX Dimension Labels & Point Labels
2. Cartesian Graphs:
   - Coordinate Axes with Ticks and Arrows
   - Linear Functions (y = mx + c), Polynomials
   - Points with Coordinate Labels & Projection Segments
   - Slopes and Intercepts
3. Standalone SVG Converter:
   - Headless export for Notion File Uploads & Web rendering
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple

FIGURE_THEMES = {
    "indigo": {
        "stroke": "#6366f1",
        "fill": "rgba(99, 102, 241, 0.08)",
        "accent": "#4f46e5",
        "text": "#1e293b",
    },
    "blue": {
        "stroke": "#0284c7",
        "fill": "rgba(14, 165, 233, 0.08)",
        "accent": "#0369a1",
        "text": "#1e293b",
    },
    "emerald": {
        "stroke": "#059669",
        "fill": "rgba(16, 185, 129, 0.08)",
        "accent": "#047857",
        "text": "#1e293b",
    },
    "amber": {
        "stroke": "#d97706",
        "fill": "rgba(245, 158, 11, 0.08)",
        "accent": "#b45309",
        "text": "#1e293b",
    },
    "rose": {
        "stroke": "#e11d48",
        "fill": "rgba(244, 63, 94, 0.08)",
        "accent": "#be123c",
        "text": "#1e293b",
    },
    "purple": {
        "stroke": "#7c3aed",
        "fill": "rgba(139, 92, 246, 0.08)",
        "accent": "#6d28d9",
        "text": "#1e293b",
    },
}


# ==============================================================================
# 2D GEOMETRY BUILDERS
# ==============================================================================


def build_rectangle_figure(
    width: float,
    height: float,
    label_w: Optional[str] = None,
    label_h: Optional[str] = None,
    theme: str = "indigo",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a semantic MathFigure for a 2D Rectangle."""
    lbl_w = label_w or f"{width:g}"
    lbl_h = label_h or f"{height:g}"

    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Rectangle",
        "points": {
            "A": [0, 0],
            "B": [round(width, 2), 0],
            "C": [round(width, 2), round(height, 2)],
            "D": [0, round(height, 2)],
        },
        "shapes": [
            {
                "type": "polygon",
                "vertices": ["A", "B", "C", "D"],
                "fill": True,
            }
        ],
        "markers": [
            {
                "type": "right_angle",
                "vertex": "A",
                "arm1": "B",
                "arm2": "D",
            }
        ],
        "labels": [
            {
                "type": "segment",
                "p1": "A",
                "p2": "B",
                "text": lbl_w,
                "side": "bottom",
            },
            {
                "type": "segment",
                "p1": "B",
                "p2": "C",
                "text": lbl_h,
                "side": "right",
            },
        ],
    }


def build_right_triangle_figure(
    base: float,
    height: float,
    label_base: Optional[str] = None,
    label_height: Optional[str] = None,
    label_hypot: Optional[str] = None,
    highlight_hypot: bool = False,
    theme: str = "emerald",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a semantic MathFigure for a Right-Angled Triangle."""
    c = math.sqrt(base**2 + height**2)
    lbl_b = label_base or f"{base:g}"
    lbl_a = label_height or f"{height:g}"
    lbl_c = label_hypot or (f"{c:g}" if abs(c - round(c)) < 1e-4 else f"\\sqrt{{{base**2 + height**2:g}}}")

    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Right Triangle",
        "points": {
            "A": [0, 0],
            "B": [round(base, 2), 0],
            "C": [0, round(height, 2)],
        },
        "shapes": [
            {
                "type": "polygon",
                "vertices": ["A", "B", "C"],
                "fill": True,
            }
        ],
        "markers": [
            {
                "type": "right_angle",
                "vertex": "A",
                "arm1": "B",
                "arm2": "C",
            }
        ],
        "labels": [
            {
                "type": "segment",
                "p1": "A",
                "p2": "B",
                "text": lbl_b,
                "side": "bottom",
            },
            {
                "type": "segment",
                "p1": "A",
                "p2": "C",
                "text": lbl_a,
                "side": "left",
            },
            {
                "type": "segment",
                "p1": "C",
                "p2": "B",
                "text": lbl_c,
                "side": "hypotenuse",
                "highlight": highlight_hypot,
            },
        ],
    }


def build_circle_figure(
    radius: float,
    label_radius: Optional[str] = None,
    show_center_dot: bool = True,
    theme: str = "blue",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a semantic MathFigure for a Circle with radius indicator."""
    lbl_r = label_radius or f"r = {radius:g}"
    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Circle",
        "points": {
            "O": [0, 0],
            "P": [round(radius, 2), 0],
        },
        "shapes": [
            {
                "type": "circle",
                "center": "O",
                "radius": round(radius, 2),
                "fill": True,
            },
            {
                "type": "segment",
                "from": "O",
                "to": "P",
                "strokeDasharray": "3 3",
            },
        ],
        "labels": [
            {
                "type": "point",
                "point": "O",
                "text": "O",
                "position": "bottom-left",
            },
            {
                "type": "segment",
                "p1": "O",
                "p2": "P",
                "text": lbl_r,
                "side": "top",
            },
        ],
    }


# ==============================================================================
# CARTESIAN GRAPH BUILDERS
# ==============================================================================


def build_cartesian_point_figure(
    coord: Tuple[float, float],
    label: Optional[str] = None,
    x_range: Optional[Tuple[float, float]] = None,
    y_range: Optional[Tuple[float, float]] = None,
    show_projections: bool = True,
    theme: str = "blue",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a Cartesian graph showing a plotted point (x, y) with dashed projection to axes."""
    px, py = coord
    lbl = label or f"P({px:g}, {py:g})"

    if x_range is None:
        margin_x = max(abs(px) * 0.4, 2)
        x_min = min(0, px) - margin_x
        x_max = max(0, px) + margin_x
        x_range = (math.floor(x_min), math.ceil(x_max))

    if y_range is None:
        margin_y = max(abs(py) * 0.4, 2)
        y_min = min(0, py) - margin_y
        y_max = max(0, py) + margin_y
        y_range = (math.floor(y_min), math.ceil(y_max))

    plots: List[Dict[str, Any]] = []

    if show_projections:
        # Projection to X axis
        plots.append(
            {
                "type": "segment",
                "from": [px, 0],
                "to": [px, py],
                "strokeDasharray": "3 3",
                "color": "#94a3b8",
            }
        )
        # Projection to Y axis
        plots.append(
            {
                "type": "segment",
                "from": [0, py],
                "to": [px, py],
                "strokeDasharray": "3 3",
                "color": "#94a3b8",
            }
        )

    # Plotted point
    plots.append(
        {
            "type": "point",
            "coord": [px, py],
            "label": lbl,
            "position": "top-right" if py >= 0 else "bottom-right",
        }
    )

    return {
        "kind": "cartesian_graph",
        "theme": theme,
        "title": title or "Cartesian Coordinate Plane",
        "xRange": list(x_range),
        "yRange": list(y_range),
        "grid": True,
        "axes": True,
        "plots": plots,
    }


def build_cartesian_line_figure(
    m: float,
    c: float,
    x_range: Tuple[float, float] = (-5, 5),
    y_range: Tuple[float, float] = (-5, 5),
    show_intercepts: bool = True,
    theme: str = "indigo",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a Cartesian graph plotting the linear equation y = mx + c."""
    c_str = f" + {c:g}" if c > 0 else f" - {abs(c):g}" if c < 0 else ""
    m_str = "" if m == 1 else "-" if m == -1 else f"{m:g}"
    expr_label = f"y = {m_str}x{c_str}"

    plots: List[Dict[str, Any]] = [
        {
            "type": "function",
            "coefficients": [round(m, 4), round(c, 4)],
            "expression": expr_label,
            "color": FIGURE_THEMES.get(theme, FIGURE_THEMES["indigo"])["stroke"],
            "strokeWidth": 2.5,
        }
    ]

    if show_intercepts:
        # Y-intercept: (0, c)
        if y_range[0] <= c <= y_range[1]:
            plots.append(
                {
                    "type": "point",
                    "coord": [0, c],
                    "label": f"(0, {c:g})",
                    "position": "right",
                }
            )
        # X-intercept: (-c / m, 0) if m != 0
        if abs(m) > 1e-6:
            x_int = -c / m
            if x_range[0] <= x_int <= x_range[1] and abs(x_int) > 1e-4:
                plots.append(
                    {
                        "type": "point",
                        "coord": [round(x_int, 2), 0],
                        "label": f"({round(x_int, 2):g}, 0)",
                        "position": "top",
                    }
                )

    return {
        "kind": "cartesian_graph",
        "theme": theme,
        "title": title or f"Graph: {expr_label}",
        "xRange": list(x_range),
        "yRange": list(y_range),
        "grid": True,
        "axes": True,
        "plots": plots,
    }


def build_transversal_figure(
    angle_acute: float = 70.0,
    angle_obtuse: float = 110.0,
    label_acute: str = "(2x + 10)^\\circ",
    label_obtuse: str = "(3x + 20)^\\circ",
    theme: str = "indigo",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a semantic MathFigure for two parallel lines cut by a transversal."""
    rad = math.radians(angle_acute)
    dx = 4.0 / math.tan(rad) if abs(math.sin(rad)) > 1e-4 else 2.0
    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Parallel Tracks & Transversal",
        "points": {
            "L1_L": [-2, 4],
            "L1_R": [10, 4],
            "L2_L": [-2, 0],
            "L2_R": [10, 0],
            "T_TOP": [4 + dx, 5.5],
            "P1": [4, 4],
            "P2": [4 - dx, 0],
            "T_BOT": [4 - 2 * dx, -1.5],
        },
        "shapes": [
            {"type": "segment", "from": "L1_L", "to": "L1_R"},
            {"type": "segment", "from": "L2_L", "to": "L2_R"},
            {"type": "segment", "from": "T_BOT", "to": "T_TOP", "strokeWidth": 2.5},
        ],
        "markers": [
            {"type": "angle_arc", "vertex": "P1", "arm1": "L1_R", "arm2": "P2", "label": label_obtuse, "radius": 24},
            {"type": "angle_arc", "vertex": "P2", "arm1": "P1", "arm2": "L2_R", "label": label_acute, "radius": 24},
        ],
        "labels": [
            {"type": "point", "point": "L1_R", "text": "L_1", "position": "right"},
            {"type": "point", "point": "L2_R", "text": "L_2", "position": "right"},
        ],
    }


def build_isosceles_triangle_figure(
    base: float,
    apex_angle: float = 44.0,
    label_apex: str = "44^\\circ",
    label_exterior: Optional[str] = None,
    theme: str = "indigo",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a semantic MathFigure for an Isosceles Triangle with optional extended base."""
    half_apex_rad = math.radians(apex_angle / 2)
    h = (base / 2) / math.tan(half_apex_rad) if math.tan(half_apex_rad) > 1e-4 else base
    pts = {
        "A": [-base / 2, 0],
        "B": [base / 2, 0],
        "C": [0, round(h, 2)],
        "EXT": [base / 2 + base * 0.35, 0],
    }
    markers = [
        {"type": "angle_arc", "vertex": "C", "arm1": "A", "arm2": "B", "label": label_apex, "radius": 26},
    ]
    if label_exterior:
        markers.append(
            {"type": "angle_arc", "vertex": "B", "arm1": "EXT", "arm2": "C", "label": label_exterior, "radius": 24}
        )
    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Truss Isosceles Triangle",
        "points": pts,
        "shapes": [
            {"type": "polygon", "vertices": ["A", "B", "C"], "fill": True},
            {"type": "segment", "from": "B", "to": "EXT", "strokeDasharray": "3 3"},
        ],
        "markers": markers,
    }


def build_trapezoid_figure(
    top_base: float,
    bottom_base: float,
    sloped_side: float,
    label_top: Optional[str] = None,
    label_bottom: Optional[str] = None,
    label_side: Optional[str] = None,
    label_height: Optional[str] = None,
    theme: str = "blue",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a semantic MathFigure for an Isosceles Trapezoid with dashed altitude."""
    dx = abs(top_base - bottom_base) / 2
    h = math.sqrt(max(sloped_side**2 - dx**2, 1.0))
    b_half = bottom_base / 2
    t_half = top_base / 2
    pts = {
        "B1": [-b_half, 0],
        "B2": [b_half, 0],
        "T2": [t_half, round(h, 2)],
        "T1": [-t_half, round(h, 2)],
        "H_BOT": [-t_half, 0],
    }
    shapes = [
        {"type": "polygon", "vertices": ["B1", "B2", "T2", "T1"], "fill": True},
        {"type": "segment", "from": "T1", "to": "H_BOT", "strokeDasharray": "3 3", "strokeWidth": 1.5},
    ]
    markers = [{"type": "right_angle", "vertex": "H_BOT", "arm1": "B1", "arm2": "T1"}]
    labels = [
        {"type": "segment", "p1": "T1", "p2": "T2", "text": label_top or f"{top_base:g}\\text{{ m}}", "side": "top"},
        {
            "type": "segment",
            "p1": "B1",
            "p2": "B2",
            "text": label_bottom or f"{bottom_base:g}\\text{{ m}}",
            "side": "bottom",
        },
        {
            "type": "segment",
            "p1": "B2",
            "p2": "T2",
            "text": label_side or f"{sloped_side:g}\\text{{ m}}",
            "side": "right",
        },
    ]
    if label_height:
        labels.append({"type": "segment", "p1": "T1", "p2": "H_BOT", "text": label_height, "side": "left"})

    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Retention Basin Trapezoid",
        "points": pts,
        "shapes": shapes,
        "markers": markers,
        "labels": labels,
    }


def build_annulus_figure(
    r_inner: float,
    r_outer: float,
    label_inner: Optional[str] = None,
    label_outer: Optional[str] = None,
    label_gap: Optional[str] = None,
    theme: str = "indigo",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a semantic MathFigure for a circular Annulus (ring)."""
    pts = {
        "O": [0, 0],
        "P_IN": [round(r_inner, 2), 0],
        "P_OUT": [round(r_outer, 2), 0],
    }
    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Turbofan Nacelle Annulus",
        "points": pts,
        "shapes": [
            {"type": "circle", "center": "O", "radius": round(r_outer, 2), "fill": True},
            {"type": "circle", "center": "O", "radius": round(r_inner, 2), "fill": False, "strokeDasharray": "4 3"},
            {"type": "segment", "from": "O", "to": "P_OUT", "strokeDasharray": "2 2"},
        ],
        "labels": [
            {"type": "point", "point": "O", "text": "O", "position": "bottom-left"},
            {
                "type": "segment",
                "p1": "O",
                "p2": "P_IN",
                "text": label_inner or f"r = {r_inner:g}\\text{{ dm}}",
                "side": "bottom",
            },
            {
                "type": "segment",
                "p1": "P_IN",
                "p2": "P_OUT",
                "text": label_gap or f"{r_outer - r_inner:g}\\text{{ dm}}",
                "side": "top",
                "highlight": True,
            },
        ],
    }


def build_box3d_figure(
    width: float,
    length: float,
    height: float,
    label_w: Optional[str] = None,
    label_l: Optional[str] = None,
    label_h: Optional[str] = None,
    label_diag: Optional[str] = None,
    theme: str = "emerald",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a semantic MathFigure for an oblique 3D Box with space diagonal."""
    dx = length * 0.45
    dy = length * 0.35
    w, h = width, height
    pts = {
        "F1": [0, 0],
        "F2": [w, 0],
        "F3": [w, h],
        "F4": [0, h],
        "B1": [dx, dy],
        "B2": [w + dx, dy],
        "B3": [w + dx, h + dy],
        "B4": [dx, h + dy],
    }
    shapes = [
        {"type": "polygon", "vertices": ["F1", "F2", "F3", "F4"], "fill": True},
        {"type": "polygon", "vertices": ["F4", "F3", "B3", "B4"], "fill": True},
        {"type": "polygon", "vertices": ["F2", "B2", "B3", "F3"], "fill": True},
        {"type": "segment", "from": "F1", "to": "B1", "strokeDasharray": "3 3"},
        {"type": "segment", "from": "B1", "to": "B2", "strokeDasharray": "3 3"},
        {"type": "segment", "from": "B1", "to": "B4", "strokeDasharray": "3 3"},
        {
            "type": "segment",
            "from": "F1",
            "to": "B3",
            "strokeDasharray": "4 2",
            "strokeWidth": 2.5,
            "stroke": "#ea580c",
        },
    ]
    labels = [
        {"type": "segment", "p1": "F1", "p2": "F2", "text": label_w or f"w = {w:g}\\text{{ m}}", "side": "bottom"},
        {"type": "segment", "p1": "F2", "p2": "B2", "text": label_l or f"l = {length:g}\\text{{ m}}", "side": "right"},
        {"type": "segment", "p1": "F1", "p2": "F4", "text": label_h or f"h = {h:g}\\text{{ m}}", "side": "left"},
    ]
    if label_diag:
        labels.append({"type": "segment", "p1": "F1", "p2": "B3", "text": label_diag, "side": "top", "highlight": True})

    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Cargo Container 3D Diagonal",
        "points": pts,
        "shapes": shapes,
        "labels": labels,
    }


def build_silo_figure(
    radius: float,
    h_cyl: float,
    h_cone: float,
    theme: str = "amber",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a semantic MathFigure for a Grain Storage Silo (Cylinder + Cone)."""
    ry = radius * 0.28
    pts = {
        "C_BOT": [0, 0],
        "C_MID": [0, h_cyl],
        "APEX": [0, h_cyl + h_cone],
        "L_BOT": [-radius, 0],
        "R_BOT": [radius, 0],
        "L_MID": [-radius, h_cyl],
        "R_MID": [radius, h_cyl],
    }
    shapes = [
        {"type": "segment", "from": "L_BOT", "to": "L_MID"},
        {"type": "segment", "from": "R_BOT", "to": "R_MID"},
        {"type": "ellipse", "center": "C_BOT", "radiusX": radius, "radiusY": ry, "strokeDasharray": "3 3"},
        {"type": "ellipse", "center": "C_MID", "radiusX": radius, "radiusY": ry, "fill": True},
        {"type": "segment", "from": "L_MID", "to": "APEX"},
        {"type": "segment", "from": "R_MID", "to": "APEX"},
        {"type": "segment", "from": "C_MID", "to": "APEX", "strokeDasharray": "3 3"},
        {"type": "segment", "from": "C_MID", "to": "R_MID", "strokeDasharray": "2 2"},
    ]
    labels = [
        {"type": "segment", "p1": "L_BOT", "p2": "L_MID", "text": f"h_1 = {h_cyl:g}\\text{{ m}}", "side": "left"},
        {"type": "segment", "p1": "C_MID", "p2": "APEX", "text": f"h_2 = {h_cone:g}\\text{{ m}}", "side": "right"},
        {"type": "segment", "p1": "C_MID", "p2": "R_MID", "text": f"r = {radius:g}\\text{{ m}}", "side": "bottom"},
    ]
    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Grain Storage Silo",
        "points": pts,
        "shapes": shapes,
        "labels": labels,
    }


def build_cylinder_figure(
    radius: float,
    height: float,
    theme: str = "blue",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a semantic MathFigure for a Submersible Cylinder Housing."""
    ry = radius * 0.3
    pts = {
        "C_BOT": [0, 0],
        "C_TOP": [0, height],
        "L_BOT": [-radius, 0],
        "R_BOT": [radius, 0],
        "L_TOP": [-radius, height],
        "R_TOP": [radius, height],
    }
    shapes = [
        {"type": "segment", "from": "L_BOT", "to": "L_TOP"},
        {"type": "segment", "from": "R_BOT", "to": "R_TOP"},
        {"type": "ellipse", "center": "C_BOT", "radiusX": radius, "radiusY": ry, "strokeDasharray": "3 3"},
        {"type": "ellipse", "center": "C_TOP", "radiusX": radius, "radiusY": ry, "fill": True},
        {"type": "segment", "from": "C_TOP", "to": "R_TOP", "strokeDasharray": "2 2"},
    ]
    labels = [
        {"type": "segment", "p1": "L_BOT", "p2": "L_TOP", "text": f"h = {height:g}\\text{{ dm}}", "side": "left"},
        {"type": "segment", "p1": "C_TOP", "p2": "R_TOP", "text": f"r = {radius:g}\\text{{ dm}}", "side": "top"},
    ]
    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Submersible Cylinder Housing",
        "points": pts,
        "shapes": shapes,
        "labels": labels,
    }


def build_cartesian_slope_triangle_figure(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    m: float,
    theme: str = "amber",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a Cartesian graph showing points P1, P2 and a Slope Triangle."""
    x1, y1 = p1
    x2, y2 = p2
    x_min = min(x1, x2) - 2
    x_max = max(x1, x2) + 2
    y_min = min(y1, y2) - 2
    y_max = max(y1, y2) + 2

    return {
        "kind": "cartesian_graph",
        "theme": theme,
        "title": title or f"Slope Triangle (m = {m:g})",
        "xRange": [math.floor(x_min), math.ceil(x_max)],
        "yRange": [math.floor(y_min), math.ceil(y_max)],
        "grid": True,
        "axes": True,
        "plots": [
            {
                "type": "slope_triangle",
                "p1": [x1, y1],
                "p2": [x2, y2],
            },
            {
                "type": "point",
                "coord": [x1, y1],
                "label": f"({x1:g}, {y1:g})",
                "position": "bottom-left",
            },
            {
                "type": "point",
                "coord": [x2, y2],
                "label": f"({x2:g}, {y2:g})",
                "position": "top-right",
            },
        ],
    }


def build_cartesian_horizontal_line_figure(
    y_val: float,
    x1: float,
    x2: float,
    theme: str = "indigo",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a Cartesian graph for a horizontal line corridor."""
    x_min = min(0, x1) - 2
    x_max = (x2 + 3) if isinstance(x2, (int, float)) else 15
    y_min = min(0, y_val) - 2
    y_max = max(0, y_val) + 3

    return {
        "kind": "cartesian_graph",
        "theme": theme,
        "title": title or f"Horizontal Corridor (y = {y_val:g})",
        "xRange": [math.floor(x_min), math.ceil(x_max)],
        "yRange": [math.floor(y_min), math.ceil(y_max)],
        "grid": True,
        "axes": True,
        "plots": [
            {
                "type": "segment",
                "from": [x_min, y_val],
                "to": [x_max, y_val],
                "strokeDasharray": "4 4",
                "color": "#94a3b8",
            },
            {
                "type": "segment",
                "from": [x1, y_val],
                "to": [x2, y_val],
                "color": "#4f46e5",
            },
            {
                "type": "point",
                "coord": [x1, y_val],
                "label": f"({x1:g}, {y_val:g})",
                "position": "top",
            },
            {
                "type": "point",
                "coord": [x2, y_val],
                "label": f"({x2:g}, {y_val:g})",
                "position": "top",
            },
        ],
    }


def build_cartesian_parallel_lines_figure(
    m: float,
    c1: float,
    c2: float,
    x_range: Tuple[float, float] = (-4, 4),
    y_range: Tuple[float, float] = (-6, 12),
    theme: str = "blue",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a Cartesian graph showing two parallel lines sharing the same slope."""
    return {
        "kind": "cartesian_graph",
        "theme": theme,
        "title": title or f"Parallel Lines (m = {m:g})",
        "xRange": list(x_range),
        "yRange": list(y_range),
        "grid": True,
        "axes": True,
        "plots": [
            {
                "type": "function",
                "coefficients": [m, c1],
                "expression": f"L_1: y = {m:g}x + {c1:g}",
                "color": "#2563eb",
            },
            {
                "type": "function",
                "coefficients": [m, c2],
                "expression": f"L_2: y = {m:g}x - {abs(c2):g}" if c2 < 0 else f"L_2: y = {m:g}x + {c2:g}",
                "color": "#0284c7",
                "strokeDasharray": "4 3",
            },
            {
                "type": "point",
                "coord": [0, c1],
                "label": f"(0, {c1:g})",
                "position": "left",
            },
        ],
    }


def calculate_smart_step(min_val: float, max_val: float, target_ticks: int = 6) -> float:
    """Calculates a human-friendly 'nice' step size (1, 2, 5, 10 rule) to avoid overcrowded ticks."""
    span = max(max_val - min_val, 1e-4)
    raw_step = span / target_ticks
    power = 10 ** math.floor(math.log10(raw_step))
    norm = raw_step / power
    if norm < 1.6:
        mult = 1
    elif norm < 3.5:
        mult = 2
    elif norm < 7.5:
        mult = 5
    else:
        mult = 10
    step = mult * power
    if span >= 6 and step < 1:
        step = 1
    return round(step, 4)


def build_cartesian_rectangle_figure(
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    theme: str = "emerald",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a Cartesian graph showing a rectangle aligned with coordinate bounds."""
    x_min = min(0, x1) - 3
    x_max = x2 + 5
    y_min = min(0, y1) - 3
    y_max = y2 + 5
    x_step = calculate_smart_step(x_min, x_max, 6)
    y_step = calculate_smart_step(y_min, y_max, 6)

    return {
        "kind": "cartesian_graph",
        "theme": theme,
        "title": title or "Solar Array Coordinate Boundary",
        "xRange": [math.floor(x_min), math.ceil(x_max)],
        "yRange": [math.floor(y_min), math.ceil(y_max)],
        "xStep": x_step,
        "yStep": y_step,
        "grid": True,
        "axes": True,
        "plots": [
            # 4 sides of rectangle
            {"type": "segment", "from": [x1, y1], "to": [x2, y1], "color": "#059669"},
            {"type": "segment", "from": [x2, y1], "to": [x2, y2], "color": "#059669"},
            {"type": "segment", "from": [x2, y2], "to": [x1, y2], "color": "#059669"},
            {"type": "segment", "from": [x1, y2], "to": [x1, y1], "color": "#059669"},
            # Vertices
            {"type": "point", "coord": [x1, y1], "label": f"({x1:g}, {y1:g})", "position": "bottom-left"},
            {"type": "point", "coord": [x2, y2], "label": f"({x2:g}, {y2:g})", "position": "top-right"},
        ],
    }


# ==============================================================================
# STANDALONE SVG EXPORTER (HEADLESS / NOTION READY) - lives in math_engine.figure_svg
# ==============================================================================


def figure_to_svg(figure: Dict[str, Any], width: int = 420, height: int = 280) -> str:
    """Self-contained SVG for any MathFigure spec (Notion pages, files). See `math_engine.figure_svg`."""
    from math_engine.figure_svg import figure_to_svg as _render

    return _render(figure, width, height)


def build_cone_figure(
    radius: float,
    height: float,
    theme: str = "amber",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a semantic MathFigure for a right circular cone (radius r, vertical height h)."""
    ry = radius * 0.3
    pts = {
        "C_BOT": [0, 0],
        "L_BOT": [-radius, 0],
        "R_BOT": [radius, 0],
        "APEX": [0, height],
    }
    shapes = [
        {"type": "segment", "from": "L_BOT", "to": "APEX"},
        {"type": "segment", "from": "R_BOT", "to": "APEX"},
        {"type": "ellipse", "center": "C_BOT", "radiusX": radius, "radiusY": ry, "fill": True},
        {"type": "segment", "from": "C_BOT", "to": "APEX", "strokeDasharray": "3 3"},
        {"type": "segment", "from": "C_BOT", "to": "R_BOT", "strokeDasharray": "2 2"},
    ]
    labels = [
        {"type": "segment", "p1": "C_BOT", "p2": "APEX", "text": f"h = {height:g}", "side": "left"},
        {"type": "segment", "p1": "C_BOT", "p2": "R_BOT", "text": f"r = {radius:g}", "side": "bottom"},
    ]
    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Cone",
        "points": pts,
        "shapes": shapes,
        "labels": labels,
    }


def build_angle_pair_figure(
    total: float,
    known: float,
    label_known: Optional[str] = None,
    label_unknown: str = "?",
    theme: str = "rose",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Two adjacent angles sharing a vertex whose sum is `total` (90 = complementary, 180 = supplementary)."""
    r = 4.0

    def pt(deg: float) -> List[float]:
        return [round(r * math.cos(math.radians(deg)), 3), round(r * math.sin(math.radians(deg)), 3)]

    pts = {"O": [0, 0], "R": pt(0), "U": pt(known), "S": pt(total)}
    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or ("Complementary Angles" if abs(total - 90) < 1e-9 else "Adjacent Angles"),
        "points": pts,
        "shapes": [
            {"type": "segment", "from": "O", "to": "R"},
            {"type": "segment", "from": "O", "to": "U"},
            {"type": "segment", "from": "O", "to": "S"},
        ],
        "markers": [
            {
                "type": "angle_arc",
                "vertex": "O",
                "arm1": "R",
                "arm2": "U",
                "label": label_known or f"{known:g}^\\circ",
                "radius": 30,
            },
            {"type": "angle_arc", "vertex": "O", "arm1": "U", "arm2": "S", "label": label_unknown, "radius": 44},
        ],
    }


def build_triangle_angles_figure(
    angle_a: float,
    angle_b: float,
    theme: str = "indigo",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Triangle with two known base angles and an unknown third angle at the apex."""
    c = 180.0 - angle_a - angle_b
    base = 8.0
    side_ac = base * math.sin(math.radians(angle_b)) / math.sin(math.radians(c))
    pts = {
        "A": [0, 0],
        "B": [base, 0],
        "C": [round(side_ac * math.cos(math.radians(angle_a)), 3), round(side_ac * math.sin(math.radians(angle_a)), 3)],
    }
    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Triangle Angles",
        "points": pts,
        "shapes": [{"type": "polygon", "vertices": ["A", "B", "C"], "fill": True}],
        "markers": [
            {
                "type": "angle_arc",
                "vertex": "A",
                "arm1": "B",
                "arm2": "C",
                "label": f"{angle_a:g}^\\circ",
                "radius": 26,
            },
            {
                "type": "angle_arc",
                "vertex": "B",
                "arm1": "C",
                "arm2": "A",
                "label": f"{angle_b:g}^\\circ",
                "radius": 26,
            },
            {"type": "angle_arc", "vertex": "C", "arm1": "A", "arm2": "B", "label": "?", "radius": 24},
        ],
    }


def build_gable_facade_figure(
    width: float,
    rect_height: float,
    tri_height: float,
    theme: str = "emerald",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Composite facade: a rectangle topped by an isosceles triangular gable of the same width."""
    pts = {
        "BL": [0, 0],
        "BR": [width, 0],
        "TR": [width, rect_height],
        "TL": [0, rect_height],
        "PK": [width / 2, rect_height + tri_height],
        "MID": [width / 2, rect_height],
    }
    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Gable Facade",
        "points": pts,
        "shapes": [
            {"type": "polygon", "vertices": ["BL", "BR", "TR", "PK", "TL"], "fill": True},
            {"type": "segment", "from": "TL", "to": "TR", "strokeDasharray": "3 3"},
            {"type": "segment", "from": "MID", "to": "PK", "strokeDasharray": "2 2"},
        ],
        "labels": [
            {"type": "segment", "p1": "BL", "p2": "BR", "text": f"{width:g}", "side": "bottom"},
            {"type": "segment", "p1": "BR", "p2": "TR", "text": f"{rect_height:g}", "side": "right"},
            {"type": "segment", "p1": "MID", "p2": "PK", "text": f"{tri_height:g}", "side": "right"},
        ],
    }


# ==============================================================================
# FUNCTION GRAPHS, NUMBER LINES, COMPLEX PLANE (T02 onwards)
# ==============================================================================


def _split(text: str, sep: str = ",") -> List[str]:
    return [t.strip() for t in str(text or "").split(sep) if t.strip()]


def _nice_range(lo: float, hi: float, include_zero: bool = True) -> Tuple[float, float]:
    if include_zero:
        lo, hi = min(lo, 0.0), max(hi, 0.0)
    span = max(hi - lo, 1.0)
    lo, hi = lo - 0.12 * span, hi + 0.12 * span
    step = calculate_smart_step(lo, hi, 6)
    return math.floor(lo / step) * step, math.ceil(hi / step) * step


def _pretty(expr: str) -> str:
    """`2*(x-1)**2 - 3` -> `2(x-1)^2 - 3` for a legend."""
    s = str(expr).replace("**", "^")
    s = re.sub(r"(\d)\s*\*\s*(\d)", r"\1\\cdot \2", s)
    s = re.sub(r"\bcbrt\(([^()]*)\)", r"\\sqrt[3]{\1}", s)
    s = re.sub(r"\bsqrt\(([^()]*)\)", r"\\sqrt{\1}", s)
    s = re.sub(r"\babs\(([^()]*)\)", r"|\1|", s)
    return s.replace("*", "")


def _sample(expr: str, x_min: float, x_max: float, n: int = 240) -> List[List[Tuple[float, float]]]:
    """Runs of (x, y) samples; a run breaks where the function is undefined, at a jump (piecewise) and across a
    vertical asymptote, so no false vertical stroke is drawn."""
    from math_engine.safe_expr import compile_expr, evaluate

    tree = compile_expr(expr)
    samples: List[Tuple[float, Optional[float]]] = []
    for i in range(n + 1):
        x = x_min + (x_max - x_min) * i / n
        try:
            samples.append((x, evaluate(tree, {"x": x})))
        except (ArithmeticError, ValueError, KeyError, TypeError):
            samples.append((x, None))
    steps = sorted(abs(b[1] - a[1]) for a, b in zip(samples, samples[1:]) if a[1] is not None and b[1] is not None)
    typical = steps[len(steps) // 2] if steps else 0.0
    runs: List[List[Tuple[float, float]]] = []
    cur: List[Tuple[float, float]] = []
    prev_step = 0.0
    for x, y in samples:
        if y is None:
            if cur:
                runs.append(cur)
            cur, prev_step = [], 0.0
            continue
        if cur:
            step = abs(y - cur[-1][1])
            if step > 8 * max(prev_step, typical) and step > 1e-9:
                runs.append(cur)
                cur, step = [], 0.0
            prev_step = step
        cur.append((round(x, 4), round(y, 4)))
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) > 1]


def _pairs(text: str) -> List[Tuple[float, float]]:
    """`"(1, 2); (3, -1)"` -> [(1, 2), (3, -1)]."""
    from math_engine.safe_expr import evaluate

    out = []
    for part in _split(text, ";"):
        inner = part.strip().strip("()")
        xs, ys = inner.split(",")
        out.append((evaluate(xs.strip()), evaluate(ys.strip())))
    return out


def build_function_graph_figure(
    expr: str = "",
    x_min: float = -5,
    x_max: float = 5,
    y_min: Optional[float] = None,
    y_max: Optional[float] = None,
    label: Optional[str] = None,
    expr2: Optional[str] = None,
    label2: Optional[str] = None,
    mark_x: str = "",
    mark_labels: str = "",
    mark_x2: str = "",
    mark_labels2: str = "",
    points: str = "",
    point_labels: str = "",
    open_points: str = "",
    vlines: str = "",
    hlines: str = "",
    theme: str = "indigo",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Graph of y = expr(x) (and optionally a second curve) for any function `math_engine.safe_expr` reads:
    polynomials, rational, radical, |x|, cbrt, exp/ln/log, sin/cos/tan, and piecewise rules
    (`2*(x-1)^2 - 3`, `1/(x-2)`, `cbrt(x)`, `x^2 if x < 0 else 2*x + 1`).

    - `mark_x` / `mark_x2`: comma-separated x values to mark on the first / second curve; `mark_labels` /
      `mark_labels2`: their labels separated by `|` (default `(x, y)`; write `?` for an asked-for coordinate).
    - `points`: free points `"(1, 2); (3, -1)"` (a relation given as ordered pairs needs no `expr`), labelled by
      `point_labels` (`|`-separated, default none); `open_points`: hollow dots, e.g. the open end of a piece.
    - `vlines` / `hlines`: comma-separated x / y values drawn as dashed lines (asymptotes, line tests).
    The y-range is fitted to the curves and points when not given.
    """
    from math_engine.safe_expr import evaluate

    exprs = [(e, lbl or f"y = {_pretty(e)}") for e, lbl in ((expr, label), (expr2, label2)) if e]
    palette = [FIGURE_THEMES.get(theme, FIGURE_THEMES["indigo"])["stroke"], "#e11d48"]
    curves = [(i, run) for i, (e, _) in enumerate(exprs) for run in _sample(e, x_min, x_max)]
    free, hollow = _pairs(points), _pairs(open_points)
    if exprs and not curves:
        raise ValueError(f"nothing to plot for {expr!r} on [{x_min}, {x_max}]")
    if not exprs and not free:
        raise ValueError("give an expr or points to plot")
    if y_min is None or y_max is None:
        ys = sorted([y for _, run in curves for _, y in run])
        lo, hi = (ys[int(0.03 * (len(ys) - 1))], ys[int(0.97 * (len(ys) - 1))]) if ys else (0.0, 0.0)
        extra = [y for _, y in free + hollow] + [float(v) for v in _split(hlines)]
        fit = _nice_range(min([lo, *extra]), max([hi, *extra]))
        y_min = fit[0] if y_min is None else y_min
        y_max = fit[1] if y_max is None else y_max
    plots: List[Dict[str, Any]] = []
    for x in [float(v) for v in _split(vlines)]:
        plots.append(
            {"type": "segment", "from": [x, y_min], "to": [x, y_max], "color": "#94a3b8", "strokeDasharray": "5 4"}
        )
    for y in [float(v) for v in _split(hlines)]:
        plots.append(
            {"type": "segment", "from": [x_min, y], "to": [x_max, y], "color": "#94a3b8", "strokeDasharray": "5 4"}
        )
    for i, run in curves:
        plots.append({"type": "curve", "points": [list(p) for p in run], "color": palette[i % 2], "strokeWidth": 2.5})
    for idx, (marks, mark_lbls) in enumerate(((mark_x, mark_labels), (mark_x2, mark_labels2))):
        if not marks:
            continue
        if idx >= len(exprs):
            raise ValueError("mark_x2 needs expr2")
        lbls = _split(mark_lbls, "|")
        for k, xs in enumerate(_split(marks)):
            x = float(xs)
            y = evaluate(exprs[idx][0], {"x": x})
            plots.append(
                {
                    "type": "point",
                    "coord": [round(x, 4), round(y, 4)],
                    "label": lbls[k] if k < len(lbls) else f"({x:g}, {y:g})",
                    "position": "top-right",
                    "color": palette[idx],
                }
            )
    plabels = _split(point_labels, "|")
    for k, (x, y) in enumerate(free):
        pt: Dict[str, Any] = {"type": "point", "coord": [x, y], "position": "top-right"}
        if k < len(plabels):
            pt["label"] = plabels[k]
        plots.append(pt)
    for x, y in hollow:
        plots.append({"type": "point", "coord": [x, y], "hollow": True, "color": palette[0]})
    legend_y = y_max - 0.08 * (y_max - y_min)
    for i, (_, text) in enumerate(exprs):
        plots.append(
            {
                "type": "text",
                "coord": [x_min + 0.22 * (x_max - x_min), legend_y - i * 0.1 * (y_max - y_min)],
                "text": text,
                "color": palette[i % 2],
            }
        )
    return {
        "kind": "cartesian_graph",
        "theme": theme,
        "title": title or "Graph",
        "xRange": [x_min, x_max],
        "yRange": [y_min, y_max],
        "grid": True,
        "axes": True,
        "plots": plots,
    }


def build_mapping_diagram_figure(
    domain: str,
    range_values: str,
    pairs: str,
    domain_label: str = "Domain",
    range_label: str = "Range",
    theme: str = "indigo",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Arrow (mapping) diagram of a relation: two ovals of elements and an arrow per pair.

    `domain` / `range_values`: comma-separated elements in display order (`"1, 2, 3"`, `"a, b"`);
    `pairs`: `"1->a; 2->b; 3->b"`. Shows at a glance whether an input has two outputs (not a function) or two
    inputs share an output (not one-to-one)."""
    left, right = _split(domain), _split(range_values)
    links = [tuple(t.strip() for t in p.split("->")) for p in _split(pairs, ";")]
    for a, b in links:
        if a not in left or b not in right:
            raise ValueError(f"pair {a}->{b} uses an element not listed in domain/range")
    rows = max(len(left), len(right), 1)
    gap, xl, xr = 1.6, 0.0, 6.0

    def ys(n: int) -> List[float]:
        return [(n - 1) * gap / 2 - k * gap for k in range(n)]

    pts: Dict[str, List[float]] = {}
    labels: List[Dict[str, Any]] = []
    for side, items, x, pos in (("L", left, xl, "left"), ("R", right, xr, "right")):
        for k, (item, y) in enumerate(zip(items, ys(len(items)))):
            pts[f"{side}{k}"] = [x, y]
            labels.append({"type": "point", "point": f"{side}{k}", "text": item, "position": pos})
    half = (rows - 1) * gap / 2 + 1.1
    pts["CL"], pts["CR"] = [xl, 0.0], [xr, 0.0]
    shapes: List[Dict[str, Any]] = [
        {"type": "ellipse", "center": "CL", "radiusX": 1.3, "radiusY": half, "fill": True},
        {"type": "ellipse", "center": "CR", "radiusX": 1.3, "radiusY": half, "fill": True},
    ]
    hidden = ["CL", "CR"]
    for n, (a, b) in enumerate(links):
        pa, pb = pts[f"L{left.index(a)}"], pts[f"R{right.index(b)}"]
        dx, dy = pb[0] - pa[0], pb[1] - pa[1]
        pts[f"A{n}"] = [pa[0] + 0.12 * dx, pa[1] + 0.12 * dy]
        pts[f"B{n}"] = [pa[0] + 0.88 * dx, pa[1] + 0.88 * dy]
        hidden += [f"A{n}", f"B{n}"]
        shapes.append({"type": "segment", "from": f"A{n}", "to": f"B{n}", "arrow": True, "strokeWidth": 1.8})
    top = half + 0.5
    pts["TL"], pts["TR"] = [xl, top + 0.3], [xr, top + 0.3]  # keep the headings inside the drawing
    hidden += ["TL", "TR"]
    labels += [
        {"type": "free", "coord": [xl, top], "text": domain_label},
        {"type": "free", "coord": [xr, top], "text": range_label},
    ]
    return {
        "kind": "geometry_2d",
        "theme": theme,
        "title": title or "Mapping Diagram",
        "points": pts,
        "hideDots": hidden,
        "shapes": shapes,
        "labels": labels,
    }


_INTERVAL = re.compile(r"^\s*([\[(])\s*([^,]+?)\s*,\s*([^\])]+?)\s*([\])])\s*$")


def _bound(text: str) -> float:
    t = text.replace("∞", "inf").replace(" ", "").lower()
    if t in ("inf", "+inf", "infinity"):
        return math.inf
    if t in ("-inf", "-infinity"):
        return -math.inf
    from math_engine.safe_expr import evaluate

    return evaluate(t)


def build_number_line_figure(
    intervals: str = "",
    points: str = "",
    x_min: Optional[float] = None,
    x_max: Optional[float] = None,
    theme: str = "indigo",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """A number line with intervals in interval notation, joined by `U`: `"(-inf, -2] U (3, inf)"`.
    A closed end is a filled dot, an open end a hollow dot, an infinite end runs off the line with an arrow.
    `points` = comma-separated single values to mark (e.g. critical values)."""
    parsed = []
    for part in [p for p in re.split(r"\s*(?:U|∪)\s*", intervals or "") if p.strip()]:
        m = _INTERVAL.match(part)
        if not m:
            raise ValueError(f"not an interval: {part!r} (write e.g. '[-2, 3)' or '(-inf, 1]')")
        parsed.append((m.group(1) == "[", _bound(m.group(2)), _bound(m.group(3)), m.group(4) == "]"))
    singles = [_bound(p) for p in _split(points)]
    finite = [v for _, a, b, _ in parsed for v in (a, b) if math.isfinite(v)] + singles or [0.0]
    lo, hi = min(finite), max(finite)
    span = max(hi - lo, 4.0)
    x_min = math.floor(lo - 0.3 * span) if x_min is None else x_min
    x_max = math.ceil(hi + 0.3 * span) if x_max is None else x_max
    color = FIGURE_THEMES.get(theme, FIGURE_THEMES["indigo"])["stroke"]
    plots: List[Dict[str, Any]] = []
    for closed_l, a, b, closed_r in parsed:
        left, right = max(a, x_min), min(b, x_max)
        plots.append(
            {
                "type": "segment",
                "from": [left, 0],
                "to": [right, 0],
                "color": color,
                "strokeWidth": 5,
                "arrow": math.isinf(b),
            }
        )
        if math.isinf(a):
            plots.append(
                {
                    "type": "segment",
                    "from": [right, 0],
                    "to": [left, 0],
                    "color": color,
                    "strokeWidth": 5,
                    "arrow": True,
                }
            )
        for v, closed in ((a, closed_l), (b, closed_r)):
            if math.isfinite(v):
                plots.append({"type": "point", "coord": [v, 0], "hollow": not closed, "color": color})
    for v in singles:
        plots.append({"type": "point", "coord": [v, 0], "color": color})
    step = 1 if x_max - x_min <= 14 else calculate_smart_step(x_min, x_max, 8)
    return {
        "kind": "cartesian_graph",
        "theme": theme,
        "title": title or "Number Line",
        "xRange": [x_min, x_max],
        "yRange": [-1, 1],
        "xStep": step,
        "grid": False,
        "axes": True,
        "yAxis": False,
        "axisLabels": ["x", ""],
        "plots": plots,
    }


def build_complex_plane_figure(
    re1: float,
    im1: float,
    label1: str = "z",
    re2: Optional[float] = None,
    im2: Optional[float] = None,
    label2: str = "w",
    show_conjugate: bool = False,
    show_modulus: bool = False,
    label_modulus: Optional[str] = None,
    theme: str = "purple",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Argand diagram: each number as a point and an arrow from 0. `show_conjugate` adds the reflection
    in the real axis; `show_modulus` labels the arrow's length (`label_modulus`, e.g. `|z| = ?`)."""
    pts = [(re1, im1, label1, FIGURE_THEMES.get(theme, FIGURE_THEMES["purple"])["stroke"])]
    if re2 is not None and im2 is not None:
        pts.append((re2, im2, label2, "#0284c7"))
    if show_conjugate:
        pts.append((re1, -im1, f"\\bar{{{label1}}}", "#94a3b8"))
    m = max([abs(v) for x, y, _, _ in pts for v in (x, y)] + [1.0])
    step = calculate_smart_step(-m, m, 6)
    r = math.ceil(1.25 * m / step) * step
    plots: List[Dict[str, Any]] = []
    for x, y, lbl, col in pts:
        dashed = {"strokeDasharray": "4 3"} if col == "#94a3b8" else {}
        plots.append(
            {"type": "segment", "from": [0, 0], "to": [x, y], "color": col, "strokeWidth": 2.2, "arrow": True, **dashed}
        )
        pos = ("top" if y >= 0 else "bottom") + ("-right" if x >= 0 else "-left")
        plots.append({"type": "point", "coord": [x, y], "label": lbl, "position": pos, "color": col})
    if show_modulus:
        plots.append(
            {
                "type": "text",
                "coord": [re1 / 2 - 0.08 * r * (1 if im1 >= 0 else -1), im1 / 2 + 0.1 * r],
                "text": label_modulus or "|z|",
            }
        )
    return {
        "kind": "cartesian_graph",
        "theme": theme,
        "title": title or "Complex Plane",
        "xRange": [-r, r],
        "yRange": [-r, r],
        "grid": True,
        "axes": True,
        "axisLabels": ["Re", "Im"],
        "plots": plots,
    }
