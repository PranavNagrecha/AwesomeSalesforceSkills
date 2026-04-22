#!/usr/bin/env python3
"""Checker script for Tenant Isolation Patterns skill.

Scans metadata for tenant-isolation anti-patterns:
- Apex classes with hard-coded tenant-name conditionals
- OWD Public Read/Write on objects that carry a Tenant__c field
- Public Groups named like global catch-alls

Usage:
    python3 check_tenant_isolation_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TENANT_CONDITIONAL_PAT = re.compile(
    r"(?i)(if|when|else\s+if)\s*\(\s*tenant(_id|Name|Key)?\s*(==|\.equals|===)\s*['\"]"
)
GLOBAL_GROUP_PAT = re.compile(
    r"(?i)<fullName>(all_?users|global_?group|everyone|all_?tenants)</fullName>"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check tenant isolation configuration for issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def check_tenant_conditionals(root: Path) -> list[str]:
    issues: list[str] = []
    for sub in ("classes", "triggers"):
        base = root / sub
        if not base.exists():
            continue
        for path in base.rglob("*.cls"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if TENANT_CONDITIONAL_PAT.search(text):
                issues.append(
                    f"{path.relative_to(root)}: tenant-name conditional; move to custom metadata feature flags"
                )
    return issues


def check_owd_on_tenant_objects(root: Path) -> list[str]:
    issues: list[str] = []
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return issues
    for obj_dir in objects_dir.iterdir():
        if not obj_dir.is_dir():
            continue
        fields_dir = obj_dir / "fields"
        has_tenant_field = False
        if fields_dir.exists():
            for field in fields_dir.glob("*.field-meta.xml"):
                if "Tenant__c" in field.name or "TenantId__c" in field.name:
                    has_tenant_field = True
                    break
        if not has_tenant_field:
            continue
        object_xml = obj_dir / f"{obj_dir.name}.object-meta.xml"
        if not object_xml.exists():
            continue
        try:
            text = object_xml.read_text(encoding="utf-8")
        except OSError:
            continue
        if re.search(r"<sharingModel>(Read|ReadWrite)</sharingModel>", text):
            issues.append(
                f"{object_xml.relative_to(root)}: tenant-scoped object with public OWD; isolation at risk"
            )
    return issues


def check_global_groups(root: Path) -> list[str]:
    issues: list[str] = []
    groups_dir = root / "groups"
    if not groups_dir.exists():
        return issues
    for path in groups_dir.rglob("*.group-meta.xml"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if GLOBAL_GROUP_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: catch-all public group suggests cross-tenant sharing"
            )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_tenant_conditionals(manifest_dir))
    issues.extend(check_owd_on_tenant_objects(manifest_dir))
    issues.extend(check_global_groups(manifest_dir))

    if not issues:
        print("No tenant isolation anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
