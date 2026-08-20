"""Tests for P12 Multi-Org Drift Analysis normalizer and inputs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "mcp" / "sfskills-mcp" / "tests" / "fixtures" / "drift"


class P12NormalizeTests(unittest.TestCase):
    def test_happy_fixture(self):
        from pipelines.product.org_compare_result import normalize_org_compare

        payload = json.loads((FIXTURES / "happy.json").read_text(encoding="utf-8"))
        out = normalize_org_compare(payload)
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(len(out["diffs"]), 1)
        self.assertTrue(out["diffs"][0]["evidence_id"].startswith("ev:dft:"))
        self.assertEqual(out["evidence_ids"], normalize_org_compare(payload)["evidence_ids"])


class P12InputTests(unittest.TestCase):

    def test_validate_requires_fields(self):
        from pipelines.product.command_inputs import validate_compare_orgs_inputs

        errors = validate_compare_orgs_inputs({})
        self.assertTrue(any(e.startswith("missing_") for e in errors))
        self.assertTrue(any("left_org_or_snapshot" in e for e in errors))

    def test_validate_accepts_complete_inputs(self):
        from pipelines.product.command_inputs import validate_compare_orgs_inputs

        errors = validate_compare_orgs_inputs({"left_org_or_snapshot": "sample", "right_org_or_snapshot": "sample"})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
