# -*- coding: utf-8 -*-
"""
Instructional content for MTH-T01 Units: C12 through C14 (17 Units).
Source: OpenStax Prealgebra 2e (Chapters 9, 10, 11).
"""

MTH_UNITS_D = {
    "MTH-T01-C12-U01": {
        "title": "Use a Problem Solving Strategy",
        "obj": "Apply a systematic 7-step algebraic modeling strategy to translate and solve number, consecutive-integer, and multi-quantity word problems.",
        "out": "Define variables explicitly, express secondary unknowns in terms of a single variable, and solve applied word problems.",
        "prereq": "MTH-T01-C11-U03 (Variables on Both Sides)",
        "source": "OpenStax Prealgebra 2e — Section 9.1: Use a Problem Solving Strategy (Verified HTTP 200).",
        "concepts": [
            "Expressing Multiple Unknowns with ONE Variable: When a problem involves two or three related unknowns, choose the base quantity as $x$ and express the others in terms of $x$ (e.g., if the Total is $T$, the two parts are $x$ and $T - x$; if $A$ is '$5$ less than twice $B$', let $B = x$ and $A = 2x - 5$).",
            "Consecutive Integer Models: Consecutive integers increase by $1$: $n,\\ n+1,\\ n+2$. Consecutive EVEN integers (or consecutive ODD integers!) BOTH increase by $2$: $n,\\ n+2,\\ n+4$.",
            "Answer the Actual Question Asked: Solving for $x$ is not always the final step—check whether the problem asked for $x$, $2x - 5$, or all three consecutive integers!"
        ],
        "equation": "\\text{Consecutive Integers: } n, n+1, n+2 \\qquad \\text{Consecutive Even/Odd: } n, n+2, n+4",
        "worked": "Example: The sum of three consecutive odd integers is $-87$. Find the three integers.\n1. Let $n =$ smallest odd integer; then the next two odd integers are $n + 2$ and $n + 4$.\n2. Equation: $n + (n + 2) + (n + 4) = -87 \\implies 3n + 6 = -87$.\n3. $3n = -93 \\implies n = -31$.\n4. The three odd integers are $-31,\\ -29,\\ -27$ (Sum $= -87$).",
        "exercises": [
            "The length of a rectangle is $4\\text{ cm}$ less than three times its width. If the perimeter is $64\\text{ cm}$, find the width and length.",
            "Find three consecutive even integers whose sum is $138$."
        ],
        "recall": [
            ("Why do consecutive ODD integers use $n,\\ n+2,\\ n+4$ instead of $n,\\ n+1,\\ n+3$?", "Because odd integers are spaced $2$ units apart on the number line (e.g., $5, 7, 9 = 5, 5+2, 5+4$). Adding $1$ to an odd integer makes it even!"),
            ("If two numbers have a sum of $50$ and you let the first number be $x$, how do you write the second number without introducing a second variable $y$?", "Write the second number as $50 - x$ (Total minus Part 1).")
        ]
    },
    "MTH-T01-C12-U02": {
        "title": "Solve Money Applications",
        "obj": "Distinguish between the quantity (count) of items and their monetary value to set up and solve coin, stamp, and ticket-sales mixture problems.",
        "out": "Construct Quantity-Value tables and solve linear equations for coin and ticket word problems.",
        "prereq": "MTH-T01-C11-U04, MTH-T01-C12-U01",
        "source": "OpenStax Prealgebra 2e — Section 9.2: Solve Money Applications (Verified HTTP 200).",
        "concepts": [
            "Quantity vs. Total Value Distinction: $7$ quarters is a QUANTITY (count $= 7$), whereas $7 \\times \\$0.25 = \\$1.75$ is their MONETARY VALUE. In general: $\\text{Total Value} = \\sum (\\text{Count}_i \\times \\text{Unit Value}_i)$.",
            "Two Relationships in Mixture Problems: (1) Total Count Relationship: if there are $40$ tickets in total and $x$ are adult tickets, then $(40 - x)$ are child tickets; (2) Total Value Equation: $v_1 x + v_2(40 - x) = V_{\\text{total}}$.",
            "Working in Integer Cents: Multiplying the value equation by $100$ expresses all prices in integer cents ($25x + 10(40-x) = 730$), eliminating decimal arithmetic."
        ],
        "equation": "V_{\\text{total}} = v_1 n_1 + v_2 n_2, \\qquad n_1 + n_2 = N_{\\text{total}} \\implies n_2 = N_{\\text{total}} - n_1",
        "worked": "Example: A cash box contains $32$ coins consisting of nickels ($\\$0.05$) and quarters ($\\$0.25$) worth a total of $\\$5.60$. How many of each coin are there?\n1. Let $q =$ number of quarters; then $32 - q =$ number of nickels.\n2. Value in cents: $25q + 5(32 - q) = 560$.\n3. $25q + 160 - 5q = 560 \\implies 20q = 400 \\implies q = 20$ quarters, and $32 - 20 = 12$ nickels.",
        "exercises": [
            "A theater sold $250$ tickets for a total revenue of $\\$2,650$. Adult tickets cost $\\$12$ and student tickets cost $\\$8$. Find how many of each ticket were sold.",
            "A jar has $9$ more dimes ($\\$0.10$) than nickels ($\\$0.05$). If the total value is $\\$4.65$, find the number of nickels and dimes."
        ],
        "recall": [
            ("What goes wrong if a student writes $n + q = 5.60$ when $n$ nickels and $q$ quarters are worth $\\$5.60$?", "They equated a pure count of coins ($n + q$) to a dollar value ($5.60$) without multiplying each coin count by its unit value ($0.05n + 0.25q = 5.60$)."),
            ("If a problem says 'there are $45$ coins in total' and you let $x$ be the number of dimes, why is the number of quarters $45 - x$ and not $x - 45$?", "Because the sum of the two counts is $45$ ($x + q = 45 \\implies q = 45 - x$); $x - 45$ would be negative since $x \\le 45$.")
        ]
    },
    "MTH-T01-C12-U03": {
        "title": "Use Properties of Angles, Triangles, and the Pythagorean Theorem",
        "obj": "Solve geometric problems using complementary/supplementary angles, the $180^\\circ$ triangle angle-sum theorem, similar triangles, and the Pythagorean Theorem ($a^2 + b^2 = c^2$).",
        "out": "Calculate missing angles and side lengths in right and similar triangles.",
        "prereq": "MTH-T01-C07-U06, MTH-T01-C09-U02, MTH-T01-C12-U01",
        "source": "OpenStax Prealgebra 2e — Section 9.3: Use Properties of Angles, Triangles, and the Pythagorean Theorem (Verified HTTP 200).",
        "concepts": [
            "Angle Pair Invariants: Complementary angles sum to $90^\\circ$ (if one is $x$, its complement is $90^\\circ - x$). Supplementary angles sum to $180^\\circ$ (if one is $x$, its supplement is $180^\\circ - x$).",
            "Triangle Angle-Sum Theorem: The sum of the measures of the three interior angles of any triangle in the Euclidean plane is $A + B + C = 180^\\circ$.",
            "Pythagorean Theorem for Right Triangles: In any right triangle with legs $a, b$ and hypotenuse $c$ (the longest side, opposite the $90^\\circ$ angle), $a^2 + b^2 = c^2$. Thus $c = \\sqrt{a^2 + b^2}$ and $a = \\sqrt{c^2 - b^2}$."
        ],
        "equation": "A + B + C = 180^\\circ, \\qquad a^2 + b^2 = c^2 \\implies c = \\sqrt{a^2 + b^2},\\quad a = \\sqrt{c^2 - b^2}",
        "worked": "Example: (a) Find the angle that is $15^\\circ$ more than twice its complement. (b) Find the unknown leg $a$ of a right triangle with hypotenuse $c = 17$ and leg $b = 15$.\n1. (a) Let complement $= x$; angle $= 2x + 15$. Sum: $x + (2x + 15) = 90 \\implies 3x = 75 \\implies x = 25^\\circ$, so the angle is $65^\\circ$.\n2. (b) $a^2 + 15^2 = 17^2 \\implies a^2 + 225 = 289 \\implies a^2 = 64 \\implies a = 8$.",
        "exercises": [
            "In a triangle, the second angle is three times the first angle, and the third angle is $20^\\circ$ more than the first angle. Find all three angles.",
            "A $13\\text{ m}$ ladder leans against a vertical wall with its base $5\\text{ m}$ from the wall. How high up the wall does the ladder reach?"
        ],
        "recall": [
            ("In the Pythagorean Theorem $a^2 + b^2 = c^2$, which side of the right triangle MUST be substituted for $c$?", "$c$ must always be the hypotenuse—the longest side located directly opposite the $90^\\circ$ right angle."),
            ("What are the two most common integer Pythagorean triples $(a, b, c)$ worth recognizing instantly?", "$(3, 4, 5)$ (and its multiples like $(6, 8, 10)$, $(9, 12, 15)$) and $(5, 12, 13)$ (plus $(8, 15, 17)$).")
        ]
    },
    "MTH-T01-C12-U04": {
        "title": "Use Properties of Rectangles, Triangles, and Trapezoids",
        "obj": "Derive and apply perimeter and area formulas for rectangles ($A = lw$), triangles ($A = \\frac{1}{2}bh$), and trapezoids ($A = \\frac{1}{2}h(b_1 + b_2)$).",
        "out": "Compute areas, perimeters, and missing dimensions of polygonal figures with correct 1D vs. 2D units.",
        "prereq": "MTH-T01-C11-U04, MTH-T01-C12-U03",
        "source": "OpenStax Prealgebra 2e — Section 9.4: Use Properties of Rectangles, Triangles, and Trapezoids (Verified HTTP 200).",
        "concepts": [
            "Geometric Intuition of the Area Formulas: A rectangle of base $b$ and height $h$ has area $A = bh$. Any triangle of base $b$ and perpendicular height $h$ is exactly half of a parallelogram/rectangle: $A = \\frac{1}{2}bh$. A trapezoid with parallel bases $b_1, b_2$ and perpendicular height $h$ averages the two bases: $A = \\left(\\frac{b_1 + b_2}{2}\\right)h$.",
            "Perpendicular Height ($h$) vs. Slanted Side Lengths: In both triangles and trapezoids, the height $h$ used in the area formula is the PERPENDICULAR distance between the base and opposite vertex/base—whereas perimeter sums the outer boundary side lengths!",
            "Dimensional Consistency: Perimeter has linear units ($\\text{cm, m, ft}$); Area has square units ($\\text{cm}^2, \\text{m}^2, \\text{ft}^2$)."
        ],
        "equation": "A_{\\text{rect}} = lw,\\quad P_{\\text{rect}} = 2l + 2w, \\qquad A_{\\text{tri}} = \\frac{1}{2}bh, \\qquad A_{\\text{trap}} = \\frac{1}{2}h(b_1 + b_2)",
        "worked": "Example: A trapezoid has area $84\\text{ cm}^2$, height $h = 7\\text{ cm}$, and one base $b_1 = 10\\text{ cm}$. Find the other parallel base $b_2$.\n1. Substitute into $A = \\frac{1}{2}h(b_1 + b_2)$: $84 = \\frac{1}{2}(7)(10 + b_2)$.\n2. Multiply both sides by $2$: $168 = 7(10 + b_2)$.\n3. Divide by $7$: $24 = 10 + b_2 \\implies b_2 = 14\\text{ cm}$.",
        "exercises": [
            "A triangle has area $54\\text{ m}^2$ and base $12\\text{ m}$. Find its height $h$.",
            "Find the area and perimeter of an isosceles trapezoid with parallel bases $12\\text{ cm}$ and $20\\text{ cm}$, perpendicular height $3\\text{ cm}$, and slanted legs of $5\\text{ cm}$ each."
        ],
        "recall": [
            ("Why is the area of a trapezoid $A = \\frac{1}{2}h(b_1 + b_2)$ naturally understood as 'average base times height'?", "Because $\\frac{b_1 + b_2}{2}$ is the arithmetic mean (midsegment length) of the two parallel bases; multiplying by perpendicular height $h$ converts the trapezoid into an equivalent rectangle."),
            ("When computing the area of a non-right triangle, why do you ignore the slanted side lengths and use the altitude $h$ instead?", "Because area measures perpendicular 2D coverage ($\\frac{1}{2} \\times \\text{base} \\times \\text{perpendicular height}$); slanted sides are only used when computing perimeter.")
        ]
    },
    "MTH-T01-C12-U05": {
        "title": "Solve Geometry Applications: Circles and Irregular Figures",
        "obj": "Calculate circumference ($C = 2\\pi r = \\pi d$) and area ($A = \\pi r^2$) of circles in both exact $\\pi$ form and decimal approximations, and find areas of composite/shaded figures.",
        "out": "Compute exact and approximate circular measurements and decompose irregular composite shapes into rectangles, triangles, and semicircles.",
        "prereq": "MTH-T01-C10-U01, MTH-T01-C12-U04",
        "source": "OpenStax Prealgebra 2e — Section 9.5: Solve Geometry Applications: Circles and Irregular Figures (Verified HTTP 200).",
        "concepts": [
            "Radius, Diameter, and $\\pi$: $d = 2r$ (so $r = \\frac{d}{2}$). The irrational constant $\\pi = \\frac{C}{d} \\approx 3.14159\\dots$ is the invariant ratio of any circle's circumference to its diameter.",
            "Circumference vs. Area (Don't Swap Them!): Circumference (1D perimeter) is $C = \\pi d = 2\\pi r$ (linear units). Area (2D interior) is $A = \\pi r^2$ (square units). Always halve the diameter to get $r$ BEFORE squaring in $A = \\pi r^2$!",
            "Composite & Shaded Figures by Addition/Subtraction: Decompose irregular shapes into non-overlapping rectangles, triangles, and semicircles ($\\frac{1}{2}\\pi r^2$), or compute $\\text{Area}_{\\text{shaded}} = \\text{Area}_{\\text{outer}} - \\text{Area}_{\\text{cutout}}$."
        ],
        "equation": "d = 2r, \\qquad C = 2\\pi r = \\pi d, \\qquad A = \\pi r^2",
        "worked": "Example: A running track consists of a $100\\text{ m}$ by $60\\text{ m}$ rectangle with a semicircle at each $60\\text{ m}$ end. Find the exact and approximate ($\\pi \\approx 3.14$) perimeter and total area.\n1. Two semicircles of diameter $d = 60\\text{ m}$ ($r = 30\\text{ m}$) form one full circle!\n2. Perimeter $= 2(100) + \\pi(60) = 200 + 60\\pi\\text{ m} \\approx 388.4\\text{ m}$.\n3. Area $= (100)(60) + \\pi(30)^2 = 6000 + 900\\pi\\text{ m}^2 \\approx 8,826\\text{ m}^2$.",
        "exercises": [
            "A circle has diameter $d = 18\\text{ cm}$. Find its exact circumference and exact area in terms of $\\pi$, and approximate both to 2 decimal places.",
            "A circular fountain of radius $4\\text{ m}$ sits inside a square courtyard of side $12\\text{ m}$. Find the area of the courtyard surrounding the fountain."
        ],
        "recall": [
            ("When computing the perimeter of a semicircle of radius $r$, why is the answer $\\pi r + 2r$ and NOT just $\\pi r$?", "Because $\\pi r = \\frac{1}{2}(2\\pi r)$ is only the curved arc; the closed boundary of a semicircle also includes the straight diameter of length $d = 2r$."),
            ("What common mistake happens when finding the area of a circle given diameter $d = 10$?", "Plugging $10$ directly into $\\pi r^2$ to get $100\\pi$ instead of first dividing the diameter by $2$ to get radius $r = 5 \\implies A = 25\\pi$.")
        ]
    },
    "MTH-T01-C12-U06": {
        "title": "Solve Geometry Applications: Volume and Surface Area",
        "obj": "Compute Volume ($V$) and Total/Lateral Surface Area ($SA$) of rectangular solids, cubes, spheres, cylinders, and cones.",
        "out": "Distinguish 2D surface area ($\\text{units}^2$) from 3D volume ($\\text{units}^3$) and evaluate solid geometry formulas.",
        "prereq": "MTH-T01-C12-U04, MTH-T01-C12-U05",
        "source": "OpenStax Prealgebra 2e — Section 9.6: Solve Geometry Applications: Volume and Surface Area (Verified HTTP 200).",
        "concepts": [
            "Surface Area (2D Wrapper) vs. Volume (3D Capacity): Surface area sums the areas of all outer faces/surfaces (measured in square units, $\\text{m}^2$). Volume measures 3D space enclosed (measured in cubic units, $\\text{m}^3$).",
            "Prisms & Cylinders ('Base Area times Height'): For any right prism or cylinder with constant cross-sectional base area $B$ and height $h$, $V = B \\cdot h$. Thus a rectangular box has $V = lwh$ and $SA = 2(lw + lh + wh)$; a right circular cylinder has $V = \\pi r^2 h$ and total surface area $SA = 2\\pi r^2 + 2\\pi r h$ (two circular caps + unrolled rectangular side of width $2\\pi r$).",
            "Spheres & Cones: Sphere of radius $r$: $V = \\frac{4}{3}\\pi r^3$ and $SA = 4\\pi r^2$. Cone of radius $r$ and height $h$: $V = \\frac{1}{3}\\pi r^2 h$ (exactly one-third of the enclosing cylinder!)."
        ],
        "equation": "V_{\\text{cyl}} = \\pi r^2 h,\\quad SA_{\\text{cyl}} = 2\\pi r^2 + 2\\pi rh, \\qquad V_{\\text{sphere}} = \\frac{4}{3}\\pi r^3, \\qquad V_{\\text{cone}} = \\frac{1}{3}\\pi r^2 h",
        "worked": "Example: Find the exact volume and total surface area of a closed cylinder with radius $r = 5\\text{ cm}$ and height $h = 12\\text{ cm}$.\n1. Volume: $V = \\pi (5)^2 (12) = 300\\pi\\text{ cm}^3$.\n2. Total Surface Area: $SA = 2\\pi(5)^2 + 2\\pi(5)(12) = 50\\pi + 120\\pi = 170\\pi\\text{ cm}^2$.",
        "exercises": [
            "Find the volume and surface area of a rectangular shipping container measuring $6\\text{ m}$ by $2.5\\text{ m}$ by $3\\text{ m}$.",
            "Find the exact volume of (a) a sphere of radius $6\\text{ cm}$ and (b) a cone of radius $6\\text{ cm}$ and height $10\\text{ cm}$."
        ],
        "recall": [
            ("Why is the lateral (side) surface area of a cylinder equal to $2\\pi r h$?", "If you cut the curved side of a cylinder vertically and unroll it flat, it forms a rectangle whose width is the circle's circumference $2\\pi r$ and whose height is $h$."),
            ("How is the volume of a cone related to the volume of a cylinder with the exact same radius $r$ and height $h$?", "The volume of the cone is exactly one-third the volume of the cylinder: $V_{\\text{cone}} = \\frac{1}{3}\\pi r^2 h$.")
        ]
    },
    "MTH-T01-C12-U07": {
        "title": "Solve a Formula for a Specific Variable",
        "obj": "Use the distance-rate-time formula ($d = rt$) and rearrange multi-variable literal equations (formulas) to isolate any specified variable.",
        "out": "Manipulate symbolic formulas in geometry, physics, and finance to solve for a target variable.",
        "prereq": "MTH-T01-C11-U04 (Solving Linear Equations)",
        "source": "OpenStax Prealgebra 2e — Section 9.7: Solve a Formula for a Specific Variable (Verified HTTP 200).",
        "concepts": [
            "Literal Equations Treat Other Variables as Constants: Solving $A = P + Prt$ for $t$ uses the exact same steps as solving $100 = 80 + 4t$ for $t$: subtract $P$ first ($A - P = Prt$), then divide by the coefficient $Pr$ multiplying $t$ ($t = \\frac{A - P}{Pr}$).",
            "Clearing Fractions Before Isolating: If the target variable is inside a fraction or parentheses (such as $b_2$ in $A = \\frac{1}{2}h(b_1 + b_2)$), multiply both sides by $2$ first ($2A = h(b_1 + b_2)$), divide by $h$ ($\\frac{2A}{h} = b_1 + b_2$), and subtract $b_1$.",
            "Why Rearranging Formulas First Matters in Engineering & Physics: Solving symbolically once lets you see how output scales with each parameter and prevents intermediate rounding errors."
        ],
        "equation": "A = \\frac{1}{2}h(b_1 + b_2) \\implies 2A = h(b_1 + b_2) \\implies \\frac{2A}{h} - b_1 = b_2",
        "worked": "Example: Solve the linear standard-form equation $4x - 3y = 18$ for $y$, and solve $S = 2lw + 2lh + 2wh$ for $h$.\n1. For $4x - 3y = 18$: subtract $4x \\implies -3y = -4x + 18$; divide every term by $-3 \\implies y = \\frac{4}{3}x - 6$.\n2. For $S = 2lw + 2h(l + w)$: subtract $2lw \\implies S - 2lw = 2h(l + w) \\implies h = \\frac{S - 2lw}{2(l + w)}$.",
        "exercises": [
            "Solve each formula for the indicated variable: (a) $V = \\frac{1}{3}\\pi r^2 h$ for $h$, (b) $P = 2l + 2w$ for $w$, (c) $3x + 5y = 20$ for $y$.",
            "Solve the kinematic equation $v = v_0 + at$ for $a$."
        ],
        "recall": [
            ("When solving $P = 2l + 2w$ for $w$, why is $w = \\frac{P - 2l}{2}$ equivalent to $w = \\frac{P}{2} - l$, and NOT $P - l$?", "Dividing the entire numerator $P - 2l$ by $2$ divides BOTH terms by $2$: $\\frac{P}{2} - \\frac{2l}{2} = \\frac{P}{2} - l$. Canceling $2$ from only one term is an illegal partial cancellation."),
            ("What should you do when the variable you are solving for appears in two terms, such as solving $A = P + Prt$ for $P$?", "Factor out the target variable $P$ using the Distributive Property in reverse: $A = P(1 + rt)$, then divide both sides by $(1 + rt)$ to get $P = \\frac{A}{1 + rt}$.")
        ]
    },
    "MTH-T01-C13-U01": {
        "title": "Add and Subtract Polynomials",
        "obj": "Classify monomials, binomials, trinomials, and polynomials, determine the degree of a polynomial, and add/subtract polynomials by combining like terms.",
        "out": "Add and subtract multi-term polynomials written in standard descending-degree form and evaluate polynomial functions.",
        "prereq": "MTH-T01-C02-U02, MTH-T01-C10-U03",
        "source": "OpenStax Prealgebra 2e — Section 10.1: Add and Subtract Polynomials (Verified HTTP 200).",
        "concepts": [
            "Definitions & Classification: A monomial has 1 term ($cx^k$, where $k \\in \\{0, 1, 2, \\dots\\}$); a binomial has 2 terms; a trinomial has 3 terms. The degree of a term is the sum of the exponents of its variables; the degree of a polynomial is the HIGHEST degree among all its nonzero terms.",
            "Standard Form of a Polynomial: Write terms in descending order of degree (e.g., $4x^3 - 7x^2 + x - 9$).",
            "Subtracting Polynomials Requires Distributing $-1$: In $(5x^2 - 3x + 4) - (2x^2 - 8x - 1)$, rewrite the subtraction by flipping the sign of EVERY term inside the second polynomial: $5x^2 - 3x + 4 - 2x^2 + 8x + 1 = 3x^2 + 5x + 5$."
        ],
        "equation": "(A) - (B - C + D) = A - B + C - D, \\qquad ax^n + bx^n = (a + b)x^n",
        "worked": "Example: Subtract $(3x^3 - 5x^2 + 4)$ from $(7x^3 - 2x^2 - 6x + 1)$ and state the degree of the result.\n1. Setup ('subtract A from B' means $B - A$): $(7x^3 - 2x^2 - 6x + 1) - (3x^3 - 5x^2 + 4)$.\n2. Distribute $-1$: $7x^3 - 2x^2 - 6x + 1 - 3x^3 + 5x^2 - 4$.\n3. Combine like terms in descending order: $4x^3 + 3x^2 - 6x - 3$ (Degree $= 3$).",
        "exercises": [
            "Simplify and write in standard form: $(6y^3 - 4y + 9) - (2y^3 - 5y^2 - 4y + 11)$.",
            "Evaluate the height polynomial $h(t) = -16t^2 + 64t + 80$ at $t = 3$ seconds."
        ],
        "recall": [
            ("Why is the degree of the polynomial $5x^4 - 3x^2 + 8x - 1$ equal to $4$ and not $4 + 2 + 1 = 7$?", "The degree of a polynomial in one variable is the MAXIMUM degree of any single term ($4$), not the sum of the degrees of all terms."),
            ("When adding $4x^3 + 5x^3 = 9x^3$, why does the exponent stay $3$ instead of becoming $6$?", "Adding like terms uses the Distributive Property $(4 + 5)x^3 = 9x^3$; only multiplying $x^3 \\cdot x^3$ adds exponents.")
        ]
    },
    "MTH-T01-C13-U02": {
        "title": "Use Multiplication Properties of Exponents",
        "obj": "Apply the Product Property, Power Property, and Product-to-a-Power Property of Exponents in combination to multiply algebraic monomials.",
        "out": "Simplify multi-step monomial products involving nested powers and signed coefficients.",
        "prereq": "MTH-T01-C08-U02, MTH-T01-C08-U04, MTH-T01-C13-U01",
        "source": "OpenStax Prealgebra 2e — Section 10.2: Use Multiplication Properties of Exponents (Verified HTTP 200).",
        "concepts": [
            "Combined Exponent Rules for Polynomial Multiplication: (1) Product Rule: $a^m \\cdot a^n = a^{m+n}$; (2) Power Rule: $(a^m)^n = a^{mn}$; (3) Product-to-a-Power: $(ab)^n = a^n b^n$.",
            "Order of Operations on Monomial Products: When simplifying $(-2x^3y)^3 (5xy^4)^2$, evaluate the outer powers FIRST via $(ab)^n = a^n b^n$ and $(a^m)^n = a^{mn}$, and then multiply the resulting monomials via $a^m \\cdot a^n = a^{m+n}$.",
            "Sign Discipline on Coefficients: $(-2)^3 = -8$ (odd power keeps negative), while $(-2)^4 = +16$ (even power becomes positive)."
        ],
        "equation": "(c_1 x^a y^b)^m (c_2 x^c y^d)^n = (c_1^m c_2^n) x^{am + cn} y^{bm + dn}",
        "worked": "Example: Simplify $(-3a^2b^4)^3 (-2ab^3)^2$.\n1. Apply outer powers first: $(-3)^3 (a^2)^3 (b^4)^3 = -27a^6b^{12}$, and $(-2)^2 a^2 (b^3)^2 = 4a^2b^6$.\n2. Multiply coefficients and add exponents of like bases: $(-27)(4) a^{6+2} b^{12+6} = -108a^8b^{18}$.",
        "exercises": [
            "Simplify: (a) $(4x^5y^2)(-3x^2y^6)$, (b) $(-2m^3n)^4 (3m^2n^5)^2$.",
            "Simplify $3x^2(2x^3)^4 - (2x^7)^2$ (combine like terms at the end!)."
        ],
        "recall": [
            ("In $3x^2(2x^3)^4$, why can't you multiply $3x^2 \\cdot 2x^3 = 6x^5$ before raising to the $4$th power?", "By the Order of Operations, exponentiation has higher precedence than multiplication; the exponent $4$ applies only to $(2x^3)$, yielding $3x^2(16x^{12}) = 48x^{14}$."),
            ("What is the difference between $(-5x^2)^2$ and $-5(x^2)^2$?", "In $(-5x^2)^2$, the base includes $-5$, so $(-5)^2 x^4 = 25x^4$. In $-5(x^2)^2$, only $x^2$ is squared, giving $-5x^4$.")
        ]
    },
    "MTH-T01-C13-U03": {
        "title": "Multiply Polynomials",
        "obj": "Multiply a polynomial by a monomial, multiply two binomials using distribution/FOIL/area models, and expand special products and general polynomial products.",
        "out": "Expand binomial and trinomial products accurately without dropping cross-terms.",
        "prereq": "MTH-T01-C13-U01, MTH-T01-C13-U02",
        "source": "OpenStax Prealgebra 2e — Section 10.3: Multiply Polynomials (Verified HTTP 200).",
        "concepts": [
            "Monomial $\\times$ Polynomial: Distribute the outside monomial to every term inside the parentheses: $a(b + c + d) = ab + ac + ad$.",
            "Binomial $\\times$ Binomial (Double Distribution / FOIL): $(a + b)(c + d) = a(c + d) + b(c + d) = ac + ad + bc + bd$ (First, Outer, Inner, Last).",
            "Special Binomial Products (Memorize & Understand!): (1) Binomial Square: $(a + b)^2 = a^2 + 2ab + b^2$ and $(a - b)^2 = a^2 - 2ab + b^2$ (NEVER forget the middle cross-term $\\pm 2ab$!); (2) Conjugate Product (Difference of Squares): $(a - b)(a + b) = a^2 - b^2$ (outer and inner terms $+ab - ab = 0$ cancel!)."
        ],
        "equation": "(a \\pm b)^2 = a^2 \\pm 2ab + b^2, \\qquad (a - b)(a + b) = a^2 - b^2",
        "worked": "Example: Multiply (a) $(3x - 5)(2x + 7)$, (b) $(4x - 3)^2$, and (c) $(x - 2)(x^2 + 3x - 4)$.\n1. (a) $6x^2 + 21x - 10x - 35 = 6x^2 + 11x - 35$.\n2. (b) $(4x)^2 - 2(4x)(3) + 3^2 = 16x^2 - 24x + 9$.\n3. (c) Distribute $x$ and $-2$: $x(x^2 + 3x - 4) - 2(x^2 + 3x - 4) = x^3 + 3x^2 - 4x - 2x^2 - 6x + 8 = x^3 + x^2 - 10x + 8$.",
        "exercises": [
            "Expand and simplify: (a) $(5y - 4)(2y - 3)$, (b) $(3m + 7)(3m - 7)$, (c) $(2x - 5)^2$.",
            "Multiply $(2x + 3)(x^2 - 4x + 5)$ and verify that $2 \\times 3 = 6$ raw products are generated before combining like terms."
        ],
        "recall": [
            ("Why does $(a - b)(a + b)$ simplify to a two-term binomial $a^2 - b^2$, whereas $(a - b)^2$ simplifies to a three-term trinomial $a^2 - 2ab + b^2$?", "In $(a - b)(a + b)$, the cross terms $+ab$ and $-ab$ have opposite signs and cancel to $0$. In $(a - b)(a - b)$, both cross terms are $-ab$, which add to $-2ab$."),
            ("If you multiply a polynomial with $m$ terms by a polynomial with $n$ terms, how many individual product terms are produced before combining like terms?", "Exactly $m \\cdot n$ terms (every term of the first polynomial multiplies every term of the second).")
        ]
    },
    "MTH-T01-C13-U04": {
        "title": "Divide Monomials",
        "obj": "Simplify quotients of monomials using the Quotient and Power Properties of Exponents, and divide a polynomial by a monomial by splitting the fraction.",
        "out": "Divide multi-variable monomials and polynomials by a monomial accurately.",
        "prereq": "MTH-T01-C08-U03, MTH-T01-C13-U02",
        "source": "OpenStax Prealgebra 2e — Section 10.4: Divide Monomials (Verified HTTP 200).",
        "concepts": [
            "Monomial Division Review: Divide numerical coefficients as a fraction and subtract exponents of matching variable bases ($\\frac{a^m}{a^n} = a^{m-n}$ or $\\frac{1}{a^{n-m}}$).",
            "Dividing a Polynomial by a Monomial: Since $\\frac{a + b - c}{d} = \\frac{a}{d} + \\frac{b}{d} - \\frac{c}{d}$ ($d \\ne 0$), divide EVERY term of the numerator polynomial separately by the monomial denominator.",
            "Self-Division Term Equals $\\pm 1$, Never Disappears: When the last term in the numerator equals the monomial denominator, e.g., $\\frac{12x^2 - 6x}{6x} = \\frac{12x^2}{6x} - \\frac{6x}{6x} = 2x - 1$ (NEVER drop the $-1$!)."
        ],
        "equation": "\\frac{A + B - C}{D} = \\frac{A}{D} + \\frac{B}{D} - \\frac{C}{D} \\quad (D \\ne 0)",
        "worked": "Example: Divide $\\frac{24x^4y^2 - 16x^3y + 8x^2y}{ -8x^2y }$.\n1. Split into three separate monomial quotients:\n   $\\frac{24x^4y^2}{-8x^2y} - \\frac{16x^3y}{-8x^2y} + \\frac{8x^2y}{-8x^2y}$.\n2. Simplify each term (watch signs and note the last term is $-1$):\n   $-3x^2y + 2x - 1$.",
        "exercises": [
            "Simplify: $\\frac{-45a^6b^4}{27a^2b^7}$.",
            "Divide: $\\frac{15m^5 - 25m^3 + 5m^2}{5m^2}$ and verify your answer by multiplying the result by $5m^2$."
        ],
        "recall": [
            ("Why is $\\frac{10x^3 + 5x}{5x} = 2x^2 + 1$ and NOT $2x^2$?", "Because $\\frac{10x^3 + 5x}{5x} = \\frac{10x^3}{5x} + \\frac{5x}{5x}$, and any nonzero expression divided by itself equals $1$ (if it were $2x^2$, multiplying back by $5x$ would only give $10x^3$)."),
            ("Why is $\\frac{a + b}{c} = \\frac{a}{c} + \\frac{b}{c}$ valid, whereas $\\frac{c}{a + b} \\ne \\frac{c}{a} + \\frac{c}{b}$?", "Because division by $c$ is multiplication by $\\frac{1}{c}$, which distributes over $a + b$. A denominator sum $a + b$ cannot be split into separate denominators.")
        ]
    },
    "MTH-T01-C13-U05": {
        "title": "Integer Exponents and Scientific Notation",
        "obj": "Apply all exponent rules seamlessly across positive, zero, and negative integer exponents, and perform scientific notation calculations in algebraic contexts.",
        "out": "Simplify rational algebraic expressions containing negative integer exponents and scientific notation.",
        "prereq": "MTH-T01-C08-U05, MTH-T01-C08-U06, MTH-T01-C13-U04",
        "source": "OpenStax Prealgebra 2e — Section 10.5: Integer Exponents and Scientific Notation (Verified HTTP 200).",
        "concepts": [
            "Unified Integer Exponent Laws ($m, n \\in \\mathbb{Z},\\ a, b \\ne 0$): Once zero and negative exponents are defined ($a^0 = 1, a^{-n} = \\frac{1}{a^n}$), all five exponent rules ($a^m a^n = a^{m+n}$, $\\frac{a^m}{a^n} = a^{m-n}$, $(a^m)^n = a^{mn}$, $(ab)^n = a^n b^n$, $(\\frac{a}{b})^n = \\frac{a^n}{b^n}$) hold for ANY integers $m$ and $n$ without case-splitting!",
            "Avoid Moving Terms inside Sums: Remember that $x^{-1} + y^{-1} = \\frac{1}{x} + \\frac{1}{y} = \\frac{x + y}{xy} \\ne \\frac{1}{x + y}$. You can only flip factors across the main fraction bar when they are multiplied, not added!",
            "Scientific Notation in Engineering Formulas: Express constants in $a \\times 10^n$ form to prevent decimal-counting errors over many orders of magnitude."
        ],
        "equation": "a^{-n} = \\frac{1}{a^n}, \\qquad x^{-1} + y^{-1} = \\frac{1}{x} + \\frac{1}{y} = \\frac{x + y}{xy} \\ne \\frac{1}{x + y}",
        "worked": "Example: Simplify $\\frac{(2x^{-3}y^2)^{-2}}{4x^5y^{-6}}$ using positive exponents only.\n1. Apply outer exponent $-2$ to numerator via Power Rules: $2^{-2} (x^{-3})^{-2} (y^2)^{-2} = 2^{-2} x^6 y^{-4}$.\n2. Divide by $4x^5y^{-6} = 2^2 x^5 y^{-6}$: subtract exponents $\\implies 2^{-2-2} x^{6-5} y^{-4 - (-6)} = 2^{-4} x^1 y^2 = \\frac{xy^2}{16}$.",
        "exercises": [
            "Simplify with positive exponents only: $\\left(\\frac{-3a^{-2}b^3}{6a^4b^{-1}}\\right)^{-3}$.",
            "Compute $(8.0 \\times 10^{-6}) \\div (1.6 \\times 10^{-9})$ in scientific notation and standard decimal form."
        ],
        "recall": [
            ("Why can you rewrite $\\frac{x^{-2}y}{z}$ as $\\frac{y}{x^2 z}$, but you CANNOT rewrite $\\frac{x^{-2} + y}{z}$ as $\\frac{y}{x^2 z}$?", "Because in $x^{-2}y$, $x^{-2} = \\frac{1}{x^2}$ is a factor of the entire numerator. In $x^{-2} + y = \\frac{1}{x^2} + y$, $x^{-2}$ is only one addend of a sum, not a factor of the numerator."),
            ("When using $\\frac{a^m}{a^n} = a^{m-n}$ on $\\frac{x^3}{x^{-4}}$, why is the result $x^7$ and not $x^{-1}$?", "Subtracting a negative exponent adds its opposite: $3 - (-4) = 3 + 4 = 7$.")
        ]
    },
    "MTH-T01-C13-U06": {
        "title": "Introduction to Factoring Polynomials",
        "obj": "Find the Greatest Common Factor (GCF) of two or more monomials and factor the GCF out of any polynomial.",
        "out": "Factor out positive and negative GCFs from polynomials and verify by distributing.",
        "prereq": "MTH-T01-C02-U05, MTH-T01-C13-U03, MTH-T01-C13-U04",
        "source": "OpenStax Prealgebra 2e — Section 10.6: Introduction to Factoring Polynomials (Verified HTTP 200).",
        "concepts": [
            "GCF of Monomials (Contrast with LCM!): The Greatest Common Factor (GCF) of two or more terms is the product of the GCF of their numerical coefficients and each shared variable raised to the SMALLEST (lowest) exponent that appears across all terms.",
            "Factoring Out the GCF as Reverse Distribution: Once you find the GCF $G$, divide every term of the polynomial by $G$ and write the polynomial as $G \\cdot \\left(\\text{quotient}\\right)$.",
            "Factoring Out a Negative Leading Coefficient: When the leading term of a polynomial is negative (e.g., $-6x^3 + 15x^2 - 3x$), always factor out a NEGATIVE GCF ($-3x$) so the leading term inside the parentheses is positive, and remember to flip every sign inside: $-3x(2x^2 - 5x + 1)$."
        ],
        "equation": "ab + ac - ad = a(b + c - d), \\qquad \\text{GCF}(x^m, x^n) = x^{\\min(m, n)}",
        "worked": "Example: Factor completely: $-12x^4y^2 + 18x^3y^3 - 6x^2y^2$.\n1. Numerical GCF of $12, 18, 6$ is $6$; lowest power of $x$ is $x^2$; lowest power of $y$ is $y^2$. Since the leading coefficient is negative, take $\\text{GCF} = -6x^2y^2$.\n2. Divide each term by $-6x^2y^2$: $\\frac{-12x^4y^2}{-6x^2y^2} = 2x^2$, $\\frac{18x^3y^3}{-6x^2y^2} = -3xy$, $\\frac{-6x^2y^2}{-6x^2y^2} = +1$.\n3. Factored form: $-6x^2y^2(2x^2 - 3xy + 1)$. Check by distributing!",
        "exercises": [
            "Find the GCF of $24a^4b^2,\\ 36a^2b^5,$ and $60a^3b^3$.",
            "Factor completely and check by multiplying: (a) $14m^3 - 35m^2 + 7m$, (b) $-8x^3y - 20x^2y^2 + 4xy$."
        ],
        "recall": [
            ("How does choosing the exponent on variables for the GCF differ from choosing the exponent for the LCM?", "For the GCF (largest factor that divides into all terms), take the LOWEST exponent of each common variable; for the LCM (smallest multiple that all terms divide into), take the HIGHEST exponent."),
            ("When factoring $7m$ out of $14m^3 - 35m^2 + 7m$, why must the polynomial inside the parentheses still have $3$ terms ($2m^2 - 5m + 1$)?", "Because $7m \\div 7m = +1$; if the $+1$ is omitted, distributing $7m(2m^2 - 5m)$ only gives $2$ terms and loses $+7m$.")
        ]
    },
    "MTH-T01-C14-U01": {
        "title": "Understand Slope of a Line",
        "obj": "Calculate the slope of a line from its graph ($\\frac{\\text{rise}}{\\text{run}}$) and from two points using the slope formula, and determine slopes of horizontal, vertical, and parallel/perpendicular lines.",
        "out": "Compute and interpret positive, negative, zero, and undefined slopes from coordinates and graphs.",
        "prereq": "MTH-T01-C03-U03, MTH-T01-C04-U02, MTH-T01-C14-U04",
        "source": "OpenStax Prealgebra 2e — Section 11.4: Understand Slope of a Line (Verified HTTP 200).",
        "concepts": [
            "Slope as Constant Rate of Change: The slope $m$ of a non-vertical line passing through $(x_1, y_1)$ and $(x_2, y_2)$ is the ratio of vertical change (rise $\\Delta y$) to horizontal change (run $\\Delta x$): $m = \\frac{y_2 - y_1}{x_2 - x_1}$ ($x_2 \\ne x_1$).",
            "Four Geometric Orientations of Slope: (1) $m > 0$: rises left-to-right; (2) $m < 0$: falls left-to-right; (3) Horizontal line ($y = b$): $\\Delta y = 0 \\implies m = \\frac{0}{\\Delta x} = 0$; (4) Vertical line ($x = a$): $\\Delta x = 0 \\implies m = \\frac{\\Delta y}{0}$ is UNDEFINED.",
            "Slope-Intercept Form ($y = mx + b$): When a linear equation is solved for $y$, the coefficient of $x$ is the slope $m$ and $(0, b)$ is the $y$-intercept."
        ],
        "equation": "m = \\frac{\\text{rise}}{\\text{run}} = \\frac{\\Delta y}{\\Delta x} = \\frac{y_2 - y_1}{x_2 - x_1} \\quad (x_2 \\ne x_1), \\qquad y = mx + b",
        "worked": "Example: Find the slope of the line through $(-3, 7)$ and $(5, -9)$, and the slopes of $y = -4$ and $x = 6$.\n1. $m = \\frac{-9 - 7}{5 - (-3)} = \\frac{-16}{8} = -2$.\n2. $y = -4$ is a horizontal line ($y$ never changes), so $m = 0$.\n3. $x = 6$ is a vertical line ($x$ never changes, $\\Delta x = 0$), so $m$ is undefined.",
        "exercises": [
            "Find the slope of the line passing through: (a) $(-4, -2)$ and $(6, 3)$, (b) $(2, -5)$ and $(2, 8)$, (c) $(-1, 4)$ and $(7, 4)$.",
            "Graph the line passing through $(1, -2)$ with slope $m = -\\frac{3}{4}$ by finding two additional points using rise and run."
        ],
        "recall": [
            ("What common error occurs if a student writes $m = \\frac{y_2 - y_1}{x_1 - x_2}$ when computing slope?", "They subtract the $y$-coordinates in one order ($2 \\to 1$) and the $x$-coordinates in the opposite order ($1 \\to 2$), which flips the sign of the slope! Always subtract in the same point order in both numerator and denominator."),
            ("How do you keep straight which line ($y = b$ vs. $x = a$) has slope $0$ and which has undefined slope?", "For $y = b$ (horizontal), $y_2 - y_1 = 0$ is in the numerator ($\\frac{0}{\\text{run}} = 0$). For $x = a$ (vertical), $x_2 - x_1 = 0$ is in the denominator ($\\frac{\\text{rise}}{0} = \\text{undefined}$).")
        ]
    },
    "MTH-T01-C14-U02": {
        "title": "Graphing with Intercepts",
        "obj": "Identify and algebraically compute the $x$-intercept $(a, 0)$ and $y$-intercept $(0, b)$ of a linear equation, and graph standard-form lines $Ax + By = C$ using intercepts.",
        "out": "Find both intercepts of any linear equation and sketch its graph accurately.",
        "prereq": "MTH-T01-C11-U02, MTH-T01-C14-U04",
        "source": "OpenStax Prealgebra 2e — Section 11.3: Graphing with Intercepts (Verified HTTP 200).",
        "concepts": [
            "Geometric & Algebraic Meaning of Intercepts: Every point on the $x$-axis has $y$-coordinate $0$, so to find the $x$-intercept $(a, 0)$, substitute $y = 0$ and solve for $x$. Every point on the $y$-axis has $x$-coordinate $0$, so to find the $y$-intercept $(0, b)$, substitute $x = 0$ and solve for $y$.",
            "When the Intercept Method Shines: For equations written in Standard Form $Ax + By = C$ where $A$ and $B$ divide evenly into $C$ (e.g., $3x - 4y = 12$), finding $(4, 0)$ and $(0, -3)$ takes two mental divisions.",
            "Lines Passing Through the Origin $(0, 0)$: If $C = 0$ (e.g., $y = 2x$ or $3x + y = 0$), both the $x$-intercept and $y$-intercept are the same single point $(0, 0)$, so you must plug in a second nonzero $x$-value to get a second point!"
        ],
        "equation": "x\\text{-intercept: set } y = 0 \\implies (a, 0), \\qquad y\\text{-intercept: set } x = 0 \\implies (0, b)",
        "worked": "Example: Find the $x$- and $y$-intercepts of $2x - 5y = 20$ and a third checkpoint.\n1. $x$-intercept (set $y = 0$): $2x - 5(0) = 20 \\implies 2x = 20 \\implies x = 10 \\implies (10, 0)$.\n2. $y$-intercept (set $x = 0$): $2(0) - 5y = 20 \\implies -5y = 20 \\implies y = -4 \\implies (0, -4)$.\n3. Third checkpoint (let $x = 5$): $10 - 5y = 20 \\implies -5y = 10 \\implies y = -2 \\implies (5, -2)$ (collinear!).",
        "exercises": [
            "Find the $x$-intercept and $y$-intercept (written as ordered pairs!) for: (a) $4x + 3y = -24$, (b) $y = 3x - 9$.",
            "Explain why the intercept method alone gives only one point for $2x + 5y = 0$, and find two distinct points on this line."
        ],
        "recall": [
            ("Why should an $x$-intercept always be written as an ordered pair $(a, 0)$ rather than just a number $a$?", "Because an intercept is a geometric point in the 2D coordinate plane, and writing $(a, 0)$ vs. $(0, b)$ prevents confusing which coordinate is zero."),
            ("To find the $x$-intercept of a line, why do you set $y = 0$ instead of $x = 0$?", "Because the $x$-intercept lies on the horizontal $x$-axis, where the vertical height $y$ is $0$.")
        ]
    },
    "MTH-T01-C14-U03": {
        "title": "Graphing Linear Equations",
        "obj": "Verify ordered-pair solutions to two-variable linear equations, graph lines by plotting three points, and graph horizontal ($y = b$) and vertical ($x = a$) lines.",
        "out": "Construct solution tables and graph linear equations in $Ax + By = C$ and $y = mx + b$ forms.",
        "prereq": "MTH-T01-C14-U04 (Use the Rectangular Coordinate System)",
        "source": "OpenStax Prealgebra 2e — Section 11.2: Graphing Linear Equations (Verified HTTP 200).",
        "concepts": [
            "Graph of a Linear Equation in Two Variables: An equation of the form $Ax + By = C$ (with $A, B$ not both zero) has infinitely many ordered-pair solutions $(x, y)$, and when plotted in the coordinate plane, they all lie on a single straight line.",
            "Why Plot THREE Points When Two Determine a Line?: Any two points determine a line, so if you miscalculate one of two points, you will draw the wrong line without realizing it. Plotting a third point acts as an error-detection checksum: if the three points are not collinear, at least one calculation has an error!",
            "Choosing Convenient $x$-Values for Fractional Coefficients: When graphing $y = -\\frac{2}{3}x + 1$, choose $x$-values that are multiples of the denominator $3$ ($x = -3, 0, 3$) so the fraction cancels cleanly to integers."
        ],
        "equation": "Ax + By = C, \\qquad y = b \\text{ (horizontal line)}, \\qquad x = a \\text{ (vertical line)}",
        "worked": "Example: Find three integer ordered-pair solutions for $y = -\\frac{3}{4}x + 2$.\n1. Choose multiples of $4$ for $x$: $x \\in \\{-4, 0, 4\\}$.\n2. At $x = -4$: $y = -\\frac{3}{4}(-4) + 2 = 3 + 2 = 5 \\implies (-4, 5)$.\n3. At $x = 0$: $y = 0 + 2 = 2 \\implies (0, 2)$.\n4. At $x = 4$: $y = -\\frac{3}{4}(4) + 2 = -3 + 2 = -1 \\implies (4, -1)$.",
        "exercises": [
            "Find three integer points on the line $y = \\frac{2}{5}x - 3$.",
            "State three points on the line $x = -3$ and three points on the line $y = 5$, and identify which is vertical and which is horizontal."
        ],
        "recall": [
            ("Why is the graph of $x = 4$ a vertical line rather than a single point on the $x$-axis?", "In the 2D coordinate plane $(x, y)$, the equation $x = 4$ places no restriction on $y$; every ordered pair $(4, y)$ for any real $y$ satisfies $x = 4$, forming a vertical line."),
            ("When graphing $y = \\frac{3}{5}x - 2$ by plotting points, why is choosing $x = -5, 0, 5$ much smarter than choosing $x = 1, 2, 3$?", "Choosing multiples of the denominator $5$ cancels the denominator in $\\frac{3}{5}x$, producing exact integer $y$-coordinates that are easy to plot accurately.")
        ]
    },
    "MTH-T01-C14-U04": {
        "title": "Use the Rectangular Coordinate System",
        "obj": "Plot points $(x, y)$ in the Cartesian coordinate plane, identify quadrants and axis points, and verify whether an ordered pair is a solution to a two-variable equation.",
        "out": "Identify coordinates, quadrants, and axis locations, and test ordered pairs in two-variable linear equations.",
        "prereq": "MTH-T01-C03-U01 (Integers), MTH-T01-C11-U01",
        "source": "OpenStax Prealgebra 2e — Section 11.1: Use the Rectangular Coordinate System (Verified HTTP 200).",
        "concepts": [
            "Ordered Pairs $(x, y)$ & Axes: The horizontal axis is the $x$-axis; the vertical axis is the $y$-axis; they intersect at the origin $(0, 0)$. In $(x, y)$, the first coordinate $x$ (abscissa) gives horizontal signed displacement from the $y$-axis, and the second coordinate $y$ (ordinate) gives vertical signed displacement from the $x$-axis. Order matters: $(-2, 5) \\ne (5, -2)$!",
            "Four Quadrants (Counterclockwise from Top-Right): Quadrant I: $(+, +)$; Quadrant II: $(-, +)$; Quadrant III: $(-, -)$; Quadrant IV: $(+, -)$. Points lying directly on the $x$-axis $(x, 0)$ or $y$-axis $(0, y)$ do NOT belong to any quadrant!",
            "Ordered Pairs as Solutions: $(x_0, y_0)$ is a solution to an equation in $x$ and $y$ if substituting $x = x_0$ and $y = y_0$ yields a true statement."
        ],
        "equation": "\\text{QI: } (+,+),\\quad \\text{QII: } (-,+),\\quad \\text{QIII: } (-,-),\\quad \\text{QIV: } (+,-)",
        "worked": "Example: State the quadrant or axis for $(-4, 0),\\ (0, -7),\\ (-3, -5),\\ (2, -6)$, and test whether $(-3, 4)$ is a solution to $2x + 5y = 14$.\n1. $(-4, 0)$: on the $x$-axis (no quadrant); $(0, -7)$: on the $y$-axis; $(-3, -5)$: Quadrant III; $(2, -6)$: Quadrant IV.\n2. Substitute $x = -3, y = 4$ into $2x + 5y = 14$: $2(-3) + 5(4) = -6 + 20 = 14$ (True $\\implies (-3, 4)$ is a solution).",
        "exercises": [
            "Determine which of the ordered pairs $\\{(0, -4),\\ (-2, -1),\\ (3, -6)\\}$ are solutions to the equation $3x - 2y = 8$.",
            "Complete the table of solutions for $2x + y = 7$ given $x = -2,\\ x = 0,$ and $y = 1$."
        ],
        "recall": [
            ("Which quadrant does the point $(0, 6)$ belong to?", "None! Because its $x$-coordinate is $0$, $(0, 6)$ lies directly on the positive $y$-axis, and points on either axis are boundary points not in any of the four quadrants."),
            ("What common mistake happens when plotting $(0, -3)$ versus $(-3, 0)$?", "Confusing which coordinate moves horizontally vs. vertically: $(0, -3)$ moves $0$ horizontally and $3$ down (on the $y$-axis), whereas $(-3, 0)$ moves $3$ left and $0$ vertically (on the $x$-axis).")
        ]
    }
}
