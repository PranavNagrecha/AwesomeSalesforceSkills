"""Guards for qa/scratch — no Dev Hub, no org create, no live mutation."""

from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / "qa" / "scratch"
SERVER = ROOT / "mcp" / "sfskills-mcp" / "src" / "sfskills_mcp" / "server.py"
FORBIDDEN_TOOL_NAMES = {
    "create_scratch_org",
    "delete_org",
    "create_org",
    "scratch_create",
}


class ScratchGuardTests(unittest.TestCase):
    def test_readme_and_not_run_exist(self):
        self.assertTrue((SCRATCH / "README.md").is_file())
        not_run = json.loads((SCRATCH / "NOT_RUN.json").read_text(encoding="utf-8"))
        self.assertEqual(not_run["status"], "not_run")
        self.assertIn("Dev Hub", not_run["required_before_run"][1])

    def test_create_script_refuses_without_opt_in(self):
        create = (SCRATCH / "scripts" / "create.py").read_text(encoding="utf-8")
        self.assertIn("SFSKILLS_SCRATCH_OPT_IN", create)
        self.assertNotIn("force:org:create", create)
        self.assertNotIn("org create scratch", create)

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
