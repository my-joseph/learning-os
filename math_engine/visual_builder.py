# -*- coding: utf-8 -*-
"""
Visual Spec Builder & SVG Converter for Math Practice Drills.
Adheres to rules/03_stem.md Part 2: Parametric Educational Diagrams.

Supports:
- 2D Geometry: Rectangles, Triangles (Right, Isosceles), Trapezoids, Circles, Annulus, Angles (Complementary, Supplementary, Transversal)
- 3D Solids: Cylinders, Boxes, Composite Silos (Cylinder + Cone)
- Coordinate Plane: Axes, Grid, Points, Linear Lines, Slope Triangles, Intercepts, Regions
- SVG Converter: Converts any declarative VisualSpec into a standalone crisp SVG vector graphic.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

THEMES = {
    "blue": {
        "primary": "#2563eb",
        "stroke": "#3b82f6",
        "fill": "rgba(59, 130, 246, 0.08)",
        "accent": "#0284c7",
        "text": "#1e293b",
        "grid": "#e2e8f0",
        "axis": "#64748b",
    },
    "emerald": {
        "primary": "#059669",
        "stroke": "#10b981",
        "fill": "rgba(16, 185, 129, 0.08)",
        "accent": "#0d9488",
        "text": "#1e293b",
    },
    "indigo": {
        "primary": "#4f46e5",
        "stroke": "#6366f1",
        "fill": "rgba(99, 102, 241, 0.08)",
        "accent": "#4338ca",
        "text": "#1e293b",
    },
    "amber": {
        "primary": "#d97706",
        "stroke": "#f59e0b",
        "fill": "rgba(245, 158, 11, 0.08)",
        "accent": "#ea580c",
        "text": "#1e293b",
    },
    "purple": {
        "primary": "#7c3aed",
        "stroke": "#8b5cf6",
        "fill": "rgba(139, 92, 246, 0.08)",
        "accent": "#6d28d9",
        "text": "#1e293b",
    },
}


def build_rectangle_visual(
    width: float,
    height: float,
    label_w: Optional[str] = None,
    label_h: Optional[str] = None,
    theme: str = "indigo",
) -> Dict[str, Any]:
    """Generates VisualSpec for a 2D Rectangle."""
    th = THEMES.get(theme, THEMES["indigo"])
    vw, vh = 320, 190
    max_w, max_h = 220, 120
    scale = min(max_w / max(width, 1e-4), max_h / max(height, 1e-4))
    draw_w = width * scale
    draw_h = height * scale

    ox = (vw - draw_w) / 2
    oy = (vh + draw_h) / 2

    p_bl = [round(ox, 1), round(oy, 1)]
    p_br = [round(ox + draw_w, 1), round(oy, 1)]
    p_tr = [round(ox + draw_w, 1), round(oy - draw_h, 1)]
    p_tl = [round(ox, 1), round(oy - draw_h, 1)]

    lbl_w = label_w or f"w = {width:g}"
    lbl_h = label_h or f"h = {height:g}"

    return {
        "type": "geometry-2d",
        "viewBox": {"width": vw, "height": vh},
        "elements": [
            {
                "type": "polygon",
                "points": [p_bl, p_br, p_tr, p_tl],
                "stroke": th["stroke"],
                "fill": th["fill"],
                "strokeWidth": 2.5,
                "rightAngleAt": p_bl,
            },
            {
                "type": "dimension-label",
                "start": p_bl,
                "end": p_br,
                "label": lbl_w,
                "position": "bottom",
                "offset": 14,
            },
            {
                "type": "dimension-label",
                "start": p_tl,
                "end": p_bl,
                "label": lbl_h,
                "position": "left",
                "offset": 12,
            },
        ],
    }


def build_right_triangle_visual(
    base: float,
    height: float,
    hypot: Optional[float] = None,
    label_b: Optional[str] = None,
    label_h: Optional[str] = None,
    label_c: Optional[str] = None,
    theme: str = "emerald",
) -> Dict[str, Any]:
    """Generates VisualSpec for a Right Triangle."""
    th = THEMES.get(theme, THEMES["emerald"])
    vw, vh = 320, 190
    max_w, max_h = 220, 130
    scale = min(max_w / max(base, 1e-4), max_h / max(height, 1e-4))
    draw_w = base * scale
    draw_h = height * scale

    ox = 55
    oy = 160

    p_origin = [round(ox, 1), round(oy, 1)]
    p_far = [round(ox + draw_w, 1), round(oy, 1)]
    p_top = [round(ox, 1), round(oy - draw_h, 1)]

    calc_hypot = hypot if hypot is not None else math.sqrt(base**2 + height**2)
    lbl_b = label_b or f"b = {base:g}"
    lbl_h = label_h or f"a = {height:g}"
    lbl_c = label_c or f"c = {calc_hypot:g}"

    return {
        "type": "geometry-2d",
        "viewBox": {"width": vw, "height": vh},
        "elements": [
            {
                "type": "polygon",
                "points": [p_origin, p_far, p_top],
                "stroke": th["stroke"],
                "fill": th["fill"],
                "strokeWidth": 2.5,
                "rightAngleAt": p_origin,
            },
            {
                "type": "dimension-label",
                "start": p_top,
                "end": p_origin,
                "label": lbl_h,
                "position": "left",
                "offset": 12,
            },
            {
                "type": "dimension-label",
                "start": p_origin,
                "end": p_far,
                "label": lbl_b,
                "position": "bottom",
                "offset": 14,
            },
            {
                "type": "dimension-label",
                "start": p_top,
                "end": p_far,
                "label": lbl_c,
                "position": "hypotenuse",
                "offset": 14,
                "highlight": True,
            },
        ],
        "interactive": {
            "mode": "pythagoras-drag",
            "initialParams": {"a": base, "b": height},
        },
    }


def build_isosceles_triangle_visual(
    base: float,
    height: float,
    apex_angle: Optional[float] = None,
    base_angle: Optional[float] = None,
    theme: str = "indigo",
) -> Dict[str, Any]:
    """Generates VisualSpec for an Isosceles Triangle with angle markers."""
    th = THEMES.get(theme, THEMES["indigo"])
    vw, vh = 320, 200
    ox, oy = 160, 160
    draw_w = 180
    draw_h = 110

    p_top = [ox, oy - draw_h]
    p_bl = [ox - draw_w / 2, oy]
    p_br = [ox + draw_w / 2, oy]

    elements = [
        {
            "type": "polygon",
            "points": [p_top, p_br, p_bl],
            "stroke": th["stroke"],
            "fill": th["fill"],
            "strokeWidth": 2.5,
        },
        {
            "type": "line",
            "points": [p_top, [ox, oy]],
            "stroke": "#94a3b8",
            "strokeWidth": 1.5,
            "strokeDasharray": "3 3",
        },
    ]

    if apex_angle is not None:
        elements.append({
            "type": "angle-arc",
            "center": p_top,
            "radius": 24,
            "startAngle": 245,
            "endAngle": 295,
            "label": f"{apex_angle:g}°",
        })

    if base_angle is not None:
        elements.append({
            "type": "angle-arc",
            "center": p_bl,
            "radius": 26,
            "startAngle": 0,
            "endAngle": 50,
            "label": f"{base_angle:g}°",
        })
        elements.append({
            "type": "angle-arc",
            "center": p_br,
            "radius": 26,
            "startAngle": 130,
            "endAngle": 180,
            "label": f"{base_angle:g}°",
        })

    return {
        "type": "geometry-2d",
        "viewBox": {"width": vw, "height": vh},
        "elements": elements,
    }


def build_trapezoid_visual(
    b1: float,
    b2: float,
    h: float,
    label_b1: Optional[str] = None,
    label_b2: Optional[str] = None,
    label_h: Optional[str] = None,
    theme: str = "indigo",
) -> Dict[str, Any]:
    """Generates VisualSpec for an Isosceles/Standard Trapezoid."""
    th = THEMES.get(theme, THEMES["indigo"])
    vw, vh = 320, 200
    max_b = max(b1, b2, 1e-4)
    scale = min(220 / max_b, 100 / max(h, 1e-4))

    w_bot = max(b1, b2) * scale
    w_top = min(b1, b2) * scale
    draw_h = h * scale

    ox = 160
    oy = 160

    p_bl = [ox - w_bot / 2, oy]
    p_br = [ox + w_bot / 2, oy]
    p_tr = [ox + w_top / 2, oy - draw_h]
    p_tl = [ox - w_top / 2, oy - draw_h]

    lbl_1 = label_b1 or f"b₁ = {b1:g}"
    lbl_2 = label_b2 or f"b₂ = {b2:g}"
    lbl_h = label_h or f"h = {h:g}"

    return {
        "type": "geometry-2d",
        "viewBox": {"width": vw, "height": vh},
        "elements": [
            {
                "type": "polygon",
                "points": [p_bl, p_br, p_tr, p_tl],
                "stroke": th["stroke"],
                "fill": th["fill"],
                "strokeWidth": 2.5,
            },
            {
                "type": "line",
                "points": [p_tl, [p_tl[0], oy]],
                "stroke": th["primary"],
                "strokeWidth": 2,
                "strokeDasharray": "3 3",
            },
            {
                "type": "dimension-label",
                "start": p_tl,
                "end": [p_tl[0], oy],
                "label": lbl_h,
                "position": "left",
                "offset": 10,
            },
            {
                "type": "dimension-label",
                "start": p_tl,
                "end": p_tr,
                "label": lbl_2,
                "position": "top",
                "offset": 12,
            },
            {
                "type": "dimension-label",
                "start": p_bl,
                "end": p_br,
                "label": lbl_1,
                "position": "bottom",
                "offset": 14,
            },
        ],
        "interactive": {
            "mode": "trapezoid-drag",
            "initialParams": {"b1": b2, "b2": b1, "h": h},
        },
    }


def build_circle_visual(
    radius: float,
    diameter: Optional[float] = None,
    show_diameter: bool = False,
    is_annulus: bool = False,
    inner_radius: Optional[float] = None,
    label_r: Optional[str] = None,
    label_d: Optional[str] = None,
    theme: str = "blue",
) -> Dict[str, Any]:
    """Generates VisualSpec for a Circle or Annulus."""
    th = THEMES.get(theme, THEMES["blue"])
    vw, vh = 320, 200
    cx, cy = 160, 100
    r_px = 65

    lbl_r = label_r or f"r = {radius:g}"
    lbl_d = label_d or (f"d = {diameter:g}" if diameter else f"d = {2*radius:g}")

    elements = [
        {
            "type": "circle",
            "center": [cx, cy],
            "radius": r_px,
            "stroke": th["stroke"],
            "fill": th["fill"],
            "strokeWidth": 2.5,
        },
        {
            "type": "point",
            "coord": [cx, cy],
            "label": "O",
            "color": "#1e293b",
        },
    ]

    if is_annulus and inner_radius:
        inner_r_px = max(20, int(r_px * (inner_radius / radius)))
        elements.append({
            "type": "circle",
            "center": [cx, cy],
            "radius": inner_r_px,
            "stroke": "#f59e0b",
            "fill": "#ffffff",
            "strokeWidth": 2,
        })
        elements.append({
            "type": "dimension-label",
            "start": [cx, cy],
            "end": [cx + inner_r_px, cy],
            "label": f"r_in = {inner_radius:g}",
            "position": "top",
            "offset": 8,
        })
        elements.append({
            "type": "dimension-label",
            "start": [cx, cy],
            "end": [cx, cy - r_px],
            "label": f"R = {radius:g}",
            "position": "left",
            "offset": 8,
        })
    elif show_diameter:
        elements.append({
            "type": "line",
            "points": [[cx - r_px, cy], [cx + r_px, cy]],
            "stroke": th["primary"],
            "strokeWidth": 2,
            "strokeDasharray": "3 3",
        })
        elements.append({
            "type": "dimension-label",
            "start": [cx - r_px, cy],
            "end": [cx + r_px, cy],
            "label": lbl_d,
            "position": "bottom",
            "offset": 12,
        })
    else:
        elements.append({
            "type": "line",
            "points": [[cx, cy], [cx + r_px, cy]],
            "stroke": th["primary"],
            "strokeWidth": 2.5,
        })
        elements.append({
            "type": "dimension-label",
            "start": [cx, cy],
            "end": [cx + r_px, cy],
            "label": lbl_r,
            "position": "top",
            "offset": 10,
        })

    return {
        "type": "geometry-2d",
        "viewBox": {"width": vw, "height": vh},
        "elements": elements,
        "interactive": {
            "mode": "circle-radius-drag",
            "initialParams": {"r": radius},
        },
    }


def build_cylinder_visual(
    radius: float,
    height: float,
    label_r: Optional[str] = None,
    label_h: Optional[str] = None,
    theme: str = "purple",
) -> Dict[str, Any]:
    """Generates VisualSpec for a 3D Cylinder."""
    th = THEMES.get(theme, THEMES["purple"])
    vw, vh = 320, 210
    cx, cy = 150, 105
    rx = 55
    ry = 18
    draw_h = 100
    top_y = cy - draw_h / 2
    bot_y = cy + draw_h / 2

    lbl_r = label_r or f"r = {radius:g}"
    lbl_h = label_h or f"h = {height:g}"

    return {
        "type": "geometry-3d-wireframe",
        "viewBox": {"width": vw, "height": vh},
        "elements": [
            {
                "type": "cylinder",
                "center": [cx, cy],
                "radiusX": rx,
                "radiusY": ry,
                "height": draw_h,
                "stroke": th["stroke"],
                "fill": th["fill"],
                "strokeWidth": 2.5,
            },
            {
                "type": "line",
                "points": [[cx, top_y], [cx + rx, top_y]],
                "stroke": th["primary"],
                "strokeWidth": 2,
            },
            {
                "type": "point",
                "coord": [cx, top_y],
                "color": "#1e293b",
            },
            {
                "type": "dimension-label",
                "start": [cx, top_y],
                "end": [cx + rx, top_y],
                "label": lbl_r,
                "position": "top",
                "offset": 8,
            },
            {
                "type": "dimension-label",
                "start": [cx + rx + 16, top_y],
                "end": [cx + rx + 16, bot_y],
                "label": lbl_h,
                "position": "right",
                "offset": 8,
            },
        ],
        "interactive": {
            "mode": "cylinder-slider",
            "initialParams": {"r": radius, "h": height},
        },
    }


def build_box3d_visual(
    length: float,
    width: float,
    height: float,
    label_l: Optional[str] = None,
    label_w: Optional[str] = None,
    label_h: Optional[str] = None,
    theme: str = "blue",
) -> Dict[str, Any]:
    """Generates VisualSpec for an Oblique 3D Box / Rectangular Prism."""
    th = THEMES.get(theme, THEMES["blue"])
    vw, vh = 320, 200
    ox, oy = 70, 160
    fw, fh = 140, 80  # front face
    dx, dy = 50, -35   # depth offset

    # Front face
    p0 = [ox, oy]
    p1 = [ox + fw, oy]
    p2 = [ox + fw, oy - fh]
    p3 = [ox, oy - fh]

    # Back face
    p4 = [ox + dx, oy + dy]
    p5 = [ox + fw + dx, oy + dy]
    p6 = [ox + fw + dx, oy - fh + dy]
    p7 = [ox + dx, oy - fh + dy]

    lbl_l = label_l or f"L = {length:g}"
    lbl_w = label_w or f"W = {width:g}"
    lbl_h = label_h or f"H = {height:g}"

    return {
        "type": "geometry-3d-wireframe",
        "viewBox": {"width": vw, "height": vh},
        "elements": [
            # Hidden / dashed edges
            {"type": "line", "points": [p0, p4], "stroke": "#94a3b8", "strokeWidth": 1.5, "strokeDasharray": "3 3"},
            {"type": "line", "points": [p4, p5], "stroke": "#94a3b8", "strokeWidth": 1.5, "strokeDasharray": "3 3"},
            {"type": "line", "points": [p4, p7], "stroke": "#94a3b8", "strokeWidth": 1.5, "strokeDasharray": "3 3"},
            # Top face
            {"type": "polygon", "points": [p3, p2, p6, p7], "stroke": th["stroke"], "fill": "rgba(59, 130, 246, 0.12)", "strokeWidth": 2},
            # Side face
            {"type": "polygon", "points": [p1, p5, p6, p2], "stroke": th["stroke"], "fill": "rgba(59, 130, 246, 0.06)", "strokeWidth": 2},
            # Front face
            {"type": "polygon", "points": [p0, p1, p2, p3], "stroke": th["stroke"], "fill": th["fill"], "strokeWidth": 2.5},
            # Dimension labels
            {"type": "dimension-label", "start": p0, "end": p1, "label": lbl_l, "position": "bottom", "offset": 14},
            {"type": "dimension-label", "start": p3, "end": p0, "label": lbl_h, "position": "left", "offset": 12},
            {"type": "dimension-label", "start": p1, "end": p5, "label": lbl_w, "position": "right", "offset": 12},
        ],
    }


def build_angles_visual(
    angle1: float,
    angle2: float,
    relation: str = "complementary",
    theme: str = "amber",
) -> Dict[str, Any]:
    """Generates VisualSpec for Angle Pairs (Complementary, Supplementary, Transversal)."""
    th = THEMES.get(theme, THEMES["amber"])
    vw, vh = 320, 200
    ox, oy = 110, 160
    r_ray = 130

    elements: List[Dict[str, Any]] = []

    if relation == "transversal":
        # Two horizontal parallel lines cut by diagonal transversal
        y1, y2 = 70, 140
        elements.extend([
            {"type": "line", "points": [[30, y1], [290, y1]], "stroke": "#475569", "strokeWidth": 2.5},
            {"type": "line", "points": [[30, y2], [290, y2]], "stroke": "#475569", "strokeWidth": 2.5},
            {"type": "line", "points": [[70, 180], [250, 30]], "stroke": th["primary"], "strokeWidth": 3},
            {"type": "angle-arc", "center": [130, y2], "radius": 24, "startAngle": 0, "endAngle": 40, "label": f"{angle1:g}°"},
            {"type": "angle-arc", "center": [190, y1], "radius": 24, "startAngle": 180, "endAngle": 220, "label": f"{angle2:g}°"},
            {"type": "text", "x": 280, "y": y1 - 8, "label": "L₁", "color": "#64748b"},
            {"type": "text", "x": 280, "y": y2 - 8, "label": "L₂", "color": "#64748b"},
        ])
    elif relation == "supplementary":
        # Straight line with dividing ray
        ox, oy = 160, 150
        rad1 = math.radians(angle1)
        ray_x = ox + r_ray * math.cos(rad1)
        ray_y = oy - r_ray * math.sin(rad1)

        elements.extend([
            {"type": "line", "points": [[40, oy], [280, oy]], "stroke": "#475569", "strokeWidth": 2.5},
            {"type": "line", "points": [[ox, oy], [round(ray_x, 1), round(ray_y, 1)]], "stroke": th["primary"], "strokeWidth": 3},
            {"type": "point", "coord": [ox, oy], "label": "O", "color": "#1e293b"},
            {"type": "angle-arc", "center": [ox, oy], "radius": 32, "startAngle": 0, "endAngle": angle1, "label": f"{angle1:g}°"},
            {"type": "angle-arc", "center": [ox, oy], "radius": 46, "startAngle": angle1, "endAngle": 180, "label": f"{angle2:g}°"},
        ])
    else:
        # Complementary (90 deg corner)
        rad1 = math.radians(angle1)
        ray_x = ox + r_ray * math.cos(rad1)
        ray_y = oy - r_ray * math.sin(rad1)

        elements.extend([
            {"type": "line", "points": [[ox, oy], [ox + r_ray, oy]], "stroke": "#475569", "strokeWidth": 2.5},
            {"type": "line", "points": [[ox, oy], [ox, oy - r_ray]], "stroke": "#475569", "strokeWidth": 2.5},
            {"type": "line", "points": [[ox, oy], [round(ray_x, 1), round(ray_y, 1)]], "stroke": th["primary"], "strokeWidth": 3},
            {"type": "polygon", "points": [[ox, oy], [ox + 18, oy], [ox + 18, oy - 18], [ox, oy - 18]], "stroke": "#94a3b8", "fill": "none", "strokeWidth": 1.5},
            {"type": "angle-arc", "center": [ox, oy], "radius": 35, "startAngle": 0, "endAngle": angle1, "label": f"{angle1:g}°"},
            {"type": "angle-arc", "center": [ox, oy], "radius": 52, "startAngle": angle1, "endAngle": 90, "label": f"{angle2:g}°"},
        ])

    return {
        "type": "geometry-2d",
        "viewBox": {"width": vw, "height": vh},
        "elements": elements,
    }


def build_coordinate_plane_visual(
    points: Optional[List[Tuple[float, float, str]]] = None,
    lines: Optional[List[Dict[str, Any]]] = None,
    rectangles: Optional[List[Dict[str, Any]]] = None,
    slope_triangles: Optional[List[Dict[str, Any]]] = None,
    x_bounds: Tuple[float, float] = (-2, 10),
    y_bounds: Tuple[float, float] = (-2, 10),
    title: Optional[str] = None,
    theme: str = "blue",
) -> Dict[str, Any]:
    """
    Generates a full Cartesian Coordinate Plane VisualSpec with axes, grid, points, and function lines.
    """
    th = THEMES.get(theme, THEMES["blue"])
    vw, vh = 340, 240
    pad_l, pad_r, pad_t, pad_b = 40, 30, 25, 35

    x_min, x_max = x_bounds
    y_min, y_max = y_bounds
    span_x = max(x_max - x_min, 1e-4)
    span_y = max(y_max - y_min, 1e-4)

    def to_svg(x: float, y: float) -> Tuple[float, float]:
        px = pad_l + (x - x_min) / span_x * (vw - pad_l - pad_r)
        py = vh - pad_b - (y - y_min) / span_y * (vh - pad_t - pad_b)
        return round(px, 1), round(py, 1)

    elements: List[Dict[str, Any]] = []

    # Grid lines
    step_x = 2 if span_x > 14 else 1 if span_x <= 8 else 2
    step_y = 2 if span_y > 14 else 1 if span_y <= 8 else 2

    cur_x = math.ceil(x_min / step_x) * step_x
    while cur_x <= x_max:
        p_bot = to_svg(cur_x, y_min)
        p_top = to_svg(cur_x, y_max)
        elements.append({
            "type": "line",
            "points": [list(p_bot), list(p_top)],
            "stroke": "#f1f5f9",
            "strokeWidth": 1,
        })
        cur_x += step_x

    cur_y = math.ceil(y_min / step_y) * step_y
    while cur_y <= y_max:
        p_left = to_svg(x_min, cur_y)
        p_right = to_svg(x_max, cur_y)
        elements.append({
            "type": "line",
            "points": [list(p_left), list(p_right)],
            "stroke": "#f1f5f9",
            "strokeWidth": 1,
        })
        cur_y += step_y

    # Axes
    ox_pt = to_svg(0, 0)
    # X-axis line (clipped to graph bounds or y=0)
    y_axis_pos = 0 if y_min <= 0 <= y_max else y_min
    x_axis_pos = 0 if x_min <= 0 <= x_max else x_min

    ax_x_start = to_svg(x_min, y_axis_pos)
    ax_x_end = to_svg(x_max, y_axis_pos)
    ax_y_start = to_svg(x_axis_pos, y_min)
    ax_y_end = to_svg(x_axis_pos, y_max)

    elements.append({
        "type": "line",
        "points": [list(ax_x_start), list(ax_x_end)],
        "stroke": "#64748b",
        "strokeWidth": 2,
    })
    elements.append({
        "type": "line",
        "points": [list(ax_y_start), list(ax_y_end)],
        "stroke": "#64748b",
        "strokeWidth": 2,
    })

    # Axis Labels
    elements.append({"type": "text", "x": ax_x_end[0] + 12, "y": ax_x_end[1] + 4, "label": "x", "color": "#334155", "fontSize": 13})
    elements.append({"type": "text", "x": ax_y_end[0] - 4, "y": ax_y_end[1] - 10, "label": "y", "color": "#334155", "fontSize": 13})
    elements.append({"type": "text", "x": ox_pt[0] - 10, "y": ox_pt[1] + 14, "label": "O", "color": "#94a3b8", "fontSize": 11})

    # Rectangles (e.g. for coordinate regions)
    if rectangles:
        for r in rectangles:
            bl = to_svg(r["x1"], r["y1"])
            br = to_svg(r["x2"], r["y1"])
            tr = to_svg(r["x2"], r["y2"])
            tl = to_svg(r["x1"], r["y2"])
            elements.append({
                "type": "polygon",
                "points": [list(bl), list(br), list(tr), list(tl)],
                "stroke": r.get("stroke", th["stroke"]),
                "fill": r.get("fill", th["fill"]),
                "strokeWidth": 2,
            })

    # Slope Triangles
    if slope_triangles:
        for st in slope_triangles:
            x1, y1 = st["p1"]
            x2, y2 = st["p2"]
            sp1 = to_svg(x1, y1)
            sp_corner = to_svg(x2, y1)
            sp2 = to_svg(x2, y2)
            elements.append({
                "type": "polygon",
                "points": [list(sp1), list(sp_corner), list(sp2)],
                "stroke": "#f59e0b",
                "fill": "rgba(245, 158, 11, 0.12)",
                "strokeWidth": 1.5,
                "strokeDasharray": "3 3",
            })
            elements.append({
                "type": "dimension-label",
                "start": list(sp1),
                "end": list(sp_corner),
                "label": f"Δx = {x2 - x1:g}",
                "position": "bottom",
                "offset": 10,
            })
            elements.append({
                "type": "dimension-label",
                "start": list(sp_corner),
                "end": list(sp2),
                "label": f"Δy = {y2 - y1:g}",
                "position": "right",
                "offset": 10,
            })

    # Lines
    if lines:
        for ln in lines:
            p_start = to_svg(ln["x1"], ln["y1"])
            p_end = to_svg(ln["x2"], ln["y2"])
            elements.append({
                "type": "line",
                "points": [list(p_start), list(p_end)],
                "stroke": ln.get("stroke", th["primary"]),
                "strokeWidth": ln.get("strokeWidth", 2.5),
                "strokeDasharray": ln.get("strokeDasharray"),
            })
            if ln.get("label"):
                mid_pt = to_svg((ln["x1"] + ln["x2"]) / 2, (ln["y1"] + ln["y2"]) / 2)
                elements.append({
                    "type": "text",
                    "x": mid_pt[0] + 8,
                    "y": mid_pt[1] - 8,
                    "label": ln["label"],
                    "color": ln.get("stroke", th["primary"]),
                    "fontSize": 12,
                })

    # Points
    if points:
        for pt in points:
            x_val, y_val, lbl = pt
            s_pt = to_svg(x_val, y_val)
            # Dashed guide lines to axes
            s_proj_x = to_svg(x_val, y_axis_pos)
            s_proj_y = to_svg(x_axis_pos, y_val)
            elements.append({
                "type": "line",
                "points": [list(s_pt), list(s_proj_x)],
                "stroke": "#cbd5e1",
                "strokeWidth": 1.2,
                "strokeDasharray": "2 2",
            })
            elements.append({
                "type": "line",
                "points": [list(s_pt), list(s_proj_y)],
                "stroke": "#cbd5e1",
                "strokeWidth": 1.2,
                "strokeDasharray": "2 2",
            })
            elements.append({
                "type": "point",
                "coord": list(s_pt),
                "label": lbl or f"({x_val:g}, {y_val:g})",
                "color": th["primary"],
            })

    if title:
        elements.append({
            "type": "text",
            "x": vw / 2,
            "y": 16,
            "label": title,
            "color": "#1e293b",
            "fontSize": 13,
        })

    return {
        "type": "coordinate-plane",
        "viewBox": {"width": vw, "height": vh},
        "elements": elements,
    }


def visual_to_svg(visual_spec: Dict[str, Any]) -> str:
    """
    Renders any declarative VisualSpec into a high-resolution, self-contained SVG string.
    Suitable for inline browser rendering and Notion Native File Uploads.
    """
    view_box = visual_spec.get("viewBox", {"width": 320, "height": 200})
    w = view_box.get("width", 320)
    h = view_box.get("height", 200)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%">',
        '  <defs>',
        '    <style>',
        '      .txt { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }',
        '      .dim-lbl { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; font-size: 12px; font-weight: bold; fill: #1e293b; }',
        '      .pt-lbl { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; font-weight: 600; fill: #1e293b; }',
        '    </style>',
        '  </defs>',
        f'  <rect width="100%" height="100%" fill="#f8fafc" rx="10" stroke="#e2e8f0" stroke-width="1"/>',
    ]

    elements = visual_spec.get("elements", [])
    for el in elements:
        t = el.get("type")
        if t == "polygon":
            pts = " ".join(f"{p[0]},{p[1]}" for p in el.get("points", []))
            stroke = el.get("stroke", "#6366f1")
            fill = el.get("fill", "rgba(99, 102, 241, 0.08)")
            sw = el.get("strokeWidth", 2.5)
            s_dash = f' stroke-dasharray="{el["strokeDasharray"]}"' if el.get("strokeDasharray") else ""
            svg_parts.append(f'  <polygon points="{pts}" stroke="{stroke}" fill="{fill}" stroke-width="{sw}" stroke-linejoin="round"{s_dash}/>')
            if el.get("rightAngleAt"):
                rx, ry = el["rightAngleAt"]
                s = 14
                svg_parts.append(f'  <rect x="{rx}" y="{ry - s}" width="{s}" height="{s}" fill="none" stroke="#64748b" stroke-width="1.5"/>')

        elif t == "line":
            pts = el.get("points", [])
            if len(pts) >= 2:
                x1, y1 = pts[0]
                x2, y2 = pts[1]
                stroke = el.get("stroke", "#64748b")
                sw = el.get("strokeWidth", 2)
                s_dash = f' stroke-dasharray="{el["strokeDasharray"]}"' if el.get("strokeDasharray") else ""
                svg_parts.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{s_dash}/>')

        elif t == "circle":
            cx, cy = el.get("center", [w / 2, h / 2])
            r = el.get("radius", 40)
            stroke = el.get("stroke", "#0284c7")
            fill = el.get("fill", "rgba(56, 189, 248, 0.08)")
            sw = el.get("strokeWidth", 2.5)
            svg_parts.append(f'  <circle cx="{cx}" cy="{cy}" r="{r}" stroke="{stroke}" fill="{fill}" stroke-width="{sw}"/>')

        elif t == "cylinder":
            cx, cy = el.get("center", [w / 2, h / 2])
            rx = el.get("radiusX", 55)
            ry = el.get("radiusY", 18)
            cyl_h = el.get("height", 100)
            top_y = cy - cyl_h / 2
            bot_y = cy + cyl_h / 2
            stroke = el.get("stroke", "#7c3aed")
            fill = el.get("fill", "rgba(139, 92, 246, 0.08)")
            sw = el.get("strokeWidth", 2.5)
            # Body path
            svg_parts.append(f'  <path d="M {cx - rx} {top_y} L {cx - rx} {bot_y} A {rx} {ry} 0 0 0 {cx + rx} {bot_y} L {cx + rx} {top_y} Z" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
            # Dashed back curve of bottom ellipse
            svg_parts.append(f'  <path d="M {cx - rx} {bot_y} A {rx} {ry} 0 0 1 {cx + rx} {bot_y}" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="3 3"/>')
            # Top ellipse
            svg_parts.append(f'  <ellipse cx="{cx}" cy="{top_y}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

        elif t == "point":
            coord = el.get("coord", [0, 0])
            cx, cy = coord[0], coord[1]
            color = el.get("color", "#2563eb")
            svg_parts.append(f'  <circle cx="{cx}" cy="{cy}" r="4.5" fill="{color}" stroke="#ffffff" stroke-width="1.5"/>')
            if el.get("label"):
                svg_parts.append(f'  <text x="{cx + 8}" y="{cy - 8}" class="pt-lbl">{el["label"]}</text>')

        elif t == "angle-arc":
            cx, cy = el.get("center", [0, 0])
            r = el.get("radius", 25)
            start_deg = el.get("startAngle", 0)
            end_deg = el.get("endAngle", 90)
            r1 = math.radians(start_deg)
            r2 = math.radians(end_deg)
            x1 = cx + r * math.cos(r1)
            y1 = cy - r * math.sin(r1)
            x2 = cx + r * math.cos(r2)
            y2 = cy - r * math.sin(r2)
            diff = (end_deg - start_deg) % 360
            large_arc = 1 if diff > 180 else 0
            svg_parts.append(f'  <path d="M {x1:.1f} {y1:.1f} A {r} {r} 0 {large_arc} 0 {x2:.1f} {y2:.1f}" fill="none" stroke="#d97706" stroke-width="2"/>')
            if el.get("label"):
                mid_rad = math.radians((start_deg + end_deg) / 2)
                lbl_x = cx + (r + 14) * math.cos(mid_rad)
                lbl_y = cy - (r + 14) * math.sin(mid_rad)
                svg_parts.append(f'  <text x="{lbl_x:.1f}" y="{lbl_y:.1f}" text-anchor="middle" dominant-baseline="central" class="dim-lbl" fill="#d97706">{el["label"]}</text>')

        elif t == "dimension-label":
            start = el.get("start", [0, 0])
            end = el.get("end", [0, 0])
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2
            pos = el.get("position", "bottom")
            offset = el.get("offset", 14)

            tx, ty = mid_x, mid_y
            anchor = "middle"
            if pos == "bottom":
                ty += offset
            elif pos == "top":
                ty -= offset - 4
            elif pos == "left":
                tx -= offset
                anchor = "end"
            elif pos == "right":
                tx += offset
                anchor = "start"
            elif pos == "hypotenuse":
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = math.sqrt(dx * dx + dy * dy) or 1
                tx += (-dy / length) * offset
                ty += (dx / length) * offset

            hl_color = '#d97706' if el.get("highlight") else '#1e293b'
            svg_parts.append(f'  <text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anchor}" dominant-baseline="central" class="dim-lbl" fill="{hl_color}">{el.get("label", "")}</text>')

        elif t == "text":
            tx = el.get("x", 0)
            ty = el.get("y", 0)
            color = el.get("color", "#1e293b")
            fs = el.get("fontSize", 12)
            svg_parts.append(f'  <text x="{tx}" y="{ty}" class="txt" font-size="{fs}" font-weight="600" fill="{color}">{el.get("label", "")}</text>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)
