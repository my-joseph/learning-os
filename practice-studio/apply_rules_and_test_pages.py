# -*- coding: utf-8 -*-
import json
import os
import re
import ssl
import time
import urllib.error
import urllib.request

def load_env(path=".env"):
    env = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

SSL_CTX = (
    ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    if os.path.exists("/etc/ssl/cert.pem")
    else ssl._create_unverified_context()
)

def notion_request(method, endpoint, token, payload=None, max_retries=7):
    url = f"https://api.notion.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (409, 429, 500, 502, 503, 504) and attempt < max_retries - 1:
                wait = 1.5 * (2 ** attempt)
                time.sleep(wait)
                continue
            body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {e.code} on {method} {endpoint}: {body}") from e

def get_all_blocks(block_id, token):
    blocks = []
    cursor = None
    while True:
        ep = f"blocks/{block_id}/children?page_size=100"
        if cursor:
            ep += f"&start_cursor={cursor}"
        res = notion_request("GET", ep, token)
        blocks.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")
    return blocks

def default_annotations(bold=False, italic=False, code=False, color="default"):
    return {
        "bold": bold,
        "italic": italic,
        "strikethrough": False,
        "underline": False,
        "code": code,
        "color": color,
    }

def rt(text, bold=False, italic=False, code=False, color="default"):
    return {
        "type": "text",
        "text": {"content": text},
        "annotations": default_annotations(bold=bold, italic=italic, code=code, color=color),
    }

def mention_page(page_id, bold=False):
    return {
        "type": "mention",
        "mention": {"type": "page", "page": {"id": page_id}},
        "annotations": default_annotations(bold=bold),
    }

def eq_inline(expr, bold=False):
    return {
        "type": "equation",
        "equation": {"expression": expr},
        "annotations": default_annotations(bold=bold),
    }

BOLD_SPLIT_RE = re.compile(r"(\*\*[^\*]+\*\*)")
INNER_TOKEN_RE = re.compile(r"(\[\[[A-Z0-9\-]+\]\]|\$[^\$]+\$|`[^`]+`)")

def parse_rt(text, id_map):
    """
    Two-pass rich text parser:
    1. Splits by **bold** segments so tokens inside **...** (such as [[ID]], $math$, or `code`)
       are still parsed into native Notion page mentions, inline equations, or inline code!
    2. Raises ValueError immediately if any [[ID]] is unknown or if any raw [[ or ]] remains.
    """
    bold_Chunks = BOLD_SPLIT_RE.split(text)
    out = []
    for chunk in bold_Chunks:
        if not chunk:
            continue
        is_bold = False
        inner_str = chunk
        if chunk.startswith("**") and chunk.endswith("**") and len(chunk) > 4:
            is_bold = True
            inner_str = chunk[2:-2]

        parts = INNER_TOKEN_RE.split(inner_str)
        for p in parts:
            if not p:
                continue
            if p.startswith("[[") and p.endswith("]]"):
                fid = p[2:-2]
                if fid not in id_map:
                    raise ValueError(f"Unknown Full ID in [[{fid}]] within text: {text}")
                out.append(mention_page(id_map[fid]["id"], bold=is_bold))
            elif p.startswith("$") and p.endswith("$") and len(p) > 2:
                out.append(eq_inline(p[1:-1], bold=is_bold))
            elif p.startswith("`") and p.endswith("`") and len(p) > 2:
                out.append(rt(p[1:-1], bold=is_bold, code=True))
            else:
                if "[[" in p or "]]" in p:
                    raise ValueError(f"Unparsed bracket token in '{p}' within text: {text}")
                out.append(rt(p, bold=is_bold))
    return out if out else [rt("")]

def validate_blocks_clean(blocks, label=""):
    dumped = json.dumps(blocks, ensure_ascii=False)
    unresolved_match = re.search(r"\[\[[A-Z0-9\-]+\]\]", dumped)
    if unresolved_match:
        raise AssertionError(f"[{label}] Found unresolved ID token {unresolved_match.group(0)} in generated blocks!")
    thai_match = re.search(r"[\u0E00-\u0E7F]+", dumped)
    if thai_match:
        raise AssertionError(f"[{label}] Found non-English (Thai) text '{thai_match.group(0)}' in generated blocks!")

def h2(text, id_map):
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": parse_rt(text, id_map)}}

def h3(text, id_map):
    return {"object": "block", "type": "heading_3", "heading_3": {"rich_text": parse_rt(text, id_map)}}

def p_block(text, id_map):
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": parse_rt(text, id_map)}}

def callout_block(text, id_map, color="gray_background"):
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": parse_rt(text, id_map),
            "color": color,
        },
    }

def quote_block(text, id_map):
    return {"object": "block", "type": "quote", "quote": {"rich_text": parse_rt(text, id_map)}}

def divider_block():
    return {"object": "block", "type": "divider", "divider": {}}

def eq_block(expr):
    return {"object": "block", "type": "equation", "equation": {"expression": expr}}

def code_block(code_str, lang="typescript"):
    return {
        "object": "block",
        "type": "code",
        "code": {
            "language": lang,
            "rich_text": [rt(code_str)],
        },
    }

def bullet(text, id_map, children=None):
    b = {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": parse_rt(text, id_map),
        },
    }
    if children:
        b["bulleted_list_item"]["children"] = children
    return b

def num_item(text, id_map, children=None):
    b = {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {
            "rich_text": parse_rt(text, id_map),
        },
    }
    if children:
        b["numbered_list_item"]["children"] = children
    return b

def todo_item(text, id_map, checked=False):
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {
            "rich_text": parse_rt(text, id_map),
            "checked": checked,
        },
    }

def toggle_block(question_text, answer_blocks, id_map):
    children = []
    for item in answer_blocks:
        if isinstance(item, str):
            children.append(p_block(item, id_map))
        else:
            children.append(item)
    return {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": parse_rt(question_text, id_map),
            "children": children,
        },
    }

def replace_page_blocks(page_id, new_blocks, label, token):
    validate_blocks_clean(new_blocks, label=label)
    existing = get_all_blocks(page_id, token)
    for b in existing:
        notion_request("DELETE", f"blocks/{b['id']}", token)
    for i in range(0, len(new_blocks), 50):
        chunk = new_blocks[i:i+50]
        notion_request("PATCH", f"blocks/{page_id}/children", token, {"children": chunk})

def update_rules_page(rules_id, id_map, token):
    print("\n=== Updating 'Learning System — AI Implementation Rules' (100% English + New Rules) ===")
    r_blocks = get_all_blocks(rules_id, token)

    # Delete any previously inserted blocks from our earlier rule updates so we can insert clean, 100% English versions
    for b in r_blocks:
        bt = b["type"]
        txt = ""
        if bt in b and "rich_text" in b[bt]:
            txt = "".join(t.get("plain_text", "") for t in b[bt]["rich_text"])
        if any(phrase in txt for phrase in [
            "Inline Page Mention & Cross-Linking Rule",
            "Multi-Level Practice Guide & Cross-Subject Connection Rules",
            "Do not embed static exercise lists or fixed problem sets",
            "Level 1 — Unit Practice Guide",
            "Level 2 — Chapter Chapter Practice Guide",
            "Level 3 — Topic Topic Practice & Synthesis Guide",
            "Practice Guide is thorough, structured into 4 scannable categories",
            "Every reference to an existing Topic, Chapter, Unit, or Resource ID",
            "Language & Formatting Integrity Rules",
            "Vertical Step-by-Step Mathematical Derivation Rule",
        ]):
            notion_request("DELETE", f"blocks/{b['id']}", token)

    # 1. Add Inline Page Mention & Verification Rule under Section 4 Relationship Rules (after 40c3818f-8ba0-81f2-b080-e0d2430c2d92)
    sec4_blocks = [
        p_block(
            "**Inline Page Mention & Link Verification Rule:** Whenever page content references any record ID that exists in the workspace (`Topic ID`, `Chapter ID`, `Unit ID`, `Full ID`, or `Resource ID` — such as [[MTH-T01-C08]], [[PHY-T01-C19]], [[PRG-T01-C02-U03]], or [[R012]]), AI must insert a clickable Notion page mention (`mention` of type `page`) rather than plain text.",
            id_map,
        ),
        bullet(
            "**Verify All Inline Mentions Render Properly:** Ensure that page mentions inside bold headings, callouts, and nested list items are properly tokenized as Notion `mention` objects and never left as raw double-bracketed IDs. Always inspect the saved page blocks after generation to confirm zero unresolved link tokens remain.",
            id_map,
        ),
    ]
    validate_blocks_clean(sec4_blocks, "Rules-Sec4")
    notion_request("PATCH", f"blocks/{rules_id}/children", token, {
        "after": "40c3818f-8ba0-81f2-b080-e0d2430c2d92",
        "children": sec4_blocks,
    })

    # 2. Add English-Only Rule, Vertical Math Derivation Rule, and Multi-Level Practice Guide Rules under Part 5 (after 40c3818f-8ba0-810e-a652-ff08877b6917)
    part5_blocks = [
        h3("Language, Mathematical Notation & Formatting Integrity Rules", id_map),
        bullet(
            "**Strict English-Only Content Rule:** All generated content across Topic, Chapter, Unit, and Resource pages (including section headings, conceptual explanations, worked examples, `Practice Guide`, `Active Recall`, and `My Implementation & Mistake Log` prompts) must be written strictly in **English**. Never leave non-English (e.g., Thai) text inside Notion pages.",
            id_map,
        ),
        bullet(
            "**Vertical Step-by-Step Mathematical Derivation Rule:** When showing mathematical equation solving, algebraic simplification, or worked examples in `MTH` and `PHY` pages, **never** chain multiple `=` steps horizontally across a single line (`A = B = C = D`). Always format step-by-step mathematical working **vertically from top to bottom** using native Notion block `equation` elements with LaTeX `\\begin{aligned} ... &= ... \\\\ &= ... \\end{aligned}` (or sequential vertical `equation` blocks under each explanatory step) so every transformation step stacks downward clearly like real mathematical writing.",
            id_map,
        ),
        h3("Multi-Level Practice Guide & Cross-Subject Connection Rules (No Static Problem Dump)", id_map),
        p_block(
            "**Core Principle:** Do **not** embed static exercise lists or fixed problem sets directly inside Topic, Chapter, or Unit page bodies. Static problems lose replay value after the first completion and cannot scale with the learner's evolving `Mastery (0-4)` score. Instead, every Unit, Chapter, and Topic must provide a **thorough, content-specific, scannable Practice Guide** in **English**, structured into **4 clear categories with indented sub-bullets** and **clickable `@Page` mentions** to all referenced Topics, Chapters, Units, and Resources.",
            id_map,
        ),
        bullet("**Level 1 — Unit `Practice Guide` (4 Required Categories):**", id_map, children=[
            bullet("**1. Core Skills to Drill:** Specify the exact calculations, algebraic manipulations, runtime traces, type-narrowing patterns, or architectural mechanics the learner must practice until fluent in this Unit, broken down into concrete sub-skills and progression tiers.", id_map),
            bullet("**2. Combine with Prior Units:** Explicitly name and link (via clickable `@Page` mentions) 2–4 specific prior Units or Chapters that should be blended into practice problems, explaining the exact combined scenario.", id_map),
            bullet("**3. Common Traps & Edge Cases to Test:** List the exact sign traps, zero/null boundary conditions, invalid algebraic steps, or compiler/runtime pitfalls unique to this Unit that practice problems must test.", id_map),
            bullet("**4. Cross-Subject & Real-World Connection (Math ↔ Physics ↔ Code):** For `MTH` and `PHY`, explicitly explain which Physics formulas/phenomena and Programming algorithms rely on this Unit's concept (with clickable `@Page` mentions). For `PRG`, explain the exact production architecture scenario and adjacent `PRG` chapters/topics where this skill is applied.", id_map),
        ]),
        bullet("**Level 2 — Chapter `Chapter Practice Guide` (4 Required Categories):**", id_map, children=[
            bullet("**1. Chapter Mixed Practice:** Guide the learner on practicing all Units in the Chapter together (with clickable `@Page` mentions to every Unit) via an unlabeled mixed problem set (where problems do not announce which Unit's formula applies) or a cohesive 60–100 line Mini-Lab/Module.", id_map),
            bullet("**2. Combine with Prior Chapters:** Identify and link specific prior Chapters/Topics (`@Page` mentions) to integrate into chapter-level practice.", id_map),
            bullet("**3. Chapter-Wide Traps:** Detail the cross-unit confusion points, formula mix-ups, or architectural boundary mistakes that arise when combining multiple Units from the Chapter.", id_map),
            bullet("**4. Cross-Subject & Real-World Connection:** Explain how the Chapter as a whole powers Physics (`PHY`), advanced Mathematics (`MTH`), or production Software Engineering (`PRG`), with clickable `@Page` mentions.", id_map),
        ]),
        bullet("**Level 3 — Topic `Topic Practice & Synthesis Guide` (4 Required Categories):**", id_map, children=[
            bullet("**1. Topic-Wide Synthesis / Capstone Project:** Define a comprehensive cross-chapter diagnostic exam (for `MTH`/`PHY`) or an end-to-end Capstone Project (for `PRG`) that integrates all Chapters of the Topic (linked via `@Page` mentions).", id_map),
            bullet("**2. Must-Be-Automatic Foundations:** Specify the non-negotiable core skills across the Topic that must become effortless before advancing.", id_map),
            bullet("**3. Cross-Chapter Traps:** Highlight systemic misconceptions or integration bugs that span multiple Chapters.", id_map),
            bullet("**4. Bridge to Next Topics in Roadmap:** Map out how this Topic directly feeds into upcoming Topics in `MTH`, `PHY`, and `PRG` using clickable `@Page` mentions.", id_map),
        ]),
    ]
    validate_blocks_clean(part5_blocks, "Rules-Part5")
    notion_request("PATCH", f"blocks/{rules_id}/children", token, {
        "after": "40c3818f-8ba0-810e-a652-ff08877b6917",
        "children": part5_blocks,
    })

    # 3. Update Section 18 Quality Assurance Checklist -> Content Quality (after 40c3818f-8ba0-80d2-a7b7-f6a46a300359)
    sec18_blocks = [
        bullet("All page content is written strictly in English with zero non-English text.", id_map),
        bullet("Every mathematical derivation and worked example formats equation steps vertically from top to bottom (`\\begin{aligned} ... \\end{aligned}` inside block `equation` elements) rather than chaining equations horizontally on a single line.", id_map),
        bullet("Practice Guide is thorough, structured into 4 scannable categories with sub-bullets (Core Skills, Combine with Prior Content, Traps/Edge Cases, Cross-Subject/Real-World Connection), and contains no static problem dump.", id_map),
        bullet("Every reference to an existing Topic, Chapter, Unit, or Resource ID in the workspace renders as a verified clickable Notion `@Page` mention with zero raw double-bracketed ID strings remaining.", id_map),
    ]
    validate_blocks_clean(sec18_blocks, "Rules-Sec18")
    notion_request("PATCH", f"blocks/{rules_id}/children", token, {
        "after": "40c3818f-8ba0-80d2-a7b7-f6a46a300359",
        "children": sec18_blocks,
    })
    print("  Updated 'Learning System — AI Implementation Rules' successfully!")

