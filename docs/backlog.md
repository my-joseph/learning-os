# Backlog: known gaps for later topics

Gaps found by test drills that do not block the current curriculum (T01 Prealgebra, T02 Algebra and Trigonometry).
Fix each one when the topic it belongs to is actually started, not before. Source: calculus test drill, 2026-11-14.

## Before T02-C05 (Exponential and Logarithmic Functions)

- `is_equal` also samples negative values, so `ln(x^2)` and `2*ln(x)` (or `ln(x)` and `ln(abs(x))`) compare as unequal. Log answers need a domain-aware comparison.

## Before adding calculus to the curriculum

- Antiderivatives: `+C` is treated as an ordinary variable. Another letter (`K`, `c`) is invalid input, and a correct answer whose constant differs (e.g. from u-substitution vs. expanding) is graded incorrect.
- Answer functions: `sec`, `csc`, `cot`, `arcsin`, `arctan` are not in `WHITELIST_FUNCS`.
- Step checks: `TRUSTED_INTERNAL_FUNCS` has `diff` but no `integrate`, so antiderivative steps cannot be machine-checked.
- Figures: no builder for area under a curve or a tangent line.

## Cosmetic

- The `whole_sign_flip` diagnostic mentions `i^2 = -1` in non-complex problems.
