#!/usr/bin/env python3
"""Checker script for ISV License Management and Trialforce skill.

Audits a Salesforce DX source tree (force-app/) for common ISV-licensing issues:
- Custom Settings / Custom Objects whose name suggests hand-rolled license enforcement
  (LicenseConfig, Subscription, Trial_Settings, etc.) — should use the LMA instead.
- Apex calls to FeatureManagement.checkPackage*Value with only a name argument
  (missing the namespace argument), which silently mis-resolves in subscriber context.
- FeatureParameter*-meta.xml files missing dataflowDirection or defaultValue.
- Apex code that calls setPackage*Value followed by checkPackage*Value of the same FP
  in the same class (treating FP propagation as synchronous).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_isv_license_management_and_trialforce.py [--manifest-dir force-app]
    python3 check_isv_license_management_and_trialforce.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Custom Setting / Custom Object names that suggest hand-rolled license enforcement.
SUSPICIOUS_LICENSE_OBJECT_NAMES = re.compile(
    r"^(license[_-]?(config|settings?|state|enforcement|guard|info)?"
    r"|subscription[_-]?(config|state|info)?"
    r"|trial[_-]?(config|settings?|state|info)?"
    r"|app[_-]?license)\.object(-meta\.xml)?$",
    re.IGNORECASE,
)

# Apex one-arg checkPackage*Value: the namespace argument is missing.
ONE_ARG_CHECK_PACKAGE = re.compile(
    r"FeatureManagement\.checkPackage(Boolean|Date|Integer)Value\s*\(\s*"
    r"(?:'[^']*'|\"[^\"]*\")\s*\)",
    re.IGNORECASE,
)

# Apex set/check pair on the same FP key in the same file (synchronous-FP assumption).
SET_PACKAGE_RE = re.compile(
    r"FeatureManagement\.setPackage(Boolean|Date|Integer)Value\s*\(\s*"
    r"(?:'([^']+)'|\"([^\"]+)\")",
    re.IGNORECASE,
)
CHECK_PACKAGE_RE = re.compile(
    r"FeatureManagement\.checkPackage(Boolean|Date|Integer)Value\s*\([^)]*"
    r"(?:'([^']+)'|\"([^\"]+)\")",
    re.IGNORECASE,
)

NAMESPACE_PREFIX = "{http://soap.sforce.com/2006/04/metadata}"

FEATURE_PARAM_FILE_RE = re.compile(
    r"\.featureParameter(Boolean|Date|Integer)-meta\.xml$",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Salesforce metadata for ISV License Management and Trialforce issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default="force-app",
        help="Root directory of the Salesforce metadata (default: force-app).",
    )
    return parser.parse_args()


def find_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    if not root.exists():
        return []
    out: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and any(str(path).endswith(s) for s in suffixes):
            out.append(path)
    return out


def check_suspicious_license_objects(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.object-meta.xml"):
        if SUSPICIOUS_LICENSE_OBJECT_NAMES.search(path.name):
            issues.append(
                f"WARN {path}: object name suggests hand-rolled license enforcement; "
                "the LMA (sfLma__License__c) is the only enforceable surface — see "
                "references/llm-anti-patterns.md anti-pattern #1."
            )
    for path in root.rglob("*.objectSettings-meta.xml"):
        if SUSPICIOUS_LICENSE_OBJECT_NAMES.search(path.name):
            issues.append(
                f"WARN {path}: settings name suggests hand-rolled license enforcement."
            )
    return issues


def check_apex_namespace_omission(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "global" not in text and "managed" not in str(path).lower():
            continue
        for match in ONE_ARG_CHECK_PACKAGE.finditer(text):
            line_num = text[: match.start()].count("\n") + 1
            issues.append(
                f"HIGH {path}:{line_num}: FeatureManagement.checkPackage*Value called "
                "with only one string argument; pass the package namespace explicitly "
                "as the first argument when this class can be invoked from subscriber "
                "Apex (see anti-pattern #3)."
            )
    return issues


def check_synchronous_fp_assumption(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        set_keys: set[str] = set()
        for m in SET_PACKAGE_RE.finditer(text):
            key = m.group(2) or m.group(3)
            if key:
                set_keys.add(key)
        if not set_keys:
            continue
        for m in CHECK_PACKAGE_RE.finditer(text):
            key = m.group(2) or m.group(3)
            if key and key in set_keys:
                line_num = text[: m.start()].count("\n") + 1
                issues.append(
                    f"HIGH {path}:{line_num}: setPackage*Value and checkPackage*Value "
                    f"on FP '{key}' in the same class — propagation is asynchronous; "
                    "the read will return the pre-write value (see anti-pattern #5)."
                )
    return issues


def check_feature_parameter_metadata(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.featureParameter*-meta.xml"):
        if not FEATURE_PARAM_FILE_RE.search(path.name):
            continue
        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            issues.append(f"WARN {path}: cannot parse XML ({exc})")
            continue
        root_el = tree.getroot()
        direction = root_el.find(f"{NAMESPACE_PREFIX}dataflowDirection")
        if direction is None or not (direction.text or "").strip():
            issues.append(
                f"HIGH {path}: Feature Parameter missing <dataflowDirection> — must be "
                "either LmoToSubscriber or SubscriberToLmo."
            )
        elif (direction.text or "").strip() not in {"LmoToSubscriber", "SubscriberToLmo"}:
            issues.append(
                f"HIGH {path}: <dataflowDirection> has invalid value '{direction.text}'; "
                "must be exactly LmoToSubscriber or SubscriberToLmo."
            )
        default = root_el.find(f"{NAMESPACE_PREFIX}defaultValue")
        if default is None or default.text is None or not default.text.strip():
            issues.append(
                f"WARN {path}: Feature Parameter missing <defaultValue>; subscribers "
                "without a propagated value will see null on read — set an explicit default."
            )
    return issues


def check_isv_license_management_and_trialforce(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues
    issues.extend(check_suspicious_license_objects(manifest_dir))
    issues.extend(check_apex_namespace_omission(manifest_dir))
    issues.extend(check_synchronous_fp_assumption(manifest_dir))
    issues.extend(check_feature_parameter_metadata(manifest_dir))
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_isv_license_management_and_trialforce(manifest_dir)

    if not issues:
        print(f"No issues found under {manifest_dir}.")
        return 0

    for issue in issues:
        print(issue, file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
