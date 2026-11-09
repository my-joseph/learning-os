# -*- coding: utf-8 -*-
"""
Unit tests for AI Code Drill Ingest, Contract Guard & Reasoning Vault.
"""

import json
import os
import tempfile
import unittest

from code_engine.ai_drill_ingest import (
    AiContractError,
    ingest_ai_code_drill,
    load_code_reasoning_vault,
    mark_code_context_used,
    register_code_archetype,
    validate_ai_code_contract,
)


class TestAiCodeIngest(unittest.TestCase):

    def _create_valid_problem(self) -> dict:
        """Returns a valid, production-grade problem adhering to all contracts."""
        return {
            "id": "Q01",
            "verificationLevel": "partial",
            "archetype": "problem-solving",
            "archetypeKey": "prg-c03-token-bucket-rate-limiter",
            "context": "api_gateway_throttle",
            "level": 3,
            "category": "Trap & Edge Case",
            "commonTrapTag": "rate-limit-window-leak",
            "trapValue": "false",
            "entryPoint": "createTokenBucketRateLimiter",
            "prompt": (
                "Implement `createTokenBucketRateLimiter(options)` for an API Gateway.\n\n"
                "**Business Requirements:**\n"
                "- `capacity`: Maximum token burst capacity (positive integer).\n"
                "- `refillRatePerSecond`: Token refill rate per second.\n"
                "- `consume(cost = 1)`: Returns `true` if sufficient tokens exist, else `false`.\n"
                "- Refill must scale proportionally to elapsed time since last check."
            ),
            "inputHint": "Implement a stateful closure tracking accumulated tokens and elapsed milliseconds",
            "starterCode": (
                "function createTokenBucketRateLimiter({ capacity, refillRatePerSecond }) {\n"
                "  // TODO: implement token bucket rate limiter\n"
                "  return {\n"
                "    consume(cost = 1) {\n"
                "      return false;\n"
                "    }\n"
                "  };\n"
                "}\n\n"
                "module.exports = { createTokenBucketRateLimiter };\n"
            ),
            "solutionCode": (
                "function createTokenBucketRateLimiter({ capacity, refillRatePerSecond }) {\n"
                "  let tokens = capacity;\n"
                "  let lastTimestamp = Date.now();\n"
                "  return {\n"
                "    consume(cost = 1) {\n"
                "      const now = Date.now();\n"
                "      const elapsed = (now - lastTimestamp) / 1000;\n"
                "      tokens = Math.min(capacity, tokens + elapsed * refillRatePerSecond);\n"
                "      lastTimestamp = now;\n"
                "      if (tokens >= cost) {\n"
                "        tokens -= cost;\n"
                "        return true;\n"
                "      }\n"
                "      return false;\n"
                "    }\n"
                "  };\n"
                "}\n\n"
                "module.exports = { createTokenBucketRateLimiter };\n"
            ),
            "visibleTests": [
                {
                    "name": "should allow burst up to capacity and reject excess",
                    "testCode": (
                        "const limiter = createTokenBucketRateLimiter({ capacity: 2, refillRatePerSecond: 10 });\n"
                        "assert.strictEqual(limiter.consume(1), true);\n"
                        "assert.strictEqual(limiter.consume(1), true);\n"
                        "assert.strictEqual(limiter.consume(1), false);\n"
                    )
                }
            ],
            "hiddenTests": [
                {
                    "name": "should refill tokens over elapsed time",
                    "testCode": (
                        "const limiter = createTokenBucketRateLimiter({ capacity: 5, refillRatePerSecond: 100 });\n"
                        "assert.strictEqual(limiter.consume(5), true);\n"
                        "assert.strictEqual(limiter.consume(1), false);\n"
                    )
                }
            ],
            "steps": [
                {
                    "explain": "Track token count and timestamp in closure; refill proportionally to elapsed seconds."
                },
                {
                    "explain": "Deduct cost atomically when available; otherwise reject without modifying balance."
                }
            ]
        }

    def test_vault_crud(self):
        """Verifies loading, registering, and updating context in the Code Reasoning Vault."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            unit_code = "PRG-T01-TEST"
            vault = load_code_reasoning_vault(unit_code, vault_dir=tmp_dir)
            self.assertEqual(vault.get("unitCode"), unit_code)
            self.assertEqual(len(vault.get("archetypes", [])), 0)

            # Register archetype
            archetype = {
                "archetypeKey": "test-rate-limiter",
                "name": "Rate Limiter",
                "level": 3,
                "usedContexts": ["tenant_api"]
            }
            register_code_archetype(unit_code, archetype, vault_dir=tmp_dir)

            v_loaded = load_code_reasoning_vault(unit_code, vault_dir=tmp_dir)
            self.assertEqual(len(v_loaded["archetypes"]), 1)
            self.assertIn("tenant_api", v_loaded["archetypes"][0]["usedContexts"])

            # Mark context used
            mark_code_context_used(unit_code, "test-rate-limiter", "webhook_delivery", vault_dir=tmp_dir)
            v_updated = load_code_reasoning_vault(unit_code, vault_dir=tmp_dir)
            self.assertEqual(
                v_updated["archetypes"][0]["usedContexts"],
                ["tenant_api", "webhook_delivery"]
            )

    def test_validate_rejects_toy_code(self):
        """Verifies that Zero Toy Code Guard rejects foo/bar/test1/funcA."""
        prob = self._create_valid_problem()
        prob["prompt"] = "Suppose we have a function foo(bar) that tests baz."

        with self.assertRaises(AiContractError) as ctx:
            validate_ai_code_contract(prob)
        self.assertIn("Zero Toy Code Guard violated", str(ctx.exception))
        self.assertIn("foo", str(ctx.exception))

        # Test toy code in starterCode
        prob = self._create_valid_problem()
        prob["starterCode"] = "function funcA() { const test1 = 123; }"
        with self.assertRaises(AiContractError) as ctx:
            validate_ai_code_contract(prob)
        self.assertIn("Zero Toy Code Guard violated", str(ctx.exception))

    def test_validate_rejects_wall_of_text(self):
        """Verifies that prompts > 250 characters without bullet points or sections are rejected."""
        prob = self._create_valid_problem()
        prob["prompt"] = (
            "We need to implement a complex rate limiter algorithm for our enterprise payment gateway "
            "that receives thousands of webhooks every single second from our upstream payment provider. "
            "It must accept a capacity configuration and a refill rate per second and correctly clamp the tokens "
            "to ensure that our database is not overwhelmed by sudden traffic bursts and spikes during peak sales."
        )
        self.assertGreater(len(prob["prompt"]), 250)
        with self.assertRaises(AiContractError) as ctx:
            validate_ai_code_contract(prob)
        self.assertIn("Zero Wall-of-Text Guard violated", str(ctx.exception))

    def test_validate_rejects_hint_leak(self):
        """Verifies that hints leaking answers, tokens, or bug lines are rejected."""
        # 1. Leaking answerPlain
        prob = self._create_valid_problem()
        prob["answerPlain"] = "401"
        prob["inputHint"] = "Enter the status code: 401 Unauthorized"
        with self.assertRaises(AiContractError) as ctx:
            validate_ai_code_contract(prob)
        self.assertIn("Zero-Leak Hint Guard violated", str(ctx.exception))

        # 2. Leaking HTTP method
        prob = self._create_valid_problem()
        prob["answerPlain"] = "POST"
        prob["inputHint"] = "Use the POST method to submit payloads"
        with self.assertRaises(AiContractError) as ctx:
            validate_ai_code_contract(prob)
        self.assertIn("Zero-Leak Hint Guard violated", str(ctx.exception))

        # 3. Leaking defective line number
        prob = self._create_valid_problem()
        prob["archetype"] = "debugging"
        prob["correctLine"] = 4
        prob["inputHint"] = "Inspect line 4 where the timestamp is incorrectly updated"
        with self.assertRaises(AiContractError) as ctx:
            validate_ai_code_contract(prob)
        self.assertIn("Zero-Leak Hint Guard violated", str(ctx.exception))

    def test_validate_rejects_failing_canonical_solution(self):
        """Verifies that a canonical solution that fails tests is rejected."""
        prob = self._create_valid_problem()
        # Buggy solution that always returns false
        prob["solutionCode"] = (
            "function createTokenBucketRateLimiter() {\n"
            "  return { consume: () => false };\n"
            "}\n"
            "module.exports = { createTokenBucketRateLimiter };\n"
        )
        with self.assertRaises(AiContractError) as ctx:
            validate_ai_code_contract(prob)
        self.assertIn("Canonical solution failed test suite", str(ctx.exception))

    def test_validate_rejects_green_starter_code_for_debugging(self):
        """Verifies that a debugging starterCode must fail at least one reproducer test (Red before Green)."""
        prob = self._create_valid_problem()
        prob["archetype"] = "debugging"
        # Starter code is already fully correct (doesn't reproduce any bug)
        prob["starterCode"] = prob["solutionCode"]

        with self.assertRaises(AiContractError) as ctx:
            validate_ai_code_contract(prob)
        self.assertIn("Red-before-Green invariant violated", str(ctx.exception))

    def test_validate_rejects_unverified_machine_level(self):
        """Verifies that AI-generated code problems must be verificationLevel='partial'."""
        prob = self._create_valid_problem()
        prob["verificationLevel"] = "machine-verified"

        with self.assertRaises(AiContractError) as ctx:
            validate_ai_code_contract(prob)
        self.assertIn("must have verificationLevel='partial'", str(ctx.exception))

    def test_full_ingest_pipeline_in_temp_dir(self):
        """Tests full end-to-end ingest into temporary data and workspace directories."""
        with tempfile.TemporaryDirectory() as tmp_data_dir, tempfile.TemporaryDirectory() as tmp_ws_dir:
            prob = self._create_valid_problem()
            drill_doc = {
                "unitCode": "PRG-T01-C03",
                "drillId": "DRL-PRG-T01-C03-TEST01",
                "environment": "node-vanilla",
                "sourceAttribution": {
                    "curriculum": "Antigravity Autonomous Engineering Synthesis",
                    "license": "CC BY 4.0"
                },
                "problems": [prob]
            }

            saved = ingest_ai_code_drill(
                drill_doc,
                data_root=tmp_data_dir,
                workspace_root=tmp_ws_dir,
                vault_dir=tmp_data_dir
            )

            # 1. Check Drill JSON persistence
            expected_json = os.path.join(tmp_data_dir, "PRG-T01-C03", "DRL-PRG-T01-C03-TEST01.json")
            self.assertTrue(os.path.exists(expected_json))

            # 2. Check Local IDE Workspace Scaffolding
            ws_dir = os.path.join(tmp_ws_dir, "drills", "workspace", "DRL-PRG-T01-C03-TEST01")
            self.assertTrue(os.path.exists(ws_dir))
            self.assertTrue(os.path.exists(os.path.join(ws_dir, "package.json")))
            self.assertTrue(os.path.exists(os.path.join(ws_dir, "README.md")))
            self.assertTrue(os.path.exists(os.path.join(ws_dir, "Q01_createTokenBucketRateLimiter.js")))
            self.assertTrue(os.path.exists(os.path.join(ws_dir, "Q01_createTokenBucketRateLimiter.test.js")))
            self.assertTrue(os.path.exists(os.path.join(ws_dir, ".canonical", "Q01_createTokenBucketRateLimiter.js")))

            # 3. Check Deep Links Contract
            p0 = saved["problems"][0]
            self.assertIn("vscodeFolderUrl", p0)
            self.assertIn("cursorFolderUrl", p0)
            self.assertTrue(p0["vscodeFolderUrl"].startswith("vscode://file/"))
            # Must target folder, not single file
            self.assertEqual(p0["vscodeFolderUrl"], f"vscode://file/{os.path.abspath(ws_dir)}")


if __name__ == "__main__":
    unittest.main()
