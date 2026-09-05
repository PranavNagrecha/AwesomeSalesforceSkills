#!/usr/bin/env python3
"""Checker for the admin/email-deliverability-strategy skill.

Lints the Salesforce Core deliverability artifacts a project keeps in source:

  settings/EmailAdministration.settings-meta.xml   (EmailAdministrationSettings)
  settings/EmailAuthorization.settings-meta.xml    (EmailAuthorizationSettings)
  deliverability/dkim-keys.json                    (EmailDomainKey inventory)
  deliverability/email-policy.json                 (org sending policy)
  any *.txt / *.md DNS record specification

Checks implemented (see references/metadata-examples.md for the grounding):

  1. The settings XML uses only elements documented for its type
     (api_meta.txt L114869-114996 and L115074).
  2. Documented field dependencies hold: enableEmailSenderIdCompliance needs
     enableEmailSpfCompliance (api_meta.txt L114884-114887); enableResendBouncedEmails
     needs enableHandleBouncedEmails (api_meta.txt L114946-114950).
  3. enableComplianceBcc is not enabled without a Compliance BCC address recorded
     in the policy file — the address has no metadata element, so the deploy
     succeeds and the BCC silently never fires (api_meta.txt L114872-114877).
  4. Bounce handling is enabled when the policy says the org sends externally
     (api_meta.txt L114908-114915); without it the Contact/Lead bounce fields
     stay empty (object_reference.txt L71679, L163389).
  5. Every sending domain in the policy has exactly one active DKIM key carrying
     a rotation date, published, at a supported key size
     (object_reference.txt L103573-103611, L103665-103674).
  6. Any DNS spec found holds one SPF record and a DMARC record with rua=.

Errors exit 1. Warnings alone exit 0.

Usage:
    python3 check_email_deliverability_strategy.py --manifest-dir force-app/main/default
    python3 check_email_deliverability_strategy.py --dns-spec deliverability/dns-records.txt
    python3 check_email_deliverability_strategy.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

# --------------------------------------------------------------------------
# Documented element sets. Source: Metadata API Developer Guide (v62/v66 PDF).
# EmailAdministrationSettings field table  — api_meta.txt L114869-114996
# EmailAuthorizationSettings field table   — api_meta.txt L115074
# --------------------------------------------------------------------------

EMAIL_ADMIN_FIELDS = {
    "enableComplianceBcc",
    "enableEmailConsentManagement",
    "enableEmailSenderIdCompliance",
    "enableEmailSpfCompliance",
    "enableEmailToSalesforce",
    "enableEmailWorkflowApproval",
    "enableEnhancedEmailEnabled",
    "enableHandleBouncedEmails",
    "enableHtmlEmail",
    "enableInternationalEmailAddresses",
    "enableListEmailLogActivities",
    "enableResendBouncedEmails",
    "enableRestrictTlsToDomains",
    "enableSendThroughGmailPref",  # documented as "Deprecated." (L114964)
    "enableSendViaExchangePref",
    "enableSendViaGmailPref",
    "enableUseOrgFootersForExtTrans",
    "sendMassEmailNotification",
    "sendTextOnlySystemEmails",
}

DEPRECATED_EMAIL_ADMIN_FIELDS = {"enableSendThroughGmailPref"}

EMAIL_AUTH_FIELDS = {"enableSubstituteFromAddress"}

# EmailDomainKey restricted picklists — object_reference.txt L103573-103594,
# L103603-103611, L103665-103674.
DOMAIN_MATCH_VALUES = {"DomainOnly", "SubdomainsOnly", "DomainAndSubdomains"}
KEY_SIZES = {1024, 2048}
PUBLISH_STATES = {"Published", "Publishing in progress", "Publishing failed"}

SETTINGS_ROOTS = {
    "EmailAdministrationSettings": EMAIL_ADMIN_FIELDS,
    "EmailAuthorizationSettings": EMAIL_AUTH_FIELDS,
}


class Findings:
    """Collects errors and warnings so every file is checked before exiting."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"[{where}] {message}")

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"[{where}] {message}")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def strip_ns(tag: str) -> str:
    """Return the local name of a possibly namespaced ElementTree tag."""
    return tag.split("}", 1)[1] if "}" in tag else tag


