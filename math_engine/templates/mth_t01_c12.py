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
import math
import sympy as sp
from math_engine.fmt import R, num, num_plain, terms
from math_engine.templates.flaw_utils import build_flaw_choice_problem

UNIT = "MTH-T01-C12"
TITLE = "Math Models and Geometry"

MISTAKE_TAGS = [
    {"id": "pythagoras-hypotenuse", "label": "Added instead of subtracted for a leg ($a^2 = c^2 - b^2$)", "name": "Pythagorean Leg vs Hypotenuse Error", "autoFrom": ["whole_sign_flip"]},
    {"id": "formula-perimeter-area", "label": "Confused perimeter formula with area formula", "name": "Perimeter vs Area Confusion", "autoFrom": []},
    {"id": "trapezoid-height", "label": "Forgot factor of 2 in numerator when solving for height", "name": "Trapezoid Height Factor Error", "autoFrom": ["off_by_factor"]},
    {"id": "omitted-half-factor", "label": "Forgot 1/2 in trapezoid area: $A = 1/2(b_1 + b_2)h$", "name": "Trapezoid Omitted Half Factor", "autoFrom": ["off_by_factor"]},
    {"id": "circle-diameter-radius", "label": "Used diameter instead of radius in formula", "name": "Diameter vs Radius Confusion", "autoFrom": ["off_by_factor"]},
    {"id": "volume-surface-area", "label": "Confused volume ($V$) with surface area ($SA$)", "name": "Volume vs Surface Area Error", "autoFrom": []},
    {"id": "linear-addition-trap", "label": "Added legs linearly without squaring ($c = a + b$)", "name": "Linear Addition Trap", "autoFrom": []},
    {"id": "pythagoras-leg-subtraction", "label": "Subtracted hypotenuse and leg linearly ($a = c - b$)", "name": "Linear Leg Subtraction Error", "autoFrom": []},
    {"id": "path-distance-vs-displacement", "label": "Calculated total perimeter path instead of straight-line distance", "name": "Path vs Displacement Error", "autoFrom": []},
    {"id": "arithmetic-slip", "label": "Arithmetic / calculation slip", "name": "Arithmetic Slip", "autoFrom": ["rounding", "off_by_factor"]},
    {"id": "whole-triangle-inradius-confusion", "label": "Computed inradius of parent triangle instead of divided altitude sub-triangle", "name": "Parent vs Sub-Triangle Inradius Confusion", "autoFrom": []},
    {"id": "trapezoid-diagonal-bisect-trap", "label": "Assumed trapezoid diagonals bisect each other instead of using similar triangle ratio", "name": "Trapezoid Diagonal Bisection Fallacy", "autoFrom": []},
    {"id": "pi-retained-in-lunes-trap", "label": "Retained pi factor in area of lunes of Hippocrates (failing to recognize pi cancellation)", "name": "Lunes Pi Factor Retention Trap", "autoFrom": []},
    {"id": "frustum-cylinder-average-trap", "label": "Averaged radii and computed as cylinder instead of conical frustum", "name": "Frustum Average Cylinder Error", "autoFrom": []},
    {"id": "internal-boundary-double-count-trap", "label": "Included internal boundary face in composite solid surface area", "name": "Internal Boundary Face Double Count", "autoFrom": []},
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
def t_pythagoras_hypotenuse(rng, form=None):
    triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (9, 12, 15)]
    a, b, c = rng.choice(triples)
    if rng.choice([True, False]):
        a, b = b, a
    if form is None:
        form = rng.choice(["direct", "reverse", "contextual"])

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
                "label": f"a = {a}" if form != "reverse" else "a = ?",
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
                "label": "c = ?" if form != "reverse" else f"c = {c}",
                "position": "hypotenuse",
                "offset": 14,
                "highlight": True,
            },
        ],
    }

    if form == "reverse":
        a_sq = c * c - b * b
        trap_val = str(c - b)  # Mistake: linear subtraction c - b without squaring
        return {
            "form": "reverse",
            "category": "Core Skill",
            "context": "Geometry: Pythagorean Theorem (Unknown Leg)",
            "references": ["MTH-T01-C12-U03"],
            "prompt": f"Find the length of the unknown leg $a$ of a right triangle with hypotenuse $c = {c}$ and leg $b = {b}$.",
            "display": f"a = \\sqrt{{{c}^2 - {b}^2}}",
            "plainText": f"sqrt({c}^2 - {b}^2)",
            "visual": visual,
            "answerSpec": {"type": "number", "value": str(a), "forms": ["exact"]},
            "answerDisplay": str(a),
            "answerPlain": str(a),
            "inputHint": "Enter integer, e.g. 31 or 47",
            "checkpointHint": f"Subtract squares to find a leg: $a^2 = c^2 - b^2 = {c * c} - {b * b} = {a_sq}$.",
            "commonTrapTag": "pythagoras-leg-subtraction",
            "steps": [
                S(f"a = \\sqrt{{c^2 - b^2}} = \\sqrt{{{c}^2 - {b}^2}}", "Solve the Pythagorean formula for leg $a$ and substitute $c$ and $b$.", f"sqrt({c}**2 - {b}**2)"),
                S(f"= \\sqrt{{{c * c} - {b * b}}} = \\sqrt{{{a_sq}}}", "Square hypotenuse and leg, then subtract under the radical.", f"sqrt({a_sq})"),
                S(f"= {a}", "Evaluate the principal square root to find leg $a$.", str(a)),
            ],
            "verify": {"source": f"sqrt({c}**2 - {b}**2)", "trapValue": trap_val},
        }

    c_sq = c * c
    trap_val = str(a + b)
    if form == "contextual":
        prompt_text = f"A guy wire stretches from the top of a ${a}$-meter vertical pole to a ground anchor ${b}$ meters from the base. Find the exact length $c$ of the wire."
        trap_tag = "path-distance-vs-displacement"
    else:
        prompt_text = f"Find the length of the hypotenuse $c$ of the right triangle with legs $a = {a}$ and $b = {b}$."
        trap_tag = "linear-addition-trap"

    return {
        "form": form,
        "category": "Core Skill",
        "context": "Geometry: Pythagorean Theorem",
        "references": ["MTH-T01-C12-U03"],
        "prompt": prompt_text,
        "display": f"c = \\sqrt{{{a}^2 + {b}^2}}",
        "plainText": f"sqrt({a}^2 + {b}^2)" if form == "direct" else f"sqrt({a}^2 + {b}^2) [ctx]",
        "visual": visual,
        "answerSpec": {"type": "number", "value": str(c), "forms": ["exact"]},
        "answerDisplay": str(c),
        "answerPlain": str(c),
        "inputHint": "Enter integer, e.g. 31 or 47",
        "checkpointHint": f"Evaluate $a^2 + b^2 = {a * a} + {b * b} = {c_sq}$.",
        "commonTrapTag": trap_tag,
        "steps": [
            S(f"c = \\sqrt{{a^2 + b^2}} = \\sqrt{{{a}^2 + {b}^2}}", "Write the Pythagorean formula solved for hypotenuse $c$ and substitute the legs.", f"sqrt({a}**2 + {b}**2)"),
            S(f"= \\sqrt{{{a * a} + {b * b}}} = \\sqrt{{{c_sq}}}", "Square both legs and add under the radical.", f"sqrt({c_sq})"),
            S(f"= {c}", "Evaluate the exact square root to find the length of the hypotenuse $c$.", str(c)),
        ],
        "verify": {"source": f"sqrt({a}**2 + {b}**2)", "trapValue": trap_val},
    }

