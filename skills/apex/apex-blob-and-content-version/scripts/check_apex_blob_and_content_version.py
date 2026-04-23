#!/usr/bin/env python3
"""Checker for Apex files that handle Blob and ContentVersion.

Flags the six highest-signal mistakes captured in references/llm-anti-patterns.md:

  1. ContentVersion insert without FirstPublishLocationId AND without a
     companion ContentDocumentLink insert (orphaned file).
  2. ContentVersion constructor setting BOTH ContentDocumentId and
     FirstPublishLocationId (silently ignored).
  3. SOQL on ContentVersion that omits VersionData while code reads it.
  4. new Attachment(...) usage in any Apex file (prefer ContentVersion).
  5. @AuraEnabled method that accepts a base64 body without a size guard.
  6. EncodingUtil.base64Decode applied to a value that likely came from an
     LWC file reader without stripping the `data:...;base64,` prefix.

Stdlib only. Emits JSON so the skill-builder pipeline can score runs.

Usage:
    python3 check_apex_blob_and_content_version.py --path force-app/main/default
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

CONTENT_VERSION_CTOR = re.compile(r"new\s+ContentVersion\s*\(", re.IGNORECASE)
FIRST_PUBLISH = re.compile(r"FirstPublishLocationId", re.IGNORECASE)
CONTENT_DOCUMENT_ID = re.compile(r"\bContentDocumentId\s*=", re.IGNORECASE)
CONTENT_DOCUMENT_LINK = re.compile(r"new\s+ContentDocumentLink\s*\(", re.IGNORECASE)
ATTACHMENT_CTOR = re.compile(r"new\s+Attachment\s*\(", re.IGNORECASE)
AURA_ENABLED = re.compile(r"@AuraEnabled\b", re.IGNORECASE)
BASE64_DECODE = re.compile(r"EncodingUtil\.base64Decode\s*\(([^)]*)\)", re.IGNORECASE)
DATA_URL_STRIP = re.compile(
    r"(startsWith\s*\(\s*['\"]data:|substringAfter\s*\(\s*['\"],['\"])",
    re.IGNORECASE,
)
SOQL_CONTENT_VERSION = re.compile(
    r"SELECT\s+(?P<fields>[^\}]+?)\s+FROM\s+ContentVersion",
    re.IGNORECASE | re.DOTALL,
)
VERSION_DATA_READ = re.compile(r"\.VersionData\b")
BASE64_PARAM_HINT = re.compile(
    r"(String\s+\w*(?:base64|b64|body|data)\w*)", re.IGNORECASE
)
SIZE_GUARD = re.compile(
    r"(\.size\s*\(\s*\)\s*[<>=!]|Limit\.getHeapSize|>\s*\d{6,})",
    re.IGNORECASE,
)


def apex_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.cls"):
        if "__tests__" in path.parts or path.name.endswith("_Test.cls"):
            continue
        yield path
    for path in root.rglob("*.trigger"):
        yield path


def find_ctor_blocks(text: str, ctor: re.Pattern[str]) -> list[tuple[int, str]]:
    blocks: list[tuple[int, str]] = []
    for match in ctor.finditer(text):
        start = match.start()
        depth = 0
        i = match.end() - 1
        while i < len(text):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    blocks.append((start, text[start : i + 1]))
                    break
            i += 1
    return blocks


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def check_file(path: Path) -> list[dict]:
    issues: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    for start, block in find_ctor_blocks(text, CONTENT_VERSION_CTOR):
        line = line_of(text, start)
        has_first_publish = bool(FIRST_PUBLISH.search(block))
        has_doc_id = bool(CONTENT_DOCUMENT_ID.search(block))
        if has_first_publish and has_doc_id:
            issues.append(
                {
                    "severity": "HIGH",
                    "rule": "both-content-doc-id-and-first-publish",
                    "file": str(path),
                    "line": line,
                    "message": (
                        "ContentVersion constructor sets both ContentDocumentId and "
                        "FirstPublishLocationId; FirstPublishLocationId is silently ignored. "
                        "Insert a separate ContentDocumentLink for the additional record."
                    ),
                }
            )
        if not has_first_publish and not has_doc_id:
            if not CONTENT_DOCUMENT_LINK.search(text):
                issues.append(
                    {
                        "severity": "HIGH",
                        "rule": "orphaned-content-version",
                        "file": str(path),
                        "line": line,
                        "message": (
                            "ContentVersion insert has no FirstPublishLocationId and no "
                            "companion ContentDocumentLink — the file will land in the "
                            "uploader's private library."
                        ),
                    }
                )

    for match in SOQL_CONTENT_VERSION.finditer(text):
        fields = match.group("fields")
        if "VersionData" not in fields and VERSION_DATA_READ.search(text):
            issues.append(
                {
                    "severity": "HIGH",
                    "rule": "version-data-not-selected",
                    "file": str(path),
                    "line": line_of(text, match.start()),
                    "message": (
                        "SOQL on ContentVersion omits VersionData but code reads "
                        "cv.VersionData elsewhere; the field is excluded by default "
                        "and will be null."
                    ),
                }
            )

    for match in ATTACHMENT_CTOR.finditer(text):
        issues.append(
            {
                "severity": "MEDIUM",
                "rule": "legacy-attachment-usage",
                "file": str(path),
                "line": line_of(text, match.start()),
                "message": (
                    "new Attachment(...) in new code — prefer ContentVersion + "
                    "ContentDocumentLink for version history, preview, and mobile parity."
                ),
            }
        )

    for match in AURA_ENABLED.finditer(text):
        trailing = text[match.end() : match.end() + 400]
        if BASE64_PARAM_HINT.search(trailing) and not SIZE_GUARD.search(trailing):
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "aura-base64-without-size-guard",
                    "file": str(path),
                    "line": line_of(text, match.start()),
                    "message": (
                        "@AuraEnabled method accepts a base64 body without a visible "
                        "size guard. Aura payloads cap around 4–6 MB; reject oversize "
                        "uploads and route large files through lightning-file-upload."
                    ),
                }
            )

    for match in BASE64_DECODE.finditer(text):
        arg = match.group(1).strip()
        if not arg:
            continue
        var = re.split(r"[.\[\s,]", arg, maxsplit=1)[0]
        window_start = max(0, match.start() - 400)
        window = text[window_start : match.start()]
        if not DATA_URL_STRIP.search(window) and re.search(
            r"(AuraEnabled|lightning|@RestResource|LWC|FileReader)", text, re.IGNORECASE
        ):
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "base64-data-url-prefix-not-stripped",
                    "file": str(path),
                    "line": line_of(text, match.start()),
                    "message": (
                        f"EncodingUtil.base64Decode({var}) called without evidence of a "
                        "`data:...;base64,` prefix strip. Browser FileReader payloads "
                        "include the prefix and will decode to garbage."
                    ),
                }
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint Apex files for Blob and ContentVersion mistakes.",
    )
    parser.add_argument(
        "--path",
        default="force-app/main/default",
        help="Root directory to scan (default: force-app/main/default).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.path)
    if not root.exists():
        print(json.dumps({"error": f"path not found: {root}"}))
        return 2

    issues: list[dict] = []
    for apex_path in apex_files(root):
        issues.extend(check_file(apex_path))

    score = sum(SEVERITY_WEIGHTS.get(i["severity"], 0) for i in issues)

    if args.format == "json":
        print(json.dumps({"score": score, "issues": issues}, indent=2))
    else:
        for issue in issues:
            print(
                f"{issue['severity']:8} {issue['file']}:{issue['line']}  "
                f"[{issue['rule']}] {issue['message']}"
            )
        print(f"\nTotal weighted score: {score}")

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
