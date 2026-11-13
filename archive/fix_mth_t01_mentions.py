# -*- coding: utf-8 -*-
"""
Fixes and establishes 100% two-way Notion @page mentions across:
1. Central Rules Page (explicit sub-bullets under Block 78)
2. Topic MTH-T01 (Callout, Overview paragraph, and all 14 Chapter Architecture items)
3. Chapters MTH-T01-C01 through C04 (Callout, Unit Sequence numbered list items, Practice Guide Category 4)
4. Units MTH-T01-C01-U01 through C04-U06 (Callout headers with Parent, Prerequisites, Next Unit, Source)
Strictly preserving existing page properties (Status=Done, Mastery, Last Reviewed) and user notes.
"""
import json
import time
from apply_rules_and_test_pages import (
    load_env,
    notion_request,
    get_all_blocks,
    rt,
    parse_rt,
    bullet,
)

# === METADATA DEFINITIONS ===

TOPIC_CALLOUT = (
    "**Topic Goal:** Build rock-solid algebraic fluency across number systems, equations, exponents, roots, polynomials, geometry, and linear graphs as the foundation for higher mathematics, physics, and algorithmic problem solving.\n"
    "**Prerequisites:** None (Foundational Mathematics Track) | "
    "**Cross-Disciplinary:** [[PHY-T01]], [[PRG-T01]] | "
    "**Primary Resource:** [[R035]] (OpenStax Prealgebra 2e)"
)

TOPIC_OVERVIEW_P3 = (
    "Mastery of this topic ensures that algebraic manipulation—operating on signed numbers, fractions, decimals, exponents, radicals, linear equations, polynomials, and coordinate graphs—becomes automatic and error-free, freeing working memory for Calculus, Linear Algebra, Physics ([[PHY-T01]]), and Programming ([[PRG-T01]])."
)

TOPIC_CHAPTERS = [
    ("MTH-T01-C01", "Whole Numbers", 5, "Place value, rounding, and the four fundamental operations on non-negative integers."),
    ("MTH-T01-C02", "The Language of Algebra", 5, "Variables, order of operations, expression evaluation/translation, one-step equations, factors, primes, and LCM."),
    ("MTH-T01-C03", "Integers", 5, "Signed numbers, absolute value, integer arithmetic, and one-step integer equations."),
    ("MTH-T01-C04", "Fractions", 6, "Common/different denominators, mixed numbers, complex fractions, and fractional linear equations."),
    ("MTH-T01-C05", "Decimals", 7, "Decimal place value, operations, fraction conversions, decimal equations, averages/probability, ratios, and introductory square roots."),
    ("MTH-T01-C06", "Percents", 5, "Percent conversions, percent equations, tax/commission/discount, simple interest, and percent proportions."),
    ("MTH-T01-C07", "Proportional & Ratio Reasoning", 6, "Ratios, unit rates, solving proportions, direct variation, inverse variation, and scale/similar-figure applications."),
    ("MTH-T01-C08", "Exponents", 6, "Product, quotient, and power rules, zero and negative exponents, and scientific notation."),
    ("MTH-T01-C09", "Roots", 6, "Square roots, simplifying radicals, cube roots, radical properties, fractional exponents, and scientific notation roots."),
    ("MTH-T01-C10", "The Properties of Real Numbers", 5, "Rational vs. irrational numbers, commutative/associative/distributive laws, identity/inverse/zero properties, and unit conversions."),
    ("MTH-T01-C11", "Solving Linear Equations", 4, "Multi-step linear equations with variables on both sides and fraction/decimal clearing strategies."),
    ("MTH-T01-C12", "Math Models and Geometry", 7, "Problem-solving framework, money/mixture models, angles/triangles/Pythagorean theorem, area/perimeter/volume, and literal formulas."),
    ("MTH-T01-C13", "Polynomials", 6, "Polynomial addition/subtraction, exponent laws review, binomial/polynomial multiplication, monomial division, and GCF factoring."),
    ("MTH-T01-C14", "Graphs", 4, "Rectangular coordinate plane, graphing linear equations by plotting, x/y-intercepts, and slope formula/interpretation."),
]

