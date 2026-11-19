"""Guard: the MCP server never registers a tool that creates or deletes an org."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "mcp" / "sfskills-mcp" / "src" / "sfskills_mcp" / "server.py"
FORBIDDEN_TOOL_NAMES = {
    "create_scratch_org",
    "delete_org",
    "create_org",
    "scratch_create",
}


class ScratchGuardTests(unittest.TestCase):
    def test_mcp_does_not_register_scratch_mutation_tools(self):
        tree = ast.parse(SERVER.read_text(encoding="utf-8"))
        names: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and getattr(getattr(decorator, "func", None), "attr", None) == "tool":
                    names.add(node.name)
        overlap = names & FORBIDDEN_TOOL_NAMES
        self.assertFalse(overlap, f"MCP must not expose scratch mutation tools: {sorted(overlap)}")


if __name__ == "__main__":
    unittest.main()
