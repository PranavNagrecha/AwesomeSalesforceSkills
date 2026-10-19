#!/usr/bin/env python3
"""Checker for the Migration From Change Sets To SFDX skill.

Inspects a Salesforce DX project directory for migration defects. Grounded in
the Summer '26 Salesforce DX Developer Guide (sfdx_dev.txt): packageDirectories
is required, relative, and needs exactly one default when there are several
(L2335-2344); sourceApiVersion is optional but decides which fields are
retrieved (L2410-2418); the convert writes into the default package directory
(L2074-2085); the profile recommendation (L11884-11887). InstalledPackage:
Metadata API Developer Guide (api_meta.txt L81389-81395).

Exit codes:
  1  the directory does not exist
  0  the directory is empty (WARN: nothing to check; 1 with --strict)
  1  the directory has files but no sfdx-project.json -- it is not an SFDX
     project yet, so every later check would be meaningless (ERROR)
  1  any other ERROR
  0  WARN only (1 with --strict)

ERROR:
  - sfdx-project.json missing (non-empty dir), not valid JSON, or with no
    packageDirectories
  - sfdx-project.json whose top level is not an object, or packageDirectories
    that is not a list of objects
  - a packageDirectories path that is absolute (including C:\\... and ~/...)
  - several packageDirectories with no default, or more than one default
  - a "default" that is not the JSON boolean true/false (e.g. the string "true")
WARN:
  - sourceApiVersion missing, or different from --expected-api-version
  - a packageDirectories path that does not exist yet
  - no .forceignore
  - profiles in source that no active .forceignore rule excludes (comments
    and ! negations don't count)
  - InstalledPackage files in source (deploying one installs or upgrades a
    1GP package and must be the only type in its manifest)
  - metadata-format leftovers inside a package directory (package.xml or
    undecomposed *.object files) -- run sf project convert mdapi

Stdlib only.

Usage:
    python3 check_migration_from_change_sets_to_sfdx.py --manifest-dir path/to/project
    python3 check_migration_from_change_sets_to_sfdx.py --manifest-dir . --expected-api-version 67.0 --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def check_project_json(root: Path, expected_api: str | None, errors: list[str], warns: list[str]) -> list[Path]:
    proj_file = root / "sfdx-project.json"
    try:
        proj = json.loads(proj_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"{proj_file}: not valid JSON: {exc}")
        return []

    if not isinstance(proj, dict):
        errors.append(f"{proj_file}: top level must be a JSON object, got {type(proj).__name__}")
        return []
    api = proj.get("sourceApiVersion")
    if not api:
        warns.append(f"{proj_file}: no sourceApiVersion; it decides which fields each type retrieves and converts, so pin it")
    elif expected_api and str(api) != expected_api:
        warns.append(f"{proj_file}: sourceApiVersion is {api}, expected {expected_api}")

    dirs = proj.get("packageDirectories") or []
    if not dirs:
        errors.append(f"{proj_file}: packageDirectories is required and is missing or empty")
        return []
    if not isinstance(dirs, list) or not all(isinstance(d, dict) for d in dirs):
        errors.append(f"{proj_file}: packageDirectories must be a list of objects like {{\"path\": \"force-app\"}}")
        return []
    for d in dirs:
        if "default" in d and not isinstance(d["default"], bool):
            errors.append(f"{proj_file}: packageDirectories '{d.get('path')}' has \"default\": {json.dumps(d['default'])}; use the JSON boolean true or false")
    defaults = [d for d in dirs if d.get("default") is True]
    if len(dirs) > 1 and not defaults:
        errors.append(f"{proj_file}: {len(dirs)} packageDirectories and none has \"default\": true; mark exactly one")
    if len(defaults) > 1:
        errors.append(f"{proj_file}: {len(defaults)} packageDirectories are marked default; only one is allowed")
    existing: list[Path] = []
    for d in dirs:
        p = str(d.get("path", ""))
        if not p:
            errors.append(f"{proj_file}: a packageDirectories entry has no path")
        elif Path(p).is_absolute() or re.match(r"^([A-Za-z]:[\\/]|\\\\|~)", p):
            errors.append(f"{proj_file}: packageDirectories path '{p}' is absolute; paths are relative to the project")
        elif not (root / p).is_dir():
            warns.append(f"{proj_file}: packageDirectories path '{p}' does not exist yet (retrieve or convert into it)")
        else:
            existing.append(root / p)
    return existing


def check_forceignore_and_profiles(root: Path, pkg_dirs: list[Path], warns: list[str]) -> None:
    fi = root / ".forceignore"
    rules = fi.read_text(encoding="utf-8", errors="ignore") if fi.is_file() else None
    if rules is None:
        warns.append(f"{root}: no .forceignore; nothing is excluded from deploy, retrieve, or convert")
    profiles = [p for d in pkg_dirs for p in d.rglob("*.profile-meta.xml")]
    active = [ln.strip() for ln in (rules or "").splitlines()
              if ln.strip() and not ln.strip().startswith(("#", "!"))]
    if profiles and not any("profile" in ln.lower() for ln in active):
        warns.append(f"{len(profiles)} profile file(s) in source (e.g. {profiles[0].name}) and .forceignore does not exclude profiles; "
                     "the DX guide recommends permission sets, or ignoring profiles if you keep them")


def check_leftovers(pkg_dirs: list[Path], warns: list[str]) -> None:
    for d in pkg_dirs:
        for p in d.rglob("*"):
            if not p.is_file():
                continue
            if p.name.endswith(".installedPackage") or p.name.endswith(".installedPackage-meta.xml"):
                warns.append(f"{p}: InstalledPackage in source; deploying it installs or upgrades a 1GP package and it must be the only type in its manifest -- exclude it")
            elif p.name == "package.xml":
                warns.append(f"{p}: package.xml inside a package directory; keep manifests in manifest/ (it looks like an unconverted metadata-format tree)")
            elif p.suffix == ".object":
                warns.append(f"{p}: metadata-format .object file; source format splits it into objects/<Name>/ -- run sf project convert mdapi")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest-dir", "--project-dir", dest="manifest_dir", required=True,
                    help="Root of the SFDX project (the directory holding sfdx-project.json). --project-dir is an alias.")
    ap.add_argument("--expected-api-version", default=None, help="Expected sourceApiVersion, e.g. 67.0.")
    ap.add_argument("--strict", action="store_true", help="Treat WARN findings as errors (exit 1).")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: project directory not found: {root}")
        sys.exit(1)
    if not any(root.iterdir()):
        print(f"WARN: {root} is empty -- nothing to check")
        return 1 if args.strict else 0
    if not (root / "sfdx-project.json").is_file():
        print(f"ERROR: {root} has files but no sfdx-project.json; run 'sf project generate --name <name>' (or point --manifest-dir at the project root)")
        sys.exit(1)

    errors: list[str] = []
    warns: list[str] = []
    pkg_dirs = check_project_json(root, args.expected_api_version, errors, warns)
    check_forceignore_and_profiles(root, pkg_dirs, warns)
    check_leftovers(pkg_dirs, warns)

    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if errors:
        sys.exit(1)
    if warns:
        return 1 if args.strict else 0
    print("OK: project structure is ready for source-driven deploys.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
