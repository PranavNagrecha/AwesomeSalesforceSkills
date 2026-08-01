#!/usr/bin/env python3
"""Detect Scheduled-ERP-Sync anti-patterns in retrieved org metadata.

Walks an SFDX-style metadata tree (force-app/) and reports:

1. Scheduled Apex (`implements Schedulable`) classes that contain `Http`
   callout calls in the same class body — Schedulable contexts cannot
   make callouts directly (see references/gotchas.md, Gotcha 3).
2. Apex classes that perform `http.send(...)` but are not in a class
   that `implements ... Database.AllowsCallouts` — the callout will
   throw if invoked from an async context that does not declare the
   marker interface.
3. Apex classes that hardcode http(s) URLs instead of using the
   `callout:NamedCredential` pattern — token refresh and security
   posture both rely on Named Credentials.
4. Any custom field with developer name `Access_Token__c` or `Bearer_Token__c`
   on an Integration / ERP custom object — token storage in Custom Settings
   or Custom Objects is anti-pattern #4 in references/llm-anti-patterns.md.
5. Missing `ERP_Sync_Watermark__mdt` Custom Metadata Type when
   any class name matches `*Erp*Sync*` or `*Erp*Pull*` — watermark
   should live in Custom Metadata, not Custom Settings.

Stdlib only — no pip dependencies.

Usage:
    python3 check_scheduled_erp_sync_pattern.py [--root force-app/main/default]

Exit codes:
    0  no findings
    1  findings present (informational, non-blocking)
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"s": "http://soap.sforce.com/2006/04/metadata"}

SCHEDULABLE_RE = re.compile(r"\bimplements\b[^{]*\bSchedulable\b", re.IGNORECASE)
HTTP_SEND_RE = re.compile(r"\b(?:Http|new\s+Http\s*\(\s*\))\b.*?\.send\s*\(", re.IGNORECASE | re.DOTALL)
HTTP_REQUEST_RE = re.compile(r"\bnew\s+HttpRequest\s*\(", re.IGNORECASE)
ALLOWS_CALLOUTS_RE = re.compile(r"\bDatabase\.AllowsCallouts\b", re.IGNORECASE)
HARDCODED_URL_RE = re.compile(r"setEndpoint\s*\(\s*['\"]https?://", re.IGNORECASE)
NAMED_CRED_RE = re.compile(r"setEndpoint\s*\(\s*['\"]callout:", re.IGNORECASE)
TOKEN_FIELD_RE = re.compile(r"^(Access_Token|Bearer_Token|Refresh_Token|Auth_Token)__c\.field-meta\.xml$", re.IGNORECASE)
ERP_CLASS_RE = re.compile(r"Erp.*?(Sync|Pull|Push|Poll)", re.IGNORECASE)


def find_apex_files(root: Path) -> list[Path]:
    apex_files: list[Path] = []
    for sub in ("classes", "triggers"):
        d = root / sub
        if not d.exists():
            continue
        for ext in ("*.cls", "*.trigger"):
            apex_files.extend(d.rglob(ext))
    return apex_files


def schedulable_with_callout(apex_files: list[Path]) -> list[tuple[Path, str]]:
    findings: list[tuple[Path, str]] = []
    for fp in apex_files:
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not SCHEDULABLE_RE.search(text):
            continue
        if HTTP_SEND_RE.search(text) or HTTP_REQUEST_RE.search(text):
            findings.append((fp, "implements Schedulable but contains HTTP callout — move callout to a Queueable"))
    return findings


def callout_without_marker(apex_files: list[Path]) -> list[tuple[Path, str]]:
    findings: list[tuple[Path, str]] = []
    for fp in apex_files:
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not HTTP_SEND_RE.search(text):
            continue
        # If the file makes a callout but does not declare AllowsCallouts,
        # it may be invoked from an async context that requires it.
        if not ALLOWS_CALLOUTS_RE.search(text):
            findings.append((fp, "callout present but class does not implement Database.AllowsCallouts — required for async callouts"))
    return findings


def hardcoded_endpoint(apex_files: list[Path]) -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    for fp in apex_files:
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines()):
            if HARDCODED_URL_RE.search(line):
                findings.append((fp, i + 1, line.strip()[:120]))
    return findings


def token_storage_fields(root: Path) -> list[Path]:
    findings: list[Path] = []
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return findings
    for obj_dir in objects_dir.iterdir():
        if not obj_dir.is_dir():
            continue
        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            continue
        for field_xml in fields_dir.glob("*.field-meta.xml"):
            if TOKEN_FIELD_RE.match(field_xml.name):
                findings.append(field_xml)
    return findings


def watermark_cmd_present(root: Path) -> bool:
    """Return True if a CMD type that looks like a sync-watermark exists."""
    cmd_dir = root / "customMetadata"
    if cmd_dir.exists():
        for fp in cmd_dir.rglob("*.md-meta.xml"):
            if "watermark" in fp.name.lower() or "sync" in fp.name.lower():
                return True
    objects_dir = root / "objects"
    if objects_dir.exists():
        for obj_dir in objects_dir.iterdir():
            if obj_dir.name.endswith("__mdt") and (
                "watermark" in obj_dir.name.lower() or "sync" in obj_dir.name.lower()
            ):
                return True
    return False


def has_erp_sync_class(apex_files: list[Path]) -> bool:
    for fp in apex_files:
        if ERP_CLASS_RE.search(fp.stem):
            return True
    return False


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="force-app/main/default")
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"metadata root not found: {root}", file=sys.stderr)
        return 0

    apex_files = find_apex_files(root)
    findings_count = 0

    sched_findings = schedulable_with_callout(apex_files)
    if sched_findings:
        print("\n## Schedulable classes containing HTTP callouts (will throw at runtime)")
        for fp, msg in sched_findings:
            print(f"  - {fp.relative_to(root)}: {msg}")
        findings_count += len(sched_findings)

    marker_findings = callout_without_marker(apex_files)
    # Filter out the schedulable matches to avoid double-reporting
    sched_paths = {fp for fp, _ in sched_findings}
    marker_findings = [f for f in marker_findings if f[0] not in sched_paths]
    if marker_findings:
        print("\n## Apex callouts without Database.AllowsCallouts marker")
        for fp, msg in marker_findings:
            print(f"  - {fp.relative_to(root)}: {msg}")
        findings_count += len(marker_findings)

    url_findings = hardcoded_endpoint(apex_files)
    if url_findings:
        print("\n## Hardcoded http(s) URLs (use callout:NamedCredential instead)")
        for fp, ln, snippet in url_findings:
            print(f"  - {fp.relative_to(root)}:{ln}: {snippet}")
        findings_count += len(url_findings)

    token_findings = token_storage_fields(root)
    if token_findings:
        print("\n## Custom fields storing OAuth tokens (use Named/External Credentials instead)")
        for fp in token_findings:
            print(f"  - {fp.relative_to(root)}")
        findings_count += len(token_findings)

    if has_erp_sync_class(apex_files) and not watermark_cmd_present(root):
        print("\n## Missing watermark Custom Metadata Type")
        print("  - ERP sync classes detected but no Custom Metadata Type matching *Sync*Watermark* found.")
        print("    Watermarks should live in CMD, not Custom Settings (survives sandbox refresh, deployable).")
        findings_count += 1

    if findings_count == 0:
        print("No Scheduled-ERP-Sync anti-patterns detected in this metadata tree.")
        return 0

    print(f"\nTotal findings: {findings_count}")
    print("Refer to the skill workflow + references/gotchas.md for remediation steps.")
    print(f"ERROR: {findings_count} scheduled-ERP-sync anti-pattern(s); see report above.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
