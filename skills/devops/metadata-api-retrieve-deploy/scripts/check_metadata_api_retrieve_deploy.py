#!/usr/bin/env python3
"""Checker for the Metadata API Retrieve / Deploy skill.

Scans a directory of manifests (and any CI scripts under it) for defects.
Grounded in the Summer '26 Metadata API Developer Guide, Deleting Components
from an Organization (api_meta.txt L4601-4660), and the Salesforce DX
Developer Guide deploy table (sfdx_dev.txt L13515-13525).

ERROR (exit 1):
  - package.xml / destructiveChanges*.xml that does not parse, whose root is
    not <Package>, or with a <types> block missing <name> or <members>
  - <members>*</members> in a destructive manifest (wildcards aren't supported there)
  - a destructive manifest with no package.xml in the same directory, or whose
    sibling package.xml has no <version> (L4630-4631: it must include one)
  - destructiveChangesPre.xml / destructiveChangesPost.xml next to a package.xml
    whose <version> is below 33.0 (Pre/Post need API 33.0+)
WARN (exit 0, or 1 with --strict):
  - the same Type:member both added (package.xml) and deleted in one directory
    (the guide is silent on this; confirm a delete-and-recreate is intended)
  - a <version> that is not a number
  - empty directory, or no manifest found
  - package.xml with no <version>
  - <members>*</members> in a package.xml (fine for a capture, not for CI)
  - --ignore-errors / -r or --test-level / -l NoTestRun on a deploy line in a
    CI script (flag names per `sf project deploy start --help`, CLI 2.151.7)

Stdlib only.

Usage:
    python3 check_metadata_api_retrieve_deploy.py --manifest-dir manifest
    python3 check_metadata_api_retrieve_deploy.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DESTRUCTIVE = {"destructiveChanges.xml", "destructiveChangesPre.xml", "destructiveChangesPost.xml"}
SCRIPT_SUFFIXES = (".sh", ".yml", ".yaml", ".ps1", ".bash")
IGNORE_ERRORS = re.compile(r"--ignore-errors\b|(?<=\s)-r(?=\s|$)")
NO_TEST_RUN = re.compile(r"(--test-level|(?<=\s)-l)[\s=]+NoTestRun\b", re.IGNORECASE)
DEPLOY_LINE = re.compile(r"\bdeploy\b")


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def read_manifest(path: Path, errors: list[str]) -> tuple[dict[str, set[str]], str | None] | None:
    """Return ({type: {members}}, version) or None when unusable."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        errors.append(f"{path}: does not parse: {exc}")
        return None
    if _local(root.tag) != "Package":
        errors.append(f"{path}: root element is <{_local(root.tag)}>, expected <Package>")
        return None
    types: dict[str, set[str]] = {}
    version = None
    for child in root:
        tag = _local(child.tag)
        if tag == "version":
            version = (child.text or "").strip() or None
        elif tag == "types":
            names = [(c.text or "").strip() for c in child if _local(c.tag) == "name"]
            members = {(c.text or "").strip() for c in child if _local(c.tag) == "members"}
            if not names or not names[0]:
                errors.append(f"{path}: <types> block with no <name> (members: {sorted(members)[:3]})")
                continue
            if not members:
                errors.append(f"{path}: <types> {names[0]} has no <members>")
            types.setdefault(names[0], set()).update(members)
    return types, version


def _version_below(version: str | None, floor: float) -> bool:
    try:
        return version is not None and float(version) < floor
    except ValueError:
        return False


def check_manifests(root: Path, errors: list[str], warns: list[str]) -> int:
    manifests = sorted(p for p in root.rglob("*.xml") if p.name == "package.xml" or p.name in DESTRUCTIVE)
    parsed = {p: read_manifest(p, errors) for p in manifests}
    for path, result in parsed.items():
        if result is None:
            continue
        types, version = result
        if version is not None and not re.fullmatch(r"\d+(\.\d+)?", version):
            warns.append(f"{path}: <version>{version}</version> is not an API version number")
        if path.name == "package.xml":
            if version is None:
                warns.append(f"{path}: no <version>; a destructive deploy needs the API version in package.xml, and every manifest should pin one")
            for t, members in types.items():
                if "*" in members:
                    warns.append(f"{path}: wildcard <members>*</members> for {t}; use explicit members for anything CI deploys")
            continue
        # destructive manifest
        for t, members in types.items():
            if "*" in members:
                errors.append(f"{path}: wildcard in {t}; destructive manifests don't support wildcards")
        sibling = path.parent / "package.xml"
        if sibling not in parsed:
            errors.append(f"{path}: no package.xml in the same directory; a destructive deploy needs one that carries the API version")
            continue
        sib = parsed[sibling]
        if sib is None:
            continue
        sib_types, sib_version = sib
        if sib_version is None:
            errors.append(f"{path}: the package.xml beside it has no <version>; a destructive deploy needs the API version there")
        if path.name != "destructiveChanges.xml" and _version_below(sib_version, 33.0):
            errors.append(f"{path}: Pre/Post destructive manifests need API 33.0+, package.xml declares {sib_version}")
        for t, members in types.items():
            clash = sorted(members & sib_types.get(t, set()) - {"*"})
            if clash:
                warns.append(f"{path}: {t} {clash} is both deployed by package.xml and deleted here")
    return len(manifests)


def check_scripts(root: Path, warns: list[str]) -> None:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not path.name.endswith(SCRIPT_SUFFIXES):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Join backslash-continued lines so a flag on a continuation line still
        # counts as part of the deploy command.
        logical: list[tuple[int, str]] = []
        buf, start = "", 1
        for n, raw in enumerate(text.splitlines(), 1):
            if not buf:
                start = n
            if raw.rstrip().endswith("\\"):
                buf += raw.rstrip()[:-1] + " "
                continue
            logical.append((start, buf + raw))
            buf = ""
        if buf:
            logical.append((start, buf))
        for line, cmd in logical:
            if not DEPLOY_LINE.search(cmd):
                continue
            for rx, msg in ((IGNORE_ERRORS, "--ignore-errors (-r) deploys whatever succeeds; not for production"),
                            (NO_TEST_RUN, "--test-level NoTestRun applies only to development environments")):
                if rx.search(cmd):
                    warns.append(f"{path}:{line}: {msg}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest-dir", required=True, help="Directory holding package.xml / destructiveChanges*.xml (and optionally CI scripts).")
    ap.add_argument("--strict", action="store_true", help="Treat WARN findings as errors (exit 1).")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    if not any(p.is_file() for p in root.rglob("*")):
        print(f"WARN: {root} is empty -- nothing to check")
        return 1 if args.strict else 0

    errors: list[str] = []
    warns: list[str] = []
    if not check_manifests(root, errors, warns):
        warns.append(f"{root}: no package.xml or destructiveChanges*.xml found -- manifests were not checked")
    check_scripts(root, warns)

    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if errors:
        sys.exit(1)
    if warns:
        return 1 if args.strict else 0
    print("OK: manifests and scripts look deployable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
