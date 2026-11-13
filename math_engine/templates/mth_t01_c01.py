# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C01: Whole Numbers."""

from math_engine.templates._prealg_helpers import S

UNIT = "MTH-T01-C01"
TITLE = "Whole Numbers"

MISTAKE_TAGS = [
    {
        "id": "c01-place-value-shift",
        "label": "Shifted place value column when adding or subtracting",
        "name": "Place Value Alignment Error",
        "description": "Misaligns multi-digit columns across addition or subtraction operations.",
        "autoFrom": [],
    },
    {
        "id": "c01-subtraction-sign-flip",
        "label": "Added instead of subtracting the final quantity: a + b + c instead of a + b - c",
        "name": "Subtraction Sign Flip",
        "description": "Flips a subtraction into addition when chaining multiple arithmetic operations.",
        "autoFrom": ["whole_sign_flip"],
    },
    {
        "id": "c01-division-remainder-drop",
        "label": "Omitted remainder in Euclidean division N = q*d + r",
        "name": "Euclidean Remainder Omission",
        "description": "Drops or forgets the non-zero remainder when reconstructing the dividend in Euclidean division.",
        "autoFrom": [],
    },
    {
        "id": "c01-remainder-addition-slip",
        "label": "Added remainder to dividend instead of subtracting: (N + r) // q instead of (N - r)/q",
        "name": "Remainder Addition Slip",
        "description": "Mistakenly adds remainder to dividend instead of subtracting before dividing to isolate divisor: (N + r) // q.",
        "autoFrom": [],
    },
    {
        "id": "c01-ceiling-rounding-trap",
        "label": "Rounded down instead of up when full containers are required",
        "name": "Container Ceiling Rounding Trap",
        "description": "Truncates or rounds down to integer quotient when practical packaging requires ceiling rounding.",
        "autoFrom": [],
    },
    {
        "id": "c01-remainder-shortfall-confusion",
        "label": "Reported leftover remainder instead of shortfall needed to fill container",
        "name": "Remainder Shortfall Confusion",
        "description": "Reports leftover remainder rather than the remaining shortfall required to complete the final container.",
        "autoFrom": [],
    },
    {
        "id": "c01-order-of-operations-trap",
        "label": "Added before multiplying in multi-unit budget calculation",
        "name": "Whole Number Precedence Trap",
        "description": "Performs addition before multiplication in multi-item budget and pricing calculations.",
        "autoFrom": [],
    },
    {
        "id": "c01-voucher-omission-trap",
        "label": "Omitted voucher or rebate discount before dividing installment costs",
        "name": "Voucher Discount Omission",
        "description": "Forgets to subtract voucher discount from total before dividing into installment shares.",
        "autoFrom": [],
    },
    {
        "id": "c01-fee-omission-trap",
        "label": "Omitted flat shipping fee before dividing net budget",
        "name": "Shipping Fee Omission",
        "description": "Forgets to add mandatory flat fee to total before allocating per-share costs.",
        "autoFrom": [],
    },
]


def t_c01_foundation(rng, form=None):
    if form not in ("direct", "contextual"):
        form = rng.choice(["direct", "contextual"])
    a = rng.randint(120, 480)
    b = rng.randint(110, 390)
    c = rng.randint(45, 95)
    ans = a + b - c
    trap = a + b + c
    trap_deriv = f"{a} + {b} + {c}"
    trap_tag = "c01-subtraction-sign-flip"
    if form == "contextual":
        prompt = f"A warehouse initially holds ${a}$ crates. It receives a shipment of ${b}$ crates and later dispatches ${c}$ crates. How many crates remain in the warehouse?"
        disp = f"{a} + {b} - {c}"
    else:
        prompt = f"Evaluate the whole-number expression ${a} + {b} - {c}$."
        disp = f"N = {a} + {b} - {c}"
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Whole Numbers: Multi-Step Addition and Subtraction",
        "references": ["MTH-T01-C01-U02"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{a} + {b} - {c}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Add the first two whole numbers, then subtract the third quantity from that sum.",
        "commonTrapTag": trap_tag,
        "trapDerivation": trap_deriv,
        "trapGivens": [a, b, c],
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(f"S = {a} + {b} = {a + b}", "Add the first two whole numbers.", eq=[f"{a} + {b}", str(a + b)]),
            S(f"N = {a + b} - {c}", "Set up the subtraction of the third quantity.", eq=[f"{a + b} - {c}", str(ans)]),
            S(
                f"N = {ans}",
                "Complete the subtraction to find the final whole number.",
                val=str(ans),
                eq=[str(ans), str(ans)],
            ),
        ],
    }


