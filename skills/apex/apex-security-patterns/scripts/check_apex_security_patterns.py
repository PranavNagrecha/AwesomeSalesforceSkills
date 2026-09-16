#!/usr/bin/env python3
"""Audit Apex files for sharing-model and CRUD/FLS enforcement risks.

Rules
-----
CRITICAL  with-security-enforced-removed   `WITH SECURITY_ENFORCED` at apiVersion >= 67.0
MEDIUM    with-security-enforced-legacy    `WITH SECURITY_ENFORCED` below 67.0 (migrate)
HIGH/MEDIUM  undeclared-sharing            public/global class with no sharing keyword
HIGH      without-sharing                  `without sharing` present
HIGH      entry-point-no-sharing           user-facing entry point, no sharing declaration
HIGH      entry-point-no-read-enforcement  entry point lacks obvious read enforcement
HIGH      entry-point-no-write-enforcement entry point DML lacks obvious write enforcement
HIGH      entry-point-system-mode          entry point opts out to system mode
REVIEW    trigger-system-mode              trigger-body operation opts out to system mode
REVIEW    elevation-without-reason         SYSTEM_MODE at 67.0+ with no nearby `// reason:`
REVIEW    stale-system-mode-claim          comment at 67.0+ asserts system-mode default
                                           (suppressed when comment or next 3 lines name
                                           SYSTEM_MODE / insertAsSystem / as system)

Every code-facing rule runs on text with `//` line comments, `/* … */` block comments,
and single-quoted string literals blanked to spaces (same length, newlines kept) so a
mention inside a comment or string cannot fire a CRITICAL/HIGH/MEDIUM. Reason-comment
and stale-claim rules read the original text.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
CLASS_RE = re.compile(r"\b(public|global)\s+(virtual\s+|abstract\s+)?(with|without|inherited)?\s*sharing?\s*class\b", re.IGNORECASE)
PUBLIC_CLASS_RE = re.compile(r"\b(public|global)\s+(virtual\s+|abstract\s+)?class\b", re.IGNORECASE)
WITHOUT_SHARING_RE = re.compile(r"\bwithout\s+sharing\b", re.IGNORECASE)
WITH_OR_INHERITED_RE = re.compile(r"\b(with|inherited)\s+sharing\b", re.IGNORECASE)
ENTRY_POINT_RE = re.compile(r"@AuraEnabled|@InvocableMethod|@RestResource", re.IGNORECASE)
# `WITH SECURITY_ENFORCED` is deliberately NOT read enforcement: it is the weaker
# clause below API 67.0 and does not compile at 67.0 and later. See SECURITY_ENFORCED_RE.
READ_ENFORCEMENT_RE = re.compile(
    r"WITH\s+USER_MODE|AccessLevel\.USER_MODE|isAccessible\s*\(", re.IGNORECASE
)
WRITE_ENFORCEMENT_RE = re.compile(
    r"stripInaccessible\s*\(|AccessLevel\.USER_MODE|\bas\s+user\b|isCreateable\s*\(|isUpdateable\s*\(",
    re.IGNORECASE,
)
SECURITY_ENFORCED_RE = re.compile(r"WITH\s+SECURITY_ENFORCED", re.IGNORECASE)
SYSTEM_MODE_RE = re.compile(r"WITH\s+SYSTEM_MODE|AccessLevel\.SYSTEM_MODE|\bas\s+system\b", re.IGNORECASE)
# Rule 2: elevation that must carry a `// reason:` — excludes `as system` (separate trigger REVIEW).
ELEVATION_RE = re.compile(r"WITH\s+SYSTEM_MODE|AccessLevel\.SYSTEM_MODE", re.IGNORECASE)
STALE_CLAIM_RE = re.compile(
    r"runs?\s+in\s+system\s+mode|system\s+mode\s+by\s+default",
    re.IGNORECASE,
)
# Negation markers that mean the comment is correcting the old default, not asserting it.
# Plain "is not" / "FLS is not checked" must NOT suppress — only claim-negating forms.
STALE_CLAIM_NEGATED_RE = re.compile(
    r"""
    \bno\s+longer\b
    | \b66\b
    | \b(?:do(?:es)?|did)\s+not\b
    | \bnot\s+(?:runs?|ran)\s+in\s+system\s+mode
    | \bnot\s+system\s+mode\s+by\s+default
    """,
    re.IGNORECASE | re.VERBOSE,
)
# Accurate descriptions of an explicit elevation (not a false default claim).
EXPLICIT_ELEVATION_DESC_RE = re.compile(
    r"SYSTEM_MODE|insertAsSystem|\bas\s+system\b",
    re.IGNORECASE,
)
API_VERSION_RE = re.compile(r"<apiVersion>\s*([0-9]+(?:\.[0-9]+)?)\s*</apiVersion>")
# API 67.0 (Summer '26) flipped the default access mode for SOQL/SOSL/DML/Database
# methods from system mode to user mode, and removed WITH SECURITY_ENFORCED.
USER_MODE_DEFAULT_API = 67.0
DML_RE = re.compile(r"\b(insert|update|upsert|delete|undelete|merge)\b", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex files for ambiguous sharing declarations and missing CRUD/FLS protections."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex classes and triggers.",
    )
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


def iter_apex_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
    )


def read_api_version(path: Path) -> float | None:
    """Return the apiVersion from the sibling .cls-meta.xml / .trigger-meta.xml, if present.

    The default access mode is gated on this value, not on the org's release: a
    Summer '26 org runs a class pinned to 58.0 with the old system-mode default.
    """
    meta = path.with_name(path.name + "-meta.xml")
    if not meta.is_file():
        return None
    match = API_VERSION_RE.search(meta.read_text(encoding="utf-8", errors="ignore"))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def strip_comments_and_literals(src: str) -> str:
    """Blank `//` line comments, `/* … */` block comments, and `'…'` literals to spaces.

    Same length as `src`; newlines inside block comments are kept as newlines so
    line numbers in the stripped text stay aligned with the original.
    """
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            out.append(" ")
            i += 1
            while i < n:
                if src[i] == "\n":
                    out.append("\n")
                    i += 1
                    break
                if src[i] == "\\" and i + 1 < n:
                    out.append(" ")
                    out.append(" ")
                    i += 2
                    continue
                if src[i] == "'":
                    # Apex doubled quote '' inside a string
                    if i + 1 < n and src[i + 1] == "'":
                        out.append(" ")
                        out.append(" ")
                        i += 2
                        continue
                    out.append(" ")
                    i += 1
                    break
                out.append(" ")
                i += 1
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == "/":
            j = i
            while j < n and src[j] != "\n":
                out.append(" ")
                j += 1
            i = j
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == "*":
            out.append(" ")
            out.append(" ")
            j = i + 2
            while j + 1 < n and not (src[j] == "*" and src[j + 1] == "/"):
                out.append("\n" if src[j] == "\n" else " ")
                j += 1
            if j + 1 < n:
                out.append(" ")
                out.append(" ")
                j += 2
            elif j < n:
                out.append("\n" if src[j] == "\n" else " ")
                j += 1
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _line_number_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _line_is_line_comment(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("//")


def statement_start_line(stripped: str, token_offset: int) -> int:
    """1-based first line of the statement that contains ``token_offset``.

    Walks back through stripped text to the previous ``;``, ``{``, or ``}``, then
    advances to the first non-whitespace character after that delimiter. Multi-line
    SOQL / ``Database.*`` calls therefore anchor on the opening line (e.g. the
    ``List<…> = [`` or ``Database.update(``), not the line that holds
    ``WITH SYSTEM_MODE`` / ``AccessLevel.SYSTEM_MODE``.
    """
    i = token_offset - 1
    while i >= 0 and stripped[i] not in ";{}":
        i -= 1
    j = i + 1
    while j < token_offset and stripped[j] in " \t\r\n":
        j += 1
    if j >= token_offset:
        return _line_number_at(stripped, token_offset)
    return _line_number_at(stripped, j)


def elevation_has_reason(original_lines: list[str], statement_line_idx: int) -> bool:
    """True when a `reason:` comment sits on the statement's first line, within the
    three lines above it, or in the contiguous `//` comment block immediately
    preceding that statement line.

    ``statement_line_idx`` is 0-based and must be the statement start (see
    ``statement_start_line``), not the elevation-token line. That way a multi-line
    SOQL whose ``WITH SYSTEM_MODE`` is several lines down still sees the ``// reason:``
    block above the opening ``List<…> = [``.
    """
    n = len(original_lines)
    if statement_line_idx < 0 or statement_line_idx >= n:
        return False

    def line_carries_reason(line: str) -> bool:
        if "reason:" not in line:
            return False
        # Same-line trailing comment: code … // reason: …
        slash = line.find("//")
        if slash != -1 and "reason:" in line[slash:]:
            return True
        # Whole line is a // comment
        if _line_is_line_comment(line) and "reason:" in line:
            return True
        return False

    # Same line + three lines above (literal rule window), anchored on statement start.
    for look in range(max(0, statement_line_idx - 3), statement_line_idx + 1):
        if line_carries_reason(original_lines[look]):
            return True

    # Contiguous preceding // comment block (skip blank lines between block and code).
    j = statement_line_idx - 1
    while j >= 0 and original_lines[j].strip() == "":
        j -= 1
    while j >= 0 and _line_is_line_comment(original_lines[j]):
        if "reason:" in original_lines[j]:
            return True
        j -= 1
    return False


def find_elevation_without_reason(
    original: str, stripped: str, api_version: float | None, path: Path
) -> list[str]:
    if api_version is None or api_version < USER_MODE_DEFAULT_API:
        return []
    findings: list[str] = []
    original_lines = original.splitlines()
    for match in ELEVATION_RE.finditer(stripped):
        token_line = _line_number_at(stripped, match.start())
        stmt_line = statement_start_line(stripped, match.start())
        if elevation_has_reason(original_lines, stmt_line - 1):
            continue
        findings.append(
            f"REVIEW {path}: system-mode elevation at line {token_line} carries no "
            "// reason: comment — state why this operation must ignore the running "
            "user's FLS/sharing (gotcha: The Default Access Mode Flipped In API 67.0)"
        )
    return findings


def iter_comments(src: str) -> list[tuple[int, str]]:
    """Return (1-based start line, comment text) for each // line and /* */ block."""
    comments: list[tuple[int, str]] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            i += 1
            while i < n:
                if src[i] == "\n":
                    i += 1
                    break
                if src[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if src[i] == "'":
                    if i + 1 < n and src[i + 1] == "'":
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == "/":
            start = i
            j = i + 2
            while j < n and src[j] != "\n":
                j += 1
            comments.append((_line_number_at(src, start), src[start:j]))
            i = j
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == "*":
            start = i
            j = i + 2
            while j + 1 < n and not (src[j] == "*" and src[j + 1] == "/"):
                j += 1
            if j + 1 < n:
                j += 2
            comments.append((_line_number_at(src, start), src[start:j]))
            i = j
            continue
        i += 1
    return comments


def comment_describes_explicit_elevation(
    original_lines: list[str], comment_start_line: int, comment_text: str
) -> bool:
    """True when the comment (or code within three lines below it) names an explicit elevation.

    Suppresses stale-claim REVIEW on accurate notes like "the insert runs in system
    mode, outside runAs(agent)" sitting directly above ``insertAsSystem`` /
    ``SYSTEM_MODE`` / ``as system``. A bare default claim with no nearby elevation
    still fires.
    """
    if EXPLICIT_ELEVATION_DESC_RE.search(comment_text):
        return True
    comment_end_line = comment_start_line + comment_text.count("\n")  # 1-based last line
    # Three lines below the comment end (1-based lines comment_end_line+1 .. +3).
    for line_1based in range(comment_end_line + 1, comment_end_line + 4):
        idx = line_1based - 1
        if idx >= len(original_lines):
            break
        if EXPLICIT_ELEVATION_DESC_RE.search(original_lines[idx]):
            return True
    return False


def find_stale_system_mode_claims(
    original: str, api_version: float | None, path: Path
) -> list[str]:
    if api_version is None or api_version < USER_MODE_DEFAULT_API:
        return []
    version_number = f"{api_version:.1f}"
    original_lines = original.splitlines()
    findings: list[str] = []
    for start_line, text in iter_comments(original):
        match = STALE_CLAIM_RE.search(text)
        if not match:
            continue
        if STALE_CLAIM_NEGATED_RE.search(text):
            continue
        if comment_describes_explicit_elevation(original_lines, start_line, text):
            continue
        # Line of the matching claim text within this comment span.
        line_no = start_line + text.count("\n", 0, match.start())
        findings.append(
            f"REVIEW {path}: comment at line {line_no} claims system-mode behaviour "
            f"that is not the default at apiVersion {version_number} (67.0+: DML/SOQL "
            "run in user mode unless WITH SYSTEM_MODE / AccessLevel.SYSTEM_MODE is "
            "stated) — correct the comment or the code"
        )
    return findings


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    code = strip_comments_and_literals(text)
    api_version = read_api_version(path)
    version_label = f"apiVersion {api_version:.1f}" if api_version is not None else "apiVersion unknown"

    if SECURITY_ENFORCED_RE.search(code):
        if api_version is not None and api_version >= USER_MODE_DEFAULT_API:
            findings.append(
                f"CRITICAL {path}: `WITH SECURITY_ENFORCED` at {version_label}; "
                "the clause was removed in API 67.0 and no longer compiles — use `WITH USER_MODE`"
            )
        else:
            findings.append(
                f"MEDIUM {path}: `WITH SECURITY_ENFORCED` found ({version_label}); it checks only the "
                "SELECT list and stops compiling at API 67.0 — migrate to `WITH USER_MODE`"
            )

    # NOTE: do not flag a trigger for carrying `WITH USER_MODE` / `WITH SYSTEM_MODE`.
    # A trigger cannot declare a *sharing* keyword, but operations inside the body do
    # take an explicit access mode, and the Apex Developer Guide documents that exact
    # pattern. Flagging it would penalise correct code.
    if path.suffix.lower() == ".trigger" and SYSTEM_MODE_RE.search(code):
        findings.append(
            f"REVIEW {path}: trigger-body operation opts out to system mode; confirm the elevation is "
            "intended and carries a `// reason:` comment (record visibility is already unrestricted here)"
        )

    if path.suffix.lower() == ".cls" and PUBLIC_CLASS_RE.search(code) and not (
        WITH_OR_INHERITED_RE.search(code) or WITHOUT_SHARING_RE.search(code)
    ):
        # At API 67.0+ an undeclared class defaults to `with sharing`, so this is an
        # explicitness defect rather than an open door. Below 67.0 it is still a real risk.
        severity = "MEDIUM" if api_version is not None and api_version >= USER_MODE_DEFAULT_API else "HIGH"
        findings.append(
            f"{severity} {path}: public/global Apex class has no explicit sharing declaration ({version_label})"
        )

    if SYSTEM_MODE_RE.search(code) and ENTRY_POINT_RE.search(code):
        findings.append(
            f"HIGH {path}: user-facing entry point opts out to system mode; justify the elevation with a "
            "`// reason:` comment or drop it"
        )

    if WITHOUT_SHARING_RE.search(code):
        findings.append(f"HIGH {path}: `without sharing` found; verify and document intentional privilege elevation")

    if ENTRY_POINT_RE.search(code) and not (WITH_OR_INHERITED_RE.search(code) or WITHOUT_SHARING_RE.search(code)):
        findings.append(f"HIGH {path}: user-facing entry point has no explicit sharing declaration")

    if ENTRY_POINT_RE.search(code) and not READ_ENFORCEMENT_RE.search(code):
        findings.append(f"HIGH {path}: user-facing entry point lacks obvious read-access enforcement (`WITH USER_MODE`, `AccessLevel.USER_MODE`, or describe checks)")

    if ENTRY_POINT_RE.search(code) and DML_RE.search(code) and not WRITE_ENFORCEMENT_RE.search(code):
        findings.append(f"HIGH {path}: user-facing entry point performs DML without obvious write-access enforcement")

    findings.extend(find_elevation_without_reason(text, code, api_version, path))
    findings.extend(find_stale_system_mode_claims(text, api_version, path))

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 Apex files; manifest directory was missing.")

    files = iter_apex_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no Apex files found"], "Scanned 0 Apex files; no .cls or .trigger files were found.")

    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))

    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} security-pattern finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
