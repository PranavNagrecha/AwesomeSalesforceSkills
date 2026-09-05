#!/usr/bin/env python3
"""Lint queryability verdict records, and report which setup objects a metadata
tree's permission sets can actually query.

Two independent modes; you can run both in one invocation.

1. Verdict linting (positional arguments).
   Each file is a verdict record in the YAML subset documented in
   ``references/metadata-examples.md`` block 6. The linter enforces the required
   keys, the closed verdict vocabulary, one entry per required probe, and the
   consistency rules that tie a verdict to the checks that justify it -- so a
   record cannot claim ``object-does-not-exist`` while its own Describe Global
   check passed.

2. Permission coverage (``--manifest-dir``).
   Parses ``*.permissionset-meta.xml`` and ``*.profile-meta.xml`` under the
   directory, collects every enabled ``userPermissions/name``, and reports which
   of the setup objects whose *Special Access Rules* name a permission the
   combined grants can query.

Grounding for the object -> permission table (Object Reference for the Salesforce
Platform, Summer '26 / v62 extract; line numbers are into the plain-text
extract):

  AsyncApexJob                    ViewSetup             L42271
  ApexTestQueueItem               ViewSetup             L32222
  ApexTestResult                  ViewSetup             L32329
  ApexTestResultLimits            ViewSetup             L32565
  ApexTestRunResult               ViewSetup             L32718
  ApexTestSuite                   ViewSetup             L32900
  ApexPageInfo                    ViewSetup             L31568
  AccountTerritoryAssignmentRule  ViewSetup             L18116
  AccountTerritoryAssignmentRuleItem ViewSetup          L18206
  AuthSession                     ManageUsers           L47053
  OauthToken                      CustomizeApplication  L189605
  AuthProvider                    CustomizeApplication  L46569

``ApiEnabled`` gates every API call at all (REST API Developer Guide, *API User
Permissions*, api_rest.txt L418-L419) and is checked as a prerequisite.

UNVERIFIED (2026-09-04): the permission API spellings ``ViewSetup``,
``ManageUsers``, ``CustomizeApplication`` and ``ApiEnabled`` are grounded in the
Metadata API guide (api_meta.txt L95384, L24495, L10981, L95216). The Object
Reference also documents "Modify All Data" for the Content* subscription objects
and "Manage AuthProviders" for AuthProvider, but neither API spelling appears in
the extracted guides, so those objects are deliberately absent from the table
above rather than guessed at.

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_salesforce_object_queryability.py --help
    python3 check_salesforce_object_queryability.py verdicts/*.verdict.yaml
    python3 check_salesforce_object_queryability.py --manifest-dir force-app/main/default
    python3 check_salesforce_object_queryability.py --manifest-dir force-app v.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

# --- verdict vocabulary -----------------------------------------------------

# The six diagnostic failure modes from SKILL.md, in order.
FAILURE_MODES = {
    "object-does-not-exist": 1,
    "edition-or-feature-gated": 2,
    "permission-denied": 3,
    "field-not-visible": 4,
    "namespace-prefix-missing": 5,
    "api-version-too-old": 6,
}

# Terminal outcomes that are not failures of diagnosis.
TERMINAL_VERDICTS = {
    "queryable",
    "not-queryable-on-this-surface",
}

VALID_VERDICTS = set(FAILURE_MODES) | TERMINAL_VERDICTS

REQUIRED_TOP_LEVEL = ("object", "surface", "api_version", "checks", "verdict", "evidence")

VALID_SURFACES = {"rest-data", "rest-tooling", "soap", "apex", "bulk"}

# Every verdict record must carry a result for each of these probes.
REQUIRED_CHECKS = (
    "org_api_enabled",
    "in_describe_global",
    "object_queryable",
    "object_accessible",
    "field_accessible",
    "query_executed",
)

VALID_RESULTS = {"pass", "fail", "skip"}

# verdict -> (check name, required result) pairs that must all hold.
VERDICT_CONSISTENCY = {
    "object-does-not-exist": [("in_describe_global", "fail")],
    "namespace-prefix-missing": [("in_describe_global", "fail")],
    "api-version-too-old": [("in_describe_global", "fail")],
    "edition-or-feature-gated": [("in_describe_global", "fail")],
    "not-queryable-on-this-surface": [
        ("in_describe_global", "pass"),
        ("object_queryable", "fail"),
    ],
    "permission-denied": [
        ("in_describe_global", "pass"),
        ("object_accessible", "fail"),
    ],
    "field-not-visible": [
        ("in_describe_global", "pass"),
        ("object_accessible", "pass"),
    ],
    "queryable": [
        ("in_describe_global", "pass"),
        ("object_queryable", "pass"),
        ("object_accessible", "pass"),
        ("query_executed", "pass"),
    ],
}

API_VERSION_RE = re.compile(r"^\d{1,3}\.\d$")
MIN_EVIDENCE_CHARS = 20

# --- setup-object permission table ------------------------------------------

SETUP_OBJECT_PERMISSIONS = {
    "AsyncApexJob": ("ViewSetup", "object_reference.txt L42271"),
    "ApexTestQueueItem": ("ViewSetup", "object_reference.txt L32222"),
    "ApexTestResult": ("ViewSetup", "object_reference.txt L32329"),
    "ApexTestResultLimits": ("ViewSetup", "object_reference.txt L32565"),
    "ApexTestRunResult": ("ViewSetup", "object_reference.txt L32718"),
    "ApexTestSuite": ("ViewSetup", "object_reference.txt L32900"),
    "ApexPageInfo": ("ViewSetup", "object_reference.txt L31568"),
    "AccountTerritoryAssignmentRule": ("ViewSetup", "object_reference.txt L18116"),
    "AccountTerritoryAssignmentRuleItem": ("ViewSetup", "object_reference.txt L18206"),
    "AuthSession": ("ManageUsers", "object_reference.txt L47053"),
    "OauthToken": ("CustomizeApplication", "object_reference.txt L189605"),
    "AuthProvider": ("CustomizeApplication", "object_reference.txt L46569; also needs Manage AuthProviders, API name not in the extracted guides"),
}

PREREQUISITE_PERMISSION = "ApiEnabled"


# --- tiny YAML-subset reader ------------------------------------------------


def _strip_scalar(raw: str) -> str:
    """Unquote a scalar and drop a trailing comment when it is unquoted."""
    text = raw.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    if " #" in text:
        text = text.split(" #", 1)[0].rstrip()
    return text


def parse_verdict_yaml(text: str) -> tuple[dict, list[str]]:
    """Parse the constrained YAML shape used by verdict records.

    Supports exactly what block 6 of references/metadata-examples.md emits:
    top-level ``key: scalar``, a list of scalars, and a list of flat mappings.
    Returns ``(record, parse_errors)``.
    """
    record: dict = {}
    errors: list[str] = []
    current_key: str | None = None
    current_map: dict | None = None

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        body = line.strip()

        if indent == 0:
            current_map = None
            if ":" not in body:
                errors.append(f"line {lineno}: expected `key: value`, got {body!r}")
                continue
            key, _, value = body.partition(":")
            current_key = key.strip()
            value = _strip_scalar(value)
            record[current_key] = value if value else []
            continue

        if current_key is None:
            errors.append(f"line {lineno}: indented line before any top-level key")
            continue

        container = record.get(current_key)
        if not isinstance(container, list):
            errors.append(f"line {lineno}: `{current_key}` has a scalar value and a nested block")
            continue

        if body.startswith("- "):
            item = body[2:].strip()
            if ":" in item and not item.startswith(("'", '"')):
                key, _, value = item.partition(":")
                current_map = {key.strip(): _strip_scalar(value)}
                container.append(current_map)
            else:
                current_map = None
                container.append(_strip_scalar(item))
            continue

        if current_map is None:
            errors.append(f"line {lineno}: continuation line outside a list item: {body!r}")
            continue

        if ":" not in body:
            errors.append(f"line {lineno}: expected `key: value` inside a list item, got {body!r}")
            continue

        key, _, value = body.partition(":")
        current_map[key.strip()] = _strip_scalar(value)

    return record, errors


# --- verdict linting --------------------------------------------------------


def check_verdict_record(path: Path) -> list[str]:
    """Return one issue string per problem found in a single verdict record."""
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path}: unreadable ({exc})"]

    record, parse_errors = parse_verdict_yaml(text)
    issues.extend(f"{path}: {err}" for err in parse_errors)

    for key in REQUIRED_TOP_LEVEL:
        if key not in record:
            issues.append(f"{path}: missing required key `{key}`")

    obj = record.get("object")
    if isinstance(obj, str) and not obj:
        issues.append(f"{path}: `object` is empty; name the sObject the verdict is about")

    surface = record.get("surface")
    if isinstance(surface, str) and surface and surface not in VALID_SURFACES:
        issues.append(
            f"{path}: `surface` is {surface!r}; expected one of {sorted(VALID_SURFACES)}"
        )

    api_version = record.get("api_version")
    if isinstance(api_version, str) and api_version and not API_VERSION_RE.match(api_version):
        issues.append(
            f"{path}: `api_version` is {api_version!r}; expected a bare API version "
            f"such as '67.0' (no leading 'v')"
        )

    verdict = record.get("verdict")
    if isinstance(verdict, str) and verdict and verdict not in VALID_VERDICTS:
        issues.append(
            f"{path}: `verdict` is {verdict!r}; expected one of the six failure modes "
            f"{sorted(FAILURE_MODES)} or a terminal outcome {sorted(TERMINAL_VERDICTS)}. "
            f"A free-text reason string is the failure this skill exists to prevent."
        )

    checks = record.get("checks")
    results: dict[str, str] = {}
    if not isinstance(checks, list) or not checks:
        issues.append(f"{path}: `checks` must be a non-empty list of probe results")
    else:
        for index, entry in enumerate(checks):
            if not isinstance(entry, dict):
                issues.append(f"{path}: checks[{index}] is not a `name/result/evidence` mapping")
                continue
            name = entry.get("name", "")
            result = entry.get("result", "")
            evidence = entry.get("evidence", "")
            if not name:
                issues.append(f"{path}: checks[{index}] has no `name`")
            if result not in VALID_RESULTS:
                issues.append(
                    f"{path}: checks[{index}] ({name or '?'}) has result {result!r}; "
                    f"expected pass, fail or skip"
                )
            if not evidence:
                issues.append(
                    f"{path}: checks[{index}] ({name or '?'}) has no `evidence`; "
                    f"an unevidenced probe result is an assertion, not a diagnosis"
                )
            if name:
                if name in results:
                    issues.append(f"{path}: duplicate check `{name}`")
                results[name] = result

        for required in REQUIRED_CHECKS:
            if required not in results:
                issues.append(
                    f"{path}: no `{required}` check; all six probes must be recorded "
                    f"even when the answer is skip"
                )

    evidence_lines = record.get("evidence")
    if not isinstance(evidence_lines, list) or not evidence_lines:
        issues.append(f"{path}: `evidence` must be a non-empty list of lines")
    else:
        for index, line in enumerate(evidence_lines):
            if not isinstance(line, str) or len(line) < MIN_EVIDENCE_CHARS:
                issues.append(
                    f"{path}: evidence[{index}] is under {MIN_EVIDENCE_CHARS} characters "
                    f"({line!r}); cite the payload, the guide, or the remediation"
                )

    if isinstance(verdict, str) and verdict in VERDICT_CONSISTENCY and results:
        for check_name, expected in VERDICT_CONSISTENCY[verdict]:
            actual = results.get(check_name)
            if actual is None:
                continue
            if actual != expected:
                issues.append(
                    f"{path}: verdict `{verdict}` requires `{check_name}` to be "
                    f"{expected}, but the record says {actual}. Either the verdict or "
                    f"the check is wrong."
                )

    if verdict == "queryable":
        failed = sorted(name for name, result in results.items() if result == "fail")
        if failed:
            issues.append(
                f"{path}: verdict `queryable` but these checks failed: {failed}. "
                f"A zero-row result is a pass; a failed probe is not."
            )

    return issues


# --- permission-set scanning ------------------------------------------------


def _child_text(element: ET.Element, tag: str) -> str | None:
    """Return the stripped text of a single named child, or None.

    Never rely on the truthiness of an Element: an element with no children is
    falsy even when it exists, so `el.find(a) or el.find(b)` silently discards
    real matches. Every lookup here tests `is not None`.
    """
    found = element.find(MD_NS + tag)
    if found is None:
        found = element.find(tag)
    if found is None:
        return None
    if found.text is None:
        return None
    return found.text.strip()


def collect_enabled_permissions(manifest_dir: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Map each enabled userPermission name to the files granting it."""
    granted: dict[str, list[str]] = {}
    issues: list[str] = []

    patterns = ("*.permissionset-meta.xml", "*.profile-meta.xml", "*.permissionset", "*.profile")
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(manifest_dir.rglob(pattern)))

    if not files:
        issues.append(
            f"no permission set or profile metadata under {manifest_dir} "
            f"(looked for {', '.join(patterns)})"
        )
        return granted, issues

    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            issues.append(f"{path}: not well-formed XML ({exc})")
            continue

        entries = root.findall(MD_NS + "userPermissions")
        if not entries:
            entries = root.findall("userPermissions")

        for entry in entries:
            name = _child_text(entry, "name")
            enabled = _child_text(entry, "enabled")
            if name is None:
                issues.append(f"{path}: a <userPermissions> block has no <name>")
                continue
            if enabled is None:
                issues.append(
                    f"{path}: <userPermissions><name>{name}</name> has no <enabled>; "
                    f"the Metadata API marks enabled as required"
                )
                continue
            if enabled.lower() == "true":
                granted.setdefault(name, []).append(path.name)

    return granted, issues


