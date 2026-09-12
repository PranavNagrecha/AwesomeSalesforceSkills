#!/usr/bin/env python3
"""Checker script for Assignment Rules skill.

Inspects Salesforce metadata in SFDX source format or retrieved XML to detect
common assignment rule anti-patterns documented in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_assignment_rules.py [--manifest-dir path/to/metadata]

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Assignment Rules metadata for common anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce project or retrieved metadata (default: current directory).",
    )
    return parser.parse_args()


def find_assignment_rule_files(root: Path) -> list[Path]:
    """Return all .assignmentRules-meta.xml files under root."""
    results = list(root.rglob("*.assignmentRules-meta.xml"))
    # Also handle retrieved metadata layout (assignmentRules/ folder)
    for candidate in root.rglob("*.assignmentRules"):
        if candidate.is_file():
            results.append(candidate)
    return results


def find_auto_response_rule_files(root: Path) -> list[Path]:
    """Return all .autoResponseRules-meta.xml files under root (source and mdapi layouts)."""
    results = list(root.rglob("*.autoResponseRules-meta.xml"))
    for candidate in root.rglob("*.autoResponseRules"):
        if candidate.is_file():
            results.append(candidate)
    return results


SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def _find(parent: ET.Element, name: str) -> ET.Element | None:
    """Find a direct child by name in namespaced or bare XML.

    ``a or b`` must not be used here: an Element with no children is falsy,
    so ``rule.find(ns) or rule.find(bare)`` silently discards a found leaf and
    made every namespaced rule look inactive and unnamed (fail-open).
    """
    el = parent.find(_tag(name))
    return el if el is not None else parent.find(name)



def check_rule_file(path: Path) -> list[str]:
    """Parse one assignment rule metadata file and return issues."""
    issues: list[str] = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [f"{path.name}: XML parse error — {exc}"]

    root = tree.getroot()
    # Handle both namespaced and bare XML
    rules = root.findall(_tag("assignmentRule")) or root.findall("assignmentRule")

    active_rules: list[str] = []
    for rule in rules:
        name_el = _find(rule, "fullName")
        active_el = _find(rule, "active")
        rule_name = name_el.text if name_el is not None else "<unnamed>"
        is_active = (active_el is not None and active_el.text == "true")

        if is_active:
            active_rules.append(rule_name)

        entries = rule.findall(_tag("ruleEntry")) or rule.findall("ruleEntry")

        if is_active and not entries:
            issues.append(
                f"{path.name} / rule '{rule_name}': active rule has no rule entries — "
                "no records will be routed."
            )
            continue

        # Check for a catch-all entry (entry with no criteriaItems)
        has_catch_all = False
        for entry in entries:
            criteria_items = (
                entry.findall(_tag("criteriaItems")) or entry.findall("criteriaItems")
            )
            criteria_filter = _find(entry, "criteriaFilterType")
            is_catch_all = (
                len(criteria_items) == 0
                and (criteria_filter is None or criteria_filter.text in (None, "", "AllCriteriaTrue"))
            )
            if is_catch_all:
                has_catch_all = True

        if is_active and not has_catch_all:
            issues.append(
                f"{path.name} / rule '{rule_name}': no catch-all entry found — "
                "records that match no criteria will not be routed by this rule "
                "(they go to the Default Lead/Case Owner). "
                "Add a final entry with no criteria to make the fallback explicit."
            )

        # Warn if entry count is approaching the 3,000-entry limit
        if len(entries) > 2500:
            issues.append(
                f"{path.name} / rule '{rule_name}': {len(entries)} rule entries — "
                "approaching the 3,000-entry platform limit. Consider consolidating criteria."
            )

        # Check for entries that assign to the same target consecutively
        # (usually means a duplicate or copy-paste error)
        targets = []
        for entry in entries:
            assigned_to = _find(entry, "assignedTo")
            targets.append(assigned_to.text if assigned_to is not None else None)

        seen: set[str | None] = set()
        for t in targets:
            if t and t in seen:
                issues.append(
                    f"{path.name} / rule '{rule_name}': target '{t}' appears in "
                    "multiple rule entries. Verify this is intentional and not a "
                    "copy-paste error."
                )
                break  # Report once per rule to avoid noise
            if t:
                seen.add(t)

    # Multiple active rules for same object would violate the one-active-rule limit,
    # but metadata typically stores only one rule per file. Flag if multiple active found.
    if len(active_rules) > 1:
        issues.append(
            f"{path.name}: multiple rules marked active: {active_rules}. "
            "Salesforce enforces only one active rule per object. "
            "Review metadata before deploying — deployment may succeed but behavior will be unpredictable."
        )

    return issues


def find_routing_addresses(root: Path) -> set[str]:
    """Collect lowercased Email-to-Case routing emailAddress values found anywhere
    under root (source layout `settings/Case.settings-meta.xml` or mdapi layout
    `settings/Case.settings`; searched tree-wide, not just under settings/).

    Shape is CaseSettings -> emailToCase -> routingAddresses -> emailAddress,
    per admin/email-to-case-configuration references/metadata-examples.md. Uses
    Element.iter() + a tag-suffix comparison (not a namespaced/bare findall pair)
    so this does not need the `find(x) or find(y)` idiom banned above.
    """
    addresses: set[str] = set()
    candidates = list(root.rglob("*.settings-meta.xml")) + list(root.rglob("*.settings"))
    for path in candidates:
        if not path.is_file():
            continue
        try:
            file_root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for element in file_root.iter():
            if element.tag.rsplit("}", 1)[-1] != "routingAddresses":
                continue
            email_el = _find(element, "emailAddress")
            if email_el is not None and email_el.text:
                addresses.add(email_el.text.strip().lower())
    return addresses


def check_auto_response_loop(path: Path, routing_emails: set[str]) -> list[str]:
    """AR-LOOP-01: flag an autoResponseRules senderEmail that equals a known
    Email-to-Case routing address — the auto-response -> reply -> new case ->
    auto-response mail loop documented in references/gotchas.md #6."""
    issues: list[str] = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [f"{path.name}: XML parse error — {exc}"]

    root = tree.getroot()
    rules = root.findall(_tag("autoResponseRule")) or root.findall("autoResponseRule")

    for rule in rules:
        name_el = _find(rule, "fullName")
        rule_name = name_el.text if name_el is not None else "<unnamed>"
        entries = rule.findall(_tag("ruleEntry")) or rule.findall("ruleEntry")
        for index, entry in enumerate(entries, start=1):
            sender_el = _find(entry, "senderEmail")
            sender = sender_el.text.strip() if sender_el is not None and sender_el.text else ""
            if sender and sender.lower() in routing_emails:
                issues.append(
                    f"AR-LOOP-01 ERROR: {path.name} / autoResponseRule '{rule_name}' entry "
                    f"{index}: senderEmail '{sender}' matches an Email-to-Case routing "
                    "address. This is a mail loop (auto-response -> customer reply -> "
                    "routing address -> new case -> auto-response) — use a distinct "
                    "OrgWideEmailAddress that is not, and does not forward into, any "
                    "routing address (admin/email-to-case-configuration)."
                )

    return issues