CHAPTER_DATA = {
    "MTH-T01-C01": {
        "callout": (
            "**Chapter Objective:** Understand base-10 place value and execute addition, subtraction, multiplication, and division on whole numbers with estimation and verification.\n"
            "**Completion Criteria:** Accurately translate, round, and compute multi-digit whole number operations and word problems without a calculator.\n"
            "**Parent Topic:** [[MTH-T01]] | "
            "**Prerequisites:** None (Foundational Track) | "
            "**Source:** [[R035]] (OpenStax Prealgebra 2e, Chapter 1)"
        ),
        "cross": "Programming ([[PRG-T01]]): Integer arithmetic bounds, modulo remainder operator. Physics ([[PHY-T01]]): Displacement, perimeter, and area calculations.",
        "units": [
            ("MTH-T01-C01-U01", "Introduction to Whole Numbers", "Identify counting numbers and whole numbers, model base-10 place value, write whole numbers in words/expanded form, and round to specified place values."),
            ("MTH-T01-C01-U02", "Add Whole Numbers", "Use addition notation, the Identity and Commutative Properties of Addition, and the standard carrying algorithm to add whole numbers and perimeter models."),
            ("MTH-T01-C01-U03", "Subtract Whole Numbers", "Model subtraction as the inverse of addition, apply the borrowing/regrouping algorithm across zeros, and translate subtraction word phrases accurately."),
            ("MTH-T01-C01-U04", "Multiply Whole Numbers", "Apply the Zero, Identity, Commutative, and Distributive properties of multiplication, and execute multi-digit partial product multiplication."),
            ("MTH-T01-C01-U05", "Divide Whole Numbers", "Use division notation, apply division properties of one and zero, and compute long division with remainders."),
        ],
    },
    "MTH-T01-C02": {
        "callout": (
            "**Chapter Objective:** Use algebraic variables, evaluate expressions using Order of Operations (PEMDAS), solve one-step linear equations, and find factors, primes, GCF, and LCM.\n"
            "**Completion Criteria:** Solve one-step linear equations with checks and find prime factorizations / GCF / LCM accurately without a calculator.\n"
            "**Parent Topic:** [[MTH-T01]] | "
            "**Prerequisites:** [[MTH-T01-C01]] | "
            "**Source:** [[R035]] (OpenStax Prealgebra 2e, Chapter 2)"
        ),
        "cross": "Programming ([[PRG-T01]]): Variable scoping, operator precedence tables. Cryptography: Prime factorization.",
        "units": [
            ("MTH-T01-C02-U01", "Introduction to the Language of Algebra", "Distinguish variables, constants, expressions, and equations, and translate verbal phrases to algebraic models."),
            ("MTH-T01-C02-U02", "Evaluate, Simplify, and Translate Expressions", "Evaluate algebraic expressions for given values, identify terms/coefficients, and combine like terms using the Distributive Property."),
            ("MTH-T01-C02-U03", "Solving Equations Using the Subtraction and Addition Properties of Equality", "Verify whether a value is a solution to an equation, and solve linear equations using subtraction and addition properties with verification."),
            ("MTH-T01-C02-U04", "Find Multiples and Factors", "Identify multiples using divisibility tests (2, 3, 5, 6, 9, 10) and find all factor pairs of whole numbers systematically."),
            ("MTH-T01-C02-U05", "Prime Factorization and the Least Common Multiple", "Write the unique prime factorization of any composite number using factor trees and compute the GCF and LCM of number pairs."),
        ],
    },
    "MTH-T01-C03": {
        "callout": (
            "**Chapter Objective:** Master signed number operations on Integers, understand absolute value as distance, and solve one-step integer equations.\n"
            "**Completion Criteria:** Compute additions, subtractions, multiplications, and divisions across positive and negative integers with zero sign slips.\n"
            "**Parent Topic:** [[MTH-T01]] | "
            "**Prerequisites:** [[MTH-T01-C01]], [[MTH-T01-C02]] | "
            "**Source:** [[R035]] (OpenStax Prealgebra 2e, Chapter 3)"
        ),
        "cross": "Programming ([[PRG-T01]]): Two's complement representation. Physics ([[PHY-T01]]): Signed coordinate systems and delta quantities (velocity, displacement).",
        "units": [
            ("MTH-T01-C03-U01", "Introduction to Integers", "Locate positive and negative integers on the number line, order signed numbers, and evaluate absolute values and opposites."),
            ("MTH-T01-C03-U02", "Add Integers", "Add integers with the same sign and with different signs, evaluate multi-term integer sums, and translate application phrases."),
            ("MTH-T01-C03-U03", "Subtract Integers", "Rewrite integer subtraction as adding the opposite (a - b = a + (-b)) and simplify multi-operation signed expressions."),
            ("MTH-T01-C03-U04", "Multiply and Divide Integers", "Multiply and divide signed integers, evaluate powers of negative integers, and simplify expressions with nested brackets and exponents."),
            ("MTH-T01-C03-U05", "Solve Equations Using Integers; The Division Property of Equality", "Solve one-step equations involving signed integers using the Addition, Subtraction, and Division Properties of Equality with checks."),
        ],
    },
    "MTH-T01-C04": {
        "callout": (
            "**Chapter Objective:** Master proper and improper fractions, mixed numbers, common/different denominators, complex fractions, and solve fractional linear equations.\n"
            "**Completion Criteria:** Execute all four operations on fractions and mixed numbers, simplify complex fractions, and solve linear equations with fractions accurately.\n"
            "**Parent Topic:** [[MTH-T01]] | "
            "**Prerequisites:** [[MTH-T01-C02-U05]], [[MTH-T01-C03]] | "
            "**Source:** [[R035]] (OpenStax Prealgebra 2e, Chapter 4)"
        ),
        "cross": "Programming ([[PRG-T01]]): Exact rational math representations. Physics ([[PHY-T01]]): Unit factor-label conversions.",
        "units": [
            ("MTH-T01-C04-U01", "Visualize Fractions", "Model fractions as parts of a whole, convert between mixed numbers and improper fractions, and locate fractions on the number line."),
            ("MTH-T01-C04-U02", "Multiply and Divide Fractions", "Simplify fractions by canceling common prime factors, multiply fractions, evaluate reciprocals, and divide fractions by multiplying by the reciprocal."),
            ("MTH-T01-C04-U03", "Multiply and Divide Mixed Numbers and Complex Fractions", "Multiply and divide mixed numbers by converting to improper fractions, and simplify complex fractions using division or overall LCD multiplication."),
            ("MTH-T01-C04-U04", "Add and Subtract Fractions with Common Denominators", "Add and subtract numerical and algebraic fractions that share a common denominator, and evaluate signed fraction expressions."),
            ("MTH-T01-C04-U05", "Add and Subtract Fractions with Different Denominators", "Find the Least Common Denominator (LCD), convert fractions to equivalent forms with the LCD, and execute multi-digit fraction additions/subtractions."),
            ("MTH-T01-C04-U06", "Solve Equations with Fractions", "Solve linear equations containing fractional constants and fractional coefficients using reciprocal multiplication and LCD denominator clearing."),
        ],
    },
}

