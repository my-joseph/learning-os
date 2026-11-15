"""Safe numeric expressions for figures: arithmetic, `^`/`**`, a few functions and piecewise rules, no `eval`.

Piecewise: `x^2 if x < 0 else 2*x + 1`, chained `-x if x < -1 else (1 if x <= 2 else x - 1)`; comparisons
may chain (`0 <= x < 2`) and combine with `and`/`or`.

Used by `figure_autofill` (vault `args` such as `sqrt(V/(pi*h))`) and by `figure_builder` (curves such as
`2*(x-1)^2 - 3`). Names other than the functions below must be supplied as variables.
"""

from __future__ import annotations

import ast
import math
import operator
import re

FUNCS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "exp": math.exp,
    "ln": math.log,
    "log": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "floor": math.floor,
    "ceil": math.ceil,
    "cbrt": lambda v: math.copysign(abs(v) ** (1 / 3), v),  # real cube root, also for negative x
    "min": min,
    "max": max,
}
CONSTS = {"pi": math.pi, "e": math.e}
_BIN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Not: operator.not_}
_CMP = {
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}


def names(expr: str) -> set[str]:
    """Variable names used by the expression (functions and constants excluded)."""
    return {n for n in re.findall(r"[A-Za-z_]\w*", expr) if n not in FUNCS and n not in CONSTS}


def compile_expr(expr: str) -> ast.Expression:
    """Parse once; raises ValueError for anything outside the allowed grammar."""
    tree = ast.parse(str(expr).replace("^", "**"), mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCS or node.keywords:
                raise ValueError(f"function not allowed in {expr!r}")
        elif not isinstance(
            node,
            (
                ast.Expression,
                ast.BinOp,
                ast.UnaryOp,
                ast.Constant,
                ast.Name,
                ast.Load,
                ast.IfExp,
                ast.Compare,
                ast.BoolOp,
                ast.And,
                ast.Or,
                *_BIN,
                *_UNARY,
                *_CMP,
            ),
        ):
            raise ValueError(f"{type(node).__name__} not allowed in {expr!r}")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ValueError(f"only numbers allowed in {expr!r}")
    return tree


def _ev(node: ast.AST, env: dict[str, float]) -> float:
    if isinstance(node, ast.Expression):
        return _ev(node.body, env)
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in env:
            return float(env[node.id])
        if node.id in CONSTS:
            return CONSTS[node.id]
        raise KeyError(node.id)
    if isinstance(node, ast.BinOp):
        return _BIN[type(node.op)](_ev(node.left, env), _ev(node.right, env))
    if isinstance(node, ast.UnaryOp):
        return _UNARY[type(node.op)](_ev(node.operand, env))
    if isinstance(node, ast.Call):
        return float(FUNCS[node.func.id](*(_ev(a, env) for a in node.args)))
    if isinstance(node, ast.IfExp):
        return _ev(node.body, env) if _ev(node.test, env) else _ev(node.orelse, env)
    if isinstance(node, ast.Compare):
        left = _ev(node.left, env)
        for op, comp in zip(node.ops, node.comparators):
            right = _ev(comp, env)
            if not _CMP[type(op)](left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.BoolOp):
        vals = (_ev(v, env) for v in node.values)
        return all(vals) if isinstance(node.op, ast.And) else any(vals)
    raise ValueError(f"unsupported node {type(node).__name__}")


def evaluate(expr: str | ast.Expression, env: dict[str, float] | None = None) -> float:
    """Value of the expression; raises ValueError/KeyError/ArithmeticError on bad input."""
    tree = expr if isinstance(expr, ast.Expression) else compile_expr(expr)
    val = _ev(tree, env or {})
    if isinstance(val, bool):
        raise ValueError("a condition is not a value; write `a if condition else b`")
    if isinstance(val, complex) or not math.isfinite(val):
        raise ArithmeticError("non-finite value")
    return val


def try_evaluate(expr: str, env: dict[str, float]) -> float | None:
    try:
        return evaluate(expr, env)
    except (ValueError, KeyError, ArithmeticError, TypeError, SyntaxError, OverflowError):
        return None
