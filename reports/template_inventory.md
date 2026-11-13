# Template Inventory: MTH-T01 (61 Templates)

This report catalogs all 61 parameterized math problem templates across chapters C01 through C14 in `MTH-T01`.
It details each template's key, declared forms, associated trap tags, target difficulty levels, skills,
pedagogical problem directions (`forward`, `reverse`, `context`, `variant`), and compliance analysis.

## 1. Summary Statistics by Pedagogical Direction

| Direction | Count | Percentage | Pedagogical Description |
| :--- | :--- | :--- | :--- |
| `forward` | 62 | 49.2% | Direct standard computation from given inputs/equations to the unknown result |
| `reverse` | 9 | 7.1% | Backwards reasoning (given output/result or inverted condition, solve for input parameter) |
| `context` | 6 | 4.8% | Applied narrative, situational word problem, or multi-step real-world constraints |
| `variant` | 49 | 38.9% | Algebraic sign variation, grouping structure, or input representation change (e.g. diameter instead of radius) |
| **Total Forms** | **126** | **100.0%** | Across 61 templates |

## 2. Complete Template & Form Inventory

| Chapter | Template Key | Form | Level | Direction | Skill Code | Primary Trap Tag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| MTH-T01-C01 | `c01-place-value-rounding` | `direct` | L1 | **forward** | `MTH-PREALG-C01-ADD-SUB` | `c01-place-value-shift` |
| MTH-T01-C01 | `c01-place-value-rounding` | `contextual` | L1 | **context** | `MTH-PREALG-C01-ADD-SUB` | `c01-place-value-shift` |
| MTH-T01-C01 | `c01-multiply-divide-whole` | `direct` | L2 | **forward** | `MTH-PREALG-C01-EUCLIDEAN-DIV` | `c01-division-remainder-drop` |
| MTH-T01-C01 | `c01-multiply-divide-whole` | `reverse` | L2 | **reverse** | `MTH-PREALG-C01-EUCLIDEAN-DIV` | `c01-division-remainder-drop` |
| MTH-T01-C01 | `c01-division-remainder-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C01-REMAINDER-TRAP` | `c01-ceiling-rounding-trap` |
| MTH-T01-C01 | `c01-division-remainder-trap` | `edge-case` | L3 | **variant** | `MTH-PREALG-C01-REMAINDER-TRAP` | `c01-ceiling-rounding-trap` |
| MTH-T01-C01 | `c01-multi-unit-budget-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C01-SYNTHESIS` | `c01-order-of-operations-trap` |
| MTH-T01-C01 | `c01-multi-unit-budget-synthesis` | `multi-constraint` | L4 | **variant** | `MTH-PREALG-C01-SYNTHESIS` | `c01-order-of-operations-trap` |
| MTH-T01-C02 | `c02-evaluate-expression` | `direct` | L1 | **forward** | `MTH-PREALG-C02-EVAL` | `c02-substitution-precedence` |
| MTH-T01-C02 | `c02-evaluate-expression` | `nested` | L1 | **variant** | `MTH-PREALG-C02-EVAL` | `c02-substitution-precedence` |
| MTH-T01-C02 | `c02-translate-and-solve-one-step` | `direct` | L2 | **forward** | `MTH-PREALG-C02-TRANSLATE` | `c02-translation-subtraction-order` |
| MTH-T01-C02 | `c02-translate-and-solve-one-step` | `reverse` | L2 | **reverse** | `MTH-PREALG-C02-TRANSLATE` | `c02-translation-subtraction-order` |
| MTH-T01-C02 | `c02-lcm-gcd-prime-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C02-LCM-TRAP` | `c02-lcm-gcd-exponent-trap` |
| MTH-T01-C02 | `c02-lcm-gcd-prime-trap` | `synodic-cycle` | L3 | **variant** | `MTH-PREALG-C02-LCM-TRAP` | `c02-lcm-gcd-exponent-trap` |
| MTH-T01-C02 | `c02-algebraic-divisibility-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C02-SYNTHESIS` | `c02-lcm-gcd-exponent-trap` |
| MTH-T01-C02 | `c02-algebraic-divisibility-synthesis` | `multi-constraint` | L4 | **variant** | `MTH-PREALG-C02-SYNTHESIS` | `c02-lcm-gcd-exponent-trap` |
| MTH-T01-C03 | `c03-abs-value-integer-add` | `direct` | L1 | **forward** | `MTH-PREALG-C03-ADD-SUB` | `c03-double-negative-slip` |
| MTH-T01-C03 | `c03-abs-value-integer-add` | `elevation` | L1 | **variant** | `MTH-PREALG-C03-ADD-SUB` | `c03-double-negative-slip` |
| MTH-T01-C03 | `c03-signed-mult-div-equations` | `direct` | L2 | **forward** | `MTH-PREALG-C03-MULT-DIV` | `c03-signed-division-sign-error` |
| MTH-T01-C03 | `c03-signed-mult-div-equations` | `reverse` | L2 | **reverse** | `MTH-PREALG-C03-MULT-DIV` | `c03-signed-division-sign-error` |
| MTH-T01-C03 | `c03-negated-power-order-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C03-POWER-TRAP` | `c03-negated-square-precedence-trap` |
| MTH-T01-C03 | `c03-negated-power-order-trap` | `nested-abs` | L3 | **variant** | `MTH-PREALG-C03-POWER-TRAP` | `c03-negated-square-precedence-trap` |
| MTH-T01-C03 | `c03-thermal-depth-integer-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C03-SYNTHESIS` | `c03-net-integer-change-trap` |
| MTH-T01-C03 | `c03-thermal-depth-integer-synthesis` | `contextual` | L4 | **context** | `MTH-PREALG-C03-SYNTHESIS` | `c03-net-integer-change-trap` |
| MTH-T01-C04 | `c04-fraction-mult-div` | `direct` | L1 | **forward** | `MTH-PREALG-C04-MULT-DIV` | `c04-reciprocal-omission` |
| MTH-T01-C04 | `c04-fraction-mult-div` | `reciprocal` | L1 | **variant** | `MTH-PREALG-C04-MULT-DIV` | `c04-reciprocal-omission` |
| MTH-T01-C04 | `c04-unlike-denom-add-sub` | `direct` | L2 | **forward** | `MTH-PREALG-C04-UNLIKE-ADD` | `c04-unlike-denominator-direct-add` |
| MTH-T01-C04 | `c04-unlike-denom-add-sub` | `missing-term` | L2 | **variant** | `MTH-PREALG-C04-UNLIKE-ADD` | `c04-unlike-denominator-direct-add` |
| MTH-T01-C04 | `c04-complex-fraction-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C04-COMPLEX-TRAP` | `c04-complex-fraction-inversion-trap` |
| MTH-T01-C04 | `c04-complex-fraction-trap` | `difference` | L3 | **variant** | `MTH-PREALG-C04-COMPLEX-TRAP` | `c04-complex-fraction-inversion-trap` |
| MTH-T01-C04 | `c04-fractional-partition-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C04-SYNTHESIS` | `c04-remainder-fraction-base-trap` |
| MTH-T01-C04 | `c04-fractional-partition-synthesis` | `contextual` | L4 | **context** | `MTH-PREALG-C04-SYNTHESIS` | `c04-remainder-fraction-base-trap` |
| MTH-T01-C05 | `c05-decimal-linear-eval` | `direct` | L1 | **forward** | `MTH-PREALG-C05-DEC-OPS` | `c05-decimal-point-alignment` |
| MTH-T01-C05 | `c05-decimal-linear-eval` | `rate` | L1 | **variant** | `MTH-PREALG-C05-DEC-OPS` | `c05-decimal-point-alignment` |
| MTH-T01-C05 | `c05-decimal-equation-mean` | `direct` | L2 | **forward** | `MTH-PREALG-C05-MEAN` | `c05-missing-score-mean-trap` |
| MTH-T01-C05 | `c05-decimal-equation-mean` | `missing-score` | L2 | **variant** | `MTH-PREALG-C05-MEAN` | `c05-missing-score-mean-trap` |
| MTH-T01-C05 | `c05-decimal-division-shift-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C05-DIV-SHIFT` | `c05-decimal-divisor-shift-trap` |
| MTH-T01-C05 | `c05-decimal-division-shift-trap` | `combined` | L3 | **variant** | `MTH-PREALG-C05-DIV-SHIFT` | `c05-decimal-divisor-shift-trap` |
| MTH-T01-C05 | `c05-weighted-average-probability-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C05-SYNTHESIS` | `c05-weighted-average-unweighted-trap` |
| MTH-T01-C05 | `c05-weighted-average-probability-synthesis` | `contextual` | L4 | **context** | `MTH-PREALG-C05-SYNTHESIS` | `c05-weighted-average-unweighted-trap` |
| MTH-T01-C06 | `c06-percent-of-base` | `direct` | L1 | **forward** | `MTH-PREALG-C06-PERCENT-BASE` | `c06-percent-decimal-conversion` |
| MTH-T01-C06 | `c06-percent-of-base` | `find-rate` | L1 | **variant** | `MTH-PREALG-C06-PERCENT-BASE` | `c06-percent-decimal-conversion` |
| MTH-T01-C06 | `c06-discount-tax-interest` | `direct` | L2 | **forward** | `MTH-PREALG-C06-DISCOUNT` | `c06-reverse-discount-base-trap` |
| MTH-T01-C06 | `c06-discount-tax-interest` | `reverse-base` | L2 | **reverse** | `MTH-PREALG-C06-DISCOUNT` | `c06-reverse-discount-base-trap` |
| MTH-T01-C06 | `c06-successive-percent-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C06-SUCCESSIVE-TRAP` | `c06-successive-percent-linear-add` |
| MTH-T01-C06 | `c06-successive-percent-trap` | `markup-discount` | L3 | **variant** | `MTH-PREALG-C06-SUCCESSIVE-TRAP` | `c06-successive-percent-linear-add` |
| MTH-T01-C06 | `c06-investment-commission-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C06-SYNTHESIS` | `c06-simple-interest-split-trap` |
| MTH-T01-C06 | `c06-investment-commission-synthesis` | `contextual` | L4 | **context** | `MTH-PREALG-C06-SYNTHESIS` | `c06-simple-interest-split-trap` |
| MTH-T01-C07 | `c07-unit-rate-proportion` | `direct` | L1 | **forward** | `MTH-PREALG-C07-PROPORTION` | `c07-cross-multiply-inversion` |
| MTH-T01-C07 | `c07-unit-rate-proportion` | `unit-rate` | L1 | **variant** | `MTH-PREALG-C07-PROPORTION` | `c07-cross-multiply-inversion` |
| MTH-T01-C07 | `c07-similar-figures-scale` | `direct` | L2 | **forward** | `MTH-PREALG-C07-RATIO-SHARE` | `c07-ratio-part-vs-whole-trap` |
| MTH-T01-C07 | `c07-similar-figures-scale` | `reverse-scale` | L2 | **reverse** | `MTH-PREALG-C07-RATIO-SHARE` | `c07-ratio-part-vs-whole-trap` |
| MTH-T01-C07 | `c07-area-scale-factor-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C07-SCALE-TRAP` | `c07-area-linear-scale-trap` |
| MTH-T01-C07 | `c07-area-scale-factor-trap` | `volume-scale` | L3 | **variant** | `MTH-PREALG-C07-SCALE-TRAP` | `c07-area-linear-scale-trap` |
| MTH-T01-C07 | `c07-harmonic-speed-work-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C07-SYNTHESIS` | `c07-arithmetic-mean-speed-trap` |
| MTH-T01-C07 | `c07-harmonic-speed-work-synthesis` | `combined-work` | L4 | **variant** | `MTH-PREALG-C07-SYNTHESIS` | `c07-arithmetic-mean-speed-trap` |
| MTH-T01-C08 | `c08-product-quotient-powers` | `direct` | L1 | **forward** | `MTH-PREALG-C08-PROD-QUOT` | `c08-exponent-product-multiply-trap` |
| MTH-T01-C08 | `c08-product-quotient-powers` | `quotient` | L1 | **forward** | `MTH-PREALG-C08-PROD-QUOT` | `c08-exponent-product-multiply-trap` |
| MTH-T01-C08 | `c08-power-of-product-neg-exp` | `direct` | L2 | **forward** | `MTH-PREALG-C08-POWER-PRODUCT` | `c08-power-of-product-unscaled-coeff` |
| MTH-T01-C08 | `c08-power-of-product-neg-exp` | `solve-exponent` | L2 | **reverse** | `MTH-PREALG-C08-POWER-PRODUCT` | `c08-power-of-product-unscaled-coeff` |
| MTH-T01-C08 | `c08-power-tower-addition-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C08-ADD-TRAP` | `c08-same-base-sum-exponent-trap` |
| MTH-T01-C08 | `c08-power-tower-addition-trap` | `same-base-sum` | L3 | **variant** | `MTH-PREALG-C08-ADD-TRAP` | `c08-same-base-sum-exponent-trap` |
| MTH-T01-C08 | `c08-scientific-notation-growth-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C08-SYNTHESIS` | `c08-common-base-conversion-trap` |
| MTH-T01-C08 | `c08-scientific-notation-growth-synthesis` | `exponential-doubling` | L4 | **variant** | `MTH-PREALG-C08-SYNTHESIS` | `c08-common-base-conversion-trap` |
| MTH-T01-C09 | `c09-perfect-square-cube-roots` | `direct` | L1 | **forward** | `MTH-PREALG-C09-ROOT-EVAL` | `c09-root-halving-trap` |
| MTH-T01-C09 | `c09-perfect-square-cube-roots` | `combined` | L1 | **variant** | `MTH-PREALG-C09-ROOT-EVAL` | `c09-root-halving-trap` |
| MTH-T01-C09 | `c09-simplify-like-radicals` | `direct` | L2 | **forward** | `MTH-PREALG-C09-RADICAL-EQ` | `c09-radical-equation-unsquared-trap` |
| MTH-T01-C09 | `c09-simplify-like-radicals` | `radical-equation` | L2 | **variant** | `MTH-PREALG-C09-RADICAL-EQ` | `c09-radical-equation-unsquared-trap` |
| MTH-T01-C09 | `c09-non-distributive-root-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C09-SUM-TRAP` | `c09-root-sum-distribution-trap` |
| MTH-T01-C09 | `c09-non-distributive-root-trap` | `quotient-radical` | L3 | **variant** | `MTH-PREALG-C09-SUM-TRAP` | `c09-root-sum-distribution-trap` |
| MTH-T01-C09 | `c09-nested-radical-geometric-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C09-SYNTHESIS` | `c09-nested-radical-evaluation-trap` |
| MTH-T01-C09 | `c09-nested-radical-geometric-synthesis` | `radical-conjugate` | L4 | **variant** | `MTH-PREALG-C09-SYNTHESIS` | `c09-nested-radical-evaluation-trap` |
| MTH-T01-C10 | `c10-distributive-collect-terms` | `direct` | L1 | **forward** | `MTH-PREALG-C10-DISTRIBUTE` | `c10-partial-distribution-slip` |
| MTH-T01-C10 | `c10-distributive-collect-terms` | `mental-split` | L1 | **variant** | `MTH-PREALG-C10-DISTRIBUTE` | `c10-partial-distribution-slip` |
| MTH-T01-C10 | `c10-additive-multiplicative-inverse` | `direct` | L2 | **forward** | `MTH-PREALG-C10-ASSOC-INV` | `c10-partial-distribution-slip` |
| MTH-T01-C10 | `c10-additive-multiplicative-inverse` | `unit-conversion` | L2 | **variant** | `MTH-PREALG-C10-ASSOC-INV` | `c10-partial-distribution-slip` |
| MTH-T01-C10 | `c10-negative-distribution-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C10-NEG-DIST-TRAP` | `c10-negative-distribution-sign-trap` |
| MTH-T01-C10 | `c10-negative-distribution-trap` | `nested-brackets` | L3 | **variant** | `MTH-PREALG-C10-NEG-DIST-TRAP` | `c10-negative-distribution-sign-trap` |
| MTH-T01-C10 | `c10-real-closure-measurement-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C10-SYNTHESIS` | `c10-dimensional-unit-conversion-trap` |
| MTH-T01-C10 | `c10-real-closure-measurement-synthesis` | `unit-rate-conversion` | L4 | **variant** | `MTH-PREALG-C10-SYNTHESIS` | `c10-dimensional-unit-conversion-trap` |
| MTH-T01-C11 | `c11-two-step-linear-equation` | `direct` | L1 | **forward** | `MTH-PREALG-C11-TWO-STEP` | `c11-constant-transposition-sign` |
| MTH-T01-C11 | `c11-two-step-linear-equation` | `negative-coeff` | L1 | **variant** | `MTH-PREALG-C11-TWO-STEP` | `c11-constant-transposition-sign` |
| MTH-T01-C11 | `c11-variables-both-sides` | `direct` | L2 | **forward** | `MTH-PREALG-C11-BOTH-SIDES` | `c11-variable-grouping-sign-slip` |
| MTH-T01-C11 | `c11-variables-both-sides` | `grouped` | L2 | **variant** | `MTH-PREALG-C11-BOTH-SIDES` | `c11-variable-grouping-sign-slip` |
| MTH-T01-C11 | `c11-fractional-equation-clearing-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C11-FRAC-CLEAR` | `c11-fraction-numerator-sign-trap` |
| MTH-T01-C11 | `c11-fractional-equation-clearing-trap` | `unscaled-constant-trap` | L3 | **variant** | `MTH-PREALG-C11-FRAC-CLEAR` | `c11-fraction-numerator-sign-trap` |
| MTH-T01-C11 | `c11-parametric-consecutive-linear-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C11-SYNTHESIS` | `c11-consecutive-parity-step-trap` |
| MTH-T01-C11 | `c11-parametric-consecutive-linear-synthesis` | `parametric-root` | L4 | **variant** | `MTH-PREALG-C11-SYNTHESIS` | `c11-consecutive-parity-step-trap` |
| MTH-T01-C12 | `pythagoras-hypotenuse` | `direct` | L1 | **forward** | `GEO-RIGHT-TRIANGLE-HYP` | `pythagoras-hypotenuse` |
| MTH-T01-C12 | `pythagoras-hypotenuse` | `reverse` | L2 | **reverse** | `GEO-RIGHT-TRIANGLE-LEG` | `pythagoras-hypotenuse` |
| MTH-T01-C12 | `pythagoras-hypotenuse` | `contextual` | L2 | **context** | `GEO-RIGHT-TRIANGLE-APPLIED` | `pythagoras-hypotenuse` |
| MTH-T01-C12 | `trapezoid-area` | `direct` | L2 | **forward** | `GEO-TRAPEZOID-AREA` | `trapezoid-height` |
| MTH-T01-C12 | `trapezoid-area` | `reverse` | L2 | **reverse** | `GEO-TRAPEZOID-HEIGHT` | `trapezoid-height` |
| MTH-T01-C12 | `circle-area-pi` | `direct` | L2 | **forward** | `GEO-CIRCLE-AREA-RADIUS` | `circle-diameter-radius` |
| MTH-T01-C12 | `circle-area-pi` | `from-diameter` | L2 | **variant** | `GEO-CIRCLE-AREA-DIAMETER` | `circle-diameter-radius` |
| MTH-T01-C12 | `cylinder-volume` | `direct` | L2 | **forward** | `GEO-CYLINDER-VOLUME-RADIUS` | `volume-surface-area` |
| MTH-T01-C12 | `cylinder-volume` | `from-diameter` | L2 | **variant** | `GEO-CYLINDER-VOLUME-DIAMETER` | `volume-surface-area` |
| MTH-T01-C12 | `altitude-inradius` | `direct` | L3 | **forward** | `GEO-RIGHT-TRIANGLE-APPLIED` | `whole-triangle-inradius-confusion` |
| MTH-T01-C12 | `altitude-inradius` | `missing-segment` | L3 | **reverse** | `GEO-RIGHT-TRIANGLE-APPLIED` | `whole-triangle-inradius-confusion` |
| MTH-T01-C12 | `trapezoid-similar-triangles` | `direct` | L4 | **forward** | `GEO-TRAPEZOID-HEIGHT` | `trapezoid-diagonal-bisect-trap` |
| MTH-T01-C12 | `trapezoid-similar-triangles` | `bottom-triangle` | L4 | **variant** | `GEO-TRAPEZOID-HEIGHT` | `trapezoid-diagonal-bisect-trap` |
| MTH-T01-C12 | `trapezoid-similar-triangles` | `side-triangle` | L4 | **variant** | `GEO-TRAPEZOID-HEIGHT` | `trapezoid-diagonal-bisect-trap` |
| MTH-T01-C12 | `lunes-hippocrates` | `direct` | L4 | **forward** | `GEO-CIRCLE-AREA-DIAMETER` | `pi-retained-in-lunes-trap` |
| MTH-T01-C12 | `lunes-hippocrates` | `single-lune` | L4 | **variant** | `GEO-CIRCLE-AREA-DIAMETER` | `pi-retained-in-lunes-trap` |
| MTH-T01-C12 | `cone-frustum-volume` | `direct` | L3 | **forward** | `GEO-CYLINDER-VOLUME-DIAMETER` | `frustum-cylinder-average-trap` |
| MTH-T01-C12 | `cone-frustum-volume` | `from-diameter` | L3 | **variant** | `GEO-CYLINDER-VOLUME-DIAMETER` | `frustum-cylinder-average-trap` |
| MTH-T01-C12 | `find-flaw-composite-surface-area` | `flaw-line-2` | L3 | **variant** | `GEO-CYLINDER-VOLUME-RADIUS` | `internal-boundary-double-count-trap` |
| MTH-T01-C12 | `find-flaw-composite-surface-area` | `flaw-line-3` | L3 | **variant** | `GEO-CYLINDER-VOLUME-RADIUS` | `internal-boundary-double-count-trap` |
| MTH-T01-C13 | `c13-add-subtract-polynomials` | `direct` | L1 | **forward** | `MTH-PREALG-C13-ADD-SUB` | `c13-polynomial-subtraction-sign-slip` |
| MTH-T01-C13 | `c13-add-subtract-polynomials` | `evaluate` | L1 | **forward** | `MTH-PREALG-C13-ADD-SUB` | `c13-polynomial-subtraction-sign-slip` |
| MTH-T01-C13 | `c13-multiply-binomials-foil` | `direct` | L2 | **forward** | `MTH-PREALG-C13-FOIL` | `c13-foil-middle-term-omission` |
| MTH-T01-C13 | `c13-multiply-binomials-foil` | `missing-middle-coeff` | L2 | **variant** | `MTH-PREALG-C13-FOIL` | `c13-foil-middle-term-omission` |
| MTH-T01-C13 | `c13-binomial-square-freshman-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C13-SPECIAL-PROD` | `c13-freshman-dream-square-trap` |
| MTH-T01-C13 | `c13-binomial-square-freshman-trap` | `subtracted-polynomial-sign-trap` | L3 | **variant** | `MTH-PREALG-C13-SPECIAL-PROD` | `c13-freshman-dream-square-trap` |
| MTH-T01-C13 | `c13-polynomial-identity-area-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C13-SYNTHESIS` | `c13-difference-of-squares-frame-trap` |
| MTH-T01-C13 | `c13-polynomial-identity-area-synthesis` | `quotient-identity` | L4 | **variant** | `MTH-PREALG-C13-SYNTHESIS` | `c13-difference-of-squares-frame-trap` |
| MTH-T01-C14 | `c14-midpoint-intercepts` | `direct` | L1 | **forward** | `MTH-PREALG-C14-INTERCEPTS` | `c14-intercept-axis-swap-trap` |
| MTH-T01-C14 | `c14-midpoint-intercepts` | `intercept-sum` | L1 | **variant** | `MTH-PREALG-C14-INTERCEPTS` | `c14-intercept-axis-swap-trap` |
| MTH-T01-C14 | `c14-slope-two-points` | `direct` | L2 | **forward** | `MTH-PREALG-C14-SLOPE` | `c14-slope-run-over-rise-trap` |
| MTH-T01-C14 | `c14-slope-two-points` | `missing-coordinate` | L2 | **variant** | `MTH-PREALG-C14-SLOPE` | `c14-slope-run-over-rise-trap` |
| MTH-T01-C14 | `c14-perpendicular-bisector-trap` | `direct` | L3 | **forward** | `MTH-PREALG-C14-PERP-TRAP` | `c14-perpendicular-slope-sign-trap` |
| MTH-T01-C14 | `c14-perpendicular-bisector-trap` | `collinear-parameter` | L3 | **variant** | `MTH-PREALG-C14-PERP-TRAP` | `c14-perpendicular-slope-sign-trap` |
| MTH-T01-C14 | `c14-perpendicular-bisector-trap` | `bisector-intercept` | L3 | **variant** | `MTH-PREALG-C14-PERP-TRAP` | `c14-perpendicular-slope-sign-trap` |
| MTH-T01-C14 | `c14-coordinate-geometry-synthesis` | `direct` | L4 | **forward** | `MTH-PREALG-C14-SYNTHESIS` | `c14-lattice-endpoint-exclusion-trap` |
| MTH-T01-C14 | `c14-coordinate-geometry-synthesis` | `reflection-point` | L4 | **variant** | `MTH-PREALG-C14-SYNTHESIS` | `c14-lattice-endpoint-exclusion-trap` |
| MTH-T01-C14 | `c14-coordinate-geometry-synthesis` | `lattice-points` | L4 | **variant** | `MTH-PREALG-C14-SYNTHESIS` | `c14-lattice-endpoint-exclusion-trap` |