def child_text(parent: ET.Element, name: str) -> str | None:
    """Text of the first direct child named `name`, or None.

    A leaf Element is falsy in ElementTree, so this compares against None
    explicitly and never chains `find(a) or find(b)`.
    """
    for child in parent:
        if strip_ns(child.tag) == name:
            text = child.text
            return text.strip() if text is not None else ""
    return None


def bool_field(parent: ET.Element, name: str) -> bool | None:
    """Parse a boolean settings element. None when the element is absent."""
    raw = child_text(parent, name)
    if raw is None:
        return None
    return raw.lower() == "true"


def parse_iso_date(raw: object) -> date | None:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.strptime(raw.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def load_json(path: Path, findings: Findings) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.error(path.name, f"could not be parsed as JSON: {exc}")
        return None
    if not isinstance(data, dict):
        findings.error(path.name, "top level must be a JSON object.")
        return None
    return data


# --------------------------------------------------------------------------
# Check 1 + 2: settings XML
# --------------------------------------------------------------------------

def check_settings_file(path: Path, findings: Findings) -> ET.Element | None:
    """Validate one *.settings file. Returns its root when it is an email type."""
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        findings.error(path.name, f"is not well-formed XML: {exc}")
        return None

    root_name = strip_ns(root.tag)
    allowed = SETTINGS_ROOTS.get(root_name)
    if allowed is None:
        return None  # some other settings type; not this skill's business

    where = path.name
    for child in root:
        element = strip_ns(child.tag)
        if element not in allowed:
            findings.error(
                where,
                f"<{element}> is not a documented {root_name} element. "
                f"Documented elements: {', '.join(sorted(allowed))}. "
                "An undocumented element fails the deploy.",
            )
        elif element in DEPRECATED_EMAIL_ADMIN_FIELDS:
            findings.warn(
                where,
                f"<{element}> is documented as Deprecated "
                "(api_meta.txt L114964). Use <enableSendViaGmailPref> instead.",
            )

    if root_name != "EmailAdministrationSettings":
        return root

    # Check 2: documented field dependencies.
    spf = bool_field(root, "enableEmailSpfCompliance")
    sender_id = bool_field(root, "enableEmailSenderIdCompliance")
    if sender_id is True and spf is not True:
        findings.error(
            where,
            "enableEmailSenderIdCompliance is true but enableEmailSpfCompliance is "
            f"{'absent' if spf is None else 'false'}. The guide requires "
            "enableEmailSpfCompliance = true to enable Sender ID compliance "
            "(api_meta.txt L114884-114887).",
        )

    handle = bool_field(root, "enableHandleBouncedEmails")
    resend = bool_field(root, "enableResendBouncedEmails")
    if resend is True and handle is not True:
        findings.error(
            where,
            "enableResendBouncedEmails is true but enableHandleBouncedEmails is "
            f"{'absent' if handle is None else 'false'}. The guide requires "
            "enableHandleBouncedEmails = true to enable resend "
            "(api_meta.txt L114946-114950).",
        )

    if spf is False:
        findings.warn(
            where,
            "enableEmailSpfCompliance is explicitly false. Its documented default "
            "is true (api_meta.txt L114893-114895) — confirm this is deliberate.",
        )
    return root


# --------------------------------------------------------------------------
# Check 3 + 4: settings vs. policy
# --------------------------------------------------------------------------

def check_policy_against_settings(
    policy: dict, policy_name: str, admin_root: ET.Element | None, findings: Findings
) -> None:
    compliance_bcc = bool_field(admin_root, "enableComplianceBcc") if admin_root is not None else None
    bcc_address = str(policy.get("complianceBccAddress") or "").strip()

    # Check 3
    if compliance_bcc is True and not bcc_address:
        findings.error(
            policy_name,
            "enableComplianceBcc is true but complianceBccAddress is empty. "
            "The address itself lives only in Setup > Compliance BCC Email and has "
            "no metadata element (api_meta.txt L114872-114877), so the deploy passes "
            "and no BCC is ever sent. Record the address here and confirm it in Setup.",
        )
    if bcc_address and compliance_bcc is not True:
        findings.warn(
            policy_name,
            f"complianceBccAddress is set to {bcc_address!r} but enableComplianceBcc "
            "is not true in the settings file — the archive is not receiving copies.",
        )

    # Check 4
    sends_external = policy.get("sendsExternalEmail")
    if sends_external is True:
        if admin_root is None:
            findings.error(
                policy_name,
                "sendsExternalEmail is true but no EmailAdministrationSettings file "
                "was found under --manifest-dir. Bounce handling cannot be reviewed.",
            )
        else:
            handle = bool_field(admin_root, "enableHandleBouncedEmails")
            if handle is not True:
                findings.error(
                    policy_name,
                    "sendsExternalEmail is true but enableHandleBouncedEmails is "
                    f"{'absent' if handle is None else 'false'}. Without bounce "
                    "handling the Contact/Lead bounce fields are never populated "
                    "(object_reference.txt L71679, L163389), so invalid addresses "
                    "stay on the list and keep damaging sender reputation.",
                )
    elif sends_external is None:
        findings.warn(
            policy_name,
            "sendsExternalEmail is missing. Set it to true or false so the bounce-"
            "handling check can run.",
        )


# --------------------------------------------------------------------------
# Check 5: DKIM inventory
# --------------------------------------------------------------------------

def check_dkim_inventory(
    inventory: dict, inv_name: str, policy: dict | None, findings: Findings
) -> None:
    keys = inventory.get("dkimKeys")
    if not isinstance(keys, list) or not keys:
        findings.error(inv_name, "dkimKeys must be a non-empty list of key records.")
        return

    active_by_domain: dict[str, list[dict]] = {}
    today = date.today()

    for index, key in enumerate(keys):
        if not isinstance(key, dict):
            findings.error(inv_name, f"dkimKeys[{index}] is not an object.")
            continue
        domain = str(key.get("domain") or "").strip().lower()
        selector = str(key.get("selector") or "").strip()
        where = f"{inv_name}:{domain or f'dkimKeys[{index}]'}/{selector or '?'}"

        if not domain:
            findings.error(where, "domain is required on every DKIM key record.")
            continue
        if not selector:
            findings.error(where, "selector is required (object_reference.txt L103639).")

        match = key.get("domainMatch")
        if match is not None and match not in DOMAIN_MATCH_VALUES:
            findings.error(
                where,
                f"domainMatch {match!r} is not a documented value. DomainMatch is a "
                f"restricted picklist: {', '.join(sorted(DOMAIN_MATCH_VALUES))} "
                "(object_reference.txt L103573-103594).",
            )

        size = key.get("keySize")
        if size is not None and size not in KEY_SIZES:
            findings.error(
                where,
                f"keySize {size!r} is not supported. EmailDomainKey.KeySize accepts "
                "1024 or 2048 only (object_reference.txt L103603-103611).",
            )

        if not key.get("isActive"):
            continue

        active_by_domain.setdefault(domain, []).append(key)

        state = key.get("txtRecordsPublishState")
        if state is not None and state not in PUBLISH_STATES:
            findings.error(
                where,
                f"txtRecordsPublishState {state!r} is not a documented value: "
                f"{', '.join(sorted(PUBLISH_STATES))} "
                "(object_reference.txt L103665-103674).",
            )
        elif state != "Published":
            findings.error(
                where,
                f"key is active but txtRecordsPublishState is {state!r}. An active key "
                "whose records are not Published signs mail with a key receivers cannot "
                "resolve, so every message fails DKIM.",
            )

        if size == 1024:
            findings.warn(where, "active key is 1024-bit; 2048 is the stronger supported size.")

        if not key.get("alternateSelector"):
            findings.warn(
                where,
                "active key has no alternateSelector, so Salesforce cannot auto-rotate it "
                "(object_reference.txt L103529-103545).",
            )

        due = parse_iso_date(key.get("nextRotationDue"))
        if due is None:
            findings.error(
                where,
                "active key has no valid nextRotationDue (YYYY-MM-DD). Nothing on the "
                "platform expires a DKIM key or warns you it is stale — this file is "
                "the only rotation record.",
            )
        elif due < today:
            findings.error(
                where,
                f"rotation was due {due.isoformat()} and has not happened.",
            )

    # Every sending domain in the policy must have exactly one active key.
    domains = []
    if policy:
        domains = [str(d).strip().lower() for d in policy.get("sendingDomains", []) if str(d).strip()]
    for domain in domains:
        active = active_by_domain.get(domain, [])
        if not active:
            findings.error(
                inv_name,
                f"sending domain {domain!r} has no active DKIM key. Outbound mail from "
                "that domain is unsigned and cannot pass DMARC on the DKIM side.",
            )
        elif len(active) > 1:
            selectors = ", ".join(str(k.get("selector")) for k in active)
            findings.warn(
                inv_name,
                f"sending domain {domain!r} has {len(active)} active DKIM keys "
                f"({selectors}). Keep two only during a rotation window.",
            )

    for domain in sorted(set(active_by_domain) - set(domains)):
        if domains:
            findings.warn(
                inv_name,
                f"domain {domain!r} has an active DKIM key but is not listed in the "
                "policy's sendingDomains — either it is sending unrecorded mail or the "
                "key should be retired.",
            )


# --------------------------------------------------------------------------
# Check 6: DNS record spec
# --------------------------------------------------------------------------

def check_dns_spec(spec_path: Path, findings: Findings) -> None:
    """Validate a DNS record specification file. Internet-standard checks only."""
    where = spec_path.name
    try:
        text = spec_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        findings.error(where, f"could not be read: {exc}")
        return

    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]

    spf_lines = [ln for ln in lines if "v=spf1" in ln]
    if len(spf_lines) > 1:
        findings.error(
            where,
            f"{len(spf_lines)} lines contain 'v=spf1'. RFC 7208 allows exactly one SPF "
            "TXT record per domain; a second one makes SPF evaluation return PermError. "
            "Merge every include: directive into one record.",
        )
    elif not spf_lines:
        findings.warn(where, "no SPF record ('v=spf1') found.")
    else:
        lookups = spf_lines[0].count("include:") + spf_lines[0].count("redirect=")
        if lookups > 10:
            findings.error(
                where,
                f"the SPF record has {lookups} include:/redirect= directives. RFC 7208 "
                "caps SPF at 10 DNS lookups; over the cap the result is PermError.",
            )

    dkim_lines = [ln for ln in lines if "_domainkey." in ln.lower()]
    if not dkim_lines:
        findings.warn(
            where,
            "no DKIM record ('<selector>._domainkey.<domain>') found. Salesforce Core "
            "DKIM is a CNAME pair pointing at EmailDomainKey.TxtRecordName and "
            "AlternateTxtRecordName (object_reference.txt L103693-103698).",
        )
    elif not any(re.search(r"\bCNAME\b", ln, re.IGNORECASE) for ln in dkim_lines):
        findings.warn(
            where,
            "DKIM entries found but none are CNAME records. Salesforce Core publishes "
            "the key itself and expects you to publish CNAMEs, not raw TXT public keys.",
        )

    dmarc_lines = [ln for ln in lines if "_dmarc." in ln.lower()]
    if not dmarc_lines:
        findings.warn(where, "no DMARC record at '_dmarc.<sending-domain>' found.")
        return

    dmarc = " ".join(dmarc_lines).lower()
    if "rua=" not in dmarc:
        findings.error(
            where,
            "the DMARC record has no rua= aggregate-report address. Without it no "
            "receiver reports alignment failures and the policy is unmonitorable.",
        )
    if not re.search(r"p\s*=\s*(none|quarantine|reject)", dmarc):
        findings.error(where, "the DMARC record has no p= policy tag (none/quarantine/reject).")
    elif "p=reject" in dmarc.replace(" ", ""):
        findings.warn(
            where,
            "DMARC policy is p=reject. Confirm aggregate reports have been reviewed and "
            "every legitimate sender passes before enforcing; a false positive here is "
            "undelivered legitimate mail.",
        )


