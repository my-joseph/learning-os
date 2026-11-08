# -*- coding: utf-8 -*-
"""
Flexible, type-driven answer checker for Math drills (SymPy).

Usage (CLI, used by the Studio API):
    echo '{"answerSpec": {...}, "input": "3 - 4i"}' | .venv/bin/python -m math_engine.answer_check

Supported answerSpec types (extensible - add a new checker function + register it in CHECKERS):
    number          {"type": "number", "value": "3/4", "forms": ["reduced_fraction", "exact"]}
    complex         {"type": "complex", "value": "-1 + 2*I", "forms": ["a+bi"]}
    expression      {"type": "expression", "value": "x**2 - 1", "variables": ["x"], "forms": ["factored"]}
    solution_set    {"type": "solution_set", "values": ["-2 + 3*I", "-2 - 3*I"], "variable": "x"}
    tuple           {"type": "tuple", "values": ["5", "3"], "labels": ["x", "y"], "acceptComplex": true}
    choice          {"type": "choice", "correct": "B"}
    text            {"type": "text", "accepted": ["server-only"]}

Result:
    {
      "verdict": "correct" | "equivalent_not_in_form" | "partial" | "incorrect" | "parse_error",
      "message": "...",                 # plain English, may contain $...$ inline math
      "components": [{"label": "...", "ok": true}],
      "diagnostics": [{"code": "...", "message": "..."}]
    }
Diagnostic codes are generic (whole_sign_flip, imag_sign_flip, real_sign_flip, swapped_parts, reciprocal,
off_by_factor, constant_offset, rounding, missing_solution, extra_solution, unseparated, complex_denominator,
unexpanded_power, uncombined_terms, unreduced_fraction, radical_denominator, decimal_not_exact, not_expanded,
not_factored). Each drill maps codes to its own mistake tags via mistakeTags[].autoFrom.
"""
import ast
import io
import json
import random
import re
import signal
import sys
import threading
import tokenize

import sympy as sp

MAX_INPUT_LEN = 200

WHITELIST_FUNCS = {
    "sqrt": sp.sqrt,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "ln": sp.log,
    "log": sp.log,
    "abs": sp.Abs,
    "Abs": sp.Abs,
    "exp": sp.exp,
    "re": sp.re,
    "im": sp.im,
    "conjugate": sp.conjugate,
}

# Functions allowed only for trusted internal evaluation (e.g. verify.source, step validation)
TRUSTED_INTERNAL_FUNCS = {
    **WHITELIST_FUNCS,
    "diff": sp.diff,
}

# Vetted extra functions that individual problem answerSpec may optionally whitelist via allowFuncs
VETTED_EXTRA_FUNCS = {
    "diff": sp.diff,
}

WHITELIST_CONSTANTS = {
    "pi": sp.pi,
    "e": sp.E,
    "oo": sp.oo,
    "i": sp.I,
    "I": sp.I,
}


class SafeParseError(ValueError):
    """Raised when an expression violates security constraints or cannot be parsed safely."""
    pass


class EqualTimeoutError(BaseException):
    """Raised when expression equality evaluation exceeds time budget."""
    pass


def _run_with_timeout(func, args=(), kwargs=None, timeout_sec=1.5):
    kwargs = kwargs or {}
    timer_active = False
    if hasattr(signal, "SIGALRM") and threading.current_thread() is threading.main_thread():
        rem, _ = signal.getitimer(signal.ITIMER_REAL)
        timer_active = (rem > 0)

    if hasattr(signal, "SIGALRM") and threading.current_thread() is threading.main_thread() and not timer_active:
        def _handler(signum, frame):
            raise EqualTimeoutError("is_equal computation timed out")

        old_handler = signal.signal(signal.SIGALRM, _handler)
        signal.setitimer(signal.ITIMER_REAL, timeout_sec)
        try:
            return func(*args, **kwargs)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        res = [None]
        err = [None]
        done = threading.Event()

        def _worker():
            try:
                res[0] = func(*args, **kwargs)
            except BaseException as e:
                err[0] = e
            finally:
                done.set()

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        finished = done.wait(timeout=timeout_sec)
        if not finished:
            raise EqualTimeoutError("is_equal computation timed out")
        if err[0] is not None:
            raise err[0]
        return res[0]

FORM_MESSAGES = {
    "unseparated": "The value is correct, but it is not separated into standard form $a + bi$ (distribute or split the fraction).",
    "complex_denominator": "The value is correct, but $i$ still appears in a denominator. Multiply by the conjugate.",
    "unexpanded_power": "The value is correct, but a power of $i$ (such as $i^2$) or a product is left unsimplified.",
    "uncombined_terms": "The value is correct, but like terms are not combined.",
    "unreduced_fraction": "The value is correct, but a fraction is not reduced to lowest terms.",
    "radical_denominator": "The value is correct, but the denominator still contains a radical (rationalize it).",
    "decimal_not_exact": "The value matches numerically, but an exact answer (fraction / radical) is required, not a decimal.",
    "not_expanded": "The expression is equivalent, but it is not fully expanded.",
    "not_factored": "The expression is equivalent, but it is not fully factored.",
    "unsimplified_radical": "The value is correct, but a radical is not simplified (extract perfect-square factors, e.g. $\\sqrt{48} = 4\\sqrt{3}$).",
}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def _normalize(raw: str) -> str:
    s = (raw or "").strip()
    repl = {
        "\u2212": "-", "\u2013": "-", "\u00d7": "*", "\u00b7": "*", "\u22c5": "*", "\u00f7": "/",
        "\u03c0": "pi", "\u221e": "oo", "**": "^",
        "\u27e8": "<", "\u27e9": ">", "\u3008": "<", "\u3009": ">",
    }
    for k, v in repl.items():
        s = s.replace(k, v)
    s = s.replace("^", "**")
    s = re.sub(r"\u221a\s*\(", "sqrt(", s)              # √(…)
    s = re.sub(r"\u221a\s*([0-9.]+|[a-zA-Z])", r"sqrt(\1)", s)  # √12, √x
    s = re.sub(r"sqrt\s*([0-9]+)", r"sqrt(\1)", s)       # sqrt12
    s = s.replace("{", "(").replace("}", ")").replace("[", "(").replace("]", ")")
    return s


