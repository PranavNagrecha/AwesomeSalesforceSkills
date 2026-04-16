"""Stdlib smoke tests for the skills module.

Uses only stdlib (pytest-optional). Run with:

    cd mcp/sfskills-mcp
    python3 -m unittest discover -s tests

These tests hit the real registry and lexical index in the surrounding repo.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import skills  # noqa: E402


class SearchSkillTest(unittest.TestCase):
    def test_returns_ranked_skills_for_common_query(self) -> None:
        result = skills.search_skill("trigger recursion", limit=5)
        self.assertIn("skills", result)
        self.assertGreater(len(result["skills"]), 0, "expected at least one skill hit")
        self.assertTrue(result["has_coverage"])
        top = result["skills"][0]
        self.assertIn("id", top)
        self.assertIn("category", top)

    def test_domain_filter_narrows_results(self) -> None:
        result = skills.search_skill("permission set", domain="admin", limit=5)
        self.assertEqual(result["domain_filter"], "admin")
        for hit in result["skills"]:
            self.assertEqual(hit.get("category"), "admin")

    def test_empty_query_returns_error(self) -> None:
        result = skills.search_skill("", limit=5)
        self.assertIn("error", result)
        self.assertEqual(result["skills"], [])


class GetSkillTest(unittest.TestCase):
    def test_returns_full_record_for_known_skill(self) -> None:
        result = skills.get_skill("apex/trigger-framework", include_markdown=False)
        self.assertIn("skill", result)
        self.assertEqual(result["skill"]["id"], "apex/trigger-framework")
        self.assertNotIn("chunk_ids", result["skill"], "chunk_ids should be stripped from responses")
        self.assertIn("references", result)

    def test_accepts_double_underscore_form(self) -> None:
        result = skills.get_skill("apex__trigger-framework", include_markdown=False)
        self.assertEqual(result["skill"]["id"], "apex/trigger-framework")

    def test_missing_skill_returns_error(self) -> None:
        result = skills.get_skill("nonsense/nope", include_markdown=False)
        self.assertIn("error", result)
        self.assertIn("hint", result)

    def test_include_markdown_returns_skill_body(self) -> None:
        result = skills.get_skill("apex/trigger-framework", include_markdown=True)
        self.assertIn("markdown", result)
        self.assertIn("Recommended Workflow", result["markdown"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
