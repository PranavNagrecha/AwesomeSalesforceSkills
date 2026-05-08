"""Stdlib smoke tests for the agents module.

Uses only stdlib (pytest-optional). Run with:

    cd mcp/sfskills-mcp
    python3 -m unittest discover -s tests

These tests read the real ``agents/`` tree in the surrounding repo. They assert
*invariants* (a known-good canary set is present, counts grow with the roster)
rather than pinning to a hand-maintained name list — the latter rotted as the
agent library expanded past Wave-1.
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


# Canary set — agents that MUST exist in the runtime roster. Expanding the
# library is fine; removing one of these without first deprecating it is a bug.
RUNTIME_CANARIES = frozenset(
    {
        "apex-refactorer",
        "trigger-consolidator",
        "test-class-generator",
        "soql-optimizer",
        "security-scanner",
        "flow-analyzer",
        "lwc-auditor",
        "lwc-builder",
        "apex-builder",
        "deployment-risk-scorer",
        "agentforce-builder",
        "audit-router",
        "field-impact-analyzer",
        "object-designer",
        "permission-set-architect",
        "flow-builder",
        "data-loader-pre-flight",
        "duplicate-rule-designer",
    }
)

# Stubs that should NOT appear under kind="runtime" because their frontmatter
# carries ``status: deprecated``. They redirect via ``list_deprecated_redirects``.
DEPRECATED_CANARIES = frozenset(
    {
        "validation-rule-auditor",
        "picklist-governor",
        "record-type-and-layout-auditor",
        "report-and-dashboard-auditor",
        "case-escalation-auditor",
        "lightning-record-page-auditor",
        "sharing-audit-agent",
        "org-drift-detector",
    }
)


class ListAgentsTest(unittest.TestCase):
    def test_runtime_filter_includes_canary_set(self) -> None:
        names = {a["name"] for a in agents.list_agents(kind="runtime")["agents"]}
        missing = RUNTIME_CANARIES - names
        self.assertFalse(
            missing,
            f"runtime roster missing canary agents: {sorted(missing)}",
        )

    def test_runtime_filter_excludes_deprecated_stubs(self) -> None:
        names = {a["name"] for a in agents.list_agents(kind="runtime")["agents"]}
        leaked = DEPRECATED_CANARIES & names
        self.assertFalse(
            leaked,
            f"deprecated stubs leaked into runtime: {sorted(leaked)}",
        )

    def test_runtime_count_meets_floor(self) -> None:
        # Floor reflects the post-Wave-C roster minus the 14 deprecation stubs.
        # Adjust the floor when retiring or adding wholesale tiers; keep it
        # below the actual count so the test stays robust to roster growth.
        result = agents.list_agents(kind="runtime")
        self.assertGreaterEqual(
            result["count"],
            40,
            f"runtime roster shrunk unexpectedly: count={result['count']}",
        )

    def test_summary_is_populated(self) -> None:
        for a in agents.list_agents(kind="runtime")["agents"]:
            self.assertTrue(a["summary"], f"empty summary for {a['name']}")
            self.assertEqual(a["kind"], "runtime")

    def test_build_filter_includes_orchestrator(self) -> None:
        names = {a["name"] for a in agents.list_agents(kind="build")["agents"]}
        self.assertIn("orchestrator", names)
        self.assertIn("code-reviewer", names)  # build-time skill-factory reviewer
        self.assertNotIn("apex-refactorer", names)
        self.assertNotIn("validation-rule-auditor", names)  # deprecated, not build

    def test_deprecated_filter_returns_redirect_stubs(self) -> None:
        result = agents.list_agents(kind="deprecated")
        names = {a["name"] for a in result["agents"]}
        for stub in DEPRECATED_CANARIES:
            self.assertIn(stub, names, f"missing deprecated canary {stub}")
        for a in result["agents"]:
            self.assertEqual(a["kind"], "deprecated")

    def test_unknown_kind_returns_error(self) -> None:
        result = agents.list_agents(kind="bogus")
        self.assertIn("error", result)
        self.assertEqual(result["count"], 0)


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

    def test_deprecated_agent_classified_correctly(self) -> None:
        # validation-rule-auditor is a known deprecation stub; get_agent
        # should still serve the markdown but tag it kind="deprecated" so
        # callers can route through list_deprecated_redirects.
        result = agents.get_agent("validation-rule-auditor")
        self.assertNotIn("error", result)
        self.assertEqual(result["kind"], "deprecated")


class CountHelpersTest(unittest.TestCase):
    def test_runtime_agent_count_matches_filter(self) -> None:
        self.assertEqual(
            agents.runtime_agent_count(),
            agents.list_agents(kind="runtime")["count"],
        )

    def test_total_agent_count_is_sum(self) -> None:
        total = agents.total_agent_count()
        sum_kinds = sum(
            agents.list_agents(kind=k)["count"]
            for k in ("runtime", "build", "deprecated")
        )
        # ``unknown`` agents are excluded from kind filters but counted in
        # total — so total >= sum_kinds.
        self.assertGreaterEqual(total, sum_kinds)


if __name__ == "__main__":
    unittest.main()
