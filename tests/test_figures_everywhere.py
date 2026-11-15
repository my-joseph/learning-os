"""Figures for every visual topic: safe expressions, `?` labels, new builders, SVG parity, the figure decision
gate (03_stem §3.1) and figure blocks on Notion pages (notion_sync.figures, unit_page)."""

import glob
import inspect
import io
import json
import xml.dom.minidom

import pytest

from math_engine import figure_builder as fb
from math_engine.ai_drill_ingest import AiContractError, require_figure_decision
from math_engine.figure_autofill import build_figure
from math_engine.figure_svg import figure_to_svg, plain
from math_engine.safe_expr import evaluate, try_evaluate
from notion_sync import figures as nf
from notion_sync import unit_page as up


def test_safe_expr_reads_math_and_refuses_code():
    assert evaluate("sqrt(V/(pi*h))", {"V": 36 * 3.141592653589793, "h": 4}) == pytest.approx(3)
    assert evaluate("2*(x-1)^2 - 3", {"x": 3}) == 5
    assert evaluate("abs(x) + ln(e)", {"x": -2}) == 3
    for bad in ("__import__('os')", "x.real", "[1,2]", "'a'", "open('f')", "lambda: 1"):
        assert try_evaluate(bad, {"x": 1}) is None, bad
    assert try_evaluate("1/x", {"x": 0}) is None
    assert try_evaluate("sqrt(x)", {"x": -1}) is None
    assert try_evaluate("y + 1", {"x": 1}) is None  # unknown name


def test_question_mark_labels_keep_the_figure_and_add_a_note():
    arch = {
        "figureBuilders": [
            {"fn": "build_circle_figure", "args": {"radius": "sqrt(A/pi)"}, "labels": {"label_radius": "r = ?"}}
        ]
    }
    fig = build_figure(arch, {"A": 50.26548})
    assert fig["shapes"][0]["radius"] == pytest.approx(4, abs=0.01)
    assert fig["labels"][1]["text"] == "r = ?"
    assert fig["note"] == "Not to scale"
    plain_arch = {"figureBuilders": [{"fn": "build_circle_figure", "args": {"radius": "r"}}]}
    assert "note" not in build_figure(plain_arch, {"r": 3})


def test_every_archetype_has_a_figure_decision_gate():
    undecided = {"archetypeKey": "k"}
    with pytest.raises(AiContractError, match="figure decision"):
        require_figure_decision({"id": "Q1", "archetypeKey": "k"}, [undecided])
    require_figure_decision({"id": "Q1", "archetypeKey": "k"}, [{"archetypeKey": "k", "figureNone": "symbolic"}])
    with pytest.raises(AiContractError):
        require_figure_decision({"id": "Q1", "archetypeKey": "k"}, [{"archetypeKey": "k", "figureNone": "  "}])


def test_vault_figure_builders_name_real_builders_and_parameters():
    """A typo in a vault's figureBuilders would silently fall through to 'no figure'."""
    for path in [
        *glob.glob("math_engine/reasoning_vault/*.json"),
        ".claude/skills/new-math-drill/template/MTH-TEMPLATE.json",
    ]:
        for arch in json.load(open(path, encoding="utf-8"))["archetypes"]:
            for spec in arch.get("figureBuilders") or []:
                fn = getattr(fb, spec["fn"], None)
                assert fn is not None, f"{path}: {arch['archetypeKey']} uses unknown builder {spec['fn']}"
                params = set(inspect.signature(fn).parameters)
                used = set(spec.get("args", {})) | set(spec.get("labels", {}))
                assert used <= params, f"{path}: {arch['archetypeKey']} passes {used - params} to {spec['fn']}"


def test_function_graph_breaks_at_asymptotes_and_marks_points():
    fig = fb.build_function_graph_figure("1/(x-2)", vlines="2")
    curves = [p for p in fig["plots"] if p["type"] == "curve"]
    assert len(curves) == 2  # one branch each side of x = 2
    assert all(x < 2 for x, _ in curves[0]["points"]) and all(x > 2 for x, _ in curves[1]["points"])
    par = fb.build_function_graph_figure("2*(x-1)^2 - 3", x_min=-2, x_max=4, mark_x="1", mark_labels="(1, ?)")
    (pt,) = [p for p in par["plots"] if p["type"] == "point"]
    assert pt["coord"] == [1, -3] and pt["label"] == "(1, ?)"
    assert par["yRange"][0] <= -3 and par["yRange"][1] >= 15
    with pytest.raises(ValueError):
        fb.build_function_graph_figure("sqrt(x)", x_min=-5, x_max=-1)


def test_number_line_open_closed_and_rays():
    fig = fb.build_number_line_figure("(-inf, -2] U (3, inf)")
    dots = {p["coord"][0]: p.get("hollow") for p in fig["plots"] if p["type"] == "point"}
    assert dots == {-2: False, 3: True}
    assert sum(1 for p in fig["plots"] if p["type"] == "segment" and p.get("arrow")) == 2
    assert fig["yAxis"] is False
    with pytest.raises(ValueError):
        fb.build_number_line_figure("x > 3")


def test_complex_plane_conjugate_and_modulus():
    fig = fb.build_complex_plane_figure(6, 5, "z", show_conjugate=True, show_modulus=True, label_modulus="|z| = ?")
    assert fig["axisLabels"] == ["Re", "Im"]
    coords = [p["coord"] for p in fig["plots"] if p["type"] == "point"]
    assert [6, -5] in coords
    assert any(p["type"] == "text" and p["text"] == "|z| = ?" for p in fig["plots"])


