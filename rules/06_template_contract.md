# 06_TEMPLATE_CONTRACT — Problem Template & Quality Gate Engineering Contract

**Module Code:** `RULES-TEMPLATE-CONTRACT`  
**Applies To:** Math & Code Problem Templates, Quality Gates G1–G6, Checker Parsers, Taxonomy & Verification  
**Priority:** Mandatory for adding, modifying, or auditing problem templates  
**Linked From:** `rules/00_core.md` (Part 1, Section 1), `rules/02_pedagogy.md` (Part 4)

---

## 1. การเพิ่มหัวข้อและโครงสร้างเทมเพลต (Adding Units & Templates)

### 1.1 ไฟล์ที่ต้องสร้าง/แก้ไข (Touchpoints)
เมื่อเพิ่มหัวข้อหรือทักษะใหม่ ต้องสร้าง/แก้ **2 ส่วนเท่านั้น** (ระบบมี Auto-discovery):
1. **Module เทมเพลต**: ใน `math_engine/templates/<module_name>.py` หรือ `code_engine/templates/<module_name>.py`
   - ต้องประกาศ `UNIT` (รหัส unit เช่น `"MTH-VECTORS"`), `TITLE`, `CHAPTER_CODE`, `TOPIC_CODE`, `MISTAKE_TAGS`, และ `TEMPLATES`
   - ระบบ `math_engine.templates` และ `code_engine.templates` จะค้นพบโมดูลที่มีตัวแปร `TEMPLATES` อัตโนมัติ โดยไม่ต้องไปฮาร์ดโค้ด register ในไฟล์อื่น
2. **Taxonomy ทักษะ**: ใน `skills_taxonomy.json`
   - เพิ่ม skill entry ภายใต้ key `skills` ระบุ `name`, `domain`, `tier`, `prerequisites` (ระบุ `skill` และ `strength`: `"hard"` หรือ `"soft"`), และ `g2_profile`

### 1.2 โครงสร้างมาตรฐานของ `TEMPLATES`
```python
TEMPLATES = [
    {
        "key": "vector-magnitude",
        "level": 1,
        "skill": "VEC-MAGNITUDE",
        "verificationLevel": "machine-verified",
        "forms": {
            "magnitude": {
                "level": 1,
                "skill": "VEC-MAGNITUDE",
                "trapTag": "magnitude-distribute-sqrt",
            },
            "unit-vector": {
                "level": 2,
                "skill": "VEC-MAGNITUDE",
                "trapTag": "unit-vector-forgot-magnitude",
            },
            "flaw-distribute-sqrt": {
                "level": 3,
                "skill": "VEC-MAGNITUDE",
                "trapTag": "magnitude-distribute-sqrt",
            },
        },
        "build": t_vector_magnitude,
    }
]
```

### 1.3 กฎของโจทย์เขียนโค้ดและ Workspace Deep Links (Coding Kata Workspace Contract)
สำหรับโจทย์ประเภทเขียนโค้ด (`codeType` เป็น `kata`, `implement`, `refactor` หรือมี `visibleTests`/`starterCode`):
1. **การสร้าง Workspace บนดิสก์**: ต้องเรียก `code_engine.workspace.materialize_drill_workspace` เพื่อสร้างโครงสร้าง `drills/workspace/<DRILL_ID>/` ที่มี `package.json`, `README.md`, ซอร์สโค้ดเริ่มต้น และไฟล์เทสต์
2. **Metadata Deep Links ระดับโฟลเดอร์ vs ไฟล์เดี่ยว**:
   - **ระดับโฟลเดอร์ (Folder-Level)**: ต้องระบุ `workspaceDir` (Absolute Path), `vscodeFolderUrl` (`vscode://file/<abs_ws>`), และ `cursorFolderUrl` (`cursor://file/<abs_ws>`)
   - **ระดับไฟล์ (File-Level)**: ต้องระบุ `workspaceFile` (Path ไฟล์), `vscodeUrl` (`vscode://file/<abs_src>`), และ `cursorUrl` (`cursor://file/<abs_src>`)
