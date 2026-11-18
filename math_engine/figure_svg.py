"""Standalone SVG for a MathFigure spec (the same spec the Studio draws with React).

Used for Notion pages (`notion_sync.figures`), where there is no KaTeX: labels are turned into plain
Unicode text (`z_1` -> z₁, `90^\\circ` -> 90°, `\\sqrt{2}` -> √(2)). Keep this in step with
`practice-studio/src/components/MathFigure/*` when a shape, marker or plot type is added.
"""

from __future__ import annotations

import math
import re
from html import escape
from typing import Any

from math_engine.safe_expr import compile_expr, evaluate

THEMES = {
    "indigo": ("#6366f1", "rgba(99,102,241,0.10)"),
    "blue": ("#0284c7", "rgba(14,165,233,0.10)"),
    "emerald": ("#059669", "rgba(16,185,129,0.10)"),
    "amber": ("#d97706", "rgba(245,158,11,0.10)"),
    "rose": ("#e11d48", "rgba(244,63,94,0.10)"),
    "purple": ("#7c3aed", "rgba(139,92,246,0.10)"),
}
INK, MUTED, GRID = "#1e293b", "#64748b", "#e2e8f0"
FONT = "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
TITLE_H, NOTE_H = 26, 22

_SUP = str.maketrans("0123456789-+n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺ⁿ")
_SUB = str.maketrans("0123456789-+", "₀₁₂₃₄₅₆₇₈₉₋₊")
_SYMBOLS = {
    "pi": "π",
    "theta": "θ",
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "Delta": "Δ",
    "delta": "δ",
    "omega": "ω",
    "cdot": "·",
    "times": "×",
    "le": "≤",
    "leq": "≤",
    "ge": "≥",
    "geq": "≥",
    "ne": "≠",
    "neq": "≠",
    "infty": "∞",
    "pm": "±",
    "approx": "≈",
    "angle": "∠",
    "circ": "°",
    "degree": "°",
    "cup": "∪",
    "cap": "∩",
    "in": "∈",
    "notin": "∉",
    "subset": "⊂",
    "to": "→",
    "rightarrow": "→",
    "Rightarrow": "⇒",
    "iff": "⇔",
    "emptyset": "∅",
    "varnothing": "∅",
    "Sigma": "Σ",
    "Pi": "Π",
    "Omega": "Ω",
    "Theta": "Θ",
    "Lambda": "Λ",
    "Phi": "Φ",
    "lambda": "λ",
    "mu": "μ",
    "sigma": "σ",
    "phi": "φ",
    "rho": "ρ",
    "epsilon": "ε",
}
_BLACKBOARD = {"R": "ℝ", "N": "ℕ", "Z": "ℤ", "Q": "ℚ", "C": "ℂ"}


def to_unicode(text: Any) -> str:
    """LaTeX-ish label to plain Unicode text (not escaped)."""
    s = str(text or "").replace("\\$", "\x00").replace("$", "").replace("\x00", "$")
    s = re.sub(r"\b(sqrt|cbrt)\(", lambda m: "√(" if m.group(1) == "sqrt" else "∛(", s)
    s = re.sub(r"\^\{?\\circ\}?", "°", s)
    s = re.sub(r"\\mathbb\{(\w)\}", lambda m: _BLACKBOARD.get(m.group(1), m.group(1)), s)
    s = re.sub(r"\\(?:text|textrm|textit|textbf|textsf|texttt|mathrm|mathbf|operatorname)\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\(?:bar|overline)\{([^{}]*)\}", lambda m: "".join(c + "\u0304" for c in m.group(1)), s)
    s = re.sub(r"\\sqrt\[3\]\{([^{}]*)\}", r"∛(\1)", s)
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"√(\1)", s)
    s = re.sub(r"([√∛])\((\w)\)", r"\1\2", s)  # √(x) -> √x for a single symbol
    s = re.sub(
        r"\\d?frac\{([^{}]*)\}\{([^{}]*)\}",
        lambda m: "/".join(g if re.fullmatch(r"\w+", g) else f"({g})" for g in m.groups()),
        s,
    )
    s = re.sub(r"\\([A-Za-z]+)", lambda m: _SYMBOLS.get(m.group(1), m.group(1)), s)
    s = s.replace("\\,", " ").replace("\\ ", " ").replace("\\;", " ")

    def sup(m: re.Match) -> str:
        body = m.group(1) or m.group(2)
        return body.translate(_SUP) if re.fullmatch(r"[0-9n+-]+", body) else f"^({body})"

    def sub(m: re.Match) -> str:
        body = m.group(1) or m.group(2)
        return body.translate(_SUB) if re.fullmatch(r"[0-9+-]+", body) else f"_{body}"

    s = re.sub(r"\^\{([^{}]*)\}|\^([0-9n])", sup, s)
    s = re.sub(r"_\{([^{}]*)\}|_([0-9])", sub, s)
    return s.replace("{", "").replace("}", "").replace("\\", "")


