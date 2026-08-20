"""Tests for P08 Integration Incident Triage normalizer and inputs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "mcp" / "sfskills-mcp" / "tests" / "fixtures" / "integration"


class P08NormalizeTests(unittest.TestCase):
    def test_happy_fixture(self):
        from pipelines.product.integration_config_result import normalize_integration_config

        payload = json.loads((FIXTURES / "happy.json").read_text(encoding="utf-8"))
        out = normalize_integration_config(payload)
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(len(out["events"]), 1)
        self.assertTrue(out["events"][0]["evidence_id"].startswith("ev:int:"))
        self.assertEqual(out["evidence_ids"], normalize_integration_config(payload)["evidence_ids"])


class P08InputTests(unittest.TestCase):

    def test_validate_requires_fields(self):
        from pipelines.product.command_inputs import validate_triage_integration_inputs

        errors = validate_triage_integration_inputs({})
        self.assertTrue(any(e.startswith("missing_") for e in errors))
        self.assertTrue(any("integration" in e for e in errors))

    def test_validate_accepts_complete_inputs(self):
        from pipelines.product.command_inputs import validate_triage_integration_inputs

        errors = validate_triage_integration_inputs({"integration": "sample", "time_window": "sample"})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
