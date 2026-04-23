#!/usr/bin/env python3
"""Audit Apex files for encoding, hashing, and crypto anti-patterns.

Scans .cls and .trigger files for:
- weak algorithms (MD5, SHA-1, HmacMD5, HmacSHA1) used in Crypto calls
- hardcoded HMAC secrets / private key literals
- standard base64 in JWT-like concatenations without base64url transform
- MAC comparison via == without constant-time wrapper
- Crypto.encrypt with a fixed IV (vs encryptWithManagedIV)
- Math.random() used near nonce / token / verifier identifiers
- Blob.toString() on a value that came from Crypto.*

stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {".cls", ".trigger"}

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

WEAK_ALGO_RE = re.compile(
    r"Crypto\.(?:generateDigest|generateMac|sign(?:WithCertificate)?)"
    r"\s*\(\s*'(HmacMD5|HmacSHA1|MD5|SHA1|SHA-1)'",
    re.IGNORECASE,
)
HARDCODED_SECRET_RE = re.compile(
    r"(secret|signingKey|apiKey|hmacKey|webhookSecret|privateKey)\s*=\s*'[^']{8,}'",
    re.IGNORECASE,
)
PEM_LITERAL_RE = re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----", re.IGNORECASE)
BASE64_IN_JWT_RE = re.compile(
    r"EncodingUtil\.base64Encode\s*\([^)]*\)(?![^;]*?replace\s*\(\s*'\+'\s*,)",
    re.IGNORECASE,
)
JWT_CONCAT_RE = re.compile(
    r"base64Encode[^;]*\+\s*['\"]\.['\"]\s*\+\s*base64Encode", re.IGNORECASE
)
EQ_COMPARE_RE = re.compile(
    r"(convertToHex|base64Encode)\s*\([^)]*\)\s*==\s*\w+", re.IGNORECASE
)
FIXED_IV_RE = re.compile(
    r"Crypto\.encrypt\s*\(\s*'AES\d+'\s*,\s*\w+\s*,\s*(Blob\.valueOf\s*\(\s*'[^']+'\s*\)|\w+\s*,)",
    re.IGNORECASE,
)
MATH_RANDOM_SEC_RE = re.compile(
    r"(?:nonce|token|verifier|csrf|otp|session)\w*\s*=\s*[^;]*Math\.random\s*\(",
    re.IGNORECASE,
)
BLOB_TOSTRING_ON_CRYPTO_RE = re.compile(
    r"(Crypto\.(?:generateDigest|generateMac|sign(?:WithCertificate)?|encrypt(?:WithManagedIV)?|decrypt(?:WithManagedIV)?)\s*\([^;]*?\))\s*\.\s*toString\s*\(",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Apex for encoding / crypto anti-patterns."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex classes and triggers.",
    )
    return parser.parse_args()


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location, message = "", remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(f) for f in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(n["severity"], 0) for n in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def iter_apex_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES
    )


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings

    if WEAK_ALGO_RE.search(text):
        findings.append(f"HIGH {path}: weak algorithm (MD5/SHA-1/HmacMD5/HmacSHA1) used in Crypto call")

    if HARDCODED_SECRET_RE.search(text):
        findings.append(f"HIGH {path}: hardcoded secret literal near secret/key/token identifier; move to Named Credential or protected CMT")

    if PEM_LITERAL_RE.search(text):
        findings.append(f"CRITICAL {path}: private key PEM literal in Apex; import into Setup → Certificate and Key Management and use signWithCertificate")

    if JWT_CONCAT_RE.search(text) and ".replace('+'" not in text and ".replace('/', '_')" not in text:
        findings.append(f"HIGH {path}: JWT-like concatenation uses standard base64 but no base64url transform (`replace('+', '-')` etc.)")

    if EQ_COMPARE_RE.search(text):
        findings.append(f"HIGH {path}: MAC / signature compared with `==` on encoded value; use a constant-time compare")

    if FIXED_IV_RE.search(text):
        findings.append(f"HIGH {path}: `Crypto.encrypt` with a literal/reused IV; prefer `encryptWithManagedIV`")

    if MATH_RANDOM_SEC_RE.search(text):
        findings.append(f"HIGH {path}: `Math.random()` used for security-relevant identifier (nonce/token/verifier); use `Crypto.getRandomInteger`")

    if BLOB_TOSTRING_ON_CRYPTO_RE.search(text):
        findings.append(f"HIGH {path}: `Blob.toString()` called directly on Crypto output; encode with `base64Encode` or `convertToHex` first")

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result(
            [f"HIGH {root}: manifest directory not found"],
            "Scanned 0 Apex files; manifest directory was missing.",
        )

    files = iter_apex_files(root)
    if not files:
        return emit_result(
            [f"REVIEW {root}: no Apex files found"],
            "Scanned 0 Apex files; no .cls or .trigger files were found.",
        )

    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))

    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} crypto/encoding finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
