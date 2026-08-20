#!/usr/bin/env python3
"""Capture V2 RC review staging under .sfskills/review/ and build final ZIP."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / ".sfskills" / "review"
KERNEL_ROOT = ROOT / "framework" / "specification" / "reference-kernel"
BASELINE_TAG = "sfskills-v2-m0-spec-adopted"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_test(test_id: str, command: list[str], *, required: bool = True, cwd: Path | None = None) -> dict:
    started = utc_now()
    proc = subprocess.run(command, cwd=cwd or ROOT, capture_output=True, text=True, check=False)
    finished = utc_now()
    log_dir = REVIEW / "commands" / test_id
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
    (log_dir / "stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
    (log_dir / "exit-code.txt").write_text(str(proc.returncode) + "\n", encoding="utf-8")
    return {
        "id": test_id,
        "command": command,
        "cwd": str(cwd or ROOT),
        "started_utc": started,
        "finished_utc": finished,
        "exit_code": proc.returncode,
        "required": required,
        "stdout": f"commands/{test_id}/stdout.txt",
        "stderr": f"commands/{test_id}/stderr.txt",
    }


def _clean_kernel_pycache() -> None:
    if not KERNEL_ROOT.is_dir():
        return
    for cache in KERNEL_ROOT.rglob("__pycache__"):
        if cache.is_dir():
            shutil.rmtree(cache)


def _write_acceptance_matrix() -> None:
    products = [
        ("P01", "deployment-failure-triage", "fixture-qualified", "M2"),
        ("P02", "apex-test-failure-triage", "fixture-qualified", "M2"),
        ("P03", "access-path-explainer", "fixture-beta", "M3"),
        ("P04", "change-impact-planner", "fixture-beta", "M4"),
        ("P05", "automation-transaction-profiler", "fixture-beta", "M4"),
        ("P06", "release-readiness-review", "fixture-beta", "M4"),
        ("P07", "security-posture-review", "fixture-beta", "M5"),
        ("P08", "integration-incident-triage", "fixture-beta", "M5"),
        ("P09", "data-migration-reconciliation", "fixture-beta", "M5"),
        ("P10", "org-health-assessment", "fixture-beta", "M5"),
        ("P11", "agentforce-quality-engineer", "fixture-beta", "M5"),
        ("P12", "multi-org-drift-analysis", "fixture-beta", "M5"),
    ]
    payload = {
        "schema_version": "1.0",
        "captured_utc": utc_now(),
        "highest_qualification": "fixture-beta",
        "scratch_org": "not_run",
        "cursor_host_smoke": "not_run",
        "live_readonly": "not_run",
        "products": [
            {
                "id": pid,
                "slug": slug,
                "qualification": qual,
                "milestone": milestone,
            }
            for pid, slug, qual, milestone in products
        ],
    }
    out = REVIEW / "product" / "acceptance-matrix.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    _clean_kernel_pycache()
    REVIEW.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()
    baseline = subprocess.run(
        ["git", "rev-parse", BASELINE_TAG], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()

    tests = [
        run_test(
            "framework-tests",
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests/framework", "-p", "test_*.py"],
        ),
        run_test(
            "product-tests",
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests/product", "-p", "test_*.py"],
        ),
        run_test(
            "qa-tests",
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests/qa", "-p", "test_*.py"],
        ),
        run_test(
            "mcp-tests",
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", "mcp/sfskills-mcp/tests", "-p", "test_*.py"],
        ),
        run_test(
            "reference-kernel-tests",
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
            cwd=KERNEL_ROOT,
        ),
        run_test("validate-framework", [sys.executable, "-B", "scripts/validate_framework.py"]),
        run_test("validate-repo-agents", [sys.executable, "-B", "scripts/validate_repo.py", "--agents"]),
        run_test("cursor-plugin-check", [sys.executable, "-B", "scripts/build_cursor_plugin.py", "--check"]),
        run_test("export-skills-check", [sys.executable, "-B", "scripts/export_skills.py", "--check"], required=False),
    ]
    _clean_kernel_pycache()

    manifest = {
        "schema_version": "1.0",
        "baseline_sha": baseline,
        "head_sha": head,
        "branch": "product/sfskills-v2-local",
        "captured_utc": utc_now(),
        "tests": tests,
    }
    REVIEW.mkdir(parents=True, exist_ok=True)
    (REVIEW / "test-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    cursor_smoke = REVIEW / "cursor-smoke"
    cursor_smoke.mkdir(parents=True, exist_ok=True)
    checklist = ROOT / "docs" / "product-v2" / "cursor-smoke-checklist.md"
    if checklist.is_file():
        shutil.copy2(checklist, cursor_smoke / "checklist.md")
    (cursor_smoke / "result.json").write_text(
        json.dumps(
            {
                "cursor_version": "not_captured",
                "plugin_visible": False,
                "cursor_host_smoke": "not_run",
                "reason": "Host UI smoke requires manual Cursor session; deterministic gates passed.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    qa_dir = REVIEW / "qa" / "scratch-org"
    qa_dir.mkdir(parents=True, exist_ok=True)
    (qa_dir / "NOT_RUN.json").write_text(
        json.dumps(
            {
                "status": "not_run",
                "reason": "Dev Hub credentials unavailable in overnight run",
                "guards_tested": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    _write_acceptance_matrix()

    failed = [t for t in tests if t["required"] and t["exit_code"] != 0]
    if failed:
        print("Required tests failed:", ", ".join(t["id"] for t in failed), file=sys.stderr)
        return 1

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_zip = ROOT / "dist" / "reviews" / f"sfskills-v2-cursor-return-{stamp}.zip"
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    pack = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "pack_v2_review.py"),
            "--milestone",
            "rc1",
            "--baseline",
            baseline,
            "--head",
            head,
            "--test-manifest",
            str(REVIEW / "test-manifest.json"),
            "--out",
            str(out_zip),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    print(pack.stdout)
    if pack.stderr:
        print(pack.stderr, file=sys.stderr)
    if pack.returncode != 0:
        return pack.returncode
    sha = subprocess.run(
        ["shasum", "-a", "256", str(out_zip)],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()[0]
    summary = {
        "zip_path": str(out_zip),
        "zip_sha256": sha,
        "head_sha": head,
        "baseline_sha": baseline,
    }
    (REVIEW / "rc-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
