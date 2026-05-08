"""Verify the 5 MCP resource shapes register and serve real content.

The resources expose skills, agents, decision trees, and templates without
forcing a tool call. This test makes sure:

1. The catalog resource returns the live skill count.
2. The 4 templated resources match real on-disk artefacts via the ``__``
   path-encoding convention (MCP URI templates only match single segments).
3. Errors come back as readable stub text, not exceptions — same posture as
   the rest of the MCP server.
"""

from __future__ import annotations

import asyncio
import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import resources  # noqa: E402
from sfskills_mcp.server import build_server  # noqa: E402


def _read(server, uri: str) -> str:
    return asyncio.run(server.read_resource(uri))[0].content


class CatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = build_server()

    def test_catalog_returns_live_count(self) -> None:
        payload = json.loads(_read(self.server, "sfskills://catalog"))
        self.assertGreaterEqual(payload["skill_count"], 900)
        self.assertEqual(payload["skill_count"], len(payload["skills"]))

    def test_catalog_entries_have_required_fields(self) -> None:
        payload = json.loads(_read(self.server, "sfskills://catalog"))
        for entry in payload["skills"][:20]:
            self.assertIn("id", entry)
            self.assertIn("category", entry)
            self.assertIn("description", entry)


class SkillResourceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = build_server()

    def test_known_skill_returns_markdown(self) -> None:
        body = _read(self.server, "sfskills://skill/apex__apex-design-patterns")
        self.assertIn("---", body[:5])  # frontmatter
        self.assertIn("apex-design-patterns", body)

    def test_unknown_skill_returns_error_stub(self) -> None:
        body = _read(self.server, "sfskills://skill/apex__not-a-real-skill")
        self.assertIn("not found", body.lower())


class AgentResourceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = build_server()

    def test_known_agent_returns_full_markdown(self) -> None:
        body = _read(self.server, "sfskills://agent/apex-refactorer")
        self.assertIn("class: runtime", body)
        self.assertIn("## What This Agent Does", body)

    def test_unknown_agent_returns_error_stub(self) -> None:
        body = _read(self.server, "sfskills://agent/no-such-agent")
        self.assertIn("not found", body.lower())

    def test_unsafe_agent_name_rejected(self) -> None:
        body = _read(self.server, "sfskills://agent/..%2Fetc")
        self.assertIn("invalid", body.lower())


class DecisionTreeResourceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = build_server()

    def test_known_tree_returns_body(self) -> None:
        body = _read(self.server, "sfskills://decision-tree/automation-selection")
        self.assertIn("Automation", body)

    def test_unknown_tree_returns_error_stub(self) -> None:
        body = _read(self.server, "sfskills://decision-tree/no-such-tree")
        self.assertIn("not found", body.lower())


class TemplateResourceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = build_server()

    def test_apex_template_returns_body(self) -> None:
        body = _read(self.server, "sfskills://template/apex__TriggerHandler.cls")
        self.assertIn("TriggerHandler", body)
        self.assertGreater(len(body), 200)

    def test_path_traversal_rejected(self) -> None:
        body = _read(self.server, "sfskills://template/..__etc__passwd")
        # Either ``invalid path`` (regex fails on leading dot) or ``rejected``
        # (explicit traversal check). Both signal proper refusal.
        lower = body.lower()
        self.assertTrue(
            "invalid" in lower or "rejected" in lower,
            f"path traversal not rejected: {body!r}",
        )

    def test_unknown_template_returns_stub(self) -> None:
        body = _read(self.server, "sfskills://template/apex__NoSuchFile.cls")
        self.assertIn("not found", body.lower())


class DiscoveryHelpersTest(unittest.TestCase):
    def test_decision_tree_listing_includes_canonical_trees(self) -> None:
        names = set(resources.list_decision_tree_names())
        for canonical in ("automation-selection", "async-selection", "sharing-selection"):
            self.assertIn(canonical, names, f"missing canonical tree {canonical}")

    def test_template_listing_includes_canonical_files(self) -> None:
        paths_ = resources.list_template_paths()
        self.assertIn("apex/TriggerHandler.cls", paths_)
        self.assertIn("apex/ApplicationLogger.cls", paths_)


class RegistrationTest(unittest.TestCase):
    def test_register_all_attaches_5_shapes(self) -> None:
        server = build_server()
        static = asyncio.run(server.list_resources())
        templates = asyncio.run(server.list_resource_templates())
        # 1 static (catalog) + 4 templated (skill, agent, decision-tree, template)
        self.assertEqual(len(static), 1)
        self.assertEqual(len(templates), 4)
        uris = {str(r.uri) for r in static} | {r.uriTemplate for r in templates}
        for required in (
            "sfskills://catalog",
            "sfskills://skill/{skill_id}",
            "sfskills://agent/{agent_name}",
            "sfskills://decision-tree/{name}",
            "sfskills://template/{path}",
        ):
            self.assertIn(required, uris, f"missing resource URI {required}")


if __name__ == "__main__":
    unittest.main()