# ---------------------------------------------------------------------------
# Template 2 (U04): Area & Perimeter of Trapezoid (Level 2 Standard Exam)
# ---------------------------------------------------------------------------
def t_trapezoid_area(rng, form=None):
    b1 = rng.choice([6, 8, 10, 12])
    b2 = b1 + rng.choice([4, 6, 8])
    h = rng.choice([4, 5, 6, 8])
    area = R(b1 + b2) * h / 2

    # SVG coordinates
    top_w = 90
    bot_w = 170
    h_px = 80
    ox, oy = 70, 140
    p1 = [ox, oy]                    # bottom left
    p2 = [ox + bot_w, oy]            # bottom right
    p3 = [ox + bot_w - 30, oy - h_px]# top right
    p4 = [ox + 20, oy - h_px]        # top left

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

    if form is None:
        form = rng.choice(["direct", "reverse"])
    if form == "reverse":
        trap_val = str(R(area) / (b1 + b2))
        return {
            "form": "reverse",
            "category": "Core Skill",
            "context": "Geometry: Quadrilaterals (Unknown Height)",
            "references": ["MTH-T01-C12-U04"],
            "prompt": f"A trapezoid with parallel bases $b_1 = {b1}$ and $b_2 = {b2}$ has an area of $A = {area}$. Find its height $h$.",
            "display": f"h = \\frac{{2A}}{{b_1 + b_2}}",
            "plainText": f"(2 * {area}) / ({b1} + {b2})",
            "visual": visual,
            "answerSpec": {"type": "number", "value": str(h), "forms": ["exact"]},
            "answerDisplay": str(h),
            "answerPlain": str(h),
            "inputHint": "Enter number, e.g. 235 or 479",
            "checkpointHint": f"Multiply area by $2$ before dividing by $b_1 + b_2 = {b1 + b2}$.",
            "commonTrapTag": "trapezoid-height",
            "steps": [
                S(f"h = \\frac{{2A}}{{b_1 + b_2}} = \\frac{{2({area})}}{{{b1} + {b2}}}", "Solve the trapezoid area formula for height $h$ and substitute known values.", f"(2*{area})/({b1} + {b2})"),
                S(f"= \\frac{{{2 * area}}}{{{b1 + b2}}}", "Double the area and sum the parallel bases.", f"({2 * area})/({b1 + b2})"),
                S(f"= {h}", "Divide to obtain the height $h$.", str(h)),
            ],
            "verify": {"source": f"(2*{area})/({b1} + {b2})", "trapValue": trap_val},
        }

    trap_val = str((b1 + b2) * h)
    return {
        "form": "direct",
        "category": "Core Skill",
        "context": "Geometry: Quadrilaterals",
        "references": ["MTH-T01-C12-U04"],
        "prompt": f"Find the area $A$ of the trapezoid with parallel bases $b_1 = {b1}$, $b_2 = {b2}$, and height $h = {h}$.",
        "display": f"A = \\frac{{1}}{{2}}(b_1 + b_2)h",
        "plainText": f"(1/2)*({b1} + {b2})*{h}",
        "visual": visual,
        "answerSpec": {"type": "number", "value": str(area), "forms": ["exact"]},
        "answerDisplay": str(area),
        "answerPlain": str(area),
        "inputHint": "Enter number, e.g. 235 or 479",
        "checkpointHint": f"The sum of the bases is $b_1 + b_2 = {b1 + b2}$.",
        "commonTrapTag": "omitted-half-factor",
        "steps": [
            S(f"A = \\frac{{1}}{{2}}(b_1 + b_2)h = \\frac{{1}}{{2}}({b1} + {b2})({h})", "Substitute the bases and height into the trapezoid area formula.", f"(1/2)*({b1} + {b2})*{h}"),
            S(f"= \\frac{{1}}{{2}}({b1 + b2})({h})", "Add the two parallel bases first.", f"(1/2)*{b1 + b2}*{h}"),
            S(f"= {area}", f"Multiply by $\\frac{{1}}{{2}}$ and the height $h = {h}$.", str(area)),
        ],
        "verify": {"source": f"(1/2)*({b1} + {b2})*{h}", "trapValue": trap_val},
    }

# ---------------------------------------------------------------------------
# Template 3 (U05): Circle Area & Circumference (Level 2 Standard Exam)
# ---------------------------------------------------------------------------
def t_circle_area_in_terms_of_pi(rng, form=None):
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

    if form is None:
        form = rng.choice(["direct", "from-diameter"])
    d = 2 * r
    if form == "from-diameter":
        trap_val = f"{d * d} pi"  # Mistake: squaring diameter instead of radius
        return {
            "form": "from-diameter",
            "category": "Core Skill",
            "context": "Geometry: Circles (Given Diameter)",
            "references": ["MTH-T01-C12-U05"],
            "prompt": f"Find the exact area $A$ of a circle with diameter $d = {d}$ (in terms of $\\pi$).",
            "display": f"A = \\pi \\left(\\frac{{d}}{{2}}\\right)^2",
            "plainText": f"pi * ({d}/2)^2",
            "visual": visual,
            "answerSpec": {"type": "expression", "value": f"{area_coeff}*pi", "variables": ["pi"]},
            "answerDisplay": f"{area_coeff}\\pi",
            "answerPlain": f"{area_coeff} pi",
            "inputHint": "Enter exact form with pi, e.g. 230 pi or 470*pi",
            "checkpointHint": f"First halve the diameter to get radius $r = {r}$, then square it.",
            "commonTrapTag": "circle-diameter-radius",
            "steps": [
                S(f"r = \\frac{{d}}{{2}} = \\frac{{{d}}}{{2}} = {r}", "Halve the diameter to obtain the radius $r$, then substitute into $A = \\pi r^2$.", eq=(f"{d}/2", str(r))),
                S(f"A = \\pi({r})^2 = {area_coeff}\\pi", f"Square the radius ${r}^2 = {area_coeff}$ and leave $\\pi$ exact.", f"{area_coeff}*pi"),
            ],
            "verify": {"source": f"pi*{r}**2", "trapValue": trap_val},
        }

    trap_val = f"{2 * r} pi"  # Mistake: calculating circumference 2*pi*r instead of area
    return {
        "form": "direct",
        "category": "Core Skill",
        "context": "Geometry: Circles",
        "references": ["MTH-T01-C12-U05"],
        "prompt": f"Find the exact area $A$ of a circle with radius $r = {r}$ (in terms of $\\pi$).",
        "display": f"A = \\pi r^2",
        "plainText": f"pi * {r}^2",
        "visual": visual,
        "answerSpec": {"type": "expression", "value": f"{area_coeff}*pi", "variables": ["pi"]},
        "answerDisplay": f"{area_coeff}\\pi",
        "answerPlain": f"{area_coeff} pi",
        "inputHint": "Enter exact form with pi, e.g. 230 pi or 470*pi",
        "checkpointHint": f"The radius squared is $r^2 = {r}^2 = {area_coeff}$.",
        "commonTrapTag": "formula-perimeter-area",
        "steps": [
            S(f"A = \\pi r^2 = \\pi({r})^2", "Write the circle area formula and substitute the radius $r$.", f"pi*{r}**2"),
            S(f"= {area_coeff}\\pi", f"Square the radius: ${r}^2 = {area_coeff}$. Leave $\\pi$ exact.", f"{area_coeff}*pi"),
        ],
        "verify": {"source": f"pi*{r}**2", "trapValue": trap_val},
    }