def find_auto_response_senders(path: Path) -> list[str]:
    """Return every senderEmail / replyToEmail address text found in one
    autoResponseRules file, in document order. Not deduped here — the caller
    dedupes across the whole run so the same address named in two entries
    (or two files) produces one AR-SENDER-01 line, not one per occurrence."""
    addresses: list[str] = []
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return addresses

    root = tree.getroot()
    rules = root.findall(_tag("autoResponseRule")) or root.findall("autoResponseRule")
    for rule in rules:
        entries = rule.findall(_tag("ruleEntry")) or rule.findall("ruleEntry")
        for entry in entries:
            for field in ("senderEmail", "replyToEmail"):
                el = _find(entry, field)
                if el is not None and el.text and el.text.strip():
                    addresses.append(el.text.strip())
    return addresses


def check_assignment_rules(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    rule_files = find_assignment_rule_files(manifest_dir)

    if not rule_files:
        # Not an error — the project may not have assignment rules deployed
        print(f"INFO: No assignment rule metadata files found under {manifest_dir}.")
    else:
        for rule_file in rule_files:
            issues.extend(check_rule_file(rule_file))

    auto_response_files = find_auto_response_rule_files(manifest_dir)
    if auto_response_files:
        routing_emails = find_routing_addresses(manifest_dir)
        if routing_emails:
            for ar_file in auto_response_files:
                issues.extend(check_auto_response_loop(ar_file, routing_emails))
        else:
            issues.append(
                "AR-LOOP-02 WARN: no Email-to-Case routing-address inventory "
                f"(settings/Case.settings-meta.xml or equivalent) found under {manifest_dir} "
                "— cannot verify the sender is not an intake address at this scope."
            )

        # AR-SENDER-01: the org-wide address named as sender/reply-to is a
        # deploy-time prerequisite (references/gotchas.md #7) — it must exist
        # and be verified (IsVerified = true) in the target org before this
        # rule deploys, and there is no metadata type that ships it. This
        # cannot be checked offline (no org connection here), so it is always
        # INFO — never ERROR or WARN — and never changes the exit code.
        # Dedupe case-insensitively across every file in this run so the same
        # address named on two rule entries prints once, not twice.
        seen_lower: set[str] = set()
        prerequisite_addresses: list[str] = []
        for ar_file in auto_response_files:
            for address in find_auto_response_senders(ar_file):
                lowered = address.lower()
                if lowered not in seen_lower:
                    seen_lower.add(lowered)
                    prerequisite_addresses.append(address)

        for address in prerequisite_addresses:
            issues.append(
                f"AR-SENDER-01 INFO: senderEmail/replyToEmail '{address}' is a "
                "deploy-time prerequisite — verify OrgWideEmailAddress exists and "
                "IsVerified in the target org before deploying (references/gotchas.md #7)."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_assignment_rules(manifest_dir)

    if not issues:
        print("No assignment rule issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    # AR-LOOP-02 is a WARN (no routing-address inventory to check against, not a
    # detected loop) and AR-SENDER-01 is INFO (an unconditional deploy-time
    # reminder that cannot be checked offline) — neither may fail the run on
    # its own. Every other issue, including AR-LOOP-01, keeps the pre-existing
    # exit-1-on-any-issue policy.
    non_blocking_prefixes = ("AR-LOOP-02", "AR-SENDER-01")
    has_error = any(not issue.startswith(non_blocking_prefixes) for issue in issues)
    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
