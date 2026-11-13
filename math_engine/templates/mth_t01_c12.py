# -*- coding: utf-8 -*-
"""
Parameterized problem templates for MTH-T01-C12: Math Models and Geometry.
Units covered:
- MTH-T01-C12-U03: Properties of Angles, Triangles, and the Pythagorean Theorem
- MTH-T01-C12-U04: Properties of Rectangles, Triangles, and Trapezoids
- MTH-T01-C12-U05: Circles and Irregular Figures
- MTH-T01-C12-U06: Volume and Surface Area (Cylinders, Boxes, Cones)

Every geometry template exports a standard declarative `visual` specification (VisualSpec)
rendered precisely via SVG on the client side.
"""

from math_engine.fmt import R

UNIT = "MTH-T01-C12"
TITLE = "Math Models and Geometry"

MISTAKE_TAGS = [
    {
        "id": "pythagoras-hypotenuse",
        "label": "Added instead of subtracted for a leg ($a^2 = c^2 - b^2$)",
        "name": "Pythagorean Leg vs Hypotenuse Error",
        "autoFrom": ["whole_sign_flip"],
    },
    {
        "id": "formula-perimeter-area",
        "label": "Confused perimeter formula with area formula",
        "name": "Perimeter vs Area Confusion",
        "autoFrom": [],
    },
    {
        "id": "trapezoid-height",
        "label": "Forgot $\\frac{1}{2}$ in trapezoid area: $A = \\frac{1}{2}(b_1 + b_2)h$",
        "name": "Trapezoid Area Constant Error",
        "autoFrom": ["off_by_factor"],
    },
    {
        "id": "circle-diameter-radius",
        "label": "Used diameter instead of radius in $\\pi r^2$",
        "name": "Diameter vs Radius Confusion",
        "autoFrom": ["off_by_factor"],
    },
    {
        "id": "volume-surface-area",
        "label": "Confused volume ($V$) with surface area ($SA$)",
        "name": "Volume vs Surface Area Error",
        "autoFrom": [],
    },
    {
        "id": "arithmetic-slip",
        "label": "Arithmetic / calculation slip",
        "name": "Arithmetic Slip",
        "autoFrom": ["rounding", "off_by_factor"],
    },
]


def S(latex, explain, val=None, eq=None):
    step = {"latex": latex, "explain": explain}
    if val is not None:
        step["val"] = val
    if eq is not None:
        step["eq"] = eq
    return step


# ---------------------------------------------------------------------------
# Template 1 (U03): Pythagorean Theorem - Find Hypotenuse (Level 1 Foundation)
# Triples: (3,4,5), (5,12,13), (6,8,10), (8,15,17), (7,24,25)
# ---------------------------------------------------------------------------
def t_pythagoras_hypotenuse(rng):
    triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (9, 12, 15)]
    a, b, c = rng.choice(triples)
    if rng.choice([True, False]):
        a, b = b, a

    scale = 140 / max(a, b)
    w_px = max(60, min(240, int(b * scale)))
    h_px = max(40, min(140, int(a * scale)))
    origin_x, origin_y = 50, 160
    p_right = [origin_x, origin_y]
    p_top = [origin_x, origin_y - h_px]
    p_far = [origin_x + w_px, origin_y]

    visual = {
        "type": "geometry-2d",
        "viewBox": {"width": 320, "height": 190},
        "elements": [
            {
                "type": "polygon",
                "points": [p_right, p_far, p_top],
                "stroke": "#818cf8",
                "fill": "rgba(129, 140, 248, 0.08)",
                "rightAngleAt": p_right,
            },
            {
                "type": "dimension-label",
                "start": p_top,
                "end": p_right,
                "label": f"a = {a}",
                "position": "left",
                "offset": 12,
            },
            {
                "type": "dimension-label",
                "start": p_right,
                "end": p_far,
                "label": f"b = {b}",
                "position": "bottom",
                "offset": 14,
            },
            {
                "type": "dimension-label",
                "start": p_top,
                "end": p_far,
                "label": "c = ?",
                "position": "hypotenuse",
                "offset": 14,
                "highlight": True,
            },
        ],
    }

    c_sq = c * c
    return {
        "category": "Core Skill",
        "context": "Geometry: Pythagorean Theorem",
        "references": ["MTH-T01-C12-U03"],
        "prompt": f"Find the length of the hypotenuse $c$ of the right triangle with legs $a = {a}$ and $b = {b}$.",
        "display": f"c = \\sqrt{{{a}^2 + {b}^2}}",
        "plainText": f"sqrt({a}^2 + {b}^2)",
        "visual": visual,
        "answerSpec": {"type": "number", "value": str(c), "forms": ["exact"]},
        "answerDisplay": str(c),
        "answerPlain": str(c),
        "inputHint": "Enter integer, e.g. 31 or 47",
        "checkpointHint": f"Evaluate $a^2 + b^2 = {a * a} + {b * b} = {c_sq}$.",
        "commonTrapTag": "pythagoras-hypotenuse",
        "steps": [
            S(
                f"c = \\sqrt{{a^2 + b^2}} = \\sqrt{{{a}^2 + {b}^2}}",
                "Write the Pythagorean formula solved for hypotenuse $c$ and substitute the legs.",
                f"sqrt({a}**2 + {b}**2)",
            ),
            S(
                f"= \\sqrt{{{a * a} + {b * b}}} = \\sqrt{{{c_sq}}}",
                "Square both legs and add under the radical.",
                f"sqrt({c_sq})",
            ),
            S(f"= {c}", "Evaluate the exact square root to find the length of the hypotenuse $c$.", str(c)),
        ],
        "verify": {"source": f"sqrt({a}**2 + {b}**2)"},
    }


