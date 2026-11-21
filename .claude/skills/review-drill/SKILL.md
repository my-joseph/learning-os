---
name: review-drill
description: Coach the learner in polite Thai after a MATH drill — summarize what went well, explain misconceptions and Mistake Log notes in plain language, and give ONE clear next action (plus at most two alternatives) ready for new-math-drill. Use when the learner says "สรุปผล drill <DRILL_ID>", "รีวิว drill <DRILL_ID>", or "review drill <DRILL_ID>".
---

# Review drill

The learner studies alone and needs a calm, honest coach after finishing (or pausing) a math drill — not raw telemetry dumps and not a menu of ten choices. Talk to the learner in polite Thai; keep explanations concrete and encouraging.

Run every command from the repo root with `.venv/bin/python`. This skill is strictly **read-only**: never edit `progress/`, `drills/data/`, or Notion.

## 1. Run the read-only drill review script

```bash
.venv/bin/python -m scripts.drill_review <DRILL_ID> --json
```

`scripts/drill_review.py` honours `PROGRESS_DIR` and `LEARNINGOS_PILOT` via `progress_store.py`. If the drill ID is missing, say so plainly in Thai and stop.

Check the learner's Notion **My Implementation & Mistake Log** section **only** if an existing read-only tool supports reading it. Today `notion_sync/unit_page.py` `--snapshot` omits `"My Implementation & Mistake Log"` by design (`rules/02_pedagogy.md` §7a), and no existing read-only CLI reads section 6 from Notion — so do not make ad-hoc Notion API calls; rely on `mistakeNote`, `revisitNote`, and `mistakes` from the script output and note this clearly in the report.

## 2. Translate findings into plain coaching language

- **Zero-leak invariant:** Never reveal prompts, answers, worked steps, `checkpointHint`, or `display` set-up of any item not yet answered correctly (and keep answers/steps out of the summary altogether).
- **No unexplained internal IDs:** Whenever you refer to an `archetypeKey`, `trapTag`, or `mistakes[]` category, explain what skill or misconception it means in plain Thai words using `archetypeName` and `description` from the JSON output.
- **Keep recommendations deterministic:** Present `recommendation.primary` as the ONE clear immediate action (**ทำทันที**), and `recommendation.alternatives` (at most 2) as **ทางเลือก**. Cite the evidence (`why`) and concrete `params` (`unit`, `archetypes`, `levels`, `count`, and `focusTags` if present).

## 3. Reply structure (Thai)

Write a short, concrete report with these five sections:

1. **ภาพรวม** — คะแนนรวม (`totalScore`/`maxScore`, `accuracyPct`%), เวลาที่ใช้, จำนวนข้อที่ทำถูกทันที / ใช้ตัวช่วยหรือทำซ้ำ / ผิด / ข้าม / ยังไม่ได้ทำ, ระดับ `Mastery` ปัจจุบันของบท (พร้อมเหตุผลที่ติด cap ถ้ามี) และวันทบทวนถัดไป (`nextReview`)
2. **จุดที่ทำได้ดี** — ทักษะ/ระดับที่ทำถูกทันทีโดยไม่พึ่งตัวช่วย (ระบุข้อและทักษะเป็นภาษาคน; ถ้ายังไม่ผ่านข้อไหน ให้ชื่นชมความพยายามหรือจุดที่ทำได้จริงโดยไม่พูดเกินจริง)
3. **จุดที่พลาดและสาเหตุ** — สรุปข้อที่ผิด ข้าม หรือพึ่งตัวช่วยมาก (hint/set-up/steps) พร้อมอธิบายกับดัก (`matchedTraps`) ด้วยภาษาง่ายๆ ว่าสับสนตรงไหน ถ้ามีกับดักซ้ำข้ามหลาย drill ให้ชี้ชัดและระบุหัวข้อบนหน้า Unit page สำหรับทบทวน; สำหรับข้อที่ข้าม (`skipped`) ให้ชี้แนวคิดพื้นฐานที่ต้องกลับไปปูใหม่โดยไม่เฉลยคำตอบ
4. **จาก Mistake Log** — สรุปโน้ตที่ผู้เรียนบันทึกไว้ (`mistakeNote` / `revisitNote`) และหมวด `mistakes` (ระบุให้ชัดว่าอ่านจากบันทึกใน Studio เพราะเครื่องมืออ่านหน้า Notion แบบ read-only ในระบบข้าม section 6 ตามกฎ `rules/02_pedagogy.md` §7a)
5. **ทำอะไรต่อ (ทำทันที / ทางเลือก)** —
   - **ทำทันที:** 1 แผนหลักจาก `recommendation.primary` (บอกเหตุผล + พารามิเตอร์ `unit`, `archetypes`, `levels`, `count`, `focusTags` แบบชัดเจน)
   - **ทางเลือก:** ไม่เกิน 2 ทางจาก `recommendation.alternatives` (ถ้ามี)
   - ปิดท้ายด้วยการถามผู้เรียนสั้นๆ ว่าอยากให้ **"สร้างเลย"** หรือไม่ — ถ้าผู้เรียนตอบ `"สร้างเลย"` ให้ส่งพารามิเตอร์ที่เลือกต่อไปยังสกิล `.claude/skills/new-math-drill/SKILL.md` เพื่อสร้าง drill ชุดถัดไป (หรือถ้าแผนหลักคือการทำ Similar / ข้อที่ค้าง / Daily Review ใน Studio ให้แนะนำให้ทำตามนั้นก่อน และเสนอ `"สร้างเลย"` สำหรับชุดเจาะจุดอ่อน/อัปเลเวลต่อ)

## 4. Never

- Reveal answers, worked steps, or hidden hints of unattempted or missed problems.
- Write to `progress/`, `drills/data/`, or Notion.
- Invent recommendations that contradict `scripts/drill_review.py` `recommendation`.
- Dump raw internal IDs (`t02-c01-...`) without plain Thai meaning.

## Final documentation check

- [ ] If this PR changes system behaviour, the matching `rules/*.md`, `docs/*.md`, `CLAUDE.md` and skills are updated in the same PR.

## Self-review

After the run, compare the outcome against this skill's goal. For each friction (unclear step, missing tool, gate miss, rework, reviewer catch, or learner correction), log `.venv/bin/python -m scripts.issues propose --target skill:review-drill --evidence "<what happened>" --proposal "<concrete change>"` (or `.venv/bin/python -m scripts.issues add --kind <kind> --severity batch --source author --where <where> --what "<what>" --target skill:review-drill`). If the fix is a small, scoped edit to this `SKILL.md`, make it in the same PR.
