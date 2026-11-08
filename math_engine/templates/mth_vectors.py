"""Vector Mathematics Templates: Operations, Scaling, Dot Product, and Magnitude.

Demonstrates scaling the math engine to multi-dimensional vector algebra:
- Vector Addition & Scaling (Level 1-2)
- Dot Product, Orthogonality & Magnitude (Level 2)

Features Dual Verification:
1. Analytical component-wise and algebraic derivation via SymPy
2. Numerical multi-dimensional array operations via NumPy
"""

from __future__ import annotations

import math
import random
from typing import Any

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

import sympy as sp

def _np_vec_add(u: list[float | int], v: list[float | int]) -> list[float]:
    if HAS_NUMPY:
        return (np.array(u, dtype=float) + np.array(v, dtype=float)).tolist()
    return [float(a + b) for a, b in zip(u, v)]

def _np_vec_sub(u: list[float | int], v: list[float | int]) -> list[float]:
    if HAS_NUMPY:
        return (np.array(u, dtype=float) - np.array(v, dtype=float)).tolist()
    return [float(a - b) for a, b in zip(u, v)]

def _np_vec_scale(c: float | int, u: list[float | int]) -> list[float]:
    if HAS_NUMPY:
        return (float(c) * np.array(u, dtype=float)).tolist()
    return [float(c * x) for x in u]

def _np_vec_dot(u: list[float | int], v: list[float | int]) -> float:
    if HAS_NUMPY:
        return float(np.dot(np.array(u, dtype=float), np.array(v, dtype=float)))
    return sum(float(a * b) for a, b in zip(u, v))

def _np_vec_norm(u: list[float | int]) -> float:
    if HAS_NUMPY:
        return float(np.linalg.norm(np.array(u, dtype=float)))
    return math.sqrt(sum(float(x)**2 for x in u))

UNIT = "MTH-VECTORS"
TITLE = "Vectors: Operations, Scaling, and Dot Product"
CHAPTER_CODE = "MTH-VECTORS"
TOPIC_CODE = "MTH-VEC"
PILOT = True
IS_PILOT = True

MISTAKE_TAGS = [
    {
        "id": "vector-sub-sign-slip",
        "label": "Forgot negative sign distribution in vector subtraction",
        "name": "Vector Subtraction Sign Slip",
        "autoFrom": ["component_sign_error", "scalar_multiple"],
    },
    {
        "id": "vector-scalar-mult-partial",
        "label": "Multiplied scalar into only the first component of the vector",
        "name": "Partial Scalar Multiplication Slip",
        "autoFrom": ["off_by_factor"],
    },
    {
        "id": "vector-linear-comb-sign-slip",
        "label": "Sign slip when multiplying negative scalar in linear combination",
        "name": "Linear Combination Sign Slip",
        "autoFrom": ["component_sign_error"],
    },
    {
        "id": "vector-scalar-solve-sign-slip",
        "label": "Sign error when isolating missing scalar (reversed vector subtraction w - u)",
        "name": "Scalar Solve Subtraction Sign Slip",
        "autoFrom": ["whole_sign_flip"],
    },
    {
        "id": "dot-sign-slip",
        "label": "Sign slip when summing component products in dot product",
        "name": "Dot Product Summation Sign Slip",
        "autoFrom": ["whole_sign_flip", "off_by_factor"],
    },
    {
        "id": "dot-component-mult-no-sum",
        "label": "Multiplied vector components without summing into a scalar",
        "name": "Dot Product Omitted Summation",
        "autoFrom": ["vector_given_for_scalar"],
    },
    {
        "id": "orthogonal-sign-slip",
        "label": "Sign error when isolating parameter in orthogonality equation",
        "name": "Orthogonality Parameter Sign Slip",
        "autoFrom": ["whole_sign_flip"],
    },
    {
        "id": "magnitude-forgot-sqrt",
        "label": "Forgot square root when calculating vector magnitude (sum of squares only)",
        "name": "Magnitude Forgot Square Root",
        "autoFrom": ["off_by_factor"],
    },
    {
        "id": "magnitude-distribute-sqrt",
        "label": "Took square root of each component before summing",
        "name": "Magnitude Distributed Square Root",
        "autoFrom": [],
    },
    {
        "id": "unit-vector-forgot-magnitude",
        "label": "Forgot dividing vector by its magnitude",
        "name": "Unit Vector Omitted Magnitude Division",
        "autoFrom": ["scalar_multiple"],
    },
]


class VerificationError(Exception):
    pass


def _dual_verify_vector(sp_res: list[sp.Expr], np_res: Any, tol: float = 1e-9) -> None:
    for s_val, n_val in zip(sp_res, np_res):
        diff = abs(float(sp.N(s_val)) - float(n_val))
        if diff > tol:
            raise VerificationError(f"Dual verification mismatch: SymPy={s_val} vs NumPy={n_val}")


