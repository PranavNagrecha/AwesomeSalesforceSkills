"""Unit tests for ``scripts/check_agent_citation_parity.py``.

AGENT_CONTRACT rule 5 requires `dependencies.skills:` and the prose reading
list to agree. The asymmetry is why it matters: the corpus-wide coverage check
reads the YAML block ONLY, so a skill listed there and never written into the
body counts as cited while being invisible to every human reviewer and unread
by the agent. That is the shape padding takes, and it also clears the 40-read
ceiling, which counts prose lines.

The permissiveness of the body matcher is itself load-bearing and is pinned
here: 29 real agents cite reads in forms the stricter reading-list regex in
``validate_repo.py`` does not recognise (markdown links, bullets, ``1)``
numbering, ``./`` prefixes). Tightening this matcher would report all of them
as divergent when they are not.

Synthetic agents in a temp dir. No corpus.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_agent_citation_parity import check_agent, collect_issues  # noqa: E402


def agent_md(declared: list[str], body: str) -> str:
    deps = "\n".join(f"    - {s}" for s in declared)
    return (
        "---\n"
        "id: sample-agent\n"
        "class: runtime\n"
        "dependencies:\n"
        "  skills:\n"
        f"{deps}\n"
        "---\n\n"
        "## Mandatory Reads Before Starting\n\n"
        f"{body}\n"
    )


class ParityBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "agents" / "sample-agent").mkdir(parents=True)
        self.addCleanup(self._tmp.cleanup)

    def write(self, declared: list[str], body: str) -> Path:
        path = self.root / "agents" / "sample-agent" / "AGENT.md"
        path.write_text(agent_md(declared, body))
        return path

    def kinds(self, declared: list[str], body: str) -> list[str]:
        return [i["kind"] for i in check_agent(self.write(declared, body), self.root)]


class AgreesIsClean(ParityBase):
    def test_matching_yaml_and_prose(self):
        self.assertEqual(
            self.kinds(
                ["apex/trigger-framework", "flow/fault-handling"],
                "1. `skills/apex/trigger-framework` — why\n"
                "2. `skills/flow/fault-handling` — why\n",
            ),
            [],
        )


class BodyMatcherIsPermissive(ParityBase):
    """Each of these forms appears in the real corpus and must count as cited."""

    def test_markdown_link_form(self):
        self.assertEqual(
            self.kinds(["apex/trigger-framework"],
                       "1. [`skills/apex/trigger-framework`](../../skills/apex/trigger-framework/SKILL.md) — why\n"),
            [],
        )

    def test_bullet_form(self):
        self.assertEqual(
            self.kinds(["apex/trigger-framework"], "- `skills/apex/trigger-framework` — why\n"),
            [],
        )

    def test_paren_numbering_form(self):
        self.assertEqual(
            self.kinds(["apex/trigger-framework"], "1) `skills/apex/trigger-framework` — why\n"),
            [],
        )

    def test_dot_slash_prefix_form(self):
        self.assertEqual(
            self.kinds(["apex/trigger-framework"], "1. ./skills/apex/trigger-framework — why\n"),
            [],
        )

    def test_mention_outside_the_reading_list_still_counts(self):
        # The question is "can a reviewer see this citation", not "is it
        # formatted as a numbered read".
        self.assertEqual(
            self.kinds(["admin/agent-output-formats"],
                       "1. `skills/apex/trigger-framework` — why\n\n"
                       "## What This Agent Does NOT Do\n\n"
                       "- refer them to `skills/admin/agent-output-formats` for conversion paths.\n"),
            ["prose-only-citation"],  # trigger-framework is in prose but not YAML
        )


class DetectsDivergence(ParityBase):
    def test_yaml_only_citation(self):
        self.assertEqual(
            self.kinds(["apex/trigger-framework", "lwc/lwc-testing"],
                       "1. `skills/apex/trigger-framework` — why\n"),
            ["yaml-only-citation"],
        )

    def test_prose_only_citation(self):
        self.assertEqual(
            self.kinds(["apex/trigger-framework"],
                       "1. `skills/apex/trigger-framework` — why\n"
                       "2. `skills/flow/fault-handling` — why\n"),
            ["prose-only-citation"],
        )

    def test_both_directions_at_once(self):
        self.assertEqual(
            sorted(self.kinds(["apex/trigger-framework", "lwc/lwc-testing"],
                              "1. `skills/apex/trigger-framework` — why\n"
                              "2. `skills/flow/fault-handling` — why\n")),
            ["prose-only-citation", "yaml-only-citation"],
        )

    def test_divergence_is_an_error_not_a_warning(self):
        issues = check_agent(
            self.write(["apex/trigger-framework", "lwc/lwc-testing"],
                       "1. `skills/apex/trigger-framework` — why\n"),
            self.root,
        )
        self.assertEqual({i["level"] for i in issues}, {"ERROR"})


class Degenerate(ParityBase):
    def test_no_frontmatter_is_skipped(self):
        path = self.root / "agents" / "sample-agent" / "AGENT.md"
        path.write_text("# no frontmatter here\n\n`skills/apex/trigger-framework`\n")
        self.assertEqual(check_agent(path, self.root), [])

    def test_malformed_yaml_is_left_to_the_schema_gate(self):
        path = self.root / "agents" / "sample-agent" / "AGENT.md"
        path.write_text("---\nid: x\n  bad: [unclosed\n---\n\nbody\n")
        self.assertEqual(check_agent(path, self.root), [])

    def test_no_dependencies_block_and_no_citations(self):
        path = self.root / "agents" / "sample-agent" / "AGENT.md"
        path.write_text("---\nid: x\nclass: build\n---\n\nNothing cited.\n")
        self.assertEqual(check_agent(path, self.root), [])

    def test_missing_agents_directory(self):
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(collect_issues(Path(empty)), [])


if __name__ == "__main__":
    unittest.main()
