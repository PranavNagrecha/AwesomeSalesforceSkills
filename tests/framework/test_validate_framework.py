from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = ROOT / "framework" / "specification"


class MigrationReconcileTests(unittest.TestCase):
    def test_live_repo_matches_ledgers(self) -> None:
        from pipelines.framework.migration_reconcile import reconcile_migration_ledgers

        result = reconcile_migration_ledgers(ROOT)
        self.assertTrue(result.valid, json.dumps(result.to_dict(), indent=2))
        self.assertEqual(result.counts["skills"]["live"], result.counts["skills"]["ledger"])
        self.assertEqual(result.counts["agents"]["live"], result.counts["agents"]["ledger"])
        self.assertEqual(result.counts["commands"]["live"], result.counts["commands"]["ledger"])
        self.assertEqual(result.counts["mcp_tools"]["live"], result.counts["mcp_tools"]["ledger"])


class ValidateFrameworkCliTests(unittest.TestCase):
    def test_cli_passes_on_clean_tree(self) -> None:
        proc = subprocess.run(  # noqa: S603
            [
                "python3",
                str(ROOT / "scripts" / "validate_framework.py"),
                "--skip-spec-checks",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["valid"])
        self.assertTrue(payload["migration"]["valid"])


class PackV2ReviewScaffoldTests(unittest.TestCase):
    def test_validate_mode_rejects_missing_zip(self) -> None:
        proc = subprocess.run(  # noqa: S603
            [
                "python3",
                str(ROOT / "scripts" / "pack_v2_review.py"),
                "--validate",
                str(ROOT / "dist" / "reviews" / "does-not-exist.zip"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)


class SpecImportTests(unittest.TestCase):
    def test_specification_paths_present(self) -> None:
        required = [
            "VERSION",
            "implementation/requirements.csv",
            "implementation/REVIEW_RETURN_CONTRACT.md",
            "reference-kernel/saef_kernel",
            "migration/catalogs/current-skills.csv",
        ]
        for rel in required:
            self.assertTrue((SPEC_ROOT / rel).exists(), rel)


if __name__ == "__main__":
    unittest.main()
