# Learning features plan — status as of 2026-11-20

Source: `pilot/research-2026-11-19/report_th.md` (learner decision 2026-11-19).

**Status:** Phases 1 and 2 are shipped. The Similar strip opens tabs on demand. Template removal is on hold. PR B/C are on hold. Phase 3–5 ideas remain future work and are not active implementation instructions.
Rules that still hold: original answers and steps require a substantive check or explicit Skip. Drill files are content only,
learner state lives in `progress/`, single learner, clean minimal Studio (zinc + indigo, no uppercase).

What already exists (do not rebuild): unit Mastery 0-4 that can fall, Last/Next Review per unit
(`notion_sync.drill_sync` → `scripts.weak_spots.review_update` / `suggest_mastery`); trap signals
(`scripts.weak_spots.trap_status`); per-problem `attempts[]`, `hintsRevealed`, `durationMs` in progress;
math steps include an `explain` line; do not rebuild this capability.

## Phase 1 — Review engine (shipped)
1. **Per-item review schedule** (`scripts/review_items.py` + `practice-studio/src/lib/reviewItems.ts`,
   same rules in both, tested for parity): an item = one problem (drillId/qid) and its trap tag.
   5 levels with intervals 1, 3, 7, 16, 35 days; correct without hint → level+1; correct with hint → same level;
   wrong → level halved (floor, min 1) and due tomorrow. Built from existing `attempts[]` (backfill, no
   migration of drill files). Stored in `progress/review_items.json` (pilot: `pilot/progress/`).
2. **Daily mixed review** page `/review` (Studio): due items across all units and both subjects, interleaved
   (never two in a row from the same unit when avoidable), default 8 items, shows each original problem with
   the normal check flow. A due item stays queued while its review is unfinished, and opening a hint or
   equation set-up still counts as help after a review reset. The first substantive server check or explicit
   Skip updates the schedule for that day. The due list and completion response share the same public metadata. "Due today" links to the page with a count.
3. **Mastery quality**: `suggest_mastery` weights hint depth and time (assisted ≠ fluent) and gates
   Mastery 3 on at least one correct L4+ item with no hint ("challenge"). Studio shows why a unit is
   capped ("needs one L4 challenge without hints").
4. Revisit note: optional one-line "next time I will…" note after a pass; shown first when that item comes back.

## Phase 2 — Variant bank and Similar questions (shipped)
1. **Variant bank** `drills/variants/<UNIT>.json` (content, not learner state): per archetype ≥ 3 verified
   math variants (same archetype + trap, different numbers/context), each with answerSpec, steps, and verify —
   passing the same math ingest gates as drills (`math_engine.ai_drill_ingest --check`).
   Variants are generated through the current gated workflow (blind-solve, reviewer, and originality). Template removal remains on hold.
2. **"Try a similar question" (+)** unlocks after a substantive check or Skip in the current cycle. It
   opens the next variant for the current cycle in bank order (preferring variants never served in earlier
   cycles, then wrapping from the first) and is accented after a wrong, assisted, or skipped answer.
   Opened tabs are scoped to the current cycle (Reset preserves history while clearing the strip until
   **+** is pressed again), and exhaustion resets per cycle. Similar tabs offer full action parity
   (including Skip, self-score, mistake tags, diverged-step flag, and notes) while remaining isolated
   from the original problem score and per-item review schedule.
3. **Worked example of a similar question** after two wrong attempts: shows one bank variant fully solved
   (steps with explain) before the learner retries their own problem. Never the learner's own problem.

## Phase 3 — Prerequisites + diagnostic (on hold)
1. **Prerequisite edges** `curriculum/prerequisites.json` (unit → prerequisite units), drafted from
   curriculum order and unit content, reviewed by Claude; validated (no cycles, codes exist in id_map).
2. **Soft warning** when opening/starting a unit whose prerequisites are due or below Mastery 2.
   On a failed review item, the review page suggests the weakest prerequisite.
3. **Chapter-start diagnostic**: 3-5 bank variants across the chapter's units; result pre-sets a starting
   mastery suggestion or says "can skip U0x" (learner confirms; never auto-writes Notion mastery).

## Phase 4 — PRG features (on hold; PR B/C on hold)
1. **Run with my own input**: input box next to the tests; runs the learner's function in the workspace on
   that input and shows only the output / thrown error (never expected values, never hidden tests).
2. **Second approach after pass**: `altSolutions` per problem (code + complexity + one-line trade-off),
   required by the PRG drill pipeline for new drills and back-filled for existing drills; shown only after pass.
3. **Complexity probe**: per problem an optional `scaleInputs` generator; after pass, time the learner's
   solution at 1x/10x/100x and show the growth curve and a rough class (O(n), O(n log n), O(n²)).
4. **Re-solve in Python**: task type that re-asks a passed JS/TS problem in Python. Deferred until the
   Python track starts (needs Python toolchain in workspaces); design only for now.

## Phase 5 — Visibility and habit (on hold)
1. **Knowledge map** page: Topic → Chapter → Unit graph/tree coloured by mastery and due state, with
   prerequisite edges from Phase 3.
2. **Daily time goal**: total focused minutes per day (Math + PRG share the 3-4 h budget, default goal
   learner-set), weekly view, private streak with 2 "charges" per week so one missed day does not reset it.

## Delivery status
Phases 1–2 are complete. Future phases require a new learner decision before implementation. The previous worker/PR sequence is historical and does not represent active assignments.
