# -*- coding: utf-8 -*-
"""Safe AST parsing, normalization, and interval/vector/list tokenizing for ``math_engine.answer_check``."""

import ast
import io
import re
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

# Functions allowed only for trusted internal evaluation (e.g. verify.source, step validation, trapDerivation)
TRUSTED_INTERNAL_FUNCS = {
    **WHITELIST_FUNCS,
    "diff": sp.diff,
    "floor": sp.floor,
    "round": round,
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


def _normalize(raw: str) -> str:
    s = (raw or "").strip()
    s = s.replace("²", "^2").replace("³", "^3")
    repl = {
        "\u2212": "-",
        "\u2013": "-",
        "\u00d7": "*",
        "\u00b7": "*",
        "\u22c5": "*",
        "\u00f7": "/",
        "\u03c0": "pi",
        "\u221e": "oo",
        "**": "^",
        "\u27e8": "<",
        "\u27e9": ">",
        "\u3008": "<",
        "\u3009": ">",
    }
    for k, v in repl.items():
        s = s.replace(k, v)
    s = s.replace("^", "**")
    s = re.sub(r"\u221a\s*\(", "sqrt(", s)  # √(…)
    s = re.sub(r"\u221a\s*([0-9.]+|[a-zA-Z])", r"sqrt(\1)", s)  # √12, √x
    s = re.sub(r"sqrt\s*([0-9]+)", r"sqrt(\1)", s)  # sqrt12
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
            t1_is_num = t1.type == tokenize.NUMBER
            t1_is_name = t1.type == tokenize.NAME
            t1_is_rparen = t1.type == tokenize.OP and t1.string in (")", "]")

            t2_is_num = t2.type == tokenize.NUMBER
            t2_is_name = t2.type == tokenize.NAME
            t2_is_lparen = t2.type == tokenize.OP and t2.string in ("(", "[")

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
    """AST validator enforcing whitelisted syntax, symbols, functions, and exponent bounds."""

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
        allowed_nodes = self.ALLOWED_NODES + ((ast.FloorDiv,) if self.trusted else ())
        target = node.func if isinstance(node, ast.Call) else node
        if not isinstance(target, allowed_nodes):
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
            is_imag_unit = (
                isinstance(node.left, ast.Name) and node.left.id in ("i", "I", "j", "k") and not self.variables
            )
            is_pure_num = all(
                not (isinstance(n, ast.Name) and (self.variables is None or n.id in self.variables))
                for n in ast.walk(node.left)
            )

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
                        raise SafeParseError(
                            f"Compound exponent magnitude {inner_exp * exp_val} exceeds limit {exp_limit}"
                        )
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
    """Rewrite numeric literals and operations into exact/unevaluated SymPy constructors."""

    def __init__(self, evaluate=True):
        self.evaluate = evaluate

    def visit_Constant(self, node):
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            return ast.Call(func=ast.Name(id="_Integer", ctx=ast.Load()), args=[node], keywords=[])
        elif isinstance(node.value, float):
            if not self.evaluate:
                return ast.Call(func=ast.Name(id="_Float", ctx=ast.Load()), args=[node], keywords=[])
            return ast.Call(
                func=ast.Name(id="_Rational", ctx=ast.Load()), args=[ast.Constant(value=str(node.value))], keywords=[]
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
        "_Rational": lambda v: sp.Rational(str(v)),
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
    for v in variables or []:
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
    basis_names = ["i", "j", "k"][: max(dim, 3)]
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
    if isinstance(value, int) and not isinstance(value, bool):
        return sp.Integer(value)
    if isinstance(value, float):
        return sp.Rational(str(value))
    if isinstance(value, (list, tuple)):
        return sp.Matrix([to_expr(x, variables=variables, trusted=trusted) for x in value])
    s = str(value).strip()
    if s.startswith("<") and s.endswith(">"):
        elements = _tokenize_vector(s)
        return sp.Matrix([safe_parse(x, variables=variables, trusted=trusted) for x in elements])
    return safe_parse(s, variables=variables, trusted=trusted)


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


_INTERVAL_FORMAT_MSG = "Write the domain/answer as an interval, e.g. [a, b) or (-inf, a) U (a, inf)."


def _parse_interval_endpoint(raw_ep: str, variables=None):
    s = (raw_ep or "").strip()
    if not s:
        raise ValueError("Interval endpoint cannot be empty.")
    s = s.replace("\u2212", "-").replace("\u2013", "-")
    s = s.replace("\\infty", "oo").replace("\u221e", "oo")
    s = re.sub(r"\b(?:infinity|inf)\b", "oo", s, flags=re.IGNORECASE)
    val = parse_math(s, variables=variables, allow_i=False)
    if isinstance(val, sp.Basic):
        val = val.replace(lambda x: isinstance(x, sp.Float), lambda x: sp.Rational(str(x)))
        if val in (sp.nan, sp.zoo) or val.has(sp.I, sp.nan, sp.zoo):
            raise ValueError("Interval endpoints must be real numbers or +/-inf.")
        val = sp.simplify(val)
    return val


def _split_interval_pieces(raw: str) -> list[str]:
    s = (raw or "").strip()
    if not s:
        raise ValueError(_INTERVAL_FORMAT_MSG)
    pieces: list[str] = []
    n = len(s)
    i = 0
    expect_piece = True
    while i < n:
        ch = s[i]
        if ch.isspace():
            i += 1
            continue
        if expect_piece:
            if ch not in "([{":
                raise ValueError(_INTERVAL_FORMAT_MSG)
            start = i
            depth = 0
            while i < n:
                c = s[i]
                if c in "([{":
                    depth += 1
                elif c in ")]}":
                    depth -= 1
                    if depth < 0:
                        raise ValueError("Unbalanced brackets in interval notation, e.g. [a, b).")
                    if depth == 0:
                        i += 1
                        break
                i += 1
            if depth != 0:
                raise ValueError("Unbalanced brackets in interval notation, e.g. [a, b).")
            pieces.append(s[start:i])
            expect_piece = False
        else:
            if s[i] == "\u222a":
                i += 1
                expect_piece = True
            elif s.startswith("\\cup", i) and (i + 4 == n or not s[i + 4].isalpha()):
                i += 4
                expect_piece = True
            elif s[i] in ("U", "u") and (i + 1 == n or not s[i + 1].isalpha()):
                i += 1
                expect_piece = True
            else:
                raise ValueError("Use U or \u222a to join intervals, e.g. (-inf, a) U (a, inf).")
    if expect_piece or not pieces:
        raise ValueError(_INTERVAL_FORMAT_MSG)
    return pieces


def _split_top_level_commas(inner: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    for idx, ch in enumerate(inner):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(inner[start:idx])
            start = idx + 1
    parts.append(inner[start:])
    return parts


def _parse_interval_piece(piece: str, variables=None) -> sp.Set:
    piece = piece.strip()
    if piece.startswith("{") and piece.endswith("}"):
        inner = piece[1:-1].strip()
        if not inner:
            return sp.EmptySet
        items = _split_top_level_commas(inner)
        return sp.FiniteSet(*[_parse_interval_endpoint(it, variables=variables) for it in items])

    if piece[0] not in "([" or piece[-1] not in ")]":
        raise ValueError(_INTERVAL_FORMAT_MSG)

    left_open = piece[0] == "("
    right_open = piece[-1] == ")"
    inner = piece[1:-1]
    parts = _split_top_level_commas(inner)
    if len(parts) != 2:
        raise ValueError("Each interval must have two endpoints separated by a comma, e.g. [a, b).")

    left_val = _parse_interval_endpoint(parts[0], variables=variables)
    right_val = _parse_interval_endpoint(parts[1], variables=variables)

    if left_val in (sp.oo, -sp.oo) and not left_open:
        raise ValueError("Use a parenthesis '(' next to -inf or inf, e.g. (-inf, b].")
    if right_val in (sp.oo, -sp.oo) and not right_open:
        raise ValueError("Use a parenthesis ')' next to -inf or inf, e.g. [a, inf).")
    if left_val == sp.oo or right_val == -sp.oo:
        raise ValueError("Lower endpoint cannot be greater than upper endpoint.")
    try:
        if bool(left_val > right_val):
            raise ValueError("Lower endpoint cannot be greater than upper endpoint.")
    except TypeError:
        pass
    return sp.Interval(left_val, right_val, left_open=left_open, right_open=right_open)


def parse_interval(raw: str, variables=None) -> sp.Set:
    """Parse interval notation (with (, [, ), ], inf/oo/∞, U/∪, {a}) into a SymPy Set."""
    pieces = _split_interval_pieces(raw)
    sets = [_parse_interval_piece(p, variables=variables) for p in pieces]
    return sp.Union(*sets) if len(sets) > 1 else sets[0]