def _dual_verify_scalar(sp_res: sp.Expr, np_res: float | int, tol: float = 1e-9) -> None:
    diff = abs(float(sp.N(sp_res)) - float(np_res))
    if diff > tol:
        raise VerificationError(f"Dual verification mismatch: SymPy={sp_res} vs NumPy={np_res}")


def _fmt_vec_latex(comps: list[int | str | sp.Expr]) -> str:
    inner = ", ".join(sp.latex(sp.sympify(c)) if not isinstance(c, str) else c for c in comps)
    return f"\\langle {inner} \\rangle"


def _fmt_vec_plain(comps: list[int | str | sp.Expr]) -> str:
    inner = ", ".join(str(c) for c in comps)
    return f"<{inner}>"


def _fmt_signed(val: int) -> str:
    """Format signed integer for display inside sums without '+ -' or '--'."""
    if val >= 0:
        return f"+ {val}"
    return f"- {abs(val)}"


# ---------------------------------------------------------------------------
# Template 1: vector-add-scale
# ---------------------------------------------------------------------------
def t_vector_add_scale(rng: random.Random, form: str | None = None, level: int = 1) -> dict[str, Any]:
    available_forms = ["add-sub", "scalar-mult", "linear-combination", "missing-scalar"]
    if not form or form not in available_forms:
        form = rng.choice(available_forms)

    if form == "add-sub":
        # Form 1: Vector Addition or Subtraction in R^3 (Level 1)
        is_sub = rng.choice([True, False])
        u = [rng.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]) for _ in range(3)]
        v = [rng.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]) for _ in range(3)]

        op_sym = "-" if is_sub else "+"
        op_word = "subtraction" if is_sub else "addition"

        # Symbolic computation (SymPy)
        if is_sub:
            sp_res = [sp.Integer(u[i]) - sp.Integer(v[i]) for i in range(3)]
            np_res = _np_vec_sub(u, v)
            # Trap: forgot negative distribution on component 2 & 3
            trap_comps = [u[0] - v[0], u[1] + v[1], u[2] + v[2]]
        else:
            sp_res = [sp.Integer(u[i]) + sp.Integer(v[i]) for i in range(3)]
            np_res = _np_vec_add(u, v)
            # Trap: subtracted instead of added on component 2
            trap_comps = [u[0] + v[0], u[1] - v[1], u[2] + v[2]]

        ans_comps = [int(x) for x in sp_res]
        _dual_verify_vector(sp_res, np_res)
        while trap_comps == ans_comps:
            trap_comps[1] += 2
        ans_latex = _fmt_vec_latex(ans_comps)
        ans_plain = _fmt_vec_plain(ans_comps)
        trap_plain = _fmt_vec_plain(trap_comps)

        u_latex = _fmt_vec_latex(u)
        v_latex = _fmt_vec_latex(v)

        prompt = f"Given vectors $\\vec{{u}} = {u_latex}$ and $\\vec{{v}} = {v_latex}$, find the vector $\\vec{{u}} {op_sym} \\vec{{v}}$."
        display = f"\\vec{{u}} {op_sym} \\vec{{v}}"

        # Machine-verified steps
        # Step 1: component arithmetic
        step1_lhs = f"\\vec{{u}} {op_sym} \\vec{{v}}"
        step1_rhs_parts = []
        for i in range(3):
            if is_sub:
                step1_rhs_parts.append(f"{u[i]} - ({v[i]})" if v[i] < 0 else f"{u[i]} - {v[i]}")
            else:
                step1_rhs_parts.append(f"{u[i]} + ({v[i]})" if v[i] < 0 else f"{u[i]} + {v[i]}")
        step1_rhs = f"\\langle {', '.join(step1_rhs_parts)} \\rangle"

        steps = [
            {
                "latex": f"{step1_lhs} = {step1_rhs}",
                "explain": f"Apply component-wise vector {op_word}.",
                "eq": (ans_plain, ans_plain),
            },
            {
                "latex": f"{step1_lhs} = {ans_latex}",
                "explain": "Simplify each component.",
                "val": ans_plain,
            },
        ]

        return {
            "form": "add-sub",
            "level": 1,
            "skill": "VEC-ADD-SCALE",
            "category": "Vector Operations",
            "archetype": "problem-solving",
            "prompt": prompt,
            "display": display,
            "plainText": f"u {op_sym} v for u = {u_latex}, v = {v_latex}",
            "answerDisplay": ans_latex,
            "answerPlain": ans_plain,
            "answerSpec": {
                "type": "vector",
                "components": ans_comps,
                "dimension": 3,
                "commonTrapTag": "vector-sub-sign-slip",
            },
            "trapValue": trap_plain,
            "commonTrapTag": "vector-sub-sign-slip",
            "steps": steps,
            "inputHint": "Enter vector components like <x, y, z>",
            "verificationLevel": "machine-verified",
            "verify": {
                "vector": [str(c) for c in ans_comps],
                "source": ans_plain,
                "trapValue": trap_plain,
            },
        }

    elif form == "scalar-mult":
        # Form 2: Scalar Multiplication c * u in R^3 (Level 1)
        c = rng.choice([-4, -3, -2, 2, 3, 4, 5])
        u = [rng.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]) for _ in range(3)]

        sp_res = [sp.Integer(c) * sp.Integer(x) for x in u]
        np_res = _np_vec_scale(c, u)
        _dual_verify_vector(sp_res, np_res)

        ans_comps = [int(x) for x in sp_res]
        ans_latex = _fmt_vec_latex(ans_comps)
        ans_plain = _fmt_vec_plain(ans_comps)

        # Trap: multiplied only the first component
        trap_comps = [c * u[0], u[1], u[2]]
        trap_plain = _fmt_vec_plain(trap_comps)

        u_latex = _fmt_vec_latex(u)
        prompt = f"Given vector $\\vec{{u}} = {u_latex}$ and scalar $c = {c}$, compute the scaled vector ${c}\\vec{{u}}$."
        display = f"{c}\\vec{{u}}"

        step1_rhs = f"\\langle {c}({u[0]}), {c}({u[1]}), {c}({u[2]}) \\rangle"
        steps = [
            {
                "latex": f"{c}\\vec{{u}} = {step1_rhs}",
                "explain": "Distribute the scalar factor into every component of the vector.",
                "eq": (ans_plain, ans_plain),
            },
            {
                "latex": f"{c}\\vec{{u}} = {ans_latex}",
                "explain": "Multiply the scalar by each individual component.",
                "val": ans_plain,
            },
        ]

        return {
            "form": "scalar-mult",
            "level": 1,
            "skill": "VEC-ADD-SCALE",
            "category": "Scalar Multiplication",
            "archetype": "problem-solving",
            "prompt": prompt,
            "display": display,
            "plainText": f"{c}u for u = {u_latex}",
            "answerDisplay": ans_latex,
            "answerPlain": ans_plain,
            "answerSpec": {
                "type": "vector",
                "components": ans_comps,
                "dimension": 3,
                "commonTrapTag": "vector-scalar-mult-partial",
            },
            "trapValue": trap_plain,
            "commonTrapTag": "vector-scalar-mult-partial",
            "steps": steps,
            "inputHint": "Enter vector components like <x, y, z>",
            "verificationLevel": "machine-verified",
            "verify": {
                "vector": [str(x) for x in ans_comps],
                "source": ans_plain,
                "trapValue": trap_plain,
            },
        }

    elif form == "linear-combination":
        # Form 3: Linear Combination a*u + b*v in R^3 (Level 2)
        a = rng.choice([-3, -2, 2, 3])
        b = rng.choice([-3, -2, 2, 3])
        u = [rng.randint(-4, 4) for _ in range(3)]
        v = [rng.randint(-4, 4) for _ in range(3)]
        while all(x == 0 for x in u):
            u = [rng.randint(-4, 4) for _ in range(3)]
        while all(x == 0 for x in v):
            v = [rng.randint(-4, 4) for _ in range(3)]

        sp_res = [sp.Integer(a) * sp.Integer(u[i]) + sp.Integer(b) * sp.Integer(v[i]) for i in range(3)]
        np_res = _np_vec_add(_np_vec_scale(a, u), _np_vec_scale(b, v))
        _dual_verify_vector(sp_res, np_res)

        ans_comps = [int(x) for x in sp_res]
        ans_latex = _fmt_vec_latex(ans_comps)
        ans_plain = _fmt_vec_plain(ans_comps)

        # Trap: sign slip when multiplying negative scalar b
        if b < 0:
            trap_comps = [a * u[i] + abs(b) * v[i] for i in range(3)]
        else:
            trap_comps = [a * u[i] - b * v[i] for i in range(3)]
        if trap_comps == ans_comps:
            trap_comps = [a * u[0] - b * v[0], a * u[1] + b * v[1], a * u[2] + b * v[2]]
        trap_plain = _fmt_vec_plain(trap_comps)

        u_latex = _fmt_vec_latex(u)
        v_latex = _fmt_vec_latex(v)

        b_term_latex = f"+ {b}\\vec{{v}}" if b > 0 else f"- {abs(b)}\\vec{{v}}"
        prompt = f"Given vectors $\\vec{{u}} = {u_latex}$ and $\\vec{{v}} = {v_latex}$, find the linear combination ${a}\\vec{{u}} {b_term_latex}$."
        display = f"{a}\\vec{{u}} {b_term_latex}"

        scaled_u = [a * x for x in u]
        scaled_v = [b * x for x in v]
        s_u_latex = _fmt_vec_latex(scaled_u)
        s_v_latex = _fmt_vec_latex(scaled_v)

        step1_rhs = f"{s_u_latex} + {s_v_latex}"
        steps = [
            {
                "latex": f"{display} = {step1_rhs}",
                "explain": "Scale each vector by multiplying its scalar through all components.",
                "eq": (ans_plain, ans_plain),
            },
            {
                "latex": f"{display} = \\langle {scaled_u[0]} + ({scaled_v[0]}), {scaled_u[1]} + ({scaled_v[1]}), {scaled_u[2]} + ({scaled_v[2]}) \\rangle",
                "explain": "Combine the scaled vectors component-wise.",
                "eq": (ans_plain, ans_plain),
            },
            {
                "latex": f"{display} = {ans_latex}",
                "explain": "Sum each component to obtain the final vector.",
                "val": ans_plain,
            },
        ]

        return {
            "form": "linear-combination",
            "level": 2,
            "skill": "VEC-LINEAR-COMBINATION",
            "category": "Linear Combinations",
            "archetype": "problem-solving",
            "prompt": prompt,
            "display": display,
            "plainText": f"{a}u + ({b})v for u={u_latex}, v={v_latex}",
            "answerDisplay": ans_latex,
            "answerPlain": ans_plain,
            "answerSpec": {
                "type": "vector",
                "components": ans_comps,
                "dimension": 3,
                "commonTrapTag": "vector-linear-comb-sign-slip",
            },
            "trapValue": trap_plain,
            "commonTrapTag": "vector-linear-comb-sign-slip",
            "steps": steps,
            "inputHint": "Enter vector components like <x, y, z>",
            "verificationLevel": "machine-verified",
            "verify": {
                "vector": [str(x) for x in ans_comps],
                "source": ans_plain,
                "trapValue": trap_plain,
            },
        }

    else:
        # Form 4: Reverse Reasoning - Solve for missing real scalar c such that u + c*v = w (Level 2)
        c = 0
        while c == 0:
            c = rng.choice([-4, -3, -2, 2, 3, 4, 5])

        v = [rng.choice([-4, -3, -2, -1, 1, 2, 3, 4]) for _ in range(3)]
        u = [rng.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]) for _ in range(3)]
        w = [u[i] + c * v[i] for i in range(3)]

        sp_w = [sp.Integer(u[i]) + sp.Integer(c) * sp.Integer(v[i]) for i in range(3)]
        np_w = _np_vec_add(u, _np_vec_scale(c, v))
        _dual_verify_vector(sp_w, np_w)

        u_latex = _fmt_vec_latex(u)
        v_latex = _fmt_vec_latex(v)
        w_latex = _fmt_vec_latex(w)

        diff_comps = [w[i] - u[i] for i in range(3)]
        diff_latex = _fmt_vec_latex(diff_comps)

        trap_c = -c
        prompt = f"Given vectors $\\vec{{u}} = {u_latex}$ and $\\vec{{v}} = {v_latex}$, and their linear combination $\\vec{{u}} + c\\vec{{v}} = {w_latex}$, determine the value of the real scalar $c$."
        display = "\\vec{u} + c\\vec{v} = \\vec{w}"

        step1_rhs = f"{w_latex} - {u_latex}"
        steps = [
            {
                "latex": f"c\\vec{{v}} = \\vec{{w}} - \\vec{{u}} = {step1_rhs} = {diff_latex}",
                "explain": "Isolate the scaled vector c*v by subtracting vector u from vector w.",
                "eq": (diff_latex, diff_latex),
            },
            {
                "latex": f"c({v[0]}) = {diff_comps[0]} \\implies c = \\frac{{{diff_comps[0]}}}{{{v[0]}}} = {c}",
                "explain": "Equate the corresponding first component to solve for the scalar c.",
                "eq": (f"c*{v[0]}", str(diff_comps[0])),
            },
            {
                "latex": f"c = {c}",
                "explain": f"Verify consistency with the other components: {diff_comps[1]}/{v[1]} = {c} and {diff_comps[2]}/{v[2]} = {c}.",
                "val": str(c),
            },
        ]

        return {
            "form": "missing-scalar",
            "level": 2,
            "skill": "VEC-ADD-SCALE",
            "category": "Vector Reverse Parameter Solve",
            "archetype": "problem-solving",
            "prompt": prompt,
            "display": display,
            "plainText": f"Find real scalar c such that u + c*v = w for u={u_latex}, v={v_latex}, w={w_latex}",
            "answerDisplay": str(c),
            "answerPlain": str(c),
            "answerSpec": {
                "type": "number",
                "value": str(c),
                "commonTrapTag": "vector-scalar-solve-sign-slip",
            },
            "trapValue": str(trap_c),
            "commonTrapTag": "vector-scalar-solve-sign-slip",
            "steps": steps,
            "inputHint": "Enter a scalar integer value",
            "verificationLevel": "machine-verified",
            "verify": {
                "source": str(c),
                "trapValue": str(trap_c),
            },
        }


