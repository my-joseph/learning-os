# Source Registry

Local raw study materials live under `sources/` in the main checkout (gitignored; override with `LEARNINGOS_SOURCES_DIR`, which defaults to `<main checkout>/sources` even from a git worktree).

## Source Families

`Priority` is an integer 0–100 (higher = preferred first during `scripts.source_find --plan`, combined with `docs/source_backlog.md` rank and Thai-exam relevance; `0` = `scope`-only, never selected for extraction).

| Family (under `sources/`) | What it is | Language | Licence / Terms | Allowed use | Priority | Topic coverage notes |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| `openstax/math/<book>/` | OpenStax mathematics textbooks (e.g. Algebra & Trigonometry, Precalculus, Calculus) | EN | CC BY-NC-SA 4.0; OpenStax restricts automated/AI ingestion (`rules/07` §4) | `scope` | `0` | Curriculum baseline TOC and learning objectives across MTH topics; **never mined for exercises** |
| `openstax/cs-physics/...` | OpenStax computer science and physics textbooks | EN | CC BY-NC-SA 4.0; OpenStax restricts automated/AI ingestion (`rules/07` §4) | `scope` | `0` | Curriculum baseline TOC and learning objectives across PHY/CS topics; **never mined for exercises** |
| `SmartMathPro/ข้อสอบเก่า _ <ชุด>/{โจทย์,เฉลย}/` | Thai past exam papers grouped by exam (PAT 1, A-Level ประยุกต์ 1/2, วิชาสามัญ คณิต 1/2, O-NET-style พื้นฐาน) and by chapter (คณิตศาสตร์เพิ่มเติม: เซต … จำนวนเชิงซ้อน … สถิติ), with separate solution files | TH | © SmartMathPro and the original exam bodies (all rights reserved) | `cores` | `100` | Richest Thai source: many years of exam items per topic (e.g. `0010_จำนวนเชิงซ้อน`); text-extractable; use `เฉลย` only to confirm the core/trap, never copy solutions; ideas/cores only |
| `thai-exams/tcas68-a-level/` | Thailand TCAS68 A-Level exam papers (`math1`, `math2`, `phy`, `sci`, `eng`) | TH | © TCAS / CUPT (all rights reserved) | `cores` | `95` | High-school Math 1/2, physics, science, English; 5-option exam formats & trap distractors; ideas/cores only |
| `thai-exams/onet-2568/` | Thailand O-NET 2568 exam papers (P6 / M3 / M6 Math & Science) | TH | © NIETS (all rights reserved) | `cores` | `90` | P6, M3, M6 national math & science exam patterns and multi-choice distractors; ideas/cores only |
| `illustrative-math/grade6-unit1/*.zip` | Illustrative Mathematics Grade 6 Unit 1 curriculum bundles | EN | CC BY 4.0 (ideas/cores only by our policy) | `cores` | `70` | Grade 6 geometry/area conceptual tasks and visual reasoning; ideas/cores only |
| `mathsgenie/Grade_N/{Booklets,Exam_Questions,Solutions}/` | MathsGenie GCSE revision booklets, exam questions, and solutions | EN | Free worksheets, all rights reserved | `cores` | `50` | GCSE Grades 1–9 math fundamentals, algebra, geometry, probability, statistics; ideas/cores only |

## Policy & Local Layout

- **`scope` families (OpenStax):** Read only table-of-contents and learning-objective pages to set unit scope (`rules/07` §4). Never extract core cards or mine exercises.
- **`cores` families:** Abstract problems into source-free core cards (`sources/_cores/<UNIT>.jsonl`) recording only the mathematical skill, reasoning move, difficulty driver, traps, and format. **Never copy, translate, or paraphrase a source problem, and never reuse its numbers.**
- **Local artifacts (all gitignored under `sources/`):**
  - `sources/_index/` — cached extracted PDF text, per-unit located-page manifests (`located_<UNIT>.json`), and budgeted extraction plans (`plan_<UNIT>.json`).
  - `sources/_cores/<UNIT>.jsonl` — validated, source-free core cards (≤ 200 chars per field, zero copied wording or numbers).
  - `sources/_cores/_ledger.json` — incremental extraction ledger keyed by `(unit, file, page)` with extraction timestamp, run ID, produced card IDs, and source file SHA-256 hash.
- **Committed summaries:** Only original, source-free archetypes and traps enter `math_engine/reasoning_vault/<UNIT>.json`, citing `"source": "OpenStax <Book> §x.y; cores: <families>"`.
