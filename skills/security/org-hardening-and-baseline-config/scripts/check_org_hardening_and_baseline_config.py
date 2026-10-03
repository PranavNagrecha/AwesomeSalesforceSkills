#!/usr/bin/env python3
"""Audit retrieved metadata for baseline org-hardening gaps.

Parses Security.settings, CspTrustedSite, CorsWhitelistOrigin, and
ProfileSessionSetting files (Salesforce DX source or Metadata API format) and
reports findings grounded in the Metadata API Developer Guide (Summer '26):

  HIGH    clickjack protection off for Setup or non-Setup Salesforce pages
  HIGH    CSRF protection off on GET or POST
  HIGH    password complexity NoRestriction, maxLoginAttempts NoLimit, or
          minimumPasswordLength below 8 (the documented default)
  HIGH    CspTrustedSite with every isApplicable*/canAccess* flag false
          (API 59.0+ requires at least one true)
  MEDIUM  requireHttpOnly false, lockSessionsToDomain false, sessionTimeout of
          12 or 24 hours, CORS urlPattern without https://, CSP endpoint that is
          neither https:// nor wss://
  MEDIUM  ProfileSessionSetting with sessionTimeout 720 or 1440 (overrides org-wide)
  REVIEW  networkAccess present (deploy replaces ALL trusted IP ranges), CSP entry
          without a description (no owner recorded), more than 25 CSP entries

Exit codes: 1 if the directory is missing, an XML file can't be parsed, or any
HIGH finding exists (MEDIUM and REVIEW too with --strict); otherwise 0.
Prints a JSON summary. Stdlib only.

Usage:
    python3 check_org_hardening_and_baseline_config.py --manifest-dir force-app
    python3 check_org_hardening_and_baseline_config.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SEVERITY_WEIGHTS = {"ERROR": 25, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}
LONG_ORG_TIMEOUTS = {"TwelveHours", "TwentyFourHours"}
LONG_PROFILE_TIMEOUTS = {"720", "1440"}


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _child_text(parent: ET.Element, name: str) -> str | None:
    for el in parent:
        if _local(el.tag) == name:
            return (el.text or "").strip()
    return None


def _child(parent: ET.Element, name: str) -> ET.Element | None:
    for el in parent:
        if _local(el.tag) == name:
            return el
    return None


def _parse(path: Path, findings: list[tuple[str, str, str]]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(("ERROR", str(path), f"XML does not parse: {exc}"))
        return None


def _files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and any(p.name.endswith(s) for s in suffixes):
            out.append(p)
    return sorted(out)


def check_security_settings(path: Path, findings: list[tuple[str, str, str]]) -> None:
    root = _parse(path, findings)
    if root is None:
        return
    loc = str(path)
    if _child(root, "networkAccess") is not None:
        findings.append(("REVIEW", loc, "networkAccess is present: deploying it REPLACES every trusted IP range; keep the full list"))
    pw = _child(root, "passwordPolicies")
    if pw is not None:
        if _child_text(pw, "complexity") == "NoRestriction":
            findings.append(("HIGH", loc, "passwordPolicies.complexity is NoRestriction"))
        if _child_text(pw, "maxLoginAttempts") == "NoLimit":
            findings.append(("HIGH", loc, "passwordPolicies.maxLoginAttempts is NoLimit"))
        length = _child_text(pw, "minimumPasswordLength")
        if length is not None and length.isdigit() and int(length) < 8:
            findings.append(("HIGH", loc, f"passwordPolicies.minimumPasswordLength is {length}; documented default is 8"))
        if _child_text(pw, "expiration") == "Never":
            findings.append(("REVIEW", loc, "passwordPolicies.expiration is Never; confirm this matches policy"))
    ss = _child(root, "sessionSettings")
    if ss is not None:
        for field, label in (("enableClickjackSetup", "clickjack protection for Setup pages"),
                             ("enableClickjackNonsetupSFDC", "clickjack protection for non-Setup Salesforce pages"),
                             ("enableCSRFOnGet", "CSRF protection on GET"),
                             ("enableCSRFOnPost", "CSRF protection on POST")):
            if _child_text(ss, field) == "false":
                findings.append(("HIGH", loc, f"sessionSettings.{field} is false ({label} off)"))
        if _child_text(ss, "requireHttpOnly") == "false":
            findings.append(("MEDIUM", loc, "sessionSettings.requireHttpOnly is false; session cookie readable by JavaScript"))
        if _child_text(ss, "lockSessionsToDomain") == "false":
            findings.append(("MEDIUM", loc, "sessionSettings.lockSessionsToDomain is false"))
        timeout = _child_text(ss, "sessionTimeout")
        if timeout in LONG_ORG_TIMEOUTS:
            findings.append(("MEDIUM", loc, f"sessionSettings.sessionTimeout is {timeout}"))


def check_csp(paths: list[Path], findings: list[tuple[str, str, str]]) -> None:
    if len(paths) > 25:
        findings.append(("REVIEW", str(paths[0].parent), f"{len(paths)} CSP Trusted Sites; keep the CSP header under 12 KB and review sprawl"))
    for path in paths:
        root = _parse(path, findings)
        if root is None:
            continue
        loc = str(path)
        url = _child_text(root, "endpointUrl") or ""
        if url and not (url.startswith("https://") or url.startswith("wss://") or url.startswith("*.")):
            findings.append(("MEDIUM", loc, f"endpointUrl '{url}' is not https:// or wss://"))
        flags = [(_local(el.tag), (el.text or "").strip()) for el in root
                 if _local(el.tag).startswith("isApplicable") or _local(el.tag).startswith("canAccess")]
        if flags and all(v == "false" for _, v in flags):
            findings.append(("HIGH", loc, "every isApplicable*/canAccess* flag is false; API 59.0+ requires at least one true"))
        if not (_child_text(root, "description") or ""):
            findings.append(("REVIEW", loc, "no description: record owner, purpose, and review date"))


def check_cors(paths: list[Path], findings: list[tuple[str, str, str]]) -> None:
    for path in paths:
        root = _parse(path, findings)
        if root is None:
            continue
        pattern = _child_text(root, "urlPattern") or ""
        if pattern and not pattern.startswith(("https://", "chrome-extension://", "moz-extension://")):
            findings.append(("MEDIUM", str(path), f"urlPattern '{pattern}' must use https:// (or a browser-extension prefix)"))


def check_profile_sessions(paths: list[Path], findings: list[tuple[str, str, str]]) -> None:
    for path in paths:
        root = _parse(path, findings)
        if root is None:
            continue
        timeout = _child_text(root, "sessionTimeout")
        if timeout in LONG_PROFILE_TIMEOUTS:
            findings.append(("MEDIUM", str(path), f"profile sessionTimeout {timeout} minutes overrides the org-wide timeout"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check retrieved metadata for baseline org-hardening gaps.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of retrieved metadata.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on MEDIUM and REVIEW findings too.")
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    findings: list[tuple[str, str, str]] = []
    security = _files(root, ("Security.settings-meta.xml", "Security.settings"))
    csp = _files(root, (".cspTrustedSite-meta.xml", ".cspTrustedSite"))
    cors = _files(root, (".corsWhitelistOrigin-meta.xml", ".corsWhitelistOrigin", ".corswhitelistorigin"))
    profile_sessions = _files(root, (".profileSessionSetting-meta.xml", ".profileSessionSetting"))

    for path in security:
        check_security_settings(path, findings)
    check_csp(csp, findings)
    check_cors(cors, findings)
    check_profile_sessions(profile_sessions, findings)

    scanned = len(security) + len(csp) + len(cors) + len(profile_sessions)
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(s, 0) for s, _, _ in findings))
    summary = (f"Scanned {len(security)} Security.settings, {len(csp)} CspTrustedSite, {len(cors)} CorsWhitelistOrigin, "
               f"and {len(profile_sessions)} ProfileSessionSetting file(s); {len(findings)} finding(s).")
    print(json.dumps({"score": score,
                      "findings": [{"severity": s, "location": l, "message": m} for s, l, m in findings],
                      "summary": summary}, indent=2))
    if scanned == 0:
        print("WARN: no hardening metadata found; retrieve Settings:Security, CspTrustedSite, CorsWhitelistOrigin first",
              file=sys.stderr)
        return 0
    blocking = {"ERROR", "HIGH"} | ({"MEDIUM", "REVIEW"} if args.strict else set())
    return 1 if any(s in blocking for s, _, _ in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