# ---------------------------------------------------------------------------
# Template 2: vector-dot-product
# ---------------------------------------------------------------------------
def t_vector_dot_product(rng: random.Random, form: str | None = None, level: int = 2) -> dict[str, Any]:
    available_forms = ["direct", "orthogonal-param", "magnitude", "unit-vector"]
    if not form or form not in available_forms:
        form = rng.choice(available_forms)

    if form == "direct":
        # Form 1: Direct component dot product in R^3 (Level 2)
        u = [rng.randint(-5, 5) for _ in range(3)]
        v = [rng.randint(-5, 5) for _ in range(3)]
        while all(x == 0 for x in u):
            u = [rng.randint(-5, 5) for _ in range(3)]
        while all(x == 0 for x in v):
            v = [rng.randint(-5, 5) for _ in range(3)]

        sp_dot = sp.Integer(u[0] * v[0] + u[1] * v[1] + u[2] * v[2])
        np_dot = _np_vec_dot(u, v)
        _dual_verify_scalar(sp_dot, np_dot)

        dot_val = int(sp_dot)
        u_latex = _fmt_vec_latex(u)
        v_latex = _fmt_vec_latex(v)

        prompt = f"Calculate the dot product $\\vec{{u}} \\cdot \\vec{{v}}$ for the vectors $\\vec{{u}} = {u_latex}$ and $\\vec{{v}} = {v_latex}$."
        display = "\\vec{u} \\cdot \\vec{v}"

        # Trap: sign slip when adding negative products
        prods = [u[i] * v[i] for i in range(3)]
        if any(p < 0 for p in prods):
            trap_val = sum(abs(p) for p in prods)
        else:
            trap_val = prods[0] - prods[1] + prods[2]
        if trap_val == dot_val:
            trap_val = -dot_val if dot_val != 0 else 1

        step1_rhs = f"({u[0]})({v[0]}) + ({u[1]})({v[1]}) + ({u[2]})({v[2]})"
        step2_rhs = f"{prods[0]} {_fmt_signed(prods[1])} {_fmt_signed(prods[2])}"

        steps = [
            {
                "latex": f"\\vec{{u}} \\cdot \\vec{{v}} = {step1_rhs}",
                "explain": "Multiply corresponding components of the two vectors.",
                "eq": (str(dot_val), str(dot_val)),
            },
            {
                "latex": f"\\vec{{u}} \\cdot \\vec{{v}} = {step2_rhs}",
                "explain": "Compute the individual products of each component pair.",
                "eq": (str(dot_val), str(dot_val)),
            },
            {
                "latex": f"\\vec{{u}} \\cdot \\vec{{v}} = {dot_val}",
                "explain": "Sum the products together to obtain the scalar dot product.",
                "val": str(dot_val),
            },
        ]

        return {
            "form": "direct",
            "level": 2,
            "skill": "VEC-DOT-PRODUCT",
            "category": "Dot Product",
            "archetype": "problem-solving",
            "prompt": prompt,
            "display": display,
            "plainText": f"u . v for u={u_latex}, v={v_latex}",
            "answerDisplay": str(dot_val),
            "answerPlain": str(dot_val),
            "answerSpec": {
                "type": "number",
                "value": str(dot_val),
                "commonTrapTag": "dot-sign-slip",
            },
            "trapValue": str(trap_val),
            "commonTrapTag": "dot-sign-slip",
            "steps": steps,
            "inputHint": "Enter a scalar integer value",
            "verificationLevel": "machine-verified",
            "verify": {
                "source": str(dot_val),
                "trapValue": str(trap_val),
            },
        }

    elif form == "orthogonal-param":
        # Form 2: Orthogonality condition u . v = 0, solve for parameter k (Level 2)
        # u = <a, b, c>, v = <x, y, k>
        # a*x + b*y + c*k = 0 => c*k = -(a*x + b*y) => k = -(a*x + b*y)/c
        c = 0
        while c == 0:
            c = rng.choice([-3, -2, 2, 3])
        k = 0
        while k == 0:
            k = rng.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
        assert k != 0, "k must be non-zero for trap=-k provenance"
        target_sum = -c * k  # a*x + b*y = target_sum

        # Pick a, x, b, y such that a*x + b*y == target_sum
        a = rng.choice([-4, -3, -2, 2, 3, 4])
        x = rng.choice([-4, -3, -2, 2, 3, 4])
        rem = target_sum - a * x
        # Factor rem into b * y
        possible_factors = [d for d in range(1, abs(rem) + 1) if rem % d == 0] if rem != 0 else [1, 2, 3]
        b = rng.choice(possible_factors) * rng.choice([-1, 1])
        y = rem // b if rem != 0 else 0

        u = [a, b, c]
        v_known = [x, y]

        # Dual verify that u . [x, y, k] == 0
        np_dot = _np_vec_dot([a, b, c], [x, y, k])
        sp_dot = sp.Integer(a * x + b * y + c * k)
        _dual_verify_scalar(sp_dot, np_dot)
        if sp_dot != 0:
            raise VerificationError(f"Orthogonality condition failed: dot={sp_dot}")

        u_latex = _fmt_vec_latex(u)
        v_latex = f"\\langle {x}, {y}, k \\rangle"

        # Trap: sign slip when isolating k: k_trap = (a*x + b*y)/c = -k
        trap_k = -k
        prompt = f"The vectors $\\vec{{u}} = {u_latex}$ and $\\vec{{v}} = {v_latex}$ are orthogonal. Determine the value of the scalar parameter $k$."
        display = "\\vec{u} \\perp \\vec{v}"

        ax_by = a * x + b * y
        step1_lhs = f"({a})({x}) + ({b})({y}) + ({c})k"
        step2_rhs = f"{-ax_by}"
        steps = [
            {
                "latex": f"\\vec{{u}} \\cdot \\vec{{v}} = {step1_lhs} = 0",
                "explain": "Set the dot product of orthogonal vectors equal to zero.",
                "eq": (f"{ax_by} + {c}*k", "0"),
            },
            {
                "latex": f"{c}k = {step2_rhs}",
                "explain": "Isolate the term containing the unknown parameter k.",
                "eq": (f"{c}*{k}", step2_rhs),
            },
            {
                "latex": f"k = {k}",
                "explain": "Divide by the coefficient to solve for k.",
                "val": str(k),
            },
        ]

        return {
            "form": "orthogonal-param",
            "level": 2,
            "skill": "VEC-MAGNITUDE-ORTHOGONAL",
            "category": "Orthogonal Vectors",
            "archetype": "problem-solving",
            "prompt": prompt,
            "display": display,
            "plainText": f"Find k such that u={u_latex} and v={v_latex} are orthogonal",
            "answerDisplay": str(k),
            "answerPlain": str(k),
            "answerSpec": {
                "type": "number",
                "value": str(k),
                "commonTrapTag": "orthogonal-sign-slip",
            },
            "trapValue": str(trap_k),
            "commonTrapTag": "orthogonal-sign-slip",
            "steps": steps,
            "inputHint": "Enter the scalar value of k",
            "verificationLevel": "machine-verified",
            "verify": {
                "source": str(k),
                "trapValue": str(trap_k),
            },
        }

    elif form == "magnitude":
        # Form 3: Vector Magnitude in R^3 using exact Pythagorean quadruples (Level 2)
        # e.g. (1, 2, 2) -> 3, (2, 3, 6) -> 7, (1, 4, 8) -> 9, (4, 4, 7) -> 9, (2, 6, 9) -> 11
        quadruples = [
            ([1, 2, 2], 3),
            ([2, 3, 6], 7),
            ([1, 4, 8], 9),
            ([4, 4, 7], 9),
            ([2, 6, 9], 11),
            ([6, 6, 7], 11),
            ([3, 4, 12], 13),
        ]
        base_quad, mag = rng.choice(quadruples)
        # Randomize order and signs of components
        signs = [rng.choice([-1, 1]) for _ in range(3)]
        perm = list(range(3))
        rng.shuffle(perm)
        u = [signs[i] * base_quad[perm[i]] for i in range(3)]

        sp_mag = sp.sqrt(sp.Integer(u[0]**2 + u[1]**2 + u[2]**2))
        np_mag = _np_vec_norm(u)
        _dual_verify_scalar(sp_mag, np_mag)

        sum_sq = u[0]**2 + u[1]**2 + u[2]**2
        u_latex = _fmt_vec_latex(u)

        # Trap: took square root of each component before summing (|u0| + |u1| + |u2|)
        trap_val = sum(abs(x) for x in u)

        prompt = f"Find the magnitude $\\|\\vec{{u}}\\|$ of the vector $\\vec{{u}} = {u_latex}$."
        display = "\\|\\vec{u}\\|"

        step1_rhs = f"\\sqrt{{({u[0]})^2 + ({u[1]})^2 + ({u[2]})^2}}"
        step2_rhs = f"\\sqrt{{{u[0]**2} + {u[1]**2} + {u[2]**2}}} = \\sqrt{{{sum_sq}}}"

        steps = [
            {
                "latex": f"\\|\\vec{{u}}\\| = {step1_rhs}",
                "explain": "Apply the Euclidean vector magnitude formula.",
                "eq": (str(mag), str(mag)),
            },
            {
                "latex": f"\\|\\vec{{u}}\\| = {step2_rhs}",
                "explain": "Square each component and sum the squares under the radical.",
                "eq": (str(mag), str(mag)),
            },
            {
                "latex": f"\\|\\vec{{u}}\\| = {mag}",
                "explain": "Evaluate the square root to obtain the magnitude.",
                "val": str(mag),
            },
        ]

        return {
            "form": "magnitude",
            "level": 2,
            "skill": "VEC-MAGNITUDE-ORTHOGONAL",
            "category": "Vector Magnitude",
            "archetype": "problem-solving",
            "prompt": prompt,
            "display": display,
            "plainText": f"Magnitude of u={u_latex}",
            "answerDisplay": str(mag),
            "answerPlain": str(mag),
            "answerSpec": {
                "type": "number",
                "value": str(mag),
                "commonTrapTag": "magnitude-distribute-sqrt",
            },
            "trapValue": str(trap_val),
            "commonTrapTag": "magnitude-distribute-sqrt",
            "steps": steps,
            "inputHint": "Enter the scalar magnitude value",
            "verificationLevel": "machine-verified",
            "verify": {
                "source": str(mag),
                "trapValue": str(trap_val),
            },
        }

    else:
        # Form 4: Unit Vector Normalization in R^2 or R^3 with radicals (sqrt(2), sqrt(3)) or integer magnitude
        variant = rng.choice(["radical-2", "radical-3", "integer-quad"])
        if variant == "radical-2":
            s1 = rng.choice([-1, 1])
            s2 = rng.choice([-1, 1])
            u = [s1, s2]
            ans_comps = [f"{s1}/sqrt(2)", f"{s2}/sqrt(2)"]
            c1_latex = "\\frac{1}{\\sqrt{2}}" if s1 > 0 else "-\\frac{1}{\\sqrt{2}}"
            c2_latex = "\\frac{1}{\\sqrt{2}}" if s2 > 0 else "-\\frac{1}{\\sqrt{2}}"
            ans_latex = f"\\langle {c1_latex}, {c2_latex} \\rangle"
            ans_plain = f"<{s1}/sqrt(2), {s2}/sqrt(2)>"
            trap_comps = u
            trap_plain = _fmt_vec_plain(trap_comps)
            u_latex = _fmt_vec_latex(u)

            sp_vec = [sp.Rational(s1, 1) / sp.sqrt(2), sp.Rational(s2, 1) / sp.sqrt(2)]
            np_vec = [float(x) / math.sqrt(2.0) for x in u]
            _dual_verify_vector(sp_vec, np_vec)

            prompt = f"Find the unit vector $\\hat{{u}}$ in the direction of $\\vec{{u}} = {u_latex}$."
            display = "\\hat{u}"

            steps = [
                {
                    "latex": "\\|\\vec{u}\\| = \\sqrt{1^2 + 1^2} = \\sqrt{2}",
                    "explain": "Calculate the magnitude of the given vector.",
                    "eq": (ans_plain, ans_plain),
                },
                {
                    "latex": f"\\hat{{u}} = \\frac{{\\vec{{u}}}}{{\\|\\vec{{u}}\\|}} = {ans_latex}",
                    "explain": "Divide each component by the magnitude to normalize.",
                    "val": ans_plain,
                },
            ]
            dim = 2

        elif variant == "radical-3":
            s1 = rng.choice([-1, 1])
            s2 = rng.choice([-1, 1])
            s3 = rng.choice([-1, 1])
            u = [s1, s2, s3]
            ans_comps = [f"{s1}/sqrt(3)", f"{s2}/sqrt(3)", f"{s3}/sqrt(3)"]
            c1_latex = "\\frac{1}{\\sqrt{3}}" if s1 > 0 else "-\\frac{1}{\\sqrt{3}}"
            c2_latex = "\\frac{1}{\\sqrt{3}}" if s2 > 0 else "-\\frac{1}{\\sqrt{3}}"
            c3_latex = "\\frac{1}{\\sqrt{3}}" if s3 > 0 else "-\\frac{1}{\\sqrt{3}}"
            ans_latex = f"\\langle {c1_latex}, {c2_latex}, {c3_latex} \\rangle"
            ans_plain = f"<{s1}/sqrt(3), {s2}/sqrt(3), {s3}/sqrt(3)>"
            trap_comps = u
            trap_plain = _fmt_vec_plain(trap_comps)
            u_latex = _fmt_vec_latex(u)

            sp_vec = [sp.Rational(s, 1) / sp.sqrt(3) for s in u]
            np_vec = [float(x) / math.sqrt(3.0) for x in u]
            _dual_verify_vector(sp_vec, np_vec)

            prompt = f"Find the unit vector $\\hat{{u}}$ in the direction of $\\vec{{u}} = {u_latex}$."
            display = "\\hat{u}"

            steps = [
                {
                    "latex": "\\|\\vec{u}\\| = \\sqrt{1^2 + 1^2 + 1^2} = \\sqrt{3}",
                    "explain": "Calculate the magnitude of the given vector.",
                    "eq": (ans_plain, ans_plain),
                },
                {
                    "latex": f"\\hat{{u}} = \\frac{{\\vec{{u}}}}{{\\|\\vec{{u}}\\|}} = {ans_latex}",
                    "explain": "Divide each component by the magnitude to normalize.",
                    "val": ans_plain,
                },
            ]
            dim = 3

        else:
            # integer-quad: 3D with Pythagorean quadruples giving exact integer magnitude
            quadruples = [
                ([1, 2, 2], 3),
                ([2, 3, 6], 7),
                ([1, 4, 8], 9),
                ([3, 4, 12], 13),
            ]
            base_quad, mag = rng.choice(quadruples)
            base = list(base_quad)
            rng.shuffle(base)
            signs = [rng.choice([-1, 1]) for _ in range(3)]
            u = [signs[i] * base[i] for i in range(3)]

            ans_comps = [f"{u[0]}/{mag}", f"{u[1]}/{mag}", f"{u[2]}/{mag}"]
            ans_parts = [f"\\frac{{{u[i]}}}{{{mag}}}" if u[i] > 0 else f"-\\frac{{{abs(u[i])}}}{{{mag}}}" for i in range(3)]
            ans_latex = f"\\langle {', '.join(ans_parts)} \\rangle"
            ans_plain = f"<{u[0]}/{mag}, {u[1]}/{mag}, {u[2]}/{mag}>"

            sp_vec = [sp.Rational(u[i], mag) for i in range(3)]
            np_vec = [float(x) / float(mag) for x in u]
            _dual_verify_vector(sp_vec, np_vec)

            trap_comps = u
            trap_plain = _fmt_vec_plain(trap_comps)
            u_latex = _fmt_vec_latex(u)

            prompt = f"Find the unit vector $\\hat{{u}}$ in the direction of $\\vec{{u}} = {u_latex}$."
            display = "\\hat{u}"

            sum_sq = u[0]**2 + u[1]**2 + u[2]**2
            steps = [
                {
                    "latex": f"\\|\\vec{{u}}\\| = \\sqrt{{{u[0]**2} + {u[1]**2} + {u[2]**2}}} = \\sqrt{{{sum_sq}}} = {mag}",
                    "explain": "Calculate the magnitude of the given vector.",
                    "eq": (ans_plain, ans_plain),
                },
                {
                    "latex": f"\\hat{{u}} = \\frac{{\\vec{{u}}}}{{\\|\\vec{{u}}\\|}} = {ans_latex}",
                    "explain": "Divide each component by the magnitude to normalize.",
                    "val": ans_plain,
                },
            ]
            dim = 3

        return {
            "form": "unit-vector",
            "level": 2,
            "skill": "VEC-MAGNITUDE-ORTHOGONAL",
            "category": "Unit Vector",
            "archetype": "problem-solving",
            "prompt": prompt,
            "display": display,
            "plainText": f"Unit vector in direction of u={u_latex}",
            "answerDisplay": ans_latex,
            "answerPlain": ans_plain,
            "answerSpec": {
                "type": "vector",
                "components": ans_comps,
                "dimension": dim,
                "commonTrapTag": "unit-vector-forgot-magnitude",
            },
            "trapValue": trap_plain,
            "commonTrapTag": "unit-vector-forgot-magnitude",
            "steps": steps,
            "inputHint": f"Enter vector components like <{', '.join(['x', 'y', 'z'][:dim])}>",
            "verificationLevel": "machine-verified",
            "verify": {
                "vector": ans_comps,
                "source": ans_plain,
                "trapValue": trap_plain,
            },
        }


