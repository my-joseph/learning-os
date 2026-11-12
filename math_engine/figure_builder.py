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
from typing import Any, Dict, List, Optional, Tuple, Union

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
        plots.append({
            "type": "segment",
            "from": [px, 0],
            "to": [px, py],
            "strokeDasharray": "3 3",
            "color": "#94a3b8",
        })
        # Projection to Y axis
        plots.append({
            "type": "segment",
            "from": [0, py],
            "to": [px, py],
            "strokeDasharray": "3 3",
            "color": "#94a3b8",
        })

    # Plotted point
    plots.append({
        "type": "point",
        "coord": [px, py],
        "label": lbl,
        "position": "top-right" if py >= 0 else "bottom-right",
    })

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
            plots.append({
                "type": "point",
                "coord": [0, c],
                "label": f"(0, {c:g})",
                "position": "right",
            })
        # X-intercept: (-c / m, 0) if m != 0
        if abs(m) > 1e-6:
            x_int = -c / m
            if x_range[0] <= x_int <= x_range[1] and abs(x_int) > 1e-4:
                plots.append({
                    "type": "point",
                    "coord": [round(x_int, 2), 0],
                    "label": f"({round(x_int, 2):g}, 0)",
                    "position": "top",
                })

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
    markers = [
        {"type": "right_angle", "vertex": "H_BOT", "arm1": "B1", "arm2": "T1"}
    ]
    labels = [
        {"type": "segment", "p1": "T1", "p2": "T2", "text": label_top or f"{top_base:g}\\text{{ m}}", "side": "top"},
        {"type": "segment", "p1": "B1", "p2": "B2", "text": label_bottom or f"{bottom_base:g}\\text{{ m}}", "side": "bottom"},
        {"type": "segment", "p1": "B2", "p2": "T2", "text": label_side or f"{sloped_side:g}\\text{{ m}}", "side": "right"},
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
            {"type": "segment", "p1": "O", "p2": "P_IN", "text": label_inner or f"r = {r_inner:g}\\text{{ dm}}", "side": "bottom"},
            {"type": "segment", "p1": "P_IN", "p2": "P_OUT", "text": label_gap or f"{r_outer - r_inner:g}\\text{{ dm}}", "side": "top", "highlight": True},
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
        {"type": "segment", "from": "F1", "to": "B3", "strokeDasharray": "4 2", "strokeWidth": 2.5, "stroke": "#ea580c"},
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
# STANDALONE SVG EXPORTER (HEADLESS / NOTION READY)
# ==============================================================================

def figure_to_svg(figure: Dict[str, Any], width: int = 420, height: int = 280) -> str:
    """
    Renders any MathFigureSpec into a self-contained, standalone SVG string.
    Suitable for direct Notion /v1/file_uploads, embedding in HTML, or writing to .svg files.
    """
    kind = figure.get("kind")
    theme_key = figure.get("theme", "indigo")
    th = FIGURE_THEMES.get(theme_key, FIGURE_THEMES["indigo"])

    if kind == "geometry_2d":
        return _render_geometry_to_svg(figure, th, width, height)
    elif kind == "cartesian_graph":
        return _render_cartesian_to_svg(figure, th, width, height)
    else:
        # Fallback empty SVG
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"></svg>'


def _render_geometry_to_svg(fig: Dict[str, Any], th: Dict[str, str], svg_w: int, svg_h: int) -> str:
    padding = 45
    points = fig.get("points", {})
    raw_coords = list(points.values())

    if not raw_coords:
        raw_coords = [[0, 0], [10, 10]]

    xs = [p[0] for p in raw_coords]
    ys = [p[1] for p in raw_coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    world_w = max(max_x - min_x, 1e-4)
    world_h = max(max_y - min_y, 1e-4)
    avail_w = svg_w - padding * 2
    avail_h = svg_h - padding * 2

    scale = min(avail_w / world_w, avail_h / world_h)
    draw_w = world_w * scale
    draw_h = world_h * scale
    off_x = padding + (avail_w - draw_w) / 2
    off_y = padding + (avail_h - draw_h) / 2

    def to_svg(pt: List[float]) -> Tuple[float, float]:
        sx = off_x + (pt[0] - min_x) * scale
        sy = svg_h - (off_y + (pt[1] - min_y) * scale)
        return (round(sx, 1), round(sy, 1))

    svg_body: List[str] = []

    # Polygons
    for shape in fig.get("shapes", []):
        if shape.get("type") == "polygon":
            verts = [to_svg(points[v]) for v in shape.get("vertices", []) if v in points]
            if len(verts) >= 2:
                pts_str = " ".join(f"{x},{y}" for x, y in verts)
                fill = th["fill"] if shape.get("fill") else "none"
                svg_body.append(
                    f'<polygon points="{pts_str}" fill="{fill}" stroke="{th["stroke"]}" stroke-width="2.5" stroke-linejoin="round" />'
                )
        elif shape.get("type") == "circle":
            c_name = shape.get("center")
            if c_name in points:
                cx, cy = to_svg(points[c_name])
                r_svg = shape.get("radius", 1) * scale
                fill = th["fill"] if shape.get("fill") else "none"
                svg_body.append(
                    f'<circle cx="{cx}" cy="{cy}" r="{r_svg:.1f}" fill="{fill}" stroke="{th["stroke"]}" stroke-width="2" />'
                )

    # Markers (Right angle)
    for marker in fig.get("markers", []):
        if marker.get("type") == "right_angle":
            v_name = marker.get("vertex")
            a_name = marker.get("arm1")
            b_name = marker.get("arm2")
            if v_name in points and a_name in points and b_name in points:
                vx, vy = to_svg(points[v_name])
                ax, ay = to_svg(points[a_name])
                bx, by = to_svg(points[b_name])
                v1 = (ax - vx, ay - vy)
                v2 = (bx - vx, by - vy)
                l1 = math.hypot(v1[0], v1[1]) or 1
                l2 = math.hypot(v2[0], v2[1]) or 1
                u1 = (v1[0] / l1, v1[1] / l1)
                u2 = (v2[0] / l2, v2[1] / l2)
                s = 14.0
                p1 = (vx + u1[0] * s, vy + u1[1] * s)
                cor = (vx + (u1[0] + u2[0]) * s, vy + (u1[1] + u2[1]) * s)
                p2 = (vx + u2[0] * s, vy + u2[1] * s)
                svg_body.append(
                    f'<polyline points="{p1[0]:.1f},{p1[1]:.1f} {cor[0]:.1f},{cor[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="none" stroke="{th["stroke"]}" stroke-width="1.6" />'
                )

    # Point dots
    for p_name, pt in points.items():
        sx, sy = to_svg(pt)
        svg_body.append(f'<circle cx="{sx}" cy="{sy}" r="3.5" fill="#1e293b" stroke="#ffffff" stroke-width="1.5" />')

    # Dimension labels
    for lbl in fig.get("labels", []):
        if lbl.get("type") == "segment":
            p1_name, p2_name = lbl.get("p1"), lbl.get("p2")
            if p1_name in points and p2_name in points:
                x1, y1 = to_svg(points[p1_name])
                x2, y2 = to_svg(points[p2_name])
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2
                dx = x2 - x1
                dy = y2 - y1
                dist = math.hypot(dx, dy) or 1
                nx = -dy / dist
                ny = dx / dist
                off = lbl.get("offset", 16)
                side = lbl.get("side", "auto")
                if side == "bottom":
                    my += off
                elif side == "top":
                    my -= off
                elif side == "left":
                    mx -= off
                elif side == "right":
                    mx += off
                else:
                    mx += nx * off
                    my += ny * off

                txt = lbl.get("text", "")
                svg_body.append(
                    f'<text x="{mx:.1f}" y="{my:.1f}" text-anchor="middle" dominant-baseline="central" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="600" fill="#1e293b">{txt}</text>'
                )

    inner = "\n  ".join(svg_body)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%">
  <rect width="100%" height="100%" fill="#f8fafc" rx="16" />
  {inner}
</svg>"""


def _render_cartesian_to_svg(fig: Dict[str, Any], th: Dict[str, str], svg_w: int, svg_h: int) -> str:
    padding = 38
    x_min, x_max = fig.get("xRange", [-5, 5])
    y_min, y_max = fig.get("yRange", [-5, 5])

    w_world = max(x_max - x_min, 1e-4)
    h_world = max(y_max - y_min, 1e-4)
    draw_w = svg_w - padding * 2
    draw_h = svg_h - padding * 2

    def to_svg_x(xw: float) -> float:
        return padding + ((xw - x_min) / w_world) * draw_w

    def to_svg_y(yw: float) -> float:
        return svg_h - padding - ((yw - y_min) / h_world) * draw_h

    ox = to_svg_x(0)
    oy = to_svg_y(0)

    x_step = fig.get("xStep") or calculate_smart_step(x_min, x_max, 6)
    y_step = fig.get("yStep") or calculate_smart_step(y_min, y_max, 6)

    svg_body: List[str] = []

    # Grid
    cur_x = math.ceil(x_min / x_step) * x_step
    while cur_x <= x_max:
        if abs(cur_x) > 1e-6:
            sx = to_svg_x(cur_x)
            svg_body.append(f'<line x1="{sx:.1f}" y1="{padding}" x2="{sx:.1f}" y2="{svg_h - padding}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="2 2" />')
        cur_x += x_step

    cur_y = math.ceil(y_min / y_step) * y_step
    while cur_y <= y_max:
        if abs(cur_y) > 1e-6:
            sy = to_svg_y(cur_y)
            svg_body.append(f'<line x1="{padding}" y1="{sy:.1f}" x2="{svg_w - padding}" y2="{sy:.1f}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="2 2" />')
        cur_y += y_step

    # Axes
    clamp_oy = max(padding, min(svg_h - padding, oy))
    clamp_ox = max(padding, min(svg_w - padding, ox))
    svg_body.append(f'<line x1="{padding - 10}" y1="{clamp_oy:.1f}" x2="{svg_w - padding + 12}" y2="{clamp_oy:.1f}" stroke="#64748b" stroke-width="2" />')
    svg_body.append(f'<line x1="{clamp_ox:.1f}" y1="{svg_h - padding + 10}" x2="{clamp_ox:.1f}" y2="{padding - 12}" stroke="#64748b" stroke-width="2" />')

    # Ticks on axes
    cur_x = math.ceil(x_min / x_step) * x_step
    while cur_x <= x_max:
        if abs(cur_x) > 1e-6:
            sx = to_svg_x(cur_x)
            svg_body.append(f'<line x1="{sx:.1f}" y1="{clamp_oy - 3}" x2="{sx:.1f}" y2="{clamp_oy + 3}" stroke="#64748b" stroke-width="1.2" />')
            svg_body.append(f'<text x="{sx:.1f}" y="{clamp_oy + 13}" font-family="monospace" font-size="9" text-anchor="middle" fill="#64748b">{cur_x:g}</text>')
        cur_x += x_step

    cur_y = math.ceil(y_min / y_step) * y_step
    while cur_y <= y_max:
        if abs(cur_y) > 1e-6:
            sy = to_svg_y(cur_y)
            svg_body.append(f'<line x1="{clamp_ox - 3}" y1="{sy:.1f}" x2="{clamp_ox + 3}" y2="{sy:.1f}" stroke="#64748b" stroke-width="1.2" />')
            svg_body.append(f'<text x="{clamp_ox - 5}" y="{sy + 3:.1f}" font-family="monospace" font-size="9" text-anchor="end" fill="#64748b">{cur_y:g}</text>')
        cur_y += y_step

    # Plots
    for plot in fig.get("plots", []):
        p_type = plot.get("type")
        if p_type == "point":
            px, py = plot.get("coord", [0, 0])
            sx = to_svg_x(px)
            sy = to_svg_y(py)
            col = plot.get("color") or th["stroke"]
            svg_body.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="4.5" fill="{col}" stroke="#ffffff" stroke-width="1.5" />')
            if plot.get("label"):
                lbl = plot["label"]
                svg_body.append(f'<text x="{sx + 8:.1f}" y="{sy - 8:.1f}" font-family="monospace" font-size="11" font-weight="bold" fill="#1e293b">{lbl}</text>')
        elif p_type == "segment":
            x1, y1 = plot.get("from", [0, 0])
            x2, y2 = plot.get("to", [0, 0])
            col = plot.get("color") or "#94a3b8"
            dash = f'stroke-dasharray="{plot["strokeDasharray"]}"' if plot.get("strokeDasharray") else ""
            svg_body.append(f'<line x1="{to_svg_x(x1):.1f}" y1="{to_svg_y(y1):.1f}" x2="{to_svg_x(x2):.1f}" y2="{to_svg_y(y2):.1f}" stroke="{col}" stroke-width="1.8" {dash} />')
        elif p_type == "function":
            coeffs = plot.get("coefficients", [])
            if coeffs:
                steps = 60
                dx = (x_max - x_min) / steps
                pts: List[str] = []
                for i in range(steps + 1):
                    cur_x = x_min + i * dx
                    cur_y = 0.0
                    for c in coeffs:
                        cur_y = cur_y * cur_x + c
                    sx = to_svg_x(cur_x)
                    sy = to_svg_y(cur_y)
                    pts.append(f"{sx:.1f},{sy:.1f}")
                pts_str = " ".join(pts)
                col = plot.get("color") or th["stroke"]
                svg_body.append(f'<polyline points="{pts_str}" fill="none" stroke="{col}" stroke-width="2.5" />')

    inner = "\n  ".join(svg_body)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%">
  <rect width="100%" height="100%" fill="#f8fafc" rx="16" />
  {inner}
</svg>"""
