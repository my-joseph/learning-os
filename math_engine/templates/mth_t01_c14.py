# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C14: Graphs (Coordinate Geometry & Linear Graphs)."""

from math_engine.templates._prealg_helpers import S

UNIT = "MTH-T01-C14"
TITLE = "Graphs"

MISTAKE_TAGS = [
    {
        "id": "c14-intercept-axis-swap-trap",
        "label": "Set x=0 instead of y=0 when solving for x-intercept",
        "name": "Coordinate Axis Intercept Swap",
        "autoFrom": [],
    },
    {
        "id": "c14-slope-run-over-rise-trap",
        "label": "Computed slope as run over rise (dx/dy) instead of rise over run (dy/dx)",
        "name": "Slope Reciprocal Inversion",
        "autoFrom": ["reciprocal"],
    },
    {
        "id": "c14-perpendicular-slope-sign-trap",
        "label": "Took reciprocal without negating sign for perpendicular line slope",
        "name": "Perpendicular Slope Sign Omission",
        "autoFrom": ["whole_sign_flip"],
    },
    {
        "id": "c14-lattice-endpoint-exclusion-trap",
        "label": "Forgot to add 1 when counting inclusive integer lattice points on a segment",
        "name": "Lattice Endpoint Fencepost Trap",
        "autoFrom": [],
    },
]