def t_c01_reverse(rng, form=None):
    if form not in ("direct", "reverse"):
        form = rng.choice(["direct", "reverse"])
    while True:
        d = rng.randint(12, 28)
        q = rng.choice([14, 16, 18, 20, 22, 24, 26, 28, 30, 32])
        if d == q:
            continue
        candidates = [rem for rem in range(3, d - 1) if (2 * rem) % q == 0]
        if candidates:
            r = rng.choice(candidates)
            break
    N = d * q + r
    if form == "reverse":
        ans = d
        trap = (N + r) // q
        trap_deriv = f"({N} + {r}) // {q}"
        trap_givens = [N, r, q]
        trap_tag = "c01-remainder-addition-slip"
        prompt = f"When the whole number ${N}$ is divided by a positive divisor $d$, the quotient is ${q}$ and the remainder is ${r}$. Find the divisor $d$."
        disp = f"{N} = {q}d + {r} \\implies d = ?"
        steps = [
            S(
                f"{q}d = {N} - {r} = {N - r}",
                "Subtract the remainder from the dividend.",
                eq=[f"{N} - {r}", str(N - r)],
            ),
            S(
                f"d = \\frac{{{N - r}}}{{{q}}}",
                "Divide by the quotient to isolate the divisor.",
                eq=[f"({N - r}) / {q}", str(d)],
            ),
            S(
                f"d = {d}",
                "Verify that the remainder is strictly less than the divisor.",
                val=str(d),
                eq=[str(d), str(d)],
            ),
        ]
    else:
        ans = N
        trap = d * q
        trap_deriv = f"{d} * {q}"
        trap_givens = [d, q]
        trap_tag = "c01-division-remainder-drop"
        prompt = (
            f"When a whole number $N$ is divided by ${d}$, the quotient is ${q}$ and the remainder is ${r}$. Find $N$."
        )
        disp = f"N = {d} \\times {q} + {r}"
        steps = [
            S(f"P = {d} \\times {q} = {d * q}", "Multiply the divisor by the quotient.", eq=[f"{d} * {q}", str(d * q)]),
            S(f"N = {d * q} + {r}", "Add the remainder to the product.", eq=[f"{d * q} + {r}", str(N)]),
            S(f"N = {N}", "Combine to obtain the dividend.", val=str(N), eq=[str(N), str(N)]),
        ]
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Whole Numbers: Euclidean Division Algorithm",
        "references": ["MTH-T01-C01-U05"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{d} * {q} + {r}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Use the division algorithm identity connecting dividend, divisor, quotient, and remainder.",
        "commonTrapTag": trap_tag,
        "trapDerivation": trap_deriv,
        "trapGivens": trap_givens,
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c01_trap(rng, form=None):
    if form not in ("direct", "edge-case"):
        form = rng.choice(["direct", "edge-case"])
    cap = rng.choice([12, 15, 18, 24, 30, 36])
    full_boxes = rng.randint(11, 29)
    while True:
        leftover = rng.randint(2, cap - 2)
        if leftover * 2 != cap:
            break
    total = cap * full_boxes + leftover
    if form == "edge-case":
        ans = cap - leftover
        trap = leftover
        trap_deriv = f"{total} - {cap} * ({total} // {cap})"
        trap_tag = "c01-remainder-shortfall-confusion"
        prompt = f"A factory produces ${total}$ sensors to be packed into crates that hold exactly ${cap}$ sensors each. How many additional sensors must be produced so that the last partially filled crate becomes completely full?"
        disp = f"\\text{{Total}} = {total},\\ \\text{{Capacity}} = {cap} \\implies \\text{{Additional Needed}} = ?"
        steps = [
            S(
                f"{total} = {cap} \\times {full_boxes} + {leftover}",
                "Divide total items by crate capacity to find the remainder in the last crate.",
                eq=[f"{total} - {cap}*{full_boxes}", str(leftover)],
            ),
            S(
                f"\\text{{Shortfall}} = {cap} - {leftover}",
                "Subtract the remainder from the crate capacity.",
                eq=[f"{cap} - {leftover}", str(ans)],
            ),
            S(
                f"\\text{{Additional Needed}} = {ans}",
                "State the exact number of items needed to complete the final crate.",
                val=str(ans),
                eq=[str(ans), str(ans)],
            ),
        ]
    else:
        ans = full_boxes + 1
        trap = full_boxes
        trap_deriv = f"{total} // {cap}"
        trap_tag = "c01-ceiling-rounding-trap"
        prompt = f"An expedition group of ${total}$ researchers needs transport vans that each hold at most ${cap}$ passengers. What is the minimum whole number of vans required to transport everyone at once?"
        disp = f"\\left\\lceil \\frac{{{total}}}{{{cap}}} \\right\\rceil = ?"
        steps = [
            S(
                f"{total} \\div {cap} = {full_boxes}\\text{{ R }}{leftover}",
                "Perform whole-number division to find full vans and remaining passengers.",
                eq=[f"{cap} * {full_boxes} + {leftover}", str(total)],
            ),
            S(
                f"N_{{\\text{{vans}}}} = {full_boxes} + 1",
                "Because remaining passengers cannot be left behind, one additional van is required.",
                eq=[f"{full_boxes} + 1", str(ans)],
            ),
            S(
                f"N_{{\\text{{vans}}}} = {ans}",
                "Conclude the minimum whole number of vans.",
                val=str(ans),
                eq=[str(ans), str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Whole Numbers: Remainder Interpretation Trap",
        "references": ["MTH-T01-C01-U05"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"ceil({total} / {cap})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Divide the total quantity by the unit capacity and carefully interpret the non-zero remainder in context.",
        "commonTrapTag": trap_tag,
        "trapDerivation": trap_deriv,
        "trapGivens": [total, cap],
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c01_synthesis(rng, form=None):
    if form not in ("direct", "multi-constraint"):
        form = rng.choice(["direct", "multi-constraint"])
    k_share = rng.choice([4, 5, 6, 8])
    rebate = k_share * rng.randint(2, 6)
    while True:
        n_a = rng.randint(6, 14)
        p_a = rng.randint(25, 55)
        n_b = rng.randint(5, 12)
        p_b = rng.randint(30, 60)
        sub_total = n_a * p_a + n_b * p_b
        if sub_total % k_share == 0:
            break
    net_cost = sub_total - rebate
    ans = net_cost // k_share
    trap = sub_total // k_share
    if form == "multi-constraint":
        bonus_fee = k_share * rng.randint(3, 9)
        ans = (net_cost + bonus_fee) // k_share
        trap = net_cost // k_share
        trap_deriv = f"({n_a} * {p_a} + {n_b} * {p_b} - {rebate}) // {k_share}"
        trap_tag = "c01-fee-omission-trap"
        trap_givens = [n_a, p_a, n_b, p_b, rebate, bonus_fee, k_share]
        prompt = f"A lab orders ${n_a}$ kits at ${p_a}$ dollars each and ${n_b}$ modules at ${p_b}$ dollars each. After receiving a bulk rebate of ${rebate}$ dollars and paying a flat shipping fee of ${bonus_fee}$ dollars, the total net cost is split equally among ${k_share}$ departments. How much does each department pay?"
        disp = f"\\frac{{({n_a} \\times {p_a} + {n_b} \\times {p_b} - {rebate} + {bonus_fee})}}{{{k_share}}}"
        steps = [
            S(
                f"C_{{\\text{{items}}}} = {n_a} \\times {p_a} + {n_b} \\times {p_b} = {sub_total}",
                "Calculate the combined item cost before adjustments.",
                eq=[f"{n_a}*{p_a} + {n_b}*{p_b}", str(sub_total)],
            ),
            S(
                f"C_{{\\text{{net}}}} = {sub_total} - {rebate} + {bonus_fee} = {net_cost + bonus_fee}",
                "Subtract the rebate and add the shipping fee.",
                eq=[f"{sub_total} - {rebate} + {bonus_fee}", str(net_cost + bonus_fee)],
            ),
            S(
                f"\\text{{Share}} = \\frac{{{net_cost + bonus_fee}}}{{{k_share}}} = {ans}",
                "Divide equally among all participating departments.",
                val=str(ans),
                eq=[f"({net_cost + bonus_fee}) / {k_share}", str(ans)],
            ),
        ]
    else:
        trap_deriv = f"({n_a} * {p_a} + {n_b} * {p_b}) // {k_share}"
        trap_tag = "c01-voucher-omission-trap"
        trap_givens = [n_a, p_a, n_b, p_b, rebate, k_share]
        prompt = f"A school purchases ${n_a}$ workbooks at ${p_a}$ dollars each and ${n_b}$ lab packs at ${p_b}$ dollars each, then applies a voucher worth ${rebate}$ dollars. If the remaining balance is divided equally into ${k_share}$ monthly installments, what is the dollar amount of each installment?"
        disp = f"\\frac{{({n_a} \\times {p_a} + {n_b} \\times {p_b} - {rebate})}}{{{k_share}}}"
        steps = [
            S(
                f"C_{{\\text{{gross}}}} = {n_a} \\times {p_a} + {n_b} \\times {p_b} = {sub_total}",
                "Multiply quantity by unit price for each item and sum.",
                eq=[f"{n_a}*{p_a} + {n_b}*{p_b}", str(sub_total)],
            ),
            S(
                f"C_{{\\text{{net}}}} = {sub_total} - {rebate} = {net_cost}",
                "Subtract the voucher amount from the gross total.",
                eq=[f"{sub_total} - {rebate}", str(net_cost)],
            ),
            S(
                f"\\text{{Installment}} = \\frac{{{net_cost}}}{{{k_share}}} = {ans}",
                "Divide the net balance equally across the installments.",
                val=str(ans),
                eq=[f"{net_cost} / {k_share}", str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Whole Numbers: Multi-Constraint Budget Allocation",
        "references": ["MTH-T01-C01-U04", "MTH-T01-C01-U05"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"({n_a}*{p_a} + {n_b}*{p_b} - {rebate}) / {k_share}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Compute the products first, apply the additive adjustments to get the net total, and finally divide by the number of equal shares.",
        "commonTrapTag": trap_tag,
        "trapDerivation": trap_deriv,
        "trapGivens": trap_givens,
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


TEMPLATES = [
    {
        "key": "c01-place-value-rounding",
        "trapTag": "c01-subtraction-sign-flip",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C01-ADD-SUB", "trapTag": "c01-subtraction-sign-flip"},
            "contextual": {"level": 1, "skill": "MTH-PREALG-C01-ADD-SUB", "trapTag": "c01-subtraction-sign-flip"},
        },
        "build": t_c01_foundation,
    },
    {
        "key": "c01-multiply-divide-whole",
        "trapTag": "c01-division-remainder-drop",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C01-EUCLIDEAN-DIV", "trapTag": "c01-division-remainder-drop"},
            "reverse": {"level": 2, "skill": "MTH-PREALG-C01-EUCLIDEAN-DIV", "trapTag": "c01-remainder-addition-slip"},
        },
        "build": t_c01_reverse,
    },
    {
        "key": "c01-division-remainder-trap",
        "trapTag": "c01-ceiling-rounding-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C01-REMAINDER-TRAP", "trapTag": "c01-ceiling-rounding-trap"},
            "edge-case": {
                "level": 3,
                "skill": "MTH-PREALG-C01-REMAINDER-TRAP",
                "trapTag": "c01-remainder-shortfall-confusion",
            },
        },
        "build": t_c01_trap,
    },
    {
        "key": "c01-multi-unit-budget-synthesis",
        "trapTag": "c01-voucher-omission-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C01-SYNTHESIS", "trapTag": "c01-voucher-omission-trap"},
            "multi-constraint": {"level": 4, "skill": "MTH-PREALG-C01-SYNTHESIS", "trapTag": "c01-fee-omission-trap"},
        },
        "build": t_c01_synthesis,
    },
]