# ---------------------------------------------------------------------------
# Template 4 (U06): Cylinder Volume (Level 3 Applied)
# ---------------------------------------------------------------------------
def t_cylinder_volume(rng, form=None):
    while True:
        r = rng.choice([2, 3, 4, 5])
        h = rng.choice([6, 8, 10, 12])
        if 2 * r * h + 2 * r * r != r * r * h:
            break
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

    if form is None:
        form = rng.choice(["direct", "from-diameter"])
    sa_coeff = 2 * r * h + 2 * r * r
    d = 2 * r
    if form == "from-diameter":
        trap_val = f"{d * d * h} pi"  # Mistake: using diameter directly as radius: pi * d^2 * h
        return {
            "form": "from-diameter",
            "category": "Trap & Edge Case",
            "context": "Geometry: 3D Solids (Diameter Trap)",
            "references": ["MTH-T01-C12-U06"],
            "prompt": f"Find the exact volume $V$ of a right circular cylinder with diameter $d = {d}$ and height $h = {h}$ (in terms of $\\pi$).",
            "display": f"V = \\pi \\left(\\frac{{d}}{{2}}\\right)^2 h",
            "plainText": f"pi * ({d}/2)^2 * {h}",
            "visual": visual,
            "answerSpec": {"type": "expression", "value": f"{v_coeff}*pi", "variables": ["pi"]},
            "answerDisplay": f"{v_coeff}\\pi",
            "answerPlain": f"{v_coeff} pi",
            "inputHint": "Enter exact form with pi, e.g. 230 pi or 470*pi",
            "checkpointHint": f"Halve the diameter to get radius $r = {r}$, then compute $B = \\pi r^2 = {r * r}\\pi$.",
            "commonTrapTag": "circle-diameter-radius",
            "steps": [
                S(f"r = \\frac{{{d}}}{{2}} = {r}, \\quad V = \\pi({r})^2({h})", "Convert diameter to radius $r$ and substitute into the volume formula.", f"pi*{r}**2*{h}"),
                S(f"= \\pi({r * r})({h})", f"Evaluate the circular base area: ${r}^2 = {r * r}$.", f"pi*{r * r}*{h}"),
                S(f"= {v_coeff}\\pi", f"Multiply by the height: ${r * r} \\times {h} = {v_coeff}$.", f"{v_coeff}*pi"),
            ],
            "verify": {"source": f"pi*{r}**2*{h}", "trapValue": trap_val},
        }

    trap_val = f"{sa_coeff} pi"  # Mistake: computing surface area 2*pi*r*h + 2*pi*r^2 instead of volume
    return {
        "form": "direct",
        "category": "Trap & Edge Case",
        "context": "Geometry: 3D Solids",
        "references": ["MTH-T01-C12-U06"],
        "prompt": f"Find the exact volume $V$ of a right circular cylinder with radius $r = {r}$ and height $h = {h}$ (in terms of $\\pi$).",
        "display": f"V = \\pi r^2 h",
        "plainText": f"pi * {r}^2 * {h}",
        "visual": visual,
        "answerSpec": {"type": "expression", "value": f"{v_coeff}*pi", "variables": ["pi"]},
        "answerDisplay": f"{v_coeff}\\pi",
        "answerPlain": f"{v_coeff} pi",
        "inputHint": "Enter exact form with pi, e.g. 230 pi or 470*pi",
        "checkpointHint": f"The base area is $B = \\pi r^2 = {r * r}\\pi$.",
        "commonTrapTag": "volume-surface-area",
        "steps": [
            S(f"V = \\pi r^2 h = \\pi({r})^2({h})", "Substitute the radius and height into the cylinder volume formula.", f"pi*{r}**2*{h}"),
            S(f"= \\pi({r * r})({h})", f"Evaluate the circular base area: ${r}^2 = {r * r}$.", f"pi*{r * r}*{h}"),
            S(f"= {v_coeff}\\pi", f"Multiply by the height: ${r * r} \\times {h} = {v_coeff}$.", f"{v_coeff}*pi"),
        ],
        "verify": {"source": f"pi*{r}**2*{h}", "trapValue": trap_val},
    }