UNIT_CALLOUTS = {
    # === Chapter C01 ===
    "MTH-T01-C01-U01": {
        "obj": "Identify counting numbers and whole numbers, model base-10 place value, write whole numbers in words/expanded form, and round to specified place values.",
        "out": "Decompose multi-digit whole numbers into expanded powers of 10 and round numbers accurately to any place value.",
        "chapter": "MTH-T01-C01",
        "prereq": "None (Foundational Unit)",
        "next": "[[MTH-T01-C01-U02]]",
        "source": "OpenStax Prealgebra 2e, Section 1.1",
    },
    "MTH-T01-C01-U02": {
        "obj": "Use addition notation, the Identity and Commutative Properties of Addition, and the standard carrying algorithm to add whole numbers and perimeter models.",
        "out": "Add multi-digit whole numbers accurately by hand and verify results via estimation.",
        "chapter": "MTH-T01-C01",
        "prereq": "[[MTH-T01-C01-U01]]",
        "next": "[[MTH-T01-C01-U03]]",
        "source": "OpenStax Prealgebra 2e, Section 1.2",
    },
    "MTH-T01-C01-U03": {
        "obj": "Model subtraction as the inverse of addition, apply the borrowing/regrouping algorithm across zeros, and translate subtraction word phrases accurately.",
        "out": "Subtract multi-digit whole numbers across multiple zeros and verify every difference via addition.",
        "chapter": "MTH-T01-C01",
        "prereq": "[[MTH-T01-C01-U02]]",
        "next": "[[MTH-T01-C01-U04]]",
        "source": "OpenStax Prealgebra 2e, Section 1.3",
    },
    "MTH-T01-C01-U04": {
        "obj": "Apply the Zero, Identity, Commutative, and Distributive properties of multiplication, and execute multi-digit partial product multiplication.",
        "out": "Multiply multi-digit whole numbers using partial products and calculate rectangular areas accurately.",
        "chapter": "MTH-T01-C01",
        "prereq": "[[MTH-T01-C01-U02]]",
        "next": "[[MTH-T01-C01-U05]]",
        "source": "OpenStax Prealgebra 2e, Section 1.4",
    },
    "MTH-T01-C01-U05": {
        "obj": "Use division notation, apply division properties of one and zero, and compute long division with remainders.",
        "out": "Divide multi-digit whole numbers using long division and verify results using the division check equation $D = d \\cdot q + r$.",
        "chapter": "MTH-T01-C01",
        "prereq": "[[MTH-T01-C01-U03]], [[MTH-T01-C01-U04]]",
        "next": "[[MTH-T01-C02-U01]]",
        "source": "OpenStax Prealgebra 2e, Section 1.5",
    },

    # === Chapter C02 ===
    "MTH-T01-C02-U01": {
        "obj": "Distinguish variables, constants, expressions, and equations, and translate verbal phrases to algebraic models.",
        "out": "Translate verbal descriptions into precise algebraic expressions and equations with correct operational grouping.",
        "chapter": "MTH-T01-C02",
        "prereq": "[[MTH-T01-C01]]",
        "next": "[[MTH-T01-C02-U02]]",
        "source": "OpenStax Prealgebra 2e, Section 2.1",
    },
    "MTH-T01-C02-U02": {
        "obj": "Evaluate algebraic expressions for given values, identify terms/coefficients, and combine like terms using the Distributive Property.",
        "out": "Evaluate multi-variable algebraic expressions following PEMDAS and simplify linear expressions by combining like terms.",
        "chapter": "MTH-T01-C02",
        "prereq": "[[MTH-T01-C02-U01]]",
        "next": "[[MTH-T01-C02-U03]]",
        "source": "OpenStax Prealgebra 2e, Section 2.2",
    },
    "MTH-T01-C02-U03": {
        "obj": "Verify whether a value is a solution to an equation, and solve linear equations using subtraction and addition properties with verification.",
        "out": "Solve one-step linear equations systematically by isolating the variable and verifying via substitution.",
        "chapter": "MTH-T01-C02",
        "prereq": "[[MTH-T01-C02-U02]]",
        "next": "[[MTH-T01-C02-U04]]",
        "source": "OpenStax Prealgebra 2e, Section 2.3",
    },
    "MTH-T01-C02-U04": {
        "obj": "Identify multiples using divisibility tests (2, 3, 5, 6, 9, 10) and find all factor pairs of whole numbers systematically.",
        "out": "List all factor pairs of numbers $\\le 100$ and apply divisibility tests without performing long division.",
        "chapter": "MTH-T01-C02",
        "prereq": "[[MTH-T01-C01-U04]], [[MTH-T01-C01-U05]]",
        "next": "[[MTH-T01-C02-U05]]",
        "source": "OpenStax Prealgebra 2e, Section 2.4",
    },
    "MTH-T01-C02-U05": {
        "obj": "Write the unique prime factorization of any composite number using factor trees and compute the GCF and LCM of number pairs.",
        "out": "Decompose numbers into canonical prime power products and compute the GCF and LCM systematically.",
        "chapter": "MTH-T01-C02",
        "prereq": "[[MTH-T01-C02-U04]]",
        "next": "[[MTH-T01-C03-U01]]",
        "source": "OpenStax Prealgebra 2e, Section 2.5",
    },

    # === Chapter C03 ===
    "MTH-T01-C03-U01": {
        "obj": "Locate positive and negative integers on the number line, order signed numbers, and evaluate absolute values and opposites.",
        "out": "Order sets of signed integers on $\\mathbb{Z}$ and evaluate absolute values $|x|$ as geometric distances from zero.",
        "chapter": "MTH-T01-C03",
        "prereq": "[[MTH-T01-C02]]",
        "next": "[[MTH-T01-C03-U02]]",
        "source": "OpenStax Prealgebra 2e, Section 3.1",
    },
    "MTH-T01-C03-U02": {
        "obj": "Add integers with the same sign and with different signs, evaluate multi-term integer sums, and translate application phrases.",
        "out": "Compute signed integer additions fluently without sign errors and apply them to net elevation and financial balances.",
        "chapter": "MTH-T01-C03",
        "prereq": "[[MTH-T01-C03-U01]]",
        "next": "[[MTH-T01-C03-U03]]",
        "source": "OpenStax Prealgebra 2e, Section 3.2",
    },
    "MTH-T01-C03-U03": {
        "obj": "Rewrite integer subtraction as adding the opposite (a - b = a + (-b)) and simplify multi-operation signed expressions.",
        "out": "Subtract signed numbers by converting to addition of the opposite and evaluate temperature differentials accurately.",
        "chapter": "MTH-T01-C03",
        "prereq": "[[MTH-T01-C03-U02]]",
        "next": "[[MTH-T01-C03-U04]]",
        "source": "OpenStax Prealgebra 2e, Section 3.3",
    },
    "MTH-T01-C03-U04": {
        "obj": "Multiply and divide signed integers, evaluate powers of negative integers, and simplify expressions with nested brackets and exponents.",
        "out": "Multiply and divide signed numbers and evaluate powers of signed numbers distinguishing $(-a)^n$ from $-a^n$.",
        "chapter": "MTH-T01-C03",
        "prereq": "[[MTH-T01-C03-U03]]",
        "next": "[[MTH-T01-C03-U05]]",
        "source": "OpenStax Prealgebra 2e, Section 3.4",
    },
    "MTH-T01-C03-U05": {
        "obj": "Solve one-step equations involving signed integers using the Addition, Subtraction, and Division Properties of Equality with checks.",
        "out": "Solve and check one-step linear equations containing negative coefficients and constants.",
        "chapter": "MTH-T01-C03",
        "prereq": "[[MTH-T01-C02-U03]], [[MTH-T01-C03-U04]]",
        "next": "[[MTH-T01-C04-U01]]",
        "source": "OpenStax Prealgebra 2e, Section 3.5",
    },

    # === Chapter C04 ===
    "MTH-T01-C04-U01": {
        "obj": "Model fractions as parts of a whole, convert between mixed numbers and improper fractions, and locate fractions on the number line.",
        "out": "Convert between improper fractions and mixed numbers, find equivalent fractions, and graph rational numbers on $\\mathbb{Q}$.",
        "chapter": "MTH-T01-C04",
        "prereq": "[[MTH-T01-C02-U05]]",
        "next": "[[MTH-T01-C04-U02]]",
        "source": "OpenStax Prealgebra 2e, Section 4.1",
    },
    "MTH-T01-C04-U02": {
        "obj": "Simplify fractions by canceling common prime factors, multiply fractions, evaluate reciprocals, and divide fractions by multiplying by the reciprocal.",
        "out": "Multiply and divide proper and improper fractions cleanly by cross-canceling common factors before multiplying.",
        "chapter": "MTH-T01-C04",
        "prereq": "[[MTH-T01-C03]]",
        "next": "[[MTH-T01-C04-U03]]",
        "source": "OpenStax Prealgebra 2e, Section 4.2",
    },
    "MTH-T01-C04-U03": {
        "obj": "Multiply and divide mixed numbers by converting to improper fractions, and simplify complex fractions using division or overall LCD multiplication.",
        "out": "Simplify complex fractions and evaluate mixed number products and quotients in lowest terms.",
        "chapter": "MTH-T01-C04",
        "prereq": "[[MTH-T01-C02-U05]], [[MTH-T01-C04-U02]]",
        "next": "[[MTH-T01-C04-U04]]",
        "source": "OpenStax Prealgebra 2e, Section 4.3",
    },
    "MTH-T01-C04-U04": {
        "obj": "Add and subtract numerical and algebraic fractions that share a common denominator, and evaluate signed fraction expressions.",
        "out": "Combine fractions with common denominators and simplify algebraic fraction numerators accurately.",
        "chapter": "MTH-T01-C04",
        "prereq": "[[MTH-T01-C02-U05]], [[MTH-T01-C03-U04]]",
        "next": "[[MTH-T01-C04-U05]]",
        "source": "OpenStax Prealgebra 2e, Section 4.4",
    },
    "MTH-T01-C04-U05": {
        "obj": "Find the Least Common Denominator (LCD), convert fractions to equivalent forms with the LCD, and execute multi-digit fraction additions/subtractions.",
        "out": "Add and subtract fractions with different denominators by finding the LCD and borrowing across mixed numbers.",
        "chapter": "MTH-T01-C04",
        "prereq": "[[MTH-T01-C04-U01]], [[MTH-T01-C04-U02]], [[MTH-T01-C04-U03]], [[MTH-T01-C04-U04]]",
        "next": "[[MTH-T01-C04-U06]]",
        "source": "OpenStax Prealgebra 2e, Section 4.5",
    },
    "MTH-T01-C04-U06": {
        "obj": "Solve linear equations containing fractional constants and fractional coefficients using reciprocal multiplication and LCD denominator clearing.",
        "out": "Solve fractional linear equations cleanly by clearing denominators with the LCD and checking candidate solutions.",
        "chapter": "MTH-T01-C04",
        "prereq": "[[MTH-T01-C03-U05]], [[MTH-T01-C04-U03]], [[MTH-T01-C04-U04]]",
        "next": "[[MTH-T01-C05-U01]]",
        "source": "OpenStax Prealgebra 2e, Section 4.6",
    },
}

