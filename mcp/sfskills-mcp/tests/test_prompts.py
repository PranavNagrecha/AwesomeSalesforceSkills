"""Verify ``commands/*.md`` register as MCP prompts.

Every wrapper in ``commands/`` should surface as a prompt in any MCP-capable
client; this test makes sure the discovery + registration loop catches them.
"""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
REPO = HERE.parent.parent.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import prompts  # noqa: E402
from sfskills_mcp.server import build_server  # noqa: E402


# Wrappers that MUST register. If any of these stops registering, something
# changed in the wrapper format and the parser needs an update.
_PROMPT_CANARIES = frozenset(
    {
        "refactor-apex",
        "audit-router",
        "build-apex",
        "build-lwc",
        "scan-security",
        "gen-tests",
    }
)


class DiscoverTest(unittest.TestCase):
    def test_discovers_at_least_60_wrappers(self) -> None:
        defs = prompts.discover()
        self.assertGreaterEqual(
            len(defs),
            60,
            f"only discovered {len(defs)} prompts; commands/ has 68+ files",
        )

    def test_canary_wrappers_present(self) -> None:
        names = {d.name for d in prompts.discover()}
        missing = _PROMPT_CANARIES - names
        self.assertFalse(missing, f"missing canary wrappers: {sorted(missing)}")

    def test_every_prompt_has_description(self) -> None:
        for d in prompts.discover():
            self.assertTrue(
                d.description,
                f"empty description for /{d.name}",
            )

    def test_every_prompt_body_is_non_trivial(self) -> None:
        for d in prompts.discover():
            self.assertGreater(
                len(d.body),
                100,
                f"/{d.name} body is suspiciously short ({len(d.body)} chars)",
            )

    def test_no_collisions(self) -> None:
        names = [d.name for d in prompts.discover()]
        self.assertEqual(len(names), len(set(names)), "duplicate prompt names")


class RegistrationTest(unittest.TestCase):
    def test_register_all_attaches_to_mcp(self) -> None:
        server = build_server()
        registered = asyncio.run(server.list_prompts())
        names = {p.name for p in registered}
        self.assertGreaterEqual(len(names), 60)
        for canary in _PROMPT_CANARIES:
            self.assertIn(canary, names)

    def test_registered_prompts_distinguish_their_bodies(self) -> None:
        # Closure-capture trap: if the registration loop accidentally captures
        # the loop variable by reference, every prompt returns the SAME body
        # (the last wrapper's). Verify two specific prompts differ.
        server = build_server()
        a_result = asyncio.run(server.get_prompt("refactor-apex", arguments={}))
        b_result = asyncio.run(server.get_prompt("audit-router", arguments={}))
        a_text = a_result.messages[0].content.text
        b_text = b_result.messages[0].content.text
        self.assertIn("refactor", a_text.lower())
        self.assertIn("audit-router", b_text.lower())
        self.assertNotEqual(a_text, b_text)


if __name__ == "__main__":
    unittest.main()
