# 01_ARCH — Learning Architecture, Database Relations & Progress Tracking

**Module Code:** `RULES-ARCH`  
**Applies To:** Notion database schemas, properties, relations, page hierarchies, and progress tracking  
**Prerequisite:** Must adhere to `rules/00_core.md`  

---

## PART 1 — Three-Level Learning Hierarchy

The Learning System enforces three primary learning levels:

### 1. Topic
Represents an overall subject, learning track, or major learning goal. Its content should explain:
- What the Topic is about.
- Why it matters.
- Overall learning goals.
- Measurable learning outcomes.
- Related Chapters and their progress.
- Learning sequence and dependencies.
- Relevant Resources.
- Overall review and reflection.

### 2. Chapter
Represents a major learning section within a Topic. Its content should explain:
- The Chapter's role within its parent Topic.
- Chapter objectives and expected competencies.
- Important concepts and relationships.
- Related Units and their learning sequence.
- Prerequisites and dependencies where relevant.
- Relevant Resources.
- Suitable practice and review activities.

### 3. Unit
Represents an individual concept, skill, or learning objective. Its content should explain:
- The specific concept or skill.
- Core explanations and important details.
- Examples, demonstrations, diagrams, or code where appropriate.
- Practical exercises and application.
- Active Recall questions.
- Completion criteria.
- Mastery and review guidance.

---

## PART 2 — Relationships, Completeness & Mentions

### 4. Hierarchy & Relationship Invariants
Maintain the strict hierarchy:
$$\text{Topic} \longrightarrow \text{Chapters} \longrightarrow \text{Units}$$
- Resources must be connected to the relevant learning levels through existing relations.
- Do not create or infer relationships without evidence.

### 5. Property & Resource Relation Completeness Rule
When inspecting a Topic, Chapter, Unit, or Resource, always evaluate all database properties (such as `Goal`, `Objective`, `Completion Criteria`, `Learning Objective`, `Expected Output`, `Sources`, and `Resources` relations) to determine whether empty fields should be populated.
- If a Topic, Chapter, or Unit references a source (e.g., via the `Sources` property or an unlinked row in `Learning Resources`), AI must ensure the `Learning Resources` entry has complete metadata (`Resource title`, `Resource ID`, `Type`, `Topic / Area`, `URL`, `Key Notes`, `Last Reviewed`) and must link the `Resources` relation across all relevant levels (`Topic ↔ Resource`, `Chapters ↔ Resource`, `Units ↔ Resource`).

### 6. Inline Page Mention & Link Verification Rule
Whenever page content references any record ID that exists in the workspace (`Topic ID`, `Chapter ID`, `Unit ID`, `Full ID`, or `Resource ID` — such as [[MTH-T01-C08]], [[PHY-T01-C19]], [[PRG-T01-C02-U03]], or [[R012]]), AI must insert a clickable Notion page mention (`mention` of type `page`) rather than plain text.
- **Verify All Inline Mentions Render Properly:** Ensure that page mentions inside bold headings, callouts, and nested list items are properly tokenized as Notion `mention` objects and never left as raw double-bracketed IDs.
- Always inspect the saved page blocks after generation to confirm zero unresolved link tokens remain (`unlinked = 0`).

---

## PART 3 — Learning Progress & Mastery (Two Dimensions)

### 7. Separate Learning Progress from Mastery
The system tracks two distinct dimensions that must never be conflated:

#### Learning Progress — `Status`
`Status` represents progress through initial learning. Use the existing `Status` options and their established meanings:
- `Not started`
- `In progress`
- `Pending Review`
- `Done`
*Do not use `Status` to represent long-term memory retention.*

#### Knowledge Mastery — `Mastery (0–4)`
`Mastery` represents the learner's current ability to recall, explain, and apply knowledge independently:
- **0 — Unranked / No Recall:** Not yet tested or completely unable to retrieve.
- **1 — Familiar:** Requires heavy prompting; recognizes terms but cannot derive or write independently.
- **2 — Competent with Guidance:** Solves standard textbook problems; occasional calculation or syntax slip.
- **3 — Autonomous & Fluent:** Rapidly solves unseen problems; correctly identifies edge cases and traps.
- **4 — Mastered / Intuitive:** Effortless recall, explains first principles simply (Feynman), synthesizes across subjects.

