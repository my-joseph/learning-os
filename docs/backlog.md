# Backlog: known gaps for later topics

Gaps found by test drills that do not block the units that have vaults today.
Fix each one when the topic it belongs to is actually started, not before. Sources: calculus and trig-equation (T02-C08-U05) test drills, 2026-11-14.

## Before T02-C06 to C09 (trigonometry)

- Answer and trusted functions: `sec`, `csc`, `cot`, `arcsin`/`asin`, `arccos`/`acos`, `arctan`/`atan` are not in `WHITELIST_FUNCS` or `TRUSTED_INTERNAL_FUNCS`. Problems must be written with `sin`, `cos`, `tan` until then.

## Before T02-C05 (Exponential and Logarithmic Functions)

- `is_equal` also samples negative values, so `ln(x^2)` and `2*ln(x)` (or `ln(x)` and `ln(abs(x))`) compare as unequal. Log answers need a domain-aware comparison.

## Before adding calculus to the curriculum

- Antiderivatives: `+C` is treated as an ordinary variable. Another letter (`K`, `c`) is invalid input, and a correct answer whose constant differs (e.g. from u-substitution vs. expanding) is graded incorrect.
- Step checks: `TRUSTED_INTERNAL_FUNCS` has `diff` but no `integrate`, so antiderivative steps cannot be machine-checked.
- Figures: no builder for area under a curve or a tangent line.

## Cosmetic

- The `whole_sign_flip` diagnostic mentions `i^2 = -1` in non-complex problems.
- `solution_set` diagnostics: `missing_solution` always says "Remember both signs of ±" (wrong hint for trig), and a value outside the requested interval (e.g. `13pi/6` for `[0, 2pi)`) is called "does not satisfy the equation" although it does.
