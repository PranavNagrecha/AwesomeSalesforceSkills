"""Unit tests for ``scripts/check_doc_counts.py``.

This lint is the regression guard for the "56 agents" drift: the roster docs
quoted a headline that no longer matched the AGENT.md frontmatter, and nine
deprecated agents sat inside the runtime tiers for weeks. A count lint that
cannot FAIL is worse than none — it launders drift as verified.

So the emphasis here is the negative direction: every check must produce an
issue when the doc is wrong, and ``--fix`` must actually rewrite the file.

Everything runs against a synthetic six-agent / three-skill root in a temp dir.
No corpus, no registry rebuild.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_doc_counts import (  # noqa: E402
    apply_fixes,
    canonical_counts,
    collect_doc_count_issues,
)


# Canonical shape of the synthetic repo:
#   3 skills (admin 2, apex 1)
#   6 agents = 1 build + 4 active runtime (tiers 1/1/1/1) + 1 deprecated
#   2 MCP tools, 1 flagship eval
SKILLS_TOTAL = 3
AGENTS_TOTAL = 6
BUILD = 1
ACTIVE_RUNTIME = 4
DEPRECATED = 1
MCP_TOOLS = 2
EVALS = 1

TIERS = (
    "- **Developer + architecture (1)** — `/build-apex`.\n"
    "- **Admin accelerators — Tier 1 (1)** — `/design-object`.\n"
    "- **Strategic — Tier 2 (1)** — `/run-fit-gap`.\n"
    "- **Vertical + governance — Tier 3 (1)** — `/assess-waf`.\n"
)

README = f"""# SfSkills

**{SKILLS_TOTAL} skills · {AGENTS_TOTAL} agents** in one library.

The corpus — {SKILLS_TOTAL} structured guides you can read end to end.

The MCP server exposes {MCP_TOOLS} tools across skill, agent and template search.

## Agents

- **Build-time ({BUILD})** — the library builders.
- **Run-time ({ACTIVE_RUNTIME})** — the agents that do Salesforce work.

{TIERS}
The server ships {MCP_TOOLS} read-only tools — the fifteen-minute setup is in the MCP README.

Ask anything of the {SKILLS_TOTAL}-skill SfSkills corpus.

- [x] {SKILLS_TOTAL} skills across every domain
- [x] Golden evals for {EVALS} flagship skills

## Covered Skills

| Domain | Count |
| --- | --- |
| Admin | 2 — declarative configuration |
| Apex | 1 — code and SOQL |
"""

MCP_README = f"""# sfskills-mcp

Serves the SfSkills library ({SKILLS_TOTAL}+ Salesforce skills) over MCP.

Agent search covers the roster ({ACTIVE_RUNTIME} active runtime agents), plus
{BUILD} build-time agents and
{DEPRECATED} deprecation stubs.

{TIERS}"""

CLAUDE_MD = f"""# CLAUDE.md

### Run-time agents ({ACTIVE_RUNTIME})

{TIERS}"""

AGENT_RULES = f"""# AGENT_RULES.md

- **Build-time ({BUILD})** — library builders.
- **Run-time ({ACTIVE_RUNTIME})** — Salesforce work.

{TIERS}"""

RUNTIME_VS_BUILD = f"""# Runtime vs Build

## Build-time agents ({BUILD})

## Run-time agents ({ACTIVE_RUNTIME})

