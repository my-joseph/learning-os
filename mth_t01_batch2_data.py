# -*- coding: utf-8 -*-
"""
Curriculum and Practice Guide Data for MTH-T01 Batch 2 (Chapters C05 to C09: 35 Pages).
Production-grade mathematical formulations, 4-category Practice Guides, Active Recall toggles with solutions.
"""

CHAPTER_DATA = {
    "MTH-T01-C05": {
        "title": "Decimals",
        "objective": "Master decimal place values, arithmetic operations on signed decimals, conversion between fractions and terminating/repeating decimals, and solving linear equations with decimal coefficients.",
        "role": "Decimals extend the base-10 positional numeral system to fractional values using negative powers of 10 ($10^{-1}, 10^{-2}, \\dots$). Decimals are essential for continuous scientific measurement, currency calculations, statistical averages, and computing in programming where floating-point arithmetic is standard.",
        "invariants": [
            "Positional Place Value: Each position right of the decimal point represents a division by 10 (tenths, hundredths, thousandths).",
            "Addition & Subtraction Alignment: Digits of identical place value must align vertically at the decimal point.",
            "Multiplication Place Value Sum: The product of two decimals contains total decimal places equal to the sum of decimal places in the factors.",
            "Division by Decimal Invariant: Multiplying dividend and divisor by $10^k$ produces an integer divisor without changing the quotient."
        ],
        "units": ["MTH-T01-C05-U01", "MTH-T01-C05-U02", "MTH-T01-C05-U03", "MTH-T01-C05-U04", "MTH-T01-C05-U05", "MTH-T01-C05-U06", "MTH-T01-C05-U07"],
        "practice_guide": {
            "conceptual": [
                "Explain why appending trailing zeros to a decimal (0.7 to 0.700) does not alter its value, whereas appending zeros to an integer changes its magnitude by powers of 10.",
                "Describe why dividing by a number between 0 and 1 results in a quotient larger than the original dividend.",
                "Contrast terminating decimals with repeating decimals in terms of prime factors of their denominator."
            ],
            "computational": [
                "Evaluate $14.28 - 6.895 + 3.4$ using strict vertical column alignment.",
                "Multiply $0.035 \\times 0.42$ and verify the placement of decimal places ($3 + 2 = 5$ places).",
                "Divide $1.872 \\div 0.08$ by clearing the divisor to an integer ($187.2 \\div 8$).",
                "Solve the linear equation with decimals: $0.25x + 1.5 = 0.4x - 0.75$."
            ],
            "traps": [
                "Alignment Trap: Aligning numbers by their rightmost digit in addition/subtraction instead of by the decimal point.",
                "Lost Leading Zeros Trap: In multiplication like $0.04 \\times 0.03$, writing $0.12$ instead of $0.0012$ ($4$ decimal places).",
                "Clearing Decimals Trap: When multiplying an equation by 100 to clear decimals, forgetting to multiply whole numbers or constants."
            ],
            "real_world": [
                "Financial calculations: Compound sales tax, unit price comparisons in supermarkets, and tip calculations.",
                "Programming ([[PRG-T01]]): Floating-point representation in IEEE 754 (e.g. why `0.1 + 0.2 != 0.3` in JavaScript/Python).",
                "Physics ([[PHY-T01]]): Measurement precision, uncertainty propagation, and significant figures in physical laboratory experiments."
            ]
        },
        "active_recall": [
            {
                "q": "What is the exact algebraic justification for multiplying both dividend and divisor by 10^k when dividing decimals?",
                "a": "Division $a \\div b$ is equivalent to the fraction $\\frac{a}{b}$. Multiplying numerator and denominator by $10^k$ is equivalent to multiplying by $\\frac{10^k}{10^k} = 1$, the Multiplicative Identity, which preserves the value of the quotient."
            },
            {
                "q": "How can you tell without dividing whether a simplified fraction a/b will terminate or repeat as a decimal?",
                "a": "A simplified fraction terminates if and only if the prime factorization of denominator $b$ contains no prime factors other than 2 and 5 ($b = 2^m 5^n$). If any other prime factor (such as 3, 7, 11) is present, the decimal will repeat infinitely."
            }
        ]
    },

    "MTH-T01-C06": {
        "title": "Percents",
        "objective": "Master the concept of percent as 'per hundred' ($/100$), fluent three-way conversion between percents, decimals, and fractions, and solve percent increase/decrease, sales tax, discounts, commission, and simple interest problems.",
        "role": "Percents provide a normalized scale of 100 for comparing proportions across different sample sizes. They form the mathematical backbone of commercial finance, probability distributions, error analysis in experimental sciences, and data analysis in software.",
        "invariants": [
            "Percent Definition: $P\\% = \\frac{P}{100} = P \\times 0.01$.",
            "Percent Equation: $\\text{Amount} = \\text{Percent} \\times \\text{Base}$ ($A = P \\cdot B$).",
            "Percent Proportion: $\\frac{\\text{is}}{\\text{of}} = \\frac{\\text{percent}}{100} \\iff \\frac{A}{B} = \\frac{P}{100}$.",
            "Percent of Change: $\\text{Percent Change} = \\frac{|\\text{New} - \\text{Original}|}{\\text{Original}} \\times 100\\%$."
        ],
        "units": ["MTH-T01-C06-U01", "MTH-T01-C06-U02", "MTH-T01-C06-U03", "MTH-T01-C06-U04", "MTH-T01-C06-U05"],
        "practice_guide": {
            "conceptual": [
                "Clarify why a 20% discount followed by a 20% markup does not return an item to its original price.",
                "Explain why the base in percent of change calculations must always be the original amount, not the new amount.",
                "Derive the relationship between the decimal multiplier $(1 + r)$ for percent increase and $(1 - r)$ for percent decrease."
            ],
            "computational": [
                "Convert $0.0045$, $\\frac{7}{8}$, and $1.35$ into percents.",
                "Solve: What percent of 64 is 48?",
                "Calculate total cost: An item priced at $85 is on a 25% discount with an 8% sales tax applied to the discounted price.",
                "Compute simple interest earned on $4,500 deposited at 4.2% annual simple interest for 3 years and 6 months ($I = Prt$)."
            ],
            "traps": [
                "Consecutive Percent Trap: Adding successive discounts together (e.g. 10% off then 15% off is NOT 25% off; $0.9 \\times 0.85 = 0.765 \\implies 23.5\\%$ off).",
                "Time Unit Inconsistency in $I = Prt$: Using months directly for $t$ instead of years ($6\\text{ months} = 0.5\\text{ years}$).",
                "Base Inversion Trap: When a population grows from 80 to 100, dividing 20 by 100 (20%) instead of dividing by original 80 (25%)."
            ],
            "real_world": [
                "Commercial banking: APR, simple interest vs compound interest growth curves.",
                "Programming ([[PRG-T01]]): Progress indicators, layout percentages in responsive CSS (`width: 50%`), and statistical sampling.",
                "Physics ([[PHY-T01]]): Percent error calculations $\\frac{|v_{\\text{exp}} - v_{\\text{theor}}|}{v_{\\text{theor}}} \\times 100\\%$ in laboratory kinematics."
            ]
        },
        "active_recall": [
            {
                "q": "Why does a 50% price increase followed by a 50% decrease leave the item at 75% of original price rather than 100%?",
                "a": "Because the 50% decrease is calculated from the larger new base. If original price is $x$, increase gives $1.50x$. A 50% decrease subtracts $0.50 \\times 1.50x = 0.75x$, leaving $0.75x$ (a net 25% loss)."
            },
            {
                "q": "State the formula for Simple Interest and identify the required unit for each variable.",
                "a": "$I = P \\cdot r \\cdot t$, where $I$ is interest earned ($), $P$ is principal principal balance ($), $r$ is annual interest rate expressed as a decimal (e.g. 5% = 0.05), and $t$ is strictly measured in years."
            }
        ]
    },

    "MTH-T01-C07": {
        "title": "Propotional & Radio",
        "objective": "Understand ratios as multiplicative comparisons between quantities of like units, rates as comparisons between different units, solve proportions via cross-multiplication, and model direct and inverse variations.",
        "role": "Ratios and proportions formalize multiplicative scale invariance. They are the mathematical foundation for unit conversions, map scales, similar triangles in geometry ([[MTH-T01-C12]]), trigonometric definitions ([[MTH-T02]]), and proportional physical laws ($F = ma$, $v = d/t$) in physics ([[PHY-T01]]).",
        "invariants": [
            "Ratio Scale Invariance: $\\frac{a}{b} = \\frac{ka}{kb}$ for any scalar $k \\neq 0$.",
            "Cross-Product Equality: $\\frac{a}{b} = \\frac{c}{d} \\iff ad = bc$ ($b, d \\neq 0$).",
            "Direct Proportion Invariant: $y = kx \\iff \\frac{y}{x} = k$ (constant ratio).",
            "Inverse Proportion Invariant: $y = \\frac{k}{x} \\iff xy = k$ (constant product)."
        ],
        "units": ["MTH-T01-C07-U01", "MTH-T01-C07-U02", "MTH-T01-C07-U03", "MTH-T01-C07-U04", "MTH-T01-C07-U05", "MTH-T01-C07-U06"],
        "practice_guide": {
            "conceptual": [
                "Distinguish between a ratio (pure number comparing like units) and a rate (dimensional quantity comparing distinct units like miles per hour).",
                "Explain the geometric and physical difference between Direct Variation (graph passes through origin $(0,0)$ with constant slope) and Inverse Variation (hyperbolic curve asymptotic to axes).",
                "Explain why cross-multiplication works algebraically by clearing fractions."
            ],
            "computational": [
                "Compute the unit rate: A vehicle travels $357\\text{ miles}$ on $12\\text{ gallons}$ of fuel.",
                "Solve the proportion for $x$: $\\frac{x + 3}{8} = \\frac{15}{20}$.",
                "If 6 workers take 14 hours to pave a road, how many hours will 8 workers take assuming inverse proportionality ($w_1 t_1 = w_2 t_2$)?",
                "Scale model calculation: A blueprint has a scale of $0.25\\text{ inch} = 4\\text{ feet}$. Find the blueprint length for a $36\\text{ foot}$ room."
            ],
            "traps": [
                "Direct vs Inverse Trap: Applying direct cross-multiplication to an inverse variation problem (e.g. more workers taking more time instead of less time!).",
                "Unit Rate Inversion: Dividing gallons by miles when miles-per-gallon (mpg) is requested.",
                "Cross-Multiplication with Terms Trap: In $\\frac{x+2}{3} = \\frac{5}{7}$, writing $7x + 2 = 15$ instead of applying the distributive property $7(x + 2) = 7x + 14$."
            ],
            "real_world": [
                "Dimensional Analysis & Unit Conversions in Physics ([[PHY-T01-C01-U02]]).",
                "Aspect ratio scaling in graphics and web development (`16:9`, `4:3`, responsive image viewports in [[PRG-T01]]).",
                "Chemical stoichiometric ratios and culinary recipe batch scaling."
            ]
        },
        "active_recall": [
            {
                "q": "What is the structural algebraic difference between Direct and Inverse Variation?",
                "a": "Direct variation has a constant ratio: $\\frac{y}{x} = k \\implies y = kx$ (as $x$ increases, $y$ increases proportionally). Inverse variation has a constant product: $x \\cdot y = k \\implies y = \\frac{k}{x}$ (as $x$ increases, $y$ decreases proportionally)."
            },
            {
                "q": "Show algebraically why cross-multiplication a/b = c/d implies ad = bc.",
                "a": "Multiply both sides of $\\frac{a}{b} = \\frac{c}{d}$ by the common denominator $bd$: $(bd) \\cdot \\frac{a}{b} = (bd) \\cdot \\frac{c}{d}$. On the left, $b$ cancels leaving $ad$. On the right, $d$ cancels leaving $bc$. Hence, $ad = bc$."
            }
        ]
    },

    "MTH-T01-C08": {
        "title": "Exponents",
        "objective": "Understand integer exponents as repeated multiplication, master product, quotient, and power rules of exponents, define zero and negative integer exponents, and apply scientific notation to represent extreme quantities.",
        "role": "Exponents model non-linear growth and decay phenomena. They provide compact representation for atomic scales and cosmic distances, forming the operational basis for polynomials ([[MTH-T01-C13]]), logarithms, binary addressing in computer science ([[PRG-T01]]), and SI metric prefixes in physics ([[PHY-T01]]).",
        "invariants": [
            "Product Rule (Same Base): $a^m \\cdot a^n = a^{m+n}$.",
            "Quotient Rule (Same Base): $\\frac{a^m}{a^n} = a^{m-n}$ ($a \\neq 0$).",
            "Power of a Power Rule: $(a^m)^n = a^{m \\cdot n}$.",
            "Power of a Product / Quotient: $(ab)^n = a^n b^n$, $\\left(\\frac{a}{b}\\right)^n = \\frac{a^n}{b^n}$.",
            "Zero Exponent Rule: $a^0 = 1$ ($a \\neq 0$).",
            "Negative Exponent Invariant: $a^{-n} = \\frac{1}{a^n}$ and $\\frac{1}{a^{-n}} = a^n$ ($a \\neq 0$)."
        ],
        "units": ["MTH-T01-C08-U01", "MTH-T01-C08-U02", "MTH-T01-C08-U03", "MTH-T01-C08-U04", "MTH-T01-C08-U05", "MTH-T01-C08-U06"],
        "practice_guide": {
            "conceptual": [
                "Prove why $a^0 = 1$ using the Quotient Rule: $\\frac{a^n}{a^n} = a^{n-n} = a^0 = 1$.",
                "Explain why negative exponents denote reciprocal division rather than negative numeric values (e.g. $2^{-3} = \\frac{1}{8} > 0$).",
                "Contrast $(-3)^4 = 81$ with $-3^4 = -81$ based on order of operations."
            ],
            "computational": [
                "Simplify: $(2x^3 y^{-2})^3 (4x^{-4} y^5)$.",
                "Evaluate with negative exponents: $\\frac{3^{-2} + 4^{-1}}{2^{-3}}$.",
                "Multiply in scientific notation: $(4.5 \\times 10^7) \\times (6.2 \\times 10^{-12})$.",
                "Divide in scientific notation: $\\frac{1.44 \\times 10^8}{1.2 \\times 10^{-4}}$."
            ],
            "traps": [
                "Negative Base vs Negative Exponent Trap: Believing $5^{-2} = -25$ or $-10$. It is $+1/25$!",
                "Base Multiplication Trap: In $2^3 \\cdot 2^4$, multiplying bases to get $4^7$ instead of keeping the base: $2^{3+4} = 2^7$.",
                "Adding Exponents in Power of Power: Writing $(x^3)^4 = x^{3+4} = x^7$ instead of multiplying: $x^{3 \\cdot 4} = x^{12}$."
            ],
            "real_world": [
                "Computer Architecture: Powers of 2 ($2^{10} = 1024\\text{ bytes} = 1\\text{ KB}$, 32-bit vs 64-bit address spaces in [[PRG-T01]]).",
                "Physics: Astronomical distances in light-years and Planck scale lengths in scientific notation ([[PHY-T01-C01-U03]]).",
                "Biology: Exponential bacterial cell division ($N(t) = N_0 2^t$)."
            ]
        },
        "active_recall": [
            {
                "q": "Why is (-2)^4 equal to +16, whereas -2^4 is equal to -16?",
                "a": "In $(-2)^4$, the parentheses bind the negative sign to the base: $(-2)(-2)(-2)(-2) = +16$. In $-2^4$, by standard Order of Operations (PEMDAS), exponentiation precedes negation: $-(2^4) = -(16) = -16$."
            },
            {
                "q": "Derive why a^(-n) = 1 / a^n using the quotient property of exponents.",
                "a": "Consider $\\frac{a^0}{a^n}$. By the quotient rule, $\\frac{a^0}{a^n} = a^{0 - n} = a^{-n}$. But since $a^0 = 1$, we also have $\\frac{a^0}{a^n} = \\frac{1}{a^n}$. Therefore, $a^{-n} = \\frac{1}{a^n}$."
            }
        ]
    },

    "MTH-T01-C09": {
        "title": "Roots",
        "objective": "Understand radical notation and principal square roots as the inverse operation of squaring, simplify radical expressions by factoring out perfect squares, evaluate cube roots, and connect radicals to fractional exponents ($x^{1/n} = \\sqrt[n]{x}$).",
        "role": "Roots allow solving quadratic and higher-degree polynomial equations ($x^2 = k$). They define Euclidean distance via the Pythagorean Theorem ([[MTH-T01-C12]]), calculate geometric means, and are central to kinetic energy, free-fall drop times ($t = \\sqrt{2h/g}$), and wave mechanics in physics ([[PHY-T01]]).",
        "invariants": [
            "Principal Square Root Definition: For $a \\ge 0$, $\\sqrt{a} = b \\iff b^2 = a$ and $b \\ge 0$.",
            "Product Property of Radicals: $\\sqrt{ab} = \\sqrt{a} \\cdot \\sqrt{b}$ ($a, b \\ge 0$).",
            "Quotient Property of Radicals: $\\sqrt{\\frac{a}{b}} = \\frac{\\sqrt{a}}{\\sqrt{b}}$ ($a \\ge 0, b > 0$).",
            "Fractional Exponent Bridge: $\\sqrt[n]{x} = x^{1/n}$ and $\\sqrt[n]{x^m} = x^{m/n}$ ($x \\ge 0$)."
        ],
        "units": ["MTH-T01-C09-U01", "MTH-T01-C09-U02", "MTH-T01-C09-U03", "MTH-T01-C09-U04", "MTH-T01-C09-U05", "MTH-T01-C09-U06"],
        "practice_guide": {
            "conceptual": [
                "Explain why $\\sqrt{a^2 + b^2} \\neq a + b$ using geometric areas and numerical counterexamples ($3^2 + 4^2 = 25 \\implies \\sqrt{25} = 5 \\neq 3 + 4$).",
                "Explain why $\\sqrt{-16}$ is not a real number, whereas $\\sqrt[3]{-8} = -2$ is a valid real number.",
                "Contrast the solutions to $x^2 = 25$ ($x = \\pm 5$) with the evaluation of the principal root $\\sqrt{25}$ (strictly $+5$)."
            ],
            "computational": [
                "Simplify completely: $\\sqrt{72}$, $\\sqrt{300}$, and $\\sqrt{180}$.",
                "Multiply and simplify: $3\\sqrt{6} \\times 2\\sqrt{15}$.",
                "Evaluate cube roots: $\\sqrt[3]{216}$, $\\sqrt[3]{-125}$, and $\\sqrt[3]{\\frac{27}{64}}$.",
                "Express with rational exponents and evaluate: $\\sqrt[4]{16^3} = (16)^{3/4}$."
            ],
            "traps": [
                "Radical Distribution Trap: Distributing square roots over addition/subtraction: $\\sqrt{x + y} \\neq \\sqrt{x} + \\sqrt{y}$.",
                "Negative Under Even Root: Attempting to evaluate $\\sqrt{-25} = -5$. (Check: $(-5)^2 = +25 \\neq -25$!).",
                "Incomplete Simplification: Leaving a perfect square factor inside the radicand (e.g. writing $\\sqrt{72} = \\sqrt{4 \\times 18} = 2\\sqrt{18}$ instead of extracting $36$: $6\\sqrt{2}$)."
            ],
            "real_world": [
                "Physics ([[PHY-T01-C03]]): Kinematic drop times $t = \\sqrt{\\frac{2h}{g}}$ and escape velocities $v = \\sqrt{2GM/R}$.",
                "Geometry ([[MTH-T01-C12]]): Pythagorean Theorem hypotenuse and leg calculations ($c = \\sqrt{a^2 + b^2}$).",
                "Statistics: Standard deviation as the square root of variance ($\\sigma = \\sqrt{\\sigma^2}$)."
            ]
        },
        "active_recall": [
            {
                "q": "Why is the principal square root sqrt(25) strictly equal to +5, even though (-5)^2 is also 25?",
                "a": "By definition, the radical symbol $\\sqrt{\\cdot}$ denotes the **principal** (non-negative) square root. While the quadratic equation $x^2 = 25$ has two solutions ($x = \\pm 5$), the value of the function $\\sqrt{25}$ is uniquely $+5$ to remain a single-valued mathematical function."
            },
            {
                "q": "Show why sqrt(a + b) cannot be simplified to sqrt(a) + sqrt(b).",
                "a": "Radicals do not distribute over addition. For example, let $a = 9$ and $b = 16$. Then $\\sqrt{a + b} = \\sqrt{9 + 16} = \\sqrt{25} = 5$. However, $\\sqrt{a} + \\sqrt{b} = \\sqrt{9} + \\sqrt{16} = 3 + 4 = 7$. Since $5 \\neq 7$, distributing the radical is mathematically invalid."
            }
        ]
    }
}
