# Source Registry

Local raw study materials live under `sources/` in the main checkout (gitignored; override with `LEARNINGOS_SOURCES_DIR`, which defaults to `<main checkout>/sources` even from a git worktree).

## Source Families

| Family (under `sources/`) | What it is | Language | Licence / Terms | Allowed use | Topic coverage notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `openstax/math/<book>/` | OpenStax mathematics textbooks (e.g. Algebra & Trigonometry, Precalculus, Calculus) | EN | CC BY-NC-SA 4.0; OpenStax restricts automated/AI ingestion (`rules/07` §4) | `scope` | Curriculum baseline TOC and learning objectives across MTH topics; **never mined for exercises** |
| `openstax/cs-physics/...` | OpenStax computer science and physics textbooks | EN | CC BY-NC-SA 4.0; OpenStax restricts automated/AI ingestion (`rules/07` §4) | `scope` | Curriculum baseline TOC and learning objectives across PHY/CS topics; **never mined for exercises** |
| `mathsgenie/Grade_N/{Booklets,Exam_Questions,Solutions}/` | MathsGenie GCSE revision booklets, exam questions, and solutions | EN | Free worksheets, all rights reserved | `cores` | GCSE Grades 1–9 math fundamentals, algebra, geometry, probability, statistics; ideas/cores only |
| `thai-exams/onet-2568/` | Thailand O-NET 2568 exam papers (P6 / M3 / M6 Math & Science) | TH | © NIETS (all rights reserved) | `cores` | P6, M3, M6 national math & science exam patterns and multi-choice distractors; ideas/cores only |
| `thai-exams/tcas68-a-level/` | Thailand TCAS68 A-Level exam papers (`math1`, `math2`, `phy`, `sci`, `eng`) | TH | © TCAS / CUPT (all rights reserved) | `cores` | High-school Math 1/2, physics, science, English; 5-option exam formats & trap distractors; ideas/cores only |
| `illustrative-math/grade6-unit1/*.zip` | Illustrative Mathematics Grade 6 Unit 1 curriculum bundles | EN | CC BY 4.0 (ideas/cores only by our policy) | `cores` | Grade 6 geometry/area conceptual tasks and visual reasoning; ideas/cores only |

## Policy & Local Layout

- **`scope` families (OpenStax):** Read only table-of-contents and learning-objective pages to set unit scope (`rules/07` §4). Never extract core cards or mine exercises.
- **`cores` families:** Abstract problems into source-free core cards (`sources/_cores/<UNIT>.jsonl`) recording only the mathematical skill, reasoning move, difficulty driver, traps, and format. **Never copy, translate, or paraphrase a source problem, and never reuse its numbers.**
- **Local artifacts (all gitignored under `sources/`):**
  - `sources/_index/` — cached extracted PDF text and per-unit located-page manifests (`located_<UNIT>.json`).
  - `sources/_cores/<UNIT>.jsonl` — validated, source-free core cards (≤ 200 chars per field, zero copied wording or numbers).
- **Committed summaries:** Only original, source-free archetypes and traps enter `math_engine/reasoning_vault/<UNIT>.json`, citing `"source": "OpenStax <Book> §x.y; cores: <families>"`.