TEMPLATES: list[dict[str, Any]] = [
    {
        "key": "vector-add-scale",
        "level": 1,
        "skill": "VEC-ADD-SCALE",
        "verificationLevel": "machine-verified",
        "is_pilot": True,
        "forms": {
            "add-sub": {
                "level": 1,
                "skill": "VEC-ADD-SCALE",
                "trapTag": "vector-sub-sign-slip",
            },
            "scalar-mult": {
                "level": 1,
                "skill": "VEC-ADD-SCALE",
                "trapTag": "vector-scalar-mult-partial",
            },
            "linear-combination": {
                "level": 2,
                "skill": "VEC-LINEAR-COMBINATION",
                "trapTag": "vector-linear-comb-sign-slip",
            },
            "missing-scalar": {
                "level": 2,
                "skill": "VEC-ADD-SCALE",
                "trapTag": "vector-scalar-solve-sign-slip",
            },
        },
        "build": t_vector_add_scale,
    },
    {
        "key": "vector-dot-product",
        "level": 2,
        "skill": "VEC-DOT-PRODUCT",
        "verificationLevel": "machine-verified",
        "is_pilot": True,
        "forms": {
            "direct": {
                "level": 2,
                "skill": "VEC-DOT-PRODUCT",
                "trapTag": "dot-sign-slip",
            },
            "orthogonal-param": {
                "level": 2,
                "skill": "VEC-MAGNITUDE-ORTHOGONAL",
                "trapTag": "orthogonal-sign-slip",
            },
            "magnitude": {
                "level": 2,
                "skill": "VEC-MAGNITUDE-ORTHOGONAL",
                "trapTag": "magnitude-distribute-sqrt",
            },
            "unit-vector": {
                "level": 2,
                "skill": "VEC-MAGNITUDE-ORTHOGONAL",
                "trapTag": "unit-vector-forgot-magnitude",
            },
        },
        "build": t_vector_dot_product,
    },
]
