#!/usr/bin/env python3
"""Offline verifier for Cursor milestone return ZIPs required by SFAEF."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "REVIEW.md", "MANIFEST.json", "SHA256SUMS.txt",
    "spec/specification-version.txt", "spec/applicable-requirements.csv", "spec/deviations.md",
    "git/repository.bundle", "git/baseline.txt", "git/head.txt", "git/branch.txt", "git/commit-log.txt",
    "git/status.txt", "git/diff.patch", "git/diff-stat.txt", "git/tags.txt", "git/bundle-verify.txt", "git/offline-reconstruction.txt",
    "source/repository-head.tar.gz", "source/changed-files.txt", "source/tree-digest.txt",
    "tests/test-index.json", "tests/baseline-comparison.md",
    "traceability/requirements.csv", "traceability/acceptance-matrix.md", "traceability/product-status.json", "traceability/known-limitations.md",
    "security/policy-matrix.md", "security/secret-scan.txt", "security/redaction-report.md",
    "integrity/review-package-validator.txt", "integrity/checksum-verification.txt", "integrity/archive-list.txt",
]
SECRET_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"(?i)(?:access[_-]?token|refresh[_-]?token|client[_-]?secret|session[_-]?id)\s*[:=]\s*['\"]?[A-Za-z0-9._-]{16,}"),
]


def safe_extract(zf: zipfile.ZipFile, target: Path) -> str:
    names = [name for name in zf.namelist() if name and not name.endswith("/")]
    roots = {Path(name).parts[0] for name in names if Path(name).parts}
    if len(roots) != 1:
        raise ValueError(f"expected one top-level directory, found {sorted(roots)}")
    root_name = next(iter(roots))
    for member in zf.infolist():
        destination = (target / member.filename).resolve()
        try:
            destination.relative_to(target.resolve())
        except ValueError as exc:
            raise ValueError(f"archive path escapes target: {member.filename}") from exc
    zf.extractall(target)
    return root_name


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path: Path) -> dict:
    issues: list[dict[str, str]] = []
    if not path.exists() or not zipfile.is_zipfile(path):
        return {"valid": False, "issues": [{"code": "not_zip", "message": str(path)}]}
    with tempfile.TemporaryDirectory(prefix="sfaef-review-") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(path) as zf:
            try:
                top = safe_extract(zf, tmp_path)
            except ValueError as exc:
                return {"valid": False, "issues": [{"code": "archive_structure", "message": str(exc)}]}
        root = tmp_path / top
        present = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
        for rel in REQUIRED:
            if rel not in present:
                issues.append({"code": "required_missing", "message": rel})
        manifest_path = root / "MANIFEST.json"
        manifest = None
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception as exc:
                issues.append({"code": "manifest_parse", "message": str(exc)})
        if manifest and Draft202012Validator is not None:
            schema = json.loads((ROOT / "schemas" / "review-manifest.schema.json").read_text(encoding="utf-8"))
            for error in Draft202012Validator(schema).iter_errors(manifest):
                issues.append({"code": "manifest_schema", "message": f"/{'/'.join(map(str,error.path))}: {error.message}"})
        if manifest:
            if manifest.get("local_only") is not True:
                issues.append({"code": "not_local_only", "message": "local_only must be true"})
            if manifest.get("clean_tree") is not True:
                issues.append({"code": "dirty_tree", "message": "clean_tree must be true for a completion package"})
            for test in manifest.get("tests", []):
                if test.get("required") and test.get("exit_code") != 0:
                    issues.append({"code": "required_test_failed", "message": str(test.get("id"))})
                for key in ("stdout_path", "stderr_path"):
                    rel = test.get(key)
                    if rel and rel not in present:
                        issues.append({"code": "test_log_missing", "message": f"{test.get('id')}:{rel}"})
        sums_path = root / "SHA256SUMS.txt"
        if sums_path.exists():
            for line in sums_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                parts = line.split(None, 1)
                if len(parts) != 2:
                    issues.append({"code": "checksum_format", "message": line})
                    continue
                expected, rel = parts[0], parts[1].lstrip(" *")
                file_path = root / rel
                if not file_path.exists():
                    issues.append({"code": "checksum_file_missing", "message": rel})
                elif sha256(file_path) != expected:
                    issues.append({"code": "checksum_mismatch", "message": rel})
        for file_path in root.rglob("*"):
            if not file_path.is_file() or file_path.stat().st_size > 20 * 1024 * 1024:
                continue
            try:
                data = file_path.read_bytes()
            except OSError:
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(data):
                    issues.append({"code": "secret_pattern", "message": file_path.relative_to(root).as_posix()})
                    break
        return {
            "valid": not issues,
            "zip": str(path),
            "sha256": sha256(path),
            "file_count": len(present),
            "issues": issues,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args()
    result = verify(args.zip_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
