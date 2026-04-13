#!/usr/bin/env python3
"""Checker script for DevOps Process Documentation skill.

Validates that deployment runbooks and environment matrices in a given directory
meet the structural requirements defined in the skill. Checks for required sections,
Named Credential re-entry steps, rollback decision gates, and environment matrix columns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_devops_process_documentation.py [--help]
    python3 check_devops_process_documentation.py --manifest-dir path/to/runbooks/
    python3 check_devops_process_documentation.py --file path/to/runbook.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Required structural elements
# ---------------------------------------------------------------------------

RUNBOOK_REQUIRED_SECTIONS = [
    "pre-deploy",
    "post-deploy",
    "rollback",
    "smoke test",
]

RUNBOOK_NAMED_CRED_KEYWORDS = [
    "named credential",
    "namedcredential",
    "external credential",
    "externalcredential",
]

RUNBOOK_CREDENTIAL_REENTRY_KEYWORDS = [
    "re-enter",
    "reenter",
    "credential",
    "password",
    "setup > security",
    "named credentials",
]

ENVIRONMENT_MATRIX_REQUIRED_COLUMNS = [
    "org name",
    "org type",
    "purpose",
    "refresh cadence",
    "data policy",
    "owner",
]

RELEASE_PLAN_ANTI_PATTERN_HEADINGS = [
    r"^#+\s*(scope|stakeholders?|timeline|risk register|project schedule)",
]


# ---------------------------------------------------------------------------
# Checker functions
# ---------------------------------------------------------------------------

def check_runbook_file(path: Path) -> list[str]:
    """Return issues found in a single runbook Markdown file."""
    issues: list[str] = []
    text = path.read_text(encoding="utf-8").lower()

    # 1. Required sections present
    for section in RUNBOOK_REQUIRED_SECTIONS:
        if section not in text:
            issues.append(
                f"[{path.name}] Missing required runbook section: '{section}'. "
                "Runbooks must include pre-deploy gate, post-deploy validation, "
                "smoke tests, and rollback decision gate."
            )

    # 2. If integration metadata is referenced, credential re-entry must be present
    has_named_cred_reference = any(kw in text for kw in RUNBOOK_NAMED_CRED_KEYWORDS)
    has_credential_reentry = any(kw in text for kw in RUNBOOK_CREDENTIAL_REENTRY_KEYWORDS)

    if has_named_cred_reference and not has_credential_reentry:
        issues.append(
            f"[{path.name}] Named Credential or External Credential is referenced but no "
            "re-entry step was found. The Metadata API does not transfer secret values. "
            "Add an explicit post-deploy credential re-entry step with field-level detail."
        )

    # 3. Rollback must have a decision owner and procedure (not just a single checklist item)
    rollback_section = _extract_section(text, "rollback")
    if rollback_section and len(rollback_section.strip().splitlines()) < 3:
        issues.append(
            f"[{path.name}] Rollback section appears to be a single line. "
            "A valid rollback decision gate must include: decision owner, go/no-go threshold, "
            "rollback procedure steps, and estimated time. Expand the rollback section."
        )

    # 4. Anti-pattern: release plan headings inside a runbook
    for pattern in RELEASE_PLAN_ANTI_PATTERN_HEADINGS:
        if re.search(pattern, text, re.MULTILINE):
            issues.append(
                f"[{path.name}] Document appears to contain release plan content "
                f"(matched heading pattern: '{pattern}'). "
                "A deployment runbook must not contain scope narrative, stakeholder lists, "
                "or project timeline. Separate the release plan from the runbook."
            )

    return issues


def check_environment_matrix_file(path: Path) -> list[str]:
    """Return issues found in an environment matrix Markdown file."""
    issues: list[str] = []
    text = path.read_text(encoding="utf-8").lower()

    # Check for required columns in at least one Markdown table
    table_lines = [line for line in text.splitlines() if "|" in line]
    if not table_lines:
        issues.append(
            f"[{path.name}] No Markdown table found. "
            "An environment matrix must be structured as a Markdown table."
        )
        return issues

    header_line = " ".join(table_lines[:2])  # join first two lines (header + separator)
    for column in ENVIRONMENT_MATRIX_REQUIRED_COLUMNS:
        if column not in header_line:
            issues.append(
                f"[{path.name}] Environment matrix is missing required column: '{column}'. "
                f"Required columns: {', '.join(ENVIRONMENT_MATRIX_REQUIRED_COLUMNS)}."
            )

    # Check for data policy — must be specific, not just "no PII"
    if "data policy" in header_line:
        data_policy_cells = _extract_column_values(text, "data policy")
        vague_entries = [v for v in data_policy_cells if v.strip() in ("no pii", "n/a", "", "-")]
        if vague_entries:
            issues.append(
                f"[{path.name}] One or more 'Data Policy' cells are too vague "
                f"({', '.join(repr(v) for v in vague_entries)}). "
                "Each cell must specify one of: 'Synthetic only', 'Anonymized prod', "
                "'Full prod copy', or 'No prod data permitted'."
            )

    return issues


def check_deployment_guide_file(path: Path) -> list[str]:
    """Return issues found in a deployment guide Markdown file."""
    issues: list[str] = []
    text = path.read_text(encoding="utf-8").lower()

    required_sections = ["promotion path", "approval", "rollback", "manual step"]
    for section in required_sections:
        if section not in text:
            issues.append(
                f"[{path.name}] Deployment guide is missing a section covering: '{section}'. "
                "A deployment guide must document the promotion path, approval gates, "
                "recurring manual steps, and rollback strategy."
            )

    return issues


# ---------------------------------------------------------------------------
# Directory scanner
# ---------------------------------------------------------------------------

def classify_file(path: Path) -> str:
    """Heuristic classification of a Markdown doc as runbook, matrix, or guide."""
    name = path.name.lower()
    text_preview = path.read_text(encoding="utf-8")[:500].lower()

    if "environment matrix" in text_preview or "matrix" in name:
        return "matrix"
    if "deployment guide" in text_preview or "guide" in name:
        return "guide"
    if "runbook" in text_preview or "runbook" in name:
        return "runbook"
    # Default: try runbook checks for generic markdown
    return "runbook"


def check_devops_process_documentation(manifest_dir: Path) -> list[str]:
    """Scan a directory for DevOps process documentation files and return issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Directory not found: {manifest_dir}")
        return issues

    md_files = list(manifest_dir.rglob("*.md"))
    if not md_files:
        issues.append(
            f"No Markdown files found in {manifest_dir}. "
            "DevOps process documentation should be stored as Markdown files."
        )
        return issues

    for md_file in md_files:
        doc_type = classify_file(md_file)
        if doc_type == "runbook":
            issues.extend(check_runbook_file(md_file))
        elif doc_type == "matrix":
            issues.extend(check_environment_matrix_file(md_file))
        elif doc_type == "guide":
            issues.extend(check_deployment_guide_file(md_file))

    return issues


