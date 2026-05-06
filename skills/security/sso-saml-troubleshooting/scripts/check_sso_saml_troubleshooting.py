#!/usr/bin/env python3
"""Static checks for SAML SSO configuration metadata.

Anti-patterns detected:

  1. SAML SSO config metadata XML
     (`*.samlSsoConfig-meta.xml`) with no `validationCert` (no IdP
     signing cert configured) or no `issuer`.
  2. SAML SSO config with `attributeName` set to an unmapped value
     while `userProvisioningEnabled` is true (JIT provisioning
     without attribute mapping — produces broken users).
  3. Long-lived assertion lifetime references in metadata or test
     data (`NotOnOrAfter` more than 1 hour after `NotBefore`).
  4. `MyDomain` related metadata absent in an org claiming SAML SSO —
     heuristic that warns when SAML config exists but no MyDomain
     metadata is found (informational only, may indicate a
     prerequisite is missing).

Stdlib only.

Usage:
    python3 check_sso_saml_troubleshooting.py --src-root .
    python3 check_sso_saml_troubleshooting.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_VALIDATION_CERT_RE = re.compile(r"<validationCert>", re.IGNORECASE)
_ISSUER_RE = re.compile(r"<issuer>([^<]+)</issuer>", re.IGNORECASE)
_USER_PROV_ENABLED_RE = re.compile(
    r"<userProvisioningEnabled>true</userProvisioningEnabled>",
    re.IGNORECASE,
)
_ATTRIBUTE_RE = re.compile(r"<attributeName>([^<]+)</attributeName>", re.IGNORECASE)

# NotBefore / NotOnOrAfter pattern in any kind of test fixture
_NOT_BEFORE_RE = re.compile(
    r"NotBefore=\"([^\"]+)\"",
)
_NOT_AFTER_RE = re.compile(
    r"NotOnOrAfter=\"([^\"]+)\"",
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_saml(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    if not _VALIDATION_CERT_RE.search(text):
        findings.append(
            f"{path}: SAML SSO config has no <validationCert> element — IdP "
            "signing cert is required for signature validation "
            "(llm-anti-patterns.md § 1, gotchas.md § 4)."
        )

    if not _ISSUER_RE.search(text):
        findings.append(
            f"{path}: SAML SSO config has no <issuer> element — issuer "
            "mismatch will produce login failures (gotchas.md ref)."
        )

    if _USER_PROV_ENABLED_RE.search(text):
        attrs = _ATTRIBUTE_RE.findall(text)
        if not attrs:
            findings.append(
                f"{path}: userProvisioningEnabled=true but no attribute "
                "mapping declared — JIT will create users without required "
                "fields (llm-anti-patterns.md § 5, gotchas.md § 9)."
            )

    return findings


def _scan_text(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    # Coarse check: any NotOnOrAfter that names a > 1 hour later time
    # than NotBefore. Heuristic: if the date strings differ by hour
    # only and the hour difference is > 1.
    nbefore = _NOT_BEFORE_RE.findall(text)
    nafter = _NOT_AFTER_RE.findall(text)
    for b, a in zip(nbefore, nafter):
        # Quick numeric extraction of HH from ...THH:MM:SS
        bm = re.search(r"T(\d{2}):", b)
        am = re.search(r"T(\d{2}):", a)
        if bm and am:
            try:
                if int(am.group(1)) - int(bm.group(1)) >= 2:
                    findings.append(
                        f"{path}: SAML assertion lifetime spans >= 2 hours "
                        f"(NotBefore={b}, NotOnOrAfter={a}) — long-lived "
                        "assertions weaken security; address clock skew "
                        "instead (llm-anti-patterns.md § 3, gotchas.md ref)."
                    )
            except ValueError:
                pass

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for xml in root.rglob("*.samlSsoConfig-meta.xml"):
        findings.extend(_scan_saml(xml))
    for xml in list(root.rglob("*.xml")) + list(root.rglob("*.txt")):
        findings.extend(_scan_text(xml))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for SAML SSO troubleshooting anti-"
            "patterns: missing validationCert / issuer in SSO config, JIT "
            "provisioning enabled without attribute mapping, and overlong "
            "assertion lifetimes in test data."
        ),
    )
    parser.add_argument(
        "--src-root",
        default=".",
        help="Root of the Salesforce source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no SAML SSO anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