def _insert_implicit_mul(expr_str: str) -> str:
    try:
        tokens = list(tokenize.tokenize(io.BytesIO(expr_str.encode("utf-8")).readline))
    except Exception as e:
        raise SafeParseError(f"Could not tokenize expression: {e}")
    filtered = [t for t in tokens if t.type not in (tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE)]

    new_tokens = []
    for i in range(len(filtered)):
        new_tokens.append(filtered[i].string)
        if i + 1 < len(filtered):
            t1, t2 = filtered[i], filtered[i + 1]
            t1_is_num = (t1.type == tokenize.NUMBER)
            t1_is_name = (t1.type == tokenize.NAME)
            t1_is_rparen = (t1.type == tokenize.OP and t1.string in (")", "]"))

            t2_is_num = (t2.type == tokenize.NUMBER)
            t2_is_name = (t2.type == tokenize.NAME)
            t2_is_lparen = (t2.type == tokenize.OP and t2.string in ("(", "["))

            insert = False
            if t1_is_num and t2_is_name:
                insert = True
            elif t1_is_rparen and (t2_is_name or t2_is_lparen or t2_is_num):
                insert = True
            elif t1_is_num and t2_is_lparen:
                insert = True
            elif t1_is_name and t1.string not in TRUSTED_INTERNAL_FUNCS and t2_is_lparen:
                insert = True
            elif t1_is_name and t2_is_name:
                insert = True

            if insert:
                new_tokens.append("*")

    return " ".join(new_tokens)


class SecurityVisitor(ast.NodeVisitor):
    ALLOWED_NODES = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Name,
        ast.Call,
        ast.Load,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.UAdd,
        ast.USub,
    )

    def __init__(self, allowed_names, allowed_funcs=None, trusted=False, variables=None):
        self.allowed_names = set(allowed_names)
        self.allowed_funcs = set(allowed_funcs) if allowed_funcs is not None else set(WHITELIST_FUNCS.keys())
        self.trusted = trusted
        self.variables = set(variables) if variables is not None else None

    def generic_visit(self, node):
        if not isinstance(node.func if isinstance(node, ast.Call) else node, self.ALLOWED_NODES):
            pass
        if not isinstance(node, self.ALLOWED_NODES):
            raise SafeParseError(f"Disallowed syntax: {type(node).__name__}")
        super().generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise SafeParseError(f"Disallowed constant type: {type(node.value).__name__}")
        if isinstance(node.value, int) and abs(node.value) > 10**100:
            raise SafeParseError("Integer literal too large")
        if isinstance(node.value, float) and abs(node.value) > 1e100:
            raise SafeParseError("Float literal too large")

    def visit_Name(self, node):
        if "_" in node.id:
            raise SafeParseError(f"Disallowed identifier containing underscore: {node.id}")
        if node.id not in self.allowed_names:
            raise SafeParseError(f"Unknown or unwhitelisted identifier: {node.id}")

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise SafeParseError("Function call must be a direct named function")
        if node.func.id not in self.allowed_funcs:
            raise SafeParseError(f"Unwhitelisted function: {node.func.id}")
        if node.keywords:
            raise SafeParseError("Keyword arguments are not allowed")
        if len(node.args) > 2:
            raise SafeParseError(f"Too many arguments for {node.func.id}")
        self.generic_visit(node)

    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Pow):
            if any(isinstance(n, ast.Pow) for n in ast.walk(node.right)):
                raise SafeParseError("Chained or nested exponentiation (e.g. 9**9**9) is not allowed")
            if isinstance(node.left, ast.BinOp) and isinstance(node.left.op, ast.Pow):
                if isinstance(node.left.left, ast.Constant):
                    raise SafeParseError("Nested numeric exponentiation (e.g. (9**9)**9) is not allowed")
            exp_val = None
            if isinstance(node.right, ast.Constant) and isinstance(node.right.value, (int, float)):
                exp_val = node.right.value
            elif isinstance(node.right, ast.UnaryOp) and isinstance(node.right.operand, ast.Constant):
                if isinstance(node.right.op, ast.USub):
                    exp_val = -node.right.operand.value
                elif isinstance(node.right.op, ast.UAdd):
                    exp_val = node.right.operand.value
            # Determine base type for exponent limit:
            # - If trusted (internal template evaluation): limit is 1000
            # - If base is imaginary unit i/I: reduces mod 4 cheaply, limit is 1000
            # - If base is purely numeric constant: limit is 1000 (blocks 2**1001, allows 2**30)
            # - If base is symbolic / contains variables: limit is 100 (blocks (k+1)**101, allows (x+1)**30)
            is_imag_unit = isinstance(node.left, ast.Name) and node.left.id in ("i", "I", "j", "k") and not self.variables
            is_pure_num = all(not (isinstance(n, ast.Name) and (self.variables is None or n.id in self.variables)) for n in ast.walk(node.left))

            if self.trusted or is_imag_unit or is_pure_num:
                exp_limit = 1000
            else:
                exp_limit = 100

            if exp_val is not None and abs(exp_val) > exp_limit:
                raise SafeParseError(f"Exponent magnitude {exp_val} exceeds limit {exp_limit}")
            if isinstance(node.left, ast.BinOp) and isinstance(node.left.op, ast.Pow):
                inner_exp = None
                if isinstance(node.left.right, ast.Constant) and isinstance(node.left.right.value, (int, float)):
                    inner_exp = node.left.right.value
                if exp_val is not None and inner_exp is not None:
                    if abs(inner_exp * exp_val) > exp_limit:
                        raise SafeParseError(f"Compound exponent magnitude {inner_exp * exp_val} exceeds limit {exp_limit}")
                else:
                    raise SafeParseError("Nested exponentiation with non-constant exponents is not allowed")
        self.generic_visit(node)


def _uneval_add(a, b):
    args = []
    for x in (a, b):
        if isinstance(x, sp.Add):
            args.extend(x.args)
        else:
            args.append(x)
    return sp.Add(*args, evaluate=False)


def _uneval_sub(a, b):
    neg_b = sp.Mul(sp.Integer(-1), b, evaluate=False)
    args = []
    for x in (a, neg_b):
        if isinstance(x, sp.Add):
            args.extend(x.args)
        else:
            args.append(x)
    return sp.Add(*args, evaluate=False)


def _uneval_mul(a, b):
    args = []
    for x in (a, b):
        if isinstance(x, sp.Mul):
            args.extend(x.args)
        else:
            args.append(x)
    return sp.Mul(*args, evaluate=False)


def _uneval_div(a, b):
    inv_b = sp.Pow(b, sp.Integer(-1), evaluate=False)
    args = []
    for x in (a, inv_b):
        if isinstance(x, sp.Mul):
            args.extend(x.args)
        else:
            args.append(x)
    return sp.Mul(*args, evaluate=False)