def plain(text: Any) -> str:
    """LaTeX-ish label to plain Unicode text, XML-escaped."""
    return escape(to_unicode(text), quote=False)


# Math in figures uses KaTeX's own fonts (embedded below), as Notion and the Studio do for equations:
# numbers, operators and function names upright (KaTeX_Main), single-letter variables italic (KaTeX_Math).
# Words of prose (titles, notes, "true root") stay in the sans-serif UI font.
MATH_FONT = "KaTeX_Main, 'Latin Modern Roman', 'STIX Two Text', 'Times New Roman', serif"
VAR_FONT = "KaTeX_Math, 'Latin Modern Math', 'STIX Two Math', 'Times New Roman', serif"
MATH_WORDS = {"sin", "cos", "tan", "cot", "sec", "csc", "ln", "log", "exp", "lim", "max", "min", "Re", "Im", "mod"}
_TOKEN = re.compile(r"([A-Za-z\u0370-\u03ff]+\u0304?)|([^A-Za-z\u0370-\u03ff]+)")  # ∪ ℝ → … are non-letters: upright


def _font_face() -> str:
    """@font-face rules with the two KaTeX fonts as data URIs (an SVG shown as an image cannot fetch fonts)."""
    import base64
    from pathlib import Path

    fonts = Path(__file__).with_name("fonts")
    rules = []
    for family, name, style in (
        ("KaTeX_Main", "KaTeX_Main-Regular.woff2", "normal"),
        ("KaTeX_Math", "KaTeX_Math-Italic.woff2", "italic"),
    ):
        data = base64.b64encode((fonts / name).read_bytes()).decode()
        rules.append(
            f"@font-face{{font-family:{family};font-style:{style};font-weight:normal;"
            f"src:url(data:font/woff2;base64,{data}) format('woff2');}}"
        )
    return "".join(rules)


def _spans(text: Any, mode: str) -> str:
    """Text as <tspan>s: math in KaTeX fonts, prose words in sans. mode: mixed | math | sans."""
    s = to_unicode(text)
    if mode == "sans":
        return escape(s, quote=False)
    tokens = _TOKEN.findall(s)

    def prose(i: int) -> bool:
        return 0 <= i < len(tokens) and bool(tokens[i][0]) and tokens[i][0] not in MATH_WORDS and len(tokens[i][0]) > 1

    out = []
    for i, (word, other) in enumerate(tokens):
        if other and not (other == "-" and prose(i - 1) and prose(i + 1)):  # "one-to-one" keeps its hyphen
            other = other.replace("-", "\u2212")
        chunk = escape(word or other, quote=False)
        if mode != "math" and other and not other.strip():
            out.append(chunk)  # spaces between words need no font
        elif mode == "math" or (other and not (other == "-" and prose(i - 1))):
            out.append(f'<tspan font-family="{MATH_FONT}" font-weight="400">{chunk}</tspan>')
        elif word in MATH_WORDS:
            out.append(f'<tspan font-family="{MATH_FONT}" font-weight="400">{chunk}</tspan>')
        elif len(word.rstrip("\u0304")) == 1 and not ("\u0391" <= word[0] <= "\u03a9"):  # Δ, Σ upright, as KaTeX
            out.append(f'<tspan font-family="{VAR_FONT}" font-style="italic" font-weight="400">{chunk}</tspan>')
        elif len(word.rstrip("\u0304")) == 1:  # capital Greek: upright, as KaTeX
            out.append(f'<tspan font-family="{MATH_FONT}" font-weight="400">{chunk}</tspan>')
        else:
            out.append(chunk)  # prose: inherits the sans-serif font of <text>
    return "".join(out)


