import json
import re
from apply_rules_and_test_pages import (
    load_env,
    notion_request,
    get_all_blocks,
    parse_rt,
    rt,
    h2,
    h3,
    p_block,
    callout_block,
    quote_block,
    divider_block,
    eq_block,
    bullet,
    num_item,
    todo_item,
    toggle_block,
    validate_blocks_clean,
    inspect_blocks_recursively
)

def file_upload_image_block(file_upload_id, caption=None, id_map=None):
    b = {
        "object": "block",
        "type": "image",
        "image": {
            "type": "file_upload",
            "file_upload": {"id": file_upload_id}
        }
    }
    if caption:
        b["image"]["caption"] = parse_rt(caption, id_map) if id_map else [rt(caption)]
    return b

def build_mth_t01_c12_consolidated_blocks(id_map, preserved_user_drill_blocks, img_map):
    """
    Consolidated single-version of MTH-T01-C12: Math Models and Geometry
    Uses 100% parametric engine diagrams hosted natively on Notion.
    """
    blocks = [
        # Callout Header
        callout_block(
            "**Chapter Objective:** Translate applied word problems, coin/mixture scenarios, and 2D/3D geometric models into solvable linear equations. Master Euclidean spatial relationships (angles, polygons, circles, and cylinders) by coupling visual figures with exact algebraic invariant constraints.\n\n"
            "**Parent Topic:** [[MTH-T01]] | **Resource:** [[R035]] (OpenStax Prealgebra 2e, Ch 9) | **Level:** Prealgebra Foundation | **Units:** 7 Units ([[MTH-T01-C12-U01]] to [[MTH-T01-C12-U07]])",
            id_map,
            color="blue_background"
        ),
        divider_block(),

        # Section 1: Role & Scope
        h2("Role in Prealgebra & Spatial Foundations", id_map),
        p_block(
            "Geometry in Prealgebra bridges abstract single-variable linear equations ([[MTH-T01-C11]]) and physical spatial modeling. Geometric theorems act as invariant equation generators: geometric properties (such as complementary angles, triangle angle sums, perimeters, and the Pythagorean theorem) define equalities that allow students to isolate unknown dimensions.",
            id_map
        ),
        p_block(
            "Furthermore, geometric models introduce dimensional progression: linear perimeter ($L$), planar surface area ($L^2$), and volumetric capacity ($L^3$). Mastering these fundamentals is the prerequisite for Cartesian graphing ([[MTH-T01-C14]]), trigonometry ([[MTH-T02]]), and Newtonian physics ([[PHY-T01]]).",
            id_map
        ),
        divider_block(),

        # Section 2: Geometric Visual Models & Algebraic Invariants
        h2("Geometric Visual Models & Algebraic Invariants", id_map),
        p_block(
            "In our Parametric Learning Architecture, every spatial configuration pairs a programmatically generated visual diagram with its exact symbolic algebraic invariant. This structure prevents spatial misinterpretations and reinforces rigorous formula derivation.",
            id_map
        ),

        # Model 1: Right Triangle & Pythagorean
        h3("1. Right Triangles & The Pythagorean Invariant", id_map),
        file_upload_image_block(
            img_map["param_triangle.svg"],
            "Figure 1: Euclidean Right Triangle with perpendicular legs $a, b$ and hypotenuse $c$.",
            id_map
        ),
        p_block(
            "In any Euclidean right triangle, the side opposite the $90^\\circ$ right angle is the hypotenuse ($c$). The two sides forming the right angle are perpendicular legs ($a$ and $b$). The relationship between side lengths is governed by the invariant:",
            id_map
        ),
        eq_block("a^2 + b^2 = c^2 \\iff c = \\sqrt{a^2 + b^2}"),
        bullet(
            "**Hypotenuse Structural Invariant:** Side $c$ is strictly opposite the right angle and is always the longest side in a Euclidean right triangle ($c > a$ and $c > b$).",
            id_map
        ),
        bullet(
            "**Isolating a Missing Leg:** When the hypotenuse $c$ and one leg $b$ are known, rearrange the formula before taking square roots:",
            id_map
        ),
        eq_block("a = \\sqrt{c^2 - b^2}"),
        bullet(
            "**Common Integer Pythagorean Triples:** $(3, 4, 5)$, $(5, 12, 13)$, $(8, 15, 17)$, and $(7, 24, 25)$. Any scalar multiple $k(a, b, c)$ is also a valid right triangle.",
            id_map
        ),

        # Model 2: Angle Relationships
        h3("2. Angle Partitions & Intersecting Rays", id_map),
        file_upload_image_block(
            img_map["complementary_angles.svg"],
            "Figure 2: Orthogonal rays forming complementary angles ($\\angle 1 + \\angle 2 = 90^\\circ$).",
            id_map
        ),
        p_block(
            "Angles express rotational divergence between intersecting rays. Fundamental angle invariants define primary linear equations:",
            id_map
        ),
        eq_block("\\angle 1 + \\angle 2 = 90^\\circ \\quad \\text{(Complementary Angles)}"),
        eq_block("\\angle 1 + \\angle 2 = 180^\\circ \\quad \\text{(Supplementary Angles / Linear Pair)}"),
        bullet(
            "**Triangle Angle-Sum Invariant:** For any triangle in the Euclidean plane with interior angles $\\alpha, \\beta, \\gamma$:",
            id_map
        ),
        eq_block("\\alpha + \\beta + \\gamma = 180^\\circ"),
        bullet(
            "**Vertical Angles Invariant:** Intersecting lines generate opposite vertical angles that are strictly congruent: $\\angle \\text{top} = \\angle \\text{bottom}$ and $\\angle \\text{left} = \\angle \\text{right}$.",
            id_map
        ),

        # Model 3: Circles
        h3("3. Circles — Radius, Diameter & Area Invariants", id_map),
        file_upload_image_block(
            img_map["param_circle.svg"],
            "Figure 3: Geometric anatomy of a circle showing center, radius $r$, diameter $d = 2r$, and circumference $C = 2\\pi r$.",
            id_map
        ),
        p_block(
            "A circle is the planar locus of points equidistant from a central origin. The fundamental structural distinction between radius and diameter is:",
            id_map
        ),
        eq_block("d = 2r \\iff r = \\frac{d}{2}"),
        eq_block("C = 2\\pi r = \\pi d"),
        eq_block("A = \\pi r^2 = \\pi \\left(\\frac{d}{2}\\right)^2 = \\frac{1}{4}\\pi d^2"),
        bullet(
            "**Critical Mistake Prevention (Diameter vs Radius Trap):** When word problems specify a diameter (e.g., *'a circular garden has diameter $10\\text{ m}$'*), students must immediately compute $r = d/2 = 5\\text{ m}$ before calculating area. Never square the diameter directly in $A = \\pi r^2$!",
            id_map
        ),
        bullet(
            "**Dimensional Consistency:** Circumference $C$ has linear units ($[L]$), whereas Area $A$ has squared units ($[L^2]$).",
            id_map
        ),

        # Model 4: Quadrilaterals & Trapezoids
        h3("4. Quadrilaterals & Trapezoid Decomposition", id_map),
        file_upload_image_block(
            img_map["param_trapezoid.svg"],
            "Figure 4: Trapezoid generated from parallel bases $b_1, b_2$ and altitude $h$.",
            id_map
        ),
        p_block(
            "A trapezoid is a quadrilateral with at least one pair of parallel sides ($b_1$ and $b_2$). The perpendicular distance between the bases is altitude $h$. Its area decomposes into the average of the bases times height:",
            id_map
        ),
        eq_block("A = \\frac{1}{2}h(b_1 + b_2)"),
        bullet(
            "**Isolating Base $b_1$:** Multiplying by $2$ and dividing by $h$ yields the linear isolation: $b_1 = \\frac{2A}{h} - b_2$.",
            id_map
        ),

        # Model 5: 3D Solids
        h3("5. 3D Spatial Geometry — Right Circular Cylinder", id_map),
        file_upload_image_block(
            img_map["param_cylinder.svg"],
            "Figure 5: Right circular cylinder of circular base radius $r$ and perpendicular height $h$.",
            id_map
        ),
        p_block(
            "3D solids extend planar 2D figures along a perpendicular axis of height $h$. For a right circular cylinder:",
            id_map
        ),
        eq_block("V = (\\text{Base Area}) \\cdot h = \\pi r^2 h"),
        eq_block("A_{\\text{total}} = 2\\pi r^2 + 2\\pi rh = 2\\pi r(r + h)"),
        bullet(
            "**Volume Invariant:** The internal volume is the uniform stacking of circular cross-sections of area $\\pi r^2$ through altitude $h$ ($[L^3]$).",
            id_map
        ),
        bullet(
            "**Surface Area Net Decomposition:** The outer boundary comprises two circular lids ($2 \\cdot \\pi r^2$) plus an unrolled rectangular lateral wrapper of dimensions $2\\pi r \\times h$.",
            id_map
        ),
        divider_block(),

        # Section 3: Unit Sequence & Progression
        h2("Unit Sequence & Progression", id_map),
        p_block("Complete the Units in ascending numerical order. Master each unit's visual models and algebraic translations:", id_map),
        num_item("**[[MTH-T01-C12-U01]] — Use a Problem Solving Strategy:** Master the 7-step modeling protocol to translate textual statements into solvable algebraic equations.", id_map),
        num_item("**[[MTH-T01-C12-U02]] — Solve Money Applications:** Disentangle quantity (count of coins/items) from monetary value using structured algebraic tables.", id_map),
        num_item("**[[MTH-T01-C12-U03]] — Use Properties of Angles, Triangles, and the Pythagorean Theorem:** Solve geometric configurations using complementary, supplementary, triangle sums, and $a^2 + b^2 = c^2$.", id_map),
        num_item("**[[MTH-T01-C12-U04]] — Use Properties of Rectangles, Triangles, and Trapezoids:** Compute perimeters and areas of rectilinear figures, trapezoids ($A = \\frac{1}{2}h(b_1 + b_2)$), and decomposed polygons.", id_map),
        num_item("**[[MTH-T01-C12-U05]] — Solve Geometry Applications: Circles and Irregular Figures:** Calculate exact and decimal circumference and area; decompose irregular composites into rectangles, triangles, and semicircles.", id_map),
        num_item("**[[MTH-T01-C12-U06]] — Solve Geometry Applications: Volume and Surface Area:** Compute capacity ($V$) and boundary surface area ($A$) for rectangular solids, cylinders, cones, and spheres.", id_map),
        num_item("**[[MTH-T01-C12-U07]] — Solve a Formula for a Specific Variable:** Isolate designated variables in multi-variable geometric formulas (e.g., solve $A = \\frac{1}{2}h(b_1 + b_2)$ for $b_1$).", id_map),
        divider_block(),

        # Section 4: Level 2 Chapter Practice Guide
        h2("Practice Guide", id_map),
        p_block("This Chapter Practice Guide directs AI drill engines and independent review across 4 core competencies:", id_map),

        h3("1. Conceptual Check", id_map),
        bullet("Verify why the hypotenuse $c$ in a Euclidean right triangle must strictly exceed either leg ($c > a$ and $c > b$).", id_map),
        bullet("Explain why multiplying all dimensions of a 2D shape by factor $k$ scales perimeter by $k^1$, area by $k^2$, and 3D volume by $k^3$.", id_map),
        bullet("Clarify why vertical angles are always congruent without performing arithmetic calculation.", id_map),

        h3("2. Computational / Formula Drill", id_map),
        bullet("Calculate the missing leg of a right triangle with hypotenuse $c = 25\\text{ cm}$ and leg $a = 7\\text{ cm}$ ($b = \\sqrt{25^2 - 7^2} = 24\\text{ cm}$).", id_map),
        bullet("Find the exact area (in terms of $\\pi$) and approximation (using $\\pi \\approx 3.14$) of a circular patio with diameter $d = 14\\text{ m}$.", id_map),
        bullet("Solve the trapezoid area formula $A = \\frac{1}{2}h(b_1 + b_2)$ for $b_1$ in fully isolated algebraic form ($b_1 = \\frac{2A}{h} - b_2$).", id_map),
        bullet("Compute the volume and total surface area of a cylinder with radius $r = 3\\text{ cm}$ and height $h = 8\\text{ cm}$.", id_map),

        h3("3. Edge Cases & Trap Detection", id_map),
        bullet("Trap: Confusing diameter with radius when computing circle area (evaluating $\\pi d^2$ instead of $\\pi (d/2)^2$).", id_map),
        bullet("Trap: Misidentifying the hypotenuse in non-standard orientations where the right angle is at the top or side.", id_map),
        bullet("Trap: Dimensional unit mismatch (e.g., base given in feet and height given in inches without unit conversion).", id_map),
        bullet("Trap: Forgetting the top and bottom circular bases when calculating total surface area of a closed cylinder.", id_map),

        h3("4. Real-world Synthesis", id_map),
        bullet("Applied flooring and fencing: Calculating perimeter for baseboards vs. area for tiling in an L-shaped room.", id_map),
        bullet("Composite architecture: Calculating the volume and exterior surface area of a grain silo (cylinder capped with a hemisphere).", id_map),
        bullet("Value-mixture translation: Setting up linear equations to calculate coin distributions (quarters and dimes) from total count and dollar value.", id_map),
        divider_block(),

        # Section 5: Active Recall
        h2("Active Recall Questions", id_map),
        p_block("Attempt each synthesis question mentally or on scratch paper before revealing the reference solution:", id_map),
        toggle_block(
            "How do you systematically avoid the 'Diameter vs Radius Confusion' in circular geometry problems?",
            [
                "**Reference Solution:** Always write down $d = \\text{given}$ and immediately compute $r = d / 2$ as the first explicit step before substituting into formulas. Circumference can use either ($C = \\pi d = 2\\pi r$), but Area strictly requires radius: $A = \\pi r^2 = \\pi (d/2)^2 = \\frac{1}{4}\\pi d^2$."
            ],
            id_map
        ),
        toggle_block(
            "Given a right triangle with hypotenuse $c = 17\\text{ cm}$ and one leg $a = 8\\text{ cm}$, derive the length of leg $b$ step-by-step.",
            [
                "**Reference Solution:**\n1. State the Pythagorean Theorem: $a^2 + b^2 = c^2$.\n2. Isolate unknown leg $b^2 = c^2 - a^2$.\n3. Substitute values: $b^2 = 17^2 - 8^2 = 289 - 64 = 225$.\n4. Take positive square root: $b = \\sqrt{225} = 15\\text{ cm}$."
            ],
            id_map
        ),
        toggle_block(
            "How do you isolate base $b_1$ from the trapezoid area formula $A = \\frac{1}{2}h(b_1 + b_2)$?",
            [
                "**Reference Solution:**\n1. Multiply both sides by 2: $2A = h(b_1 + b_2)$.\n2. Divide both sides by $h$: $\\frac{2A}{h} = b_1 + b_2$.\n3. Subtract $b_2$: $b_1 = \\frac{2A}{h} - b_2$."
            ],
            id_map
        ),
        divider_block(),

        # Section 6: Synthesis & Challenge
        h2("Chapter Synthesis & Problem-Solving Challenge", id_map),
        todo_item("Solve the trapezoid area formula $A = \\frac{1}{2}h(b_1 + b_2)$ for $b_1$, and evaluate for $A = 90\\text{ cm}^2, h = 6\\text{ cm}, b_2 = 12\\text{ cm}$.", id_map),
        todo_item("Find the exact total surface area and volume of a cylinder with radius $r = 4\\text{ cm}$ and height $h = 10\\text{ cm}$ in terms of $\\pi$.", id_map),
        todo_item("Calculate the perimeter and area of a Norman window (a rectangle of width $6\\text{ ft}$ and height $8\\text{ ft}$ surmounted by a semicircle).", id_map),
        divider_block(),

        # Section 7: Chapter Review & Spaced Retention Guide
        h2("Chapter Review & Spaced Retention Guide", id_map),
        bullet("Keep 'Status' (initial completion) separate from 'Mastery (0-4)' (long-term recall and problem-solving fluency).", id_map),
        bullet("When reviewing this Chapter, inspect the 'My Implementation & Mistake Log' inside each Unit first to target past sign, unit, and radius/diameter errors.", id_map),
    ]

    # Append all preserved drill blocks from user's history!
    if preserved_user_drill_blocks:
        for b in preserved_user_drill_blocks:
            bt = b["type"]
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": b[bt]["rich_text"]
                }
            })

    return blocks