def _uneval_pow(a, b):
    return sp.Pow(a, b, evaluate=False)


def _uneval_usub(a):
    return sp.Mul(sp.Integer(-1), a, evaluate=False)


class ASTTransformer(ast.NodeTransformer):
    def __init__(self, evaluate=True):
        self.evaluate = evaluate

    def visit_Constant(self, node):
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            return ast.Call(
                func=ast.Name(id="_Integer", ctx=ast.Load()),
                args=[node],
                keywords=[]
            )
        elif isinstance(node.value, float):
            return ast.Call(
                func=ast.Name(id="_Float", ctx=ast.Load()),
                args=[node],
                keywords=[]
            )
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if not self.evaluate:
            op_map = {
                ast.Add: "_uneval_add",
                ast.Sub: "_uneval_sub",
                ast.Mult: "_uneval_mul",
                ast.Div: "_uneval_div",
                ast.Pow: "_uneval_pow",
            }
            fn = op_map.get(type(node.op))
            if fn:
                return ast.Call(func=ast.Name(id=fn, ctx=ast.Load()), args=[node.left, node.right], keywords=[])
        return node

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if not self.evaluate and isinstance(node.op, ast.USub):
            return ast.Call(func=ast.Name(id="_uneval_usub", ctx=ast.Load()), args=[node.operand], keywords=[])
        return node


def safe_parse(raw, variables=None, evaluate=True, allow_i=True, allowed_funcs=None, trusted=False):
    raw_str = str(raw or "")
    if len(raw_str) > MAX_INPUT_LEN:
        raise SafeParseError(f"Input exceeds maximum length of {MAX_INPUT_LEN} characters.")
    s = _normalize(raw_str)
    if not s:
        raise SafeParseError("Empty input")
    if len(s) > MAX_INPUT_LEN:
        raise SafeParseError(f"Input exceeds maximum length of {MAX_INPUT_LEN} characters.")

    s = _insert_implicit_mul(s)
    try:
        tree = ast.parse(s, mode="eval")
    except SyntaxError as e:
        raise SafeParseError(f"Syntax error: {e}")

    if trusted:
        funcs = TRUSTED_INTERNAL_FUNCS
    elif allowed_funcs is not None:
        funcs = allowed_funcs
    else:
        funcs = WHITELIST_FUNCS

    allowed_names = set(WHITELIST_CONSTANTS.keys()) | set(funcs.keys()) | set(variables or [])
    if not allow_i:
        if not (variables and "i" in variables):
            allowed_names.discard("i")
        allowed_names.discard("I")

    SecurityVisitor(allowed_names, allowed_funcs=funcs.keys(), trusted=trusted, variables=variables).visit(tree)

    transformed_tree = ASTTransformer(evaluate=evaluate).visit(tree)
    ast.fix_missing_locations(transformed_tree)

    safe_globals = {
        "__builtins__": {},
        "_Integer": sp.Integer,
        "_Float": sp.Float,
        "_uneval_add": _uneval_add,
        "_uneval_sub": _uneval_sub,
        "_uneval_mul": _uneval_mul,
        "_uneval_div": _uneval_div,
        "_uneval_pow": _uneval_pow,
        "_uneval_usub": _uneval_usub,
    }
    for k, v in funcs.items():
        safe_globals[k] = v
    for k, v in WHITELIST_CONSTANTS.items():
        if allow_i:
            if not (variables and k in variables):
                safe_globals[k] = v
        else:
            if k not in ("i", "I"):
                safe_globals[k] = v
    for v in (variables or []):
        safe_globals[v] = sp.Symbol(v)

    try:
        code_obj = compile(transformed_tree, "<math>", "eval")
        return eval(code_obj, safe_globals, {})
    except Exception as e:
        raise SafeParseError(f"Evaluation error: {e}")


def _tokenize_vector(raw: str) -> list[str]:
    s = (raw or "").strip()
    s = s.replace("\u27e8", "<").replace("\u27e9", ">").replace("\u3008", "<").replace("\u3009", ">")
    if not s:
        raise SafeParseError("Empty vector input")
    if len(s) > MAX_INPUT_LEN:
        raise SafeParseError(f"Input exceeds maximum length of {MAX_INPUT_LEN} characters.")

    first, last = s[0], s[-1]
    bracket_pairs = {
        "<": ">",
        "(": ")",
        "[": "]",
    }

    if first in bracket_pairs:
        expected_close = bracket_pairs[first]
        if last != expected_close:
            raise SafeParseError(f"Mismatched vector brackets: starts with '{first}' but ends with '{last}'")
        inner = s[1:-1].strip()
        if "<" in inner or ">" in inner:
            raise SafeParseError("Nested angle brackets are not allowed in vectors")
        if "[" in inner or "]" in inner:
            raise SafeParseError("Nested square brackets are not allowed in vectors")
    else:
        if any(b in s for b in "<>[]"):
            raise SafeParseError("Mismatched or invalid vector bracket formatting")
        if last in (">", ")", "]"):
            raise SafeParseError(f"Unmatched closing bracket '{last}'")
        inner = s

    elements = []
    current = []
    depth = 0
    for char in inner:
        if char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise SafeParseError("Unbalanced parentheses in vector component")
            current.append(char)
        elif char == "," and depth == 0:
            elem = "".join(current).strip()
            if not elem:
                raise SafeParseError("Empty vector component between commas")
            elements.append(elem)
            current = []
        else:
            current.append(char)

    if depth != 0:
        raise SafeParseError("Unbalanced parentheses in vector")

    last_elem = "".join(current).strip()
    if not last_elem:
        if elements:
            raise SafeParseError("Trailing comma with empty vector component")
        else:
            raise SafeParseError("Empty vector components")
    elements.append(last_elem)

    if len(elements) > 4:
        raise SafeParseError(f"Vector component count ({len(elements)}) exceeds maximum allowed (4)")

    return elements


def _parse_vector_unit_notation(raw: str, dim: int) -> list[sp.Expr]:
    s = raw
    s = re.sub(r"\\hat\{\\imath\}|\\hat\{i\}|\\mathbf\{i\}|\\vec\{i\}|i_hat", " i ", s)
    s = re.sub(r"\\hat\{\\jmath\}|\\hat\{j\}|\\mathbf\{j\}|\\vec\{j\}|j_hat", " j ", s)
    s = re.sub(r"\\hat\{k\}|\\mathbf\{k\}|\\vec\{k\}|k_hat", " k ", s)
    s = re.sub(r"([0-9])\s*([ijk])", r"\1 * \2", s)
    basis_names = ["i", "j", "k"][:max(dim, 3)]
    parsed_expr = safe_parse(s, variables=basis_names, allow_i=False)

    comps = []
    check_expr = parsed_expr
    for bname in basis_names[:dim]:
        sym = sp.Symbol(bname)
        coeff = parsed_expr.coeff(sym)
        comps.append(coeff)
        check_expr = check_expr - coeff * sym

    if sp.simplify(check_expr) != 0:
        raise SafeParseError("Invalid unit vector notation: extraneous or non-linear terms found")
    return comps


