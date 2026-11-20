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
| `SmartMathPro/ข้อสอบเก่า _ <ชุด>/{โจทย์,เฉลย}/` | Thai past exam papers grouped by exam (PAT 1, A-Level ประยุกต์ 1/2, วิชาสามัญ คณิต 1/2, O-NET-style พื้นฐาน) and by chapter (คณิตศาสตร์เพิ่มเติม: เซต … จำนวนเชิงซ้อน … สถิติ), with separate solution files | TH | © SmartMathPro and the original exam bodies (all rights reserved) | `cores` | Richest Thai source: many years of exam items per topic (e.g. `0010_จำนวนเชิงซ้อน`); text-extractable; use `เฉลย` only to confirm the core/trap, never copy solutions; ideas/cores only |
| `illustrative-math/grade6-unit1/*.zip` | Illustrative Mathematics Grade 6 Unit 1 curriculum bundles | EN | CC BY 4.0 (ideas/cores only by our policy) | `cores` | Grade 6 geometry/area conceptual tasks and visual reasoning; ideas/cores only |

## PRG Source Families (under `sources/prg/`)

Fetched 2026-11-20 for the PRG-T00-C03 pilot; licences re-verified with `gh api repos/<owner>/<repo> --jq .license.spdx_id`. REUSE = may adapt with attribution (rewrite; never paste code, identifiers, test names or strings verbatim); extraction still produces source-free core cards.

| Family (under `sources/prg/`) | Upstream | Licence | Allowed use | Coverage |
| :--- | :--- | :--- | :--- | :--- |
| `exercism-typescript/` | github.com/exercism/typescript | MIT | `reuse` | TS exercises with Jest + tsc checks (PRG-T00-C03, T01-C02..C04) |
| `exercism-javascript/` | github.com/exercism/javascript | MIT | `reuse` | JS exercises with tests (PRG-T00-C03, T01-C01, C03..C04) |
| `typescript-exercises/` | github.com/typescript-exercises/typescript-exercises | MIT | `reuse` | Type-level TS drills: narrowing, unions, generics (PRG-T00-C03, T01-C02) |
| `eslint/` (sparse: `docs/src/rules`) | github.com/eslint/eslint | MIT | `reuse` | Incorrect/correct code pairs for find-the-bug & review (PRG-T00-C03, T01-C01, C04) |
| `javascript-questions/` | github.com/lydiahallie/javascript-questions | MIT | `reuse` | Predict-output questions: scope, closures, this, async (PRG-T00-C03, T01-C01) |
| `javascript-koans/` | github.com/mrdavidlaing/javascript-koans | MIT | `reuse` | Fill-in assertions on JS semantics (PRG-T00-C03, T01-C01) |
| `wtfjs/` | github.com/denysdovhan/wtfjs | WTFPL | `reuse` | Coercion and runtime edge-case puzzles (PRG-T00-C03, T01-C01) |

## Policy & Local Layout

- **`scope` families (OpenStax):** Read only table-of-contents and learning-objective pages to set unit scope (`rules/07` §4). Never extract core cards or mine exercises.
- **`cores` families:** Abstract problems into source-free core cards (`sources/_cores/<UNIT>.jsonl`) recording only the mathematical skill, reasoning move, difficulty driver, traps, and format. **Never copy, translate, or paraphrase a source problem, and never reuse its numbers.**
- **Local artifacts (all gitignored under `sources/`):**
  - `sources/_index/` — cached extracted PDF text and per-unit located-page manifests (`located_<UNIT>.json`).
  - `sources/_cores/<UNIT>.jsonl` — validated, source-free core cards (≤ 200 chars per field, zero copied wording or numbers).
- **Committed summaries:** Only original, source-free archetypes and traps enter `math_engine/reasoning_vault/<UNIT>.json`, citing `"source": "OpenStax <Book> §x.y; cores: <families>"`.