# ---------------------------------------------------------------------------
# Template 2 (U04): Area & Perimeter of Trapezoid (Level 2 Standard Exam)
# ---------------------------------------------------------------------------
def t_trapezoid_area(rng):
    b1 = rng.choice([6, 8, 10, 12])
    b2 = b1 + rng.choice([4, 6, 8])
    h = rng.choice([4, 5, 6, 8])
    area = R(b1 + b2) * h / 2

    # SVG coordinates
    top_w = 90
    bot_w = 170
    h_px = 80
    ox, oy = 70, 140
    p1 = [ox, oy]  # bottom left
    p2 = [ox + bot_w, oy]  # bottom right
    p3 = [ox + bot_w - 30, oy - h_px]  # top right
    p4 = [ox + 20, oy - h_px]  # top left

    visual = {
        "type": "geometry-2d",
        "viewBox": {"width": 320, "height": 180},
        "elements": [
            {
                "type": "polygon",
                "points": [p1, p2, p3, p4],
                "stroke": "#10b981",
                "fill": "rgba(16, 185, 129, 0.08)",
            },
            {
                "type": "line",
                "points": [[p4[0], p4[1]], [p4[0], oy]],
                "stroke": "#94a3b8",
                "strokeDasharray": "3 3",
            },
            {
                "type": "dimension-label",
                "start": p4,
                "end": p3,
                "label": f"b₁ = {b1}",
                "position": "top",
                "offset": 10,
            },
            {
                "type": "dimension-label",
                "start": p1,
                "end": p2,
                "label": f"b₂ = {b2}",
                "position": "bottom",
                "offset": 14,
            },
            {
                "type": "dimension-label",
                "start": [p4[0], p4[1]],
                "end": [p4[0], oy],
                "label": f"h = {h}",
                "position": "right",
                "offset": 10,
                "highlight": True,
            },
        ],
    }

    return {
        "category": "Core Skill",
        "context": "Geometry: Quadrilaterals",
        "references": ["MTH-T01-C12-U04"],
        "prompt": f"Find the area $A$ of the trapezoid with parallel bases $b_1 = {b1}$, $b_2 = {b2}$, and height $h = {h}$.",
        "display": "A = \\frac{1}{2}(b_1 + b_2)h",
        "plainText": f"(1/2)*({b1} + {b2})*{h}",
        "visual": visual,
        "answerSpec": {"type": "number", "value": str(area), "forms": ["exact"]},
        "answerDisplay": str(area),
        "answerPlain": str(area),
        "inputHint": "Enter number, e.g. 235 or 479",
        "checkpointHint": f"The sum of the bases is $b_1 + b_2 = {b1 + b2}$.",
        "commonTrapTag": "trapezoid-height",
        "steps": [
            S(
                f"A = \\frac{{1}}{{2}}(b_1 + b_2)h = \\frac{{1}}{{2}}({b1} + {b2})({h})",
                "Substitute the bases and height into the trapezoid area formula.",
                f"(1/2)*({b1} + {b2})*{h}",
            ),
            S(f"= \\frac{{1}}{{2}}({b1 + b2})({h})", "Add the two parallel bases first.", f"(1/2)*{b1 + b2}*{h}"),
            S(f"= {area}", f"Multiply by $\\frac{{1}}{{2}}$ and the height $h = {h}$.", str(area)),
        ],
        "verify": {"source": f"(1/2)*({b1} + {b2})*{h}"},
    }


