"""Figures on Notion pages: render a MathFigure spec to SVG and upload it as a native Notion image.

A page spec block (`notion_sync.unit_page`) of type `figure` names a builder from `math_engine.figure_builder`
and its arguments, or gives a ready figure spec:

    {"type": "figure", "fn": "build_function_graph_figure",
     "args": {"expr": "(x-1)^2 - 4", "x_min": -2, "x_max": 4, "mark_x": "1", "mark_labels": "vertex"},
     "caption": "The vertex is the lowest point."}
    {"type": "figure", "figure": {"kind": "cartesian_graph", ...}}

Upload uses the Notion File Upload API (`POST /v1/file_uploads`, then multipart `send`), TLS verified through
`notion_sync.client.SSL_CTX`.
"""

from __future__ import annotations

import json
import re
import urllib.request
import uuid
from collections.abc import Callable

from math_engine import figure_builder
from math_engine.figure_svg import figure_to_svg
from notion_sync.blocks import parse_rt
from notion_sync.client import NOTION_VERSION, SSL_CTX, notion_request

Uploader = Callable[[str, str], str]  # (svg, filename) -> file_upload id


def figure_from_spec(item: dict) -> dict:
    """The MathFigure spec for a page-spec `figure` block; raises ValueError when it cannot be built."""
    if isinstance(item.get("figure"), dict):
        fig = dict(item["figure"])
    else:
        name = str(item.get("fn", ""))
        fn = getattr(figure_builder, name, None) if name.startswith("build_") else None
        if fn is None:
            raise ValueError(
                f"figure block needs 'fn' (a build_* function in math_engine.figure_builder) or 'figure'; got {name!r}"
            )
        try:
            fig = fn(**(item.get("args") or {}))
        except TypeError as exc:
            raise ValueError(f"{name}: {exc}") from exc
    if item.get("title"):
        fig["title"] = item["title"]
    if item.get("note"):
        fig["note"] = item["note"]
    if fig.get("kind") not in ("geometry_2d", "cartesian_graph"):
        raise ValueError(f"figure kind must be geometry_2d or cartesian_graph, got {fig.get('kind')!r}")
    return fig


def upload_svg(svg: str, filename: str, token: str) -> str:
    """Upload an SVG with the File Upload API; returns the file_upload id to attach in an image block."""
    created = notion_request(
        "POST", "file_uploads", token, {"mode": "single_part", "filename": filename, "content_type": "image/svg+xml"}
    )
    boundary = uuid.uuid4().hex
    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            "Content-Type: image/svg+xml\r\n\r\n"
        ).encode()
        + svg.encode("utf-8")
        + f"\r\n--{boundary}--\r\n".encode()
    )
    req = urllib.request.Request(
        created.get("upload_url") or f"https://api.notion.com/v1/file_uploads/{created['id']}/send",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=60) as resp:
        status = json.loads(resp.read().decode("utf-8")).get("status")
    if status != "uploaded":
        raise RuntimeError(f"Notion file upload {created['id']} ended as {status!r}")
    return created["id"]


def caption_rich_text(caption: str, id_map: dict) -> list[dict]:
    """Caption as Notion rich text with the page-text syntax: `$math$` becomes an inline equation,
    `[[CODE]]` a page mention, `**bold**` bold (a plain-text caption would show LaTeX or `sqrt(...)` raw)."""
    check_plain_math(caption, "caption")
    return parse_rt(caption[:1900], id_map)


def image_block(upload_id: str, caption: str = "", id_map: dict | None = None) -> dict:
    block = {"object": "block", "type": "image", "image": {"type": "file_upload", "file_upload": {"id": upload_id}}}
    if caption:
        block["image"]["caption"] = caption_rich_text(caption, id_map or {})
    return block


# Math written as plain text outside `$...$`: `sqrt(x + 2)`, `x^2`, `\frac`, `\sqrt`.
_PLAIN_MATH = re.compile(r"\bsqrt\(|\bcbrt\(|[A-Za-z0-9)\]]\^[A-Za-z0-9({]|\\(?:frac|sqrt|cdot|le|ge|infty|pi|Delta)\b")


def check_plain_math(text: str, where: str = "text") -> None:
    """Refuse math outside `$...$`, so it renders as an equation on Notion instead of `sqrt(x + 2)`."""
    outside = re.sub(r"(?<!\\)\$(?:\\\$|[^$])+?(?<!\\)\$|`[^`]*`", " ", str(text or ""))
    m = _PLAIN_MATH.search(outside)
    if m:
        raise ValueError(
            f"{where}: math written as plain text near {outside[max(0, m.start() - 15) : m.end() + 15]!r}; "
            "wrap it in $...$ (e.g. $\\sqrt{x+2}$, $x^2$) so Notion renders it"
        )


def figure_block(item: dict, uploader: Uploader, name: str = "figure", id_map: dict | None = None) -> dict:
    """Build, render and upload one figure; returns the Notion image block."""
    caption = item.get("caption", "")
    check_plain_math(caption, "figure caption")  # before uploading anything
    svg = figure_to_svg(figure_from_spec(item))
    return image_block(uploader(svg, f"{name}.svg"), caption, id_map)


def dry_run_uploader(svg: str, filename: str) -> str:
    """Stand-in for --dry-run: the figure is built and rendered, nothing is sent."""
    return "dry-run-" + filename
