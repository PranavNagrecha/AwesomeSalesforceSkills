"""Tests for P10 Org Health Assessment normalizer and inputs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "mcp" / "sfskills-mcp" / "tests" / "fixtures" / "health"


class P10NormalizeTests(unittest.TestCase):
    def test_happy_fixture(self):
        from pipelines.product.org_snapshot_result import normalize_org_snapshot

        payload = json.loads((FIXTURES / "happy.json").read_text(encoding="utf-8"))
        out = normalize_org_snapshot(payload)
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(len(out["signals"]), 1)
        self.assertTrue(out["signals"][0]["evidence_id"].startswith("ev:hlt:"))
        self.assertEqual(out["evidence_ids"], normalize_org_snapshot(payload)["evidence_ids"])


class P10InputTests(unittest.TestCase):

    def test_validate_requires_source(self):
        from pipelines.product.command_inputs import validate_assess_org_health_inputs

        self.assertIn("missing_evidence_source", validate_assess_org_health_inputs({}))

    def test_validate_accepts_fixture_path(self):
        from pipelines.product.command_inputs import validate_assess_org_health_inputs

        path = FIXTURES / "happy.json"
        errors = validate_assess_org_health_inputs({"result_path": str(path)})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
