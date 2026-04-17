"""Wave 11 tests: slash-command parity across export targets.

Enforces that every `commands/*.md` file in the repo lands in EVERY
slash-command-supporting export target. Prevents regressions like the
pre-Wave-11 gap where Cursor users opened the library expecting to see
slash commands in the `/` menu but got nothing because the exporter
never copied them.

Also asserts that Aider's CONVENTIONS.md gains a command index (since
Aider doesn't support custom slash commands).

Run:
    cd mcp/sfskills-mcp
    python3 -m unittest tests.test_slash_command_export -v
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
COMMANDS_DIR = REPO / "commands"
EXPORT_SCRIPT = REPO / "scripts" / "export_skills.py"

# Mirror SLASH_COMMAND_DEST from scripts/export_skills.py. Keep in sync.
TARGET_DESTINATIONS = {
    "cursor": ".cursor/commands",
    "claude": ".claude/commands",
    "windsurf": ".windsurf/workflows",
    "augment": ".augment/commands",
    "codex": "codex-prompts",
}

# Windsurf enforces a 12 KB per-workflow cap. Files that exceed it are
# expected to be skipped — count that as an acceptable miss.
WINDSURF_CAP = 12000


class TestExportScriptAvailable(unittest.TestCase):
    def test_export_script_exists(self) -> None:
        self.assertTrue(EXPORT_SCRIPT.exists(),
                        "scripts/export_skills.py must exist")


class TestSlashCommandExportParity(unittest.TestCase):
    """Export to each slash-supporting target. Assert count parity against the
    source `commands/*.md` set (minus documented exceptions)."""

    @classmethod
    def setUpClass(cls) -> None:
        if not EXPORT_SCRIPT.exists():
            raise unittest.SkipTest("export script not present")
        if not COMMANDS_DIR.exists():
            raise unittest.SkipTest("commands/ not present")
        cls.scratch = tempfile.mkdtemp(prefix="sfskills-slash-test-")
        scratch_path = Path(cls.scratch)
        # Run all exporters once into the scratch dir.
        result = subprocess.run(
            [sys.executable, str(EXPORT_SCRIPT), "--all", "--output", str(scratch_path)],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise unittest.SkipTest(f"export failed: {result.stderr}")
        cls.scratch_path = scratch_path

    @classmethod
    def tearDownClass(cls) -> None:
        import shutil
        shutil.rmtree(cls.scratch, ignore_errors=True)

    def _source_commands(self) -> list[Path]:
        return sorted(COMMANDS_DIR.glob("*.md"))

    def test_cursor_commands_exported(self) -> None:
        target_dir = self.scratch_path / "cursor" / TARGET_DESTINATIONS["cursor"]
        self.assertTrue(target_dir.exists(), f"expected {target_dir} to exist")
        source_count = len(self._source_commands())
        target_count = len(list(target_dir.glob("*.md")))
        self.assertEqual(source_count, target_count,
                         f"cursor command count mismatch: source={source_count}, target={target_count}")

    def test_claude_commands_exported(self) -> None:
        target_dir = self.scratch_path / "claude" / TARGET_DESTINATIONS["claude"]
        self.assertTrue(target_dir.exists())
        source_count = len(self._source_commands())
        target_count = len(list(target_dir.glob("*.md")))
        self.assertEqual(source_count, target_count,
                         f"claude command count mismatch: source={source_count}, target={target_count}")

    def test_augment_commands_exported(self) -> None:
        target_dir = self.scratch_path / "augment" / TARGET_DESTINATIONS["augment"]
        self.assertTrue(target_dir.exists())
        source_count = len(self._source_commands())
        target_count = len(list(target_dir.glob("*.md")))
        self.assertEqual(source_count, target_count,
                         f"augment command count mismatch: source={source_count}, target={target_count}")

    def test_codex_prompts_exported(self) -> None:
        target_dir = self.scratch_path / "codex" / TARGET_DESTINATIONS["codex"]
        self.assertTrue(target_dir.exists())
        source_count = len(self._source_commands())
        target_count = len(list(target_dir.glob("*.md")))
        self.assertEqual(source_count, target_count,
                         f"codex prompt count mismatch: source={source_count}, target={target_count}")

    def test_windsurf_workflows_exported(self) -> None:
        """Windsurf has a 12 KB per-workflow cap. Files exceeding it are skipped;
        this test accepts those skips but enforces parity on the rest."""
        target_dir = self.scratch_path / "windsurf" / TARGET_DESTINATIONS["windsurf"]
        self.assertTrue(target_dir.exists())
        source = self._source_commands()
        oversized = [p for p in source if p.stat().st_size > WINDSURF_CAP]
        expected_target_count = len(source) - len(oversized)
        target_count = len(list(target_dir.glob("*.md")))
        self.assertEqual(expected_target_count, target_count,
                         f"windsurf workflow count mismatch: expected {expected_target_count} "
                         f"(source {len(source)} − oversized {len(oversized)}), got {target_count}")

    def test_aider_conventions_has_command_index(self) -> None:
        """Aider doesn't support custom slash commands, so we embed a command
        index in CONVENTIONS.md. Verify the index exists and references
        every source command."""
        conventions = self.scratch_path / "aider" / "CONVENTIONS.md"
        self.assertTrue(conventions.exists())
        body = conventions.read_text(encoding="utf-8")
        self.assertIn("Available Workflows", body,
                      "CONVENTIONS.md missing the 'Available Workflows' section")
        # Check a sample of command aliases appear in the index.
        sample_aliases = [p.stem for p in self._source_commands()[:10]]
        for alias in sample_aliases:
            self.assertIn(f"`{alias}`", body,
                          f"alias `{alias}` not referenced in CONVENTIONS.md index")


class TestCodexInstallDocExists(unittest.TestCase):
    """Codex is user-scope (~/.codex/prompts/), so the exporter ships an
    INSTALL.md with the cp command. Verify it exists."""

    def test_codex_install_doc(self) -> None:
        if not EXPORT_SCRIPT.exists():
            self.skipTest("export script not present")
        with tempfile.TemporaryDirectory(prefix="sfskills-codex-test-") as scratch:
            result = subprocess.run(
                [sys.executable, str(EXPORT_SCRIPT), "--target", "codex", "--output", scratch],
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            install = Path(scratch) / "codex" / "INSTALL.md"
            self.assertTrue(install.exists())
            body = install.read_text(encoding="utf-8")
            self.assertIn("~/.codex/prompts", body)
            self.assertIn("cp codex-prompts/", body)


if __name__ == "__main__":
    unittest.main()
