#!/usr/bin/env python3
"""Run all package-level checks and optionally refresh generated artifacts."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(identifier: str, command: list[str], cwd: Path, env: dict[str, str] | None = None) -> dict:
    started = time.monotonic()
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, env=env)
    duration = time.monotonic() - started
    print(f"[{identifier}] exit={proc.returncode} duration={duration:.3f}s")
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="" if proc.stderr.endswith("\n") else "\n")
    return {"id": identifier, "command": command, "cwd": str(cwd), "exit_code": proc.returncode, "duration_seconds": round(duration, 3)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-generated", action="store_true")
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args()
    py = sys.executable
    generation_flag = [] if args.write_generated else ["--check"]
    steps = [
        ("requirements", [py, "-B", "scripts/build_requirement_catalog.py", *generation_flag], ROOT),
        ("catalogs", [py, "-B", "scripts/build_catalogs.py", *generation_flag], ROOT),
        ("machine-contracts", [py, "-B", "tools/enrich_machine_contracts.py", "--write" if args.write_generated else "--check"], ROOT),
        ("api-references", [py, "-B", "scripts/build_api_references.py", *( [] if args.write_generated else ["--check"] )], ROOT),
    ]
    if args.write_generated:
        steps.append(("manifest-write", [py, "-B", "scripts/build_framework_manifest.py"], ROOT))
    steps += [
        ("package-validation", [py, "-B", "scripts/validate_framework_package.py"], ROOT),
        ("strict-package-validation", [py, "-B", "tools/validate_spec_package.py", str(ROOT)], ROOT),
        ("root-tests", [py, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"], ROOT),
        ("validator-tests", [py, "-B", "-m", "unittest", "discover", "-s", "tools/tests", "-p", "test_*.py", "-v"], ROOT),
        ("reference-kernel-tests", [py, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"], ROOT / "reference-kernel"),
        ("project-inspector-tests", [py, "-B", "-m", "unittest", "discover", "-s", "tests/product", "-p", "test_*.py", "-v"], ROOT / "reference-components/project-inspector/repo-files"),
        ("python-compile", [py, "-m", "compileall", "-q", "scripts", "tools", "reference-kernel", "reference-components/project-inspector/repo-files"], ROOT),
    ]
    if not args.write_generated:
        steps.append(("manifest-check", [py, "-B", "scripts/build_framework_manifest.py", "--check"], ROOT))
    results = []
    with tempfile.TemporaryDirectory(prefix="sfaef-pycache-") as cache_dir:
        clean_env = dict(os.environ)
        clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
        clean_env["PYTHONPYCACHEPREFIX"] = cache_dir
        for step in steps:
            results.append(run(*step, env=clean_env))
    report = {"valid": all(item["exit_code"] == 0 for item in results), "steps": results}
    if args.json_report:
        args.json_report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