def parse_math(raw, variables=None, evaluate=True, allow_i=True):
    return safe_parse(raw, variables=variables, evaluate=evaluate, allow_i=allow_i)


def to_expr(value, variables=None, trusted=True):
    if value is None:
        return None
    if isinstance(value, sp.Basic):
        return value
    if isinstance(value, (int, float)):
        return sp.nsimplify(value)
    if isinstance(value, (list, tuple)):
        return sp.Matrix([to_expr(x, variables=variables, trusted=trusted) for x in value])
    s = str(value).strip()
    if s.startswith("<") and s.endswith(">"):
        elements = _tokenize_vector(s)
        return sp.Matrix([safe_parse(x, variables=variables, trusted=trusted) for x in elements])
    return safe_parse(s, variables=variables, trusted=trusted)


# ---------------------------------------------------------------------------
# Equality helpers
# ---------------------------------------------------------------------------
def is_equal(a, b, variables=None, tolerance=None, timeout=1.5, raise_on_timeout=False):
    if a == b:
        return True

    def _eval():
        if isinstance(a, sp.Matrix) and isinstance(b, sp.Matrix):
            if a.shape != b.shape:
                return False
            return all(is_equal(a[i], b[i], variables=variables, tolerance=tolerance, timeout=timeout, raise_on_timeout=raise_on_timeout) for i in range(len(a)))
        if isinstance(a, sp.Matrix) != isinstance(b, sp.Matrix):
            return False

        # If tolerance is specified, check numerical difference
        if tolerance is not None:
            try:
                if not variables:
                    diff = abs(sp.N(a - b, 30))
                    val_b = abs(sp.N(b, 30))
                    if isinstance(tolerance, (int, float)):
                        if diff <= tolerance or diff <= tolerance * max(1.0, float(val_b)):
                            return True
                    elif isinstance(tolerance, dict):
                        abs_tol = tolerance.get("abs", 0.0)
                        rel_tol = tolerance.get("rel", 0.0)
                        if (abs_tol and diff <= abs_tol) or (rel_tol and diff <= rel_tol * max(1.0, float(val_b))):
                            return True
                else:
                    syms = [sp.Symbol(v) for v in variables]
                    tol_val = tolerance if isinstance(tolerance, (int, float)) else tolerance.get("abs", 1e-3)
                    all_close = True
                    for _ in range(5):
                        subs = {s: sp.Rational(random.randint(1, 10), 1) for s in syms}
                        diff_sub = abs(sp.N((a - b).subs(subs), 30))
                        val_b = abs(sp.N(b.subs(subs), 30))
                        if not (diff_sub <= tol_val or diff_sub <= tol_val * max(1.0, float(val_b))):
                            all_close = False
                            break
                    if all_close:
                        return True
            except Exception:
                pass

        # Quick pre-filter for expressions with variables
        if variables:
            syms = [sp.Symbol(v) for v in variables]
            try:
                for _ in range(2):
                    subs = {s: sp.Rational(random.randint(2, 6), 1) for s in syms}
                    diff_sub = (a - b).subs(subs)
                    if abs(sp.N(diff_sub, 30)) > 1e-9:
                        return False
            except Exception:
                pass

        try:
            diff = sp.simplify(sp.expand_complex(a - b)) if not variables else sp.simplify(a - b)
            if diff == 0:
                return True
            if not variables:
                val = abs(sp.N(diff, 30))
                return bool(val < 1e-12)
            if diff.is_number and diff != 0:
                return False
        except Exception:
            pass

        syms = [sp.Symbol(v) for v in (variables or [])]
        if not syms:
            return False

        try:
            for _ in range(6):
                subs = {s: sp.Rational(random.randint(-90, 90), random.randint(7, 19)) for s in syms}
                diff_sub = diff.subs(subs)
                val = abs(sp.N(diff_sub, 30))
                if val > 1e-9:
                    return False
            return True
        except Exception:
            return False

    try:
        return _run_with_timeout(_eval, timeout_sec=timeout)
    except EqualTimeoutError:
        if raise_on_timeout:
            raise
        return False


def numeric_close(a, b, rel=1e-2):
    try:
        va, vb = complex(sp.N(a)), complex(sp.N(b))
        return abs(va - vb) <= rel * max(1.0, abs(vb)) and abs(va - vb) > 1e-12
    except Exception:
        return False


def _has_large_exponent(expr, threshold=20):
    try:
        for p in sp.preorder_traversal(expr):
            if isinstance(p, sp.Pow) and isinstance(p.exp, sp.Number) and abs(p.exp) > threshold:
                return True
    except Exception:
        pass
    return False


def generic_value_diagnostics(u, e, variables=None):
    """Diagnostics that apply to any scalar / expression comparison."""
    if _has_large_exponent(u, threshold=20) or _has_large_exponent(e, threshold=20):
        return []
    diags = []
    try:
        if e != 0 and is_equal(u, -e, variables):
            diags.append({"code": "whole_sign_flip", "message": "Your answer is the exact negative of the correct value. Check a sign (for example $i^2 = -1$ or a subtraction)."})
            return diags
        if e != 0 and u != 0 and is_equal(u, 1 / e, variables):
            diags.append({"code": "reciprocal", "message": "Your answer is the reciprocal of the correct value. Check which quantity is in the numerator."})
            return diags
        if e != 0 and u != 0:
            # Fast check: only simplify if ratio could be constant
            can_be_const = True
            if variables:
                syms = [sp.Symbol(v) for v in variables]
                try:
                    p1 = {s: sp.Rational(2, 1) for s in syms}
                    p2 = {s: sp.Rational(3, 1) for s in syms}
                    r1 = complex(sp.N((u / e).subs(p1)))
                    r2 = complex(sp.N((u / e).subs(p2)))
                    if abs(r1 - r2) > 1e-6 * max(1.0, abs(r1)):
                        can_be_const = False
                except Exception:
                    pass
            if can_be_const:
                ratio = sp.simplify(u / e)
                if ratio.is_number and ratio.is_rational and ratio not in (1, -1):
                    diags.append({"code": "off_by_factor", "message": f"Your answer differs from the correct value by a constant factor of ${sp.latex(ratio)}$."})
                    return diags
        if variables:
            # Fast check: only simplify if offset could be constant
            can_be_const_offset = True
            syms = [sp.Symbol(v) for v in variables]
            try:
                p1 = {s: sp.Rational(2, 1) for s in syms}
                p2 = {s: sp.Rational(3, 1) for s in syms}
                o1 = complex(sp.N((u - e).subs(p1)))
                o2 = complex(sp.N((u - e).subs(p2)))
                if abs(o1 - o2) > 1e-6 * max(1.0, abs(o1)):
                    can_be_const_offset = False
            except Exception:
                pass
            if can_be_const_offset:
                offset = sp.simplify(u - e)
                if offset.is_number and offset != 0:
                    diags.append({"code": "constant_offset", "message": f"Your expression differs from the correct one by the constant ${sp.latex(offset)}$."})
                    return diags
        if not variables and numeric_close(u, e):
            diags.append({"code": "rounding", "message": "Your answer is numerically close but not exact. Check rounding or keep exact fractions / radicals."})
    except Exception:
        pass
    return diags