def _text(
    x: float,
    y: float,
    s: Any,
    size: int = 12,
    anchor: str = "middle",
    color: str = INK,
    extra: str = "",
    mode: str = "mixed",
) -> str:
    """mode: `mixed` (math in KaTeX fonts, prose in sans), `math` (all KaTeX_Main, e.g. tick numbers), `sans`."""
    # One alphabetic baseline for every tspan (dominant-baseline does not carry across fonts); +0.35em = centred.
    return (
        f'<text x="{x:.1f}" y="{y + 0.35 * size:.1f}" text-anchor="{anchor}" font-family="{FONT}" '
        f'font-size="{size}" font-weight="600" fill="{color}" xml:space="preserve" {extra}>{_spans(s, mode)}</text>'
    )


_POS = {
    "top": (0, -16, "middle"),
    "bottom": (0, 16, "middle"),
    "left": (-10, 0, "end"),
    "right": (10, 0, "start"),
    "top-left": (-8, -12, "end"),
    "top-right": (8, -12, "start"),
    "bottom-left": (-8, 12, "end"),
    "bottom-right": (8, 12, "start"),
}


def _dash(item: dict) -> str:
    d = item.get("strokeDasharray")
    return f' stroke-dasharray="{d}"' if d else ""


class _Markers:
    """Arrowhead <marker> defs, one per colour."""

    def __init__(self) -> None:
        self.colors: dict[str, str] = {}

    def ref(self, color: str) -> str:
        mid = self.colors.setdefault(color, f"arr{len(self.colors)}")
        return f' marker-end="url(#{mid})"'

    def defs(self) -> str:
        return "".join(
            f'<marker id="{mid}" viewBox="0 0 10 10" refX="8" refY="5" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" '
            f'orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="{c}"/></marker>'
            for c, mid in self.colors.items()
        )


def figure_to_svg(figure: dict, width: int = 420, height: int = 280) -> str:
    """A self-contained SVG string with an explicit size (Notion needs one), title on top and note below."""
    kind = figure.get("kind")
    stroke, fill = THEMES.get(figure.get("theme", "indigo"), THEMES["indigo"])
    markers = _Markers()
    if kind == "cartesian_graph" and figure.get("yAxis") is False:
        height = min(height, 110)  # a number line is one row
    if kind == "geometry_2d":
        body = _geometry(figure, stroke, fill, width, height, markers)
    elif kind == "cartesian_graph":
        body = _cartesian(figure, stroke, fill, width, height, markers)
    else:
        body = ""
    top = TITLE_H if figure.get("title") else 0
    bottom = NOTE_H if figure.get("note") else 0
    total = height + top + bottom
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {total}" width="{width}" height="{total}">',
        f"<defs><style>{_font_face()}</style>{markers.defs()}</defs>",
        f'<rect width="{width}" height="{total}" fill="#f8fafc" rx="14"/>',
    ]
    if top:
        parts.append(_text(16, 16, figure["title"], size=12, anchor="start", color=MUTED))
    parts.append(f'<g transform="translate(0,{top})">{body}</g>')
    if bottom:
        parts.append(
            _text(
                width - 16,
                top + height + 8,
                figure["note"],
                size=11,
                anchor="end",
                color=MUTED,
                extra='font-style="italic"',
                mode="sans",
            )
        )
    parts.append("</svg>")
    return "\n".join(parts)


# ----------------------------------------------------------------------------- geometry


