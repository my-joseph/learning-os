# Source Registry

Local raw study materials live under `sources/` in the main checkout (gitignored; override with `LEARNINGOS_SOURCES_DIR`, which defaults to `<main checkout>/sources` even from a git worktree).

For Thai exam PDFs, `scripts.source_find` falls back to page-level OCR when extracted text is empty or shows legacy-font corruption, and caches OCR text plus rendered page images under `sources/_index/`; weak OCR pages are flagged for visual review in the worker prompt. Install the optional local tools with `brew install tesseract tesseract-lang` (including the Thai language data); when either binary is unavailable, indexing continues with a warning and no OCR results.

## Source Families

`Priority` is an integer 0–100 (higher = preferred first during `scripts.source_find --plan`, combined with `docs/source_backlog.md` rank and Thai-exam relevance; `0` = `scope`-only, never selected for extraction).

| Family (under `sources/`) | What it is | Language | Licence / Terms | Allowed use | Priority | Topic coverage notes |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| `openstax/math/<book>/` | OpenStax mathematics textbooks (e.g. Algebra & Trigonometry, Precalculus, Calculus) | EN | CC BY-NC-SA 4.0; OpenStax restricts automated/AI ingestion (`rules/07` §4) | `scope` | `0` | Curriculum baseline TOC and learning objectives across MTH topics; **never mined for exercises** |
| `openstax/cs-physics/...` | OpenStax computer science and physics textbooks | EN | CC BY-NC-SA 4.0; OpenStax restricts automated/AI ingestion (`rules/07` §4) | `scope` | `0` | Curriculum baseline TOC and learning objectives across PHY/CS topics; **never mined for exercises** |
| `SmartMathPro/ข้อสอบเก่า _ <ชุด>/{โจทย์,เฉลย}/` | Thai past exam papers grouped by exam (PAT 1, A-Level ประยุกต์ 1/2, วิชาสามัญ คณิต 1/2, O-NET-style พื้นฐาน) and by chapter (คณิตศาสตร์เพิ่มเติม: เซต … จำนวนเชิงซ้อน … สถิติ), with separate solution files | TH | © SmartMathPro and the original exam bodies (all rights reserved) | `cores` | `100` | Richest Thai source: many years of exam items per topic (e.g. `0010_จำนวนเชิงซ้อน`); text-extractable; use `เฉลย` only to confirm the core/trap, never copy solutions; ideas/cores only |
| `thai-exams/tcas68-a-level/` | Thailand TCAS68 A-Level exam papers (`math1`, `math2`, `phy`, `sci`, `eng`) | TH | © TCAS / CUPT (all rights reserved) | `cores` | `95` | High-school Math 1/2, physics, science, English; 5-option exam formats & trap distractors; ideas/cores only |
| `thai-exams/onet-2568/` | Thailand O-NET 2568 exam papers (P6 / M3 / M6 Math & Science) | TH | © NIETS (all rights reserved) | `cores` | `90` | P6, M3, M6 national math & science exam patterns and multi-choice distractors; ideas/cores only |
| `thai-exams/onet-2566/` | NIETS O-NET M6 Mathematics and Science 2566 public exam PDFs | TH | © NIETS (all rights reserved); PDFs publicly exposed on the official O-NET page | `cores` | `92` | Official M6 exam formats and baseline algebra; source-free core/trap ideas only |
| `thai-exams/onet-2567/` | NIETS O-NET M6 Mathematics sample paper 2567 | TH | © NIETS (all rights reserved); sample PDF publicly exposed on the official O-NET page | `cores` | `88` | M6 sample exam patterns; source-free core/trap ideas only |
| `rathcenter/` | Rath Center public direct-PDF exam archive: PAT 1 and 9-Saman Math 1/2, multiple years | TH | © Rath Center / original exam bodies (all rights reserved); direct PDFs publicly offered in archive; no explicit no-download term observed | `cores` | `96` | PAT 1 and 9-Saman Math papers from B.E. 2559–2563; read papers and embedded solutions only to infer abstract cores/traps; never copy wording, numbers, choices, or solution steps |
| `illustrative-math/grade6-unit1/*.zip` | Illustrative Mathematics Grade 6 Unit 1 curriculum bundles | EN | CC BY 4.0 (ideas/cores only by our policy) | `cores` | `70` | Grade 6 geometry/area conceptual tasks and visual reasoning; ideas/cores only |
| `mathsgenie/Grade_N/{Booklets,Exam_Questions,Solutions}/` | MathsGenie GCSE revision booklets, exam questions, and solutions | EN | Free worksheets, all rights reserved | `cores` | `50` | GCSE Grades 1–9 math fundamentals, algebra, geometry, probability, statistics; ideas/cores only |
| `nzqa-ncea/complex/` | NZQA NCEA Level 3 standard 91577 examinations and paired assessment schedules | EN | CC BY 4.0 | `reuse` | `85` | Complex-number algebra, roots, Argand diagrams, and polar/rectangular forms. Attribute to the New Zealand Qualifications Authority (NZQA), standard 91577; use the schedule only with its matching exam. |
| `libretexts-math/complex/` | Selected LibreTexts complex-number chapters by Ken Kuttler and Leif Jordan | EN | CC BY 4.0 (verified on each page; excludes any separately licensed embedded media) | `reuse` | `75` | Complex-number operations and representations. Attribute Kuttler or Jordan and the LibreTexts page; these selections are not OpenStax text. |
| `mathematics-vision-project/quadratics/` | Mathematics Vision Project Algebra I and Secondary Math II student modules | EN | CC BY 4.0 | `reuse` | `75` | Quadratic functions and solving quadratic equations. Attribute the Mathematics Vision Project and the listed module authors; third-party images retain their own licences. |
| `tyler-wallace-algebra/` | Beginning and Intermediate Algebra by Tyler Wallace | EN | CC BY 3.0 Unported | `reuse` | `70` | Complex numbers, factoring, completing the square, quadratic formula, and quadratic equations. Attribute Tyler Wallace and link to the source book. |

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
- **`no-automation` families:** Never indexed, cached, or extracted automatically by `scripts.source_find` or worker jobs; only individual items provided manually by the learner may be discussed.
- **`cores` families:** Abstract problems into source-free core cards (`sources/_cores/<UNIT>.jsonl`) recording only the abstract skill, reasoning move/archetype kind (including `chain` with ordered `operations` of ≥ 2 distinct taught sub-skills for L2 multi-operation math expressions vs `multi-relation`/`model` for L3+ unstated equations), difficulty driver, traps, and format/QC ideas. **Never copy, translate, or paraphrase a source problem, and never reuse its numbers, code, identifiers, test names, or strings.**
- **`reuse` families (PRG under `sources/prg/`):** Still extracted into source-free PRG core cards (`prg_schema.json`); may include an optional `reuse` block (`{license, attribution, adaptedIdea?}`) when a test idea is adapted (still rewritten from scratch, never pasted).
- **Local artifacts (all gitignored under `sources/`):**
  - `sources/_index/` — cached extracted PDF/code/markdown text (`pdf_*.json`, `code_*.json`), per-unit located manifests (`located_<UNIT>.json`), and budgeted extraction plans (`plan_<UNIT>.json`).
  - `sources/_cores/<UNIT>.jsonl` — validated, source-free core cards (≤ 200 chars per field, zero copied wording, numbers, code, identifiers, test names, or strings).
  - `sources/_cores/_ledger.json` — incremental extraction ledger keyed by `(unit, file, page)` with extraction timestamp, run ID, produced card IDs, and source file SHA-256 hash.
- **Committed summaries:** Only original, source-free archetypes and traps enter `math_engine/reasoning_vault/<UNIT>.json` (`"source": "OpenStax <Book> §x.y; cores: <families>"`; chain archetypes may declare an optional `operations` list) or `code_engine/reasoning_vault/<CHAPTER>.json` (`"source": "docs: <primary doc>; cores: <families>"`).

For progress-free audits, pass `--no-progress` to `scripts.source_gap`. The report still lists bridge candidates and leaves their eligibility unassessed.