# ---------------------------------------------------------------------------
# Template 5 (U03): Right Triangle Altitude & Inscribed Circle (Level 3 Trap & Diagnostic)
# ---------------------------------------------------------------------------
def t_pythagoras_altitude_inradius(rng, form=None):
    cases = [
        {"AD": 9, "DB": 16, "CD": 12, "AC": 15, "BC": 20, "AB": 25, "r": 3, "r_bcd": 4, "trap_r": 5},
        {"AD": 16, "DB": 9, "CD": 12, "AC": 20, "BC": 15, "AB": 25, "r": 4, "r_bcd": 3, "trap_r": 5},
        {"AD": 18, "DB": 32, "CD": 24, "AC": 30, "BC": 40, "AB": 50, "r": 6, "r_bcd": 8, "trap_r": 10},
        {"AD": 32, "DB": 18, "CD": 24, "AC": 40, "BC": 30, "AB": 50, "r": 8, "r_bcd": 6, "trap_r": 10},
        {"AD": 25, "DB": 144, "CD": 60, "AC": 65, "BC": 156, "AB": 169, "r": 10, "r_bcd": 24, "trap_r": 26},
        {"AD": 144, "DB": 25, "CD": 60, "AC": 156, "BC": 65, "AB": 169, "r": 24, "r_bcd": 10, "trap_r": 26},
    ]
    c = rng.choice(cases)
    ad, db, cd, ac, bc, ab = c["AD"], c["DB"], c["CD"], c["AC"], c["BC"], c["AB"]
    r, r_bcd, trap_r = c["r"], c["r_bcd"], c["trap_r"]

    if form is None:
        form = rng.choice(["direct", "missing-segment"])

    if form == "missing-segment":
        return {
            "form": "missing-segment",
            "category": "Trap & Edge Case",
            "context": "Geometry: Altitude & Sub-Triangle Inradius",
            "references": ["MTH-T01-C12-U03"],
            "prompt": f"In a right-angled triangle $ABC$ with right angle at $C$ and hypotenuse $AB = {ab}$, altitude $CD$ is drawn perpendicular to $AB$ such that $AD = {ad}$. A circle is inscribed inside the complementary sub-triangle $BCD$. Find the radius $r$ of this inscribed circle.",
            "display": f"\\triangle ABC: \\angle C = 90^\\circ,\\ AB = {ab},\\ AD = {ad} \\implies r_{{\\text{{in}}}}(\\triangle BCD) = ?",
            "plainText": f"(({ab} - {ad}) + sqrt({ad}*({ab} - {ad})) - sqrt(({ab} - {ad})^2 + {ad}*({ab} - {ad}))) / 2",
            "answerSpec": {"type": "number", "value": str(r_bcd)},
            "answerDisplay": str(r_bcd),
            "answerPlain": str(r_bcd),
            "inputHint": "Enter the integer radius of the inscribed circle",
            "checkpointHint": "Subtract $AD$ from $AB$ to find segment $DB$, use the Geometric Mean Theorem for altitude $CD$, find leg $BC$, and apply the right-triangle inradius formula.",
            "commonTrapTag": "whole-triangle-inradius-confusion",
            "verify": {"source": str(r_bcd), "trapValue": str(trap_r)},
            "steps": [
                S(f"DB = AB - AD = {ab} - {ad} = {db}, \\quad CD = \\sqrt{{AD \\cdot DB}} = \\sqrt{{{ad} \\cdot {db}}} = {cd}",
                  "Subtract $AD$ from $AB$ to find $DB$, then apply the Geometric Mean Theorem.",
                  eq=[f"sqrt({ad} * ({ab} - {ad}))", f"{cd}"]),
                S(f"BC = \\sqrt{{DB^2 + CD^2}} = \\sqrt{{{db}^2 + {cd}^2}} = {bc}",
                  "Apply the Pythagorean theorem on right triangle $\\triangle BCD$.",
                  eq=[f"sqrt({db}**2 + {cd}**2)", f"{bc}"]),
                S(f"r = \\frac{{DB + CD - BC}}{{2}} = \\frac{{{db} + {cd} - {bc}}}{{2}} = {r_bcd}",
                  "Use the right-triangle inradius formula $r = \\frac{a + b - c}{2}$ on $\\triangle BCD$.",
                  val=str(r_bcd),
                  eq=[f"({db} + {cd} - {bc})/2", str(r_bcd)]),
            ],
        }

    return {
        "form": "direct",
        "category": "Trap & Edge Case",
        "context": "Geometry: Altitude & Inscribed Circle",
        "references": ["MTH-T01-C12-U03"],
        "prompt": f"In a right-angled triangle $ABC$ with right angle at $C$ and hypotenuse $AB = {ab}$, altitude $CD$ is drawn perpendicular to $AB$, dividing the hypotenuse into two segments $AD = {ad}$ and $DB = {db}$. A circle is inscribed inside triangle $ACD$. Find the radius $r$ of this inscribed circle.",
        "display": f"\\triangle ABC: \\angle C = 90^\\circ,\\ AB = {ab},\\ CD \\perp AB,\\ AD = {ad},\\ DB = {db} \\implies r_{{\\text{{in}}}}(\\triangle ACD) = ?",
        "plainText": f"({ad} + sqrt({ad}*{db}) - sqrt({ad}^2 + {ad}*{db})) / 2",
        "answerSpec": {"type": "number", "value": str(r)},
        "answerDisplay": str(r),
        "answerPlain": str(r),
        "inputHint": "Enter the integer radius of the inscribed circle",
        "checkpointHint": "Use the Geometric Mean Theorem to find altitude $CD = \\sqrt{AD \\cdot DB}$. Then apply the Pythagorean theorem on $\\triangle ACD$ to find leg $AC$. Finally, use the right triangle inradius formula $r = \\frac{a + b - c}{2}$.",
        "commonTrapTag": "whole-triangle-inradius-confusion",
        "verify": {"source": str(r), "trapValue": str(trap_r)},
        "steps": [
            S(f"CD^2 = AD \\cdot DB = {ad} \\cdot {db} = {ad * db} \\implies CD = {cd}",
              "The altitude to the hypotenuse satisfies $CD^2 = AD \\cdot DB$.",
              eq=[f"sqrt({ad} * {db})", f"{cd}"]),
            S(f"AC = \\sqrt{{AD^2 + CD^2}} = \\sqrt{{{ad}^2 + {cd}^2}} = {ac}",
              "Apply the Pythagorean theorem on right triangle $\\triangle ACD$.",
              eq=[f"sqrt({ad}**2 + {cd}**2)", f"{ac}"]),
            S(f"r = \\frac{{AD + CD - AC}}{{2}} = \\frac{{{ad} + {cd} - {ac}}}{{2}} = {r}",
              "For any right triangle with legs $a, b$ and hypotenuse $c$, the inradius is $r = \\frac{a + b - c}{2}$.",
              val=str(r),
              eq=[f"({ad} + {cd} - {ac})/2", str(r)]),
        ],
    }

