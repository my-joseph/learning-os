# Learning System — AI Implementation Rules (Modular System)

**Document Type:** Central Rule Architecture  
**Purpose:** Modular implementation rules for AI and autonomous engineering workflows  
**Applies To:** Learning Topics, Chapters, Learning Units, Resources, Practice Drills, Labs, and Database Schemas  
**Priority:** Mandatory inspection before any implementation task  

---

## Architecture Overview: Local-First & Modular Context Injection

To prevent context window bloat and instruction dilution, the Learning System rules are organized into decoupled, specialized modules. AI agents must selectively load only the module relevant to their immediate task, rather than loading the entire rulebook.

### Task-to-Module Routing Matrix

| Task / Activity | Required Rule Modules | Key Invariants Covered |
| :--- | :--- | :--- |
| **All Tasks (Universal)** | `rules/00_core.md` | Scope protection, source of truth, user content preservation, English-only mandate, Git hygiene & version control |
| **Database, Relations & Schema** | `rules/00_core.md`<br>`rules/01_arch.md` | Topic ➔ Chapter ➔ Unit hierarchy, property completeness, `@page` mentions, Status vs. Mastery (0–4) |
| **Practice Studio UI, scoring & review** | `rules/00_core.md`<br>`rules/01_arch.md`<br>`docs/studio_design.md` | Studio interaction and visual rules; scoring contract; Notion unit Mastery and per-item review schedules |
| **Post-drill coaching & review (`MTH`)** | `rules/00_core.md`<br>`rules/01_arch.md`<br>`rules/07_problem_generation.md` | Read-only post-drill diagnosis, zero-leak coaching, deterministic next-action rules (`review-drill`, `scripts/drill_review.py`) |
| **Curriculum Design & Content Authoring** | `rules/00_core.md`<br>`rules/02_pedagogy.md` | Reference structure, Active Recall toggles, 4-tier Practice Guides (no problem dumps), Feynman workspace |
| **Mathematics & Physics (`MTH`, `PHY`)** | `rules/00_core.md`<br>`rules/03_stem.md` | Vertical LaTeX derivations (`\begin{aligned}`), KaTeX formatting, Parametric SVG Diagrams, native Notion file uploads |
| **Programming Drills & Labs (`PRG`)** | `rules/00_core.md`<br>`rules/04_code.md`<br>`rules/07_problem_generation.md` | Local IDE workflow, three-layer evaluation (Tests + Lint/Types + Rubric Review), 5 archetypes, 5-tier milestone taxonomy |
| **Verification, Audit & Delivery** | `rules/00_core.md`<br>`rules/05_qa.md` | 5-dimension QA checklist, scripted Notion API audit (`unlinked = 0`), reporting protocol |
| **System Health Audit** | `rules/00_core.md`<br>`rules/05_qa.md` | Read-only automated and worker audits, ranked fix planning (`health-check`) |
| **Area Improvement Roadmap** | `rules/00_core.md`<br>Area-specific playbook in `.claude/skills/improve/areas/` | One-area deep assessment, verified phased roadmap, learner approval, small implementation PRs (`improve <area>`) |
| **Quality Gates / Template Contract (legacy; removal on hold)** | `rules/00_core.md`<br>`rules/06_template_contract.md` | L1–L5 levels, trap provenance & operational derivations, verification gates G1–G6, answer-type safety checklist |
| **Sources and synthesis** | `rules/00_core.md`<br>`rules/07_problem_generation.md`<br>`docs/sources.md` | Source registry, core-card synthesis, attribution, and originality checks |
| **Variants and bridge drills** | `rules/00_core.md`<br>`rules/01_arch.md`<br>`rules/07_problem_generation.md` | Variant bank, item isolation, bridge eligibility, scope, and authoring |
| **Drill Composition & Problem Generation** | `rules/00_core.md`<br>`rules/07_problem_generation.md` | Drill composition, weak-spot targeting (`trapMatched` signals), progression rules, AI-written problem verification (V1–V3) |
| **Drill Quality from Practice Evidence** | `rules/00_core.md`<br>`rules/07_problem_generation.md` | Per-archetype/level learner outcomes, trap and level coverage (`drill-quality`) |

---

## Local-Only Rules

1. **Local Markdown Files (`rules/*.md`)** are the canonical source for agent operating rules and are maintained in Git.
2. **No Notion copy:** rules are **not** synced to Notion (retired 2026-11-13; nobody read them there). Edit `rules/*.md` and commit; that is the whole workflow. Any old rule pages left in Notion are stale and must never be used as a reference. The retired sync code is in `archive/rules_sync.py`.
