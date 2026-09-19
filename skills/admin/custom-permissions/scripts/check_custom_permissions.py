#!/usr/bin/env python3
"""Checker script for the admin/custom-permissions skill.

Scans a Salesforce DX metadata tree and reports, by severity:

  ERROR  A permission set (or profile) grants a custom permission that is not
         defined anywhere in the tree. This is a deploy-breaking dangling
         reference: the grant cannot be deployed to an org that lacks the
         definition.
  WARN   A `requiredPermission` names a custom permission that is not in the
         tree. The dependency target must ship in the same package as its
         parent (Metadata API Developer Guide, CustomPermissionDependencyRequired).
  ERROR  CP-DESC-01 -- a custom permission's `description` is over 255
         characters. Metadata API Developer Guide, CustomPermission field
         table: "The custom permission description. Limit: 255 characters."
         (api_meta.txt L46651-46652). The deploy will be rejected.
  INFO   CP-DESC-02 -- a custom permission's `description` is over 200
         characters, approaching the 255-character limit above. Headroom is
         advisory, not a deploy risk: it is printed and counted but never
         affects the exit code, even under --strict.
  WARN   A custom permission has an empty or missing `description`. The
         description is the only place the consumer list can live.
  WARN   A consumer references a custom permission that is not defined in the
         tree -- `$Permission.X` in a validation rule / formula / Flow /
         FlexiPage, `FeatureManagement.checkPermission('X')` in Apex, or
         `@salesforce/customPermission/X` in an LWC module.
  INFO   A custom permission is defined but no permission set or profile in
         the tree grants it. Often intentional (the grant lives in another
         package), so it is not an error.

A run that read no files at all prints "Scanned 0 file(s)" rather than a
summary of zero findings: a tree with no custom permission, no permission
set or profile and no consumer file in it has not been cleared, it has not
been checked.

Exit codes:
  0 -- no ERROR (and no WARN when --strict is passed)
  1 -- at least one ERROR, or at least one WARN under --strict
  2 -- the manifest directory does not exist

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_custom_permissions.py --manifest-dir force-app/main/default
    python3 check_custom_permissions.py --manifest-dir force-app/main/default --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Namespace helpers
# ---------------------------------------------------------------------------

# Salesforce metadata XML uses a default namespace. ElementTree requires
# explicit namespace handling.
_SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    """Return a Clark-notation tag for the Salesforce metadata namespace."""
    return f"{{{_SF_NS}}}{local}"


# CP-DESC-01 / CP-DESC-02 thresholds. 255 is the Metadata API Developer
# Guide's documented ceiling for CustomPermission.description: "The custom
# permission description. Limit: 255 characters." (api_meta.txt
# L46651-46652). 200 is headroom to catch a description before it grows past
# the limit.
CP_DESC_MAX_LEN = 255
CP_DESC_WARN_LEN = 200


def child_text(parent, local: str) -> str | None:
    """Return the stripped text of a direct child element, or None.

    A leaf ``Element`` is falsy, so ``parent.find(a) or parent.find(b)`` is a
    trap. Always compare against None explicitly.
    """
    node = parent.find(_tag(local))
    if node is None:
        node = parent.find(local)  # tolerate namespace-stripped fixtures
    if node is None:
        return None
    if node.text is None:
        return ""
    return node.text.strip()


def find_all(parent, local: str) -> list:
    """Return direct children by local name, namespaced or not."""
    found = parent.findall(_tag(local))
    if not found:
        found = parent.findall(local)
    return found


# ---------------------------------------------------------------------------
# Consumer scanning
# ---------------------------------------------------------------------------

# Component-visibility grammar carries an extra segment and must be matched
# first so the plain-formula pattern does not capture "CustomPermission".
_RE_VISIBILITY = re.compile(r"\$Permission\.CustomPermission\.([A-Za-z]\w*)")
_RE_STANDARD = re.compile(r"\$Permission\.StandardPermission\.[A-Za-z]\w*")
_RE_FORMULA = re.compile(r"\$Permission\.([A-Za-z]\w*)")
_RE_APEX = re.compile(
    r"""checkPermission\s*\(\s*['"]([^'"]+)['"]\s*\)""", re.IGNORECASE
)
_RE_LWC_IMPORT = re.compile(r"@salesforce/customPermission/([A-Za-z]\w*)")

# Extensions worth scanning for consumers, by what they are.
_CONSUMER_SUFFIXES = (
    ".validationRule-meta.xml",
    ".field-meta.xml",
    ".object-meta.xml",
    ".flow-meta.xml",
    ".workflow-meta.xml",
    ".flexipage-meta.xml",
    ".prompt-meta.xml",
    ".quickAction-meta.xml",
    ".cls",
    ".trigger",
    ".page",
    ".cmp",
    ".js",
)


def is_consumer_file(path: Path) -> bool:
    return any(path.name.endswith(suffix) for suffix in _CONSUMER_SUFFIXES)


def scan_consumer_references(
    manifest_dir: Path, scanned: list[Path]
) -> dict[str, list[tuple[str, int]]]:
    """Return {custom-permission-name: [(relative path, line number), ...]}.

    Namespaced references (containing ``__``) are skipped: they belong to an
    installed managed package whose definition is not expected in this tree.
    """
    refs: dict[str, list[tuple[str, int]]] = {}

    def record(name: str, path: Path, lineno: int) -> None:
        if "__" in name:
            return
        rel = str(path.relative_to(manifest_dir))
        refs.setdefault(name, []).append((rel, lineno))

    for path in sorted(manifest_dir.rglob("*")):
        if not path.is_file() or not is_consumer_file(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        scanned.append(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in _RE_VISIBILITY.finditer(line):
                record(match.group(1), path, lineno)
            scrubbed = _RE_VISIBILITY.sub("", line)
            scrubbed = _RE_STANDARD.sub("", scrubbed)
            for match in _RE_FORMULA.finditer(scrubbed):
                record(match.group(1), path, lineno)
            for match in _RE_APEX.finditer(line):
                record(match.group(1), path, lineno)
            for match in _RE_LWC_IMPORT.finditer(line):
                record(match.group(1), path, lineno)

    return refs


# ---------------------------------------------------------------------------
# Metadata parsing
# ---------------------------------------------------------------------------


def parse_custom_permissions(
    manifest_dir: Path, scanned: list[Path]
) -> tuple[dict[str, dict], list[str]]:
    """Return ({api name: {description, required}}, parse errors)."""
    defined: dict[str, dict] = {}
    parse_errors: list[str] = []

    for cp_file in sorted(manifest_dir.rglob("*.customPermission-meta.xml")):
        name = cp_file.name.replace(".customPermission-meta.xml", "")
        rel = str(cp_file.relative_to(manifest_dir))
        scanned.append(cp_file)
        record: dict = {"file": rel, "description": None, "required": []}
        try:
            root = ET.parse(cp_file).getroot()
        except ET.ParseError as exc:
            parse_errors.append(f"{rel}: malformed XML ({exc})")
            defined[name] = record
            continue

        record["description"] = child_text(root, "description")
        for dep in find_all(root, "requiredPermission"):
            required_name = child_text(dep, "customPermission")
            dependency = child_text(dep, "dependency")
            if required_name:
                record["required"].append((required_name, dependency))
        defined[name] = record

    return defined, parse_errors


def parse_grants(
    manifest_dir: Path, scanned: list[Path]
) -> tuple[dict[str, list[str]], list[str]]:
    """Return ({granting container: [permission names]}, parse errors).

    Covers ``*.permissionset-meta.xml`` and ``*.profile-meta.xml`` -- Profile
    carries the same ``customPermissions`` element from API version 31.0.
    """
    grants: dict[str, list[str]] = {}
    parse_errors: list[str] = []

    patterns = (
        ("*.permissionset-meta.xml", ".permissionset-meta.xml", "permission set"),
        ("*.profile-meta.xml", ".profile-meta.xml", "profile"),
    )

    for glob, suffix, kind in patterns:
        for ps_file in sorted(manifest_dir.rglob(glob)):
            label = f"{kind} '{ps_file.name.replace(suffix, '')}'"
            scanned.append(ps_file)
            try:
                root = ET.parse(ps_file).getroot()
            except ET.ParseError as exc:
                rel = str(ps_file.relative_to(manifest_dir))
                parse_errors.append(f"{rel}: malformed XML ({exc})")
                grants[label] = []
                continue

            enabled_names: list[str] = []
            for cp_node in find_all(root, "customPermissions"):
                name = child_text(cp_node, "name")
                enabled = child_text(cp_node, "enabled")
                if name and enabled == "true":
                    enabled_names.append(name)
            grants[label] = enabled_names

    return grants, parse_errors


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def analyse(
    defined: dict[str, dict],
    grants: dict[str, list[str]],
    consumer_refs: dict[str, list[tuple[str, int]]],
) -> tuple[list[str], list[str], list[str], dict[str, list[str]]]:
    """Return (errors, warnings, infos, coverage_map)."""
    errors: list[str] = []
    warnings: list[str] = []
    infos: list[str] = []

    coverage_map: dict[str, list[str]] = {name: [] for name in defined}

    # ERROR -- a grant naming a permission that does not exist in the tree.
    for container, names in grants.items():
        for name in names:
            if name in coverage_map:
                coverage_map[name].append(container)
            elif "__" in name:
                infos.append(
                    f"{container} grants namespaced '{name}'; its definition "
                    f"belongs to an installed package, not this tree."
                )
            else:
                errors.append(
                    f"{container} grants '{name}', which is not defined by any "
                    f"*.customPermission-meta.xml in the tree. The deploy will fail."
                )

    # WARN -- requiredPermission target missing, or dependency not true.
    for name, record in sorted(defined.items()):
        for required_name, dependency in record["required"]:
            if "__" in required_name:
                continue
            if required_name not in defined:
                warnings.append(
                    f"'{name}' requires '{required_name}', which is not defined in "
                    f"the tree. A dependency target must ship in the same package "
                    f"as its parent."
                )
            if dependency is not None and dependency != "true":
                warnings.append(
                    f"'{name}' declares requiredPermission '{required_name}' with "
                    f"<dependency>{dependency}</dependency>; only 'true' makes the "
                    f"target required."
                )

    # ERROR/WARN -- empty description, or description length (CP-DESC-01 / CP-DESC-02).
    for name, record in sorted(defined.items()):
        description = record["description"]
        if description is None or not description.strip():
            warnings.append(
                f"'{name}' has no description ({record['file']}). Name the "
                f"consumers there -- it is the only place that list survives."
            )
        elif len(description) > CP_DESC_MAX_LEN:
            errors.append(
                f"CP-DESC-01 '{name}' has a {len(description)}-character description "
                f"({record['file']}); the Metadata API field limit is "
                f"{CP_DESC_MAX_LEN} characters (CustomPermission.description, "
                "api_meta.txt L46651-46652) and the deploy will be rejected."
            )
        elif len(description) > CP_DESC_WARN_LEN:
            infos.append(
                f"CP-DESC-02 '{name}' has a {len(description)}-character description "
                f"({record['file']}); approaching the {CP_DESC_MAX_LEN}-character limit. "
                "Headroom only -- never fails the run, even under --strict."
            )

    # WARN -- a consumer references a permission that is not defined here.
    for name, locations in sorted(consumer_refs.items()):
        if name in defined:
            continue
        shown = ", ".join(f"{path}:{line}" for path, line in locations[:4])
        if len(locations) > 4:
            shown += f", +{len(locations) - 4} more"
        warnings.append(
            f"'{name}' is referenced by {len(locations)} consumer "
            f"location(s) but is not defined in the tree: {shown}"
        )

    # INFO -- defined but ungranted.
    for name, containers in sorted(coverage_map.items()):
        if not containers:
            infos.append(
                f"'{name}' is defined but granted by no permission set or profile "
                f"in this tree. Nobody holds it unless the grant lives elsewhere."
            )

    return errors, warnings, infos, coverage_map


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_coverage_report(
    coverage_map: dict[str, list[str]],
    consumer_refs: dict[str, list[tuple[str, int]]],
) -> None:
    """Print a human-readable coverage table."""
    if not coverage_map:
        print("  (no custom permissions found)")
        return

    width = max(len(name) for name in coverage_map)
    width = max(width, len("Custom Permission"))
    print(f"  {'Custom Permission':<{width}}  Consumers  Granted by")
    print("  " + "-" * (width + 30))
    for name in sorted(coverage_map):
        containers = coverage_map[name]
        granted = ", ".join(sorted(containers)) if containers else "(none)"
        uses = len(consumer_refs.get(name, []))
        print(f"  {name:<{width}}  {uses:>9}  {granted}")


def print_block(title: str, lines: list[str]) -> None:
    if not lines:
        return
    print(title)
    for line in lines:
        print(f"  {line}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for custom permission definitions, the "
            "permission sets and profiles that grant them, dependency targets, "
            "and consumer references that point at nothing."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on warnings as well as errors.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.is_dir():
        print(f"ERROR: Manifest directory not found: {manifest_dir}")
        return 2

    print(f"Scanning: {manifest_dir.resolve()}")
    print()

    # Every file actually opened lands here, so a run that read nothing can
    # say so instead of printing a summary of zero findings as if it passed.
    scanned: list[Path] = []
    defined, cp_parse_errors = parse_custom_permissions(manifest_dir, scanned)
    grants, grant_parse_errors = parse_grants(manifest_dir, scanned)
    consumer_refs = scan_consumer_references(manifest_dir, scanned)

    print(f"Custom permissions defined:        {len(defined)}")
    print(f"Permission sets / profiles parsed: {len(grants)}")
    print(f"Distinct permissions referenced:   {len(consumer_refs)}")
    print()

    if not defined:
        print("  (no *.customPermission-meta.xml files found)")
        print()

    errors, warnings, infos, coverage_map = analyse(defined, grants, consumer_refs)
    errors = [f"malformed metadata: {e}" for e in cp_parse_errors + grant_parse_errors] + errors

    print("Coverage (custom permission -> consumers, granting containers):")
    print_coverage_report(coverage_map, consumer_refs)
    print()

    print_block("ERROR:", errors)
    print_block("WARN:", warnings)
    print_block("INFO:", infos)

    print(
        f"Summary: {len(errors)} error(s), {len(warnings)} warning(s), "
        f"{len(infos)} info."
    )

    if not scanned and not errors and not warnings and not infos:
        print("Scanned 0 file(s) — nothing asserted; check --manifest-dir")

    if errors:
        return 1
    if args.strict and warnings:
        print("--strict: failing on warnings.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
