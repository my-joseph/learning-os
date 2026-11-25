---
name: review-drill
description: Coach the learner in polite Thai after a MATH drill — summarize what went well, explain misconceptions and Mistake Log notes in plain language, and give ONE clear next action (plus at most two alternatives) ready for new-math-drill. Use when the learner says "สรุปผล drill <DRILL_ID>", "รีวิว drill <DRILL_ID>", or "review drill <DRILL_ID>".
---

# Review drill

The learner studies alone and needs a calm, short, plain-Thai coach report after finishing (or pausing) a math drill — never raw telemetry dumps, internal IDs, or long technical essays.

Run every command from the repo root with `.venv/bin/python`. This skill is strictly **read-only**: never edit `progress/`, `drills/data/`, or Notion.

## 1. Run the read-only drill review script

```bash
.venv/bin/python -m scripts.drill_review <DRILL_ID> --json
```

`scripts/drill_review.py` honours `PROGRESS_DIR` and `LEARNINGOS_PILOT` via `progress_store.py`.
- `mistakes` includes checker-added tags from the current cycle and any learner-selected tags.
- If the drill ID is missing or not found, say so plainly in Thai and stop.
- If the ID is a programming drill or lab (`DRL-PRG-*` or `LAB-*`), refuse clearly in Thai and tell the learner to use `review-code` (`"ตรวจโค้ด <DRILL_ID> <QID>"` or `"ตรวจโค้ด <LAB_ID> M1"`) instead, then stop.
- If `totals.attemptedCount == 0` (`practiceStatus == "Not started"`), tell the learner in 2–3 polite Thai lines that this drill has not been attempted yet (`0/<problemCount>` ข้อ) and recommend opening it in Practice Studio first instead of writing an empty review.

Check the learner's Notion **My Implementation & Mistake Log** section **only** if an existing read-only tool supports reading it. Today `notion_sync/unit_page.py` `--snapshot` omits `"My Implementation & Mistake Log"` by design (`rules/02_pedagogy.md` §7a), and no existing read-only CLI reads section 6 from Notion — so do not make ad-hoc Notion API calls; rely on `mistakeNote`, `revisitNote`, and `mistakes` from the script output.

## 2. Translate findings into short, plain coaching language

- **Keep it SHORT:** Aim for **≤ 20 lines** total (hard maximum ~30 lines).
- **Zero-leak & no worked values:** Never reveal prompts, answers, worked steps, `checkpointHint`, or `display` set-up of any item. Do **not** restate the correct answer or a worked value of an item the learner got wrong — explain the misconception generally in one plain sentence and send them to Similar variants.
- **Zero internal tokens in the learner text:** Do **not** put any internal IDs, keys, tags, backticks, JSON, or parameter blocks in the Thai reply — no `archetypeKey`, no `trapTag`, no drill/unit codes, no rule names like `retry_similar_then_targeted`, and no `Q01` lists beyond plain Thai `"ข้อ 1, 3, 5"`. Translate skills and traps into natural Thai using `archetypeName`, `coreConcept`, and `description` from the JSON output (when `hasVaultDescription` is `false`, explain the mathematical meaning of the tag in plain Thai rather than repeating the English label).
- **Reconcile schedule vs. live evidence:** Use the live `unitContext.mastery` and `unitContext.masteryCap` (which prefer live `evidenceMastery` over a stale `_review_schedule.json` cap when the learner just completed an unassisted L4 challenge in local practice).
- **Keep parameters internal until requested:** Hold `recommendation.primary.params` (and `recommendation.alternatives[].params`: `unit`, `archetypes`, `levels`, `count`, `focusTags`) internally; pass them to `.claude/skills/new-math-drill/SKILL.md` only when the learner replies **"สร้างเลย"**.

## 3. Reply structure (Thai, ≤ 20 lines target, max ~30 lines)

Use these concise sections (with **no backticks, no internal IDs/tags/rule names, and no JSON/parameter dumps**):