{TIERS}
## Deprecated ({DEPRECATED})
"""

AGENTS = [
    ("build-skills", "build", "active"),
    ("build-apex", "runtime", "active"),
    ("design-object", "runtime", "active"),
    ("run-fit-gap", "runtime", "active"),
    ("assess-waf", "runtime", "active"),
    ("audit-sharing", "runtime", "deprecated"),
]


def make_root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="sfskills-docs-"))

    (root / "registry").mkdir()
    (root / "registry" / "skills.json").write_text(
        json.dumps({"skill_count": SKILLS_TOTAL, "domain_counts": {"admin": 2, "apex": 1}}),
        encoding="utf-8",
    )

    for name, cls, status in AGENTS:
        agent_dir = root / "agents" / name
        agent_dir.mkdir(parents=True)
        (agent_dir / "AGENT.md").write_text(
            f"---\nname: {name}\nclass: {cls}\nstatus: {status}\n---\n\n# {name}\n", encoding="utf-8"
        )

    server = root / "mcp" / "sfskills-mcp" / "src" / "sfskills_mcp"
    server.mkdir(parents=True)
    (server / "server.py").write_text(
        "@mcp.tool()\ndef search_skill(): ...\n\n@mcp.tool()\ndef search_agent(): ...\n",
        encoding="utf-8",
    )

    (root / "evals" / "golden").mkdir(parents=True)
    (root / "evals" / "golden" / "trigger-recursion.md").write_text("# eval\n", encoding="utf-8")

    (root / "agents" / "_shared").mkdir(parents=True)
    for rel, text in (
        ("README.md", README),
        ("mcp/sfskills-mcp/README.md", MCP_README),
        ("CLAUDE.md", CLAUDE_MD),
        ("AGENT_RULES.md", AGENT_RULES),
        ("agents/_shared/RUNTIME_VS_BUILD.md", RUNTIME_VS_BUILD),
    ):
        (root / rel).write_text(text, encoding="utf-8")

    return root


class RootMixin:
    def setUp(self):
        self.root = make_root()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def edit(self, rel: str, old: str, new: str) -> None:
        path = self.root / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"fixture drift: {old!r} not in {rel}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def joined(self) -> str:
        return " | ".join(f"{path}: {msg}" for _lvl, path, msg in collect_doc_count_issues(self.root))


class CanonicalCountsTest(RootMixin, unittest.TestCase):
    """Counts are DERIVED. A hardcoded number here is the "56" regression."""

    def test_derives_every_count_from_machine_sources(self):
        self.assertEqual(
            canonical_counts(self.root),
            {
                "skills_total": SKILLS_TOTAL,
                "domain_counts": {"admin": 2, "apex": 1},
                "agents_total": AGENTS_TOTAL,
                "build": BUILD,
                "active_runtime": ACTIVE_RUNTIME,
                "deprecated": DEPRECATED,
                "mcp_tools": MCP_TOOLS,
                "evals_flagship": EVALS,
            },
        )

    def test_status_deprecated_wins_over_class_runtime(self):
        """The exact invariant that broke: a deprecated agent still carries
        `class: runtime`, and must NOT be counted as active."""
        counts = canonical_counts(self.root)
        runtime_class = sum(1 for _n, cls, _s in AGENTS if cls == "runtime")
        self.assertEqual(runtime_class, ACTIVE_RUNTIME + DEPRECATED)
        self.assertEqual(counts["active_runtime"], ACTIVE_RUNTIME)

    def test_promoting_an_agent_moves_the_canonical_count(self):
        agent = self.root / "agents" / "audit-sharing" / "AGENT.md"
        agent.write_text(agent.read_text(encoding="utf-8").replace("deprecated", "active"), encoding="utf-8")
        counts = canonical_counts(self.root)
        self.assertEqual(counts["active_runtime"], ACTIVE_RUNTIME + 1)
        self.assertEqual(counts["deprecated"], 0)
        self.assertEqual(counts["agents_total"], AGENTS_TOTAL)


class PassingRepoTest(RootMixin, unittest.TestCase):

    def test_a_consistent_repo_reports_no_issues(self):
        self.assertEqual(collect_doc_count_issues(self.root), [])


class DriftIsDetectedTest(RootMixin, unittest.TestCase):
    """One test per drift shape. Each must FAIL the lint — a lint that only
    ever passes is the failure mode this file exists to prevent."""

    def assert_fails(self, needle: str) -> None:
        issues = collect_doc_count_issues(self.root)
        self.assertTrue(issues, "expected a doc-count error, got none")
        self.assertIn("ERROR", {level for level, _p, _m in issues})
        self.assertIn(needle, self.joined())

    def test_wrong_skill_total_in_the_readme_headline(self):
        self.edit("README.md", f"**{SKILLS_TOTAL} skills ·", "**999 skills ·")
        self.assert_fails("skills_total is 999 in doc but canonical is 3")

    def test_wrong_agent_total_in_the_readme_headline(self):
        self.edit("README.md", f"· {AGENTS_TOTAL} agents", "· 56 agents")
        self.assert_fails("agents_total is 56 in doc but canonical is 6")

    def test_wrong_mcp_tool_count(self):
        self.edit("README.md", f"{MCP_TOOLS} tools across skill", "17 tools across skill")
        self.assert_fails("mcp_tools is 17 in doc but canonical is 2")

    def test_wrong_build_agent_count(self):
        self.edit("AGENT_RULES.md", f"**Build-time ({BUILD})**", "**Build-time (9)**")
        self.assert_fails("build is 9 in doc but canonical is 1")

    def test_wrong_active_runtime_count_in_claude_md(self):
        self.edit("CLAUDE.md", f"Run-time agents ({ACTIVE_RUNTIME})", "Run-time agents (47)")
        self.assert_fails("active_runtime is 47 in doc but canonical is 4")

    def test_wrong_deprecated_count_in_the_mcp_readme(self):
        self.edit("mcp/sfskills-mcp/README.md", f"{DEPRECATED} deprecation stubs", "14 deprecation stubs")
        self.assert_fails("deprecated is 14 in doc but canonical is 1")

    def test_wrong_flagship_eval_count(self):
        self.edit("README.md", f"Golden evals for {EVALS} flagship", "Golden evals for 10 flagship")
        self.assert_fails("evals_flagship is 10 in doc but canonical is 1")

    def test_wrong_per_domain_count_in_the_covered_skills_table(self):
        self.edit("README.md", "| Admin | 2 —", "| Admin | 252 —")
        self.assert_fails("Covered-Skills table: admin shows 252 but canonical is 2")

    def test_runtime_tiers_that_do_not_sum_to_the_active_total(self):
        """The nine-deprecated-agents-in-the-tiers bug, reproduced."""
        self.edit("README.md", "Vertical + governance — Tier 3 (1)", "Vertical + governance — Tier 3 (10)")
        self.assert_fails("runtime tiers sum to 13 (1+1+1+10) but active-runtime total is 4")

    def test_a_removed_label_is_an_error_not_a_silent_pass(self):
        """If a doc is restructured so a labelled count disappears, the lint
        must say it can no longer guard it — not quietly succeed."""
        self.edit("README.md", f"Golden evals for {EVALS} flagship", "Golden evals for flagship")
        self.assert_fails("labelled count not found")

    def test_a_removed_tier_heading_is_an_error(self):
        self.edit("AGENT_RULES.md", "Strategic — Tier 2 (1)", "Strategic agents")
        self.assert_fails("runtime-tier header not found")

    def test_a_missing_doc_is_an_error(self):
        (self.root / "AGENT_RULES.md").unlink()
        self.assert_fails("file not found")

    def test_adding_an_agent_without_updating_the_docs_fails(self):
        """End-to-end: the drift the lint is actually deployed against."""
        agent_dir = self.root / "agents" / "design-flow"
        agent_dir.mkdir()
        (agent_dir / "AGENT.md").write_text(
            "---\nname: design-flow\nclass: runtime\nstatus: active\n---\n\n# design-flow\n",
            encoding="utf-8",
        )
        issues = collect_doc_count_issues(self.root)
        self.assertTrue(issues)
        joined = self.joined()
        self.assertIn("agents_total is 6 in doc but canonical is 7", joined)
        self.assertIn("active_runtime is 4 in doc but canonical is 5", joined)

    def test_every_doc_quoting_a_count_is_checked_not_just_the_readme(self):
        for rel, old, new in (
            ("README.md", f"**{SKILLS_TOTAL} skills ·", "**8 skills ·"),
            ("mcp/sfskills-mcp/README.md", f"({SKILLS_TOTAL}+ Salesforce", "(8+ Salesforce"),
            ("CLAUDE.md", f"Run-time agents ({ACTIVE_RUNTIME})", "Run-time agents (8)"),
            ("AGENT_RULES.md", f"**Run-time ({ACTIVE_RUNTIME})**", "**Run-time (8)**"),
            ("agents/_shared/RUNTIME_VS_BUILD.md", f"Deprecated ({DEPRECATED})", "Deprecated (8)"),
        ):
            with self.subTest(doc=rel):
                root = make_root()
                path = root / rel
                path.write_text(path.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8")
                try:
                    paths = {p for _l, p, _m in collect_doc_count_issues(root)}
                    self.assertIn(rel, paths)
                finally:
                    shutil.rmtree(root, ignore_errors=True)


class ApplyFixesTest(RootMixin, unittest.TestCase):

    def test_a_clean_repo_needs_no_fixes(self):
        self.assertEqual(apply_fixes(self.root), {})

    def test_fix_rewrites_the_file_and_clears_the_issue(self):
        self.edit("README.md", f"**{SKILLS_TOTAL} skills ·", "**999 skills ·")
        changes = apply_fixes(self.root)
        self.assertIn("README.md", changes)
        self.assertIn("skills_total: 999 -> 3", " ".join(changes["README.md"]))
        self.assertEqual(collect_doc_count_issues(self.root), [])

    def test_fix_repairs_every_drifted_doc_in_one_pass(self):
        self.edit("README.md", f"**{SKILLS_TOTAL} skills ·", "**999 skills ·")
        self.edit("CLAUDE.md", f"Run-time agents ({ACTIVE_RUNTIME})", "Run-time agents (47)")
        self.edit("mcp/sfskills-mcp/README.md", f"{DEPRECATED} deprecation stubs", "14 deprecation stubs")
        apply_fixes(self.root)
        self.assertEqual(collect_doc_count_issues(self.root), [])

    def test_fix_preserves_thousands_comma_formatting(self):
        big = self.root / "registry" / "skills.json"
        big.write_text(
            json.dumps({"skill_count": 1027, "domain_counts": {"admin": 2, "apex": 1}}), encoding="utf-8"
        )
        self.edit("README.md", f"**{SKILLS_TOTAL} skills ·", "**1,004 skills ·")
        apply_fixes(self.root)
        self.assertIn("**1,027 skills ·", (self.root / "README.md").read_text(encoding="utf-8"))

    def test_fix_repairs_the_covered_skills_table(self):
        self.edit("README.md", "| Admin | 2 —", "| Admin | 252 —")
        changes = apply_fixes(self.root)
        self.assertIn("Covered-Skills Admin: 252 -> 2", " ".join(changes["README.md"]))
        self.assertIn("| Admin | 2 —", (self.root / "README.md").read_text(encoding="utf-8"))

    def test_fix_does_not_touch_runtime_tier_breakdowns(self):
        """Only the tier SUM has a canonical machine source; the split is a
        doc-level decision and must be left for a human."""
        self.edit("README.md", "Vertical + governance — Tier 3 (1)", "Vertical + governance — Tier 3 (10)")
        apply_fixes(self.root)
        text = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("Vertical + governance — Tier 3 (10)", text)
        self.assertTrue(collect_doc_count_issues(self.root))

    def test_fix_leaves_untouched_files_byte_identical(self):
        before = {
            rel: (self.root / rel).read_bytes()
            for rel in ("CLAUDE.md", "AGENT_RULES.md", "agents/_shared/RUNTIME_VS_BUILD.md")
        }
        self.edit("README.md", f"**{SKILLS_TOTAL} skills ·", "**999 skills ·")
        apply_fixes(self.root)
        for rel, blob in before.items():
            self.assertEqual((self.root / rel).read_bytes(), blob, rel)

    def test_fix_is_idempotent(self):
        self.edit("README.md", f"**{SKILLS_TOTAL} skills ·", "**999 skills ·")
        apply_fixes(self.root)
        first = (self.root / "README.md").read_bytes()
        self.assertEqual(apply_fixes(self.root), {})
        self.assertEqual((self.root / "README.md").read_bytes(), first)


class FrontmatterFieldTest(unittest.TestCase):
    """The AGENT.md frontmatter reader — CLAUDE.md makes it the canonical
    source for agent class/status, so a silent None here mis-counts the roster."""

    def setUp(self):
        from scripts.check_doc_counts import _frontmatter_field

        self.read = _frontmatter_field

    def test_reads_a_quoted_and_an_unquoted_value(self):
        text = '---\nname: build-apex\nclass: "runtime"\nstatus: \'active\'\n---\nbody\n'
        self.assertEqual(self.read(text, "name"), "build-apex")
        self.assertEqual(self.read(text, "class"), "runtime")
        self.assertEqual(self.read(text, "status"), "active")

    def test_absent_field_is_none(self):
        self.assertIsNone(self.read("---\nname: x\n---\n", "class"))

    def test_file_without_frontmatter_is_none(self):
        self.assertIsNone(self.read("# Just a heading\n", "class"))

    def test_a_matching_key_in_the_body_is_not_read(self):
        text = "---\nname: x\n---\n\nclass: runtime should not be read from prose\n"
        self.assertIsNone(self.read(text, "class"))


if __name__ == "__main__":
    unittest.main()
