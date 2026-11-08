"""Unit tests for Quality Gates G1, G2, G3, G4, Audit Mode G5, and Generator Retry Logic."""

from __future__ import annotations

import copy
import glob
import json
import os
import shutil
import tempfile
import unittest

from code_engine.answer_check import check_answer as code_check_answer
from code_engine.generate import generate_drill_set as generate_code_drill_set
from code_engine.verify import verify_problem as verify_code_problem
from math_engine.answer_check import check_answer as math_check_answer
from math_engine.audit import run_audit
from math_engine.generate import generate_drill_set as generate_math_drill_set
from math_engine.verify import verify_problem as verify_math_problem
from quality_rules import (
    QualityError,
    check_gate_g1,
    check_gate_g2,
    check_gate_g3_set,
    check_gate_g4,
    check_gate_g6,
    generate_with_quality_retries,
)


class TestQualityGates(unittest.TestCase):
    """Tests for the 4 Quality Gates + Audit Mode + Generator Retries."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._orig_drills_data_dir = os.environ.get("DRILLS_DATA_DIR")
        cls._orig_notion_dry_run = os.environ.get("NOTION_DRY_RUN")
        os.environ["NOTION_DRY_RUN"] = "1"
        cls._tmp_dir = tempfile.TemporaryDirectory()
        base_files = sorted([f for f in glob.glob("drills/data/**/*.json", recursive=True) if "MTH-CALC-DIFF" not in f])
        for src_path in base_files:
            rel = os.path.relpath(src_path, "drills/data")
            dst_path = os.path.join(cls._tmp_dir.name, rel)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copyfile(src_path, dst_path)
        os.environ["DRILLS_DATA_DIR"] = cls._tmp_dir.name

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp_dir.cleanup()
        if cls._orig_drills_data_dir is not None:
            os.environ["DRILLS_DATA_DIR"] = cls._orig_drills_data_dir
        else:
            os.environ.pop("DRILLS_DATA_DIR", None)
        if cls._orig_notion_dry_run is not None:
            os.environ["NOTION_DRY_RUN"] = cls._orig_notion_dry_run
        else:
            os.environ.pop("NOTION_DRY_RUN", None)

    def test_1_prg_q02_tcp_handshake_labeled_code_tracing_fails_g1(self) -> None:
        """Test 1: Q02 in DRL-PRG-T00-C01-U01-01.json (TCP handshake labeled code-tracing) MUST fail G1."""
        data_dir = os.environ.get("DRILLS_DATA_DIR", "drills/data")
        path = os.path.join(data_dir, "PRG-T00-C01-U01", "DRL-PRG-T00-C01-U01-01.json")
        with open(path, "r", encoding="utf-8") as f:
            drill = json.load(f)

        q02 = next(p for p in drill["problems"] if p["id"] == "Q02")
        self.assertEqual(q02["archetype"], "code-tracing")

        with self.assertRaises(QualityError) as ctx:
            verify_code_problem(copy.deepcopy(q02))

        self.assertEqual(ctx.exception.gate, "G1")
        self.assertEqual(ctx.exception.problem_id, "Q02")
        self.assertIn("recall", str(ctx.exception))

        # Verify that relabeling a conceptual question to 'recall' (and removing predict-output) passes G1
        fixed_q02 = copy.deepcopy(q02)
        fixed_q02["archetype"] = "recall"
        fixed_q02["codeType"] = "recall"
        res_g1 = check_gate_g1(fixed_q02, is_code=True)
        self.assertTrue(res_g1["passed"])

    def test_2_mth_q01_and_q02_duplicate_skeleton_fails_g3(self) -> None:
        """Test 2: Q01 and Q02 in DRL-MTH-T01-C12-04.json (90-37 vs 180-124) MUST fail G3 in same set/form."""
        data_dir = os.environ.get("DRILLS_DATA_DIR", "drills/data")
        path = os.path.join(data_dir, "MTH-T01-C12-U03", "DRL-MTH-T01-C12-04.json")
        with open(path, "r", encoding="utf-8") as f:
            drill = json.load(f)

        q01 = copy.deepcopy(next(p for p in drill["problems"] if p["id"] == "Q01"))
        q02 = copy.deepcopy(next(p for p in drill["problems"] if p["id"] == "Q02"))
        q01["form"] = "direct"
        q02["form"] = "direct"

        with self.assertRaises(QualityError) as ctx:
            check_gate_g3_set([q01, q02])

        self.assertEqual(ctx.exception.gate, "G3")
        self.assertEqual(ctx.exception.problem_id, "Q02")
        self.assertIn("Q01", str(ctx.exception))
        self.assertEqual(q01["fingerprint"], q02["fingerprint"])

    def test_3_level3_with_1_step_and_no_trap_fails_g2(self) -> None:
        """Test 3: A problem labeled L3 with 1 step and no trap MUST fail G2."""
        fake_l3_prob = {
            "id": "Q99",
            "category": "Core Skill",
            "level": 3,
            "prompt": "Find $2 + 3$.",
            "display": "2 + 3",
            "plainText": "2 + 3",
            "answerSpec": {"type": "number", "value": "5"},
            "answerDisplay": "5",
            "answerPlain": "5",
            "inputHint": "Enter integer",
            "checkpointHint": "Add the two integers.",
            "steps": [
                {"latex": "2 + 3 = 5", "explain": "Add 2 and 3.", "val": "5"},
            ],
            "verify": {"source": "5"},
        }

        with self.assertRaises(QualityError) as ctx:
            verify_math_problem(fake_l3_prob)

        self.assertEqual(ctx.exception.gate, "G2")
        self.assertEqual(ctx.exception.problem_id, "Q99")
        self.assertIn("L3", str(ctx.exception))

    def test_4_trap_value_equal_to_correct_answer_fails_g4(self) -> None:
        """Test 4: A problem where trapValue equals the correct answer MUST fail G4."""
        bad_trap_prob = {
            "id": "Q04",
            "form": "direct",
            "category": "Core Skill",
            "level": 1,
            "prompt": "Find the hypotenuse of a right triangle with legs $3$ and $4$.",
            "display": "c = \\sqrt{3^2 + 4^2}",
            "plainText": "sqrt(3^2 + 4^2)",
            "answerSpec": {"type": "number", "value": "5", "forms": ["exact"]},
            "answerDisplay": "5",
            "answerPlain": "5",
            "inputHint": "Enter integer",
            "checkpointHint": "3^2 + 4^2 = 25.",
            "commonTrapTag": "pythagoras-hypotenuse",
            "steps": [
                {"latex": "c = \\sqrt{3^2 + 4^2}", "explain": "Substitute legs.", "val": "5"},
                {"latex": "= \\sqrt{25} = 5", "explain": "Take square root.", "val": "5"},
            ],
            # Trap value mistakenly set to 5 (same as correct answer!)
            "verify": {"source": "5", "trapValue": "5"},
        }

        with self.assertRaises(QualityError) as ctx:
            verify_math_problem(bad_trap_prob)

        self.assertEqual(ctx.exception.gate, "G4")
        self.assertEqual(ctx.exception.problem_id, "Q04")

        # Also test MCQ distractor missing provenance / duplicating correct option fails G4
        bad_mcq = {
            "id": "Q05",
            "level": 1,
            "answerSpec": {
                "type": "choice",
                "options": [
                    {"id": "A", "label": "53"},
                    {"id": "B", "label": "143"},
                    {"id": "C", "label": "37"},
                ],
                "correct": "A",
            },
            "answerPlain": "A",
        }
        with self.assertRaises(QualityError) as ctx_mcq:
            check_gate_g4(bad_mcq)
        self.assertEqual(ctx_mcq.exception.gate, "G4")

    def test_5_valid_problems_and_generators_pass_all_gates(self) -> None:
        """Test 5: Valid problems in Math & Code generators pass G1-G4 and check_answer round-trip."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 1. Generate Math MTH-T01-C12 drill set
            mth_geo = generate_math_drill_set(
                unit_code="MTH-T01-C12",
                count=5,
                difficulty="ALL",
                seed=42,
                data_root=tmp_dir,
            )
            self.assertEqual(len(mth_geo["problems"]), 5)
            for p in mth_geo["problems"]:
                self.assertIn("form", p)
                self.assertIn("fingerprint", p)
                self.assertIn("qualityGates", p)
                self.assertTrue(p["qualityGates"]["G1"]["passed"])
                self.assertTrue(p["qualityGates"]["G2"]["passed"])
                self.assertTrue(p["qualityGates"]["G3"]["passed"])
                self.assertTrue(p["qualityGates"]["G4"]["passed"])
                chk = math_check_answer(p["answerSpec"], p["answerPlain"])
                self.assertEqual(chk["verdict"], "correct")

            # 2. Generate Math MTH-T02-C01-U01 drill set
            mth_cx = generate_math_drill_set(
                unit_code="MTH-T02-C01-U01",
                count=8,
                difficulty="ALL",
                seed=101,
                data_root=tmp_dir,
            )
            self.assertEqual(len(mth_cx["problems"]), 8)
            for p in mth_cx["problems"]:
                self.assertTrue(p["qualityGates"]["G1"]["passed"])
                self.assertTrue(p["qualityGates"]["G2"]["passed"])
                self.assertTrue(p["qualityGates"]["G3"]["passed"])
                self.assertTrue(p["qualityGates"]["G4"]["passed"])
                chk = math_check_answer(p["answerSpec"], p["answerPlain"])
                self.assertEqual(chk["verdict"], "correct")

            # 3. Generate Code PRG-T01-C01 drill set (code-tracing & debugging)
            prg_js = generate_code_drill_set(
                unit_code="PRG-T01-C01",
                count=5,
                difficulty="ALL",
                seed=77,
                data_root=tmp_dir,
            )
            self.assertEqual(len(prg_js["problems"]), 5)
            for p in prg_js["problems"]:
                self.assertTrue(p["qualityGates"]["G1"]["passed"])
                self.assertTrue(p["qualityGates"]["G2"]["passed"])
                self.assertTrue(p["qualityGates"]["G3"]["passed"])
                self.assertTrue(p["qualityGates"]["G4"]["passed"])
                chk = code_check_answer(p["answerSpec"], p["answerPlain"])
                self.assertEqual(chk["verdict"], "correct")

    def test_6_retry_exhaustion_reports_most_frequent_gate(self) -> None:
        """Test that 12 failed retries raise QualityError reporting the most frequent failing gate."""
        calls = 0

        def _always_fails_g2(seed: int):
            nonlocal calls
            calls += 1
            raise QualityError("G2", "Q01", f"Simulated G2 failure on seed={seed}")

        with self.assertRaises(QualityError) as ctx:
            generate_with_quality_retries(_always_fails_g2, base_seed=100)

        self.assertEqual(calls, 12)
        self.assertEqual(ctx.exception.gate, "G2")
        self.assertIn("12 ครั้ง", str(ctx.exception))
        self.assertIn("G2", str(ctx.exception))

    def test_7_audit_mode_does_not_modify_existing_files(self) -> None:
        """Test G5 audit mode scans all consolidated drill files, separating actual from legacy missing fields."""
        data_dir = os.environ.get("DRILLS_DATA_DIR", "drills/data")
        actual, legacy, c_act, c_leg, n_files, n_probs = run_audit(data_dir)
        self.assertEqual(n_files, 28)
        self.assertEqual(n_probs, 226)
        # Actual violations: G1 (archetype mismatch) and G2 (step count / flaw mismatch)
        self.assertGreater(c_act["G1"], 0)
        self.assertGreater(c_act["G2"], 0)
        # Legacy missing fields: G3 (missing form) and G4 (missing trapValue)
        self.assertGreater(c_leg["G3"], 0)
        self.assertGreater(c_leg["G4"], 0)

    def test_8_skills_taxonomy_minimal_schema_and_registration(self) -> None:
        """Test 8: skills_taxonomy.json contains valid minimal schema with all 36 skills."""
        from quality_rules import load_skills_taxonomy
        taxonomy = load_skills_taxonomy("skills_taxonomy.json")
        self.assertGreaterEqual(len(taxonomy), 36)

        required_domains = {"geometry", "complex_numbers", "javascript_core", "software_architecture"}
        domains_found = set()

        for skill_id, s in taxonomy.items():
            self.assertIn("domain", s, f"{skill_id} missing domain")
            self.assertIn("tier", s, f"{skill_id} missing tier")
            self.assertIn("prerequisites", s, f"{skill_id} missing prerequisites")
            self.assertIsInstance(s["prerequisites"], list)
            self.assertIn("g2_profile", s, f"{skill_id} missing g2_profile")
            domains_found.add(s["domain"])

            # Verify g2_profile has ranges for levels
            for lv_str in ("1", "2", "3", "4"):
                self.assertIn(lv_str, s["g2_profile"])
                prof = s["g2_profile"][lv_str]
                self.assertIn("min_steps", prof)
                self.assertIn("max_steps", prof)
                self.assertLessEqual(prof["min_steps"], prof["max_steps"])

        self.assertTrue(required_domains.issubset(domains_found))

    def test_9_per_form_level_and_skill(self) -> None:
        """Test 9: Template declares level and skill per form; scheduler sets active form level/skill."""
        from math_engine.templates.mth_t01_c12 import TEMPLATES
        pyth_tpl = next(t for t in TEMPLATES if t["key"] == "pythagoras-hypotenuse")
        self.assertIsInstance(pyth_tpl["forms"], dict)
        self.assertEqual(pyth_tpl["forms"]["direct"]["level"], 1)
        self.assertEqual(pyth_tpl["forms"]["direct"]["skill"], "GEO-RIGHT-TRIANGLE-HYP")
        self.assertEqual(pyth_tpl["forms"]["reverse"]["level"], 2)
        self.assertEqual(pyth_tpl["forms"]["reverse"]["skill"], "GEO-RIGHT-TRIANGLE-LEG")
        self.assertEqual(pyth_tpl["forms"]["contextual"]["level"], 2)
        self.assertEqual(pyth_tpl["forms"]["contextual"]["skill"], "GEO-RIGHT-TRIANGLE-APPLIED")

    def test_10_g2_profile_step_ranges_and_l3_trap_retention(self) -> None:
        """Test 10: G2 reads step range from skill profile and strictly enforces L3 trap requirement."""
        # Problem using PRG-ARCH-PROJECT-RATE-LIMITER (profile allows up to 8 steps at L4)
        prob_l4_long = {
            "id": "Q01",
            "level": 4,
            "skill": "PRG-ARCH-PROJECT-RATE-LIMITER",
            "archetype": "project-based",
            "codeType": "project-based",
            "starterCode": "class Limiter {}",
            "solutionCode": "class Limiter { hit() {} }",
            "visibleTests": [{"id": "t1", "name": "t1", "testCode": "1"}],
            "hiddenTests": [{"id": "t2", "name": "t2", "testCode": "2"}],
            "references": ["PRG-T01-C03-U04", "PRG-T01-C03-U05"],
            "steps": [{"latex": f"step {i}", "explain": f"explain {i}"} for i in range(7)],
        }
        res_g2 = check_gate_g2(prob_l4_long)
        self.assertTrue(res_g2["passed"])
        self.assertEqual(res_g2["stepRange"], (2, 8))

        # L3 problem with 3 steps but missing trap/flaw MUST fail G2
        prob_l3_no_trap = {
            "id": "Q02",
            "level": 3,
            "skill": "GEO-CYLINDER-VOLUME-RADIUS",
            "category": "Core Skill",
            "steps": [{"latex": f"step {i}", "explain": f"explain {i}"} for i in range(3)],
        }
        with self.assertRaises(QualityError) as ctx:
            check_gate_g2(prob_l3_no_trap)
        self.assertEqual(ctx.exception.gate, "G2")
        self.assertIn("trap/flaw/debug", str(ctx.exception))

    def test_11_scheduler_round_robin_and_skill_cells(self) -> None:
        """Test 11: Scheduler round-robins across (template, form), covering all 9 skill cells in MTH-T01-C12."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            drill = generate_math_drill_set(
                unit_code="MTH-T01-C12",
                count=20,
                difficulty="ALL",
                seed=42,
                data_root=tmp_dir,
            )
            problems = drill["problems"]
            self.assertEqual(len(problems), 20)

            skill_cells = set((p["templateKey"], p["form"], p.get("commonTrapTag")) for p in problems)
            # All 9 available (template, form, trapTag) combinations in MTH-T01-C12 must be present
            self.assertEqual(len(skill_cells), 9)

            for p in problems:
                self.assertIn("skill", p)
                self.assertIn("form", p)
                self.assertEqual(p["verificationLevel"], "machine-verified")
                self.assertEqual(p["qualityGates"]["verificationLevel"], "machine-verified")

    def test_12_accept_template_standard_and_kata_exemption(self) -> None:
        """Test 12: accept_template evaluates standard templates and respects kata exemptions."""
        from scripts.accept_template import evaluate_template
        from math_engine.templates.mth_t01_c12 import TEMPLATES as MTH_TPLS
        from code_engine.templates.prg_t01_c03 import TEMPLATES as PRG_TPLS

        pyth_tpl = next(t for t in MTH_TPLS if t["key"] == "pythagoras-hypotenuse")
        res_pyth = evaluate_template("MTH-T01-C12", pyth_tpl, is_code=False, n_seeds=50)
        self.assertTrue(res_pyth["passed"])
        self.assertFalse(res_pyth["is_exempt"])
        self.assertGreaterEqual(res_pyth["distinct_skill_cells"], 3)

        kata_tpl = next(t for t in PRG_TPLS if t["key"] == "kata_debounce")
        res_kata = evaluate_template("PRG-T01-C03", kata_tpl, is_code=True, n_seeds=30)
        self.assertTrue(res_kata["passed"])
        self.assertTrue(res_kata["is_exempt"])

    def test_13_safe_parse_security_payloads_blocked(self) -> None:
        """Test 13: All malicious / dangerous payloads are blocked with verdict 'invalid input'."""
        from math_engine.answer_check import check_answer
        import time

        spec_expr = {"type": "expression", "value": "x**2 - 1", "variables": ["x"]}
        spec_comp = {"type": "complex", "value": "3 - 4*I"}
        spec_num = {"type": "number", "value": "17"}

        malicious_inputs = [
            ("__import__('os').system('echo X')", "RCE import attempt"),
            ("().__class__.__base__.__subclasses__()", "Sandbox escape via subclass inspection"),
            ("open('f').read()", "File access attempt"),
            ("9**9**9", "Exponentiation DoS bomb"),
            ("(9**9)**9", "Chained exponentiation DoS"),
            ("1" * 201, "Input exceeding 200 character limit"),
            ("lambda x: x", "Lambda expression injection"),
            ("f(x)", "Call to unwhitelisted function f"),
            ("eval('1+1')", "Direct eval call"),
            ("exec('x=1')", "Direct exec call"),
            ("2**1001", "Exponent magnitude exceeding limit (1000)"),
            ("my_secret_var", "Identifier with disallowed underscore"),
            ("\"hello_string\"", "Disallowed string literal"),
            ("[x for x in (1, 2)]", "Disallowed comprehension syntax"),
        ]

        for payload, description in malicious_inputs:
            for spec in (spec_expr, spec_comp, spec_num):
                res = check_answer(spec, payload)
                self.assertEqual(
                    res["verdict"],
                    "invalid input",
                    f"Payload '{payload}' ({description}) was not blocked for spec {spec['type']}: {res}"
                )
                self.assertIn("message", res)
                self.assertNotIn("Traceback", res["message"])

    def test_14_check_answer_regression_existing_drills(self) -> None:
        """Test 14: All existing math drill canonical answers pass check_answer round-trip."""
        import glob
        from math_engine.answer_check import check_answer
        import time

        data_dir = os.environ.get("DRILLS_DATA_DIR", "drills/data")
        files = sorted(glob.glob(os.path.join(data_dir, "*", "*.json")))
        checked = 0
        passed = 0

        for fpath in files:
            with open(fpath, encoding="utf-8") as fp:
                drill = json.load(fp)
            if drill.get("subject") not in ("MATH", "MTH"):
                continue
            for prob in drill.get("problems", []):
                spec = prob.get("answerSpec")
                ans = prob.get("answerPlain")
                if not spec or not ans:
                    continue
                checked += 1
                res = check_answer(spec, ans)
                self.assertEqual(
                    res["verdict"],
                    "correct",
                    f"File {fpath} problem {prob.get('id')} failed check_answer: ans={ans!r}, res={res}"
                )
                passed += 1

        self.assertGreaterEqual(checked, 160)
        self.assertEqual(passed, checked)

        # Explicit format regression checks
        # 1. Fraction: 3/4
        res_frac = check_answer({"type": "number", "value": "3/4"}, "3/4")
        self.assertEqual(res_frac["verdict"], "correct")

        # 2. Radical: sqrt(2)/2
        res_rad = check_answer({"type": "number", "value": "sqrt(2)/2"}, "sqrt(2)/2")
        self.assertEqual(res_rad["verdict"], "correct")

        # 3. Complex: 3 - 4i
        res_cx = check_answer({"type": "complex", "value": "3 - 4*I"}, "3 - 4i")
        self.assertEqual(res_cx["verdict"], "correct")

        # 4. Caret exponent: x^2 - 1
        res_pow = check_answer({"type": "expression", "value": "x**2 - 1", "variables": ["x"]}, "x^2 - 1")
        self.assertEqual(res_pow["verdict"], "correct")

        # 5. Implicit multiplication: 100 pi
        res_pi = check_answer({"type": "number", "value": "100*pi"}, "100 pi")
        self.assertEqual(res_pi["verdict"], "correct")

        # 6. Form check: unreduced fraction 2/4
        res_unreduced = check_answer({"type": "number", "value": "1/2", "forms": ["reduced_fraction"]}, "2/4")
        self.assertEqual(res_unreduced["verdict"], "equivalent_not_in_form")

        # 7. Form check: decimal 0.75 for exact fraction
        res_dec = check_answer({"type": "number", "value": "3/4", "forms": ["exact"]}, "0.75")
        self.assertEqual(res_dec["verdict"], "equivalent_not_in_form")

    def test_15_heavy_input_does_not_hang(self) -> None:
        """Test 15: Heavy inputs like (x+1)**1000 complete rapidly and do not hang."""
        import time
        from math_engine.answer_check import check_answer
        import time

        spec = {"type": "expression", "value": "x**2 - 1", "variables": ["x"]}
        t0 = time.time()
        res = check_answer(spec, "(x+1)**1000")
        elapsed = time.time() - t0

        self.assertLess(elapsed, 1.5, f"Evaluation of (x+1)**1000 took {elapsed:.2f}s, expected < 1.5s")
        self.assertIn(res["verdict"], ("invalid input", "incorrect"))
        self.assertIsInstance(res.get("message"), str)

        # Confirm numeric large exponents > 20 are NOT marked invalid input and evaluate correctly:
        # 1. 2^30
        res_2_30 = check_answer({"type": "number", "value": "2**30"}, "2^30")
        self.assertEqual(res_2_30["verdict"], "correct")
        self.assertNotEqual(res_2_30["verdict"], "invalid input")

        # 2. 10^25
        res_10_25 = check_answer({"type": "number", "value": "10**25"}, "10^25")
        self.assertEqual(res_10_25["verdict"], "correct")
        self.assertNotEqual(res_10_25["verdict"], "invalid input")

        # 3. i^23
        res_i_23 = check_answer({"type": "complex", "value": "I**23"}, "i^23")
        self.assertEqual(res_i_23["verdict"], "correct")
        self.assertNotEqual(res_i_23["verdict"], "invalid input")

        # 4. Equivalent evaluation: i^23 = -i
        res_neg_i = check_answer({"type": "complex", "value": "-I"}, "i^23")
        self.assertEqual(res_neg_i["verdict"], "correct")

    def test_16_coverage_report_and_sample_sheet(self) -> None:
        """Test 16: scripts.coverage_report and scripts.sample_sheet produce valid Markdown."""
        from scripts.coverage_report import generate_coverage_report
        from scripts.sample_sheet import build_sample_sheet
        import tempfile

        # 1. Coverage report written to isolated tempdir
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_cov = os.path.join(tmp_dir, "coverage.md")
            cov_content = generate_coverage_report(output_path=tmp_cov)
            self.assertTrue(os.path.exists(tmp_cov))
            self.assertIn("Coverage & Skills Taxonomy Report", cov_content)
            self.assertIn("GEO-CYLINDER-VOLUME-RADIUS", cov_content)
            self.assertIn("MTH-COMPLEX-RADICAL-SIMPLIFY", cov_content)
            self.assertIn("PRG-JS-THIS-BINDING-DEBUG", cov_content)
            self.assertIn("PRG-ARCH-PROJECT-RATE-LIMITER", cov_content)
            self.assertIn("Missing Levels per Domain", cov_content)

        # 2. Sample sheet for math template (cylinder-volume)
        sheet_cyl = build_sample_sheet("cylinder-volume", seed=42)
        self.assertIn("Sample Sheet: `cylinder-volume`", sheet_cyl)
        self.assertIn("Form 1/2: `direct`", sheet_cyl)
        self.assertIn("Form 2/2: `from-diameter`", sheet_cyl)
        self.assertIn("GEO-CYLINDER-VOLUME-RADIUS", sheet_cyl)
        self.assertIn("32 pi", sheet_cyl)

        # 3. Sample sheet for code template (find_bug_this_binding)
        sheet_code = build_sample_sheet("find_bug_this_binding", seed=42)
        self.assertIn("Sample Sheet: `find_bug_this_binding`", sheet_code)
        self.assertIn("PRG-JS-THIS-BINDING-DEBUG", sheet_code)
        self.assertIn("```javascript", sheet_code)
        self.assertIn("Canonical Answer", sheet_code)

    def test_17_symbolic_expression_large_exponent(self) -> None:
        """Test 17: Symbolic expressions with exponent > 20 like (x+1)**30 evaluate correctly and do not hang."""
        import time
        from math_engine.answer_check import check_answer
        import time

        spec = {"type": "expression", "value": "(x+1)^30", "variables": ["x"]}

        # 1. Self comparison: (x+1)**30 == (x+1)^30 -> correct
        t0 = time.time()
        res_exact = check_answer(spec, "(x+1)**30")
        elapsed = time.time() - t0
        self.assertLess(elapsed, 0.3, f"Symbolic large exponent took {elapsed:.2f}s, expected < 0.3s")
        self.assertEqual(res_exact["verdict"], "correct")

        # 2. Inequivalent answer: (x+1)**30 + 1 != (x+1)^30 -> incorrect (NOT correct or invalid input)
        res_wrong = check_answer(spec, "(x+1)**30 + 1")
        self.assertEqual(res_wrong["verdict"], "incorrect")

        # 3. Large integer precision: 10**25 vs 10**25 + 1
        num_spec = {"type": "number", "value": "10**25"}
        res_num_correct = check_answer(num_spec, "10^25")
        self.assertEqual(res_num_correct["verdict"], "correct")
        res_num_wrong = check_answer(num_spec, "10**25 + 1")
        self.assertEqual(res_num_wrong["verdict"], "incorrect")

    def test_18_skills_taxonomy_dag_and_prerequisites(self) -> None:
        """Test 18: skills_taxonomy.json contains exactly 23 DAG edges with valid strengths and no cycles."""
        from collections import defaultdict, deque, Counter

        with open("skills_taxonomy.json", "r", encoding="utf-8") as f:
            tax = json.load(f)

        skills = tax.get("skills", {})
        self.assertEqual(len(skills), 43)
        domain_skill_counts = Counter(sdata.get("domain") for sdata in skills.values())
        self.assertEqual(
            dict(domain_skill_counts),
            {
                "calculus": 2,
                "complex_numbers": 14,
                "geometry": 9,
                "javascript_core": 6,
                "software_architecture": 7,
                "vectors": 5,
            },
        )

        edges = []
        in_degree = {s: 0 for s in skills}
        adj = defaultdict(list)

        cut_edges = {
            ("MTH-COMPLEX-POWER-I-MOD4", "MTH-COMPLEX-MULTIPLICATION"),
            ("PRG-JS-SCOPE-HOISTING-VAR", "PRG-JS-EVENT-LOOP-MICROTASK"),
            ("PRG-JS-PROMISE-ASYNC-FLOW", "PRG-JS-THIS-BINDING-DEBUG"),
            ("PRG-JS-THIS-BINDING-DEBUG", "PRG-JS-PROTOTYPE-CHAIN-MUTATION"),
            ("PRG-ARCH-PIPELINE-PRICING", "PRG-ARCH-REFACTOR-SUBSCRIPTION"),
        }

        for sid, sdata in skills.items():
            for p in sdata.get("prerequisites", []):
                src = p.get("skill")
                st = p.get("strength")
                self.assertIn(src, skills, f"Prerequisite {src} not found in registered skills")
                self.assertIn(st, ["hard", "soft"], f"Invalid strength '{st}' on edge {src} -> {sid}")
                self.assertNotIn((src, sid), cut_edges, f"Edge {src} -> {sid} was supposed to be cut")
                edges.append((src, sid, st))
                adj[src].append(sid)
                in_degree[sid] += 1

        self.assertEqual(len(edges), 28)
        edge_domains = Counter()
        for src, sid, _ in edges:
            src_dom = skills[src]["domain"]
            tgt_dom = skills[sid]["domain"]
            dkey = src_dom if src_dom == tgt_dom else f"{src_dom}->{tgt_dom}"
            edge_domains[dkey] += 1

        self.assertEqual(
            dict(edge_domains),
            {
                "calculus": 1,
                "complex_numbers": 11,
                "geometry": 6,
                "geometry->vectors": 1,
                "javascript_core": 2,
                "javascript_core->software_architecture": 1,
                "software_architecture": 3,
                "vectors": 3,
            },
        )

        # Verify cross-domain edge
        cross_domain_edge = ("PRG-JS-PROMISE-ASYNC-FLOW", "PRG-ARCH-ASYNC-CACHE-RACE", "hard")
        self.assertIn(cross_domain_edge, edges)

        # Verify calculus hard prerequisite
        calc_edge = ("CAL-DIFF-POWER", "CAL-DIFF-CHAIN", "hard")
        self.assertIn(calc_edge, edges)

        # Verify vectors domain prerequisites
        self.assertIn(("VEC-ADD-SCALE", "VEC-DOT-PRODUCT", "soft"), edges)
        self.assertIn(("VEC-ADD-SCALE", "VEC-LINEAR-COMBINATION", "hard"), edges)
        self.assertIn(("VEC-DOT-PRODUCT", "VEC-ORTHOGONAL", "hard"), edges)
        self.assertIn(("GEO-RIGHT-TRIANGLE-HYP", "VEC-MAGNITUDE", "soft"), edges)

        # Verify soft edges demoted from hard per pedagogical definition
        soft_add = ("MTH-COMPLEX-RADICAL-SIMPLIFY", "MTH-COMPLEX-ADDITION", "soft")
        self.assertIn(soft_add, edges)
        soft_let = ("PRG-JS-SCOPE-HOISTING-VAR", "PRG-JS-SCOPE-HOISTING-LET", "soft")
        self.assertIn(soft_let, edges)

        # Verify DAG topological sort
        q = deque([s for s, deg in in_degree.items() if deg == 0])
        visited = 0
        while q:
            curr = q.popleft()
            visited += 1
            for nxt in adj[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    q.append(nxt)

        self.assertEqual(visited, len(skills), "Cycle detected in skills prerequisite graph! Must be a DAG.")

    def test_19_coverage_report_deduplication_and_ready_to_learn(self) -> None:
        """Test 19: coverage_report outputs studio deduplication audit and 3-part 'Ready to Learn' section."""
        from scripts.coverage_report import generate_coverage_report

        content = generate_coverage_report(output_path=None)
        self.assertIn("Studio File Deduplication Audit", content)
        self.assertIn("DRL-MTH-T01-C12-01-studio-attempt.json", content)
        self.assertIn("DRL-MTH-T01-C12-02-studio.json", content)
        self.assertIn("DRL-PRG-T01-C03-01-studio.json", content)
        self.assertIn("DRL-PRG-T01-C03-02-studio.json", content)
        self.assertIn("พร้อมเรียนต่อ (Ready to Learn)", content)
        self.assertIn("แนะนำถัดไป (Top 3 Recommendations)", content)
        self.assertIn("ทักษะที่ถูกล็อก (Locked Skills)", content)
        self.assertIn("รากที่ยังไม่เคยฝึก (Unpracticed Root Skills)", content)
        self.assertIn("ตารางความสัมพันธ์ 28 เส้น Prerequisite", content)
        self.assertIn("flowchart TD", content)

    def test_20_tolerance_and_decimal_approximation(self) -> None:
        """Test 20: Decimal approximation handling with and without optional tolerance field."""
        from math_engine.answer_check import check_answer
        import time

        # 1. Without tolerance (default strict behavior)
        r1 = check_answer({"type": "number", "value": "2/3"}, "0.667")
        self.assertEqual(r1["verdict"], "incorrect")
        self.assertTrue(any(d["code"] == "rounding" for d in r1.get("diagnostics", [])))

        r2 = check_answer({"type": "number", "value": "sqrt(2)/2"}, "0.7071")
        self.assertEqual(r2["verdict"], "incorrect")
        self.assertTrue(any(d["code"] == "rounding" for d in r2.get("diagnostics", [])))

        # 2. With tolerance enabled (loose enough)
        r3 = check_answer({"type": "number", "value": "2/3", "tolerance": 0.001}, "0.667")
        self.assertEqual(r3["verdict"], "correct")

        r4 = check_answer({"type": "number", "value": "sqrt(2)/2", "tolerance": 0.001}, "0.7071")
        self.assertEqual(r4["verdict"], "correct")

        # 3. With tolerance enabled (too tight)
        r5 = check_answer({"type": "number", "value": "2/3", "tolerance": 0.0001}, "0.667")
        self.assertEqual(r5["verdict"], "incorrect")

    def test_21_calculus_pilot_templates_and_dual_verification(self) -> None:
        """Test 21: Calculus templates (power rule and chain rule) pass G1-G4, dual verification, and trap check."""
        import random
        from math_engine.templates.mth_calc_diff import t_diff_power, t_diff_chain
        from math_engine.answer_check import check_answer
        import time
        from quality_rules import check_gate_g1, check_gate_g2, check_gate_g4

        for seed in range(50):
            rng = random.Random(seed)
            # Power rule
            p_pow = t_diff_power(rng)
            check_gate_g1(p_pow)
            check_gate_g2(p_pow)
            check_gate_g4(p_pow)
            r_pow_trap = check_answer(p_pow["answerSpec"], p_pow["verify"]["trapValue"])
            self.assertEqual(r_pow_trap["verdict"], "incorrect", f"Power trap on seed {seed} must be incorrect")

            # Chain rule
            p_chn = t_diff_chain(rng)
            check_gate_g1(p_chn)
            check_gate_g2(p_chn)
            check_gate_g4(p_chn)
            r_chn_trap = check_answer(p_chn["answerSpec"], p_chn["verify"]["trapValue"])
            self.assertEqual(r_chn_trap["verdict"], "incorrect", f"Chain trap on seed {seed} must be incorrect")

    def test_22_auto_discovery_of_new_templates(self) -> None:
        """Test 22: Auto-discovery dynamically finds newly added template modules without code modifications."""
        import os
        from math_engine.templates import load_unit, discover_units
        from scripts.accept_template import get_all_registered_templates
        from scripts.sample_sheet import load_all_templates

        mock_file = os.path.join("math_engine", "templates", "tmp_mock_unit.py")
        mock_content = """UNIT = "MTH-MOCK-AUTODISCOVER"