1. **ภาพรวม** (2–3 lines) — คะแนนรวมและเปอร์เซ็นต์ (ถ้ายังทำไม่ครบชุดให้บอกความแม่นยำของข้อที่ทำแล้วควบคู่กับจำนวนข้อที่ค้าง), เวลาที่ใช้, จำนวนข้อที่ถูกทันที / ใช้ตัวช่วย / ผิด / ข้าม / ยังไม่ได้ทำ, ระดับความเชี่ยวชาญของบทพร้อมเหตุผลที่ติดเพดานแบบภาษาคน (ถ้ามี) และวันทบทวนถัดไป
2. **ทำได้ดี** (≤ 3 bullets) — สรุปกลุ่มข้อและทักษะที่ทำถูกทันทีโดยไม่พึ่งตัวช่วยเป็นภาษาไทยสั้นๆ (อ้างอิงเป็น `"ข้อ 1, 2"`)
3. **พลาดเพราะอะไร** (≤ 3 bullets) — แต่ละ bullet เขียนในรูปแบบ **"ชื่อทักษะภาษาไทย (ข้อ ...) — ความเข้าใจผิดหรือสาเหตุที่พึ่งตัวช่วย/ข้าม ใน 1 ประโยคภาษาคนเข้าใจง่าย"** (ห้ามเฉลยคำตอบหรือค่าจากการคำนวณของข้อที่ผิด; ถ้าเป็นกับดักซ้ำข้ามชุดฝึกให้บอกว่าเป็นจุดที่พลาดซ้ำ แนะนำหัวข้อบนหน้าบทเรียนที่ควรอ่านทบทวน และบอกว่าต้องทำชุดฝึกเจาะจุดอ่อนให้ผ่านแบบไม่ใช้ตัวช่วยติดกัน 2 ชุดเพื่อปิดจุดอ่อน; ถ้าเป็นข้อที่ข้ามให้ชี้แนวคิดพื้นฐานที่ต้องกลับไปทบทวน)
4. **Mistake Log** (1–2 lines; **ตัดหัวข้อนี้ออกทันทีถ้าผู้เรียนไม่ได้เขียนโน้ต**) — สรุปโน้ตที่ผู้เรียนจดไว้ใน Studio สั้นๆ 1–2 บรรทัด (ไม่ต้องมีหัวข้อนี้เลยถ้าไม่มีโน้ต)
5. **ทำอะไรต่อ** —
   - แผนหลัก **1 อย่างใน 1 ประโยค** + **เหตุผล 1 ประโยค** (เช่น ให้กลับไปกดทำโจทย์คล้าย Similar ของข้อที่พลาดแบบไม่เปิดคำใบ้ หรือให้อ่านทบทวนหน้าบทเรียนแล้วสร้างชุดฝึกใหม่)
   - **ทางเลือก:** ไม่เกิน 2 ข้อ ข้อละ 1 บรรทัดสั้นๆ
   - ปิดท้ายสั้นๆ ว่าหากต้องการให้สร้างชุดฝึกตามแผนหรือทางเลือกไหน ให้ตอบว่า **"สร้างเลย"** (เมื่อผู้เรียนตอบ "สร้างเลย" ค่อยส่งพารามิเตอร์ที่เก็บไว้ภายในไปยังสกิล `new-math-drill`)

## 4. Never

- Reveal answers, worked values, worked steps, or hidden hints of missed or unattempted problems.
- Include internal IDs (`t02-c01-...`, `DRL-...`, `MTH-...`), `trapTag`s, rule names (`retry_similar_then_targeted`), `Q01` tokens, backticks, JSON, or parameter lists in the learner-facing report.
- Include an empty Mistake Log section when the learner wrote no notes.
- Write to `progress/`, `drills/data/`, or Notion.
- Invent recommendations that contradict `scripts/drill_review.py` `recommendation`.

## Final documentation check

- [ ] If this PR changes system behaviour, the matching `rules/*.md`, `docs/*.md`, `CLAUDE.md` and skills are updated in the same PR.

## Self-review

After the run, compare the outcome against this skill's goal. For each friction (unclear step, missing tool, gate miss, rework, reviewer catch, or learner correction), log `.venv/bin/python -m scripts.issues propose --target skill:review-drill --evidence "<what happened>" --proposal "<concrete change>"` (or `.venv/bin/python -m scripts.issues add --kind <kind> --severity batch --source author --where <where> --what "<what>" --target skill:review-drill`). If the fix is a small, scoped edit to this `SKILL.md`, make it in the same PR.
