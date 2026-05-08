"""Tests for the Tier-C knowledge-search tools in ``library.py``.

These tests run against the real on-disk corpus (agents/, templates/,
standards/decision-trees/). The corpus moves slowly enough that asserting on
specific top hits is a stable signal — if the canonical answer for "trigger
handler" stops being ``apex/TriggerHandler.cls`` something has gone wrong.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import library  # noqa: E402


class SearchAgentsTest(unittest.TestCase):
    def test_query_required(self) -> None:
        out = library.search_agents("")
        self.assertIn("error", out)

    def test_finds_audit_router_for_audit_query(self) -> None:
        out = library.search_agents("audit picklists", limit=5)
        names = [a["name"] for a in out["agents"]]
        self.assertIn("audit-router", names[:3], f"top hits: {names}")

    def test_finds_lwc_auditor_for_lwc_query(self) -> None:
        out = library.search_agents("lightning web component bundle", limit=5)
        names = [a["name"] for a in out["agents"]]
        self.assertTrue(
            "lwc-auditor" in names[:3] or "lwc-builder" in names[:3] or "lwc-debugger" in names[:3],
            f"top hits: {names}",
        )

    def test_each_result_has_required_fields(self) -> None:
        out = library.search_agents("trigger", limit=3)
        for a in out["agents"]:
            for field in ("name", "title", "summary", "path", "score"):
                self.assertIn(field, a)

    def test_unknown_terms_return_empty_not_error(self) -> None:
        out = library.search_agents("xyzzy_no_such_term_123", limit=3)
        self.assertEqual(out["result_count"], 0)
        self.assertNotIn("error", out)


class SearchTemplatesTest(unittest.TestCase):
    def test_finds_trigger_handler_template(self) -> None:
        out = library.search_templates("trigger handler", limit=5)
        paths_ = [t["path"] for t in out["templates"]]
        self.assertIn("apex/TriggerHandler.cls", paths_[:3])

    def test_returns_resource_uri_with_double_underscore(self) -> None:
        out = library.search_templates("trigger handler", limit=1)
        if out["templates"]:
            uri = out["templates"][0]["uri"]
            self.assertTrue(uri.startswith("sfskills://template/"))
            # The URI MUST use ``__`` separators because MCP URI templates
            # only match a single path segment — same convention as
            # resources.read_template.
            self.assertIn("__", uri)

    def test_preview_is_short(self) -> None:
        out = library.search_templates("trigger", limit=1)
        if out["templates"]:
            preview = out["templates"][0]["preview"]
            self.assertLessEqual(len(preview.splitlines()), 8)


class SearchDecisionTreesTest(unittest.TestCase):
    def test_finds_automation_selection_for_flow_apex(self) -> None:
        out = library.search_decision_trees("flow vs apex", limit=5)
        names = [t["name"] for t in out["trees"]]
        self.assertIn("automation-selection", names[:3], f"top hits: {names}")

    def test_returns_best_section(self) -> None:
        out = library.search_decision_trees("flow vs apex", limit=3)
        for t in out["trees"]:
            # best_section is None when no sub-section scored — but for
            # a real query at least the top hit should have one.
            if t["score"] > 0:
                self.assertIsNotNone(
                    t["best_section"],
                    f"{t['name']} matched but no best_section",
                )

    def test_excludes_readme(self) -> None:
        out = library.search_decision_trees("decision", limit=10)
        names = {t["name"] for t in out["trees"]}
        self.assertNotIn("README", names)


class GetTemplateTest(unittest.TestCase):
    def test_returns_full_body_for_known_template(self) -> None:
        out = library.get_template("apex/TriggerHandler.cls")
        self.assertNotIn("error", out)
        self.assertIn("TriggerHandler", out["body"])
        self.assertGreater(out["byte_size"], 200)

    def test_invalid_path_returns_error(self) -> None:
        out = library.get_template("../etc/passwd")
        self.assertIn("error", out)


class GetDecisionTreeTest(unittest.TestCase):
    def test_returns_body_for_known_tree(self) -> None:
        out = library.get_decision_tree("automation-selection")
        self.assertNotIn("error", out)
        self.assertGreater(out["byte_size"], 500)
        self.assertIn("Automation", out["body"])

    def test_unknown_tree_returns_error(self) -> None:
        out = library.get_decision_tree("no-such-tree")
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