TEMPLATES = [
    {
        "key": "mock-autodiscover-tpl",
        "level": 1,
        "skill": "MOCK-SKILL",
        "forms": {"direct": {"level": 1, "skill": "MOCK-SKILL"}},
        "build": lambda rng, form=None: {"answerSpec": {"type": "number", "value": "42"}},
    }
]
"""
        try:
            with open(mock_file, "w", encoding="utf-8") as f:
                f.write(mock_content)

            # 1. load_unit finds mock unit via auto-discovery
            mod = load_unit("MTH-MOCK-AUTODISCOVER")
            self.assertEqual(getattr(mod, "UNIT", None), "MTH-MOCK-AUTODISCOVER")

            # 2. scripts.accept_template discovers mock template
            all_accepted = get_all_registered_templates()
            mock_found_accept = any(tpl["key"] == "mock-autodiscover-tpl" for _, tpl, _ in all_accepted)
            self.assertTrue(mock_found_accept, "mock-autodiscover-tpl must be discovered by accept_template")

            # 3. scripts.sample_sheet discovers mock template
            all_sample = load_all_templates()
            self.assertIn("mock-autodiscover-tpl", all_sample)

        finally:
            if os.path.exists(mock_file):
                os.remove(mock_file)
            discover_units(force_refresh=True)

    def test_23_diff_whitelist_and_notion_dry_run(self) -> None:
        """Test 23: User input diff(...) blocked as invalid input; Notion dry-run works without network."""
        from math_engine.answer_check import check_answer
        import time
        from practice_hub import sync_drill_to_notion

        # 1. User typing diff(...) returns 'invalid input'
        spec = {"type": "expression", "value": "2*x", "variables": ["x"]}
        res_diff = check_answer(spec, "diff(x**2, x)")
        self.assertEqual(res_diff["verdict"], "invalid input")
        self.assertIn("diff", res_diff["message"])

        # 2. Canonical math answer still passes
        res_correct = check_answer(spec, "2*x")
        self.assertEqual(res_correct["verdict"], "correct")

        # 3. Dangerous payloads still blocked
        res_bad = check_answer(spec, "__import__('os').system('ls')")
        self.assertEqual(res_bad["verdict"], "invalid input")

        # 4. Notion dry-run test: never calls real network, returns dryRun flag
        mock_doc = {
            "drillId": "DRL-MTH-TEST-DRYRUN-01",
            "unitCode": "MTH-CALC-DIFF",
            "chapterCode": "MTH-CALC",
            "topicCode": "MTH-CALC",
            "problems": [],
        }
        dry_res = sync_drill_to_notion(mock_doc)
        try:
            self.assertTrue(dry_res["ok"])
            self.assertTrue(dry_res.get("dryRun"))
            self.assertEqual(dry_res.get("drillPageId"), "mock-DRL-MTH-TEST-DRYRUN-01")
        finally:
            saved_path = dry_res.get("localFilePath")
            if saved_path and os.path.exists(saved_path):
                os.remove(saved_path)
                try:
                    os.rmdir(os.path.dirname(saved_path))
                except OSError:
                    pass

    def test_24_gate_g6_formatting_rejects_sloppy_math(self) -> None:
        """Test 24: G6 rejects '+ -', '- -', '+-', '--', '^1', 'x^0', '*1', '1x' and passes clean forms."""
        from quality_rules import check_gate_g6, QualityError
        import random
        from math_engine.templates import get_all_unit_templates as get_math_units
        from code_engine.templates import get_all_unit_templates as get_code_units

        # 1. Verify that feeding text with sloppy patterns is rejected with QualityError (gate 'G6')
        bad_cases = [
            ("prompt", "Calculate 1x", "1x"),
            ("display", "+ 1x", "1x"),
            ("plainText", "- 1x", "1x"),
            ("display", "x^1", "^1"),
            ("answerDisplay", "x^{1}", "^1"),
            ("prompt", "Evaluate *1", "*1"),
            ("prompt", "Calculate 3 + -4", "+ -"),
            ("display", "x +- 4", "+ -"),
            ("plainText", "x - -4", "- -"),
            ("display", "x--4", "- -"),
            ("answerDisplay", "5x^0 + 2", "x^0"),
            ("answerDisplay", "-1x^{-2}", "1x"),
            ("prompt", "Calculate x^1/2", "^1"),
        ]
        for field, text, expected_pat in bad_cases:
            prob = {"id": "TEST_Q", field: text}
            with self.assertRaises(QualityError, msg=f"Should reject {expected_pat} in {field}: '{text}'") as ctx:
                check_gate_g6(prob, is_code=False)
            self.assertEqual(ctx.exception.gate, "G6")
            self.assertIn(expected_pat, ctx.exception.reason)

        # 2. Verify that bounded / valid patterns pass G6 (including user-specified false-positive guards)
        good_cases = [
            {"prompt": "0.1x"},
            {"prompt": "2.1x"},
            {"prompt": "2*1.5"},
            {"prompt": "e^{1/2}"},
            {"prompt": "11x^2"},
            {"prompt": "21x"},
            {"prompt": "x^10"},
            {"prompt": "x^{10}"},
            {"prompt": "2*10"},
            {"prompt": "(-1)"},
            {"prompt": "10x"},
            {"prompt": "Calculate 3 + (-4)"},
            {"prompt": "Calculate 3 - (-4)"},
            {"prompt": "Choice: ( + ) or ( - ) or (- -)"},
            {"prompt": "Solution with \\pm: x = 2 \\pm 3"},
            {"explain": "| :--- | :--- |\n| col1 | col2 |"},
            {"prompt": "Horizontal divider ---\nNext section"},
            {"prompt": "for (let i = 10; i--; ) {}", "is_code": True},
        ]
        for c in good_cases:
            is_code = c.pop("is_code", False)
            c["id"] = "GOOD_Q"
            res = check_gate_g6(c, is_code=is_code)
            self.assertTrue(res["passed"])

        # 3. Verify all registered templates x all forms x 50 seeds pass G6
        for engine, get_units, is_code in [("math", get_math_units, False), ("code", get_code_units, True)]:
            for ucode, tpls in get_units():
                for t in tpls:
                    key = t["key"]
                    forms = list(t["forms"].keys()) if isinstance(t.get("forms"), dict) else t.get("forms", ["direct"])
                    for f in forms:
                        for s in range(1, 51):
                            rng = random.Random(s * 1000 + 7)
                            try:
                                cand = t["build"](rng, form=f) if "form" in t["build"].__code__.co_varnames else t["build"](rng)
                            except Exception:
                                continue
                            cand["id"] = "Q01"
                            try:
                                g6_res = check_gate_g6(cand, is_code=is_code)
                                self.assertTrue(g6_res["passed"])
                            except QualityError as exc:
                                self.fail(f"Template {key} [{f}] seed={s} failed G6: {exc.reason}")

    def test_25_vector_comparator_and_security(self):
        """Test vector comparator, notation flags, diagnostics, and security parser constraints."""
        import random
        from math_engine.answer_check import check_answer
        import time

        spec3d = {"type": "vector", "components": [1, -2, 3]}

        # 1. Valid bracket syntaxes
        for valid_input in ["<1, -2, 3>", "(1, -2, 3)", "[1, -2, 3]"]:
            res = check_answer(spec3d, valid_input)
            self.assertEqual(res["verdict"], "correct", f"Failed for {valid_input}")

        # 2. Radical equivalences
        spec_rad = {"type": "vector", "components": ["1/sqrt(2)", "1/sqrt(2)"]}
        res_rad = check_answer(spec_rad, "<sqrt(2)/2, 1/sqrt(2)>")
        self.assertEqual(res_rad["verdict"], "correct")

        # 3. Diagnostics
        # Dimension mismatch
        res_dim = check_answer(spec3d, "<1, -2>")
        self.assertEqual(res_dim["verdict"], "incorrect")
        self.assertTrue(any(d["code"] == "dimension_mismatch" for d in res_dim["diagnostics"]))

        # Scalar multiple / parallel
        res_scale = check_answer(spec3d, "<2, -4, 6>")
        self.assertEqual(res_scale["verdict"], "incorrect")
        self.assertTrue(any(d["code"] == "scalar_multiple" for d in res_scale["diagnostics"]))

        # Swapped order
        res_swap = check_answer(spec3d, "<-2, 1, 3>")
        self.assertEqual(res_swap["verdict"], "incorrect")
        self.assertTrue(any(d["code"] == "swapped_order" for d in res_swap["diagnostics"]))

        # Component sign error
        res_sign = check_answer(spec3d, "<1, 2, 3>")
        self.assertEqual(res_sign["verdict"], "incorrect")
        self.assertTrue(any(d["code"] == "component_sign_error" for d in res_sign["diagnostics"]))

        # Component sign error on components 1 and 3 of 3D vector (consolidated single message)
        res_sign_1_3 = check_answer(spec3d, "<-1, -2, -3>")
        self.assertEqual(res_sign_1_3["verdict"], "incorrect")
        diag_sign_1_3 = next((d for d in res_sign_1_3["diagnostics"] if d["code"] == "component_sign_error"), None)
        self.assertIsNotNone(diag_sign_1_3)
        self.assertIn("Components 1 and 3 have the opposite sign.", diag_sign_1_3["message"])

        # Invert entire vector: reported as scalar_multiple (-1), component_sign_error skipped
        res_invert_all = check_answer(spec3d, "<-1, 2, -3>")
        self.assertEqual(res_invert_all["verdict"], "incorrect")
        self.assertTrue(any(d["code"] == "scalar_multiple" and "factor of -1" in d["message"] for d in res_invert_all["diagnostics"]))
        self.assertFalse(any(d["code"] == "component_sign_error" for d in res_invert_all["diagnostics"]))

        # Scalar multiple formatting via nsimplify (e.g. \sqrt{2} rather than 1.414)
        spec_unit_rad = {"type": "vector", "components": ["-1/sqrt(2)", "1/sqrt(2)"]}
        res_sqrt2 = check_answer(spec_unit_rad, "<-1, 1>")
        self.assertEqual(res_sqrt2["verdict"], "incorrect")
        diag_scale = next((d for d in res_sqrt2["diagnostics"] if d["code"] == "scalar_multiple"), None)
        self.assertIsNotNone(diag_scale)
        self.assertIn(r"\sqrt{2}", diag_scale["message"])
        self.assertNotIn("1.414", diag_scale["message"])

        # 4. Unit vector notation: only enabled when vectorNotation is True
        spec_unit = {"type": "vector", "components": [2, 3, -4], "vectorNotation": True}
        res_unit_i = check_answer(spec_unit, "2i + 3j - 4k")
        self.assertEqual(res_unit_i["verdict"], "correct")

        res_unit_hat = check_answer(spec_unit, r"2\hat{i} + 3\hat{j} - 4\hat{k}")
        self.assertEqual(res_unit_hat["verdict"], "correct")

        # Disabled by default
        spec_no_unit = {"type": "vector", "components": [2, 3, -4]}
        res_no_unit = check_answer(spec_no_unit, "2i + 3j - 4k")
        self.assertNotEqual(res_no_unit["verdict"], "correct")

        # 5. Vector entered for scalar question in check_number
        spec_num = {"type": "number", "value": "13"}
        res_vec_for_num = check_answer(spec_num, "<5, -4, -5>")
        self.assertEqual(res_vec_for_num["verdict"], "incorrect")
        self.assertTrue(any(d["code"] == "vector_given_for_scalar" for d in res_vec_for_num["diagnostics"]))

        # 6. Security tests: malicious inputs & formatting attacks
        security_payloads = [
            "<__import__('os'), 1>",
            "<eval('1+1'), 1>",
            "[__builtins__, 1]",
            "<1, 2]",
            "(1, 2>",
            "[1, 2)",
            "<1, <2, 3>>",
            "[1, [2, 3]]",
            "[(1, 2), 3]",
            "[x for x in range(10)]",
            "[1, 2, 3, 4, 5]",
            "<" + "1," * 150 + "1>",
            "9**9**9",
        ]
        for payload in security_payloads:
            res_sec = check_answer(spec3d, payload)
            self.assertEqual(res_sec["verdict"], "invalid input", f"Payload failed to be rejected safely: {payload}")
            self.assertIn("Invalid input", res_sec["message"])

        # Heavy exponent with variable allowed: (k+1)**101 rejected by limit 100, (k+1)**100 evaluates to incorrect without hanging
        from math_engine.answer_check import safe_parse, is_equal, EqualTimeoutError, SafeParseError
        with self.assertRaises(SafeParseError):
            safe_parse("(k+1)**101", variables=["k"])

        res_k100 = check_answer({"type": "expression", "value": "k + 1", "variables": ["k"]}, "(k+1)**100")
        self.assertEqual(res_k100["verdict"], "incorrect")

        # is_equal timeout test with heavy symbolic expression
        import sympy as sp
        sym_k = sp.Symbol("k")
        heavy_pow = (sym_k + 1)**1000
        t_start = time.time()
        res_eq = is_equal(heavy_pow, sym_k, timeout=0.5, raise_on_timeout=False)
        self.assertFalse(res_eq)
        self.assertLess(time.time() - t_start, 1.0)

        with self.assertRaises(EqualTimeoutError):
            is_equal(heavy_pow, sym_k, timeout=0.5, raise_on_timeout=True)

        # 7. Quality gate evaluation of vector templates across seeds
        from math_engine.templates.mth_vectors import TEMPLATES as VEC_TEMPLATES
        for tpl in VEC_TEMPLATES:
            for form_name, finfo in tpl["forms"].items():
                for seed in range(1, 51):
                    rng = random.Random(seed * 1000 + 42)
                    prob = tpl["build"](rng, form=form_name)
                    prob["id"] = "VEC_Q01"
                    prob["templateKey"] = tpl["key"]
                    prob["level"] = finfo.get("level", tpl.get("level", 1))
                    prob["skill"] = finfo.get("skill", tpl.get("skill", "VEC-ADD-SCALE"))
                    prob["verificationLevel"] = tpl.get("verificationLevel", "machine-verified")

                    # Verify G1, G2, G4, G6
                    g1 = check_gate_g1(prob, is_code=False)
                    self.assertTrue(g1["passed"])
                    g2 = check_gate_g2(prob)
                    self.assertTrue(g2["passed"])
                    g4 = check_gate_g4(prob, is_code=False)
                    self.assertTrue(g4["passed"])
                    g6 = check_gate_g6(prob, is_code=False)
                    self.assertTrue(g6["passed"])

    def test_20_numpy_fallback_vector_generation(self) -> None:
        """Test 20: Vector template generation succeeds 100% when HAS_NUMPY is False."""
        import random
        import math_engine.templates.mth_vectors as mv
        orig_has_np = mv.HAS_NUMPY
        try:
            mv.HAS_NUMPY = False
            for tpl in mv.TEMPLATES:
                for form_name in tpl["forms"].keys():
                    for seed in range(1, 21):
                        rng = random.Random(seed * 777)
                        prob = tpl["build"](rng, form=form_name)
                        self.assertIn("answerPlain", prob)
                        self.assertIn("verify", prob)
        finally:
            mv.HAS_NUMPY = orig_has_np

    def test_21_vector_variable_and_unicode_brackets(self) -> None:
        """Test 21: Vector checker normalizes Unicode brackets, supports variables, and detects vector for scalar."""
        from math_engine.answer_check import check_answer

        # 1. Unicode brackets: U+27E8 / U+27E9 and U+3008 / U+3009
        spec = {"type": "vector", "components": ["1", "2", "3"]}
        res_u27 = check_answer(spec, "⟨1, 2, 3⟩")
        self.assertEqual(res_u27["verdict"], "correct")
        res_u30 = check_answer(spec, "〈1, 2, 3〉")
        self.assertEqual(res_u30["verdict"], "correct")

        # 2. check_number detects vectors in [], (), and <>
        num_spec = {"type": "number", "value": "10"}
        res_br = check_answer(num_spec, "[1, 2, 3]")
        self.assertEqual(res_br["verdict"], "incorrect")
        self.assertEqual(res_br["diagnostics"][0]["code"], "vector_given_for_scalar")
        res_par = check_answer(num_spec, "(1, 2, 3)")
        self.assertEqual(res_par["verdict"], "incorrect")
        self.assertEqual(res_par["diagnostics"][0]["code"], "vector_given_for_scalar")

        # 3. Pilot variables support: <2t, cos(t)>
        var_spec = {"type": "vector", "components": ["2*t", "cos(t)"], "variables": ["t"]}
        res_var = check_answer(var_spec, "<2*t, cos(t)>")
        self.assertEqual(res_var["verdict"], "correct")

        # 4. Heavy input with variables does not hang and respects limits
        res_heavy = check_answer(var_spec, "<(t+1)**1000, cos(t)>")
        self.assertIn(res_heavy["verdict"], ("invalid input", "incorrect"))

        # 5. Heavy input: <(t+1)**100, 2> vs <(t+2)**100, 2> returns 'incorrect' in < 200 ms
        import time
        heavy_spec = {"type": "vector", "components": ["(t+2)**100", "2"], "variables": ["t"]}
        t_start = time.perf_counter()
        res_heavy_mismatch = check_answer(heavy_spec, "<(t+1)**100, 2>")
        t_elapsed = time.perf_counter() - t_start
        self.assertEqual(res_heavy_mismatch["verdict"], "incorrect")
        self.assertLess(t_elapsed, 0.200, f"Heavy mismatch took {t_elapsed*1000:.2f} ms, expected < 200 ms")

        # Also when compared against scalar (t+2)**100
        num_heavy_spec = {"type": "number", "value": "(t+2)**100", "variables": ["t"]}
        t_start2 = time.perf_counter()
        res_num_mismatch = check_answer(num_heavy_spec, "<(t+1)**100, 2>")
        t_elapsed2 = time.perf_counter() - t_start2
        self.assertEqual(res_num_mismatch["verdict"], "incorrect")
        self.assertLess(t_elapsed2, 0.200)

    def test_22_anti_leak_gate(self) -> None:
        """Test 22: Anti-leak gate rejects prompts or hints containing answers or spoiler examples."""
        from quality_rules import check_gate_anti_leak, QualityError

        # A leaking hint with answerPlain
        p_leak = {
            "id": "LEAK_01",
            "answerPlain": "<-1/sqrt(2), 1/sqrt(2)>",
            "answerSpec": {"type": "vector", "components": ["-1/sqrt(2)", "1/sqrt(2)"]},
            "inputHint": "Enter vector components like <-1/sqrt(2), 1/sqrt(2)>",
        }
        with self.assertRaises(QualityError):
            check_gate_anti_leak(p_leak)

        # A clean structural hint
        p_clean = {
            "id": "CLEAN_01",
            "answerPlain": "<-1/sqrt(2), 1/sqrt(2)>",
            "answerSpec": {"type": "vector", "components": ["-1/sqrt(2)", "1/sqrt(2)"]},
            "inputHint": "Enter vector components like <x, y>",
        }
        res = check_gate_anti_leak(p_clean)
        self.assertTrue(res["passed"])

        # Targeted positive/negative anti-leak test cases:
        # 1. Must be rejected: hint "The real parts combine to $16$." when answer is 16 + 3i
        p_re_leak = {
            "id": "LEAK_RE_PART",
            "answerPlain": "16 + 3i",
            "answerSpec": {"type": "complex", "value": "16 + (3)*I"},
            "checkpointHint": "The real parts combine to $16$.",
        }
        with self.assertRaises(QualityError):
            check_gate_anti_leak(p_re_leak)

        # 2. Must be rejected: hint "the answer is 24" when answer is 24
        p_num_leak = {
            "id": "LEAK_EXACT_NUM",
            "answerPlain": "24",
            "answerSpec": {"type": "number", "value": "24"},
            "checkpointHint": "the answer is 24",
        }
        with self.assertRaises(QualityError):
            check_gate_anti_leak(p_num_leak)

        # 3. Must be rejected: hint printing value/label of correct choice
        p_choice_leak = {
            "id": "LEAK_CHOICE_OPT",
            "answerPlain": "2",
            "answerSpec": {
                "type": "choice",
                "options": [{"id": "1", "label": "Line 1"}, {"id": "2", "label": "Line 2"}],
                "correct": "2",
            },
            "checkpointHint": "The student made an error in Line 2.",
        }
        with self.assertRaises(QualityError):
            check_gate_anti_leak(p_choice_leak)

        # 4. Must pass: hint containing $i^2 = -1$ when answer contains digit 2
        p_i_sq_pass = {
            "id": "PASS_I_SQUARED",
            "answerPlain": "2",
            "answerSpec": {"type": "number", "value": "2"},
            "checkpointHint": "Remember that $i^2 = -1$.",
        }
        res_i = check_gate_anti_leak(p_i_sq_pass)
        self.assertTrue(res_i["passed"])

        # 5. Must pass: hint "square each component"
        p_sq_pass = {
            "id": "PASS_SQUARE_COMP",
            "answerPlain": "<3, 4>",
            "answerSpec": {"type": "vector", "components": [3, 4]},
            "checkpointHint": "square each component",
        }
        res_sq = check_gate_anti_leak(p_sq_pass)
        self.assertTrue(res_sq["passed"])

    def test_26_all_templates_and_forms_ci_pass(self) -> None:
        """Test 26: All registered templates across math and code units pass G1, G2, G4, G6 with 0 exhausted retries."""
        import random
        from scripts.accept_template import get_all_registered_templates
        from quality_rules import check_gate_g1, check_gate_g2, check_gate_g4, check_gate_g6, QualityError

        all_tpls = get_all_registered_templates()
        self.assertGreaterEqual(len(all_tpls), 33)

        for unit, tpl, is_code in all_tpls:
            key = tpl.get("key", "")
            forms = list(tpl["forms"].keys()) if isinstance(tpl.get("forms"), dict) else tpl.get("forms", ["direct"])
            for form_name in forms:
                for seed in range(1, 11):
                    prob = None
                    last_err = None
                    for attempt in range(12):
                        rng = random.Random(seed * 1000 + attempt * 73 + 42)
                        try:
                            if "form" in tpl["build"].__code__.co_varnames:
                                cand = tpl["build"](rng, form=form_name)
                            else:
                                cand = tpl["build"](rng)
                            cand["id"] = f"{key}_{form_name}_s{seed}"
                            cand["templateKey"] = key
                            finfo = tpl.get("forms", {}).get(form_name, {}) if isinstance(tpl.get("forms"), dict) else {}
                            cand["level"] = finfo.get("level", tpl.get("level", 1))
                            cand["skill"] = finfo.get("skill", tpl.get("skill", ""))
                            cand["verificationLevel"] = tpl.get("verificationLevel", "machine-verified")

                            # Gates check
                            g1 = check_gate_g1(cand, is_code=is_code)
                            self.assertTrue(g1["passed"])
                            g2 = check_gate_g2(cand)
                            self.assertTrue(g2["passed"])
                            g4 = check_gate_g4(cand, is_code=is_code)
                            self.assertTrue(g4["passed"])
                            g6 = check_gate_g6(cand, is_code=is_code)
                            self.assertTrue(g6["passed"])
                            prob = cand
                            break
                        except Exception as exc:
                            last_err = exc

                    self.assertIsNotNone(
                        prob,
                        f"Template '{key}' [{form_name}] exhausted 12 retries on seed {seed}: {last_err}",
                    )

    def test_27_sample_sheet_flaw_forms_and_hints(self) -> None:
        """Test 27: Sample sheet for find-the-flaw forms displays all student lines, options, and both hint fields."""
        from scripts.sample_sheet import build_sample_sheet

        # 1. vector-magnitude
        sheet_vec = build_sample_sheet("vector-magnitude", seed=42)
        self.assertIn("## Form 3/3: `flaw-distribute-sqrt`", sheet_vec)
        self.assertIn("### Display & Student Work", sheet_vec)
        self.assertIn("Line 1:", sheet_vec)
        self.assertIn("Line 2:", sheet_vec)
        self.assertIn("Line 3:", sheet_vec)
        self.assertIn("### Options", sheet_vec)
        self.assertIn("- `[1]` Line 1", sheet_vec)
        self.assertIn("- `[2]` Line 2", sheet_vec)
        self.assertIn("- `[3]` Line 3", sheet_vec)
        self.assertIn("**Input Hint (`inputHint`)**: `Choose a line`", sheet_vec)
        self.assertIn("**Checkpoint Hint (`checkpointHint`)**:", sheet_vec)
        self.assertNotIn("**Checkpoint Hint (`checkpointHint`)**: `(None)`", sheet_vec)
        self.assertIn("**Anti-Leak Verification**: `PASS", sheet_vec)

        # 2. diff-chain-rule
        sheet_diff = build_sample_sheet("diff-chain-rule", seed=42)
        self.assertIn("## Form 3/5: `flaw-line-1`", sheet_diff)
        self.assertIn("### Display & Student Work", sheet_diff)
        self.assertIn("Line 1:", sheet_diff)
        self.assertIn("Line 2:", sheet_diff)
        self.assertIn("Line 3:", sheet_diff)
        self.assertIn("### Options", sheet_diff)
        self.assertIn("- `[1]` Line 1", sheet_diff)
        self.assertIn("- `[2]` Line 2", sheet_diff)
        self.assertIn("- `[3]` Line 3", sheet_diff)
        self.assertIn("**Input Hint (`inputHint`)**: `Choose a line`", sheet_diff)
        self.assertIn("**Checkpoint Hint (`checkpointHint`)**:", sheet_diff)
        self.assertNotIn("**Checkpoint Hint (`checkpointHint`)**: `(None)`", sheet_diff)
        self.assertIn("**Anti-Leak Verification**: `PASS", sheet_diff)

    def test_28_contract_references_and_touchpoints_exist(self) -> None:
        """Test 28: All files, env vars, and CLI modules referenced in 06_template_contract.md exist."""
        import importlib
        touchpoints = [
            "rules/06_template_contract.md",
            "rules/02_pedagogy.md",
            "rules/00_core.md",
            "skills_taxonomy.json",
            "math_engine/answer_spec_registry.py",
            "math_engine/answer_check.py",
            "math_engine/verify.py",
            "quality_rules.py",
            "practice-studio/src/types/drill.ts",
            "practice-studio/src/components/MathProblemCard.tsx",
        ]
        for path in touchpoints:
            self.assertTrue(os.path.exists(path), f"Touchpoint file {path} referenced in contract does not exist")

        cli_modules = [
            "scripts.accept_template",
            "scripts.sample_sheet",
            "scripts.coverage_report",
            "math_engine.generate",
            "code_engine.generate",
            "math_engine.audit",
        ]
        for mod_name in cli_modules:
            mod = importlib.import_module(mod_name)
            self.assertIsNotNone(mod, f"CLI module {mod_name} could not be imported")

    def test_29_flaw_hint_rejects_spoilers(self) -> None:
        """Test 29: Level 3 Find-the-Flaw hints reject spoiler keywords and line positions."""
        import copy
        from math_engine.templates.mth_vectors import t_vector_magnitude
        from math_engine.templates.mth_calc_diff import t_diff_chain
        from quality_rules import check_gate_anti_leak, QualityError
        import random

        rng = random.Random(42)
        p_vec = t_vector_magnitude(rng, form="flaw-distribute-sqrt")
        p_diff = t_diff_chain(rng, form="flaw-line-2")

        # Clean hints must pass
        self.assertTrue(check_gate_anti_leak(p_vec)["passed"])
        self.assertTrue(check_gate_anti_leak(p_diff)["passed"])

        # Spoilers that must be rejected with QualityError G1:
        bad_hints = [
            "Recall that square root does not distribute across addition.",
            "Check Line 2 for calculation errors.",
            "Inspect the second step closely.",
            "Remember to multiply by the inner derivative.",
            "Watch out for a sign slip in the second row.",
        ]
        for bad_h in bad_hints:
            mut_vec = copy.deepcopy(p_vec)
            mut_vec["checkpointHint"] = bad_h
            with self.assertRaises(QualityError, msg=f"Should reject spoiler hint: {bad_h}") as ctx:
                check_gate_anti_leak(mut_vec)
            self.assertEqual(ctx.exception.gate, "G1")

    def test_30_flaw_step_explains_student_error_with_latex(self) -> None:
        """Test 30: Step at flaw_line in Find-the-Flaw displays the student's flawed LaTeX line."""
        import random
        from math_engine.templates.mth_vectors import t_vector_magnitude
        from math_engine.templates.mth_calc_diff import t_diff_chain
        from math_engine.templates.mth_t02_c01_u01 import t_find_flaw

        # 1. vector-magnitude flaw-distribute-sqrt
        p_vec = t_vector_magnitude(random.Random(42), form="flaw-distribute-sqrt")
        explain_vec = p_vec["steps"][1]["explain"]  # flaw_line = 2
        self.assertIn("\\sqrt{(", explain_vec)
        self.assertIn("The student wrote", explain_vec)

        # 2. diff-chain-rule flaw-line-1..3
        for fl in (1, 2, 3):
            p_diff = t_diff_chain(random.Random(42), form=f"flaw-line-{fl}")
            explain_diff = p_diff["steps"][fl - 1]["explain"]
            self.assertIn("The student wrote", explain_diff)
            self.assertIn("$", explain_diff)

        # 3. complex find-the-flaw flaw-line-1..3
        for fl in (1, 2, 3):
            p_cplx = t_find_flaw(random.Random(42), form=f"flaw-line-{fl}")
            explain_cplx = p_cplx["steps"][fl - 1]["explain"]
            self.assertIn("The student wrote", explain_cplx)
            self.assertIn("$", explain_cplx)

    def test_31_cli_templates_and_focus_tag_filtering(self) -> None:
        """Test 31: generate_drill_set correctly filters by --templates and --focus-tag."""
        import tempfile
        from math_engine.generate import generate_drill_set

        with tempfile.TemporaryDirectory() as tmp_dir:
            old_dry = os.environ.get("NOTION_DRY_RUN")
            os.environ["NOTION_DRY_RUN"] = "1"
            try:
                doc = generate_drill_set(
                    unit_code="MTH-T02-C01-U01",
                    count=4,
                    difficulty="ALL",
                    seed=42,
                    templates="multiply,divide-conjugate",
                    focus_tags="conjugate-denominator",
                    data_root=tmp_dir,
                )
                self.assertEqual(len(doc["problems"]), 4)
                allowed_keys = {"multiply", "divide-conjugate"}
                for p in doc["problems"]:
                    self.assertIn(p["templateKey"], allowed_keys)
                has_focus = any(p.get("commonTrapTag") == "conjugate-denominator" for p in doc["problems"])
                self.assertTrue(has_focus, "At least one problem must match focus tag conjugate-denominator")
            finally:
                if old_dry is not None:
                    os.environ["NOTION_DRY_RUN"] = old_dry
                else:
                    os.environ.pop("NOTION_DRY_RUN", None)


if __name__ == "__main__":
    unittest.main()
