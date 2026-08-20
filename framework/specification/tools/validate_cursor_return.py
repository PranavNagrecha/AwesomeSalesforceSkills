#!/usr/bin/env python3
"""Validate a Cursor-produced SfSkills V2 review directory or ZIP.

The validator has two levels:

- structural (default): a blocked package may contain failing required tests, but
  integrity, cleanliness, checksums, referenced evidence, and truthful status must pass;
- release (--release): requires a completed package with all required tests and
  release evidence passing.

It is offline except for invoking local Git during --deep verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover
    raise SystemExit("jsonschema is required: python3 -m pip install jsonschema") from exc

CORE_REQUIRED = {
    "REVIEW.md",
    "MANIFEST.json",
    "SHA256SUMS.txt",
    "spec/specification-version.txt",
    "spec/applicable-requirements.csv",
    "spec/deviations.md",
    "git/repository.bundle",
    "git/baseline.txt",
    "git/head.txt",
    "git/branch.txt",
    "git/commit-log.txt",
    "git/status.txt",
    "git/diff.patch",
    "git/diff-stat.txt",
    "git/tags.txt",
    "git/bundle-verify.txt",
    "git/offline-reconstruction.txt",
    "source/repository-head.tar.gz",
    "source/changed-files.txt",
    "source/tree-digest.txt",
    "tests/test-index.json",
    "tests/baseline-comparison.md",
    "builds/cursor-plugin.zip",
    "builds/cursor-plugin-tree.txt",
    "builds/cursor-plugin-manifest.json",
    "builds/generated-drift-checks.txt",
    "builds/install-dry-run.txt",
    "builds/install-host-path.txt",
    "builds/uninstall-dry-run.txt",
    "qa/scenario-index.json",
    "qa/benchmark-summary.json",
    "qa/benchmark-report.md",
    "qa/context-rot-report.md",
    "qa/scratch-org-report.md",
    "security/policy-matrix.md",
    "security/shell-bypass-results.json",
    "security/mcp-bypass-results.json",
    "security/prompt-injection-results.json",
    "security/target-identity-tests.json",
    "security/secret-scan.txt",
    "security/redaction-report.md",
    "security/dependency-report.txt",
    "traceability/requirements.csv",
    "traceability/acceptance-matrix.md",
    "traceability/product-status.json",
    "traceability/known-limitations.md",
    "integrity/review-package-validator.txt",
    "integrity/checksum-verification.txt",
    "integrity/archive-list.txt",
}

HIGH_RISK_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "sfdx_auth_url": re.compile(r"force://[^\s'\"]{20,}"),
    "salesforce_session": re.compile(r"\b00D[A-Za-z0-9]{12,18}![A-Za-z0-9._-]{20,}\b"),
    "generic_secret_assignment": re.compile(
        r"(?i)\b(?:client_secret|refresh_token|access_token)\b\s*[:=]\s*['\"]?[A-Za-z0-9._~+/-]{24,}"
    ),
}
TEXT_SUFFIXES = {".txt", ".md", ".json", ".yaml", ".yml", ".csv", ".log", ".xml", ".py", ".js", ".ts", ".sh"}


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    message: str

    def render(self) -> str:
        return f"{self.code}: {self.path}: {self.message}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_sums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
            raise ValueError(f"line {lineno}: expected '<sha256>  <relative-path>'")
        rel = parts[1].lstrip("* ")
        if rel in result:
            raise ValueError(f"line {lineno}: duplicate checksum path {rel!r}")
        result[rel] = parts[0].lower()
    return result


def iter_string_paths(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_string_paths(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_string_paths(item)


def safe_member_name(name: str) -> bool:
    p = PurePosixPath(name)
    return not p.is_absolute() and ".." not in p.parts and not name.startswith(("/", "\\"))


def locate_review_root(extracted: Path) -> Path:
    entries = [p for p in extracted.iterdir() if p.name not in {"__MACOSX", ".DS_Store"}]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return extracted


class ReturnValidator:
    def __init__(self, root: Path, schema_path: Path, *, release: bool = False, deep: bool = False, secret_scan: bool = True) -> None:
        self.root = root.resolve()
        self.schema_path = schema_path.resolve()
        self.release = release
        self.deep = deep
        self.secret_scan = secret_scan
        self.issues: list[Issue] = []
        self.manifest: dict[str, Any] = {}

    def error(self, code: str, path: Path | str, message: str) -> None:
        if isinstance(path, Path):
            try:
                path = str(path.relative_to(self.root))
            except ValueError:
                path = str(path)
        self.issues.append(Issue(code, str(path), message))

    def exists(self, rel: str) -> bool:
        return (self.root / rel).is_file()

    def require_core_tree(self) -> None:
        for rel in sorted(CORE_REQUIRED):
            if not self.exists(rel):
                self.error("MISSING_REQUIRED_FILE", rel, "required review artifact is absent")
        changed_dir = self.root / "source/changed-files"
        if not changed_dir.is_dir():
            self.error("MISSING_REQUIRED_DIR", "source/changed-files", "exact changed-file directory is absent")
        host_dir = self.root / "host-smoke/cursor"
        if not host_dir.is_dir():
            self.error("MISSING_REQUIRED_DIR", "host-smoke/cursor", "actual Cursor smoke evidence directory is absent")
        runs_dir = self.root / "runs"
        if not runs_dir.is_dir():
            self.error("MISSING_REQUIRED_DIR", "runs", "representative product run directory is absent")

    def load_manifest(self) -> None:
        path = self.root / "MANIFEST.json"
        if not path.is_file():
            return
        try:
            self.manifest = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            self.error("INVALID_MANIFEST_JSON", path, str(exc))
            return
        try:
            schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            for err in sorted(validator.iter_errors(self.manifest), key=lambda e: list(e.path)):
                location = ".".join(str(x) for x in err.path) or "<root>"
                self.error("MANIFEST_SCHEMA", path, f"{location}: {err.message}")
        except Exception as exc:  # noqa: BLE001
            self.error("MANIFEST_SCHEMA_ERROR", self.schema_path, str(exc))

    def validate_manifest_truth(self) -> None:
        if not self.manifest:
            return
        status = self.manifest.get("status")
        if self.manifest.get("local_only") is not True:
            self.error("REMOTE_ACTIVITY_NOT_DENIED", "MANIFEST.json", "local_only must be true")
        if self.manifest.get("clean_tree") is not True:
            self.error("DIRTY_TREE", "MANIFEST.json", "reviewed head must be represented by a clean local tree")
        integrity = self.manifest.get("integrity", {})
        for key in (
            "git_bundle_verified",
            "checksums_verified",
            "offline_reconstruction_verified",
            "source_tree_digest_verified",
            "secret_scan_passed",
        ):
            if integrity.get(key) is not True:
                self.error("INTEGRITY_NOT_PROVEN", "MANIFEST.json", key)
        if self.release and status != "completed":
            self.error("RELEASE_STATUS", "MANIFEST.json", f"release validation requires completed, got {status!r}")

        required_failures = [t for t in self.manifest.get("tests", []) if t.get("required", True) and t.get("exit_code") != 0]
        if required_failures and status not in {"blocked", "failed"}:
            self.error("FAILED_TEST_WITH_NONBLOCKED_STATUS", "MANIFEST.json", ", ".join(str(t.get("id")) for t in required_failures))
        if self.release and required_failures:
            self.error("REQUIRED_TEST_FAILURE", "MANIFEST.json", ", ".join(str(t.get("id")) for t in required_failures))

        release_blockers = [x for x in self.manifest.get("unrun_checks", []) if x.get("impact") == "blocks-release"]
        if self.release and release_blockers:
            self.error("UNRUN_RELEASE_BLOCKER", "MANIFEST.json", ", ".join(str(x.get("id")) for x in release_blockers))

        # Identity files must agree with the manifest.
        for field, rel in (("baseline_sha", "git/baseline.txt"), ("head_sha", "git/head.txt"), ("branch", "git/branch.txt")):
            path = self.root / rel
            if path.is_file() and path.read_text(encoding="utf-8").strip() != str(self.manifest.get(field, "")).strip():
                self.error("IDENTITY_MISMATCH", rel, f"does not match MANIFEST.json {field}")

        # Every declared test must have exact logs.
        test_ids: list[str] = []
        for test in self.manifest.get("tests", []):
            test_id = str(test.get("id", ""))
            if test_id in test_ids:
                self.error("DUPLICATE_TEST_ID", "MANIFEST.json", test_id)
            test_ids.append(test_id)
            for key in ("stdout_path", "stderr_path"):
                rel = test.get(key)
                if not isinstance(rel, str) or not (self.root / rel).is_file():
                    self.error("MISSING_TEST_LOG", "MANIFEST.json", f"{test_id}: {key}={rel!r}")

        # Host and run paths must exist.
        for host in self.manifest.get("host_smoke", []):
            for rel in host.get("evidence_paths", []):
                if not (self.root / rel).exists():
                    self.error("MISSING_HOST_EVIDENCE", "MANIFEST.json", f"{host.get('host')}: {rel}")
            if self.release and host.get("host") == "cursor" and host.get("status") != "passed":
                self.error("CURSOR_HOST_NOT_PROVEN", "MANIFEST.json", str(host.get("status")))
        for product in self.manifest.get("products", []):
            for rel in product.get("representative_run_paths", []):
                if not (self.root / rel).exists():
                    self.error("MISSING_PRODUCT_RUN", "MANIFEST.json", f"{product.get('product_id')}: {rel}")
            if self.release and product.get("status") == "stable" and product.get("qualification") not in {"host-qualified", "read-only-org-qualified", "scratch-qualified"}:
                self.error("UNQUALIFIED_STABLE_PRODUCT", "MANIFEST.json", str(product.get("product_id")))

        for rel in (self.manifest.get("requirement_traceability_path"), self.manifest.get("deviations_path")):
            if isinstance(rel, str) and not (self.root / rel).is_file():
                self.error("MISSING_MANIFEST_PATH", "MANIFEST.json", rel)

        # Generic artifact references are enforced when they look relative.
        for rel in iter_string_paths(self.manifest.get("artifacts", {})):
            if rel.startswith(("http://", "https://", "/")) or "${" in rel:
                continue
            candidate = self.root / rel
            if not candidate.exists():
                self.error("MISSING_DECLARED_ARTIFACT", "MANIFEST.json", rel)

    def validate_test_index(self) -> None:
        path = self.root / "tests/test-index.json"
        if not path.is_file() or not self.manifest:
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            self.error("INVALID_TEST_INDEX", path, str(exc))
            return
        records = data.get("tests", []) if isinstance(data, dict) else data
        if not isinstance(records, list):
            self.error("INVALID_TEST_INDEX", path, "expected array or object with tests array")
            return
        manifest_ids = {str(x.get("id")) for x in self.manifest.get("tests", [])}
        index_ids = {str(x.get("id")) for x in records if isinstance(x, dict)}
        if manifest_ids != index_ids:
            self.error("TEST_INDEX_DRIFT", path, f"manifest-only={sorted(manifest_ids-index_ids)}; index-only={sorted(index_ids-manifest_ids)}")

    def validate_checksums(self) -> None:
        sums_path = self.root / "SHA256SUMS.txt"
        if not sums_path.is_file():
            return
        try:
            sums = parse_sums(sums_path)
        except Exception as exc:  # noqa: BLE001
            self.error("INVALID_CHECKSUM_FILE", sums_path, str(exc))
            return
        for rel, expected in sums.items():
            path = self.root / rel
            try:
                path.resolve().relative_to(self.root)
            except ValueError:
                self.error("CHECKSUM_PATH_ESCAPE", sums_path, rel)
                continue
            if not path.is_file():
                self.error("CHECKSUM_TARGET_MISSING", sums_path, rel)
            elif sha256_file(path) != expected:
                self.error("CHECKSUM_MISMATCH", path, f"expected {expected}")

        excluded = {"SHA256SUMS.txt"}
        actual = {
            str(path.relative_to(self.root)).replace(os.sep, "/")
            for path in self.root.rglob("*")
            if path.is_file() and str(path.relative_to(self.root)).replace(os.sep, "/") not in excluded
        }
        missing_coverage = sorted(actual - set(sums))
        extra = sorted(set(sums) - actual)
        if missing_coverage:
            self.error("CHECKSUM_COVERAGE", sums_path, f"unlisted files: {missing_coverage[:20]}" + (" ..." if len(missing_coverage) > 20 else ""))
        if extra:
            self.error("CHECKSUM_EXTRA", sums_path, str(extra))

    def validate_archive_shapes(self) -> None:
        source_archive = self.root / "source/repository-head.tar.gz"
        if source_archive.is_file():
            try:
                with tarfile.open(source_archive, "r:gz") as archive:
                    members = archive.getmembers()
                    if not members:
                        self.error("EMPTY_SOURCE_ARCHIVE", source_archive, "archive has no members")
                    for member in members:
                        if not safe_member_name(member.name):
                            self.error("UNSAFE_SOURCE_ARCHIVE_PATH", source_archive, member.name)
                        if member.issym() or member.islnk():
                            link = PurePosixPath(member.linkname)
                            if link.is_absolute() or ".." in link.parts:
                                self.error("UNSAFE_SOURCE_ARCHIVE_LINK", source_archive, f"{member.name} -> {member.linkname}")
            except Exception as exc:  # noqa: BLE001
                self.error("INVALID_SOURCE_ARCHIVE", source_archive, str(exc))
        plugin = self.root / "builds/cursor-plugin.zip"
        if plugin.is_file():
            try:
                with zipfile.ZipFile(plugin) as archive:
                    files = [n for n in archive.namelist() if not n.endswith("/")]
                    if not files:
                        self.error("EMPTY_CURSOR_PLUGIN", plugin, "plugin archive has no files")
                    for name in files:
                        if not safe_member_name(name):
                            self.error("UNSAFE_CURSOR_PLUGIN_PATH", plugin, name)
            except Exception as exc:  # noqa: BLE001
                self.error("INVALID_CURSOR_PLUGIN", plugin, str(exc))

    def validate_secret_scan(self) -> None:
        if not self.secret_scan:
            return
        for path in self.root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            rel = str(path.relative_to(self.root)).replace(os.sep, "/")
            # Source code may contain detection regex examples. Skip the returned validator itself.
            if rel.endswith("validate_cursor_return.py"):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for label, pattern in HIGH_RISK_PATTERNS.items():
                if pattern.search(text):
                    self.error("POTENTIAL_SECRET", path, label)

    def deep_git_verify(self) -> None:
        if not self.deep:
            return
        if shutil.which("git") is None:
            self.error("GIT_UNAVAILABLE", "git/repository.bundle", "--deep requested but git is unavailable")
            return
        bundle = self.root / "git/repository.bundle"
        if not bundle.is_file():
            return
        head = str(self.manifest.get("head_sha", ""))
        baseline = str(self.manifest.get("baseline_sha", ""))
        with tempfile.TemporaryDirectory(prefix="sfaef-review-git-") as tmp:
            bare = Path(tmp) / "verify.git"
            subprocess.run(["git", "init", "--bare", str(bare)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            proc = subprocess.run(["git", "-C", str(bare), "bundle", "verify", str(bundle)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                self.error("GIT_BUNDLE_VERIFY", bundle, proc.stderr.strip() or proc.stdout.strip())
                return
            proc = subprocess.run(["git", "-C", str(bare), "fetch", str(bundle), "refs/*:refs/*"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                # Not every bundle uses refs/*; fetch all advertised heads as fallback.
                proc = subprocess.run(["git", "-C", str(bare), "fetch", str(bundle), "HEAD:refs/heads/review-head"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                self.error("GIT_BUNDLE_FETCH", bundle, proc.stderr.strip() or proc.stdout.strip())
                return
            for label, sha in (("head", head), ("baseline", baseline)):
                proc = subprocess.run(["git", "-C", str(bare), "cat-file", "-e", f"{sha}^{{commit}}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc.returncode != 0:
                    self.error("GIT_COMMIT_MISSING", bundle, f"{label} {sha}")
            if head:
                proc = subprocess.run(["git", "-C", str(bare), "rev-parse", f"{head}^{{tree}}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc.returncode == 0:
                    expected_text = (self.root / "source/tree-digest.txt").read_text(encoding="utf-8") if (self.root / "source/tree-digest.txt").is_file() else ""
                    tree_sha = proc.stdout.strip()
                    if tree_sha not in expected_text:
                        self.error("TREE_DIGEST_MISMATCH", "source/tree-digest.txt", f"Git tree {tree_sha} not recorded")

    def run(self) -> list[Issue]:
        self.require_core_tree()
        self.load_manifest()
        self.validate_manifest_truth()
        self.validate_test_index()
        self.validate_checksums()
        self.validate_archive_shapes()
        self.validate_secret_scan()
        self.deep_git_verify()
        return sorted(self.issues, key=lambda issue: (issue.code, issue.path, issue.message))


def extract_zip_safely(path: Path, destination: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not safe_member_name(info.filename):
                raise ValueError(f"unsafe ZIP member: {info.filename}")
            # Unix symlink file type in external attributes.
            if ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError(f"symlink ZIP member is not allowed: {info.filename}")
        archive.extractall(destination)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", help="review directory or .zip")
    parser.add_argument(
        "--schema",
        default=str(Path(__file__).resolve().parents[1] / "schemas/review-manifest.schema.json"),
        help="review-manifest schema path",
    )
    parser.add_argument("--release", action="store_true", help="enforce completed release-candidate gates")
    parser.add_argument("--deep", action="store_true", help="invoke local Git to verify the bundle and tree")
    parser.add_argument("--no-secret-scan", action="store_true", help="skip built-in high-risk secret-pattern scan")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(list(argv) if argv is not None else None)

    artifact = Path(args.artifact).resolve()
    if not artifact.exists():
        print(f"artifact does not exist: {artifact}", file=sys.stderr)
        return 2

    temp: tempfile.TemporaryDirectory[str] | None = None
    try:
        if artifact.is_file():
            temp = tempfile.TemporaryDirectory(prefix="sfaef-review-zip-")
            extracted = Path(temp.name)
            extract_zip_safely(artifact, extracted)
            root = locate_review_root(extracted)
        else:
            root = artifact
        validator = ReturnValidator(
            root,
            Path(args.schema),
            release=args.release,
            deep=args.deep,
            secret_scan=not args.no_secret_scan,
        )
        issues = validator.run()
        result = {
            "artifact": str(artifact),
            "review_root": str(root),
            "mode": "release" if args.release else "structural",
            "status": "pass" if not issues else "fail",
            "issue_count": len(issues),
            "issues": [issue.__dict__ for issue in issues],
        }
        if args.as_json:
            print(json.dumps(result, indent=2, sort_keys=True))
        elif issues:
            print(f"FAIL: {len(issues)} issue(s)")
            for issue in issues:
                print(issue.render())
        else:
            print(f"PASS: Cursor return package ({result['mode']})")
        return 0 if not issues else 1
    except (zipfile.BadZipFile, ValueError, OSError) as exc:
        if args.as_json:
            print(json.dumps({"artifact": str(artifact), "status": "fail", "issue_count": 1, "issues": [{"code": "ARCHIVE_ERROR", "path": str(artifact), "message": str(exc)}]}, indent=2))
        else:
            print(f"FAIL: ARCHIVE_ERROR: {exc}")
        return 1
    finally:
        if temp is not None:
            temp.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
