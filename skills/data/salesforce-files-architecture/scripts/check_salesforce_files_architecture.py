#!/usr/bin/env python3
"""Static checks for Salesforce Files anti-patterns.

Anti-patterns detected:

  1. New development using `Attachment` (deprecated).
  2. SOQL referencing `ContentDocument.ParentId` (field does not
     exist; use ContentDocumentLink).
  3. Direct `insert` of `ContentDocument` (platform creates it).
  4. `ContentVersion ... VersionData` SELECT without IsLatest filter.
  5. `ContentDocumentLink` insert without `Visibility`.

Stdlib only.

Findings print as `WARN:` lines and exit 0; `--strict` exits 1 on any finding.
No Apex files prints one WARN line (exit 0, 1 with --strict). A missing or
non-directory path prints `ERROR:` and exits 1.

Usage:
    python3 check_salesforce_files_architecture.py --src-root . [--strict]
    python3 check_salesforce_files_architecture.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_NEW_ATTACHMENT_RE = re.compile(
    r"new\s+Attachment\s*\(",
    re.IGNORECASE,
)

_CONTENTDOC_PARENTID_RE = re.compile(
    r"ContentDocument(\s|\.)\s*WHERE[^]]*ParentId|ContentDocument\.ParentId",
    re.IGNORECASE | re.DOTALL,
)

_INSERT_CONTENTDOC_RE = re.compile(
    r"\binsert\s+\w*ContentDocument\b(?!Link)(?!\.)",
    re.IGNORECASE,
)

_NEW_CONTENTDOC_RE = re.compile(
    r"new\s+ContentDocument\s*\(",
    re.IGNORECASE,
)

_VERSIONDATA_SOQL_RE = re.compile(
    r"\[\s*SELECT[^\]]*VersionData[^\]]*\]",
    re.IGNORECASE | re.DOTALL,
)
_ISLATEST_RE = re.compile(r"\bIsLatest\b", re.IGNORECASE)

_NEW_CDL_RE = re.compile(
    r"new\s+ContentDocumentLink\s*\(([^)]*)\)",
    re.IGNORECASE | re.DOTALL,
)
_VISIBILITY_RE = re.compile(r"\bVisibility\s*=", re.IGNORECASE)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for m in _NEW_ATTACHMENT_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: `new Attachment(...)` — "
            "Attachment is deprecated for new development. Use ContentVersion "
            "+ ContentDocumentLink (llm-anti-patterns.md § 1)."
        )

    for m in _CONTENTDOC_PARENTID_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: ContentDocument.ParentId "
            "referenced — field does not exist on ContentDocument. Join via "
            "ContentDocumentLink.LinkedEntityId instead "
            "(llm-anti-patterns.md § 3, gotchas.md § 1)."
        )

    for m in _NEW_CONTENTDOC_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: `new ContentDocument(...)` — "
            "ContentDocument is platform-created from a ContentVersion insert; "
            "do not insert it directly (llm-anti-patterns.md § 2, gotchas.md "
            "§ 2)."
        )

    for m in _VERSIONDATA_SOQL_RE.finditer(text):
        soql = m.group(0)
        if not _ISLATEST_RE.search(soql):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: ContentVersion query "
                "selecting VersionData without an IsLatest filter — returns "
                "every version per file. Add `IsLatest = true` (llm-anti-"
                "patterns.md § 4, gotchas.md § 3)."
            )

    for m in _NEW_CDL_RE.finditer(text):
        body = m.group(1)
        if not _VISIBILITY_RE.search(body):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: ContentDocumentLink "
                "constructor without `Visibility` — defaults can expose files "
                "to community / portal users. Set Visibility explicitly "
                "(llm-anti-patterns.md § 6, gotchas.md § 6)."
            )

    return findings


def apex_files(root: Path) -> list[Path]:
    return list(root.rglob("*.cls")) + list(root.rglob("*.trigger"))


def scan_tree(root: Path) -> list[str]:
    findings: list[str] = []
    for apex in apex_files(root):
        findings.extend(_scan(apex))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex source for Salesforce Files anti-patterns: legacy "
            "Attachment usage, ContentDocument.ParentId references, direct "
            "ContentDocument inserts, VersionData SOQL without IsLatest, and "
            "ContentDocumentLink inserts without Visibility."
        ),
    )
    parser.add_argument(
        "--src-root",
        "--manifest-dir",
        dest="src_root",
        default=".",
        help="Root of the Apex source tree (default: current directory). --manifest-dir is an alias.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when any finding (or the empty-directory WARN) is reported.",
    )
    args = parser.parse_args()

    root = Path(args.src_root)
    if not root.exists():
        print(f"ERROR: src-root does not exist: {root}")
        return 1
    if not root.is_dir():
        print(f"ERROR: src-root is not a directory: {root}")
        return 1
    if not apex_files(root):
        print(f"WARN: no .cls or .trigger files found under {root}")
        return 1 if args.strict else 0

    findings = scan_tree(root)

    if not findings:
        print("OK: no Salesforce Files anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
