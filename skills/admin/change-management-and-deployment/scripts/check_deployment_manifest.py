#!/usr/bin/env python3
"""Audit deployment manifests and metadata folders for common release risks.

Two entry points:

    python3 check_deployment_manifest.py --manifest-dir manifest/
    python3 check_deployment_manifest.py manifest/package.xml force-app/

The --manifest-dir form runs the directory-level checks that need to see the whole
manifest set at once (a destructive manifest with no companion package.xml, a release
manifest asking for NoTestRun). It recurses: point it at a build root and it finds
every package.xml under it, and applies the companion-manifest checks per directory,
so a wider scope reads more, not less. The positional form keeps the original
per-file scan.

Severities and exit codes:
  ERROR / CRITICAL   the manifest will not deploy as written; exit 1
  HIGH / WARN /      risk to review before deploying -- notably a RISKY_TYPES
  MEDIUM / LOW       member such as SharingRules, which is a legitimate thing to
                     ship and must not fail the run on its own; printed, exit 0

  0 -- no ERROR/CRITICAL (and no finding at all when --strict is passed)
  1 -- at least one ERROR/CRITICAL, or any finding under --strict

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

RISKY_TYPES = {"SharingRules", "ConnectedApp", "ExternalCredential", "NamedCredential"}
TEXT_SUFFIXES = {".xml", ".cls", ".trigger", ".js", ".json", ".yaml", ".yml"}
SEVERITY_WEIGHTS = {"ERROR": 25, "CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "WARN": 5, "LOW": 1, "REVIEW": 0}

# Metadata API deploy(): testLevel enum. NoTestRun "applies only to deployments to
# development environments, such as sandbox, Developer Edition, or trial organizations."
DEV_ONLY_TEST_LEVELS = {"notestrun"}
VALID_TEST_LEVELS = {
    "notestrun",
    "runspecifiedtests",
    "runrelevanttests",
    "runlocaltests",
    "runalltestsinorg",
}

# Signals in a release-manifest YAML/JSON note that the target is production.
PRODUCTION_HINTS = re.compile(
    r"(?im)^\s*(?:target_org|target|org|environment|env)\s*:\s*[\"']?(prod\w*)\b"
)
TEST_LEVEL_LINE = re.compile(r"(?im)^\s*(?:testlevel|test_level|test-level)\s*:\s*[\"']?([A-Za-z]+)")


# --------------------------------------------------------------------------- helpers

def child(element, tag: str):
    """Return the first child with `tag`, namespaced or not, or None.

    Never use `a.find(x) or a.find(y)` on ElementTree: an Element with no children is
    falsy even when it exists, so the `or` silently discards a real match.
    """
    found = element.find(f"{MD_NS}{tag}")
    if found is None:
        found = element.find(tag)
    return found


def children(element, tag: str) -> list:
    found = element.findall(f"{MD_NS}{tag}")
    if not found:
        found = element.findall(tag)
    return found


def text_of(element, tag: str) -> str:
    node = child(element, tag)
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(candidate for candidate in path.rglob("*") if candidate.is_file())
        else:
            files.append(path)
    return files


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


BLOCKING_SEVERITIES = {"ERROR", "CRITICAL"}


def emit_result(findings: list[str], summary: str, strict: bool = False) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    errors = [item for item in normalized if item["severity"] in BLOCKING_SEVERITIES]
    if normalized:
        print(
            f"{len(normalized)} finding(s) detected ({len(errors)} blocking)",
            file=sys.stderr,
        )
    if errors:
        return 1
    if strict and normalized:
        print("--strict: failing on non-blocking findings.", file=sys.stderr)
        return 1
    return 0


# ------------------------------------------------------------------- per-file checks

def audit_package_xml(path: Path, text: str) -> list[str]:
    """Check 1: the manifest parses as XML and declares an API version."""
    findings: list[str] = []

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return [f"ERROR {path}: manifest is not well-formed XML ({exc})"]

    if not root.tag.endswith("Package"):
        findings.append(
            f"ERROR {path}: root element is <{root.tag}>; a manifest's root must be <Package>"
        )

    version = text_of(root, "version")
    is_destructive = path.name.lower().startswith("destructivechanges")

    if not version:
        if is_destructive:
            # The version lives in the companion package.xml, not here.
            pass
        else:
            findings.append(
                f"ERROR {path}: package.xml declares no <version>; the deploy has no API version"
            )
    elif not re.fullmatch(r"\d+\.0", version):
        findings.append(
            f"WARN {path}: <version> is '{version}'; expected a form like '66.0'"
        )

    type_blocks = children(root, "types")
    if not type_blocks and not is_destructive and version:
        findings.append(
            f"LOW {path}: manifest lists no components (valid for a delete-only deploy)"
        )

    profile_members: list[str] = []
    wildcard_objects = False

    for block in type_blocks:
        name_node = child(block, "name")
        type_name = (name_node.text or "").strip() if name_node is not None else ""
        members = [(node.text or "").strip() for node in children(block, "members")]

        if not type_name:
            findings.append(f"ERROR {path}: a <types> block has no <name> element")
            continue
        if not members:
            findings.append(f"ERROR {path}: <types> block for {type_name} lists no <members>")

        if is_destructive and "*" in members:
            findings.append(
                f"ERROR {path}: destructive manifest uses the '*' wildcard for {type_name}; "
                "wildcards are not supported in a destructive-changes manifest"
            )

        if type_name == "Profile":
            profile_members.extend(m for m in members if m)
        if type_name == "CustomObject" and "*" in members:
            wildcard_objects = True

        if type_name in RISKY_TYPES:
            # A risky type in the manifest is a review flag, not a defect: a
            # release that changes sharing rules has to name SharingRules.
            findings.append(
                f"WARN {path}: manifest includes {type_name}; require explicit review and smoke tests"
            )
        if type_name in ("Flow", "Profile", "PermissionSet", "CustomObject") and "*" in members:
            findings.append(
                f"MEDIUM {path}: wildcard deployment for `{type_name}` reduces review precision"
            )

    # Check 3: Profile members alongside a CustomObject wildcard.
    if profile_members and wildcard_objects:
        findings.append(
            f"WARN {path}: manifest deploys Profile ({', '.join(sorted(profile_members))}) "
            "alongside CustomObject '*'. A retrieved profile carries field-level security only "
            "for objects in the same manifest, and a profile deploy overlays rather than "
            "replaces, so this pair silently rewrites permissions across every object in the org"
        )

    return findings


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"HIGH {path}: file not found"]
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name != "package.xml":
        return findings

    text = path.read_text(encoding="utf-8", errors="ignore")
    lower_path = str(path).lower()
    lower_name = path.name.lower()

    if lower_name == "package.xml" or lower_name.startswith("destructivechanges"):
        findings.extend(audit_package_xml(path, text))

    if "/profiles/" in lower_path or path.name.endswith(".profile-meta.xml"):
        findings.append(
            f"MEDIUM {path}: profile deployment detected; prefer permission-set-focused releases where possible"
        )

    if "/flows/" in lower_path and "<status>Active</status>" in text:
        findings.append(
            f"LOW {path}: active Flow metadata present; confirm activation timing and smoke tests"
        )

    if any(token in lower_path for token in ("connectedapp", "namedcredential", "externalcredential")):
        findings.append(
            f"HIGH {path}: integration metadata present; verify environment-specific config and rollback"
        )

    return findings


# -------------------------------------------------------------- directory-level checks

def is_manifest_file(path: Path) -> bool:
    name = path.name.lower()
    return name == "package.xml" or name.startswith("destructivechanges")


def find_manifest_files(directory: Path) -> list[Path]:
    """Every package.xml / destructiveChanges*.xml under `directory`, recursively.

    Recursion is deliberate: a build root holds one manifest per step, and a
    non-recursive scan of the root would report "no package.xml found" while
    silently ignoring all of them.
    """
    return sorted(
        candidate
        for candidate in directory.rglob("*")
        if candidate.is_file() and is_manifest_file(candidate)
    )


def audit_manifest_dir(directory: Path) -> list[str]:
    findings: list[str] = []

    if not directory.is_dir():
        return [f"ERROR {directory}: --manifest-dir is not a directory"]

    manifest_files = find_manifest_files(directory)

    for path in manifest_files:
        findings.extend(audit_package_xml(path, path.read_text(encoding="utf-8", errors="ignore")))

    # Companion-manifest checks are per directory: a destructiveChanges*.xml
    # needs its package.xml beside it, not merely somewhere in the tree.
    by_directory: dict[Path, list[Path]] = {}
    for path in manifest_files:
        by_directory.setdefault(path.parent, []).append(path)

    for parent, entries in sorted(by_directory.items()):
        package = None
        for candidate in entries:
            if candidate.name.lower() == "package.xml":
                package = candidate
                break
        destructive = [p for p in entries if p.name.lower().startswith("destructivechanges")]

        # Check 2: a destructive manifest with no companion package.xml in the same directory.
        if destructive and package is None:
            names = ", ".join(p.name for p in destructive)
            findings.append(
                f"ERROR {parent}: {names} present with no package.xml in the same directory. "
                "A destructive deploy also needs a package.xml that lists no components but "
                "declares the API version, beside the destructive manifest"
            )
        elif destructive and package is not None:
            pkg_text = package.read_text(encoding="utf-8", errors="ignore")
            if "<version>" not in pkg_text:
                findings.append(
                    f"ERROR {package}: companion package.xml for a destructive deploy declares no <version>"
                )

        for path in destructive:
            stem = path.name.lower()
            if stem not in ("destructivechanges.xml", "destructivechangespre.xml", "destructivechangespost.xml"):
                findings.append(
                    f"WARN {path}: unrecognised destructive-manifest filename; ordering is chosen by "
                    "name (destructiveChanges.xml / destructiveChangesPre.xml / destructiveChangesPost.xml)"
                )

    # Check 4: NoTestRun in a release-manifest note aimed at production. Notes are
    # found recursively too, alongside the manifests they describe.
    notes = sorted(
        candidate
        for candidate in directory.rglob("*")
        if candidate.is_file() and candidate.suffix.lower() in (".yml", ".yaml", ".json", ".md")
    )
    for path in notes:
        note = path.read_text(encoding="utf-8", errors="ignore")
        level_match = TEST_LEVEL_LINE.search(note)
        if not level_match:
            continue
        level = level_match.group(1).strip().lower()
        if level not in VALID_TEST_LEVELS:
            findings.append(
                f"WARN {path}: testLevel '{level_match.group(1)}' is not a Metadata API TestLevel value"
            )
            continue
        if level in DEV_ONLY_TEST_LEVELS:
            prod = PRODUCTION_HINTS.search(note)
            if prod:
                findings.append(
                    f"WARN {path}: release manifest sets testLevel NoTestRun with target "
                    f"'{prod.group(1)}'. NoTestRun applies only to development environments "
                    "(sandbox, Developer Edition, trial); a production deploy will not accept it"
                )
            else:
                findings.append(
                    f"WARN {path}: release manifest sets testLevel NoTestRun; confirm the target "
                    "is a development environment, not production"
                )

    if not manifest_files:
        findings.append(
            f"ERROR {directory}: no package.xml or destructive manifest found anywhere under this directory"
        )

    return findings


# ------------------------------------------------------------------------------ main

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check deployment manifests and metadata folders for release-risk indicators."
    )
    parser.add_argument(
        "--manifest-dir",
        help="Directory holding package.xml and any destructiveChanges*.xml for this release",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Manifest files or metadata directories to inspect",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on review findings (HIGH/WARN/MEDIUM/LOW) as well as ERROR/CRITICAL.",
    )
    args = parser.parse_args()

    if not args.manifest_dir and not args.paths:
        parser.error("provide --manifest-dir, one or more paths, or both")

    findings: list[str] = []
    scanned = 0

    if args.manifest_dir:
        directory = Path(args.manifest_dir)
        findings.extend(audit_manifest_dir(directory))
        if directory.is_dir():
            scanned += sum(1 for p in directory.rglob("*") if p.is_file())

    if args.paths:
        files = iter_files(args.paths)
        scanned += len(files)
        for path in files:
            findings.extend(audit_file(path))
        if not files:
            findings.append("HIGH no manifest or metadata files matched the provided paths")

    summary = (
        f"Scanned {scanned} manifest or metadata file(s); "
        f"{len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary, args.strict)


if __name__ == "__main__":
    exit_code = main()
    if exit_code:
        # An ERROR/CRITICAL finding (or any finding under --strict) — explicit
        # failure path for CI and the repo validator.
        sys.exit(1)
    sys.exit(0)
