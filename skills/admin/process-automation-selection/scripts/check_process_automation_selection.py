#!/usr/bin/env python3
"""Audit metadata for legacy automation, and lint automation decision records.

Two modes, both stdlib-only:

  --manifest-dir DIR       Scan retrieved metadata for Workflow Rule files, flows whose
                           processType is Workflow (retrieved Process Builder), and objects
                           carrying both Flow and Apex trigger automation.

  --decision-record FILE   Lint one decision record written from
                           templates/process-automation-selection-template.md: required
                           fields present and non-empty, decision-tree citations in the
                           documented `automation-selection.md Q<n>` form, and every
                           rejected alternative carrying a reason.

Both emit the same JSON envelope: {"score", "findings", "summary"}.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


FLOW_OBJECT_RE = re.compile(r"<object>\s*([A-Za-z0-9_]+)\s*</object>", re.IGNORECASE)
PROCESS_TYPE_RE = re.compile(r"<processType>\s*([A-Za-z0-9_]+)\s*</processType>", re.IGNORECASE)
TRIGGER_RE = re.compile(r"trigger\s+\w+\s+on\s+([A-Za-z0-9_]+)", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

# --- decision-record linting -------------------------------------------------
# The record shape is defined in templates/process-automation-selection-template.md
# and worked in references/decision-record-examples.md.
REQUIRED_RECORD_FIELDS = (
    "record_id",
    "requirement",
    "trigger",
    "volume",
    "cross_object",
    "timing",
    "chosen_mechanism",
    "tree_steps_cited",
    "rejected",
    "owner",
    "review_date",
)
# A citation must name a real decision tree and a numbered question in it, e.g.
# "automation-selection.md Q3" / "flow-pattern-selector.md Q6" / "async-selection.md Q8".
TREE_STEP_RE = re.compile(
    r"\b(?:automation-selection|flow-pattern-selector|async-selection)\.md\s+Q\d+\b"
)
FRONT_MATTER_RE = re.compile(r"^\s*---\s*$", re.MULTILINE)
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$")
LIST_ITEM_RE = re.compile(r"^\s*-\s*(.*)$")
REVIEW_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Salesforce metadata for weak automation tool selection and legacy overlap, or lint an automation decision record.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for metadata and Apex.")
    parser.add_argument(
        "--decision-record",
        default=None,
        help="Path to a decision record (markdown with a YAML front-matter block) to lint instead of scanning metadata.",
    )
    return parser.parse_args()


def extract_front_matter(text: str) -> list[str] | None:
    """Return the lines of the first `---` fenced block, or None if there isn't one.

    Handles both a bare front-matter block at the top of the file and one wrapped
    in a ```yaml fence, which is how the template ships it.
    """
    lines = text.splitlines()
    fence_indexes = [i for i, line in enumerate(lines) if FRONT_MATTER_RE.match(line)]
    if len(fence_indexes) < 2:
        return None
    return lines[fence_indexes[0] + 1: fence_indexes[1]]


def parse_record_block(block: list[str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Flat parse of the record's top-level keys and their nested list items.

    Deliberately not a YAML parser: this script is stdlib-only, and the record
    shape is fixed and shallow. Returns (scalar-ish values keyed by top-level
    name, raw nested lines keyed by top-level name).
    """
    scalars: dict[str, str] = {}
    nested: dict[str, list[str]] = {}
    current: str | None = None
    for raw in block:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        match = TOP_LEVEL_KEY_RE.match(raw)
        if match and not raw.startswith((" ", "\t")):
            current = match.group(1)
            value = match.group(2)
            # Strip a trailing `# ...` placeholder comment so the blank template
            # reports its unfilled fields instead of counting the hint as a value.
            if "#" in value:
                value = value.split("#", 1)[0]
            scalars[current] = value.strip()
            nested[current] = []
            continue
        if current is not None:
            nested[current].append(raw)
    return scalars, nested


