#!/usr/bin/env python3
"""Checker script for the tooling-api-patterns skill.

Scans an external-tool source tree (Python, TypeScript, JavaScript) for the
most common Tooling API anti-patterns covered in this skill:

- Querying Tooling-only sObjects against the Data API endpoint
  (`/services/data/vXX.0/query/...`) instead of the Tooling endpoint
  (`/services/data/vXX.0/tooling/query/...`).
- Accessing `DeployDetails.componentFailures` without first JSON.parse /
  json.loads — the field is a JSON-encoded string.
- `while True:` / `while not done:` polling on `ContainerAsyncRequest` or
  `AsyncApexJob` without a timeout / deadline.
- Creating a `MetadataContainer`, `TraceFlag`, or `ApexExecutionOverlayAction`
  without a corresponding `DELETE` call (no cleanup).
- Inserting `TraceFlag` without a prior duplicate check (per-(user, LogType)
  uniqueness constraint).
- Hard-coded API version older than v55 (Spring '22) — likely missing recent
  Tooling API surface.

Stdlib only — no pip dependencies.

Usage:
    python3 check_tooling_api_patterns.py [--source-root path/to/tool]
    python3 check_tooling_api_patterns.py --source-root . --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TOOLING_ONLY_SOBJECTS = {
    "ApexClass", "ApexClassMember", "ApexTrigger", "ApexTriggerMember",
    "ApexCodeCoverage", "ApexCodeCoverageAggregate", "ApexLog",
    "TraceFlag", "DebugLevel",
    "ApexExecutionOverlayAction", "ApexExecutionOverlayResult",
    "EntityDefinition", "FieldDefinition",
    "FlowDefinition", "Flow",
    "ValidationRule",
    "MetadataContainer", "ContainerAsyncRequest",
    "ApexComponent", "ApexPage",
}

# Patterns we look for in source files.
DATA_QUERY_RE = re.compile(
    r"/services/data/v\d+\.\d+/query/?\?q=([^\"'`\s]+)",
    re.IGNORECASE,
)
TOOLING_QUERY_RE = re.compile(
    r"/services/data/v\d+\.\d+/tooling/query/?\?q=",
    re.IGNORECASE,
)
DEPLOYDETAILS_ACCESS_RE = re.compile(
    r"DeployDetails['\"]?\s*[\)\]]?\s*\.\s*(componentFailures|componentSuccesses|runTestResult)",
)
JSON_PARSE_RE = re.compile(
    r"(?:JSON\.parse|json\.loads)\s*\([^)]*DeployDetails",
)
WHILE_TRUE_RE = re.compile(r"\bwhile\s+(True|true|1)\s*[:{]")
WHILE_NOT_DONE_RE = re.compile(
    r"\bwhile\s+(not\s+done|!\s*done|state\s*[!=]=\s*['\"]?(Completed|Failed))",
    re.IGNORECASE,
)
TIMEOUT_HINT_RE = re.compile(
    r"\b(deadline|timeout|max[-_ ]?wait|monotonic|time\.time|Date\.now)\b",
    re.IGNORECASE,
)
CREATE_CONTAINER_RE = re.compile(r"['\"]MetadataContainer['\"]")
CREATE_TRACEFLAG_RE = re.compile(r"['\"]TraceFlag['\"]")
CREATE_OVERLAY_RE = re.compile(r"['\"]ApexExecutionOverlayAction['\"]")
DELETE_CALL_RE = re.compile(
    r"(?:\.\s*delete\s*\(|\bdestroy\s*\(|\bdel_\w+\s*\(|requests\.delete\s*\(|"
    r"session\.delete\s*\(|client\.delete\s*\(|conn\.\w+\.delete\s*\()",
)
SOQL_TRACEFLAG_QUERY_RE = re.compile(
    r"FROM\s+TraceFlag\b",
    re.IGNORECASE,
)
EXECUTE_ANONYMOUS_RE = re.compile(
    r"executeAnonymous|/tooling/executeAnonymous",
    re.IGNORECASE,
)
API_VERSION_RE = re.compile(r"/services/data/v(\d+)(?:\.\d+)?/")

DEFAULT_GLOBS = ("*.py", "*.ts", "*.js", "*.mjs", "*.cjs", "*.tsx", "*.jsx")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit external Tooling API tooling for common mistakes.",
    )
    parser.add_argument(
        "--source-root",
        default=".",
        help="Root of the tool source tree (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on any finding (default: exit non-zero only on errors).",
    )
    return parser.parse_args()


def candidate_files(root: Path) -> list[Path]:
    """All Python / TS / JS files under root, excluding common vendor dirs."""
    if not root.exists():
        return []
    skip = {"node_modules", ".git", "dist", "build", "lib", "out", ".venv", "venv", "__pycache__"}
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip for part in path.parts):
            continue
        if path.suffix in {".py", ".ts", ".js", ".mjs", ".cjs", ".tsx", ".jsx"}:
            files.append(path)
    return sorted(files)


def check_data_endpoint_misuse(text: str, path: Path) -> list[tuple[str, str]]:
    """Find Data endpoint queries that reference Tooling-only sObjects."""
    findings: list[tuple[str, str]] = []
    for match in DATA_QUERY_RE.finditer(text):
        query = match.group(1)
        # Look for FROM <Tooling-only>.
        from_match = re.search(r"FROM[\+\s]+([A-Za-z_]+)", query, re.IGNORECASE)
        if not from_match:
            continue
        sobject = from_match.group(1)
        if sobject in TOOLING_ONLY_SOBJECTS:
            findings.append((
                "ERROR",
                f"{path}: Data endpoint query references Tooling-only sObject '{sobject}'. "
                f"Use /services/data/vXX.0/tooling/query/ instead. Query: ...{match.group(0)[:100]}",
            ))
    return findings


def check_deploydetails_unparsed(text: str, path: Path) -> list[tuple[str, str]]:
    """Catch direct .componentFailures access on DeployDetails without JSON parse."""
    findings: list[tuple[str, str]] = []
    if not DEPLOYDETAILS_ACCESS_RE.search(text):
        return findings
    if JSON_PARSE_RE.search(text):
        return findings
    findings.append((
        "ERROR",
        f"{path}: accesses DeployDetails.componentFailures (or similar) without "
        "a JSON.parse/json.loads on DeployDetails. The field is a JSON-encoded string.",
    ))
    return findings


def check_unbounded_polling(text: str, path: Path) -> list[tuple[str, str]]:
    """Flag while-True / while-not-done loops on async Tooling jobs without a timeout hint."""
    findings: list[tuple[str, str]] = []
    has_loop = bool(WHILE_TRUE_RE.search(text) or WHILE_NOT_DONE_RE.search(text))
    if not has_loop:
        return findings
    # Only warn if the loop body looks like it polls a Tooling async sObject.
    polls_tooling_async = bool(re.search(
        r"\b(ContainerAsyncRequest|AsyncApexJob|ApexExecutionOverlayResult)\b",
        text,
    ))
    if not polls_tooling_async:
        return findings
    if TIMEOUT_HINT_RE.search(text):
        return findings
    findings.append((
        "WARN",
        f"{path}: polls a Tooling async resource (ContainerAsyncRequest / AsyncApexJob / "
        "ApexExecutionOverlayResult) inside a while-loop with no timeout/deadline hint. "
        "Add a max-wait ceiling.",
    ))
    return findings


def check_missing_cleanup(text: str, path: Path) -> list[tuple[str, str]]:
    """Heuristic: if MetadataContainer/TraceFlag/Overlay are created, expect a DELETE somewhere."""
    findings: list[tuple[str, str]] = []
    creates = []
    if CREATE_CONTAINER_RE.search(text) and "MetadataContainer" in text:
        creates.append("MetadataContainer")
    if CREATE_TRACEFLAG_RE.search(text) and "TraceFlag" in text:
        creates.append("TraceFlag")
    if CREATE_OVERLAY_RE.search(text) and "ApexExecutionOverlayAction" in text:
        creates.append("ApexExecutionOverlayAction")
    if not creates:
        return findings
    if not DELETE_CALL_RE.search(text):
        for sobj in creates:
            findings.append((
                "WARN",
                f"{path}: references '{sobj}' but no delete/destroy call found in the same "
                f"file. Confirm cleanup runs in a finally/try-with-resources block.",
            ))
    return findings


def check_traceflag_no_dupe_check(text: str, path: Path) -> list[tuple[str, str]]:
    """If we POST a TraceFlag, look for a prior SELECT against TraceFlag."""
    findings: list[tuple[str, str]] = []
    if not CREATE_TRACEFLAG_RE.search(text):
        return findings
    if "TraceFlag" not in text:
        return findings
    # Heuristic: look for a SOQL FROM TraceFlag in the same file.
    if SOQL_TRACEFLAG_QUERY_RE.search(text):
        return findings
    findings.append((
        "WARN",
        f"{path}: inserts TraceFlag but no SOQL query against TraceFlag found. "
        "A user can have only one active TraceFlag per LogType — query first to avoid DUPLICATE_VALUE.",
    ))
    return findings


def check_old_api_version(text: str, path: Path) -> list[tuple[str, str]]:
    """Warn on hard-coded API versions older than v55 (Spring '22)."""
    findings: list[tuple[str, str]] = []
    versions = {int(m.group(1)) for m in API_VERSION_RE.finditer(text)}
    for v in versions:
        if v < 55:
            findings.append((
                "WARN",
                f"{path}: hard-coded API version v{v}.0 detected. Tooling API tracks releases; "
                "pin to a recent version (v55+ recommended) and bump deliberately.",
            ))
            break
    return findings


def check_anonymous_apex_no_principal_note(text: str, path: Path) -> list[tuple[str, str]]:
    """Note: anonymous Apex via Tooling REST runs in caller's user context."""
    findings: list[tuple[str, str]] = []
    if not EXECUTE_ANONYMOUS_RE.search(text):
        return findings
    # If the file mentions sharing/permission-set context, assume the author has thought about it.
    if re.search(r"\b(without sharing|with sharing|permission[\s_-]?set|profile)\b", text, re.IGNORECASE):
        return findings
    findings.append((
        "WARN",
        f"{path}: invokes executeAnonymous without any reference to sharing or permission-set "
        "context. Anonymous Apex runs in the caller's user context, not as a system superuser.",
    ))
    return findings


def run_checks(root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for path in candidate_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        findings.extend(check_data_endpoint_misuse(text, path))
        findings.extend(check_deploydetails_unparsed(text, path))
        findings.extend(check_unbounded_polling(text, path))
        findings.extend(check_missing_cleanup(text, path))
        findings.extend(check_traceflag_no_dupe_check(text, path))
        findings.extend(check_old_api_version(text, path))
        findings.extend(check_anonymous_apex_no_principal_note(text, path))
    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.source_root)
    if not root.exists():
        print(f"Source root not found: {root}", file=sys.stderr)
        return 2

    findings = run_checks(root)
    if not findings:
        print("No issues found.")
        return 0

    errors = [f for f in findings if f[0] == "ERROR"]
    warns = [f for f in findings if f[0] == "WARN"]

    for severity, message in findings:
        stream = sys.stderr if severity == "ERROR" else sys.stdout
        print(f"{severity}: {message}", file=stream)

    if errors:
        return 1
    if args.strict and warns:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