# ---------------------------------------------------------------------------
# Form checks (performed on the UNEVALUATED parse tree)
# ---------------------------------------------------------------------------
def _is_rational_number(t):
    try:
        return bool(t.is_number) and bool(sp.nsimplify(t).is_rational) and not t.has(sp.I) and not any(
            isinstance(p, sp.Pow) and not p.exp.is_integer for p in sp.preorder_traversal(t)
        )
    except Exception:
        return False


def form_issues(tree, forms):
    issues = []
    forms = forms or []

    def walk(e):
        if "a+bi" in forms:
            if isinstance(e, sp.Pow) and e.base.has(sp.I):
                ex = e.exp
                if ex.is_number and ex.is_negative:
                    issues.append("complex_denominator")
                else:
                    issues.append("unexpanded_power")
            if isinstance(e, sp.Mul):
                if any(isinstance(a, sp.Add) and a.has(sp.I) for a in e.args):
                    issues.append("unseparated")
                if sum(1 for a in e.args if a == sp.I) > 1:
                    issues.append("unexpanded_power")
        if "reduced_fraction" in forms and isinstance(e, sp.Mul):
            ints = [a for a in e.args if isinstance(a, sp.Integer)]
            dens = [a.base for a in e.args if isinstance(a, sp.Pow) and isinstance(a.base, sp.Integer) and a.exp == -1]
            for p in ints:
                for q in dens:
                    if sp.gcd(int(p), int(q)) > 1:
                        issues.append("unreduced_fraction")
        if "rationalized" in forms and isinstance(e, sp.Pow) and e.exp.is_number and e.exp.is_negative:
            if any(isinstance(p, sp.Pow) and p.exp == sp.Rational(1, 2) for p in sp.preorder_traversal(e.base)) or (
                isinstance(e.base, sp.Pow) and e.base.exp == sp.Rational(1, 2)
            ):
                issues.append("radical_denominator")
        if "exact" in forms and isinstance(e, sp.Float):
            issues.append("decimal_not_exact")
        if "simplified_radical" in forms and isinstance(e, sp.Pow) and e.exp == sp.Rational(1, 2) and isinstance(e.base, sp.Integer):
            n = abs(int(e.base))
            if n > 1 and any(n % (k * k) == 0 for k in range(2, int(n ** 0.5) + 1)):
                issues.append("unsimplified_radical")
        for a in e.args:
            walk(a)

    walk(tree)

    if "a+bi" in forms and isinstance(tree, sp.Add):
        im_terms = [t for t in tree.args if t.has(sp.I)]
        re_terms = [t for t in tree.args if not t.has(sp.I)]
        if sum(1 for t in re_terms if _is_rational_number(t)) > 1:
            issues.append("uncombined_terms")
        if sum(1 for t in im_terms if _is_rational_number(t / sp.I)) > 1:
            issues.append("uncombined_terms")

    return list(dict.fromkeys(issues))


def _evaluated_form_issues(u, forms, variables):
    issues = []
    if "expanded" in forms and sp.expand(u) != u:
        issues.append("not_expanded")
    if "factored" in forms and sp.factor(u) != u:
        issues.append("not_factored")
    return issues


def _form_result(raw, u, spec, variables=None):
    forms = spec.get("forms", [])
    try:
        tree = parse_math(raw, variables, evaluate=False)
        issues = form_issues(tree, forms)
    except Exception:
        issues = []
    issues += _evaluated_form_issues(u, forms, variables)
    if issues:
        return {
            "verdict": "equivalent_not_in_form",
            "message": FORM_MESSAGES.get(issues[0], "Equivalent, but not in the required final form."),
            "diagnostics": [{"code": c, "message": FORM_MESSAGES.get(c, c)} for c in issues],
        }
    return None


# ---------------------------------------------------------------------------
# Type checkers
# ---------------------------------------------------------------------------
def check_number(spec, raw):
    try:
        u = parse_math(raw)
    except SafeParseError:
        s_raw = (raw or "").strip()
        s_raw = s_raw.replace("\u27e8", "<").replace("\u27e9", ">").replace("\u3008", "<").replace("\u3009", ">")
        is_vec = (
            (s_raw.startswith("<") and s_raw.endswith(">"))
            or (s_raw.startswith("[") and s_raw.endswith("]"))
            or (s_raw.startswith("(") and s_raw.endswith(")") and "," in s_raw)
        )
        if is_vec:
            try:
                vars_list = spec.get("variables") or []
                toks = _tokenize_vector(s_raw)
                for t in toks:
                    safe_parse(t, variables=vars_list, allow_i=False)
                return {
                    "verdict": "incorrect",
                    "message": "Expected a scalar number, but received a vector. (If calculating a dot product, remember to sum the component products: $u_1 v_1 + u_2 v_2 + u_3 v_3$).",
                    "components": [{"label": "Value", "ok": False}],
                    "diagnostics": [{"code": "vector_given_for_scalar", "message": "Expected a scalar, received a vector."}],
                }
            except Exception:
                pass
        raise
    tol = spec.get("tolerance")
    e = to_expr(spec["value"])
    comps = [{"label": "Value", "ok": False}]
    if is_equal(u, e, tolerance=tol):
        comps[0]["ok"] = True
        fr = _form_result(raw, u, spec)
        if fr:
            return {**fr, "components": comps}
        return {"verdict": "correct", "message": "Correct.", "components": comps, "diagnostics": []}
    diags = generic_value_diagnostics(u, e)
    return {"verdict": "incorrect", "message": "Not equal to the verified answer.", "components": comps, "diagnostics": diags}