# ---------------------------------------------------------------------------
# Template 6 (U04): Trapezoid Similar Triangles Area Partition (Level 4 Applied Synthesis)
# ---------------------------------------------------------------------------
def t_trapezoid_similar_triangles_area(rng, form=None):
    cases = [
        {"b1": 10, "b2": 24, "leg": 25, "x": 7, "h": 24, "r1": 5, "r2": 12, "h1_str": "120/17", "h2_str": "288/17", "area_top": "600/17", "area_bot": "3456/17", "area_side": "1440/17", "trap_top": "60", "trap_bot": "144", "trap_side": "84"},
        {"b1": 6, "b2": 16, "leg": 13, "x": 5, "h": 12, "r1": 3, "r2": 8, "h1_str": "36/11", "h2_str": "96/11", "area_top": "108/11", "area_bot": "768/11", "area_side": "288/11", "trap_top": "18", "trap_bot": "48", "trap_side": "30"},
        {"b1": 8, "b2": 24, "leg": 17, "x": 8, "h": 15, "r1": 1, "r2": 3, "h1_str": "15/4", "h2_str": "45/4", "area_top": "15", "area_bot": "135", "area_side": "45", "trap_top": "30", "trap_bot": "90", "trap_side": "60"},
        {"b1": 4, "b2": 18, "leg": 25, "x": 7, "h": 24, "r1": 2, "r2": 9, "h1_str": "48/11", "h2_str": "216/11", "area_top": "96/11", "area_bot": "1944/11", "area_side": "432/11", "trap_top": "24", "trap_bot": "108", "trap_side": "66"},
        {"b1": 12, "b2": 28, "leg": 17, "x": 8, "h": 15, "r1": 3, "r2": 7, "h1_str": "9/2", "h2_str": "21/2", "area_top": "27", "area_bot": "147", "area_side": "63", "trap_top": "45", "trap_bot": "105", "trap_side": "75"},
    ]
    c = rng.choice(cases)
    b1, b2, leg, x, h, r1, r2 = c["b1"], c["b2"], c["leg"], c["x"], c["h"], c["r1"], c["r2"]

    if form is None:
        form = rng.choice(["direct", "bottom-triangle", "side-triangle"])

    if form == "bottom-triangle":
        h2_str = c["h2_str"]
        area_str = c["area_bot"]
        trap_area = c["trap_bot"]
        disp_area = f"\\frac{{{area_str.split('/')[0]}}}{{{area_str.split('/')[1]}}}" if "/" in area_str else area_str
        return {
            "form": "bottom-triangle",
            "category": "Interleaved Synthesis",
            "context": "Geometry: Trapezoid Lower Diagonal Triangle",
            "references": ["MTH-T01-C12-U03", "MTH-T01-C12-U04"],
            "prompt": f"In an isosceles trapezoid $ABCD$, the parallel bases are $AB = {b1}$ and $CD = {b2}$, and the non-parallel legs are $AD = BC = {leg}$. Diagonals $AC$ and $BD$ intersect at point $E$. Find the exact area of lower triangle $CDE$.",
            "display": f"\\text{{Trapezoid }} ABCD:\\ AB = {b1},\\ CD = {b2},\\ AD = BC = {leg} \\implies \\text{{Area}}(\\triangle CDE) = ?",
            "plainText": f"(1/2) * {b2} * sqrt({leg}^2 - (({b2} - {b1})/2)^2) * ({b2}/({b1} + {b2}))",
            "answerSpec": {"type": "expression", "value": area_str},
            "answerDisplay": disp_area,
            "answerPlain": area_str,
            "inputHint": "Enter exact fraction or integer e.g. 35/4 or 42",
            "checkpointHint": "Find trapezoid height $h$ via the Pythagorean theorem on the leg projection, then partition $h$ using similarity ratio $CD : (AB + CD)$.",
            "commonTrapTag": "trapezoid-diagonal-bisect-trap",
            "verify": {"source": area_str, "trapValue": trap_area},
            "steps": [
                S(f"x = \\frac{{{b2} - {b1}}}{{2}} = {x}, \\quad h = \\sqrt{{{leg}^2 - {x}^2}} = {h}",
                  f"Symmetrical base offset gives a right triangle with hypotenuse {leg} and base {x}.",
                  eq=[f"sqrt({leg}**2 - {x}**2)", f"{h}"]),
                S(f"\\triangle ABE \\sim \\triangle CDE \\implies \\frac{{h_1}}{{h_2}} = \\frac{{{b1}}}{{{b2}}} = \\frac{{{r1}}}{{{r2}}}",
                  "Since $AB \\parallel CD$, alternate interior angles make $\\triangle ABE \\sim \\triangle CDE$.",
                  eq=[f"{b1}/{b2}", f"{r1}/{r2}"]),
                S(f"h_2 = {h} \\times \\frac{{{r2}}}{{{r1} + {r2}}} = {h2_str}",
                  f"The lower triangle takes fraction {r2}/({r1}+{r2}) of the total height {h}.",
                  eq=[f"{h} * {r2} / ({r1} + {r2})", h2_str]),
                S(f"\\text{{Area}}(\\triangle CDE) = \\frac{{1}}{{2}} \\times {b2} \\times {h2_str} = {area_str}",
                  "Calculate area of triangle $CDE$: $\\frac{1}{2} \\times \\text{base} \\times h_2$.",
                  val=area_str,
                  eq=[f"(1/2) * {b2} * ({h2_str})", area_str]),
            ],
        }

    if form == "side-triangle":
        h1_str = c["h1_str"]
        area_top = c["area_top"]
        area_str = c["area_side"]
        trap_area = c["trap_side"]
        abd_area = (b1 * h) // 2
        disp_area = f"\\frac{{{area_str.split('/')[0]}}}{{{area_str.split('/')[1]}}}" if "/" in area_str else area_str
        return {
            "form": "side-triangle",
            "category": "Interleaved Synthesis",
            "context": "Geometry: Trapezoid Flank Diagonal Triangle",
            "references": ["MTH-T01-C12-U03", "MTH-T01-C12-U04"],
            "prompt": f"In an isosceles trapezoid $ABCD$, the parallel bases are $AB = {b1}$ and $CD = {b2}$, and the non-parallel legs are $AD = BC = {leg}$. Diagonals $AC$ and $BD$ intersect at point $E$. Find the exact area of flank triangle $ADE$.",
            "display": f"\\text{{Trapezoid }} ABCD:\\ AB = {b1},\\ CD = {b2},\\ AD = BC = {leg} \\implies \\text{{Area}}(\\triangle ADE) = ?",
            "plainText": f"(1/2) * {b1} * sqrt({leg}^2 - (({b2} - {b1})/2)^2) * ({b2}/({b1} + {b2}))",
            "answerSpec": {"type": "expression", "value": area_str},
            "answerDisplay": disp_area,
            "answerPlain": area_str,
            "inputHint": "Enter exact fraction or integer e.g. 35/4 or 42",
            "checkpointHint": "Find total height $h$, compute $\\text{Area}(\\triangle ABD) = \\frac{1}{2}(AB)h$, and subtract $\\text{Area}(\\triangle ABE)$ found via similar triangles.",
            "commonTrapTag": "trapezoid-diagonal-bisect-trap",
            "verify": {"source": area_str, "trapValue": trap_area},
            "steps": [
                S(f"x = \\frac{{{b2} - {b1}}}{{2}} = {x}, \\quad h = \\sqrt{{{leg}^2 - {x}^2}} = {h}",
                  f"Use the Pythagorean theorem on the leg projection to find height $h = {h}$.",
                  eq=[f"sqrt({leg}**2 - {x}**2)", f"{h}"]),
                S(f"h_1 = {h} \\times \\frac{{{r1}}}{{{r1} + {r2}}} = {h1_str} \\implies \\text{{Area}}(\\triangle ABE) = \\frac{{1}}{{2}}({b1})({h1_str}) = {area_top}",
                  "Use similarity ratio $AB : CD$ to find height $h_1$ and area of upper triangle $ABE$.",
                  eq=[f"(1/2) * {b1} * ({h1_str})", area_top]),
                S(f"\\text{{Area}}(\\triangle ABD) = \\frac{{1}}{{2}}({b1})({h}) = {abd_area} \\implies \\text{{Area}}(\\triangle ADE) = {abd_area} - {area_top} = {area_str}",
                  "Subtract $\\text{Area}(\\triangle ABE)$ from $\\text{Area}(\\triangle ABD)$.",
                  val=area_str,
                  eq=[f"{abd_area} - ({area_top})", area_str]),
            ],
        }

    h1_str, area_str, trap_area = c["h1_str"], c["area_top"], c["trap_top"]
    disp_area = f"\\frac{{{area_str.split('/')[0]}}}{{{area_str.split('/')[1]}}}" if "/" in area_str else area_str

    return {
        "form": "direct",
        "category": "Interleaved Synthesis",
        "context": "Geometry: Trapezoid & Similar Triangles Partition",
        "references": ["MTH-T01-C12-U03", "MTH-T01-C12-U04"],
        "prompt": f"In an isosceles trapezoid $ABCD$, the parallel bases are $AB = {b1}$ and $CD = {b2}$, and the non-parallel legs are $AD = BC = {leg}$. Diagonals $AC$ and $BD$ intersect at point $E$. Find the exact area of triangle $ABE$.",
        "display": f"\\text{{Trapezoid }} ABCD:\\ AB = {b1},\\ CD = {b2},\\ AD = BC = {leg} \\implies \\text{{Area}}(\\triangle ABE) = ?",
        "plainText": f"(1/2) * {b1} * sqrt({leg}^2 - (({b2} - {b1})/2)^2) * ({b1}/({b1} + {b2}))",
        "answerSpec": {"type": "expression", "value": area_str},
        "answerDisplay": disp_area,
        "answerPlain": area_str,
        "inputHint": "Enter exact fraction or integer e.g. 35/4 or 42",
        "checkpointHint": "Find trapezoid height $h$ by projecting $AB$ onto $CD$ to get leg base offset $(CD - AB)/2$, then calculate $h = \\sqrt{\\text{leg}^2 - \\text{offset}^2}$. Use similar triangles $\\triangle ABE \\sim \\triangle CDE$ with ratio $AB : CD$ to partition the height.",
        "commonTrapTag": "trapezoid-diagonal-bisect-trap",
        "verify": {"source": area_str, "trapValue": trap_area},
        "steps": [
            S(f"x = \\frac{{{b2} - {b1}}}{{2}} = {x}, \\quad h = \\sqrt{{{leg}^2 - {x}^2}} = \\sqrt{{{leg*leg} - {x*x}}} = {h}",
              f"Symmetrical base offset gives a right triangle with hypotenuse {leg} and base {x}.",
              eq=[f"sqrt({leg}**2 - {x}**2)", f"{h}"]),
            S(f"\\triangle ABE \\sim \\triangle CDE \\implies \\frac{{h_1}}{{h_2}} = \\frac{{{b1}}}{{{b2}}} = \\frac{{{r1}}}{{{r2}}}",
              "Since $AB \\parallel CD$, alternate interior angles make $\\triangle ABE \\sim \\triangle CDE$.",
              eq=[f"{b1}/{b2}", f"{r1}/{r2}"]),
            S(f"h_1 = {h} \\times \\frac{{{r1}}}{{{r1} + {r2}}} = {h1_str}",
              f"The total height {h} is partitioned in ratio {r1}:{r2}.",
              eq=[f"{h} * {r1} / ({r1} + {r2})", h1_str]),
            S(f"\\text{{Area}}(\\triangle ABE) = \\frac{{1}}{{2}} \\times {b1} \\times {h1_str} = {area_str}",
              "Calculate area of triangle $ABE$: $\\frac{1}{2} \\times \\text{base} \\times h_1$.",
              val=area_str,
              eq=[f"(1/2) * {b1} * ({h1_str})", area_str]),
        ],
    }

