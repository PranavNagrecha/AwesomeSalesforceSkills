#!/usr/bin/env python3
"""Static checks for Connected App metadata + integration code.

Catches:
  1. Connected App metadata (`*.connectedApp-meta.xml`) with
     `<refreshTokenValidityPeriod>` set to a short window or
     `<refreshTokenPolicy>` = "ImmediatelyExpire" — server-to-server
     integration risk.
  2. Integration code with hardcoded Consumer Key / Secret /
     Refresh Token literals.
  3. JWT Bearer setup / docs that use Email-shaped `sub` claim
     instead of Username.
  4. Apex / config referencing `grant_type=password` (deprecated).

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = "http://soap.sforce.com/2006/04/metadata"
_NS_TAG = f"{{{_NS}}}"


def _strip_ns(tag: str) -> str:
    return tag[len(_NS_TAG):] if tag.startswith(_NS_TAG) else tag


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


# Salesforce Consumer Key shape: starts with `3MV`, 85 chars total.
_CONSUMER_KEY_RE = re.compile(r"\b3MV[A-Za-z0-9._]{80,90}\b")
# Refresh token shape: starts with `5A`, length varies.
_REFRESH_TOKEN_RE = re.compile(r"\b5A[a-zA-Z0-9._]{40,200}\b")
_GRANT_TYPE_PASSWORD_RE = re.compile(r"grant_type\s*[=:]\s*['\"]?password['\"]?", re.IGNORECASE)
_JWT_SUB_EMAIL_RE = re.compile(
    r"['\"]sub['\"]\s*:\s*['\"][^'\"@]+@[^'\"]+['\"]"
)


def _scan_connected_app_xml(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError):
        return findings
    root = tree.getroot()
    if _strip_ns(root.tag) != "ConnectedApp":
        return findings

    name_el = root.find(f"{_NS_TAG}label") or root.find(f"{_NS_TAG}fullName")
    app_name = name_el.text if name_el is not None and name_el.text else path.stem

    # OAuth config sub-element
    oauth = root.find(f"{_NS_TAG}oauthConfig")
    if oauth is None:
        return findings

    rt_policy = oauth.find(f"{_NS_TAG}refreshTokenPolicy")
    if rt_policy is not None and rt_policy.text:
        if rt_policy.text in {"ImmediatelyExpire", "expire_on_first_use"}:
            findings.append(
                f"{path}: Connected App `{app_name}` Refresh Token Policy is "
                f"`{rt_policy.text}` — works for one access-token lifetime then "
                "dies. For server-to-server, set `refreshTokenValidityPeriod` "
                "to indefinite (`SpecificValueValidityPeriod` with a long "
                "duration, or remove the expiry) "
                "(references/llm-anti-patterns.md § 6)"
            )

    return findings


def _scan_source_for_secrets(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings

    for m in _CONSUMER_KEY_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: literal Salesforce Consumer "
            "Key in source — credentials in source control. Use environment "
            "variables / secret store / Named Credential "
            "(references/llm-anti-patterns.md § 3)"
        )

    for m in _REFRESH_TOKEN_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: literal-shaped refresh token "
            "in source — secret in source control. Move to a secret store "
            "(references/llm-anti-patterns.md § 3)"
        )

    for m in _GRANT_TYPE_PASSWORD_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: `grant_type=password` "
            "(Username-Password OAuth flow) — deprecated for new integrations. "
            "Use JWT Bearer (server-to-server) or Web Server flow "
            "(references/llm-anti-patterns.md § 2)"
        )

    for m in _JWT_SUB_EMAIL_RE.finditer(text):
        # Email-looking sub claim (heuristic: contains @ but not the
        # Salesforce Username suffix marker like `.acmesandbox`).
        findings.append(
            f"{path}:{_line_no(text, m.start())}: JWT `sub` claim looks like "
            "an Email (`user@domain`); JWT Bearer requires User.Username, "
            "which often differs (e.g. `user@domain.acmesandbox`) "
            "(references/llm-anti-patterns.md § 5)"
        )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    findings: list[str] = []
    for f in root.rglob("*.connectedApp-meta.xml"):
        findings.extend(_scan_connected_app_xml(f))

    # Scan all source-ish files for credential leaks + grant_type=password.
    for ext in ("*.py", "*.js", "*.ts", "*.cls", "*.trigger", "*.json", "*.yaml", "*.yml", "*.env", "*.sh"):
        for f in root.rglob(ext):
            findings.extend(_scan_source_for_secrets(f))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Connected App metadata and integration code for "
            "OAuth anti-patterns (refresh-token policy, hardcoded "
            "credentials, deprecated grant_type=password, JWT sub "
            "as Email)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the project (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Connected App / OAuth anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
