"""Tests for get_apex_test_run normalization and refusal paths."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

FIXTURES = HERE / "fixtures" / "apex"


class ApexTestRunToolTests(unittest.TestCase):
    def test_fixture_assertion(self):
        from sfskills_mcp import apex_test

        out = apex_test.get_apex_test_run_from_file(str(FIXTURES / "assertion_failure.json"))
        self.assertTrue(out["ok"])
        self.assertEqual(out["method_failures"][0]["failure_kind"], "assertion")

    def test_malformed_id(self):
        from sfskills_mcp import apex_test

        out = apex_test.get_apex_test_run("not-a-run")
        self.assertFalse(out.get("ok", True))
        self.assertEqual(out["error"], "malformed_test_run_id")

    def test_missing_id(self):
        from sfskills_mcp import apex_test

        out = apex_test.get_apex_test_run("")
        self.assertEqual(out["error"], "test_run_id is required")

    def test_fixture_not_found(self):
        from sfskills_mcp import apex_test

        out = apex_test.get_apex_test_run_from_file("/no/such/file.json")
        self.assertEqual(out["error"], "fixture_not_found")

    @mock.patch("sfskills_mcp.apex_test.sf_cli.run_sf_json")
    def test_cli_error_path(self, run_sf_json):
        from sfskills_mcp import apex_test

        run_sf_json.return_value = {"error": "not found", "status": 1}
        out = apex_test.get_apex_test_run("707000000000001AAA")
        self.assertFalse(out.get("ok", True))
        self.assertIn(out["error"], {"unknown_or_expired_run", "cli_error"})


if __name__ == "__main__":
    unittest.main()