# ---------------------------------------------------------------------------
# Template 7 (U05): Lunes of Hippocrates Invariant Area (Level 4 Applied Synthesis)
# ---------------------------------------------------------------------------
def t_lunes_of_hippocrates(rng, form=None):
    sides = [6, 8, 10, 12, 14, 16, 18, 20]
    s = rng.choice(sides)
    s2 = s * s
    circle_area_pi = s2 // 2
    single_lune = s2 // 4

    if form is None:
        form = rng.choice(["direct", "single-lune"])

    if form == "single-lune":
        return {
            "form": "single-lune",
            "category": "Interleaved Synthesis",
            "context": "Geometry: Single Lune of Hippocrates",
            "references": ["MTH-T01-C12-U04", "MTH-T01-C12-U05"],
            "prompt": f"A square of side length $s = {s}$ is inscribed inside a circle. Four congruent semicircles are drawn externally on the four sides of the square as diameters, forming four congruent crescent-shaped Lunes of Hippocrates outside the circumscribed circle. Find the exact area of ONE such lune.",
            "display": f"\\text{{Single Lune on square of side }} s = {s} \\implies \\text{{Area}}(\\text{{1 lune}}) = ?",
            "plainText": f"({s}^2) / 4",
            "answerSpec": {"type": "number", "value": str(single_lune)},
            "answerDisplay": str(single_lune),
            "answerPlain": str(single_lune),
            "inputHint": "Enter the integer area of one lune",
            "checkpointHint": "First find the total area of all four lunes by subtracting the circumscribed circle from the square plus four semicircles, then divide by 4 by symmetry.",
            "commonTrapTag": "pi-retained-in-lunes-trap",
            "verify": {"source": str(single_lune), "trapValue": str(s2)},
            "steps": [
                S(f"A_{{\\text{{square}}}} = {s}^2 = {s2}, \\quad A_{{\\text{{circle}}}} = \\pi({s//2}\\sqrt{{2}})^2 = {circle_area_pi}\\pi",
                  "Find the area of the inscribed square and circumscribed circle.",
                  eq=[f"({s//2}*sqrt(2))**2", str(circle_area_pi)]),
                S(f"A_{{\\text{{4 semicircles}}}} = 4 \\times \\left(\\frac{{1}}{{2}}\\pi ({s//2})^2\\right) = {circle_area_pi}\\pi",
                  f"The four outer semicircles have total area ${circle_area_pi}\\pi$, matching the circumscribed circle.",
                  eq=[f"4 * (1/2) * ({s//2})**2", str(circle_area_pi)]),
                S(f"A_{{\\text{{1 lune}}}} = \\frac{{A_{{\\text{{square}}}} + A_{{\\text{{4 semicircles}}}} - A_{{\\text{{circle}}}}}}{{4}} = \\frac{{{s2}}}{{4}} = {single_lune}",
                  "The $\\pi$ terms cancel out, leaving one-fourth of the square's area for each lune.",
                  val=str(single_lune),
                  eq=[f"{s2} / 4", str(single_lune)]),
            ],
        }

    return {
        "form": "direct",
        "category": "Interleaved Synthesis",
        "context": "Geometry: Circles & Lunes of Hippocrates",
        "references": ["MTH-T01-C12-U04", "MTH-T01-C12-U05"],
        "prompt": f"A square of side length $s = {s}$ is inscribed inside a circle. Four semicircles are drawn externally on the four sides of the square as diameters. The region outside the circumscribed circle but inside the four semicircles forms four crescent-shaped regions known as the Lunes of Hippocrates. Find the exact total area of all four lunes.",
        "display": f"\\text{{Lunes of Hippocrates on square of side }} s = {s} \\implies \\text{{Total Area}} = ?",
        "plainText": f"{s}^2 + {circle_area_pi}*pi - {circle_area_pi}*pi",
        "answerSpec": {"type": "number", "value": str(s2)},
        "answerDisplay": str(s2),
        "answerPlain": str(s2),
        "inputHint": "Enter the integer area (pi cancels out!)",
        "checkpointHint": "Calculate the total area of the four semicircles plus the area of the square, then subtract the area of the circumscribed circle. Notice how the terms involving $\\pi$ cancel out.",
        "commonTrapTag": "pi-retained-in-lunes-trap",
        "verify": {"source": str(s2), "trapValue": str(circle_area_pi)},
        "steps": [
            S(f"A_{{\\text{{square}}}} = {s}^2 = {s2}",
              f"The inscribed square has area ${s} \\times {s} = {s2}$.",
              eq=[f"{s}**2", str(s2)]),
            S(f"R = \\frac{{{s}\\sqrt{{2}}}}{{2}} = {s//2}\\sqrt{{2}} \\implies A_{{\\text{{circle}}}} = \\pi({s//2}\\sqrt{{2}})^2 = {circle_area_pi}\\pi",
              "The diameter of the circumscribed circle is the diagonal of the square.",
              eq=[f"({s//2}*sqrt(2))**2", str(circle_area_pi)]),
            S(f"A_{{\\text{{4 semicircles}}}} = 4 \\times \\left(\\frac{{1}}{{2}}\\pi ({s//2})^2\\right) = {circle_area_pi}\\pi",
              f"Each side of length {s} is the diameter of a semicircle with radius {s//2}.",
              eq=[f"4 * (1/2) * ({s//2})**2", str(circle_area_pi)]),
            S(f"A_{{\\text{{lunes}}}} = (A_{{\\text{{square}}}} + A_{{\\text{{4 semicircles}}}}) - A_{{\\text{{circle}}}} = ({s2} + {circle_area_pi}\\pi) - {circle_area_pi}\\pi = {s2}",
              "The area of the circumscribed circle perfectly cancels the area of the four semicircles, leaving exactly the area of the square!",
              val=str(s2),
              eq=[f"{s2} + {circle_area_pi} - {circle_area_pi}", str(s2)]),
        ],
    }

