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
]
