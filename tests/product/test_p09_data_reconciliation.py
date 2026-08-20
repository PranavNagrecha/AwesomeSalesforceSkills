"""Tests for P09 Data Migration Reconciliation normalizer and inputs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "mcp" / "sfskills-mcp" / "tests" / "fixtures" / "data"


class P09NormalizeTests(unittest.TestCase):
    def test_happy_fixture(self):
        from pipelines.product.data_load_result import normalize_data_load

        payload = json.loads((FIXTURES / "happy.json").read_text(encoding="utf-8"))
        out = normalize_data_load(payload)
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(len(out["rejects"]), 1)
        self.assertTrue(out["rejects"][0]["evidence_id"].startswith("ev:dml:"))
        self.assertEqual(out["evidence_ids"], normalize_data_load(payload)["evidence_ids"])


class P09InputTests(unittest.TestCase):

    def test_validate_requires_fields(self):
        from pipelines.product.command_inputs import validate_reconcile_data_load_inputs

        errors = validate_reconcile_data_load_inputs({})
        self.assertTrue(any(e.startswith("missing_") for e in errors))
        self.assertTrue(any("migration_manifest" in e for e in errors))

    def test_validate_accepts_complete_inputs(self):
        from pipelines.product.command_inputs import validate_reconcile_data_load_inputs

        path = FIXTURES / "happy.json"
        errors = validate_reconcile_data_load_inputs({"migration_manifest": "manifest.json", "result_files": str(path)})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
