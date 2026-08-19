"""Tests for get_deployment_result normalization and refusal paths."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
ROOT = HERE.parents[2]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sfskills_mcp import deploy  # noqa: E402

FIXTURES = HERE / "fixtures" / "deploy"


class GetDeploymentResultTests(unittest.TestCase):
    def test_from_file_component_failures(self):
        out = deploy.get_deployment_result_from_file(str(FIXTURES / "component_failures.json"))
        self.assertTrue(out["ok"])
        self.assertTrue(out["evidence_ids"])

    def test_malformed_file(self):
        out = deploy.get_deployment_result_from_file(str(FIXTURES / "malformed.txt"))
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "malformed_json")

    def test_malformed_job_id(self):
        out = deploy.get_deployment_result("not-a-job")
        self.assertEqual(out["error"], "malformed_job_id")

    def test_missing_job_id(self):
        out = deploy.get_deployment_result("")
        self.assertIn("job_id", out["error"] + out.get("refusal_code", ""))

    def test_cli_timeout(self):
        fake = {"status": 124, "error": "sf command timed out after 90s", "args": ["project", "deploy", "report"]}
        with mock.patch("sfskills_mcp.deploy.sf_cli.run_sf_json", return_value=fake):
            out = deploy.get_deployment_result("0Af000000000001AAA")
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "cli_timeout")

    def test_unauthenticated(self):
        fake = {"status": 1, "error": "No default org is set. Please authenticate.", "args": []}
        with mock.patch("sfskills_mcp.deploy.sf_cli.run_sf_json", return_value=fake):
            out = deploy.get_deployment_result("0Af000000000001AAA")
        self.assertEqual(out["error"], "unauthenticated_org")

    def test_unknown_job(self):
        fake = {"status": 1, "error": "Couldn't find a job with id 0Af000000000001AAA", "args": []}
        with mock.patch("sfskills_mcp.deploy.sf_cli.run_sf_json", return_value=fake):
            out = deploy.get_deployment_result("0Af000000000001AAA")
        self.assertEqual(out["error"], "unknown_or_expired_job")

    def test_redaction_shaped_error(self):
        fake = {"status": 1, "error": "access token leaked 00Dxx!abcdefghijklmnopqr", "args": []}
        with mock.patch("sfskills_mcp.deploy.sf_cli.run_sf_json", return_value=fake):
            out = deploy.get_deployment_result("0Af000000000001AAA")
        self.assertEqual(out["error"], "redacted_auth_error")

    def test_no_use_most_recent_in_source(self):
        text = Path(deploy.__file__).read_text(encoding="utf-8")
        self.assertNotIn("use-most-recent", text)
        self.assertNotIn("deploy start", text)


if __name__ == "__main__":
    unittest.main()
