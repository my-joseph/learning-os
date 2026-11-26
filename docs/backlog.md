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

### Interactive math and physics visuals (candidates, learner 2026-11-26)

Not installed. When a topic below starts, pilot ONE interactive in the Studio only as an extra beside the static figure: problem figures stay on the shared `MathFigure` spec so the Studio and Notion (`math_engine/figure_svg.py`) match. Each library needs learner approval, a Studio wrapper, token colours, lazy loading and a size check (docs/design/components.md, External libraries).

- **Mafs** (https://mafs.dev, MIT, React >=18, uses KaTeX): coordinate plane, function plots, draggable points, vectors, circles, polygons. First choice for 2D: draggable unit circle (trigonometry), parabola/transform sliders (functions), tangent line and area under a curve (calculus). Could later replace the hand-written `InteractiveCircle2D`, `InteractivePythagoras2D`, `InteractiveTrapezoid2D`. Last release 2025-03.
- **D3** (https://d3js.org, ISC): low-level data/SVG toolkit (scales, axes, shapes, transitions). Use only for a custom chart or visual nothing else covers (e.g. a Skills Status or progress chart); for math plots prefer Mafs, for dashboards see the chart registries in `pilot/research/shadcn-registry-shortlist.md`.
- **Matter.js** (https://brm.io/matter-js, MIT): 2D rigid-body physics (gravity, collisions, springs, friction). Candidate for `PHY` units (motion, forces, momentum, energy) as a play-and-observe sandbox; not for MTH.
- **awesome-interactive-math** (https://github.com/ubavic/awesome-interactive-math): reference list. Worth a look when designing a topic: JSXGraph (interactive geometry and plotting), Mathigon (open-source interactive-course libraries), CindyJS, Desmos API (embed; licence/terms check needed), and examples for inspiration such as *Seeing circles, sines and signals* (trigonometry), *Immersive linear algebra*, *Complex analysis* by Ponce Campuzano (complex numbers, MTH-T02-C01), setosa.io and Bartosz Ciechanowski's articles.

### Open cosmetic observations

- A `solution_set` value outside the requested interval (e.g. `13pi/6` for `[0, 2pi)`) is called "does not satisfy the equation" even though it does.

## Resolved

- **Answer diagnostics:** `whole_sign_flip` reserves the `$i^2 = -1$` reminder for complex expressions; `solution_set` sign and missing-root diagnostics use domain-neutral guidance, mentioning both signs only for symmetric roots.

- **T02-C05 (`is_equal` logarithm domain sampling):** `math_engine/answer_check.py`'s `is_equal` skips non-real samples so equivalent log forms (`ln(x^2)` vs `2*ln(x)`, `ln(x)` vs `ln(abs(x))`) compare equal on their shared real domain; `MTH-T02-C05-U01` is active.
- **Studio Math / Programming workspace split:** live at `/math/[drillId]`, `/code/[drillId]`, and `/code/lab/[labId]`.
