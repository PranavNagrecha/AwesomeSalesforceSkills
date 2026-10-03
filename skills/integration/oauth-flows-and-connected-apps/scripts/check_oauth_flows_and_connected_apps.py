#!/usr/bin/env python3
"""Audit OAuth, connected-app, and external-client-app usage for weak integration patterns.

Stdlib only. Rules added 2026-10-03 are grounded on the Identity guide (Spring '26:
Client Credentials, JWT Bearer, Block Authorization Flows) and the Metadata API
Developer Guide v67.0 (ExtlClntAppGlobalOauthSettings, ExtlClntAppOauthConfigurablePolicies,
OauthOidcSettings):

  HIGH    username-password grant (grant_type=password)
  HIGH    hardcoded secret or bearer token, including <consumerSecret> in metadata
  HIGH    ExtlClntAppGlobalOauthSettings file present in the tree (must not be in source control)
  HIGH    client credentials enabled in policies with no clientCredentialsFlowUser
  MEDIUM  broad `full` scope
  MEDIUM  scope parameter on a client_credentials or jwt-bearer token request (ignored by Salesforce)
  MEDIUM  OauthOidcSettings leaves the username-password or user-agent flow unblocked
  MEDIUM  permittedUsersPolicyType AllSelfAuthorized on a client-credentials app
  LOW     refreshTokenPolicyType Infinite

Usage:
    python3 check_oauth_flows_and_connected_apps.py --manifest-dir force-app/main/default
    python3 check_oauth_flows_and_connected_apps.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


USERNAME_PASSWORD_RE = re.compile(r"grant_type\s*[=:]\s*[\"']password[\"']|grant_type=password|username-password", re.IGNORECASE)
FULL_SCOPE_RE = re.compile(r"scope[^\n]{0,80}\bfull\b", re.IGNORECASE)
HARDCODED_SECRET_RE = re.compile(r"(client_secret|consumersecret|refresh_token|access_token)\s*[=:]\s*[\"'][^\"']+[\"']", re.IGNORECASE)
TOKEN_LITERAL_RE = re.compile(r"Bearer\s+[A-Za-z0-9._-]{16,}", re.IGNORECASE)
XML_SECRET_RE = re.compile(r"<consumerSecret>\s*[^<\s]+\s*</consumerSecret>", re.IGNORECASE)
SCOPE_ON_TOKEN_RE = re.compile(r"grant_type=(client_credentials|urn:ietf:params:oauth:grant-type:jwt-bearer)[^'\"\n]*&scope=|scope=[^&'\"\n]*&grant_type=(client_credentials|urn:ietf)", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check code and config for weak OAuth flow and secret handling patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for source and metadata files.")
    parser.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    return parser.parse_args()


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def iter_files(root: Path) -> list[Path]:
    allowed = {".cls", ".js", ".ts", ".xml", ".json", ".yml", ".yaml", ".properties"}
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in allowed)


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    if USERNAME_PASSWORD_RE.search(text):
        findings.append(f"HIGH {path}: username-password OAuth flow pattern detected; blocked by default in orgs created Summer '23 or later and unsupported by external client apps")
    if FULL_SCOPE_RE.search(text):
        findings.append(f"MEDIUM {path}: broad `full` OAuth scope detected; confirm least-privilege need")
    if HARDCODED_SECRET_RE.search(text) or TOKEN_LITERAL_RE.search(text) or XML_SECRET_RE.search(text):
        findings.append(f"HIGH {path}: apparent hardcoded OAuth secret or bearer token detected")
    if SCOPE_ON_TOKEN_RE.search(text):
        findings.append(f"MEDIUM {path}: scope parameter sent on a client_credentials or jwt-bearer token request; Salesforce takes scopes from the app configuration, not the token call")
    if "<ExtlClntAppGlobalOauthSettings" in text:
        findings.append(f"HIGH {path}: ExtlClntAppGlobalOauthSettings is in the tree; the Metadata API guide says it must not be added to source control")
    if "<ExtlClntAppOauthConfigurablePolicies" in text:
        cc_on = re.search(r"<isClientCredentialsFlowEnabled>\s*true\s*<", text, re.IGNORECASE)
        if cc_on and "<clientCredentialsFlowUser>" not in text:
            findings.append(f"HIGH {path}: client credentials flow enabled with no clientCredentialsFlowUser; tokens need an execution user with the API Only permission")
        if cc_on and re.search(r"<permittedUsersPolicyType>\s*AllSelfAuthorized\s*<", text):
            findings.append(f"MEDIUM {path}: AllSelfAuthorized on a client-credentials app; prefer AdminApprovedPreAuthorized with a permission set")
        if re.search(r"<refreshTokenPolicyType>\s*Infinite\s*<", text):
            findings.append(f"LOW {path}: refreshTokenPolicyType Infinite; document why refresh tokens never expire")
    if "<OauthOidcSettings" in text:
        for tag, label in (("blockOAuthUnPwFlow", "username-password"), ("blockOAuthUsrAgtFlow", "user-agent")):
            if not re.search(rf"<{tag}>\s*true\s*</{tag}>", text):
                findings.append(f"MEDIUM {path}: OauthOidcSettings does not block the {label} flow; the Identity guide recommends blocking it after testing in a sandbox")
    return findings


def self_test() -> int:
    here = Path(__file__).resolve().parent / "fixtures"
    good = [f for p in iter_files(here / "good") for f in audit_file(p)]
    bad = [f for p in iter_files(here / "bad") for f in audit_file(p)]
    expected = ["username-password OAuth flow", "hardcoded OAuth secret", "must not be added to source control",
                "no clientCredentialsFlowUser", "scope parameter sent", "AllSelfAuthorized", "Infinite",
                "does not block the username-password", "does not block the user-agent"]
    missing = [e for e in expected if not any(e in f for f in bad)]
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for f in good:
        print(f"  unexpected: {f}")
    print(f"bad fixtures: {len(bad)} finding(s); missing expected: {missing or 'none'}")
    return 0 if not good and not missing else 1


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 files; manifest directory was missing.")
    files = iter_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no relevant files found"], "Scanned 0 files; no OAuth-relevant source or metadata files were found.")
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    summary = f"Scanned {len(files)} file(s); {len(findings)} OAuth finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