def _geometry(fig: dict, stroke: str, fill: str, w: int, h: int, markers: _Markers) -> str:
    pad = 45
    pts = fig.get("points", {}) or {}
    coords = [list(p) for p in pts.values()]
    for sh in fig.get("shapes", []):
        c = pts.get(sh.get("center"))
        if c is None:
            continue
        rx = sh.get("radius", sh.get("radiusX", 0)) or 0
        ry = sh.get("radius", sh.get("radiusY", 0)) or 0
        coords += [[c[0] - rx, c[1] - ry], [c[0] + rx, c[1] + ry]]
    if not coords:
        coords = [[0, 0], [10, 10]]
    min_x, max_x = min(p[0] for p in coords), max(p[0] for p in coords)
    min_y, max_y = min(p[1] for p in coords), max(p[1] for p in coords)
    ww, wh = max(max_x - min_x, 1e-4), max(max_y - min_y, 1e-4)
    scale = min((w - 2 * pad) / ww, (h - 2 * pad) / wh)
    off_x = pad + ((w - 2 * pad) - ww * scale) / 2
    off_y = pad + ((h - 2 * pad) - wh * scale) / 2

    def sv(p) -> tuple[float, float]:
        return off_x + (p[0] - min_x) * scale, h - (off_y + (p[1] - min_y) * scale)

    def pt(name):
        return sv(pts[name]) if name in pts else None

    out: list[str] = []
    for sh in fig.get("shapes", []):
        t, col = sh.get("type"), sh.get("stroke") or stroke
        f = fill if sh.get("fill") else "none"
        if t == "polygon":
            vs = [pt(v) for v in sh.get("vertices", []) if v in pts]
            if len(vs) >= 2:
                out.append(
                    f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in vs)}" fill="{f}" stroke="{col}" '
                    f'stroke-width="2.5" stroke-linejoin="round"{_dash(sh)}/>'
                )
        elif t == "segment" and pt(sh.get("from")) and pt(sh.get("to")):
            (x1, y1), (x2, y2) = pt(sh["from"]), pt(sh["to"])
            arrow = markers.ref(col) if sh.get("arrow") else ""
            out.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" '
                f'stroke-width="{sh.get("strokeWidth", 2)}"{_dash(sh)}{arrow}/>'
            )
        elif t == "circle" and pt(sh.get("center")):
            cx, cy = pt(sh["center"])
            out.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{sh.get("radius", 1) * scale:.1f}" fill="{f}" stroke="{col}" '
                f'stroke-width="2"{_dash(sh)}/>'
            )
        elif t == "ellipse" and pt(sh.get("center")):
            cx, cy = pt(sh["center"])
            out.append(
                f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{sh.get("radiusX", 1) * scale:.1f}" '
                f'ry="{sh.get("radiusY", 1) * scale:.1f}" fill="{f}" stroke="{col}" stroke-width="2"{_dash(sh)}/>'
            )
        elif t == "arc" and pt(sh.get("center")):
            cx, cy = pt(sh["center"])
            r = sh.get("radius", 1) * scale
            a0, a1 = math.radians(sh.get("startAngle", 0)), math.radians(sh.get("endAngle", 90))
            x0, y0 = cx + r * math.cos(a0), cy - r * math.sin(a0)
            x1, y1 = cx + r * math.cos(a1), cy - r * math.sin(a1)
            large = 1 if (sh.get("endAngle", 90) - sh.get("startAngle", 0)) % 360 > 180 else 0
            out.append(
                f'<path d="M{x0:.1f},{y0:.1f} A{r:.1f},{r:.1f} 0 {large} 0 {x1:.1f},{y1:.1f}" fill="none" '
                f'stroke="{col}" stroke-width="2"/>'
            )

    for mk in fig.get("markers", []):
        t = mk.get("type")
        if t in ("right_angle", "angle_arc"):
            v, a, b = pt(mk.get("vertex")), pt(mk.get("arm1")), pt(mk.get("arm2"))
            if not (v and a and b):
                continue
            if t == "right_angle":
                u1 = _unit(a[0] - v[0], a[1] - v[1])
                u2 = _unit(b[0] - v[0], b[1] - v[1])
                s = 14.0
                p1 = (v[0] + u1[0] * s, v[1] + u1[1] * s)
                cor = (v[0] + (u1[0] + u2[0]) * s, v[1] + (u1[1] + u2[1]) * s)
                p2 = (v[0] + u2[0] * s, v[1] + u2[1] * s)
                out.append(
                    f'<polyline points="{p1[0]:.1f},{p1[1]:.1f} {cor[0]:.1f},{cor[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" '
                    f'fill="none" stroke="{stroke}" stroke-width="1.6"/>'
                )
            else:
                r = mk.get("radius") or 24
                aa = math.atan2(a[1] - v[1], a[0] - v[0])
                sweep = math.atan2(b[1] - v[1], b[0] - v[0]) - aa
                sweep = (sweep + math.pi) % (2 * math.pi) - math.pi
                s0 = (v[0] + math.cos(aa) * r, v[1] + math.sin(aa) * r)
                s1 = (v[0] + math.cos(aa + sweep) * r, v[1] + math.sin(aa + sweep) * r)
                out.append(
                    f'<path d="M{s0[0]:.1f},{s0[1]:.1f} A{r},{r} 0 0 {1 if sweep > 0 else 0} {s1[0]:.1f},{s1[1]:.1f}" '
                    f'fill="none" stroke="{stroke}" stroke-width="1.6"/>'
                )
                if mk.get("label"):
                    mid = aa + sweep / 2
                    out.append(
                        _text(
                            v[0] + math.cos(mid) * (r + 14),
                            v[1] + math.sin(mid) * (r + 14),
                            mk["label"],
                            11,
                            color="#b45309",
                        )
                    )
        elif t == "tick" and pt(mk.get("p1")) and pt(mk.get("p2")):
            (x1, y1), (x2, y2) = pt(mk["p1"]), pt(mk["p2"])
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ux, uy = _unit(x2 - x1, y2 - y1)
            for i in range(int(mk.get("count", 1))):
                o = (i - (int(mk.get("count", 1)) - 1) / 2) * 5
                cx, cy = mx + ux * o, my + uy * o
                out.append(
                    f'<line x1="{cx - uy * 6:.1f}" y1="{cy + ux * 6:.1f}" x2="{cx + uy * 6:.1f}" y2="{cy - ux * 6:.1f}" '
                    f'stroke="{stroke}" stroke-width="1.6"/>'
                )

    hidden = set(fig.get("hideDots") or [])
    for name in pts:
        if name in hidden:
            continue
        x, y = pt(name)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{INK}" stroke="#ffffff" stroke-width="1.5"/>')

    for lb in fig.get("labels", []):
        t = lb.get("type")
        if t == "point" and pt(lb.get("point")):
            x, y = pt(lb["point"])
            dx, dy, anchor = _POS.get(lb.get("position", "top"), _POS["top"])
            out.append(_text(x + dx, y + dy, lb.get("text") or lb["point"], 12, anchor))
        elif t == "segment" and pt(lb.get("p1")) and pt(lb.get("p2")):
            (x1, y1), (x2, y2) = pt(lb["p1"]), pt(lb["p2"])
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            off, side = lb.get("offset", 16), lb.get("side", "auto")
            if side in ("top", "bottom", "left", "right"):
                mx += {"left": -off, "right": off}.get(side, 0)
                my += {"top": -off, "bottom": off}.get(side, 0)
            else:
                nx, ny = _unit(-(y2 - y1), x2 - x1)
                mx, my = mx + nx * off, my + ny * off
            out.append(_text(mx, my, lb.get("text", ""), 12))
        elif t == "free" and lb.get("coord"):
            x, y = sv(lb["coord"])
            out.append(_text(x, y, lb.get("text", ""), 12))
    return "\n".join(out)


