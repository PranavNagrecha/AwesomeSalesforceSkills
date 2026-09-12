#!/usr/bin/env python3
"""Checker script for the Email-to-Case Configuration skill.

Inspects retrieved Salesforce metadata (sf project retrieve start
--metadata "Settings:Case" "AssignmentRules:Case" "AutoResponseRules:Case")
for Email-to-Case configuration faults.

ERROR-level findings (fix before deploying):
- Email-to-Case enabled with zero routing addresses
- Two routing addresses sharing the same emailAddress
- A routing address with caseOwner set but no caseOwnerType
- More than one routing address setting caseOwner: each one writes the single
  org-level CaseSettings.defaultCaseOwner, so the last one silently wins
  (Metadata API Developer Guide, EmailToCaseRoutingAddress.caseOwner)
- An auto-response senderEmail / replyToEmail equal to a routing emailAddress,
  which is the Email-to-Case reply loop
- An auto-response rule entry with no email template
- E2C-RT-01: newEntityRecordType carrying a bare developer name. The org rejects
  it with "In field: newEntityRecordType - no RecordType named <name> found";
  only the object-qualified Case.<DeveloperName> form resolves (proven live
  2026-09-12; the guide documents no value format)
- E2C-RT-02: newEntityRecordType present while a package.xml in the same tree
  declares an API version below 64.0. The org rejects the deploy with
  "Property 'newEntityRecordType' not valid in version <n>" (proven live at
  62.0 and 63.0, accepted at 64.0; the guide carries no version note)
- E2C-PRI-01: a routing address with no casePriority. The org rejects the
  deploy with "EmailToCaseRoutingAddress[<address>]: Missing casePriority"
  (proven live 2026-09-12; the guide marks the field neither required nor
  optional, but its own sample sets it on every address - api_meta L112187,
  L112200)

WARN-level findings (review, then justify or fix):
- A routing address whose isVerified is false or absent; Salesforce does not
  accept inbound mail at an unverified address
- Both the Lightning-threading and the legacy-threading token switches set
- authorizedSenders populated on a routing address, which turns every unknown
  customer into an unauthorized sender
- Discard selected for unauthorizedSenderAction or overEmailLimitAction
- No active case assignment rule, so auto-response rules will not fire
- Email-to-Case enabled without On-Demand

Element names follow the Metadata API Developer Guide: CaseSettings,
EmailToCaseSettings, EmailToCaseRoutingAddress.
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

Exit code: 1 on any ERROR, 0 when only WARNs remain. Several WARNs above are
advisory or describe state metadata cannot set at all (isVerified is read-only),
so a correct artefact must still be able to exit 0. Pass --strict to promote
every WARN to a failure.

Uses stdlib only - no pip dependencies.

Usage:
    python3 check_email_to_case_configuration.py --manifest-dir path/to/metadata
    python3 check_email_to_case_configuration.py --manifest-dir force-app/main/default --verbose
    python3 check_email_to_case_configuration.py --manifest-dir force-app/main/default --strict
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# Salesforce metadata XML namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"

# On-Demand Email-to-Case inbound size limits.
# Salesforce enforces ONE limit: the total redirected message size
# (body + attachments + HTML). There is no documented per-attachment cap.
# https://help.salesforce.com/s/articleView?id=000386265&type=1
ON_DEMAND_TOTAL_MESSAGE_LIMIT_MB = 35
# MIME transfer encoding inflates a message by up to 33% in transit, so the
# usable attachment payload inside the 35 MB total is roughly 25 MB.
ON_DEMAND_EFFECTIVE_ATTACHMENT_MB = 25

# EmailToCaseOnFailureActionType values that destroy the message silently.
SILENT_FAILURE_ACTIONS = {"discard"}

# EmailToCaseRoutingAddress.newEntityRecordType is listed in the Metadata API
# Developer Guide (api_meta L112078) with no "Available in API version N and
# later" note, unlike its neighbours fallbackQueue (56.0) and isPermsetControlled
# (61.0). The gate exists anyway: a checkOnly deploy at 62.0 and at 63.0 is
# rejected with "Property 'newEntityRecordType' not valid in version 63.0", and
# the same file is accepted at 64.0.
# UNVERIFIED (2026-09-12): version gate observed live, not in the guide.
NEW_ENTITY_RECORD_TYPE_MIN_API = 64.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Email-to-Case configuration faults. "
            "Inspects Case.settings, case assignment rules, and case auto-response rules."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print informational notes in addition to findings.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any finding, including the advisory WARNs.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# XML helpers
#
# NEVER write `element.find(a) or element.find(b)` - an ElementTree Element with
# no children is falsy even when it exists, so that idiom silently drops real
# elements. Every lookup below tests `is not None`.
# ---------------------------------------------------------------------------


def xml_root(path: Path):
    """Parse an XML file and return the root element, or None on parse failure."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def child(element, tag: str):
    """Return the named child element, or None. Explicit `is not None` throughout."""
    if element is None:
        return None
    found = element.find(f"{{{SF_NS}}}{tag}")
    return found if found is not None else None


