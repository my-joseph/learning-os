# -*- coding: utf-8 -*-
"""
Curriculum and Practice Guide Data for MTH-T01 Batch 3 (Chapters C10, C11, C13, C14: 30 Pages total).
Production-grade mathematical formulations, 4-category Practice Guides, Active Recall toggles with solutions.
"""

CHAPTER_DATA = {
    "MTH-T01-C10": {
        "title": "The Properties of Real Numbers",
        "objective": "Classify numbers across the real number system, master commutative, associative, distributive, identity, and inverse axioms, and apply dimensional analysis across unit systems.",
        "role": "Real number properties form the axiomatic bedrock of algebra. By formalizing operations over sets ($\\mathbb{N} \\subset \\mathbb{W} \\subset \\mathbb{Z} \\subset \\mathbb{Q} \\subset \\mathbb{R}$), learners gain the mathematical justification required to manipulate expressions, prove equivalence, and transition into abstract algebraic structures.",
        "invariants": [
            "Set Inclusion Hierarchy: $\\mathbb{N} \\subset \\mathbb{W} \\subset \\mathbb{Z} \\subset \\mathbb{Q} \\subset \\mathbb{R}$; every rational number is real, but not every real is rational.",
            "Commutative Axiom: Order of operands does not change sum or product: $a + b = b + a$ and $ab = ba$. (Does NOT hold for subtraction or division).",
            "Associative Axiom: Grouping of operands does not change sum or product: $(a + b) + c = a + (b + c)$ and $(ab)c = a(bc)$.",
            "Distributive Law: Multiplication distributes over addition: $a(b + c) = ab + ac$.",
            "Identities and Inverses: $a + 0 = a$ (Additive Identity), $a \\times 1 = a$ (Multiplicative Identity); $a + (-a) = 0$ (Additive Inverse), $a \\times \\frac{1}{a} = 1$ ($a \\neq 0$, Multiplicative Inverse)."
        ],
        "units": ["MTH-T01-C10-U01", "MTH-T01-C10-U02", "MTH-T01-C10-U03", "MTH-T01-C10-U04", "MTH-T01-C10-U05"],
        "practice_guide": {
            "conceptual": [
                "Explain why $\\sqrt{2}$ and $\\pi$ cannot be written as $\\frac{a}{b}$ ($a, b \\in \\mathbb{Z}, b \\neq 0$), and prove that their decimal expansions neither terminate nor repeat.",
                "Contrast the Associative Property (regrouping parentheses without moving terms) with the Commutative Property (reordering positions).",
                "Explain why division by zero is mathematically undefined using the definition of multiplicative inverse."
            ],
            "computational": [
                "Classify the following numbers into all applicable subsets of $\\mathbb{R}$: $-7, 0, \\frac{5}{8}, \\sqrt{16}, \\sqrt{17}, 0.\\overline{45}, -\\frac{24}{6}$.",
                "Simplify using properties: $48 \\cdot \\frac{3}{4} + 48 \\cdot \\frac{1}{4} = 48\\left(\\frac{3}{4} + \\frac{1}{4}\\right) = 48(1) = 48$.",
                "Convert 65 miles per hour to feet per second using multi-step dimensional analysis."
            ],
            "traps": [
                "Commutative Subtraction Fallacy: Assuming $a - b = b - a$ (e.g. $5 - 2 \\neq 2 - 5$). Subtraction is non-commutative.",
                "Distributive Sign Slip: Writing $-(3x - 5) = -3x - 5$ instead of $-3x + 5$ (negating every term).",
                "Conversion Inversion Trap: Multiplying by $\\frac{1\\text{ hr}}{60\\text{ min}}$ when hours need to cancel from the denominator."
            ],
            "real_world": [
                "Physics ([[PHY-T01]]): Dimensional analysis in kinematics conversions (m/s to km/h, g/cm³ to kg/m³).",
                "Software Engineering ([[PRG-T01]]): Type system hierarchies (e.g. `number` vs `BigInt` vs `Float64`), and floating-point associativity violations (`(a + b) + c != a + (b + c)`).",
                "Finance: Currency conversion pipelines using chained conversion factors."
            ]
        },
        "active_recall": [
            {
                "q": "What is the key structural difference between a Rational number and an Irrational number?",
                "a": "A rational number can be expressed as a ratio $\\frac{a}{b}$ of two integers ($b \\neq 0$), resulting in a decimal that either terminates or repeats periodically. An irrational number cannot be expressed as a fraction of integers, and its decimal expansion is non-terminating and non-repeating (e.g., $\\sqrt{2}, \\pi, e$)."
            },
            {
                "q": "Why is division by zero undefined in the real number system?",
                "a": "Division $a \\div b = c$ is defined as the unique number $c$ such that $c \\cdot b = a$. If $b = 0$ and $a \\neq 0$, $c \\cdot 0 = 0 \\neq a$, so no solution exists. If $a = 0$, any number $c$ satisfies $c \\cdot 0 = 0$, so no unique quotient exists."
            }
        ]
    },

    "MTH-T01-C11": {
        "title": "Solving Linear Equations",
        "objective": "Master algebraic equality axioms, isolate variables systematically using inverse operations, solve multi-step linear equations with fractions and decimals, and identify conditional, identity, and contradiction equations.",
        "role": "Linear equations are the core gateway to all higher mathematics and scientific computing. They translate verbal relationships into deterministic mathematical equality, establishing the inverse operations methodology used throughout algebra, calculus, physics, and algorithmic state updates.",
        "invariants": [
            "Addition & Subtraction Property of Equality: If $a = b$, then $a + c = b + c$ and $a - c = b - c$.",
            "Multiplication & Division Property of Equality: If $a = b$, then $ac = bc$ and $\\frac{a}{c} = \\frac{b}{c}$ ($c \\neq 0$).",
            "Conservation of Equality: Any transformation applied to the left-hand side must be applied identically to the entire right-hand side.",
            "Classification of Solutions: Conditional (exactly one solution $x = k$), Identity (infinitely many solutions, true for all real numbers $0 = 0$), Contradiction (no solution, impossible statement $0 = k$ where $k \\neq 0$)."
        ],
        "units": ["MTH-T01-C11-U01", "MTH-T01-C11-U02", "MTH-T01-C11-U03", "MTH-T01-C11-U04"],
        "practice_guide": {
            "conceptual": [
                "Explain the balance scale model of an equation and why multiplying both sides by zero destroys the equation's truth set.",
                "Describe how to distinguish an Identity ($0=0$, all real numbers) from a Contradiction ($0=5$, no solution) when isolating variables.",
                "Justify why clearing fractions using the Least Common Denominator (LCD) preserves the solution set of an equation."
            ],
            "computational": [
                "Solve: $4(2x - 3) - 5x = 3x - 12$ and classify the solution type.",
                "Solve with fractions: $\\frac{2}{3}x - \\frac{1}{4} = \\frac{5}{6}x + \\frac{1}{2}$ by clearing denominators via $\\text{LCD} = 12$.",
                "Solve with decimals: $0.15(x - 20) + 0.05x = 0.10(120)$ by clearing decimals ($\times 100$)."
            ],
            "traps": [
                "Selective Multiplication Trap: When multiplying by the LCD or 100 to clear fractions/decimals, failing to multiply terms that are already integers.",
                "Sign Distribution Trap: In $-2(x - 4)$, failing to distribute the negative sign to both terms (writing $-2x - 8$ instead of $-2x + 8$).",
                "Contradiction Misinterpretation: Interpreting $0 = 7$ as $x = 0$ rather than recognizing that no solution exists."
            ],
            "real_world": [
                "Physics ([[PHY-T01]]): Solving kinematics formulas ($v = v_0 + at$ for $t$, $F = ma$ for $m$).",
                "Programming ([[PRG-T01]]): Linear rate-limiting algorithms, binary search partition balancing, and progress bar calculations.",
                "Business: Break-even analysis equating total revenue to total fixed plus variable costs."
            ]
        },
        "active_recall": [
            {
                "q": "What are the systematic four steps for solving any multi-step linear equation?",
                "a": "1. Simplify each side independently (clear parentheses with distributive property, combine like terms, optionally clear fractions/decimals using LCD/powers of 10). 2. Collect variable terms on one side using addition/subtraction. 3. Collect constant terms on the opposite side. 4. Isolate the variable using multiplication or division. 5. Check the candidate solution in the original equation."
            },
            {
                "q": "What does it mean algebraically when all variable terms cancel out and you are left with -3 = -3?",
                "a": "It means the equation is an Identity. The statement is true for all real values of $x$. The solution set is all real numbers ($\\mathbb{R}$)."
            }
        ]
    },

    "MTH-T01-C13": {
        "title": "Polynomials",
        "objective": "Classify polynomials by degree and number of terms, master polynomial addition, subtraction, multiplication, and monomial division, apply negative and zero exponent rules, and introduce polynomial factoring.",
        "role": "Polynomials represent continuous algebraic expressions composed of variables, exponents, and coefficients. They generalize arithmetic into multi-term symbolic functions, serving as the core modeling language for quadratic dynamics, area expansion, physics projectile motion, and algorithm polynomial complexity ($O(n^k)$).",
        "invariants": [
            "Polynomial Definition: An algebraic expression consisting of variables with non-negative integer exponents and real coefficients: $\\sum_{i=0}^n a_i x^i$.",
            "Degree Invariant: The degree of a term is the sum of the exponents of its variables; the degree of a polynomial is the highest degree of any non-zero term.",
            "Like Terms Combination: Only terms with identical variable bases and identical exponents can be combined by adding their coefficients.",
            "Exponent Laws: $x^a \\cdot x^b = x^{a+b}$, $\\frac{x^a}{x^b} = x^{a-b}$ ($x \\neq 0$), $(x^a)^b = x^{ab}$, $x^0 = 1$ ($x \\neq 0$), $x^{-n} = \\frac{1}{x^n}$.",
            "FOIL & Distributive Extension: Every term of the first polynomial must multiply every term of the second polynomial: $(a+b)(c+d) = ac + ad + bc + bd$."
        ],
        "units": ["MTH-T01-C13-U01", "MTH-T01-C13-U02", "MTH-T01-C13-U03", "MTH-T01-C13-U04", "MTH-T01-C13-U05", "MTH-T01-C13-U06"],
        "practice_guide": {
            "conceptual": [
                "Explain why $\\frac{1}{x}$ and $\\sqrt{x}$ are NOT polynomials, referencing the definition of variable exponents.",
                "Prove why $x^0 = 1$ ($x \\neq 0$) using the Quotient Rule for exponents $\\frac{x^n}{x^n}$.",
                "Explain the geometric area model of binomial multiplication $(x + a)(x + b)$."
            ],
            "computational": [
                "Add and subtract: $(5x^2 - 3x + 7) - (2x^2 + 8x - 11) + (x^2 - 4)$.",
                "Multiply: $(3x - 5)(2x^2 + 4x - 6)$ and collect like terms in descending degree order.",
                "Divide monomial: $\\frac{24x^5y^3 - 16x^3y^2 + 8xy}{4xy}$.",
                "Factor greatest common factor (GCF): $18a^3b^2 - 27a^2b^3 + 9ab$."
            ],
            "traps": [
                "Exponent Addition in Polynomial Addition: Adding exponents when combining like terms (writing $3x^2 + 4x^2 = 7x^4$ instead of $7x^2$). Exponents change ONLY during multiplication!",
                "Freshman's Dream Fallacy: Writing $(a + b)^2 = a^2 + b^2$. The correct expansion is $a^2 + 2ab + b^2$ (do not forget the middle term!).",
                "Negative Sign Distribution in Subtraction: In $(3x^2 - 2) - (x^2 - 5x + 4)$, failing to distribute the negative to $-5x$ and $+4$."
            ],
            "real_world": [
                "Physics ([[PHY-T01]]): Position-time functions under constant acceleration $x(t) = x_0 + v_0 t + \\frac{1}{2}at^2$ (a quadratic polynomial).",
                "Computer Science ([[PRG-T01]]): Computational complexity classes (polynomial time $O(n^2), O(n^3)$ vs exponential time $O(2^n)$).",
                "Geometry: Formulas for surface area and volume of solids expressed as variable polynomials."
            ]
        },
        "active_recall": [
            {
                "q": "Why is (a + b)^2 NOT equal to a^2 + b^2?",
                "a": "Squaring a binomial means multiplying the binomial by itself: $(a + b)^2 = (a + b)(a + b)$. By the FOIL method, $(a+b)(a+b) = a^2 + ab + ba + b^2 = a^2 + 2ab + b^2$. Omitting the middle term $2ab$ loses the cross-product terms."
            },
            {
                "q": "What is the systematic process for factoring out the Greatest Common Factor (GCF) from a polynomial?",
                "a": "1. Find the numerical GCF of all integer coefficients. 2. For each variable common to all terms, identify the lowest exponent that appears. 3. Multiply the numerical GCF and variable factors to form the overall GCF monomial. 4. Divide each term of the polynomial by the GCF to write the factored expression as $\\text{GCF} \\cdot (\\text{quotient terms})$."
            }
        ]
    },

    "MTH-T01-C14": {
        "title": "Graphs",
        "objective": "Plot ordered pairs on the Cartesian coordinate plane, graph linear equations using tables, intercepts, and slope-intercept form ($y = mx + b$), interpret the rate of change slope ($m$), and identify parallel and perpendicular slopes.",
        "role": "Graphs bridge algebraic equations and geometric spatial intuition. The Cartesian coordinate plane maps pairs of numerical values to geometric points, transforming algebraic equations into geometric lines and curves. Graphing is foundational for physics trajectories, calculus derivatives, and data visualization in engineering.",
        "invariants": [
            "Cartesian Coordinate Axiom: Every ordered pair $(x, y)$ corresponds to exactly one point in the plane, divided into four quadrants by perpendicular axes intersecting at $(0, 0)$.",
            "Linear Equation Graph: The graph of any linear equation $Ax + By = C$ (where $A, B$ are not both zero) is a straight line representing all solutions $(x, y)$.",
            "Slope as Rate of Change: Slope $m = \\frac{\\Delta y}{\\Delta x} = \\frac{y_2 - y_1}{x_2 - x_1}$ measures the vertical change per unit horizontal change.",
            "Slope Invariants: Positive slope rises left-to-right; negative slope falls; horizontal line has slope $m = 0$ ($y = c$); vertical line has undefined slope ($x = c$).",
            "Parallel & Perpendicular Invariants: Parallel lines have equal slopes ($m_1 = m_2$); perpendicular lines have negative reciprocal slopes ($m_1 \\cdot m_2 = -1$)."
        ],
        "units": ["MTH-T01-C14-U01", "MTH-T01-C14-U02", "MTH-T01-C14-U03", "MTH-T01-C14-U04"],
        "practice_guide": {
            "conceptual": [
                "Explain why the slope of a vertical line is undefined, contrasting it with a horizontal line whose slope is zero.",
                "Describe the geometric meaning of the $x$-intercept (where $y = 0$) and the $y$-intercept (where $x = 0$).",
                "Explain why any point lying on a line must make the line's equation a true statement when substituted."
            ],
            "computational": [
                "Find the slope of the line passing through $(-3, 4)$ and $(5, -2)$: $m = \\frac{-2 - 4}{5 - (-3)} = \\frac{-6}{8} = -\\frac{3}{4}$.",
                "Find the $x$- and $y$-intercepts of $3x - 4y = 12$ and use them to graph the line.",
                "Graph $y = -\\frac{2}{3}x + 4$ using the $y$-intercept $(0, 4)$ and slope $m = -\\frac{2}{3}$.",
                "Determine whether the lines $2x + y = 6$ and $y = \\frac{1}{2}x - 3$ are parallel, perpendicular, or neither."
            ],
            "traps": [
                "Order of Subtraction in Slope Formula: Writing $m = \\frac{y_2 - y_1}{x_1 - x_2}$ (inconsistent order between numerator and denominator). Must maintain $(y_2 - y_1)/(x_2 - x_1)$.",
                "Inverted Slope Coordinates: Calculating $\\frac{\\Delta x}{\\Delta y}$ (run over rise) instead of $\\frac{\\Delta y}{\\Delta x}$ (rise over run).",
                "Intercept Coordinate Inversion: Writing the $x$-intercept as $(0, a)$ and $y$-intercept as $(b, 0)$ instead of $(a, 0)$ and $(0, b)$."
            ],
            "real_world": [
                "Physics ([[PHY-T01]]): Position-time graphs where slope = velocity ($v$), and velocity-time graphs where slope = acceleration ($a$).",
                "Data Science & Programming ([[PRG-T01]]): Linear regression models, line charts, SVG screen coordinates (noting inverted $y$-axis in computer graphics).",
                "Economics: Supply and demand curves, fixed cost vs marginal cost visualization."
            ]
        },
        "active_recall": [
            {
                "q": "Why is the slope of a horizontal line 0, while the slope of a vertical line is undefined?",
                "a": "For a horizontal line, $\\Delta y = 0$ while $\\Delta x \\neq 0$, so $m = \\frac{0}{\\Delta x} = 0$. For a vertical line, $\\Delta x = 0$, requiring division by zero ($m = \\frac{\\Delta y}{0}$), which is mathematically undefined."
            },
            {
                "q": "How do you graph a line in 30 seconds given its equation in slope-intercept form y = mx + b?",
                "a": "1. Plot the $y$-intercept at $(0, b)$. 2. Interpret slope $m = \\frac{\\text{rise}}{\\text{run}}$. From $(0, b)$, move vertically by 'rise' and horizontally by 'run' to plot a second point. 3. Draw a straight line passing through both points with arrows at each end."
            }
        ]
    }
}