def report_setup_object_coverage(granted: dict[str, list[str]]) -> list[str]:
    """Describe which documented setup objects the granted permissions can query."""
    lines: list[str] = []
    has_api = PREREQUISITE_PERMISSION in granted

    lines.append("Setup-object query coverage from the scanned permission sets and profiles:")
    if has_api:
        lines.append(
            f"  {PREREQUISITE_PERMISSION:22s} GRANTED by {', '.join(granted[PREREQUISITE_PERMISSION])}"
        )
    else:
        lines.append(
            f"  {PREREQUISITE_PERMISSION:22s} NOT GRANTED - without it no API call succeeds "
            f"at all, so every row below is theoretical (api_rest.txt L418-L419)"
        )

    for obj in sorted(SETUP_OBJECT_PERMISSIONS):
        permission, source = SETUP_OBJECT_PERMISSIONS[obj]
        if permission in granted:
            where = ", ".join(granted[permission])
            lines.append(f"  QUERYABLE     {obj} - {permission} granted by {where} [{source}]")
        else:
            lines.append(f"  NOT QUERYABLE {obj} - needs {permission} [{source}]")

    covered = sum(1 for obj in SETUP_OBJECT_PERMISSIONS if SETUP_OBJECT_PERMISSIONS[obj][0] in granted)
    lines.append(
        f"  {covered}/{len(SETUP_OBJECT_PERMISSIONS)} documented setup objects are queryable "
        f"by the union of these grants."
    )
    return lines


