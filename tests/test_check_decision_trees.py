"""Unit tests for ``scripts/check_decision_trees.py``.

The trees are read BEFORE any skill (`standards/decision-trees/README.md`), so a
tree defect outranks correct skill content inside an agent's context window. But
this gate's expensive failure mode is the opposite of missing a defect: it is
firing on correct trees, because a gate that cries wolf gets disabled rather
than obeyed. Its first draft did exactly that twice — once by computing
reachability per fenced block when trees route ACROSS blocks, and once by
treating a checklist-shaped tree as a routed one.

So these tests pin both directions:
  * every defect class must be DETECTED (the mutation direction), and
  * the two shapes that are legitimately not routed must stay SILENT.

Everything runs against synthetic trees in a temp dir. No corpus.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_decision_trees import check_tree, collect_issues  # noqa: E402


ROUTED = """# Decision Tree — Sample

```
Q1. First?
    ├── Yes → Q2
    └── No  → Q3
```

Some prose between the blocks, which is how the real trees are written.

```
Q2. Second?
    ├── Yes → Q4
    └── No  → Done

Q3. Third?
    └── Anything → Q4
```

```
Q4. Fourth?
    └── Done — see `apex/trigger-framework`
```
"""

CHECKLIST = """# Decision Tree — Dimensions

```
Q1. Authentication?
    ├── OAuth  → Named Credential
    └── Basic  → Named Credential (dev only)

Q2. Payload shape?
    ├── JSON → HttpClient
    └── SOAP → WSDL2Apex

Q3. Rate limiting?
    └── 429 → backoff
```
"""


class TreeCheckBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "standards" / "decision-trees").mkdir(parents=True)
        # A real skill so resolvable references resolve.
        skill = self.root / "skills" / "apex" / "trigger-framework"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("stub")
        self.addCleanup(self._tmp.cleanup)

    def write(self, name: str, text: str) -> Path:
        path = self.root / "standards" / "decision-trees" / name
        path.write_text(text)
        return path

    def kinds(self, path: Path) -> list[str]:
        return [i["kind"] for i in check_tree(path, self.root)]


class SilentOnCorrectTrees(TreeCheckBase):
    """The direction that matters most: no findings on well-formed input."""

    def test_routed_tree_is_clean(self):
        self.assertEqual(self.kinds(self.write("routed.md", ROUTED)), [])

    def test_checklist_tree_is_clean(self):
        # Q2 and Q3 are independent dimensions, not branches. Reachability does
        # not apply, and reporting it would be a false positive on the shape
        # integration-pattern-selection.md actually uses.
        self.assertEqual(self.kinds(self.write("checklist.md", CHECKLIST)), [])

    def test_reachability_crosses_fenced_block_boundaries(self):
        # Q2/Q3/Q4 are each defined in a different block from the branch that
        # routes to them. Per-block analysis called all three unreachable.
        issues = self.kinds(self.write("routed.md", ROUTED))
        self.assertNotIn("unreachable-question", issues)


class DetectsRealDefects(TreeCheckBase):
    def test_unresolvable_skill_reference_backticked(self):
        text = ROUTED.replace("`apex/trigger-framework`", "`apex/no-such-skill`")
        self.assertIn("unresolvable-skill-reference", self.kinds(self.write("t.md", text)))

    def test_unresolvable_skill_reference_path_form(self):
        text = ROUTED + "\nAlso read skills/apex/does-not-exist for background.\n"
        self.assertIn("unresolvable-skill-reference", self.kinds(self.write("t.md", text)))

    def test_reference_to_unknown_domain_is_not_a_skill_reference(self):
        # `docs/architecture` and `1/2` share the shape but are not skills.
        text = ROUTED + "\nSee `docs/architecture` and a 1/2 split.\n"
        self.assertEqual(self.kinds(self.write("t.md", text)), [])

    def test_dangling_branch_target(self):
        text = ROUTED.replace("→ Q3", "→ Q77")
        self.assertIn("dangling-branch-target", self.kinds(self.write("t.md", text)))

    def test_unreachable_question_when_its_only_arrow_is_removed(self):
        text = ROUTED.replace("└── No  → Q3", "└── No  → Done")
        self.assertIn("unreachable-question", self.kinds(self.write("t.md", text)))


class Severity(TreeCheckBase):
    def test_structural_defects_are_errors(self):
        text = ROUTED.replace("`apex/trigger-framework`", "`apex/no-such-skill`")
        levels = {i["level"] for i in check_tree(self.write("t.md", text), self.root)}
        self.assertEqual(levels, {"ERROR"})

    def test_reachability_is_only_a_warning(self):
        # Deliberate: routed and sequential questions are not mechanically
        # separable, so this one advises rather than blocks.
        text = ROUTED.replace("└── No  → Q3", "└── No  → Done")
        issues = check_tree(self.write("t.md", text), self.root)
        unreachable = [i for i in issues if i["kind"] == "unreachable-question"]
        self.assertTrue(unreachable)
        self.assertEqual({i["level"] for i in unreachable}, {"WARN"})


class RootHandling(TreeCheckBase):
    def test_relative_root_does_not_raise(self):
        # collect_issues(Path(".")) used to blow up in relative_to().
        self.write("routed.md", ROUTED)
        self.assertEqual(collect_issues(self.root), [])

    def test_missing_tree_directory_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(collect_issues(Path(empty)), [])


if __name__ == "__main__":
    unittest.main()
