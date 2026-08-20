"""Tests for P06 Release Readiness Review normalizer and inputs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "mcp" / "sfskills-mcp" / "tests" / "fixtures" / "release"


class P06NormalizeTests(unittest.TestCase):
    def test_happy_fixture(self):
        from pipelines.product.flow_test_result import normalize_flow_test

        payload = json.loads((FIXTURES / "happy.json").read_text(encoding="utf-8"))
        out = normalize_flow_test(payload)
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(len(out["tests"]), 1)
        self.assertTrue(out["tests"][0]["evidence_id"].startswith("ev:rel:"))
        self.assertEqual(out["evidence_ids"], normalize_flow_test(payload)["evidence_ids"])


class P06InputTests(unittest.TestCase):

    def test_validate_requires_fields(self):
        from pipelines.product.command_inputs import validate_review_release_readiness_inputs

        errors = validate_review_release_readiness_inputs({})
        self.assertTrue(any(e.startswith("missing_") for e in errors))
        self.assertTrue(any("release_scope" in e for e in errors))

    def test_validate_accepts_complete_inputs(self):
        from pipelines.product.command_inputs import validate_review_release_readiness_inputs

        errors = validate_review_release_readiness_inputs({"release_scope": "sample"})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
