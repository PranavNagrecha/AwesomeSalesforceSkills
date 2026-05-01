#!/usr/bin/env python3
"""Static checks for zero-trust posture in a Salesforce metadata tree.

Looks for the highest-confidence design smells documented in this
skill's references/llm-anti-patterns.md and references/gotchas.md.
Stdlib only — no pip dependencies.

What this script catches:

  1. Profile XML files that set `<sessionSettings>` with
     `<sessionSecurityLevel>HIGH_ASSURANCE</sessionSecurityLevel>` —
     the gotcha is that High Assurance belongs on a PSG, not a
     Profile (gotcha #2).
  2. Transaction Security Policy metadata referencing
     `IdentityVerificationEvent` or `MobileEmailEvent` — those event
     types do NOT support TSP enforcement (gotcha #1).
  3. Profile XML files that grant `modifyAllData=true`,
     `viewAllData=true`, or `apiEnabled=true` directly on the Profile
     when a PSG-based pattern would be safer for the zero-trust
     least-privilege leg (gotcha #4).
  4. PermissionSetGroup XML with no `mutingPermissionSets` reference
     when the group's profile permission set list contains
     high-blast permissions — flag as a candidate for muting.

Signal tool, not a gate. Prints findings; exits 1 if any are found.

Usage:
    python3 check_zero_trust_salesforce_patterns.py --src-root .
    python3 check_zero_trust_salesforce_patterns.py --src-root force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_PROFILE_HA_RE = re.compile(
    r"<sessionSecurityLevel>\s*HIGH_ASSURANCE\s*</sessionSecurityLevel>",
    re.IGNORECASE,
)
_TSP_EVENT_RE = re.compile(
    r"<eventType>\s*(IdentityVerificationEvent|MobileEmailEvent)\s*</eventType>",
    re.IGNORECASE,
)
_TSP_ACTION_RE = re.compile(
    r"<action>\s*(Block|RequireMFA|EndSession)\s*</action>",
    re.IGNORECASE,
)
_PROFILE_HIGH_BLAST_RE = re.compile(
    r"<name>\s*(modifyAllData|viewAllData|apiEnabled|manageUsers)\s*</name>"
    r"\s*<enabled>\s*true\s*</enabled>",
    re.IGNORECASE,
)
_PSG_HIGH_BLAST_PS_RE = re.compile(
    r"<permissionSets?>\s*([^<]*?(?:Admin|Modify|ViewAll|Manage)[^<]*?)\s*</permissionSets?>",
    re.IGNORECASE,
)
_PSG_HAS_MUTING_RE = re.compile(r"<mutingPermissionSets?>", re.IGNORECASE)


def _scan_profile(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]
    if _PROFILE_HA_RE.search(text):
        findings.append(
            f"{path}: Profile sets High-Assurance session level. Move this to a "
            "Permission Set Group instead — Profile-level forces step-up too "
            "aggressively (see references/gotchas.md § 2)"
        )
    profile_high_blasts = _PROFILE_HIGH_BLAST_RE.findall(text)
    for perm in profile_high_blasts:
        findings.append(
            f"{path}: Profile grants `{perm}=true`. For zero-trust "
            "least-privilege, move high-blast permissions out of Profiles into "
            "Permission Set Groups, then mute by default "
            "(see references/gotchas.md § 4 and SKILL.md Pattern D)"
        )
    return findings


def _scan_tsp(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]
    events = _TSP_EVENT_RE.findall(text)
    actions = _TSP_ACTION_RE.findall(text)
    for evt in events:
        # Any enforcement action paired with these event types is the smell.
        if actions:
            findings.append(
                f"{path}: TSP references `{evt}` with an enforcement action — "
                f"`{evt}` is notification-only and does NOT support TSP block/MFA. "
                "Treat as detect-only (see references/gotchas.md § 1)"
            )
        else:
            # Even without a direct action capture, flag as risk.
            findings.append(
                f"{path}: TSP references `{evt}` — confirm the policy is "
                "notification-only; TSPs do NOT block on this event type "
                "(see references/gotchas.md § 1)"
            )
    return findings


def _scan_psg(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]
    if _PSG_HIGH_BLAST_PS_RE.search(text) and not _PSG_HAS_MUTING_RE.search(text):
        findings.append(
            f"{path}: Permission Set Group bundles a high-blast Permission Set "
            "but defines no Muting Permission Set. Consider defaulting to "
            "muted-by-default and JIT-granting the high-blast right "
            "(see SKILL.md Pattern D)"
        )
    return findings


def scan_tree(root: Path) -> list[str]:
    findings: list[str] = []
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    profiles = list(root.rglob("*.profile-meta.xml"))
    tsps = list(root.rglob("*.transactionSecurityPolicy-meta.xml"))
    psgs = list(root.rglob("*.permissionsetgroup-meta.xml"))

    for p in profiles:
        findings.extend(_scan_profile(p))
    for t in tsps:
        findings.extend(_scan_tsp(t))
    for g in psgs:
        findings.extend(_scan_psg(g))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for zero-trust design smells: "
            "Profile-level High-Assurance Session, TSP rules referencing "
            "unsupported event types, Profile-granted high-blast "
            "permissions, and PSGs without muting."
        ),
    )
    parser.add_argument(
        "--src-root",
        default=".",
        help="Root of the source tree to scan (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no zero-trust design smells detected.")
        return 0

    for finding in findings:
        print(f"WARN: {finding}", file=sys.stderr)
    print(
        f"\n{len(findings)} finding(s). See references/llm-anti-patterns.md "
        "and references/gotchas.md for rationale and the correct pattern.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
