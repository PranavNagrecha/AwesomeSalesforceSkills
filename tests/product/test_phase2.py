"""Phase 2 product tests: Apex test normalizer, inputs, policy."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "mcp" / "sfskills-mcp" / "tests" / "fixtures" / "apex"


class ApexNormalizeTests(unittest.TestCase):
    def _load(self, name: str):
        from pipelines.product.apex_test_result import normalize_apex_test_run

        payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
        return normalize_apex_test_run(payload)

    def test_assertion_failure_kind(self):
        out = self._load("assertion_failure.json")
        self.assertTrue(out["ok"])
        self.assertEqual(out["method_failures"][0]["failure_kind"], "assertion")
        self.assertEqual(out["method_failures"][0]["class_name"], "AccountServiceTest")

    def test_mixed_dml_classification(self):
        out = self._load("mixed_dml.json")
        self.assertEqual(out["method_failures"][0]["failure_kind"], "mixed_dml")

    def test_shared_root_clustering(self):
        out = self._load("shared_root.json")
        self.assertGreaterEqual(len(out["shared_root_clusters"]), 1)
        cluster = out["shared_root_clusters"][0]
        self.assertGreaterEqual(cluster["occurrence_count"], 3)
        self.assertIn("SharedRootHelper.load", cluster["stack_root"])

    def test_stable_evidence_ids(self):
        first = self._load("assertion_failure.json")
        second = self._load("assertion_failure.json")
        self.assertEqual(first["evidence_ids"], second["evidence_ids"])

    def test_pagination(self):
        from pipelines.product.apex_test_result import normalize_apex_test_run

        tests = [
            {
                "FullName": f"BulkTest.testMethod{i}",
                "MethodName": f"testMethod{i}",
                "Outcome": "Fail",
                "Message": f"fail {i}",
                "StackTrace": f"Class.BulkTest.testMethod{i}: line {i}, column 1",
                "ApexClass": {"Name": "BulkTest"},
            }
            for i in range(25)
        ]
        payload = {
            "result": {
                "summary": {"outcome": "Failed", "testRunId": "707000000000099AAA"},
                "tests": tests,
            }
        }
        page0 = normalize_apex_test_run(payload, method_limit=10, cursor=None)
        self.assertTrue(page0["truncated"])
        self.assertEqual(page0["next_cursor"], "10")


class ApexInputTests(unittest.TestCase):
    def test_validate_requires_source(self):
        from pipelines.product.command_inputs import validate_triage_apex_inputs

        self.assertIn("missing_evidence_source", validate_triage_apex_inputs({}))

    def test_validate_malformed_run_id(self):
        from pipelines.product.command_inputs import validate_triage_apex_inputs

        errors = validate_triage_apex_inputs({"test_run_id": "0Af000000000001AAA"})
        self.assertIn("malformed_test_run_id", errors)

    def test_validate_accepts_fixture_path(self):
        from pipelines.product.command_inputs import validate_triage_apex_inputs

        path = FIXTURES / "assertion_failure.json"
        errors = validate_triage_apex_inputs({"result_path": str(path)})
        self.assertEqual(errors, [])


class ApexPolicyTests(unittest.TestCase):
    def test_mcp_get_apex_test_run_allowed(self):
        from pipelines.product.policy import evaluate_mcp_call

        out = evaluate_mcp_call("get_apex_test_run", {"test_run_id": "707000000000001AAA"})
        self.assertEqual(out["decision"], "allow")

    def test_sf_apex_get_test_allowed(self):
        from pipelines.product.policy import evaluate_shell_command

        out = evaluate_shell_command("sf apex get test --test-run-id 707000000000001AAA --json")
        self.assertEqual(out["decision"], "allow")

    def test_sf_apex_run_denied(self):
        from pipelines.product.policy import evaluate_shell_command

        out = evaluate_shell_command("sf apex run test --json")
        self.assertEqual(out["decision"], "deny")


if __name__ == "__main__":
    unittest.main()