3. **Invariants ห้ามละเมิด**:
   - ปุ่มหลัก "Open in VS Code" / "Open in Cursor" ในหน้า Practice Studio **ต้องเปิดโฟลเดอร์ Workspace เสมอ** (`vscodeFolderUrl`) ห้ามชี้หรือ fallback เป็นไฟล์เดี่ยว เพื่อให้ VS Code ตรวจพบ `package.json`, แสดงแผง NPM Scripts, และเปิด Terminal ถูก Directory ทันที
   - การเปิดไฟล์เดี่ยว (`vscodeUrl`) อนุญาตให้เป็นปุ่มรอง "Open File" เท่านั้น

---

## 2. นิยามระดับ L1–L4, Tier และ `g2_profile` (Levels vs Tiers)

> [!IMPORTANT]
> **ความสัมพันธ์กับกรอบการเรียนรู้หลัก:**
> - **Pedagogy Reference**: ดูนิยามขอบเขตการฝึกตามระดับหลักสูตรใน [rules/02_pedagogy.md](file:///Users/Joseph/Documents/antigravity/brave-borg/rules/02_pedagogy.md#L87-L113) (Part 4: Multi-Level Practice Guides) และระดับความชำนาญใน [rules/01_arch.md](file:///Users/Joseph/Documents/antigravity/brave-borg/rules/01_arch.md#L78-L86) (`Mastery (0-4)`)
> - **Template Usage**: ในระบบเทมเพลตปัจจุบัน ฟิลด์ `level` (L1–L4) ถูกนำมาใช้กำหนด **ชนิดงานทางพุทธิปัญญา (Cognitive Task Type)** ของโจทย์ในแต่ละ `form` เพื่อควบคุมจำนวน steps และโครงสร้างของโจทย์ผ่าน `g2_profile` ใน `skills_taxonomy.json`
> - **Tier**: ใน `skills_taxonomy.json` (`foundational`, `intermediate`, `advanced`, `expert`) บ่งบอกลำดับความลึกขององค์ความรู้ในหลักสูตร ไม่ผูกขาดกับ Level เดียว

| Level | Cognitive Task Type ในเทมเพลต | ลักษณะโครงสร้าง | ขอบเขต Steps ใน G2 (ค่าเริ่มต้น) |
| :---: | :--- | :--- | :---: |
| **L1** | **Direct Computation / Recall** | คำนวณตรงไปตรงมาตามสูตรหรือนิยามแกนหลัก ไม่ซับซ้อน | 1–3 steps |
| **L2** | **Reverse Solve / Multi-step Synthesis** | แก้สมการย้อนหาพารามิเตอร์ หรือคำนวณแปลงค่าหลายขั้น | 2–4 steps |
| **L3** | **Trap, Flaw Diagnosis & Edge Cases** | วิเคราะห์จุดผิดพลาด (Find-the-Flaw) หรือกับดักเชิงแนวคิด | 2–5 steps (ต้องมี trap/flaw ที่ตรวจได้จริง) |
| **L4** | **Applied / Multi-concept Constraint** | นำไปประยุกต์ข้ามโดเมน หรือมีเงื่อนไขบังคับหลายด้าน | 2–6 steps (ต้องมี >= 2 concepts หรือเงื่อนไขเสริม) |

### 2.1 กฎห้าม Silent Fallback ระดับความยาก (Strict Difficulty Level Invariant)
เมื่อผู้เรียนหรือระบบสั่งเจเนอเรตโจทย์โดยระบุระดับความยากแบบเจาะจง (`difficulty in ('1', '2', '3', '4')`):
1. **ห้ามมี Silent Fallback เด็ดขาด**: หากยูนิตนั้นยังไม่มีเทมเพลตที่รองรับระดับความยากดังกล่าว ตัว Generator (`math_engine.generate` และ `code_engine.generate`) **ต้อง raise `ValueError` แสดงรายชื่อระดับความยากที่ยูนิตนั้นมีจริงทันที** ห้ามแอบ fallback ไปสุ่มหยิบโจทย์ระดับอื่นมาแทนโดยเด็ดขาด
2. **ป้ายหัวไฟล์ต้องตรงกับโจทย์จริง**: ทุกข้อในชุดโจทย์ (`problems`) ต้องมี `prob["level"]` ตรงกับค่า `config.difficulty` ที่ระบุเสมอ ห้ามให้มีโจทย์เลเวลอื่นหลุดเข้าไปในชุดโจทย์ที่ระบุเลเวลเฉพาะ

---

## 3. กฎของกับดักและการวินิจฉัยจุดผิด (Trap Provenance & Flaw Diagnosis)

1. **ผูกกับขั้นตอนที่แตกต่าง**: `trapTag` และ `trapValue` ต้องสะท้อนจุดสะดุดทางความคิดที่เป็นธรรมชาติของมนุษย์ (Distractor Provenance) ไม่ใช่การสุ่มตัวเลขมั่ว
2. **การแยกฟิลด์ในโจทย์หาจุดผิด (Choice/Flaw Questions)**:
   - **`flawTag`**: คือข้อผิดพลาดในขั้นตอนแสดงวิธีทำที่โจทย์ต้องการให้ผู้เรียนตรวจจับ (Underlying Derivation Flaw)
   - **`trapTag` ในตัวเลือก (`options`)**: คือข้อผิดพลาดเชิงมโนทัศน์ของผู้เรียนเองเมื่อเลือกตัวเลือกหลอกข้อนั้น (Learner Distractor Misconception)
   - **บันทึก telemetry**: เมื่อผู้เรียนตอบผิด ระบบต้องบันทึก mistake tag จาก `trapTag` ของตัวเลือกที่ผู้เรียนเลือก ไม่ใช่หยิบ `commonTrapTag` รวมมาทับ
3. **คำอธิบายขั้นตอนของโจทย์หาจุดผิด (Step Explanations in Find-the-Flaw)**:
   - บรรทัดที่ชี้ข้อผิดพลาด (flaw step) **ต้องแสดง LaTeX ของบรรทัดที่นักเรียนทำผิด** (ตรงกับที่ปรากฏใน `display`) ตามด้วยบรรทัดที่ถูกต้องและเหตุผลทางคณิตศาสตร์
4. **กฎคำใบ้สำหรับโจทย์ระดับ L3 (Process-Oriented Hints for L3 Flaw)**:
   - `checkpointHint` สำหรับโจทย์หาจุดผิด **ห้ามระบุตำแหน่งหรือประเภทข้อผิดพลาดเด็ดขาด** (เช่น ห้ามใช้คำว่า `distribute`, `inner derivative`, `sign`, `Line 2`, `second step`)
   - ต้องเป็นคำใบ้เชิงกระบวนการ (Process Hint) เท่านั้น เช่น: *"Work through the derivation step-by-step on scratch paper, then compare your solution line by line with the student's work to identify where they diverge."*

---

## 4. เกณฑ์คุณภาพด่าน G1–G6 (Quality Gates Specification)

| Gate | ชื่อด่าน | เกณฑ์การผ่าน | ตัวอย่างกรณีที่ตก (Failure Examples) |
| :---: | :--- | :--- | :--- |
| **G1** | Archetype Integrity & Anti-Leak | 1. โค้ด/คณิตตรง archetype<br>2. คำใบ้ (`inputHint`, `checkpointHint`) **ห้ามรั่วเฉลย**<br>3. โจทย์ L3 flaw คำใบ้ต้องเป็นเชิงกระบวนการ ห้ามสปอยล์ตำแหน่งหรือคีย์เวิร์ดข้อผิด | - `checkpointHint` เขียนว่า `$(1+2i)^2 = -3+4i$` เมื่อเฉลยคือ `2i`<br>- ใส่ตัวอย่างคำตอบใน `inputHint` ตรงกับเฉลย<br>- คำใบ้โจทย์ L3 บอกว่า *"Check line 2 for missing inner derivative"* |
| **G2** | Level-Structure Alignment | จำนวน steps และโครงสร้าง trap/flaw ต้องตรงกับ Level และ `g2_profile` | - โจทย์ L3 แต่ไม่มี `verify.flaw` หรือไม่มี `trapValue`<br>- โจทย์ L1 แต่เขียนยาว 5 steps เกินเพดาน |
| **G3** | Diversity & Non-Duplication | 1. กระจาย form ทั่วถึงใน 1 drill set<br>2. สุ่ม 200 เมล็ด ห้ามได้ fingerprint ซ้ำเกินโควตา | - สุ่มโจทย์ 20 ข้อแต่ได้โครงเดิมซ้ำกัน 15 ข้อ<br>- แม่พิมพ์เดิมเปลี่ยนแค่ตัวเลข |
| **G4** | Distractor Provenance & Trap Validity | 1. `trapValue != answerPlain` เสมอ<br>2. สำหรับโจทย์ Choice: ตัวเลือกหลอกทุกตัวต้องมี `trapTag` และที่มา | ตัวเลือกหลอกเป็นตัวเลขสุ่มที่ไม่มีความหมายทางการเรียนรู้ หรือ `trapValue` เท่ากับเฉลย |
| **G5** | Audit Mode (Batch Quality Audit) | โหมดสแกนตรวจสอบไฟล์ drill JSON ที่มีอยู่ทั้งหมดใน `drills/data/` แบบ non-destructive (`math_engine/audit.py`) โดยแยกข้อผิดจริงออกจาก legacy missing fields<br>*(หมายเหตุ: การ Dual Verification ระหว่าง SymPy กับตัวเลขจะถูกตรวจสอบก่อนบันทึกใน generator)* | ไฟล์ drill เก่ามีโครงสร้างคำตอบผิดรูป หรือคำตอบเฉลยไม่ตรงกับที่ระบุในไฟล์ |
| **G6** | Mathematical Typography | ไม่มีเครื่องหมายซ้อนหรือสัญลักษณ์ที่ไม่เรียบร้อยในฟิลด์ที่ผู้เรียนเห็น | มี `+ -`, `- -`, `+-`, `--`, `^1`, `x^0`, `*1`, `1x` ใน latex |

---

## 5. คำสั่งทดสอบและกติกาความปลอดภัยของระบบไฟล์ (CLI & Test Isolation)

### 5.1 ชุดคำสั่งหลัก
- **ทดสอบความพร้อมเทมเพลต**: `python -m scripts.accept_template <key> [--seeds 200]`
- **ตรวจรายงานทุกเทมเพลต**: `python -m scripts.accept_template --all` (แยกกลุ่ม Regression vs Backlog)
- **สุ่มดูตัวอย่างโจทย์ทุกฟอร์ม**: `python -m scripts.sample_sheet <key>`
- **สร้างรายงานครอบคลุม**: `python -m scripts.coverage_report`
- **รันชุดทดสอบทั้งหมด**: `python -m unittest discover tests -v`
- **สแกนโหมด Audit (G5)**: `python -m math_engine.audit`
- **สร้างชุดแบบฝึกหัด (Generate Drills)**:
  - ทั่วไป: `python -m math_engine.generate --unit <UNIT_CODE> --count <N>`
  - กรองเฉพาะเทมเพลต: `python -m math_engine.generate --unit <UNIT_CODE> --templates <tpl1,tpl2> --count <N>`
  - เจาะจงฝึกจุดอ่อน (Focus Tag): `python -m math_engine.generate --unit <UNIT_CODE> --focus-tag <tag_name> --count <N>`
  - ระหว่างสถานะนำร่อง (Pilot): `ENABLE_PILOT_DRILLS=1 python -m math_engine.generate --unit <UNIT_CODE> --count <N>`
  - คำสั่งทดสอบแบบปลอดภัย (Dry-run / Isolation): `DRILLS_DATA_DIR=$(mktemp -d) NOTION_DRY_RUN=1 python -m math_engine.generate --unit <UNIT_CODE> --count <N>`
- **การปลดสถานะนำร่อง (Graduating Unit out of Pilot)**:
  - แก้ในไฟล์โมดูลเทมเพลต (`math_engine/templates/<module>.py` หรือ `code_engine/templates/<module>.py`): เปลี่ยน `IS_PILOT = True` เป็น `IS_PILOT = False` (หรือลบตัวแปร `IS_PILOT` ออก)

### 5.2 กติกาความปลอดภัยของระบบไฟล์ (Filesystem Safety)
> [!CAUTION]
> **ห้ามเขียนทับข้อมูลจริงจากชุดเทสต์โดยเด็ดขาด**
> 1. การทดสอบการเจนโจทย์ ต้องชี้ `DRILLS_DATA_DIR` ไปยัง `tempfile.TemporaryDirectory()` ห้ามเขียนลง `drills/data/` จริง
> 2. การทดสอบ Notion ต้องเปิดแฟล็ก `NOTION_DRY_RUN=1` เสมอ ห้ามยิง API หรือสร้างบล็อกบนฐานข้อมูลจริง
> 3. เทสต์ที่เรียก `coverage_report` (เช่น `test_16`) ต้องส่งพารามิเตอร์ `output_path` ไปยังโฟลเดอร์ชั่วคราว ห้ามเขียนทับ `reports/coverage.md`

---

## 6. กติกาความปลอดภัยของ Parser (Safe Parse Security Invariants)

1. **นโยบาย Whitelist ฟังก์ชันทางคณิตศาสตร์**:
   - `WHITELIST_FUNCS` ส่วนกลางใน `math_engine/answer_check.py` ถูกจำกัดไว้เฉพาะฟังก์ชันคณิตศาสตร์มาตรฐาน ได้แก่:
     `sqrt`, `sin`, `cos`, `tan`, `ln`, `log`, `exp`, `abs`, `Abs`, `re`, `im`, `conjugate`
   - **ห้ามเพิ่มฟังก์ชันพีชคณิตเชิงสัญลักษณ์/แคลคูลัสขั้นสูง** เช่น `diff`, `integrate`, `solve`, `limit` ลงใน `WHITELIST_FUNCS` เด็ดขาด เพื่อป้องกันผู้เรียนพิมพ์คำสั่งให้โปรแกรมแคลคูลัสหาคำตอบแทน
   - หากโจทย์ต้องการตัวแปร ให้ส่งผ่าน `variables=["x"]` ประจำโจทย์
2. **นโยบายจำกัดเลขชี้กำลัง (Bounded Exponent Policy)**:
   - **Internal/Trusted Path**: สตริงภายในระบบที่ผ่านการตรวจสอบแล้ว กำหนดเพดานที่ $\le 1000$ (`trusted=True`)
   - **User Input: Imaginary Base ($i^N$)**: ลดโมดูโล 4 ได้ใน $O(1)$ กำหนดเพดานที่ $\le 1000$
   - **User Input: Numeric Constant Base ($2^N$)**: จำกัดตามขนาดผลลัพธ์ กำหนดเพดานที่ $\le 1000$
   - **User Input: Symbolic Base ($(x+1)^N$)**: การกระจายพจน์แบบพหุนามกินหน่วยความจำแบบ exponential กำหนดเพดานเข้มงวดที่ $\le 100$
   - การยกกำลังซ้อน (`9**9**9`, `(9**9)**9`) และตัวเลขเกินเพดานต้องถูกตัดสิทธิ์ด้วย `invalid input` เสมอ

---

## 7. เช็กลิสต์การเพิ่ม `answerSpec` ชนิดใหม่ (New Answer Types Checklist)

เมื่อต้องการเพิ่มชนิดคำตอบใหม่ (เช่น `vector`, `matrix`) ต้องปรับปรุงครบทั้ง **7 จุดทางวิศวกรรม** ดังนี้:
1. **`math_engine/answer_spec_registry.py`**: ลงทะเบียนชนิดคำตอบใน `ANSWER_SPEC_REGISTRY` กำหนด schema ฟิลด์บังคับ และ parser handler
2. **`math_engine/answer_check.py`**: เพิ่มฟังก์ชันตรวจสอบเฉพาะ (เช่น `check_vector`), ระบบ normalizer วงเล็บ, diagnostics แบบ deterministic ที่จำกัดเวลา timeout, และ dispatch ใน `check_answer()`
3. **`math_engine/verify.py`**: เพิ่มการตรวจเฉลยกับ `verify.source` (รองรับทั้ง SymPy analytical และ fallback เชิงตัวเลข)
4. **`quality_rules.py`**: อัปเดตด่าน G1 (Anti-Leak component extraction), G2, G4, และ G6 ให้รองรับโครงสร้าง spec ใหม่
5. **`practice-studio/src/types/drill.ts`**: ประกาศ TypeScript interface สำหรับ `AnswerSpec` และชนิดตัวแปรใหม่ให้ตรงกัน
6. **`practice-studio/src/components/MathProblemCard.tsx`**: เพิ่มคอมโพเนนต์สำหรับรับค่า (Input Box / Bracket layout) และ placeholder
7. **`tests/test_quality_gates.py`**: เพิ่ม unit test สำหรับ comparator, parser bounds, edge cases, unicode normalization, และ template round-trip

---

## 8. เช็กลิสต์สำหรับผู้ตรวจสอบ `sample_sheet` (Human Review Checklist)

ก่อนอนุมัติเทมเพลตใหม่ ให้รัน `python -m scripts.sample_sheet <key>` แล้วตรวจด้วยสายตา:
- [ ] **วิธีคิดต่างจริงไหม**: แต่ละ `form` ต้องมีขั้นตอนการคิดและกลยุทธ์ที่ต่างกัน ไม่ใช่แค่เปลี่ยนชื่อตัวแปร
- [ ] **กับดักเป็นของจริงไหม**: `trapValue` และ `trapTag` เป็นข้อผิดพลาดที่ผู้เรียนทำบ่อยจริงหรือไม่
- [ ] **โจทย์หาจุดผิด (L3)**:
  - Step ที่ระบุบรรทัดผิดต้องแสดง LaTeX ของบรรทัดผิดของนักเรียน ก่อนตามด้วยบรรทัดที่ถูกและเหตุผล
  - `checkpointHint` ต้องเป็นเชิงกระบวนการ ไม่มีคำสปอยล์ประเภทข้อผิด (`distribute`, `inner derivative`, `sign`) หรือตำแหน่ง (`Line 2`)
  - ฟิลด์ `flawTag` แยกชัดเจนจาก `trapTag` ของตัวเลือกหลอก
- [ ] **ระดับตรงตามพุทธิปัญญาไหม**: L1 (ตรงตัว), L2 (ย้อนกลับ/หลายขั้น), L3 (จับผิด/กับดัก), L4 (ประยุกต์)
- [ ] **Prerequisite ไม่วนลูป**: ตรวจสอบว่าความสัมพันธ์ใน DAG ไม่เกิด Cycle (`test_18` ผ่าน)
- [ ] **ไม่มีเครื่องหมายซ้อน**: ดูข้อความ Latex ว่าไม่มี `+ -`, `--`, หรือฟอร์แมตขยะ

---

## 9. กติกาการรายงานงาน (Reporting Protocol)

1. **รายงานเฉพาะสิ่งที่ทำจริงในรอบนั้น**: ระบุรายชื่อไฟล์ที่แก้ไขเฉพาะรอบปัจจุบัน
2. **ห้ามผ่อน Threshold เงียบๆ**: เกณฑ์ทั้งหมด (G1/G2/G4/G6 $\ge 98.0\%$, retries $\le 12$, timeout) ต้องคงเดิม
3. **แยกข้อเท็จจริงชัดเจน**: แยกส่วนระหว่าง **"รันตรวจเองตอนนี้"** (มีผลรันดิบยืนยัน) กับ **"อ่านจากโค้ด/ไม่ได้รันตรวจ"**
4. **ความกระชับ**: รายงานผลสรุปให้ตรงประเด็น ไม่เยิ่นเย้อ