def check_complex(spec, raw):
    tol = spec.get("tolerance")
    e = sp.expand_complex(to_expr(spec["value"]))
    u = sp.expand_complex(parse_math(raw))
    ere, eim = sp.re(e), sp.im(e)
    ure, uim = sp.re(u), sp.im(u)
    re_ok, im_ok = is_equal(ure, ere, tolerance=tol), is_equal(uim, eim, tolerance=tol)
    comps = [{"label": "Real part", "ok": re_ok}, {"label": "Imaginary part", "ok": im_ok}]
    if re_ok and im_ok:
        fr = _form_result(raw, u, spec)
        if fr:
            return {**fr, "components": comps}
        return {"verdict": "correct", "message": "Correct.", "components": comps, "diagnostics": []}

    diags = []
    if re_ok and eim != 0 and is_equal(uim, -eim, tolerance=tol):
        diags.append({"code": "imag_sign_flip", "message": "Real part is correct, but the imaginary part has the opposite sign. Check $i^2 = -1$ or the conjugate sign."})
    elif im_ok and ere != 0 and is_equal(ure, -ere, tolerance=tol):
        diags.append({"code": "real_sign_flip", "message": "Imaginary part is correct, but the real part has the opposite sign. Check $i^2 = -1$ when combining real terms."})
    elif is_equal(ure, eim, tolerance=tol) and is_equal(uim, ere, tolerance=tol) and ere != eim:
        diags.append({"code": "swapped_parts", "message": "Your real and imaginary parts are swapped."})
    else:
        diags = generic_value_diagnostics(u, e)

    verdict = "partial" if (spec.get("allowPartial") and (re_ok or im_ok)) else "incorrect"
    msg = "One component matches; inspect the other." if (re_ok or im_ok) else "Not equal to the verified answer."
    return {"verdict": verdict, "message": msg, "components": comps, "diagnostics": diags}


def check_expression(spec, raw):
    tol = spec.get("tolerance")
    variables = spec.get("variables", ["x"])
    allowed_funcs = dict(WHITELIST_FUNCS)
    if "allowFuncs" in spec:
        for fn_name in spec["allowFuncs"]:
            if fn_name not in VETTED_EXTRA_FUNCS:
                raise SafeParseError(f"Unvetted function in allowFuncs: {fn_name}")
            allowed_funcs[fn_name] = VETTED_EXTRA_FUNCS[fn_name]
    e = to_expr(spec["value"], variables, trusted=True)
    u = safe_parse(raw, variables, allow_i=spec.get("allowI", False), allowed_funcs=allowed_funcs)
    comps = [{"label": "Equivalence", "ok": False}]
    if is_equal(u, e, variables=variables, tolerance=tol):
        comps[0]["ok"] = True
        fr = _form_result(raw, u, spec, variables)
        if fr:
            return {**fr, "components": comps}
        return {"verdict": "correct", "message": "Correct.", "components": comps, "diagnostics": []}
    return {"verdict": "incorrect", "message": "Not equivalent to the verified answer.", "components": comps, "diagnostics": generic_value_diagnostics(u, e, variables)}


def _split_items(raw, variable):
    s = raw.strip()
    s = re.sub(r"^[\(\{\[]\s*|\s*[\)\}\]]$", "", s) if re.match(r"^[\{\[]", s) else s
    parts = re.split(r",|;|\bor\b|\band\b", s)
    items = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if variable:
            p = re.sub(rf"^\s*{re.escape(variable)}\s*(_?\d+)?\s*=\s*", "", p)
        if "\u00b1" in p or "+-" in p:
            a, b = re.split(r"\u00b1|\+-", p, maxsplit=1)
            a = a.strip() or "0"
            items += [f"({a})+({b})", f"({a})-({b})"]
        else:
            items.append(p)
    return items


def check_solution_set(spec, raw):
    variable = spec.get("variable", "x")
    expected = [sp.expand_complex(to_expr(v)) for v in spec["values"]]
    try:
        users = [sp.expand_complex(parse_math(it)) for it in _split_items(raw, variable)]
    except Exception as ex:
        raise ValueError(f"Could not parse the solution list: {ex}")
    matched_u = set()
    comps, diags = [], []
    for i, ev in enumerate(expected):
        hit = next((j for j, uv in enumerate(users) if j not in matched_u and is_equal(uv, ev)), None)
        ok = hit is not None
        if ok:
            matched_u.add(hit)
        comps.append({"label": f"Solution {i + 1}: ${sp.latex(ev)}$", "ok": ok})
    extras = [users[j] for j in range(len(users)) if j not in matched_u]
    for x in extras:
        if any(is_equal(x, -ev) for ev in expected):
            diags.append({"code": "whole_sign_flip", "message": f"${sp.latex(x)}$ is the negative of a true solution. Check the sign in front of $b$ in the quadratic formula."})
        elif any(is_equal(sp.conjugate(x), ev) or is_equal(sp.re(x), sp.re(ev)) for ev in expected):
            diags.append({"code": "imag_sign_flip", "message": f"${sp.latex(x)}$ has the right real part but the wrong imaginary part."})
        else:
            diags.append({"code": "extra_solution", "message": f"${sp.latex(x)}$ does not satisfy the equation (extraneous value)."})
    missing = sum(1 for c in comps if not c["ok"])
    if missing:
        diags.append({"code": "missing_solution", "message": f"{missing} solution(s) missing. Remember both signs of $\\pm$."})
    if missing == 0 and not extras:
        forms = spec.get("forms", [])
        issues = []
        for it in _split_items(raw, variable):
            try:
                issues += form_issues(parse_math(it, evaluate=False), forms)
            except Exception:
                pass
        if issues:
            return {"verdict": "equivalent_not_in_form", "message": FORM_MESSAGES.get(issues[0], "Not in required form."), "components": comps,
                    "diagnostics": [{"code": c, "message": FORM_MESSAGES.get(c, c)} for c in dict.fromkeys(issues)]}
        return {"verdict": "correct", "message": "Correct. All solutions found.", "components": comps, "diagnostics": []}
    verdict = "partial" if missing < len(expected) else "incorrect"
    return {"verdict": verdict, "message": "Some solutions match." if verdict == "partial" else "No solution matches.", "components": comps, "diagnostics": diags}


