#!/usr/bin/env python3
"""Static checks for zero-trust posture in a Salesforce metadata tree.

Looks for design smells documented in this skill's references/gotchas.md and
references/llm-anti-patterns.md. Stdlib only — no pip dependencies.

What this script catches, and the corpus line behind each rule:

  1. TransactionSecurityPolicy XML whose <eventName> is IdentityVerificationEvent or
     MobileEmailEvent. Neither is a valid eventName (api_meta 264 L138737-138798), so the
     policy cannot deploy: ERROR.
  2. TransactionSecurityPolicy XML that sets <action><block> or <twoFactorAuthentication>
     on a notify-only store (ApiAnomalyEventStore, CredentialStuffingEventStore,
     ReportAnomalyEventStore, SessionHijackingEventStore: secguide 262 L6144, L6194,
     L6470, L6492) or MFA on ApiEvent / BulkApiResultEventStore / FileEventStore
     (secguide 262 L5943, L5953, L5969): WARN. <endSession> and <freezeUser> are Legacy
     Transaction Security only, a retired feature (api_meta 264 L138877-138880): WARN.
     Earlier versions matched <eventType> and a plain-text <action> value, which real
     metadata does not use, so these rules never fired.
  3. Profile XML that grants ModifyAllData, ViewAllData, ApiEnabled or ManageUsers in
     <userPermissions> (child order is <enabled> then <name>, api_meta 264 L97915-97918;
     the earlier regex expected the reverse and never matched): WARN, a design opinion.
  4. ProfileSessionSetting XML with <requiredSessionLevel>HIGH_ASSURANCE (api_meta 264
     L101471, L101529): INFO. Profile metadata has no session-level element; an earlier
     version matched <sessionSecurityLevel> in *.profile-meta.xml, which never fires.
     UNVERIFIED (2026-10-20): "set it on the PSG instead" is Help-level.
  5. PermissionSetGroup XML bundling a high-blast permission set with no
     <mutingPermissionSets> (api_meta 264 L98039-98041): WARN.

Exit codes: ERROR findings (unparseable XML, invalid eventName, missing --src-root) exit
1 always; WARN and INFO findings exit 0 unless --strict is given. A tree with no profiles,
policies or groups prints one WARN and exits 0.

Usage:
    python3 check_zero_trust_salesforce_patterns.py --src-root .
    python3 check_zero_trust_salesforce_patterns.py --src-root force-app/main/default --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"

INVALID_TSP_EVENTS = {"IdentityVerificationEvent", "MobileEmailEvent"}
NOTIFY_ONLY_EVENTS = {
    "ApiAnomalyEventStore",
    "CredentialStuffingEventStore",
    "ReportAnomalyEventStore",
    "SessionHijackingEventStore",
}
NO_MFA_EVENTS = {"ApiEvent", "BulkApiResultEventStore", "FileEventStore"}
HIGH_BLAST_PERMS = {"modifyalldata", "viewalldata", "apienabled", "manageusers"}

_HIGH_BLAST_PS_NAME_RE = re.compile(r"(Admin|Modify|ViewAll|Manage)", re.IGNORECASE)


def _tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


def _text(parent: ET.Element | None, name: str) -> str:
    if parent is None:
        return ""
    child = parent.find(_tag(name))
    if child is not None and child.text:
        return child.text.strip()
    return ""


def _load(path: Path, findings: list[str]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(f"ERROR: {path}: cannot parse XML: {exc}")
    except OSError as exc:
        findings.append(f"ERROR: {path}: cannot read: {exc}")
    return None


def _scan_profile(path: Path, findings: list[str]) -> None:
    root = _load(path, findings)
    if root is None:
        return
    for perm in root.findall(_tag("userPermissions")):
        name = _text(perm, "name")
        if name.lower() in HIGH_BLAST_PERMS and _text(perm, "enabled").lower() == "true":
            findings.append(
                f"WARN: {path}: Profile grants `{name}`. For zero-trust least privilege, "
                "move high-blast permissions into Permission Set Groups and mute where "
                "needed (see references/gotchas.md § 4 and SKILL.md Pattern D)"
            )


def _scan_session_setting(path: Path, findings: list[str]) -> None:
    root = _load(path, findings)
    if root is None:
        return
    if _text(root, "requiredSessionLevel").upper() == "HIGH_ASSURANCE":
        findings.append(
            f"INFO: {path}: profile `{_text(root, 'profile')}` requires the High-Assurance "
            "session level at login (api_meta 264 L101471). UNVERIFIED (2026-10-20): the "
            "PSG-level alternative is Help-level; see references/gotchas.md § 2"
        )


def _scan_tsp(path: Path, findings: list[str]) -> None:
    root = _load(path, findings)
    if root is None:
        return
    event = _text(root, "eventName")
    action = root.find(_tag("action"))
    block = _text(action, "block").lower() == "true"
    mfa = _text(action, "twoFactorAuthentication").lower() == "true"
    if event in INVALID_TSP_EVENTS:
        findings.append(
            f"ERROR: {path}: eventName `{event}` is not a valid Transaction Security "
            "Policy event (api_meta 264 L138737-138798); treat it as detect-only and "
            "subscribe via Apex or Flow (see references/gotchas.md § 1)"
        )
    if event in NOTIFY_ONLY_EVENTS and (block or mfa):
        findings.append(
            f"WARN: {path}: `{event}` policies allow Notifications only "
            "(secguide 262 L6144, L6194, L6470, L6492) but this one sets block or MFA"
        )
    if event in NO_MFA_EVENTS and mfa:
        findings.append(
            f"WARN: {path}: `{event}` policies do not support multi-factor authentication "
            "(secguide 262 L5943, L5953, L5969) but this one sets twoFactorAuthentication"
        )
    for legacy in ("endSession", "freezeUser"):
        if _text(action, legacy).lower() == "true":
            findings.append(
                f"WARN: {path}: `{legacy}` is Legacy Transaction Security only, a retired "
                "feature (api_meta 264 L138877-138880)"
            )


def _scan_psg(path: Path, findings: list[str]) -> None:
    root = _load(path, findings)
    if root is None:
        return
    members = [(p.text or "").strip() for p in root.findall(_tag("permissionSets"))]
    has_muting = root.find(_tag("mutingPermissionSets")) is not None
    if any(_HIGH_BLAST_PS_NAME_RE.search(m) for m in members) and not has_muting:
        findings.append(
            f"WARN: {path}: Permission Set Group bundles a high-blast Permission Set but "
            "defines no Muting Permission Set. Consider muted-by-default with JIT grants "
            "(see SKILL.md Pattern D)"
        )


def scan_tree(root: Path) -> list[str]:
    findings: list[str] = []
    if not root.exists():
        return [f"ERROR: src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"ERROR: src-root is not a directory: {root}"]

    profiles = sorted(root.rglob("*.profile-meta.xml"))
    tsps = sorted(root.rglob("*.transactionSecurityPolicy-meta.xml"))
    psgs = sorted(root.rglob("*.permissionsetgroup-meta.xml"))
    sessions = sorted(
        set(root.rglob("*.profileSessionSetting")) | set(root.rglob("*.profileSessionSetting-meta.xml"))
    )
    if not (profiles or tsps or psgs or sessions):
        return [f"WARN: no profiles, profile session settings, transaction security policies or permission set groups under {root}; nothing to check"]

    for p in profiles:
        _scan_profile(p, findings)
    for t in tsps:
        _scan_tsp(t, findings)
    for g in psgs:
        _scan_psg(g, findings)
    for s in sessions:
        _scan_session_setting(s, findings)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for zero-trust design smells: "
            "TSP rules naming invalid or notify-only events, Profile-granted high-blast "
            "permissions, Profile-level High-Assurance, and PSGs without muting."
        ),
    )
    parser.add_argument(
        "--src-root",
        "--manifest-dir",
        dest="src_root",
        default=".",
        help="Root of the source tree to scan (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN and INFO findings to exit 1 (ERROR always exits 1).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no zero-trust design smells detected.")
        return 0

    for finding in findings:
        print(finding, file=sys.stderr)
    print(
        f"\n{len(findings)} finding(s). See references/llm-anti-patterns.md "
        "and references/gotchas.md for rationale and the correct pattern.",
        file=sys.stderr,
    )
    if any(f.startswith("ERROR:") for f in findings):
        sys.exit(1)
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
