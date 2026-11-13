# -*- coding: utf-8 -*-
"""
Topic and Chapter instructional data for MTH-T01 (Prealgebra).
Source: OpenStax Prealgebra 2e (https://openstax.org/books/prealgebra-2e/pages/preface)
No emojis in page body blocks.
"""

MTH_TOPIC_DATA = {
    "full_id": "MTH-T01",
    "title": "Prealgebra",
    "goal": "Build rock-solid algebraic fluency across number systems, equations, exponents, roots, polynomials, geometry, and linear graphs as the foundation for higher mathematics, physics, and algorithmic problem solving.",
    "source_url": "https://openstax.org/books/prealgebra-2e/pages/preface",
    "source_note": "OpenStax — Prealgebra 2e (https://openstax.org/books/prealgebra-2e/pages/preface) | Status: URL Accessible | Content Accessible | Content Verified (HTTP 200). Chapters C07, C08, and C09 expand upon the OpenStax Ratios/Exponents/Roots sections with dedicated problem-solving progressions; those supplementary extensions are explicitly noted where applicable.",
    "overview": [
        "Prealgebra (MTH-T01) is the structural bridge between arithmetic (computing with specific numbers) and symbolic algebra (reasoning about general relationships, invariants, and functions).",
        "Mastery of this topic ensures that algebraic manipulation—operating on signed numbers, fractions, decimals, exponents, radicals, linear equations, polynomials, and coordinate graphs—becomes automatic and error-free, freeing working memory for Calculus, Linear Algebra, Physics (PHY-T01), and Programming (PRG).",
        "Every Unit in MTH-T01 uses a Subject-Adaptive Mathematical Design: intuitive & visual models, formal properties & LaTeX equations, step-by-step worked examples, graduated problem-solving exercises, Active Recall toggles, and a dedicated 'My Implementation & Mistake Log' to record your own derivations and calculation pitfalls."
    ],
    "outcomes": [
        "Operate fluently across the hierarchy of Real Numbers (Whole Numbers, Integers, Rational Fractions/Decimals, and Irrational Roots) without sign, order-of-operations, or denominator errors.",
        "Translate verbal problem statements into algebraic expressions, equations, proportions, and geometric formulas, and solve single-variable linear equations systematically.",
        "Apply the laws of exponents, scientific notation, and radical simplification (square roots, cube roots, fractional exponents) using algebraic properties rather than rote memorization.",
        "Perform polynomial arithmetic (addition, subtraction, multiplication, monomial division, and introductory factoring) and analyze two-variable linear relationships on the rectangular coordinate plane using intercepts and slope."
    ],
    "chapters_summary": [
        ("MTH-T01-C01 — Whole Numbers (5 Units)", "Place value, rounding, and the four fundamental operations on non-negative integers."),
        ("MTH-T01-C02 — The Language of Algebra (5 Units)", "Variables, order of operations, expression evaluation/translation, one-step equations, factors, primes, and LCM."),
        ("MTH-T01-C03 — Integers (5 Units)", "Signed numbers, absolute value, integer arithmetic, and one-step integer equations."),
        ("MTH-T01-C04 — Fractions (6 Units)", "Common/different denominators, mixed numbers, complex fractions, and fractional linear equations."),
        ("MTH-T01-C05 — Decimals (7 Units)", "Decimal place value, operations, fraction conversions, decimal equations, averages/probability, ratios, and introductory square roots."),
        ("MTH-T01-C06 — Percents (5 Units)", "Percent conversions, percent equations, tax/commission/discount, simple interest, and percent proportions."),
        ("MTH-T01-C07 — Proportional & Ratio Reasoning (6 Units)", "Ratios, unit rates, solving proportions, direct variation, inverse variation, and scale/similar-figure applications."),
        ("MTH-T01-C08 — Exponents (6 Units)", "Product, quotient, and power rules, zero and negative exponents, and scientific notation."),
        ("MTH-T01-C09 — Roots (6 Units)", "Square roots, simplifying radicals, cube roots, radical properties, fractional exponents, and scientific notation roots."),
        ("MTH-T01-C10 — The Properties of Real Numbers (5 Units)", "Rational vs. irrational numbers, commutative/associative/distributive laws, identity/inverse/zero properties, and unit conversions."),
        ("MTH-T01-C11 — Solving Linear Equations (4 Units)", "Multi-step linear equations with variables on both sides and fraction/decimal clearing strategies."),
        ("MTH-T01-C12 — Math Models and Geometry (7 Units)", "Problem-solving framework, money/mixture models, angles/triangles/Pythagorean theorem, area/perimeter/volume, and literal formulas."),
        ("MTH-T01-C13 — Polynomials (6 Units)", "Polynomial addition/subtraction, exponent laws review, binomial/polynomial multiplication, monomial division, and GCF factoring."),
        ("MTH-T01-C14 — Graphs (4 Units)", "Rectangular coordinate plane, graphing linear equations by plotting, x/y-intercepts, and slope formula/interpretation.")
    ],
    "final_review": [
        "Can you justify why dividing by zero is undefined, why a negative times a negative is positive, and why any nonzero number to the zero power equals 1?",
        "Can you solve any multi-step linear equation containing parentheses, negative signs, fractions, and decimals on both sides without losing a sign?",
        "Audit all 77 Units in MTH-T01: ensure every Unit marked 'Done' has an honest 'Mastery (0-4)' score, a filled 'My Implementation & Mistake Log', and a scheduled 'Next Review' date."
    ]
}

