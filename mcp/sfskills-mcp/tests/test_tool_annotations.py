"""Verify every registered MCP tool carries honest annotations.

MCP clients (Cursor, Cline, Claude Desktop) use these annotations to decide
whether a tool is safe to auto-approve. Missing or wrong annotations turn into
either friction (every call prompts the user) or risk (a write tool slips
through as ``readOnlyHint=True``).

This test enforces three invariants:

1. Every tool registered by ``build_server`` has annotations attached.
2. Every tool except ``emit_envelope`` is honest about being read-only.
3. The org-touching tools mark themselves ``openWorldHint=True`` so clients
   know the output reflects external (org) state.
"""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp.server import build_server  # noqa: E402


# Tools whose output depends on external (org) state. Everything else is a
# pure repo read or a scoped repo write.
_ORG_TOUCHING = frozenset(
    {
        # Wave-2 baseline org tools.
        "describe_org",
        "list_custom_objects",
        "list_flows_on_object",
        "validate_against_org",
        "list_validation_rules",
        "list_permission_sets",
        "describe_permission_set",
        "list_record_types",
        "list_named_credentials",
        "list_approval_processes",
        "tooling_query",
        "probe_apex_references",
        "probe_flow_references",
        "probe_matching_rules",
        "probe_permset_shape",
        "probe_automation_graph",
        # Tier-C developer-tier additions.
        "list_apex_classes",
        "get_apex_class",
        "list_apex_triggers",
        "list_lwc_bundles",
        "get_lwc_bundle",
        "list_custom_fields",
        "describe_object_full",
        "list_orgs",
    }
)

# The single tool that writes to disk.
_WRITERS = frozenset({"emit_envelope"})


def _registered_tools() -> list:
    server = build_server()
    return asyncio.run(server.list_tools())


class ToolAnnotationsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tools = _registered_tools()
        cls.by_name = {t.name: t for t in cls.tools}

    def test_every_tool_has_annotations(self) -> None:
        missing = [t.name for t in self.tools if not t.annotations]
        self.assertFalse(missing, f"tools missing annotations: {missing}")

    def test_destructive_hint_always_false(self) -> None:
        # No tool in this server performs DML, deploys metadata, or runs Apex.
        # Even ``emit_envelope`` writes only to docs/reports/<agent>/<run_id>
        # with overwrite protection — not destructive in the spec sense.
        bad = [t.name for t in self.tools if t.annotations.destructiveHint]
        self.assertFalse(bad, f"tools wrongly flagged destructive: {bad}")

    def test_writers_not_marked_read_only(self) -> None:
        for name in _WRITERS:
            tool = self.by_name[name]
            self.assertFalse(
                tool.annotations.readOnlyHint,
                f"{name} writes to disk but is flagged readOnlyHint=True",
            )

    def test_non_writers_marked_read_only(self) -> None:
        for tool in self.tools:
            if tool.name in _WRITERS:
                continue
            self.assertTrue(
                tool.annotations.readOnlyHint,
                f"{tool.name} should be readOnlyHint=True (no disk write, no DML)",
            )

    def test_org_tools_open_world(self) -> None:
        for name in _ORG_TOUCHING:
            tool = self.by_name[name]
            self.assertTrue(
                tool.annotations.openWorldHint,
                f"{name} reads org state but openWorldHint is False",
            )

    def test_non_org_tools_closed_world(self) -> None:
        # Anything that doesn't touch the org should be openWorldHint=False
        # so clients can cache the result aggressively.
        for tool in self.tools:
            if tool.name in _ORG_TOUCHING:
                continue
            self.assertFalse(
                tool.annotations.openWorldHint,
                f"{tool.name} doesn't touch the org but openWorldHint=True",
            )

    def test_emit_envelope_idempotency(self) -> None:
        env = self.by_name["emit_envelope"]
        # Default behaviour rejects re-runs of the same run_id, so we flag
        # idempotentHint=False; the tool only becomes idempotent when the
        # caller passes overwrite=True.
        self.assertFalse(env.annotations.idempotentHint)


if __name__ == "__main__":
    unittest.main()