## 3. Top 10 Most Repetitive Templates (Smallest Unique Problem Space)

Measured by unique mathematical `display` expressions produced across 200 random seeds:

| Rank | Chapter | Template Key | Unique Displays (200 Seeds) | Root Cause & Failure Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| 1 | MTH-T01-C12 | `circle-area-pi` | 2 | Fixed formula string in `display` without embedding numerical radius/diameter (e.g. `A = \pi r^2`). |
| 2 | MTH-T01-C12 | `cylinder-volume` | 2 | Fixed formula string in `display` without embedding numerical radius/height. |
| 3 | MTH-T01-C12 | `trapezoid-area` | 2 | Fixed formula string in `display` without embedding numerical dimensions. |
| 4 | MTH-T01-C12 | `cone-frustum-volume` | 8 | Only 4 hardcoded geometric dimension sets in template cases. |
| 5 | MTH-T01-C04 | `c04-complex-fraction-trap` | 10 | Fixed list of 5 fraction pairs × 2 forms = 10 total unique problems. |
| 6 | MTH-T01-C04 | `c04-fractional-partition-synthesis` | 10 | Fixed list of 5 fraction application cases × 2 forms = 10 total unique problems. |
| 7 | MTH-T01-C05 | `c05-decimal-linear-eval` | 10 | Fixed list of 5 coefficient sets × 2 forms = 10 total unique problems. |
| 8 | MTH-T01-C05 | `c05-weighted-average-probability-synthesis` | 10 | Fixed list of 5 probability/weighting scenarios × 2 forms = 10 total unique problems. |
| 9 | MTH-T01-C06 | `c06-discount-tax-interest` | 10 | Fixed list of 5 financial numbers × 2 forms = 10 total unique problems. |
| 10 | MTH-T01-C06 | `c06-investment-commission-synthesis` | 10 | Fixed list of 5 financial cases × 2 forms = 10 total unique problems. |

