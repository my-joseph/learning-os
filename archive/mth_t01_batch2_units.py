# -*- coding: utf-8 -*-
"""
Unit-level curriculum and practice guide data for MTH-T01 Batch 2 (30 Units: C05-U01 through C09-U06).
Each unit features rigorous mathematical formulations, worked examples, 4-category Practice Guides,
and Active Recall questions with full step-by-step Reference Solutions.
"""

UNIT_DATA = {
    # =========================================================================
    # CHAPTER C05: DECIMALS (7 Units)
    # =========================================================================
    "MTH-T01-C05-U01": {
        "title": "Decimals",
        "chapter": "MTH-T01-C05",
        "objective": "Name, write, and identify place values of decimals, and convert terminating decimals to simplified fractions.",
        "expected_output": "Fluency in identifying negative powers of 10 place values and converting decimals to reduced fractions.",
        "concepts": [
            "**Decimal Place Value Hierarchy:** Positions right of the decimal point represent $10^{-1}$ (tenths), $10^{-2}$ (hundredths), $10^{-3}$ (thousandths), $10^{-4}$ (ten-thousandths).",
            "**Fractional Equivalence:** A terminating decimal with $k$ decimal places converts to a fraction with denominator $10^k$ (e.g., $0.045 = \\frac{45}{1000} = \\frac{9}{200}$).",
            "**Ordering Decimals:** Pad numbers with trailing zeros to identical decimal lengths before comparing magnitudes.",
        ],
        "formulas": [
            "0.d_1 d_2 d_3 = \\frac{d_1}{10} + \\frac{d_2}{100} + \\frac{d_3}{1000} = \\frac{d_1 d_2 d_3}{1000}"
        ],
        "example": {
            "title": "Converting Decimal to Lowest Terms Fraction & Ordering",
            "steps": [
                "Convert $0.375$ to a fraction: The last digit is in the thousandths place, so write as $\\frac{375}{1000}$.",
                "Simplify: Divide numerator and denominator by $\\gcd(375, 1000) = 125$:",
                "\\frac{375 \\div 125}{1000 \\div 125} = \\frac{3}{8}",
                "Compare $-0.45$, $-0.405$, and $-0.4$: Pad to 3 decimal places $\\implies -0.450, -0.405, -0.400$.",
                "Order from least to greatest: $-0.450 < -0.405 < -0.400$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Explain why $0.7 = 0.700$ but $7 \\neq 700$.",
                "Prove why every terminating decimal represents a rational number.",
            ],
            "computational": [
                "Convert $0.064$ and $-2.85$ to lowest-term fractions/mixed numbers.",
                "Order from least to greatest: $0.34, 0.304, 0.344, 0.3$.",
            ],
            "traps": [
                "Negative ordering trap: Believing $-0.45 > -0.405$ because $45 > 40.5$. On the negative number line, greater magnitude is further left!",
                "Place-value shift trap: Miscounting digits when converting $0.008$ to $8/100$ instead of $8/1000$.",
            ],
            "cross": [
                "Programming ([[PRG-T01]]): Float representation and base-2 precision limits in IEEE 754.",
                "Physics ([[PHY-T01]]): Significant figures and scale precision in micrometer readings.",
            ],
        },
        "active_recall": [
            {
                "q": "Why does adding zeros to the right of a decimal not change its value?",
                "a": "Adding trailing zeros adds terms with 0 in smaller fractional place values ($0 \\times 10^{-k} = 0$), which does not change the numeric sum.",
            },
            {
                "q": "How do you systematically convert any terminating decimal into a fraction in lowest terms?",
                "a": "Count the number of decimal digits $n$. Write the digits as numerator over denominator $10^n$, then divide numerator and denominator by their greatest common divisor (GCD).",
            },
        ],
    },
    "MTH-T01-C05-U02": {
        "title": "Decimal Operations",
        "chapter": "MTH-T01-C05",
        "objective": "Perform vertical addition, subtraction, multiplication, and long division with signed decimal numbers.",
        "expected_output": "Mastery of decimal point alignment rules in addition/subtraction and place counting in multiplication/division.",
        "concepts": [
            "**Addition & Subtraction Alignment:** Decimal points must be vertically aligned so identical place values combine.",
            "**Multiplication Rule:** Multiply as whole numbers, then place the decimal point so the product has total decimal places equal to the sum of decimal places in the factors.",
            "**Division Invariant:** Shift the decimal point in both divisor and dividend until the divisor is an integer before executing long division.",
        ],
        "formulas": [
            "\\text{Total Places in Product} = \\text{Places in Factor 1} + \\text{Places in Factor 2}",
            "\\frac{a}{b} = \\frac{a \\times 10^k}{b \\times 10^k}",
        ],
        "example": {
            "title": "Multiplication & Division of Decimals",
            "steps": [
                "Multiply $0.045 \\times 0.6$: Count places ($3 + 1 = 4$ total decimal places).",
                "Compute integer product: $45 \\times 6 = 270$.",
                "Shift left 4 places: $0.0270 = 0.027$.",
                "Divide $4.68 \\div 0.12$: Shift decimal 2 places in both numbers $\\implies 468 \\div 12$.",
                "Evaluate long division: $468 \\div 12 = 39$ exactly.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Explain why $0.2 \\times 0.3 = 0.06$ instead of $0.6$.",
                "Why does dividing by a number less than 1 increase the value?",
            ],
            "computational": [
                "Evaluate: $15.4 - 8.927 + 4.15$.",
                "Evaluate: $(-0.075) \\times (-0.4)$.",
                "Compute quotient: $0.1872 \\div 0.036$.",
            ],
            "traps": [
                "Column misalignment: Aligning by the rightmost digit instead of decimal point in subtraction.",
                "Forgotten shift: Dividing $4.68 \\div 0.12$ by shifting only the divisor.",
            ],
            "cross": [
                "Physics ([[PHY-T01]]): Kinetic energy calculations with decimal velocities ($E_k = \\frac{1}{2}mv^2$).",
                "Programming ([[PRG-T01]]): Decimal vs integer division (`/` vs `//` in Python).",
            ],
        },
        "active_recall": [
            {
                "q": "What is the rule for determining the position of the decimal point in a product of two decimals?",
                "a": "Count the number of decimal places in each factor, add these counts together, and place the decimal point that many places from the right of the product.",
            },
            {
                "q": "How do you divide by a decimal without changing the quotient?",
                "a": "Multiply both the divisor and dividend by the power of 10 ($10^k$) that converts the divisor into an integer, which is equivalent to multiplying by $\\frac{10^k}{10^k} = 1$.",
            },
        ],
    },
    "MTH-T01-C05-U03": {
        "title": "Decimals and Fractions",
        "chapter": "MTH-T01-C05",
        "objective": "Convert fractions to terminating or repeating decimals using long division, and simplify expressions containing mixed fractions and decimals.",
        "expected_output": "Ability to categorize terminating vs repeating decimals and evaluate mixed rational expressions.",
        "concepts": [
            "**Fraction to Decimal Conversion:** Divide the numerator by the denominator using decimal long division.",
            "**Terminating vs Repeating Invariant:** In lowest terms, $\\frac{a}{b}$ terminates if and only if prime factors of $b$ are strictly 2 and/or 5. Any other prime factor produces an infinite repeating cycle.",
            "**Bar Notation:** A horizontal bar (vinculum) placed over repeating digits denotes infinite repetition: $\\frac{1}{3} = 0.\\overline{3}$, $\\frac{5}{6} = 0.8\\overline{3}$.",
        ],
        "formulas": ["\\frac{a}{b} = a \\div b = 0.d_1 d_2 \\dots \\overline{r_1 r_2 \\dots}"],
        "example": {
            "title": "Classifying and Converting Fractions to Decimals",
            "steps": [
                "Convert $\\frac{7}{16}$ to decimal: Prime factors of denominator $16 = 2^4$ (strictly powers of 2 $\\implies$ terminating).",
                "Divide $7.0000 \\div 16$:",
                "7 \\div 16 = 0.4375 \\quad \\text{(Terminating)}",
                "Convert $\\frac{5}{12}$ to decimal: Prime factors of $12 = 2^2 \\cdot 3$ (contains factor 3 $\\implies$ repeating).",
                "Divide $5.000 \\div 12 = 0.41666\\dots = 0.41\\overline{6}$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why does prime factor 3 in the denominator guarantee an infinite repeating decimal in base 10?",
                "Explain how to convert repeating decimal $0.\\overline{7}$ to fraction using algebra.",
            ],
            "computational": [
                "Convert $\\frac{9}{40}$, $\\frac{7}{15}$, and $3\\frac{5}{8}$ to decimals.",
                "Evaluate mixed operation: $\\frac{3}{5} + 0.45 \\times \\frac{2}{3}$.",
            ],
            "traps": [
                "Premature rounding trap: Rounding $0.666\\dots$ to $0.67$ midway through a multi-step calculation, introducing accumulation error.",
                "Bar misplacement: Writing $0.\\overline{416}$ when only the $6$ repeats ($0.41\\overline{6}$).",
            ],
            "cross": [
                "Programming ([[PRG-T01]]): Exact rational number libraries (`fractions.Fraction` in Python) vs floating point rounding error.",
                "Physics ([[PHY-T01]]): Unit conversion fractions ($1\\text{ in} = 2.54\\text{ cm}$).",
            ],
        },
        "active_recall": [
            {
                "q": "What condition must the denominator of a simplified fraction satisfy for its decimal to terminate?",
                "a": "The prime factorization of the denominator must contain only the prime factors 2 and 5 ($b = 2^m 5^n$).",
            },
            {
                "q": "How do you represent a repeating decimal in standard mathematical notation?",
                "a": "Place a horizontal bar (vinculum) strictly over the repeating block of digits (e.g. $0.41\\overline{6}$).",
            },
        ],
    },
    "MTH-T01-C05-U04": {
        "title": "Solve Equations with Decimals",
        "chapter": "MTH-T01-C05",
        "objective": "Solve linear equations containing decimal coefficients by directly combining like terms or by clearing decimals via multiplication by powers of 10.",
        "expected_output": "Proficiency in solving decimal linear equations using the clearing decimals strategy.",
        "concepts": [
            "**Clearing Decimals Protocol:** Multiply every term on both sides of an equation by $10^k$, where $k$ is the maximum number of decimal places across all terms.",
            "**Direct Solution vs Clearing:** Both methods yield identical solutions; clearing decimals eliminates arithmetic mistakes with decimal points.",
            "**Verification by Substitution:** Always substitute the final solution back into the original un-cleared equation to verify equality.",
        ],
        "formulas": ["10^k (ax + b) = 10^k (cx + d) \\implies 10^k ax + 10^k b = 10^k cx + 10^k d"],
        "example": {
            "title": "Solving a Decimal Linear Equation by Clearing Decimals",
            "steps": [
                "Solve: $0.25x + 1.5 = 0.4x - 0.75$.",
                "Max decimal places is 2 (hundredths place in $0.25$ and $-0.75$).",
                "Multiply entire equation by $100$:",
                "100(0.25x + 1.5) = 100(0.4x - 0.75)",
                "25x + 150 = 40x - 75",
                "Isolate variable terms: Subtract $25x$ from both sides $\\implies 150 = 15x - 75$.",
                "Add 75 to both sides: $225 = 15x \\implies x = 15$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Explain why multiplying both sides of an equation by 100 maintains algebraic equality (Multiplication Property of Equality).",
                "When is clearing decimals preferable to solving with decimals directly?",
            ],
            "computational": ["Solve: $0.05x + 0.10(x + 8) = 1.85$.", "Solve: $1.2(y - 3) = 0.8y + 4.4$."],
            "traps": [
                "Neglected constant trap: When multiplying $0.25x + 1.5$ by 100, multiplying $1.5$ to get $15$ instead of $150$!",
                "Distributive order error: Multiplying inside parentheses when multiplying the outer coefficient.",
            ],
            "cross": [
                "Physics ([[PHY-T01-C02]]): Solving 1D kinematic equations $x_f = x_i + vt$ with measured decimal velocities.",
                "Programming ([[PRG-T01]]): Integer arithmetic scaling in financial software to avoid floating-point drift.",
            ],
        },
        "active_recall": [
            {
                "q": "What is the 'Clearing Decimals' method for solving linear equations?",
                "a": "Identify the term with the greatest number of decimal places ($k$), and multiply every term on both sides of the equation by $10^k$ to transform all coefficients into integers.",
            },
            {
                "q": "If an equation has terms with 1, 2, and 3 decimal places, what power of 10 should you multiply by to clear all decimals?",
                "a": "Multiply by $10^3 = 1000$ because the maximum number of decimal places is 3.",
            },
        ],
    },
    "MTH-T01-C05-U05": {
        "title": "Averages and Probability",
        "chapter": "MTH-T01-C05",
        "objective": "Calculate mean, median, and mode for decimal datasets, and compute theoretical probability of simple discrete events.",
        "expected_output": "Competence in statistical measures of central tendency and basic classical probability.",
        "concepts": [
            "**Mean (Arithmetic Average):** Sum of all data values divided by the total number of values: $\\bar{x} = \\frac{\\sum x_i}{n}$.",
            "**Median:** The physical middle value when data is sorted in ascending order (average of the two middle values if $n$ is even).",
            "**Mode:** The data value that occurs with greatest frequency (a dataset can have one mode, multiple modes, or no mode).",
            "**Theoretical Probability:** Ratio of favorable outcomes to total equally likely outcomes: $P(E) = \\frac{n(E)}{n(S)}$, with $0 \\le P(E) \\le 1$.",
        ],
        "formulas": [
            "\\bar{x} = \\frac{\\sum_{i=1}^n x_i}{n}",
            "P(\\text{Event}) = \\frac{\\text{Number of Favorable Outcomes}}{\\text{Total Number of Possible Outcomes}}",
        ],
        "example": {
            "title": "Calculating Mean, Median, and Probability",
            "steps": [
                "Dataset: $4.5, 6.2, 5.0, 7.8, 6.2, 5.7$.",
                "Mean: Sum $= 4.5 + 6.2 + 5.0 + 7.8 + 6.2 + 5.7 = 35.4$. Count $n = 6$.",
                "\\bar{x} = \\frac{35.4}{6} = 5.9",
                "Median: Sort dataset $\\implies 4.5, 5.0, 5.7, 6.2, 6.2, 7.8$. Middle two are $5.7$ and $6.2$.",
                "\\text{Median} = \\frac{5.7 + 6.2}{2} = \\frac{11.9}{2} = 5.95",
                "Mode: $6.2$ (occurs twice).",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "How does an extreme outlier affect the mean versus the median?",
                "Explain why probability $P(E)$ is strictly bounded between 0 (impossible) and 1 (certain).",
            ],
            "computational": [
                "Find the mean, median, and mode of: $12.4, 15.6, 12.4, 18.2, 14.0, 16.8, 12.4$.",
                "A bag contains 5 red, 8 blue, and 7 green marbles. Find $P(\\text{blue})$ as a fraction, decimal, and percent.",
            ],
            "traps": [
                "Unsorted median trap: Finding the middle value without sorting the dataset into ascending order first!",
                "Even n median trap: Selecting only one of the middle two values instead of computing their mean.",
            ],
            "cross": [
                "Physics ([[PHY-T01-C01]]): Computing average velocity from repeated experimental timing trials.",
                "Programming ([[PRG-T01]]): Sorting algorithms and calculating summary statistics on numeric arrays.",
            ],
        },
        "active_recall": [
            {
                "q": "How do you find the median of a dataset with an even number of values?",
                "a": "Sort the data in ascending order, locate the two middle values, and calculate their arithmetic mean (add them and divide by 2).",
            },
            {
                "q": "What is the theoretical range of any valid probability value?",
                "a": "Between 0 and 1 inclusive ($0 \\le P \\le 1$), where 0 denotes an impossible event and 1 denotes an absolute certainty.",
            },
        ],
    },
    "MTH-T01-C05-U06": {
        "title": "Ratios and Rate",
        "chapter": "MTH-T01-C05",
        "objective": "Express ratios in simplest fractional form with like units, compute unit rates and unit prices involving decimals, and solve comparison word problems.",
        "expected_output": "Mastery of unit rate calculations and ratio simplification across varying measurement units.",
        "concepts": [
            "**Ratio:** A quotient comparing two quantities with identical units; units cancel out to yield a pure dimensionless scalar.",
            "**Rate:** A quotient comparing two quantities with different dimensional units (e.g., miles per hour, dollars per ounce).",
            "**Unit Rate:** A rate with a denominator of strictly 1 unit, calculated by dividing numerator by denominator.",
        ],
        "formulas": [
            "\\text{Unit Rate} = \\frac{\\text{Quantity A}}{\\text{Quantity B}} = \\frac{A \\div B}{1 \\text{ unit of } B}"
        ],
        "example": {
            "title": "Finding Unit Price to Determine Best Buy",
            "steps": [
                "Brand A offers $18\\text{ oz}$ of cereal for $\\$4.32$.",
                "Brand B offers $24\\text{ oz}$ of cereal for $\\$5.52$.",
                "Calculate Unit Price for Brand A: $\\frac{\\$4.32}{18\\text{ oz}} = \\$0.24\\text{ per oz}$.",
                "Calculate Unit Price for Brand B: $\\frac{\\$5.52}{24\\text{ oz}} = \\$0.23\\text{ per oz}$.",
                "Comparison: Brand B is more economical by $\\$0.01\\text{ per ounce}$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why must units be converted to the same unit before writing a simplified ratio?",
                "What is the physical interpretation of unit rate in speed ($v = d/t$?",
            ],
            "computational": [
                "Express the ratio of $8\\text{ inches}$ to $2\\text{ feet}$ in lowest terms ($2\\text{ ft} = 24\\text{ in}$).",
                "A driver travels $412.5\\text{ miles}$ on $15\\text{ gallons}$ of fuel. Calculate fuel economy in miles per gallon.",
            ],
            "traps": [
                "Inverted unit price: Dividing ounces by dollars instead of dollars by ounces (giving ounces per dollar instead of cost per ounce).",
                "Mismatched units in ratios: Writing $8/2 = 4$ for 8 inches to 2 feet without converting feet to inches first ($8/24 = 1/3$).",
            ],
            "cross": [
                "Physics ([[PHY-T01-C02]]): Average speed as distance over time ($v = \\Delta x / \\Delta t$).",
                "Programming ([[PRG-T01]]): Aspect ratio computations for images and responsive viewports.",
            ],
        },
        "active_recall": [
            {
                "q": "What is the structural difference between a ratio and a rate?",
                "a": "A ratio compares two quantities measured in the same units (units cancel out to a dimensionless number), while a rate compares two quantities measured in different units (units remain as a compound dimension, like miles/hour).",
            },
            {
                "q": "How do you calculate a unit price?",
                "a": "Divide the total monetary cost by the total quantity of units to get the cost for exactly one unit (Price per Unit).",
            },
        ],
    },
    "MTH-T01-C05-U07": {
        "title": "Simplify and Use Square Roots",
        "chapter": "MTH-T01-C05",
        "objective": "Evaluate principal square roots of perfect squares and perfect-square decimals/fractions, and approximate irrational square roots between consecutive integers.",
        "expected_output": "Fluency in identifying square roots and estimating irrational radicals on the real number line.",
        "concepts": [
            "**Square Root Definition:** If $b^2 = a$ and $b \\ge 0$, then $b$ is the principal square root of $a$, denoted $\\sqrt{a} = b$.",
            "**Square Roots of Decimals:** $\\sqrt{0.04} = 0.2$ because $(0.2)^2 = 0.04$ (halves the number of decimal places).",
            "**Irrational Square Roots:** If a whole number is not a perfect square, its square root is an irrational number with a non-terminating, non-repeating decimal expansion.",
        ],
        "formulas": [
            "\\sqrt{a} = b \\iff b^2 = a \\quad (a, b \\ge 0)",
            "\\sqrt{\\frac{a}{b}} = \\frac{\\sqrt{a}}{\\sqrt{b}}",
        ],
        "example": {
            "title": "Evaluating and Estimating Square Roots",
            "steps": [
                "Evaluate $\\sqrt{0.64}$: Notice $64/100 \\implies \\sqrt{64}/\\sqrt{100} = 8/10 = 0.8$.",
                "Evaluate $\\sqrt{\\frac{49}{144}} = \\frac{\\sqrt{49}}{\\sqrt{144}} = \\frac{7}{12}$.",
                "Estimate $\\sqrt{75}$ between consecutive integers:",
                "Perfect squares bounding 75: $64 < 75 < 81$.",
                "Taking square roots: $\\sqrt{64} < \\sqrt{75} < \\sqrt{81} \\implies 8 < \\sqrt{75} < 9$.",
                "Since 75 is closer to 81 than 64, $\\sqrt{75} \\approx 8.7$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why is $\\sqrt{0.09} = 0.3$ and not $0.03$?",
                "Why does a negative number not have a real square root?",
            ],
            "computational": [
                "Evaluate: $\\sqrt{1.44}$, $\\sqrt{0.0025}$, and $\\sqrt{\\frac{81}{100}}$.",
                "Estimate $\\sqrt{42}$ to the nearest tenth.",
            ],
            "traps": [
                "Halving trap: Confusing taking the square root with dividing by 2 (e.g. writing $\\sqrt{16} = 8$ instead of 4).",
                "Decimal place doubling trap: Believing $\\sqrt{0.4} = 0.2$. Notice $(0.2)^2 = 0.04 \\neq 0.4$!",
            ],
            "cross": [
                "Geometry ([[MTH-T01-C12]]): Pythagorean Theorem hypotenuse calculations ($c = \\sqrt{a^2 + b^2}$).",
                "Physics ([[PHY-T01-C03]]): Free-fall drop velocity $v = \\sqrt{2gh}$.",
            ],
        },
        "active_recall": [
            {
                "q": "What is the principal square root of 0.04, and why?",
                "a": "The principal square root is 0.2 because $(0.2)^2 = 0.2 \\times 0.2 = 0.04$.",
            },
            {
                "q": "How do you estimate the value of an irrational square root like sqrt(53)?",
                "a": "Identify the two closest perfect squares that sandwich 53: $49 < 53 < 64$. Therefore, $7 < \\sqrt{53} < 8$. Since 53 is closer to 49, $\\sqrt{53} \\approx 7.3$.",
            },
        ],
    },
    # =========================================================================
    # CHAPTER C06: PERCENTS (5 Units)
    # =========================================================================
    "MTH-T01-C06-U01": {
        "title": "Understand Percent",
        "chapter": "MTH-T01-C06",
        "objective": "Define percent as a ratio per 100, and fluently convert between percents, decimals, and fractions.",
        "expected_output": "Three-way conversion fluency between percent, decimal, and fractional forms.",
        "concepts": [
            "**Definition of Percent:** 'Percent' means 'per hundred'. $P\\% = \\frac{P}{100} = P \\times 0.01$.",
            "**Percent to Decimal:** Remove the \\% sign and divide by 100 (shift decimal point two places to the left).",
            "**Decimal to Percent:** Multiply by 100 and append the \\% sign (shift decimal point two places to the right).",
        ],
        "formulas": ["P\\% = \\frac{P}{100} = 0.01 P"],
        "example": {
            "title": "Three-Way Conversions",
            "steps": [
                "Convert $0.075$ to percent: Multiply by $100 \\implies 0.075 \\times 100 = 7.5\\%$.",
                "Convert $135\\%$ to decimal and fraction:",
                "Decimal: $135 \\div 100 = 1.35$.",
                "Fraction: $\\frac{135}{100} = \\frac{27}{20} = 1\\frac{7}{20}$.",
            ],
        },
        "practice_guide": {
            "conceptual": ["Why is 100% equal to the integer 1?", "Explain why 0.5% is not equal to 0.5."],
            "computational": [
                "Convert $0.008$ to a percent.",
                "Convert $62.5\\%$ to a fraction in lowest terms.",
                "Convert $\\frac{7}{12}$ to a percent rounded to the nearest tenth.",
            ],
            "traps": [
                "Decimal shift direction: Shifting the decimal left instead of right when converting from decimal to percent.",
                "Small percent trap: Confusing $0.4\\%$ with $0.4$. Note: $0.4\\% = 0.004$ while $0.4 = 40\\%$.",
            ],
            "cross": [
                "Programming ([[PRG-T01]]): Percent calculations in CSS styling and data dashboards.",
                "Physics ([[PHY-T01]]): Fractional efficiency $\\eta = \\frac{W_{\\text{out}}}{W_{\\text{in}}} \\times 100\\%$.",
            ],
        },
        "active_recall": [
            {"q": "What is the exact decimal value of 0.25%?", "a": "0.0025 (divide 0.25 by 100)."},
            {
                "q": "How do you convert any fraction a/b into a percent?",
                "a": "Divide $a$ by $b$ to get a decimal, then multiply by 100 and add the % sign (or multiply $\\frac{a}{b} \\times 100\\%$ directly).",
            },
        ],
    },
    "MTH-T01-C06-U02": {
        "title": "Solve General Applications of Percent",
        "chapter": "MTH-T01-C06",
        "objective": "Translate and solve basic percent problems using the percent equation (Amount = Percent * Base) and calculate percent of increase and decrease.",
        "expected_output": "Proficiency in solving 'what percent', 'find the amount', and percent change word problems.",
        "concepts": [
            "**The Percent Equation:** $\\text{Amount} = \\text{Percent} \\times \\text{Base}$ ($A = P \\cdot B$), where Percent must be written in decimal or fractional form.",
            "**Key Translation Words:** 'is' translates to $=$, 'of' translates to $\\times$, 'what' translates to variable $x$.",
            "**Percent of Change Formula:** $\\text{Percent Change} = \\frac{|\\text{New Amount} - \\text{Original Amount}|}{\\text{Original Amount}} \\times 100\\%$.",
        ],
        "formulas": [
            "A = P \\cdot B",
            "\\text{Percent Change} = \\frac{\\text{Amount of Change}}{\\text{Original Amount}} \\times 100\\%",
        ],
        "example": {
            "title": "Solving Percent Equations & Percent Change",
            "steps": [
                "Problem: What percent of 84 is 21?",
                "Translate: $x \\cdot 84 = 21 \\implies x = \\frac{21}{84} = \\frac{1}{4} = 0.25 = 25\\%$.",
                "Problem: An item's price increases from $\\$40$ to $\\$50$. Find the percent increase.",
                "Change $= 50 - 40 = 10$. Original $= 40$.",
                "\\text{Percent Increase} = \\frac{10}{40} \\times 100\\% = 25\\%.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why must the denominator in percent change always be the original amount?",
                "Explain why a change from 100 to 150 is a 50% increase, but from 150 to 100 is a 33.3% decrease.",
            ],
            "computational": [
                "Find the amount: $35\\%$ of $240$.",
                "Find the base: $45$ is $15\\%$ of what number?",
                "A store stock drops from $250$ units to $190$ units. Find the percent decrease.",
            ],
            "traps": [
                "New Base Trap: Dividing the change by the new amount instead of the original amount in percent decrease.",
                "Forgetting Decimal Conversion: Multiplying $240 \\times 35$ directly instead of $240 \\times 0.35$.",
            ],
            "cross": [
                "Physics ([[PHY-T01]]): Percent relative error between measured and theoretical values.",
                "Economics: Inflation rates and GDP growth percentages.",
            ],
        },
        "active_recall": [
            {
                "q": "State the standard algebraic formula for percent of change.",
                "a": "$\\text{Percent Change} = \\frac{|\\text{New Value} - \\text{Original Value}|}{\\text{Original Value}} \\times 100\\%$.",
            },
            {
                "q": "In the sentence '24 is 30% of what number?', identify the Amount, Percent, and Base.",
                "a": "Amount ($A$) = 24, Percent ($P$) = 30% (0.30), Base ($B$) = unknown variable ($x$). Equation: $24 = 0.30x$.",
            },
        ],
    },
    "MTH-T01-C06-U03": {
        "title": "Solve Sales Tax, Commission, and Discount Applications",
        "chapter": "MTH-T01-C06",
        "objective": "Calculate sales tax, total purchase cost, sales commission, discount amounts, and final sale prices.",
        "expected_output": "Fluency in solving multi-step commercial percent applications.",
        "concepts": [
            "**Sales Tax:** $\\text{Tax} = \\text{Tax Rate} \\times \\text{Purchase Price}$. $\\text{Total Cost} = \\text{Price} + \\text{Tax}$.",
            "**Discount & Sale Price:** $\\text{Discount} = \\text{Discount Rate} \\times \\text{List Price}$. $\\text{Sale Price} = \\text{List Price} - \\text{Discount} = (1 - r) \\cdot \\text{List Price}$.",
            "**Commission:** $\\text{Commission} = \\text{Commission Rate} \\times \\text{Total Sales}$.",
        ],
        "formulas": [
            "\\text{Total Cost} = \\text{Price} \\times (1 + r_{\\text{tax}})",
            "\\text{Sale Price} = \\text{Price} \\times (1 - r_{\\text{discount}})",
        ],
        "example": {
            "title": "Calculating Discount and Sales Tax Sequentially",
            "steps": [
                "A jacket listed at $\\$120$ is on a $25\\%$ discount. Sales tax is $8\\%$. Find final cost.",
                "Calculate discount: $0.25 \\times 120 = \\$30$.",
                "Sale price: $120 - 30 = \\$90$.",
                "Calculate tax on the sale price: $0.08 \\times 90 = \\$7.20$.",
                "Total cost: $90 + 7.20 = \\$97.20$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why is sales tax calculated on the sale price rather than the original list price?",
                "Show why $(1 - 0.20)(1 + 0.08) \\neq 1 - 0.12$.",
            ],
            "computational": [
                "A real estate agent earns a $3.5\\%$ commission on a house sold for $\\$340,000$. Find the commission.",
                "A smartphone marked $\\$800$ is discounted by $15\\%$. With $7.5\\%$ sales tax, what is the total cost?",
            ],
            "traps": [
                "Tax on original price trap: Calculating sales tax on the initial price before taking the discount off.",
                "Combined rate trap: Subtracting tax from discount directly (e.g. $25\\% - 8\\% = 17\\%$ off).",
            ],
            "cross": [
                "Finance & E-commerce: Shopping cart checkout algorithms in web development ([[PRG-T01]]).",
                "Accounting: Gross margin and sales revenue reconciliation.",
            ],
        },
        "active_recall": [
            {
                "q": "What is the single-multiplier shortcut for finding a price after an 8% sales tax?",
                "a": "Multiply the price directly by $1.08$ (representing $100\\% + 8\\%$).",
            },
            {
                "q": "If an item is discounted by 30%, what fraction of the original price does the buyer pay?",
                "a": "The buyer pays $100\\% - 30\\% = 70\\%$, or $0.70$ times the original price.",
            },
        ],
    },
    "MTH-T01-C06-U04": {
        "title": "Solve Simple Interest Applications",
        "chapter": "MTH-T01-C06",
        "objective": "Apply the simple interest formula I = Prt to calculate interest earned, principal, interest rate, or investment time.",
        "expected_output": "Mastery of the simple interest formula with appropriate time unit conversions.",
        "concepts": [
            "**Simple Interest Formula:** $I = P \\cdot r \\cdot t$, where $I$ is interest, $P$ is principal, $r$ is annual interest rate (in decimal), and $t$ is time strictly in years.",
            "**Total Future Value:** The total amount accumulated after time $t$ is $A = P + I = P(1 + rt)$.",
            "**Time Unit Normalization:** If time is given in months, divide by 12 ($t = \\frac{m}{12}$). If given in days, divide by 365 ($t = \\frac{d}{365}$).",
        ],
        "formulas": ["I = P \\cdot r \\cdot t", "A = P + I = P(1 + rt)"],
        "example": {
            "title": "Calculating Simple Interest with Fractional Years",
            "steps": [
                "Principal $P = \\$6,000$ invested at $4.5\\%$ annual interest for $18$ months.",
                "Convert time to years: $t = \\frac{18}{12} = 1.5\\text{ years}$.",
                "Convert rate to decimal: $r = 0.045$.",
                "Compute interest: $I = (6000)(0.045)(1.5) = 405$.",
                "Total accumulated value: $A = 6000 + 405 = \\$6,405$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "What is the difference between simple interest and compound interest?",
                "Why must the interest rate and time be calibrated to the same unit (annual/years)?",
            ],
            "computational": [
                "Find interest earned on $\\$2,400$ at $5.2\\%$ for $9$ months.",
                "Find the principal needed to earn $\\$500$ in interest at $4\\%$ over $2.5$ years.",
            ],
            "traps": [
                "Raw months trap: Plugging $18$ directly into $t$ instead of $1.5$, inflating the interest by a factor of 12!",
                "Percent to decimal error: Using $4.5$ instead of $0.045$ for $r$.",
            ],
            "cross": [
                "Banking & Economics: Bond yields, treasury notes, and short-term loans.",
                "Programming ([[PRG-T01]]): Financial amortisation loops and interest calculators.",
            ],
        },
        "active_recall": [
            {
                "q": "In the formula I = Prt, what unit of measurement must time t strictly have?",
                "a": "Time $t$ must strictly be measured in years (if given in months, divide by 12).",
            },
            {
                "q": "How do you rearrange I = Prt to solve for the principal P?",
                "a": "$P = \\frac{I}{rt}$ (divide both sides by $rt$).",
            },
        ],
    },
    "MTH-T01-C06-U05": {
        "title": "Solve Proportions and their Applications",
        "chapter": "MTH-T01-C06",
        "objective": "Solve percent problems and real-world scaling applications using the percent proportion (Part / Whole = Percent / 100).",
        "expected_output": "Proficiency in setting up and solving percent proportions via cross-multiplication.",
        "concepts": [
            "**The Percent Proportion:** $\\frac{\\text{is}}{\\text{of}} = \\frac{\\text{percent}}{100} \\iff \\frac{\\text{Part}}{\\text{Whole}} = \\frac{P}{100}$.",
            "**Advantage of Proportions:** Cross-multiplication eliminates the need to manually shift decimals for $P$ before solving.",
            "**Cross-Product Equation:** For $\\frac{A}{B} = \\frac{P}{100}$, cross-multiplying yields $100A = B \\cdot P$.",
        ],
        "formulas": [
            "\\frac{\\text{Part}}{\\text{Whole}} = \\frac{P}{100} \\iff 100 \\times \\text{Part} = \\text{Whole} \\times P"
        ],
        "example": {
            "title": "Solving a Percent Proportion",
            "steps": [
                "Problem: 42 is what percent of 120?",
                "Identify components: Part $= 42$, Whole $= 120$, Percent $= P$.",
                "Set up proportion: $\\frac{42}{120} = \\frac{P}{100}$.",
                "Cross-multiply: $120P = 42 \\times 100 = 4200$.",
                "Solve for P: $P = \\frac{4200}{120} = 35\\%$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Contrast solving a percent problem using the Percent Equation ($A = P \\cdot B$) vs the Percent Proportion ($A/B = P/100$).",
                "Why is the denominator of the right side always 100 in percent proportions?",
            ],
            "computational": [
                "Use a proportion to find $28\\%$ of $175$.",
                "Use a proportion to find the whole if $18$ is $45\\%$ of a number.",
            ],
            "traps": [
                "Part/Whole Inversion: Setting up $\\frac{120}{42} = \\frac{P}{100}$ when 42 is the part and 120 is the whole.",
                "Unnecessary double conversion: Converting $P$ to a decimal when already writing it over 100.",
            ],
            "cross": [
                "Medicine: Dosage proportions based on patient body weight.",
                "Surveying & Mapping: Scale conversions and geographic ratio mappings.",
            ],
        },
        "active_recall": [
            {
                "q": "What is the classic mnemonic for setting up a percent proportion?",
                "a": "$\\frac{\\text{is}}{\\text{of}} = \\frac{\\%}{100}$, where the number attached to 'is' is the part, and the number attached to 'of' is the whole base.",
            },
            {"q": "Solve for x: x / 80 = 45 / 100.", "a": "$100x = 45 \\times 80 = 3600 \\implies x = 36$."},
        ],
    },
    # =========================================================================
    # CHAPTER C07: PROPORTIONAL & RATIO (6 Units)
    # =========================================================================
    "MTH-T01-C07-U01": {
        "title": "Understanding Ratios",
        "chapter": "MTH-T01-C07",
        "objective": "Express ratios in three equivalent notations (a to b, a:b, a/b), reduce ratios to simplest fractional terms, and scale quantities.",
        "expected_output": "Fluency in simplifying and interpreting dimensionless ratios.",
        "concepts": [
            "**Ratio Definition:** A mathematical comparison of two numbers or quantities measured in identical units.",
            "**Dimensionless Invariant:** Because the units in numerator and denominator are identical, they cancel out entirely, leaving a pure unitless ratio.",
            "**Scale Invariance:** Multiplying or dividing both terms of a ratio by a nonzero constant $k$ preserves the ratio: $\\frac{a}{b} = \\frac{ka}{kb}$.",
        ],
        "formulas": ["a : b = \\frac{a}{b} = \\frac{a \\div \\gcd(a,b)}{b \\div \\gcd(a,b)}"],
        "example": {
            "title": "Simplifying Ratios with Unit Conversion",
            "steps": [
                "Write the ratio of $15\\text{ minutes}$ to $2\\text{ hours}$ in simplest form.",
                "Convert to common units: $2\\text{ hours} = 2 \\times 60 = 120\\text{ minutes}$.",
                "Write as fraction: $\\frac{15\\text{ min}}{120\\text{ min}} = \\frac{15}{120}$.",
                "Divide by $\\gcd(15, 120) = 15$:",
                "\\frac{15 \\div 15}{120 \\div 15} = \\frac{1}{8} \\quad (1 : 8)",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why does a ratio have no units?",
                "Explain the difference between a part-to-part ratio and a part-to-whole ratio.",
            ],
            "computational": [
                "Simplify the ratio: $36\\text{ cm}$ to $1.2\\text{ meters}$.",
                "In a class of 28 students, 12 are boys. Find the ratio of girls to boys and girls to total students.",
            ],
            "traps": [
                "Unit Mismatch Trap: Simplifying $15\\text{ min} / 2\\text{ hours}$ as $15/2$ without converting hours to minutes.",
                "Part-to-Part vs Part-to-Whole Confusion: Using girls-to-boys ($16:12$) when asked for girls-to-total ($16:28$).",
            ],
            "cross": [
                "Art & Design: Golden Ratio $\\phi = \\frac{1 + \\sqrt{5}}{2} \\approx 1.618$.",
                "Chemistry: Stoichiometric molar ratios in chemical reactions.",
            ],
        },
        "active_recall": [
            {
                "q": "Why must you convert quantities to the same unit before simplifying a ratio?",
                "a": "Because a ratio is a comparison of like quantities. Only when units are identical can they cancel out to yield a true, dimensionless mathematical ratio.",
            },
            {
                "q": "If the ratio of cement to sand is 1:3, what fraction of the total mixture is cement?",
                "a": "Total parts = $1 + 3 = 4$. Cement is $\\frac{1}{4}$ ($25\\%$) of the total mixture.",
            },
        ],
    },
    "MTH-T01-C07-U02": {
        "title": "Rates and Unit Rates",
        "chapter": "MTH-T01-C07",
        "objective": "Identify rates as comparisons of different units, calculate unit rates by dividing, and compute unit pricing to compare values.",
        "expected_output": "Proficiency in evaluating unit rates and dimensional quotients.",
        "concepts": [
            "**Rate Definition:** A comparison of two quantities measured in different units (e.g., meters per second, dollars per gallon).",
            "**Unit Rate Definition:** A rate simplified so the denominator equals exactly 1 unit of measurement.",
            "**Unit Price:** Cost per one unit of mass, volume, or count, used to identify economical purchases.",
        ],
        "formulas": [
            "\\text{Unit Rate} = \\frac{\\text{Quantity 1}}{\\text{Quantity 2}} = \\frac{Q_1 \\div Q_2}{1 \\text{ unit of } Q_2}"
        ],
        "example": {
            "title": "Unit Speed and Unit Price",
            "steps": [
                "A car travels $345\\text{ miles}$ in $6\\text{ hours}$.",
                "Unit Rate (Speed): $\\frac{345\\text{ miles}}{6\\text{ hours}} = 57.5\\text{ miles per hour (mph)}$.",
                "Store A sells 16 oz detergent for $\\$4.48$ $\\implies \\frac{4.48}{16} = \\$0.28/\\text{oz}$.",
                "Store B sells 25 oz detergent for $\\$6.75$ $\\implies \\frac{6.75}{25} = \\$0.27/\\text{oz}$.",
                "Store B is cheaper by $\\$0.01$ per ounce.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "What is the difference between speed (rate) and distance (scalar)?",
                "Why does a unit rate always have a 1 in the denominator?",
            ],
            "computational": [
                "A runner completes $10\\text{ kilometers}$ in $48\\text{ minutes}$. Find their speed in km/hr ($48\\text{ min} = 0.8\\text{ hr}$).",
                "Calculate the unit price for a 32-pack of water bottles costing $\\$8.96$.",
            ],
            "traps": [
                "Numerator/Denominator Inversion: Dividing hours by miles instead of miles by hours.",
                "Unit omission: Writing $57.5$ instead of $57.5\\text{ mph}$ (rates require units!).",
            ],
            "cross": [
                "Physics ([[PHY-T01-C02]]): Average velocity $v = \\Delta x / \\Delta t$.",
                "Economics: Inflation rate, GDP per capita, and currency exchange rates.",
            ],
        },
        "active_recall": [
            {
                "q": "What distinguishes a rate from a ratio?",
                "a": "A ratio compares quantities of the same unit (units cancel), whereas a rate compares quantities with different units (units do not cancel and form a compound unit like miles/hour).",
            },
            {
                "q": "How do you calculate speed given distance d and time t?",
                "a": "$v = \\frac{d}{t}$ (divide distance by time).",
            },
        ],
    },
    "MTH-T01-C07-U03": {
        "title": "Solving Proportions",
        "chapter": "MTH-T01-C07",
        "objective": "State the Cross-Products Property of proportions and solve single-variable proportions algebraically.",
        "expected_output": "Mastery of solving linear and binomial proportions via cross-multiplication.",
        "concepts": [
            "**Proportion Definition:** An equation stating that two ratios are equal: $\\frac{a}{b} = \\frac{c}{d}$ ($b, d \\neq 0$).",
            "**Cross-Products Property:** In any true proportion, the product of the extremes equals the product of the means: $ad = bc$.",
            "**Extraneous Check:** The solution must not cause any denominator in the proportion to equal zero.",
        ],
        "formulas": ["\\frac{a}{b} = \\frac{c}{d} \\iff a \\cdot d = b \\cdot c"],
        "example": {
            "title": "Solving a Proportion with an Algebraic Binomial",
            "steps": [
                "Solve for $x$: $\\frac{x - 2}{5} = \\frac{8}{10}$.",
                "Apply Cross-Products Property: $10(x - 2) = 5 \\times 8$.",
                "Distribute: $10x - 20 = 40$.",
                "Add 20: $10x = 60$.",
                "Divide by 10: $x = 6$.",
                "Verify: $\\frac{6-2}{5} = \\frac{4}{5} = \\frac{8}{10}$ (Verified).",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why does cross-multiplication solve a proportion?",
                "When does cross-multiplication NOT apply (e.g. adding fractions $\\frac{a}{b} + \\frac{c}{d}$)?",
            ],
            "computational": [
                "Solve: $\\frac{3}{7} = \\frac{x}{35}$.",
                "Solve: $\\frac{2y + 1}{4} = \\frac{y - 2}{3}$.",
            ],
            "traps": [
                "Distribution error: In $10(x - 2)$, writing $10x - 2$ instead of $10x - 20$.",
                "Applying cross-multiplication to addition: Attempting to cross-multiply in $\\frac{1}{2} + \\frac{3}{4}$!",
            ],
            "cross": [
                "Geometry ([[MTH-T01-C12]]): Similar triangles ratio of corresponding sides.",
                "Physics ([[PHY-T01]]): Ohm's Law $V/I = R$ and proportional scaling.",
            ],
        },
        "active_recall": [
            {
                "q": "What is the Cross-Products Property of proportions?",
                "a": "If $\\frac{a}{b} = \\frac{c}{d}$, then $a \\cdot d = b \\cdot c$.",
            },
            {"q": "Solve for y: 4 / y = 12 / 15.", "a": "$12y = 4 \\times 15 = 60 \\implies y = 5$."},
        ],
    },
    "MTH-T01-C07-U04": {
        "title": "Direct Proportion",
        "chapter": "MTH-T01-C07",
        "objective": "Define and identify direct variation, determine the constant of proportionality k, and graph direct variation relationships.",
        "expected_output": "Understanding of linear direct variation y = kx and its graphical representation.",
        "concepts": [
            "**Direct Variation Invariant:** Two quantities $x$ and $y$ are directly proportional if their ratio is constant: $\\frac{y}{x} = k \\iff y = kx$ ($k \\neq 0$).",
            "**Constant of Proportionality (k):** The fixed multiplier $k = y/x$, which represents the slope of the line.",
            "**Geometric Property:** The graph of a direct variation relationship is strictly a straight line passing through the origin $(0, 0)$.",
        ],
        "formulas": ["y = kx \\quad \\text{or} \\quad k = \\frac{y}{x}"],
        "example": {
            "title": "Finding Constant k and Evaluating Direct Variation",
            "steps": [
                "Suppose $y$ varies directly with $x$, and $y = 36$ when $x = 4$.",
                "Find constant $k$: $k = \\frac{y}{x} = \\frac{36}{4} = 9$.",
                "Write equation: $y = 9x$.",
                "Find $y$ when $x = 7$:",
                "y = 9(7) = 63",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why must a direct variation graph pass through the origin (0, 0)?",
                "How is the constant of proportionality k related to unit rate and slope?",
            ],
            "computational": [
                "If $y$ is directly proportional to $x$ and $y = 45$ when $x = 15$, find $k$ and evaluate $y$ when $x = 22$.",
                "Determine if the table represents direct variation: $(2, 6), (5, 15), (8, 24)$.",
            ],
            "traps": [
                "Non-zero y-intercept trap: Mistaking $y = 2x + 3$ for direct variation (fails because $(0, 0)$ is not on the line).",
                "Inverted k trap: Calculating $k = x/y$ instead of $y/x$.",
            ],
            "cross": [
                "Physics ([[PHY-T01-C04]]): Newton's Second Law $F = ma$ ($F$ varies directly with $a$ for constant $m$).",
                "Physics: Hooke's Law for springs $F = kx$.",
            ],
        },
        "active_recall": [
            {
                "q": "What is the general mathematical equation for direct variation?",
                "a": "$y = kx$, where $k = \\frac{y}{x}$ is the non-zero constant of proportionality.",
            },
            {
                "q": "What two visual features must the graph of a direct proportion always possess?",
                "a": "It must be a straight line and it must pass through the origin $(0, 0)$.",
            },
        ],
    },
    "MTH-T01-C07-U05": {
        "title": "Inverse Proportion",
        "chapter": "MTH-T01-C07",
        "objective": "Define and identify inverse variation, determine the constant of proportionality k = xy, and model real-world inverse relationships.",
        "expected_output": "Mastery of inverse variation xy = k and hyperbolic relationship analysis.",
        "concepts": [
            "**Inverse Variation Invariant:** Two quantities are inversely proportional if their product is constant: $x \\cdot y = k \\iff y = \\frac{k}{x}$ ($k \\neq 0$).",
            "**Behavioral Invariant:** As one quantity increases by factor $c$, the other quantity decreases by factor $1/c$.",
            "**Graph Structure:** The graph of inverse variation is a hyperbola in the first and third quadrants with asymptotic axes ($x \\neq 0, y \\neq 0$).",
        ],
        "formulas": ["xy = k \\iff y = \\frac{k}{x}"],
        "example": {
            "title": "Modeling Work and Time with Inverse Proportion",
            "steps": [
                "It takes 4 workers 15 hours to complete a job. How long will 6 workers take at the same pace?",
                "Recognize inverse variation: More workers $\\implies$ less time.",
                "Find constant work amount $k$: $k = x_1 y_1 = (4\\text{ workers})(15\\text{ hours}) = 60\\text{ worker-hours}$.",
                "Form equation for 6 workers: $6 \\cdot t = 60$.",
                "Solve for time $t$: $t = \\frac{60}{6} = 10\\text{ hours}$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why is the product xy constant in inverse variation rather than the ratio y/x?",
                "Explain why an inverse variation graph never touches the x-axis or y-axis.",
            ],
            "computational": [
                "If $y$ varies inversely with $x$ and $y = 8$ when $x = 3$, find $k$ and calculate $y$ when $x = 12$.",
                "A car travels a fixed distance at $60\\text{ mph}$ in $4\\text{ hours}$. What speed is needed to make the trip in $3\\text{ hours}$?",
            ],
            "traps": [
                "Direct Proportion Reflex: Setting up $\\frac{4}{15} = \\frac{6}{t}$, which incorrectly predicts 6 workers would take 22.5 hours!",
                "Zero Division: Attempting to evaluate $y$ at $x = 0$.",
            ],
            "cross": [
                "Physics: Boyle's Law for ideal gases $PV = k$ at constant temperature.",
                "Physics: Electrical resistance and current $I = V/R$ for constant voltage.",
            ],
        },
        "active_recall": [
            {
                "q": "What is the defining algebraic invariant of an inverse proportion?",
                "a": "The product of the two variables is constant: $x \\cdot y = k$ (or $y = \\frac{k}{x}$).",
            },
            {
                "q": "If 3 painters take 8 hours to paint a fence, how long will 4 painters take?",
                "a": "$k = 3 \\times 8 = 24\\text{ painter-hours}$. For 4 painters: $4t = 24 \\implies t = 6\\text{ hours}$.",
            },
        ],
    },
    "MTH-T01-C07-U06": {
        "title": "Applications of Proportions",
        "chapter": "MTH-T01-C07",
        "objective": "Apply direct and inverse proportions to solve map scale, blueprint, recipe, similar figure, and gear ratio problems.",
        "expected_output": "Competence in translating physical and geometric word problems into solvable proportions.",
        "concepts": [
            "**Scale Factor:** The ratio of a model's dimension to the corresponding actual dimension: $\\text{Scale} = \\frac{\\text{Model Dimension}}{\\text{Actual Dimension}}$.",
            "**Similar Figures Invariant:** In similar polygons, corresponding angles are congruent, and corresponding side lengths are strictly proportional: $\\frac{s_1}{s_2} = \\frac{p_1}{p_2}$.",
            "**Area & Volume Scaling:** If side lengths scale by $k$, surface area scales by $k^2$ and volume scales by $k^3$.",
        ],
        "formulas": [
            "\\frac{\\text{Model}}{\\text{Actual}} = \\text{Scale Factor}",
            "\\frac{\\text{Length}_1}{\\text{Length}_2} = \\frac{\\text{Width}_1}{\\text{Width}_2}",
        ],
        "example": {
            "title": "Map Scale and Similar Triangle Height Calculation",
            "steps": [
                "A map scale is $0.5\\text{ inch} = 15\\text{ miles}$. Two towns are $3.5\\text{ inches}$ apart on the map.",
                "Set up proportion: $\\frac{0.5\\text{ in}}{15\\text{ mi}} = \\frac{3.5\\text{ in}}{x\\text{ mi}}$.",
                "Cross-multiply: $0.5x = 15 \\times 3.5 = 52.5$.",
                "Solve for actual distance: $x = \\frac{52.5}{0.5} = 105\\text{ miles}$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why does doubling the linear dimension of a rectangular garden quadruple its area?",
                "Explain how shadow length proportions allow measuring the height of tall structures.",
            ],
            "computational": [
                "A flagpole casts a $12\\text{ ft}$ shadow when a $6\\text{ ft}$ tall person casts a $4\\text{ ft}$ shadow. Find flagpole height.",
                "A blueprint scale is $1\\text{ cm} = 2.5\\text{ m}$. What area on the blueprint represents a $50\\text{ m}^2$ room?",
            ],
            "traps": [
                "Area scaling trap: Multiplying area by $k$ instead of $k^2$ when linear dimensions scale by $k$.",
                "Cross-matching terms: Setting up $\\frac{\\text{map}_1}{\\text{actual}_1} = \\frac{\\text{actual}_2}{\\text{map}_2}$.",
            ],
            "cross": [
                "Architecture: Scale drawings and BIM computer-aided drafting (CAD).",
                "Physics ([[PHY-T01-C01]]): Dimensional scaling laws in planetary bodies and animal physiology.",
            ],
        },
        "active_recall": [
            {
                "q": "If a blueprint has a scale of 1 inch = 5 feet, how many feet does 4.5 inches represent?",
                "a": "$4.5 \\times 5 = 22.5\\text{ feet}$.",
            },
            {
                "q": "If two triangles are similar and the sides of the larger are 3 times the smaller, by what factor is the larger triangle's area greater?",
                "a": "By a factor of $3^2 = 9$.",
            },
        ],
    },
    # =========================================================================
    # CHAPTER C08: EXPONENTS (6 Units)
    # =========================================================================
    "MTH-T01-C08-U01": {
        "title": "Introduction to Exponents",
        "chapter": "MTH-T01-C08",
        "objective": "Identify the base and exponent in exponential expressions, evaluate integer powers, and apply the order of operations to expressions with exponents.",
        "expected_output": "Fluency in exponential notation and parentheses distinctions.",
        "concepts": [
            "**Exponential Definition:** For base $a$ and positive integer exponent $n$, $a^n = \\underbrace{a \\cdot a \\cdot \\dots \\cdot a}_{n \\text{ times}}$.",
            "**Parentheses Invariant:** $(-a)^n$ raises negative $a$ to power $n$. In contrast, $-a^n$ negates $a^n$ after exponentiation: $(-2)^4 = +16$ while $-2^4 = -16$.",
            "**Order of Operations (PEMDAS):** Evaluate terms inside grouping symbols first, followed immediately by exponents before multiplication/division.",
        ],
        "formulas": ["a^n = \\prod_{i=1}^n a", "(-a)^{2k} = a^{2k}, \\quad (-a)^{2k+1} = -a^{2k+1}"],
        "example": {
            "title": "Evaluating Expressions with Exponents and Signs",
            "steps": [
                "Evaluate $(-3)^4$ vs $-3^4$:",
                "(-3)^4 = (-3)(-3)(-3)(-3) = 81",
                "-3^4 = -(3 \\cdot 3 \\cdot 3 \\cdot 3) = -81",
                "Evaluate $4(2 + 3)^2 - 5 \\cdot 2^3$:",
                "Parentheses first: $2 + 3 = 5 \\implies 4(5)^2 - 5 \\cdot 2^3$.",
                "Exponents: $5^2 = 25$ and $2^3 = 8 \\implies 4(25) - 5(8)$.",
                "Multiply and subtract: $100 - 40 = 60$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why does an odd power of a negative number remain negative, while an even power becomes positive?",
                "Why does exponentiation precede multiplication in the order of operations?",
            ],
            "computational": [
                "Evaluate: $(-4)^3$, $-4^3$, and $(-1)^{100}$.",
                "Evaluate: $3 \\cdot 2^4 - 2(5 - 2)^3$.",
            ],
            "traps": [
                "Base-exponent multiplication trap: Writing $2^3 = 6$ instead of $8$ ($2 \\times 3 \\neq 2 \\times 2 \\times 2$).",
                "Sign omission: Treating $-5^2$ as $+25$ instead of $-25$.",
            ],
            "cross": [
                "Programming ([[PRG-T01]]): Operator precedence (`**` in Python, `Math.pow()` in JS).",
                "Computer Science: Binary memory representation ($2^8 = 256$, $2^{16} = 65,536$, $2^{32} \\approx 4.29\\times 10^9$).",
            ],
        },
        "active_recall": [
            {"q": "What is the value of (-1)^99?", "a": "-1 (because 99 is an odd exponent)."},
            {
                "q": "Explain the difference between -4^2 and (-4)^2.",
                "a": "In $-4^2$, exponentiation happens before negation: $-(4 \\times 4) = -16$. In $(-4)^2$, the base is $-4$: $(-4) \\times (-4) = +16$.",
            },
        ],
    },
    "MTH-T01-C08-U02": {
        "title": "Multiplication Properties of Exponents",
        "chapter": "MTH-T01-C08",
        "objective": "Apply the Product Rule for exponents (a^m * a^n = a^(m+n)) to simplify algebraic expressions with like bases.",
        "expected_output": "Mastery of combining exponential terms with identical bases under multiplication.",
        "concepts": [
            "**Product Rule (Same Base):** When multiplying powers with the same base, keep the base and add the exponents: $a^m \\cdot a^n = a^{m+n}$.",
            "**Proof of Product Rule:** $a^m \\cdot a^n = (a \\cdot \\dots \\cdot a) \\cdot (a \\cdot \\dots \\cdot a) = a^{m+n}$.",
            "**Coefficient Separation:** Multiply numeric coefficients independently of variable exponents: $(ca^m)(da^n) = (cd)a^{m+n}$.",
        ],
        "formulas": ["a^m \\cdot a^n = a^{m+n}", "(c a^m)(d a^n) = (c \\cdot d) a^{m+n}"],
        "example": {
            "title": "Applying Product Rule with Multiple Variables and Coefficients",
            "steps": [
                "Simplify: $(-3x^4 y^2)(5x^3 y^6)$.",
                "Group coefficients: $(-3 \\cdot 5) = -15$.",
                "Combine $x$ powers: $x^4 \\cdot x^3 = x^{4+3} = x^7$.",
                "Combine $y$ powers: $y^2 \\cdot y^6 = y^{2+6} = y^8$.",
                "Final expression: $-15x^7 y^8$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why do you add exponents when multiplying powers with the same base?",
                "Why does the Product Rule NOT apply to $2^3 \\cdot 3^4$?",
            ],
            "computational": ["Simplify: $x^5 \\cdot x^8$.", "Simplify: $(4a^3 b)(2a^2 b^5)(-3a b^2)$."],
            "traps": [
                "Base multiplication trap: In $2^3 \\cdot 2^5$, multiplying bases to write $4^8$ instead of $2^8$.",
                "Missing exponent 1: Forgetting that a variable without an exponent has implicit exponent $1$ ($x = x^1$).",
            ],
            "cross": [
                "Algebra ([[MTH-T01-C13]]): Multiplying monomials and distributing polynomials.",
                "Physics: Multiplying physical units ($[m] \\cdot [m] = [m^2]$).",
            ],
        },
        "active_recall": [
            {
                "q": "State the Product Rule for Exponents.",
                "a": "$a^m \\cdot a^n = a^{m+n}$ (keep the base and add exponents).",
            },
            {"q": "Simplify: (3x^2)(4x^5).", "a": "$12x^7$ ($3 \\times 4 = 12$, and $x^{2+5} = x^7$)."},
        ],
    },
    "MTH-T01-C08-U03": {
        "title": "Division Properties of Exponents",
        "chapter": "MTH-T01-C08",
        "objective": "Apply the Quotient Rule for exponents (a^m / a^n = a^(m-n)) to simplify algebraic quotients.",
        "expected_output": "Fluency in simplifying algebraic quotients with like bases.",
        "concepts": [
            "**Quotient Rule (Same Base):** When dividing powers with the same nonzero base, keep the base and subtract the exponent of the denominator from the exponent of the numerator: $\\frac{a^m}{a^n} = a^{m-n}$ ($a \\neq 0$).",
            "**Proof via Cancellation:** $\\frac{a^m}{a^n} = \\frac{\\overbrace{a \\cdot a \\dots a}^{m}}{\\underbrace{a \\cdot a \\dots a}_{n}} = a^{m-n}$.",
            "**Coefficient Division:** Divide numerical coefficients as regular rational numbers: $\\frac{c a^m}{d a^n} = \\left(\\frac{c}{d}\\right) a^{m-n}$.",
        ],
        "formulas": ["\\frac{a^m}{a^n} = a^{m-n} \\quad (a \\neq 0)"],
        "example": {
            "title": "Simplifying Quotients with Multiple Variables",
            "steps": [
                "Simplify: $\\frac{24x^7 y^5}{8x^3 y^2}$.",
                "Divide coefficients: $\\frac{24}{8} = 3$.",
                "Subtract $x$ exponents: $x^{7-3} = x^4$.",
                "Subtract $y$ exponents: $y^{5-2} = y^3$.",
                "Final expression: $3x^4 y^3$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why do you subtract exponents when dividing powers with like bases?",
                "What happens when $m = n$ in $\\frac{a^m}{a^n}$?",
            ],
            "computational": ["Simplify: $\\frac{y^{12}}{y^4}$.", "Simplify: $\\frac{-36a^8 b^5 c^2}{9a^3 b^5 c}$."],
            "traps": [
                "Dividing exponents trap: Writing $\\frac{x^{12}}{x^4} = x^{12/4} = x^3$ instead of $x^{12-4} = x^8$!",
                "Zero power cancellation: When $b^5 / b^5 = b^0 = 1$, writing 0 instead of 1.",
            ],
            "cross": [
                "Physics ([[PHY-T01-C01]]): Dimensional analysis unit cancellation ($[m/s] / [s] = [m/s^2]$).",
                "Computer Science: Bit shifting operations equivalent to dividing by powers of 2.",
            ],
        },
        "active_recall": [
            {
                "q": "State the Quotient Rule for Exponents.",
                "a": "$\\frac{a^m}{a^n} = a^{m-n}$ for $a \\neq 0$ (keep the base and subtract exponents).",
            },
            {"q": "Simplify: 15x^9 / (3x^3).", "a": "$5x^6$ ($15/3 = 5$, and $x^{9-3} = x^6$)."},
        ],
    },
    "MTH-T01-C08-U04": {
        "title": "Power Rules of Exponents",
        "chapter": "MTH-T01-C08",
        "objective": "Apply the Power of a Power Rule ((a^m)^n = a^(mn)), Power of a Product Rule ((ab)^n = a^n b^n), and Power of a Quotient Rule.",
        "expected_output": "Proficiency in expanding composite powers of products, quotients, and nested exponents.",
        "concepts": [
            "**Power of a Power Rule:** When raising a power to another power, keep the base and multiply exponents: $(a^m)^n = a^{m \\cdot n}$.",
            "**Power of a Product Rule:** Each factor inside parentheses is raised to the outer exponent: $(ab)^n = a^n b^n$.",
            "**Power of a Quotient Rule:** Both numerator and denominator are raised to the outer exponent: $\\left(\\frac{a}{b}\\right)^n = \\frac{a^n}{b^n}$ ($b \\neq 0$).",
        ],
        "formulas": [
            "(a^m)^n = a^{m \\cdot n}",
            "(ab)^n = a^n b^n",
            "\\left(\\frac{a}{b}\\right)^n = \\frac{a^n}{b^n}",
        ],
        "example": {
            "title": "Simplifying Nested Powers of Products",
            "steps": [
                "Simplify: $(-2x^3 y^4)^3$.",
                "Apply outer exponent 3 to all factors:",
                "(-2)^3 \\cdot (x^3)^3 \\cdot (y^4)^3",
                "Evaluate coefficient: $(-2)^3 = -8$.",
                "Multiply variable exponents: $(x^3)^3 = x^{3 \\cdot 3} = x^9$ and $(y^4)^3 = y^{4 \\cdot 3} = y^{12}$.",
                "Final result: $-8x^9 y^{12}$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Explain the distinction between $x^2 \\cdot x^3$ (add exponents $\\implies x^5$) and $(x^2)^3$ (multiply exponents $\\implies x^6$).",
                "Why does $(a + b)^2 \\neq a^2 + b^2$?",
            ],
            "computational": [
                "Simplify: $(y^5)^4$.",
                "Simplify: $(3a^2 b^4)^3$.",
                "Simplify: $\\left(\\frac{2x^3}{y^2}\\right)^4$.",
            ],
            "traps": [
                "Neglected Coefficient Exponent: In $(2x^3)^4$, writing $2x^{12}$ instead of $2^4 x^{12} = 16x^{12}$!",
                "Freshman's Dream Trap: Distributing an exponent over addition: $(x + y)^2 \\neq x^2 + y^2$.",
            ],
            "cross": [
                "Algebra ([[MTH-T01-C13]]): Polynomial expansions and binomial formulas.",
                "Geometry ([[MTH-T01-C12]]): Scaling volume $(kr)^3 = k^3 r^3$.",
            ],
        },
        "active_recall": [
            {
                "q": "State the Power of a Power Rule for exponents.",
                "a": "$(a^m)^n = a^{m \\cdot n}$ (keep the base and multiply exponents).",
            },
            {"q": "Simplify: (-3a^2)^3.", "a": "$-27a^6$ ($(-3)^3 = -27$, and $a^{2 \\cdot 3} = a^6$)."},
        ],
    },
    "MTH-T01-C08-U05": {
        "title": "Negative and Zero Exponents",
        "chapter": "MTH-T01-C08",
        "objective": "Define zero and negative integer exponents, and rewrite algebraic expressions containing negative exponents using only positive exponents.",
        "expected_output": "Mastery of reciprocal properties of negative exponents and the zero power.",
        "concepts": [
            "**Zero Exponent Definition:** Any nonzero real number raised to the zero power equals 1: $a^0 = 1$ ($a \\neq 0$). $0^0$ is an indeterminate form.",
            "**Negative Exponent Definition:** A negative exponent represents the reciprocal of the positive power: $a^{-n} = \\frac{1}{a^n}$ and $\\frac{1}{a^{-n}} = a^n$ ($a \\neq 0$).",
            "**Position Inversion Property:** Moving a factor across the fraction bar inverts the sign of its exponent: $\\frac{x^{-a}}{y^{-b}} = \\frac{y^b}{x^a}$.",
        ],
        "formulas": [
            "a^0 = 1 \\quad (a \\neq 0)",
            "a^{-n} = \\frac{1}{a^n}, \\quad \\frac{1}{a^{-n}} = a^n \\quad (a \\neq 0)",
        ],
        "example": {
            "title": "Simplifying Expressions with Negative Exponents",
            "steps": [
                "Simplify and write with positive exponents: $\\frac{4x^{-3} y^5}{12x^2 y^{-3}}$.",
                "Simplify coefficients: $\\frac{4}{12} = \\frac{1}{3}$.",
                "Apply quotient rule for $x$: $x^{-3 - 2} = x^{-5} = \\frac{1}{x^5}$.",
                "Apply quotient rule for $y$: $y^{5 - (-3)} = y^{5 + 3} = y^8$.",
                "Combine into fraction: $\\frac{y^8}{3x^5}$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Prove why $a^0 = 1$ using the Quotient Property $\\frac{a^n}{a^n}$.",
                "Explain why $3^{-2} \\neq -9$ or $-6$.",
            ],
            "computational": [
                "Evaluate: $5^0 + (-5)^0 - 5^{-2}$.",
                "Simplify with positive exponents: $\\frac{x^{-4} y^2}{z^{-3}}$.",
            ],
            "traps": [
                "Negative Base vs Negative Exponent: Believing $x^{-2}$ is negative. It is strictly positive for any positive $x$ ($1/x^2 > 0$)!",
                "Coefficient Migration Trap: In $3x^{-2}$, moving 3 to the denominator: $3x^{-2} = \\frac{3}{x^2}$, NOT $\\frac{1}{3x^2}$.",
            ],
            "cross": [
                "Physics: Inverse-square laws (gravitational force $F \\propto r^{-2}$, electrostatic force $F \\propto r^{-2}$).",
                "Computer Science: Negative indexing and bit shifting.",
            ],
        },
        "active_recall": [
            {"q": "What is the numerical value of 4^(-3)?", "a": "$\\frac{1}{4^3} = \\frac{1}{64}$."},
            {
                "q": "How do you rewrite 5x^(-4) with a positive exponent?",
                "a": "$\\frac{5}{x^4}$ (only $x$ has the negative exponent, not 5).",
            },
        ],
    },
    "MTH-T01-C08-U06": {
        "title": "Scientific Notation",
        "chapter": "MTH-T01-C08",
        "objective": "Convert between standard decimal notation and scientific notation, and perform multiplication and division with numbers in scientific notation.",
        "expected_output": "Proficiency in scientific notation conversions and arithmetic operations.",
        "concepts": [
            "**Scientific Notation Standard:** A number written in the form $a \\times 10^n$, where $1 \\le |a| < 10$ and $n$ is an integer.",
            "**Positive Exponent ($n > 0$):** Indicates large numbers (shift decimal right $n$ places).",
            "**Negative Exponent ($n < 0$):** Indicates microscopic decimal numbers between 0 and 1 (shift decimal left $|n|$ places).",
            "**Arithmetic Protocol:** Multiply/divide coefficients $a$ separately, add/subtract powers of 10, then normalize $a$ back to $1 \\le |a| < 10$.",
        ],
        "formulas": ["a \\times 10^n \\quad (1 \\le |a| < 10, \\, n \\in \\mathbb{Z})"],
        "example": {
            "title": "Multiplication in Scientific Notation with Normalization",
            "steps": [
                "Multiply: $(4.2 \\times 10^5) \\times (5.0 \\times 10^6)$.",
                "Multiply coefficients: $4.2 \\times 5.0 = 21.0$.",
                "Add powers of 10: $10^5 \\cdot 10^6 = 10^{5+6} = 10^{11}$.",
                "Combine: $21.0 \\times 10^{11}$.",
                "Normalize: $21.0$ is not $< 10$. Shift left: $21.0 = 2.1 \\times 10^1$.",
                "Final scientific notation: $2.1 \\times 10^{12}$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why is $34.5 \\times 10^4$ not in proper scientific notation?",
                "How does scientific notation simplify order of magnitude comparisons?",
            ],
            "computational": [
                "Write in scientific notation: $0.0000452$ and $63,000,000$.",
                "Divide: $\\frac{1.44 \\times 10^8}{1.2 \\times 10^{-3}}$.",
            ],
            "traps": [
                "Failure to Normalize: Leaving $(3 \\times 10^4)(4 \\times 10^5)$ as $12 \\times 10^9$ instead of $1.2 \\times 10^{10}$.",
                "Sign of exponent in small numbers: Writing $0.005$ as $5 \\times 10^3$ instead of $5 \\times 10^{-3}$.",
            ],
            "cross": [
                "Physics ([[PHY-T01-C01-U03]]): Speed of light $c \\approx 3.0 \\times 10^8\\text{ m/s}$, mass of electron $m_e \\approx 9.11 \\times 10^{-31}\\text{ kg}$.",
                "Chemistry: Avogadro's number $N_A \\approx 6.022 \\times 10^{23}\\text{ mol}^{-1}$.",
            ],
        },
        "active_recall": [
            {
                "q": "What two conditions must a number satisfy to be in proper scientific notation a * 10^n?",
                "a": "1. The coefficient $a$ must satisfy $1 \\le |a| < 10$. 2. The exponent $n$ must be an integer.",
            },
            {"q": "Convert 0.000072 into scientific notation.", "a": "$7.2 \\times 10^{-5}$."},
        ],
    },
    # =========================================================================
    # CHAPTER C09: ROOTS (6 Units)
    # =========================================================================
    "MTH-T01-C09-U01": {
        "title": "Introduction to Square Roots",
        "chapter": "MTH-T01-C09",
        "objective": "Define square roots as the inverse of squaring, distinguish principal square roots from equation solutions, and identify perfect squares.",
        "expected_output": "Understanding of radical notation and principal root uniqueness.",
        "concepts": [
            "**Inverse Operation:** Finding a square root is the exact inverse operation of squaring a number.",
            "**Principal Square Root Invariant:** For $a \\ge 0$, $\\sqrt{a} = b$ means $b^2 = a$ and $b \\ge 0$. The radical symbol $\\sqrt{\\cdot}$ strictly denotes the non-negative root.",
            "**Roots of Negatives:** $\\sqrt{-a}$ (where $a > 0$) has no solution in the real number system $\\mathbb{R}$.",
        ],
        "formulas": [
            "\\sqrt{a} = b \\iff b^2 = a \\quad \\text{and} \\quad b \\ge 0",
            "x^2 = a \\implies x = \\pm \\sqrt{a}",
        ],
        "example": {
            "title": "Evaluating Square Roots vs Solving Quadratic Equations",
            "steps": [
                "Evaluate $\\sqrt{49}$: Since $7^2 = 49$ and $7 \\ge 0$, $\\sqrt{49} = 7$.",
                "Evaluate $-\\sqrt{49}$: Negation is outside $\\implies -(7) = -7$.",
                "Solve $x^2 = 49$: Two numbers square to 49 $\\implies x = 7$ or $x = -7$ ($x = \\pm 7$).",
                "Evaluate $\\sqrt{-49}$: No real number squared produces a negative value $\\implies$ Not a real number.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why is $\\sqrt{64}$ strictly equal to +8 and not -8?",
                "Contrast solving $x^2 = 81$ with evaluating $\\sqrt{81}$.",
            ],
            "computational": [
                "Evaluate: $\\sqrt{121}$, $-\\sqrt{169}$, and $\\sqrt{\\frac{36}{121}}$.",
                "Solve for $x$: $x^2 = 100$.",
            ],
            "traps": [
                "Double Sign Trap on Radical: Writing $\\sqrt{36} = \\pm 6$. The radical symbol strictly produces $+6$!",
                "Negative Radicand Error: Writing $\\sqrt{-16} = -4$. (Check: $(-4)^2 = +16 \\neq -16$).",
            ],
            "cross": [
                "Geometry ([[MTH-T01-C12]]): Pythagorean Theorem side length calculations.",
                "Physics ([[PHY-T01-C03]]): Velocity from height in free fall $v = \\sqrt{2gh}$.",
            ],
        },
        "active_recall": [
            {
                "q": "What does the radical symbol sqrt(a) strictly denote?",
                "a": "The principal (non-negative) square root of $a$.",
            },
            {"q": "What are the two real solutions to x^2 = 64?", "a": "$x = +8$ and $x = -8$ ($x = \\pm 8$)."},
        ],
    },
    "MTH-T01-C09-U02": {
        "title": "Simplify Square Roots",
        "chapter": "MTH-T01-C09",
        "objective": "Apply the Product Property of Radicals (sqrt(ab) = sqrt(a) * sqrt(b)) to factor out perfect squares and simplify radical expressions.",
        "expected_output": "Proficiency in simplifying square roots to exact radical form.",
        "concepts": [
            "**Product Property of Radicals:** $\\sqrt{ab} = \\sqrt{a} \\cdot \\sqrt{b}$ for all non-negative real numbers $a, b \\ge 0$.",
            "**Simplest Radical Form:** A square root is in simplest form when the radicand contains no perfect square factors other than 1.",
            "**Factoring Protocol:** Find the largest perfect square factor ($4, 9, 16, 25, 36, 49, 64, 81, 100$) of the radicand and extract its root.",
        ],
        "formulas": [
            "\\sqrt{ab} = \\sqrt{a} \\cdot \\sqrt{b} \\quad (a, b \\ge 0)",
            "\\sqrt{k^2 a} = k\\sqrt{a} \\quad (k > 0)",
        ],
        "example": {
            "title": "Simplifying Square Roots to Exact Form",
            "steps": [
                "Simplify $\\sqrt{72}$:",
                "Find largest perfect square factor: $72 = 36 \\times 2$.",
                "Apply Product Property: $\\sqrt{72} = \\sqrt{36 \\times 2} = \\sqrt{36} \\cdot \\sqrt{2}$.",
                "Evaluate perfect square: $\\sqrt{36} = 6$.",
                "Final simplest form: $6\\sqrt{2}$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why is $2\\sqrt{18}$ not in simplest radical form?",
                "Explain why $\\sqrt{a + b} \\neq \\sqrt{a} + \\sqrt{b}$ using counterexample $a=9, b=16$.",
            ],
            "computational": [
                "Simplify completely: $\\sqrt{48}$, $\\sqrt{200}$, and $\\sqrt{108}$.",
                "Simplify: $3\\sqrt{20} - 2\\sqrt{45}$.",
            ],
            "traps": [
                "Suboptimal factoring trap: Factoring $72 = 4 \\times 18 \\implies 2\\sqrt{18}$ and forgetting that 18 still contains perfect square 9!",
                "Radical Addition Trap: Attempting to combine unlike radicals $\\sqrt{2} + \\sqrt{3} = \\sqrt{5}$ (invalid!).",
            ],
            "cross": [
                "Trigonometry ([[MTH-T02]]): Exact values of special angles ($\to \\sin 45^\\circ = \\frac{\\sqrt{2}}{2}, \\cos 30^\\circ = \\frac{\\sqrt{3}}{2}$).",
                "Geometry ([[MTH-T01-C12]]): Diagonals of squares ($d = s\\sqrt{2}$).",
            ],
        },
        "active_recall": [
            {
                "q": "State the Product Property of Radicals.",
                "a": "$\\sqrt{ab} = \\sqrt{a} \\cdot \\sqrt{b}$ for $a, b \\ge 0$.",
            },
            {"q": "Simplify sqrt(50) into exact radical form.", "a": "$\\sqrt{25 \\times 2} = 5\\sqrt{2}$."},
        ],
    },
    "MTH-T01-C09-U03": {
        "title": "Cube Roots",
        "chapter": "MTH-T01-C09",
        "objective": "Define cube roots as the inverse of cubing, evaluate cube roots of positive and negative real numbers, and simplify cube root expressions.",
        "expected_output": "Mastery of cube roots and negative radicand behavior under odd indices.",
        "concepts": [
            "**Cube Root Invariant:** $\\sqrt[3]{a} = b \\iff b^3 = a$. Unlike square roots, cube roots of negative numbers are valid real numbers!",
            "**Sign Preservation:** $\\sqrt[3]{-a} = -\\sqrt[3]{a}$ because an odd number of negative factors produces a negative product: $(-2)^3 = -8 \\implies \\sqrt[3]{-8} = -2$.",
            "**Product Property of Cube Roots:** $\\sqrt[3]{ab} = \\sqrt[3]{a} \\cdot \\sqrt[3]{b}$.",
        ],
        "formulas": ["\\sqrt[3]{a} = b \\iff b^3 = a", "\\sqrt[3]{-a} = -\\sqrt[3]{a}"],
        "example": {
            "title": "Evaluating and Simplifying Cube Roots",
            "steps": [
                "Evaluate $\\sqrt[3]{-64}$: Since $(-4)^3 = -64$, $\\sqrt[3]{-64} = -4$.",
                "Simplify $\\sqrt[3]{54}$:",
                "Find perfect cube factor ($8, 27, 64, 125$): $54 = 27 \\times 2$.",
                "Apply product rule: $\\sqrt[3]{54} = \\sqrt[3]{27 \\times 2} = \\sqrt[3]{27} \\cdot \\sqrt[3]{2}$.",
                "Evaluate: $\\sqrt[3]{27} = 3 \\implies 3\\sqrt[3]{2}$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why is $\\sqrt[3]{-27}$ a real number, while $\\sqrt{-27}$ is not?",
                "Compare the geometric meaning of square root (side of square) vs cube root (edge of cube).",
            ],
            "computational": [
                "Evaluate: $\\sqrt[3]{125}$, $\\sqrt[3]{-1}$, and $\\sqrt[3]{\\frac{8}{27}}$.",
                "Simplify: $\\sqrt[3]{16}$ and $\\sqrt[3]{-250}$.",
            ],
            "traps": [
                "Even vs Odd Index Trap: Claiming $\\sqrt[3]{-8}$ has no real solution because of the negative sign.",
                "Index confusion: Treating $\\sqrt[3]{27}$ as $\\sqrt{27}$.",
            ],
            "cross": [
                "Geometry ([[MTH-T01-C12]]): Finding the side length of a cube from its volume ($s = \\sqrt[3]{V}$).",
                "Physics: Planetary orbital radius from period via Kepler's Third Law ($r \\propto \\sqrt[3]{T^2}$).",
            ],
        },
        "active_recall": [
            {"q": "What is the cube root of -125?", "a": "-5 (since $(-5)^3 = -125$)."},
            {
                "q": "If a cube has volume 216 cubic centimeters, what is the length of each edge?",
                "a": "Edge $s = \\sqrt[3]{216} = 6\\text{ cm}$.",
            },
        ],
    },
    "MTH-T01-C09-U04": {
        "title": "Properties of Roots",
        "chapter": "MTH-T01-C09",
        "objective": "Apply the Quotient Property of Radicals (sqrt(a/b) = sqrt(a)/sqrt(b)) and rationalize denominators with square roots.",
        "expected_output": "Competence in simplifying radical quotients and eliminating radicals from denominators.",
        "concepts": [
            "**Quotient Property of Radicals:** $\\sqrt{\\frac{a}{b}} = \\frac{\\sqrt{a}}{\\sqrt{b}}$ ($a \\ge 0, b > 0$).",
            "**Rationalizing Denominators:** Rewriting a fraction so that no radicals remain in the denominator, achieved by multiplying numerator and denominator by the appropriate root.",
            "**Multiplicative Identity:** Multiplying $\\frac{a}{\\sqrt{b}}$ by $\\frac{\\sqrt{b}}{\\sqrt{b}} = 1$ clears the radical since $\\sqrt{b} \\cdot \\sqrt{b} = b$.",
        ],
        "formulas": [
            "\\sqrt{\\frac{a}{b}} = \\frac{\\sqrt{a}}{\\sqrt{b}}",
            "\\frac{a}{\\sqrt{b}} = \\frac{a}{\\sqrt{b}} \\cdot \\frac{\\sqrt{b}}{\\sqrt{b}} = \\frac{a\\sqrt{b}}{b}",
        ],
        "example": {
            "title": "Simplifying Radical Quotients and Rationalizing Denominators",
            "steps": [
                "Simplify $\\sqrt{\\frac{50}{18}}$: Reduce fraction inside first: $\\frac{50}{18} = \\frac{25}{9}$.",
                "Apply Quotient Property: $\\sqrt{\\frac{25}{9}} = \\frac{\\sqrt{25}}{\\sqrt{9}} = \\frac{5}{3}$.",
                "Rationalize denominator in $\\frac{6}{\\sqrt{3}}$:",
                "Multiply by $\\frac{\\sqrt{3}}{\\sqrt{3}}$:",
                "\\frac{6}{\\sqrt{3}} \\cdot \\frac{\\sqrt{3}}{\\sqrt{3}} = \\frac{6\\sqrt{3}}{3} = 2\\sqrt{3}",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why is a fraction with a radical in the denominator considered not fully simplified in classical algebra?",
                "Show why reducing a fraction before taking roots is more efficient.",
            ],
            "computational": [
                "Simplify: $\\sqrt{\\frac{48}{75}}$.",
                "Rationalize the denominator: $\\frac{5}{\\sqrt{7}}$ and $\\frac{12}{\\sqrt{6}}$.",
            ],
            "traps": [
                "Incomplete cancellation: In $\\frac{6\\sqrt{3}}{3}$, canceling 3 with the radicand inside the square root instead of the outside coefficient!",
                "Squaring numerator and denominator: In $\\frac{2}{\\sqrt{5}}$, squaring both to get $\\frac{4}{5}$, which alters the numerical value!",
            ],
            "cross": [
                "Trigonometry ([[MTH-T02]]): Rationalizing trigonometric values (e.g. $\\frac{1}{\\sqrt{2}} = \\frac{\\sqrt{2}}{2}$).",
                "Physics: Period of simple pendulum $T = 2\\pi \\sqrt{\\frac{L}{g}}$.",
            ],
        },
        "active_recall": [
            {
                "q": "State the Quotient Property of Radicals.",
                "a": "$\\sqrt{\\frac{a}{b}} = \\frac{\\sqrt{a}}{\\sqrt{b}}$ for $a \\ge 0, b > 0$.",
            },
            {
                "q": "How do you rationalize the denominator of 4 / sqrt(2)?",
                "a": "Multiply numerator and denominator by $\\sqrt{2}$: $\\frac{4\\sqrt{2}}{\\sqrt{2} \\cdot \\sqrt{2}} = \\frac{4\\sqrt{2}}{2} = 2\\sqrt{2}$.",
            },
        ],
    },
    "MTH-T01-C09-U05": {
        "title": "Roots and Fractional Exponents",
        "chapter": "MTH-T01-C09",
        "objective": "Connect radicals to rational (fractional) exponents (x^(1/n) = nth-root(x)) and evaluate expressions with fractional exponents.",
        "expected_output": "Mastery of the rational exponent bridge x^(m/n) = (nth-root(x))^m.",
        "concepts": [
            "**The Rational Exponent Bridge:** A fractional exponent $\\frac{1}{n}$ denotes the $n$-th root: $x^{1/n} = \\sqrt[n]{x}$.",
            "**General Rational Exponent:** In $x^{m/n}$, the denominator $n$ is the root index, and numerator $m$ is the power: $x^{m/n} = (\\sqrt[n]{x})^m = \\sqrt[n]{x^m}$.",
            "**Evaluation Order Invariant:** When evaluating numerically, taking the root first ($(\\sqrt[n]{x})^m$) keeps numbers smaller and easier to compute.",
        ],
        "formulas": ["x^{1/n} = \\sqrt[n]{x}", "x^{m/n} = (\\sqrt[n]{x})^m = \\sqrt[n]{x^m}"],
        "example": {
            "title": "Evaluating Expressions with Rational Exponents",
            "steps": [
                "Evaluate $16^{3/4}$:",
                "Identify index and power: Root index is $4$, power is $3$.",
                "Take 4th root first: $(\\sqrt[4]{16})^3$.",
                "Evaluate root: $\\sqrt[4]{16} = 2$ (since $2^4 = 16$).",
                "Apply power: $2^3 = 8$.",
                "Evaluate $27^{-2/3}$:",
                "Negative exponent reciprocal: $\\frac{1}{27^{2/3}} = \\frac{1}{(\\sqrt[3]{27})^2} = \\frac{1}{3^2} = \\frac{1}{9}$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why does $x^{1/2} \\cdot x^{1/2} = x^1$ prove that $x^{1/2} = \\sqrt{x}$ by the Product Property of Exponents?",
                "Why is it usually easier to evaluate $(\\sqrt[n]{x})^m$ than $\\sqrt[n]{x^m}$ by hand?",
            ],
            "computational": [
                "Evaluate: $81^{1/2}$, $64^{2/3}$, and $32^{-3/5}$.",
                "Rewrite in radical form: $x^{5/3}$ and $(2y)^{3/4}$.",
            ],
            "traps": [
                "Root vs Power inversion: Treating $x^{2/3}$ as $\\sqrt{x^3}$ instead of $\\sqrt[3]{x^2}$. Denominator is always the root!",
                "Powering the base instead of root: Computing $16^{3/4}$ as $16 \\times \\frac{3}{4} = 12$.",
            ],
            "cross": [
                "Calculus: Power Rule for derivatives $\\frac{d}{dx}[x^{m/n}] = \\frac{m}{n} x^{m/n - 1}$.",
                "Physics: Scaling laws and adiabatic gas expansion $PV^\\gamma = k$.",
            ],
        },
        "active_recall": [
            {
                "q": "In the rational exponent expression x^(m/n), what do m and n represent?",
                "a": "The denominator $n$ represents the root index (the $n$-th root), and the numerator $m$ represents the exponent power.",
            },
            {"q": "Evaluate 25^(3/2).", "a": "$(\\sqrt{25})^3 = 5^3 = 125$."},
        ],
    },
    "MTH-T01-C09-U06": {
        "title": "Simplify Roots with Scientific Notation",
        "chapter": "MTH-T01-C09",
        "objective": "Evaluate square and cube roots of numbers expressed in scientific notation by partitioning powers of 10 into even or multiple-of-3 exponents.",
        "expected_output": "Proficiency in evaluating radicals of extreme quantities in scientific notation.",
        "concepts": [
            "**Even Exponent Invariant for Square Roots:** $\\sqrt{10^{2k}} = (10^{2k})^{1/2} = 10^k$. The exponent of 10 must be even before extracting a square root.",
            "**Odd Exponent Normalization:** If the exponent $n$ is odd, adjust the decimal coefficient by 1 place to make the exponent even: $4.0 \\times 10^7 = 40.0 \\times 10^6 \\implies \\sqrt{40} \\times 10^3$.",
            "**Cube Root Exponent Invariant:** For cube roots, the power of 10 must be a multiple of 3: $\\sqrt[3]{10^{3k}} = 10^k$.",
        ],
        "formulas": [
            "\\sqrt{a \\times 10^{2k}} = \\sqrt{a} \\times 10^k",
            "\\sqrt[3]{a \\times 10^{3k}} = \\sqrt[3]{a} \\times 10^k",
        ],
        "example": {
            "title": "Evaluating Square Root in Scientific Notation",
            "steps": [
                "Evaluate $\\sqrt{9.0 \\times 10^{10}}$:",
                "Exponent 10 is even $\\implies \\sqrt{9.0} \\times \\sqrt{10^{10}} = 3.0 \\times 10^{10/2} = 3.0 \\times 10^5$.",
                "Evaluate $\\sqrt{4.0 \\times 10^7}$:",
                "Exponent 7 is odd. Shift decimal to make exponent even: $4.0 \\times 10^7 = 40 \\times 10^6$.",
                "Extract roots: $\\sqrt{40} \\times \\sqrt{10^6} \\approx 6.32 \\times 10^3$.",
            ],
        },
        "practice_guide": {
            "conceptual": [
                "Why must the power of 10 be even when taking a square root?",
                "How do you adjust $a \\times 10^n$ if $n$ is not divisible by the root index?",
            ],
            "computational": [
                "Evaluate: $\\sqrt{1.44 \\times 10^{-6}}$.",
                "Evaluate: $\\sqrt[3]{8.0 \\times 10^{12}}$.",
                "Evaluate: $\\sqrt{2.5 \\times 10^5}$.",
            ],
            "traps": [
                "Halving an odd exponent: Writing $\\sqrt{10^7} = 10^{3.5}$ and leaving it in an unsimplified non-integer scientific notation.",
                "Forgetting to take the root of the coefficient: Taking $\\sqrt{9 \\times 10^6} = 9 \\times 10^3$ instead of $3 \\times 10^3$.",
            ],
            "cross": [
                "Physics ([[PHY-T01-C01-U03]]): Astronomical calculations of orbital period and distance ($r = \\sqrt{G M / g}$).",
                "Quantum Physics: De Broglie wavelength and Planck constant calculations.",
            ],
        },
        "active_recall": [
            {
                "q": "What is the square root of 4.0 * 10^8 in scientific notation?",
                "a": "$2.0 \\times 10^4$ (since $\\sqrt{4} = 2$ and $\\sqrt{10^8} = 10^4$).",
            },
            {
                "q": "How do you prepare sqrt(1.6 * 10^5) for evaluation?",
                "a": "Shift the decimal to make the exponent even: $1.6 \\times 10^5 = 16 \\times 10^4$. Then $\\sqrt{16 \\times 10^4} = 4 \\times 10^2 = 400$.",
            },
        ],
    },
}