# ---------------------------------------------------------------------------
# Template 8 (U06): Conical Frustum Volume (Level 3 Trap & Diagnostic)
# ---------------------------------------------------------------------------
def t_conical_frustum_volume(rng, form=None):
    cases = [
        {"R": 9, "H": 12, "h": 4, "h_top": 8, "r_top": 6, "v_tot": 324, "v_top": 96, "v_coeff": 228, "trap_v": 225},
        {"R": 6, "H": 8, "h": 4, "h_top": 4, "r_top": 3, "v_tot": 96, "v_top": 12, "v_coeff": 84, "trap_v": 81},
        {"R": 12, "H": 16, "h": 4, "h_top": 12, "r_top": 9, "v_tot": 768, "v_top": 324, "v_coeff": 444, "trap_v": 441},
        {"R": 15, "H": 20, "h": 8, "h_top": 12, "r_top": 9, "v_tot": 1500, "v_top": 324, "v_coeff": 1176, "trap_v": 1152},
    ]
    c = rng.choice(cases)
    R, H, h, h_top, r_top = c["R"], c["H"], c["h"], c["h_top"], c["r_top"]
    v_tot, v_top, v_coeff, trap_v = c["v_tot"], c["v_top"], c["v_coeff"], c["trap_v"]

    if form is None:
        form = rng.choice(["direct", "from-diameter"])

    if form == "from-diameter":
        D = 2 * R
        return {
            "form": "from-diameter",
            "category": "Trap & Edge Case",
            "context": "Geometry: 3D Conical Frustum from Diameter",
            "references": ["MTH-T01-C12-U06"],
            "prompt": f"A right circular cone has base diameter $D = {D}$ and total height $H = {H}$. The cone is truncated by a plane parallel to the base at a distance of $h = {h}$ above the base, forming a conical frustum. Find the exact volume of this frustum in terms of $\\pi$.",
            "display": f"\\text{{Frustum of Cone: }} D = {D},\\ H = {H},\\ h = {h} \\implies V = ?",
            "plainText": f"(1/3)*pi*(({D}/2)^2)*{H} - (1/3)*pi*(({r_top})^2)*{h_top}",
            "answerSpec": {"type": "expression", "value": f"{v_coeff}*pi", "variables": ["pi"]},
            "answerDisplay": f"{v_coeff}\\pi",
            "answerPlain": f"{v_coeff} pi",
            "inputHint": "Enter exact form with pi, e.g. 150 pi or 150*pi",
            "checkpointHint": "Halve the base diameter to get $R = D/2$, use similar triangles to determine the top cone radius at height $H - h$, and subtract the top cone volume from the full cone volume.",
            "commonTrapTag": "frustum-cylinder-average-trap",
            "verify": {"source": f"{v_coeff}*pi", "trapValue": f"{trap_v}*pi"},
            "steps": [
                S(f"R = \\frac{{{D}}}{{2}} = {R}, \\quad h_{{\\text{{top}}}} = {H} - {h} = {h_top} \\implies r_{{\\text{{top}}}} = {R} \\times \\frac{{{h_top}}}{{{H}}} = {r_top}",
                  f"Convert diameter to radius $R = {R}$ and find top cone radius $r_{{\\text{{top}}}} = {r_top}$ by similar triangles.",
                  eq=[f"{R} * {h_top} / {H}", f"{r_top}"]),
                S(f"V_{{\\text{{total}}}} = \\frac{{1}}{{3}}\\pi ({R}^2)({H}) = {v_tot}\\pi, \\quad V_{{\\text{{top}}}} = \\frac{{1}}{{3}}\\pi ({r_top}^2)({h_top}) = {v_top}\\pi",
                  "Compute volumes of original cone and removed top cone via $V = \\frac{1}{3}\\pi r^2 h$.",
                  eq=[f"(1/3)*pi*({R}**2)*{H} - (1/3)*pi*({r_top}**2)*{h_top}", f"{v_coeff}*pi"]),
                S(f"V_{{\\text{{frustum}}}} = V_{{\\text{{total}}}} - V_{{\\text{{top}}}} = {v_tot}\\pi - {v_top}\\pi = {v_coeff}\\pi",
                  f"Subtract volumes: ${v_tot}\\pi - {v_top}\\pi = {v_coeff}\\pi$.",
                  val=f"{v_coeff}*pi",
                  eq=[f"{v_tot}*pi - {v_top}*pi", f"{v_coeff}*pi"]),
            ],
        }

    return {
        "form": "direct",
        "category": "Trap & Edge Case",
        "context": "Geometry: 3D Conical Frustum",
        "references": ["MTH-T01-C12-U06"],
        "prompt": f"A right circular cone has base radius $R = {R}$ and total height $H = {H}$. The cone is truncated by a plane parallel to the base at a distance of $h = {h}$ above the base, forming a conical frustum. Find the exact volume of this frustum in terms of $\\pi$.",
        "display": f"\\text{{Frustum of Cone: }} R = {R},\\ H = {H},\\ \\text{{height of frustum }} h = {h} \\implies V = ?",
        "plainText": f"(1/3)*pi*({R}^2)*{H} - (1/3)*pi*({r_top}^2)*{h_top}",
        "answerSpec": {"type": "expression", "value": f"{v_coeff}*pi", "variables": ["pi"]},
        "answerDisplay": f"{v_coeff}\\pi",
        "answerPlain": f"{v_coeff} pi",
        "inputHint": "Enter exact form with pi, e.g. 150 pi or 150*pi",
        "checkpointHint": "The top smaller cone has height $H - h$. Use similar triangles to determine the top radius $r_{\\text{top}}$, then subtract the volume of the smaller cone from the total volume of the original cone.",
        "commonTrapTag": "frustum-cylinder-average-trap",
        "verify": {"source": f"{v_coeff}*pi", "trapValue": f"{trap_v}*pi"},
        "steps": [
            S(f"h_{{\\text{{top}}}} = {H} - {h} = {h_top}, \\quad r_{{\\text{{top}}}} = {R} \\times \\frac{{{h_top}}}{{{H}}} = {r_top}",
              f"Similar triangles give top cone radius $r_{{\\text{{top}}}} = {r_top}$ at height {h_top}.",
              eq=[f"{R} * {h_top} / {H}", f"{r_top}"]),
            S(f"V_{{\\text{{total}}}} = \\frac{{1}}{{3}}\\pi ({R}^2)({H}) = {v_tot}\\pi, \\quad V_{{\\text{{top}}}} = \\frac{{1}}{{3}}\\pi ({r_top}^2)({h_top}) = {v_top}\\pi",
              "Compute volumes of original cone and removed top cone via $V = \\frac{1}{3}\\pi r^2 h$.",
              eq=[f"(1/3)*pi*({R}**2)*{H} - (1/3)*pi*({r_top}**2)*{h_top}", f"{v_coeff}*pi"]),
            S(f"V_{{\\text{{frustum}}}} = V_{{\\text{{total}}}} - V_{{\\text{{top}}}} = {v_tot}\\pi - {v_top}\\pi = {v_coeff}\\pi",
              f"Subtract volumes: ${v_tot}\\pi - {v_top}\\pi = {v_coeff}\\pi$.",
              val=f"{v_coeff}*pi",
              eq=[f"{v_tot}*pi - {v_top}*pi", f"{v_coeff}*pi"]),
        ],
    }