# --------------------------------------------------------------------------
# Discovery + entry point
# --------------------------------------------------------------------------

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".sfdx", ".sf"}


def walk(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and not SKIP_DIRS.intersection(path.parts):
            yield path


def check_manifest_dir(manifest_dir: Path, findings: Findings) -> None:
    if not manifest_dir.exists():
        findings.error(str(manifest_dir), "manifest directory not found.")
        return

    admin_root: ET.Element | None = None
    policies: list[tuple[Path, dict]] = []
    inventories: list[tuple[Path, dict]] = []
    dns_specs: list[Path] = []
    saw_settings = False

    for path in walk(manifest_dir):
        name = path.name.lower()
        if name.endswith(".settings-meta.xml") or name.endswith(".settings"):
            root = check_settings_file(path, findings)
            if root is not None:
                saw_settings = True
                if strip_ns(root.tag) == "EmailAdministrationSettings":
                    admin_root = root
        elif name.endswith(".json"):
            head = path.read_text(encoding="utf-8", errors="replace")[:4000]
            if '"dkimKeys"' in head:
                data = load_json(path, findings)
                if data:
                    inventories.append((path, data))
            elif '"sendsExternalEmail"' in head or '"sendingDomains"' in head:
                data = load_json(path, findings)
                if data:
                    policies.append((path, data))
        elif name.endswith((".txt", ".md")) and any(
            kw in name for kw in ("dns", "spf", "dkim", "dmarc")
        ):
            dns_specs.append(path)

    if not saw_settings:
        findings.warn(
            str(manifest_dir),
            "no EmailAdministrationSettings or EmailAuthorizationSettings file found. "
            "Retrieve them first (references/metadata-examples.md § 7) so the org's real "
            "deliverability posture is in source before you change it.",
        )

    policy = policies[0][1] if policies else None
    if not policies:
        findings.warn(
            str(manifest_dir),
            "no deliverability policy JSON found (an object with sendsExternalEmail / "
            "sendingDomains / complianceBccAddress). Checks 3, 4 and the per-domain DKIM "
            "check cannot run without it — see references/metadata-examples.md § 3.",
        )
    else:
        for path, data in policies:
            check_policy_against_settings(data, path.name, admin_root, findings)

    if not inventories:
        findings.warn(
            str(manifest_dir),
            "no DKIM key inventory JSON found (an object with a dkimKeys list). Nothing "
            "on the platform tracks DKIM key age; this file is the rotation record.",
        )
    else:
        for path, data in inventories:
            check_dkim_inventory(data, path.name, policy, findings)

    for path in dns_specs:
        check_dns_spec(path, findings)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint Salesforce Core email deliverability artifacts: EmailAdministration / "
            "EmailAuthorization settings XML, the EmailDomainKey inventory, the org "
            "sending policy, and any DNS record specification."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce DX project or metadata directory (default: .).",
    )
    parser.add_argument(
        "--dns-spec",
        default=None,
        help="Check only this DNS record specification file and nothing else.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (exit 1 when any warning is raised).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings = Findings()

    if args.dns_spec:
        spec = Path(args.dns_spec)
        if not spec.exists():
            findings.error(str(spec), "DNS spec file not found.")
        else:
            check_dns_spec(spec, findings)
    else:
        check_manifest_dir(Path(args.manifest_dir), findings)

    for warning in findings.warnings:
        print(f"WARN:  {warning}", file=sys.stderr)
    for error in findings.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if findings.errors:
        print(
            f"\n{len(findings.errors)} error(s), {len(findings.warnings)} warning(s).",
            file=sys.stderr,
        )
        return 1
    if findings.warnings and args.strict:
        print(f"\n{len(findings.warnings)} warning(s), --strict.", file=sys.stderr)
        return 1

    print(f"OK — no deliverability errors ({len(findings.warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
