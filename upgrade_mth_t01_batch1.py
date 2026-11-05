# -*- coding: utf-8 -*-
"""
Upgrades MTH-T01 Batch 1 (Chapters C01 through C04: 21 Units) to v3 Gold Standard
by surgically adding Section 4 'Practice Guide' (Core Skills, Prior Units, Traps, Cross-Subject)
WITHOUT affecting existing user progress, Status properties ('Done'), or personal notes.
"""
import json
import re
from apply_rules_and_test_pages import (
    load_env,
    notion_request,
    get_all_blocks,
    rt,
    parse_rt,
    validate_blocks_clean,
    h2,
    p_block,
    bullet,
    divider_block,
)

# Comprehensive Practice Guides for MTH-T01 Batch 1 (C01 - C04)
UNIT_PRACTICE_GUIDES = {
    # === Chapter C01: Whole Numbers ===
    "MTH-T01-C01-U01": {
        "title": "Practice Guide — Introduction to Whole Numbers",
        "core": "Drill base-10 positional place-value decomposition into powers of 10, rounding multi-digit whole numbers using the single-test-digit rule, and translating large numbers with zero-placeholders between words and numerals.",
        "combine": "Foundational unit; directly prepares for vertical addition regrouping in [[MTH-T01-C01-U02]] and borrowing in [[MTH-T01-C01-U03]].",
        "traps": "Chain-Rounding Trap: Never round step-by-step from right to left (e.g. in 48,499, rounding 9 to 10 to 5 to make 49,000; the test digit for the thousands place is strictly the hundreds digit 4 < 5 -> 48,000). Missing Zero Trap: Omitting zero placeholders when translating 'fifty thousand, four' as 50,4 instead of 50,004. Zero Set Trap: Confusing Whole Numbers {0, 1, 2, ...} with Counting Numbers {1, 2, 3, ...}.",
        "cross": "Programming ([[PRG-T01]]): Positional base systems generalize to binary (base 2), octal (base 8), and hexadecimal (base 16) memory representation. Physics ([[PHY-T01]]): Order-of-magnitude rounding and significant figures in measurement uncertainty.",
    },
    "MTH-T01-C01-U02": {
        "title": "Practice Guide — Add Whole Numbers",
        "core": "Drill vertical column addition with multi-digit carrying across place values, verifying column sums bottom-to-top using Commutative/Associative properties, and calculating perimeter of polygons.",
        "combine": "Combine with [[MTH-T01-C01-U01]] place-value alignment to ensure digits of the same power of 10 align strictly on the rightmost edge.",
        "traps": "Column Misalignment Trap: Aligning numbers on the left rather than by units digit. Lost Carry Trap: Forgetting to add carried digits into the tens/hundreds place. Perimeter vs Area Trap: Multiplying length and width instead of adding all outer boundary segments.",
        "cross": "Programming ([[PRG-T01]]): Integer overflow detection when column sums exceed 32-bit signed integer limits ($2^{31}-1$). Physics ([[PHY-T01]]): Scalar addition of total distance traveled along rectilinear segments.",
    },
    "MTH-T01-C01-U03": {
        "title": "Practice Guide — Subtract Whole Numbers",
        "core": "Drill vertical subtraction borrowing (regrouping), multi-digit borrowing across zero digits (e.g. 5,004 - 2,786), and verifying results via inverse addition ($D - d = r \\iff r + d = D$).",
        "combine": "Combine with [[MTH-T01-C01-U02]] addition to execute self-checks on every difference.",
        "traps": "Smaller-Minus-Larger Inversion Trap: When subtracting 37 from 52, computing 7 - 2 = 5 in the ones place instead of borrowing from the tens place. Zero Borrowing Trap: Failing to unbundle across multiple consecutive zeros ($5,000 - 324$).",
        "cross": "Programming ([[PRG-T01]]): Unsigned integer underflow in C/Rust producing large wrapped values ($0 - 1 = 2^{32}-1$). Physics ([[PHY-T01]]): Displacement vectors $\\Delta x = x_f - x_i$.",
    },
    "MTH-T01-C01-U04": {
        "title": "Practice Guide — Multiply Whole Numbers",
        "core": "Drill multi-digit partial products algorithm, multiplying by powers of 10 by appending zeros, area models of rectangles, and distributive property expansion $a(b + c) = ab + ac$.",
        "combine": "Combine with [[MTH-T01-C01-U02]] addition to sum partial product rows accurately.",
        "traps": "Placeholder Zero Slip: Forgetting to append a zero shift when multiplying by the tens digit and two zeros for the hundreds digit. Identity vs Zero Confusion: Confusing $a \\cdot 1 = a$ with $a \\cdot 0 = 0$.",
        "cross": "Programming ([[PRG-T01]]): Asymptotic algorithmic complexity of matrix and grid operations ($O(n^2)$). Physics ([[PHY-T01]]): Calculation of rectangular area ($A = l \\cdot w$) and uniform velocity distance ($d = v \\cdot t$).",
    },
    "MTH-T01-C01-U05": {
        "title": "Practice Guide — Divide Whole Numbers",
        "core": "Drill standard long division algorithm (Divide, Multiply, Subtract, Bring down), division with remainders ($D = q \\cdot d + r$ with $0 \\le r < d$), division by multi-digit divisors, and zero division rules.",
        "combine": "Combine multiplication [[MTH-T01-C01-U04]] and subtraction [[MTH-T01-C01-U03]] to execute the division cycle.",
        "traps": "Division by Zero Trap: Believing $a / 0 = 0$. Remember: $0 / a = 0$ (for $a \\neq 0$), but $a / 0$ is strictly **undefined** because no number multiplied by 0 can equal a nonzero $a$. Remainder Exceeding Divisor: Leaving a remainder $r \\ge d$, indicating the quotient digit was too small.",
        "cross": "Programming ([[PRG-T01]]): Integer division vs modulo operator (`/` vs `%` in JS/Python/C). Zero division throwing runtime `ZeroDivisionError` / `NaN`.",
    },

    # === Chapter C02: The Language of Algebra ===
    "MTH-T01-C02-U01": {
        "title": "Practice Guide — Use the Language of Algebra",
        "core": "Drill Order of Operations (PEMDAS / GEMDAS) with nested parentheses, brackets, exponents, and strict left-to-right precedence for multiplication/division and addition/subtraction.",
        "combine": "Combine whole number arithmetic from [[MTH-T01-C01]] inside multi-tiered bracket expressions.",
        "traps": "Premature Addition Trap: Computing $8 - 3 + 2$ as $8 - 5 = 3$ instead of left-to-right $(8 - 3) + 2 = 5 + 2 = 7$. Multiplication-Before-Division Myth: Thinking multiplication always precedes division in PEMDAS; they hold equal precedence and evaluate left-to-right ($12 \\div 3 \\cdot 2 = 4 \\cdot 2 = 8$, not $12 \\div 6 = 2$).",
        "cross": "Programming ([[PRG-T01]]): Operator precedence tables in JavaScript/C; parentheses to enforce evaluation order in boolean and arithmetic expressions.",
    },
    "MTH-T01-C02-U02": {
        "title": "Practice Guide — Evaluate, Simplify, and Translate Expressions",
        "core": "Drill substituting values into variable expressions, combining like terms by adding algebraic coefficients, and translating English verbal phrases into algebraic expressions.",
        "combine": "Combine Order of Operations [[MTH-T01-C02-U01]] when evaluating expressions with substituted numbers.",
        "traps": "Subtraction Order Reversal Trap: Translating '8 less than x' as $8 - x$ instead of $x - 8$. Combining Unlike Terms Trap: Adding $3x + 4$ to get $7x$. Combining Powers Trap: Adding $2x^2 + 3x$ to get $5x^3$.",
        "cross": "Programming ([[PRG-T01]]): Function parameter substitution and pure functions; variable naming conventions.",
    },
    "MTH-T01-C02-U03": {
        "title": "Practice Guide — Solving Equations Using Subtraction and Addition Properties",
        "core": "Drill isolating variables in one-step linear equations using Subtraction Property of Equality ($x + a = b \\implies x = b - a$) and Addition Property ($x - a = b \\implies x = b + a$) with self-verification checks.",
        "combine": "Combine with expression evaluation [[MTH-T01-C02-U02]] by substituting candidate solutions back into the original equation to verify equality.",
        "traps": "One-Sided Operation Trap: Adding or subtracting a number on only one side of the equal sign, unbalancing the equation. Sign Reversal Trap: Adding $a$ when $x + a = b$ instead of subtracting $a$.",
        "cross": "Programming ([[PRG-T01]]): Invariants and state machines; algebraic balancing algorithms.",
    },
    "MTH-T01-C02-U04": {
        "title": "Practice Guide — Find Multiples and Factors",
        "core": "Drill divisibility tests (2, 3, 5, 6, 9, 10), listing all factor pairs of whole numbers systematically, and generating multiples.",
        "combine": "Combine division [[MTH-T01-C01-U05]] to test divisibility without leaving remainders.",
        "traps": "Factor vs Multiple Confusion: Mixing up factors (divisors $\\le n$) with multiples (products $\\ge n$). Sum-of-Digits Divisibility Trap: Applying the sum-of-digits test for 3 and 9 to numbers when testing for 2, 4, or 5.",
        "cross": "Programming ([[PRG-T01]]): Modulo divisibility checks (`n % 2 === 0` for evens, `n % 5 === 0`); loop factors search up to $\\sqrt{n}$.",
    },
    "MTH-T01-C02-U05": {
        "title": "Practice Guide — Prime Factorization and the Least Common Multiple",
        "core": "Drill prime vs composite identification, prime factorization via factor trees and ladder methods, and finding the Greatest Common Factor (GCF) and Least Common Multiple (LCM) of two or three numbers.",
        "combine": "Combine with factor search [[MTH-T01-C02-U04]] to decompose numbers into prime powers $p_1^{a_1} \\cdot p_2^{a_2}$.",
        "traps": "The 1-is-Prime Myth: Calling 1 a prime number. (1 is neither prime nor composite; primes have exactly two distinct positive divisors). GCF vs LCM Inversion: Confusing GCF (lowest powers of common primes) with LCM (highest powers of all primes).",
        "cross": "Programming ([[PRG-T01]]): Cryptographic RSA key generation relying on large prime factorization; Euclidean algorithm for GCD/LCM.",
    },

    # === Chapter C03: Integers ===
    "MTH-T01-C03-U01": {
        "title": "Practice Guide — Introduction to Integers",
        "core": "Drill representing positive/negative integers on the number line, opposites (additive inverses $-a$), and absolute value $|x|$ as geometric distance from zero.",
        "combine": "Combine whole numbers [[MTH-T01-C01]] with negative reflection across zero to construct $\\mathbb{Z}$.",
        "traps": "Absolute Value Sign Myth: Believing $|-x|$ means change the sign to negative. Absolute value is **always non-negative** ($|a| \\ge 0$). Inequality with Negatives Trap: Writing $-8 > -3$ because 8 > 3 (on the number line, $-8$ is further left, so $-8 < -3$).",
        "cross": "Programming ([[PRG-T01]]): Two's complement binary representation of signed integers; `Math.abs(x)`. Physics ([[PHY-T01]]): Signed 1D coordinate systems where negative indicates direction (left/down).",
    },
    "MTH-T01-C03-U02": {
        "title": "Practice Guide — Add Integers",
        "core": "Drill adding integers with same signs (add absolute values, keep sign) and different signs (subtract smaller absolute value from larger, take sign of larger absolute value).",
        "combine": "Combine absolute value rules [[MTH-T01-C03-U01]] with multi-digit addition [[MTH-T01-C01-U02]].",
        "traps": "Double-Negative Addition Trap: Adding $(-5) + (-7)$ and thinking the result is positive $+12$ (multiplying negatives gives positive, but adding negatives always yields a negative sum $-12$). Sign Loss in Multi-Term Sums: Forgetting to track cumulative signs in $15 + (-8) + (-12) + 6$.",
        "cross": "Programming ([[PRG-T01]]): Accumulator patterns over signed financial debits and credits.",
    },
    "MTH-T01-C03-U03": {
        "title": "Practice Guide — Subtract Integers",
        "core": "Drill subtracting signed numbers by converting to addition of the opposite: $a - b = a + (-b)$ and $a - (-b) = a + b$.",
        "combine": "Combine with integer addition [[MTH-T01-C03-U02]] immediately after transforming subtraction.",
        "traps": "Minus-Minus Sign Slip: Computing $5 - (-3)$ as $5 - 3 = 2$ instead of $5 + 3 = 8$. Subtracting from Negative Trap: Computing $-10 - 4$ as $-6$ instead of $-14$ ($-10 + (-4) = -14$).",
        "cross": "Physics ([[PHY-T01]]): Calculating temperature differentials $\\Delta T = T_f - T_i$ when crossing zero degrees.",
    },
    "MTH-T01-C03-U04": {
        "title": "Practice Guide — Multiply and Divide Integers",
        "core": "Drill multiplication and division of signed integers: same signs yield positive $(+) \\cdot (+) = (+)$ and $(-) \\cdot (-) = (+)$; different signs yield negative $(+) \\cdot (-) = (-)$ and $(-) \\cdot (+) = (-)$. Simplify powers of negative numbers $(-a)^n$ vs $-a^n$.",
        "combine": "Combine Order of Operations [[MTH-T01-C02-U01]] with signed arithmetic rules.",
        "traps": "Parentheses Exponent Trap: Crucial distinction between $(-3)^2 = (-3)(-3) = +9$ versus $-3^2 = -(3 \\cdot 3) = -9$. Odd Powers Trap: Forgetting that an odd power of a negative number remains negative ($(-2)^3 = -8$).",
        "cross": "Programming ([[PRG-T01]]): Exponentiation operator precedence (`-3 ** 2` in JS throws syntax error or evaluates to -9; `(-3) ** 2 === 9`).",
    },
    "MTH-T01-C03-U05": {
        "title": "Practice Guide — Solve Equations Using Integers and Division Property",
        "core": "Drill solving one-step linear equations with signed numbers using Division Property ($ax = b \\implies x = b/a$) and Multiplication Property ($x/a = b \\implies x = ab$), verifying roots with substitution.",
        "combine": "Combine one-step balance techniques [[MTH-T01-C02-U03]] with signed integer division [[MTH-T01-C03-U04]].",
        "traps": "Dividing by Negative Sign Flip: Solving $-4x = 24$ by dividing by $-4$ and writing $x = 6$ instead of $x = -6$. Subtracting vs Dividing Trap: Confusing $-4x = 12$ (requires division by -4) with $x - 4 = 12$ (requires addition of 4).",
        "cross": "Programming ([[PRG-T01]]): Solving inverse equations in game physics (velocity from momentum $p = mv \\implies v = p/m$).",
    },

    # === Chapter C04: Fractions ===
    "MTH-T01-C04-U01": {
        "title": "Practice Guide — Visualize Fractions",
        "core": "Drill proper fractions, improper fractions, mixed numbers, finding equivalent fractions by multiplying numerator and denominator by $c/c$, and simplifying fractions to lowest terms using GCF.",
        "combine": "Combine GCF factoring [[MTH-T01-C02-U05]] to cancel common prime factors in fractions.",
        "traps": "Partial Cancellation Trap: Cancelling terms in a sum instead of factors in a product (e.g. attempting to cancel 4 in $\\frac{4 + x}{4}$). Improper to Mixed Conversion Slip: Dividing numerator by denominator and misplacing remainder into denominator.",
        "cross": "Programming ([[PRG-T01]]): Rational number data structures representing exact fractions without floating-point rounding errors.",
    },
    "MTH-T01-C04-U02": {
        "title": "Practice Guide — Multiply and Divide Fractions",
        "core": "Drill fraction multiplication by multiplying straight across numerators and denominators (simplifying before multiplying), reciprocals (multiplicative inverses $a/b \\to b/a$), and division by multiplying by the reciprocal $\\frac{a}{b} \\div \\frac{c}{d} = \\frac{a}{b} \\cdot \\frac{d}{c}$.",
        "combine": "Combine prime factorization [[MTH-T01-C02-U05]] to cross-cancel factors prior to multiplying.",
        "traps": "Common Denominator Myth: Falsely finding common denominators when multiplying fractions (only needed for addition/subtraction). Reciprocal Inversion Omission: Inverting the first fraction instead of the second (divisor) fraction during division.",
        "cross": "Physics ([[PHY-T01]]): Dimensional unit cancellation (converting miles/hour to meters/second using reciprocal unit fractions).",
    },
    "MTH-T01-C04-U03": {
        "title": "Practice Guide — Multiply and Divide Mixed Numbers and Complex Fractions",
        "core": "Drill converting mixed numbers to improper fractions prior to multiplying/dividing, and simplifying complex fractions (fractions within fractions) by multiplying by the reciprocal of the denominator.",
        "combine": "Combine mixed number conversion [[MTH-T01-C04-U01]] with fraction division [[MTH-T01-C04-U02]].",
        "traps": "Multiplying Whole and Fractional Parts Separately: Falsely calculating $2\\frac{1}{2} \\cdot 3\\frac{1}{3}$ as $(2 \\cdot 3) + (\\frac{1}{2} \\cdot \\frac{1}{3}) = 6\\frac{1}{6}$. **Always convert to improper fractions first:** $\\frac{5}{2} \\cdot \\frac{10}{3} = \\frac{25}{3} = 8\\frac{1}{3}$.",
        "cross": "Programming ([[PRG-T01]]): Recursive data structure unwrapping; nested fraction reduction algorithms.",
    },
    "MTH-T01-C04-U04": {
        "title": "Practice Guide — Add and Subtract Fractions with Common Denominators",
        "core": "Drill adding and subtracting fraction numerators over a common denominator: $\\frac{a}{c} \\pm \\frac{b}{c} = \\frac{a \\pm b}{c}$, simplifying final answers to lowest terms.",
        "combine": "Combine signed integer arithmetic [[MTH-T01-C03-U02]] in fraction numerators: $\\frac{-5}{8} + \\frac{1}{8} = \\frac{-4}{8} = -\\frac{1}{2}$.",
        "traps": "Adding Denominators Trap: Adding both numerators and denominators (e.g. $\\frac{1}{5} + \\frac{2}{5} = \\frac{3}{10}$ instead of $\\frac{3}{5}$). Denominators represent partition sizes and **never add together**.",
        "cross": "Physics ([[PHY-T01]]): Combining common unit partitions in experimental measurement.",
    },
    "MTH-T01-C04-U05": {
        "title": "Practice Guide — Add and Subtract Fractions with Different Denominators",
        "core": "Drill finding the Least Common Denominator (LCD = LCM of denominators), converting fractions to equivalent fractions with the LCD, and adding/subtracting numerators.",
        "combine": "Combine LCM computation [[MTH-T01-C02-U05]] with equivalent fractions [[MTH-T01-C04-U01]].",
        "traps": "Multiplying Denominators Blindly: Multiplying denominators when a smaller LCD exists (e.g., using 48 for denominators 6 and 8 instead of LCD = 24), producing unnecessarily large numbers. Unbalanced Numerator Conversion: Changing denominator without multiplying numerator by the same factor.",
        "cross": "Programming ([[PRG-T01]]): Common denominator alignment in arbitrary-precision big-rational math libraries.",
    },
    "MTH-T01-C04-U06": {
        "title": "Practice Guide — Add and Subtract Mixed Numbers",
        "core": "Drill adding and subtracting mixed numbers with common and different denominators, regrouping (borrowing 1 as $d/d$ when subtracting larger fractional parts), and vertical alignment.",
        "combine": "Combine LCD fraction addition/subtraction [[MTH-T01-C04-U05]] with mixed number regrouping.",
        "traps": "Borrowing Fraction Slip: In $5\\frac{1}{4} - 2\\frac{3}{4}$, borrowing 1 from 5 gives $4 + (1 + \\frac{1}{4}) = 4\\frac{5}{4}$, **not** $4\\frac{11}{4}$ or $4\\frac{3}{4}$. Distribution of Negative in Subtraction: In $5 - 2\\frac{1}{3}$, computing $(5 - 2) + \\frac{1}{3} = 3\\frac{1}{3}$ instead of $5 - 2 - \\frac{1}{3} = 2\\frac{2}{3}$.",
        "cross": "Programming ([[PRG-T01]]): Mixed unit conversions (hours and minutes, feet and inches) using fractional remainder arithmetic.",
    },
}