*Mastery must be assessed through actual recall and application, not familiarity alone. A Unit may remain `Done` even when its `Mastery` decreases over time. Do not change `Status` simply because the learner has forgotten previously learned material.*

### 7a. Scoring contract
The scoring rule is specified authoritatively in [`docs/studio_design.md`](../docs/studio_design.md), **“Scoring rule”**, and implemented by `practice-studio/src/lib/scoring.ts` and `progress_store.score_problem`. Apply these outcomes to the current cycle only:
- First-try clean correct: `1.0`.
- Otherwise-correct (retry, help, or partial credit): `0.5`.
- Wrong or skipped: `0`.
- PRG work awaiting review: `null` until a review supplies a score.
- Lock an item after a correct check. Reset starts a new cycle at `cycleStartedAt` and retains prior history.
- Self-score may only lower an automatic score; it cannot raise a wrong/skipped result.
- Marking a diverged step adds a note only and does not change the score.

When wording here and the named scoring rule differ, use the authoritative scoring rule and update this summary in the same documentation change.

### 8. Spaced Review Properties & Intervals
Where available in the database, use:
- `Mastery (0–4)`
- `Last Reviewed`
- `Next Review`

Do not create duplicate properties if equivalent properties already exist. The current evidence-based unit schedule is 2 / 5 / 17 / 45 days for Mastery 1 / 2 / 3 / 4 respectively. This unit-level schedule is separate from the per-item schedule in §9a.

### 9. Spaced Review Workflow
A review session should follow this sequence:
1. Recall without opening notes.
2. Explain the concept in the learner's own words.
3. Apply the knowledge through an exercise or example.
4. Check notes and Resources.
5. Identify forgotten or misunderstood concepts.
6. Update `Mastery`.
7. Update `Last Reviewed`.
8. Schedule `Next Review`.

The Review Queue view should surface Units whose `Next Review` date is due.

`[code]` Drill practice updates these automatically: when a drill with an attempt is synced, `notion_sync.drill_sync.update_unit_reviews` writes, for every unit the drill covers, an evidence-based `Mastery (0–4)` from the learner's last 10 items in that unit (`scripts.weak_spots.evaluate_mastery` / `suggest_mastery(..., return_cap=True)` and `review_update`: 1 under 50%; 3 when at least 3 recent L3+ items average ≥ 70%, no weak spot is open, and the unit has at least one correct L4+ item with no hint ("challenge"); otherwise 2), `Last Reviewed` = the attempt date, and `Next Review` = attempt date + 2 / 5 / 17 / 45 days for Mastery 1 / 2 / 3 / 4. Assisted items (hints, equation set-up, or solution steps revealed before answering) are weighted at half of fluent items (`0.5` vs `1.0`) and never qualify as the L4+ challenge, capping Mastery at 2 and returning a cap reason so Practice Studio can display why a unit is capped. Drills cannot show Mastery 4 (Feynman explanation, cross-subject synthesis): only the learner sets 4, and a learner-set 4 is kept while the evidence still says 3.

### 9a. Per-item review engine
Unit Mastery in Notion (§8–9) and the per-item review engine are two separate review layers. Do not replace one schedule with the other.

The per-item engine is implemented in `scripts/review_items.py` and `practice-studio/src/lib/reviewItems.ts`; parity is checked by `practice-studio/tests/reviewItemsParity.test.ts`. It stores item-level schedules in `progress/review_items.json` (pilot: `pilot/progress/review_items.json`) and uses five levels with intervals of **1 / 3 / 7 / 16 / 35 days**. Correct without help advances one level, correct with help keeps the level, and wrong halves the level (floor, minimum 1) and makes the item due tomorrow.

The engine orders due work by priority, supports interleaving and the Daily Review `cycleStartedAt`, and isolates variants from the original item's score and review item. It also supports the current review scopes and bridge items. Item-level schedule state stays in `review_items.json` / progress storage; it is not the Notion unit Mastery property or the unit cache `progress/_review_schedule.json`.