def check_single_file(path: Path) -> list[str]:
    """Check a single file, classifying it automatically."""
    if not path.exists():
        return [f"File not found: {path}"]
    doc_type = classify_file(path)
    if doc_type == "runbook":
        return check_runbook_file(path)
    elif doc_type == "matrix":
        return check_environment_matrix_file(path)
    elif doc_type == "guide":
        return check_deployment_guide_file(path)
    return check_runbook_file(path)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _extract_section(text: str, heading_keyword: str) -> str | None:
    """Extract text content under a Markdown heading containing heading_keyword."""
    lines = text.splitlines()
    in_section = False
    section_lines: list[str] = []
    for line in lines:
        if re.match(r"^#+\s+.*" + re.escape(heading_keyword), line):
            in_section = True
            continue
        if in_section:
            if re.match(r"^#+\s+", line):
                break
            section_lines.append(line)
    return "\n".join(section_lines) if section_lines else None


def _extract_column_values(text: str, column_name: str) -> list[str]:
    """Extract cell values from a Markdown table column by header name."""
    lines = text.splitlines()
    header_index: int | None = None
    col_position: int | None = None
    values: list[str] = []

    for i, line in enumerate(lines):
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        if header_index is None:
            # Find the column position in the header row
            for j, cell in enumerate(cells):
                if column_name in cell:
                    header_index = i
                    col_position = j
                    break
        elif col_position is not None:
            # Skip separator row
            if set(line.replace("|", "").replace("-", "").replace(" ", "")) == set():
                continue
            if col_position < len(cells):
                values.append(cells[col_position])

    return values


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Salesforce DevOps process documentation (runbooks, environment matrices, "
            "deployment guides) for structural completeness and common omissions."
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--manifest-dir",
        help="Directory containing DevOps documentation Markdown files to scan.",
    )
    group.add_argument(
        "--file",
        help="Single Markdown file to check.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.file:
        issues = check_single_file(Path(args.file))
    elif args.manifest_dir:
        issues = check_devops_process_documentation(Path(args.manifest_dir))
    else:
        # Default: check current directory
        issues = check_devops_process_documentation(Path("."))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