# ---------------------------------------------------------------------------
# Template 9 (U06): Find the Flaw in Composite Surface Area (Level 3 Diagnostic)
# ---------------------------------------------------------------------------
def t_find_flaw_composite_surface_area(rng, form=None):
    cases = [
        {"r": 3, "h": 5, "base": 9, "lat": 30, "wrong_dome": 27, "true_dome": 18, "wrong_sum": 66, "true_sum": 57},
        {"r": 4, "h": 6, "base": 16, "lat": 48, "wrong_dome": 48, "true_dome": 32, "wrong_sum": 112, "true_sum": 96},
        {"r": 5, "h": 7, "base": 25, "lat": 70, "wrong_dome": 75, "true_dome": 50, "wrong_sum": 170, "true_sum": 145},
        {"r": 2, "h": 4, "base": 4, "lat": 16, "wrong_dome": 12, "true_dome": 8, "wrong_sum": 32, "true_sum": 28},
        {"r": 6, "h": 8, "base": 36, "lat": 96, "wrong_dome": 108, "true_dome": 72, "wrong_sum": 240, "true_sum": 204},
    ]
    c = rng.choice(cases)
    r, h, base, lat = c["r"], c["h"], c["base"], c["lat"]
    wrong_dome, true_dome, wrong_sum, true_sum = c["wrong_dome"], c["true_dome"], c["wrong_sum"], c["true_sum"]

    if form == "flaw-line-2":
        flaw_line = 2
    elif form == "flaw-line-3":
        flaw_line = 3
    else:
        flaw_line = rng.choice([2, 3])

    src = f"{true_sum}*pi"
    line1_ok = f"SA = \\pi({r})^2 + 2\\pi({r})({h}) + 2\\pi({r})^2"
    line2_ok = f"= {base}\\pi + {lat}\\pi + {true_dome}\\pi"
    line3_ok = f"= {true_sum}\\pi"

    if flaw_line == 2:
        shown = [
            line1_ok,
            f"= {base}\\pi + {lat}\\pi + {wrong_dome}\\pi",
            f"= {wrong_sum}\\pi",
        ]
        vals = [src, f"{wrong_sum}*pi", None]
    else:
        shown = [
            line1_ok,
            line2_ok,
            f"= {wrong_sum}\\pi",
        ]
        vals = [src, src, f"{wrong_sum}*pi"]

    steps = [
        S(line1_ok, "Sum the exposed bottom circle $\\pi r^2$, lateral sleeve $2\\pi r h$, and curved hemisphere $2\\pi r^2$.", src),
        S(line2_ok, f"Evaluate each component: ${base}\\pi$, ${lat}\\pi$, and curved dome ${true_dome}\\pi$.", src),
        S(line3_ok, f"Combine like terms in $\\pi$ to obtain ${true_sum}\\pi$.", src),
    ]
    line_trap_map = {
        1: "volume-surface-area",
        2: "internal-boundary-double-count-trap",
        3: "arithmetic-slip",
    }
    prob = build_flaw_choice_problem(
        prompt=(
            f"A composite solid consists of a right circular cylinder with radius $r = {r}$ and height $h = {h}$, "
            f"capped at one end with a hemispherical dome of the same radius $r = {r}$. "
            f"A student calculates the total exterior surface area as shown. Which line contains the FIRST error?"
        ),
        shown_lines=shown,
        steps=steps,
        flaw_line=flaw_line,
        line_trap_map=line_trap_map,
        verify_source=src,
        vals=vals,
        common_trap_tag="internal-boundary-double-count-trap",
        variables=["pi"],
    )
    prob["context"] = "Geometry: 3D Solids Diagnostic Flaw"
    prob["references"] = ["MTH-T01-C12-U06"]
    prob["plainText"] = f"Find flaw in: SA for r={r}, h={h} (flaw-{flaw_line})"
    return prob

TEMPLATES = [
    {
        "key": "pythagoras-hypotenuse",
        "trapTag": "pythagoras-hypotenuse",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "GEO-RIGHT-TRIANGLE-HYP"},
            "reverse": {"level": 2, "skill": "GEO-RIGHT-TRIANGLE-LEG"},
            "contextual": {"level": 2, "skill": "GEO-RIGHT-TRIANGLE-APPLIED"},
        },
        "build": t_pythagoras_hypotenuse,
    },
    {
        "key": "trapezoid-area",
        "trapTag": "trapezoid-height",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "GEO-TRAPEZOID-AREA"},
            "reverse": {"level": 2, "skill": "GEO-TRAPEZOID-HEIGHT"},
        },
        "build": t_trapezoid_area,
    },
    {
        "key": "circle-area-pi",
        "trapTag": "circle-diameter-radius",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "GEO-CIRCLE-AREA-RADIUS"},
            "from-diameter": {"level": 2, "skill": "GEO-CIRCLE-AREA-DIAMETER"},
        },
        "build": t_circle_area_in_terms_of_pi,
    },
    {
        "key": "cylinder-volume",
        "trapTag": "volume-surface-area",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "GEO-CYLINDER-VOLUME-RADIUS"},
            "from-diameter": {"level": 2, "skill": "GEO-CYLINDER-VOLUME-DIAMETER"},
        },
        "build": t_cylinder_volume,
    },
    {
        "key": "altitude-inradius",
        "trapTag": "whole-triangle-inradius-confusion",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "GEO-RIGHT-TRIANGLE-APPLIED"},
            "missing-segment": {"level": 3, "skill": "GEO-RIGHT-TRIANGLE-APPLIED"},
        },
        "build": t_pythagoras_altitude_inradius,
    },
    {
        "key": "trapezoid-similar-triangles",
        "trapTag": "trapezoid-diagonal-bisect-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "GEO-TRAPEZOID-HEIGHT"},
            "bottom-triangle": {"level": 4, "skill": "GEO-TRAPEZOID-HEIGHT"},
            "side-triangle": {"level": 4, "skill": "GEO-TRAPEZOID-HEIGHT"},
        },
        "build": t_trapezoid_similar_triangles_area,
    },
    {
        "key": "lunes-hippocrates",
        "trapTag": "pi-retained-in-lunes-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "GEO-CIRCLE-AREA-DIAMETER"},
            "single-lune": {"level": 4, "skill": "GEO-CIRCLE-AREA-DIAMETER"},
        },
        "build": t_lunes_of_hippocrates,
    },
    {
        "key": "cone-frustum-volume",
        "trapTag": "frustum-cylinder-average-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "GEO-CYLINDER-VOLUME-DIAMETER"},
            "from-diameter": {"level": 3, "skill": "GEO-CYLINDER-VOLUME-DIAMETER"},
        },
        "build": t_conical_frustum_volume,
    },
    {
        "key": "find-flaw-composite-surface-area",
        "trapTag": "internal-boundary-double-count-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "flaw-line-2": {"level": 3, "skill": "GEO-CYLINDER-VOLUME-RADIUS"},
            "flaw-line-3": {"level": 3, "skill": "GEO-CYLINDER-VOLUME-RADIUS"},
        },
        "build": t_find_flaw_composite_surface_area,
    },
]
