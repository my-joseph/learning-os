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
import urllib.request
import uuid
from collections.abc import Callable

from math_engine import figure_builder
from math_engine.figure_svg import figure_to_svg
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


def image_block(upload_id: str, caption: str = "") -> dict:
    block = {"object": "block", "type": "image", "image": {"type": "file_upload", "file_upload": {"id": upload_id}}}
    if caption:
        block["image"]["caption"] = [{"type": "text", "text": {"content": caption[:1900]}}]
    return block


def figure_block(item: dict, uploader: Uploader, name: str = "figure") -> dict:
    """Build, render and upload one figure; returns the Notion image block."""
    svg = figure_to_svg(figure_from_spec(item))
    return image_block(uploader(svg, f"{name}.svg"), item.get("caption", ""))


def dry_run_uploader(svg: str, filename: str) -> str:
    """Stand-in for --dry-run: the figure is built and rendered, nothing is sent."""
    return "dry-run-" + filename