def text(element, *path: str) -> str:
    """Navigate a chain of child tag names and return the text of the final element."""
    current = element
    for step in path:
        current = child(current, step)
        if current is None:
            return ""
    return (current.text or "").strip()


def first_text(element, *tags: str) -> str:
    """Return the text of the first of `tags` that is present and non-empty."""
    for tag in tags:
        value = text(element, tag)
        if value:
            return value
    return ""


def flag(element, *path: str) -> bool:
    """True only when the element exists and its text is exactly 'true'."""
    return text(element, *path).lower() == "true"


def find_xml_files(base: Path, subdir: str) -> list[Path]:
    """Return all XML files under base/subdir."""
    target = base / subdir
    if not target.is_dir():
        return []
    return sorted(target.rglob("*.xml"))


def manifest_api_versions(manifest_dir: Path) -> list[tuple[Path, float, str]]:
    """Return (path, API version) for every package.xml under the manifest tree.

    The version in the manifest is what the deploy is sent as, so it - not the
    sourceApiVersion of some enclosing project - is what decides whether
    newEntityRecordType is a valid property (E2C-RT-02).
    """
    versions: list[tuple[Path, float, str]] = []
    for path in sorted(manifest_dir.rglob("package.xml")):
        root = xml_root(path)
        if root is None:
            continue
        raw = text(root, "version")
        if not raw:
            continue
        try:
            parsed = float(raw)
        except ValueError:
            continue
        # The raw text is carried through so the finding quotes the manifest and
        # the org's error message verbatim ("version 63.0", not "version 63").
        versions.append((path, parsed, raw))
    return versions


