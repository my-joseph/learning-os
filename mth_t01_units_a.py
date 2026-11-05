# -*- coding: utf-8 -*-
"""
Instructional content for MTH-T01 Units: C01 through C04 (21 Units).
Source: OpenStax Prealgebra 2e (Chapters 1-4).
"""

MTH_UNITS_A = {
    "MTH-T01-C01-U01": {
        "title": "Introduction to Whole Numbers",
        "obj": "Identify counting numbers and whole numbers, model base-10 place value, write whole numbers in words/expanded form, and round to specified place values.",
        "out": "Decompose multi-digit whole numbers into expanded powers of 10 and round numbers accurately to any place value.",
        "prereq": "None (Foundational Unit)",
        "source": "OpenStax Prealgebra 2e — Section 1.1: Introduction to Whole Numbers (Verified HTTP 200).",
        "concepts": [
            "Counting Numbers vs. Whole Numbers: Counting (natural) numbers are $\\mathbb{N} = \\{1, 2, 3, \\dots\\}$. Adjoining zero forms the Whole Numbers $\\mathbb{W} = \\{0, 1, 2, 3, \\dots\\}$.",
            "Base-10 Place Value & Periods: Each position represents a power of $10$ ($10^0=1, 10^1=10, 10^2=100, \\dots$), grouped right-to-left into three-digit periods (ones, thousands, millions, billions).",
            "Rounding Rule: Locate the target place value and inspect the single digit immediately to its right (the test digit). If the test digit is $\\ge 5$, add $1$ to the target digit; if $< 5$, keep the target digit unchanged, then replace all digits to the right with zeros."
        ],
        "equation": "52,804 = 5 \\times 10^4 + 2 \\times 10^3 + 8 \\times 10^2 + 0 \\times 10^1 + 4 \\times 10^0",
        "worked": "Example: Round $849,612$ to the nearest thousand.\n1. Target digit (thousands place): $9$. Test digit to its right (hundreds place): $6$.\n2. Since $6 \\ge 5$, increase $9$ by $1$ (which carries into the ten-thousands place: $49 \\to 50$).\n3. Replace all digits to the right with zeros: $850,000$.",
        "exercises": [
            "Write $70,409,050$ in expanded base-10 form and in words.",
            "Round $399,540$ to the nearest (a) hundred, (b) thousand, and (c) ten-thousand."
        ],
        "recall": [
            ("What is the exact difference between the set of Counting Numbers and the set of Whole Numbers?", "The set of Whole Numbers includes $0$ ($\\{0, 1, 2, 3, \\dots\\}$), whereas Counting (Natural) Numbers start at $1$ ($\\{1, 2, 3, \\dots\\}$)."),
            ("When rounding $48,499$ to the nearest thousand, why is the answer $48,000$ and not $49,000$?", "Rounding depends ONLY on the single test digit immediately to the right of the target place (the hundreds digit $4 < 5$); you never chain-round from the ones/tens digits.")
        ]
    },
    "MTH-T01-C01-U02": {
        "title": "Add Whole Numbers",
        "obj": "Use addition notation, the Identity and Commutative Properties of Addition, and the standard carrying algorithm to add whole numbers and perimeter models.",
        "out": "Add multi-digit whole numbers accurately by hand and verify results via estimation.",
        "prereq": "MTH-T01-C01-U01 (Introduction to Whole Numbers)",
        "source": "OpenStax Prealgebra 2e — Section 1.2: Add Whole Numbers (Verified HTTP 200).",
        "concepts": [
            "Addition Properties: Identity Property of Addition states $a + 0 = a = 0 + a$. Commutative Property of Addition states $a + b = b + a$.",
            "Place-Value Carrying (Regrouping): Only digits in the same place-value column can be added directly. Whenever a column sum reaches $10$ or more, bundle each group of $10$ into $1$ unit of the next higher place value to the left.",
            "Translation Keywords: 'Sum of', 'increased by', 'more than', 'total of', and geometric 'perimeter' (sum of all outer side lengths)."
        ],
        "equation": "a + 0 = a, \\quad a + b = b + a, \\quad (a + b) + c = a + (b + c)",
        "worked": "Example: Compute $4,786 + 3,597$.\n1. Ones: $6 + 7 = 13$ (write $3$, carry $1$ ten).\n2. Tens: $1 + 8 + 9 = 18$ (write $8$, carry $1$ hundred).\n3. Hundreds: $1 + 7 + 5 = 13$ (write $3$, carry $1$ thousand).\n4. Thousands: $1 + 4 + 3 = 8$. Result: $8,383$ (Estimate check: $4,800 + 3,600 = 8,400$).",
        "exercises": [
            "Compute $58,947 + 6,385 + 409$ by hand and check by rounding to the nearest thousand.",
            "Find the perimeter of a rectangular plot of land measuring $145\\text{ m}$ by $88\\text{ m}$."
        ],
        "recall": [
            ("Why do we align numbers vertically by their rightmost digit when adding whole numbers?", "To ensure we only combine like powers of $10$ (ones with ones, tens with tens, hundreds with hundreds)."),
            ("What mathematical property justifies checking column addition by adding bottom-to-top after adding top-to-bottom?", "The Commutative and Associative Properties of Addition, which guarantee that reordering addends does not change the sum.")
        ]
    },
    "MTH-T01-C01-U03": {
        "title": "Subtract Whole Numbers",
        "obj": "Model subtraction as the inverse of addition, apply the borrowing/regrouping algorithm across zeros, and translate subtraction word phrases accurately.",
        "out": "Subtract multi-digit whole numbers across multiple zeros and verify every difference via addition.",
        "prereq": "MTH-T01-C01-U02 (Add Whole Numbers)",
        "source": "OpenStax Prealgebra 2e — Section 1.3: Subtract Whole Numbers (Verified HTTP 200).",
        "concepts": [
            "Inverse Definition of Subtraction: In $a - b = c$ ($a$: minuend, $b$: subtrahend, $c$: difference), $a - b = c \\iff c + b = a$. Subtraction is NOT commutative ($a - b \\ne b - a$).",
            "Regrouping Across Zeros: When subtracting from a number like $5,000$, unbundle $1$ thousand into $10$ hundreds ($4\\text{ thousands} + 9\\text{ hundreds} + 9\\text{ tens} + 10\\text{ ones}$) before subtracting column by column.",
            "Order-Sensitive Translation Trap: 'Subtract $a$ from $b$' and '$a$ less than $b$' both translate to $b - a$, NOT $a - b$."
        ],
        "equation": "a - b = c \\iff c + b = a, \\qquad a - a = 0, \\qquad a - 0 = a",
        "worked": "Example: Compute $60,003 - 24,587$.\n1. Regroup $60,003$ as $5\\text{ ten-thousands}, 9\\text{ thousands}, 9\\text{ hundreds}, 9\\text{ tens}, 13\\text{ ones}$.\n2. Subtract column by column: $13-7=6$, $9-8=1$, $9-5=4$, $9-4=5$, $5-2=3 \\implies 35,416$.\n3. Check by addition: $35,416 + 24,587 = 60,003$.",
        "exercises": [
            "Compute $80,200 - 39,764$ and verify your answer using addition.",
            "Translate and evaluate: '185 less than the sum of 412 and 98'."
        ],
        "recall": [
            ("How do the phrases '$12$ less $5$' and '$12$ less than $5$' differ in algebraic translation?", "'$12$ less $5$' means $12 - 5$, whereas '$12$ less than $5$' means $5 - 12$ (starting from $5$ and subtracting $12$)."),
            ("How can you immediately verify whether a multi-digit subtraction $a - b = c$ is correct?", "Add the difference and the subtrahend ($c + b$); the sum must equal the original minuend $a$.")
        ]
    },
    "MTH-T01-C01-U04": {
        "title": "Multiply Whole Numbers",
        "obj": "Apply the Zero, Identity, Commutative, and Distributive properties of multiplication, multiply multi-digit whole numbers, and compute rectangular areas.",
        "out": "Multiply multi-digit numbers using partial products and explain why each row shifts left by one place value.",
        "prereq": "MTH-T01-C01-U02 (Add Whole Numbers)",
        "source": "OpenStax Prealgebra 2e — Section 1.4: Multiply Whole Numbers (Verified HTTP 200).",
        "concepts": [
            "Multiplication Properties: Zero Property $a \\cdot 0 = 0$; Identity Property $a \\cdot 1 = a$; Commutative $ab = ba$; Associative $(ab)c = a(bc)$.",
            "Partial Products as Distributive Law: Multiplying $438 \\times 52$ uses the distributive property $438 \\times (50 + 2) = 438 \\times 2 + 438 \\times 50$. The trailing $0$ in the second partial product comes from multiplying by $5$ tens ($50$).",
            "Multiplication by Powers of 10: Multiplying a whole number by $10^k$ appends $k$ zeros to the right."
        ],
        "equation": "a(b + c) = ab + ac, \\qquad a \\cdot 0 = 0, \\qquad a \\cdot 1 = a",
        "worked": "Example: Compute $608 \\times 47$.\n1. First partial product: $608 \\times 7 = 4,256$.\n2. Second partial product: $608 \\times 40 = 24,320$.\n3. Sum partial products: $4,256 + 24,320 = 28,576$.",
        "exercises": [
            "Compute $904 \\times 308$ by hand, paying careful attention to the zero in the tens place of both factors.",
            "Find the area and perimeter of a server room floor measuring $24\\text{ ft}$ by $18\\text{ ft}$ (include correct units: $\\text{ft}^2$ vs. $\\text{ft}$)."
        ],
        "recall": [
            ("Why do we place a zero in the ones column of the second row when multiplying a multi-digit number by a two-digit multiplier?", "Because we are multiplying by the tens digit ($d \\times 10$), so every resulting product is a multiple of $10$."),
            ("What is the difference in units between the perimeter and the area of a rectangle measured in meters?", "Perimeter is a 1D length measured in linear meters ($\\text{m}$), whereas area is a 2D surface measured in square meters ($\\text{m}^2$).")
        ]
    },
    "MTH-T01-C01-U05": {
        "title": "Divide Whole Numbers",
        "obj": "Use division notation, apply division properties of one and zero, execute long division with remainders, and verify via the Division Algorithm.",
        "out": "Perform multi-digit long division and verify the quotient and remainder using $D = d \\cdot q + r$.",
        "prereq": "MTH-T01-C01-U03 (Subtract Whole Numbers), MTH-T01-C01-U04 (Multiply Whole Numbers)",
        "source": "OpenStax Prealgebra 2e — Section 1.5: Divide Whole Numbers (Verified HTTP 200).",
        "concepts": [
            "Division Algorithm Invariant: Dividing dividend $D$ by nonzero divisor $d$ yields unique whole numbers quotient $q$ and remainder $r$ such that $D = d \\cdot q + r$ with $0 \\le r < d$.",
            "Division Properties of Zero: $0 \\div a = 0$ (for $a \\ne 0$) because $0 \\cdot a = 0$. However, $a \\div 0$ is UNDEFINED because no number $q$ satisfies $q \\cdot 0 = a$ (and for $0 \\div 0$, every number satisfies $q \\cdot 0 = 0$, so it is indeterminate/undefined).",
            "Zero Placeholders in Long Division: After bringing down a digit, if the divisor is larger than the current partial dividend, you MUST write a $0$ in that quotient place before bringing down the next digit."
        ],
        "equation": "D = d \\cdot q + r \\quad (0 \\le r < d), \\qquad \\frac{0}{a} = 0 \\ (a \\ne 0), \\qquad \\frac{a}{0} \\text{ is undefined}",
        "worked": "Example: Compute $15,629 \\div 39$.\n1. $156 \\div 39 = 4$ ($4 \\times 39 = 156$, remainder $0$).\n2. Bring down $2$: since $2 < 39$, write $0$ in the tens place of the quotient!\n3. Bring down $9$ to make $29$: since $29 < 39$, write $0$ in the ones place of the quotient.\n4. Result: $q = 400$ with remainder $r = 29$. Check: $39 \\times 400 + 29 = 15,600 + 29 = 15,629$.",
        "exercises": [
            "Compute $24,385 \\div 48$ and verify using $D = d \\cdot q + r$.",
            "A warehouse must ship $1,250$ monitors in crates that hold $24$ monitors each. How many full crates are filled, and how many crates are needed in total to ship every monitor?"
        ],
        "recall": [
            ("Use the inverse relationship with multiplication to explain why $\\frac{12}{0}$ is undefined while $\\frac{0}{12} = 0$.", "If $\\frac{12}{0} = q$, then $q \\cdot 0 = 12$, which is impossible since any number times $0$ is $0$. Conversely, $\\frac{0}{12} = 0$ because $0 \\cdot 12 = 0$."),
            ("In long division, why is $1,218 \\div 6 = 203$ and not $23$?", "After $12 \\div 6 = 2$, bringing down $1$ gives a partial dividend of $1 < 6$, requiring a $0$ in the tens place of the quotient before bringing down $8$ to form $18 \\div 6 = 3$.")
        ]
    },
    "MTH-T01-C02-U01": {
        "title": "Use the Language of Algebra",
        "obj": "Distinguish variables, constants, expressions, and equations, use exponential notation, and simplify expressions using the Order of Operations.",
        "out": "Simplify multi-operation numerical expressions containing nested grouping symbols and exponents.",
        "prereq": "MTH-T01-C01 (Whole Numbers)",
        "source": "OpenStax Prealgebra 2e — Section 2.1: Use the Language of Algebra (Verified HTTP 200).",
        "concepts": [
            "Expressions vs. Equations & Inequalities: An expression ($4x + 7$) has no equals/inequality sign and simplifies to a value; an equation ($4x + 7 = 19$) or inequality ($4x + 7 < 19$) is a mathematical sentence that is either true or false.",
            "Exponential Notation: $a^n$ means $n$ factors of $a$ multiplied together ($a^n = \\underbrace{a \\cdot a \\cdots a}_{n\\text{ factors}}$).",
            "Order of Operations (Left-to-Right Equal Precedence): (1) Grouping symbols $(), [], \\{\\}$, fraction bars; (2) Exponents and roots; (3) Multiplication AND Division from LEFT to RIGHT; (4) Addition AND Subtraction from LEFT to RIGHT."
        ],
        "equation": "24 \\div 4 \\cdot 3 = (24 \\div 4) \\cdot 3 = 6 \\cdot 3 = 18 \\quad (\\text{NOT } 24 \\div 12 = 2)",
        "worked": "Example: Simplify $18 \\div 3 \\cdot 2 + 4[15 - 2(3 + 1)^2] + 50$.\n1. Innermost parentheses: $(3+1) = 4$.\n2. Exponent inside brackets: $4^2 = 16$, then multiply by $2$: $2(16) = 32$.\n3. Note on whole numbers: for whole-number domain, consider $4[20 - 2(3)^2]$: $2(9)=18 \\implies 20-18=2 \\implies 4(2)=8$.\n4. Left-to-right division/multiplication: $18 \\div 3 \\cdot 2 = 6 \\cdot 2 = 12$.\n5. Add: $12 + 8 = 20$.",
        "exercises": [
            "Simplify $36 \\div 9 \\cdot 4 - 2^3 + 3(12 - 5)$ step-by-step.",
            "Simplify $\\frac{5^2 - 1}{2^3 - 2} + 4[18 - 3(2 + 3)]$."
        ],
        "recall": [
            ("Why does $30 - 10 + 5$ equal $25$ instead of $15$, and why does $30 \\div 5 \\cdot 2$ equal $12$ instead of $3$?", "Subtraction and addition share the same precedence level and are evaluated strictly left-to-right; similarly, division and multiplication share the same precedence level and are evaluated left-to-right."),
            ("How does a fraction bar act as an invisible grouping symbol in $\\frac{14 + 6}{9 - 4}$?", "A fraction bar groups the entire numerator and the entire denominator separately, equivalent to $(14 + 6) \\div (9 - 4) = 20 \\div 5 = 4$.")
        ]
    },
    "MTH-T01-C02-U02": {
        "title": "Evaluate, Simplify, and Translate Expressions",
        "obj": "Evaluate algebraic expressions for given values, identify terms, coefficients, and like terms, combine like terms, and translate English phrases into algebraic expressions.",
        "out": "Evaluate multi-variable expressions, combine like terms, and translate verbal descriptions into algebraic expressions.",
        "prereq": "MTH-T01-C02-U01 (Use the Language of Algebra)",
        "source": "OpenStax Prealgebra 2e — Section 2.2: Evaluate, Simplify, and Translate Expressions (Verified HTTP 200).",
        "concepts": [
            "Substitution with Parentheses: When evaluating an expression for a given variable value, always wrap the substituted value in parentheses first to preserve multiplication and exponent grouping.",
            "Anatomy of an Algebraic Expression: Terms are separated by $+$ or $-$ signs. The numerical factor of a term is its coefficient (the coefficient of $x$ is $1$).",
            "Combining Like Terms: Like terms have the EXACT same variables raised to the EXACT same exponents ($5x^2$ and $3x^2$ are like terms; $5x^2$ and $3x$ are NOT). Combine like terms by adding/subtracting their coefficients via the distributive property: $5x^2 + 3x^2 = (5+3)x^2 = 8x^2$."
        ],
        "equation": "ax^k + bx^k = (a + b)x^k",
        "worked": "Example: Simplify $7x^2 + 4x + 9 + 2x^2 + 5x + 3$, then evaluate for $x = 2$.\n1. Group like terms: $(7x^2 + 2x^2) + (4x + 5x) + (9 + 3) = 9x^2 + 9x + 12$.\n2. Substitute $x = (2)$: $9(2)^2 + 9(2) + 12 = 9(4) + 18 + 12 = 36 + 30 = 66$.",
        "exercises": [
            "Simplify $12y^2 + 8y + 5 + 3y^2 + y + 11$ and evaluate at $y = 3$.",
            "Translate: 'The quotient of eight times a number $n$ and the difference of $n$ and three'."
        ],
        "recall": [
            ("Why can $4x^2 + 7x^2$ be simplified to $11x^2$, while $4x^2 + 7x$ cannot be combined into a single term?", "Combining like terms relies on factoring out a common variable part via $ax^2 + bx^2 = (a+b)x^2$. Since $x^2$ and $x$ represent different quantities, they do not share an identical variable part."),
            ("Why doesn't the exponent change when you add $5x^3 + 2x^3 = 7x^3$?", "Because addition counts how many $x^3$ units we have ($5$ of them plus $2$ of them equals $7$ of them); exponents only change when multiplying bases ($x^3 \\cdot x^3 = x^6$).")
        ]
    },
    "MTH-T01-C02-U03": {
        "title": "Solving Equations Using the Subtraction and Addition Properties of Equality",
        "obj": "Verify whether a value is a solution to an equation, and solve one-step equations using the Subtraction and Addition Properties of Equality.",
        "out": "Solve and check one-step linear equations and word problems using inverse addition/subtraction operations.",
        "prereq": "MTH-T01-C02-U02 (Evaluate, Simplify, and Translate Expressions)",
        "source": "OpenStax Prealgebra 2e — Section 2.3: Solving Equations Using the Subtraction and Addition Properties of Equality (Verified HTTP 200).",
        "concepts": [
            "Solution of an Equation: A value of the variable that makes the equation a true statement when substituted.",
            "Subtraction & Addition Properties of Equality: For any real numbers $a, b, c$: if $a = b$, then $a - c = b - c$ and $a + c = b + c$. Doing the exact same additive operation to both sides keeps the balance scale level.",
            "Isolating the Variable via Inverse Operations: To undo addition ($x + c = d$), subtract $c$ from both sides; to undo subtraction ($x - c = d$), add $c$ to both sides so the constant term becomes $+ 0$."
        ],
        "equation": "x + c = d \\implies x = d - c, \\qquad x - c = d \\implies x = d + c",
        "worked": "Example: Solve $x - 47 = 128$ and check.\n1. Add $47$ to both sides: $x - 47 + 47 = 128 + 47$.\n2. Simplify: $x = 175$.\n3. Check: Substitute $x = 175$ into original: $175 - 47 = 128$ (True).",
        "exercises": [
            "Solve and check: (a) $y + 89 = 214$, (b) $m - 136 = 264$.",
            "After a $35\\text{ GB}$ backup was deleted, a drive had $188\\text{ GB}$ used. Write and solve an equation for the initial used space $s$."
        ],
        "recall": [
            ("What is the difference between 'simplifying an expression' and 'solving an equation'?", "Simplifying an expression rewrites it in a more compact equivalent form using properties like combining like terms; solving an equation finds the specific variable value(s) that make the equality true."),
            ("Why do we add $19$ to both sides to solve $x - 19 = 30$?", "Because $+19$ is the additive inverse of $-19$, yielding $x + 0 = x$ on the left side while preserving equality on the right side.")
        ]
    },
    "MTH-T01-C02-U04": {
        "title": "Find Multiples and Factors",
        "obj": "Identify multiples using divisibility tests (2, 3, 5, 6, 9, 10), find all factor pairs of a whole number, and classify numbers as prime or composite.",
        "out": "Apply divisibility tests rapidly and list complete factor sets of composite numbers.",
        "prereq": "MTH-T01-C01-U04, MTH-T01-C01-U05",
        "source": "OpenStax Prealgebra 2e — Section 2.4: Find Multiples and Factors (Verified HTTP 200).",
        "concepts": [
            "Factors vs. Multiples: If $a \\cdot b = m$, then $a$ and $b$ are factors (divisors) of $m$, and $m$ is a multiple of both $a$ and $b$. A number has finitely many factors (bounded between $1$ and $m$) but infinitely many multiples.",
            "Rapid Divisibility Tests: Divisible by $2$ if last digit is even; by $3$ if sum of digits is divisible by $3$; by $5$ if last digit is $0$ or $5$; by $6$ if divisible by BOTH $2$ and $3$; by $9$ if sum of digits is divisible by $9$; by $10$ if last digit is $0$.",
            "Prime vs. Composite Numbers: A prime number ($2, 3, 5, 7, 11, \\dots$) is a whole number greater than $1$ whose only factors are $1$ and itself. A composite number has other factors. The number $1$ is neither prime nor composite."
        ],
        "equation": "\\text{Test factor pairs } d \\text{ only up to } d \\le \\sqrt{n}",
        "worked": "Example: Find all factors of $72$.\n1. Test integers $d$ up to $\\sqrt{72} \\approx 8.4$: $1 \\times 72, 2 \\times 36, 3 \\times 24, 4 \\times 18, 6 \\times 12, 8 \\times 9$.\n2. Complete ordered factor list: $1, 2, 3, 4, 6, 8, 9, 12, 18, 24, 36, 72$.",
        "exercises": [
            "Test $4,752$ for divisibility by $2, 3, 5, 6, 9,$ and $10$ without performing long division.",
            "List all factors of $120$ and determine whether $103$ is prime or composite (explain which primes you need to test)."
        ],
        "recall": [
            ("Why is the number $1$ classified as neither prime nor composite?", "By definition, a prime has exactly two distinct positive factors ($1$ and itself), while $1$ has only one factor; making $1$ prime would break the uniqueness of prime factorization."),
            ("To check whether $97$ is prime, why do you only need to test divisibility by primes $2, 3, 5,$ and $7$?", "Because $\\sqrt{97} < 10$. If $97$ had a factor greater than $10$, its partner factor would have to be less than $10$, which would already be caught by testing primes $\\le 7$.")
        ]
    },
    "MTH-T01-C02-U05": {
        "title": "Prime Factorization and the Least Common Multiple",
        "obj": "Write the unique prime factorization of any composite number and compute the Least Common Multiple (LCM) using prime factors.",
        "out": "Compute prime factorizations and LCMs of two or three numbers using the prime-powers method.",
        "prereq": "MTH-T01-C02-U04 (Find Multiples and Factors)",
        "source": "OpenStax Prealgebra 2e — Section 2.5: Prime Factorization and the Least Common Multiple (Verified HTTP 200).",
        "concepts": [
            "Fundamental Theorem of Arithmetic: Every composite whole number can be written as a product of prime numbers in one and only one way (up to the order of factors).",
            "Prime Factorization via Factor Tree or Division Ladder: Repeatedly divide by the smallest prime factor ($2, 3, 5, 7, \\dots$) until the quotient is prime, then write in exponential form ($p_1^{a_1} p_2^{a_2} \\cdots$).",
            "LCM via Prime Powers: To find $\\text{LCM}(a, b)$, write each number in prime-power form and take the product of all prime bases present, each raised to the HIGHEST exponent that appears in either factorization."
        ],
        "equation": "\\text{LCM}(p_1^{a_1}p_2^{a_2},\\ p_1^{b_1}p_2^{b_2}) = p_1^{\\max(a_1, b_1)} p_2^{\\max(a_2, b_2)}",
        "worked": "Example: Find $\\text{LCM}(36, 48, 60)$.\n1. Prime factorizations: $36 = 2^2 \\cdot 3^2$, $48 = 2^4 \\cdot 3^1$, $60 = 2^2 \\cdot 3^1 \\cdot 5^1$.\n2. Highest power of each prime: $2^4$, $3^2$, $5^1$.\n3. $\\text{LCM} = 2^4 \\cdot 3^2 \\cdot 5 = 16 \\cdot 9 \\cdot 5 = 720$.",
        "exercises": [
            "Find the prime factorization in exponential form for $360$ and $504$.",
            "Find the Least Common Multiple (LCM) of $45, 75,$ and $90$ using the prime factorization method."
        ],
        "recall": [
            ("Why do we take the HIGHEST power of each prime factor when computing the LCM?", "Because the LCM must be a multiple of every input number, so its prime factorization must contain at least as many copies of each prime factor as the input number that has the most."),
            ("How is the LCM method used directly in Chapter 4 (Fractions)?", "The Least Common Denominator (LCD) of two or more fractions is simply the Least Common Multiple (LCM) of their denominators.")
        ]
    },
    "MTH-T01-C03-U01": {
        "title": "Introduction to Integers",
        "obj": "Locate positive and negative integers on the number line, order integers using inequality symbols, find opposites, and simplify expressions with absolute value.",
        "out": "Evaluate nested opposite and absolute value expressions and order signed numbers accurately.",
        "prereq": "MTH-T01-C02 (The Language of Algebra)",
        "source": "OpenStax Prealgebra 2e — Section 3.1: Introduction to Integers (Verified HTTP 200).",
        "concepts": [
            "Integers & Number Line Ordering: $\\mathbb{Z} = \\{\\dots, -3, -2, -1, 0, 1, 2, 3, \\dots\\}$. On a horizontal number line, $a < b$ whenever $a$ lies to the LEFT of $b$ (so $-10 < -2$).",
            "Opposite Notation ($-a$): $-a$ means 'the opposite of $a$', NOT necessarily a negative number! If $a = -7$, then $-a = -(-7) = +7$.",
            "Absolute Value ($|a|$) as Grouping & Distance: $|a|$ is the non-negative distance from $a$ to $0$. Inside an expression, absolute value bars act as grouping symbols: simplify inside $|\\dots|$ completely first, take the non-negative magnitude, and ONLY THEN apply any outside negative sign."
        ],
        "equation": "|a| = \\begin{cases} a, & a \\ge 0 \\\\ -a, & a < 0 \\end{cases}, \\qquad -|-5| = -(5) = -5 \\ne -(-5) = 5",
        "worked": "Example: Simplify $24 - |19 - 3(8 - 2)|$ and compare $-|-9|$ vs. $-(-9)$.\n1. Inside absolute value: $8 - 2 = 6 \\implies 3(6) = 18 \\implies |19 - 18| = |1| = 1$.\n2. $24 - 1 = 23$.\n3. $-|-9| = -(9) = -9$, whereas $-(-9) = +9$, so $-|-9| < -(-9)$.",
        "exercises": [
            "Evaluate $-|x|$ and $|-x|$ when $x = -14$.",
            "Simplify $35 - 3|10 - 4(2 + 1)|$."
        ],
        "recall": [
            ("Why is $-(-8) = 8$, whereas $-|-8| = -8$?", "In $-(-8)$, the opposite of $-8$ is $+8$. In $-|-8|$, we first evaluate the absolute value $|-8| = 8$, and then the outside negative sign takes the opposite of $8$, giving $-8$."),
            ("Is the algebraic expression $-x$ always negative? Explain.", "No! $-x$ means 'the opposite of $x$'. If $x$ is negative (e.g., $x = -5$), then $-x = -(-5) = +5$, which is positive.")
        ]
    },
    "MTH-T01-C03-U02": {
        "title": "Add Integers",
        "obj": "Add integers with the same sign and with different signs, evaluate variable expressions with integers, and model net change.",
        "out": "Compute sums of multiple signed integers fluently without number-line drawing.",
        "prereq": "MTH-T01-C03-U01 (Introduction to Integers)",
        "source": "OpenStax Prealgebra 2e — Section 3.2: Add Integers (Verified HTTP 200).",
        "concepts": [
            "Same-Sign Addition: When adding two integers with the same sign, add their absolute values and keep the common sign ($-8 + (-5) = -(8+5) = -13$).",
            "Different-Sign Addition: When adding two integers with opposite signs, subtract the smaller absolute value from the larger absolute value and keep the sign of the number with the larger absolute value ($-12 + 7 = -(12 - 7) = -5$).",
            "Additive Inverse Property: The sum of any integer and its opposite is zero: $a + (-a) = 0$."
        ],
        "equation": "a + (-a) = 0, \\qquad (-a) + (-b) = -(a + b)",
        "worked": "Example: Evaluate $x^2 + 3x + (-15)$ when $x = -4$.\n1. Substitute with parentheses: $(-4)^2 + 3(-4) + (-15)$.\n2. $(-4)^2 = 16$ and $3(-4) = -12$.\n3. $16 + (-12) + (-15) = 4 + (-15) = -11$.",
        "exercises": [
            "Simplify $-27 + 43 + (-19) + 12$ by grouping positive addends and negative addends first.",
            "Evaluate $(a + b)^2$ and $a^2 + b^2$ when $a = -5$ and $b = 2$."
        ],
        "recall": [
            ("How do you determine the sign and magnitude of $a + b$ when $a$ and $b$ have opposite signs?", "The sign matches whichever operand has the larger absolute value, and the magnitude is the difference between their absolute values ($||a| - |b||$)."),
            ("Why is wrapping negative numbers in parentheses essential when substituting into $x^2$?", "Because if $x = -4$, then $x^2 = (-4)^2 = (-4)(-4) = +16$, whereas writing $-4^2$ without parentheses means $-(4^2) = -16$.")
        ]
    },
    "MTH-T01-C03-U03": {
        "title": "Subtract Integers",
        "obj": "Rewrite integer subtraction as adding the opposite ($a - b = a + (-b)$), simplify expressions combining addition and subtraction, and solve applied difference problems.",
        "out": "Simplify multi-term integer addition and subtraction expressions without sign errors.",
        "prereq": "MTH-T01-C03-U02 (Add Integers)",
        "source": "OpenStax Prealgebra 2e — Section 3.3: Subtract Integers (Verified HTTP 200).",
        "concepts": [
            "Subtraction Property (Add the Opposite): Subtracting $b$ is identical to adding the opposite of $b$: $a - b = a + (-b)$, and $a - (-b) = a + b$.",
            "Unifying Sums & Differences: Any chain of additions and subtractions like $-7 - 4 - (-9) + 2$ can be viewed as a sum of signed terms: $(-7) + (-4) + (+9) + (+2)$.",
            "Net Distance / Change Formula: Change $= \\text{Final} - \\text{Initial}$ (e.g., temperature rising from $-14^\\circ\\text{C}$ to $8^\\circ\\text{C}$ is $8 - (-14) = 8 + 14 = +22^\\circ\\text{C}$)."
        ],
        "equation": "a - b = a + (-b), \\qquad a - (-b) = a + b",
        "worked": "Example: Simplify $-15 - (-23) - 11 - (-4)$.\n1. Rewrite subtractions as adding opposites: $-15 + 23 + (-11) + 4$.\n2. Combine positives and negatives: $(23 + 4) + (-15 + (-11)) = 27 + (-26) = 1$.",
        "exercises": [
            "Simplify $-32 - (-18) - 14 - (-25)$.",
            "Translate and simplify: 'Subtract $-19$ from the difference of $-8$ and $12$'."
        ],
        "recall": [
            ("Why does subtracting a negative number ($a - (-b)$) equal adding a positive number ($a + b$)?", "Because subtraction adds the additive inverse, and the additive inverse (opposite) of $-b$ is $+b$."),
            ("What is a common mistake when finding the elevation difference between a peak at $1,200\\text{ m}$ and a trench at $-350\\text{ m}$?", "Writing $1200 - 350 = 850$ instead of $1200 - (-350) = 1,550\\text{ m}$.")
        ]
    },
    "MTH-T01-C03-U04": {
        "title": "Multiply and Divide Integers",
        "obj": "Multiply and divide signed integers, evaluate powers of negative bases, and simplify combined order-of-operations expressions with integers.",
        "out": "Correctly evaluate expressions with negative bases, exponents, products, and quotients.",
        "prereq": "MTH-T01-C03-U03 (Subtract Integers)",
        "source": "OpenStax Prealgebra 2e — Section 3.4: Multiply and Divide Integers (Verified HTTP 200).",
        "concepts": [
            "Why $(-a)(-b) = +ab$: By the distributive property, $(-a)[b + (-b)] = (-a)(0) = 0$. Expanding the left side gives $(-a)(b) + (-a)(-b) = -ab + (-a)(-b) = 0$, which forces $(-a)(-b) = +ab$.",
            "Parity of Negative Factors: In a product or quotient of nonzero numbers, an EVEN number of negative signs produces a positive result; an ODD number of negative signs produces a negative result.",
            "Critical Distinction: $(-a)^n$ vs. $-a^n$: In $(-2)^4 = (-2)(-2)(-2)(-2) = +16$, the base is $-2$. In $-2^4 = -(2 \\cdot 2 \\cdot 2 \\cdot 2) = -16$, the exponent binds ONLY to $2$ before the unary negation is applied!"
        ],
        "equation": "(-a)(-b) = ab, \\qquad (-2)^4 = 16 \\ne -2^4 = -16",
        "worked": "Example: Simplify $-3^2 - 4(-5)(-2) + (-36) \\div (-9)$.\n1. Exponent first: $-3^2 = -(9) = -9$.\n2. Products/quotients left-to-right: $-4(-5)(-2) = +20(-2) = -40$, and $(-36) \\div (-9) = +4$.\n3. Combine: $-9 - 40 + 4 = -45$.",
        "exercises": [
            "Evaluate $(-5)^2$, $-5^2$, $(-2)^5$, and $-(-2)^4$.",
            "Simplify $\\frac{(-4)^3 - 2(-11)}{3(-5) + 8}$."
        ],
        "recall": [
            ("Why does $-4^2$ equal $-16$ while $(-4)^2$ equals $+16$?", "By the Order of Operations, exponentiation has higher precedence than unary negation. Without parentheses around $-4$, $-4^2$ means $-(4^2) = -16$."),
            ("Use the distributive property on $(-3)(5 + (-5)) = 0$ to prove that $(-3)(-5) = +15$.", "Since $5 + (-5) = 0$, $(-3)(5 + (-5)) = 0$. Distributing gives $(-3)(5) + (-3)(-5) = -15 + (-3)(-5) = 0$. Adding $15$ to both sides yields $(-3)(-5) = +15$.")
        ]
    },
    "MTH-T01-C03-U05": {
        "title": "Solve Equations Using Integers; The Division Property of Equality",
        "obj": "Solve one-step equations involving signed integers using the Addition, Subtraction, and Division Properties of Equality.",
        "out": "Translate and solve integer equations of the form $ax = b$ and $x + a = b$ with sign verification.",
        "prereq": "MTH-T01-C02-U03, MTH-T01-C03-U04",
        "source": "OpenStax Prealgebra 2e — Section 3.5: Solve Equations Using Integers; The Division Property of Equality (Verified HTTP 200).",
        "concepts": [
            "Division Property of Equality: For any real numbers $a, b, c$ with $c \\ne 0$, if $a = b$, then $\\frac{a}{c} = \\frac{b}{c}$.",
            "Dividing by the Exact Signed Coefficient: To solve $-9x = 63$, divide both sides by $-9$ (NOT $+9$), because $\\frac{-9}{-9} = +1$, isolating $+1x = x$.",
            "Handling $-x = k$: An equation like $-x = 14$ means $(-1)x = 14$; divide or multiply both sides by $-1$ to get $x = -14$."
        ],
        "equation": "ax = b \\ (a \\ne 0) \\implies \\frac{ax}{a} = \\frac{b}{a} \\implies x = \\frac{b}{a}",
        "worked": "Example: Solve $-12y = -108$ and $p - (-18) = -5$.\n1. For $-12y = -108$: divide both sides by $-12 \\implies y = \\frac{-108}{-12} = 9$. Check: $-12(9) = -108$.\n2. For $p - (-18) = -5$: simplify left side first to $p + 18 = -5$, then subtract $18 \\implies p = -23$.",
        "exercises": [
            "Solve and check: (a) $-16k = 144$, (b) $-x = -29$, (c) $w + (-24) = -61$.",
            "Translate into an equation and solve: 'The product of $-15$ and $n$ is $135$'."
        ],
        "recall": [
            ("When solving $-8x = -56$, why do we divide both sides by $-8$ instead of adding $8$?", "Because $-8$ is multiplied by $x$ ($-8 \\cdot x$), and the inverse operation of multiplication by $-8$ is division by $-8$."),
            ("What common mistake happens if a student divides $-7x = 42$ by $+7$ instead of $-7$?", "They are left with $-x = 6$ instead of $x = -6$, forgetting that the coefficient $-1$ is still attached to $x$.")
        ]
    },
    "MTH-T01-C04-U01": {
        "title": "Add and Subtract Mixed Numbers",
        "obj": "Convert between mixed numbers and improper fractions, and add and subtract mixed numbers with common and different denominators.",
        "out": "Add and subtract mixed numbers accurately using both improper-fraction conversion and whole/fraction regrouping.",
        "prereq": "MTH-T01-C02-U05 (Prime Factorization and LCM)",
        "source": "OpenStax Prealgebra 2e — Section 4.1 & 4.6: Visualize Fractions & Add and Subtract Mixed Numbers (Verified HTTP 200).",
        "concepts": [
            "Mixed Number as an Implicit Sum: A mixed number $W\\frac{a}{b}$ ($W > 0$) means $W + \\frac{a}{b} = \\frac{W \\cdot b + a}{b}$. For negative mixed numbers, $-W\\frac{a}{b} = -\\left(W + \\frac{a}{b}\\right) = -\\frac{W \\cdot b + a}{b}$.",
            "Two Reliable Methods for Mixed Number Addition/Subtraction: Method 1 (Universal & Sign-Safe): Convert all mixed numbers to improper fractions, find the LCD, add/subtract numerators, and simplify. Method 2 (Vertical Regrouping): Add/subtract whole parts and fractional parts separately, borrowing $1 = \\frac{d}{d}$ from the whole number when the top fraction is smaller in subtraction.",
            "Final Normalization: Ensure the fractional part of a mixed number is a proper fraction ($\\text{numerator} < \\text{denominator}$) in lowest terms."
        ],
        "equation": "W\\frac{a}{b} = \\frac{Wb + a}{b}, \\qquad 5\\frac{1}{4} - 2\\frac{3}{4} = 4\\frac{5}{4} - 2\\frac{3}{4} = 2\\frac{2}{4} = 2\\frac{1}{2}",
        "worked": "Example: Compute $6\\frac{1}{6} - 2\\frac{5}{8}$.\n1. LCD of $6$ and $8$ is $24$: rewrite as $6\\frac{4}{24} - 2\\frac{15}{24}$.\n2. Since $\\frac{4}{24} < \\frac{15}{24}$, borrow $1 = \\frac{24}{24}$ from $6$: $5\\frac{28}{24} - 2\\frac{15}{24}$.\n3. Subtract wholes and fractions: $(5 - 2) + \\frac{28 - 15}{24} = 3\\frac{13}{24}$.",
        "exercises": [
            "Compute $4\\frac{5}{6} + 3\\frac{7}{10}$ and express in simplest mixed-number form.",
            "Compute $8 - 3\\frac{5}{12}$ and $-4\\frac{2}{3} + 2\\frac{3}{4}$."
        ],
        "recall": [
            ("When converting a negative mixed number $-3\\frac{2}{5}$ to an improper fraction, why is the numerator $-17$ and not $-13$?", "Because $-3\\frac{2}{5}$ means $-\\left(3 + \\frac{2}{5}\\right) = -\\frac{3 \\cdot 5 + 2}{5} = -\\frac{17}{5}$, not $\\frac{(-3)(5) + 2}{5}$."),
            ("When borrowing $1$ from the whole number $7$ in $7\\frac{2}{9} - 4\\frac{5}{9}$, why does $7\\frac{2}{9}$ become $6\\frac{11}{9}$ and not $6\\frac{12}{9}$?", "Because $1$ whole equals $\\frac{9}{9}$ (not $\\frac{10}{9}$), and $\\frac{9}{9} + \\frac{2}{9} = \\frac{11}{9}$.")
        ]
    },
    "MTH-T01-C04-U02": {
        "title": "Add and Subtract Fractions with Common Denominators",
        "obj": "Add and subtract numerical and algebraic fractions that share a common denominator and simplify results to lowest terms.",
        "out": "Combine signed and variable fractions over a common denominator without altering the denominator.",
        "prereq": "MTH-T01-C03 (Integers)",
        "source": "OpenStax Prealgebra 2e — Section 4.4: Add and Subtract Fractions with Common Denominators (Verified HTTP 200).",
        "concepts": [
            "Common Denominator Rule: For $c \\ne 0$, $\\frac{a}{c} + \\frac{b}{c} = \\frac{a + b}{c}$ and $\\frac{a}{c} - \\frac{b}{c} = \\frac{a - b}{c}$. The denominator $c$ represents the unit size of the slices, so only numerators are combined.",
            "Placement of Negative Signs in Fractions: For $b \\ne 0$, $\\frac{-a}{b} = \\frac{a}{-b} = -\\frac{a}{b}$. Moving the negative sign to the numerator streamlines addition and subtraction.",
            "Always Reduce at the End: After combining numerators, factor numerator and denominator to cancel any common factors."
        ],
        "equation": "\\frac{a}{c} + \\frac{b}{c} = \\frac{a + b}{c}, \\qquad \\frac{a}{c} - \\frac{b}{c} = \\frac{a - b}{c} \\quad (c \\ne 0)",
        "worked": "Example: Simplify $\\frac{5x}{12} - \\frac{-7x}{12} - \\frac{3x}{12}$.\n1. Combine numerators over the common denominator $12$: $\\frac{5x - (-7x) - 3x}{12} = \\frac{9x}{12}$.\n2. Reduce by dividing numerator and denominator by $3$: $\\frac{3x}{4}$.",
        "exercises": [
            "Simplify $-\\frac{11}{18} + \\frac{5}{18} - \\frac{3}{18}$ to lowest terms.",
            "Simplify $\\frac{4y - 3}{10} - \\frac{y - 7}{10}$ (watch the distribution of the subtraction sign across $y - 7$!)."
        ],
        "recall": [
            ("Why is $\\frac{3}{8} + \\frac{1}{8} = \\frac{4}{8} = \\frac{1}{2}$ instead of $\\frac{4}{16}$?", "Adding eighths counts how many one-eighth pieces we have: $3(\\frac{1}{8}) + 1(\\frac{1}{8}) = (3+1)(\\frac{1}{8}) = \\frac{4}{8}$. Adding denominators would shrink the piece size."),
            ("What common error occurs when simplifying $\\frac{5x}{6} - \\frac{x - 2}{6}$?", "Writing $\\frac{5x - x - 2}{6}$ instead of distributing the minus sign across the entire second numerator: $\\frac{5x - (x - 2)}{6} = \\frac{4x + 2}{6} = \\frac{2x + 1}{3}$.")
        ]
    },
    "MTH-T01-C04-U03": {
        "title": "Add and Subtract Fractions with Different Denominators",
        "obj": "Find the Least Common Denominator (LCD), convert fractions to equivalent fractions with the LCD, and add or subtract fractions with unlike denominators.",
        "out": "Add and subtract multi-term fractions with different denominators using prime-factored LCDs.",
        "prereq": "MTH-T01-C02-U05 (LCM), MTH-T01-C04-U02 (Common Denominators)",
        "source": "OpenStax Prealgebra 2e — Section 4.5: Add and Subtract Fractions with Different Denominators (Verified HTTP 200).",
        "concepts": [
            "Finding the LCD: The Least Common Denominator (LCD) of $\\frac{a}{b}$ and $\\frac{c}{d}$ is $\\text{LCM}(b, d)$.",
            "Building Equivalent Fractions via Multiplication by 1: Multiply each fraction by the missing prime factors of the LCD in the form $\\frac{k}{k} = 1$ so all denominators match the LCD.",
            "Order of Operations: Never cancel factors between a numerator and denominator BEFORE adding or subtracting two separate fractions; combine into a single fraction over the LCD first, then simplify."
        ],
        "equation": "\\frac{a}{b} + \\frac{c}{d} = \\frac{a \\cdot (\\text{LCD}/b) + c \\cdot (\\text{LCD}/d)}{\\text{LCD}}",
        "worked": "Example: Compute $-\\frac{7}{18} + \\frac{5}{24}$.\n1. Prime factor denominators: $18 = 2 \\cdot 3^2$, $24 = 2^3 \\cdot 3 \\implies \\text{LCD} = 2^3 \\cdot 3^2 = 72$.\n2. Build equivalent fractions: $-\\frac{7 \\cdot 4}{18 \\cdot 4} + \\frac{5 \\cdot 3}{24 \\cdot 3} = \\frac{-28 + 15}{72} = -\\frac{13}{72}$.",
        "exercises": [
            "Compute $\\frac{11}{30} - \\frac{7}{45} + \\frac{1}{18}$ in lowest terms.",
            "Simplify $\\frac{x}{6} - \\frac{3x}{8}$ into a single fraction."
        ],
        "recall": [
            ("Why is multiplying by $\\frac{4}{4}$ to convert $\\frac{5}{6}$ into $\\frac{20}{24}$ mathematically valid?", "Because $\\frac{4}{4} = 1$, and by the Identity Property of Multiplication, multiplying any number by $1$ leaves its value unchanged."),
            ("What happens if you use the product of denominators $b \\cdot d$ instead of the $\\text{LCD} = \\text{LCM}(b, d)$?", "The math is still valid, but the intermediate numerators and denominator are unnecessarily large and require heavier factoring to reduce at the end.")
        ]
    },
    "MTH-T01-C04-U04": {
        "title": "Multiply and Divide Fractions",
        "obj": "Simplify fractions by canceling common factors, multiply fractions, find reciprocals, and divide fractions.",
        "out": "Multiply and divide signed numerical and variable fractions efficiently by pre-canceling common factors.",
        "prereq": "MTH-T01-C02-U05 (Prime Factorization), MTH-T01-C03-U04 (Multiply/Divide Integers)",
        "source": "OpenStax Prealgebra 2e — Section 4.2: Multiply and Divide Fractions (Verified HTTP 200).",
        "concepts": [
            "Fraction Multiplication & Pre-Canceling: $\\frac{a}{b} \\cdot \\frac{c}{d} = \\frac{ac}{bd}$ ($b, d \\ne 0$). You do NOT need a common denominator to multiply! Factor numerators and denominators and cancel common factors BEFORE multiplying to keep numbers small.",
            "Reciprocals (Multiplicative Inverses): Two numbers are reciprocals if their product is $1$. The reciprocal of $\\frac{a}{b}$ ($a, b \\ne 0$) is $\\frac{b}{a}$ (note: a reciprocal keeps the SAME sign; the reciprocal of $-\\frac{3}{4}$ is $-\\frac{4}{3}$).",
            "Fraction Division: To divide by a nonzero fraction, multiply by its reciprocal: $\\frac{a}{b} \\div \\frac{c}{d} = \\frac{a}{b} \\cdot \\frac{d}{c}$. Never cancel factors before flipping the divisor!"
        ],
        "equation": "\\frac{a}{b} \\cdot \\frac{c}{d} = \\frac{ac}{bd}, \\qquad \\frac{a}{b} \\div \\frac{c}{d} = \\frac{a}{b} \\cdot \\frac{d}{c} = \\frac{ad}{bc} \\quad (b, c, d \\ne 0)",
        "worked": "Example: Simplify $\\left(-\\frac{14x^2}{15y}\\right) \\div \\left(\\frac{21x}{25y^2}\\right)$.\n1. Rewrite division as multiplication by the reciprocal: $-\\frac{14x^2}{15y} \\cdot \\frac{25y^2}{21x}$.\n2. Cancel common factors ($7x$ from $14x^2$ and $21x$; $5y$ from $25y^2$ and $15y$): $-\\frac{2x}{3} \\cdot \\frac{5y}{3} = -\\frac{10xy}{9}$.",
        "exercises": [
            "Compute $\\left(-\\frac{18}{35}\\right) \\cdot \\left(-\\frac{49}{27}\\right)$ by canceling common factors before multiplying.",
            "Compute $\\left(-\\frac{16a}{21}\\right) \\div \\left(\\frac{24a}{35}\\right)$."
        ],
        "recall": [
            ("Why must you NEVER cancel factors across two fractions in $\\frac{a}{b} \\div \\frac{c}{d}$ until AFTER you rewrite it as $\\frac{a}{b} \\cdot \\frac{d}{c}$?", "Cancellation removes a factor from both numerator and denominator of a product. Before inverting the divisor, $c$ is still a numerator in the second fraction but acts as a denominator in the overall quotient."),
            ("What is the difference between the additive inverse (opposite) and the multiplicative inverse (reciprocal) of $-\\frac{2}{5}$?", "The additive inverse is $+\\frac{2}{5}$ (sum is $0$); the multiplicative inverse is $-\\frac{5}{2}$ (product is $+1$).")
        ]
    },
    "MTH-T01-C04-U05": {
        "title": "Multiply and Divide Mixed Numbers and Complex Fractions",
        "obj": "Multiply and divide mixed numbers by converting to improper fractions, and simplify complex fractions using both division and LCD multiplication.",
        "out": "Simplify multi-operation complex fractions and mixed-number products/quotients accurately.",
        "prereq": "MTH-T01-C04-U01 through MTH-T01-C04-U04",
        "source": "OpenStax Prealgebra 2e — Section 4.3: Multiply and Divide Mixed Numbers and Complex Fractions (Verified HTTP 200).",
        "concepts": [
            "Rule for Multiplying/Dividing Mixed Numbers: ALWAYS convert mixed numbers into improper fractions BEFORE multiplying or dividing. Note that $2\\frac{1}{2} \\times 3\\frac{1}{2} \\ne 6\\frac{1}{4}$ because $(2 + \\frac{1}{2})(3 + \\frac{1}{2})$ has four distributive cross-terms!",
            "Complex Fractions — Method 1 (Simplify Top & Bottom, Then Divide): Combine the numerator into a single fraction and the denominator into a single fraction, then rewrite the main fraction bar as $\\div$.",
            "Complex Fractions — Method 2 (Multiply Top & Bottom by Overall LCD): Multiply both the main numerator and main denominator by the LCD of all mini-fractions to clear all internal denominators in one step."
        ],
        "equation": "\\frac{\\frac{a}{b} + \\frac{c}{d}}{\\frac{e}{f} - \\frac{g}{h}} = \\frac{L \\cdot \\left(\\frac{a}{b} + \\frac{c}{d}\\right)}{L \\cdot \\left(\\frac{e}{f} - \\frac{g}{h}\\right)} \\quad \\text{where } L = \\text{LCM}(b, d, f, h)",
        "worked": "Example: Simplify $\\frac{\\frac{1}{2} + \\frac{2}{3}}{\\frac{3}{4} - \\frac{1}{6}}$.\n1. Overall LCD of $2, 3, 4, 6$ is $12$. Multiply top and bottom by $12$:\n2. $\\frac{12(\\frac{1}{2} + \\frac{2}{3})}{12(\\frac{3}{4} - \\frac{1}{6})} = \\frac{6 + 8}{9 - 2} = \\frac{14}{7} = 2$.",
        "exercises": [
            "Compute $\\left(-3\\frac{3}{4}\\right) \\div 2\\frac{1}{2}$ and express as a mixed number.",
            "Simplify the complex fraction $\\frac{2 - \\frac{3}{5}}{\\frac{7}{10} + \\frac{1}{2}}$ using both Method 1 and Method 2."
        ],
        "recall": [
            ("Why is $3\\frac{1}{2} \\times 2\\frac{1}{3}$ NOT equal to $(3 \\times 2) + (\\frac{1}{2} \\times \\frac{1}{3})$?", "Because $3\\frac{1}{2} = 3 + \\frac{1}{2}$ and $2\\frac{1}{3} = 2 + \\frac{1}{3}$; by the distributive property, multiplying two sums produces four products, not just two. Converting to improper fractions $\\frac{7}{2} \\times \\frac{7}{3} = \\frac{49}{6} = 8\\frac{1}{6}$ accounts for all terms."),
            ("Why is multiplying the numerator and denominator of a complex fraction by their overall LCD valid?", "Because multiplying top and bottom by the same nonzero number $L$ is multiplying the entire expression by $\\frac{L}{L} = 1$.")
        ]
    },
    "MTH-T01-C04-U06": {
        "title": "Solve Equations with Fractions",
        "obj": "Solve linear equations containing fractional constants and fractional coefficients using the Addition, Subtraction, Multiplication, and Reciprocal Properties of Equality.",
        "out": "Solve fractional linear equations cleanly by multiplying by reciprocals or clearing denominators with the LCD.",
        "prereq": "MTH-T01-C03-U05, MTH-T01-C04-U03, MTH-T01-C04-U04",
        "source": "OpenStax Prealgebra 2e — Section 4.7: Solve Equations with Fractions (Verified HTTP 200).",
        "concepts": [
            "Multiplication Property of Equality & Reciprocals: When an equation has the form $\\frac{a}{b}x = c$, multiply both sides by the reciprocal $\\frac{b}{a}$ so that $\\left(\\frac{b}{a}\\right)\\left(\\frac{a}{b}\\right)x = 1x = x$.",
            "Clearing Denominators via the LCD: For equations with multiple fraction terms like $x - \\frac{3}{8} = -\\frac{5}{6}$, you can either combine fractions over the LCD OR multiply every term on both sides by $\\text{LCD}(8, 6) = 24$ to convert it into an integer equation immediately.",
            "Substituting Fractions to Verify: Always check the solution in the original fractional equation before simplifying."
        ],
        "equation": "\\frac{a}{b}x = c \\implies x = \\frac{b}{a} \\cdot c",
        "worked": "Example: Solve $-\\frac{5}{8}x = \\frac{15}{16}$.\n1. Multiply both sides by the reciprocal of $-\\frac{5}{8}$, which is $-\\frac{8}{5}$:\n2. $\\left(-\\frac{8}{5}\\right)\\left(-\\frac{5}{8}x\\right) = \\left(-\\frac{8}{5}\\right)\\left(\\frac{15}{16}\\right)$.\n3. Cancel common factors ($8$ and $16$; $5$ and $15$): $x = -\\frac{3}{2}$.",
        "exercises": [
            "Solve and check: (a) $y - \\frac{5}{12} = -\\frac{3}{8}$, (b) $-\\frac{9}{14}m = -\\frac{27}{35}$.",
            "Solve $\\frac{3}{4}x + \\frac{1}{6} = \\frac{11}{12}$."
        ],
        "recall": [
            ("Why is multiplying both sides of $-\\frac{3}{7}x = 12$ by $-\\frac{7}{3}$ faster and less error-prone than dividing both sides by $-\\frac{3}{7}$?", "Dividing by a fraction creates a complex fraction that you have to rewrite as multiplication by the reciprocal anyway; multiplying directly by $-\\frac{7}{3}$ isolates $x$ in a single step."),
            ("What is the difference between using the LCD to simplify an expression $\\frac{x}{2} + \\frac{x}{3}$ versus solving an equation $\\frac{x}{2} + \\frac{x}{3} = 5$?", "An expression has no equals sign, so you must keep the denominator $\\frac{5x}{6}$. An equation allows multiplying both sides by $6$ to clear the denominator completely: $3x + 2x = 30$.")
        ]
    }
}
