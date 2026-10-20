#!/usr/bin/env python3
"""Checker script for Salesforce DX Project Structure skill.

Validates sfdx-project.json against the Salesforce DX Developer Guide (sfdx_dev 264):
- ERROR: invalid JSON, missing/empty packageDirectories (required, L2352), an entry with no path,
  a path that is not a directory, several entries with no default or more than one default
  (L2363-2364, L14795-14798), a malformed versionNumber (MAJOR.MINOR.PATCH.BUILD, NEXT or a number
  in the build slot, L14867-14873), credential-like content.
- REVIEW: duplicate paths (handling undocumented), missing/odd sourceApiVersion (optional, L2428),
  keys outside the documented set, scratch-org keys, .gitignore without .sfdx/.sf.

A single packageDirectories entry needs no "default" (L2363-2364) and a concrete build number
(1.2.1.8) is valid (L14868), so neither is flagged.

Severity contract: ERROR exits 1 always. REVIEW findings exit 0 unless --strict. An empty directory
is one WARN, exit 0. A missing path is an ERROR, exit 1.

Uses stdlib only. Usage:
    python3 check_salesforce_dx_project_structure.py --project-dir path/to/project [--strict]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Documented keys: sfdx_dev 264 L2322-2463. signupTargetLoginUrl is accepted although neither corpus lists it.
KNOWN_KEYS = {
    "name", "namespace", "oauthLocalPort", "packageAliases", "packageDirectories", "plugins",
    "pushPackageDirectoriesSequentially", "replacements", "sfdcLoginUrl", "sourceApiVersion",
    "sourceBehaviorOptions", "signupTargetLoginUrl",
}
SCRATCH_KEYS = {"edition", "features", "orgName", "settings", "orgPreferences"}
OWN_VERSION = re.compile(r"^\d+\.\d+\.\d+\.(\d+|NEXT)$")
DEP_VERSION = re.compile(r"^\d+\.\d+\.\d+\.(\d+|NEXT|LATEST)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check sfdx-project.json for common configuration issues.")
    parser.add_argument("--project-dir", "--manifest-dir", dest="project_dir", default=".",
                        help="Root directory of the DX project (default: .). --manifest-dir is an alias.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on REVIEW/WARN findings too.")
    return parser.parse_args()


def check_package_directories(data: dict, project_dir: Path, errors: list[str], reviews: list[str]) -> None:
    pkg_dirs = data.get("packageDirectories")
    if not isinstance(pkg_dirs, list) or not pkg_dirs:
        errors.append("ERROR: 'packageDirectories' is required and must be a non-empty array of {\"path\": ...} entries.")
        return
    entries = [e for e in pkg_dirs if isinstance(e, dict)]
    if len(entries) != len(pkg_dirs):
        errors.append("ERROR: every packageDirectories entry must be a JSON object.")
    defaults = [e for e in entries if e.get("default") is True]
    if len(entries) > 1 and not defaults:
        errors.append("ERROR: several packageDirectories but none has \"default\": true; the guide requires you to indicate the default.")
    if len(defaults) > 1:
        errors.append(f"ERROR: {len(defaults)} packageDirectories have \"default\": true; there can be only one default path.")

    seen: set[str] = set()
    for i, entry in enumerate(entries):
        path_val = entry.get("path")
        if not path_val or not isinstance(path_val, str):
            errors.append(f"ERROR: packageDirectories[{i}] has no 'path'.")
            continue
        if Path(path_val).is_absolute():
            errors.append(f"ERROR: packageDirectories[{i}].path '{path_val}' is absolute; the path is relative to the project.")
        norm = str(Path(path_val))
        if norm in seen:
            reviews.append(f"REVIEW: duplicate path '{path_val}' in packageDirectories; duplicate-path handling is undocumented, keep paths unique.")
        seen.add(norm)
        if not (project_dir / path_val).is_dir():
            errors.append(f"ERROR: packageDirectories[{i}].path '{path_val}' is not a directory under the project.")
        version = entry.get("versionNumber")
        if version is not None and not (isinstance(version, str) and OWN_VERSION.match(version)):
            errors.append(f"ERROR: packageDirectories[{i}].versionNumber '{version}' is not MAJOR.MINOR.PATCH.BUILD (a number or NEXT in the build slot).")
        for dep in entry.get("dependencies", []) if isinstance(entry.get("dependencies"), list) else []:
            dep_version = dep.get("versionNumber") if isinstance(dep, dict) else None
            if dep_version is not None and not (isinstance(dep_version, str) and DEP_VERSION.match(dep_version)):
                errors.append(f"ERROR: packageDirectories[{i}] dependency versionNumber '{dep_version}' is not MAJOR.MINOR.PATCH.(BUILD|NEXT|LATEST).")


def check_rest(data: dict, project_dir: Path, reviews: list[str], errors: list[str]) -> None:
    version = data.get("sourceApiVersion")
    if version is None:
        reviews.append("REVIEW: no sourceApiVersion; it is optional but decides which fields are retrieved per type.")
    elif not isinstance(version, str) or not re.match(r"^\d+\.\d+$", version):
        reviews.append(f"REVIEW: sourceApiVersion {version!r} is not a string like \"63.0\" (the form the guide uses).")

    if "force://" in json.dumps(data).lower():
        errors.append("ERROR: possible sfdxAuthUrl (force://) in sfdx-project.json; never commit auth URLs.")
    for key in data:
        if key.lower() in {"password", "secret", "token", "accesstoken", "refreshtoken"}:
            errors.append(f"ERROR: credential-like top-level key '{key}' in sfdx-project.json.")
        elif key in SCRATCH_KEYS:
            reviews.append(f"REVIEW: '{key}' belongs in the scratch org definition file (config/project-scratch-def.json).")
        elif key not in KNOWN_KEYS:
            reviews.append(f"REVIEW: top-level key '{key}' is not in the documented set: {', '.join(sorted(KNOWN_KEYS))}.")

    gitignore = project_dir / ".gitignore"
    if not gitignore.is_file():
        reviews.append("REVIEW: no .gitignore at the project root; exclude .sfdx/, .sf/ and auth files.")
    else:
        lines = {ln.strip().rstrip("/").lstrip("/") for ln in gitignore.read_text(encoding="utf-8", errors="replace").splitlines()}
        for needed in (".sfdx", ".sf"):
            if needed not in lines:
                reviews.append(f"REVIEW: .gitignore has no '{needed}/' entry.")


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        print(f"ERROR: project directory not found: {project_dir}")
        sys.exit(1)
    if not any(project_dir.iterdir()):
        print(f"WARN: {project_dir} is empty; nothing to check.")
        return 1 if args.strict else 0

    errors: list[str] = []
    reviews: list[str] = []
    sfdx_json = project_dir / "sfdx-project.json"
    if not sfdx_json.is_file():
        errors.append("ERROR: sfdx-project.json not found at the project root; create it with 'sf project generate --name <name>'.")
    else:
        try:
            data = json.loads(sfdx_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            data = None
            errors.append(f"ERROR: sfdx-project.json is not valid JSON: {exc}")
        if data is not None and not isinstance(data, dict):
            data = None
            errors.append("ERROR: sfdx-project.json root must be a JSON object.")
        if data is not None:
            check_package_directories(data, project_dir, errors, reviews)
            check_rest(data, project_dir, reviews, errors)

    for line in errors + reviews:
        print(line)
    if errors:
        return 1
    if reviews:
        return 1 if args.strict else 0
    print("No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