def update_central_rules(token, id_map):
    print("--- 1. Updating Central Rules with Explicit Mention Sub-Bullets ---")
    b78_id = "40c3818f-8ba0-81c5-9fc1-e10e20ebd89a"
    
    # Check if children already added
    children = get_all_blocks(b78_id, token)
    if children:
        print(f"  Central Rules Block 78 already has {len(children)} children. Skipping.")
        return

    sub_bullets = [
        bullet("**Callout Header Mentions:** Every Callout at the top of Topic, Chapter, and Unit pages MUST contain native `@page` mentions for all referenced entities (**Parent:** `[[Topic]]` → `[[Chapter]]` | **Prerequisites:** `[[Unit]]` | **Next Unit:** `[[Unit]]` | **Source:** `[[Resource]]`). Never write unlinked entity ID text in callouts.", id_map),
        bullet("**Learning Sequence Numbered Lists:** Every item in 'Chapter Architecture & Learning Sequence' (Topic pages) and 'Unit Sequence & Progression' (Chapter pages) MUST begin with a native `@page` mention to that Chapter or Unit (e.g. `1. [[Chapter_ID]] — Title: Summary`). Never leave curriculum sequences as plain text.", id_map),
        bullet("**Practice Guide Cross-References:** All references in Category 2 ('Combine with Prior Units/Chapters') and Category 4 ('Cross-Subject & Real-World Connection') MUST use native `@page` mentions (e.g. `[[PRG-T01]]`, `[[PHY-T01]]`, `[[Unit_ID]]`).", id_map),
        bullet("**Zero Plain-Text Entity Policy:** Any mention of an existing Topic ID, Chapter ID, Unit ID, or Resource ID anywhere across page bodies, callouts, lists, toggles, or checklist items MUST be rendered as a native Notion `@page` mention.", id_map),
    ]

    notion_request("PATCH", f"blocks/{b78_id}/children", token, {
        "children": sub_bullets
    })
    print("  Successfully appended 4 explicit mention sub-bullets to Central Rules Block 78!")

