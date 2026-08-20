"""Tests for P07 Security Posture Review normalizer and inputs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "mcp" / "sfskills-mcp" / "tests" / "fixtures" / "security"


class P07NormalizeTests(unittest.TestCase):
    def test_happy_fixture(self):
        from pipelines.product.code_analysis_result import normalize_code_analysis

        payload = json.loads((FIXTURES / "happy.json").read_text(encoding="utf-8"))
        out = normalize_code_analysis(payload)
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(len(out["findings"]), 1)
        self.assertTrue(out["findings"][0]["evidence_id"].startswith("ev:sec:"))
        self.assertEqual(out["evidence_ids"], normalize_code_analysis(payload)["evidence_ids"])


class P07InputTests(unittest.TestCase):

    def test_validate_requires_fields(self):
        from pipelines.product.command_inputs import validate_review_security_posture_inputs

        errors = validate_review_security_posture_inputs({})
        self.assertTrue(any(e.startswith("missing_") for e in errors))
        self.assertTrue(any("scope" in e for e in errors))

    def test_validate_accepts_complete_inputs(self):
        from pipelines.product.command_inputs import validate_review_security_posture_inputs

        errors = validate_review_security_posture_inputs({"scope": "sample"})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
