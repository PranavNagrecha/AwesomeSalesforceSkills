"""Tests for ``routing.suggest_agent``.

Plan-mandated invariant: top-1 accuracy ≥ 80% on the hand-curated fixture
in ``tests/fixtures/routing_cases.json``. Top-3 accuracy ≥ 90% as a safety
net — even when the verb-rule heuristic picks a wrong winner, the right
agent should be in the user's three suggestions.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
FIXTURE = HERE / "fixtures" / "routing_cases.json"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import agents as agents_mod  # noqa: E402
from sfskills_mcp import routing  # noqa: E402


def _load_fixture() -> list[dict[str, str]]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]


class SuggestAgentBasicsTest(unittest.TestCase):
    def test_query_required(self) -> None:
        out = routing.suggest_agent(task="")
        self.assertIn("error", out)

    def test_returns_agents_decision_trees_next_step(self) -> None:
        out = routing.suggest_agent(task="audit picklists", limit=3)
        self.assertIn("agents", out)
        self.assertIn("decision_trees", out)
        self.assertIn("next_step", out)
        self.assertGreater(len(out["agents"]), 0)
        self.assertIn("get_agent", out["next_step"])

    def test_excludes_deprecated_stubs(self) -> None:
        # 'audit picklists' would naturally pull in the deprecated
        # picklist-governor; the router should never recommend a stub.
        classes = agents_mod._agent_classes()
        out = routing.suggest_agent(task="audit picklists", limit=10)
        for entry in out["agents"]:
            self.assertEqual(
                classes.get(entry["name"]),
                "runtime",
                f"deprecated/non-runtime agent leaked into suggestions: {entry['name']}",
            )

    def test_decision_trees_optional(self) -> None:
        out = routing.suggest_agent(task="audit picklists", include_decision_trees=False)
        self.assertEqual(out["decision_trees"], [])

    def test_limit_bounded(self) -> None:
        out = routing.suggest_agent(task="audit picklists", limit=99)
        # Internal cap is 10.
        self.assertLessEqual(len(out["agents"]), 10)


class SuggestAgentAccuracyTest(unittest.TestCase):
    """Run the fixture and enforce the plan-mandated accuracy floors."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = _load_fixture()
        assert len(cls.cases) >= 20, "fixture should have ≥ 20 cases"
        cls.results: list[tuple[str, str, list[str]]] = []
        for case in cls.cases:
            out = routing.suggest_agent(task=case["task"], limit=3)
            top3 = [a["name"] for a in out["agents"]]
            cls.results.append((case["task"], case["expected"], top3))

    def test_top1_accuracy_at_least_80_percent(self) -> None:
        hits = sum(1 for _, exp, top3 in self.results if top3 and top3[0] == exp)
        accuracy = hits / len(self.results)
        # Print the misses so a regression diagnoses itself.
        if accuracy < 0.80:
            for task, exp, top3 in self.results:
                if not top3 or top3[0] != exp:
                    print(f"  miss: {task!r} → {top3[:1] if top3 else None}, wanted {exp}")
        self.assertGreaterEqual(
            accuracy,
            0.80,
            f"top-1 accuracy {accuracy:.0%} < 80% floor (hits={hits}/{len(self.results)})",
        )

    def test_top3_accuracy_at_least_90_percent(self) -> None:
        hits = sum(1 for _, exp, top3 in self.results if exp in top3)
        accuracy = hits / len(self.results)
        if accuracy < 0.90:
            for task, exp, top3 in self.results:
                if exp not in top3:
                    print(f"  miss-top3: {task!r} → {top3}, wanted {exp}")
        self.assertGreaterEqual(
            accuracy,
            0.90,
            f"top-3 accuracy {accuracy:.0%} < 90% floor (hits={hits}/{len(self.results)})",
        )


class SuggestAgentSurfaceTest(unittest.TestCase):
    def test_each_agent_entry_has_required_fields(self) -> None:
        out = routing.suggest_agent(task="audit picklists", limit=3)
        for entry in out["agents"]:
            for field in ("name", "title", "summary", "path", "score"):
                self.assertIn(field, entry, f"missing field {field} in {entry}")

    def test_each_tree_entry_has_uri(self) -> None:
        out = routing.suggest_agent(task="flow vs apex", limit=3)
        for tree in out["decision_trees"]:
            self.assertTrue(tree["uri"].startswith("sfskills://decision-tree/"))


if __name__ == "__main__":
    unittest.main()
