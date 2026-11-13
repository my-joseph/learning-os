# -*- coding: utf-8 -*-
"""
Instructional content for MTH-T01 Units: C05 through C08 (24 Units).
Source: OpenStax Prealgebra 2e (Chapters 5, 6, 10.2/10.5 + Ratios/Exponents extensions).
"""

MTH_UNITS_B = {
    "MTH-T01-C05-U01": {
        "title": "Decimals",
        "obj": "Name and write decimals using negative powers of 10, convert decimals to fractions in lowest terms, order signed decimals, and round decimals.",
        "out": "Convert decimals to reduced fractions and order/round positive and negative decimals accurately.",
        "prereq": "MTH-T01-C01-U01, MTH-T01-C04-U02",
        "source": "OpenStax Prealgebra 2e — Section 5.1: Decimals (Verified HTTP 200).",
        "concepts": [
            "Decimal Place Value Positions: To the right of the decimal point, place values are tenths ($10^{-1} = \\frac{1}{10}$), hundredths ($10^{-2} = \\frac{1}{100}$), thousandths ($10^{-3} = \\frac{1}{1000}$), ten-thousandths ($10^{-4}$), etc.",
            "Reading & Converting Decimals to Fractions: The decimal point is read as 'and'. A decimal with $k$ digits after the decimal point equals the integer formed by those digits divided by $10^k$, then reduced to lowest terms.",
            "Trailing Zeros & Ordering: Appending zeros to the right of the last decimal digit does not change value ($0.4 = 0.400$), making it easy to compare decimals of different lengths."
        ],
        "equation": "0.375 = \\frac{375}{1000} = \\frac{3 \\cdot 125}{8 \\cdot 125} = \\frac{3}{8}",
        "worked": "Example: Order $-0.405, -0.45,$ and $-0.4$ from least to greatest, and convert $-0.32$ to a simplified fraction.\n1. Pad to 3 decimal places: $-0.405, -0.450, -0.400$.\n2. For negative numbers, larger magnitude is further left: $-0.45 < -0.405 < -0.4$.\n3. $-0.32 = -\\frac{32}{100} = -\\frac{8}{25}$.",
        "exercises": [
            "Convert $0.084$ and $-3.625$ to fractions/mixed numbers in lowest terms.",
            "Round $19.9964$ to the nearest (a) thousandth, (b) hundredth, and (c) tenth."
        ],
        "recall": [
            ("Why is $0.7$ equal to $0.700$, whereas $7$ is not equal to $700$?", "In $0.700$, the extra zeros are in the hundredths and thousandths places ($\\frac{7}{10} + \\frac{0}{100} + \\frac{0}{1000} = \\frac{7}{10}$), whereas in $700$ the zeros shift the $7$ from the ones place to the hundreds place."),
            ("When rounding $4.897$ to the nearest hundredth, why must you write $4.90$ and not $4.9$?", "Writing the trailing zero in $4.90$ communicates the precision to which the number was rounded (the hundredths place).")
        ]
    },
    "MTH-T01-C05-U02": {
        "title": "Decimal Operations",
        "obj": "Add, subtract, multiply, and divide positive and negative decimal numbers accurately by hand.",
        "out": "Perform all four operations on signed decimals with correct decimal-point placement.",
        "prereq": "MTH-T01-C03-U04, MTH-T01-C05-U01",
        "source": "OpenStax Prealgebra 2e — Section 5.2: Decimal Operations (Verified HTTP 200).",
        "concepts": [
            "Addition & Subtraction Alignment: Line up the decimal points vertically (aligning matching powers of $10$) and pad missing places with trailing zeros before adding or subtracting.",
            "Multiplication Decimal Count: Do NOT align decimal points to multiply. Multiply as whole numbers, then place the decimal point so the product has the SUM of the number of decimal places in the factors (because $10^{-a} \\cdot 10^{-b} = 10^{-(a+b)}$).",
            "Division Decimal Shift: If the divisor has $k$ decimal places, shift the decimal point $k$ places right in BOTH the divisor and dividend (multiplying the fraction by $\\frac{10^k}{10^k} = 1$) so the divisor becomes a whole number."
        ],
        "equation": "(a \\cdot 10^{-m})(b \\cdot 10^{-n}) = (ab) \\cdot 10^{-(m+n)}, \\qquad \\frac{D}{d} = \\frac{D \\cdot 10^k}{d \\cdot 10^k}",
        "worked": "Example: Compute $(-0.045) \\times 0.12$ and $3.42 \\div (-0.09)$.\n1. Product: $45 \\times 12 = 540$. Count decimal places: $3 + 2 = 5$ places $\\implies -0.00540 = -0.0054$.\n2. Quotient: Shift decimal $2$ places right in both: $342 \\div (-9) = -38$.",
        "exercises": [
            "Compute $20 - 14.087$ and $(-3.06) \\times (-0.015)$ by hand.",
            "Compute $0.1872 \\div 0.024$ and verify by multiplying the quotient by $0.024$."
        ],
        "recall": [
            ("Why do we sum the number of decimal places when multiplying two decimals?", "Because a decimal with $m$ places is $\\frac{A}{10^m}$ and one with $n$ places is $\\frac{B}{10^n}$; their product is $\\frac{AB}{10^{m+n}}$, which has $m+n$ decimal places."),
            ("What mathematical property justifies moving the decimal point the same number of places to the right in both the divisor and dividend?", "The Fundamental Property of Fractions: multiplying both dividend (numerator) and divisor (denominator) by $10^k$ is multiplying by $\\frac{10^k}{10^k} = 1$.")
        ]
    },
    "MTH-T01-C05-U03": {
        "title": "Decimals and Fractions",
        "obj": "Convert fractions to terminating or repeating decimals, order mixed lists of fractions and decimals, and simplify combined expressions.",
        "out": "Convert between fractions and repeating/terminating decimals and evaluate expressions mixing both forms.",
        "prereq": "MTH-T01-C04-U04, MTH-T01-C05-U02",
        "source": "OpenStax Prealgebra 2e — Section 5.3: Decimals and Fractions (Verified HTTP 200).",
        "concepts": [
            "Fraction-to-Decimal Conversion: Divide the numerator by the denominator ($\\frac{a}{b} = a \\div b$). Every rational number produces either a terminating decimal or a repeating decimal (denoted with a vinculum bar, e.g., $\\frac{5}{11} = 0.\\overline{45}$).",
            "When Does a Reduced Fraction Terminate?: A fraction $\\frac{a}{b}$ in lowest terms terminates if and only if the prime factorization of its denominator $b$ contains ONLY factors of $2$ and/or $5$ (the prime factors of $10$).",
            "Mixed-Form Expressions: When an expression mixes fractions and decimals (e.g., $\\frac{3}{8} + 0.45$ or $\\frac{2}{3} \\times 1.8$), convert to a single consistent form—if a fraction is repeating (like $\\frac{2}{3}$), convert the decimal to a fraction to avoid rounding errors!"
        ],
        "equation": "\\frac{a}{2^m \\cdot 5^n} \\text{ terminates}, \\qquad \\frac{7}{12} = 7 \\div 12 = 0.58\\overline{3}",
        "worked": "Example: Compute $\\frac{5}{6} \\cdot 2.4 - 0.75$ exactly.\n1. Since $\\frac{5}{6} = 0.8\\overline{3}$ repeats, convert the decimals to fractions: $2.4 = \\frac{12}{5}$ and $0.75 = \\frac{3}{4}$.\n2. Multiply first: $\\frac{5}{6} \\cdot \\frac{12}{5} = 2$.\n3. Subtract: $2 - \\frac{3}{4} = \\frac{5}{4} = 1.25$.",
        "exercises": [
            "Convert $-\\frac{7}{8}$ and $\\frac{5}{12}$ to decimals (use bar notation for repeating digits).",
            "Order from least to greatest: $-\\frac{3}{5}, -0.65, -\\frac{5}{8}, -0.6\\overline{2}$."
        ],
        "recall": [
            ("How can you tell without dividing that $\\frac{13}{40}$ terminates while $\\frac{13}{30}$ repeats?", "In lowest terms, $40 = 2^3 \\cdot 5$ has only prime factors $2$ and $5$, whereas $30 = 2 \\cdot 3 \\cdot 5$ contains a prime factor of $3$."),
            ("Why should you convert $0.25$ to $\\frac{1}{4}$ when computing $\\frac{1}{3} + 0.25$ instead of converting $\\frac{1}{3}$ to $0.33$?", "Because $\\frac{1}{3} = 0.\\overline{3}$ is an infinite repeating decimal; truncating it to $0.33$ introduces a rounding error, whereas $\\frac{1}{3} + \\frac{1}{4} = \\frac{7}{12}$ is exact.")
        ]
    },
    "MTH-T01-C05-U04": {
        "title": "Solve Equations with Decimals",
        "obj": "Verify solutions to decimal equations and solve one-step and two-step equations containing decimal coefficients and constants.",
        "out": "Solve decimal linear equations directly or by clearing decimals with powers of 10.",
        "prereq": "MTH-T01-C04-U06, MTH-T01-C05-U02",
        "source": "OpenStax Prealgebra 2e — Section 5.4: Solve Equations with Decimals (Verified HTTP 200).",
        "concepts": [
            "Same Equality Properties Apply: The Addition, Subtraction, Multiplication, and Division Properties of Equality work identically for decimals.",
            "Clearing Decimals via Powers of 10: If an equation has decimals with at most $k$ decimal places (e.g., $0.08x - 1.2 = 0.44$ has at most $2$ places), multiplying EVERY term on both sides by $10^k = 100$ converts it into a clean integer equation ($8x - 120 = 44$).",
            "Decimal Division Isolation: When dividing $ax = b$ directly by a decimal $a$, shift the decimal point equally in numerator and denominator."
        ],
        "equation": "0.06x + 0.4 = 1.18 \\xrightarrow{\\times 100} 6x + 40 = 118 \\implies 6x = 78 \\implies x = 13",
        "worked": "Example: Solve $-0.05x - 1.4 = 0.85$.\n1. Multiply every term on both sides by $100$: $-5x - 140 = 85$.\n2. Add $140$ to both sides: $-5x = 225$.\n3. Divide by $-5$: $x = -45$. Check: $-0.05(-45) - 1.4 = 2.25 - 1.4 = 0.85$.",
        "exercises": [
            "Solve and check: (a) $y - 4.73 = -8.2$, (b) $-0.08m = 5.6$.",
            "Solve $0.12x + 0.05(200) = 19.6$ by clearing decimals first."
        ],
        "recall": [
            ("When clearing decimals in $0.25x - 3 = 1.5$ by multiplying by $100$, what common mistake happens with the whole number $3$?", "Forgetting to multiply the whole-number term $-3$ by $100$; every single term on both sides must be multiplied by $100$, giving $25x - 300 = 150$."),
            ("By what power of $10$ should you multiply both sides of $0.4x - 0.075 = 1.2$ to clear all decimals?", "Multiply by $10^3 = 1000$, because the term with the most decimal places ($-0.075$) has $3$ decimal places.")
        ]
    },
    "MTH-T01-C05-U05": {
        "title": "Averages and Probability",
        "obj": "Calculate the mean, median, and mode of a dataset, and compute the basic theoretical probability of an event as a fraction and decimal.",
        "out": "Compute measures of central tendency (mean, median, mode) and basic probabilities accurately.",
        "prereq": "MTH-T01-C05-U03 (Decimals and Fractions)",
        "source": "OpenStax Prealgebra 2e — Section 5.5: Averages and Probability (Verified HTTP 200).",
        "concepts": [
            "Three Measures of Central Tendency: (1) Mean (arithmetic average): sum of all values divided by the count $n$; (2) Median: the middle value when the data is sorted in ascending order (if $n$ is even, the mean of the two middle values); (3) Mode: the value(s) occurring most frequently (a dataset can have no mode, one mode, or multiple modes).",
            "Sensitivity to Outliers: Extreme outliers pull the Mean strongly toward the outlier, whereas the Median remains resistant.",
            "Theoretical Probability: For equally likely outcomes in sample space $S$, $P(E) = \\frac{\\text{number of outcomes favorable to } E}{\\text{total number of outcomes in } S}$, always satisfying $0 \\le P(E) \\le 1$."
        ],
        "equation": "\\bar{x} = \\frac{\\sum_{i=1}^n x_i}{n}, \\qquad 0 \\le P(E) = \\frac{n(E)}{n(S)} \\le 1",
        "worked": "Example: Find the mean, median, and mode of $\\{18, 12, 24, 12, 30, 15\\}$.\n1. Sort first: $12, 12, 15, 18, 24, 30$ ($n = 6$).\n2. Mean: $\\frac{12+12+15+18+24+30}{6} = \\frac{111}{6} = 18.5$.\n3. Median (average of 3rd and 4th values): $\\frac{15 + 18}{2} = 16.5$.\n4. Mode: $12$ (appears twice).",
        "exercises": [
            "Find the mean, median, and mode of the response times (in ms): $42, 38, 45, 190, 38, 43$, and explain why the median better represents typical performance here.",
            "A standard 6-sided die is rolled once. Find the probability of rolling (a) a prime number, (b) a number greater than $4$, expressed as both a reduced fraction and a decimal."
        ],
        "recall": [
            ("What mandatory step must you perform BEFORE finding the median of a list of numbers, and how do you handle an even number of items?", "You must sort the numbers in order from least to greatest. If the count $n$ is even, the median is the mean (average) of the two middle numbers."),
            ("Why can a probability never be negative or greater than $1$?", "Because the number of favorable outcomes $n(E)$ cannot be less than $0$ or greater than the total number of possible outcomes $n(S)$.")
        ]
    },
    "MTH-T01-C05-U06": {
        "title": "Ratios and Rate",
        "obj": "Write ratios of two quantities in simplest fraction form, including ratios of decimals and mixed units, and compute unit rates and unit prices.",
        "out": "Simplify decimal/fractional ratios and compute unit prices to compare value.",
        "prereq": "MTH-T01-C04-U04, MTH-T01-C05-U02",
        "source": "OpenStax Prealgebra 2e — Section 5.6: Ratios and Rate (Verified HTTP 200).",
        "concepts": [
            "Ratios ($a:b$ or $\\frac{a}{b}$): A comparison of two quantities of the same kind by division. Order matters! If the two quantities are measured in convertible units (e.g., $18\\text{ inches}$ to $3\\text{ feet}$), convert them to the SAME unit first so the units cancel.",
            "Clearing Decimals in Ratios: To simplify a ratio of decimals like $\\frac{1.2}{1.8}$, multiply numerator and denominator by $10^k$ to get whole numbers ($\\frac{12}{18} = \\frac{2}{3}$).",
            "Rates vs. Unit Rates: A rate compares two quantities with different units (e.g., $270\\text{ miles}$ in $6\\text{ hours}$). A unit rate has a denominator of $1$ unit ($45\\text{ miles/hour}$); unit price is $\\frac{\\text{Total Cost}}{\\text{Quantity}}$."
        ],
        "equation": "\\text{Unit Rate} = \\frac{a\\text{ units of } A}{b\\text{ units of } B} = \\left(\\frac{a}{b}\\right)\\text{ units of } A \\text{ per } 1\\text{ unit of } B",
        "worked": "Example: Write the ratio of $2.25$ to $3.5$ as a reduced fraction, and compare $16\\text{ oz}$ for $\\$3.68$ vs. $24\\text{ oz}$ for $\\$5.28$.\n1. Ratio: $\\frac{2.25}{3.5} = \\frac{2.25 \\times 100}{3.5 \\times 100} = \\frac{225}{350} = \\frac{9}{14}$.\n2. Unit prices: $\\frac{\\$3.68}{16\\text{ oz}} = \\$0.23/\\text{oz}$ vs. $\\frac{\\$5.28}{24\\text{ oz}} = \\$0.22/\\text{oz}$ ($24\\text{ oz}$ is the lower unit price).",
        "exercises": [
            "Write each ratio as a fraction in lowest terms: (a) $1.68$ to $4.2$, (b) $8\\text{ months}$ to $2\\text{ years}$.",
            "A runner completes $7.5\\text{ km}$ in $30\\text{ minutes}$. Find the runner's speed in $\\text{km/min}$ and $\\text{km/hour}$."
        ],
        "recall": [
            ("Why is the ratio of $40\\text{ minutes}$ to $2\\text{ hours}$ equal to $\\frac{1}{3}$ and not $\\frac{20}{1}$?", "Because both quantities measure time and must be expressed in the same unit before comparing: $2\\text{ hours} = 120\\text{ minutes}$, so $\\frac{40\\text{ min}}{120\\text{ min}} = \\frac{1}{3}$."),
            ("Unlike a simplified fraction where we write $\\frac{5}{1}$ as $5$, why do we keep the $1$ unit in the denominator of a unit rate?", "A rate compares two different units (e.g., $5\\text{ meters per } 1\\text{ second}$), so both units must remain visible.")
        ]
    },
    "MTH-T01-C05-U07": {
        "title": "Simplify and Use Square Roots",
        "obj": "Evaluate principal square roots of perfect squares, estimate irrational square roots between consecutive integers, and apply square roots in formulas.",
        "out": "Evaluate exact principal square roots, bound irrational square roots, and apply $\\sqrt{\\cdot}$ in geometric/physics formulas.",
        "prereq": "MTH-T01-C03-U04, MTH-T01-C05-U02",
        "source": "OpenStax Prealgebra 2e — Section 5.7: Simplify and Use Square Roots (Verified HTTP 200).",
        "concepts": [
            "Principal Square Root ($\\sqrt{m}$): If $n^2 = m$ for $n \\ge 0$, then $\\sqrt{m} = n$. The radical symbol $\\sqrt{\\cdot}$ ALWAYS denotes the non-negative root ($\\sqrt{64} = 8$, never $-8$). Note that $\\sqrt{-64}$ is not a real number because no real number squared is negative.",
            "Bounding Irrational Square Roots: To estimate $\\sqrt{m}$, find the consecutive perfect squares $a^2 < m < (a+1)^2$; then $a < \\sqrt{m} < a + 1$.",
            "Radical Sign as a Grouping Symbol: In $\\sqrt{9 + 16}$, simplify inside the radicand first: $\\sqrt{25} = 5 \\ne \\sqrt{9} + \\sqrt{16} = 7$."
        ],
        "equation": "\\sqrt{a^2 + b^2} \\ne a + b, \\qquad a^2 < m < b^2 \\implies a < \\sqrt{m} < b \\quad (a, b \\ge 0)",
        "worked": "Example: Simplify $-\\sqrt{144}$, $\\sqrt{25 + 144}$, and bound $\\sqrt{70}$ between two consecutive integers.\n1. $-\\sqrt{144} = -(12) = -12$.\n2. $\\sqrt{25 + 144} = \\sqrt{169} = 13$.\n3. Since $64 < 70 < 81$, we have $\\sqrt{64} < \\sqrt{70} < \\sqrt{81} \\implies 8 < \\sqrt{70} < 9$.",
        "exercises": [
            "Simplify: (a) $\\sqrt{196}$, (b) $-\\sqrt{0.81}$, (c) $\\sqrt{\\frac{49}{121}}$, (d) $\\sqrt{36 + 64}$.",
            "Estimate $\\sqrt{115}$ between two consecutive whole numbers and verify which square it is closer to."
        ],
        "recall": [
            ("Why is $-\\sqrt{36}$ a real number ($-6$), whereas $\\sqrt{-36}$ is not a real number?", "In $-\\sqrt{36}$, we take the opposite of the principal square root of $36$. In $\\sqrt{-36}$, we ask for a real number whose square is $-36$, which does not exist since $x^2 \\ge 0$ for all $x \\in \\mathbb{R}$."),
            ("Why does $\\sqrt{9 + 16}$ equal $5$ and not $3 + 4 = 7$?", "The radical bar is a grouping symbol: you must add $9 + 16 = 25$ first before taking the square root $\\sqrt{25} = 5$.")
        ]
    },
    "MTH-T01-C06-U01": {
        "title": "Understand Percent",
        "obj": "Define percent as a ratio per 100, and convert fluently among percents, decimals, and simplified fractions.",
        "out": "Convert any percent (including fractional and decimal percents or percents $>100\\%$ and $<1\\%$) into both a decimal and a reduced fraction.",
        "prereq": "MTH-T01-C05-U03 (Decimals and Fractions)",
        "source": "OpenStax Prealgebra 2e — Section 6.1: Understand Percent (Verified HTTP 200).",
        "concepts": [
            "Meaning of Percent: $p\\%$ means '$p$ per hundred' $= \\frac{p}{100} = p \\times 0.01$. Therefore $100\\% = 1$; percents greater than $100\\%$ represent numbers greater than $1$, and percents less than $1\\%$ (e.g., $0.25\\%$) are less than $0.01$.",
            "Percent <-> Decimal Conversions: Percent to decimal: divide by $100$ (shift decimal point $2$ places LEFT and remove $\\%$). Decimal to percent: multiply by $100\\%$ (shift decimal point $2$ places RIGHT and append $\\%$).",
            "Percent <-> Fraction Conversions: Percent to fraction: replace $\\%$ with $\\times \\frac{1}{100}$ and reduce to lowest terms. Fraction to percent: convert fraction to decimal first (or set up $\\frac{a}{b} \\times 100\\%$).",
        ],
        "equation": "p\\% = \\frac{p}{100} = 0.01p, \\qquad \\frac{a}{b} = \\left(\\frac{a}{b} \\times 100\\right)\\%",
        "worked": "Example: Convert $0.4\\%$, $135\\%$, and $16\\frac{2}{3}\\%$ to decimals and reduced fractions.\n1. $0.4\\% = 0.004 = \\frac{4}{1000} = \\frac{1}{250}$.\n2. $135\\% = 1.35 = \\frac{135}{100} = \\frac{27}{20} = 1\\frac{7}{20}$.\n3. $16\\frac{2}{3}\\% = \\frac{50}{3} \\times \\frac{1}{100} = \\frac{1}{6} = 0.1\\overline{6}$.",
        "exercises": [
            "Convert $0.08\\%$, $6.25\\%$, and $240\\%$ each into a decimal and a simplified fraction.",
            "Convert $\\frac{5}{8}$ and $\\frac{7}{12}$ into percents (give exact fractional percent and rounded to 2 decimal places)."
        ],
        "recall": [
            ("What common mistake happens when converting $0.5\\%$ to a decimal?", "Writing $0.5$ (which is $50\\%$) instead of dividing by $100$ to get $0.005$."),
            ("How do you convert a mixed-number percent like $33\\frac{1}{3}\\%$ into an exact fraction without rounding?", "Write $33\\frac{1}{3}$ as the improper fraction $\\frac{100}{3}$ and multiply by $\\frac{1}{100}$: $\\frac{100}{3} \\cdot \\frac{1}{100} = \\frac{1}{3}$.")
        ]
    },
    "MTH-T01-C06-U02": {
        "title": "Solve General Applications of Percent",
        "obj": "Translate and solve the three cases of the basic percent equation (finding amount, base, or percent) and compute percent increase and percent decrease.",
        "out": "Solve for unknown Amount, Base, or Percent and calculate percent change accurately.",
        "prereq": "MTH-T01-C05-U04, MTH-T01-C06-U01",
        "source": "OpenStax Prealgebra 2e — Section 6.2: Solve General Applications of Percent (Verified HTTP 200).",
        "concepts": [
            "The Three-Component Percent Equation: $\\text{Amount} = \\text{Percent (as decimal)} \\times \\text{Base}$ ($A = p \\cdot B$). In English phrasing, 'is' translates to $=$, 'of' translates to $\\times$, and the quantity immediately following 'of' is the Base $B$.",
            "Percent Increase & Percent Decrease: Always divide the absolute change by the ORIGINAL (starting) value, NEVER the final value!",
            "Asymmetry of Percent Change: Increasing $100$ by $25\\%$ gives $125$, but decreasing $125$ by $25\\%$ takes $25\\%$ of the new base $125$ ($125 - 31.25 = 93.75 \\ne 100$)."
        ],
        "equation": "\\text{Percent Change} = \\frac{\\text{New Value} - \\text{Original Value}}{\\text{Original Value}} \\times 100\\%",
        "worked": "Example: (a) $42$ is $35\\%$ of what number? (b) Server latency dropped from $80\\text{ ms}$ to $52\\text{ ms}$; find the percent decrease.\n1. (a) $42 = 0.35 \\cdot B \\implies B = \\frac{42}{0.35} = \\frac{4200}{35} = 120$.\n2. (b) Change $= 52 - 80 = -28\\text{ ms}$. Divide by ORIGINAL $80$: $\\frac{28}{80} = 0.35 = 35\\%$ decrease.",
        "exercises": [
            "Solve: (a) What number is $18\\%$ of $350$? (b) $68$ is what percent of $80$? (c) $117$ is $65\\%$ of what number?",
            "A cloud subscription increased from $\\$40$ to $\\$50$ per month, and later decreased from $\\$50$ back to $\\$40$. Compute both the percent increase and the subsequent percent decrease."
        ],
        "recall": [
            ("In any percent change problem, why must the denominator always be the ORIGINAL value?", "Because percent change measures the change relative to the starting baseline before the change occurred."),
            ("In the sentence '$72$ is $120\\%$ of what number?', which quantity is the Amount and which is the Base?", "$72$ is the Amount ($A$), $1.20$ is the Percent ($p$), and 'what number' (following 'of') is the unknown Base ($B$).")
        ]
    },
    "MTH-T01-C06-U03": {
        "title": "Solve Sales Tax, Commission, and Discount Applications",
        "obj": "Calculate sales tax, total purchase price, commission, discount amount, sale price, and markups, including reverse pre-tax/original-price problems.",
        "out": "Solve forward and reverse tax, commission, and discount problems without misapplying the base.",
        "prereq": "MTH-T01-C06-U02 (Solve General Applications of Percent)",
        "source": "OpenStax Prealgebra 2e — Section 6.3: Solve Sales Tax, Commission, and Discount Applications (Verified HTTP 200).",
        "concepts": [
            "Sales Tax & Total Cost: $\\text{Tax} = r_{\\text{tax}} \\times \\text{Price}$, so $\\text{Total Cost} = \\text{Price}(1 + r_{\\text{tax}})$.",
            "Discount & Sale Price: $\\text{Discount} = r_{\\text{disc}} \\times \\text{Original Price}$, so $\\text{Sale Price} = \\text{Original Price}(1 - r_{\\text{disc}})$.",
            "Finding the Original Price (Reverse Percent Problem): If you know the Sale Price after a $20\\%$ discount is $\\$160$, do NOT add $20\\%$ of $\\$160$! Instead, solve $0.80 \\cdot P = 160 \\implies P = \\frac{160}{0.80} = \\$200$."
        ],
        "equation": "\\text{Total} = P(1 + r_{\\text{tax}}), \\qquad \\text{Sale Price} = P(1 - r_{\\text{disc}})",
        "worked": "Example: A laptop is on sale for $\\$680$ after a $15\\%$ discount. What was the original list price, and what is the final total with $7\\%$ sales tax?\n1. Sale price is $(1 - 0.15)P = 0.85P = 680 \\implies P = \\frac{680}{0.85} = \\$800$ original list price.\n2. Total with $7\\%$ tax on the sale price: $680(1.07) = \\$727.60$.",
        "exercises": [
            "A real estate agent earns a $3.5\\%$ commission on a home that sells for $\\$420,000$. Find the commission.",
            "After a $25\\%$ discount, a monitor costs $\\$285$. Find the original price before the discount."
        ],
        "recall": [
            ("If a bill including $7\\%$ VAT is $1,070$ Baht, why is the pre-tax price $\\frac{1070}{1.07} = 1,000$ Baht instead of $1070 - 0.07(1070)$?", "Because the $7\\%$ VAT was calculated as $7\\%$ of the unknown pre-tax price $P$ ($P + 0.07P = 1.07P = 1070$), not $7\\%$ of the post-tax total."),
            ("If a store applies a $20\\%$ discount and then an additional $10\\%$ coupon off the reduced price, what is the combined effective discount percent?", "$(1 - 0.20)(1 - 0.10) = 0.80 \\times 0.90 = 0.72$, which is a $28\\%$ discount (not $30\\%$).")
        ]
    },
    "MTH-T01-C06-U04": {
        "title": "Solve Simple Interest Applications",
        "obj": "Use the simple interest formula $I = Prt$ and total amount formula $A = P + I$ to solve for interest, principal, rate, or time (including fractional years).",
        "out": "Solve simple interest problems for any of the four variables ($I, P, r, t$) with consistent time units.",
        "prereq": "MTH-T01-C06-U02",
        "source": "OpenStax Prealgebra 2e — Section 6.4: Solve Simple Interest Applications (Verified HTTP 200).",
        "concepts": [
            "Simple Interest Formula: $I = Prt$, where $I$ is interest earned/owed, $P$ is the principal (initial amount invested/borrowed), $r$ is the ANNUAL interest rate written as a decimal, and $t$ is time expressed in YEARS.",
            "Time Unit Consistency: Since $r$ is an annual rate ('per year'), $t$ must be in years. If time is given in $m$ months, substitute $t = \\frac{m}{12}$ years.",
            "Total Maturity Value: $A = P + I = P + Prt = P(1 + rt)$."
        ],
        "equation": "I = Prt, \\qquad A = P(1 + rt), \\qquad t_{\\text{years}} = \\frac{\\text{months}}{12}",
        "worked": "Example: Find the principal $P$ that must be invested at $4.5\\%$ simple annual interest to earn $\\$270$ in $8\\text{ months}$.\n1. Convert units: $r = 0.045$, $t = \\frac{8}{12} = \\frac{2}{3}\\text{ year}$, $I = 270$.\n2. $270 = P(0.045)\\left(\\frac{2}{3}\\right) = 0.03P$.\n3. $P = \\frac{270}{0.03} = \\$9,000$.",
        "exercises": [
            "Calculate the simple interest and total maturity value on a $\\$12,000$ loan at $6.5\\%$ annual interest for $18\\text{ months}$.",
            "An investment of $\\$5,000$ earned $\\$675$ in simple interest over $3\\text{ years}$. Find the annual interest rate $r$ as a percent."
        ],
        "recall": [
            ("Why must $9\\text{ months}$ be written as $t = \\frac{9}{12} = 0.75$ in $I = Prt$ when $r$ is an annual interest rate?", "Because $r$ has units of $\\text{year}^{-1}$; multiplying by $t$ in years ensures the time units cancel properly."),
            ("How do you solve $I = Prt$ for the interest rate $r$?", "Divide both sides by $Pt$ to get $r = \\frac{I}{Pt}$, then multiply by $100\\%$ to express $r$ as a percentage.")
        ]
    },
    "MTH-T01-C06-U05": {
        "title": "Solve Proportions and their Applications",
        "obj": "Set up and solve proportions using cross-products, apply proportions to similar figures and scale models, and translate percent problems into percent proportions.",
        "out": "Solve rational proportions and similar-triangle / percent-proportion word problems.",
        "prereq": "MTH-T01-C05-U06, MTH-T01-C06-U02",
        "source": "OpenStax Prealgebra 2e — Section 6.5: Solve Proportions and their Applications (Verified HTTP 200).",
        "concepts": [
            "Definition of a Proportion: An equation stating that two ratios or rates are equal: $\\frac{a}{b} = \\frac{c}{d}$ ($b, d \\ne 0$).",
            "Cross-Products Property: Multiplying both sides of $\\frac{a}{b} = \\frac{c}{d}$ by the LCD $bd$ yields $ad = bc$. A proportion is true if and only if its cross-products are equal.",
            "Percent Proportion & Unit Alignment: $\\frac{\\text{Amount}}{\\text{Base}} = \\frac{p}{100}$. In any applied proportion, verify that matching units occupy matching positions ($\\frac{\\text{km}}{\\text{min}} = \\frac{\\text{km}}{\\text{min}}$)."
        ],
        "equation": "\\frac{a}{b} = \\frac{c}{d} \\iff ad = bc \\quad (b, d \\ne 0), \\qquad \\frac{\\text{Amount}}{\\text{Base}} = \\frac{p}{100}",
        "worked": "Example: Solve $\\frac{x}{63} = \\frac{4}{7}$ and find the height $h$ of a tree that casts a $24\\text{ ft}$ shadow when a $6\\text{ ft}$ pole casts a $4\\text{ ft}$ shadow.\n1. $7x = 63 \\cdot 4 \\implies x = \\frac{63 \\cdot 4}{7} = 9 \\cdot 4 = 36$.\n2. Similar triangles: $\\frac{h\\text{ (height)}}{24\\text{ (shadow)}} = \\frac{6\\text{ (height)}}{4\\text{ (shadow)}} \\implies 4h = 144 \\implies h = 36\\text{ ft}$.",
        "exercises": [
            "Solve for the variable: (a) $\\frac{15}{x} = \\frac{25}{40}$, (b) $\\frac{n + 3}{8} = \\frac{5}{4}$.",
            "Rewrite '$45$ is what percent of $72$?' as a percent proportion $\\frac{A}{B} = \\frac{p}{100}$ and solve for $p$."
        ],
        "recall": [
            ("Where does the Cross-Products rule $ad = bc$ come from algebraically?", "It comes directly from multiplying both sides of the equation $\\frac{a}{b} = \\frac{c}{d}$ by the common denominator $bd$."),
            ("What rule ensures you set up a word-problem proportion correctly?", "Keep consistent units in the numerators and consistent units in the denominators across both sides of the equation.")
        ]
    },
    "MTH-T01-C07-U01": {
        "title": "Understanding Ratios",
        "obj": "Model part-to-part and part-to-whole ratios, simplify multi-part ratios ($a:b:c$), and divide a total quantity according to a given ratio.",
        "out": "Convert between part-to-part and part-to-whole ratios and partition quantities by ratio shares.",
        "prereq": "MTH-T01-C05-U06 (Ratios and Rate)",
        "source": "OpenStax Prealgebra 2e — Section 5.6 (Ratios) + Supplementary Ratio Partitioning Module (Verified HTTP 200).",
        "concepts": [
            "Part-to-Part vs. Part-to-Whole Ratios: If a mixture has $3$ parts acid to $5$ parts water (part-to-part ratio $3:5$), the total number of parts is $3 + 5 = 8$, so the part-to-whole fractions are $\\frac{3}{8}$ acid and $\\frac{5}{8}$ water.",
            "Scaling Invariant ($kx : ky$): Representing quantities in ratio $a:b$ as $ax$ and $bx$ (where $x$ is the common scale factor of 1 share) turns ratio problems into simple linear equations.",
            "Multi-Part Ratios ($a:b:c$): If $A:B:C = 2:3:5$, the total shares are $2+3+5 = 10$, and the three quantities are $2x, 3x,$ and $5x$."
        ],
        "equation": "\\text{If } A:B = a:b \\text{ and } A + B = T, \\text{ then } A = \\frac{a}{a+b}T, \\quad B = \\frac{b}{a+b}T",
        "worked": "Example: Divide $\\$1,800$ among three partners in the ratio $2:3:4$.\n1. Let each share be $x$: total shares $= 2x + 3x + 4x = 9x$.\n2. $9x = 1800 \\implies x = 200$.\n3. Shares are $2(200) = \\$400$, $3(200) = \\$600$, and $4(200) = \\$800$ (Sum $= \\$1,800$).",
        "exercises": [
            "The ratio of wins to losses for a team is $7:3$. What fraction and percent of the total games played did the team win?",
            "The perimeter of a triangle is $108\\text{ cm}$, and its side lengths are in the ratio $3:4:5$. Find the length of each side."
        ],
        "recall": [
            ("If the ratio of frontend engineers to backend engineers on a team is $2:5$, why is the fraction of frontend engineers on the team $\\frac{2}{7}$ and not $\\frac{2}{5}$?", "Because $2:5$ is a part-to-part ratio; the whole team consists of $2 + 5 = 7$ parts in total."),
            ("If $A:B = 2:3$ and $B:C = 4:5$, how do you combine them into a single compound ratio $A:B:C$?", "Match the shared term $B$ using $\\text{LCM}(3, 4) = 12$: $A:B = 8:12$ and $B:C = 12:15$, giving $A:B:C = 8:12:15$.")
        ]
    },
    "MTH-T01-C07-U02": {
        "title": "Rates and Unit Rates",
        "obj": "Compute unit rates involving fractions and decimals, convert rates across compound units (e.g., $\\text{km/h}$ to $\\text{m/s}$), and analyze combined work/flow rates.",
        "out": "Compute complex fractional unit rates and convert compound rates using unit-factor cancellation.",
        "prereq": "MTH-T01-C04-U05, MTH-T01-C05-U06",
        "source": "OpenStax Prealgebra 2e — Section 5.6 (Rates) + Supplementary Compound Rate Analysis (Verified HTTP 200).",
        "concepts": [
            "Fractional Unit Rates: If a pump fills $\\frac{3}{4}$ of a tank in $\\frac{2}{5}$ of an hour, the unit rate in tanks per hour is the complex fraction $\\frac{3/4\\text{ tank}}{2/5\\text{ hour}} = \\frac{3}{4} \\cdot \\frac{5}{2} = \\frac{15}{8} = 1\\frac{7}{8}\\text{ tanks/hour}$.",
            "Reciprocal Dual Unit Rates: Every rate $\\frac{A}{B}$ has two valid unit rates: units of $A$ per $1$ unit of $B$ ($\\frac{a}{b}$), and units of $B$ per $1$ unit of $A$ ($\\frac{b}{a}$). Always check the word after 'per' to know which quantity belongs in the denominator!",
            "Compound Unit Conversion: Multiply by unit fractions equal to $1$ (e.g., $\\frac{1000\\text{ m}}{1\\text{ km}}$ and $\\frac{1\\text{ h}}{3600\\text{ s}}$) so old units cancel."
        ],
        "equation": "v\\text{ km/h} \\times \\frac{1000\\text{ m}}{1\\text{ km}} \\times \\frac{1\\text{ h}}{3600\\text{ s}} = \\frac{v}{3.6}\\text{ m/s}",
        "worked": "Example: A 3D printer uses $\\frac{5}{8}\\text{ kg}$ of filament in $2\\frac{1}{2}\\text{ hours}$. Find the rate in (a) $\\text{kg/hour}$ and (b) $\\text{hours/kg}$.\n1. (a) $\\frac{5/8\\text{ kg}}{5/2\\text{ hr}} = \\frac{5}{8} \\cdot \\frac{2}{5} = \\frac{1}{4} = 0.25\\text{ kg/hour}$.\n2. (b) Reciprocal: $\\frac{5/2\\text{ hr}}{5/8\\text{ kg}} = 4\\text{ hours/kg}$.",
        "exercises": [
            "A cyclist travels $12\\frac{3}{5}\\text{ km}$ in $\\frac{3}{4}\\text{ hour}$. Find the unit speed in $\\text{km/hour}$.",
            "Convert $90\\text{ km/hour}$ into $\\text{meters/second}$ showing explicit unit cancellation."
        ],
        "recall": [
            ("How do you decide which quantity goes in the denominator when asked for 'cost per kilogram' versus 'kilograms per dollar'?", "The quantity immediately following the word 'per' (or 'for each') always goes in the denominator."),
            ("Why can you NOT find the average speed of a round trip ($60\\text{ km/h}$ going out, $40\\text{ km/h}$ coming back over the same distance $d$) by averaging $\\frac{60+40}{2} = 50$?", "Because more time is spent traveling at the slower speed. Total distance divided by total time is $\\frac{2d}{d/60 + d/40} = \\frac{2}{5/120} = 48\\text{ km/h}$.")
        ]
    },
    "MTH-T01-C07-U03": {
        "title": "Solving Proportions",
        "obj": "Solve algebraic proportions containing binomial numerators or denominators using cross-multiplication and the distributive property.",
        "out": "Solve linear equations arising from proportions of the form $\\frac{ax+b}{c} = \\frac{dx+e}{f}$.",
        "prereq": "MTH-T01-C06-U05 (Solve Proportions and their Applications)",
        "source": "OpenStax Prealgebra 2e — Section 6.5 (Proportions) + Algebraic Proportion Extension (Verified HTTP 200).",
        "concepts": [
            "Grouping Binomials in Proportions: Remember that fraction bars group multi-term numerators and denominators! When cross-multiplying $\\frac{x - 2}{5} = \\frac{x + 4}{8}$, ALWAYS wrap binomials in parentheses: $8(x - 2) = 5(x + 4)$.",
            "Domain Restriction (Nonzero Denominators): If the variable appears in a denominator (e.g., $\\frac{6}{x - 1} = \\frac{3}{4}$), note the excluded value ($x \\ne 1$) before cross-multiplying.",
            "Simplifying Before Cross-Multiplying: If one side's fraction can be reduced first (e.g., $\\frac{12}{18} = \\frac{2}{3}$), reduce it first to keep cross-products small."
        ],
        "equation": "\\frac{A}{B} = \\frac{C}{D} \\implies D \\cdot (A) = B \\cdot (C) \\quad (B \\ne 0, D \\ne 0)",
        "worked": "Example: Solve $\\frac{2x - 5}{3} = \\frac{x + 2}{4}$.\n1. Cross-multiply with parentheses: $4(2x - 5) = 3(x + 2)$.\n2. Distribute: $8x - 20 = 3x + 6$.\n3. Subtract $3x$ and add $20$: $5x = 26 \\implies x = \\frac{26}{5} = 5.2$.",
        "exercises": [
            "Solve and check: (a) $\\frac{3y + 1}{6} = \\frac{y - 2}{3}$, (b) $\\frac{9}{w - 4} = \\frac{15}{w + 2}$.",
            "Find the value of $x$ such that the ratio of $x - 3$ to $x + 5$ equals $3:5$."
        ],
        "recall": [
            ("What common mistake occurs when cross-multiplying $\\frac{x + 3}{4} = \\frac{5}{2}$ if parentheses are omitted?", "Writing $2x + 3 = 20$ instead of $2(x + 3) = 2x + 6 = 20$."),
            ("Why must you check that a solution to a proportion does not make any denominator equal to $0$?", "Division by zero is undefined; any value that makes a denominator $0$ is an extraneous value and cannot be a valid solution.")
        ]
    },
    "MTH-T01-C07-U04": {
        "title": "Direct Proportion",
        "obj": "Model direct variation ($y = kx$), find the constant of proportionality $k$, and solve direct proportion problems using both $y = kx$ and equal ratios.",
        "out": "Identify direct variation from tables/equations, determine $k = \\frac{y}{x}$, and solve applied scaling problems.",
        "prereq": "MTH-T01-C07-U03 (Solving Proportions)",
        "source": "OpenStax Prealgebra 2e — Section 6.5 + Supplementary Direct Variation Module (Verified HTTP 200).",
        "concepts": [
            "Definition of Direct Variation: Two quantities $x$ and $y$ vary directly ($y \\propto x$) if their ratio is a nonzero constant $k$: $\\frac{y}{x} = k$, or equivalently $y = kx$.",
            "Key Properties of Direct Proportion: (1) When $x = 0$, $y = 0$ (the graph passes through the origin $(0,0)$); (2) Doubling $x$ doubles $y$; multiplying $x$ by $c$ multiplies $y$ by $c$.",
            "Two Solution Methods: Either find the constant of proportionality $k = \\frac{y_1}{x_1}$ first and compute $y_2 = k x_2$, or set up the proportion $\\frac{y_1}{x_1} = \\frac{y_2}{x_2}$."
        ],
        "equation": "y = kx \\iff \\frac{y_1}{x_1} = \\frac{y_2}{x_2} = k",
        "worked": "Example: According to Hooke's Law, the stretch $s$ of a spring varies directly with the attached mass $m$. If a $150\\text{ g}$ mass stretches the spring $6\\text{ cm}$, how far does a $250\\text{ g}$ mass stretch it?\n1. Constant of proportionality: $k = \\frac{s}{m} = \\frac{6}{150} = 0.04\\text{ cm/g}$.\n2. For $m = 250\\text{ g}$: $s = 0.04(250) = 10\\text{ cm}$.",
        "exercises": [
            "If $y$ varies directly as $x$, and $y = 42$ when $x = 12$, find the equation relating $x$ and $y$, and find $y$ when $x = 30$.",
            "Determine whether the table $(x, y) \\in \\{(2, 7), (4, 14), (6, 21)\\}$ vs. $\\{(2, 7), (4, 11), (6, 15)\\}$ represents direct proportion, and explain why."
        ],
        "recall": [
            ("Why does the linear equation $y = 3x + 5$ NOT represent a direct proportion even though $y$ increases as $x$ increases?", "In a direct proportion, the ratio $\\frac{y}{x}$ must be constant and $y$ must equal $0$ when $x = 0$. In $y = 3x + 5$, doubling $x$ from $1$ to $2$ changes $y$ from $8$ to $11$ (not doubled)."),
            ("What is the physical meaning of the constant of proportionality $k = \\frac{y}{x}$ in a direct variation problem?", "$k$ is the unit rate: the amount of change in $y$ per $1$ unit of $x$.")
        ]
    },
    "MTH-T01-C07-U05": {
        "title": "Inverse Proportion",
        "obj": "Model inverse variation ($y = \\frac{k}{x}$ or $xy = k$), distinguish it from direct variation, and solve inverse proportion applications.",
        "out": "Solve inverse variation problems (speed-time, workforce-duration, gear/lever problems) using $x_1 y_1 = x_2 y_2 = k$.",
        "prereq": "MTH-T01-C07-U04 (Direct Proportion)",
        "source": "OpenStax Prealgebra 2e (Proportional Reasoning) + Supplementary Inverse Variation Module (Verified HTTP 200).",
        "concepts": [
            "Definition of Inverse Variation: Two positive quantities $x$ and $y$ vary inversely ($y \\propto \\frac{1}{x}$) if their PRODUCT is a nonzero constant $k$: $x \\cdot y = k$, or equivalently $y = \\frac{k}{x}$.",
            "Scaling Behavior: Doubling $x$ cuts $y$ in HALF; multiplying $x$ by $c$ divides $y$ by $c$ so that $(cx)\\left(\\frac{y}{c}\\right) = xy = k$.",
            "Common Trap — Using Cross-Products on Inverse Proportion: Never set up $\\frac{y_1}{x_1} = \\frac{y_2}{x_2}$ for inverse variation! Instead, equate products: $x_1 y_1 = x_2 y_2$."
        ],
        "equation": "y = \\frac{k}{x} \\iff x_1 y_1 = x_2 y_2 = k",
        "worked": "Example: It takes $6$ servers $40\\text{ minutes}$ to process a batch job. Assuming linear scaling (inverse variation between server count and time), how long will $15$ servers take?\n1. Constant workload: $k = n \\cdot t = 6 \\times 40 = 240\\text{ server-minutes}$.\n2. With $n_2 = 15$ servers: $15 \\cdot t_2 = 240 \\implies t_2 = \\frac{240}{15} = 16\\text{ minutes}$.",
        "exercises": [
            "At a constant temperature (Boyle's Law), gas pressure $P$ varies inversely with volume $V$. If $P = 120\\text{ kPa}$ when $V = 4\\text{ L}$, find the pressure when the volume is compressed to $1.5\\text{ L}$.",
            "For each scenario, state whether the variables are in Direct Proportion, Inverse Proportion, or Neither: (a) Speed vs. travel time for a fixed $300\\text{ km}$ trip; (b) Hours worked vs. pay at a fixed hourly wage."
        ],
        "recall": [
            ("How do you test a table of $(x, y)$ values to tell whether it represents direct variation or inverse variation?", "Check whether the ratio $\\frac{y}{x}$ is constant across all pairs (Direct Variation) or whether the product $x \\cdot y$ is constant across all pairs (Inverse Variation)."),
            ("Why does setting up $\\frac{6\\text{ workers}}{40\\text{ min}} = \\frac{15\\text{ workers}}{t\\text{ min}}$ give a nonsensical answer ($100\\text{ min}$)?", "Because it treats an inverse relationship as a direct proportion, claiming that adding more workers increases the time required instead of keeping total work $n \\cdot t$ constant.")
        ]
    },
    "MTH-T01-C07-U06": {
        "title": "Applications of Proportions",
        "obj": "Apply direct and inverse proportional reasoning to scale drawings, maps, similar geometric figures, mixture scaling, and joint rate problems.",
        "out": "Solve multi-step applied proportion problems by first classifying the relationship and verifying units.",
        "prereq": "MTH-T01-C07-U04, MTH-T01-C07-U05",
        "source": "OpenStax Prealgebra 2e — Section 6.5 & 9.3 (Proportions & Similar Figures) (Verified HTTP 200).",
        "concepts": [
            "Scale Drawings & Maps: A scale $1 : s$ means $1$ unit on the drawing represents $s$ of the same units in reality. Note that while linear lengths scale by $s$, 2D areas scale by $s^2$!",
            "Similar Polygons: Two figures are similar if their corresponding angles are equal and the ratios of their corresponding side lengths are equal (constant scale factor).",
            "Decision Protocol for Applied Problems: Before writing an equation, ask: 'If quantity $X$ doubles while holding constraints fixed, does $Y$ double ($\\frac{y_1}{x_1} = \\frac{y_2}{x_2}$) or halve ($x_1 y_1 = x_2 y_2$)?'"
        ],
        "equation": "\\text{Linear Scale} = k \\implies \\text{Area Scale} = k^2, \\quad \\text{Volume Scale} = k^3",
        "worked": "Example: An architectural blueprint uses a scale of $2\\text{ cm} : 5\\text{ m}$. A rectangular hall measures $6\\text{ cm}$ by $4\\text{ cm}$ on the blueprint. Find its actual dimensions and actual area in $\\text{m}^2$.\n1. Unit scale: $1\\text{ cm}$ represents $2.5\\text{ m}$.\n2. Actual length $= 6 \\times 2.5 = 15\\text{ m}$; actual width $= 4 \\times 2.5 = 10\\text{ m}$.\n3. Actual area $= 15 \\times 10 = 150\\text{ m}^2$ (Notice: blueprint area $24\\text{ cm}^2 \\times 2.5^2 = 150\\text{ m}^2$).",
        "exercises": [
            "A gear with $36$ teeth rotating at $150\\text{ rpm}$ meshes with a smaller gear with $18$ teeth. Find the rotation speed of the smaller gear (hint: teeth count $\\times$ rpm is constant!).",
            "On a map with scale $1.5\\text{ cm} = 40\\text{ km}$, two cities are $5.25\\text{ cm}$ apart. How long will it take to drive between them at an average speed of $70\\text{ km/h}$?"
        ],
        "recall": [
            ("If the side lengths of a triangle are tripled (scale factor $k = 3$), by what factor does its perimeter increase, and by what factor does its area increase?", "Its perimeter (a 1D length) increases by a factor of $k = 3$, whereas its area (2D) increases by a factor of $k^2 = 3^2 = 9$."),
            ("Why do two meshing gears obey an inverse proportion ($T_1 \\cdot \\omega_1 = T_2 \\cdot \\omega_2$) between number of teeth $T$ and angular speed $\\omega$?", "Because the same number of teeth must pass the contact point per minute on both gears ($T_1 \\omega_1 = T_2 \\omega_2$), so the smaller gear with fewer teeth must spin faster.")
        ]
    },
    "MTH-T01-C08-U01": {
        "title": "Introduction to Exponents",
        "obj": "Identify the base and exponent in exponential expressions, evaluate powers of integers, fractions, and decimals, and distinguish $-a^n$ from $(-a)^n$.",
        "out": "Evaluate exponential expressions across whole, integer, fractional, and decimal bases without scope/sign errors.",
        "prereq": "MTH-T01-C03-U04, MTH-T01-C04-U04",
        "source": "OpenStax Prealgebra 2e — Section 10.2: Use Multiplication Properties of Exponents (Verified HTTP 200).",
        "concepts": [
            "Base & Exponent Binding Scope: An exponent $n$ applies ONLY to the symbol or parenthesized group immediately to its left. Thus: $(-a)^n$ has base $-a$; $-a^n = -(a^n)$ has base $a$; $3x^2 = 3 \\cdot (x^2)$ has base $x$ (whereas $(3x)^2 = 9x^2$ has base $3x$).",
            "Fractional Bases Require Parentheses: $\\left(\\frac{2}{3}\\right)^3 = \\frac{2^3}{3^3} = \\frac{8}{27}$, whereas $\\frac{2^3}{3} = \\frac{8}{3}$.",
            "Behavior of Powers When $0 < a < 1$: Squaring or cubing a positive proper fraction or decimal between $0$ and $1$ produces a SMALLER number (e.g., $(0.2)^2 = 0.04 < 0.2$)."
        ],
        "equation": "a^n = \\underbrace{a \\cdot a \\cdots a}_{n\\text{ factors}}, \\qquad -a^n = -(a^n) \\ne (-a)^n \\text{ (for even } n\\text{)}",
        "worked": "Example: Evaluate (a) $-2^4$, (b) $(-2)^4$, (c) $-(-2)^3$, and (d) $5x^3$ at $x = -2$.\n1. (a) $-2^4 = -(2 \\cdot 2 \\cdot 2 \\cdot 2) = -16$.\n2. (b) $(-2)^4 = (-2)(-2)(-2)(-2) = +16$.\n3. (c) $-(-2)^3 = -(-8) = +8$.\n4. (d) $5(-2)^3 = 5(-8) = -40$.",
        "exercises": [
            "Evaluate: (a) $\\left(-\\frac{3}{4}\\right)^3$, (b) $-\\left(\\frac{3}{4}\\right)^2$, (c) $(0.3)^4$.",
            "Evaluate $2a^2 - (2a)^2$ when $a = -3$."
        ],
        "recall": [
            ("In the expression $4x^3$, what is the base of the exponent $3$?", "The base is $x$ only (not $4x$). The coefficient $4$ is multiplied by $x^3$ after the exponent is evaluated."),
            ("Why is $(0.5)^3 = 0.125$ smaller than $0.5$, whereas $5^3 = 125$ is larger than $5$?", "Multiplying by a positive number less than $1$ scales the quantity down ($\\frac{1}{2}$ of $\\frac{1}{2}$ of $\\frac{1}{2} = \\frac{1}{8}$).")
        ]
    },
    "MTH-T01-C08-U02": {
        "title": "Multiplication Properties of Exponents",
        "obj": "Derive and apply the Product Property of Exponents ($a^m \\cdot a^n = a^{m+n}$) to simplify numerical and multi-variable monomial products.",
        "out": "Multiply monomials and exponential expressions with the same base accurately.",
        "prereq": "MTH-T01-C08-U01 (Introduction to Exponents)",
        "source": "OpenStax Prealgebra 2e — Section 10.2: Use Multiplication Properties of Exponents (Verified HTTP 200).",
        "concepts": [
            "Product Property Derivation: Counting total factors of base $a$: $a^m \\cdot a^n = (\\underbrace{a \\cdots a}_{m})(\\underbrace{a \\cdots a}_{n}) = \\underbrace{a \\cdots a}_{m+n} = a^{m+n}$.",
            "Keep the Base Unchanged: When multiplying powers with the same base, add the exponents and KEEP the common base: $2^3 \\cdot 2^4 = 2^7$ (NEVER multiply the bases to get $4^7$!).",
            "Multiplying Monomials: By the Commutative and Associative Properties of Multiplication, multiply numerical coefficients together and add exponents of matching variable bases: $(ax^m)(bx^n) = (ab)x^{m+n}$."
        ],
        "equation": "a^m \\cdot a^n = a^{m+n}, \\qquad (c_1 x^m y^p)(c_2 x^n y^q) = (c_1 c_2) x^{m+n} y^{p+q}",
        "worked": "Example: Simplify $(-4x^3y)(-6x^5y^4)$ and $3^4 \\cdot 3^5$.\n1. Multiply coefficients: $(-4)(-6) = 24$.\n2. Add exponents of like bases (note $y = y^1$): $x^{3+5} y^{1+4} = x^8 y^5 \\implies 24x^8y^5$.\n3. $3^4 \\cdot 3^5 = 3^{4+5} = 3^9$ (base stays $3$).",
        "exercises": [
            "Simplify: (a) $x^7 \\cdot x \\cdot x^4$, (b) $5^3 \\cdot 5^6$, (c) $(-3a^4b^2)(7ab^5)(-2a^2)$.",
            "Contrast and simplify both: $2x^3 + 5x^3$ versus $(2x^3)(5x^3)$."
        ],
        "recall": [
            ("Why is $5^2 \\cdot 5^4 = 5^6$ and NOT $25^6$?", "Because $5^2 \\cdot 5^4$ means $(5 \\cdot 5) \\cdot (5 \\cdot 5 \\cdot 5 \\cdot 5)$, which is $6$ factors of $5$ multiplied together ($5^6$), not $6$ factors of $25$."),
            ("What invisible exponent must you remember when multiplying $y^4 \\cdot y$?", "A bare variable $y$ has an unwritten exponent of $1$ ($y = y^1$), so $y^4 \\cdot y^1 = y^{4+1} = y^5$.")
        ]
    },
    "MTH-T01-C08-U03": {
        "title": "Division Properties of Exponents",
        "obj": "Derive and apply the Quotient Property of Exponents ($\\frac{a^m}{a^n} = a^{m-n}$) and Quotient to a Power Property to simplify monomial quotients.",
        "out": "Simplify quotients of exponential expressions and multi-variable monomials.",
        "prereq": "MTH-T01-C08-U02 (Multiplication Properties of Exponents)",
        "source": "OpenStax Prealgebra 2e — Section 10.4: Divide Monomials (Verified HTTP 200).",
        "concepts": [
            "Quotient Property Derivation: For $a \\ne 0$, canceling common factors of $a$ between numerator and denominator gives $\\frac{a^m}{a^n} = a^{m-n}$ (or $\\frac{1}{a^{n-m}}$ when $n > m$ to keep exponents positive).",
            "Coefficients vs. Exponents in Division: Divide (reduce) the numerical coefficients using normal fraction reduction, while SUBTRACTING the exponents of like bases!",
            "Identical Numerator & Denominator: For any $a \\ne 0$, $\\frac{a^m}{a^m} = 1$."
        ],
        "equation": "\\frac{a^m}{a^n} = a^{m-n} \\quad (a \\ne 0), \\qquad \\frac{c_1 x^m}{c_2 x^n} = \\left(\\frac{c_1}{c_2}\\right) x^{m-n}",
        "worked": "Example: Simplify $\\frac{-24x^7y^3}{18x^2y^9}$.\n1. Reduce numerical fraction $\\frac{-24}{18} = -\\frac{4}{3}$.\n2. For $x$: $m > n$, so $x^{7-2} = x^5$ in the numerator.\n3. For $y$: $9 > 3$, so $y^{9-3} = y^6$ remains in the denominator.\n4. Result: $-\\frac{4x^5}{3y^6}$.",
        "exercises": [
            "Simplify: (a) $\\frac{m^{11}}{m^4}$, (b) $\\frac{7^8}{7^6}$, (c) $\\frac{35a^6b^4}{-14a^9b}$.",
            "Simplify $\\frac{(x^4 \\cdot x^5)}{x^3}$."
        ],
        "recall": [
            ("In $\\frac{12x^8}{4x^2}$, why is the result $3x^6$ instead of $3x^4$ or $8x^6$?", "The coefficients $12$ and $4$ are divided ($12 \\div 4 = 3$), whereas the exponents of the common base $x$ are subtracted ($8 - 2 = 6$)."),
            ("When simplifying $\\frac{x^3}{x^8}$ by canceling $x^3$ from top and bottom, why is the numerator $1$ ($\\frac{1}{x^5}$) and not $0$?", "Because $x^3 \\div x^3 = 1$, leaving $1$ in the numerator.")
        ]
    },
    "MTH-T01-C08-U04": {
        "title": "Power Rules of Exponents",
        "obj": "Derive and apply the Power Property $((a^m)^n = a^{mn})$, Product to a Power $((ab)^n = a^n b^n)$, and Quotient to a Power $(\\left(\\frac{a}{b}\\right)^n = \\frac{a^n}{b^n})$.",
        "out": "Simplify nested powers of products and quotients without confusing $(a^m)^n$ with $a^m \\cdot a^n$ or $(a+b)^n$.",
        "prereq": "MTH-T01-C08-U02, MTH-T01-C08-U03",
        "source": "OpenStax Prealgebra 2e — Section 10.2 & 10.4 (Power, Product-to-Power, Quotient-to-Power) (Verified HTTP 200).",
        "concepts": [
            "Power of a Power $((a^m)^n = a^{mn})$: Raising $a^m$ to the $n$-th power multiplies $n$ copies of $a^m$ together, adding the exponent $m$ to itself $n$ times: $m \\cdot n$.",
            "Product & Quotient to a Power: $(ab)^n = a^n b^n$ and $\\left(\\frac{a}{b}\\right)^n = \\frac{a^n}{b^n}$ ($b \\ne 0$). Don't forget to raise the numerical coefficient to the outer power too: $(-3x^4)^2 = (-3)^2 (x^4)^2 = 9x^8$!",
            "Crucial Warning — Exponents Do NOT Distribute Over Addition/Subtraction: $(a + b)^2 = a^2 + 2ab + b^2 \\ne a^2 + b^2$!"
        ],
        "equation": "(a^m)^n = a^{mn}, \\qquad (ab)^n = a^n b^n, \\qquad \\left(\\frac{a}{b}\\right)^n = \\frac{a^n}{b^n} \\quad (b \\ne 0)",
        "worked": "Example: Simplify $(-2x^3y^2)^4 \\cdot (3xy^5)^2$.\n1. Apply Power Rules to each factor first: $(-2)^4 (x^3)^4 (y^2)^4 = 16x^{12}y^8$, and $3^2 x^2 (y^5)^2 = 9x^2y^{10}$.\n2. Multiply the resulting monomials: $(16 \\cdot 9) x^{12+2} y^{8+10} = 144x^{14}y^{18}$.",
        "exercises": [
            "Simplify: (a) $(-5a^4b)^3$, (b) $\\left(\\frac{-2x^3}{3y^4}\\right)^3$.",
            "Simplify $\\frac{(2m^2n^3)^4}{(4mn^2)^2}$ completely."
        ],
        "recall": [
            ("How do you remember when to ADD exponents ($x^3 \\cdot x^4 = x^7$) versus when to MULTIPLY exponents ($(x^3)^4 = x^{12}$)?", "When multiplying two bases ($x^3 \\cdot x^4$), add their exponents. When raising a single base with an exponent to another power ($(x^3)^4$), multiply the exponents."),
            ("Why is $(x + 3)^2$ NOT equal to $x^2 + 9$?", "Because the product-to-a-power rule $(ab)^n = a^n b^n$ only applies to multiplication, never addition. $(x+3)^2 = (x+3)(x+3) = x^2 + 6x + 9$.")
        ]
    },
    "MTH-T01-C08-U05": {
        "title": "Negative and Zero Exponents",
        "obj": "Derive the Zero Exponent Property ($a^0 = 1$) and Negative Exponent Property ($a^{-n} = \\frac{1}{a^n}$), and rewrite exponential expressions with positive exponents only.",
        "out": "Simplify expressions containing zero and negative exponents accurately without confusing negative exponents with negative signs.",
        "prereq": "MTH-T01-C08-U03, MTH-T01-C08-U04",
        "source": "OpenStax Prealgebra 2e — Section 10.4 & 10.5: Integer Exponents (Verified HTTP 200).",
        "concepts": [
            "Zero Exponent Property ($a^0 = 1$ for $a \\ne 0$): From the Quotient Rule, $1 = \\frac{a^n}{a^n} = a^{n-n} = a^0$. Careful with scope: $5x^0 = 5(1) = 5$, whereas $(5x)^0 = 1$ ($x \\ne 0$). Note: $0^0$ is undefined/indeterminate.",
            "Negative Exponent = Reciprocal (NOT a Negative Number!): For $a \\ne 0$, $a^{-n} = \\frac{1}{a^n}$ and $\\frac{1}{a^{-n}} = a^n$, and $\\left(\\frac{a}{b}\\right)^{-n} = \\left(\\frac{b}{a}\\right)^n$. A negative exponent flips the base across the fraction bar and becomes positive; it NEVER changes the sign of the coefficient!",
            "Only Move Factors That Have Negative Exponents: In $4x^{-3}$, the exponent $-3$ applies ONLY to $x$, so $4x^{-3} = \\frac{4}{x^3}$ (the $4$ stays in the numerator because its exponent is $+1$)."
        ],
        "equation": "a^0 = 1 \\ (a \\ne 0), \\qquad a^{-n} = \\frac{1}{a^n}, \\qquad \\frac{1}{a^{-n}} = a^n, \\qquad \\left(\\frac{a}{b}\\right)^{-n} = \\left(\\frac{b}{a}\\right)^n",
        "worked": "Example: Simplify $\\frac{6x^{-2}y^3}{15x^4y^{-5}}$ and $\\left(\\frac{-2a^3}{b^{-2}}\\right)^{-3}$ with positive exponents only.\n1. First expression: reduce $\\frac{6}{15} = \\frac{2}{5}$, combine exponents $x^{-2-4} = x^{-6}$ and $y^{3-(-5)} = y^8 \\implies \\frac{2y^8}{5x^6}$.\n2. Second expression: flip fraction for outer $-3$: $\\left(\\frac{b^{-2}}{-2a^3}\\right)^3 = \\frac{b^{-6}}{-8a^9} = -\\frac{1}{8a^9b^6}$.",
        "exercises": [
            "Evaluate: (a) $-7^0 + (-7)^0$, (b) $3^{-2} + 2^{-3}$, (c) $\\left(-\\frac{3}{5}\\right)^{-2}$.",
            "Simplify $\\frac{(-3x^{-1}y^2)^2}{9x^3y^{-4}}$ using only positive exponents."
        ],
        "recall": [
            ("Why is $3x^{-2}$ equal to $\\frac{3}{x^2}$ and NOT $\\frac{1}{3x^2}$ or $-9x^2$?", "A negative exponent indicates a reciprocal (not a negative number), and in $3x^{-2}$ the exponent $-2$ binds only to $x$, while $3$ has exponent $+1$."),
            ("Use the Quotient Property of Exponents on $\\frac{a^3}{a^5}$ to show why $a^{-2} = \\frac{1}{a^2}$.", "By canceling factors, $\\frac{a^3}{a^5} = \\frac{1}{a^2}$. By the Quotient Rule, $\\frac{a^3}{a^5} = a^{3-5} = a^{-2}$. Therefore $a^{-2} = \\frac{1}{a^2}$.")
        ]
    },
    "MTH-T01-C08-U06": {
        "title": "Scientific Notation",
        "obj": "Convert between decimal notation and normalized scientific notation ($a \\times 10^n$), and multiply and divide numbers in scientific notation.",
        "out": "Convert very large and very small numbers to scientific notation and compute products/quotients in normalized scientific notation.",
        "prereq": "MTH-T01-C05-U02, MTH-T01-C08-U05",
        "source": "OpenStax Prealgebra 2e — Section 10.5: Integer Exponents and Scientific Notation (Verified HTTP 200).",
        "concepts": [
            "Normalized Scientific Notation Form: A nonzero number is in scientific notation when written as $a \\times 10^n$, where the significand (mantissa) satisfies $1 \\le |a| < 10$ (exactly ONE nonzero digit to the left of the decimal point) and $n \\in \\mathbb{Z}$.",
            "Sign of the Exponent $n$: Numbers with magnitude $\\ge 10$ have a POSITIVE power of $10$ (e.g., $45,000 = 4.5 \\times 10^4$); positive numbers between $0$ and $1$ have a NEGATIVE power of $10$ (e.g., $0.00045 = 4.5 \\times 10^{-4}$).",
            "Re-Normalizing After Multiplication/Division: Multiply/divide the significands and add/subtract the powers of $10$. If the resulting significand is $\\ge 10$ or $< 1$ (e.g., $24 \\times 10^5$ or $0.4 \\times 10^{-3}$), rewrite the significand in scientific notation and combine powers of $10$ ($2.4 \\times 10^1 \\times 10^5 = 2.4 \\times 10^6$)."
        ],
        "equation": "x = a \\times 10^n \\quad (1 \\le |a| < 10,\\ n \\in \\mathbb{Z})",
        "worked": "Example: Compute $\\frac{(6.4 \\times 10^{-4})(5.0 \\times 10^9)}{8.0 \\times 10^{-2}}$ in normalized scientific notation.\n1. Combine significands: $\\frac{6.4 \\times 5.0}{8.0} = \\frac{32}{8} = 4.0$.\n2. Combine powers of $10$: $10^{-4 + 9 - (-2)} = 10^{7}$.\n3. Result: $4.0 \\times 10^7$ (already normalized since $1 \\le 4.0 < 10$).",
        "exercises": [
            "Convert $0.00000708$ and $94,600,000,000$ to scientific notation.",
            "Compute $(7.5 \\times 10^6)(4.0 \\times 10^{-11})$ and express the final answer in normalized scientific notation."
        ],
        "recall": [
            ("Why is $35.2 \\times 10^4$ NOT in proper scientific notation, and how do you normalize it?", "Because the coefficient $35.2$ does not satisfy $1 \\le |a| < 10$. Since $35.2 = 3.52 \\times 10^1$, we write $(3.52 \\times 10^1) \\times 10^4 = 3.52 \\times 10^5$."),
            ("How do you avoid mixing up which direction shifts the exponent positively vs. negatively when converting to scientific notation?", "Use magnitude intuition: if the original number is large ($\\ge 10$), the exponent on $10$ is positive; if the original number is a small decimal ($< 1$), the exponent on $10$ is negative.")
        ]
    }
}