def lint_decision_record(path: Path) -> tuple[list[str], str]:
    """Lint one decision record. Returns (findings, summary)."""
    if not path.exists():
        return ([f"HIGH {path}: decision record not found"], "Linted 0 decision records.")

    text = read_text(path)
    block = extract_front_matter(text)
    if block is None:
        return (
            [f"HIGH {path}: no `---` front-matter block found; copy templates/process-automation-selection-template.md"],
            "Linted 1 decision record; the record shape was missing entirely.",
        )

    scalars, nested = parse_record_block(block)
    findings: list[str] = []

    # 1. Every required field present, and not left as an empty placeholder.
    for field in REQUIRED_RECORD_FIELDS:
        if field not in scalars:
            findings.append(f"HIGH {path}: required field `{field}` is missing from the decision record")
        elif not scalars[field] and not [ln for ln in nested[field] if ln.strip()]:
            findings.append(f"MEDIUM {path}: required field `{field}` is present but empty; fill it or delete the record")

    # 2. Tree citations must resolve to a numbered question in a real tree.
    citation_lines = [ln for ln in nested.get("tree_steps_cited", []) if LIST_ITEM_RE.match(ln)]
    if not citation_lines:
        findings.append(
            f"HIGH {path}: `tree_steps_cited` lists no steps; every branch of the choice must cite a tree question number"
        )
    else:
        for line in citation_lines:
            if not TREE_STEP_RE.search(line):
                snippet = line.strip()[:80]
                findings.append(
                    f"MEDIUM {path}: citation does not match `<tree>.md Q<n>` "
                    f"(automation-selection / flow-pattern-selector / async-selection): {snippet}"
                )

    # 3. Every rejected alternative needs a reason, not just a name.
    rejected_lines = nested.get("rejected", [])
    alternatives = 0
    reasons = 0
    for line in rejected_lines:
        stripped = line.strip()
        if stripped.startswith("- alternative:") or stripped.startswith("-alternative:"):
            alternatives += 1
            if not stripped.split(":", 1)[1].strip():
                findings.append(f"MEDIUM {path}: a `rejected` entry names no alternative")
        elif stripped.startswith("reason:"):
            reasons += 1
            if not stripped.split(":", 1)[1].strip():
                findings.append(f"MEDIUM {path}: a `rejected` entry has an empty `reason:`")
    if alternatives == 0:
        findings.append(
            f"HIGH {path}: no rejected alternatives recorded; a choice with nothing rejected is not a decision"
        )
    elif reasons < alternatives:
        findings.append(
            f"HIGH {path}: {alternatives} rejected alternative(s) but only {reasons} reason(s); "
            f"each rejected alternative must say why it loses"
        )

    # 4. review_date must be a real ISO date, not a placeholder.
    review_date = scalars.get("review_date", "")
    if review_date and not REVIEW_DATE_RE.match(review_date.strip("\"'")):
        findings.append(f"LOW {path}: `review_date` is not an ISO YYYY-MM-DD date: {review_date}")

    summary = (
        f"Linted 1 decision record ({len(REQUIRED_RECORD_FIELDS)} required fields, "
        f"{len(citation_lines)} tree citation(s), {alternatives} rejected alternative(s)); "
        f"{len(findings)} finding(s)."
    )
    return findings, summary


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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    args = parse_args()

    if args.decision_record:
        findings, summary = lint_decision_record(Path(args.decision_record))
        return emit_result(findings, summary)

    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 files; manifest directory was missing.")

    findings: list[str] = []
    object_flows: dict[str, int] = defaultdict(int)
    object_triggers: dict[str, int] = defaultdict(int)

    workflow_files = sorted(root.rglob("*.workflow-meta.xml"))
    if workflow_files:
        findings.append(f"REVIEW {root}: {len(workflow_files)} Workflow Rule metadata file(s) found; treat them as migration inventory, not ongoing design")

    for path in sorted(root.rglob("*.flow-meta.xml")):
        text = read_text(path)
        object_match = FLOW_OBJECT_RE.search(text)
        if object_match:
            object_flows[object_match.group(1)] += 1
        process_type = PROCESS_TYPE_RE.search(text)
        if process_type and process_type.group(1).lower() == "workflow":
            findings.append(f"REVIEW {path}: legacy workflow-style Flow metadata found; verify this is migration scope and not an active architecture choice")

    for path in sorted(root.rglob("*.trigger")):
        text = read_text(path)
        object_match = TRIGGER_RE.search(text)
        if object_match:
            object_triggers[object_match.group(1)] += 1

    for object_name in sorted(set(object_flows) | set(object_triggers)):
        flow_count = object_flows.get(object_name, 0)
        trigger_count = object_triggers.get(object_name, 0)
        if flow_count >= 3:
            findings.append(f"REVIEW {root}: {flow_count} Flow metadata files found for object {object_name}; confirm automation ownership is still clear")
        if flow_count > 0 and trigger_count > 0:
            findings.append(f"REVIEW {root}: object {object_name} has both Flow and Apex trigger automation; verify the tool boundary is intentional and documented")

    scanned = len(workflow_files) + len(list(root.rglob('*.flow-meta.xml'))) + len(list(root.rglob('*.trigger')))
    if scanned == 0:
        return emit_result([f"HIGH {root}: no Flow, Workflow Rule, or trigger metadata found"], "Scanned 0 automation files.")

    summary = f"Scanned {scanned} automation file(s); {len(findings)} selection-boundary finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