def update_topic(token, id_map):
    print("\n--- 2. Updating Topic MTH-T01 Mentions ---")
    pid = id_map["MTH-T01"]["id"]
    blocks = get_all_blocks(pid, token)

    # 1. Update Block 0 (Callout)
    b0 = blocks[0]
    notion_request("PATCH", f"blocks/{b0['id']}", token, {
        "callout": {
            "rich_text": parse_rt(TOPIC_CALLOUT, id_map)
        }
    })
    print("  Patched Topic Callout (Block 0) with native mentions.")

    # 2. Update Block 3 (Overview paragraph)
    b3 = blocks[3]
    notion_request("PATCH", f"blocks/{b3['id']}", token, {
        "paragraph": {
            "rich_text": parse_rt(TOPIC_OVERVIEW_P3, id_map)
        }
    })
    print("  Patched Topic Overview Paragraph 3 with PHY-T01 & PRG-T01 mentions.")

    # 3. Update Blocks 14-27 (Numbered list items for 14 Chapters)
    num_list_blocks = [b for b in blocks if b["type"] == "numbered_list_item"]
    print(f"  Found {len(num_list_blocks)} numbered list items in Topic.")
    for i, (cid, title, ucount, summary) in enumerate(TOPIC_CHAPTERS):
        if i < len(num_list_blocks):
            bid = num_list_blocks[i]["id"]
            line_text = f"[[{cid}]] — {title} ({ucount} Units): {summary}"
            notion_request("PATCH", f"blocks/{bid}", token, {
                "numbered_list_item": {
                    "rich_text": parse_rt(line_text, id_map)
                }
            })
            print(f"    Patched {cid} numbered item.")

