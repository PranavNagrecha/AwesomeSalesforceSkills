"""Drift-prevention tests.

These tests assert that no count or roster size in the MCP code is hardcoded
to a stale value. They exist because the prototype shipped with literals like
``686+`` and a 37-name ``_RUNTIME_AGENTS`` frozenset that fell out of sync as
the skill / agent library grew.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
REPO = HERE.parent.parent.parent  # mcp/sfskills-mcp/tests/.. -> repo root
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import agents, server  # noqa: E402


# Stale literals we never want to see again in the MCP source.
# Each one was a hand-maintained number that drifted from reality and forced
# a doc-fix PR; the test pins them to extinction.
_STALE_LITERALS = (
    "686+",
    "_RUNTIME_AGENTS",
    "twenty-three tools",
    "registers twenty-three",
    "six tools",
    "56 total",
    "56 run-time",
    "56 runtime",
)


class NoStaleLiteralsInSourceTest(unittest.TestCase):
    def test_source_has_no_stale_literals(self) -> None:
        for py in (SRC / "sfskills_mcp").rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            for needle in _STALE_LITERALS:
                self.assertNotIn(
                    needle,
                    text,
                    f"stale literal {needle!r} reappeared in {py.relative_to(SRC)}",
                )


class CountsAreLiveTest(unittest.TestCase):
    def test_server_instructions_reflect_real_skill_count(self) -> None:
        instructions = server._server_instructions()
        # The real count comes from registry/skills.json; we only insist that
        # the instructions mention it (or the fallback "950+").
        skill_count = server._registry_skill_count()
        if skill_count > 0:
            self.assertIn(str(skill_count), instructions)

    def test_server_instructions_reflect_real_agent_counts(self) -> None:
        instructions = server._server_instructions()
        runtime = agents.runtime_agent_count()
        self.assertIn(str(runtime), instructions)
        # Sanity: > 40 runtime agents in the post-Wave-C library.
        self.assertGreater(runtime, 40)


class RegistryHelpersTest(unittest.TestCase):
    def test_registry_skill_count_is_accurate(self) -> None:
        registry_path = REPO / "registry" / "skills.json"
        if not registry_path.exists():
            self.skipTest("registry/skills.json missing")
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertEqual(server._registry_skill_count(), len(payload.get("skills", [])))


if __name__ == "__main__":
    unittest.main()