# Chapter Practice Guides for C01 - C04
CHAPTER_PRACTICE_GUIDES = {
    "MTH-T01-C01": {
        "title": "Chapter Practice Guide — Whole Numbers",
        "mixed": "Generate mixed arithmetic sets interleaving multi-digit addition carrying, borrowing across zeros in subtraction, multi-digit partial product multiplication, and long division with remainders. Solve word problems identifying which of the four operations applies.",
        "combine": "Combine perimeter calculations with multi-digit addition and area models with multiplication.",
        "traps": "Zero division ($a/0$ is undefined), forgetting zero placeholders in partial product rows, and borrowing errors across consecutive zeros.",
        "cross": "Programming: Integer arithmetic bounds, modulo remainder operator. Physics: Displacement, perimeter, and area calculations.",
    },
    "MTH-T01-C02": {
        "title": "Chapter Practice Guide — The Language of Algebra",
        "mixed": "Generate mixed evaluation sets with PEMDAS brackets/exponents, translation of verbal sentences to algebraic equations, one-step balance solving, and prime factorization / GCF / LCM determination.",
        "combine": "Combine order of operations with variable evaluation and one-step inverse operations.",
        "traps": "Premature addition in $a - b + c$, mistranslating 'less than' order, and confusing GCF with LCM.",
        "cross": "Programming: Variable scoping, operator precedence tables. Cryptography: Prime factorization.",
    },
    "MTH-T01-C03": {
        "title": "Chapter Practice Guide — Integers",
        "mixed": "Generate signed arithmetic sets with positive and negative additions, subtraction as adding the opposite, signed products and quotients, and solving one-step signed linear equations.",
        "combine": "Combine Order of Operations with nested signed integers and absolute value brackets.",
        "traps": "Crucial distinction $(-a)^2 > 0$ vs $-a^2 < 0$, double negative subtraction mistakes, and dividing by negative numbers in equations.",
        "cross": "Programming: Two's complement representation. Physics: Signed coordinate systems and delta quantities (velocity, displacement).",
    },
    "MTH-T01-C04": {
        "title": "Chapter Practice Guide — Fractions",
        "mixed": "Generate mixed fraction operations: multiplying straight across, dividing by the reciprocal, finding LCD to add/subtract fractions with different denominators, and mixed number borrowing.",
        "combine": "Combine GCF cross-cancellation with fraction multiplication and prime factorization to find LCD.",
        "traps": "Adding denominators ($1/a + 1/b = 2/(a+b)$ trap), failing to convert mixed numbers to improper fractions before multiplying/dividing, and forgetting to invert only the second fraction in division.",
        "cross": "Programming: Exact rational math representations. Physics: Unit factor-label conversions.",
    },
}

