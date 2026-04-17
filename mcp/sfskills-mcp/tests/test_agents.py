"""Stdlib smoke tests for the agents module.

Uses only stdlib (pytest-optional). Run with:

    cd mcp/sfskills-mcp
    python3 -m unittest discover -s tests

These tests read the real ``agents/`` tree in the surrounding repo.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import agents  # noqa: E402


EXPECTED_RUNTIME = {
    # Wave-1 developer + architecture tier (11)
    "apex-refactorer",
    "trigger-consolidator",
    "test-class-generator",
    "soql-optimizer",
    "security-scanner",
    "flow-analyzer",
    "bulk-migration-planner",
    "lwc-auditor",
    "deployment-risk-scorer",
    "agentforce-builder",
    "org-drift-detector",
    # Wave A — Tier-1 admin accelerators (8)
    "field-impact-analyzer",
    "object-designer",
    "permission-set-architect",
    "flow-builder",
    "workflow-and-pb-migrator",
    "validation-rule-auditor",
    "data-loader-pre-flight",
    "duplicate-rule-designer",
    # Wave B — Tier-2 strategic (10)
    "sharing-audit-agent",
    "lightning-record-page-auditor",
    "approval-to-flow-orchestrator-migrator",
    "record-type-and-layout-auditor",
    "picklist-governor",
    "data-model-reviewer",
    "integration-catalog-builder",
    "report-and-dashboard-auditor",
    "csv-to-object-mapper",
    "email-template-modernizer",
    # Wave C — Tier-3 vertical + governance (10)
    "omni-channel-routing-designer",
    "knowledge-article-taxonomy-agent",
    "sales-stage-designer",
    "lead-routing-rules-designer",
    "case-escalation-auditor",
    "sandbox-strategy-designer",
    "release-train-planner",
    "waf-assessor",
    "agentforce-action-reviewer",
    "prompt-library-governor",
}


class ListAgentsTest(unittest.TestCase):
    def test_runtime_filter_returns_expected_roster(self) -> None:
        result = agents.list_agents(kind="runtime")
        names = {a["name"] for a in result["agents"]}
        self.assertEqual(names, EXPECTED_RUNTIME)
        self.assertEqual(result["count"], len(EXPECTED_RUNTIME))

    def test_summary_is_populated(self) -> None:
        result = agents.list_agents(kind="runtime")
        for a in result["agents"]:
            self.assertTrue(a["summary"], f"empty summary for {a['name']}")
            self.assertEqual(a["kind"], "runtime")

    def test_build_filter_includes_orchestrator(self) -> None:
        result = agents.list_agents(kind="build")
        names = {a["name"] for a in result["agents"]}
        self.assertIn("orchestrator", names)
        self.assertNotIn("apex-refactorer", names)


class GetAgentTest(unittest.TestCase):
    def test_returns_full_markdown_for_known_agent(self) -> None:
        result = agents.get_agent("apex-refactorer")
        self.assertNotIn("error", result)
        self.assertEqual(result["kind"], "runtime")
        self.assertIn("markdown", result)
        self.assertGreater(len(result["markdown"]), 500)
        for section in (
            "## What This Agent Does",
            "## Invocation",
            "## Mandatory Reads Before Starting",
            "## Plan",
            "## Output Contract",
        ):
            self.assertIn(section, result["markdown"], f"missing {section}")

    def test_unknown_agent_returns_error_not_exception(self) -> None:
        result = agents.get_agent("not-a-real-agent")
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
