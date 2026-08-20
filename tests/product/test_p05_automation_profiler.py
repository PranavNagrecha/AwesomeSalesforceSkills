"""Tests for P05 Automation Transaction Profiler normalizer and inputs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "mcp" / "sfskills-mcp" / "tests" / "fixtures" / "automation"


class P05NormalizeTests(unittest.TestCase):
    def test_happy_fixture(self):
        from pipelines.product.automation_inventory_result import normalize_automation_inventory

        payload = json.loads((FIXTURES / "happy.json").read_text(encoding="utf-8"))
        out = normalize_automation_inventory(payload)
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(len(out["automations"]), 1)
        self.assertTrue(out["automations"][0]["evidence_id"].startswith("ev:aut:"))
        self.assertEqual(out["evidence_ids"], normalize_automation_inventory(payload)["evidence_ids"])


class P05InputTests(unittest.TestCase):

    def test_validate_requires_fields(self):
        from pipelines.product.command_inputs import validate_profile_automation_inputs

        errors = validate_profile_automation_inputs({})
        self.assertTrue(any(e.startswith("missing_") for e in errors))
        self.assertTrue(any("object" in e for e in errors))

    def test_validate_accepts_complete_inputs(self):
        from pipelines.product.command_inputs import validate_profile_automation_inputs

        errors = validate_profile_automation_inputs({"object": "sample", "operation": "sample"})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
