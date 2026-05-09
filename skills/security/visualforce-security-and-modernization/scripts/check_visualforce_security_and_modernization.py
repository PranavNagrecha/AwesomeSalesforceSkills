#!/usr/bin/env python3
"""Checker script for the visualforce-security-and-modernization skill.

Scans Salesforce SFDX metadata for the security findings that drive the
retire-vs-harden-vs-leave-alone decision for legacy Visualforce pages:

  - <apex:page csrfProtection="false"> — CSRF protection disabled.
  - <apex:page action="{!method}"> — page-action attribute that may trigger
    GET-side state changes; requires manual review of the action method.
  - Apex controllers without `with sharing` / `without sharing` / `inherited
    sharing` — sharing keyword is not declared (defaults to without sharing
    in older orgs, ambiguous in any case).
  - Getters returning an sObject from a SOQL query without WITH USER_MODE or
    WITH SECURITY_ENFORCED — FLS is not enforced for the rendered page.
  - <apex:outputText value="{!record.Field}"/> bound to an sObject field —
    outputText does not enforce FLS; should be outputField.
  - <apex:dynamicComponent componentValue="..."/> — dynamic-component branch
    is hard to security-review and is a strong rewrite candidate.

Uses stdlib only — no pip dependencies.

Exit codes:
  0  — no issues found
  1  — issues reported

Usage:
    python3 check_visualforce_security_and_modernization.py [--manifest-dir DIR]
    python3 check_visualforce_security_and_modernization.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# CSRF protection explicitly disabled on the apex:page element
_CSRF_DISABLED = re.compile(
    r'<apex:page\b[^>]*\bcsrfProtection\s*=\s*["\']false["\']',
    re.IGNORECASE | re.DOTALL,
)

# apex:page with an action attribute (state change risk on GET)
_PAGE_ACTION_ATTR = re.compile(
    r'<apex:page\b[^>]*\baction\s*=\s*["\']\s*\{\s*!\s*([A-Za-z_][\w\.]*)\s*\}\s*["\']',
    re.IGNORECASE | re.DOTALL,
)

# apex:dynamicComponent — rewrite candidate
_DYNAMIC_COMPONENT = re.compile(
    r'<apex:dynamicComponent\b',
    re.IGNORECASE,
)

# apex:outputText bound to a record field path (e.g. {!account.Salary__c})
# Heuristic: value binding has a dot and references something other than a
# pure controller variable. False positives are acceptable; this surfaces
# pages for manual review.
_OUTPUT_TEXT_FIELD = re.compile(
    r'<apex:outputText\b[^>]*\bvalue\s*=\s*["\']\s*\{\s*!\s*([A-Za-z_]\w*\.[A-Za-z_]\w*(?:__c)?)\s*\}\s*["\']',
    re.IGNORECASE | re.DOTALL,
)

# Apex class declaration with sharing keyword
_CLASS_WITH_SHARING = re.compile(
    r'\b(public|global|private)\s+(with\s+sharing|without\s+sharing|inherited\s+sharing)\s+class\b',
    re.IGNORECASE,
)

# Apex class declaration without any sharing keyword (heuristic — first match)
_CLASS_DECL = re.compile(
    r'\b(public|global|private)\s+(?:abstract\s+|virtual\s+|with\s+sharing\s+|without\s+sharing\s+|inherited\s+sharing\s+)*class\s+(\w+)',
    re.IGNORECASE,
)

# SOQL query — used to detect missing enforcement clause
_SOQL_QUERY = re.compile(
    r'\[\s*SELECT\b.*?\]',
    re.DOTALL | re.IGNORECASE,
)

_SOQL_USER_MODE = re.compile(
    r'\bWITH\s+(USER_MODE|SECURITY_ENFORCED)\b',
    re.IGNORECASE,
)

# Controller hint — class references ApexPages or has page-controller markers
_VF_CONTROLLER_HINT = re.compile(
    r'\bApexPages\b|\bApexPages\.StandardController\b|\bApexPages\.standardController\b',
    re.IGNORECASE,
)

# Heuristic: getter that returns an sObject (custom or standard with __c suffix on field path)
# Matches "public SomeObject__c getX()" or "public Account getX()" patterns
_GETTER_SOBJECT = re.compile(
    r'\bpublic\s+([A-Z]\w*(?:__c)?)\s+get[A-Z]\w*\s*\(\s*\)',
)


# Common standard sObject names — used to check whether a getter return type
# is likely an sObject. Includes the most common standard objects plus any
# custom-suffix __c. Conservative list.
_STANDARD_SOBJECTS = {
    "Account", "Contact", "Lead", "Opportunity", "Case", "User", "Task", "Event",
    "Campaign", "CampaignMember", "Order", "Asset", "Contract", "Product2",
    "PricebookEntry", "Quote", "QuoteLineItem", "OpportunityLineItem",
    "FeedItem", "Attachment", "Document", "Note", "ContentVersion",
    "EmailMessage", "Group", "Profile", "PermissionSet", "PermissionSetAssignment",
    "Site", "Network", "Idea", "Solution", "Knowledge__kav", "Article__kav",
}


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def _is_likely_sobject_type(type_name: str) -> bool:
    """Return True if the type name looks like an sObject (custom suffix __c or known standard)."""
    if type_name.endswith("__c") or type_name.endswith("__kav"):
        return True
    if type_name in _STANDARD_SOBJECTS:
        return True
    return False


def check_visualforce_pages(pages_dir: Path) -> list[str]:
    """Scan .page files for CSRF, action, dynamicComponent, and outputText findings."""
    issues: list[str] = []
    page_files = list(pages_dir.rglob("*.page"))

    for page_file in page_files:
        try:
            markup = page_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if _CSRF_DISABLED.search(markup):
            issues.append(
                f"[CSRF-DISABLED] {page_file.name}: "
                f"<apex:page csrfProtection=\"false\"> is set. "
                f"Re-enable CSRF protection unless there is a written security-review "
                f"justification. See SKILL.md Concept 1."
            )

        action_match = _PAGE_ACTION_ATTR.search(markup)
        if action_match:
            method_name = action_match.group(1)
            issues.append(
                f"[PAGE-ACTION-DML-RISK] {page_file.name}: "
                f"<apex:page action=\"{{!{method_name}}}\"> fires on every GET. "
                f"Verify {method_name}() performs only read-only data loading. "
                f"DML in page actions is CSRF-vulnerable regardless of the form token."
            )

        for match in _DYNAMIC_COMPONENT.finditer(markup):
            issues.append(
                f"[DYNAMIC-COMPONENT] {page_file.name}: "
                f"Found <apex:dynamicComponent> — strong rewrite-to-LWC candidate. "
                f"Dynamic-component branches are hard to reason about for security review."
            )

        for match in _OUTPUT_TEXT_FIELD.finditer(markup):
            binding = match.group(1)
            issues.append(
                f"[OUTPUTTEXT-SOBJECT-FIELD] {page_file.name}: "
                f"<apex:outputText value=\"{{!{binding}}}\"/> binds an sObject field path. "
                f"<apex:outputText> does NOT enforce FLS. Replace with <apex:outputField>."
            )

    return issues


def check_apex_controllers(apex_dir: Path) -> list[str]:
    """Scan .cls files for sharing-keyword absence, FLS-unenforced SOQL, and risky getters."""
    issues: list[str] = []
    cls_files = list(apex_dir.rglob("*.cls"))

    for cls_file in cls_files:
        try:
            source = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        is_vf_controller = bool(_VF_CONTROLLER_HINT.search(source))

        # Check sharing keyword
        if is_vf_controller:
            class_decl = _CLASS_DECL.search(source)
            if class_decl and not _CLASS_WITH_SHARING.search(source):
                issues.append(
                    f"[NO-SHARING-KEYWORD] {cls_file.name}: "
                    f"VF controller class {class_decl.group(2)!r} declares no sharing keyword "
                    f"(with sharing / without sharing / inherited sharing). "
                    f"Default depends on context — explicitly declare `with sharing` for record-level "
                    f"enforcement. Note: this does NOT cover FLS — pair with WITH USER_MODE on SOQL."
                )

        # Check SOQL queries lacking enforcement
        for match in _SOQL_QUERY.finditer(source):
            query_text = match.group(0)
            if not _SOQL_USER_MODE.search(query_text):
                snippet = query_text[:80].strip().replace("\n", " ")
                issues.append(
                    f"[SOQL-NO-USER-MODE] {cls_file.name}: "
                    f"SOQL query missing WITH USER_MODE or WITH SECURITY_ENFORCED — "
                    f"snippet: {snippet!r}. FLS will not be enforced; pages binding "
                    f"this query's result via <apex:outputField> will still expose "
                    f"FLS-restricted fields."
                )

        # Check for getters returning sObjects without enforcement nearby
        if is_vf_controller:
            for match in _GETTER_SOBJECT.finditer(source):
                return_type = match.group(1)
                if not _is_likely_sobject_type(return_type):
                    continue
                # Locate the method body and check whether it contains a USER_MODE SOQL
                method_start = match.end()
                # Look for the matching `}` — naive but adequate for a heuristic
                brace_depth = 0
                method_end = method_start
                in_method = False
                for i, ch in enumerate(source[method_start:], start=method_start):
                    if ch == "{":
                        brace_depth += 1
                        in_method = True
                    elif ch == "}":
                        brace_depth -= 1
                        if in_method and brace_depth == 0:
                            method_end = i + 1
                            break
                method_body = source[method_start:method_end]
                if _SOQL_QUERY.search(method_body) and not _SOQL_USER_MODE.search(method_body):
                    issues.append(
                        f"[GETTER-SOBJECT-NO-FLS] {cls_file.name}: "
                        f"Getter returning sObject type {return_type!r} runs SOQL "
                        f"without WITH USER_MODE. Pages binding this getter via "
                        f"<apex:outputField> will not have FLS enforced."
                    )

    return issues


def check_visualforce_security_and_modernization(manifest_dir: Path) -> list[str]:
    """Run all checks across the SFDX metadata layout. Return aggregated issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Common SFDX layouts
    page_dirs = [
        manifest_dir / "force-app" / "main" / "default" / "pages",
        manifest_dir / "src" / "pages",
        manifest_dir / "pages",
        manifest_dir,
    ]
    apex_dirs = [
        manifest_dir / "force-app" / "main" / "default" / "classes",
        manifest_dir / "src" / "classes",
        manifest_dir / "classes",
        manifest_dir,
    ]

    pages_checked = False
    for d in page_dirs:
        if d.exists() and list(d.rglob("*.page")):
            issues.extend(check_visualforce_pages(d))
            pages_checked = True
            break
    if not pages_checked:
        # No .page files anywhere; that's fine, may be apex-only inventory
        pass

    apex_checked = False
    for d in apex_dirs:
        if d.exists() and list(d.rglob("*.cls")):
            issues.extend(check_apex_controllers(d))
            apex_checked = True
            break
    if not apex_checked:
        # No .cls files anywhere
        pass

    if not pages_checked and not apex_checked:
        issues.append(
            f"No .page or .cls files found under {manifest_dir} — "
            f"verify the --manifest-dir points at SFDX metadata root."
        )

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce SFDX metadata for Visualforce security and "
            "modernization findings: CSRF disabled, page-action DML risk, "
            "missing FLS enforcement on getters and SOQL, dynamic components, "
            "and outputText bindings to sObject fields."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_visualforce_security_and_modernization(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
