#!/usr/bin/env python3
"""Capture M0 milestone evidence under .sfskills/v2-evidence/m0/."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / ".sfskills" / "v2-evidence" / "m0"
BASELINE_SHA = "774d666d1"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(command: list[str], cwd: Path | None = None) -> dict:
    started = utc_now()
    proc = subprocess.run(command, cwd=cwd or ROOT, capture_output=True, text=True, check=False)
    finished = utc_now()
    return {
        "command": command,
        "cwd": str(cwd or ROOT),
        "started_utc": started,
        "finished_utc": finished,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def write_gate(name: str, result: dict, classification: str) -> None:
    payload = {**result, "classification": classification}
    path = EVIDENCE / "gates" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    log = EVIDENCE / "gates" / f"{name}.log"
    log.write_text(
        "\n".join(
            [
                f"command: {' '.join(result['command'])}",
                f"cwd: {result['cwd']}",
                f"started_utc: {result['started_utc']}",
                f"finished_utc: {result['finished_utc']}",
                f"exit_code: {result['exit_code']}",
                f"classification: {classification}",
                "",
                "----- stdout -----",
                result.get("stdout") or "",
                "----- stderr -----",
                result.get("stderr") or "",
                "",
            ]
        ),
        encoding="utf-8",
    )


def sha256_dir(source: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(source.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(source).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(path.read_bytes())
    return digest.hexdigest()


def preserve_start_state() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "preserve").mkdir(exist_ok=True)

    meta = {
        "branch": "product/sfskills-v2-local",
        "baseline_sha": BASELINE_SHA,
        "captured_utc": utc_now(),
    }
    (EVIDENCE / "preserve" / "metadata.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    for name, cmd in [
        ("branch.txt", ["git", "branch", "--show-current"]),
        ("head.txt", ["git", "rev-parse", "HEAD"]),
        ("status-short.txt", ["git", "status", "--short"]),
        ("status-full.txt", ["git", "status"]),
        ("changed-files.txt", ["git", "diff", "--name-only", BASELINE_SHA]),
        ("diff-stat.txt", ["git", "diff", "--stat", BASELINE_SHA]),
        ("diff.patch", ["git", "diff", BASELINE_SHA]),
        ("staged-files.txt", ["git", "diff", "--cached", "--name-only"]),
    ]:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        out = EVIDENCE / "preserve" / name
        if name.endswith(".patch"):
            out.write_text(proc.stdout, encoding="utf-8")
        else:
            out.write_text(proc.stdout if proc.returncode == 0 else proc.stderr, encoding="utf-8")

    versions = {}
    for key, cmd in [
        ("python3", [sys.executable, "-V"]),
        ("git", ["git", "--version"]),
        ("sf", ["sf", "--version"]),
        ("cursor", ["cursor", "--version"]),
    ]:
        try:
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
            versions[key] = {
                "command": cmd,
                "exit_code": proc.returncode,
                "output": (proc.stdout or proc.stderr or "").strip(),
            }
        except FileNotFoundError:
            versions[key] = {"command": cmd, "exit_code": None, "output": "not available on PATH"}
    (EVIDENCE / "preserve" / "tool-versions.json").write_text(
        json.dumps(versions, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def export_drift_compare() -> None:
    out_dir = EVIDENCE / "export-drift"
    out_dir.mkdir(parents=True, exist_ok=True)
    worktree = ROOT.parent / "sfskills-export-drift-baseline-worktree"
    if worktree.exists():
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=ROOT, check=False)
    subprocess.check_call(
        ["git", "worktree", "add", "--detach", str(worktree), BASELINE_SHA],
        cwd=ROOT,
    )
    baseline = run([sys.executable, "scripts/export_skills.py", "--check"], cwd=worktree)
    current = run([sys.executable, "scripts/export_skills.py", "--check"], cwd=ROOT)
    write_gate("export-skills-check-baseline", baseline, "required")
    write_gate("export-skills-check-current", current, "required")
    same_message = (
        baseline["exit_code"] == current["exit_code"]
        and "aider" in baseline["stdout"]
        and "CONVENTIONS.md" in baseline["stdout"]
        and baseline["stdout"].split("✖ export drift", 1)[-1]
        == current["stdout"].split("✖ export drift", 1)[-1]
    )
    report = {
        "baseline_sha": BASELINE_SHA,
        "baseline_exit_code": baseline["exit_code"],
        "current_exit_code": current["exit_code"],
        "drift_message_unchanged": same_message,
        "verdict": "baseline_deviation_unchanged" if same_message else "drift_changed_or_worsened",
    }
    (out_dir / "comparison.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=ROOT, check=False)


def spec_checksum_report() -> None:
    source = Path.home() / "Downloads/SfSkills_Salesforce_AI_Engineering_Framework_Spec_v0.9.0"
    imported = ROOT / "framework" / "specification"
    report = {
        "source_path": str(source),
        "imported_path": str(imported),
        "source_tree_sha256": sha256_dir(source) if source.is_dir() else None,
        "imported_tree_sha256": sha256_dir(imported),
        "version": (imported / "VERSION").read_text(encoding="utf-8").strip() if (imported / "VERSION").is_file() else None,
        "imported_file_count": sum(1 for p in imported.rglob("*") if p.is_file() and "__pycache__" not in p.parts),
    }
    diffs: list[str] = []
    if source.is_dir():
        proc = subprocess.run(
            ["diff", "-qr", str(source), str(imported)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        diffs = [line for line in proc.stdout.splitlines() if line.strip()]
    report["diff_lines"] = diffs
    report["diff_count"] = len(diffs)
    (EVIDENCE / "spec-package-checksum.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run_all_gates() -> dict:
    gates = [
        ("validate-framework", [sys.executable, "scripts/validate_framework.py"], "required"),
        ("product-tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests/product", "-p", "test_*.py", "-v"], "required"),
        ("framework-tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests/framework", "-p", "test_*.py", "-v"], "required"),
        ("validate-repo-agents", [sys.executable, "scripts/validate_repo.py", "--agents"], "required"),
        ("build-plugin-check", [sys.executable, "scripts/build_plugin.py", "--check"], "required"),
        ("export-skills-check", [sys.executable, "scripts/export_skills.py", "--check"], "advisory"),
        ("migration-reconcile", [sys.executable, "scripts/validate_framework.py", "--skip-spec-checks", "--json"], "required"),
        ("spec-run-all-checks", [sys.executable, "-B", "scripts/run_all_checks.py"], "required"),
        ("pack-v2-review-negative", [sys.executable, "scripts/pack_v2_review.py", "--validate", str(ROOT / "dist/reviews/does-not-exist.zip")], "required"),
        (
            "python-compile-new",
            [
                sys.executable,
                "-m",
                "compileall",
                "-q",
                "pipelines/framework",
                "scripts/validate_framework.py",
                "scripts/refresh_migration_ledgers.py",
                "tests/framework",
            ],
            "required",
        ),
    ]
    spec_root = ROOT / "framework" / "specification"
    results = {}
    for name, cmd, classification in gates:
        cwd = spec_root if name == "spec-run-all-checks" else ROOT
        result = run(cmd, cwd=cwd)
        write_gate(name, result, classification)
        results[name] = result["exit_code"]
    failed_required = []
    for name, cmd, classification in gates:
        code = results[name]
        if classification != "required":
            continue
        if name == "pack-v2-review-negative":
            if code == 0:
                failed_required.append(name)
            continue
        if code != 0:
            failed_required.append(name)
    return results, failed_required


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preserve-only", action="store_true")
    parser.add_argument("--gates-only", action="store_true")
    parser.add_argument("--export-drift", action="store_true")
    parser.add_argument("--spec-checksum", action="store_true")
    args = parser.parse_args()
    if args.preserve_only or not any([args.gates_only, args.export_drift, args.spec_checksum]):
        preserve_start_state()
    if args.export_drift or not any([args.preserve_only, args.gates_only, args.spec_checksum]):
        export_drift_compare()
    if args.spec_checksum or not any([args.preserve_only, args.gates_only, args.export_drift]):
        spec_checksum_report()
    if args.gates_only or not any([args.preserve_only, args.export_drift, args.spec_checksum]):
        results, failed_required = run_all_gates()
        if failed_required:
            return 1
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
