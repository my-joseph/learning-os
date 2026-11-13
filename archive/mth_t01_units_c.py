# -*- coding: utf-8 -*-
"""
Instructional content for MTH-T01 Units: C09 through C11 (15 Units).
Source: OpenStax Prealgebra 2e (Chapters 7, 8 + Radicals Extensions).
"""

MTH_UNITS_C = {
    "MTH-T01-C09-U01": {
        "title": "Introduction to Square Roots",
        "obj": "Define principal and negative square roots, recognize perfect squares up to $25^2$, evaluate square roots of fractions/decimals, and simplify $\\sqrt{x^2} = |x|$.",
        "out": "Evaluate exact square roots of integers, fractions, decimals, and even variable powers.",
        "prereq": "MTH-T01-C05-U07, MTH-T01-C08-U01",
        "source": "OpenStax Prealgebra 2e — Section 5.7 & Radical Foundation Module (Verified HTTP 200).",
        "concepts": [
            "Principal vs. Both Square Roots: Every positive number $m$ has two real square roots ($\\pm\\sqrt{m}$), but the radical symbol $\\sqrt{m}$ denotes ONLY the non-negative principal square root.",
            "Absolute Value Identity ($\\sqrt{x^2} = |x|$): Because $\\sqrt{\\cdot}$ is never negative, $\\sqrt{(-7)^2} = \\sqrt{49} = 7 = |-7|$. In general, for any real number $x$, $\\sqrt{x^2} = |x|$ (and $\\sqrt{x^{2k}} = |x|^k$).",
            "Square Roots of Fractions & Decimals: $\\sqrt{\\frac{a}{b}} = \\frac{\\sqrt{a}}{\\sqrt{b}}$ ($a \\ge 0, b > 0$). A decimal with $2k$ decimal places has a square root with $k$ decimal places ($\\sqrt{0.0064} = 0.08$)."
        ],
        "equation": "\\sqrt{x^2} = |x|, \\qquad \\sqrt{x^{2k}} = |x|^k, \\qquad \\sqrt{\\frac{a}{b}} = \\frac{\\sqrt{a}}{\\sqrt{b}}",
        "worked": "Example: Simplify (a) $\\sqrt{(-13)^2}$, (b) $\\sqrt{16x^6}$ (for $x \\ge 0$), and (c) $-\\sqrt{0.0121}$.\n1. (a) $\\sqrt{(-13)^2} = |-13| = 13$.\n2. (b) $\\sqrt{16x^6} = \\sqrt{(4x^3)^2} = 4x^3$ (for $x \\ge 0$).\n3. (c) $-\\sqrt{0.0121} = -0.11$ (since $(0.11)^2 = 0.0121$).",
        "exercises": [
            "Simplify: (a) $\\sqrt{\\frac{144}{289}}$, (b) $\\sqrt{0.0009}$, (c) $\\sqrt{81a^8b^{12}}$.",
            "Explain why $\\sqrt{x^2} = x$ is false when $x = -9$, and demonstrate the correct identity."
        ],
        "recall": [
            ("Why does $\\sqrt{x^8} = x^4$ not require absolute value bars for any real $x$, whereas $\\sqrt{x^6} = |x^3|$ does?", "Because $x^4 = (x^2)^2 \\ge 0$ is already non-negative for all real $x$, whereas $x^3$ is negative whenever $x < 0$."),
            ("Why is $\\sqrt{0.04} = 0.2$ and not $0.02$?", "Because $(0.2)(0.2) = 0.04$ (summing $1 + 1 = 2$ decimal places), whereas $(0.02)^2 = 0.0004$.")
        ]
    },
    "MTH-T01-C09-U02": {
        "title": "Simplify Square Roots",
        "obj": "Factor radicands to extract largest perfect-square factors and simplify numerical and variable square roots using the Product Property of Radicals.",
        "out": "Simplify non-perfect square roots ($\\sqrt{72x^5}$) into standard radical form $a\\sqrt{b}$ where $b$ is square-free.",
        "prereq": "MTH-T01-C02-U05 (Prime Factorization), MTH-T01-C09-U01",
        "source": "OpenStax Prealgebra 2e / Elementary Algebra — Simplify Square Roots (Verified HTTP 200).",
        "concepts": [
            "Simplified Square Root Conditions: A square root $\\sqrt{R}$ is in simplest form when the radicand $R$ contains NO perfect-square factors greater than $1$ (it is 'square-free').",
            "Extraction via Largest Perfect Square or Prime Pairs: Using $\\sqrt{ab} = \\sqrt{a}\\sqrt{b}$ ($a, b \\ge 0$), factor $R = s^2 \\cdot k$ where $s^2$ is the largest perfect-square factor, so $\\sqrt{s^2 k} = s\\sqrt{k}$. Equivalently, in prime factorization, every pair of identical primes $p^2$ comes outside the radical as a single $p$.",
            "Odd Variable Exponents: Split an odd power $x^{2k+1}$ into the largest even power times $x^1$: $\\sqrt{x^7} = \\sqrt{x^6 \\cdot x} = x^3\\sqrt{x}$ ($x \\ge 0$)."
        ],
        "equation": "\\sqrt{a^2 b} = a\\sqrt{b} \\quad (a, b \\ge 0), \\qquad \\sqrt{x^{2k+1}} = x^k\\sqrt{x} \\quad (x \\ge 0)",
        "worked": "Example: Simplify $\\sqrt{108x^7y^4}$ (assuming $x, y \\ge 0$).\n1. Factor $108 = 36 \\cdot 3 = 6^2 \\cdot 3$, and split $x^7 = x^6 \\cdot x$.\n2. Group perfect squares: $\\sqrt{(36x^6y^4) \\cdot (3x)} = \\sqrt{36x^6y^4} \\cdot \\sqrt{3x}$.\n3. Extract square roots: $6x^3y^2\\sqrt{3x}$.",
        "exercises": [
            "Simplify completely (assume variables $\\ge 0$): (a) $\\sqrt{98}$, (b) $3\\sqrt{75a^5b^8}$, (c) $\\sqrt{180m^9n^2}$.",
            "Combine like radicals after simplifying: $2\\sqrt{50} - 3\\sqrt{18} + \\sqrt{72}$."
        ],
        "recall": [
            ("Why do we split $x^9$ as $x^8 \\cdot x$ instead of $x^5 \\cdot x^4$ when simplifying $\\sqrt{x^9}$?", "Because $x^8 = (x^4)^2$ is the largest even power (perfect square) inside $x^9$, leaving only a single $x^1$ inside the square root."),
            ("When can two radical terms like $a\\sqrt{m}$ and $b\\sqrt{n}$ be added or subtracted?", "Only when they are like radicals—meaning after simplification, they have the exact same index and the exact same radicand ($m = n$).")
        ]
    },
    "MTH-T01-C09-U03": {
        "title": "Cube Roots",
        "obj": "Define and evaluate cube roots ($\\sqrt[3]{a}$) of positive and negative real numbers, and simplify cube-root expressions by extracting perfect cubes.",
        "out": "Evaluate and simplify cube roots of signed numbers and variable expressions.",
        "prereq": "MTH-T01-C08-U01, MTH-T01-C09-U02",
        "source": "OpenStax Elementary Algebra Extension — Cube Roots & Higher Radicals (Verified HTTP 200).",
        "concepts": [
            "Cube Root Definition ($\\sqrt[3]{a}$): $\\sqrt[3]{a} = b \\iff b^3 = a$. Unlike square roots, the cube of a negative number is negative, so $\\sqrt[3]{a}$ is a real number for ALL real $a$ (positive, negative, or zero): $\\sqrt[3]{-a} = -\\sqrt[3]{a}$, and $\\sqrt[3]{x^3} = x$ (no absolute value needed!).",
            "Common Perfect Cubes to Memorize: $1^3=1, 2^3=8, 3^3=27, 4^3=64, 5^3=125, 6^3=216, 10^3=1000$.",
            "Simplifying Cube Roots: Factor the radicand into its largest perfect-cube factor $c^3$ (or prime triplets $p^3$) and variable exponents divisible by $3$ ($x^{3k}$): $\\sqrt[3]{c^3 \\cdot d} = c\\sqrt[3]{d}$."
        ],
        "equation": "\\sqrt[3]{-a} = -\\sqrt[3]{a}, \\qquad \\sqrt[3]{x^3} = x, \\qquad \\sqrt[3]{a^3 b} = a\\sqrt[3]{b}",
        "worked": "Example: Simplify $\\sqrt[3]{-250x^8y^6}$.\n1. Factor $-250 = (-125) \\cdot 2 = (-5)^3 \\cdot 2$, and split $x^8 = x^6 \\cdot x^2$ ($6$ is the largest multiple of $3 \\le 8$).\n2. $\\sqrt[3]{(-5)^3 x^6 y^6 \\cdot (2x^2)} = -5x^2y^2\\sqrt[3]{2x^2}$.",
        "exercises": [
            "Evaluate or simplify: (a) $\\sqrt[3]{-64}$, (b) $\\sqrt[3]{\\frac{27}{125}}$, (c) $\\sqrt[3]{-0.008}$.",
            "Simplify completely: $\\sqrt[3]{108a^{10}b^3}$ and $\\sqrt[3]{-54x^5y^7}$."
        ],
        "recall": [
            ("Why is $\\sqrt[3]{-27} = -3$ a valid real number, whereas $\\sqrt{-27}$ is not a real number?", "Because $(-3)^3 = (-3)(-3)(-3) = -27$ (an odd power preserves a negative sign), whereas no real number squared can be negative."),
            ("When simplifying $\\sqrt[3]{x^{11}}$, how do you split the exponent $11$, and why?", "Split $11 = 9 + 2$ ($x^{11} = x^9 \\cdot x^2$) because $9$ is the largest multiple of the index $3$ that is $\\le 11$, giving $x^3\\sqrt[3]{x^2}$.")
        ]
    },
    "MTH-T01-C09-U04": {
        "title": "Properties of Roots",
        "obj": "Apply the Product and Quotient Properties of $n$-th roots and rationalize monomial denominators.",
        "out": "Multiply, divide, and rationalize radical expressions into standard simplified form.",
        "prereq": "MTH-T01-C09-U02, MTH-T01-C09-U03",
        "source": "OpenStax Elementary Algebra Extension — Properties of Radicals & Rationalizing Denominators (Verified HTTP 200).",
        "concepts": [
            "Product & Quotient Properties of $n$-th Roots: For real $n$-th roots ($b \\ne 0$), $\\sqrt[n]{a} \\cdot \\sqrt[n]{b} = \\sqrt[n]{ab}$ and $\\frac{\\sqrt[n]{a}}{\\sqrt[n]{b}} = \\sqrt[n]{\\frac{a}{b}}$. You can either combine under one radical to cancel common factors first, or split into separate radicals.",
            "Three Conditions for Fully Simplified Radicals: (1) No perfect $n$-th power factors remain inside the radicand; (2) No fractions remain inside a radical; (3) No radicals remain in the denominator of a fraction.",
            "Rationalizing a Monomial Denominator: Multiply numerator and denominator by the smallest radical $\\frac{\\sqrt[n]{c}}{\\sqrt[n]{c}} = 1$ that turns the denominator's radicand into a perfect $n$-th power (e.g., for $\\frac{1}{\\sqrt{5}}$, multiply by $\\frac{\\sqrt{5}}{\\sqrt{5}}$; for $\\frac{1}{\\sqrt[3]{2}}$, multiply by $\\frac{\\sqrt[3]{2^2}}{\\sqrt[3]{2^2}} = \\frac{\\sqrt[3]{4}}{\\sqrt[3]{4}}$)."
        ],
        "equation": "\\frac{a}{\\sqrt{b}} = \\frac{a}{\\sqrt{b}} \\cdot \\frac{\\sqrt{b}}{\\sqrt{b}} = \\frac{a\\sqrt{b}}{b} \\quad (b > 0)",
        "worked": "Example: Simplify (a) $\\frac{\\sqrt{75x^5}}{\\sqrt{3x}}$ ($x > 0$) and (b) $\\frac{6}{\\sqrt{12}}$.\n1. (a) Combine under one radical first to cancel: $\\sqrt{\\frac{75x^5}{3x}} = \\sqrt{25x^4} = 5x^2$.\n2. (b) Simplify denominator first: $\\sqrt{12} = 2\\sqrt{3} \\implies \\frac{6}{2\\sqrt{3}} = \\frac{3}{\\sqrt{3}} \\cdot \\frac{\\sqrt{3}}{\\sqrt{3}} = \\frac{3\\sqrt{3}}{3} = \\sqrt{3}$.",
        "exercises": [
            "Simplify (assume variables $> 0$): (a) $\\sqrt{6x^3} \\cdot \\sqrt{15x}$, (b) $\\frac{\\sqrt{96a^7}}{\\sqrt{2a}}$.",
            "Rationalize the denominator and simplify: (a) $\\frac{10}{\\sqrt{5}}$, (b) $\\sqrt{\\frac{7}{18x}}$, (c) $\\frac{4}{\\sqrt[3]{2}}$."
        ],
        "recall": [
            ("When simplifying $\\frac{\\sqrt{50}}{\\sqrt{2}}$, why is it much faster to use the Quotient Property $\\sqrt{\\frac{50}{2}}$ first rather than rationalizing $\\sqrt{2}$ immediately?", "Combining under one radical reduces $\\frac{50}{2} = 25$ immediately to $\\sqrt{25} = 5$, avoiding unnecessary radical multiplication."),
            ("To rationalize $\\frac{1}{\\sqrt[3]{x}}$ ($x > 0$), why must you multiply top and bottom by $\\sqrt[3]{x^2}$ instead of $\\sqrt[3]{x}$?", "Because a cube root requires three factors of $x$ ($x^3$) inside the radical to simplify: $\\sqrt[3]{x} \\cdot \\sqrt[3]{x^2} = \\sqrt[3]{x^3} = x$.")
        ]
    },
    "MTH-T01-C09-U05": {
        "title": "Roots and Fractional Exponents",
        "obj": "Connect $n$-th roots to rational exponents ($a^{m/n} = (\\sqrt[n]{a})^m = \\sqrt[n]{a^m}$) and apply the Laws of Exponents to fractional powers.",
        "out": "Convert between radical and rational-exponent notation and evaluate/simplify fractional powers.",
        "prereq": "MTH-T01-C08-U04, MTH-T01-C08-U05, MTH-T01-C09-U04",
        "source": "OpenStax Elementary Algebra Extension — Rational Exponents (Verified HTTP 200).",
        "concepts": [
            "Why $a^{1/n} = \\sqrt[n]{a}$: For the Power Rule $(a^{1/n})^n = a^{(1/n) \\cdot n} = a^1 = a$ to hold, $a^{1/n}$ must be the number whose $n$-th power is $a$, which is $\\sqrt[n]{a}$.",
            "General Rational Exponent ($a^{m/n}$): The denominator $n$ is the ROOT index, and the numerator $m$ is the POWER: $a^{m/n} = \\left(\\sqrt[n]{a}\\right)^m = \\sqrt[n]{a^m}$. When evaluating numbers by hand, ALWAYS take the $n$-th root FIRST ($\\left(\\sqrt[n]{a}\\right)^m$) so numbers stay small!",
            "All Exponent Laws Apply to Fractional Exponents: $a^{p} \\cdot a^{q} = a^{p+q}$, $\\frac{a^p}{a^q} = a^{p-q}$, $(a^p)^q = a^{pq}$, and $a^{-m/n} = \\frac{1}{a^{m/n}}$."
        ],
        "equation": "a^{1/n} = \\sqrt[n]{a}, \\qquad a^{m/n} = \\left(\\sqrt[n]{a}\\right)^m = \\sqrt[n]{a^m}, \\qquad a^{-m/n} = \\frac{1}{\\left(\\sqrt[n]{a}\\right)^m}",
        "worked": "Example: Evaluate $16^{-3/4}$ and $(-32)^{2/5}$, and simplify $x^{2/3} \\cdot x^{1/2}$.\n1. $16^{-3/4} = \\frac{1}{16^{3/4}} = \\frac{1}{(\\sqrt[4]{16})^3} = \\frac{1}{2^3} = \\frac{1}{8}$.\n2. $(-32)^{2/5} = (\\sqrt[5]{-32})^2 = (-2)^2 = 4$.\n3. $x^{2/3} \\cdot x^{1/2} = x^{2/3 + 1/2} = x^{4/6 + 3/6} = x^{7/6}$.",
        "exercises": [
            "Evaluate without a calculator: (a) $8^{4/3}$, (b) $81^{-3/4}$, (c) $\\left(\\frac{27}{64}\\right)^{-2/3}$.",
            "Simplify using rational exponent rules (assume $x, y > 0$): $\\frac{(x^{3/4} y^{-1/2})^4}{x^{1/2} y^2}$."
        ],
        "recall": [
            ("In $a^{m/n}$, which part of the fraction is the root index and which part is the power?", "The denominator $n$ is the root index ($\\sqrt[n]{\\cdot}$), and the numerator $m$ is the exponent power."),
            ("Why is it much easier to compute $64^{2/3}$ as $(\\sqrt[3]{64})^2$ rather than $\\sqrt[3]{64^2}$?", "Taking the cube root first reduces $64$ to $4$, and $4^2 = 16$ immediately, whereas squaring $64$ first produces $4,096$.")
        ]
    },
    "MTH-T01-C09-U06": {
        "title": "Simplify Roots with Scientific Notation",
        "obj": "Evaluate square roots and cube roots of numbers in scientific notation by ensuring the power of 10 is divisible by the root index.",
        "out": "Compute $\\sqrt{a \\times 10^n}$ and $\\sqrt[3]{a \\times 10^n}$ accurately for both even and odd exponents $n$.",
        "prereq": "MTH-T01-C08-U06 (Scientific Notation), MTH-T01-C09-U05 (Roots and Fractional Exponents)",
        "source": "OpenStax Prealgebra 2e / Physics Math Prep — Roots with Scientific Notation (Verified HTTP 200).",
        "concepts": [
            "Root of a Product in Scientific Notation: By the Product Property of Radicals, $\\sqrt[k]{a \\times 10^n} = \\sqrt[k]{a} \\times 10^{n/k}$.",
            "Crucial Trick When $n$ Is Not Divisible by $k$: For a square root ($k=2$), the exponent $n$ on $10^n$ MUST be even so $10^{n/2}$ is an integer power of $10$! If $n$ is odd (e.g., $\\sqrt{2.5 \\times 10^7}$ or $\\sqrt{4.9 \\times 10^{-5}}$), rewrite $a \\times 10^n$ by shifting one factor of $10$ into $a$ first: $2.5 \\times 10^7 = 25 \\times 10^6$, and $4.9 \\times 10^{-5} = 49 \\times 10^{-6}$.",
            "For Cube Roots ($k=3$): Adjust the significand so the exponent on $10$ is a multiple of $3$ before taking the cube root."
        ],
        "equation": "\\sqrt{a \\times 10^{2m}} = \\sqrt{a} \\times 10^m, \\qquad \\sqrt[3]{a \\times 10^{3m}} = \\sqrt[3]{a} \\times 10^m",
        "worked": "Example: Compute (a) $\\sqrt{1.6 \\times 10^{-5}}$ and (b) $\\sqrt[3]{2.7 \\times 10^7}$ in normalized scientific notation.\n1. (a) $-5$ is odd! Rewrite $1.6 \\times 10^{-5} = 16 \\times 10^{-6}$. Now take square root: $\\sqrt{16} \\times 10^{-6/2} = 4.0 \\times 10^{-3}$.\n2. (b) $7$ is not divisible by $3$! Rewrite $2.7 \\times 10^7 = 27 \\times 10^6$. Cube root: $\\sqrt[3]{27} \\times 10^{6/3} = 3.0 \\times 10^2$.",
        "exercises": [
            "Evaluate in normalized scientific notation: (a) $\\sqrt{6.4 \\times 10^9}$, (b) $\\sqrt{8.1 \\times 10^{-7}}$, (c) $\\sqrt[3]{6.4 \\times 10^{-11}}$.",
            "In orbital mechanics, escape speed is $v = \\sqrt{\\frac{2GM}{R}}$. Given $2GM = 8.0 \\times 10^{14}\\text{ m}^3/\\text{s}^2$ and $R = 5.0 \\times 10^6\\text{ m}$, compute $v$ in scientific notation."
        ],
        "recall": [
            ("Why can't you immediately write $\\sqrt{3.6 \\times 10^5} = \\sqrt{3.6} \\times 10^{2.5}$ when simplifying by hand?", "Because $10^{2.5}$ is not an integer power of $10$ (and $3.6$ is not a nice square as written), whereas rewriting it as $\\sqrt{36 \\times 10^4}$ gives $6.0 \\times 10^2$ immediately."),
            ("When converting $4.9 \\times 10^{-5}$ so the exponent becomes $-6$, why does $4.9$ become $49$ instead of $0.49$?", "Because decreasing the power of $10$ by $10^{-1}$ requires multiplying the coefficient by $10^1$ to keep the product unchanged: $(4.9 \\times 10^1) \\times 10^{-6} = 49 \\times 10^{-6}$.")
        ]
    },
    "MTH-T01-C10-U01": {
        "title": "Rational and Irrational Numbers",
        "obj": "Classify real numbers into Counting, Whole, Integer, Rational, and Irrational subsets based on fractional and decimal representations.",
        "out": "Classify any real number into all applicable subsets of $\\mathbb{R}$.",
        "prereq": "MTH-T01-C05-U03, MTH-T01-C09-U01",
        "source": "OpenStax Prealgebra 2e — Section 7.1: Rational and Irrational Numbers (Verified HTTP 200).",
        "concepts": [
            "Rational Numbers ($\\mathbb{Q}$): Any number that can be written as $\\frac{p}{q}$ where $p, q \\in \\mathbb{Z}$ and $q \\ne 0$. In decimal form, a real number is rational if and only if its decimal expansion either TERMINATES ($0.75$) or REPEATS in a periodic block ($0.\\overline{27}$).",
            "Irrational Numbers ($\\mathbb{R} \\setminus \\mathbb{Q}$): Real numbers that cannot be written as a ratio of integers; their decimal expansions are non-terminating AND non-repeating (e.g., $\\pi$, $\\sqrt{2}$, $\\sqrt{n}$ for any non-square positive integer $n$, and $0.1010010001\\dots$).",
            "Nested Subset Hierarchy of Real Numbers ($\\mathbb{R}$): $\\mathbb{N} \\subset \\mathbb{W} \\subset \\mathbb{Z} \\subset \\mathbb{Q} \\subset \\mathbb{R}$, while $\\mathbb{Q}$ and the Irrational Numbers partition $\\mathbb{R}$ into two disjoint sets."
        ],
        "equation": "\\mathbb{N} \\subset \\mathbb{W} \\subset \\mathbb{Z} \\subset \\mathbb{Q} \\subset \\mathbb{R}, \\qquad \\mathbb{Q} \\cap \\text{Irrationals} = \\emptyset",
        "worked": "Example: Classify each number into all subsets ($\\mathbb{N}, \\mathbb{W}, \\mathbb{Z}, \\mathbb{Q}, \\text{Irrational}, \\mathbb{R}$): $-\\sqrt{36},\\ \\sqrt{15},\\ 0.\\overline{4},\\ 0$.\n1. $-\\sqrt{36} = -6$: Integer ($\\mathbb{Z}$), Rational ($\\mathbb{Q}$), Real ($\\mathbb{R}$).\n2. $\\sqrt{15}$: $15$ is not a perfect square $\\implies$ Irrational, Real ($\\mathbb{R}$).\n3. $0.\\overline{4} = \\frac{4}{9}$: repeating decimal $\\implies$ Rational ($\\mathbb{Q}$), Real ($\\mathbb{R}$).\n4. $0$: Whole ($\\mathbb{W}$), Integer ($\\mathbb{Z}$), Rational ($\\mathbb{Q}$), Real ($\\mathbb{R}$).",
        "exercises": [
            "Classify each number into all applicable subsets of $\\mathbb{R}$: $\\left\\{-\\frac{24}{6},\\ \\sqrt{49},\\ -\\sqrt{20},\\ 3.14159,\\ \\pi,\\ -0.\\overline{72}\\right\\}$.",
            "Explain why $3.14$ and $\\frac{22}{7}$ are rational numbers whereas $\\pi$ is irrational."
        ],
        "recall": [
            ("How can you tell from a number's decimal expansion whether it is Rational or Irrational?", "A decimal is Rational if and only if it terminates or eventually repeats a fixed block of digits forever; it is Irrational if it continues forever without any repeating period."),
            ("Is every square root $\\sqrt{n}$ an irrational number?", "No! If $n$ is a perfect square (such as $\\sqrt{64} = 8$ or $\\sqrt{\\frac{4}{9}} = \\frac{2}{3}$), then $\\sqrt{n}$ is rational.")
        ]
    },
    "MTH-T01-C10-U02": {
        "title": "Commutative and Associative Properties",
        "obj": "Recognize and apply the Commutative and Associative Properties of Addition and Multiplication to reorder and regroup algebraic expressions.",
        "out": "Justify and execute mental-math and algebraic simplifications using Commutative and Associative laws.",
        "prereq": "MTH-T01-C02-U02, MTH-T01-C04-U03",
        "source": "OpenStax Prealgebra 2e — Section 7.2: Commutative and Associative Properties (Verified HTTP 200).",
        "concepts": [
            "Commutative Property (Order Changes): $a + b = b + a$ and $a \\cdot b = b \\cdot a$. Think 'commute = move positions'.",
            "Associative Property (Grouping Changes, Order Stays Fixed): $(a + b) + c = a + (b + c)$ and $(a \\cdot b) \\cdot c = a \\cdot (b \\cdot c)$. Think 'associate = who is grouped inside parentheses'.",
            "Why Subtraction & Division Fail Both: $8 - 3 \\ne 3 - 8$ and $(12 - 6) - 2 \\ne 12 - (6 - 2)$. However, once you rewrite subtraction as adding the opposite ($8 + (-3)$) and division as multiplying by the reciprocal ($12 \\cdot \\frac{1}{6}$), you CAN commute and associate the signed addends or factors!"
        ],
        "equation": "a + b = b + a, \\quad ab = ba, \\qquad (a + b) + c = a + (b + c), \\quad (ab)c = a(bc)",
        "worked": "Example: Simplify $\\left(\\frac{5}{13} + \\frac{3}{4}\\right) + \\frac{1}{4}$ and $\\left(-\\frac{7}{9}\\right) \\cdot 15 \\cdot \\left(-\\frac{9}{7}\\right)$ using Commutative/Associative properties.\n1. Regroup via Associative Property of Addition: $\\frac{5}{13} + \\left(\\frac{3}{4} + \\frac{1}{4}\\right) = \\frac{5}{13} + 1 = 1\\frac{5}{13}$.\n2. Reorder & regroup via Commutative and Associative Properties of Multiplication: $\\left[\\left(-\\frac{7}{9}\\right)\\left(-\\frac{9}{7}\\right)\\right] \\cdot 15 = 1 \\cdot 15 = 15$.",
        "exercises": [
            "Name the exact property illustrated: (a) $(4x + 7) + 3 = 4x + (7 + 3)$, (b) $(4x + 7) + 3 = 3 + (4x + 7)$, (c) $6(5y) = (6 \\cdot 5)y$.",
            "Use the Commutative and Associative Properties to simplify mentally: $-17 + 48 + 17 - 18$ and $\\frac{4}{9} \\cdot 23 \\cdot \\frac{9}{4}$."
        ],
        "recall": [
            ("How can you immediately tell whether an equation step used the Commutative Property or the Associative Property?", "Check the left-to-right sequence of the terms/factors: if the sequence of symbols changed places, it is Commutative; if the sequence stayed identical and only the parentheses shifted, it is Associative."),
            ("How can you legally reorder terms in $10 - 7 + 4$ without changing its value?", "Rewrite subtraction as adding the opposite: $10 + (-7) + 4$, ensuring the negative sign stays attached to $7$ wherever $(-7)$ moves.")
        ]
    },
    "MTH-T01-C10-U03": {
        "title": "Distributive Property",
        "obj": "Apply the Distributive Property of Multiplication over Addition and Subtraction forward (expanding parentheses) and backward (combining like terms), including negative multipliers.",
        "out": "Expand nested algebraic expressions with negative coefficients without sign errors.",
        "prereq": "MTH-T01-C10-U02",
        "source": "OpenStax Prealgebra 2e — Section 7.3: Distributive Property (Verified HTTP 200).",
        "concepts": [
            "Forward Expansion: $a(b + c) = ab + ac$ and $a(b - c) = ab - ac$. Multiplication distributes over every term inside the parentheses.",
            "Distributing a Negative Sign: A minus sign directly in front of parentheses, $-(b - c + d)$, represents $(-1)(b - c + d) = -b + c - d$, flipping the sign of EVERY term inside the parentheses.",
            "Order of Operations Priority: In an expression like $8 - 3(2x - 5)$, NEVER subtract $8 - 3$ first! Multiplication ($-3$ distributed over $(2x - 5)$) has higher precedence than subtraction: $8 - 6x + 15 = 23 - 6x$."
        ],
        "equation": "a(b + c) = ab + ac, \\qquad -(a - b) = -a + b, \\qquad p - k(qx - r) = p - kqx + kr",
        "worked": "Example: Simplify $12 - 4(3x - 5) - (2x - 7)$.\n1. Distribute $-4$ across $(3x - 5)$ and $-1$ across $(2x - 7)$:\n   $12 - 12x + 20 - 2x + 7$.\n2. Combine like terms: $(-12x - 2x) + (12 + 20 + 7) = -14x + 39$.",
        "exercises": [
            "Simplify completely: (a) $-6(2y - 3) + 4(3y - 5)$, (b) $\\frac{3}{4}(12x - 8) - (5x - 9)$.",
            "Identify and fix the two errors in the student work: $10 - 2(x - 4) = 8(x - 4) = 8x - 4$."
        ],
        "recall": [
            ("Why is $10 - 2(x - 4)$ NOT equal to $8(x - 4)$?", "Because by the Order of Operations, multiplication ($-2$ times $(x-4)$) must be performed before subtracting from $10$: $10 - 2x + 8 = 18 - 2x$."),
            ("What happens to the signs of every term inside parentheses when you simplify $-(4x^2 - 7x + 9)$?", "Every sign inside flips because you are distributing $-1$: $-4x^2 + 7x - 9$.")
        ]
    },
    "MTH-T01-C10-U04": {
        "title": "Properties of Identity, Inverses, and Zero",
        "obj": "Recognize and apply the Identity, Inverse, and Zero Properties of addition and multiplication to simplify expressions and justify equation-solving steps.",
        "out": "Identify and apply additive/multiplicative identities and inverses and zero division rules.",
        "prereq": "MTH-T01-C01-U05, MTH-T01-C10-U03",
        "source": "OpenStax Prealgebra 2e — Section 7.4: Properties of Identity, Inverses, and Zero (Verified HTTP 200).",
        "concepts": [
            "Identity Properties (Leave Value Unchanged): Additive Identity is $0$ ($a + 0 = a$); Multiplicative Identity is $1$ ($a \\cdot 1 = a$).",
            "Inverse Properties (Return to the Identity): Additive Inverse (Opposite) of $a$ is $-a$ because $a + (-a) = 0$. Multiplicative Inverse (Reciprocal) of nonzero $a$ is $\\frac{1}{a}$ because $a \\cdot \\frac{1}{a} = 1$. Zero has NO multiplicative inverse!",
            "Properties of Zero: Multiplication by zero: $a \\cdot 0 = 0$. Zero Product Property preview: if $ab = 0$, then $a = 0$ or $b = 0$. Division with zero: $\\frac{0}{a} = 0$ ($a \\ne 0$), while $\\frac{a}{0}$ is undefined."
        ],
        "equation": "a + 0 = a, \\quad a \\cdot 1 = a, \\qquad a + (-a) = 0, \\quad a \\cdot \\frac{1}{a} = 1 \\ (a \\ne 0)",
        "worked": "Example: For $x = -\\frac{4}{9}$, find its (a) additive inverse and (b) multiplicative inverse, and simplify $\\frac{0}{5x^2 + 1}$ vs. $\\frac{5x^2 + 1}{0}$.\n1. (a) Additive inverse (opposite): $+\\frac{4}{9}$ (sum is $0$).\n2. (b) Multiplicative inverse (reciprocal): $-\\frac{9}{4}$ (product is $+1$).\n3. Since $5x^2 + 1 \\ge 1 \\ne 0$, $\\frac{0}{5x^2 + 1} = 0$, whereas $\\frac{5x^2 + 1}{0}$ is undefined.",
        "exercises": [
            "Find both the additive inverse and the multiplicative inverse of: (a) $-12$, (b) $0.25$, (c) $2\\frac{3}{5}$.",
            "Explain which two properties (Inverse and Identity) are used in sequence when solving $x - 7 = 10$ via $(x - 7) + 7 = x + (-7 + 7) = x + 0 = x$."
        ],
        "recall": [
            ("Why does $0$ have an additive inverse ($0 + 0 = 0$) but NO multiplicative inverse?", "A multiplicative inverse of $0$ would have to be a number $r$ such that $0 \\cdot r = 1$, which is impossible because $0 \\cdot r = 0$ for every real number $r$."),
            ("How do the Multiplicative Inverse Property and Multiplicative Identity Property work together to build equivalent fractions?", "Multiplying $\\frac{a}{b}$ by $\\frac{k}{k}$ ($k \\ne 0$) uses $\\frac{k}{k} = k \\cdot \\frac{1}{k} = 1$ (Inverse Property), and multiplying by $1$ preserves value (Identity Property).")
        ]
    },
    "MTH-T01-C10-U05": {
        "title": "Systems of Measurement",
        "obj": "Perform unit conversions within the US Customary system, within the Metric (SI) system, and between systems using Dimensional Analysis (unit conversion factors).",
        "out": "Convert single and compound measurements across Metric and US units with explicit unit cancellation.",
        "prereq": "MTH-T01-C05-U02, MTH-T01-C07-U02",
        "source": "OpenStax Prealgebra 2e — Section 7.5: Systems of Measurement (Verified HTTP 200).",
        "concepts": [
            "Dimensional Analysis (Unit Factor Method): Any equivalence $1\\text{ unit}_A = k\\text{ units}_B$ forms two unit fractions equal to $1$: $\\frac{1\\text{ unit}_A}{k\\text{ units}_B} = 1$ and $\\frac{k\\text{ units}_B}{1\\text{ unit}_A} = 1$. Multiply the starting measurement by the fraction that places the old unit in the opposite position (numerator vs. denominator) so it cancels.",
            "Metric (SI) Base-10 Prefix Ladder: $\\text{kilo (k)} = 10^3$, $\\text{hecto (h)} = 10^2$, $\\text{deka (da)} = 10^1$, Base unit ($\text{m, g, L}$) $= 10^0$, $\\text{deci (d)} = 10^{-1}$, $\\text{centi (c)} = 10^{-2}$, $\\text{milli (m)} = 10^{-3}$, $\\text{micro (}\\mu\\text{)} = 10^{-6}$.",
            "Temperature Conversions: $F = \\frac{9}{5}C + 32$ and $C = \\frac{5}{9}(F - 32)$."
        ],
        "equation": "x\\text{ unit}_A \\times \\frac{k\\text{ unit}_B}{1\\text{ unit}_A} = (x \\cdot k)\\text{ unit}_B, \\qquad C = \\frac{5}{9}(F - 32)",
        "worked": "Example: Convert $2.45\\text{ kg}$ to milligrams ($\\text{mg}$), and convert $98.6^\\circ\\text{F}$ to Celsius.\n1. $2.45\\text{ kg} \\times \\frac{1000\\text{ g}}{1\\text{ kg}} \\times \\frac{1000\\text{ mg}}{1\\text{ g}} = 2,450,000\\text{ mg} = 2.45 \\times 10^6\\text{ mg}$.\n2. $C = \\frac{5}{9}(98.6 - 32) = \\frac{5}{9}(66.6) = 5(7.4) = 37^\\circ\\text{C}$.",
        "exercises": [
            "Convert using unit factors: (a) $5\\text{ ft } 9\\text{ in}$ to inches and to meters ($1\\text{ in} = 2.54\\text{ cm}$), (b) $350\\text{ mL}$ to liters.",
            "Convert a square area of $3\\text{ m}^2$ into $\\text{cm}^2$ (explain why you must multiply by $\\left(\\frac{100\\text{ cm}}{1\\text{ m}}\\right)^2 = 10,000$!)."
        ],
        "recall": [
            ("Why is $1\\text{ m}^2$ equal to $10,000\\text{ cm}^2$ ($10^4\\text{ cm}^2$) instead of $100\\text{ cm}^2$?", "Because $\\text{m}^2 = \\text{m} \\times \\text{m}$; canceling two factors of meters requires multiplying by $\\frac{100\\text{ cm}}{1\\text{ m}}$ twice: $(100\\text{ cm})^2 = 10,000\\text{ cm}^2$."),
            ("In $C = \\frac{5}{9}(F - 32)$, why are the parentheses around $F - 32$ mandatory?", "Because $0^\\circ\\text{C}$ corresponds to $32^\\circ\\text{F}$, so you must shift the zero point by subtracting $32$ BEFORE scaling the degree size by $\\frac{5}{9}$.")
        ]
    },
    "MTH-T01-C11-U01": {
        "title": "Solve Equations Using the Subtraction and Addition Properties of Equality",
        "obj": "Simplify both sides of a linear equation by distributing and combining like terms, then isolate the variable using the Subtraction and Addition Properties of Equality.",
        "out": "Solve multi-term equations that reduce to $x + c = d$ after simplifying each side.",
        "prereq": "MTH-T01-C03-U05, MTH-T01-C10-U03",
        "source": "OpenStax Prealgebra 2e — Section 8.1: Solve Equations Using the Subtraction and Addition Properties of Equality (Verified HTTP 200).",
        "concepts": [
            "Simplify Each Side Before Moving Terms Across '=': Before adding or subtracting across the equals sign, distribute to clear parentheses and combine like terms on the left side and right side independently.",
            "Distinguishing Within-Side Combination vs. Cross-Side Inverse Operations: Combining $5x - 4x$ on the SAME side uses the distributive property ($(5-4)x = x$). Moving a constant $+9$ to the OTHER side subtracts $9$ from both sides.",
            "Translating Multi-Term Sentences into Equations: Identify the main verb ('is', 'equals', 'is the same as') to place the $=$ sign first."
        ],
        "equation": "\\text{Simplify } L(x) = R \\implies x + c = d \\implies x = d - c",
        "worked": "Example: Solve $4(2x - 3) - 7x = -15 + 8$.\n1. Simplify left side: $8x - 12 - 7x = x - 12$.\n2. Simplify right side: $-15 + 8 = -7$.\n3. Equation is now $x - 12 = -7$. Add $12$ to both sides: $x = 5$.\n4. Check in original: $4(10 - 3) - 35 = 4(7) - 35 = 28 - 35 = -7$, and $-15 + 8 = -7$.",
        "exercises": [
            "Solve and check: (a) $9y - 3 - 8y = -14$, (b) $5(2m - 1) - 9m = -11 + 4$.",
            "Translate and solve: 'The difference of six times a number $n$ and five times the quantity $n$ minus three is $-8$'."
        ],
        "recall": [
            ("In $6x - 5x - 4 = 10$, why do you compute $6x - 5x = x$ instead of adding $5x$ to $6x$?", "Because $6x$ and $-5x$ are already on the SAME side of the equals sign; you simply combine like terms rather than applying an inverse operation across both sides."),
            ("Why should you always substitute your final solution back into the ORIGINAL un-simplified equation rather than an intermediate step?", "If you made a sign or distribution mistake in the very first simplification step, substituting into the intermediate equation will not catch that error.")
        ]
    },
    "MTH-T01-C11-U02": {
        "title": "Solve Equations Using the Division and Multiplication Properties of Equality",
        "obj": "Solve linear equations that simplify to $ax = b$ or $\\frac{x}{a} = b$ by combining like terms first and then dividing or multiplying by the coefficient/reciprocal.",
        "out": "Solve two-step and simplified multi-term equations of the form $ax + b = c$.",
        "prereq": "MTH-T01-C04-U06, MTH-T01-C11-U01",
        "source": "OpenStax Prealgebra 2e — Section 8.2: Solve Equations Using the Division and Multiplication Properties of Equality (Verified HTTP 200).",
        "concepts": [
            "Reverse Order of Operations When Isolating $x$ in $ax + b = c$: When evaluating $ax + b$, you multiply by $a$ first and add $b$ second. To UNDO those operations and isolate $x$, go in reverse order: undo the addition/subtraction ($-b$) FIRST, then undo the multiplication/division ($\\div a$) SECOND!",
            "Fractional Coefficients: For $\\frac{a}{b}x = c$, multiply both sides by the reciprocal $\\frac{b}{a}$.",
            "Negative Sign in Front of a Fraction: $-\\frac{x}{5} = 4$ is equivalent to $\\frac{x}{-5} = 4$; multiply both sides by $-5$ to get $x = -20$."
        ],
        "equation": "ax + b = c \\xrightarrow{-b} ax = c - b \\xrightarrow{\\div a} x = \\frac{c - b}{a} \\quad (a \\ne 0)",
        "worked": "Example: Solve $-3(2x - 4) - x = 33$.\n1. Distribute and combine like terms on the left: $-6x + 12 - x = -7x + 12 = 33$.\n2. Undo $+12$ by subtracting $12$ from both sides: $-7x = 21$.\n3. Undo multiplication by $-7$: $x = \\frac{21}{-7} = -3$. Check: $-3(-6 - 4) - (-3) = -3(-10) + 3 = 33$.",
        "exercises": [
            "Solve and check: (a) $-8w - 15 = 49$, (b) $\\frac{3}{5}k - 7 = -19$, (c) $14 - 5x = -26$.",
            "A technician charges a $\\$65$ diagnostic fee plus $\\$45$ per hour. If the total bill before tax was $\\$222.50$, how many hours did the repair take?"
        ],
        "recall": [
            ("When solving $4x - 9 = 23$, why do we add $9$ to both sides BEFORE dividing by $4$?", "Adding $9$ first isolates the variable term $4x = 32$ cleanly; dividing by $4$ first would require dividing EVERY term by $4$ ($x - \\frac{9}{4} = \\frac{23}{4}$), introducing unnecessary fractions."),
            ("In $14 - 5x = -26$, what is the coefficient of $x$ after you subtract $14$ from both sides?", "The coefficient is $-5$ (not $+5$), leaving $-5x = -40 \\implies x = 8$.")
        ]
    },
    "MTH-T01-C11-U03": {
        "title": "Solve Equations with Variables and Constants on Both Sides",
        "obj": "Apply the general multi-step strategy to solve linear equations with variables and constants on both sides, and classify equations as conditional, identities, or contradictions.",
        "out": "Solve multi-step linear equations with parentheses and variables on both sides, and identify infinite-solution and no-solution cases.",
        "prereq": "MTH-T01-C11-U01, MTH-T01-C11-U02",
        "source": "OpenStax Prealgebra 2e — Section 8.3: Solve Equations with Variables and Constants on Both Sides (Verified HTTP 200).",
        "concepts": [
            "Choosing the Variable Side Strategically: Given $ax + b = cx + d$, move the variable term with the SMALLER coefficient to the other side (e.g., for $3x + 10 = 7x - 2$, subtract $3x$ from both sides) so the resulting variable coefficient stays positive ($4x$).",
            "General Five-Step Strategy: (1) Distribute to clear parentheses on each side; (2) Combine like terms on each side; (3) Collect all variable terms on one side; (4) Collect all constant terms on the opposite side; (5) Divide by the coefficient of the variable and check.",
            "Three Solution Classifications: (a) Conditional Equation: yields a unique solution $x = k$; (b) Identity: variable terms cancel on both sides leaving a TRUE statement like $12 = 12$ (Solution set: all real numbers $\\mathbb{R}$); (c) Contradiction: variable terms cancel leaving a FALSE statement like $5 = -3$ (No solution, $\\emptyset$)."
        ],
        "equation": "ax + b = cx + d \\implies (a - c)x = d - b",
        "worked": "Example: Solve (a) $5(2x - 1) - 3 = 3(4x + 2) - 8$, and classify (b) $2(3x - 4) = 6x - 8$.\n1. (a) Simplify each side: $10x - 5 - 3 = 12x + 6 - 8 \\implies 10x - 8 = 12x - 2$.\n2. Subtract $10x$ and add $2$: $-6 = 2x \\implies x = -3$ (Conditional equation).\n3. (b) $6x - 8 = 6x - 8 \\implies -8 = -8$ (Always true $\\implies$ Identity; all real numbers are solutions).",
        "exercises": [
            "Solve and check: $8 - 2(3y + 1) = 4(y - 5) + 6$.",
            "Solve and classify each as Conditional, Identity, or Contradiction: (a) $4(2x - 3) - 5x = 3(x - 4)$, (b) $7m - 2(m + 4) = 5m + 1$."
        ],
        "recall": [
            ("What happens algebraically when you solve an equation and all variable terms cancel out, leaving $0 = 0$ versus $0 = 7$?", "$0 = 0$ is an Identity (true for every real number $x \\in \\mathbb{R}$), whereas $0 = 7$ is a Contradiction (false for every $x$, so there is no solution)."),
            ("Why is it helpful to subtract the smaller variable term when collecting variables on one side?", "It produces a positive coefficient on the variable term, reducing the chance of dropping a negative sign during the final division step.")
        ]
    },
    "MTH-T01-C11-U04": {
        "title": "Solve Equations with Fraction or Decimal Coefficients",
        "obj": "Clear fractions by multiplying both sides by the LCD and clear decimals by multiplying by $10^k$ to solve complex multi-step linear equations.",
        "out": "Transform any fractional or decimal multi-step linear equation into an equivalent integer equation and solve it.",
        "prereq": "MTH-T01-C04-U06, MTH-T01-C05-U04, MTH-T01-C11-U03",
        "source": "OpenStax Prealgebra 2e — Section 8.4: Solve Equations with Fraction or Decimal Coefficients (Verified HTTP 200).",
        "concepts": [
            "Clearing Fractions in One Step (LCD Strategy): Find the LCD of ALL denominators in the equation and multiply EVERY term on both sides by the LCD. Each denominator cancels with the LCD, leaving a clean integer equation.",
            "Parentheses With Fractional Multipliers: In $\\frac{1}{4}(x + 6) - \\frac{1}{3}(2x - 1) = \\frac{5}{12}$, notice that $\\frac{1}{4}(x + 6)$ is ONE term (a product)! Multiplying that term by $\\text{LCD} = 12$ multiplies the outside fraction $\\frac{1}{4}$ by $12$ to get $3(x + 6)$—do NOT multiply both $\\frac{1}{4}$ and the inside $(x + 6)$ by $12$!",
            "Clearing Decimals in Coin/Mixture Equations: Multiply every term by $100$ (or $10^k$) to work in integer cents."
        ],
        "equation": "\\frac{1}{4}(x + 6) - \\frac{1}{3}(2x - 1) = \\frac{5}{12} \\xrightarrow{\\times 12} 3(x + 6) - 4(2x - 1) = 5",
        "worked": "Example: Solve $\\frac{1}{4}(x + 6) - \\frac{1}{3}(2x - 1) = \\frac{5}{12}$.\n1. Multiply both sides by $\\text{LCD} = 12$: $12 \\cdot \\frac{1}{4}(x + 6) - 12 \\cdot \\frac{1}{3}(2x - 1) = 12 \\cdot \\frac{5}{12}$.\n2. Simplify products: $3(x + 6) - 4(2x - 1) = 5$.\n3. Distribute (watch $-4 \\cdot (-1) = +4$!): $3x + 18 - 8x + 4 = 5 \\implies -5x + 22 = 5$.\n4. $-5x = -17 \\implies x = \\frac{17}{5}$.",
        "exercises": [
            "Solve by clearing fractions first: (a) $\\frac{3}{4}x - \\frac{1}{2} = \\frac{1}{3}x + \\frac{5}{6}$, (b) $\\frac{2x - 3}{6} - \\frac{x - 4}{4} = \\frac{1}{3}$.",
            "Solve by clearing decimals first: $0.05x + 0.10(25 - x) = 1.90$."
        ],
        "recall": [
            ("When multiplying $\\frac{2}{3}(x - 5)$ by $12$, why is the result $8(x - 5)$ and NOT $8(12x - 60)$?", "Because $\\frac{2}{3} \\cdot (x - 5)$ is a single product; by the Associative Property of Multiplication, $12 \\cdot \\left[\\frac{2}{3}(x - 5)\\right] = \\left(12 \\cdot \\frac{2}{3}\\right)(x - 5) = 8(x - 5)$. Multiplying both factors by $12$ would multiply the term by $144$."),
            ("What sign error frequently occurs after clearing denominators in $\\frac{5x}{6} - \\frac{x - 3}{6} = 1$?", "Writing $5x - x - 3 = 6$ instead of wrapping the second numerator in parentheses: $5x - (x - 3) = 5x - x + 3 = 6$.")
        ]
    }
}