def locate(manifest_dir: Path, subdir: str, stem: str, suffix: str) -> list[Path]:
    """Find `<subdir>/<stem><suffix>` and its -meta.xml twin, anywhere under the tree."""
    names = [f"{stem}{suffix}", f"{stem}{suffix}-meta.xml"]
    found: list[Path] = []
    for name in names:
        direct = manifest_dir / subdir / name
        if direct.exists():
            found.append(direct)
    for name in names:
        for path in manifest_dir.rglob(name):
            if path not in found:
                found.append(path)
    return found


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def check_email_to_case_settings(
    manifest_dir: Path, verbose: bool
) -> tuple[list[str], list[str]]:
    """Check Case.settings for Email-to-Case faults.

    Returns (findings, routing_email_addresses) so the caller can cross-reference
    the auto-response senders against the routing addresses.
    """
    findings: list[str] = []
    notes: list[str] = []
    routing_emails: list[str] = []

    candidate_paths = locate(manifest_dir, "settings", "Case", ".settings")

    if not candidate_paths:
        notes.append(
            "Case.settings metadata not found. "
            "Cannot verify Email-to-Case enabled state or routing address configuration. "
            'Retrieve it with: sf project retrieve start --metadata "Settings:Case"'
        )
        if verbose:
            for note in notes:
                print(f"NOTE: {note}")
        return findings, routing_emails

    for path in candidate_paths:
        root = xml_root(path)
        if root is None:
            findings.append(f"ERROR: could not parse Case.settings: {path}")
            continue

        e2c = child(root, "emailToCase")
        if e2c is None:
            notes.append(f"{path.name}: no <emailToCase> block; Email-to-Case is not configured here.")
            continue

        # The element is enableEmailToCase, not enable. A file using <enable>
        # deploys cleanly and turns nothing on.
        enabled = flag(e2c, "enableEmailToCase")
        if child(e2c, "enable") is not None and child(e2c, "enableEmailToCase") is None:
            findings.append(
                f"ERROR: {path.name}: <emailToCase> uses <enable>, which is not an "
                "EmailToCaseSettings field. The correct element is <enableEmailToCase>. "
                "As written this deploys successfully and leaves the feature off."
            )
        if not enabled:
            findings.append(
                f"ERROR: {path.name}: enableEmailToCase is not true. "
                "Routing addresses do nothing until the feature is enabled."
            )

        on_demand = flag(e2c, "enableOnDemandEmailToCase")
        if enabled and not on_demand:
            findings.append(
                f"WARN: {path.name}: enableOnDemandEmailToCase is not true. "
                "Standard Email-to-Case needs a locally installed agent and consumes API "
                "calls per email. Enable On-Demand unless data residency policy forbids it."
            )

        # Threading: two mutually exclusive pairs plus a header fallback.
        lightning_pair = flag(e2c, "enableThreadTokenInBody") or flag(
            e2c, "enableThreadTokenInSubject"
        )
        legacy_pair = flag(e2c, "enableThreadIDInBody") or flag(e2c, "enableThreadIDInSubject")
        if lightning_pair and legacy_pair:
            findings.append(
                f"WARN: {path.name}: both threading switch pairs are set. "
                "enableThreadTokenInBody/Subject apply only to orgs using Lightning "
                "Threading; enableThreadIDInBody/Subject apply only to orgs that do not. "
                "One pair is inert - confirm which mode the org is in and set only that pair."
            )
        if enabled and not lightning_pair and not legacy_pair:
            findings.append(
                f"WARN: {path.name}: no threading token switch is set in either pair. "
                "Replies will rely entirely on useEmailHeadersForThreading, if that is on."
            )
        if enabled and not flag(e2c, "useEmailHeadersForThreading"):
            notes.append(
                f"{path.name}: useEmailHeadersForThreading is off. It is the fallback that "
                "matches a reply when a mail gateway has stripped the token."
            )

        for setting in ("unauthorizedSenderAction", "overEmailLimitAction"):
            value = text(e2c, setting)
            if value.lower() in SILENT_FAILURE_ACTIONS:
                findings.append(
                    f"WARN: {path.name}: {setting} is '{value}'. Discarded mail leaves no "
                    "Case, no EmailMessage and no bounce - the sender and the org both have "
                    "no record it arrived. Prefer Bounce, or Requeue for overEmailLimitAction."
                )

        routing_addresses = e2c.findall(f"{{{SF_NS}}}routingAddresses")

        if enabled and not routing_addresses:
            findings.append(
                f"ERROR: {path.name}: Email-to-Case is enabled but no <routingAddresses> "
                "element is present. Inbound email cannot create cases. Note that "
                "routingAddresses is a full-replacement list: deploying this file to an org "
                "that has addresses deletes them."
            )

        seen_addresses: dict[str, list[str]] = defaultdict(list)
        owner_setters: list[str] = []
        record_type_setters: list[str] = []

        for index, addr in enumerate(routing_addresses, start=1):
            name = text(addr, "routingName") or f"#{index}"
            email_address = text(addr, "emailAddress")

            if not email_address:
                findings.append(
                    f"ERROR: routing address '{name}': no <emailAddress>. "
                    "This is the customer-facing address mail is forwarded from; "
                    "without it the address cannot receive anything."
                )
            else:
                routing_emails.append(email_address.lower())
                seen_addresses[email_address.lower()].append(name)

            # isVerified is read-only, so a fresh deploy always lands unverified.
            if not flag(addr, "isVerified"):
                findings.append(
                    f"WARN: routing address '{name}': isVerified is false or absent. "
                    "Salesforce does not process inbound mail at an unverified address, and "
                    "the failure is silent - the mail server logs a successful delivery and "
                    "no case appears. Send the verification email from Setup and confirm the "
                    "address reads Verified in the org (isVerified cannot be set from metadata)."
                )

            case_owner = text(addr, "caseOwner")
            case_owner_type = text(addr, "caseOwnerType")
            if case_owner:
                owner_setters.append(name)
                if not case_owner_type:
                    findings.append(
                        f"ERROR: routing address '{name}': caseOwner is '{case_owner}' but "
                        "caseOwnerType is missing. caseOwnerType declares whether the owner "
                        "is a User or a Queue; without it the owner is ambiguous."
                    )
            elif case_owner_type:
                findings.append(
                    f"ERROR: routing address '{name}': caseOwnerType is "
                    f"'{case_owner_type}' but caseOwner is missing."
                )

            if text(addr, "authorizedSenders"):
                findings.append(
                    f"WARN: routing address '{name}': authorizedSenders is populated. "
                    "Only the listed addresses and domains can create cases here; every "
                    "other sender hits unauthorizedSenderAction. Leave it empty on a public "
                    "support address."
                )

            if flag(addr, "createTask") and not text(addr, "taskStatus"):
                findings.append(
                    f"WARN: routing address '{name}': createTask is true but taskStatus is "
                    "not set. taskStatus applies only when createTask is true and gives the "
                    "generated task a deliberate starting status."
                )

            if not flag(addr, "saveEmailHeaders"):
                findings.append(
                    f"WARN: routing address '{name}': saveEmailHeaders is false or absent. "
                    "EmailMessage.Headers is populated at the moment mail is processed and "
                    "cannot be backfilled, so a later phishing or spoofing investigation on "
                    "this channel has no envelope evidence to read."
                )

            # E2C-PRI-01. The guide describes casePriority as "the default case
            # priority for cases created through this routing address"
            # (api_meta L112039) and marks it neither Required nor Optional, but
            # a checkOnly deploy of an address without it is rejected:
            # "EmailToCaseRoutingAddress[support@acme.example]: Missing
            # casePriority". The guide's own sample sets it on both of its
            # addresses (api_meta L112187, L112200).
            # UNVERIFIED (2026-09-12): required-ness proven live, not in the guide.
            if not text(addr, "casePriority"):
                findings.append(
                    f"ERROR: E2C-PRI-01 routing address '{name}': no <casePriority>. "
                    "The org rejects the deploy with 'EmailToCaseRoutingAddress"
                    f"[{email_address or name}]: Missing casePriority'. Set it to a live "
                    "CasePriority value, and treat the stamped priority as the channel's "
                    "starting tier - an email case is never created with Priority null, so a "
                    "null-guarded downstream stamp will not fire."
                )

            # E2C-RT-01 / E2C-RT-02. Both proven live 2026-09-12; neither the
            # value format nor the version gate is in the guide (api_meta L112078).
            new_entity_record_type = text(addr, "newEntityRecordType")
            if new_entity_record_type:
                record_type_setters.append(name)
                if "." not in new_entity_record_type:
                    findings.append(
                        f"ERROR: E2C-RT-01 routing address '{name}': newEntityRecordType is "
                        f"'{new_entity_record_type}', a bare developer name. The org rejects it "
                        f"with 'In field: newEntityRecordType - no RecordType named "
                        f"{new_entity_record_type} found'. Use the object-qualified form, "
                        f"'Case.{new_entity_record_type}'."
                    )

            address_type = text(addr, "addressType")
            if address_type and address_type not in {"EmailToCase", "Outlook"}:
                findings.append(
                    f"ERROR: routing address '{name}': addressType '{address_type}' is not a "
                    "valid EmailToCaseRoutingAddressType. Valid values: EmailToCase, Outlook."
                )

        for email_address, names in seen_addresses.items():
            if len(names) > 1:
                findings.append(
                    f"ERROR: emailAddress '{email_address}' is used by "
                    f"{len(names)} routing addresses ({', '.join(names)}). "
                    "Inbound mail to a duplicated address has no deterministic configuration; "
                    "give each channel its own address or collapse them into one entry."
                )

        if len(owner_setters) > 1:
            findings.append(
                f"ERROR: {len(owner_setters)} routing addresses set caseOwner "
                f"({', '.join(owner_setters)}). Per the Metadata API Developer Guide, setting "
                "caseOwner on a routing address writes the single org-level "
                "CaseSettings.defaultCaseOwner, so the last one processed wins and the others "
                "silently do nothing. Give each address its own caseOrigin and route on "
                "Case.Origin in the assignment rule instead."
            )

        if record_type_setters:
            for manifest_path, api_version, raw_version in manifest_api_versions(manifest_dir):
                if api_version < NEW_ENTITY_RECORD_TYPE_MIN_API:
                    findings.append(
                        f"ERROR: E2C-RT-02 {manifest_path.name} declares "
                        f"<version>{raw_version}</version>, but "
                        f"{len(record_type_setters)} routing address(es) "
                        f"({', '.join(record_type_setters)}) set newEntityRecordType. The org "
                        f"rejects the deploy with \"Property 'newEntityRecordType' not valid in "
                        f"version {raw_version}\". Raise the manifest to "
                        f"{NEW_ENTITY_RECORD_TYPE_MIN_API:.1f} or later, or drop the element."
                    )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return findings, routing_emails


