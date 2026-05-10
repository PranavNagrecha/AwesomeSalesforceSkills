"""Tests for sandbox-vs-production inference from instance_url.

Motivated by ExampleOrg Dev PN where ``sf org display`` returned
``isSandbox=null`` even though the URL ``*.sandbox.my.salesforce.com``
makes the classification obvious. The MCP needs to surface a reliable
``is_sandbox`` flag because consumers (including LLM agents) decide
risk policy on it.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import org  # noqa: E402


class InferSandboxFromUrlTest(unittest.TestCase):
    def test_my_domain_sandbox(self) -> None:
        cases = (
            "https://acme--devSandbox.sandbox.my.salesforce.com",
            "https://something.sandbox.my.salesforce.com",
            "acme--devSandbox.sandbox.my.salesforce.com/",
        )
        for url in cases:
            self.assertTrue(org._infer_sandbox_from_url(url), f"URL {url!r} not flagged sandbox")

    def test_my_domain_production(self) -> None:
        cases = (
            "https://acme.my.salesforce.com",
            "https://something.my.salesforce.com",
            "ACME.MY.SALESFORCE.COM",
        )
        for url in cases:
            self.assertFalse(org._infer_sandbox_from_url(url), f"URL {url!r} wrongly flagged sandbox")

    def test_legacy_cs_pods_are_sandbox(self) -> None:
        for url in ("https://cs17.my.salesforce.com", "https://cs2.salesforce.com", "cs200.salesforce.com"):
            self.assertTrue(org._infer_sandbox_from_url(url), f"URL {url!r} not flagged sandbox")

    def test_scratch_org(self) -> None:
        self.assertTrue(org._infer_sandbox_from_url("https://something.scratch.my.salesforce.com"))

    def test_developer_org(self) -> None:
        # Developer orgs are non-production; we treat them as sandbox-class
        # for risk policy purposes.
        self.assertTrue(org._infer_sandbox_from_url("https://something.develop.my.salesforce.com"))

    def test_legacy_production_pod(self) -> None:
        # na12.salesforce.com (production legacy pod) should be classified
        # as production (False).
        self.assertFalse(org._infer_sandbox_from_url("https://na12.salesforce.com"))
        self.assertFalse(org._infer_sandbox_from_url("https://eu8.salesforce.com"))

    def test_invalid_input(self) -> None:
        self.assertIsNone(org._infer_sandbox_from_url(None))
        self.assertIsNone(org._infer_sandbox_from_url(""))
        self.assertIsNone(org._infer_sandbox_from_url(42))
        # Non-Salesforce domain — can't classify.
        self.assertIsNone(org._infer_sandbox_from_url("https://example.com"))


class DescribeOrgSandboxResolutionTest(unittest.TestCase):
    """Ensure describe_org honors CLI value when set; falls back to URL
    inference when CLI returns null."""

    def _mock_run(self, result: dict) -> mock.Mock:
        return mock.Mock(return_value={"result": result})

    def test_cli_value_takes_precedence(self) -> None:
        # CLI says NOT sandbox, URL looks like sandbox.
        # CLI wins → is_sandbox=False, source=cli.
        with mock.patch.object(org.sf_cli, "run_sf_json", self._mock_run({
            "id": "00DVB000",
            "instanceUrl": "https://acme--devSandbox.sandbox.my.salesforce.com",
            "isSandbox": False,
        })):
            out = org.describe_org()
        self.assertEqual(out["is_sandbox"], False)
        self.assertEqual(out["is_sandbox_source"], "cli")

    def test_url_inference_when_cli_null(self) -> None:
        with mock.patch.object(org.sf_cli, "run_sf_json", self._mock_run({
            "id": "00DVB000",
            "instanceUrl": "https://acme--devSandbox.sandbox.my.salesforce.com",
            # No isSandbox field.
        })):
            out = org.describe_org()
        self.assertEqual(out["is_sandbox"], True)
        self.assertEqual(out["is_sandbox_source"], "inferred-from-url")

    def test_neither_cli_nor_url_can_decide(self) -> None:
        with mock.patch.object(org.sf_cli, "run_sf_json", self._mock_run({
            "id": "00DVB000",
            "instanceUrl": "https://example.com",
        })):
            out = org.describe_org()
        # is_sandbox missing or None → both stripped from output dict.
        self.assertNotIn("is_sandbox", out)
        self.assertNotIn("is_sandbox_source", out)


if __name__ == "__main__":
    unittest.main()