ALL_BUILDS = [
    lambda: fb.build_rectangle_figure(12, 5, label_w="12\\text{ m}", label_h="h = ?"),
    lambda: fb.build_right_triangle_figure(6, 8),
    lambda: fb.build_circle_figure(3),
    lambda: fb.build_cone_figure(3, 4),
    lambda: fb.build_cylinder_figure(2, 5),
    lambda: fb.build_transversal_figure(),
    lambda: fb.build_cartesian_slope_triangle_figure((1, 2), (4, 8), 2),
    lambda: fb.build_cartesian_line_figure(2, -3),
    lambda: fb.build_function_graph_figure("sin(x)", x_min=-6, x_max=6),
    lambda: fb.build_number_line_figure("[-1, 4)"),
    lambda: fb.build_complex_plane_figure(3, -4, "z_1", -2, 1, "z_2"),
]


@pytest.mark.parametrize("build", ALL_BUILDS)
def test_svg_is_well_formed_with_explicit_size(build):
    fig = build()
    fig["note"] = "Not to scale"
    svg = figure_to_svg(fig)
    doc = xml.dom.minidom.parseString(svg)
    root = doc.documentElement
    assert root.getAttribute("width").isdigit() and root.getAttribute("height").isdigit()
    assert "Not to scale" in svg


def test_svg_draws_every_plot_type_the_studio_draws():
    svg = figure_to_svg(fb.build_cartesian_slope_triangle_figure((1, 2), (4, 8), 2))
    assert 'stroke-dasharray="4 3"' in svg  # rise and run legs
    svg = figure_to_svg(fb.build_cone_figure(3, 4))
    assert "<ellipse" in svg
    svg = figure_to_svg(fb.build_transversal_figure())
    assert "<path" in svg  # angle arcs
    svg = figure_to_svg(fb.build_number_line_figure("[-1, 4)"))
    assert "marker-end" in svg and 'fill="#ffffff"' in svg  # ray arrow, hollow dot


def test_plain_labels():
    assert plain("$z_1$") == "z₁"
    assert plain("90^\\circ") == "90°"
    assert plain("\\sqrt{2}") == "√(2)"
    assert plain("x^2 < 4") == "x² &lt; 4"
    assert plain("\\bar{z}") == "z̄"


def test_page_spec_figure_block_uploads_once_per_figure():
    sent = []
    spec = [
        {"type": "p", "text": "Before"},
        {"type": "figure", "fn": "build_number_line_figure", "args": {"intervals": "[0, 2]"}, "caption": "Closed"},
        {"type": "toggle", "text": "Why", "children": [{"type": "figure", "figure": fb.build_circle_figure(2)}]},
    ]
    blocks = up.spec_to_blocks(spec, {}, lambda svg, name: sent.append((svg, name)) or f"id{len(sent)}", "U9")
    assert [n for _, n in sent] == ["U9-1.svg", "U9-2.svg"]
    assert blocks[1]["image"] == {
        "type": "file_upload",
        "file_upload": {"id": "id1"},
        "caption": [{"type": "text", "text": {"content": "Closed"}}],
    }
    assert blocks[2]["toggle"]["children"][0]["image"]["file_upload"]["id"] == "id2"
    with pytest.raises(ValueError, match="build_"):
        up.spec_to_blocks([{"type": "figure", "fn": "os.system"}], {})
    with pytest.raises(ValueError, match="unexpected keyword"):
        up.spec_to_blocks([{"type": "figure", "fn": "build_circle_figure", "args": {"radius": 1, "bad": 2}}], {})


def test_write_page_builds_every_figure_before_uploading(monkeypatch):
    uploads = []
    monkeypatch.setattr(up, "upload_svg", lambda svg, name, token: uploads.append(name) or "fid")
    monkeypatch.setattr(up, "get_all_blocks", lambda pid, token: [])
    monkeypatch.setattr(up, "insert_after", lambda *a, **k: None)
    good = {"type": "figure", "fn": "build_circle_figure", "args": {"radius": 1}}
    bad = {"type": "figure", "fn": "build_circle_figure", "args": {}}
    with pytest.raises(ValueError):
        up.write_page("U", [good, bad], "new", None, "t", {"U": {"id": "p"}})
    assert uploads == []  # nothing half-uploaded
    up.write_page("U", [good], "new", None, "t", {"U": {"id": "p"}})
    assert uploads == ["U-1.svg"]


def test_upload_svg_sends_multipart_to_the_upload_url(monkeypatch):
    monkeypatch.setattr(
        nf,
        "notion_request",
        lambda *a, **k: {"id": "f1", "upload_url": "https://api.notion.com/v1/file_uploads/f1/send"},
    )
    seen = {}

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, context=None, timeout=None):
        seen.update(url=req.full_url, ctype=req.headers["Content-type"], body=req.data, ctx=context)
        return Resp(b'{"status": "uploaded"}')

    monkeypatch.setattr(nf.urllib.request, "urlopen", fake_urlopen)
    assert nf.upload_svg("<svg/>", "a.svg", "tok") == "f1"
    assert seen["url"].endswith("/f1/send") and seen["ctype"].startswith("multipart/form-data; boundary=")
    assert b"<svg/>" in seen["body"] and b'filename="a.svg"' in seen["body"]
    assert seen["ctx"] is nf.SSL_CTX  # TLS verified
