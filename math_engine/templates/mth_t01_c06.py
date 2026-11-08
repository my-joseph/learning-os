# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C06: Percents."""
from math_engine.templates._prealg_helpers import S

UNIT = "MTH-T01-C06"
TITLE = "Percents"

MISTAKE_TAGS = [
    {"id": "c06-percent-decimal-conversion", "label": "Failed to divide by 100 when converting percent to decimal or fraction", "name": "Percent to Decimal Conversion Error", "autoFrom": ["off_by_factor"]},
    {"id": "c06-reverse-discount-base-trap", "label": "Applied discount percentage to the discounted sale price instead of original price", "name": "Reverse Discount Base Trap", "autoFrom": []},
    {"id": "c06-successive-percent-linear-add", "label": "Added successive percentage changes linearly instead of compounding multipliers", "name": "Successive Percent Linear Addition Trap", "autoFrom": []},
    {"id": "c06-simple-interest-split-trap", "label": "Swapped interest rates between split investment principals", "name": "Split Principal Interest Rate Swap", "autoFrom": []},
]



def t_c06_foundation(rng, form=None):
    if form not in ("direct", "find-rate"):
        form = rng.choice(["direct", "find-rate"])
    cases = [
        (15, 240, 36),
        (25, 320, 80),
        (35, 180, 63),
        (45, 260, 117),
        (20, 450, 90),
        (30, 350, 105),
    ]
    pct, base, part = rng.choice(cases)
    if form == "find-rate":
        ans = pct
        trap = part
        prompt = f"What percent of ${base}$ is ${part}$? (Enter the number without the $\\%$ symbol.)"
        disp = f"\\frac{{{part}}}{{{base}}} \\times 100 = ?"
        steps = [
            S(f"r = \\frac{{\\text{{part}}}}{{\\text{{base}}}} = \\frac{{{part}}}{{{base}}}", "Set up the ratio of the part to the base.", eq=[f"({part} * 100) / {base}", str(ans)]),
            S(f"p = \\frac{{{part} \\times 100}}{{{base}}}", "Multiply the ratio by 100 to convert to a percentage.", eq=[f"({part} * 100) / {base}", str(ans)]),
            S(f"p = {ans}", "Simplify the quotient to obtain the percentage rate.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        ans = part
        trap = base - part
        prompt = f"Find ${pct}\\%$ of ${base}$."
        disp = f"\\frac{{{pct}}}{{100}} \\times {base}"
        steps = [
            S(f"{pct}\\% = \\frac{{{pct}}}{{100}}", "Write the percentage as a fraction over 100.", eq=[f"{pct} / 100", f"{pct}/100"]),
            S(f"\\text{{Part}} = \\frac{{{pct} \\times {base}}}{{100}} = \\frac{{{pct * base}}}{{100}}", "Multiply the base by the percentage numerator.", eq=[f"({pct} * {base}) / 100", str(ans)]),
            S(f"= {ans}", "Divide by 100 to obtain the exact value.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Percents: Base, Rate, and Part",
        "references": ["MTH-T01-C06-U02"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{pct}% of {base} = {part}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Use the fundamental percent relation Part = (Percent / 100) * Base.",
        "commonTrapTag": "c06-percent-decimal-conversion",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c06_reverse(rng, form=None):
    if form not in ("direct", "reverse-base"):
        form = rng.choice(["direct", "reverse-base"])
    cases = [
        (20, 250, 200, 240),
        (25, 360, 270, 337),
        (15, 400, 340, 391),
        (30, 500, 350, 455),
        (40, 300, 180, 252),
    ]
    disc_pct, orig, sale, trap_orig = rng.choice(cases)
    keep_pct = 100 - disc_pct
    if form == "reverse-base":
        ans = orig
        trap = trap_orig
        prompt = f"After a ${disc_pct}\\%$ discount, a monitor is sold for ${sale}$ dollars. What was the original list price in dollars before the discount?"
        disp = f"\\left(1 - \\frac{{{disc_pct}}}{{100}}\\right) P = {sale} \\implies P = ?"
        steps = [
            S(f"100\\% - {disc_pct}\\% = {keep_pct}\\% = \\frac{{{keep_pct}}}{{100}}", "Find the percentage of the original price that the customer pays.", eq=[f"100 - {disc_pct}", str(keep_pct)]),
            S(f"\\frac{{{keep_pct}}}{{100}} P = {sale} \\implies P = \\frac{{{sale} \\times 100}}{{{keep_pct}}}", "Divide the sale price by the retention rate.", eq=[f"({sale} * 100) / {keep_pct}", str(ans)]),
            S(f"P = {ans}", "Simplify to obtain the original list price.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        ans = sale
        trap = orig - disc_pct
        prompt = f"An item with an original list price of ${orig}$ dollars is discounted by ${disc_pct}\\%$. Find the sale price in dollars."
        disp = f"S = {orig} \\times \\left(1 - \\frac{{{disc_pct}}}{{100}}\\right)"
        steps = [
            S(f"\\text{{Discount}} = \\frac{{{disc_pct}}}{{100}} \\times {orig} = {orig - sale}", "Compute the dollar amount of the discount.", eq=[f"({disc_pct} * {orig}) / 100", str(orig - sale)]),
            S(f"S = {orig} - {orig - sale}", "Subtract the discount from the original list price.", eq=[f"{orig} - ({orig - sale})", str(ans)]),
            S(f"S = {ans}", "State the final sale price.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Percents: Discount & Original Price Recovery",
        "references": ["MTH-T01-C06-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{orig} * (100 - {disc_pct}) / 100 = {sale}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Express the sale price as (100 - discount)% of the original price, then solve for the unknown quantity.",
        "commonTrapTag": "c06-reverse-discount-base-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c06_trap(rng, form=None):
    if form not in ("direct", "markup-discount"):
        form = rng.choice(["direct", "markup-discount"])
    cases = [
        (200, 20, 20, 240, 192),
        (300, 30, 30, 390, 273),
        (500, 20, 10, 600, 540),
        (400, 25, 20, 500, 400),
        (250, 40, 20, 350, 280),
    ]
    base, up_pct, down_pct, mid_val, final_val = rng.choice(cases)
    naive_trap = int(base * (100 + up_pct - down_pct) // 100)
    if naive_trap == final_val:
        naive_trap = final_val + 15
    if form == "markup-discount":
        ans = final_val
        trap = naive_trap
        prompt = f"A wholesale item costs ${base}$ dollars. The store marks the price up by ${up_pct}\\%$, and later applies a clearance discount of ${down_pct}\\%$ off the marked-up price. What is the final clearance price in dollars?"
        disp = f"{base} \\times \\left(1 + \\frac{{{up_pct}}}{{100}}\\right)\\left(1 - \\frac{{{down_pct}}}{{100}}\\right)"
    else:
        ans = final_val
        trap = naive_trap
        prompt = f"A portfolio valued at ${base}$ dollars increases by ${up_pct}\\%$ in Quarter 1 and then decreases by ${down_pct}\\%$ in Quarter 2. Find the value of the portfolio in dollars at the end of Quarter 2."
        disp = f"V = {base} \\times \\frac{{{100 + up_pct}}}{{100}} \\times \\frac{{{100 - down_pct}}}{{100}}"
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Percents: Successive Percent Multiplier Trap",
        "references": ["MTH-T01-C06-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{base} * ({100 + up_pct}/100) * ({100 - down_pct}/100)",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Apply the first percentage change to find the intermediate value, then apply the second percentage change to that intermediate value.",
        "commonTrapTag": "c06-successive-percent-linear-add",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(f"V_1 = {base} \\times \\frac{{{100 + up_pct}}}{{100}} = {mid_val}", "Compute the intermediate value after the percentage increase.", eq=[f"({base} * ({100 + up_pct})) / 100", str(mid_val)]),
            S(f"V_2 = {mid_val} \\times \\frac{{{100 - down_pct}}}{{100}}", "Apply the percentage decrease multiplier to the intermediate value.", eq=[f"({mid_val} * ({100 - down_pct})) / 100", str(ans)]),
            S(f"V_2 = {ans}", "Evaluate the product to find the final value.", val=str(ans), eq=[str(ans), str(ans)]),
        ],
    }


def t_c06_synthesis(rng, form=None):
    if form not in ("direct", "contextual"):
        form = rng.choice(["direct", "contextual"])
    cases = [
        (5000, 2000, 3000, 4, 7, 80, 210, 290, 310),
        (6000, 2500, 3500, 4, 6, 100, 210, 310, 290),
        (8000, 3000, 5000, 5, 8, 150, 400, 550, 490),
        (4000, 1500, 2500, 4, 8, 60, 200, 260, 220),
        (7000, 3000, 4000, 3, 6, 90, 240, 330, 300),
    ]
    tot_p, p1, p2, r1, r2, i1, i2, tot_i, trap_i = rng.choice(cases)
    if form == "contextual":
        ans = p2
        trap = p1
        prompt = f"An investor splits ${tot_p}$ dollars between Bond A paying ${r1}\\%$ annual simple interest and Bond B paying ${r2}\\%$ annual simple interest. After 1 year, the combined interest earned is ${tot_i}$ dollars. How many dollars were invested in Bond B?"
        disp = f"\\frac{{{r1}}}{{100}}({tot_p} - x) + \\frac{{{r2}}}{{100}}x = {tot_i}"
        steps = [
            S(f"{r1}({tot_p} - x) + {r2}x = {tot_i * 100}", "Multiply the annual simple interest equation by 100 to clear denominators.", eq=[f"{r1}*({tot_p} - {p2}) + {r2}*{p2}", str(tot_i * 100)]),
            S(f"{r1 * tot_p} + {r2 - r1}x = {tot_i * 100} \\implies {r2 - r1}x = {tot_i * 100 - r1 * tot_p}", "Expand and isolate the variable term.", eq=[f"{tot_i * 100} - {r1 * tot_p}", str((r2 - r1) * p2)]),
            S(f"x = \\frac{{{tot_i * 100 - r1 * tot_p}}}{{{r2 - r1}}} = {ans}", "Divide to find the principal invested in Bond B.", val=str(ans), eq=[f"({tot_i * 100 - r1 * tot_p}) / ({r2 - r1})", str(ans)]),
        ]
    else:
        ans = tot_i
        trap = trap_i
        prompt = f"An endowment invests ${p1}$ dollars at ${r1}\\%$ annual simple interest and ${p2}$ dollars at ${r2}\\%$ annual simple interest. Find the total simple interest in dollars earned after 1 year."
        disp = f"I = \\frac{{{r1}}}{{100}}({p1}) + \\frac{{{r2}}}{{100}}({p2})"
        steps = [
            S(f"I_1 = \\frac{{{r1}}}{{100}} \\times {p1} = {i1}", "Calculate the annual simple interest from the first account.", eq=[f"({r1} * {p1}) / 100", str(i1)]),
            S(f"I_2 = \\frac{{{r2}}}{{100}} \\times {p2} = {i2}", "Calculate the annual simple interest from the second account.", eq=[f"({r2} * {p2}) / 100", str(i2)]),
            S(f"I_{{\\text{{total}}}} = {i1} + {i2} = {ans}", "Add both interest amounts together.", val=str(ans), eq=[f"{i1} + {i2}", str(ans)]),
        ]
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Percents: Split Principal Simple Interest Synthesis",
        "references": ["MTH-T01-C06-U02", "MTH-T01-C06-U04"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"({r1}*{p1} + {r2}*{p2}) / 100 = {tot_i}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Express the simple interest from each portion as Principal * Rate * Time and equate their sum to total interest.",
        "commonTrapTag": "c06-simple-interest-split-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


TEMPLATES = [
    {
        "key": "c06-percent-of-base",
        "trapTag": "c06-percent-decimal-conversion",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C06-PERCENT-BASE"},
            "find-rate": {"level": 1, "skill": "MTH-PREALG-C06-PERCENT-BASE"},
        },
        "build": t_c06_foundation,
    },
    {
        "key": "c06-discount-tax-interest",
        "trapTag": "c06-reverse-discount-base-trap",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C06-DISCOUNT"},
            "reverse-base": {"level": 2, "skill": "MTH-PREALG-C06-DISCOUNT"},
        },
        "build": t_c06_reverse,
    },
    {
        "key": "c06-successive-percent-trap",
        "trapTag": "c06-successive-percent-linear-add",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C06-SUCCESSIVE-TRAP"},
            "markup-discount": {"level": 3, "skill": "MTH-PREALG-C06-SUCCESSIVE-TRAP"},
        },
        "build": t_c06_trap,
    },
    {
        "key": "c06-investment-commission-synthesis",
        "trapTag": "c06-simple-interest-split-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C06-SYNTHESIS"},
            "contextual": {"level": 4, "skill": "MTH-PREALG-C06-SYNTHESIS"},
        },
        "build": t_c06_synthesis,
    },
]