def check_tuple(spec, raw):
    expected = [to_expr(v) for v in spec["values"]]
    labels = spec.get("labels") or [f"Component {i + 1}" for i in range(len(expected))]
    s = raw.strip()
    if spec.get("acceptComplex") and "," not in s and len(expected) == 2:
        z = sp.expand_complex(parse_math(s))
        users = [sp.re(z), sp.im(z)]
    else:
        s = re.sub(r"^\s*[\(\[\{<]|[\)\]\}>]\s*$", "", s)
        users = [parse_math(p) for p in s.split(",") if p.strip()]
    comps = [{"label": labels[i], "ok": i < len(users) and is_equal(users[i], expected[i])} for i in range(len(expected))]
    if len(users) == len(expected) and all(c["ok"] for c in comps):
        return {"verdict": "correct", "message": "Correct.", "components": comps, "diagnostics": []}
    diags = []
    if len(users) != len(expected):
        diags.append({"code": "wrong_component_count", "message": f"Expected {len(expected)} components, received {len(users)}."})
    else:
        for i, (uv, ev) in enumerate(zip(users, expected)):
            if not comps[i]["ok"] and ev != 0 and is_equal(uv, -ev):
                diags.append({"code": "whole_sign_flip", "message": f"{labels[i]} has the opposite sign."})
        if len(expected) == 2 and is_equal(users[0], expected[1]) and is_equal(users[1], expected[0]):
            diags.append({"code": "swapped_parts", "message": "The components are swapped."})
    verdict = "partial" if any(c["ok"] for c in comps) else "incorrect"
    return {"verdict": verdict, "message": "Some components match." if verdict == "partial" else "No component matches.", "components": comps, "diagnostics": diags}


def check_choice(spec, raw):
    ok = raw.strip().upper() == str(spec["correct"]).strip().upper()
    return {"verdict": "correct" if ok else "incorrect", "message": "Correct." if ok else "Incorrect choice.", "components": [{"label": "Choice", "ok": ok}], "diagnostics": []}


def check_text(spec, raw):
    norm = lambda t: re.sub(r"\s+", " ", t.strip().lower())
    ok = norm(raw) in [norm(a) for a in spec["accepted"]]
    return {"verdict": "correct" if ok else "incorrect", "message": "Correct." if ok else "Does not match the accepted answers.", "components": [{"label": "Answer", "ok": ok}], "diagnostics": []}


def _check_parallel_numeric(user_comps, expected_comps, vars_list=None):
    if not vars_list:
        try:
            pivot_idx = None
            for i, e in enumerate(expected_comps):
                try:
                    if abs(float(e)) > 1e-12:
                        pivot_idx = i
                        break
                except Exception:
                    continue
            if pivot_idx is None:
                return None

            val_e_pivot = float(expected_comps[pivot_idx])
            val_u_pivot = float(user_comps[pivot_idx])
            if abs(val_e_pivot) < 1e-12 or abs(val_u_pivot) < 1e-12:
                return None
            k = val_u_pivot / val_e_pivot
            for u, e in zip(user_comps, expected_comps):
                if abs(float(u) - k * float(e)) > 1e-5 * max(1.0, abs(float(u))):
                    return None
            return k
        except Exception:
            return None
    else:
        syms = [sp.Symbol(v) for v in vars_list]
        try:
            fixed_points = [
                {s: sp.Rational(base + i * 2, 1) for i, s in enumerate(syms)}
                for base in (2, 3, 5)
            ]
            sample_ks = []
            for pt in fixed_points:
                pivot_idx = None
                for i, e in enumerate(expected_comps):
                    try:
                        v_e = float(e.subs(pt))
                        if abs(v_e) > 1e-6:
                            pivot_idx = i
                            break
                    except Exception:
                        continue
                if pivot_idx is None:
                    continue

                val_e = float(expected_comps[pivot_idx].subs(pt))
                val_u = float(user_comps[pivot_idx].subs(pt))
                if abs(val_e) < 1e-6 or abs(val_u) < 1e-9:
                    continue
                k = val_u / val_e
                all_match = True
                for u, e in zip(user_comps, expected_comps):
                    u_val = float(u.subs(pt))
                    e_val = float(e.subs(pt))
                    if abs(u_val - k * e_val) > 1e-5 * max(1.0, abs(u_val)):
                        all_match = False
                        break
                if not all_match:
                    return None
                sample_ks.append(k)

            if len(sample_ks) >= 2 and all(abs(k - sample_ks[0]) < 1e-5 for k in sample_ks):
                return sample_ks[0]
            return None
        except Exception:
            return None


def _format_scalar_multiple_ratio(k_val):
    """Formats scalar multiple ratio cleanly to integer, simple fraction, or simple radical (sqrt(2), sqrt(3))."""
    import math
    # 1. Exact or simple rational fraction (e.g. 5, 3/2, -2/3)
    try:
        q = sp.nsimplify(k_val, rational=True)
        if abs(k_val - float(q)) < 1e-5 and getattr(q, "q", 1) <= 20:
            return sp.latex(q)
    except Exception:
        pass

    # 2. Simple rational multiple of sqrt(2) or sqrt(3) (e.g. \sqrt{2}, 2\sqrt{2}, \frac{\sqrt{2}}{2}, \sqrt{3})
    for rad_sym, rad_val in [(sp.sqrt(2), math.sqrt(2)), (sp.sqrt(3), math.sqrt(3))]:
        try:
            ratio = k_val / rad_val
            q = sp.nsimplify(ratio, rational=True)
            if abs(ratio - float(q)) < 1e-4 and getattr(q, "q", 1) <= 10:
                return sp.latex(q * rad_sym)
        except Exception:
            pass

    # 3. Clean decimal fallback
    if abs(k_val - round(k_val)) < 1e-5:
        return str(int(round(k_val)))
    return f"{k_val:.3f}"


