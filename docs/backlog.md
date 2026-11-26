# Backlog: known gaps for later topics

Gaps found by test drills that do not block the units that have vaults today.
Fix each one when the topic it belongs to is actually started, not before. Sources: calculus and trig-equation (T02-C08-U05) test drills, 2026-11-14.

## Open gaps

### Before T02-C06 to C09 (trigonometry)

- Answer and trusted functions: `sec`, `csc`, `cot`, `arcsin`/`asin`, `arccos`/`acos`, `arctan`/`atan` are not in `WHITELIST_FUNCS` or `TRUSTED_INTERNAL_FUNCS`. Problems must be written with `sin`, `cos`, `tan` until then.

### Before adding calculus to the curriculum

- Antiderivatives: `+C` is treated as an ordinary variable. Another letter (`K`, `c`) is invalid input, and a correct answer whose constant differs (e.g. from u-substitution vs. expanding) is graded incorrect.
- Step checks: `TRUSTED_INTERNAL_FUNCS` has `diff` but no `integrate`, so antiderivative steps cannot be machine-checked.
- Figures: no builder for area under a curve or a tangent line.
- Trigonometry figures: no unit-circle builder and no right triangle labelled with an angle θ and opposite/adjacent/hypotenuse (`build_function_graph_figure` already draws `sin`/`cos` graphs).

### Isometric interactive figures (merged, experimental — learner polishes before use)

Learner decision 2026-11-26: the ported Isometric engine is in the repo, but nothing uses it outside `/ui-poc/isometric` and `/ui-poc/isometric-math` until the learner has polished it and says to start. Do not add these figures to drills, unit pages or Studio screens before that.

- What exists: engine `practice-studio/src/lib/isometric/` (MIT, vendored; primitives box, cylinder, pyramid, frustum, lathe, extrude, torus, tube, wheel/teeth, mapMesh; picking, springs, keyboard parts); figures Cube, Pulley, Lever (`practice-studio/src/lib/isometric/physics/lever.ts`), DiskMethod (`practice-studio/src/lib/isometric/math/diskMethod.ts`), each with pure logic + unit tests; research notes in `pilot/isometric/` (local).
- Cost measured 2026-11-26: about 20 min and 0.3–0.5M agy tokens per new figure, plus 10–15 min review; about 3 KB gzip per figure, engine about 10 KB once, lazy-loaded.
- Review checklist for every figure (both experiment figures failed a check that tests missed): subject correctness against a cited source (formulas, units — force in N, never kg); the lesson is visible by default (e.g. the lever must look level vs tipped; the disk method must show error shrinking); stated assumptions (massless beam, g = 9.8); zero-leak mode when used in a problem; light/dark, keyboard, reduced motion.
- Missing before real use: static SVG export so Notion shows the same figure; a figure spec (`{ kind, params }`) so problems reference builders instead of code; surface z = f(x, y) primitive if needed.

### Open cosmetic observations

- A `solution_set` value outside the requested interval (e.g. `13pi/6` for `[0, 2pi)`) is called "does not satisfy the equation" even though it does.

## Resolved

- **Answer diagnostics:** `whole_sign_flip` reserves the `$i^2 = -1$` reminder for complex expressions; `solution_set` sign and missing-root diagnostics use domain-neutral guidance, mentioning both signs only for symmetric roots.

- **T02-C05 (`is_equal` logarithm domain sampling):** `math_engine/answer_check.py`'s `is_equal` skips non-real samples so equivalent log forms (`ln(x^2)` vs `2*ln(x)`, `ln(x)` vs `ln(abs(x))`) compare equal on their shared real domain; `MTH-T02-C05-U01` is active.
- **Studio Math / Programming workspace split:** live at `/math/[drillId]`, `/code/[drillId]`, and `/code/lab/[labId]`.