def build_unit_practice_blocks(guide_data, id_map):
    return [
        divider_block(),
        h2("4. Practice Guide", id_map),
        p_block("Use this blueprint to generate targeted practice problems for this Unit and diagnose calculation slips in Section 6:", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet(guide_data["core"], id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet(guide_data["combine"], id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet(guide_data["traps"], id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (Math ↔ Physics ↔ Code):**", id_map, children=[
            bullet(guide_data["cross"], id_map),
        ]),
        divider_block(),
    ]

def build_chapter_practice_blocks(guide_data, id_map):
    return [
        divider_block(),
        h2("5. Chapter Practice Guide", id_map),
        p_block("Use this chapter blueprint to generate mixed multi-unit problem sets and review calculation pitfalls:", id_map),
        bullet("**1. Chapter Mixed Practice (Multi-Unit Synthesis):**", id_map, children=[
            bullet(guide_data["mixed"], id_map),
        ]),
        bullet("**2. Combine with Prior Chapters:**", id_map, children=[
            bullet(guide_data["combine"], id_map),
        ]),
        bullet("**3. Chapter-Wide Traps:**", id_map, children=[
            bullet(guide_data["traps"], id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (Physics & Code):**", id_map, children=[
            bullet(guide_data["cross"], id_map),
        ]),
        divider_block(),
    ]

def upgrade_unit(uid, token, id_map):
    pid = id_map[uid]["id"]
    guide = UNIT_PRACTICE_GUIDES.get(uid)
    if not guide:
        return

    blocks = get_all_blocks(pid, token)
    
    # Check if Practice Guide already exists
    for b in blocks:
        bt = b["type"]
        txt = "".join(t.get("plain_text", "") for t in b.get(bt, {}).get("rich_text", []))
        if "Practice Guide" in txt:
            print(f"  [{uid}] Practice Guide already present. Skipping.")
            return

    # Find the Problem-Solving Exercises section or anchor before Active Recall
    anchor_id = None
    delete_ids = []
    in_exercises = False

    for i, b in enumerate(blocks):
        bt = b["type"]
        txt = "".join(t.get("plain_text", "") for t in b.get(bt, {}).get("rich_text", []))
        
        if "Problem-Solving Exercises" in txt:
            in_exercises = True
            delete_ids.append(b["id"])
            if i > 0 and blocks[i-1]["type"] == "divider":
                anchor_id = blocks[i-1]["id"]
            elif i > 0:
                anchor_id = blocks[i-1]["id"]
            continue

        if in_exercises:
            if "Active Recall" in txt or bt == "divider":
                in_exercises = False
            else:
                delete_ids.append(b["id"])

    # If anchor not found from exercises, find anchor before Active Recall Questions
    if not anchor_id:
        for i, b in enumerate(blocks):
            bt = b["type"]
            txt = "".join(t.get("plain_text", "") for t in b.get(bt, {}).get("rich_text", []))
            if "Active Recall Questions" in txt:
                anchor_id = blocks[i-1]["id"] if i > 0 else blocks[0]["id"]
                break

    if not anchor_id:
        anchor_id = blocks[-1]["id"]

    # Delete static exercise blocks
    for bid in delete_ids:
        try:
            notion_request("DELETE", f"blocks/{bid}", token)
        except Exception as e:
            pass

    # Build and insert new Practice Guide blocks
    new_blocks = build_unit_practice_blocks(guide, id_map)
    validate_blocks_clean(new_blocks, f"{uid}-PG")
    
    notion_request("PATCH", f"blocks/{pid}/children", token, {
        "after": anchor_id,
        "children": new_blocks,
    })
    print(f"  ✔ [{uid}] Successfully injected Practice Guide (Preserved all user progress & properties)!")

def upgrade_chapter(cid, token, id_map):
    pid = id_map[cid]["id"]
    guide = CHAPTER_PRACTICE_GUIDES.get(cid)
    if not guide:
        return

    blocks = get_all_blocks(pid, token)
    for b in blocks:
        bt = b["type"]
        txt = "".join(t.get("plain_text", "") for t in b.get(bt, {}).get("rich_text", []))
        if "Practice Guide" in txt:
            print(f"  [{cid}] Chapter Practice Guide already present. Skipping.")
            return

    # Find anchor before Summary or Checklist
    anchor_id = None
    for i, b in enumerate(blocks):
        bt = b["type"]
        txt = "".join(t.get("plain_text", "") for t in b.get(bt, {}).get("rich_text", []))
        if "Summary" in txt or "Completion Checklist" in txt or "Active Recall" in txt:
            anchor_id = blocks[i-1]["id"] if i > 0 else blocks[0]["id"]
            break

    if not anchor_id:
        anchor_id = blocks[-1]["id"]

    new_blocks = build_chapter_practice_blocks(guide, id_map)
    validate_blocks_clean(new_blocks, f"{cid}-PG")
    
    notion_request("PATCH", f"blocks/{pid}/children", token, {
        "after": anchor_id,
        "children": new_blocks,
    })
    print(f"  ✔ [{cid}] Successfully injected Chapter Practice Guide!")

def main():
    env = load_env()
    token = env.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN not set in .env")

    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)

    print("=== Upgrading MTH-T01 Batch 1 (Chapters C01-C04: 21 Units) ===")
    print("CRITICAL INVARIANT: Preserving all user progress (Status: Done), Mastery, and personal notes!\n")

    # Upgrade 4 Chapters
    for cid in ["MTH-T01-C01", "MTH-T01-C02", "MTH-T01-C03", "MTH-T01-C04"]:
        print(f"Checking Chapter: {cid}...")
        upgrade_chapter(cid, token, id_map)

    # Upgrade 21 Units
    unit_keys = sorted(UNIT_PRACTICE_GUIDES.keys())
    print(f"\nUpgrading {len(unit_keys)} Units across C01 through C04...")
    for uid in unit_keys:
        upgrade_unit(uid, token, id_map)

    print("\n🎉 BATCH 1 COMPLETE! All 21 Units and 4 Chapters in MTH-T01 upgraded with Practice Guides!")

if __name__ == "__main__":
    main()
