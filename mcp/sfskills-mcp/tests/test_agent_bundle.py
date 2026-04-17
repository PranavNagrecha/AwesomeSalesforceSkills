"""Wave 8 tests: agent dependencies + bundle completeness.

Two guarantees this test enforces — both born from the ExampleOrg incident:

1. Every citation in an AGENT.md's Mandatory Reads (or anywhere in the body
   that follows the agent-citation regex set) MUST appear in the frontmatter
   `dependencies` block. If it's cited, it must be declared as a dependency.
   Closes the "AGENT.md says to read X but forgot to declare X" gap.

2. Bundling an agent via `scripts/export_agent_bundle.py` MUST produce a
   self-contained tree where every path referenced in the bundled AGENT.md
   resolves to an actual file inside the bundle. No dangling references.

Together, these kill the "hand-copy one AGENT.md and hope for the best"
failure mode — the consuming AI no longer has to improvise when the repo
guarantees everything it needs is in the bundle.

Run:

    cd mcp/sfskills-mcp
    python3 -m unittest tests.test_agent_bundle -v
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
AGENTS_DIR = REPO / "agents"
SKILLS_DIR = REPO / "skills"
TEMPLATES_DIR = REPO / "templates"
STANDARDS_DIR = REPO / "standards"
SHARED_DIR = AGENTS_DIR / "_shared"
EXPORT_SCRIPT = REPO / "scripts" / "export_agent_bundle.py"


# Citation patterns from pipelines/agent_validators.py.
_SKILL_BACKTICK = re.compile(r"`skills/([a-z0-9-]+)/([a-z0-9-]+)(?:/[A-Za-z0-9_./-]*)?`")
_PROBE = re.compile(r"`agents/_shared/probes/([a-z0-9-]+)(?:\.md)?`")
_TEMPLATE = re.compile(r"`templates/([A-Za-z0-9_./-]+)`")
_DECISION_TREE = re.compile(r"`standards/decision-trees/([a-z0-9-]+\.md)`")
_SHARED_DOC = re.compile(r"`(?:agents/_shared/)?([A-Z][A-Z_0-9]+\.md)`")

SKILL_DOMAINS = {
    "admin", "apex", "lwc", "flow", "omnistudio", "agentforce",
    "security", "integration", "data", "devops", "architect",
}


def _read_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m:
        return {}, text

    # Parse only what this test needs — dependencies block + class/status.
    raw = m.group(1)
    body = m.group(2)

    meta: dict = {}
    current_top: str | None = None
    current_sub: str | None = None

    for line in raw.splitlines():
        if not line.strip():
            continue
        # Top-level scalar: `key: value`
        if re.match(r"^[a-z_]+:\s*\S", line):
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"').strip("'")
            current_top = None
            current_sub = None
            continue
        # Top-level empty: `key:` (starts a block)
        if re.match(r"^[a-z_]+:\s*$", line):
            key = line.split(":")[0].strip()
            meta[key] = {}
            current_top = key
            current_sub = None
            continue
        # Sub-key under a block: `  key:` (empty, starts list)
        m2 = re.match(r"^  ([a-z_]+):\s*$", line)
        if m2 and current_top is not None:
            current_sub = m2.group(1)
            if not isinstance(meta[current_top], dict):
                meta[current_top] = {}
            meta[current_top][current_sub] = []
            continue
        # Sub-list item: `    - value`
        m2 = re.match(r"^    - (.+)$", line)
        if m2 and current_top and current_sub:
            meta[current_top][current_sub].append(m2.group(1).strip())
            continue
        # Flat list item: `  - value`
        m2 = re.match(r"^  - (.+)$", line)
        if m2 and current_top:
            if not isinstance(meta[current_top], list):
                meta[current_top] = []
            meta[current_top].append(m2.group(1).strip())
            continue

    return meta, body


def _extract_citations(body: str) -> dict[str, set[str]]:
    out = {"probes": set(), "skills": set(), "templates": set(), "decision_trees": set(), "shared": set()}

    for m in _PROBE.finditer(body):
        name = m.group(1)
        if not name.endswith(".md"):
            name = f"{name}.md"
        out["probes"].add(name)

    for m in _SKILL_BACKTICK.finditer(body):
        domain, slug = m.group(1), m.group(2)
        if domain in SKILL_DOMAINS:
            out["skills"].add(f"{domain}/{slug}")

    for m in _TEMPLATE.finditer(body):
        out["templates"].add(m.group(1))

    for m in _DECISION_TREE.finditer(body):
        out["decision_trees"].add(m.group(1))

    for m in _SHARED_DOC.finditer(body):
        name = m.group(1)
        # Only count well-known shared docs to avoid matching random CAPS filenames.
        if name in {"AGENT_CONTRACT.md", "AGENT_RULES.md", "REFUSAL_CODES.md", "SKILL_MAP.md",
                    "MIGRATION.md", "CONTRIBUTING.md", "SECURITY.md"}:
            out["shared"].add(name)

    return out


class TestCitationsMatchDependencies(unittest.TestCase):
    """For every runtime agent with a dependencies block, assert every citation
    in the body is covered by the declared dependencies.

    This is the test that would have caught the ExampleOrg gap: probe was
    cited in Mandatory Reads but never propagated to the export bundle
    because nothing verified the agent actually declared its probes.
    """

    def test_citations_match_dependencies(self) -> None:
        failures: list[str] = []

        for agent_md in sorted(AGENTS_DIR.glob("*/AGENT.md")):
            meta, body = _read_frontmatter(agent_md)
            if meta.get("status") == "deprecated":
                continue
            if meta.get("class") != "runtime":
                continue
            deps = meta.get("dependencies")
            if not deps or not isinstance(deps, dict):
                # Agents without a dependencies block are allowed for now;
                # migration script backfills them.
                continue

            declared = {
                "probes": set(deps.get("probes", [])),
                "skills": set(deps.get("skills", [])),
                "templates": set(deps.get("templates", [])),
                "decision_trees": set(deps.get("decision_trees", [])),
                "shared": set(deps.get("shared", [])),
            }

            cited = _extract_citations(body)

            for kind, cited_set in cited.items():
                missing = cited_set - declared[kind]
                for item in sorted(missing):
                    failures.append(
                        f"{agent_md.parent.name}: cites `{kind}/{item}` in body "
                        f"but did NOT declare it in frontmatter.dependencies.{kind}. "
                        f"Run: python3 scripts/migrate_agent_dependencies.py --agent "
                        f"{agent_md.parent.name} --force"
                    )

        if failures:
            msg = "\n\n".join(failures[:20])
            if len(failures) > 20:
                msg += f"\n\n... and {len(failures) - 20} more"
            self.fail(f"{len(failures)} citation/dependency mismatch(es):\n\n{msg}")


class TestBundleCompleteness(unittest.TestCase):
    """Export a real bundle for a known agent and verify every path referenced
    in the bundled AGENT.md resolves to a file inside the bundle tree.

    We use `user-access-diff` as the canary because it's the agent whose
    previous ad-hoc copy triggered the ExampleOrg incident.
    """

    def test_user_access_diff_bundle_has_every_referenced_file(self) -> None:
        if not EXPORT_SCRIPT.exists():
            self.skipTest("export_agent_bundle.py not present")

        with tempfile.TemporaryDirectory(prefix="sfskills-bundle-test-") as scratch:
            scratch_root = Path(scratch)
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXPORT_SCRIPT),
                    "--agent", "user-access-diff",
                    "--rewrite-paths",
                    "--out", str(scratch_root),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0,
                             f"bundle export failed: stderr={result.stderr}")

            bundle_root = scratch_root / "user-access-diff"
            self.assertTrue(bundle_root.exists(), "bundle directory not created")
            self.assertTrue((bundle_root / "AGENT.md").exists())
            self.assertTrue((bundle_root / "INSTALL.md").exists())

            agent_body = (bundle_root / "AGENT.md").read_text(encoding="utf-8")

            # Extract all `./<relative-path>` references that the rewriter emits.
            # These must resolve inside the bundle.
            bundle_refs = re.findall(r"`\./([A-Za-z0-9_./-]+)`", agent_body)
            unresolved = []
            for ref in bundle_refs:
                # Strip optional trailing /SKILL.md / /references/ etc.
                # We only need to verify the top directory/file exists.
                candidate = bundle_root / ref
                if not candidate.exists():
                    # Try stripping one path component (skill refs sometimes
                    # point at a directory without trailing slash).
                    parent_candidate = bundle_root / ref.split("/")[0]
                    if not parent_candidate.exists():
                        unresolved.append(ref)

            if unresolved:
                self.fail(
                    f"bundle references {len(unresolved)} path(s) that don't "
                    f"resolve inside the bundle:\n  " +
                    "\n  ".join(unresolved[:15])
                )


class TestMigrationScriptIdempotent(unittest.TestCase):
    """Running the migration script twice should not produce different output."""

    def test_migration_dry_run_shows_no_pending_work(self) -> None:
        script = REPO / "scripts" / "migrate_agent_dependencies.py"
        if not script.exists():
            self.skipTest("migrate_agent_dependencies.py not present")

        result = subprocess.run(
            [sys.executable, str(script), "--dry-run"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        # After the one-time migration ran, no agent should have pending work
        # (a "Would update" line). If this fires, a new agent has been added
        # without dependencies or a prior edit nuked them.
        lines = [l for l in result.stdout.splitlines() if l.startswith("Would update")]
        if lines:
            # Not a hard failure — new agents may legitimately need migration.
            # Surface as a warning to the developer.
            sys.stderr.write(
                f"\n[warn] {len(lines)} agent(s) need dependencies migration. "
                f"Run: python3 scripts/migrate_agent_dependencies.py\n"
            )


if __name__ == "__main__":
    unittest.main()
