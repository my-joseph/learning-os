# -*- coding: utf-8 -*-
"""
Unit-level curriculum and practice guide data for MTH-T01 Batch 3 (26 Units).
Covers:
- C10 (5 Units: U01 to U05)
- C11 (4 Units: U01 to U04)
- C12 (7 Units: U01 to U07)
- C13 (6 Units: U01 to U06)
- C14 (4 Units: U01 to U04)
Each unit features rigorous mathematical formulations, worked examples, 4-category Practice Guides,
and Active Recall questions with full step-by-step Reference Solutions.
"""

UNIT_DATA = {
    # =========================================================================
    # CHAPTER C10: THE PROPERTIES OF REAL NUMBERS (5 Units)
    # =========================================================================
    "MTH-T01-C10-U01": {
        "title": "Rational and Irrational Numbers",
        "chapter": "MTH-T01-C10",
        "objective": "Classify real numbers into subsets (natural, whole, integers, rational, irrational), and evaluate square roots of non-perfect squares as irrational numbers.",
        "expected_output": "Rigorous classification of arbitrary real numbers and identification of non-terminating, non-repeating decimals.",
        "concepts": [
            "**Real Number System Hierarchy:** Natural ($\\mathbb{N} = \\{1, 2, \\dots\\}$), Whole ($\\mathbb{W} = \\{0, 1, 2, \\dots\\}$), Integers ($\\mathbb{Z} = \\{\\dots, -1, 0, 1, \\dots\\}$), Rational ($\\mathbb{Q} = \\{\\frac{a}{b} \\mid a, b \\in \\mathbb{Z}, b \\neq 0\\}$), and Irrational ($\\mathbb{I} = \\mathbb{R} \\setminus \\mathbb{Q}$).",
            "**Decimal Expansion Invariant:** A number is rational if and only if its decimal terminates or repeats infinitely. A number is irrational if its decimal is non-terminating and non-repeating (e.g., $\\pi, \\sqrt{2}, e$).",
            "**Square Roots of Non-Perfect Squares:** If positive integer $n$ is not a perfect square, $\\sqrt{n}$ is strictly irrational."
        ],
        "formulas": [
            "\\mathbb{N} \\subset \\mathbb{W} \\subset \\mathbb{Z} \\subset \\mathbb{Q} \\subset \\mathbb{R}",
            "x \\in \\mathbb{Q} \\iff x = \\frac{a}{b} \\quad (a, b \\in \\mathbb{Z}, b \\neq 0)"
        ],
        "example": {
            "title": "Classifying Given Numbers Across All Applicable Sets",
            "steps": [
                "Classify $-5$: Not natural or whole. It is an Integer ($\\mathbb{Z}$), Rational ($-5 = -5/1 \\in \\mathbb{Q}$), and Real ($\\mathbb{R}$).",
                "Classify $\\sqrt{49}$: Since $\\sqrt{49} = 7$, it is Natural ($\\mathbb{N}$), Whole ($\\mathbb{W}$), Integer ($\\mathbb{Z}$), Rational ($\\mathbb{Q}$), and Real ($\\mathbb{R}$).",
                "Classify $\\sqrt{11}$: Since 11 is not a perfect square, its decimal expansion never terminates and never repeats. It is Irrational ($\\mathbb{I}$) and Real ($\\mathbb{R}$).",
                "Classify $0.\\overline{63}$: Repeating decimal $\\implies \\frac{63}{99} = \\frac{7}{11}$. It is Rational ($\\mathbb{Q}$) and Real ($\\mathbb{R}$)."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why zero is a whole number, an integer, and a rational number, but not a natural number.", "Prove that the sum of a rational number and an irrational number is always irrational."],
            "computational": ["Classify each value into all applicable subsets: $-\\sqrt{100}, \\frac{22}{7}, \\sqrt{50}, -3.14159, 0, \\sqrt{\\frac{4}{25}}$.", "Convert $0.\\overline{72}$ to a simplified fraction in $\\mathbb{Q}$ using algebraic subtraction."],
            "traps": ["Radical Misconception Trap: Assuming every radical is irrational (e.g. $\\sqrt{36} = 6 \\in \\mathbb{N}$). Must evaluate radicals first!", "Approximation Trap: Confusing $\\pi$ (irrational) with its rational approximations $\\frac{22}{7}$ or $3.14$."],
            "cross": ["Programming ([[PRG-T01]]): Primitive data types (`int`, `BigInt`, `float`) and representing arbitrary-precision rational fractions.", "Physics ([[PHY-T01]]): Continuous measurement domains in physical constants ($G, c, h$)."]
        },
        "active_recall": [
            {"q": "What two decimal behaviors uniquely characterize irrational numbers?", "a": "An irrational number's decimal expansion is both non-terminating (continues forever) and non-repeating (never enters a repeating cyclic pattern)."},
            {"q": "Is the number -12/4 an integer or only a rational number?", "a": "It is both. Simplified, $-\\frac{12}{4} = -3$, which is an Integer ($\\mathbb{Z}$) as well as a Rational number ($\\mathbb{Q}$) and Real number ($\\mathbb{R}$)."}
        ]
    },

    "MTH-T01-C10-U02": {
        "title": "Commutative and Associative Properties",
        "chapter": "MTH-T01-C10",
        "objective": "Apply the commutative and associative properties of addition and multiplication to simplify algebraic and numerical expressions.",
        "expected_output": "Fluent reordering and regrouping of terms and factors to compute mental arithmetic and algebraic simplifications efficiently.",
        "concepts": [
            "**Commutative Property (Order):** Changing the order of addends or factors does not change the result: $a + b = b + a$ and $ab = ba$. Note: Subtraction and division are NOT commutative ($a - b \\neq b - a$, $a/b \\neq b/a$).",
            "**Associative Property (Grouping):** Changing the grouping of addends or factors does not change the result: $(a + b) + c = a + (b + c)$ and $(ab)c = a(bc)$.",
            "**Combining Both Properties:** When simplifying multi-term expressions, reorder using commutative property, then group using associative property."
        ],
        "formulas": [
            "a + b = b + a, \\qquad ab = ba \\quad (\\text{Commutative})",
            "(a + b) + c = a + (b + c), \\qquad (ab)c = a(bc) \\quad (\\text{Associative})"
        ],
        "example": {
            "title": "Simplifying via Strategic Regrouping",
            "steps": [
                "Simplify: $(47 + 29) + 53$.",
                "Apply Commutative Property to swap inner terms: $(29 + 47) + 53$.",
                "Apply Associative Property to regroup compatible numbers: $29 + (47 + 53)$.",
                "Add compatible pair: $29 + 100 = 129$.",
                "Simplify: $\\left(\\frac{5}{12} \\cdot 19\\right) \\cdot \\frac{12}{5} = \\left(19 \\cdot \\frac{5}{12}\\right) \\cdot \\frac{12}{5} = 19 \\cdot \\left(\\frac{5}{12} \\cdot \\frac{12}{5}\\right) = 19 \\cdot 1 = 19$."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain the distinction between the Commutative Property (moving term positions) and the Associative Property (moving parentheses grouping).", "Provide concrete counterexamples proving that subtraction and division are neither commutative nor associative."],
            "computational": ["Evaluate using regrouping: $(0.25 \\times 37) \\times 4$.", "Simplify algebraically: $\\frac{3}{8} + (x + \\frac{5}{8})$."],
            "traps": ["Moving vs Regrouping Trap: Thinking that $a(bc) = (ab)c$ is commutative. The order $a, b, c$ did not change; only parentheses moved, so it is strictly associative!", "Subtraction Regrouping Trap: Writing $(10 - 5) - 2 = 10 - (5 - 2)$, which incorrectly yields $3 = 7$. Subtraction is non-associative."],
            "cross": ["Programming ([[PRG-T01]]): Function composition associativity $(f \\circ g) \\circ h = f \\circ (g \\circ h)$ and compiler optimization reordering rules.", "Physics ([[PHY-T01]]): Vector addition commutativity $\\vec{A} + \\vec{B} = \\vec{B} + \\vec{A}$."]
        },
        "active_recall": [
            {"q": "How can you tell whether an algebraic identity demonstrates the Commutative or Associative property?", "a": "If the left-to-right order of the terms/factors changes (e.g. $x + y = y + x$), it is Commutative. If the left-to-right order remains identical while only the parentheses shift (e.g. $(x+y)+z = x+(y+z)$), it is Associative."},
            {"q": "Why is (24 / 4) / 2 not equal to 24 / (4 / 2)?", "a": "$(24 / 4) / 2 = 6 / 2 = 3$, whereas $24 / (4 / 2) = 24 / 2 = 12$. Division is non-associative; operations must follow standard left-to-right order of operations unless explicitly grouped."}
        ]
    },

    "MTH-T01-C10-U03": {
        "title": "Distributive Property",
        "chapter": "MTH-T01-C10",
        "objective": "Apply the distributive property to expand algebraic products, factor common monomial terms, and simplify expressions with signed variables.",
        "expected_output": "Fluency in expanding expressions of the form $a(b + c) = ab + ac$ and handling negative distribution without sign errors.",
        "concepts": [
            "**Distributive Law of Multiplication over Addition:** Multiplying a sum by a factor is identical to multiplying each addend by that factor and summing the products: $a(b + c) = ab + ac$.",
            "**Geometric Area Model:** The total area of a rectangle of height $a$ and base $(b + c)$ is the sum of sub-rectangles $ab$ and $ac$.",
            "**Negative Sign Distribution:** Distributing a negative factor negates every term inside: $-(x - y) = -1(x - y) = -x + y$."
        ],
        "formulas": [
            "a(b + c) = ab + ac",
            "a(b - c) = ab - ac",
            "-(a + b) = -a - b, \\qquad -(a - b) = -a + b"
        ],
        "example": {
            "title": "Distributing and Combining Linear Like Terms",
            "steps": [
                "Expand and simplify: $3(2x - 5) - 4(x - 3)$.",
                "Distribute $+3$ to the first group: $3(2x) + 3(-5) = 6x - 15$.",
                "Distribute $-4$ to the second group (watch sign on $-4 \\cdot (-3)$): $-4(x) - 4(-3) = -4x + 12$.",
                "Combine expressions: $6x - 15 - 4x + 12$.",
                "Collect like terms: $(6x - 4x) + (-15 + 12) = 2x - 3$."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain how the Distributive Property justifies combining like terms: $3x + 5x = (3 + 5)x = 8x$.", "Draw a geometric area model illustrating $4(x + 3) = 4x + 12$."],
            "computational": ["Expand: $-5(3y - 7) + 2(4 - y)$.", "Simplify by factoring out common terms: $24x + 36y = 12(2x + 3y)$."],
            "traps": ["Single-Term Distribution Trap: In $3(x + 4)$, multiplying only $x$ to get $3x + 4$ instead of $3x + 12$.", "Sign Drop on Second Term: In $-(2x - 7)$, writing $-2x - 7$ instead of $-2x + 7$."],
            "cross": ["Programming ([[PRG-T01]]): Distributive refactoring in code logic `if (A && (B || C)) === if ((A && B) || (A && C))`. (De Morgan's Laws).", "Physics ([[PHY-T01]]): Net torque calculations $\\sum \\tau = r(F_1 + F_2) = rF_1 + rF_2$."]
        },
        "active_recall": [
            {"q": "What is the result of expanding -(4x - 9)?", "a": "$-4x + 9$. The leading negative acts as multiplying by $-1$: $(-1)(4x) + (-1)(-9) = -4x + 9$."},
            {"q": "How is combining like terms (e.g. 7a + 11a) mathematically justified by the distributive property?", "a": "By using the distributive property in reverse (factoring): $7a + 11a = (7 + 11)a = 18a$."}
        ]
    },

    "MTH-T01-C10-U04": {
        "title": "Properties of Identity, Inverses, and Zero",
        "chapter": "MTH-T01-C10",
        "objective": "Identify and apply the additive identity, multiplicative identity, additive inverse, multiplicative inverse (reciprocal), and zero properties of multiplication and division.",
        "expected_output": "Complete understanding of arithmetic identities and zero edge cases, including division by zero.",
        "concepts": [
            "**Additive Identity & Inverse:** $a + 0 = a$; $a + (-a) = 0$. (Opposites sum to zero).",
            "**Multiplicative Identity & Inverse:** $a \\cdot 1 = a$; $a \\cdot \\frac{1}{a} = 1$ ($a \\neq 0$). (Reciprocals multiply to 1).",
            "**Multiplication by Zero:** $a \\cdot 0 = 0$ for all real numbers $a$.",
            "**Division Involving Zero:** $\\frac{0}{a} = 0$ ($a \\neq 0$), but $\\frac{a}{0}$ is **strictly undefined**."
        ],
        "formulas": [
            "a + 0 = a, \\qquad a + (-a) = 0",
            "a \\cdot 1 = a, \\qquad a \\cdot \\frac{1}{a} = 1 \\quad (a \\neq 0)",
            "a \\cdot 0 = 0, \\qquad \\frac{0}{a} = 0 \\quad (a \\neq 0), \\qquad \\frac{a}{0} = \\text{Undefined}"
        ],
        "example": {
            "title": "Evaluating Expressions Using Identity and Inverse Properties",
            "steps": [
                "Find the additive inverse and multiplicative inverse of $-\\frac{4}{7}$.",
                "Additive inverse (opposite): $-(-4/7) = +\\frac{4}{7}$, because $-\\frac{4}{7} + \\frac{4}{7} = 0$.",
                "Multiplicative inverse (reciprocal): $-\\frac{7}{4}$, because $\\left(-\\frac{4}{7}\\right)\\left(-\\frac{7}{4}\\right) = +1$.",
                "Evaluate $\\frac{14 - 2 \\times 7}{5 - 5} = \\frac{14 - 14}{0} = \\frac{0}{0} \\implies$ Undefined."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why 0 has an additive inverse but no multiplicative inverse.", "Differentiate between 0 divided by a number vs a number divided by 0."],
            "computational": ["State the additive inverse and reciprocal of: (a) $-8$, (b) $\\frac{2}{5}$, (c) $1$, (d) $-1$.", "Simplify using inverse properties: $\\frac{3}{5}\\left(\\frac{5}{3}x\\right) + [7 + (-7)]$."],
            "traps": ["Reciprocal Sign Change Trap: Changing the sign when finding the reciprocal of a negative number (e.g. thinking the reciprocal of $-3$ is $+1/3$). Reciprocals preserve sign: reciprocal of $-3$ is $-1/3$!", "Zero Division Trap: Writing $\\frac{5}{0} = 0$ or $\\frac{5}{0} = 5$. Division by zero is completely undefined."],
            "cross": ["Programming ([[PRG-T01]]): `ZeroDivisionError` handling and IEEE 754 representations of `NaN` and `Infinity`.", "Physics ([[PHY-T01]]): Conservation laws where net forces balance to the additive identity $\\sum \\vec{F} = 0$."]
        },
        "active_recall": [
            {"q": "What is the additive inverse of x, and what is its multiplicative inverse (reciprocal)?", "a": "The additive inverse of $x$ is $-x$ (sums to $0$). The multiplicative inverse of $x$ (for $x \\neq 0$) is $\\frac{1}{x}$ (multiplies to $1$)."},
            {"q": "Why is 0/8 equal to 0, but 8/0 is undefined?", "a": "$\\frac{0}{8} = 0$ because $0 \\times 8 = 0$ (a unique valid answer). But $\\frac{8}{0} = c$ would require $c \\times 0 = 8$, which is impossible for any real number $c$."}
        ]
    },

    "MTH-T01-C10-U05": {
        "title": "Systems of Measurement",
        "chapter": "MTH-T01-C10",
        "objective": "Convert units within and between the US Customary and Metric systems using multi-step unit fractions (dimensional analysis).",
        "expected_output": "Mastery of dimensional analysis unit fractions, canceling intermediate units to compute derived conversion factors.",
        "concepts": [
            "**Unit Fraction Invariant:** A fraction where numerator and denominator represent equal quantities in different units has value $1$ (e.g. $\\frac{1\\text{ ft}}{12\\text{ in}} = 1$). Multiplying by a unit fraction preserves magnitude while transforming dimensions.",
            "**Metric Prefixes (Powers of 10):** Kilo ($10^3$), Hecto ($10^2$), Deka ($10^1$), Base ($10^0$), Deci ($10^{-1}$), Centi ($10^{-2}$), Milli ($10^{-3}$).",
            "**Cancellation Rule:** The unit to eliminate must be in the opposite position (numerator vs denominator) of the conversion factor."
        ],
        "formulas": [
            "\\text{Value in Unit B} = \\text{Value in Unit A} \\times \\left(\\frac{\\text{Unit B}}{\\text{Unit A}}\\right)",
            "1\\text{ in} = 2.54\\text{ cm}, \\quad 1\\text{ kg} \\approx 2.205\\text{ lb}, \\quad 1\\text{ mi} = 5280\\text{ ft} = 1.609\\text{ km}"
        ],
        "example": {
            "title": "Multi-Step Rate Conversion: Miles per Hour to Meters per Second",
            "steps": [
                "Convert $60\\text{ miles/hour}$ to meters per second ($1\\text{ mile} = 1609.34\\text{ m}, 1\\text{ hr} = 3600\\text{ s}$).",
                "Set up chained unit fractions:",
                "\\frac{60\\text{ mi}}{1\\text{ hr}} \\times \\frac{1609.34\\text{ m}}{1\\text{ mi}} \\times \\frac{1\\text{ hr}}{3600\\text{ s}}",
                "Cancel units (miles and hours cancel):",
                "= \\frac{60 \\times 1609.34}{3600} \\text{ m/s} = \\frac{96560.4}{3600} \\approx 26.82\\text{ m/s}."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why multiplying a measurement by $\\frac{100\\text{ cm}}{1\\text{ m}}$ does not change the physical length.", "Explain how to convert square units (e.g. $\\text{m}^2$ to $\\text{cm}^2$) by squaring the conversion factor."],
            "computational": ["Convert 3.5 miles to inches using two conversion factors ($1\\text{ mi} = 5280\\text{ ft}, 1\\text{ ft} = 12\\text{ in}$).", "Convert $850\\text{ mL}$ to liters.", "Convert $90\\text{ km/h}$ to $\\text{m/s}$."],
            "traps": ["Inverted Factor Trap: Multiplying by $\\frac{12\\text{ in}}{1\\text{ ft}}$ instead of $\\frac{1\\text{ ft}}{12\\text{ in}}$ when converting inches to feet (resulting in $\\text{in}^2/\\text{ft}$).", "Area/Volume Dimension Trap: Converting $2\\text{ m}^2$ to $\\text{cm}^2$ by multiplying by $100$ instead of $100^2 = 10,000$."],
            "cross": ["Physics ([[PHY-T01]]): Core skill for physical kinematics ($[L][T]^{-1}$) and SI unit conversions.", "Programming ([[PRG-T01]]): Unit conversion microservices and avoiding Mars Climate Orbiter unit-mismatch bugs."]
        },
        "active_recall": [
            {"q": "Why must you square the conversion factor when converting square feet to square inches?", "a": "Area has dimension $[L]^2$. $1\\text{ ft} = 12\\text{ in} \\implies 1\\text{ ft}^2 = (12\\text{ in})^2 = 144\\text{ in}^2$. Both the unit and its numerical scale factor must be squared."},
            {"q": "What is the systematic check to ensure you set up a unit fraction correctly?", "a": "Verify that the unwanted unit appears in the numerator of one factor and the denominator of the other, allowing algebraic cancellation and leaving only the target unit."}
        ]
    },

    # =========================================================================
    # CHAPTER C11: SOLVING LINEAR EQUATIONS (4 Units)
    # =========================================================================
    "MTH-T01-C11-U01": {
        "title": "Solve Equations Using the Subtraction and Addition Properties of Equality",
        "chapter": "MTH-T01-C11",
        "objective": "Solve one-step linear equations using addition and subtraction properties of equality, translate verbal models to equations, and verify solutions.",
        "expected_output": "Fluency in isolating variables with additive inverses and formal verification via substitution.",
        "concepts": [
            "**Addition Property of Equality:** If $a = b$, then $a + c = b + c$. Adding the same number to both sides maintains balance.",
            "**Subtraction Property of Equality:** If $a = b$, then $a - c = b - c$. Subtracting the same number from both sides maintains balance.",
            "**Inverse Operation Strategy:** To eliminate an added constant $+c$, subtract $c$ (or add $-c$). To eliminate a subtracted constant $-c$, add $c$."
        ],
        "formulas": [
            "x + c = d \\iff x + c - c = d - c \\iff x = d - c",
            "x - c = d \\iff x - c + c = d + c \\iff x = d + c"
        ],
        "example": {
            "title": "Solving and Formally Verifying an Additive Linear Equation",
            "steps": [
                "Solve: $y - 14 = -32$.",
                "Identify the operation on the variable: 14 is subtracted from $y$.",
                "Apply the Addition Property of Equality (add 14 to both sides):",
                "\\begin{aligned} y - 14 + 14 &= -32 + 14 \\\\ y &= -18 \\end{aligned}",
                "Check by substituting $y = -18$ into original equation:",
                "-18 - 14 = -32 \\implies -32 = -32 \\quad (\\text{True})."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain the balance scale analogy of algebraic equality.", "Explain why subtracting $c$ is algebraically identical to adding $(-c)$."],
            "computational": ["Solve: $x + 28 = -15$.", "Solve: $m - \\frac{3}{7} = \\frac{4}{7}$.", "Solve: $-18 = p - 45$."],
            "traps": ["Sign Direction Trap: In $x - 8 = 10$, subtracting 8 from both sides instead of adding 8.", "Unbalanced Transformation: Applying the operation to only one side of the equation."],
            "cross": ["Physics ([[PHY-T01]]): Displacement delta $\\Delta x = x_f - x_i \\implies x_f = x_i + \\Delta x$.", "Programming ([[PRG-T01]]): Variable assignment vs mathematical equivalence (`x = x + 1`)."]
        },
        "active_recall": [
            {"q": "What inverse operation isolates the variable in x + 19 = 5?", "a": "Subtract 19 from both sides (or add $-19$), yielding $x = 5 - 19 = -14$."},
            {"q": "Why must you check your solution in the original unsimplified equation?", "a": "Checking in a later step might mask algebraic mistakes made between the original equation and that step. Only the original equation tests the true truth condition."}
        ]
    },

    "MTH-T01-C11-U02": {
        "title": "Solve Equations Using the Division and Multiplication Properties of Equality",
        "chapter": "MTH-T01-C11",
        "objective": "Solve one-step linear equations using multiplication and division properties of equality, handling negative and fractional coefficients.",
        "expected_output": "Mastery of dividing by coefficients and multiplying by reciprocals to isolate variables.",
        "concepts": [
            "**Division Property of Equality:** If $a = b$ and $c \\neq 0$, then $\\frac{a}{c} = \\frac{b}{c}$.",
            "**Multiplication Property of Equality:** If $a = b$, then $ac = bc$.",
            "**Fractional Coefficient Shortcut (Reciprocal):** To solve $\\frac{a}{b}x = c$, multiply both sides by the reciprocal $\\frac{b}{a}$, since $\\frac{b}{a} \\cdot \\frac{a}{b} = 1$."
        ],
        "formulas": [
            "ax = b \\iff \\frac{ax}{a} = \\frac{b}{a} \\iff x = \\frac{b}{a} \\quad (a \\neq 0)",
            "\\frac{a}{b}x = c \\iff \\left(\\frac{b}{a}\\right)\\left(\\frac{a}{b}x\\right) = \\left(\\frac{b}{a}\\right)c \\iff x = \\frac{bc}{a}"
        ],
        "example": {
            "title": "Solving with a Negative Fractional Coefficient",
            "steps": [
                "Solve: $-\\frac{3}{5}k = 27$.",
                "Identify coefficient: $-\\frac{3}{5}$. Its multiplicative inverse is $-\\frac{5}{3}$.",
                "Multiply both sides by $-\\frac{5}{3}$:",
                "\\begin{aligned} \\left(-\\frac{5}{3}\\right)\\left(-\\frac{3}{5}k\\right) &= \\left(-\\frac{5}{3}\\right)(27) \\\\ (1)k &= -5 \\times 9 \\\\ k &= -45 \\end{aligned}",
                "Check: $-\\frac{3}{5}(-45) = -3(-9) = 27 = 27 \\quad (\\text{True})."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why dividing by $a$ is equivalent to multiplying by $\\frac{1}{a}$.", "Explain why multiplying both sides of an equation by zero is invalid."],
            "computational": ["Solve: $-7x = 91$.", "Solve: $\\frac{y}{-4} = -16$.", "Solve: $\\frac{4}{9}w = -28$."],
            "traps": ["Negative Drop Trap: In $-5x = 30$, dividing by $5$ instead of $-5$, leading to an incorrect sign $x = 6$ instead of $x = -6$.", "Reciprocal Inversion Error: When solving $\\frac{x}{6} = 3$, dividing by 6 instead of multiplying by 6."],
            "cross": ["Physics ([[PHY-T01]]): Newton's second law $F = ma \\implies m = \\frac{F}{a}$ or $a = \\frac{F}{m}$.", "Programming ([[PRG-T01]]): Scaling factors, normalizing vectors, and proportional resizing."]
        },
        "active_recall": [
            {"q": "What is the fastest way to isolate x in (2/3)x = 18?", "a": "Multiply both sides by the reciprocal $\\frac{3}{2}$: $x = 18 \\times \\frac{3}{2} = 9 \\times 3 = 27$."},
            {"q": "When solving -x = 14, what is the value of x and why?", "a": "$x = -14$. The term $-x$ represents $(-1)x$. Dividing or multiplying both sides by $-1$ gives $x = -14$."}
        ]
    },

    "MTH-T01-C11-U03": {
        "title": "Solve Equations with Variables and Constants on Both Sides",
        "chapter": "MTH-T01-C11",
        "objective": "Solve multi-step linear equations by simplifying expressions, collecting variable terms on one side and constants on the other, and classifying identities and contradictions.",
        "expected_output": "Fluency in executing the 4-phase equation solving pipeline and categorizing solution sets.",
        "concepts": [
            "**Variable Gathering Strategy:** Add or subtract variable terms so that all variable instances collect on one side of the equation.",
            "**Constant Gathering Strategy:** Add or subtract constants so that all numerical constants collect on the opposite side.",
            "**Classification of Solution Sets:**",
            "- **Conditional:** $x = k$ (Exactly one unique solution).",
            "- **Identity:** $0 = 0$ (True for all $x \\in \\mathbb{R}$, infinitely many solutions).",
            "- **Contradiction:** $0 = k$ ($k \\neq 0$, false statement, no solution $\\emptyset$)."
        ],
        "formulas": [
            "ax + b = cx + d \\iff (a - c)x = d - b \\iff x = \\frac{d - b}{a - c} \\quad (a \\neq c)"
        ],
        "example": {
            "title": "Solving a Multi-Step Linear Equation with Distribution",
            "steps": [
                "Solve: $5(2x - 3) + 4 = 7x - 20$.",
                "Step 1: Simplify left side using distributive property:",
                "10x - 15 + 4 = 7x - 20 \\implies 10x - 11 = 7x - 20",
                "Step 2: Collect variables on left side (subtract $7x$ from both sides):",
                "10x - 7x - 11 = -20 \\implies 3x - 11 = -20",
                "Step 3: Collect constants on right side (add $11$ to both sides):",
                "3x = -20 + 11 \\implies 3x = -9",
                "Step 4: Isolate variable (divide both sides by $3$):",
                "x = -3"
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain how you recognize that an equation has no solution during algebraic steps.", "Explain why an equation like $2(x + 1) = 2x + 2$ is called an Identity."],
            "computational": ["Solve: $7x - 8 = 3x + 16$.", "Solve: $4(3y - 1) = 2(6y + 5)$ and classify.", "Solve: $6(x - 2) - 4x = 2(x - 6)$ and classify."],
            "traps": ["Premature Division: Dividing by coefficient before collecting all constants, creating messy fractions.", "Lost Variable Confusion: When $3x = 3x + 4 \\implies 0 = 4$, writing $x = 0$ instead of recognizing No Solution."],
            "cross": ["Physics ([[PHY-T01]]): Meeting-point problems where two moving objects have equal positions $x_1(t) = x_2(t)$.", "Finance: Finding the break-even quantity where Total Cost = Total Revenue."]
        },
        "active_recall": [
            {"q": "What is the difference between an equation that has x = 0 as a solution and one that has No Solution?", "a": "$x = 0$ is a valid single numerical solution (the graph crosses at the origin). 'No Solution' means all variables cancelled to leave a false statement like $0 = 7$, meaning no real number satisfies the equation."},
            {"q": "What should be your first two steps when solving 3(x - 4) + 5 = 2x + 9?", "a": "1. Distribute 3 to simplify the left side: $3x - 12 + 5 = 3x - 7$. 2. Subtract $2x$ from both sides to gather variable terms on the left: $x - 7 = 9$."}
        ]
    },

    "MTH-T01-C11-U04": {
        "title": "Solve Equations with Fraction or Decimal Coefficients",
        "chapter": "MTH-T01-C11",
        "objective": "Solve linear equations containing fraction and decimal coefficients by clearing fractions using the LCD and clearing decimals using powers of 10.",
        "expected_output": "Proficiency in clearing denominators and decimal points to transform complex equations into integer linear equations.",
        "concepts": [
            "**Clearing Fractions (LCD Method):** Multiply every term on both sides of the equation by the Least Common Denominator (LCD) of all fractions. Denominators cancel completely, leaving an equivalent integer equation.",
            "**Clearing Decimals (Power of 10 Method):** If the maximum number of decimal places in any term is $k$, multiply every term on both sides by $10^k$.",
            "**Universal Distribution Rule:** When clearing fractions or decimals, every single term—including integer constants—must be multiplied by the clearing factor."
        ],
        "formulas": [
            "\\text{LCD}(d_1, d_2, \\dots) \\times (\\text{Entire Equation}) \\implies \\text{Integer Equation}",
            "10^{\\max(\\text{decimals})} \\times (\\text{Entire Equation}) \\implies \\text{Integer Equation}"
        ],
        "example": {
            "title": "Clearing Fractions Using LCD = 12",
            "steps": [
                "Solve: $\\frac{1}{2}x - \\frac{2}{3} = \\frac{5}{6} + \\frac{1}{4}x$.",
                "Find the LCD of denominators $2, 3, 6, 4$: $\\text{LCD} = 12$.",
                "Multiply every term by $12$:",
                "12\\left(\\frac{1}{2}x\\right) - 12\\left(\\frac{2}{3}\\right) = 12\\left(\\frac{5}{6}\\right) + 12\\left(\\frac{1}{4}x\\right)",
                "Simplify each product into integer coefficients:",
                "6x - 8 = 10 + 3x",
                "Collect variables on left (subtract $3x$): $3x - 8 = 10$.",
                "Collect constants on right (add $8$): $3x = 18$.",
                "Isolate $x$: $x = 6$."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why multiplying both sides of an equation by the LCD does not change its solution set.", "Describe how to determine what power of 10 is needed to clear decimals in $0.4x + 0.05 = 1.25$."],
            "computational": ["Solve by clearing fractions: $\\frac{3}{4}(x - 2) = \\frac{1}{3}x + 1$.", "Solve by clearing decimals: $0.25(x - 4) + 0.1x = 1.8$."],
            "traps": ["Neglecting Integer Terms: In $\\frac{1}{3}x + 5 = 2$, multiplying $\\frac{1}{3}x$ by 3 but forgetting to multiply 5 and 2 by 3.", "Parentheses Double-Multiplication: In $12 \\cdot \\frac{1}{4}(x - 8)$, multiplying both the outer factor and the inner terms by 12. Multiply only the outer coefficient!"],
            "cross": ["Finance: Loan amortization formulas and interest equation calculations.", "Physics ([[PHY-T01]]): Cleared kinematic equations with fractional constants like $\\frac{1}{2}at^2$."]
        },
        "active_recall": [
            {"q": "What is the LCD needed to clear fractions in (1/4)x + 2/5 = (3/10)x - 1?", "a": "The denominators are 4, 5, 10. $\\text{LCM}(4, 5, 10) = 20$. Multiplying every term by 20 clears all fractions."},
            {"q": "When clearing decimals in 0.05x + 0.4 = 1.2, what power of 10 should you multiply by?", "a": "Multiply by $10^2 = 100$ because the greatest number of decimal digits is 2 (in $0.05$). This yields $5x + 40 = 120$."}
        ]
    },

    # =========================================================================
    # CHAPTER C12: MATH MODELS AND GEOMETRY (7 Units: U01 to U07)
    # =========================================================================
    "MTH-T01-C12-U01": {
        "title": "Use a Problem Solving Strategy",
        "chapter": "MTH-T01-C12",
        "objective": "Apply Polya's 4-step problem solving framework (Understand, Translate, Solve, Check) to analyze and solve applied algebra word problems.",
        "expected_output": "Systematic transformation of narrative word problems into defined variables, algebraic equations, and contextual solutions.",
        "concepts": [
            "**Polya's Problem Solving Framework:**",
            "1. **Read & Understand:** Identify what is given and what must be found. Assign descriptive variables with explicit units.",
            "2. **Translate to Algebra:** Convert verbal relationship phrases ('more than', 'product of', 'decreased by') into mathematical equations.",
            "3. **Solve the Equation:** Apply algebraic equality properties to isolate the unknown.",
            "4. **Check & Interpret:** Confirm the numerical answer satisfies the original problem constraints and makes physical sense."
        ],
        "formulas": [
            "\\text{Total} = \\sum \\text{Parts}, \\qquad \\text{Consecutive Integers: } n, n+1, n+2, \\dots"
        ],
        "example": {
            "title": "Consecutive Odd Integers Sum Problem",
            "steps": [
                "Problem: The sum of three consecutive odd integers is 141. Find the integers.",
                "Let $n = \\text{first odd integer}$. Then the next two are $(n + 2)$ and $(n + 4)$.",
                "Translate to equation: $n + (n + 2) + (n + 4) = 141$.",
                "Combine like terms: $3n + 6 = 141$.",
                "Solve: $3n = 135 \\implies n = 45$.",
                "Interpret: The three integers are $45, 47, 49$. Check: $45 + 47 + 49 = 141$."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why consecutive odd integers are represented as $n, n+2, n+4$ rather than $n, n+1, n+3$.", "Explain why an answer like '$-4.5$ cars' indicates an error even if the algebra was solved without arithmetic slips."],
            "computational": ["The perimeter of a triangle is $48\\text{ cm}$. One side is twice the shortest side, and the third side is $4\\text{ cm}$ longer than the shortest. Find all three sides.", "Two angles are supplementary, and one is $18^\\circ$ less than three times the other. Find both."],
            "traps": ["Undefined Variable Trap: Writing equations without specifying what $x$ represents, causing confusion when interpreting the final answer.", "Partial Solution Trap: Finding $x = 15$ and stopping when the problem asked for the dimensions of all three items."],
            "cross": ["Programming ([[PRG-T01]]): Requirement analysis -> pseudocode -> unit testing (Polya's 4 steps mirrored in SDLC).", "Physics ([[PHY-T01]]): Word problem translation into free-body diagrams and kinematic equations."]
        },
        "active_recall": [
            {"q": "What are the algebraic expressions for three consecutive even integers starting with n?", "a": "$n$, $n + 2$, and $n + 4$ (where $n$ is an even integer)."},
            {"q": "What is the crucial final step of Polya's problem-solving strategy?", "a": "Check and Interpret: Substitute the solution back into the original real-world problem context to verify that units, values, and physical constraints make sense."}
        ]
    },

    "MTH-T01-C12-U02": {
        "title": "Solve Money Applications",
        "chapter": "MTH-T01-C12",
        "objective": "Model and solve coin, currency, ticket, and price-mix applications using number-times-value equations.",
        "expected_output": "Fluency in constructing tables separating item quantity from monetary unit value.",
        "concepts": [
            "**Total Value Principle:** $\\text{Total Value} = \\text{Number of Items} \\times \\text{Value per Item}$.",
            "**Two-Variable Single-Equation Method:** When two item counts sum to a total $T$, express them as $x$ and $(T - x)$.",
            "**Unit Consistency:** Work entirely in cents (integer equations) or entirely in dollars (decimal equations), never mixing both."
        ],
        "formulas": [
            "\\text{Total Value} = n_1 v_1 + n_2 v_2 + \\dots + n_k v_k"
        ],
        "example": {
            "title": "Solving a Dime and Quarter Cash Register Problem",
            "steps": [
                "Problem: A cashier has 35 coins in dimes and quarters totaling $5.75. How many of each coin are there?",
                "Let $d = \\text{number of dimes}$. Then $(35 - d) = \\text{number of quarters}$.",
                "Set up equation in cents (dimes = 10¢, quarters = 25¢, total = 575¢):",
                "10d + 25(35 - d) = 575",
                "Distribute: $10d + 875 - 25d = 575 \\implies -15d + 875 = 575$.",
                "Subtract 875: $-15d = -300 \\implies d = 20$.",
                "Quarters: $35 - 20 = 15$. Check: $20(0.10) + 15(0.25) = 2.00 + 3.75 = 5.75$."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why the equation $d + q = 5.75$ is dimensionally invalid for counting coins.", "Explain the advantage of clearing cents ($5.75 \\implies 575$) when solving coin problems."],
            "computational": ["A concert sold student tickets for $8 and adult tickets for $14. Total sales for 450 tickets were $4,860. How many of each were sold?", "A collector has twice as many nickels as dimes and 4 more quarters than dimes. The total value is $4.60. Find each coin count."],
            "traps": ["Confusing Number with Value: Setting $(d)(0.10) = 35$ instead of equating count and value separately.", "Sign Error in $(T - x)$: Expanding $25(35 - d)$ as $875 + 25d$ instead of $875 - 25d$."],
            "cross": ["Economics & Accounting: Inventory valuation via weighted average unit cost.", "Programming ([[PRG-T01]]): Preventing floating-point rounding errors in financial transactions by storing values as integer cents."]
        },
        "active_recall": [
            {"q": "If you have 50 total coins consisting of nickels and dimes, and n is the number of nickels, what expression represents the number of dimes?", "a": "$50 - n$."},
            {"q": "Why is it best to solve coin problems in cents rather than dollars?", "a": "Working in cents multiplies the equation by 100, eliminating all decimals and preventing floating-point/decimal calculation slips."}
        ]
    },

    "MTH-T01-C12-U03": {
        "title": "Use Properties of Angles, Triangles, and the Pythagorean Theorem",
        "chapter": "MTH-T01-C12",
        "objective": "Calculate complementary, supplementary, and triangle interior angles, and apply the Pythagorean Theorem ($a^2 + b^2 = c^2$) to find hypotenuse and leg lengths in right triangles.",
        "expected_output": "Rigorous geometric derivations of missing angles and exact/approximate right triangle side lengths.",
        "diagram_upload_id": "40f3818f-8ba0-81d7-b263-00b298c9a86f",
        "concepts": [
            "**Angle Invariants:** Complementary angles sum to $90^\\circ$ ($\\alpha + \\beta = 90^\\circ$); Supplementary angles sum to $180^\\circ$ ($\\alpha + \\beta = 180^\\circ$); Vertical angles are equal.",
            "**Triangle Angle Sum Theorem:** The interior angles of any triangle in the Euclidean plane sum to $180^\\circ$ ($A + B + C = 180^\\circ$).",
            "**The Pythagorean Theorem:** In any right-angled triangle with legs $a, b$ and hypotenuse $c$ (opposite the $90^\\circ$ angle): $a^2 + b^2 = c^2$."
        ],
        "formulas": [
            "\\alpha + \\beta = 90^\\circ \\quad (\\text{Complementary}), \\qquad \\alpha + \\beta = 180^\\circ \\quad (\\text{Supplementary})",
            "A + B + C = 180^\\circ \\quad (\\text{Triangle Sum})",
            "a^2 + b^2 = c^2 \\iff c = \\sqrt{a^2 + b^2}"
        ],
        "example": {
            "title": "Finding Missing Leg Using the Pythagorean Theorem",
            "steps": [
                "Problem: A right triangle has hypotenuse $c = 15\\text{ cm}$ and one leg $a = 9\\text{ cm}$. Find leg $b$.",
                "State the Pythagorean Theorem: $a^2 + b^2 = c^2$.",
                "Substitute known values:",
                "9^2 + b^2 = 15^2 \\implies 81 + b^2 = 225",
                "Isolate $b^2$ by subtracting 81 from both sides:",
                "b^2 = 225 - 81 = 144",
                "Take principal square root (lengths must be positive):",
                "b = \\sqrt{144} = 12\\text{ cm}."
            ]
        },
        "practice_guide": {
            "conceptual": ["Prove why a triangle can have at most one right angle or obtuse angle using the Triangle Angle Sum theorem.", "Explain why the hypotenuse is always strictly longer than either leg in a right triangle."],
            "computational": ["Find the hypotenuse of a right triangle with legs $a = 5$ and $b = 12$.", "A $20\\text{-foot}$ ladder leans against a building. The base is $12\\text{ feet}$ from the wall. How high up the building does the ladder reach?", "The angles of a triangle are $x, 2x+10,$ and $3x-40$. Find all three angles."],
            "traps": ["Hypotenuse Identification Trap: Mistaking a leg for the hypotenuse. The hypotenuse is ALWAYS opposite the right angle ($c$).", "Linear Square Trap: Claiming $a + b = c$ because $\\sqrt{a^2 + b^2} \\neq a + b$!"],
            "cross": ["Physics ([[PHY-T01]]): Vector magnitude calculation from orthogonal components $|\\vec{R}| = \\sqrt{R_x^2 + R_y^2}$.", "Programming ([[PRG-T01]]): Euclidean 2D distance formula between two game points $d = \\sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}$."]
        },
        "active_recall": [
            {"q": "What is the Pythagorean Theorem and which side is strictly represented by c?", "a": "$a^2 + b^2 = c^2$, where $a$ and $b$ are the perpendicular legs and $c$ is the hypotenuse (the longest side opposite the $90^\\circ$ angle)."},
            {"q": "If two angles are supplementary and one angle is 115 degrees, what is the other angle?", "a": "$180^\\circ - 115^\\circ = 65^\\circ$."}
        ]
    },

    "MTH-T01-C12-U04": {
        "title": "Use Properties of Rectangles, Triangles, and Trapezoids",
        "chapter": "MTH-T01-C12",
        "objective": "Calculate perimeter and area for rectangles, triangles, parallelograms, and trapezoids, and solve applied geometric algebraic equations.",
        "expected_output": "Fluency in deriving 2D perimeter and decomposed area formulas across quadrilaterals and triangles.",
        "diagram_upload_id": "40f3818f-8ba0-81bd-a00b-00b2246b6405",
        "concepts": [
            "**Rectangle Invariants:** Perimeter $P = 2L + 2W$; Area $A = L \\times W$.",
            "**Triangle Area:** $A = \\frac{1}{2}bh$, where height $h$ is strictly perpendicular to base $b$.",
            "**Trapezoid Area Decomposition:** A trapezoid has parallel bases $b_1, b_2$ and perpendicular height $h$. Dividing it into two triangles shows $A = \\frac{1}{2}h(b_1 + b_2)$."
        ],
        "formulas": [
            "P_{\\text{rect}} = 2L + 2W, \\qquad A_{\\text{rect}} = LW",
            "A_{\\text{tri}} = \\frac{1}{2}bh",
            "A_{\\text{trap}} = \\frac{1}{2}h(b_1 + b_2)"
        ],
        "example": {
            "title": "Calculating Trapezoid Area and Rectangle Dimensions",
            "steps": [
                "Find the area of a trapezoid with bases $b_1 = 14\\text{ cm}, b_2 = 22\\text{ cm}$, and perpendicular height $h = 8\\text{ cm}$.",
                "Apply trapezoid formula: $A = \\frac{1}{2}h(b_1 + b_2)$.",
                "A = \\frac{1}{2}(8)(14 + 22) = 4(36) = 144\\text{ cm}^2.",
                "Algebraic Application: A rectangle has length $3\\text{ cm}$ greater than twice its width ($L = 2W + 3$). Its perimeter is $54\\text{ cm}$. Find $L$ and $W$:",
                "2(2W + 3) + 2W = 54 \\implies 4W + 6 + 2W = 54 \\implies 6W = 48 \\implies W = 8\\text{ cm}, L = 19\\text{ cm}."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why the height in the triangle area formula $\\frac{1}{2}bh$ must be perpendicular to the base, not the slanted side.", "Demonstrate how rotating a trapezoid $180^\\circ$ creates a parallelogram of base $(b_1 + b_2)$ and height $h$."],
            "computational": ["Find the area of a right triangle with legs $12\\text{ m}$ and $9\\text{ m}$.", "Find the height of a trapezoid with area $120\\text{ ft}^2$ and bases $10\\text{ ft}$ and $14\\text{ ft}$."],
            "traps": ["Slant Height Trap: Using the slanted side length instead of the perpendicular height $h$ when calculating triangle or trapezoid area.", "Unit Multiplication Error: Forgetting that area is measured in square units ($\\text{cm}^2$) while perimeter is linear ($\\text{cm}$)."],
            "cross": ["Physics ([[PHY-T01]]): Work done as area under a Force-displacement curve ($W = \\int F dx$, trapezoid area approximation).", "Computer Graphics ([[PRG-T01]]): Bounding box collision detection and polygon triangulation."]
        },
        "active_recall": [
            {"q": "What is the formula for the area of a trapezoid and what do b1 and b2 represent?", "a": "$A = \\frac{1}{2}h(b_1 + b_2)$, where $h$ is the perpendicular height and $b_1, b_2$ are the lengths of the two parallel bases."},
            {"q": "Why does the triangle area formula have the factor 1/2?", "a": "Because any triangle represents exactly half of a parallelogram with the identical base and perpendicular height."}
        ]
    },

    "MTH-T01-C12-U05": {
        "title": "Solve Geometry Applications: Circles and Irregular Figures",
        "chapter": "MTH-T01-C12",
        "objective": "Calculate radius, diameter, circumference, and area of circles, and decompose composite/irregular 2D figures into standard geometric components.",
        "expected_output": "Proficiency in exact ($\\pi$) and approximate circle calculations and decomposing compound areas.",
        "diagram_upload_id": "40f3818f-8ba0-8104-a498-00b2a8a92fad",
        "concepts": [
            "**Circle Geometry:** Radius $r$ is the distance from center to boundary; diameter $d = 2r$.",
            "**Circumference & Area:** Circumference $C = 2\\pi r = \\pi d$; Area $A = \\pi r^2$.",
            "**Exact vs Approximate Answers:** Exact answers keep the $\\pi$ symbol (e.g. $25\\pi\\text{ cm}^2$); approximate answers substitute $\\pi \\approx 3.14159$ or $\\frac{22}{7}$.",
            "**Composite Figure Decomposition:** Irregular polygons and shapes are solved by partitioning into non-overlapping standard shapes (rectangles, triangles, semicircles) and summing or subtracting areas."
        ],
        "formulas": [
            "d = 2r, \\qquad C = 2\\pi r = \\pi d",
            "A = \\pi r^2"
        ],
        "example": {
            "title": "Calculating Circular Perimeter & Area and Composite Decomposition",
            "steps": [
                "Find exact and approximate circumference and area of a circle with radius $r = 7\\text{ cm}$.",
                "Exact Circumference: $C = 2\\pi(7) = 14\\pi\\text{ cm}$. Approximate ($22/7$): $14(22/7) = 44\\text{ cm}$.",
                "Exact Area: $A = \\pi(7^2) = 49\\pi\\text{ cm}^2$. Approximate ($22/7$): $49(22/7) = 154\\text{ cm}^2$.",
                "Composite Shape: A basketball key consists of a $12\\times 19\\text{ ft}$ rectangle attached to a semicircle of diameter $12\\text{ ft}$ ($r = 6$).",
                "Total Area = $A_{\\text{rect}} + A_{\\text{semi}} = (12 \\times 19) + \\frac{1}{2}\\pi(6^2) = 228 + 18\\pi \\approx 228 + 56.55 = 284.55\\text{ ft}^2$."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain the geometric definition of $\\pi$ as the ratio of circumference to diameter $\\frac{C}{d}$.", "Explain why the area of a circle has unit $r^2$ while circumference has unit $r$."],
            "computational": ["Find the area of a circle with diameter $d = 16\\text{ ft}$ in terms of $\\pi$.", "A garden is a rectangle $20\\text{ m} \\times 15\\text{ m}$ with a circular fountain of radius $3\\text{ m}$ inside. Find the remaining lawn area."],
            "traps": ["Diameter in Area Formula Trap: Using diameter instead of radius in $\\pi r^2$ (e.g. for $d = 10$, writing $\\pi(10^2)$ instead of $\\pi(5^2)$).", "Order of Operations Trap: Computing $\\pi r^2$ as $(\\pi r)^2$. Only $r$ is squared!"],
            "cross": ["Physics ([[PHY-T01]]): Uniform circular motion paths ($2\\pi r$), and cross-sectional wire areas ($A = \\pi r^2$) in electrical resistance.", "Programming ([[PRG-T01]]): Circle-circle collision detection and raycasting bounding spheres."]
        },
        "active_recall": [
            {"q": "What is the relationship between the radius and diameter of a circle?", "a": "$d = 2r$ (diameter is twice the radius) or $r = \\frac{d}{2}$."},
            {"q": "What is the exact area of a circle with radius 9 cm, and what is its exact circumference?", "a": "Area $= \\pi(9^2) = 81\\pi\\text{ cm}^2$. Circumference $= 2\\pi(9) = 18\\pi\\text{ cm}$."}
        ]
    },

    "MTH-T01-C12-U06": {
        "title": "Solve Geometry Applications: Volume and Surface Area",
        "chapter": "MTH-T01-C12",
        "objective": "Calculate volume and surface area for rectangular solids, cylinders, cones, and spheres, distinguishing between volumetric capacity and exterior boundary surface.",
        "expected_output": "Fluency in 3D spatial calculations and multi-step geometric modeling.",
        "diagram_upload_id": "40f3818f-8ba0-8111-be1e-00b292329eda",
        "concepts": [
            "**Volume vs Surface Area:** Volume ($V$) measures 3D space enclosed (cubic units, $\\text{cm}^3$); Surface Area ($SA$) measures total exterior boundary area (square units, $\\text{cm}^2$).",
            "**Right Cylinder Invariants:** $V = \\pi r^2 h$ (base area $\\times$ height); $SA = 2\\pi r^2 + 2\\pi rh$ (two circular bases $+$ unrolled rectangular lateral label).",
            "**Sphere Geometry:** $V = \\frac{4}{3}\\pi r^3$; $SA = 4\\pi r^2$."
        ],
        "formulas": [
            "V_{\\text{rect}} = LWH, \\qquad SA_{\\text{rect}} = 2LW + 2LH + 2WH",
            "V_{\\text{cyl}} = \\pi r^2 h, \\qquad SA_{\\text{cyl}} = 2\\pi r^2 + 2\\pi rh",
            "V_{\\text{sphere}} = \\frac{4}{3}\\pi r^3, \\qquad SA_{\\text{sphere}} = 4\\pi r^2"
        ],
        "example": {
            "title": "Calculating Volume and Surface Area of a Cylinder",
            "steps": [
                "A soup can has radius $r = 4\\text{ cm}$ and height $h = 10\\text{ cm}$. Find exact $V$ and $SA$.",
                "Volume: $V = \\pi r^2 h = \\pi (4^2)(10) = 160\\pi\\text{ cm}^3 \\approx 502.65\\text{ cm}^3$.",
                "Surface Area: Two bases $= 2\\pi r^2 = 2\\pi(16) = 32\\pi$.",
                "Lateral surface: $2\\pi rh = 2\\pi(4)(10) = 80\\pi$.",
                "Total Surface Area: $SA = 32\\pi + 80\\pi = 112\\pi\\text{ cm}^2 \\approx 351.86\\text{ cm}^2$."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why the lateral area of a cylinder unrolls into a rectangle of dimensions $2\\pi r$ by $h$.", "Explain why doubling all linear dimensions of a 3D solid multiplies its volume by 8 ($2^3$)."],
            "computational": ["Find the volume and surface area of a rectangular prism with dimensions $8\\text{ m} \\times 5\\text{ m} \\times 3\\text{ m}$.", "Find the volume of a spherical ball of radius $r = 6\\text{ in}$ in terms of $\\pi$."],
            "traps": ["Unit Dimension Trap: Reporting volume in $\\text{cm}^2$ or surface area in $\\text{cm}^3$.", "Lateral Area Omission: Forgetting to include the top and bottom circular bases ($2\\pi r^2$) when asked for total surface area."],
            "cross": ["Physics ([[PHY-T01]]): Density $\\rho = \\frac{m}{V}$ and hydrostatic pressure calculations.", "Engineering: Material cost estimation for tanks and container packaging efficiency."]
        },
        "active_recall": [
            {"q": "What are the two components of the surface area formula for a cylinder?", "a": "1. Two circular bases: $2\\pi r^2$. 2. The lateral curved surface: $2\\pi rh$ (circumference times height). Total: $2\\pi r^2 + 2\\pi rh$."},
            {"q": "If all sides of a cube are tripled, by what factor does its volume increase?", "a": "By a factor of $3^3 = 27$."}
        ]
    },

    "MTH-T01-C12-U07": {
        "title": "Solve a Formula for a Specific Variable",
        "chapter": "MTH-T01-C12",
        "objective": "Transform and isolate specified variables in geometric, scientific, and algebraic formulas using literal equation inverse operations.",
        "expected_output": "Mastery of literal equation transformation to express target variables in terms of other parameters.",
        "concepts": [
            "**Literal Equations:** Equations containing multiple variables representing constants and parameters. The rules of algebra apply identically to letters as they do to numbers.",
            "**Target Variable Isolation:** Treat all non-target variables as constants. Use inverse operations (subtraction/addition, division/multiplication) to isolate the target variable.",
            "**Geometric Reversal:** Rearranging formulas allows direct computation of dimensions (e.g. finding height from area: $A = \\frac{1}{2}bh \\implies h = \\frac{2A}{b}$)."
        ],
        "formulas": [
            "d = rt \\iff r = \\frac{d}{t} \\iff t = \\frac{d}{r}",
            "P = 2L + 2W \\iff W = \\frac{P - 2L}{2}",
            "C = \\frac{5}{9}(F - 32) \\iff F = \\frac{9}{5}C + 32"
        ],
        "example": {
            "title": "Isolating Radius r in the Cylinder Volume Formula",
            "steps": [
                "Solve $V = \\pi r^2 h$ for $r$ (assuming $r > 0$).",
                "Divide both sides by $\\pi h$ to isolate $r^2$:",
                "\\frac{V}{\\pi h} = r^2",
                "Take the principal square root of both sides:",
                "r = \\sqrt{\\frac{V}{\\pi h}}."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain how solving $3x + 12 = 24$ is identical in structure to solving $ax + b = c$ for $x$.", "Explain why $W = \\frac{P - 2L}{2}$ cannot be simplified to $W = P - L$."],
            "computational": ["Solve $A = \\frac{1}{2}h(b_1 + b_2)$ for $h$.", "Solve $A = \\frac{1}{2}h(b_1 + b_2)$ for $b_1$.", "Solve $I = Prt$ for $r$."],
            "traps": ["Illegal Fraction Cancellation: Canceling 2 in $\\frac{P - 2L}{2}$ without dividing both terms in the numerator.", "Dividing by Variable without Parentheses: In $y = mx + b$, writing $x = y - b / m$ instead of $x = \\frac{y - b}{m}$."],
            "cross": ["Physics ([[PHY-T01]]): Fundamental physics mechanics skill ($v = v_0 + at \\implies t = \\frac{v - v_0}{a}$).", "Programming ([[PRG-T01]]): Writing getter methods and inversion formulas for graphics rendering transforms."]
        },
        "active_recall": [
            {"q": "Solve perimeter formula P = 2L + 2W for L.", "a": "Subtract $2W$: $P - 2W = 2L$. Divide by 2: $L = \\frac{P - 2W}{2}$ (or $L = \\frac{P}{2} - W$)."},
            {"q": "Solve kinetic energy E = (1/2)m v^2 for m.", "a": "Multiply by 2: $2E = mv^2$. Divide by $v^2$: $m = \\frac{2E}{v^2}$."}
        ]
    },

    # =========================================================================
    # CHAPTER C13: POLYNOMIALS (6 Units)
    # =========================================================================
    "MTH-T01-C13-U01": {
        "title": "Add and Subtract Polynomials",
        "chapter": "MTH-T01-C13",
        "objective": "Identify monomial, binomial, and trinomial polynomials, determine term and polynomial degrees, and add and subtract signed polynomials by combining like terms.",
        "expected_output": "Fluency in arranging polynomials in standard descending order and combining like terms accurately.",
        "concepts": [
            "**Polynomial Anatomy:** A monomial is one term ($ax^n$); a binomial has two terms ($ax + b$); a trinomial has three terms ($ax^2 + bx + c$).",
            "**Degree of Polynomial:** The highest exponent of the variable in any non-zero term. Constant terms have degree 0.",
            "**Standard Form:** Terms written in descending order of exponents (e.g. $4x^3 - 2x^2 + 7x - 5$).",
            "**Subtraction Distribution Rule:** Subtracting a polynomial requires negating every term inside the parentheses before combining like terms."
        ],
        "formulas": [
            "(a x^n) + (b x^n) = (a + b)x^n \\quad (\\text{Like Terms})",
            "-(ax^2 + bx + c) = -ax^2 - bx - c"
        ],
        "example": {
            "title": "Subtracting Polynomials and Arranging in Standard Form",
            "steps": [
                "Simplify: $(5x^3 - 2x^2 + 8) - (3x^3 + 7x^2 - 4x - 6)$.",
                "Distribute the negative sign across the second polynomial:",
                "5x^3 - 2x^2 + 8 - 3x^3 - 7x^2 + 4x + 6",
                "Group like terms by descending degree:",
                "(5x^3 - 3x^3) + (-2x^2 - 7x^2) + (4x) + (8 + 6)",
                "Combine coefficients:",
                "2x^3 - 9x^2 + 4x + 14."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why $4x^2$ and $4x^3$ are NOT like terms even though they share the same base and coefficient.", "Explain why the degree of $7x^2y^3$ is 5."],
            "computational": ["State the degree and type of: $9x^4 - 2x + 7$.", "Add: $(3y^2 - 5y + 11) + (8y^2 + 2y - 15)$.", "Subtract: $(7a^2 - 4a + 9) - (10a^2 - 4a - 3)$."],
            "traps": ["Exponent Addition Error: Writing $3x^2 + 4x^2 = 7x^4$. Exponents NEVER change during addition/subtraction!", "Sign Omission in Subtraction: In $-(x^2 - 5x)$, failing to turn $-5x$ into $+5x$."],
            "cross": ["Programming ([[PRG-T01]]): Polynomial interpolation algorithms and Big-O term dominance ($O(n^3 + n^2) = O(n^3)$).", "Physics ([[PHY-T01]]): Position polynomial equations $s(t) = s_0 + v_0 t + \\frac{1}{2}at^2$."]
        },
        "active_recall": [
            {"q": "What is the degree of the polynomial 4x^5 - 7x^3 + 2x - 19?", "a": "Degree 5 (the highest exponent of the variable)."},
            {"q": "What is the result of (3x^2 - 5) - (x^2 - 2x + 7)?", "a": "$3x^2 - 5 - x^2 + 2x - 7 = 2x^2 + 2x - 12$."}
        ]
    },

    "MTH-T01-C13-U02": {
        "title": "Use Multiplication Properties of Exponents",
        "chapter": "MTH-T01-C13",
        "objective": "Apply the product rule ($a^m \\cdot a^n = a^{m+n}$), power of a power rule ($(a^m)^n = a^{mn}$), and power of a product rule ($(ab)^n = a^n b^n$) to simplify monomial expressions.",
        "expected_output": "Mastery of exponent multiplication identities across positive integer powers.",
        "concepts": [
            "**Product Property of Exponents:** When multiplying like bases, add exponents: $a^m \\cdot a^n = a^{m+n}$.",
            "**Power Property of Exponents:** When raising a power to a power, multiply exponents: $(a^m)^n = a^{mn}$.",
            "**Product to a Power Property:** Each factor in the base is raised to the power: $(ab)^n = a^n b^n$."
        ],
        "formulas": [
            "a^m \\cdot a^n = a^{m+n}",
            "(a^m)^n = a^{mn}",
            "(ab)^n = a^n b^n"
        ],
        "example": {
            "title": "Simplifying Compound Monomial Products",
            "steps": [
                "Simplify: $(-3x^4 y^2)^3 (2x^3 y^5)^2$.",
                "Apply Power to a Power property to first factor: $(-3)^3 (x^4)^3 (y^2)^3 = -27 x^{12} y^6$.",
                "Apply Power to a Power property to second factor: $2^2 (x^3)^2 (y^5)^2 = 4 x^6 y^{10}$.",
                "Multiply numerical coefficients: $-27 \\times 4 = -108$.",
                "Multiply like bases using Product Property: $x^{12} \\cdot x^6 = x^{12+6} = x^{18}$; $y^6 \\cdot y^{10} = y^{6+10} = y^{16}$.",
                "Final combined monomial: $-108 x^{18} y^{16}$."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain the algebraic justification for why $x^3 \\cdot x^4 = x^7$ using expanded factor form.", "Contrast $x^3 \\cdot x^4$ (add exponents $\\implies x^7$) with $(x^3)^4$ (multiply exponents $\\implies x^{12}$)."],
            "computational": ["Simplify: $(4a^3b^5)(7a^2b)$.", "Simplify: $(-2m^3n^4)^4$.", "Simplify: $(x^2)^5 \\cdot (x^3)^4$."],
            "traps": ["Base Multiplication Fallacy: Writing $2^3 \\cdot 2^4 = 4^7$. The base NEVER changes: $2^3 \\cdot 2^4 = 2^7$!", "Coefficient Exponent Miss: In $(3x^4)^2$, writing $3x^8$ instead of $3^2 x^8 = 9x^8$."],
            "cross": ["Computer Science ([[PRG-T01]]): Binary data units ($2^{10} = 1024 = 1\\text{ KiB}$) and logarithmic time scale analysis.", "Physics ([[PHY-T01]]): Calculating squared and cubed physical quantities (e.g. $[L]^2$ for area, $[L]^3$ for volume)."]
        },
        "active_recall": [
            {"q": "What is the difference between x^4 * x^5 and (x^4)^5?", "a": "$x^4 \\cdot x^5 = x^{4+5} = x^9$ (adding exponents when multiplying like bases). But $(x^4)^5 = x^{4 \\times 5} = x^{20}$ (multiplying exponents when raising a power to a power)."},
            {"q": "Simplify (-2x^3)^4.", "a": "$(-2)^4 (x^3)^4 = 16x^{12}$."}
        ]
    },

    "MTH-T01-C13-U03": {
        "title": "Multiply Polynomials",
        "chapter": "MTH-T01-C13",
        "objective": "Multiply monomials by polynomials using distribution, multiply binomials using FOIL, and multiply multi-term polynomials using vertical and horizontal methods.",
        "expected_output": "Fluency in expanding products of arbitrary polynomials and special product patterns.",
        "concepts": [
            "**Monomial by Polynomial:** Distribute the monomial to every term: $a(b + c + d) = ab + ac + ad$.",
            "**FOIL Method for Binomials:** First, Outer, Inner, Last: $(a + b)(c + d) = ac + ad + bc + bd$.",
            "**Special Products:**",
            "- Binomial Squares: $(a + b)^2 = a^2 + 2ab + b^2$; $(a - b)^2 = a^2 - 2ab + b^2$.",
            "- Difference of Squares: $(a + b)(a - b) = a^2 - b^2$."
        ],
        "formulas": [
            "(a + b)(c + d) = ac + ad + bc + bd",
            "(a + b)^2 = a^2 + 2ab + b^2, \\qquad (a - b)^2 = a^2 - 2ab + b^2",
            "(a + b)(a - b) = a^2 - b^2"
        ],
        "example": {
            "title": "Multiplying a Binomial by a Trinomial",
            "steps": [
                "Multiply: $(2x - 3)(x^2 + 4x - 5)$.",
                "Distribute $2x$ to all three terms:",
                "2x(x^2) + 2x(4x) + 2x(-5) = 2x^3 + 8x^2 - 10x",
                "Distribute $-3$ to all three terms:",
                "-3(x^2) - 3(4x) - 3(-5) = -3x^2 - 12x + 15",
                "Combine all terms:",
                "2x^3 + (8x^2 - 3x^2) + (-10x - 12x) + 15",
                "= 2x^3 + 5x^2 - 22x + 15."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why $(x + 5)^2$ is NOT equal to $x^2 + 25$ using an area diagram.", "Explain why the middle terms cancel out in the product $(x + 4)(x - 4)$."],
            "computational": ["Multiply using FOIL: $(3x - 4)(2x + 5)$.", "Expand special product: $(2x - 7)^2$.", "Multiply: $(x - 5)(x^2 + 5x + 25)$."],
            "traps": ["Freshman's Dream Fallacy: Omitting the middle term $2ab$ when squaring a binomial ($(x + 3)^2 = x^2 + 9$ is WRONG; must be $x^2 + 6x + 9$).", "Sign Error on Last Term: In $(x - 4)(x - 6)$, writing $-24$ instead of $+24$ for $(-4)(-6)$."],
            "cross": ["Algebra & Calculus: Quadratic expansions and finding roots via factoring.", "Physics ([[PHY-T01]]): Kinetic energy expansions when velocity changes $v = (v_0 + \\Delta v)$."]
        },
        "active_recall": [
            {"q": "What is the complete expansion of (3x - 5)^2?", "a": "$(3x)^2 - 2(3x)(5) + 5^2 = 9x^2 - 30x + 25$."},
            {"q": "What special product results from (2x + 7)(2x - 7)?", "a": "$(2x)^2 - (7)^2 = 4x^2 - 49$ (Difference of Squares; outer and inner terms $+14x - 14x = 0$ cancel)."}
        ]
    },

    "MTH-T01-C13-U04": {
        "title": "Divide Monomials",
        "chapter": "MTH-T01-C13",
        "objective": "Apply the quotient property of exponents ($\\frac{a^m}{a^n} = a^{m-n}$), divide monomials, and divide polynomials by a monomial.",
        "expected_output": "Proficiency in simplifying quotients of monomials and multi-term polynomial division by a monomial.",
        "concepts": [
            "**Quotient Property of Exponents:** When dividing like non-zero bases, subtract exponents: $\\frac{a^m}{a^n} = a^{m-n}$ ($a \\neq 0$).",
            "**Dividing a Polynomial by a Monomial:** Distribute the divisor to every term in the numerator independently: $\\frac{a + b + c}{d} = \\frac{a}{d} + \\frac{b}{d} + \\frac{c}{d}$.",
            "**Simplifying Numerical Coefficients:** Divide or reduce integer coefficients as standard fractions."
        ],
        "formulas": [
            "\\frac{a^m}{a^n} = a^{m-n} \\quad (a \\neq 0)",
            "\\left(\\frac{a}{b}\\right)^n = \\frac{a^n}{b^n} \\quad (b \\neq 0)",
            "\\frac{a + b}{c} = \\frac{a}{c} + \\frac{b}{c} \\quad (c \\neq 0)"
        ],
        "example": {
            "title": "Dividing a Trinomial by a Monomial",
            "steps": [
                "Divide: $\\frac{18x^5 y^4 - 24x^3 y^2 + 6x^2 y}{6x^2 y}$.",
                "Separate into individual fractional terms:",
                "\\frac{18x^5 y^4}{6x^2 y} - \\frac{24x^3 y^2}{6x^2 y} + \\frac{6x^2 y}{6x^2 y}",
                "Simplify each term using numerical division and quotient rule for exponents:",
                "Term 1: $\\frac{18}{6} x^{5-2} y^{4-1} = 3x^3 y^3$.",
                "Term 2: $-\\frac{24}{6} x^{3-2} y^{2-1} = -4xy$.",
                "Term 3: $\\frac{6x^2 y}{6x^2 y} = 1$.",
                "Combine: $3x^3 y^3 - 4xy + 1$."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why $\\frac{x^5}{x^2} = x^3$ by writing out the factor expansion $\\frac{x \\cdot x \\cdot x \\cdot x \\cdot x}{x \\cdot x}$.", "Explain why the last term in $\\frac{4x + 8}{4}$ simplifies to 2, not 0."],
            "computational": ["Simplify: $\\frac{-48a^8 b^5 c^2}{12a^3 b^5 c}$.", "Divide: $\\frac{15x^4 - 25x^3 + 5x}{5x}$."],
            "traps": ["Disappearing Last Term Trap: In $\\frac{6x^2 + 3x}{3x}$, simplifying $\\frac{3x}{3x}$ to nothing/zero instead of 1, writing $2x$ instead of $2x + 1$!", "Illegal Partial Cancellation: Canceling $x$ in $\\frac{x + 5}{x}$. A factor can only cancel if it divides EVERY term in the numerator!"],
            "cross": ["Algebra & Precalculus: Finding horizontal and vertical asymptotes in rational functions $\\frac{P(x)}{Q(x)}$.", "Physics ([[PHY-T01]]): Dimension cancellation in unit rates (e.g. $[L][T]^{-1} / [T]$)."]
        },
        "active_recall": [
            {"q": "What is the result of dividing 12x^3 - 4x by 4x?", "a": "$\\frac{12x^3}{4x} - \\frac{4x}{4x} = 3x^2 - 1$ (do not forget the $-1$)."},
            {"q": "Simplify (x^8 * y^4) / (x^3 * y^4).", "a": "$x^{8-3} y^{4-4} = x^5 y^0 = x^5(1) = x^5$."}
        ]
    },

    "MTH-T01-C13-U05": {
        "title": "Integer Exponents and Scientific Notation",
        "chapter": "MTH-T01-C13",
        "objective": "Define and apply zero exponents ($x^0 = 1$) and negative integer exponents ($x^{-n} = \\frac{1}{x^n}$), and convert and perform arithmetic with numbers in scientific notation ($a \\times 10^n$).",
        "expected_output": "Mastery of negative exponent inversion and scientific notation calculations across scientific scales.",
        "concepts": [
            "**Zero Exponent Definition:** For any non-zero real number $a$, $a^0 = 1$. (Justified by $\\frac{a^n}{a^n} = a^{n-n} = a^0 = 1$). Note: $0^0$ is indeterminate.",
            "**Negative Exponent Definition:** A negative exponent indicates the reciprocal of the base raised to the positive power: $a^{-n} = \\frac{1}{a^n}$ and $\\frac{1}{a^{-n}} = a^n$ ($a \\neq 0$).",
            "**Fractional Base with Negative Exponent:** $\\left(\\frac{a}{b}\\right)^{-n} = \\left(\\frac{b}{a}\\right)^n = \\frac{b^n}{a^n}$.",
            "**Scientific Notation:** Expressed as $a \\times 10^n$, where $1 \\le |a| < 10$ and $n \\in \\mathbb{Z}$."
        ],
        "formulas": [
            "a^0 = 1 \\quad (a \\neq 0), \\qquad a^{-n} = \\frac{1}{a^n} \\quad (a \\neq 0)",
            "\\left(\\frac{a}{b}\\right)^{-n} = \\left(\\frac{b}{a}\\right)^n, \\qquad a \\times 10^n \\quad (1 \\le a < 10)"
        ],
        "example": {
            "title": "Simplifying Negative Exponents & Multiplying Scientific Notation",
            "steps": [
                "Simplify and express with positive exponents: $\\frac{4x^{-3} y^5}{20x^2 y^{-4}}$.",
                "Reduce coefficients: $\\frac{4}{20} = \\frac{1}{5}$.",
                "Apply quotient rule on $x$: $x^{-3 - 2} = x^{-5} = \\frac{1}{x^5}$.",
                "Apply quotient rule on $y$: $y^{5 - (-4)} = y^{5 + 4} = y^9$.",
                "Combine: $\\frac{y^9}{5x^5}$.",
                "Scientific Notation: $(3.2 \\times 10^4) \\times (5.0 \\times 10^{-7}) = (3.2 \\times 5.0) \\times 10^{4 + (-7)} = 16.0 \\times 10^{-3} = 1.6 \\times 10^{-2} = 0.016$."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why $2^{-3}$ is positive $\\frac{1}{8}$ and NOT negative $-8$.", "Explain why the coefficient $a$ in scientific notation must satisfy $1 \\le |a| < 10$."],
            "computational": ["Evaluate: (a) $(-5)^0$, (b) $-5^0$, (c) $4^{-3}$, (d) $\\left(\\frac{2}{3}\\right)^{-2}$.", "Convert to scientific notation: $0.0000408$ and $72,500,000$.", "Divide: $\\frac{8.4 \\times 10^8}{2.1 \\times 10^{-3}}$."],
            "traps": ["Negative Exponent = Negative Number Fallacy: Believing $x^{-2} = -x^2$. A negative exponent indicates a reciprocal, NOT a sign change!", "Parentheses Negation Difference: $(-4)^0 = 1$, whereas $-4^0 = -(4^0) = -1$."],
            "cross": ["Physics ([[PHY-T01]]): Universal constants (Speed of light $3.0 \\times 10^8\\text{ m/s}$, electron charge $1.6 \\times 10^{-19}\\text{ C}$).", "Astronomy: Astronomical distances in light-years and parsecs."]
        },
        "active_recall": [
            {"q": "What is the exact value of (3/4)^(-2)?", "a": "$\\left(\\frac{4}{3}\\right)^2 = \\frac{16}{9}$."},
            {"q": "Why is 45 * 10^6 NOT in scientific notation, and how do you fix it?", "a": "Because the leading coefficient 45 is not strictly between 1 and 10 ($45 \\ge 10$). To fix it: $45 = 4.5 \\times 10^1 \\implies (4.5 \\times 10^1) \\times 10^6 = 4.5 \\times 10^7$."}
        ]
    },

    "MTH-T01-C13-U06": {
        "title": "Introduction to Factoring Polynomials",
        "chapter": "MTH-T01-C13",
        "objective": "Identify and factor out the greatest common factor (GCF) of polynomial terms, and factor 4-term polynomials by grouping.",
        "expected_output": "Proficiency in reversing polynomial multiplication by extracting monomial GCFs and executing factor by grouping.",
        "concepts": [
            "**Factoring as Inverse Multiplication:** Multiplication combines factors into an expanded polynomial; factoring decomposes a polynomial back into a product of simpler factors.",
            "**Greatest Common Factor (GCF):** The product of the largest common integer factor and the lowest power of each shared variable.",
            "**Factoring by Grouping (4 terms):** Pair terms $(T_1 + T_2) + (T_3 + T_4)$, extract the GCF from each binomial group, and extract the resulting common binomial factor."
        ],
        "formulas": [
            "ab + ac = a(b + c) \\quad (\\text{GCF Factoring})",
            "ax + ay + bx + by = a(x + y) + b(x + y) = (a + b)(x + y) \\quad (\\text{Grouping})"
        ],
        "example": {
            "title": "Factoring by GCF and Factoring by Grouping",
            "steps": [
                "Part 1: Factor out the GCF from $18x^4 y^3 - 27x^3 y^2 + 9x^2 y$.",
                "Numerical GCF of 18, 27, 9 is 9. Lowest variable powers: $x^2$ and $y^1$. GCF $= 9x^2 y$.",
                "Divide each term by $9x^2 y$:",
                "9x^2 y (2x^2 y^2 - 3xy + 1).",
                "Part 2: Factor by grouping: $x^3 + 3x^2 + 4x + 12$.",
                "Group pairs: $(x^3 + 3x^2) + (4x + 12)$.",
                "Extract GCF from each group: $x^2(x + 3) + 4(x + 3)$.",
                "Extract common binomial factor $(x + 3)$:",
                "(x^2 + 4)(x + 3)."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why factoring is the reverse process of the distributive property.", "Explain how to check whether a polynomial factorization is correct."],
            "computational": ["Factor out GCF: $14m^5n^3 - 21m^3n^4 + 35m^2n^2$.", "Factor by grouping: $2x^3 - 6x^2 + 5x - 15$.", "Factor by grouping with sign change: $xy + 4y - 3x - 12$."],
            "traps": ["Incomplete Factoring: Factoring out $2$ when $4$ is the true GCF, leaving non-prime factors in the parenthesis.", "Negative Sign Drop in Grouping: In $(xy - 3x) - (4y + 12)$, forgetting that pulling out a negative flips the inner sign to $- (4y - 12)$."],
            "cross": ["Algebra & Calculus: Finding polynomial roots and solving quadratic equations $ax^2 + bx + c = 0$.", "Physics ([[PHY-T01]]): Finding when a projectile hits the ground by setting height $h(t) = 0$ and factoring."]
        },
        "active_recall": [
            {"q": "What is the GCF of 12x^3y^2 and 18x^2y^5?", "a": "Numerical GCF of 12 and 18 is 6. Lowest power of $x$ is $x^2$; lowest power of $y$ is $y^2$. $\\text{GCF} = 6x^2y^2$."},
            {"q": "What is the factored form of 3x(x - 5) + 4(x - 5)?", "a": "$(3x + 4)(x - 5)$."}
        ]
    },

    # =========================================================================
    # CHAPTER C14: GRAPHS (4 Units)
    # =========================================================================
    "MTH-T01-C14-U01": {
        "title": "Understand Slope of a Line",
        "chapter": "MTH-T01-C14",
        "objective": "Calculate and interpret the slope of a line ($m = \\frac{\\text{rise}}{\\text{run}} = \\frac{y_2 - y_1}{x_2 - x_1}$) from coordinates, graphs, and rates of change, and identify positive, negative, zero, and undefined slopes.",
        "expected_output": "Fluency in computing slope from ordered pairs and interpreting slope as a physical and geometric rate of change.",
        "concepts": [
            "**Slope Definition:** The ratio of vertical change ($\\Delta y$, rise) to horizontal change ($\\Delta x$, run): $m = \\frac{y_2 - y_1}{x_2 - x_1}$.",
            "**Four Slope Geometries:**",
            "- **Positive ($m > 0$):** Rises from left to right.",
            "- **Negative ($m < 0$):** Falls from left to right.",
            "- **Zero ($m = 0$):** Horizontal line ($y = c$).",
            "- **Undefined ($m = \\text{undefined}$):** Vertical line ($x = c$, division by zero $\\Delta x = 0$)."
        ],
        "formulas": [
            "m = \\frac{\\text{rise}}{\\text{run}} = \\frac{y_2 - y_1}{x_2 - x_1} \\quad (x_1 \\neq x_2)"
        ],
        "example": {
            "title": "Calculating Slope from Two Points",
            "steps": [
                "Find the slope of the line passing through $(-2, 5)$ and $(4, -7)$.",
                "Label coordinates: $(x_1, y_1) = (-2, 5)$ and $(x_2, y_2) = (4, -7)$.",
                "Apply the slope formula:",
                "m = \\frac{y_2 - y_1}{x_2 - x_1} = \\frac{-7 - 5}{4 - (-2)}",
                "Simplify numerator and denominator:",
                "m = \\frac{-12}{4 + 2} = \\frac{-12}{6} = -2.",
                "Interpretation: For every 1 unit moved right, the line drops 2 units vertically."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why a vertical line has an undefined slope, whereas a horizontal line has a slope of zero.", "Explain why the order of points does not matter as long as coordinates are subtracted in the same direction."],
            "computational": ["Find the slope through $(3, 8)$ and $(7, 8)$.", "Find the slope through $(-5, -2)$ and $(-5, 4)$.", "Find the slope through $(-4, -1)$ and $(2, 3)$."],
            "traps": ["Inverted Slope Trap: Calculating $\\frac{x_2 - x_1}{y_2 - y_1}$ (run over rise) instead of $\\frac{y_2 - y_1}{x_2 - x_1}$.", "Sign Inversion Trap: In $4 - (-2)$, forgetting that subtracting a negative equals adding a positive."],
            "cross": ["Physics ([[PHY-T01]]): Velocity as the slope of a position-time graph ($v = \\frac{\\Delta x}{\\Delta t}$), and acceleration as slope of $v\\text{-}t$ graph.", "Economics: Marginal cost as the slope of the total cost curve."]
        },
        "active_recall": [
            {"q": "What is the slope of a horizontal line and what is the slope of a vertical line?", "a": "A horizontal line has slope $m = 0$ (no rise, $\\frac{0}{\\text{run}} = 0$). A vertical line has an undefined slope (division by zero, $\\frac{\\text{rise}}{0}$)."},
            {"q": "What is the slope of the line passing through (2, 5) and (6, 17)?", "a": "$m = \\frac{17 - 5}{6 - 2} = \\frac{12}{4} = 3$."}
        ]
    },

    "MTH-T01-C14-U02": {
        "title": "Graphing with Intercepts",
        "chapter": "MTH-T01-C14",
        "objective": "Identify, calculate, and plot the x-intercept and y-intercept of a linear equation, and graph standard form linear equations ($Ax + By = C$) using intercepts.",
        "expected_output": "Speed and precision in finding intercepts by setting opposite variables to zero and graphing standard lines.",
        "concepts": [
            "**$x$-intercept:** The point where the graph crosses the $x$-axis. Occurs when $y = 0$; coordinate is $(a, 0)$.",
            "**$y$-intercept:** The point where the graph crosses the $y$-axis. Occurs when $x = 0$; coordinate is $(0, b)$.",
            "**The Cover-Up Method for Standard Form ($Ax + By = C$):**",
            "- Set $y = 0 \\implies Ax = C \\implies x = \\frac{C}{A}$ ($x$-intercept).",
            "- Set $x = 0 \\implies By = C \\implies y = \\frac{C}{B}$ ($y$-intercept)."
        ],
        "formulas": [
            "x\\text{-intercept: } (a, 0) \\iff y = 0",
            "y\\text{-intercept: } (0, b) \\iff x = 0"
        ],
        "example": {
            "title": "Graphing 3x - 4y = 12 Using Intercepts",
            "steps": [
                "Find $x$-intercept: Set $y = 0$:",
                "3x - 4(0) = 12 \\implies 3x = 12 \\implies x = 4. \\quad \\text{Point: } (4, 0).",
                "Find $y$-intercept: Set $x = 0$:",
                "3(0) - 4y = 12 \\implies -4y = 12 \\implies y = -3. \\quad \\text{Point: } (0, -3).",
                "Graphing: Plot $(4, 0)$ on the $x$-axis, plot $(0, -3)$ on the $y$-axis.",
                "Draw a straight line passing through both intercepts and extending with arrows."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why setting $y = 0$ reveals the $x$-intercept.", "What happens when both intercepts are $(0, 0)$? How do you graph the line in that case?"],
            "computational": ["Find intercepts and graph: $2x + 5y = 20$.", "Find intercepts and graph: $4x - y = 8$.", "Find intercepts for $y = -3x$."],
            "traps": ["Swapped Coordinates: Writing the $x$-intercept $(4, 0)$ as $(0, 4)$ or vice versa.", "Sign Slip on Negative Coefficient: In $2x - 3y = 6$, setting $x = 0$ yields $-3y = 6 \\implies y = -2$, not $+2$."],
            "cross": ["Economics: Budget constraint lines where intercepts represent purchasing only good X or only good Y.", "Physics ([[PHY-T01]]): Initial position $x_0$ as the $y$-intercept of a position-time graph at $t = 0$."]
        },
        "active_recall": [
            {"q": "How do you find the x-intercept of any linear equation?", "a": "Substitute $y = 0$ into the equation and solve for $x$. Write the answer as the coordinate pair $(x, 0)$."},
            {"q": "What are the x- and y-intercepts of 5x + 2y = 10?", "a": "$x$-intercept is $(2, 0)$ (since $5x = 10$). $y$-intercept is $(0, 5)$ (since $2y = 10$)."}
        ]
    },

    "MTH-T01-C14-U03": {
        "title": "Graphing Linear Equations",
        "chapter": "MTH-T01-C14",
        "objective": "Graph linear equations using slope-intercept form ($y = mx + b$), convert standard form equations to slope-intercept form, and graph horizontal and vertical lines.",
        "expected_output": "Fluency in rapid slope-intercept graphing and identifying parallel and perpendicular line relationships.",
        "concepts": [
            "**Slope-Intercept Form:** $y = mx + b$, where $m$ is the slope and $(0, b)$ is the $y$-intercept.",
            "**Horizontal Line:** $y = c$. Slope is $0$. Crosses $y$-axis at $(0, c)$. Every point has $y$-coordinate $c$.",
            "**Vertical Line:** $x = c$. Slope is undefined. Crosses $x$-axis at $(c, 0)$. Every point has $x$-coordinate $c$.",
            "**Parallel Lines ($L_1 \\parallel L_2$):** Slopes are equal: $m_1 = m_2$.",
            "**Perpendicular Lines ($L_1 \\perp L_2$):** Slopes are negative reciprocals: $m_1 \\cdot m_2 = -1$ (or $m_2 = -\\frac{1}{m_1}$)."
        ],
        "formulas": [
            "y = mx + b \\quad (\\text{Slope-Intercept Form})",
            "y = c \\quad (\\text{Horizontal}), \\qquad x = c \\quad (\\text{Vertical})",
            "m_1 = m_2 \\quad (\\text{Parallel}), \\qquad m_1 \\cdot m_2 = -1 \\quad (\\text{Perpendicular})"
        ],
        "example": {
            "title": "Converting Standard Form to Slope-Intercept Form & Graphing",
            "steps": [
                "Convert $2x + 3y = 9$ to slope-intercept form, identify slope and intercept, and graph.",
                "Subtract $2x$ from both sides: $3y = -2x + 9$.",
                "Divide every term by $3$: $y = -\\frac{2}{3}x + 3$.",
                "Identify: Slope $m = -\\frac{2}{3} = \\frac{-2}{3}$ (down 2, right 3); $y$-intercept is $(0, 3)$.",
                "Graphing steps:",
                "1. Plot $(0, 3)$ on the $y$-axis.",
                "2. From $(0, 3)$, move down 2 units and right 3 units to plot $(3, 1)$.",
                "3. Draw the straight line passing through $(0, 3)$ and $(3, 1)$."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why parallel lines never intersect in terms of their identical slopes.", "Explain why the slopes of perpendicular lines multiply to $-1$."],
            "computational": ["Graph $y = \\frac{3}{4}x - 2$ using slope and intercept.", "Graph the line $y = -4$ and the line $x = 5$.", "Determine if the lines $y = 3x - 1$ and $x + 3y = 6$ are perpendicular."],
            "traps": ["Negative Slope Direction: When slope is $-\\frac{2}{3}$, moving down 2 AND left 3 (which makes a positive slope!). Only ONE direction is negative: down 2, right 3.", "Equation Confusion: Graphing $y = 4$ as a vertical line instead of horizontal."],
            "cross": ["Physics ([[PHY-T01]]): Kinematic equation $v(t) = at + v_0$, matching $y = mx + b$ with slope $a$ and intercept $v_0$.", "Data Science: Linear regression fit lines minimizing least-squares residual distance."]
        },
        "active_recall": [
            {"q": "What is the slope and y-intercept of y = -5x + 8?", "a": "Slope $m = -5$ (or $\\frac{-5}{1}$) and $y$-intercept is $(0, 8)$."},
            {"q": "If line 1 has slope 2/5, what is the slope of a line parallel to it, and what is the slope of a line perpendicular to it?", "a": "Parallel slope is $\\frac{2}{5}$ (equal). Perpendicular slope is $-\\frac{5}{2}$ (negative reciprocal)."}
        ]
    },

    "MTH-T01-C14-U04": {
        "title": "Use the Rectangular Coordinate System",
        "chapter": "MTH-T01-C14",
        "objective": "Identify quadrants, plot ordered pairs $(x, y)$, verify solutions to two-variable linear equations by substitution, and interpret coordinate boundaries.",
        "expected_output": "Complete fluency in navigation, plotting, and algebraic verification on the 2D Cartesian plane.",
        "concepts": [
            "**Cartesian Coordinate Plane Structure:** Two perpendicular real number lines intersecting at the origin $(0, 0)$: horizontal $x$-axis and vertical $y$-axis.",
            "**Four Quadrants (Counterclockwise):**",
            "- **Quadrant I:** $(+, +)$",
            "- **Quadrant II:** $(-, +)$",
            "- **Quadrant III:** $(-, -)$",
            "- **Quadrant IV:** $(+, -)$",
            "- Axis Points: On $x$-axis $(x, 0)$; on $y$-axis $(0, y)$ (do NOT belong to any quadrant).",
            "**Solution to an Equation in Two Variables:** An ordered pair $(a, b)$ that makes the equation true when $x = a$ and $y = b$ are substituted."
        ],
        "formulas": [
            "(x, y) \\in \\text{Graph} \\iff Ax + By = C \\text{ is True}"
        ],
        "example": {
            "title": "Plotting Points Across Quadrants & Verifying Solutions",
            "steps": [
                "Identify the quadrant or axis for: $A(3, -4), B(-2, 5), C(-6, -1), D(0, -3), E(4, 0)$.",
                "$A(3, -4) \\implies (+, -) \\implies$ Quadrant IV.",
                "$B(-2, 5) \\implies (-, +) \\implies$ Quadrant II.",
                "$C(-6, -1) \\implies (-, -) \\implies$ Quadrant III.",
                "$D(0, -3) \\implies$ On the negative $y$-axis (no quadrant).",
                "$E(4, 0) \\implies$ On the positive $x$-axis (no quadrant).",
                "Verify whether $(2, -1)$ is a solution to $3x - 5y = 11$:",
                "Substitute $x = 2, y = -1$: $3(2) - 5(-1) = 6 + 5 = 11 = 11 \\quad (\\text{True! It is a solution})."
            ]
        },
        "practice_guide": {
            "conceptual": ["Explain why points on the axes do not belong to Quadrants I–IV.", "Explain why any linear equation has infinitely many solutions $(x, y)$."],
            "computational": ["Plot points $(2, 3), (-4, 2), (-3, -3), (1, -4)$ on a Cartesian grid.", "Determine whether $(-3, 4)$ is a solution to $2x + y = -2$."],
            "traps": ["Axis Order Slip: Plotting $(x, y)$ by moving vertically first. Always move horizontally ($x$) first, then vertically ($y$)!", "Negative Coordinate Sign Inversion: Plotting $(-3, 4)$ in Quadrant IV instead of Quadrant II."],
            "cross": ["Computer Graphics ([[PRG-T01]]): Screen coordinate space (top-left origin $(0, 0)$ with inverted $y$-axis).", "Physics ([[PHY-T01]]): 2D projectile coordinate tracking $(x(t), y(t))$."]
        },
        "active_recall": [
            {"q": "In which quadrant does the point (-7, -3) lie?", "a": "Quadrant III (both $x$ and $y$ are negative)."},
            {"q": "Is the point (3, 2) a solution to the equation 4x - 3y = 7?", "a": "Substitute: $4(3) - 3(2) = 12 - 6 = 6 \\neq 7$. No, $(3, 2)$ is not a solution."}
        ]
    }
}
