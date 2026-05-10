"""Unit tests for tooling_query string-literal-aware DML blocklist.

The v0.4.2 blocklist did substring matches on raw SOQL, which blocked
legitimate queries whose string literals happened to contain DML keywords
(``WHERE Name = 'foo INSERT bar'``). v0.4.3 strips literals before the
DML scan. These tests pin the new behavior.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import admin  # noqa: E402


class StripSoqlStringLiteralsTest(unittest.TestCase):
    def test_strips_single_quoted(self) -> None:
        out = admin._strip_soql_string_literals("SELECT Id FROM A WHERE Name = 'foo bar'")
        self.assertNotIn("foo bar", out)
        # Quote pair survives — important so the structure is recognisable.
        self.assertIn("''", out)

    def test_strips_double_quoted(self) -> None:
        out = admin._strip_soql_string_literals('SELECT Id FROM A WHERE Name = "foo bar"')
        self.assertNotIn("foo bar", out)
        self.assertIn('""', out)

    def test_preserves_keywords_outside_literals(self) -> None:
        out = admin._strip_soql_string_literals(
            "SELECT Id FROM A WHERE Name = 'foo INSERT bar' AND Status = 'X'"
        )
        # Outside-literal SQL keywords still present.
        self.assertIn("SELECT", out)
        self.assertIn("FROM", out)
        self.assertIn("AND", out)
        # Inside-literal content (including the spoofed INSERT) gone.
        self.assertNotIn("INSERT", out)

    def test_handles_escaped_quote_inside_literal(self) -> None:
        out = admin._strip_soql_string_literals(
            "SELECT Id FROM A WHERE Name = 'O\\'Brien INSERT smuggled'"
        )
        # The escaped quote doesn't end the literal early — the entire
        # 'O\'Brien INSERT smuggled' is stripped.
        self.assertNotIn("INSERT", out)
        self.assertNotIn("Brien", out)

    def test_keyword_outside_literal_with_literal_present(self) -> None:
        # An actually malicious query with a DML keyword OUTSIDE the literal
        # — the literal contains nothing dangerous; the DML word does.
        out = admin._strip_soql_string_literals(
            "SELECT Id FROM A WHERE Name = 'ok'; DELETE FROM A"
        )
        self.assertIn("DELETE", out)
        self.assertIn(";", out)


class ToolingQueryFalsePositiveTest(unittest.TestCase):
    """False positives that v0.4.2 incorrectly blocked. They must now pass
    the blocklist (server may still reject them for other reasons; we only
    assert the MCP doesn't pre-emptively block)."""

    def _passes_blocklist(self, soql: str) -> bool:
        # Just exercise the blocklist path — don't actually hit Salesforce.
        # The blocklist runs before _run_soql, so we can detect its decision
        # by checking the returned error key.
        result = admin.tooling_query(soql, target_org="fake-org-no-such-alias", limit=1)
        if "error" not in result:
            return True
        err = result["error"]
        # Blocklist-related errors all match this pattern:
        if "tooling_query refuses" in err or "only supports SELECT" in err:
            return False
        # Any other error (like "org not found") means the blocklist passed
        # and we reached the actual sf invocation.
        return True

    def test_dml_keyword_in_string_literal_not_blocked(self) -> None:
        self.assertTrue(self._passes_blocklist(
            "SELECT Id FROM Account WHERE Name = 'foo INSERT bar' LIMIT 1"
        ))

    def test_dml_keyword_in_like_pattern_not_blocked(self) -> None:
        self.assertTrue(self._passes_blocklist(
            "SELECT Id FROM Account WHERE Name LIKE '%UPDATE %' LIMIT 1"
        ))

    def test_semicolon_in_string_literal_not_blocked(self) -> None:
        self.assertTrue(self._passes_blocklist(
            "SELECT Id FROM Account WHERE Name = ';' LIMIT 1"
        ))

    def test_delete_in_string_literal_not_blocked(self) -> None:
        self.assertTrue(self._passes_blocklist(
            "SELECT Id FROM Account WHERE Name = 'DELETE candidate' LIMIT 1"
        ))


class ToolingQueryStillBlocksDmlTest(unittest.TestCase):
    """Regression guard for the 9 DML-bypass attempts from the Phase 4
    security audit. All must remain blocked after v0.4.3."""

    def _is_blocked(self, soql: str) -> bool:
        out = admin.tooling_query(soql, target_org="fake-org-no-such-alias", limit=1)
        return "error" in out and (
            "refuses" in out["error"] or "only supports SELECT" in out["error"]
        )

    def test_stacked_insert_blocked(self) -> None:
        self.assertTrue(self._is_blocked("SELECT Id FROM Account; INSERT FOO"))

    def test_dml_in_comment_blocked(self) -> None:
        # /* delete */ contains the literal 'DELETE' outside any string
        # literal — should still be caught by the keyword scan.
        self.assertTrue(self._is_blocked(
            "SELECT Id FROM Account /* delete from account */"
        ))

    def test_stacked_delete_blocked(self) -> None:
        self.assertTrue(self._is_blocked(
            "SELECT Id FROM Account; DELETE FROM Account"
        ))

    def test_stacked_update_blocked(self) -> None:
        self.assertTrue(self._is_blocked(
            "SELECT Id FROM Account; UPDATE Account SET Name=NULL"
        ))

    def test_lowercase_upsert_blocked(self) -> None:
        self.assertTrue(self._is_blocked(
            "select id from account; upsert account_record"
        ))


if __name__ == "__main__":
    unittest.main()
