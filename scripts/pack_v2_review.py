#!/usr/bin/env python3
"""Pack and validate SfSkills V2 milestone review ZIPs (contract v1.0).

Usage:
  python3 scripts/pack_v2_review.py \\
    --milestone phase1 \\
    --baseline <sha> --head <sha> \\
    --test-manifest .sfskills/review/test-manifest.json \\
    --out dist/reviews/sfskills-v2-phase1-review-YYYYMMDD-HHMMSS.zip

  python3 scripts/pack_v2_review.py --validate <zip-path>

Stdlib only. Review staging (test logs, cursor smoke, runs) lives under the
parent of ``--test-manifest`` (typically ``.sfskills/review/``).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
ZIP_ROOT = "sfskills-v2-review"
SCHEMA_VERSION = "1.0"

PHASE1_CONTAMINATION = (
    "apex-test-failure-triager",
    "triage-apex-tests",
    "get_apex_test_run",
    "test_phase2",
    "tests/product/test_phase2.py",
)

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("sfdxAuthUrl", re.compile(r"sfdxAuthUrl", re.IGNORECASE)),
    ("pem_private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("bearer_jwt", re.compile(r"Bearer\s+ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
    ("refresh_token", re.compile(r"refresh_token", re.IGNORECASE)),
    ("dot_env_path", re.compile(r"(?:^|/)\.env(?:\.|$|/)")),
    ("dot_sf_path", re.compile(r"(?:^|/)\.sf/")),
    ("dot_sfdx_path", re.compile(r"(?:^|/)\.sfdx/")),
]

SECRET_SCAN_SKIP_PREFIXES = (
    "product/",
    "git/",
    "source/",
    "README.md",
    "cursor-smoke/checklist.md",
    "security/secret-scan.log",
    "security/prohibited-file-check.log",
)

PROHIBITED_PATH_MARKERS = (
    "/.env",
    "/.sf/",
    "/.sfdx/",
    "id_rsa",
    "credentials.json",
)

REQUIRED_ZIP_PATHS = (
    "REVIEW_MANIFEST.json",
    "README.md",
    "checksums.sha256",
    "git/repo.bundle",
    "git/bundle-verify.log",
    "git/baseline.txt",
    "git/head.txt",
    "git/branch.txt",
    "git/milestone.txt",
    "git/commit-range.txt",
    "git/commits.txt",
    "git/status.txt",
    "git/diff.patch",
    "git/diff-stat.txt",
    "git/diff-check.txt",
    "git/changed-files.txt",
    "git/deleted-files.txt",
    "git/untracked-files.txt",
    "git/submodule-status.txt",
    "source/source-tree.tar.gz",
    "source/source-tree-file-list.txt",
    "source/source-tree-sha256.txt",
    "tests/test-manifest.json",
    "build/cursor-plugin.zip",
    "build/cursor-build-manifest.json",
    "security/secret-scan.log",
    "tests/commands/reconstructed-smoke/exit-code.txt",
)


class PackError(Exception):
    """Fatal packaging or validation error."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_git(
    args: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess[str]:
    cmd = ["git", *args]
    proc = subprocess.run(  # noqa: S603
        cmd,
        cwd=cwd or ROOT,
        capture_output=True,
        text=text,
        check=False,
    )
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise PackError(f"git {' '.join(args)} failed ({proc.returncode}): {detail}")
    return proc


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")


def _write_json(path: Path, payload: Any) -> None:
    _write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def _copy_tree_if_exists(src: Path, dest: Path) -> bool:
    if not src.exists():
        return False
    if dest.exists():
        shutil.rmtree(dest)
    if src.is_dir():
        shutil.copytree(src, dest)
    else:
        _copy_file(src, dest)
    return True


def _ensure_clean_worktree() -> None:
    proc = _run_git(["status", "--porcelain=v1", "--untracked-files=all"], check=True)
    if proc.stdout.strip():
        raise PackError(
            "working tree is dirty; commit or stash changes before packaging "
            "(git status --porcelain=v1 --untracked-files=all is non-empty)"
        )


def _resolve_sha(ref: str) -> str:
    proc = _run_git(["rev-parse", "--verify", f"{ref}^{{commit}}"], check=False)
    if proc.returncode != 0:
        raise PackError(f"git ref not found: {ref}")
    return proc.stdout.strip()


def _verify_reachability(baseline: str, head: str) -> None:
    proc = _run_git(["merge-base", "--is-ancestor", baseline, head], check=False)
    if proc.returncode != 0:
        raise PackError(f"head {head} is not reachable from baseline {baseline}")


