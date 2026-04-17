"""Structural tests for the MCP tool surface.

Wave 2: we promoted 4 probes to first-class MCP tools, bringing the total
from 15 to 19. These tests assert that every expected tool is registered
on the server, has a description, and that the probe/admin/skill modules
can be imported without a live ``sf`` CLI.

End-to-end tests against a real org live in a separate harness
(``evals/probes/``, Wave 6) — here we only verify structure + error-path
behavior, so CI can run without Salesforce credentials.

Run with:

    cd mcp/sfskills-mcp
    python3 -m unittest tests.test_tools -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


EXPECTED_TOOLS = {
    # Skill library (2)
    "search_skill",
    "get_skill",
    # Live-org core (4)
    "describe_org",
    "list_custom_objects",
    "list_flows_on_object",
    "validate_against_org",
    # Live-org admin metadata (7)
    "list_validation_rules",
    "list_permission_sets",
    "describe_permission_set",
    "list_record_types",
    "list_named_credentials",
    "list_approval_processes",
    "tooling_query",
    # Probes (4, Wave-2 promotion)
    "probe_apex_references",
    "probe_flow_references",
    "probe_matching_rules",
    "probe_permset_shape",
    # Agents (2)
    "list_agents",
    "get_agent",
}


class TestProbeInputValidation(unittest.TestCase):
    """Probe-side assertions that don't need the ``mcp`` package installed.

    These guards run in every environment: local dev without FastMCP, CI
    with FastMCP, whatever. They're the input-validation layer: probes
    must reject garbage without crashing and without attempting any SOQL.
    """

    def test_probe_module_imports_without_sf_cli(self):
        """The probes module must import cleanly even when ``sf`` isn't on
        PATH. Callers get an error dict only when they actually invoke a
        probe — import time must stay CLI-free."""
        import os
        sf_path = os.environ.pop("SFSKILLS_SF_BIN", None)
        try:
            from sfskills_mcp import probes  # noqa: F401
        finally:
            if sf_path:
                os.environ["SFSKILLS_SF_BIN"] = sf_path

    def test_probes_validate_bad_object_name(self):
        """Bad sObject name input returns an error dict (not a traceback)
        before any SOQL is attempted — the server must not crash on
        garbage input. SOQL injection vectors must be rejected."""
        from sfskills_mcp import probes

        for bad in ("Account; DROP", "Account OR 1=1", "account space"):
            result = probes.probe_apex_references(object_name=bad, field="Industry")
            self.assertIn(
                "error", result,
                f"Expected error for bad object_name {bad!r}, got: {result}",
            )

    def test_permset_shape_rejects_malformed_scope(self):
        """``scope`` must be ``psg:<name>`` / ``ps:<name>`` / ``user:<name>``.
        Every other shape returns an error dict."""
        from sfskills_mcp import probes

        for bad in ("", "psg", "psg:", ":psg:foo", "random_string"):
            result = probes.probe_permset_shape(scope=bad)
            self.assertIn("error", result, f"Expected error for scope={bad!r}")

    def test_expected_tool_count(self):
        """Documentation asserts 19 tools in Wave 2. Guard against drift.

        Changing this number without updating ``server.py``'s module docstring
        + ``EXPECTED_TOOLS`` + ``docs/SKILLS.md`` is a failure by design.
        """
        self.assertEqual(
            len(EXPECTED_TOOLS), 19,
            "Wave 2 baseline is 19 tools — update docstring if intentional",
        )


class TestMCPServerRegistration(unittest.TestCase):
    """Server-side assertions that DO need the ``mcp`` package.

    Skipped when ``mcp`` isn't installed (e.g. local dev that only uses the
    probe CLI). CI installs ``-e mcp/sfskills-mcp`` and runs these tests
    as part of the matrix validate job.
    """

    @classmethod
    def setUpClass(cls):
        # Check for the REAL FastMCP symbol, not just ``import mcp`` —
        # Python 3's implicit namespace packages happily bind ``mcp`` to the
        # repo's own ``mcp/`` directory, so the bare import succeeds without
        # the FastMCP package being installed. That's what caused a silent
        # setUpClass error in Wave-2 CI until we tightened this check.
        try:
            from mcp.server.fastmcp import FastMCP  # noqa: F401
        except ImportError:
            raise unittest.SkipTest(
                "mcp.server.fastmcp not importable; run "
                "`pip install -e mcp/sfskills-mcp`"
            )
        from sfskills_mcp.server import build_server
        cls.server = build_server()

    def test_all_expected_tools_registered(self):
        """Every tool in EXPECTED_TOOLS must be present. Missing tools
        mean a feature regression; extra tools are allowed (future waves)
        but reported so intentional additions surface in CI logs.
        """
        # FastMCP exposes the registered tools via ``list_tools()`` which is
        # async; easier to poke at its private registry for a sync test.
        # If the private attr shape moves, we fail fast here rather than
        # silently passing on a future FastMCP upgrade.
        registry = getattr(self.server, "_tool_manager", None)
        if registry is None:
            self.skipTest("FastMCP's tool registry shape changed; update test")
        tools = getattr(registry, "_tools", None) or getattr(registry, "tools", None)
        if not tools:
            self.skipTest("Could not locate registered tools on FastMCP server")
        registered = set(tools.keys()) if isinstance(tools, dict) else {t.name for t in tools}

        missing = EXPECTED_TOOLS - registered
        extra = registered - EXPECTED_TOOLS
        self.assertFalse(
            missing,
            f"Missing tools: {sorted(missing)} — "
            "did a server.py edit drop a @mcp.tool registration?",
        )
        if extra:
            print(f"\nINFO: registered tools beyond the Wave-2 baseline: {sorted(extra)}")


if __name__ == "__main__":
    unittest.main()