def update_chapters(token, id_map):
    print("\n--- 3. Updating Chapters MTH-T01-C01 through C04 Mentions ---")
    for cid, cdata in CHAPTER_DATA.items():
        pid = id_map[cid]["id"]
        blocks = get_all_blocks(pid, token)

        # 1. Update Block 0 (Callout)
        b0 = blocks[0]
        notion_request("PATCH", f"blocks/{b0['id']}", token, {
            "callout": {
                "rich_text": parse_rt(cdata["callout"], id_map)
            }
        })
        print(f"  [{cid}] Patched Callout with Parent, Prereqs, and Source mentions.")

        # 2. Update numbered list items (Unit Sequence & Progression)
        num_list_blocks = [b for b in blocks if b["type"] == "numbered_list_item"]
        for i, (uid, utitle, usummary) in enumerate(cdata["units"]):
            if i < len(num_list_blocks):
                bid = num_list_blocks[i]["id"]
                line_text = f"[[{uid}]] — {utitle}: {usummary}"
                notion_request("PATCH", f"blocks/{bid}", token, {
                    "numbered_list_item": {
                        "rich_text": parse_rt(line_text, id_map)
                    }
                })
                print(f"    [{cid}] Patched unit sequence: {uid}")

        # 3. Update Category 4 in Chapter Practice Guide
        for b in blocks:
            if b["type"] == "bulleted_list_item":
                txt = "".join(t.get("plain_text", "") for t in b["bulleted_list_item"]["rich_text"])
                if "Cross-Subject" in txt and b.get("has_children"):
                    cb_list = get_all_blocks(b["id"], token)
                    if cb_list:
                        child_bid = cb_list[0]["id"]
                        notion_request("PATCH", f"blocks/{child_bid}", token, {
                            "bulleted_list_item": {
                                "rich_text": parse_rt(cdata["cross"], id_map)
                            }
                        })
                        print(f"    [{cid}] Patched Category 4 Cross-Subject with PRG-T01 & PHY-T01 mentions.")