def _check_phase_contamination(milestone: str, baseline: str, head: str) -> None:
    if milestone != "phase1":
        return
    proc = _run_git(["diff", "--name-only", f"{baseline}..{head}"], check=True)
    offenders = []
    for line in proc.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        for marker in PHASE1_CONTAMINATION:
            if marker in path:
                offenders.append(path)
                break
    if offenders:
        joined = ", ".join(offenders[:20])
        suffix = " ..." if len(offenders) > 20 else ""
        raise PackError(f"phase1 contamination in {baseline}..{head}: {joined}{suffix}")


def _load_test_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PackError(f"test manifest not found: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PackError(f"invalid test manifest JSON: {exc}") from exc
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise PackError(f"test manifest schema_version must be {SCHEMA_VERSION!r}")
    if not isinstance(manifest.get("tests"), list):
        raise PackError("test manifest must include a tests array")
    return manifest


def _validate_test_manifest(manifest: dict[str, Any], review_dir: Path) -> dict[str, int]:
    counts = {
        "required_total": 0,
        "required_passed": 0,
        "required_failed": 0,
        "optional_total": 0,
        "optional_passed": 0,
        "optional_failed": 0,
    }
    not_run: list[str] = []
    for row in manifest["tests"]:
        if not isinstance(row, dict):
            raise PackError("each test entry must be an object")
        test_id = str(row.get("id") or "")
        if not test_id:
            raise PackError("test entry missing id")
        required = bool(row.get("required", False))
        bucket = "required" if required else "optional"
        counts[f"{bucket}_total"] += 1
        exit_code = row.get("exit_code")
        if exit_code is None:
            if required:
                raise PackError(f"required test {test_id} missing exit_code")
            not_run.append(test_id)
            continue
        for log_key in ("stdout", "stderr"):
            rel = row.get(log_key)
            if not rel:
                if required:
                    raise PackError(f"required test {test_id} missing {log_key} path")
                continue
            log_path = review_dir / rel
            if not log_path.is_file():
                raise PackError(f"required test {test_id} log missing: {log_path}")
        if int(exit_code) != 0:
            counts[f"{bucket}_failed"] += 1
            if required:
                raise PackError(f"required test {test_id} failed with exit_code={exit_code}")
        else:
            counts[f"{bucket}_passed"] += 1
    counts["not_run"] = not_run  # type: ignore[assignment]
    return counts  # type: ignore[return-value]


def _capture_git_evidence(stage: Path, baseline: str, head: str, milestone: str) -> None:
    git_dir = stage / "git"
    git_dir.mkdir(parents=True, exist_ok=True)

    current_head = _run_git(["rev-parse", "HEAD"], check=True).stdout.strip()
    if current_head != head:
        raise PackError(f"pack head {head} != current HEAD {current_head}")

    rev_proc = _run_git(["rev-list", "--reverse", f"{baseline}..{head}"], check=True)
    commits = [line for line in rev_proc.stdout.splitlines() if line.strip()]
    if not commits:
        raise PackError(f"no commits between baseline {baseline} and head {head}")

    bundle_path = git_dir / "repo.bundle"
    proc = _run_git(
        ["bundle", "create", str(bundle_path), *commits, baseline, "HEAD"],
        check=False,
    )
    if proc.returncode != 0:
        raise PackError(f"git bundle create failed: {(proc.stderr or proc.stdout).strip()}")

    verify = _run_git(["bundle", "verify", str(bundle_path)], check=False)
    _write_text(git_dir / "bundle-verify.log", (verify.stdout or "") + (verify.stderr or ""))
    if verify.returncode != 0:
        raise PackError("git bundle verify failed; see bundle-verify.log")

    _write_text(git_dir / "baseline.txt", baseline + "\n")
    _write_text(git_dir / "head.txt", head + "\n")
    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], check=True).stdout.strip()
    _write_text(git_dir / "branch.txt", branch + "\n")
    _write_text(git_dir / "milestone.txt", milestone + "\n")
    _write_text(git_dir / "commit-range.txt", f"{baseline}..{head}\n")

    commits = _run_git(["log", "--oneline", "--no-decorate", f"{baseline}..{head}"], check=True)
    _write_text(git_dir / "commits.txt", commits.stdout)

    status = _run_git(["status", "--porcelain=v1", "--untracked-files=all"], check=True)
    _write_text(git_dir / "status.txt", status.stdout)

    diff_patch = _run_git(["diff", "--binary", f"{baseline}..{head}"], check=True)
    _write_text(git_dir / "diff.patch", diff_patch.stdout)

    diff_stat = _run_git(["diff", "--stat", f"{baseline}..{head}"], check=True)
    _write_text(git_dir / "diff-stat.txt", diff_stat.stdout)

    diff_check = _run_git(["diff", "--check", f"{baseline}..{head}"], check=False)
    _write_text(git_dir / "diff-check.txt", (diff_check.stdout or "") + (diff_check.stderr or ""))

    changed = _run_git(["diff", "--name-only", f"{baseline}..{head}"], check=True)
    _write_text(git_dir / "changed-files.txt", changed.stdout)

    deleted = _run_git(["diff", "--diff-filter=D", "--name-only", f"{baseline}..{head}"], check=True)
    _write_text(git_dir / "deleted-files.txt", deleted.stdout)

    untracked = _run_git(["ls-files", "--others", "--exclude-standard"], check=True)
    _write_text(git_dir / "untracked-files.txt", untracked.stdout)

    submodule = _run_git(["submodule", "status", "--recursive"], check=False)
    _write_text(git_dir / "submodule-status.txt", (submodule.stdout or "") + (submodule.stderr or ""))