# --- CLI --------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint queryability verdict records and report which setup objects a "
            "metadata tree's permission sets can query."
        ),
    )
    parser.add_argument(
        "verdicts",
        nargs="*",
        help="Verdict record files to lint (the YAML subset from references/metadata-examples.md).",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help=(
            "Root directory of a Salesforce DX metadata tree. Scans permission sets "
            "and profiles and reports setup-object query coverage."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    issues: list[str] = []
    notes: list[str] = []

    if not args.verdicts and args.manifest_dir is None:
        print(
            "Nothing to check. Pass verdict files, --manifest-dir, or both. "
            "See --help.",
            file=sys.stderr,
        )
        return 1

    for name in args.verdicts:
        path = Path(name)
        if not path.exists():
            issues.append(f"{path}: verdict file not found")
            continue
        issues.extend(check_verdict_record(path))

    if args.manifest_dir is not None:
        manifest_dir = Path(args.manifest_dir)
        if not manifest_dir.exists():
            issues.append(f"Manifest directory not found: {manifest_dir}")
        else:
            granted, scan_issues = collect_enabled_permissions(manifest_dir)
            issues.extend(scan_issues)
            if granted:
                notes.extend(report_setup_object_coverage(granted))

    for line in notes:
        print(line)

    if not issues:
        if args.verdicts:
            print(f"No issues found in {len(args.verdicts)} verdict record(s).")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    print(f"{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
