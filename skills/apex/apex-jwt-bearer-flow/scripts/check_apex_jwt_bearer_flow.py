#!/usr/bin/env python3
"""Static checks for Apex JWT Bearer Flow anti-patterns.

Scans Apex source for the high-confidence anti-patterns documented in
`references/llm-anti-patterns.md`:

  1. Hand-rolled JWT signing (Crypto.signWithCertificate near base64
     encoding and `+ '.' +` concatenation, instead of Auth.JWS).
  2. Wrong `aud` claim — `setAud(...)` containing `.my.salesforce.com`
     for what should be `login.salesforce.com` / `test.salesforce.com`.
  3. `grant_type=password` appearing alongside JWT bearer logic.
  4. Logging the full compact JWT assertion at debug INFO/DEBUG.

Stdlib only.

Usage:
    python3 check_apex_jwt_bearer_flow.py --src-root .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


_SIGN_WITH_CERT_RE = re.compile(r"\bCrypto\.signWithCertificate\s*\(")
_BASE64URL_RE = re.compile(r"\bEncodingUtil\.base64Encode\s*\(")
_DOT_CONCAT_RE = re.compile(r"\+\s*'\.'\s*\+")
_SET_AUD_MY_DOMAIN_RE = re.compile(
    r"\.setAud\s*\(\s*'https?://[^']*\.my\.salesforce\.com[^']*'\s*\)",
    re.IGNORECASE,
)
_PASSWORD_GRANT_RE = re.compile(
    r"grant_type\s*=\s*password", re.IGNORECASE
)
_JWT_HINT_RE = re.compile(r"\bAuth\.JW[ST]\b|\bjwt\b|\bbearer\b", re.IGNORECASE)
_DEBUG_ASSERTION_RE = re.compile(
    r"System\.debug\s*\([^)]*getCompactSerialization\s*\(",
    re.IGNORECASE | re.DOTALL,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_apex(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    # 1. Hand-rolled JWT signing — three signals close together
    for m in _SIGN_WITH_CERT_RE.finditer(text):
        window = text[max(0, m.start() - 600): min(len(text), m.end() + 600)]
        if (
            _BASE64URL_RE.search(window)
            and _DOT_CONCAT_RE.search(window)
            and _JWT_HINT_RE.search(window)
        ):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: hand-rolled JWT "
                "signing detected (Crypto.signWithCertificate + "
                "base64Encode + '.' concat). Use Auth.JWT/Auth.JWS "
                "instead (references/llm-anti-patterns.md § 1)"
            )

    # 2. setAud on a My Domain
    for m in _SET_AUD_MY_DOMAIN_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: setAud(...) points at a "
            "My Domain URL — `aud` must be the token endpoint server "
            "(login.salesforce.com / test.salesforce.com) "
            "(references/llm-anti-patterns.md § 2)"
        )

    # 3. grant_type=password alongside JWT logic
    for m in _PASSWORD_GRANT_RE.finditer(text):
        if _JWT_HINT_RE.search(text):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: grant_type=password "
                "in a file that also references JWT — JWT Bearer should "
                "not have a password fallback "
                "(references/llm-anti-patterns.md § 5)"
            )

    # 4. Logging the full assertion
    for m in _DEBUG_ASSERTION_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: System.debug logging "
            "result of getCompactSerialization() — assertion is a bearer "
            "credential and must not be logged in full "
            "(references/llm-anti-patterns.md § 6)"
        )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for apex in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        findings.extend(_scan_apex(apex))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex sources for JWT Bearer anti-patterns "
            "(hand-rolled signing, wrong aud, password fallback, "
            "assertion logging)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the Apex source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Apex JWT Bearer anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