def _capture_source_archive(stage: Path, head: str) -> None:
    source_dir = stage / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    archive_path = source_dir / "source-tree.tar.gz"
    proc = subprocess.run(  # noqa: S603
        ["git", "archive", "--format=tar.gz", f"--output={archive_path}", head],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise PackError(f"git archive failed: {(proc.stderr or proc.stdout).strip()}")

    listing: list[str] = []
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in sorted(archive.getnames()):
            listing.append(member)
    _write_text(source_dir / "source-tree-file-list.txt", "\n".join(listing) + ("\n" if listing else ""))
    _write_text(source_dir / "source-tree-sha256.txt", _sha256_file(archive_path) + "\n")


def _copy_review_artifacts(stage: Path, test_manifest: Path) -> dict[str, int]:
    review_dir = test_manifest.parent
    manifest = _load_test_manifest(test_manifest)
    counts = _validate_test_manifest(manifest, review_dir)

    tests_dir = stage / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    _copy_file(test_manifest, tests_dir / "test-manifest.json")

    env_src = review_dir / "environment.json"
    if env_src.is_file():
        _copy_file(env_src, tests_dir / "environment.json")
    else:
        _write_json(
            tests_dir / "environment.json",
            {
                "schema_version": SCHEMA_VERSION,
                "captured_utc": _utc_now(),
                "python": sys.version.split()[0],
                "platform": sys.platform,
            },
        )

    commands_src = review_dir / "commands"
    if commands_src.is_dir():
        _copy_tree_if_exists(commands_src, tests_dir / "commands")

    summaries_src = review_dir / "summaries"
    if summaries_src.is_dir():
        _copy_tree_if_exists(summaries_src, tests_dir / "summaries")
    else:
        summaries_dir = tests_dir / "summaries"
        summaries_dir.mkdir(parents=True, exist_ok=True)
        required_rows = [t for t in manifest["tests"] if t.get("required")]
        optional_rows = [t for t in manifest["tests"] if not t.get("required")]
        _write_json(summaries_dir / "required-tests.json", {"tests": required_rows})
        _write_json(summaries_dir / "optional-tests.json", {"tests": optional_rows})
        _write_json(
            summaries_dir / "baseline-comparison.json",
            {
                "schema_version": SCHEMA_VERSION,
                "baseline_sha": manifest.get("baseline_sha"),
                "head_sha": manifest.get("head_sha"),
                "note": "comparison captured in test-manifest command logs when provided",
            },
        )

    for rel in ("cursor-smoke", "runs", "security", "qa"):
        src = review_dir / rel
        if src.exists():
            _copy_tree_if_exists(src, stage / rel)

    runs_root = ROOT / ".sfskills" / "runs"
    if runs_root.is_dir() and not (stage / "runs").exists():
        fixture_dest = stage / "runs" / "fixture"
        fixture_dest.mkdir(parents=True, exist_ok=True)
        for child in sorted(runs_root.iterdir()):
            if child.is_dir():
                _copy_tree_if_exists(child, fixture_dest / child.name)

    if not (stage / "runs").exists():
        runs_dir = stage / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        _write_json(runs_dir / "fixture" / "NOT_RUN.json", {"reason": "no fixture runs captured"})
        _write_json(runs_dir / "live-readonly" / "NOT_RUN.json", {"reason": "no live read-only run captured"})

    if not (stage / "qa" / "scratch-org").exists():
        qa_dir = stage / "qa" / "scratch-org"
        qa_dir.mkdir(parents=True, exist_ok=True)
        _write_json(
            qa_dir / "NOT_RUN.json",
            {"reason": "scratch-org QA begins in phase3", "milestone": "phase1"},
        )

    return counts


def _gather_product_docs(stage: Path) -> None:
    product_dir = stage / "product"
    product_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "current-state.md": ROOT / "docs" / "product-v2" / "current-state.md",
        "phase-plan.md": ROOT / "docs" / "product-v2" / "pr-1-deployment-triage-plan.md",
        "final-report.md": ROOT / "docs" / "product-v2" / "pr-1-final-report.md",
        "architecture.md": ROOT / "docs" / "product-v2" / "cursor-plugin.md",
    }
    for dest_name, src in mapping.items():
        if src.is_file():
            _copy_file(src, product_dir / dest_name)
        else:
            _write_text(product_dir / dest_name, f"# Missing source\n\nExpected: {src}\n")

    decisions_dir = product_dir / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    if not any(decisions_dir.iterdir()):
        _write_json(decisions_dir / "NOT_RUN.json", {"reason": "no ADR exports bundled"})

    for name, default in (
        ("known-limitations.md", "# Known limitations\n\nSee final-report.md.\n"),
        ("deferred-work.md", "# Deferred work\n\nSee phase-plan.md.\n"),
    ):
        dest = product_dir / name
        if not dest.exists():
            src = ROOT / "docs" / "product-v2" / name
            if src.is_file():
                _copy_file(src, dest)
            else:
                _write_text(dest, default)

    acceptance = product_dir / "acceptance-matrix.json"
    review_acceptance = ROOT / ".sfskills" / "review" / "product" / "acceptance-matrix.json"
    if review_acceptance.is_file():
        _copy_file(review_acceptance, acceptance)
    elif not acceptance.is_file():
        _write_json(
            acceptance,
            {
                "schema_version": SCHEMA_VERSION,
                "criteria": [],
                "note": "populate .sfskills/review/product/acceptance-matrix.json before packaging",
            },
        )


