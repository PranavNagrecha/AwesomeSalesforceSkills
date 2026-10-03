#!/usr/bin/env python3
"""Checker for the package-development-strategy skill.

Reads a Salesforce DX project's sfdx-project.json (and its CI scripts) and flags
package-strategy mistakes that the Salesforce DX Developer Guide and the
Second-Generation Managed Packaging Developer Guide (Summer '26) document:

  ERROR  sfdx-project.json is not valid JSON, or has no packageDirectories
  ERROR  a packaged directory has a versionNumber that is not MAJOR.MINOR.PATCH.(BUILD|NEXT)
  WARN   a packaged directory's versionNumber does not end in NEXT (a forgotten
         update reuses the previous number)
  WARN   a dependency uses LATEST (maps to the most recently created version,
         which may not be the promoted one; RELEASED maps to the promoted one)
  WARN   ancestorVersion / ancestorId is NONE (existing customers can't upgrade)
  WARN   namespace is not 1-15 alphanumeric characters
  WARN   a CI script both builds with --skip-validation and promotes (versions
         built with skip validation can't be promoted)

Stdlib only. Exit codes: 0 clean or warnings only, 1 on any ERROR (or on
warnings with --strict), 1 if the project directory is missing.

Usage:
    python3 check_package_development_strategy.py --project-dir path/to/project
    python3 check_package_development_strategy.py --project-dir . --strict
    python3 check_package_development_strategy.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+\.(\d+|NEXT)$")
NAMESPACE_RE = re.compile(r"^[A-Za-z0-9]{1,15}$")
CI_GLOBS = ("*.sh", "*.yml", "*.yaml")


def check_project(project_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    proj = project_dir / "sfdx-project.json"
    if not proj.exists():
        warns.append(f"{proj}: not found; nothing to check")
        return errors, warns
    try:
        data = json.loads(proj.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        errors.append(f"{proj}: invalid JSON ({exc})")
        return errors, warns

    dirs = data.get("packageDirectories")
    if not isinstance(dirs, list) or not dirs:
        errors.append(f"{proj}: packageDirectories is missing or empty")
        return errors, warns

    namespace = data.get("namespace", "")
    if namespace and not NAMESPACE_RE.match(namespace):
        warns.append(
            f"{proj}: namespace '{namespace}' is not 1-15 alphanumeric characters "
            "(2GP guide: 'A namespace is a 1-15 character alphanumeric identifier')"
        )

    for entry in dirs:
        if not isinstance(entry, dict):
            continue
        name = entry.get("package")
        if not name:
            continue  # plain source directory, not a package
        ver = entry.get("versionNumber")
        if ver is None:
            errors.append(f"{proj}: package '{name}' has no versionNumber")
        elif not VERSION_RE.match(str(ver)):
            errors.append(
                f"{proj}: package '{name}' versionNumber '{ver}' is not MAJOR.MINOR.PATCH.(BUILD|NEXT)"
            )
        elif not str(ver).endswith(".NEXT"):
            warns.append(
                f"{proj}: package '{name}' versionNumber '{ver}' does not use NEXT; "
                "a forgotten update creates a version with the same number as the previous one"
            )
        for key in ("ancestorVersion", "ancestorId"):
            if str(entry.get(key, "")).upper() == "NONE":
                warns.append(
                    f"{proj}: package '{name}' sets {key}=NONE; existing customers can't upgrade to that version"
                )
        for dep in entry.get("dependencies", []) or []:
            if isinstance(dep, dict) and str(dep.get("versionNumber", "")).upper().endswith("LATEST"):
                warns.append(
                    f"{proj}: package '{name}' depends on '{dep.get('package')}' at "
                    f"{dep.get('versionNumber')}; LATEST may resolve to an unpromoted build, use RELEASED for release candidates"
                )

    for pattern in CI_GLOBS:
        for script in list(project_dir.glob(pattern)) + list(project_dir.glob(f".github/workflows/{pattern}")) \
                + list(project_dir.glob(f"scripts/{pattern}")):
            try:
                text = script.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "--skip-validation" in text and "package version promote" in text:
                warns.append(
                    f"{script}: builds with --skip-validation and runs 'package version promote'; "
                    "versions created with skip validation can't be promoted"
                )
    return errors, warns


def _self_test() -> int:
    good = {
        "packageDirectories": [
            {"path": "force-app", "package": "Core", "versionNumber": "1.0.0.NEXT", "default": True},
            {"path": "ext", "package": "Ext", "versionNumber": "1.0.0.NEXT",
             "dependencies": [{"package": "Core", "versionNumber": "1.0.0.RELEASED"}]},
        ],
        "namespace": "acmecore",
        "sourceApiVersion": "67.0",
    }
    bad = {
        "packageDirectories": [
            {"path": "force-app", "package": "Core", "versionNumber": "1.0", "default": True},
            {"path": "ext", "package": "Ext", "versionNumber": "1.0.0.3", "ancestorVersion": "NONE",
             "dependencies": [{"package": "Core", "versionNumber": "1.0.0.LATEST"}]},
        ],
        "namespace": "exp-mgr",
    }
    cases = [("good", good, 0, 0), ("bad", bad, 1, 4)]
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for label, payload, want_err, min_warn in cases:
            d = Path(tmp) / label
            d.mkdir()
            (d / "sfdx-project.json").write_text(json.dumps(payload), encoding="utf-8")
            errs, warns = check_project(d)
            if len(errs) != want_err or len(warns) < min_warn:
                ok = False
                print(f"SELF-TEST FAIL {label}: errors={errs} warns={warns}")
        empty = Path(tmp) / "empty"
        empty.mkdir()
        errs, warns = check_project(empty)
        if errs or not warns:
            ok = False
            print(f"SELF-TEST FAIL empty: errors={errs} warns={warns}")
    print("SELF-TEST PASS" if ok else "SELF-TEST FAILED")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Check sfdx-project.json for package-strategy mistakes.")
    parser.add_argument("--project-dir", default=".", help="Salesforce DX project root (default: .)")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--self-test", action="store_true", help="Run built-in fixtures and exit")
    args = parser.parse_args()

    if args.self_test:
        return _self_test()

    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        print(f"ERROR: project directory not found: {project_dir}")
        sys.exit(1)

    errors, warns = check_project(project_dir)
    for w in warns:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if errors or (args.strict and warns):
        return 1
    if not warns:
        print("OK: no package-strategy issues found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