def build_mth_t02_topic(id_map):
    return [
        callout_block(
            "**Topic Goal:** Master non-linear equations, complex numbers, function transformations, polynomial/rational/exponential/logarithmic models, the unit circle, trigonometric identities, systems of equations, analytic geometry, and discrete probability as the mathematical engine for Calculus, Physics ([[PHY-T01]]), and Algorithmic Engineering ([[PRG-T01]]).\n"
            "**Prerequisites:** [[MTH-T01]] (specifically [[MTH-T01-C04]], [[MTH-T01-C08]], [[MTH-T01-C09]], [[MTH-T01-C11]], [[MTH-T01-C13]], and [[MTH-T01-C14]]) | **Primary Resource:** [[R036]] (`OpenStax – Algebra and Trigonometry 2e`)",
            id_map,
        ),
        h2("1. Overview & Mathematical Context", id_map),
        p_block(
            "While [[MTH-T01]] (`Prealgebra`) focuses on single-variable linear relationships and arithmetic fluency across real numbers, [[MTH-T02]] (`Algebra and Trigonometry`) transitions your thinking from **isolated symbolic manipulation** to **multi-family function analysis and periodic/geometric modeling**.",
            id_map,
        ),
        p_block(
            "In this Topic, you extend the number system from Real Numbers ($\\mathbb{R}$) to Complex Numbers ($\\mathbb{C}$), master non-linear equations (quadratic, radical, rational, and absolute-value), analyze five core families of functions (linear, polynomial, rational, exponential/logarithmic, and trigonometric/periodic), solve multi-variable systems, and unify algebra with geometry via conic sections and vectors.",
            id_map,
        ),
        divider_block(),
        h2("2. Measurable Learning Outcomes", id_map),
        bullet(
            "**Non-Linear Equations & Complex Arithmetic ([[MTH-T02-C01]]):** Perform arithmetic in $\\mathbb{C}$ ($a + bi$), solve quadratic equations via all four methods (factoring, square root property, completing the square, quadratic formula), analyze the discriminant ($\\Delta = b^2 - 4ac$), and solve radical, rational, and absolute-value equations/inequalities in interval notation.",
            id_map,
        ),
        bullet(
            "**Function Architecture & Algebraic Families ([[MTH-T02-C02]] – [[MTH-T02-C05]]):** Determine domain, range, composition $(f \\circ g)(x)$, inverse functions $f^{-1}(x)$, and transformations; model rates of change, polynomial end behavior/zeros, rational asymptotes, and exponential/logarithmic growth and decay.",
            id_map,
        ),
        bullet(
            "**Trigonometry & Periodic Systems ([[MTH-T02-C06]] – [[MTH-T02-C09]]):** Define circular functions on the unit circle in radians and degrees, graph sinusoidal waves ($y = A\\sin(Bx - C) + D$), prove trigonometric identities, solve trigonometric equations, and apply the Law of Sines, Law of Cosines, polar coordinates, and vectors.",
            id_map,
        ),
        bullet(
            "**Systems, Conics & Discrete Mathematics ([[MTH-T02-C10]] – [[MTH-T02-C12]]):** Solve linear/non-linear systems and matrix equations, derive equations for parabolas, ellipses, and hyperbolas, and evaluate arithmetic/geometric sequences, series, mathematical induction, and combinatorics/probability.",
            id_map,
        ),
        divider_block(),
        h2("3. Chapter Sequence & Learning Path (12 Chapters)", id_map),
        p_block("Follow the 12 Chapters in strict dependency order. Click any Chapter mention below to open its learning guide:", id_map),
        num_item("[[MTH-T02-C01]] — **Equations and Inequalities:** Complex numbers ($a+bi$), quadratic equations, radical/rational equations, and interval/absolute-value inequalities.", id_map),
        num_item("[[MTH-T02-C02]] — **Functions:** Domain/range, difference quotients, function composition, transformations, and inverse functions.", id_map),
        num_item("[[MTH-T02-C03]] — **Linear Functions:** Linear rate-of-change models, parallel/perpendicular lines, and linear regression.", id_map),
        num_item("[[MTH-T02-C04]] — **Polynomial and Rational Functions:** Quadratic extrema, polynomial division/zeros (Fundamental Theorem of Algebra), and rational asymptotes.", id_map),
        num_item("[[MTH-T02-C05]] — **Exponential and Logarithmic Functions:** Exponential and logarithmic functions, log laws, and continuous growth/decay models ($A = Pe^{rt}$).", id_map),
        num_item("[[MTH-T02-C06]] — **The Unit Circle — Sine and Cosine Functions:** Radian measure, arc length, unit circle coordinates $(\\cos t, \\sin t)$, and right-triangle ratios.", id_map),
        num_item("[[MTH-T02-C07]] — **Periodic Functions:** Graphs of sine/cosine/tangent (amplitude, period, phase shift) and inverse trigonometric functions.", id_map),
        num_item("[[MTH-T02-C08]] — **Trigonometric Identities and Equations:** Pythagorean, sum/difference, double/half-angle identities, and trigonometric equations.", id_map),
        num_item("[[MTH-T02-C09]] — **Further Applications of Trigonometry:** Law of Sines, Law of Cosines, polar coordinates, polar form of complex numbers (De Moivre's Theorem), and 2D vectors.", id_map),
        num_item("[[MTH-T02-C10]] — **Systems of Equations and Inequalities:** $2 \\times 2$ and $3 \\times 3$ linear systems, non-linear systems, partial fractions, matrices, Gaussian elimination, and determinants/Cramer's Rule.", id_map),
        num_item("[[MTH-T02-C11]] — **Analytic Geometry:** Parabolas, ellipses, hyperbolas, rotated conics, and conic sections in polar coordinates.", id_map),
        num_item("[[MTH-T02-C12]] — **Sequences, Probability, and Counting Theory:** Sequences, summation notation, arithmetic/geometric series, mathematical induction, Binomial Theorem, permutations/combinations, and probability.", id_map),
        divider_block(),
        h2("4. Source Verification & Resource Guide", id_map),
        bullet(
            "**Primary Linked Resource:** [[R036]] (`OpenStax – Algebra and Trigonometry 2e` — `https://openstax.org/books/algebra-and-trigonometry-2e/pages/preface`) | **Verification Status:** `URL Accessible` (`HTTP 200`) · `Content Accessible` · `Content Verified`.",
            id_map,
        ),
        bullet(
            "**Curriculum Mapping Note:** OpenStax Chapter 1 (*Prerequisites*) reviews real numbers, exponents, radicals, and polynomials already covered in [[MTH-T01-C08]], [[MTH-T01-C09]], [[MTH-T01-C10]], and [[MTH-T01-C13]]. Therefore, [[MTH-T02-C01]] begins directly at **OpenStax Chapter 2 (Sections 2.4–2.7)**, and [[MTH-T02-C02]] through [[MTH-T02-C12]] map 1-to-1 with **OpenStax Chapters 3 through 13**.",
            id_map,
        ),
        divider_block(),
        h2("5. Topic Practice & Synthesis Guide", id_map),
        p_block("Use this blueprint to design comprehensive cross-chapter practice sets and readiness checks across [[MTH-T02]]:", id_map),
        bullet("**1. Topic-Wide Synthesis (Comprehensive Mixed Practice):**", id_map, children=[
            bullet("**Cross-Family Equation Diagnosis (15–20 Unlabeled Problems):** Generate mixed problem sets combining equations from [[MTH-T02-C01]] (Quadratic / Radical / Rational), [[MTH-T02-C04]] (Higher-Degree Polynomials), [[MTH-T02-C05]] (Exponential & Logarithmic Equations), and [[MTH-T02-C08]] (Trigonometric Equations) without chapter labels so you practice diagnosing whether to factor, multiply by a conjugate, apply $\\ln$, or substitute a trigonometric identity.", id_map),
            bullet("**Multi-Representation Function & System Modeling:** Practice problems that give a graph or physical scenario (such as a parabola in [[MTH-T02-C04]], a sinusoidal wave in [[MTH-T02-C07]], or a conic section in [[MTH-T02-C11]]) and require deriving its equation, stating its domain and range in interval notation ([[MTH-T02-C01-U04]], [[MTH-T02-C02]]), and finding its intersections with another curve via non-linear systems ([[MTH-T02-C10]]).", id_map),
        ]),
        bullet("**2. Must-Be-Automatic Foundations:**", id_map, children=[
            bullet("**Quadratic & Factoring Fluency:** Solve quadratic equations and interpret the discriminant ($\\Delta = b^2 - 4ac$) from [[MTH-T02-C01-U02]] effortlessly across both real and complex roots ([[MTH-T02-C01-U01]]), as this skill recurs in polynomial zeros ([[MTH-T02-C04]]), logarithmic equations ([[MTH-T02-C05]]), quadratic-in-form trig equations ([[MTH-T02-C08]]), and conic sections ([[MTH-T02-C11]]).", id_map),
            bullet("**Function Transformation & Inverse Fluency:** Read any transformed equation $g(x) = a f(b(x - h)) + k$ ([[MTH-T02-C02]]) and immediately identify shifts, stretches, and reflections across all function families, including swapping Domain and Range for inverse pairs ($e^x \\leftrightarrow \\ln x$ in [[MTH-T02-C05]] and $\\sin x \\leftrightarrow \\arcsin x$ in [[MTH-T02-C07]]).", id_map),
            bullet("**Unit Circle & Radian Reflex:** Recall exact $\\sin, \\cos, \\tan$ values for special angles in radians ($0, \\frac{\\pi}{6}, \\frac{\\pi}{4}, \\frac{\\pi}{3}, \\frac{\\pi}{2}$ and all four quadrants in [[MTH-T02-C06]]) and apply Pythagorean identities ($\\sin^2\\theta + \\cos^2\\theta = 1$ in [[MTH-T02-C08]]) without hesitation.", id_map),
        ]),
        bullet("**3. Cross-Chapter Traps:**", id_map, children=[
            bullet("**Extraneous Solutions:** Forgetting to check candidate solutions against domain restrictions in radical/rational equations ([[MTH-T02-C01-U03]]) and logarithmic equations ([[MTH-T02-C05]]) where a step produces zero denominators or negative log arguments.", id_map),
            bullet("**False Linearity Trap:** Illegally distributing non-linear functions over addition — such as writing $\\sqrt{a+b} = \\sqrt{a}+\\sqrt{b}$, $\\ln(a+b) = \\ln a + \\ln b$, or $\\sin(a+b) = \\sin a + \\sin b$.", id_map),
            bullet("**Root Loss via Variable Division:** Dividing both sides of an equation by a variable expression (such as dividing by $x$ or $\\sin x$) instead of moving terms to one side and factoring out the common factor, which silently discards valid roots like $x = 0$ or $\\sin x = 0$.", id_map),
        ]),
        bullet("**4. Bridge to Next Topics in Roadmap:**", id_map, children=[
            bullet("**Physics ([[PHY-T01]]):** Quadratic equations and inequalities ([[MTH-T02-C01]]) solve constant-acceleration kinematics $y = y_0 + v_{0y}t - \\frac{1}{2}gt^2$ in [[PHY-T01-C02]] and [[PHY-T01-C03]]; trigonometry and 2D vectors ([[MTH-T02-C06]]–[[MTH-T02-C09]]) resolve forces, projectiles, and torque in [[PHY-T01-C04]], [[PHY-T01-C05]], and [[PHY-T01-C06]]; periodic wave functions ([[MTH-T02-C07]]) model mechanical waves and sound in [[PHY-T01-C13]]–[[PHY-T01-C14]]; conic sections ([[MTH-T02-C11]]) describe gravitational orbits in [[PHY-T01-C07]] and mirror/lens optics in [[PHY-T01-C16]].", id_map),
            bullet("**Programming & Algorithms ([[PRG-T01]]):** Logarithms, sequences, and series ([[MTH-T02-C05]], [[MTH-T02-C12]]) underpin asymptotic complexity analysis ($O(\\log n)$, $O(n \\log n)$) and recursive proof by induction, while vectors and matrices ([[MTH-T02-C09]], [[MTH-T02-C10]]) form the foundation of 2D/3D graphics and physics engines.", id_map),
        ]),
        divider_block(),
        h2("6. Final Review & Mastery Audit", id_map),
        todo_item("Verify all 12 Chapters ([[MTH-T02-C01]] – [[MTH-T02-C12]]) have completed Units with `Mastery (0-4)` >= 3 before marking [[MTH-T02]] as `Done`.", id_map),
        todo_item("Review every Unit's `My Implementation & Mistake Log` across [[MTH-T02]] to eliminate recurring algebraic, domain, or trigonometric pitfalls.", id_map),
    ]

