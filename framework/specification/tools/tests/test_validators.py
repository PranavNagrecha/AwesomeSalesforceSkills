from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile

from tools.validate_cursor_return import CORE_REQUIRED, ReturnValidator, sha256_file
from tools.validate_spec_package import PackageValidator


SPEC_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = SPEC_ROOT / "schemas/review-manifest.schema.json"


def write_text(path: Path, text: str = "ok\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_minimal_review(root: Path, *, status: str = "completed", test_exit: int = 0) -> None:
    for rel in sorted(CORE_REQUIRED - {"SHA256SUMS.txt", "source/repository-head.tar.gz", "builds/cursor-plugin.zip", "MANIFEST.json", "tests/test-index.json"}):
        write_text(root / rel)
    (root / "source/changed-files").mkdir(parents=True, exist_ok=True)
    write_text(root / "source/changed-files/example.py", "print('safe')\n")
    (root / "host-smoke/cursor").mkdir(parents=True, exist_ok=True)
    write_text(root / "host-smoke/cursor/discovery.md")
    (root / "runs/P01/run-example").mkdir(parents=True, exist_ok=True)
    write_text(root / "runs/P01/run-example/output.json", "{}\n")

    with tarfile.open(root / "source/repository-head.tar.gz", "w:gz") as archive:
        data = b"example\n"
        info = tarfile.TarInfo("repository/README.md")
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
    with zipfile.ZipFile(root / "builds/cursor-plugin.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("sfskills/.cursor-plugin/plugin.json", "{}\n")

    write_text(root / "tests/unit.stdout.txt", "OK\n")
    write_text(root / "tests/unit.stderr.txt", "")
    tests = [{
        "id": "unit",
        "command": "python3 -m unittest",
        "cwd": ".",
        "started_at": "2026-08-19T00:00:00Z",
        "ended_at": "2026-08-19T00:00:01Z",
        "duration_seconds": 1.0,
        "exit_code": test_exit,
        "stdout_path": "tests/unit.stdout.txt",
        "stderr_path": "tests/unit.stderr.txt",
        "required": True,
        "environment": {"python": "3.x"},
    }]
    write_text(root / "tests/test-index.json", json.dumps({"tests": tests}, indent=2) + "\n")

    baseline = "a" * 40
    head = "b" * 40
    write_text(root / "git/baseline.txt", baseline + "\n")
    write_text(root / "git/head.txt", head + "\n")
    write_text(root / "git/branch.txt", "product/sfskills-v2-local\n")
    write_text(root / "source/tree-digest.txt", "c" * 40 + "\n")
    manifest = {
        "$schema": "review-manifest.schema.json",
        "schema_version": "1.0.0",
        "specification_version": "0.9.0",
        "phase": "M6",
        "status": status,
        "baseline_sha": baseline,
        "head_sha": head,
        "branch": "product/sfskills-v2-local",
        "local_only": True,
        "clean_tree": True,
        "commits": [{"sha": head, "subject": "test"}],
        "tags": ["sfskills-v2-m6-rc"],
        "milestones": [{"id": "M6", "status": "completed" if status == "completed" else "blocked", "tag": "sfskills-v2-m6-rc", "notes": "test"}],
        "products": [{
            "product_id": "P01",
            "status": "release-candidate",
            "qualification": "host-qualified",
            "representative_run_paths": ["runs/P01/run-example"],
            "known_blockers": [],
        }],
        "tests": tests,
        "host_smoke": [{
            "host": "cursor",
            "version": "test",
            "status": "passed",
            "evidence_paths": ["host-smoke/cursor/discovery.md"],
            "reason_not_run": None,
        }],
        "artifacts": {
            "cursor_plugin": "builds/cursor-plugin.zip",
            "source_archive": "source/repository-head.tar.gz",
        },
        "integrity": {
            "git_bundle_verified": True,
            "checksums_verified": True,
            "offline_reconstruction_verified": True,
            "source_tree_digest_verified": True,
            "secret_scan_passed": True,
        },
        "unrun_checks": [],
        "known_limitations": [],
        "requirement_traceability_path": "traceability/requirements.csv",
        "deviations_path": "spec/deviations.md",
    }
    write_text(root / "MANIFEST.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    sums = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rel = path.relative_to(root).as_posix()
            sums.append(f"{sha256_file(path)}  {rel}")
    write_text(root / "SHA256SUMS.txt", "\n".join(sums) + "\n")


class SpecValidatorTests(unittest.TestCase):
    def test_actual_spec_package_is_consistent(self) -> None:
        self.assertEqual(PackageValidator(SPEC_ROOT).run(), [])


class CursorReturnValidatorTests(unittest.TestCase):
    def validate(self, root: Path, **kwargs):
        return ReturnValidator(root, SCHEMA, secret_scan=True, **kwargs).run()

    def test_completed_structural_and_release_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_minimal_review(root)
            self.assertEqual(self.validate(root), [])
            self.assertEqual(self.validate(root, release=True), [])

    def test_blocked_with_failed_test_is_structurally_reviewable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_minimal_review(root, status="blocked", test_exit=1)
            self.assertEqual(self.validate(root), [])
            codes = {issue.code for issue in self.validate(root, release=True)}
            self.assertIn("RELEASE_STATUS", codes)
            self.assertIn("REQUIRED_TEST_FAILURE", codes)

    def test_failed_test_cannot_claim_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_minimal_review(root, status="completed", test_exit=1)
            codes = {issue.code for issue in self.validate(root)}
            self.assertIn("FAILED_TEST_WITH_NONBLOCKED_STATUS", codes)

    def test_checksum_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_minimal_review(root)
            write_text(root / "REVIEW.md", "tampered\n")
            codes = {issue.code for issue in self.validate(root)}
            self.assertIn("CHECKSUM_MISMATCH", codes)

    def test_missing_test_log_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_minimal_review(root)
            (root / "tests/unit.stdout.txt").unlink()
            codes = {issue.code for issue in self.validate(root)}
            self.assertIn("MISSING_TEST_LOG", codes)


if __name__ == "__main__":
    unittest.main()