# ---------------------------------------------------------------------------
# Template 3 (U05): Circle Area & Circumference (Level 2 Standard Exam)
# ---------------------------------------------------------------------------
def t_circle_area_in_terms_of_pi(rng):
    r = rng.choice([3, 4, 5, 6, 7, 8, 9, 10])
    area_coeff = r * r

    visual = {
        "type": "geometry-2d",
        "viewBox": {"width": 300, "height": 180},
        "elements": [
            {
                "type": "circle",
                "center": [150, 90],
                "radius": 55,
                "stroke": "#38bdf8",
                "fill": "rgba(56, 189, 248, 0.08)",
            },
            {
                "type": "line",
                "points": [[150, 90], [205, 90]],
                "stroke": "#cbd5e1",
                "strokeDasharray": "2 2",
            },
            {
                "type": "dimension-label",
                "start": [150, 90],
                "end": [205, 90],
                "label": f"r = {r}",
                "position": "top",
                "offset": 8,
                "highlight": True,
            },
        ],
    }

    return {
        "category": "Core Skill",
        "context": "Geometry: Circles",
        "references": ["MTH-T01-C12-U05"],
        "prompt": f"Find the exact area $A$ of a circle with radius $r = {r}$ (in terms of $\\pi$).",
        "display": "A = \\pi r^2",
        "plainText": f"pi * {r}^2",
        "visual": visual,
        "answerSpec": {"type": "expression", "value": f"{area_coeff}*pi", "variables": ["pi"]},
        "answerDisplay": f"{area_coeff}\\pi",
        "answerPlain": f"{area_coeff} pi",
        "inputHint": "Enter exact form with pi, e.g. 230 pi or 470*pi",
        "checkpointHint": f"The radius squared is $r^2 = {r}^2 = {area_coeff}$.",
        "commonTrapTag": "circle-diameter-radius",
        "steps": [
            S(
                f"A = \\pi r^2 = \\pi({r})^2",
                "Write the circle area formula and substitute the radius $r$.",
                f"pi*{r}**2",
            ),
            S(
                f"= {area_coeff}\\pi",
                f"Square the radius: ${r}^2 = {area_coeff}$. Leave $\\pi$ exact.",
                f"{area_coeff}*pi",
            ),
        ],
        "verify": {"source": f"pi*{r}**2"},
    }


# ---------------------------------------------------------------------------
# Template 4 (U06): Cylinder Volume (Level 3 Applied)
# ---------------------------------------------------------------------------
def t_cylinder_volume(rng):
    r = rng.choice([2, 3, 4, 5])
    h = rng.choice([6, 8, 10, 12])
    v_coeff = r * r * h

    visual = {
        "type": "geometry-3d-wireframe",
        "viewBox": {"width": 300, "height": 190},
        "elements": [
            {
                "type": "cylinder",
                "center": [150, 95],
                "radiusX": 55,
                "radiusY": 16,
                "height": 90,
                "stroke": "#38bdf8",
                "fill": "rgba(56, 189, 248, 0.08)",
            },
            {
                "type": "line",
                "points": [[150, 50], [205, 50]],
                "stroke": "#cbd5e1",
                "strokeDasharray": "2 2",
            },
            {
                "type": "dimension-label",
                "start": [150, 50],
                "end": [205, 50],
                "label": f"r = {r}",
                "position": "top",
                "offset": 8,
            },
            {
                "type": "dimension-label",
                "start": [215, 50],
                "end": [215, 140],
                "label": f"h = {h}",
                "position": "right",
                "offset": 12,
                "highlight": True,
            },
        ],
    }

    return {
        "category": "Core Skill",
        "context": "Geometry: 3D Solids",
        "references": ["MTH-T01-C12-U06"],
        "prompt": f"Find the exact volume $V$ of a right circular cylinder with radius $r = {r}$ and height $h = {h}$ (in terms of $\\pi$).",
        "display": "V = \\pi r^2 h",
        "plainText": f"pi * {r}^2 * {h}",
        "visual": visual,
        "answerSpec": {"type": "expression", "value": f"{v_coeff}*pi", "variables": ["pi"]},
        "answerDisplay": f"{v_coeff}\\pi",
        "answerPlain": f"{v_coeff} pi",
        "inputHint": "Enter exact form with pi, e.g. 230 pi or 470*pi",
        "checkpointHint": f"The base area is $B = \\pi r^2 = {r * r}\\pi$.",
        "commonTrapTag": "volume-surface-area",
        "steps": [
            S(
                f"V = \\pi r^2 h = \\pi({r})^2({h})",
                "Substitute the radius and height into the cylinder volume formula.",
                f"pi*{r}**2*{h}",
            ),
            S(f"= \\pi({r * r})({h})", f"Evaluate the base area: ${r}^2 = {r * r}$.", f"pi*{r * r}*{h}"),
            S(f"= {v_coeff}\\pi", f"Multiply by the height: ${r * r} \\times {h} = {v_coeff}$.", f"{v_coeff}*pi"),
        ],
        "verify": {"source": f"pi*{r}**2*{h}"},
    }


TEMPLATES = [
    {"key": "pythagoras-hypotenuse", "trapTag": "pythagoras-hypotenuse", "level": 1, "build": t_pythagoras_hypotenuse},
    {"key": "trapezoid-area", "trapTag": "trapezoid-height", "level": 2, "build": t_trapezoid_area},
    {"key": "circle-area-pi", "trapTag": "circle-diameter-radius", "level": 2, "build": t_circle_area_in_terms_of_pi},
    {"key": "cylinder-volume", "trapTag": "volume-surface-area", "level": 3, "build": t_cylinder_volume},
]