def build_mth_t02_c01(id_map):
    return [
        callout_block(
            "**Chapter Objective:** Extend equation-solving from single-variable real linear equations into Complex Numbers ($\\mathbb{C}$), Quadratic Equations, Radical/Rational/Polynomial Equations, and Interval-Based Linear & Absolute-Value Inequalities.\n"
            "**Completion Criteria:** Perform complex arithmetic ($a + bi$) fluently, solve any quadratic or reducible equation while filtering out extraneous roots, and express linear/absolute-value inequality solution sets in interval notation.\n"
            "**Parent Topic:** [[MTH-T02]] | **Prerequisites:** [[MTH-T01-C04]], [[MTH-T01-C08]], [[MTH-T01-C09]], [[MTH-T01-C11]], [[MTH-T01-C13]] | **Source:** [[R036]] (`OpenStax Algebra and Trigonometry 2e`, Chapter 2, Sections 2.4–2.7)",
            id_map,
        ),
        h2("1. Chapter Role & Mathematical Mental Model", id_map),
        p_block(
            "In [[MTH-T01-C11]] (`Solving Linear Equations`), every non-degenerate linear equation $ax + b = 0$ had a single point solution on the real number line $\\mathbb{R}$. [[MTH-T02-C01]] (`Equations and Inequalities`) expands that foundation across three critical dimensions:",
            id_map,
        ),
        num_item(
            "**Number System Closure ($\\mathbb{R} \\to \\mathbb{C}$ in [[MTH-T02-C01-U01]]):** Simple quadratic equations like $x^2 + 1 = 0$ have no solution in $\\mathbb{R}$. Introducing the imaginary unit $i = \\sqrt{-1}$ ($i^2 = -1$) constructs the Complex Number System $\\mathbb{C} = \\{a + bi \\mid a, b \\in \\mathbb{R}\\}$, guaranteeing that every polynomial equation has solutions.",
            id_map,
        ),
        num_item(
            "**Non-Linear Degree & Domain-Restricted Equations ([[MTH-T02-C01-U02]] & [[MTH-T02-C01-U03]]):** Quadratic equations ($ax^2 + bx + c = 0$) introduce up to two roots governed by the discriminant $\\Delta = b^2 - 4ac$. Radical, rational, and absolute-value equations require strict domain tracking because non-reversible steps (such as squaring both sides or multiplying by a variable denominator) can introduce **extraneous solutions**.",
            id_map,
        ),
        num_item(
            "**From Point Solutions to Continuous Intervals ([[MTH-T02-C01-U04]]):** Inequalities ($<, \\le, >, \\ge$) and absolute-value bounds ($|ax + b| < c$ vs. $|ax + b| > c$) produce continuous intervals rather than isolated points, preparing you directly for Function Domain & Range analysis in [[MTH-T02-C02]].",
            id_map,
        ),
        divider_block(),
        h2("2. Core Mathematical Concepts & Formulas", id_map),
        bullet("**Complex Number Standard Form, Conjugate & Modulus ([[MTH-T02-C01-U01]]):**", id_map),
        eq_block("\\begin{aligned} i &= \\sqrt{-1}, \\qquad i^2 = -1 \\\\ z &= a + bi, \\qquad \\bar{z} = a - bi \\\\ z \\cdot \\bar{z} &= (a + bi)(a - bi) = a^2 + b^2 = |z|^2 \\end{aligned}"),
        bullet("**Quadratic Formula & Discriminant Classification ([[MTH-T02-C01-U02]]):**", id_map),
        eq_block("\\begin{aligned} ax^2 + bx + c &= 0 \\quad (a \\neq 0) \\\\ x &= \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}, \\qquad \\Delta = b^2 - 4ac \\end{aligned}"),
        bullet("**Absolute-Value Inequality Equivalence ([[MTH-T02-C01-U04]], for $c > 0$):**", id_map),
        eq_block("\\begin{aligned} |E| < c &\\iff -c < E < c &&\\text{(Intersection / AND: } (-c, c)\\text{)} \\\\ |E| > c &\\iff E < -c \\;\\text{ or }\\; E > c &&\\text{(Union / OR: } (-\\infty, -c) \\cup (c, \\infty)\\text{)} \\end{aligned}"),
        divider_block(),
        h2("3. Unit Sequence & Progression (4 Units)", id_map),
        num_item(
            "[[MTH-T02-C01-U01]] — **Complex Numbers:** Define $i = \\sqrt{-1}$, simplify $\\sqrt{-b} = i\\sqrt{b}$, perform addition, subtraction, multiplication, conjugate division, and simplify cyclic powers $i^n$. *(Placed first because [[MTH-T02-C01-U02]] requires complex numbers whenever $\\Delta < 0$.)*",
            id_map,
        ),
        num_item(
            "[[MTH-T02-C01-U02]] — **Quadratic Equations:** Solve $ax^2 + bx + c = 0$ by factoring, the square root property, completing the square, and the quadratic formula; classify solutions using the discriminant $\\Delta = b^2 - 4ac$.",
            id_map,
        ),
        num_item(
            "[[MTH-T02-C01-U03]] — **Other Types of Equations:** Solve higher-degree factorable polynomials, equations in quadratic form ($u$-substitution), radical equations, rational-exponent equations ($x^{m/n} = k$), and absolute-value equations while eliminating extraneous roots.",
            id_map,
        ),
        num_item(
            "[[MTH-T02-C01-U04]] — **Linear Inequalities and Absolute Value Inequalities:** Express solution sets using set-builder and interval notation $[a, b), (-\\infty, c]$, solve compound inequalities (`AND` / `OR`), and solve $|ax + b| \\lessgtr c$.",
            id_map,
        ),
        divider_block(),
        h2("4. Resources & Source Attribution", id_map),
        bullet(
            "**Primary Textbook Reference:** [[R036]] (`OpenStax – Algebra and Trigonometry 2e` — Chapter 2: *Equations and Inequalities*, Sections 2.4 *Complex Numbers*, 2.5 *Quadratic Equations*, 2.6 *Other Types of Equations*, and 2.7 *Linear Inequalities and Absolute Value Inequalities*).",
            id_map,
        ),
        bullet(
            "**Prerequisite Coverage Note:** OpenStax Sections 2.1–2.3 (*Rectangular Coordinates, Linear Equations in One Variable, Models and Applications*) are already covered in [[MTH-T01-C11]], [[MTH-T01-C12]], and [[MTH-T01-C14]].",
            id_map,
        ),
        divider_block(),
        h2("5. Chapter Practice Guide", id_map),
        p_block("After studying all 4 Units in [[MTH-T02-C01]], use this blueprint to generate and practice mixed chapter problem sets:", id_map),
        bullet("**1. Chapter Mixed Practice (Unlabeled Multi-Unit Synthesis):**", id_map, children=[
            bullet("**Unlabeled Equation Diagnosis Set (6–10 Problems Mixing All 4 Units):** Generate a mixed problem set combining [[MTH-T02-C01-U01]], [[MTH-T02-C01-U02]], [[MTH-T02-C01-U03]], and [[MTH-T02-C01-U04]] without telling yourself which method to use. Practice diagnosing on sight whether an equation requires direct factoring, completing the square, the quadratic formula (including complex conjugate roots $a \\pm bi$), $u$-substitution (e.g., $x^4 - 5x^2 + 6 = 0$ or $x^{2/3} - 3x^{1/3} - 10 = 0$), isolating a radical before squaring, or splitting an absolute-value inequality into `AND` vs. `OR` intervals.", id_map),
            bullet("**Extraneous Root Filtering Drill:** Include at least two radical equations ($\\sqrt{ax+b} = cx+d$) and rational equations in [[MTH-T02-C01-U03]] where squaring or clearing denominators leads to a quadratic equation ([[MTH-T02-C01-U02]]) with two algebraic candidates, one of which violates the original domain and must be rejected.", id_map),
        ]),
        bullet("**2. Combine with Prior Chapters:**", id_map, children=[
            bullet("**Fractions & LCD Clearing ([[MTH-T01-C04]] & [[MTH-T01-C11]]):** Practice solving quadratic equations and compound inequalities with fractional/decimal coefficients by multiplying through by the Least Common Denominator (LCD) first, and practice simplifying complex quotients $\\frac{a+bi}{c+di}$ into lowest-terms fractional form $\\frac{p}{q} + \\frac{r}{s}i$.", id_map),
            bullet("**Exponent & Radical Laws ([[MTH-T01-C08]] & [[MTH-T01-C09]]):** Combine negative square roots $\\sqrt{-b} = i\\sqrt{b}$ with radical simplification (extracting perfect square factors) and solve rational-exponent equations $x^{m/n} = k$ by raising both sides to the reciprocal power $\\frac{n}{m}$ (accounting for $\\pm$ when $m$ is even).", id_map),
            bullet("**Polynomial Multiplication & Special Products ([[MTH-T01-C13]]):** Connect difference-of-squares $(A+B)(A-B) = A^2 - B^2$ to complex conjugates $(a+bi)(a-bi) = a^2 + b^2$ and perfect-square trinomials $(x + k)^2 = x^2 + 2kx + k^2$ to completing the square.", id_map),
        ]),
        bullet("**3. Chapter-Wide Traps:**", id_map, children=[
            bullet("**Multiplying Negative Radicals Before Extracting $i$ ([[MTH-T02-C01-U01]]):** Falsely writing $\\sqrt{-4}\\cdot\\sqrt{-9} = \\sqrt{36} = 6$ instead of $(2i)(3i) = 6i^2 = -6$.", id_map),
            bullet("**Dividing by a Variable Expression ([[MTH-T02-C01-U02]] & [[MTH-T02-C01-U03]]):** Dividing both sides of $x^2 = 5x$ or $x^3 = 4x$ by $x$, which loses the root $x = 0$. Always move all terms to one side and factor.", id_map),
            bullet("**Forgetting the Middle Term When Squaring a Radical Side ([[MTH-T02-C01-U03]]):** When solving $\\sqrt{2x+3} = x - 1$, squaring the right side gives $(x - 1)^2 = x^2 - 2x + 1$, **not** $x^2 - 1$ or $x^2 + 1$.", id_map),
            bullet("**Reversing Inequality Signs & Mixing Up `AND` vs. `OR` ([[MTH-T02-C01-U04]]):** Forgetting to flip the inequality symbol when multiplying or dividing by a negative number, or confusing $|E| < c$ (`AND` / bounded interval) with $|E| > c$ (`OR` / two disjoint rays), or failing to spot negative bounds like $|ax+b| < -3$ (no solution, $\\varnothing$).", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (Physics & Code):**", id_map, children=[
            bullet("**Physics — Free Fall & Projectile Kinematics ([[PHY-T01-C02]], [[PHY-T01-C03]], [[PHY-T01-C05]]):** Vertical position under gravity $y(t) = y_0 + v_{0y}t - \\frac{1}{2}gt^2$ is a quadratic equation in time $t$ ([[MTH-T02-C01-U02]]). Solving for impact time yields two roots (where negative time $t < 0$ is physically discarded), and a negative discriminant $\\Delta < 0$ (producing complex roots from [[MTH-T02-C01-U01]]) proves physically that the projectile never reaches the target height $y$.", id_map),
            bullet("**Physics — Energy Conservation & AC Circuit Impedance ([[PHY-T01-C09]], [[PHY-T01-C19]]):** Solving $\\frac{1}{2}mv^2 + \\frac{1}{2}kx^2 = E_{\\text{total}}$ for velocity or displacement uses the square root property, while AC circuit analysis models impedance as a complex number $Z = R + j(X_L - X_C)$ ([[MTH-T02-C01-U01]]).", id_map),
            bullet("**Code — Floating-Point Tolerance & Ray-Sphere Intersection ([[PRG-T01-C03]]):** Absolute-value inequalities $|a - b| < \\varepsilon$ ([[MTH-T02-C01-U04]]) are the standard pattern for safe floating-point equality checks (`Math.abs(a - b) < 1e-9`), and the quadratic discriminant $\\Delta = b^2 - 4ac$ determines whether a 3D ray intersects a sphere ($\\Delta < 0$ = miss, $\\Delta = 0$ = tangent hit, $\\Delta > 0$ = entry and exit hits).", id_map),
        ]),
        divider_block(),
        h2("6. Summary & Spaced Review Guide", id_map),
        todo_item("Complete [[MTH-T02-C01-U01]], [[MTH-T02-C01-U02]], [[MTH-T02-C01-U03]], and [[MTH-T02-C01-U04]] and record your derivations and pitfalls in each Unit's `My Implementation & Mistake Log`.", id_map),
        todo_item("Complete one Mixed Chapter Practice session covering complex conjugates, quadratic formula, radical/rational extraneous roots, and interval inequalities before advancing to [[MTH-T02-C02]].", id_map),
    ]

def build_mth_t02_c01_u01(id_map):
    return [
        callout_block(
            "**Learning Objective:** Define the imaginary unit $i = \\sqrt{-1}$, express square roots of negative numbers in terms of $i$, perform addition, subtraction, multiplication, and conjugate division of complex numbers in standard form $a + bi$, and simplify cyclic powers $i^n$.\n"
            "**Expected Output:** Simplify radical and algebraic expressions over $\\mathbb{C}$ into exact standard form $a + bi$ using vertical step-by-step derivations, evaluate complex conjugates and moduli, and document your work and pitfalls in `My Implementation & Mistake Log`.\n"
            "**Parent:** [[MTH-T02]] → [[MTH-T02-C01]] | **Prerequisites:** [[MTH-T01-C04]], [[MTH-T01-C08]], [[MTH-T01-C09]], [[MTH-T01-C13]] | **Next Unit:** [[MTH-T02-C01-U02]] | **Source:** [[R036]] (`OpenStax Algebra and Trigonometry 2e`, Section 2.4)",
            id_map,
        ),
        h2("1. Core Concepts & Mathematical Intuition", id_map),
        bullet(
            "**Why Real Numbers ($\\mathbb{R}$) Are Incomplete:** In [[MTH-T01-C09]] (`Roots`), the square root of a negative number such as $\\sqrt{-9}$ had no real value because the square of any real number is non-negative ($x^2 \\ge 0$). To solve equations like $x^2 + 1 = 0$ or $x^2 - 4x + 5 = 0$ (in [[MTH-T02-C01-U02]]), we define the **imaginary unit** $i$ such that:",
            id_map,
        ),
        eq_block("i = \\sqrt{-1} \\qquad \\text{and} \\qquad i^2 = -1"),
        bullet(
            "**Principal Square Root of a Negative Number:** For any positive real number $b > 0$, the principal square root of $-b$ is $\\sqrt{-b} = \\sqrt{-1 \\cdot b} = i\\sqrt{b}$. **Critical Rule:** Always rewrite $\\sqrt{-b}$ as $i\\sqrt{b}$ *before* multiplying or dividing radicals, because the real radical rule $\\sqrt{A}\\sqrt{B} = \\sqrt{AB}$ is invalid when both $A < 0$ and $B < 0$.",
            id_map,
        ),
        bullet(
            "**Standard Form of a Complex Number ($z = a + bi$):** Adding real numbers to real multiples of $i$ produces the **Complex Number System** $\\mathbb{C} = \\{a + bi \\mid a, b \\in \\mathbb{R}\\}$. Here $a = \\text{Re}(z)$ is the **real part** and $b = \\text{Im}(z)$ is the **imaginary part**. If $b = 0$, $z = a$ is a real number ($\\mathbb{R} \\subset \\mathbb{C}$); if $a = 0$ and $b \\neq 0$, $z = bi$ is a **pure imaginary number**. Two complex numbers are equal ($a + bi = c + di$) if and only if $a = c$ and $b = d$.",
            id_map,
        ),
        bullet(
            "**Geometric Interpretation on the Complex Plane:** While real numbers lie on a 1D line ([[MTH-T01-C10]]), a complex number $z = a + bi$ is plotted as the coordinates $(a, b)$ on a 2D plane where the horizontal axis is the **Real Axis** and the vertical axis is the **Imaginary Axis**. By the Pythagorean Theorem ([[MTH-T01-C12]]), the distance from the origin $(0,0)$ to $(a,b)$ is the **modulus** (or absolute value) $|z| = \\sqrt{a^2 + b^2}$.",
            id_map,
        ),
        bullet(
            "**Complex Conjugate ($\\bar{z} = a - bi$) & Division:** The complex conjugate of $z = a + bi$ changes **only** the sign of the imaginary part: $\\bar{z} = a - bi$. Multiplying a complex number by its conjugate eliminates $i$ completely and yields the square of its modulus: $z\\bar{z} = a^2 + b^2 \\in \\mathbb{R}$. To divide $\\frac{a+bi}{c+di}$, multiply both numerator and denominator by the denominator's conjugate $c - di$.",
            id_map,
        ),
        bullet(
            "**Modulo-4 Cycle of Powers of $i$:** Because $i^4 = (i^2)^2 = (-1)^2 = 1$, integer powers $i^n$ repeat in a cycle of length 4 determined by the remainder $r = n \\bmod 4$.",
            id_map,
        ),
        divider_block(),
        h2("2. Key Formulas & Algebraic Identities", id_map),
        p_block("All fundamental operations on complex numbers flow vertically from the definition $i^2 = -1$:", id_map),
        eq_block("\\begin{aligned} \\text{Addition / Subtraction:} \\quad (a + bi) \\pm (c + di) &= (a \\pm c) + (b \\pm d)i \\\\[6pt] \\text{Multiplication (FOIL):} \\quad (a + bi)(c + di) &= ac + adi + bci + bdi^2 \\\\ &= ac + (ad + bc)i + bd(-1) \\\\ &= (ac - bd) + (ad + bc)i \\\\[6pt] \\text{Conjugate Product:} \\quad (a + bi)(a - bi) &= a^2 - (bi)^2 \\\\ &= a^2 - b^2(-1) \\\\ &= a^2 + b^2 \\\\[6pt] \\text{Division by Conjugate:} \\quad \\frac{a + bi}{c + di} &= \\frac{(a + bi)(c - di)}{(c + di)(c - di)} \\\\ &= \\frac{(ac + bd) + (bc - ad)i}{c^2 + d^2} \\\\ &= \\left(\\frac{ac + bd}{c^2 + d^2}\\right) + \\left(\\frac{bc - ad}{c^2 + d^2}\\right)i \\\\[6pt] \\text{Powers of } i \\text{ (Modulo 4):} \\quad i^n &= i^{4q + r} = (i^4)^q \\cdot i^r = i^r \\quad (r \\in \\{0,1,2,3\\}) \\\\ i^0 &= 1, \\quad i^1 = i, \\quad i^2 = -1, \\quad i^3 = -i, \\quad i^4 = 1 \\end{aligned}"),
        divider_block(),
        h2("3. Step-by-Step Worked Examples (Vertical Derivations)", id_map),
        h3("Example 1: Multiplying Negative Square Roots (Avoiding the Sign Trap)", id_map),
        p_block("**Problem:** Simplify $\\sqrt{-12} \\cdot \\sqrt{-27}$ and write the result in standard form $a + bi$.", id_map),
        p_block("**Step-by-Step Solution:** Extract $i = \\sqrt{-1}$ and simplify each radical first before multiplying:", id_map),
        eq_block("\\begin{aligned} \\sqrt{-12} \\cdot \\sqrt{-27} &= \\left(i\\sqrt{12}\\right) \\cdot \\left(i\\sqrt{27}\\right) &&\\text{(Extract } i \\text{ from each negative radical first)} \\\\ &= \\left(i\\sqrt{4 \\cdot 3}\\right) \\cdot \\left(i\\sqrt{9 \\cdot 3}\\right) &&\\text{(Factor out perfect squares } 4 \\text{ and } 9\\text{)} \\\\ &= \\left(2i\\sqrt{3}\\right) \\cdot \\left(3i\\sqrt{3}\\right) &&\\text{(Simplify } \\sqrt{4}=2 \\text{ and } \\sqrt{9}=3\\text{)} \\\\ &= (2 \\cdot 3) \\cdot i^2 \\cdot \\left(\\sqrt{3}\\right)^2 &&\\text{(Group rational coefficients, } i^2, \\text{ and radicals)} \\\\ &= 6 \\cdot (-1) \\cdot 3 &&\\text{(Substitute } i^2 = -1 \\text{ and } (\\sqrt{3})^2 = 3\\text{)} \\\\ &= -18 \\\\ &= -18 + 0i &&\\text{(Standard form } a + bi\\text{)} \\end{aligned}"),
        p_block("*Warning:* Never multiply negative radicands directly as $\\sqrt{(-12)(-27)} = \\sqrt{324} = +18$, which produces the wrong sign!", id_map),
        h3("Example 2: Complex Multiplication & Conjugate Product", id_map),
        p_block("**Problem:** Multiply and simplify $(3 - 4i)(2 + 5i)$ into standard form $a + bi$.", id_map),
        p_block("**Step-by-Step Solution:** Expand using the distributive property (FOIL) and replace $i^2$ with $-1$:", id_map),
        eq_block("\\begin{aligned} (3 - 4i)(2 + 5i) &= 3(2) + 3(5i) - 4i(2) - 4i(5i) &&\\text{(Distribute / FOIL)} \\\\ &= 6 + 15i - 8i - 20i^2 &&\\text{(Multiply terms)} \\\\ &= 6 + 7i - 20(-1) &&\\text{(Combine like } i \\text{ terms and substitute } i^2 = -1\\text{)} \\\\ &= 6 + 7i + 20 &&\\text{(Simplify } -20(-1) = +20\\text{)} \\\\ &= (6 + 20) + 7i &&\\text{(Group real and imaginary parts)} \\\\ &= 26 + 7i &&\\text{(Standard form } a + bi\\text{)} \\end{aligned}"),
        h3("Example 3: Dividing Complex Numbers Using the Complex Conjugate", id_map),
        p_block("**Problem:** Divide $\\frac{2 + 5i}{4 - i}$ and express the quotient in exact standard form $a + bi$.", id_map),
        p_block("**Step-by-Step Solution:** Multiply numerator and denominator by the conjugate of the denominator ($\\overline{4 - i} = 4 + i$):", id_map),
        eq_block("\\begin{aligned} \\frac{2 + 5i}{4 - i} &= \\frac{(2 + 5i)(4 + i)}{(4 - i)(4 + i)} &&\\text{(Multiply top and bottom by conjugate } 4 + i\\text{)} \\\\ &= \\frac{2(4) + 2(i) + 5i(4) + 5i(i)}{4^2 + (-1)^2} &&\\text{(Expand numerator; denominator uses } c^2 + d^2\\text{)} \\\\ &= \\frac{8 + 2i + 20i + 5i^2}{16 + 1} &&\\text{(Simplify products)} \\\\ &= \\frac{8 + 22i + 5(-1)}{17} &&\\text{(Substitute } i^2 = -1\\text{)} \\\\ &= \\frac{(8 - 5) + 22i}{17} &&\\text{(Combine real terms in numerator)} \\\\ &= \\frac{3 + 22i}{17} \\\\ &= \\frac{3}{17} + \\frac{22}{17}i &&\\text{(Separate into standard form } a + bi\\text{)} \\end{aligned}"),
        h3("Example 4: Simplifying High Powers of $i$ & Evaluating a Quadratic Polynomial at $z = a + bi$", id_map),
        p_block("**Problem:** (a) Simplify $i^{75}$, and (b) evaluate $f(z) = z^2 - 4z + 5$ at $z = 2 - i$.", id_map),
        p_block("**Step-by-Step Solution for (a):** Divide the exponent $75$ by $4$ to find the remainder ($75 = 4 \\cdot 18 + 3$):", id_map),
        eq_block("\\begin{aligned} i^{75} &= i^{4(18) + 3} \\\\ &= \\left(i^4\\right)^{18} \\cdot i^3 &&\\text{(Apply exponent product/power laws from MTH-T01-C08)} \\\\ &= (1)^{18} \\cdot (-i) &&\\text{(Substitute } i^4 = 1 \\text{ and } i^3 = -i\\text{)} \\\\ &= -i \\end{aligned}"),
        p_block("**Step-by-Step Solution for (b):** Substitute $z = 2 - i$ into $f(z) = z^2 - 4z + 5$ and simplify vertically:", id_map),
        eq_block("\\begin{aligned} f(2 - i) &= (2 - i)^2 - 4(2 - i) + 5 &&\\text{(Substitute } z = 2 - i\\text{)} \\\\ &= \\left(2^2 - 2(2)(i) + i^2\\right) - 8 + 4i + 5 &&\\text{(Expand binomial square and distribute } -4\\text{)} \\\\ &= (4 - 4i - 1) - 8 + 4i + 5 &&\\text{(Substitute } i^2 = -1\\text{)} \\\\ &= 3 - 4i - 3 + 4i &&\\text{(Simplify real numbers)} \\\\ &= (3 - 3) + (-4 + 4)i &&\\text{(Group real and imaginary parts)} \\\\ &= 0 + 0i = 0 &&\\text{(Confirms } z = 2 - i \\text{ is a root of } z^2 - 4z + 5 = 0\\text{)} \\end{aligned}"),
        divider_block(),
        h2("4. Practice Guide", id_map),
        p_block("Use this blueprint to generate targeted practice problems for [[MTH-T02-C01-U01]] and record your vertical derivations in Section 6:", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Negative Radical Simplification:** Drill converting $\\sqrt{-b} = i\\sqrt{b}$ while factoring out perfect squares, and multiplying or dividing expressions with multiple negative radicals such as $\\sqrt{-18}\\cdot\\sqrt{-50}$ or $\\frac{\\sqrt{-48}}{\\sqrt{3}}$.", id_map),
            bullet("**Standard-Form Arithmetic & Conjugate Division:** Practice adding, subtracting, expanding binomial powers $(a \\pm bi)^2$ and $(a \\pm bi)^3$, and dividing complex numbers $\\frac{a+bi}{c+di}$ by multiplying by the denominator's conjugate and splitting the result into exact $a + bi$ fractions.", id_map),
            bullet("**Modulo-4 Powers of $i$ & Complex Root Verification:** Drill simplifying expressions with large positive or negative powers of $i$ (e.g., $2i^{102} - 5i^{47} + i^{-13}$) and substituting $z = a + bi$ into quadratic polynomials $az^2 + bz + c$ to verify complex roots for [[MTH-T02-C01-U02]].", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Radical Simplification & Rationalization ([[MTH-T01-C09]] — `Roots`):** Generate problems where the negative radicands are non-perfect squares, such as $(3 - \\sqrt{-24})(2 + \\sqrt{-54})$, requiring you to simplify $\\sqrt{-24} = 2i\\sqrt{6}$ and $\\sqrt{-54} = 3i\\sqrt{6}$ before multiplying.", id_map),
            bullet("**Polynomial Multiplication & Special Products ([[MTH-T01-C13]] — `Polynomials`):** Combine perfect-square trinomials $(A \\pm B)^2$ and difference-of-squares $(A - B)(A + B)$ in multi-term complex expressions like $(2 - 3i)^2 - (4 + i)(4 - i)$.", id_map),
            bullet("**Fraction Reduction & LCD Arithmetic ([[MTH-T01-C04]] — `Fractions`):** Practice complex division problems where the resulting real and imaginary fractions $\\frac{ac+bd}{c^2+d^2} + \\frac{bc-ad}{c^2+d^2}i$ must be reduced to lowest terms by canceling greatest common factors.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**Premature Radical Multiplication Trap:** Never apply $\\sqrt{A}\\sqrt{B} = \\sqrt{AB}$ when $A < 0$ and $B < 0$. Always extract $i$ first so that $(i\\sqrt{|A|})(i\\sqrt{|B|}) = i^2\\sqrt{|AB|} = -\\sqrt{|AB|}$.", id_map),
            bullet("**Conjugate Denominator Sign Trap:** In $(c + di)(c - di)$, students frequently write $c^2 - d^2$ out of habit from real algebra, forgetting that $-d^2i^2 = -d^2(-1) = +d^2$. The denominator is always the sum of squares **$c^2 + d^2$** and never contains $i$.", id_map),
            bullet("**Reordered Conjugate Trap:** When finding the conjugate of an expression written as $-5i + 3$, rewrite it in standard form $3 - 5i$ first so you flip the sign of the **imaginary part** ($3 + 5i$), not the real part.", id_map),
            bullet("**Unseparated Fraction Trap:** Leaving a quotient as a single fraction $\\frac{3 + 22i}{17}$ instead of splitting it into standard form $\\frac{3}{17} + \\frac{22}{17}i$.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (Math ↔ Physics ↔ Code):**", id_map, children=[
            bullet("**Physics — AC Electrical Circuits & Impedance ([[PHY-T01-C19]] — `Electrical Circuits`):** In alternating-current (AC) circuits, resistors ($R$), inductors ($X_L = \\omega L$), and capacitors ($X_C = \\frac{1}{\\omega C}$) shift voltage and current out of phase by $90^\\circ$. Physics and electrical engineering represent total impedance as a complex number $Z = R + j(X_L - X_C)$ (using $j$ for $\\sqrt{-1}$ so it is not confused with current $I$). Computing the current $I = \\frac{V}{Z}$ or equivalent parallel impedance $Z_{\\text{eq}} = \\frac{Z_1 Z_2}{Z_1 + Z_2}$ requires **complex multiplication and conjugate division** from this exact Unit!", id_map),
            bullet("**Physics — Wave Superposition, Optics & Quantum Mechanics ([[PHY-T01-C13]], [[PHY-T01-C17]], [[PHY-T01-C21]]):** Wave phase and quantum state amplitudes are modeled as complex numbers $\\psi = a + bi$, where measurable wave intensity or probability density is given by the conjugate product $|\\psi|^2 = \\psi \\cdot \\bar{\\psi} = a^2 + b^2$.", id_map),
            bullet("**Code — 2D Rotations, Signal Processing (FFT) & Mandelbrot Fractals ([[PRG-T01-C03]]):** Multiplying any complex number $z = x + yi$ by $i$ produces $iz = -y + xi$, which is an exact $90^\\circ$ counterclockwise rotation of $(x, y)$ in 2D space without calling `Math.sin` or `Math.cos`. Complex arithmetic (`{ re: number, im: number }`) also powers the Fast Fourier Transform (FFT) in audio/image processing.", id_map),
        ]),
        divider_block(),
        h2("5. Active Recall Questions", id_map),
        toggle_block(
            "1. Why does the real radical product rule $\\sqrt{a}\\cdot\\sqrt{b} = \\sqrt{ab}$ fail when $a = -4$ and $b = -9$, and what is the correct vertical derivation?",
            [
                "The property $\\sqrt{a}\\sqrt{b} = \\sqrt{ab}$ is valid in $\\mathbb{R}$ only when at least one radicand is non-negative. When both are negative, multiplying under the radical cancels the negative signs prematurely. Instead, extract $i$ first:",
                eq_block("\\begin{aligned} \\sqrt{-4} \\cdot \\sqrt{-9} &= (2i)(3i) \\\\ &= 6i^2 \\\\ &= 6(-1) = -6 \\end{aligned}"),
            ],
            id_map,
        ),
        toggle_block(
            "2. Why does multiplying any complex number $z = a + bi$ by its conjugate $\\bar{z} = a - bi$ always yield a non-negative real number, and how does this relate to the Pythagorean Theorem?",
            [
                "Expanding the product eliminates the cross terms and converts $i^2$ into $-1$:",
                eq_block("\\begin{aligned} z \\cdot \\bar{z} &= (a + bi)(a - bi) \\\\ &= a^2 - abi + abi - b^2i^2 \\\\ &= a^2 - b^2(-1) \\\\ &= a^2 + b^2 \\ge 0 \\end{aligned}"),
                "Geometrically, on the complex plane ([[MTH-T01-C12]]), the distance from $(0,0)$ to $(a,b)$ is $|z| = \\sqrt{a^2 + b^2}$, so $z\\bar{z} = |z|^2$.",
            ],
            id_map,
        ),
        toggle_block(
            "3. How do you simplify $i^{253}$ and $i^{-14}$ using modulo-4 arithmetic?",
            [
                "Divide the exponent by $4$ and keep the remainder $r = n \\bmod 4$:",
                eq_block("\\begin{aligned} i^{253} &= i^{4(63) + 1} = (i^4)^{63} \\cdot i^1 = 1^{63} \\cdot i = i \\\\[4pt] i^{-14} &= i^{4(-4) + 2} = (i^4)^{-4} \\cdot i^2 = 1^{-4} \\cdot (-1) = -1 \\end{aligned}"),
            ],
            id_map,
        ),
        toggle_block(
            "4. If a quadratic equation with real coefficients (in [[MTH-T02-C01-U02]]) has $z_1 = 3 - 2i$ as one solution, what is the other solution $z_2$, and what are their sum and product?",
            [
                "Complex roots of real-coefficient polynomials always occur in conjugate pairs, so $z_2 = \\overline{z_1} = 3 + 2i$. Their sum and product are both real numbers:",
                eq_block("\\begin{aligned} z_1 + z_2 &= (3 - 2i) + (3 + 2i) = 6 \\\\ z_1 \\cdot z_2 &= (3 - 2i)(3 + 2i) = 3^2 + 2^2 = 9 + 4 = 13 \\end{aligned}"),
            ],
            id_map,
        ),
        divider_block(),
        h2("6. My Implementation & Mistake Log", id_map),
        quote_block("**Feynman One-Liner (Summarize the core concept of this Unit in 1–2 sentences in your own words):**\n[Write your summary here after studying]", id_map),
        quote_block("**My Solution / Working / Code (Workspace for your vertical mathematical derivations or practice problems):**\n[Paste the problems you generated and your step-by-step solutions here]", id_map),
        quote_block("**Mistake & Pitfall Log (Record sign errors, conjugate mistakes, or traps encountered during practice to target on Next Review):**\n- [Log mistakes and lessons learned here]", id_map),
        divider_block(),
        h2("7. Completion Checklist & Mastery Review", id_map),
        todo_item("Studied the core concepts and vertical worked examples for [[MTH-T02-C01-U01]] (`Complex Numbers`).", id_map),
        todo_item("Generated and solved practice problems covering negative radicals, complex multiplication, conjugate division, and powers of $i$ using the Section 4 `Practice Guide`.", id_map),
        todo_item("Answered all 4 Active Recall questions without peeking and logged personal work/mistakes in Section 6.", id_map),
        todo_item("Updated `Status`, `Mastery (0-4)`, `Last Reviewed`, and `Next Review` properties on this page.", id_map),
    ]

def build_prg_t03_topic(id_map):
    return [
        callout_block(
            "**Topic Goal:** Master the Next.js App Router (`app/`), React Server Components (RSC), Client/Server execution boundaries, streaming & caching architectures, and end-to-end validated mutations (`Server Actions` & `Route Handlers`).\n"
            "**Prerequisites:** [[PRG-T00]], [[PRG-T01]] (specifically [[PRG-T01-C01]], [[PRG-T01-C02]]), and [[PRG-T02]] (specifically [[PRG-T02-C01]], [[PRG-T02-C02]], [[PRG-T02-C03]]) | **Linked Resources:** [[R011]] (`Next.js Learn`), [[R012]] (`Next.js App Router Docs`), [[R009]] (`Zod Docs`)",
            id_map,
        ),
        h2("1. Overview & Architectural Context", id_map),
        p_block(
            "In [[PRG-T02]] (`Frontend Engineering`), React applications ran primarily as client-side component trees that fetched data after JavaScript downloaded and hydrated in the browser. [[PRG-T03]] (`Next.js & Full-Stack React`) extends React across the network boundary using the **Next.js App Router**.",
            id_map,
        ),
        p_block(
            "Every route segment in `app/` is server-first by default: **React Server Components (RSC)** execute exclusively on the server (with zero client bundle cost and direct access to databases/secrets), while interactive islands explicitly opt into the browser via `'use client'`. Together with nested layouts, streaming `Suspense` boundaries (`loading.tsx`), error boundaries (`error.tsx`), and schema-validated `Server Actions` ([[R009]]), Next.js turns React into a cohesive full-stack application framework.",
            id_map,
        ),
        divider_block(),
        h2("2. Measurable Learning Outcomes", id_map),
        bullet(
            "**File-System Routing & Layout Hierarchy ([[PRG-T03-C01]]):** Architect multi-route Next.js applications using `app/` conventions (`page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`), Route Groups `(group)`, Private Folders `_folder`, typed dynamic route parameters, SEO metadata, and static vs. dynamic rendering.",
            id_map,
        ),
        bullet(
            "**Server/Client Boundaries & Streaming Data Flow ([[PRG-T03-C02]]):** Partition components cleanly between Server Components and Client Components (`'use client'`), enforce serializable prop contracts across the network boundary, eliminate request waterfalls via parallel `Promise.all` and streaming `Suspense`, and control caching (`revalidatePath`, `revalidateTag`).",
            id_map,
        ),
        bullet(
            "**Full-Stack Mutations, Validation & Route Handlers ([[PRG-T03-C03]]):** Implement type-safe `Server Actions` and HTTP `Route Handlers` (`route.ts`) validated at runtime with [[R009]] (`Zod`), handle pending/optimistic UI states (`useActionState`), and ship a complete CRUD Content Management flow.",
            id_map,
        ),
        divider_block(),
        h2("3. Chapter Sequence & Learning Path (3 Chapters)", id_map),
        num_item(
            "[[PRG-T03-C01]] — **Next.js App Router Foundations (7 Units: [[PRG-T03-C01-U01]] – [[PRG-T03-C01-U07]]):** Project structure, file-system routing, nested layouts, loading/error boundaries, dynamic params, metadata/navigation, and static vs. dynamic rendering.",
            id_map,
        ),
        num_item(
            "[[PRG-T03-C02]] — **Server/Client Components & Data Flow (8 Units):** Server vs. Client component mental model, `'use client'` boundary rules, server data fetching, parallel fetching & streaming `Suspense`, URL search params state, caching/revalidation, and environment variable security.",
            id_map,
        ),
        num_item(
            "[[PRG-T03-C03]] — **Mutations, Route Handlers & CMS Mini App (8 Units):** Server Actions vs. Route Handlers (`route.ts`), form progressive enhancement, runtime validation with [[R009]] (`Zod`), error/optimistic UI feedback, cache invalidation after mutations, and building a full-stack CMS mini-application.",
            id_map,
        ),
        divider_block(),
        h2("4. Source Verification & Resource Guide", id_map),
        bullet("**[[R012]] (`Next.js App Router Docs` — `https://nextjs.org/docs/app`):** `URL Accessible` (`HTTP 200`) · `Content Accessible` · `Content Verified`. Authoritative reference for `app/` file conventions, Server/Client composition, caching, and Server Actions.", id_map),
        bullet("**[[R011]] (`Next.js Learn` — `https://nextjs.org/learn`):** `URL Accessible` (`HTTP 200`) · `Content Accessible` · `Content Verified`. Guided full-stack dashboard curriculum aligned with [[PRG-T03-C01]]–[[PRG-T03-C03]].", id_map),
        bullet("**[[R009]] (`Zod Docs` — `https://zod.dev/`):** `URL Accessible` (`HTTP 200`) · `Content Accessible` · `Content Verified`. Schema validation library used in [[PRG-T03-C03]] to validate untrusted `FormData`, route params, and `searchParams`.", id_map),
        divider_block(),
        h2("5. Topic Practice & Synthesis Guide", id_map),
        p_block("Use this blueprint to design end-to-end full-stack practice and Capstone projects across [[PRG-T03]]:", id_map),
        bullet("**1. Topic Capstone Project (Full-Stack Integration):**", id_map, children=[
            bullet("**Multi-Route Full-Stack Content / Task Manager:** Build a complete mini-application integrating all 3 Chapters: separate Route Groups `(public)` and `(dashboard)` with persistent nested layouts ([[PRG-T03-C01]]), fetch initial data in parallel inside Server Components wrapped in streaming `<Suspense>` / `loading.tsx` while passing minimal serializable props to Client Components that manage URL `searchParams` filters ([[PRG-T03-C02]]), and implement Create / Edit / Delete mutations via `Server Actions` validated with [[R009]] (`Zod`) and cache invalidation via `revalidatePath` ([[PRG-T03-C03]]).", id_map),
        ]),
        bullet("**2. Must-Be-Automatic Foundations:**", id_map, children=[
            bullet("**Server vs. Client Execution Reflex:** Look at any component file and immediately know whether it executes on the Node.js server or in the browser, and why Server Components can be `async` functions while Client Components own `useState`, `useEffect`, and DOM event listeners.", id_map),
            bullet("**Leaf-Boundary & `children` Composition Pattern:** Place `'use client'` as far down the component tree as possible (at interactive leaf components), and pass Server Components through a Client wrapper's `children: React.ReactNode` prop so server-rendered sub-trees are not forced into the client bundle.", id_map),
            bullet("**Zero-Trust Boundary Validation:** Treat every `params`, `searchParams`, `FormData`, and `Request.json()` payload as untrusted `unknown` data that must be narrowed with TypeScript ([[PRG-T01-C02-U03]]) or validated with [[R009]] (`Zod`) before querying or mutating state.", id_map),
        ]),
        bullet("**3. Cross-Chapter Traps:**", id_map, children=[
            bullet("**Client Bundle Poisoning & Secret Leakage:** Placing `'use client'` at the top of a large page/layout or importing a module that reads server secrets / database clients into a `'use client'` file.", id_map),
            bullet("**Passing Non-Serializable Props Across the RSC Boundary:** Attempting to pass plain functions, class instances, or unserialized `Map`/`Set` objects from a Server Component into a Client Component (only JSON-serializable values, React elements, Promises, and `'use server'` Server Actions can cross the boundary).", id_map),
            bullet("**Stale UI After Server Mutation:** Completing a database insert/update in [[PRG-T03-C03]] without calling `revalidatePath` or `revalidateTag`, leaving the cached route from [[PRG-T03-C02]] displaying outdated data.", id_map),
        ]),
        bullet("**4. Bridge to Next Topics in Roadmap:**", id_map, children=[
            bullet("**[[PRG-T04]] (`Backend Engineering`) & [[PRG-T05]] (`Database Engineering`):** Your understanding of HTTP request/response lifecycles in `Route Handlers` (`route.ts`) and server-side execution in [[PRG-T03]] connects directly to standalone HTTP API design ([[PRG-T04-C01]]) and relational data modeling with PostgreSQL & Prisma ([[PRG-T05-C01]], [[PRG-T05-C02]]).", id_map),
            bullet("**[[PRG-T06]] (`Authentication, Authorization & Security`) & [[PRG-T07]] (`Full-Stack Product Engineering`):** Protecting routes with Next.js Middleware, reading HTTP-only session cookies on the server, and enforcing authorization inside Server Components and Server Actions build directly on [[PRG-T03]].", id_map),
        ]),
        divider_block(),
        h2("6. Final Review & Mastery Audit", id_map),
        todo_item("Verify all 3 Chapters ([[PRG-T03-C01]], [[PRG-T03-C02]], [[PRG-T03-C03]]) and their 23 Units have been practiced and scored in `Mastery (0-4)`.", id_map),
        todo_item("Audit your `My Implementation & Mistake Log` entries across [[PRG-T03]] before advancing to [[PRG-T04]].", id_map),
    ]

def build_prg_t03_c01(id_map):
    return [
        callout_block(
            "**Chapter Objective:** Understand Next.js App Router project structure, file-system routing conventions, nested persistent layouts, streaming loading/error boundaries, typed dynamic route parameters, SEO metadata, and static vs. dynamic rendering.\n"
            "**Completion Criteria:** Architect a multi-route Next.js application with Route Groups, nested layouts, dynamic `[slug]` routes, custom `loading.tsx`/`error.tsx`/`not-found.tsx` boundaries, and verified static/dynamic build output.\n"
            "**Parent Topic:** [[PRG-T03]] | **Prerequisites:** [[PRG-T01-C01-U05]], [[PRG-T01-C02]], [[PRG-T02-C01]] | **Sources:** [[R011]] (`Next.js Learn`), [[R012]] (`Next.js App Router Docs`)",
            id_map,
        ),
        h2("1. Chapter Role & Architectural Mental Model", id_map),
        p_block(
            "[[PRG-T03-C01]] (`Next.js App Router Foundations`) establishes the structural skeleton of a Next.js application. Instead of configuring routes in a central JavaScript router file, the App Router uses **directories inside `src/app/` to define URL segments** and **reserved file names to define the React component hierarchy** for each segment.",
            id_map,
        ),
        p_block(
            "When Next.js renders a route segment, it automatically nests the reserved files of that folder inside its parent segment's layout in a strict, predictable wrapper order:",
            id_map,
        ),
        code_block(
            "// Automatic Component Wrapping Hierarchy inside each Route Segment:\n"
            "<Layout>                         {/* layout.tsx: persists state across navigation */}\n"
            "  <Template>                     {/* template.tsx: optional, remounts on navigation */}\n"
            "    <ErrorBoundary fallback={<Error />}>     {/* error.tsx: must be 'use client' */}\n"
            "      <Suspense fallback={<Loading />}>      {/* loading.tsx: instant streaming UI */}\n"
            "        <ErrorBoundary fallback={<NotFound />}> {/* not-found.tsx */}\n"
            "          <Page />               {/* page.tsx: makes the route publicly accessible */}\n"
            "        </ErrorBoundary>\n"
            "      </Suspense>\n"
            "    </ErrorBoundary>\n"
            "  </Template>\n"
            "</Layout>",
            "typescript",
        ),
        divider_block(),
        h2("2. Core Concepts & Routing Mechanics", id_map),
        bullet(
            "**Safe Colocation vs. Route Exposure ([[PRG-T03-C01-U01]] & [[PRG-T03-C01-U02]]):** Creating a folder inside `src/app/` does **not** expose a URL route by itself—a segment only becomes publicly routable when it contains a `page.tsx` (UI) or `route.ts` (API handler). Furthermore, **Route Groups** `(groupName)` organize routes into logical sections (or separate layouts) without appearing in the URL path, while **Private Folders** `_folderName` completely opt a folder and its children out of routing.",
            id_map,
        ),
        bullet(
            "**Persistent Nested Layouts vs. Templates ([[PRG-T03-C01-U03]]):** `layout.tsx` wraps child segments and **does not re-render or lose client state** when navigating between sibling routes sharing that layout. Only the inner `page.tsx` sub-tree swaps.",
            id_map,
        ),
        bullet(
            "**Declarative Resilience Boundaries ([[PRG-T03-C01-U04]]):** `loading.tsx` wraps the segment in a React `<Suspense>` boundary for instant skeleton streaming, while `error.tsx` (which **must** be a Client Component `'use client'`) catches runtime errors in child segments and provides a `reset()` recovery function without crashing the parent layout.",
            id_map,
        ),
        bullet(
            "**Typed Dynamic Segments, Metadata & Rendering Modes ([[PRG-T03-C01-U05]] – [[PRG-T03-C01-U07]]):** Dynamic folders `[id]`, `[...slug]`, and `[[...slug]]` pass `params` as a `Promise` (in Next.js 15+) to `page.tsx`, `layout.tsx`, and `generateMetadata`. Routes are **Statically Rendered** at build time by default (or pre-generated via `generateStaticParams`) unless they read request-time APIs (`cookies()`, `headers()`, `searchParams`) or opt into **Dynamic Rendering**.",
            id_map,
        ),
        divider_block(),
        h2("3. Unit Sequence & Progression (7 Units)", id_map),
        num_item("[[PRG-T03-C01-U01]] — **Next.js Project Structure:** Top-level folders (`src/app`, `public`), config files (`next.config.ts`, `tsconfig.json` `@/*`), colocation rules, Route Groups `(group)`, and Private Folders `_folder`.", id_map),
        num_item("[[PRG-T03-C01-U02]] — **App Router and File-system Routing:** Mapping directory trees to URL paths and exposing routes with `page.tsx`.", id_map),
        num_item("[[PRG-T03-C01-U03]] — **Layouts and Nested Routes:** Root `app/layout.tsx` (`<html>`/`<body>` requirements), nested segment layouts, and partial rendering across navigation.", id_map),
        num_item("[[PRG-T03-C01-U04]] — **Loading and Error UI:** Streaming skeletons with `loading.tsx`, isolated error recovery with `error.tsx` (`'use client'`), and `notFound()` / `not-found.tsx`.", id_map),
        num_item("[[PRG-T03-C01-U05]] — **Dynamic Routes and Route Parameters:** `[id]`, catch-all `[...slug]`, awaiting `params: Promise<{ id: string }>`, and `generateStaticParams`.", id_map),
        num_item("[[PRG-T03-C01-U06]] — **Metadata and Navigation:** `<Link>` prefetching, `usePathname`/`useRouter`/`redirect`, and static `metadata` vs. dynamic `generateMetadata`.", id_map),
        num_item("[[PRG-T03-C01-U07]] — **Static and Dynamic Rendering:** Build-time static rendering vs. request-time dynamic rendering and inspecting `next build` route indicators (`○ Static`, `● SSG`, `ƒ Dynamic`).", id_map),
        divider_block(),
        h2("4. Resources & Source Attribution", id_map),
        bullet("**[[R012]] (`Next.js App Router Docs`):** *Getting Started: Project Structure, Layouts and Pages, Linking and Navigating, Server and Client Components* (`https://nextjs.org/docs/app`).", id_map),
        bullet("**[[R011]] (`Next.js Learn`):** Chapters 1–5 (*Getting Started, CSS Styling, Optimizing Fonts and Images, Creating Layouts and Pages, Navigating Between Pages*).", id_map),
        divider_block(),
        h2("5. Chapter Practice Guide", id_map),
        p_block("After studying [[PRG-T03-C01-U01]] through [[PRG-T03-C01-U07]], use this blueprint to practice integrating all 7 Units together:", id_map),
        bullet("**1. Chapter Mixed Practice (Multi-Layout Application Shell Mini-Lab):**", id_map, children=[
            bullet("**Integrated Multi-Route Shell:** Build a cohesive Next.js routing shell that combines all 7 Units ([[PRG-T03-C01-U01]]–[[PRG-T03-C01-U07]]): separate a `(marketing)` Route Group (Home, Pricing) from a `(workspace)` Route Group (Dashboard with a persistent sidebar layout), add a dynamic route `projects/[projectId]/page.tsx` that awaits `params` for both the page UI and `generateMetadata`, wire up segment-level `loading.tsx`, `error.tsx` (`'use client'`), and `not-found.tsx` boundaries, and run `next build` to verify which routes compile as Static (`○` / `●`) versus Dynamic (`ƒ`).", id_map),
        ]),
        bullet("**2. Combine with Prior Chapters:**", id_map, children=[
            bullet("**Strict TypeScript & Narrowing ([[PRG-T01-C02]]):** Type all route props (`params: Promise<{ projectId: string }>`, `searchParams: Promise<{ [key: string]: string | string[] | undefined }>`) under strict compiler settings ([[PRG-T01-C02-U09]]) and apply control-flow narrowing ([[PRG-T01-C02-U03]]) to validate route parameters before rendering or triggering `notFound()`.", id_map),
            bullet("**React Component Architecture & Accessible Navigation ([[PRG-T02-C01]] & [[PRG-T02-C04]]):** Structure nested layouts with semantic landmarks (`<header>`, `<nav aria-label=\"Main\">`, `<main>`, `<aside>`) and build a client navigation link component using `usePathname()` that sets `aria-current=\"page\"` on the active route.", id_map),
        ]),
        bullet("**3. Chapter-Wide Traps:**", id_map, children=[
            bullet("**Route Group URL Collisions ([[PRG-T03-C01-U01]] & [[PRG-T03-C01-U02]]):** Creating `app/(marketing)/about/page.tsx` and `app/(shop)/about/page.tsx` in the same project—both resolve to `/about` and fail the build.", id_map),
            bullet("**Expecting `error.tsx` to Catch Errors in Its Own Sibling `layout.tsx` ([[PRG-T03-C01-U03]] & [[PRG-T03-C01-U04]]):** Because Next.js renders `<Layout><ErrorBoundary><Page /></ErrorBoundary></Layout>`, `app/dashboard/error.tsx` catches errors thrown in `app/dashboard/page.tsx` or child segments, **not** errors thrown inside `app/dashboard/layout.tsx` (which must be caught by a parent segment's `error.tsx` or root `global-error.tsx`).", id_map),
            bullet("**Forgetting to `await params` or Accidentally Forcing Dynamic Rendering ([[PRG-T03-C01-U05]] & [[PRG-T03-C01-U07]]):** Accessing `params.id` synchronously without `await params` in Next.js 15+, or reading request-time APIs (`cookies()`, `headers()`, `searchParams`) inside a shared parent layout and unintentionally forcing every child page into Dynamic Rendering (`ƒ`).", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection:**", id_map, children=[
            bullet("**Production Multi-Tenant / SaaS Architecture:** Combining Route Groups `(marketing)` vs. `(dashboard)`, persistent nested layouts, and segment-scoped error/loading boundaries is the industry-standard architecture for SaaS applications that serve fast static marketing pages alongside authenticated application workspaces.", id_map),
            bullet("**Bridge to [[PRG-T03-C02]]:** Mastering the file-system hierarchy in [[PRG-T03-C01]] prepares you directly for [[PRG-T03-C02]], where you decide which components in this hierarchy execute on the server versus the client and how data streams through `<Suspense>` boundaries.", id_map),
        ]),
        divider_block(),
        h2("6. Summary & Spaced Review Guide", id_map),
        todo_item("Complete all 7 Units ([[PRG-T03-C01-U01]] – [[PRG-T03-C01-U07]]) and log your code experiments and pitfalls in each Unit's `My Implementation & Mistake Log`.", id_map),
        todo_item("Verify your multi-route layout & boundary setup with `next build` before advancing to [[PRG-T03-C02]].", id_map),
    ]

def build_prg_t03_c01_u01(id_map):
    return [
        callout_block(
            "**Learning Objective:** Organize a production Next.js App Router codebase using standard top-level directories (`src/app/`, `public/`), configuration files (`next.config.ts`, `tsconfig.json` `@/*` path aliases, `.env.local`), safe component colocation, Private Folders (`_folder`), and Route Groups (`(group)`).\n"
            "**Expected Output:** Design a clean, scalable Next.js directory tree that separates public routes, private colocated modules, and multi-layout Route Groups without URL collisions or client-side secret leaks.\n"
            "**Parent:** [[PRG-T03]] → [[PRG-T03-C01]] | **Prerequisites:** [[PRG-T00-C03]], [[PRG-T01-C01-U05]], [[PRG-T01-C02-U09]], [[PRG-T02-C01]] | **Next Unit:** [[PRG-T03-C01-U02]] | **Sources:** [[R012]] (`Next.js App Router Docs`), [[R011]] (`Next.js Learn`)",
            id_map,
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet(
            "**Top-Level Directory & Configuration Anatomy:** A modern Next.js project places application code inside `src/` to cleanly separate source modules from root configuration files:",
            id_map,
            children=[
                bullet("`src/app/` — The App Router root where directory hierarchies define route segments and reserved files define UI/API entrypoints.", id_map),
                bullet("`public/` — Static assets (images, fonts, `robots.txt`, `favicon.ico`) served directly from the root URL path `/`.", id_map),
                bullet("`next.config.ts` — Type-safe Next.js build, image domain, redirect, and compiler configuration.", id_map),
                bullet("`tsconfig.json` — Strict TypeScript configuration ([[PRG-T01-C02-U09]]) defining path aliases (`\"@/*\": [\"./src/*\"]`) so imports remain stable regardless of folder nesting depth.", id_map),
                bullet("`.env.local` — Environment variables loaded on the server by default; **only** variables explicitly prefixed with `NEXT_PUBLIC_` are inlined into the browser JavaScript bundle.", id_map),
            ],
        ),
        bullet(
            "**Safe Colocation by Default inside `src/app/`:** Unlike the legacy `pages/` router (where every file inside `pages/` automatically became a public URL route), folders inside `src/app/` are **not publicly routable** until you place a `page.tsx` or `route.ts` file inside them. Even when a folder contains `page.tsx`, any sibling helper files (such as `components.tsx`, `schema.ts`, or `utils.ts`) are safely ignored by the router.",
            id_map,
        ),
        bullet(
            "**Private Folders (`_folderName`) — Explicit Routing Opt-Out:** Prefixing any folder name with an underscore (e.g., `src/app/dashboard/_components/` or `src/app/dashboard/_lib/`) marks that folder and all of its subfolders as a **Private Folder**. The App Router completely ignores it for routing, even if someone accidentally places a `page.tsx` file inside it later.",
            id_map,
        ),
        bullet(
            "**Route Groups (`(groupName)`) — Logical Organization Without URL Impact:** Wrapping a folder name in parentheses (e.g., `src/app/(marketing)/about/page.tsx` and `src/app/(dashboard)/settings/page.tsx`) creates a **Route Group**. The parenthesized folder name is **omitted from the public URL** (`/about` and `/settings`), allowing you to group routes by team/feature or give different route groups completely separate `layout.tsx` hierarchies (explored further in [[PRG-T03-C01-U03]]).",
            id_map,
        ),
        bullet(
            "**Reserved File Conventions in `src/app/`:** Only specific filenames trigger App Router behavior: `layout.tsx` (shared persistent UI), `page.tsx` (unique route UI that exposes the URL), `loading.tsx` (Suspense fallback), `error.tsx` (Error boundary), `not-found.tsx` (404 UI), `template.tsx` (re-mounted wrapper), `route.ts` (HTTP API endpoint — **cannot** coexist in the exact same folder level as `page.tsx`), and `default.tsx` (Parallel route fallback).",
            id_map,
        ),
        divider_block(),
        h2("2. Code & Structure Examples", id_map),
        h3("Example 1: Production Next.js Directory Tree with Route Groups & Private Folders", id_map),
        code_block(
            "my-nextjs-app/\n"
            "├── public/\n"
            "│   └── logo.svg                   # Served at /logo.svg\n"
            "├── src/\n"
            "│   ├── app/\n"
            "│   │   ├── layout.tsx             # Root Layout (wraps entire app with <html> & <body>)\n"
            "│   │   ├── globals.css\n"
            "│   │   ├── (marketing)/           # Route Group: omitted from URL path\n"
            "│   │   │   ├── layout.tsx         # Marketing navbar/footer layout\n"
            "│   │   │   ├── page.tsx           # -> URL: /\n"
            "│   │   │   └── pricing/\n"
            "│   │   │       └── page.tsx       # -> URL: /pricing\n"
            "│   │   ├── (dashboard)/           # Route Group: omitted from URL path\n"
            "│   │   │   ├── layout.tsx         # Authenticated sidebar layout\n"
            "│   │   │   ├── _components/       # Private Folder: opted out of routing completely\n"
            "│   │   │   │   └── metric-card.tsx\n"
            "│   │   │   └── analytics/\n"
            "│   │   │       ├── page.tsx       # -> URL: /analytics\n"
            "│   │   │       └── chart-math.ts  # Safely colocated helper (not a route)\n"
            "│   │   └── api/\n"
            "│   │       └── health/\n"
            "│   │           └── route.ts       # -> HTTP API Endpoint: GET /api/health\n"
            "│   ├── components/                # Shared cross-feature UI components (@/components/...)\n"
            "│   └── lib/                       # Shared utilities, DB client, env schema (@/lib/...)\n"
            "├── .env.local                     # Server-only secrets + NEXT_PUBLIC_* vars\n"
            "├── next.config.ts\n"
            "└── tsconfig.json",
            "plain text",
        ),
        h3("Example 2: Type-Safe Path Aliases (`tsconfig.json`) & Environment Boundary (`src/lib/env.ts`)", id_map),
        code_block(
            "// 1. tsconfig.json (excerpt — links with PRG-T01-C02-U09 Strict Compiler Options)\n"
            "// {\n"
            "//   \"compilerOptions\": {\n"
            "//     \"strict\": true,\n"
            "//     \"baseUrl\": \".\",\n"
            "//     \"paths\": { \"@/*\": [\"./src/*\"] }\n"
            "//   }\n"
            "// }\n\n"
            "// 2. src/lib/env.ts — Fail-fast environment variable check\n"
            "function requireServerEnv(key: string): string {\n"
            "  const value = process.env[key];\n"
            "  if (!value) {\n"
            "    throw new Error(`Missing required server environment variable: ${key}`);\n"
            "  }\n"
            "  return value;\n"
            "}\n\n"
            "export const serverEnv = {\n"
            "  // NEVER prefix secrets with NEXT_PUBLIC_:\n"
            "  DATABASE_URL: requireServerEnv(\"DATABASE_URL\"),\n"
            "} as const;\n\n"
            "export const publicEnv = {\n"
            "  // Safe to expose to browser bundle:\n"
            "  APP_URL: process.env.NEXT_PUBLIC_APP_URL ?? \"http://localhost:3000\",\n"
            "} as const;",
            "typescript",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        p_block("Use this blueprint to generate targeted architecture & configuration drills for [[PRG-T03-C01-U01]] and record your work in Section 5:", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**URL Mapping & Colocation Audit:** Given a complex `src/app/` directory tree containing regular folders, Route Groups `(group)`, Private Folders `_folder`, `page.tsx`, `route.ts`, and colocated helper files, determine the exact public URL (or non-routable status) of every file with 100% accuracy.", id_map),
            bullet("**Feature-Sliced Directory Design:** Practice designing clean folder trees for multi-domain web apps (e.g., Public Marketing, Auth Flows, Authenticated Dashboard, and REST Webhooks) using `(group)`, `_components`, and `@/lib/*`.", id_map),
            bullet("**Path Alias & Environment Variable Guardrails:** Configure `@/*` path aliases in `tsconfig.json` and write a fail-fast `env.ts` module that strictly separates server-only secrets from `NEXT_PUBLIC_*` browser variables.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**ESM Modules & Export Conventions ([[PRG-T01-C01-U05]] — `Modules and Code Organization`):** Combine directory organization with Next.js module export rules (`page.tsx` and `layout.tsx` require `export default`, whereas `route.ts` HTTP verbs and `metadata` require named exports like `export async function GET` and `export const metadata`).", id_map),
            bullet("**Strict TypeScript Config & Type Narrowing ([[PRG-T01-C02-U03]] & [[PRG-T01-C02-U09]]):** Narrow `process.env.KEY` from `string | undefined` to `string` at server startup so application code never handles `undefined` environment variables.", id_map),
            bullet("**React Component Separation ([[PRG-T02-C01]]):** Decide which UI components belong in a route-specific `_components/` folder versus the shared cross-feature `src/components/ui/` directory.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**Route Group URL Collision Trap:** Placing `src/app/(marketing)/about/page.tsx` and `src/app/(dashboard)/about/page.tsx` in the same app—both resolve to `/about` and trigger a build-time conflict.", id_map),
            bullet("**Same-Segment `page.tsx` + `route.ts` Conflict:** Placing both `page.tsx` and `route.ts` inside `src/app/dashboard/`, which causes both to compete for `GET /dashboard` (move the API handler to `src/app/api/dashboard/route.ts`).", id_map),
            bullet("**Literal Underscore URL Segment (`%5F` vs `_`):** If a public URL genuinely needs a leading underscore (e.g., `/_preview`), you must name the folder `%5Fpreview`, because `_preview` is treated as a Private Folder and opted out of routing.", id_map),
            bullet("**`NEXT_PUBLIC_` Secret Leak Trap:** Prefixing sensitive credentials like `NEXT_PUBLIC_DATABASE_URL` or `NEXT_PUBLIC_SECRET_KEY`, which causes Next.js to inline the secret directly into client-side JavaScript bundles.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection:**", id_map, children=[
            bullet("**Scalable Feature Colocation in Production Codebases:** In large engineering teams (50+ routes), colocating route-specific `_components`, `_hooks`, and `_actions` inside each feature folder prevents the global `src/components/` directory from becoming an unmaintainable dumping ground.", id_map),
            bullet("**Bridge to [[PRG-T03-C01-U02]], [[PRG-T03-C01-U03]] & [[PRG-T06]]:** The Route Groups `(marketing)` and `(dashboard)` established in this Unit allow separate root/nested layouts in [[PRG-T03-C01-U03]] and targeted authentication middleware protection in [[PRG-T06]].", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "1. If you create `src/app/reports/helpers.ts` and `src/app/reports/chart.tsx` without a `page.tsx` file, is `/reports` accessible in the browser? Why?",
            [
                "No. In the Next.js App Router, directories inside `src/app/` only define route segments—they are not publicly routable until a `page.tsx` (or `route.ts`) file is added inside that directory. This makes colocation safe by default."
            ],
            id_map,
        ),
        toggle_block(
            "2. What is the exact difference between `src/app/(admin)/users/page.tsx` and `src/app/_admin/users/page.tsx`?",
            [
                "`(admin)` is a Route Group: the folder name `(admin)` is omitted from the URL, so `src/app/(admin)/users/page.tsx` is publicly routable at `/users`. By contrast, `_admin` is a Private Folder: the leading underscore opts `_admin` and all its subdirectories out of routing completely, so `src/app/_admin/users/page.tsx` produces no route at all (404)."
            ],
            id_map,
        ),
        toggle_block(
            "3. Why does placing both `page.tsx` and `route.ts` inside `src/app/items/` cause a conflict, and how should you structure them instead?",
            [
                "`page.tsx` renders HTML for requests to `/items`, while `route.ts` handles raw HTTP verbs (`GET`, `POST`, etc.) at the exact same URL `/items`. Because both would compete to handle `GET /items`, Next.js forbids having both in the same segment level. Instead, keep `src/app/items/page.tsx` for UI and place the API handler in `src/app/api/items/route.ts` (or use a Server Action in [[PRG-T03-C03]])."
            ],
            id_map,
        ),
        toggle_block(
            "4. What happens at build time when an environment variable is named `NEXT_PUBLIC_STRIPE_SECRET_KEY` versus `STRIPE_SECRET_KEY`?",
            [
                "Any variable prefixed with `NEXT_PUBLIC_` is statically replaced (inlined as a literal string) into the client-side JavaScript bundle during `next build`, exposing it to anyone who inspects browser DevTools. Without `NEXT_PUBLIC_`, `process.env.STRIPE_SECRET_KEY` is only accessible in server environments (Server Components, Server Actions, Route Handlers) and evaluates to `undefined` in browser code."
            ],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        quote_block("**Feynman One-Liner (Summarize the core concept of this Unit in 1–2 sentences in your own words):**\n[Write your summary here after studying]", id_map),
        quote_block("**My Solution / Working / Code (Workspace for your directory architecture, config files, or practice exercises):**\n[Paste your practice tasks and code solutions here]", id_map),
        quote_block("**Mistake & Pitfall Log (Record routing collisions, env leaks, or misconceptions encountered during practice to target on Next Review):**\n- [Log mistakes and lessons learned here]", id_map),
        divider_block(),
        h2("6. Completion Checklist & Mastery Review", id_map),
        todo_item("Studied the core project structure conventions, Route Groups `(group)`, and Private Folders `_folder` in [[PRG-T03-C01-U01]].", id_map),
        todo_item("Practiced URL-mapping and directory architecture scenarios using the Section 3 `Practice Guide`.", id_map),
        todo_item("Answered all 4 Active Recall questions and recorded personal notes/solutions in Section 5.", id_map),
        todo_item("Updated `Status`, `Mastery (0-4)`, `Last Reviewed`, and `Next Review` properties on this page.", id_map),
    ]

def inspect_blocks_recursively(block_id, token):
    """Fetch all blocks and nested children to count @Page mentions and verify zero [[ or Thai text."""
    top_blocks = get_all_blocks(block_id, token)
    all_fetched = list(top_blocks)
    for b in top_blocks:
        if b.get("has_children"):
            children = get_all_blocks(b["id"], token)
            all_fetched.extend(children)
    dumped = json.dumps(all_fetched, ensure_ascii=False)
    unresolved_match = re.search(r"\[\[[A-Z0-9\-]+\]\]", dumped)
    if unresolved_match:
        raise AssertionError(f"Found unresolved ID token {unresolved_match.group(0)} in live Notion page {block_id}!")
    thai_match = re.search(r"[\u0E00-\u0E7F]+", dumped)
    if thai_match:
        raise AssertionError(f"Found Thai characters '{thai_match.group(0)}' in live Notion page {block_id}!")
    mention_count = dumped.count('"type": "mention"')
    eq_block_count = sum(1 for b in all_fetched if b.get("type") == "equation")
    return len(top_blocks), len(all_fetched), mention_count, eq_block_count

def main():
    env = load_env()
    token = env.get("NOTION_TOKEN")
    rules_id = "40c3818f-8ba0-8002-92f1-e971793125e3"

    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)

    mth_t02_id = id_map["MTH-T02"]["id"]
    mth_t02_c01_id = id_map["MTH-T02-C01"]["id"]
    mth_t02_c01_u01_id = id_map["MTH-T02-C01-U01"]["id"]

    prg_t03_id = id_map["PRG-T03"]["id"]
    prg_t03_c01_id = id_map["PRG-T03-C01"]["id"]
    prg_t03_c01_u01_id = id_map["PRG-T03-C01-U01"]["id"]

    # Step 1: Update Rules Page (100% English + Inline Link Check + Vertical Math Derivation Rule)
    update_rules_page(rules_id, id_map, token)

    # Step 2: Replace & Validate All 6 Test Pages
    print("\n=== Populating & Validating All 6 Test Pages (100% English, Resolved @Page Mentions, Vertical Math Derivations) ===")
    targets = [
        ("MTH-T02", mth_t02_id, build_mth_t02_topic(id_map)),
        ("MTH-T02-C01", mth_t02_c01_id, build_mth_t02_c01(id_map)),
        ("MTH-T02-C01-U01", mth_t02_c01_u01_id, build_mth_t02_c01_u01(id_map)),
        ("PRG-T03", prg_t03_id, build_prg_t03_topic(id_map)),
        ("PRG-T03-C01", prg_t03_c01_id, build_prg_t03_c01(id_map)),
        ("PRG-T03-C01-U01", prg_t03_c01_u01_id, build_prg_t03_c01_u01(id_map)),
    ]
    for fid, pid, blocks in targets:
        replace_page_blocks(pid, blocks, label=fid, token=token)
        top_n, total_n, mentions, eq_blks = inspect_blocks_recursively(pid, token)
        print(f"  Verified {fid} ({pid}): {top_n} top blocks ({total_n} total incl. children), {mentions} live @Page mentions, {eq_blks} vertical equation blocks, 0 unresolved [[ID]], 0 non-English chars!")

    print("\n=== ALL 6 PAGES + RULES PAGE VERIFIED 100% CLEAN! ===")

if __name__ == "__main__":
    main()