## 4. Deep-Dive Pedagogical Direction Analysis

### Case A: `circle-area-pi` / `from-diameter`
- **Is it Reverse?** **NO (Classified as `variant`).**
- **Mathematical Rationale:** Both `direct` (given radius $r$, find $A = \pi r^2$) and `from-diameter` (given diameter $d$, find $A = \pi (d/2)^2$) operate in the exact same forward operational direction: calculating area from linear length inputs. The only difference is requiring an initial division by 2 ($r = d/2$).
- **True Reverse Form would be:** Given Area $A = 36\pi$, solve backwards for the radius $r = \sqrt{A/\pi} = 6$ or diameter $d = 12$.

### Case B: `c11-two-step-linear-equation` / `negative-coeff`
- **Is it Reverse?** **NO (Classified as `variant`).**
- **Mathematical Rationale:** Both `direct` ($ax + b = c$) and `negative-coeff` ($b - ax = c$) are forward linear algebraic manipulations solving for $x$. Swapping terms or introducing negative coefficients tests sign handling, not reverse reasoning.
- **True Reverse Form would be:** Given the solution root $x = 8$ and partial equation $5x - c = 27$, solve backwards for the missing constant $c$, or given the solution, select/construct the matching equation.

## 5. Templates Lacking Genuine Reverse Reasoning & Constant-Only Variations