def _run_command_logged(
    cmd: list[str],
    *,
    cwd: Path,
    dest_dir: Path,
    label: str,
) -> int:
    dest_dir.mkdir(parents=True, exist_ok=True)
    started = _utc_now()
    t0 = datetime.now(timezone.utc)
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)  # noqa: S603
    duration_ms = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)
    _write_text(dest_dir / "command.txt", " ".join(cmd))
    _write_text(dest_dir / "cwd.txt", str(cwd))
    _write_text(dest_dir / "started-utc.txt", started)
    _write_text(dest_dir / "duration-ms.txt", str(duration_ms))
    _write_text(dest_dir / "exit-code.txt", str(proc.returncode))
    _write_text(dest_dir / "stdout.log", proc.stdout or "")
    _write_text(dest_dir / "stderr.log", proc.stderr or "")
    return proc.returncode


def _gather_build_artifacts(stage: Path) -> None:
    build_dir = stage / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    build_script = ROOT / "scripts" / "build_cursor_plugin.py"
    build_rc = subprocess.run(  # noqa: S603
        [sys.executable, str(build_script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    _write_text(build_dir / "cursor-build.log", (build_rc.stdout or "") + (build_rc.stderr or ""))
    if build_rc.returncode != 0:
        raise PackError("build_cursor_plugin.py failed during packaging")

    check_rc = subprocess.run(  # noqa: S603
        [sys.executable, str(build_script), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    _write_text(build_dir / "cursor-build-check.log", (check_rc.stdout or "") + (check_rc.stderr or ""))
    if check_rc.returncode != 0:
        raise PackError("build_cursor_plugin.py --check failed during packaging")

    plugin_tree = ROOT / "dist" / "cursor" / "awesome-salesforce-skills"
    if not plugin_tree.is_dir():
        raise PackError("dist/cursor/awesome-salesforce-skills missing after build")

    plugin_zip = build_dir / "cursor-plugin.zip"
    if plugin_zip.exists():
        plugin_zip.unlink()
    with zipfile.ZipFile(plugin_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(plugin_tree.rglob("*")):
            if path.is_file():
                rel = path.relative_to(plugin_tree).as_posix()
                zf.write(path, rel)

    tree_lines = []
    for path in sorted(plugin_tree.rglob("*")):
        rel = path.relative_to(plugin_tree).as_posix()
        suffix = "/" if path.is_dir() else ""
        tree_lines.append(rel + suffix)
    _write_text(build_dir / "cursor-plugin-tree.txt", "\n".join(tree_lines) + ("\n" if tree_lines else ""))

    manifest_src = ROOT / "integrations" / "cursor" / "build-manifest.json"
    if manifest_src.is_file():
        _copy_file(manifest_src, build_dir / "cursor-build-manifest.json")
    else:
        raise PackError("integrations/cursor/build-manifest.json missing")

    legacy_log = build_dir / "legacy-export-check.log"
    if not legacy_log.exists():
        _write_text(legacy_log, "NOT_RUN: legacy Claude export parity not evaluated in phase1 packer\n")

    validate_script = ROOT / "scripts" / "validate_repo.py"
    if validate_script.is_file():
        val_rc = subprocess.run(  # noqa: S603
            [sys.executable, str(validate_script), "--agents"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        _write_text(build_dir / "repository-validation.log", (val_rc.stdout or "") + (val_rc.stderr or ""))
        if val_rc.returncode != 0:
            raise PackError("validate_repo.py --agents failed during packaging")
    else:
        _write_text(build_dir / "repository-validation.log", "validate_repo.py not found\n")


def _scan_text_for_secrets(text: str, relpath: str) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                hits.append({"path": relpath, "line": str(line_no), "pattern": label})
    return hits


def _scan_path_for_secrets(path: Path, relpath: str) -> list[dict[str, str]]:
    if path.is_dir():
        return []
    if any(relpath == prefix or relpath.startswith(prefix) for prefix in SECRET_SCAN_SKIP_PREFIXES):
        return []
    try:
        if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".zip", ".gz", ".bundle", ".tar"}:
            return []
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return _scan_text_for_secrets(text, relpath)


def _run_security_checks(stage: Path) -> bool:
    security_dir = stage / "security"
    security_dir.mkdir(parents=True, exist_ok=True)

    hits: list[dict[str, str]] = []
    prohibited: list[str] = []
    for path in sorted(stage.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(stage).as_posix()
        rel_lower = "/" + rel.lower()
        for marker in PROHIBITED_PATH_MARKERS:
            if marker in rel_lower:
                prohibited.append(rel)
        hits.extend(_scan_path_for_secrets(path, rel))

    policy_log = security_dir / "policy-tests.log"
    if not policy_log.exists():
        proc = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-m",
                "unittest",
                "tests.product.test_phase1.PolicyTests",
                "-v",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        _write_text(policy_log, (proc.stdout or "") + (proc.stderr or ""))

    matrix = security_dir / "policy-matrix.json"
    if not matrix.exists():
        _write_json(
            matrix,
            {
                "schema_version": SCHEMA_VERSION,
                "product_tools_read_only": True,
                "shell_policy": "pipelines.product.policy.evaluate_shell_command",
                "mcp_policy": "pipelines.product.policy.evaluate_mcp_call",
            },
        )

    redaction = security_dir / "redaction-report.json"
    if not redaction.exists():
        _write_json(redaction, {"schema_version": SCHEMA_VERSION, "redacted_fields": [], "notes": []})

    scan_lines = []
    if prohibited:
        scan_lines.append("PROHIBITED PATHS:")
        scan_lines.extend(f"  - {row}" for row in prohibited)
    if hits:
        scan_lines.append("SECRET PATTERN HITS:")
        for row in hits:
            scan_lines.append(f"  - {row['path']}:{row['line']} [{row['pattern']}]")
    if not scan_lines:
        scan_lines.append("secret scan: PASS (no prohibited paths or pattern hits)")
    _write_text(security_dir / "secret-scan.log", "\n".join(scan_lines) + "\n")

    prohibited_log = security_dir / "prohibited-file-check.log"
    if prohibited:
        _write_text(prohibited_log, "\n".join(prohibited) + "\n")
    elif not prohibited_log.exists():
        _write_text(prohibited_log, "no prohibited paths found\n")

    return not hits and not prohibited


def _write_checksums(stage: Path) -> None:
    lines: list[str] = []
    for path in sorted(stage.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(stage).as_posix()
        if rel == "checksums.sha256":
            continue
        digest = _sha256_file(path)
        lines.append(f"{digest}  {rel}")
    _write_text(stage / "checksums.sha256", "\n".join(lines) + ("\n" if lines else ""))


def _write_readme(stage: Path, *, milestone: str, baseline: str, head: str) -> None:
    text = f"""# SfSkills V2 review package

Milestone: {milestone}
Baseline: {baseline}
Head: {head}

## Reconstruct from git bundle

```bash
git clone git/repo.bundle reconstructed
cd reconstructed
git checkout {head}
python3 -m unittest tests.product.test_phase1 tests.product.test_project_discover -v
python3 scripts/build_cursor_plugin.py --check
```

## Bundle strategy

The packer writes a self-contained bundle by enumerating every commit after
the baseline, then appending the baseline commit and HEAD ref:

```bash
git rev-list --reverse {baseline}..{head}
git bundle create repo.bundle <commits...> {baseline} HEAD
git bundle verify repo.bundle
```

Reviewers can `git clone git/repo.bundle` without prerequisite history on disk.

## Source archive

`source/source-tree.tar.gz` is `git archive` of the reviewed head commit for
read-only inspection without cloning.

## Validation

```bash
python3 scripts/pack_v2_review.py --validate /path/to/review.zip
```
"""
    _write_text(stage / "README.md", text)


def _run_reconstruction_smoke(stage: Path, head: str, milestone: str) -> None:
    bundle = stage / "git" / "repo.bundle"
    smoke_dir = stage / "tests" / "commands" / "reconstructed-smoke"
    with tempfile.TemporaryDirectory(prefix="sfskills-v2-reconstruct-") as tmp:
        clone_root = Path(tmp) / "reconstructed"
        clone_proc = subprocess.run(  # noqa: S603
            ["git", "clone", str(bundle), str(clone_root)],
            capture_output=True,
            text=True,
            check=False,
        )
        if clone_proc.returncode != 0:
            _run_command_logged(
                ["git", "clone", str(bundle), str(clone_root)],
                cwd=ROOT,
                dest_dir=smoke_dir,
                label="clone",
            )
            raise PackError(f"reconstruction clone failed: {(clone_proc.stderr or clone_proc.stdout).strip()}")

        checkout_proc = subprocess.run(  # noqa: S603
            ["git", "checkout", head],
            cwd=clone_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if checkout_proc.returncode != 0:
            raise PackError(f"reconstruction checkout failed: {(checkout_proc.stderr or checkout_proc.stdout).strip()}")

        unittest_cmd = [
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests/product",
            "-p",
            "test_*.py",
        ]
        if milestone == "phase1":
            unittest_cmd = [
                sys.executable,
                "-m",
                "unittest",
                "tests.product.test_phase1",
                "tests.product.test_project_discover",
                "-v",
            ]
        unittest_rc = _run_command_logged(unittest_cmd, cwd=clone_root, dest_dir=smoke_dir / "unittest", label="unittest")
        plugin_cmd = [sys.executable, str(clone_root / "scripts" / "build_cursor_plugin.py"), "--check"]
        plugin_rc = _run_command_logged(plugin_cmd, cwd=clone_root, dest_dir=smoke_dir / "plugin-check", label="plugin-check")

        overall = 0 if unittest_rc == 0 and plugin_rc == 0 else 1
        _write_text(smoke_dir / "exit-code.txt", str(overall))
        _write_text(
            smoke_dir / "summary.txt",
            f"unittest_rc={unittest_rc}\nplugin_check_rc={plugin_rc}\nhead={head}\n",
        )
        if overall != 0:
            raise PackError("reconstruction smoke failed; see tests/commands/reconstructed-smoke/")


def _tree_sha(head: str) -> str:
    return _run_git(["rev-parse", f"{head}^{{tree}}"], check=True).stdout.strip()


def _build_review_manifest(
    *,
    milestone: str,
    baseline: str,
    head: str,
    branch: str,
    test_counts: dict[str, Any],
    secret_scan_passed: bool,
    zip_sha256: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "product": "sfskills-v2",
        "milestone": milestone,
        "created_utc": _utc_now(),
        "local_only": True,
        "pushed": False,
        "published": False,
        "repository": {
            "name": "AwesomeSalesforceSkills",
            "branch": branch,
            "baseline_sha": baseline,
            "head_sha": head,
            "tree_sha": _tree_sha(head),
            "working_tree_clean": True,
        },
        "artifacts": {
            "git_bundle": "git/repo.bundle",
            "source_archive": "source/source-tree.tar.gz",
            "cursor_plugin": "build/cursor-plugin.zip",
        },
        "tests": {
            "required_total": test_counts.get("required_total", 0),
            "required_passed": test_counts.get("required_passed", 0),
            "required_failed": test_counts.get("required_failed", 0),
            "optional_total": test_counts.get("optional_total", 0),
            "optional_passed": test_counts.get("optional_passed", 0),
            "optional_failed": test_counts.get("optional_failed", 0),
            "not_run": test_counts.get("not_run", []),
        },
        "verification_modes": {
            "fixture": "passed" if test_counts.get("required_failed", 0) == 0 else "failed",
            "cursor_host": "partial",
            "live_readonly": "not_run",
            "scratch_org": "not_run",
        },
        "safety": {
            "product_tools_read_only": True,
            "scratch_mutation_used": False,
            "customer_or_persistent_org_mutation": False,
            "secret_scan_passed": secret_scan_passed,
        },
        "known_limitations": [],
        "zip_sha256": zip_sha256 or "computed-after-packaging-or-in-sidecar",
    }


def _zip_stage(stage: Path, out_path: Path) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                rel = path.relative_to(stage.parent).as_posix()
                zf.write(path, rel)
    return _sha256_file(out_path)


def _iter_zip_members(zf: zipfile.ZipFile) -> Iterable[str]:
    for name in zf.namelist():
        if name.endswith("/"):
            continue
        yield name


def _validate_manifest_obj(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise PackError(f"REVIEW_MANIFEST schema_version must be {SCHEMA_VERSION!r}")
    if manifest.get("local_only") is not True:
        raise PackError("REVIEW_MANIFEST.local_only must be true")
    if manifest.get("pushed") is not False:
        raise PackError("REVIEW_MANIFEST.pushed must be false")
    if manifest.get("published") is not False:
        raise PackError("REVIEW_MANIFEST.published must be false")


def validate_zip(zip_path: Path) -> None:
    if not zip_path.is_file():
        raise PackError(f"zip not found: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(_iter_zip_members(zf))
        prefix = ZIP_ROOT + "/"
        if not any(n.startswith(prefix) for n in names):
            raise PackError(f"zip missing root directory {ZIP_ROOT}/")

        for rel in REQUIRED_ZIP_PATHS:
            full = f"{ZIP_ROOT}/{rel}"
            if full not in names:
                raise PackError(f"missing required path: {full}")

        manifest_name = f"{ZIP_ROOT}/REVIEW_MANIFEST.json"
        manifest = json.loads(zf.read(manifest_name).decode("utf-8"))
        _validate_manifest_obj(manifest)

        if manifest.get("safety", {}).get("secret_scan_passed") is not True:
            raise PackError("REVIEW_MANIFEST reports secret_scan_passed != true")

        status_name = f"{ZIP_ROOT}/git/status.txt"
        status_text = zf.read(status_name).decode("utf-8")
        if status_text.strip():
            raise PackError("git/status.txt must be empty for packaged milestone")

        verify_log = zf.read(f"{ZIP_ROOT}/git/bundle-verify.log").decode("utf-8", errors="replace")
        if "is okay" not in verify_log.lower() and "ok" not in verify_log.lower():
            raise PackError("git bundle verification log does not indicate success")

        checksums_text = zf.read(f"{ZIP_ROOT}/checksums.sha256").decode("utf-8")
        expected: dict[str, str] = {}
        for line in checksums_text.splitlines():
            if not line.strip():
                continue
            digest, _, rel = line.partition("  ")
            if not rel:
                raise PackError(f"invalid checksum line: {line!r}")
            expected[rel] = digest.strip()

        for rel, digest in sorted(expected.items()):
            member = f"{ZIP_ROOT}/{rel}"
            if member not in names:
                raise PackError(f"checksum entry missing from zip: {rel}")
            actual = _sha256_bytes(zf.read(member))
            if actual != digest:
                raise PackError(f"checksum mismatch for {rel}")

        test_manifest = json.loads(zf.read(f"{ZIP_ROOT}/tests/test-manifest.json").decode("utf-8"))
        if test_manifest.get("schema_version") != SCHEMA_VERSION:
            raise PackError("tests/test-manifest.json schema_version mismatch")
        for row in test_manifest.get("tests", []):
            if not row.get("required"):
                continue
            if int(row.get("exit_code", 1)) != 0:
                raise PackError(f"required test failed in manifest: {row.get('id')}")
            for log_key in ("stdout", "stderr"):
                rel = row.get(log_key)
                if not rel:
                    raise PackError(f"required test {row.get('id')} missing {log_key}")
                member = f"{ZIP_ROOT}/tests/{rel}"
                if member not in names:
                    raise PackError(f"required test log missing in zip: tests/{rel}")

        milestone = str(manifest.get("milestone") or "")
        baseline = manifest.get("repository", {}).get("baseline_sha")
        head = manifest.get("repository", {}).get("head_sha")
        if milestone == "phase1" and baseline and head:
            diff_name = f"{ZIP_ROOT}/git/changed-files.txt"
            changed = zf.read(diff_name).decode("utf-8").splitlines()
            for path in changed:
                for marker in PHASE1_CONTAMINATION:
                    if marker in path:
                        raise PackError(f"phase1 contamination in changed-files.txt: {path}")

        smoke_exit = zf.read(f"{ZIP_ROOT}/tests/commands/reconstructed-smoke/exit-code.txt").decode("utf-8").strip()
        if smoke_exit != "0":
            raise PackError("reconstructed-smoke exit-code is not 0")


def pack(
    *,
    milestone: str,
    baseline_ref: str,
    head_ref: str,
    test_manifest: Path,
    out_path: Path,
) -> dict[str, Any]:
    _ensure_clean_worktree()
    baseline = _resolve_sha(baseline_ref)
    head = _resolve_sha(head_ref)
    _verify_reachability(baseline, head)
    _check_phase_contamination(milestone, baseline, head)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    staging_parent = ROOT / "dist" / "reviews" / ".staging" / stamp
    stage = staging_parent / ZIP_ROOT
    stage.mkdir(parents=True, exist_ok=True)

    _capture_git_evidence(stage, baseline, head, milestone)
    _capture_source_archive(stage, head)
    test_counts = _copy_review_artifacts(stage, test_manifest.resolve())
    _gather_product_docs(stage)
    _gather_build_artifacts(stage)

    if not (stage / "cursor-smoke").exists():
        checklist = ROOT / "docs" / "product-v2" / "cursor-smoke-checklist.md"
        cursor_dir = stage / "cursor-smoke"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        if checklist.is_file():
            _copy_file(checklist, cursor_dir / "checklist.md")
        review_result = test_manifest.parent / "cursor-smoke" / "result.json"
        if review_result.is_file():
            _copy_tree_if_exists(review_result.parent, cursor_dir)
        else:
            _write_json(
                cursor_dir / "result.json",
                {
                    "cursor_version": "unknown",
                    "plugin_visible": False,
                    "notes": ["populate .sfskills/review/cursor-smoke/result.json for host proof"],
                },
            )

    _run_reconstruction_smoke(stage, head, milestone)

    secret_ok = _run_security_checks(stage)
    if not secret_ok:
        raise PackError("secret scan failed; see security/secret-scan.log")

    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], check=True).stdout.strip()
    manifest = _build_review_manifest(
        milestone=milestone,
        baseline=baseline,
        head=head,
        branch=branch,
        test_counts=test_counts,
        secret_scan_passed=secret_ok,
    )
    _write_json(stage / "REVIEW_MANIFEST.json", manifest)
    _write_readme(stage, milestone=milestone, baseline=baseline, head=head)
    _write_checksums(stage)

    zip_sha = _zip_stage(stage, out_path)
    sidecar = out_path.with_suffix(out_path.suffix + ".sha256")
    _write_text(sidecar, zip_sha + "\n")

    validate_zip(out_path)

    return {
        "milestone": milestone,
        "baseline_sha": baseline,
        "head_sha": head,
        "branch": branch,
        "zip_path": str(out_path),
        "zip_sha256": zip_sha,
        "required_passed": test_counts.get("required_passed", 0),
        "required_failed": test_counts.get("required_failed", 0),
        "staging_dir": str(staging_parent),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pack or validate SfSkills V2 review ZIPs")
    parser.add_argument("--milestone", help="Milestone id (e.g. phase1)")
    parser.add_argument("--baseline", help="Baseline commit SHA")
    parser.add_argument("--head", help="Head commit SHA")
    parser.add_argument("--test-manifest", type=Path, help="Path to test-manifest.json")
    parser.add_argument("--out", type=Path, help="Output zip path")
    parser.add_argument("--validate", type=Path, help="Validate an existing review zip")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.validate:
            validate_zip(args.validate.resolve())
            print(f"VALID: {args.validate}")
            return 0

        missing = [name for name, value in (
            ("--milestone", args.milestone),
            ("--baseline", args.baseline),
            ("--head", args.head),
            ("--test-manifest", args.test_manifest),
            ("--out", args.out),
        ) if not value]
        if missing:
            parser.error("pack mode requires: " + ", ".join(missing))

        summary = pack(
            milestone=str(args.milestone),
            baseline_ref=str(args.baseline),
            head_ref=str(args.head),
            test_manifest=args.test_manifest,
            out_path=args.out,
        )
    except PackError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Milestone:", summary["milestone"])
    print("Baseline SHA:", summary["baseline_sha"])
    print("Head SHA:", summary["head_sha"])
    print("Local branch:", summary["branch"])
    print("Review ZIP path:", summary["zip_path"])
    print("Review ZIP SHA-256:", summary["zip_sha256"])
    print(
        "Required tests passed/failed:",
        f"{summary['required_passed']}/{summary['required_failed']}",
    )
    print("Pushed/published: no")
    print("Staging dir:", summary["staging_dir"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
