"""MCP parity tests for the public Salesforce skill-source integration.

The repository is the source of truth. A new package is not considered landed
until MCP can retrieve it, the new user workflows surface as prompts, and their
runtime agents are visible through the agent catalog.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import agents, prompts, skills  # noqa: E402


NEW_SKILLS = {
    "architect/salesforce-decision-analysis": "weighted criteria sensitivity Salesforce decision",
    "architect/salesforce-learning-research": "claim level source ledger Salesforce research",
    "admin/salesforce-learning-brief": "role aware Salesforce learning brief misconceptions exercises",
    "apex/apexguru-performance-analysis": "ApexGuru static production runtime findings",
    "lwc/lwc-typescript-migration": "migrate Lightning Web Component JavaScript TypeScript",
}
NEW_AGENTS = {
    "salesforce-decision-facilitator",
    "salesforce-learning-guide",
}
NEW_PROMPTS = {
    "decide-salesforce",
    "learn-salesforce",
}


class PublicSourceMcpParityTest(unittest.TestCase):
    def test_new_commands_surface_as_mcp_prompts(self) -> None:
        names = {definition.name for definition in prompts.discover()}
        self.assertTrue(NEW_PROMPTS <= names, f"missing MCP prompts: {sorted(NEW_PROMPTS - names)}")

    def test_new_runtime_agents_surface_in_catalog_and_get_agent(self) -> None:
        names = {item["name"] for item in agents.list_agents(kind="runtime")["agents"]}
        self.assertTrue(NEW_AGENTS <= names, f"missing MCP agents: {sorted(NEW_AGENTS - names)}")
        for name in sorted(NEW_AGENTS):
            result = agents.get_agent(name)
            self.assertNotIn("error", result, result)
            self.assertEqual(result["kind"], "runtime")
            self.assertIn("## Output Contract", result["markdown"])

    def test_new_skills_are_retrievable_by_id(self) -> None:
        for skill_id in NEW_SKILLS:
            result = skills.get_skill(skill_id, include_markdown=True)
            self.assertNotIn("error", result, result)
            self.assertEqual(result["skill"]["id"], skill_id)
            self.assertIn("## Recommended Workflow", result["markdown"])

    def test_new_skills_are_searchable_through_mcp(self) -> None:
        for expected, query in NEW_SKILLS.items():
            result = skills.search_skill(query, limit=5)
            ids = [item["id"] for item in result.get("skills", [])]
            self.assertIn(expected, ids, f"{expected} absent from MCP top 5 for {query!r}: {ids}")


if __name__ == "__main__":
    unittest.main()
