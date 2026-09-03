"""Regression tests for new-skill agent wiring.

The documented scaffold path must reject weak citation text before writing and
must be able to wire a newly scaffolded agent whose YAML uses ``skills: []``.
"""

from __future__ import annotations

import unittest

from scripts.new_skill import _parse_agent_justifications
from scripts.patch_agent_skill import insert_yaml_skill


class AgentJustificationTests(unittest.TestCase):
    def test_accepts_scenario_specific_justification(self) -> None:
        actual = _parse_agent_justifications(
            [
                "decision-agent=without this rubric, options can be scored against "
                "criteria that do not reflect the stated Salesforce constraints"
            ],
            ["decision-agent"],
            "architect/salesforce-decision-analysis",
        )
        self.assertIn("decision-agent", actual)

    def test_rejects_echo_only_justification(self) -> None:
        with self.assertRaisesRegex(ValueError, "must name the failure scenario"):
            _parse_agent_justifications(
                ["decision-agent=salesforce decision analysis"],
                ["decision-agent"],
                "architect/salesforce-decision-analysis",
            )

    def test_rejects_missing_agent_prefix(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected AGENT_ID=TEXT"):
            _parse_agent_justifications(
                ["a useful reason but no agent id"],
                ["decision-agent"],
                "architect/salesforce-decision-analysis",
            )


class InlineEmptySkillsTests(unittest.TestCase):
    def test_converts_inline_empty_list_to_block(self) -> None:
        lines = [
            "dependencies:\n",
            "  probes: []\n",
            "  skills: []\n",
            "  shared:\n",
            "    - AGENT_CONTRACT.md\n",
        ]
        changed = insert_yaml_skill(lines, "architect/salesforce-decision-analysis")
        self.assertTrue(changed)
        self.assertIn("  skills:\n", lines)
        self.assertIn("    - architect/salesforce-decision-analysis\n", lines)
        self.assertNotIn("  skills: []\n", lines)

    def test_converts_empty_block_to_first_item(self) -> None:
        lines = [
            "dependencies:\n",
            "  probes: []\n",
            "  skills:\n",
            "  shared:\n",
            "    - AGENT_CONTRACT.md\n",
        ]
        changed = insert_yaml_skill(lines, "admin/salesforce-learning-brief")
        self.assertTrue(changed)
        self.assertEqual(lines[3], "    - admin/salesforce-learning-brief\n")


if __name__ == "__main__":
    unittest.main()
