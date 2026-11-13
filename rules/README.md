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
| **Curriculum Design & Content Authoring** | `rules/00_core.md`<br>`rules/02_pedagogy.md` | Reference structure, Active Recall toggles, 4-tier Practice Guides (no problem dumps), Feynman workspace |
| **Mathematics & Physics (`MTH`, `PHY`)** | `rules/00_core.md`<br>`rules/03_stem.md` | Vertical LaTeX derivations (`\begin{aligned}`), KaTeX formatting, Parametric SVG Diagrams, native Notion file uploads |
| **Programming Drills & Labs (`PRG`)** | `rules/00_core.md`<br>`rules/04_code.md` | 100% VS Code execution mandate, Dual-Engine evaluation (Tests + AI Review), 4 Real-World Archetypes, 5-tier milestone taxonomy, terminal telemetry (`submit_lab.py`) |
| **Verification, Audit & Delivery** | `rules/00_core.md`<br>`rules/05_qa.md` | 5-dimension QA checklist, scripted Notion API audit (`unlinked = 0`), reporting protocol |
| **Problem Templates & Quality Gates** | `rules/00_core.md`<br>`rules/06_template_contract.md` | L1–L4 taxonomy, trap provenance & operational derivations, machine verification gates G1–G6, verification levels, reporting protocol |
| **Drill Composition & Problem Generation** | `rules/00_core.md`<br>`rules/07_problem_generation.md` | Drill composition (sequence of drills), weak-spot targeting (`trapMatched` signals), progression rules, AI-written problem verification (V1–V3) |

---

## Local-First & Auto-Sync Protocol

1. **Local Markdown Files (`rules/*.md`)** serve as the primary **Source of Truth** for AI agent operations, offering:
   - Zero network latency (`< 1ms` local file read)
   - Zero API rate limits or connection reset risks
   - 3–4x higher token density compared to Notion JSON block structures
   - Full Git version control and rollback history
2. **Notion Child Pages** serve as the clean, human-readable presentation layer in the Notion workspace.
3. **Auto-Sync:** Run `python3 -m notion_sync.rules_sync` (add `--dry-run` to preview) from the repo root to synchronize any local rule modifications directly to Notion.
