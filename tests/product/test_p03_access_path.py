"""Tests for P03 Access Path Explainer normalizer and inputs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "mcp" / "sfskills-mcp" / "tests" / "fixtures" / "access"


class P03NormalizeTests(unittest.TestCase):
    def test_happy_fixture(self):
        from pipelines.product.user_access_result import normalize_user_access

        payload = json.loads((FIXTURES / "happy.json").read_text(encoding="utf-8"))
        out = normalize_user_access(payload)
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(len(out["layers"]), 1)
        self.assertTrue(out["layers"][0]["evidence_id"].startswith("ev:acc:"))
        self.assertEqual(out["evidence_ids"], normalize_user_access(payload)["evidence_ids"])


class P03InputTests(unittest.TestCase):

    def test_validate_requires_fields(self):
        from pipelines.product.command_inputs import validate_why_cant_user_inputs

        errors = validate_why_cant_user_inputs({})
        self.assertTrue(any(e.startswith("missing_") for e in errors))
        self.assertTrue(any("user" in e for e in errors))

    def test_validate_accepts_complete_inputs(self):
        from pipelines.product.command_inputs import validate_why_cant_user_inputs

        errors = validate_why_cant_user_inputs({"user": "sample", "resource": "sample", "operation": "sample"})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