def check_vector(spec, raw):
    vars_list = spec.get("variables") or []

    def _eval_vector():
        raw_str = (raw or "").strip()
        if not raw_str:
            return {"verdict": "invalid input", "message": "Type your final answer first.", "components": [], "diagnostics": []}

        expected_raw = spec.get("components") or spec.get("values") or spec.get("value")
        if expected_raw is None:
            raise ValueError("Vector answerSpec missing 'components' or 'values'")

        if isinstance(expected_raw, (list, tuple)):
            expected_comps = [to_expr(c, variables=vars_list) for c in expected_raw]
        elif isinstance(expected_raw, str):
            toks = _tokenize_vector(expected_raw)
            expected_comps = [safe_parse(t, variables=vars_list, allow_i=False) for t in toks]
        else:
            expected_comps = [to_expr(expected_raw, variables=vars_list)]

        dim = len(expected_comps)
        vector_notation = spec.get("vectorNotation", False)
        user_comps = None

        if vector_notation and not (raw_str.startswith(("<", "[", "(")) or "," in raw_str):
            user_comps = _parse_vector_unit_notation(raw_str, dim)

        if user_comps is None:
            toks = _tokenize_vector(raw_str)
            user_comps = [safe_parse(t, variables=vars_list, allow_i=False) for t in toks]

        # 1. Dimension mismatch check
        if len(user_comps) != len(expected_comps):
            comps = [{"label": f"Component {i + 1}", "ok": False} for i in range(len(expected_comps))]
            diags = [{
                "code": "dimension_mismatch",
                "message": f"Dimension mismatch: expected {len(expected_comps)} components, received {len(user_comps)}."
            }]
            return {
                "verdict": "incorrect",
                "message": f"Expected a {len(expected_comps)}-dimensional vector.",
                "components": comps,
                "diagnostics": diags,
            }

        tol = spec.get("tolerance")
        comp_matches = [is_equal(u, e, variables=vars_list, tolerance=tol) for u, e in zip(user_comps, expected_comps)]
        comps = [{"label": f"Component {i + 1}", "ok": comp_matches[i]} for i in range(len(expected_comps))]

        if all(comp_matches):
            return {
                "verdict": "correct",
                "message": "Correct.",
                "components": comps,
                "diagnostics": [],
            }

        # Determine verdict strictly from component comparison first
        verdict = "partial" if (spec.get("allowPartial") and any(comp_matches)) else "incorrect"
        message = "Some components match." if verdict == "partial" else "Not equal to the verified vector."

        # Diagnostics (parallel/swapped/sign): isolated so timeouts or errors discard diagnostics and keep determined verdict
        diags = []
        try:
            def _gather_diagnostics():
                d_list = []
                # 2. Parallel / scalar multiple check (numeric substitution, no sp.simplify)
                k_ratio = _check_parallel_numeric(user_comps, expected_comps, vars_list)
                is_opposite_dir = False
                if k_ratio is not None and abs(k_ratio) > 1e-6:
                    if abs(k_ratio - (-1.0)) < 1e-5:
                        is_opposite_dir = True
                        d_list.append({
                            "code": "scalar_multiple",
                            "message": "Your vector points in the opposite direction (factor of -1). Check negative signs."
                        })
                    else:
                        k_disp = _format_scalar_multiple_ratio(k_ratio)
                        d_list.append({
                            "code": "scalar_multiple",
                            "message": f"Your vector is parallel to the correct answer but differs by a scalar factor of ${k_disp}$."
                        })

                # 3. Swapped order / permutation check
                if not d_list:
                    from itertools import permutations
                    is_swapped = False
                    for p in permutations(range(len(expected_comps))):
                        if list(p) == list(range(len(expected_comps))):
                            continue
                        if all(is_equal(user_comps[p[i]], expected_comps[i], variables=vars_list, tolerance=tol, timeout=0.08) for i in range(len(expected_comps))):
                            is_swapped = True
                            break
                    if is_swapped:
                        d_list.append({
                            "code": "swapped_order",
                            "message": "The vector components are swapped or entered in the wrong order."
                        })

                # 4. Component sign error check (skipped if parallel(-1) already reported)
                if not is_opposite_dir:
                    inverted_indices = []
                    for i, (u, e) in enumerate(zip(user_comps, expected_comps)):
                        if not comp_matches[i] and e != 0 and is_equal(u, -e, variables=vars_list, tolerance=tol, timeout=0.08):
                            inverted_indices.append(i + 1)
                    if inverted_indices:
                        if len(inverted_indices) == 1:
                            sign_msg = f"Component {inverted_indices[0]} has the opposite sign."
                        else:
                            comps_str = ", ".join(str(x) for x in inverted_indices[:-1]) + f" and {inverted_indices[-1]}"
                            sign_msg = f"Components {comps_str} have the opposite sign."
                        d_list.append({
                            "code": "component_sign_error",
                            "message": sign_msg,
                        })

                return d_list

            diags = _run_with_timeout(_gather_diagnostics, timeout_sec=0.15)
        except (Exception, EqualTimeoutError):
            diags = []

        # Deduplicate diagnostics by code
        seen_codes = set()
        unique_diags = []
        for d in diags:
            c = d.get("code")
            if c not in seen_codes:
                seen_codes.add(c)
                unique_diags.append(d)

        return {
            "verdict": verdict,
            "message": message,
            "components": comps,
            "diagnostics": unique_diags,
        }

    try:
        return _run_with_timeout(_eval_vector, timeout_sec=1.5)
    except EqualTimeoutError:
        return {
            "verdict": "invalid input",
            "message": "Evaluation timed out. Input is too complex.",
            "components": [],
            "diagnostics": [],
        }


from math_engine.answer_spec_registry import ANSWER_SPEC_TYPES, validate_answer_spec

CHECKERS = {
    "number": check_number,
    "complex": check_complex,
    "expression": check_expression,
    "solution_set": check_solution_set,
    "tuple": check_tuple,
    "choice": check_choice,
    "text": check_text,
    "vector": check_vector,
}


def check_answer(spec, raw):
    if not (raw or "").strip():
        return {"verdict": "invalid input", "message": "Type your final answer first.", "components": [], "diagnostics": []}
    fn = CHECKERS.get(spec.get("type"))
    if not fn:
        return {"verdict": "invalid input", "message": f"Unsupported answer type: {spec.get('type')}", "components": [], "diagnostics": []}
    try:
        return fn(spec, raw)
    except SafeParseError as ex:
        return {"verdict": "invalid input", "message": f"Invalid input: {ex}", "components": [], "diagnostics": []}
    except EqualTimeoutError as ex:
        return {"verdict": "invalid input", "message": "Evaluation timed out. Input is too complex.", "components": [], "diagnostics": []}
    except ValueError as ex:
        return {"verdict": "invalid input", "message": f"Invalid input: {ex}", "components": [], "diagnostics": []}
    except Exception:
        return {"verdict": "invalid input", "message": "Could not read that input. Use forms like 3 - 4i, 3/4, sqrt(2)/2, x^2 + 1, or x = 2, x = -3.", "components": [], "diagnostics": []}


if __name__ == "__main__":
    payload = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(check_answer(payload.get("answerSpec", {}), payload.get("input", ""))))
