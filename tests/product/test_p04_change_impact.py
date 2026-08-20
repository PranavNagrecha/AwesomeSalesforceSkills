"""Tests for P04 Change Impact Planner normalizer and inputs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "mcp" / "sfskills-mcp" / "tests" / "fixtures" / "impact"


class P04NormalizeTests(unittest.TestCase):
    def test_happy_fixture(self):
        from pipelines.product.component_dependency_result import normalize_component_dependency

        payload = json.loads((FIXTURES / "happy.json").read_text(encoding="utf-8"))
        out = normalize_component_dependency(payload)
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(len(out["dependencies"]), 1)
        self.assertTrue(out["dependencies"][0]["evidence_id"].startswith("ev:dep:"))
        self.assertEqual(out["evidence_ids"], normalize_component_dependency(payload)["evidence_ids"])


class P04InputTests(unittest.TestCase):

    def test_validate_requires_fields(self):
        from pipelines.product.command_inputs import validate_plan_metadata_change_inputs

        errors = validate_plan_metadata_change_inputs({})
        self.assertTrue(any(e.startswith("missing_") for e in errors))
        self.assertTrue(any("component" in e for e in errors))

    def test_validate_accepts_complete_inputs(self):
        from pipelines.product.command_inputs import validate_plan_metadata_change_inputs

        errors = validate_plan_metadata_change_inputs({"component": "sample", "proposed_change": "sample"})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