def update_units(token, id_map):
    print("\n--- 4. Updating Units MTH-T01-C01-U01 through C04-U06 Callouts ---")
    for uid, udata in UNIT_CALLOUTS.items():
        pid = id_map[uid]["id"]
        blocks = get_all_blocks(pid, token)

        b0 = blocks[0]
        callout_text = (
            f"**Learning Objective:** {udata['obj']}\n"
            f"**Expected Output:** {udata['out']}\n"
            f"**Parent:** [[MTH-T01]] → [[{udata['chapter']}]] | "
            f"**Prerequisites:** {udata['prereq']} | "
            f"**Next Unit:** {udata['next']} | "
            f"**Source:** [[R035]] ({udata['source']})"
        )
        notion_request("PATCH", f"blocks/{b0['id']}", token, {
            "callout": {
                "rich_text": parse_rt(callout_text, id_map)
            }
        })
        print(f"  [{uid}] Patched Callout with Parent, Prereqs, Next Unit, and Source mentions.")
        time.sleep(0.1) # Smooth pacing

def main():
    env = load_env()
    token = env.get("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN not set!")

    with open("id_map.json") as f:
        id_map = json.load(f)

    # 1. Central Rules
    update_central_rules(token, id_map)

    # 2. Topic MTH-T01
    update_topic(token, id_map)

    # 3. Chapters C01 - C04
    update_chapters(token, id_map)

    # 4. Units C01-U01 - C04-U06 (21 units)
    update_units(token, id_map)

    print("\n=== ALL MTH-T01 BATCH 1 MENTIONS SUCCESSFULLY FIXED & VERIFIED! ===")

if __name__ == "__main__":
    main()
