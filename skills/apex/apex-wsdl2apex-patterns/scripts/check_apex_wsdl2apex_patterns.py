#!/usr/bin/env python3
"""Checker for outbound-SOAP / wsdl2apex anti-patterns in an SFDX project.

Scans `force-app/main/default/classes/**/*.cls` for the issues documented in
`references/gotchas.md` and `references/llm-anti-patterns.md`. Reports issues
with file:line citations; exits 0 only when no issues are found.

Detection heuristics (stdlib only, regex-based — no semantic Apex parse):

  - A class is identified as a wsdl2apex-generated stub by the presence of
    two or more of `endpoint_x`, `timeout_x`, `clientCertName_x`,
    `outputHttpHeaders_x`, `inputHttpHeaders_x` declarations.
  - Classes that instantiate or use a stub are recognized by an
    assignment `<var>.endpoint_x =` or a reference to `WebServiceMock`.

Issues flagged:

  1. Literal `https://` URL assigned to `endpoint_x`
     (should be `callout:<NC>`)
  2. Stub usage without a matching `timeout_x` assignment within 10 lines
  3. `Authorization` key set in `inputHttpHeaders_x` on a code path that
     also sets `endpoint_x = 'callout:...'`
  4. `catch (CalloutException ...)` without a preceding catch for
     `WebServiceCalloutException` on the same try block
  5. `Test.setMock(HttpCalloutMock.class, ...)` in a test that references
     a SOAP type (WebServiceMock or a `_element` response class)
  6. Hand-edit markers (`// CUSTOM`, `@TestVisible`, `@AuraEnabled`) inside
     a class identified as a generated stub

Usage:
    python3 check_apex_wsdl2apex_patterns.py [--manifest-dir PATH] [--apex-dir SUBDIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


STUB_MARKERS = (
    "endpoint_x",
    "timeout_x",
    "clientCertName_x",
    "outputHttpHeaders_x",
    "inputHttpHeaders_x",
)

WSDL2APEX_GENERATED_HINTS = (
    "_type_info = new String[]",
    "private transient String endpoint_x",
    "private String[] ws_apiType",
)

ISSUE_PREFIX = "WSDL2APEX"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex source for outbound-SOAP / wsdl2apex anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Project root containing force-app/ (default: current directory).",
    )
    parser.add_argument(
        "--apex-dir",
        default="force-app/main/default/classes",
        help="Override Apex class root relative to manifest-dir.",
    )
    return parser.parse_args()


def is_stub_file(text: str) -> bool:
    marker_hits = sum(1 for m in STUB_MARKERS if m in text)
    return marker_hits >= 2


def has_generated_signature(text: str) -> bool:
    return any(h in text for h in WSDL2APEX_GENERATED_HINTS)


def find_hand_edits(path: Path, text: str) -> list[str]:
    """Flag hand-edit markers inside what looks like a generated stub."""
    issues: list[str] = []
    if not is_stub_file(text):
        return issues
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("//") and "CUSTOM" in stripped.upper():
            issues.append(
                f"{path}:{i}: {ISSUE_PREFIX}-HAND-EDIT generated stub contains 'CUSTOM' marker "
                "— customization belongs in the wrapper, not the stub"
            )
        if stripped.startswith("@TestVisible") or stripped.startswith("@AuraEnabled"):
            issues.append(
                f"{path}:{i}: {ISSUE_PREFIX}-HAND-EDIT generated stub carries '{stripped}' "
                "annotation that wsdl2apex never emits — will be lost on regen"
            )
    return issues


def find_endpoint_issues(path: Path, text: str) -> list[str]:
    """Flag literal URLs assigned to endpoint_x in wrapper classes."""
    issues: list[str] = []
    pattern = re.compile(
        r"\.endpoint_x\s*=\s*[\'\"](https?://[^\'\"]+)[\'\"]",
        re.IGNORECASE,
    )
    for i, line in enumerate(text.splitlines(), start=1):
        m = pattern.search(line)
        if m:
            issues.append(
                f"{path}:{i}: {ISSUE_PREFIX}-LITERAL-URL endpoint_x assigned literal URL "
                f"'{m.group(1)}' — use 'callout:<Named_Credential>' instead"
            )
    return issues


def find_missing_timeout(path: Path, text: str) -> list[str]:
    """Flag .endpoint_x assignment without a nearby .timeout_x assignment."""
    issues: list[str] = []
    lines = text.splitlines()
    endpoint_assign = re.compile(r"(\w+)\.endpoint_x\s*=")
    for i, line in enumerate(lines):
        m = endpoint_assign.search(line)
        if not m:
            continue
        var = m.group(1)
        # Skip field declarations (`private transient String endpoint_x` etc.)
        if "transient" in line or "private String" in line:
            continue
        window = "\n".join(lines[i : i + 11])
        timeout_pat = re.compile(rf"{re.escape(var)}\.timeout_x\s*=")
        if not timeout_pat.search(window):
            issues.append(
                f"{path}:{i+1}: {ISSUE_PREFIX}-NO-TIMEOUT stub '{var}' sets endpoint_x without "
                "timeout_x assignment within 10 lines — default of 10s is rarely correct"
            )
    return issues


def find_auth_header_with_nc(path: Path, text: str) -> list[str]:
    """Flag Authorization header set in inputHttpHeaders_x when endpoint uses callout:NC."""
    issues: list[str] = []
    if not re.search(r"\.endpoint_x\s*=\s*[\'\"]callout:", text):
        return issues
    lines = text.splitlines()
    inside = False
    for i, line in enumerate(lines, start=1):
        if "inputHttpHeaders_x" in line:
            inside = True
        if inside and re.search(r"['\"]Authorization['\"]", line, re.IGNORECASE):
            issues.append(
                f"{path}:{i}: {ISSUE_PREFIX}-AUTH-AND-NC Authorization header set in "
                "inputHttpHeaders_x while endpoint_x = 'callout:<NC>' — NC will strip it"
            )
            inside = False
        elif inside and ("}" in line or ";" in line.rstrip()):
            inside = False
    return issues


def find_callout_only_catch(path: Path, text: str) -> list[str]:
    """Flag `catch (CalloutException)` without a preceding `catch (WebServiceCalloutException)`."""
    issues: list[str] = []
    lines = text.splitlines()
    callout_pat = re.compile(r"catch\s*\(\s*(?:System\.)?CalloutException\b")
    wse_pat = re.compile(r"catch\s*\(\s*(?:System\.)?WebServiceCalloutException\b")
    for i, line in enumerate(lines):
        if not callout_pat.search(line):
            continue
        # Walk upward through the contiguous catch chain.
        j = i - 1
        saw_wse = False
        while j >= 0:
            up = lines[j].strip()
            if not up:
                j -= 1
                continue
            if "catch" in up and wse_pat.search(up):
                saw_wse = True
                break
            if "catch" in up or up.startswith("}") or up.endswith("}"):
                j -= 1
                continue
            break
        if not saw_wse:
            issues.append(
                f"{path}:{i+1}: {ISSUE_PREFIX}-CATCH-ORDER catch (CalloutException) without "
                "a preceding catch (WebServiceCalloutException) — SOAP fault metadata is lost"
            )
    return issues


def find_http_mock_in_soap_test(path: Path, text: str) -> list[str]:
    """Flag Test.setMock(HttpCalloutMock.class, ...) in tests that reference SOAP."""
    issues: list[str] = []
    if "Test.setMock(HttpCalloutMock.class" not in text:
        return issues
    soap_hint = ("WebServiceMock" in text or "_element" in text)
    if not soap_hint:
        return issues
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        if "Test.setMock(HttpCalloutMock.class" in line:
            issues.append(
                f"{path}:{i}: {ISSUE_PREFIX}-WRONG-MOCK HttpCalloutMock used in a test that "
                "references SOAP types — use Test.setMock(WebServiceMock.class, ...) instead"
            )
    return issues


def scan_directory(root: Path, apex_subdir: str) -> list[str]:
    apex_root = root / apex_subdir
    if not apex_root.exists():
        return [
            f"{root}: manifest-dir does not contain '{apex_subdir}' — "
            "is this an SFDX project? Pass --apex-dir to override."
        ]

    all_issues: list[str] = []
    for cls_file in apex_root.rglob("*.cls"):
        try:
            text = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            all_issues.append(f"{cls_file}: read error — {exc}")
            continue

        all_issues.extend(find_hand_edits(cls_file, text))

        # Skip the stub itself for wrapper-side checks (the stub
        # legitimately declares endpoint_x and timeout_x as fields).
        if is_stub_file(text) and has_generated_signature(text):
            continue

        all_issues.extend(find_endpoint_issues(cls_file, text))
        all_issues.extend(find_missing_timeout(cls_file, text))
        all_issues.extend(find_auth_header_with_nc(cls_file, text))
        all_issues.extend(find_callout_only_catch(cls_file, text))
        all_issues.extend(find_http_mock_in_soap_test(cls_file, text))

    return all_issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = scan_directory(manifest_dir, args.apex_dir)

    if not issues:
        print("No wsdl2apex anti-patterns detected.")
        return 0

    print(f"Found {len(issues)} issue(s):", file=sys.stderr)
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