def _unit(dx: float, dy: float) -> tuple[float, float]:
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d


# ----------------------------------------------------------------------------- cartesian


def nice_step(lo: float, hi: float, target: int = 6) -> float:
    span = max(hi - lo, 1e-4)
    raw = span / target
    power = 10 ** math.floor(math.log10(raw))
    norm = raw / power
    mult = 1 if norm < 1.6 else 2 if norm < 3.5 else 5 if norm < 7.5 else 10
    step = mult * power
    return 1.0 if span >= 6 and step < 1 else round(step, 4)


def _ticks(lo: float, hi: float, step: float) -> list[float]:
    out, v = [], math.ceil(lo / step) * step
    while v <= hi + 1e-9:
        out.append(round(v, 6))
        v += step
    return out


def _cartesian(fig: dict, stroke: str, fill: str, w: int, h: int, markers: _Markers) -> str:
    pad = 38
    x0, x1 = fig.get("xRange", [-5, 5])
    y0, y1 = fig.get("yRange", [-5, 5])
    show_y = fig.get("yAxis", True) is not False
    xs = fig.get("xStep") or nice_step(x0, x1)
    ys = fig.get("yStep") or nice_step(y0, y1)

    def sx(v: float) -> float:
        return pad + (v - x0) / max(x1 - x0, 1e-4) * (w - 2 * pad)

    def sy(v: float) -> float:
        return h - pad - (v - y0) / max(y1 - y0, 1e-4) * (h - 2 * pad)

    ox = min(max(sx(0), pad), w - pad)
    oy = min(max(sy(0), pad), h - pad) if show_y else h / 2
    if not show_y:
        sy = lambda v: oy - v * 0  # noqa: E731 - a number line has one row
    out: list[str] = [
        f'<clipPath id="vp"><rect x="{pad}" y="{pad - 6}" width="{w - 2 * pad}" height="{h - 2 * pad + 12}"/></clipPath>'
    ]

    if fig.get("grid", True) and show_y:
        for v in _ticks(x0, x1, xs):
            if abs(v) > 1e-9:
                out.append(
                    f'<line x1="{sx(v):.1f}" y1="{pad}" x2="{sx(v):.1f}" y2="{h - pad}" stroke="{GRID}" stroke-dasharray="2 2"/>'
                )
        for v in _ticks(y0, y1, ys):
            if abs(v) > 1e-9:
                out.append(
                    f'<line x1="{pad}" y1="{sy(v):.1f}" x2="{w - pad}" y2="{sy(v):.1f}" stroke="{GRID}" stroke-dasharray="2 2"/>'
                )

    axis_ref = markers.ref(MUTED)
    labels = fig.get("axisLabels") or ["x", "y"]
    out.append(
        f'<line x1="{pad - 10}" y1="{oy:.1f}" x2="{w - pad + 12}" y2="{oy:.1f}" stroke="{MUTED}" stroke-width="1.8"{axis_ref}/>'
    )
    out.append(_text(w - pad + 18, oy - 12, labels[0], 13, "middle", MUTED))
    if show_y:
        out.append(
            f'<line x1="{ox:.1f}" y1="{h - pad + 10}" x2="{ox:.1f}" y2="{pad - 12}" stroke="{MUTED}" stroke-width="1.8"{axis_ref}/>'
        )
        out.append(_text(ox - 8, pad - 16, labels[1], 13, "end", MUTED))
    vlines = [
        p
        for p in fig.get("plots", [])
        if p.get("type") == "segment"
        and p.get("strokeDasharray")
        and p.get("from", [0, 0])[0] == p.get("to", [0, 0])[0]
    ]
    hlines = [
        p
        for p in fig.get("plots", [])
        if p.get("type") == "segment"
        and p.get("strokeDasharray")
        and p.get("from", [0, 0])[1] == p.get("to", [0, 0])[1]
    ]
    for v in _ticks(x0, x1, xs):
        if show_y and abs(sx(v) - ox) < 18 or any(abs(v - p["from"][0]) < xs * 0.04 for p in vlines):
            continue
        if abs(v) > 1e-9 or not show_y:
            out.append(
                f'<line x1="{sx(v):.1f}" y1="{oy - 3:.1f}" x2="{sx(v):.1f}" y2="{oy + 3:.1f}" stroke="{MUTED}" stroke-width="1.2"/>'
            )
            out.append(_text(sx(v), oy + 13, f"{v:g}", 10, "middle", MUTED, mode="math"))
    if show_y:
        for v in _ticks(y0, y1, ys):
            if any(abs(v - p["from"][1]) < ys * 0.04 for p in hlines):
                continue
            if abs(v) > 1e-9:
                out.append(
                    f'<line x1="{ox - 3:.1f}" y1="{sy(v):.1f}" x2="{ox + 3:.1f}" y2="{sy(v):.1f}" stroke="{MUTED}" stroke-width="1.2"/>'
                )
                out.append(_text(ox - 6, sy(v), f"{v:g}", 10, "end", MUTED, mode="math"))
        if x0 < 0 < x1 and y0 < 0 < y1:
            out.append(_text(ox - 6, oy + 12, "0", 10, "end", MUTED, mode="math"))

    lines: list[str] = []
    top: list[str] = []
    for p in fig.get("plots", []):
        t, col = p.get("type"), p.get("color") or stroke
        sw = p.get("strokeWidth", 2.4)
        if t in ("function", "curve"):
            for run in _runs(p, x0, x1):
                pts = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in run)
                lines.append(
                    f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round"{_dash(p)}/>'
                )
        elif t == "area":
            pts = _area(p, x0, x1)
            if pts:
                lines.append(
                    f'<polygon points="{" ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in pts)}" fill="{p.get("color") or fill}" '
                    f'fill-opacity="{p.get("opacity", 0.35)}" stroke="none"/>'
                )
        elif t == "segment":
            (ax, ay), (bx, by) = p.get("from", [0, 0]), p.get("to", [0, 0])
            arrow = markers.ref(p.get("color") or "#94a3b8") if p.get("arrow") else ""
            lines.append(
                f'<line x1="{sx(ax):.1f}" y1="{sy(ay):.1f}" x2="{sx(bx):.1f}" y2="{sy(by):.1f}" '
                f'stroke="{p.get("color") or "#94a3b8"}" stroke-width="{p.get("strokeWidth", 2)}"{_dash(p)}{arrow}/>'
            )
        elif t == "slope_triangle":
            (ax, ay), (bx, by) = p["p1"], p["p2"]
            a, c, b = (sx(ax), sy(ay)), (sx(bx), sy(ay)), (sx(bx), sy(by))
            lines.append(
                f'<polygon points="{a[0]:.1f},{a[1]:.1f} {c[0]:.1f},{c[1]:.1f} {b[0]:.1f},{b[1]:.1f}" fill="rgba(245,158,11,0.12)" stroke="none"/>'
            )
            for (px, py), (qx, qy) in ((a, c), (c, b)):
                lines.append(
                    f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{qx:.1f}" y2="{qy:.1f}" stroke="#d97706" stroke-width="2" stroke-dasharray="4 3"/>'
                )
            lines.append(
                f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{stroke}" stroke-width="2.5"/>'
            )
        elif t == "point":
            x, y = sx(p["coord"][0]), sy(p["coord"][1])
            face = "#ffffff" if p.get("hollow") else col
            top.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{face}" stroke="{col}" stroke-width="2"/>')
            if p.get("label"):
                dx, dy, anchor = _POS.get(p.get("position", "top-right"), _POS["top-right"])
                top.append(_text(x + dx, y + dy, p["label"], 11, anchor))
        elif t == "text":
            top.append(
                _text(
                    sx(p["coord"][0]),
                    sy(p["coord"][1]),
                    p.get("text", ""),
                    12,
                    p.get("anchor", "middle"),
                    color=p.get("color") or INK,
                )
            )
    out.append(f'<g clip-path="url(#vp)">{"".join(lines)}</g>')
    out += top
    return "\n".join(out)


