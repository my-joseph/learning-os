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

### 8. Spaced Review Properties & Intervals
Where available in the database, use:
- `Mastery (0–4)`
- `Last Reviewed`
- `Next Review`

Do not create duplicate properties if equivalent properties already exist. Review scheduling should respond dynamically to the learner's current Mastery:
- Mastery 1: 1–2 days
- Mastery 2: 4–7 days
- Mastery 3: 14–21 days
- Mastery 4: 30–60 days
*(These intervals are starting guidelines, not inflexible rules).*

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
