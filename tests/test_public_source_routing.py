"""Run the public-source integration routing pack against the MCP ranker."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCP_SRC = ROOT / "mcp" / "sfskills-mcp" / "src"
if str(MCP_SRC) not in sys.path:
    sys.path.insert(0, str(MCP_SRC))

from sfskills_mcp.skills import search_skill  # noqa: E402

PACK = ROOT / "evals" / "source-integrations" / "public-salesforce-skills-routing.json"
ALLOWED_TYPES = {"positive", "negative", "neighbor", "boundary"}


class PublicSourceRoutingPackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(PACK.read_text(encoding="utf-8"))

    def test_pack_has_all_four_case_types(self) -> None:
        types = {case.get("type") for case in self.payload["cases"]}
        self.assertEqual(types, ALLOWED_TYPES)

    def test_case_ids_are_unique(self) -> None:
        ids = [case["id"] for case in self.payload["cases"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_routing_cases(self) -> None:
        failures: list[str] = []
        for case in self.payload["cases"]:
            top_k = int(case.get("top_k", 3))
            result = search_skill(case["query"], limit=max(5, top_k))
            ids = [item["id"] for item in result.get("skills", [])]
            expected = case.get("expected_skill")
            forbidden = case.get("forbidden_skill")
            if expected and expected not in ids[:top_k]:
                failures.append(
                    f"{case['id']}: expected {expected} in top {top_k}, got {ids[:top_k]}"
                )
            if forbidden and forbidden in ids[:top_k]:
                failures.append(
                    f"{case['id']}: forbidden {forbidden} appeared in top {top_k}: {ids[:top_k]}"
                )
        self.assertFalse(failures, "\n" + "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
