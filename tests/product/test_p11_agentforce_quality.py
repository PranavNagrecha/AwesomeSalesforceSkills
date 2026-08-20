"""Tests for P11 Agentforce Quality Engineer normalizer and inputs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "mcp" / "sfskills-mcp" / "tests" / "fixtures" / "agentforce"


class P11NormalizeTests(unittest.TestCase):
    def test_happy_fixture(self):
        from pipelines.product.agentforce_test_result import normalize_agentforce_test

        payload = json.loads((FIXTURES / "happy.json").read_text(encoding="utf-8"))
        out = normalize_agentforce_test(payload)
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(len(out["tests"]), 1)
        self.assertTrue(out["tests"][0]["evidence_id"].startswith("ev:afx:"))
        self.assertEqual(out["evidence_ids"], normalize_agentforce_test(payload)["evidence_ids"])


class P11InputTests(unittest.TestCase):

    def test_validate_requires_fields(self):
        from pipelines.product.command_inputs import validate_review_agentforce_agent_inputs

        errors = validate_review_agentforce_agent_inputs({})
        self.assertTrue(any(e.startswith("missing_") for e in errors))
        self.assertTrue(any("agent_metadata_path" in e for e in errors))

    def test_validate_accepts_complete_inputs(self):
        from pipelines.product.command_inputs import validate_review_agentforce_agent_inputs

        errors = validate_review_agentforce_agent_inputs({"agent_metadata_path": "sample", "agent_developer_name": "sample"})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