def _runs(plot: dict, x0: float, x1: float) -> list[list[tuple[float, float]]]:
    if plot.get("type") == "curve":
        return [[(float(x), float(y)) for x, y in plot.get("points", [])]]
    lo, hi = plot.get("domain") or [x0, x1]
    lo, hi = max(lo, x0), min(hi, x1)
    coeffs, fn = plot.get("coefficients"), plot.get("fn")
    tree = compile_expr(fn) if fn and not coeffs else None
    runs, cur = [], []
    for i in range(121):
        x = lo + (hi - lo) * i / 120
        try:
            y = (
                sum(c * x ** (len(coeffs) - 1 - k) for k, c in enumerate(coeffs))
                if coeffs
                else evaluate(tree, {"x": x})
            )
        except (ArithmeticError, ValueError, KeyError, TypeError):
            y = None
        if y is None:
            if len(cur) > 1:
                runs.append(cur)
            cur = []
        else:
            cur.append((x, y))
    if len(cur) > 1:
        runs.append(cur)
    return runs


def _area(plot: dict, x0: float, x1: float) -> list[tuple[float, float]]:
    lo, hi = plot.get("domain") or [x0, x1]
    try:
        f1 = compile_expr(plot["fn1"])
        f2 = compile_expr(plot["fn2"]) if plot.get("fn2") else None
        xs = [lo + (hi - lo) * i / 60 for i in range(61)]
        upper = [(x, evaluate(f1, {"x": x})) for x in xs]
        lower = [(x, evaluate(f2, {"x": x}) if f2 else 0.0) for x in reversed(xs)]
    except (ArithmeticError, ValueError, KeyError, TypeError):
        return []
    return upper + lower
