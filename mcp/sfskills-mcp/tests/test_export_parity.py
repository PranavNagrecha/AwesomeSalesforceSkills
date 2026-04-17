"""Export determinism + first-class parity tests.

Wave-2 contract: exports must be byte-deterministic across runs and the
Claude + Cursor + MCP targets must carry the same set of skill IDs. Wave-6
promotes these assertions to GitHub Actions; this module is what CI runs.

Three assertions:

1.  Determinism — running ``scripts/export_skills.py --all --manifest`` three
    times produces the same ``registry/export_manifest.json`` bytes every
    time. Any drift means a non-deterministic exporter (file ordering,
    timestamp leak, dict-iteration ordering) has snuck in.

2.  Set parity — the first-class targets (Claude, Cursor, MCP) contain the
    same SET of skill IDs. Content per target differs (Cursor wraps in
    ``.mdc``, MCP bundles the registry) but the SET must match.

3.  Manifest shape — the manifest has the expected schema: per-target
    ``overall_hash``, ``skill_count``, ``skills`` map keyed on skill id.

Run with:

    cd mcp/sfskills-mcp
    python3 -m unittest tests.test_export_parity

Requires PyYAML (already in root requirements.txt).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
EXPORT_SCRIPT = REPO / "scripts" / "export_skills.py"


def _run_export(scratch: Path, *args: str) -> subprocess.CompletedProcess:
    """Run export_skills.py against a scratch output dir and return the
    completed process. The real registry/export_manifest.json is NEVER
    touched by these tests — we always redirect to ``--output <scratch>``.
    """
    cmd = [sys.executable, str(EXPORT_SCRIPT), "--output", str(scratch)] + list(args)
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)


def _hash_scratch_tree(scratch: Path) -> dict:
    """Build a manifest from a scratch export dir by importing
    ``export_skills._build_manifest``. Isolates the "did the output change"
    question from the "did the CLI wrapper change" question.
    """
    sys.path.insert(0, str(REPO))
    try:
        from scripts.export_skills import PLATFORMS, _build_manifest
    finally:
        sys.path.pop(0)
    return _build_manifest(scratch, PLATFORMS)


class TestExportParity(unittest.TestCase):
    """Assertions about the export pipeline's determinism + parity."""

    @classmethod
    def setUpClass(cls):
        if not EXPORT_SCRIPT.exists():
            raise unittest.SkipTest(f"{EXPORT_SCRIPT} not present")

    def test_export_is_deterministic_across_three_runs(self):
        """Three runs must produce three identical manifests.

        This catches:
          - dict-iteration ordering leaks (historically a problem pre-Py3.7)
          - timestamp leaks (anything writing datetime.now() into output)
          - filesystem-ordering leaks (os.listdir vs sorted())
          - hash-seed drift (hashlib isn't affected, but a dict keyed on an
            unhashable-by-identity object would be)
        """
        with tempfile.TemporaryDirectory(prefix="sfskills-parity-") as tmp:
            scratch = Path(tmp)
            hashes = []
            for run in range(3):
                run_dir = scratch / f"run-{run}"
                proc = _run_export(run_dir, "--all")
                self.assertEqual(
                    proc.returncode, 0,
                    f"export run {run} failed:\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
                )
                manifest = _hash_scratch_tree(run_dir)
                # Drop the generated_at timestamp — it's expected to change.
                manifest.pop("generated_at", None)
                hashes.append(json.dumps(manifest, sort_keys=True))

            self.assertEqual(
                hashes[0], hashes[1],
                "Export non-deterministic: run 1 differs from run 0",
            )
            self.assertEqual(
                hashes[1], hashes[2],
                "Export non-deterministic: run 2 differs from run 1",
            )

    def test_first_class_targets_have_identical_skill_sets(self):
        """Claude + Cursor + MCP must all contain the same set of skill IDs.

        Cursor's .mdc wrapper byte-differs from Claude's SKILL.md, so we
        don't assert byte parity across the three — only set parity of the
        skill-id keys.
        """
        with tempfile.TemporaryDirectory(prefix="sfskills-setparity-") as tmp:
            scratch = Path(tmp)
            proc = _run_export(scratch, "--all")
            self.assertEqual(proc.returncode, 0, proc.stderr)

            manifest = _hash_scratch_tree(scratch)
            targets = manifest["targets"]

            claude_ids = set(targets["claude"]["skills"])
            cursor_ids = set(targets["cursor"]["skills"])
            mcp_ids = set(targets["mcp"]["skills"])

            self.assertEqual(
                claude_ids, cursor_ids,
                f"Claude XOR Cursor skill-id set: "
                f"{sorted(claude_ids ^ cursor_ids)[:5]}",
            )
            self.assertEqual(
                claude_ids, mcp_ids,
                f"Claude XOR MCP skill-id set: "
                f"{sorted(claude_ids ^ mcp_ids)[:5]}",
            )

    def test_manifest_has_expected_shape(self):
        """Every target has overall_hash + skill_count + skills map; every
        hash is prefixed ``sha256:`` so the format is unambiguous."""
        with tempfile.TemporaryDirectory(prefix="sfskills-shape-") as tmp:
            scratch = Path(tmp)
            proc = _run_export(scratch, "--all")
            self.assertEqual(proc.returncode, 0, proc.stderr)

            manifest = _hash_scratch_tree(scratch)
            self.assertIn("schema_version", manifest)
            self.assertIn("first_class_targets", manifest)
            self.assertEqual(
                sorted(manifest["first_class_targets"]),
                ["claude", "cursor", "mcp"],
            )

            for name, data in manifest["targets"].items():
                self.assertIn("overall_hash", data, f"{name} missing overall_hash")
                self.assertTrue(
                    data["overall_hash"].startswith("sha256:"),
                    f"{name}.overall_hash missing sha256: prefix",
                )
                self.assertIn("skill_count", data)
                self.assertIn("skills", data)
                self.assertGreater(
                    data["skill_count"], 0,
                    f"{name} produced zero skills",
                )

    def test_cli_check_mode_against_committed_manifest(self):
        """If a committed registry/export_manifest.json exists, ``--check``
        exits 0 when the tree matches. If it doesn't exist, the test is a
        no-op (nothing to diff against yet)."""
        manifest_path = REPO / "registry" / "export_manifest.json"
        if not manifest_path.exists():
            self.skipTest("No committed manifest yet")
        proc = subprocess.run(
            [sys.executable, str(EXPORT_SCRIPT), "--check"],
            cwd=REPO, capture_output=True, text=True,
        )
        self.assertEqual(
            proc.returncode, 0,
            f"`export_skills.py --check` reports drift vs committed "
            f"manifest:\n{proc.stdout}\n{proc.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