def check_assignment_rule_active(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check that an active case assignment rule exists (required for auto-response)."""
    findings: list[str] = []
    notes: list[str] = []

    files = locate(manifest_dir, "assignmentRules", "Case", ".assignmentRules")
    if not files:
        files = [
            f
            for f in find_xml_files(manifest_dir, "assignmentRules")
            if "case" in f.stem.lower()
        ]

    if not files:
        findings.append(
            "WARN: no case assignment rule metadata found. Auto-response rules do not fire "
            "without an active case assignment rule, and cases fall to the org default owner. "
            'Retrieve it with: sf project retrieve start --metadata "AssignmentRules:Case"'
        )
        return findings

    active_count = 0
    for path in files:
        root = xml_root(path)
        if root is None:
            findings.append(f"ERROR: could not parse assignment rule file: {path}")
            continue
        for rule in root.findall(f"{{{SF_NS}}}assignmentRule"):
            rule_name = text(rule, "fullName") or path.stem
            if not flag(rule, "active"):
                notes.append(f"Assignment rule '{rule_name}' is not active.")
                continue
            active_count += 1
            rule_entries = rule.findall(f"{{{SF_NS}}}ruleEntry")
            if not rule_entries:
                findings.append(
                    f"ERROR: active assignment rule '{rule_name}' has no rule entries. "
                    "Cases land with the default owner and auto-response does not fire."
                )
                continue
            last_entry = rule_entries[-1]
            if last_entry.findall(f"{{{SF_NS}}}criteriaItems"):
                findings.append(
                    f"WARN: active assignment rule '{rule_name}': the last rule entry has "
                    "criteria, so it is not a catch-all. Email-to-Case cases that match no "
                    "entry fall to the org default owner rather than a queue."
                )

    if active_count == 0:
        findings.append(
            "WARN: no active case assignment rule found. Auto-response rules only fire when "
            "the assignment rule fires. Activate the rule at Setup -> Assignment Rules -> Cases."
        )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return findings


def check_auto_response_rules(
    manifest_dir: Path,
    routing_emails: list[str],
    verbose: bool,
) -> list[str]:
    """Check case auto-response rules for loop risk and missing templates."""
    findings: list[str] = []
    notes: list[str] = []

    files = locate(manifest_dir, "autoResponseRules", "Case", ".autoResponseRules")
    if not files:
        files = [
            f
            for f in find_xml_files(manifest_dir, "autoResponseRules")
            if "case" in f.stem.lower()
        ]

    if not files:
        notes.append(
            "No case auto-response rule metadata found; skipping the loop check. "
            "If the org has auto-response rules, retrieve them "
            '(--metadata "AutoResponseRules:Case") and re-run - the loop check is the '
            "reason this script exists."
        )
        if verbose:
            for note in notes:
                print(f"NOTE: {note}")
        return findings

    for path in files:
        root = xml_root(path)
        if root is None:
            findings.append(f"ERROR: could not parse auto-response rule file: {path}")
            continue

        for rule in root.findall(f"{{{SF_NS}}}autoResponseRule"):
            rule_name = text(rule, "fullName") or path.stem
            if not flag(rule, "active"):
                notes.append(f"Auto-response rule '{rule_name}' is not active.")
                continue

            for index, entry in enumerate(rule.findall(f"{{{SF_NS}}}ruleEntry"), start=1):
                if not text(entry, "template"):
                    findings.append(
                        f"ERROR: auto-response rule '{rule_name}', entry {index}: no "
                        "<template>. The entry matches cases and sends no acknowledgement."
                    )

                for field in ("senderEmail", "replyToEmail"):
                    value = text(entry, field)
                    if value and value.lower() in routing_emails:
                        findings.append(
                            f"ERROR: auto-response rule '{rule_name}', entry {index}: "
                            f"{field} '{value}' is also an Email-to-Case routing address. "
                            "This is the reply loop: auto-response -> customer -> reply -> "
                            "routing address -> new case -> auto-response. Use a no-reply "
                            "address that does not forward into Salesforce."
                        )

                sender = first_text(entry, "senderEmail", "replyToEmail")
                if not sender:
                    findings.append(
                        f"WARN: auto-response rule '{rule_name}', entry {index}: neither "
                        "senderEmail nor replyToEmail is set, so the sender identity depends "
                        "on org defaults rather than a verified org-wide address."
                    )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return findings


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def check_email_to_case_configuration(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Run every Email-to-Case check and return the findings as prefixed strings."""
    findings: list[str] = []

    if not manifest_dir.exists():
        return [f"ERROR: manifest directory not found: {manifest_dir}"]

    settings_findings, routing_emails = check_email_to_case_settings(manifest_dir, verbose)
    findings.extend(settings_findings)
    findings.extend(check_assignment_rule_active(manifest_dir, verbose))
    findings.extend(check_auto_response_rules(manifest_dir, routing_emails, verbose))

    return findings


def main() -> int:
    args = parse_args()
    findings = check_email_to_case_configuration(Path(args.manifest_dir), verbose=args.verbose)

    if not findings:
        print("No Email-to-Case configuration issues found.")
        return 0

    errors = [f for f in findings if f.startswith("ERROR")]
    warnings = [f for f in findings if not f.startswith("ERROR")]

    print(f"Findings: {len(errors)} error(s), {len(warnings)} warning(s).")
    for finding in errors + warnings:
        print(f"  {finding}", file=sys.stderr)

    # Exit 1 on ERRORs only. The WARNs above are advisory, and one of them
    # (isVerified) reports state that metadata cannot set at all, so a correct
    # artefact has to be able to exit 0. --strict promotes every WARN.
    if errors:
        return 1
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