- **Templates Lacking Genuine Reverse Reasoning (Forms are purely Forward or Variant):**
  - `c01-place-value-rounding`: `direct` vs `contextual` (both forward arithmetic)
  - `c03-divisibility-prime-factors`: `direct` vs `exponent-sum` (both forward factorizations)
  - `c05-decimal-linear-eval`: `direct` vs `bracket` (both forward evaluation)
  - `c10-radical-simplification`: `direct` vs `fractional-radicand` (both forward simplification)
  - `c11-two-step-linear-equation`: `direct` vs `negative-coeff` (both forward equation solving)
  - `circle-area-pi`: `direct` vs `from-diameter` (both forward area calculation)
  - `cylinder-volume`: `direct` vs `from-diameter` (both forward volume calculation)
  - `c13-add-subtract-polynomials`: `direct` vs `evaluate` (both forward polynomial evaluations)
  - `c14-midpoint-intercepts`: `direct` vs `intercept-sum` (both forward intercept calculations)

- **Templates where Forms Differ Only by Constants / Cosmetic Tags:**
  - `c08-power-tower-addition-trap`: `direct` ($2^m + 2^m$) vs `same-base-sum` ($3^m + 3^m$) only changes base constant 2 to 3.
  - `c09-scientific-notation-arithmetic`: `direct` vs `subtraction` only swaps addition operator with subtraction.
  - `c10-radical-operations`: `direct` vs `mixed-operations` only switches multiplication to mixed mult/add.