#!/usr/bin/env python3
"""Static checker for subscriber-side managed package install hygiene.

Scans a Salesforce metadata source tree (`force-app/...`) for signals that
a subscriber org has the install posture this skill recommends:

- subscriber Apex / Flow references to managed package namespaces — useful
  for the pre-uninstall reference audit
- absence of subscriber-owned Permission Set Groups that wrap a packaged
  Permission Set (a signal that grants are baked into profiles)
- profiles that explicitly grant field-level access to namespaced fields
  (a signal that "Install for All Users" was used)
- packaged Custom Objects that contain subscriber-added fields with
  collision-prone names (subscriber added `Status__c` on a `pkg__Foo__c`
  object, which collides on upgrade)

Stdlib only. Regex / XML parsing.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS_PREFIX_RE = re.compile(r"\b([a-z][a-z0-9_]{0,14})__([A-Z][A-Za-z0-9_]+)\b")
# Salesforce managed namespace pattern: 1-15 lowercase alphanumeric/underscore + '__'
# Followed by a CamelCase or snake_case identifier (Apex symbol / API name).
PROFILE_NS = "{http://soap.sforce.com/2006/04/metadata}"
COMMON_BUILTIN_PREFIXES = {
    # Standard Salesforce-shipped namespace prefixes that aren't third-party packages.
    "force", "lightning", "ui", "schema", "system", "apex", "auraenabled",
    "salesforce", "test", "console",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit subscriber-side managed package install hygiene.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current directory).",
    )
    return parser.parse_args()


def force_app_root(manifest_dir: Path) -> Path | None:
    candidate = manifest_dir / "force-app"
    if candidate.exists():
        return candidate
    return None


def find_namespace_refs_in_apex(root: Path) -> dict[str, set[str]]:
    """Return mapping of namespace -> set of files that reference it."""
    refs: dict[str, set[str]] = {}
    for ext in ("*.cls", "*.trigger"):
        for path in root.rglob(ext):
            # Skip files inside a managed-package install directory itself.
            if "installedPackages" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for match in NS_PREFIX_RE.finditer(text):
                ns = match.group(1).lower()
                if ns in COMMON_BUILTIN_PREFIXES:
                    continue
                refs.setdefault(ns, set()).add(str(path))
    return refs


def find_namespace_refs_in_flows(root: Path) -> dict[str, set[str]]:
    """Return mapping of namespace -> set of Flow files that reference it."""
    refs: dict[str, set[str]] = {}
    for path in root.rglob("*.flow-meta.xml"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for match in NS_PREFIX_RE.finditer(text):
            ns = match.group(1).lower()
            if ns in COMMON_BUILTIN_PREFIXES:
                continue
            refs.setdefault(ns, set()).add(str(path))
    return refs


def profiles_granting_namespaced_field_access(root: Path) -> list[tuple[str, str]]:
    """Return list of (profile_path, namespaced_field) where a profile grants access."""
    findings: list[tuple[str, str]] = []
    for path in root.rglob("*.profile-meta.xml"):
        try:
            tree = ET.parse(path)
        except (ET.ParseError, OSError):
            continue
        root_el = tree.getroot()
        for fp in root_el.findall(f"{PROFILE_NS}fieldPermissions"):
            field_el = fp.find(f"{PROFILE_NS}field")
            editable_el = fp.find(f"{PROFILE_NS}editable")
            readable_el = fp.find(f"{PROFILE_NS}readable")
            field_text = field_el.text if field_el is not None else None
            if not field_text:
                continue
            granted = False
            for el in (editable_el, readable_el):
                if el is not None and (el.text or "").strip().lower() == "true":
                    granted = True
                    break
            if not granted:
                continue
            # Look for a namespace prefix on object or field.
            for match in NS_PREFIX_RE.finditer(field_text):
                ns = match.group(1).lower()
                if ns in COMMON_BUILTIN_PREFIXES:
                    continue
                findings.append((str(path), field_text))
                break
    return findings


def subscriber_fields_on_packaged_objects(root: Path) -> list[tuple[str, str]]:
    """Return (object_dir, subscriber_field_api) pairs where subscriber fields
    sit on a packaged object — collision risk on package upgrade."""
    findings: list[tuple[str, str]] = []
    objects_root = root / "main" / "default" / "objects"
    if not objects_root.exists():
        # SFDX projects may use a different layout — fall back to any objects/ dir.
        candidates = list(root.rglob("objects"))
        objects_root = candidates[0] if candidates else None
    if not objects_root:
        return findings
    for obj_dir in objects_root.iterdir():
        if not obj_dir.is_dir():
            continue
        name = obj_dir.name
        # Packaged object: namespace_prefix__name__c style
        if "__" not in name:
            continue
        # Strip trailing __c; check if there are two double-underscores total.
        # Packaged object pattern: ns__name__c (so the dir name has two "__" separators).
        if name.count("__") < 2:
            continue
        prefix = name.split("__", 1)[0].lower()
        if prefix in COMMON_BUILTIN_PREFIXES:
            continue
        # Look for fields/*.field-meta.xml that lack a namespace prefix.
        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            continue
        for field_file in fields_dir.glob("*.field-meta.xml"):
            field_name = field_file.stem.replace(".field-meta", "")
            # Subscriber-added fields on a packaged object will NOT have a namespace
            # prefix (only the publisher can ship namespaced fields). If the file
            # name starts with a lowercase namespace + "__" the field is packaged.
            if "__" in field_name:
                lead = field_name.split("__", 1)[0]
                if lead and lead[0].islower() and lead.isalnum():
                    # Could be packaged field — skip.
                    continue
            findings.append((name, field_name))
    return findings


def permission_set_groups(root: Path) -> set[str]:
    """Return set of subscriber-owned Permission Set Group developer names."""
    out: set[str] = set()
    for path in root.rglob("*.permissionsetgroup-meta.xml"):
        out.add(path.stem.replace(".permissionsetgroup-meta", ""))
    return out


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    fa = force_app_root(root)
    if fa is None:
        print(f"ERROR: no force-app/ directory under {root}", file=sys.stderr)
        return 1

    apex_refs = find_namespace_refs_in_apex(fa)
    flow_refs = find_namespace_refs_in_flows(fa)
    profile_findings = profiles_granting_namespaced_field_access(fa)
    collision_findings = subscriber_fields_on_packaged_objects(fa)
    psgs = permission_set_groups(fa)

    issues: list[str] = []

    # Combine apex + flow references for the namespace audit.
    all_refs: dict[str, set[str]] = {}
    for src in (apex_refs, flow_refs):
        for ns, files in src.items():
            all_refs.setdefault(ns, set()).update(files)

    if all_refs:
        for ns, files in sorted(all_refs.items()):
            sample = sorted(files)[:3]
            issues.append(
                f"subscriber code references managed namespace `{ns}__` "
                f"in {len(files)} file(s): {', '.join(sample)}"
                f"{' (and more)' if len(files) > len(sample) else ''}"
                " — audit each reference before any uninstall"
            )

    if profile_findings:
        # De-dup by profile.
        by_profile: dict[str, set[str]] = {}
        for prof, field in profile_findings:
            by_profile.setdefault(prof, set()).add(field)
        for prof, fields in sorted(by_profile.items()):
            sample = sorted(fields)[:3]
            issues.append(
                f"profile `{prof}` grants access to namespaced field(s) "
                f"{', '.join(sample)}{' (and more)' if len(fields) > len(sample) else ''}"
                " — likely \"Install for All Users\"; consider migrating to Permission Set Group"
            )

    if collision_findings:
        by_obj: dict[str, set[str]] = {}
        for obj, field in collision_findings:
            by_obj.setdefault(obj, set()).add(field)
        for obj, fields in sorted(by_obj.items()):
            sample = sorted(fields)[:3]
            issues.append(
                f"packaged object `{obj}` has subscriber-added field(s) "
                f"{', '.join(sample)}{' (and more)' if len(fields) > len(sample) else ''}"
                " — verify no API-name collision against publisher's next upgrade"
            )

    if all_refs and not psgs:
        issues.append(
            "subscriber code references managed namespaces but no "
            "subscriber-owned Permission Set Groups exist — feature access may "
            "be granted via profile baseline; build Permission Set Groups to "
            "make grants reversible"
        )

    if not issues:
        print("[managed-package-installation-and-upgrade] no install-hygiene issues found")
        return 0

    for i in issues:
        print(f"WARN: {i}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