def t_c14_foundation(rng, form=None):
    if form not in ("direct", "intercept-sum"):
        form = rng.choice(["direct", "intercept-sum"])
    a = rng.choice([2, 3, 4, 5, 6])
    b = rng.choice([3, 4, 5, 6, 7])
    if a == b:
        b += 1
    k = rng.randint(2, 4)
    C = a * b * k
    x_int = C // a
    y_int = C // b
    if form == "intercept-sum":
        ans = x_int + y_int
        trap = a + b
        prompt = f"A line is given by the standard equation ${a}x + {b}y = {C}$ in the rectangular coordinate plane. Find the sum of its $x$-intercept value and its $y$-intercept value."
        disp = f"{a}x + {b}y = {C} \\implies a_{{\\text{{int}}}} + b_{{\\text{{int}}}} = ?"
        steps = [
            S(
                f"y = 0 \\implies {a}x = {C} \\implies a_{{\\text{{int}}}} = {x_int}",
                "Set $y = 0$ to find the $x$-intercept.",
                eq=[f"{C} / {a}", str(x_int)],
            ),
            S(
                f"x = 0 \\implies {b}y = {C} \\implies b_{{\\text{{int}}}} = {y_int}",
                "Set $x = 0$ to find the $y$-intercept.",
                eq=[f"{C} / {b}", str(y_int)],
            ),
            S(
                f"a_{{\\text{{int}}}} + b_{{\\text{{int}}}} = {x_int} + {y_int} = {ans}",
                "Add the two intercept coordinates.",
                val=str(ans),
                eq=[f"{x_int} + {y_int}", str(ans)],
            ),
        ]
    else:
        ans = x_int
        trap = y_int
        prompt = f"Find the $x$-coordinate of the $x$-intercept of the line ${a}x + {b}y = {C}$."
        disp = f"{a}x + {b}y = {C},\\quad y = 0 \\implies x = ?"
        steps = [
            S(
                f"{a}x + {b}(0) = {C}",
                "Substitute $y = 0$ into the linear equation to locate the $x$-intercept.",
                eq=[f"{a}*{x_int} + 0", str(C)],
            ),
            S(
                f"{a}x = {C} \\implies x = \\frac{{{C}}}{{{a}}}",
                "Divide both sides by the coefficient of $x$.",
                eq=[f"{C} / {a}", str(ans)],
            ),
            S(f"x = {ans}", "State the $x$-intercept value.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Graphs: Coordinate Axes & Linear Intercepts",
        "references": ["MTH-T01-C14-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{a}*x + {b}*y = {C} intercepts",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "To find the x-intercept set y = 0; to find the y-intercept set x = 0.",
        "commonTrapTag": "c14-intercept-axis-swap-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c14_reverse(rng, form=None):
    if form not in ("direct", "missing-coordinate"):
        form = rng.choice(["direct", "missing-coordinate"])
    x1 = rng.randint(-6, 3)
    y1 = rng.randint(-5, 5)
    dx = rng.choice([2, 3, 4, 5])
    m = rng.choice([-4, -3, -2, 2, 3, 4])
    x2 = x1 + dx
    y2 = y1 + m * dx
    if form == "missing-coordinate":
        ans = y2
        trap = y1 - m * dx
        prompt = f"The line passing through the points $({x1}, {y1})$ and $({x2}, k)$ has a slope of $m = {m}$. Find the missing coordinate $k$."
        disp = f"\\frac{{k - ({y1})}}{{{x2} - ({x1})}} = {m} \\implies k = ?"
        steps = [
            S(
                f"\\Delta x = {x2} - ({x1}) = {dx}",
                "Compute the horizontal run between the two points.",
                eq=[f"{x2} - ({x1})", str(dx)],
            ),
            S(
                f"k - ({y1}) = m \\cdot \\Delta x = ({m})({dx}) = {m * dx}",
                "Multiply the slope by the horizontal run to find the vertical rise.",
                eq=[f"({m}) * ({dx})", str(m * dx)],
            ),
            S(
                f"k = {y1} + ({m * dx}) = {ans}",
                "Add the vertical rise to the initial y-coordinate.",
                val=str(ans),
                eq=[f"{y1} + ({m * dx})", str(ans)],
            ),
        ]
    else:
        ans = m
        trap = -m
        prompt = f"Find the slope $m$ of the line passing through the points $({x1}, {y1})$ and $({x2}, {y2})$."
        disp = f"m = \\frac{{{y2} - ({y1})}}{{{x2} - ({x1})}}"
        steps = [
            S(
                f"\\Delta y = {y2} - ({y1}) = {y2 - y1}",
                "Compute the change in $y$ (vertical rise).",
                eq=[f"{y2} - ({y1})", str(y2 - y1)],
            ),
            S(
                f"\\Delta x = {x2} - ({x1}) = {dx}",
                "Compute the change in $x$ (horizontal run).",
                eq=[f"{x2} - ({x1})", str(dx)],
            ),
            S(
                f"m = \\frac{{{y2 - y1}}}{{{dx}}} = {ans}",
                "Divide the vertical rise by the horizontal run.",
                val=str(ans),
                eq=[f"({y2 - y1}) / {dx}", str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Graphs: Slope Formula & Missing Coordinate",
        "references": ["MTH-T01-C14-U04"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"slope ({x1},{y1}) to ({x2},{y2})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact signed integer value",
        "checkpointHint": "Use the slope formula m = (y2 - y1) / (x2 - x1) keeping the subtraction order consistent in numerator and denominator.",
        "commonTrapTag": "c14-slope-run-over-rise-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c14_trap(rng, form=None):
    if form not in ("direct", "collinear-parameter", "bisector-intercept"):
        form = rng.choice(["direct", "collinear-parameter", "bisector-intercept"])
    if form == "collinear-parameter":
        cases = [
            (1, 2, 3, 6, 5, 10, 4, 2),
            (2, 1, 5, 7, 8, 13, 6, 3),
            (-1, 3, 2, 9, 5, 15, 7, 4),
            (1, -2, 4, 7, 6, 13, 9, 5),
            (0, 4, 3, 10, 7, 18, 12, 8),
        ]
        x1, y1, x2, y2, x3, y3, offset, k_ans = rng.choice(cases)
        m = (y2 - y1) // (x2 - x1)
        c_const = y3 - k_ans
        ans = k_ans
        trap = -k_ans
        c_sign = "+" if c_const >= 0 else "-"
        c_abs = abs(c_const)
        prompt = f"Three distinct points $A({x1}, {y1})$, $B({x2}, {y2})$, and $C({x3}, k {c_sign} {c_abs})$ are collinear in the coordinate plane. Find the exact value of $k$."
        disp = f"m_{{AB}} = m_{{BC}} \\implies \\frac{{{y2} - ({y1})}}{{{x2} - ({x1})}} = \\frac{{(k {c_sign} {c_abs}) - ({y2})}}{{{x3} - ({x2})}}"
        steps = [
            S(
                f"m_{{AB}} = \\frac{{{y2} - ({y1})}}{{{x2} - ({x1})}} = {m}",
                "Calculate the slope of segment $AB$.",
                eq=[f"({y2} - ({y1})) / ({x2} - ({x1}))", str(m)],
            ),
            S(
                f"y_C = {y2} + {m}({x3} - {x2}) = {y3}",
                "Use collinearity to find the required y-coordinate of point $C$.",
                eq=[f"{y2} + {m}*({x3} - {x2})", str(y3)],
            ),
            S(
                f"k {c_sign} {c_abs} = {y3} \\implies k = {ans}",
                "Solve the linear relation for parameter $k$.",
                val=str(ans),
                eq=[f"{y3} - ({c_const})", str(ans)],
            ),
        ]
    elif form == "bisector-intercept":
        cases = [
            (-2, 1, 6, 5, 2, 3, 2, -2, 7, -1),
            (0, 2, 4, 4, 2, 3, 2, -2, 7, -1),
            (-4, 0, 4, 4, 0, 2, 2, -2, 2, 4),
            (2, 1, 6, 3, 4, 2, 2, -2, 10, -6),
            (-2, -1, 6, 3, 2, 1, 2, -2, 5, -3),
        ]
        x1, y1, x2, y2, mx, my, inv_m, perp_m, ans, trap = rng.choice(cases)
        prompt = f"Segment $AB$ has endpoints $A({x1}, {y1})$ and $B({x2}, {y2})$. Line $L$ is the perpendicular bisector of segment $AB$. Find the $y$-intercept $b$ of line $L$ (where $L$ is written as $y = mx + b$)."
        disp = f"A({x1}, {y1}),\\ B({x2}, {y2}) \\implies L \\perp AB \\text{{ at }} M({mx}, {my}) \\implies b = ?"
        steps = [
            S(
                f"M = \\left(\\frac{{{x1} + {x2}}}{{2}}, \\frac{{{y1} + {y2}}}{{2}}\\right) = ({mx}, {my})",
                "Find the midpoint $M$ of segment $AB$.",
                eq=[f"({x1} + {x2}) / 2", str(mx)],
            ),
            S(
                f"m_{{AB}} = \\frac{{{y2} - ({y1})}}{{{x2} - ({x1})}} = \\frac{{1}}{{2}} \\implies m_L = -2",
                "Take the negative reciprocal of $m_{AB} = 1/2$ to get perpendicular slope $m_L = -2$.",
                eq=["-1 / (1/2)", "-2"],
            ),
            S(
                f"b = y_M - m_L x_M = {my} - (-2)({mx}) = {ans}",
                "Substitute midpoint $M$ into $y = m_L x + b$ to solve for $b$.",
                val=str(ans),
                eq=[f"{my} - (-2)*({mx})", str(ans)],
            ),
        ]
    else:
        cases = [
            (1, 2, 7, 4, 4, 3, -3, 15, -9),
            (2, 1, 8, 3, 5, 2, -3, 17, -13),
            (-1, 3, 5, 5, 2, 4, -3, 10, -2),
            (0, 1, 6, 3, 3, 2, -3, 11, -7),
            (3, 2, 9, 4, 6, 3, -3, 21, -15),
        ]
        x1, y1, x2, y2, mx, my, perp_m, ans, trap = rng.choice(cases)
        prompt = f"Line $L$ is the perpendicular bisector of the segment connecting $P({x1}, {y1})$ and $Q({x2}, {y2})$. If line $L$ has equation $y = mx + b$, find the value of $b$."
        disp = f"P({x1}, {y1}),\\ Q({x2}, {y2}) \\implies y = mx + b \\implies b = ?"
        steps = [
            S(
                f"M = \\left(\\frac{{{x1} + {x2}}}{{2}}, \\frac{{{y1} + {y2}}}{{2}}\\right) = ({mx}, {my})",
                "Compute the midpoint $M$ of segment $PQ$.",
                eq=[f"({y1} + {y2}) / 2", str(my)],
            ),
            S(
                f"m_{{PQ}} = \\frac{{{y2} - {y1}}}{{{x2} - ({x1})}} = \\frac{{1}}{{3}} \\implies m_L = -3",
                "Compute $m_{PQ} = 1/3$ and take its negative reciprocal $m_L = -3$.",
                eq=["-1 / (1/3)", "-3"],
            ),
            S(
                f"b = {my} - (-3)({mx}) = {ans}",
                "Substitute the midpoint coordinates to find the y-intercept $b$.",
                val=str(ans),
                eq=[f"{my} - (-3)*({mx})", str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Graphs: Perpendicular Bisector & Collinearity Traps",
        "references": ["MTH-T01-C14-U01", "MTH-T01-C14-U04"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"coord trap {form} {ans}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact signed integer value",
        "checkpointHint": "For perpendicular lines use the negative reciprocal slope -1/m; for collinear points equate the slopes of adjacent segments.",
        "commonTrapTag": "c14-perpendicular-slope-sign-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c14_synthesis(rng, form=None):
    if form not in ("direct", "reflection-point", "lattice-points"):
        form = rng.choice(["direct", "reflection-point", "lattice-points"])
    if form == "reflection-point":
        cases = [
            (2, 1, 6, 3, 2, 5, 5, 9),
            (2, 3, 8, 4, 2, 7, 6, 12),
            (2, -1, 7, 3, 3, 5, 6, 10),
            (2, 5, 7, 4, 1, 7, 5, 11),
            (2, -3, 8, 3, 4, 5, 7, 11),
        ]
        m, b, xp, yp, xq, yq, ans, trap = rng.choice(cases)
        b_sign = "+" if b >= 0 else "-"
        b_abs = abs(b)
        prompt = f"Point $P({xp}, {yp})$ is reflected across the line $L: y = {m}x {b_sign} {b_abs}$ to its mirror image $P'(x', y')$. Find the sum of coordinates $x' + y'$ of the reflected point."
        disp = f"P({xp}, {yp}) \\xrightarrow{{\\text{{reflect across }} y = {m}x {b_sign} {b_abs}}} P'(x', y') \\implies x' + y' = ?"
        steps = [
            S(
                f"M = \\left(\\frac{{{xp} + x'}}{{2}}, \\frac{{{yp} + y'}}{{2}}\\right) = ({xq}, {yq}) \\text{{ lies on }} L",
                "The foot of the perpendicular from $P$ to line $L$ is the midpoint $M$ of $PP'$.",
                eq=[f"{m}*{xq} + ({b})", str(yq)],
            ),
            S(
                f"x' = 2({xq}) - {xp} = {2 * xq - xp}, \\quad y' = 2({yq}) - ({yp}) = {2 * yq - yp}",
                "Double the midpoint coordinates and subtract the original coordinates of $P$.",
                eq=[f"(2*{xq} - {xp}) + (2*{yq} - ({yp}))", str(ans)],
            ),
            S(
                f"x' + y' = {2 * xq - xp} + ({2 * yq - yp}) = {ans}",
                "Sum the coordinates of the reflected image $P'$.",
                val=str(ans),
                eq=[str(ans), str(ans)],
            ),
        ]
    elif form == "lattice-points":
        cases = [
            (3, 4, 60, 20, 15, 5, 6, 5),
            (2, 5, 70, 35, 14, 7, 8, 7),
            (4, 3, 72, 18, 24, 6, 7, 6),
            (5, 6, 120, 24, 20, 4, 5, 4),
            (3, 5, 90, 30, 18, 6, 7, 6),
        ]
        a, b, C, x_int, y_int, g, ans, trap = rng.choice(cases)
        prompt = f"Line $L$ has equation ${a}x + {b}y = {C}$. How many lattice points $(x, y)$ (points where both $x$ and $y$ are integers) lie on the line segment of $L$ in the first quadrant ($x \\ge 0,\\ y \\ge 0$, including both axis intercepts)?"
        disp = f"{a}x + {b}y = {C},\\quad x, y \\in \\mathbb{{Z}}_{{\\ge 0}} \\implies N_{{\\text{{lattice}}}} = ?"
        steps = [
            S(
                f"A = ({x_int}, 0), \\quad B = (0, {y_int})",
                "Find the x-intercept and y-intercept bounding the first-quadrant segment.",
                eq=[f"{C} / {a}", str(x_int)],
            ),
            S(
                f"\\gcd(|\\Delta x|, |\\Delta y|) = \\gcd({x_int}, {y_int}) = {g}",
                "Compute the greatest common divisor of the horizontal and vertical spans.",
                eq=[str(g), str(g)],
            ),
            S(
                f"N_{{\\text{{lattice}}}} = \\gcd({x_int}, {y_int}) + 1 = {g} + 1 = {ans}",
                "Add 1 to include both endpoints of the segment.",
                val=str(ans),
                eq=[f"{g} + 1", str(ans)],
            ),
        ]
    else:
        cases = [
            (2, 6, -2, 18, 3, 12, -3, 9, 72, 144),
            (3, 6, -2, 16, 2, 12, -2, 8, 60, 120),
            (2, 8, -2, 16, 2, 12, -4, 8, 72, 144),
            (3, 9, -3, 27, 3, 18, -3, 9, 108, 216),
            (4, 8, -2, 20, 2, 16, -2, 10, 96, 192),
        ]
        m1, b1, m2, b2, xi, yi, x1_int, x2_int, _, _ = rng.choice(cases)
        base_len = x2_int - x1_int
        ans = (base_len * yi) // 2
        trap = base_len * yi
        prompt = f"In the rectangular coordinate plane, line $L_1$ is given by $y = {m1}x + {b1}$ and line $L_2$ is given by $y = {m2}x + {b2}$. Find the exact area of the triangle bounded by $L_1$, $L_2$, and the $x$-axis ($y = 0$)."
        disp = f"L_1: y = {m1}x + {b1},\\quad L_2: y = {m2}x + {b2},\\quad y = 0 \\implies \\text{{Area}} = ?"
        steps = [
            S(
                f"{m1}x + {b1} = {m2}x + {b2} \\implies x = {xi},\\ y = {yi}",
                "Find the intersection vertex of $L_1$ and $L_2$, which gives triangle height $h = y_I$.",
                eq=[f"{m1}*{xi} + {b1}", str(yi)],
            ),
            S(
                f"x_1 = {x1_int}, \\quad x_2 = {x2_int} \\implies \\text{{base}} = {x2_int} - ({x1_int}) = {base_len}",
                "Find the x-intercepts of both lines and subtract to get the base along the x-axis.",
                eq=[f"{x2_int} - ({x1_int})", str(base_len)],
            ),
            S(
                f"\\text{{Area}} = \\frac{{1}}{{2}} \\times {base_len} \\times {yi} = {ans}",
                "Compute half the product of the base and height.",
                val=str(ans),
                eq=[f"(1/2) * {base_len} * {yi}", str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Graphs: Coordinate Geometry Multi-Concept Synthesis",
        "references": ["MTH-T01-C14-U02", "MTH-T01-C14-U03", "MTH-T01-C14-U04"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"coord synthesis {form} {ans}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact signed integer value",
        "checkpointHint": "Combine intersection coordinates, perpendicular slope relations, or greatest common divisor step counts to determine the geometric invariant.",
        "commonTrapTag": "c14-lattice-endpoint-exclusion-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


TEMPLATES = [
    {
        "key": "c14-midpoint-intercepts",
        "trapTag": "c14-intercept-axis-swap-trap",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C14-INTERCEPTS"},
            "intercept-sum": {"level": 1, "skill": "MTH-PREALG-C14-INTERCEPTS"},
        },
        "build": t_c14_foundation,
    },
    {
        "key": "c14-slope-two-points",
        "trapTag": "c14-slope-run-over-rise-trap",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C14-SLOPE"},
            "missing-coordinate": {"level": 2, "skill": "MTH-PREALG-C14-SLOPE"},
        },
        "build": t_c14_reverse,
    },
    {
        "key": "c14-perpendicular-bisector-trap",
        "trapTag": "c14-perpendicular-slope-sign-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C14-PERP-TRAP"},
            "collinear-parameter": {"level": 3, "skill": "MTH-PREALG-C14-PERP-TRAP"},
            "bisector-intercept": {"level": 3, "skill": "MTH-PREALG-C14-PERP-TRAP"},
        },
        "build": t_c14_trap,
    },
    {
        "key": "c14-coordinate-geometry-synthesis",
        "trapTag": "c14-lattice-endpoint-exclusion-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C14-SYNTHESIS"},
            "reflection-point": {"level": 4, "skill": "MTH-PREALG-C14-SYNTHESIS"},
            "lattice-points": {"level": 4, "skill": "MTH-PREALG-C14-SYNTHESIS"},
        },
        "build": t_c14_synthesis,
    },
]