MTH_CHAPTERS_DATA = {
    "MTH-T01-C01": {
        "title": "Whole Numbers",
        "objective": "Understand base-10 place value and execute addition, subtraction, multiplication, and division on whole numbers with estimation and verification.",
        "criteria": "Accurately translate, round, and compute multi-digit whole number operations and word problems without a calculator.",
        "role": "Establishes the base-10 positional number system and the four fundamental arithmetic operations (and their inverse relationships) that generalize to integers, fractions, decimals, and polynomials in later chapters.",
        "source_section": "OpenStax Prealgebra 2e — Chapter 1: Whole Numbers (Sections 1.1–1.5)",
        "concepts": [
            "Base-10 Positional Structure: Every digit's value is its face value multiplied by a power of 10 ($10^0, 10^1, 10^2, \\dots$). Carrying in addition/multiplication and borrowing (regrouping) in subtraction are direct consequences of bundling or unbundling powers of 10.",
            "Inverse Operation Pairs: Addition and subtraction are inverse operations ($a + b = c \\iff c - b = a$); multiplication and division are inverse operations ($q \\cdot d + r = D$ with $0 \\le r < d$).",
            "Estimation as an Error Check: Rounding operands to their leading place value before computing provides an immediate order-of-magnitude sanity check against arithmetic slips."
        ],
        "challenge": [
            "Compute $40,205 - 18,649$ by hand and verify the result using addition.",
            "Compute $3,408 \\times 27$ and $19,652 \\div 38$ (expressing the result in $D = d \\cdot q + r$ form).",
            "Solve a multi-step budgeting word problem combining multiplication, addition, and subtraction."
        ]
    },
    "MTH-T01-C02": {
        "title": "The Language of Algebra",
        "objective": "Use variables, algebraic notation, order of operations, prime factorization, and equality properties to simplify expressions and solve one-step equations.",
        "criteria": "Simplify nested algebraic expressions, find prime factorizations/LCMs, and solve one-step addition/subtraction equations.",
        "role": "Transitions from pure arithmetic to symbolic reasoning: introducing variables, expressions vs. equations, the universal order of operations (PEMDAS), and number-theoretic building blocks (primes, factors, LCM) required for fraction arithmetic in C04.",
        "source_section": "OpenStax Prealgebra 2e — Chapter 2: The Language of Algebra (Sections 2.1–2.5)",
        "concepts": [
            "Expressions vs. Equations: An expression ($3x + 5$) represents a value and can be evaluated or simplified; an equation ($3x + 5 = 20$) asserts equality between two expressions and can be solved for the variable values that make it true.",
            "Order of Operations Hierarchy: Grouping symbols first, then exponents/roots, then multiplication and division left-to-right (equal priority), then addition and subtraction left-to-right (equal priority).",
            "Fundamental Theorem of Arithmetic & LCM: Every integer greater than 1 factors uniquely into primes; the Least Common Multiple (LCM) takes the highest power of each prime factor present."
        ],
        "challenge": [
            "Simplify $48 \\div 6 \\cdot 2 + 3(10 - 2^3)^2$ step-by-step without falling into the 'multiply before divide' trap.",
            "Find the prime factorization and LCM of $72$ and $108$.",
            "Translate three verbal sentences into algebraic equations and solve them using the Addition and Subtraction Properties of Equality."
        ]
    },
    "MTH-T01-C03": {
        "title": "Integers",
        "objective": "Represent signed numbers on the number line, evaluate absolute value, perform all four operations on integers, and solve integer equations.",
        "criteria": "Evaluate complex signed-number expressions and solve integer equations with zero sign errors.",
        "role": "Extends the Whole Numbers ($\{0, 1, 2, \\dots\}$) to the full set of Integers ($\{\\dots, -2, -1, 0, 1, 2, \\dots\}$) by introducing additive inverses (opposites) and magnitude (absolute value).",
        "source_section": "OpenStax Prealgebra 2e — Chapter 3: Integers (Sections 3.1–3.5)",
        "concepts": [
            "Opposites vs. Absolute Value: $-a$ denotes the additive inverse (opposite) of $a$ (so if $a = -5$, then $-a = 5$), whereas $|a|$ denotes distance from $0$ on the number line (always non-negative: $|a| \\ge 0$).",
            "Unified Addition/Subtraction via Additive Inverse: Subtraction is defined as adding the opposite: $a - b = a + (-b)$.",
            "Sign Rules for Multiplication & Division: Multiplying or dividing two numbers with the same sign yields a positive result; opposite signs yield a negative result. An even number of negative factors is positive; an odd number is negative."
        ],
        "challenge": [
            "Compare $-3^4$ vs. $(-3)^4$ and evaluate $-12 - (-5) \\cdot (-3) + |-18 \\div 6|$.",
            "Solve $-7x = 84$ and $y - (-19) = -31$, checking both solutions by substitution."
        ]
    },
    "MTH-T01-C04": {
        "title": "Fractions",
        "objective": "Perform addition, subtraction, multiplication, and division on fractions, mixed numbers, and complex fractions, and solve fractional equations.",
        "criteria": "Simplify complex fractions, operate on mixed numbers, and solve equations involving fractional coefficients and constants.",
        "role": "Introduces Rational Numbers ($\mathbb{Q}$) in fractional form $\\frac{a}{b}$ ($b \\ne 0$), which are essential for algebraic manipulation, rates of change (slope), and rational expressions.",
        "source_section": "OpenStax Prealgebra 2e — Chapter 4: Fractions (Sections 4.1–4.7)",
        "concepts": [
            "Equivalent Fractions & Fundamental Property: Multiplying or dividing numerator and denominator by the same nonzero number preserves value ($\\frac{a \\cdot k}{b \\cdot k} = \\frac{a}{b}$) because $\\frac{k}{k} = 1$.",
            "Why Multiplication vs. Addition Differ: Multiplication scales both numerator and denominator directly ($\\frac{a}{b} \\cdot \\frac{c}{d} = \\frac{ac}{bd}$), whereas addition/subtraction requires counting identically sized parts (Least Common Denominator, LCD).",
            "Reciprocals & Division: Dividing by $\\frac{c}{d}$ is equivalent to multiplying by its multiplicative inverse $\\frac{d}{c}$."
        ],
        "challenge": [
            "Simplify the complex fraction $\\frac{\\frac{3}{4} - \\frac{2}{3}}{\\frac{5}{6} + \\frac{1}{2}}$ using both the division method and the LCD clearing method.",
            "Solve $\\frac{3}{4}x - \\frac{2}{3} = \\frac{5}{12}$ and verify your solution."
        ]
    },
    "MTH-T01-C05": {
        "title": "Decimals",
        "objective": "Perform arithmetic on decimals, convert between fractions and decimals, solve decimal equations, and apply decimals to averages, probability, rates, and square roots.",
        "criteria": "Execute decimal computations, convert repeating/terminating decimals, and solve applied decimal equations.",
        "role": "Connects fractions to base-10 decimal expansions ($10^{-1}, 10^{-2}, \\dots$) and introduces foundational data analysis concepts (mean, median, mode, basic probability, unit rates, and radical approximations).",
        "source_section": "OpenStax Prealgebra 2e — Chapter 5: Decimals (Sections 5.1–5.7)",
        "concepts": [
            "Decimals as Base-10 Fractions: Every terminating decimal is a fraction whose denominator is a power of 10 ($0.375 = \\frac{375}{1000} = \\frac{3}{8}$).",
            "Alignment in Operations: Addition/subtraction aligns decimal points (matching powers of 10); multiplication sums the decimal places of the factors; division shifts the decimal point equally in divisor and dividend (multiplying by $\\frac{10^k}{10^k}$).",
            "Central Tendency & Basic Probability: Mean ($\\frac{\\sum x_i}{n}$), Median (middle value when sorted), Mode (most frequent), and theoretical probability $P(E) = \\frac{\\text{favorable outcomes}}{\\text{total outcomes}}$."
        ],
        "challenge": [
            "Compute $(-4.08) \\times 1.25$ and $14.76 \\div (-0.06)$ by hand.",
            "Solve $-0.4x + 1.85 = -2.35$ and verify by substitution."
        ]
    },
    "MTH-T01-C06": {
        "title": "Percents",
        "objective": "Convert among percents, decimals, and fractions, and solve percent change, tax, commission, discount, simple interest, and proportion applications.",
        "criteria": "Set up and solve financial and real-world percent equations accurately without confusing the base in percent change problems.",
        "role": "Applies fractional and decimal reasoning to normalized 'per hundred' ($\\% = \\frac{1}{100}$) comparisons used across finance, science, and statistics.",
        "source_section": "OpenStax Prealgebra 2e — Chapter 6: Percents (Sections 6.1–6.5)",
        "concepts": [
            "Percent Definition: $p\\% = \\frac{p}{100} = 0.01p$.",
            "The Fundamental Percent Equation: $\\text{Amount} = \\text{Percent} \\times \\text{Base}$ (or $\\frac{\\text{Amount}}{\\text{Base}} = \\frac{p}{100}$). Always identify the Base ('of what original quantity?') first.",
            "Simple Interest Model: $I = Prt$ and total maturity value $A = P(1 + rt)$, where $r$ is the annual rate in decimal form and $t$ is time in years."
        ],
        "challenge": [
            "Explain with a concrete calculation why increasing a price by $20\\%$ and then discounting the new price by $20\\%$ results in a net $4\\%$ loss rather than returning to the original price.",
            "Find the original pre-tax price of an item if the total price after $7\\%$ sales tax is $\\$588.50$."
        ]
    },
    "MTH-T01-C07": {
        "title": "Propotional & Radio",
        "objective": "Analyze ratios, unit rates, and proportions, and model both direct variation and inverse variation in real-world problems.",
        "criteria": "Distinguish direct vs. inverse proportion, solve rational proportions, and apply scaling to geometry and rates.",
        "role": "Deepens proportional reasoning beyond basic percents—bridging ratio comparisons to linear functions ($y = kx$, direct variation) and reciprocal relationships ($y = \\frac{k}{x}$, inverse variation).",
        "source_section": "OpenStax Prealgebra 2e — Sections 5.6 & 6.5 (Ratios, Rates, and Proportions) + Supplementary Direct & Inverse Variation Modules",
        "concepts": [
            "Ratios vs. Rates: A ratio compares two quantities of the same kind (dimensionless when units match); a rate compares quantities with different units (e.g., $\\text{km/h}$).",
            "Cross-Product Property of Proportions: For $b \\ne 0, d \\ne 0$, $\\frac{a}{b} = \\frac{c}{d} \\iff ad = bc$.",
            "Direct vs. Inverse Variation: In direct proportion, the ratio is constant ($\\frac{y}{x} = k \\implies y = kx$); in inverse proportion, the product is constant ($x \\cdot y = k \\implies y = \\frac{k}{x}$)."
        ],
        "challenge": [
            "Solve $\\frac{2x - 3}{6} = \\frac{x + 1}{4}$ and check for extraneous or invalid denominators.",
            "Compare a direct variation task (distance vs. time at constant speed) with an inverse variation task (number of workers vs. time to complete a fixed job)."
        ]
    },
    "MTH-T01-C08": {
        "title": "Exponents",
        "objective": "Derive and apply product, quotient, power, zero, and negative exponent laws, and compute with scientific notation.",
        "criteria": "Simplify multi-variable exponential expressions containing negative exponents and perform arithmetic in scientific notation.",
        "role": "Formalizes the laws of integer exponents ($a^n$ for $n \\in \\mathbb{Z}$), which underpin polynomial algebra (C13), radical/fractional exponents (C09), and scientific measurement in physics.",
        "source_section": "OpenStax Prealgebra 2e — Section 10.2 & 10.5 (Exponent Properties & Integer Exponents/Scientific Notation) + Dedicated Exponent Mastery Progression",
        "concepts": [
            "Core Laws of Exponents ($a, b \\ne 0$): Product Rule $a^m \\cdot a^n = a^{m+n}$; Quotient Rule $\\frac{a^m}{a^n} = a^{m-n}$; Power Rule $(a^m)^n = a^{mn}$; Power of a Product/Quotient $(ab)^n = a^n b^n$ and $\\left(\\frac{a}{b}\\right)^n = \\frac{a^n}{b^n}$.",
            "Zero & Negative Exponents from Pattern Continuity: Decreasing the exponent by 1 divides by the base $a$, so $a^0 = 1$ ($a \\ne 0$) and $a^{-n} = \\frac{1}{a^n}$.",
            "Normalized Scientific Notation: $a \\times 10^n$ where $1 \\le |a| < 10$ and $n \\in \\mathbb{Z}$."
        ],
        "challenge": [
            "Simplify $\\left(\\frac{-3x^{-2}y^4}{6x^3y^{-1}}\\right)^{-2}$ so that all exponents in the final answer are positive.",
            "Compute $\\frac{(4.8 \\times 10^{-5})(2.5 \\times 10^{11})}{6.0 \\times 10^{-3}}$ and express the result in normalized scientific notation."
        ]
    },
    "MTH-T01-C09": {
        "title": "Roots",
        "objective": "Evaluate and simplify square roots, cube roots, and higher radicals, connect radicals to fractional exponents, and apply root properties.",
        "criteria": "Simplify radical expressions using prime/perfect-power factoring and convert fluently between radicals and rational exponents.",
        "role": "Extends exponent laws from integers to rational numbers ($a^{m/n} = \\sqrt[n]{a^m}$) and introduces irrational numbers ($\\sqrt{2}, \\sqrt{3}$) needed for geometry (Pythagorean theorem) and algebra.",
        "source_section": "OpenStax Prealgebra 2e — Section 5.7 (Square Roots) & OpenStax Elementary Algebra Radical Extensions",
        "concepts": [
            "Principal Root Definition: $\\sqrt{a}$ denotes the non-negative number whose square is $a$ (so $\\sqrt{x^2} = |x|$). For odd index $n$, $\\sqrt[n]{a}$ is defined for all real $a$ and preserves sign ($\\sqrt[3]{-8} = -2$).",
            "Product & Quotient Properties of Radicals: $\\sqrt[n]{ab} = \\sqrt[n]{a}\\sqrt[n]{b}$ and $\\sqrt[n]{\\frac{a}{b}} = \\frac{\\sqrt[n]{a}}{\\sqrt[n]{b}}$ (Warning: $\\sqrt{a + b} \\ne \\sqrt{a} + \\sqrt{b}$!).",
            "Rational Exponents Bridge: $a^{1/n} = \\sqrt[n]{a}$ and $a^{m/n} = \\left(\\sqrt[n]{a}\\right)^m = \\sqrt[n]{a^m}$."
        ],
        "challenge": [
            "Simplify $\\sqrt{72x^5y^4}$ (assuming $x, y \\ge 0$) and $\\sqrt[3]{-54a^6b^4}$.",
            "Evaluate $27^{-2/3}$ and simplify $\\sqrt{3.6 \\times 10^{-5}}$ in normalized scientific notation."
        ]
    },
    "MTH-T01-C10": {
        "title": "The Properties of Real Numbers",
        "objective": "Classify real numbers into rational and irrational sets, apply field axioms (commutative, associative, distributive, identity, inverse, zero), and convert between measurement systems.",
        "criteria": "Classify real numbers accurately, justify algebraic simplifications by naming the exact axiom used, and perform dimensional analysis unit conversions.",
        "role": "Unifies all number types studied so far into the complete Real Number System ($\mathbb{R} = \\mathbb{Q} \\cup \\text{Irrationals}$) and formalizes the structural axioms that make algebraic manipulation legal.",
        "source_section": "OpenStax Prealgebra 2e — Chapter 7: The Properties of Real Numbers (Sections 7.1–7.5)",
        "concepts": [
            "Real Number Hierarchy: $\\mathbb{N} \\subset \\mathbb{W} \\subset \\mathbb{Z} \\subset \\mathbb{Q} \\subset \\mathbb{R}$. Rational numbers ($\mathbb{Q}$) have terminating or repeating decimal expansions; Irrational numbers ($\\sqrt{2}, \\pi$) have non-terminating, non-repeating expansions.",
            "Field Axioms: Commutative ($a+b=b+a, ab=ba$), Associative ($(a+b)+c=a+(b+c)$), Distributive ($a(b+c)=ab+ac$), Identities ($0$ for $+$, $1$ for $\\times$), and Inverses ($a+(-a)=0$, $a \\cdot \\frac{1}{a}=1$ for $a \\ne 0$).",
            "Dimensional Analysis (Unit Factor Method): Multiply by unit conversion fractions equal to $1$ arranged so unwanted units cancel diagonally."
        ],
        "challenge": [
            "Simplify $-3(2x - 5) - 4(x + 2)$ and annotate the exact real-number property used at each step.",
            "Convert $72\\text{ km/h}$ into $\\text{m/s}$ and $15\\text{ miles}$ into kilometers using dimensional analysis."
        ]
    },
    "MTH-T01-C11": {
        "title": "Solving Linear Equations",
        "objective": "Solve multi-step linear equations in one variable, including equations with variables on both sides, parentheses, fractions, and decimals.",
        "criteria": "Solve any first-degree equation in one variable systematically and classify conditional equations, identities, and contradictions.",
        "role": "Synthesizes integer, fraction, decimal, and real-number properties into a single universal algorithm for solving first-degree equations.",
        "source_section": "OpenStax Prealgebra 2e — Chapter 8: Solving Linear Equations (Sections 8.1–8.4)",
        "concepts": [
            "Equivalence-Preserving Transformations: Adding/subtracting the same expression or multiplying/dividing by the same nonzero constant on both sides preserves the solution set of an equation.",
            "Five-Step General Strategy: (1) Clear fractions/decimals by multiplying both sides by the LCD or $10^k$; (2) Distribute to clear parentheses and combine like terms on each side; (3) Collect variable terms on one side and constant terms on the other; (4) Isolate the variable by dividing by its coefficient; (5) Substitute into the original equation to verify.",
            "Solution Types: Conditional equation (1 unique solution), Identity (infinitely many solutions, simplifies to $a = a$), Contradiction (no solution, simplifies to $a = b$ with $a \\ne b$)."
        ],
        "challenge": [
            "Solve $\\frac{1}{3}(6x - 9) - \\frac{1}{2}(4x + 8) = \\frac{5}{6}x - 2$ by clearing fractions first.",
            "Construct one example each of a linear equation with one solution, infinitely many solutions, and no solution."
        ]
    },
    "MTH-T01-C12": {
        "title": "Math Models and Geometry",
        "objective": "Translate applied word problems, money/mixture problems, and 2D/3D geometric configurations into algebraic equations, and solve literal formulas for specified variables.",
        "criteria": "Set up and solve word problems, geometric area/volume/Pythagorean applications, and literal formula rearrangements.",
        "role": "Applies linear equation solving (C11) to real-world modeling, Euclidean geometry (angles, triangles, polygons, circles, 3D solids), and symbolic formula manipulation.",
        "source_section": "OpenStax Prealgebra 2e — Chapter 9: Math Models and Geometry (Sections 9.1–9.7)",
        "concepts": [
            "Algebraic Modeling Loop: Read -> Identify unknown & assign variable -> Translate relationships into an equation -> Solve -> Check units and physical reasonableness.",
            "Core Geometric Invariants: Complementary angles sum to $90^\\circ$; supplementary angles sum to $180^\\circ$; interior angles of a triangle sum to $180^\\circ$; Pythagorean Theorem $a^2 + b^2 = c^2$ for right triangles; similar triangles have proportional corresponding sides.",
            "Literal Equations (Solving Formulas): Isolate a target variable inside a multi-variable formula (e.g., solving $A = \\frac{1}{2}h(b_1 + b_2)$ for $b_1$) using the exact same inverse operations used for numerical equations."
        ],
        "challenge": [
            "Solve the trapezoid area formula $A = \\frac{1}{2}h(b_1 + b_2)$ for $b_1$, and the Celsius-Fahrenheit formula $F = \\frac{9}{5}C + 32$ for $C$.",
            "Find the total surface area and volume of a cylinder with radius $r = 4\\text{ cm}$ and height $h = 10\\text{ cm}$ in both exact $\\pi$ form and decimal approximation."
        ]
    },
    "MTH-T01-C13": {
        "title": "Polynomials",
        "objective": "Classify, add, subtract, multiply, and divide polynomials by monomials, work with integer exponents, and factor out the Greatest Common Factor (GCF).",
        "criteria": "Perform polynomial operations and GCF factoring accurately without sign or exponent-rule errors.",
        "role": "Generalizes base-10 place value into powers of a variable ($a_n x^n + \\dots + a_1 x + a_0$), laying the algebraic foundation for quadratics, functions, and calculus.",
        "source_section": "OpenStax Prealgebra 2e — Chapter 10: Polynomials (Sections 10.1–10.6)",
        "concepts": [
            "Polynomial Structure & Degree: A monomial is $ax^k$ ($k \\in \\{0, 1, 2, \\dots\\}$). Only like terms (identical variable parts and exponents) can be combined in addition/subtraction—exponents do NOT change when adding like terms!",
            "Distributive Multiplication & Special Products: Multiplying polynomials distributes every term of the first factor across every term of the second: $(a+b)(c+d) = ac + ad + bc + bd$, $(a+b)^2 = a^2 + 2ab + b^2$, and $(a-b)(a+b) = a^2 - b^2$.",
            "Factoring as Reverse Distribution: Factoring out the GCF reverses the distributive property: $ab + ac = a(b + c)$."
        ],
        "challenge": [
            "Expand and simplify $(3x - 4)^2 - (2x + 5)(2x - 5)$ without forgetting the middle term in $(3x - 4)^2$.",
            "Divide $\\frac{18x^4y^3 - 12x^3y^2 + 6x^2y}{-6x^2y}$ and factor $15a^3b^2 - 25a^2b^3 + 10a^2b^2$ completely using the GCF."
        ]
    },
    "MTH-T01-C14": {
        "title": "Graphs",
        "objective": "Plot points and linear equations on the rectangular coordinate plane, find x- and y-intercepts, and compute and interpret the slope of a line.",
        "criteria": "Graph any two-variable linear equation using point plotting, intercepts, and slope-intercept form ($y = mx + b$).",
        "role": "Connects symbolic algebra (two-variable linear equations $Ax + By = C$) to analytic geometry (lines in the Cartesian plane $\mathbb{R}^2$), introducing rate of change (slope $m$).",
        "source_section": "OpenStax Prealgebra 2e — Chapter 11: Graphs (Sections 11.1–11.4)",
        "concepts": [
            "Cartesian Coordinate Correspondence: Every ordered pair $(x, y)$ corresponds to a unique point in the plane, and the graph of an equation in $x$ and $y$ is the set of all points $(x, y)$ that make the equation true.",
            "Intercepts: The $x$-intercept occurs where $y = 0$ ($(a, 0)$); the $y$-intercept occurs where $x = 0$ ($(0, b)$).",
            "Slope as Constant Rate of Change: $m = \\frac{\\text{rise}}{\\text{run}} = \\frac{y_2 - y_1}{x_2 - x_1}$ ($x_2 \\ne x_1$). Horizontal lines ($y = b$) have slope $m = 0$; vertical lines ($x = a$) have undefined slope; slope-intercept form $y = mx + b$ immediately reveals slope $m$ and $y$-intercept $(0, b)$."
        ],
        "challenge": [
            "Given $3x - 4y = 12$, find its $x$-intercept, $y$-intercept, and slope, rewrite it in slope-intercept form $y = mx + b$, and find the equation of a line parallel to it passing through $(0, -5)$."
        ]
    }
}
