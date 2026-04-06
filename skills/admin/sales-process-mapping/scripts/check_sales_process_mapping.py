#!/usr/bin/env python3
"""Checker script for Sales Process Mapping skill.

Validates a sales process mapping document (Markdown table format) for common
structural and Salesforce platform constraint issues:
  - All required sections present in the mapping document
  - ForecastCategoryName values are restricted to the five platform-fixed values
  - At least one Closed Won stage present
  - At least one Closed Lost stage present
  - Win/loss taxonomy size within the recommended 5-8 value range
  - Open questions log has no unresolved items
  - Stage names do not contain characters invalid in Salesforce picklist values
  - No catch-all "Other" win/loss category
  - No free-text field recommendation for win/loss capture

Optionally checks deployed Salesforce metadata (OpportunityStage XML) for
ForecastCategoryName violations and generic stage name collisions.

Uses stdlib only - no pip dependencies.

Usage:
    python3 check_sales_process_mapping.py [--help]
    python3 check_sales_process_mapping.py --doc path/to/mapping-document.md
    python3 check_sales_process_mapping.py --manifest-dir path/to/metadata
    python3 check_sales_process_mapping.py --doc path/to/mapping-document.md --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Platform-fixed ForecastCategoryName values - cannot be renamed in Salesforce
VALID_FORECAST_CATEGORIES = {"Pipeline", "Best Case", "Commit", "Closed", "Omitted"}

# Non-platform forecast category labels commonly produced by LLMs or legacy processes
INVALID_FORECAST_LABELS_PATTERN = re.compile(
    r"\b(upside|strong upside|called|at risk|best commit|pipeline 2|pipeline ii|forecast 1|forecast 2)\b",
    re.IGNORECASE,
)

# Characters that are invalid in Salesforce picklist label values
INVALID_PICKLIST_CHARS_PATTERN = re.compile(r'[<>{}\\|^~`]')

# Maximum recommended win/loss taxonomy size per outcome before data quality degrades
WIN_LOSS_RECOMMENDED_MAX = 8
WIN_LOSS_HARD_MAX = 12

# Minimum recommended win/loss taxonomy size per outcome
WIN_LOSS_MIN = 3

# Salesforce metadata namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a sales process mapping document and/or Salesforce metadata for "
            "structural issues and platform constraint violations. "
            "Pass --doc to check a Markdown mapping document; "
            "pass --manifest-dir to check deployed stage metadata XML."
        ),
    )
    parser.add_argument(
        "--doc",
        default=None,
        help="Path to the Markdown mapping document to validate.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of Salesforce metadata (optional, checked alongside --doc).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat advisory warnings as errors (non-zero exit on any issue).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sf_tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


def _find_text(element: ET.Element, tag: str) -> str:
    child = element.find(_sf_tag(tag))
    return child.text.strip() if child is not None and child.text else ""


def _extract_table_rows_after(text: str, heading_keyword: str) -> list[list[str]]:
    """Return Markdown table data rows found after the first heading that contains heading_keyword.

    Skips the header row and separator rows. Returns empty list if no table found.
    """
    lines = text.splitlines()
    found_heading = False
    in_table = False
    skipped_header = False
    rows: list[list[str]] = []

    for line in lines:
        if not found_heading:
            if heading_keyword.lower() in line.lower():
                found_heading = True
            continue

        stripped = line.strip()
        if stripped.startswith("|"):
            if not in_table:
                in_table = True
                skipped_header = False
                continue  # skip header row

            if not skipped_header:
                skipped_header = True
                continue  # skip separator row

            # Skip pure separator rows
            if re.match(r"^\|[\s\-|:]+\|$", stripped):
                continue

            cells = [c.strip() for c in stripped.strip("|").split("|")]
            rows.append(cells)
        else:
            if in_table:
                break  # table ended

    return rows


# ---------------------------------------------------------------------------
# Document-level checks
# ---------------------------------------------------------------------------

def check_stage_map_document(doc_path: Path) -> tuple[list[str], list[str]]:
    """Check a Markdown mapping document for completeness and platform constraint issues.

    Returns (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not doc_path.exists():
        errors.append(f"Mapping document not found: {doc_path}")
        return errors, warnings

    try:
        text = doc_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"Could not read mapping document: {exc}")
        return errors, warnings

    text_lower = text.lower()

    # --- Check 1: Required sections present ---
    required_sections = {
        "Stage Map": "stage map",
        "Win/Loss Reason": "win/loss reason",
        "Transition Rule": "transition rule",
        "Handoff Brief": "handoff brief",
    }
    for label, keyword in required_sections.items():
        if keyword not in text_lower:
            warnings.append(
                f"Section '{label}' not found in the mapping document. "
                "Ensure the document uses the standard template sections."
            )

    # --- Check 2: Open questions log has no unresolved Open items ---
    if "open questions" in text_lower:
        rows = _extract_table_rows_after(text, "Open Questions")
        open_items = [r for r in rows if len(r) >= 5 and "open" in r[-1].lower()]
        if open_items:
            errors.append(
                f"Open Questions log contains {len(open_items)} unresolved item(s). "
                "Resolve all open questions before handing off to the "
                "opportunity-management skill for Salesforce configuration."
            )

    # --- Check 3: Invalid ForecastCategoryName labels ---
    invalid_labels = INVALID_FORECAST_LABELS_PATTERN.findall(text)
    if invalid_labels:
        unique = list(dict.fromkeys(m.title() for m in invalid_labels))
        errors.append(
            f"Non-platform ForecastCategoryName label(s) found: {', '.join(unique)}. "
            f"Valid platform values are: {', '.join(sorted(VALID_FORECAST_CATEGORIES))}. "
            "These five values cannot be renamed in Salesforce."
        )

    # --- Check 4: Closed Won stage present ---
    if "closed won" not in text_lower:
        errors.append(
            "No 'Closed Won' stage found. "
            "Every sales process must include a Closed Won terminal stage."
        )

    # --- Check 5: Closed Lost stage present ---
    if "closed lost" not in text_lower:
        warnings.append(
            "No 'Closed Lost' stage found. "
            "Including a Closed Lost stage is strongly recommended for pipeline health reporting."
        )

    # --- Check 6: Stage names with invalid picklist characters ---
    # Scan table cell content for suspicious characters
    table_cell_pattern = re.compile(r"\|\s*([^|\n]{2,50}?)\s*(?=\|)")
    for match in table_cell_pattern.finditer(text):
        cell_value = match.group(1).strip()
        if INVALID_PICKLIST_CHARS_PATTERN.search(cell_value):
            errors.append(
                f"Potential stage name '{cell_value}' contains character(s) invalid in "
                "Salesforce picklist values. Remove: < > {{ }} \\ | ^ ~ `"
            )

    # --- Check 7: Win/Loss taxonomy size ---
    win_match = re.search(r"win reason", text, re.IGNORECASE)
    if win_match:
        win_section = text[win_match.start(): win_match.start() + 2000]
        win_rows = _extract_table_rows_after(win_section, "Win Reason")
        win_count = len([r for r in win_rows if any(c.strip() for c in r)])
        if win_count > WIN_LOSS_HARD_MAX:
            errors.append(
                f"Win reason taxonomy has {win_count} values "
                f"(maximum recommended: {WIN_LOSS_RECOMMENDED_MAX}). "
                "Taxonomies exceeding 12 values are rarely completed consistently. "
                "Consolidate to 5-8 mutually exclusive categories."
            )
        elif win_count > WIN_LOSS_RECOMMENDED_MAX:
            warnings.append(
                f"Win reason taxonomy has {win_count} values "
                f"(recommended maximum: {WIN_LOSS_RECOMMENDED_MAX}). "
                "Consider consolidating to improve rep completion rates."
            )

    loss_match = re.search(r"loss reason", text, re.IGNORECASE)
    if loss_match:
        loss_section = text[loss_match.start(): loss_match.start() + 2000]
        loss_rows = _extract_table_rows_after(loss_section, "Loss Reason")
        loss_count = len([r for r in loss_rows if any(c.strip() for c in r)])
        if loss_count > WIN_LOSS_HARD_MAX:
            errors.append(
                f"Loss reason taxonomy has {loss_count} values "
                f"(maximum recommended: {WIN_LOSS_RECOMMENDED_MAX}). "
                "Consolidate to 5-8 mutually exclusive categories."
            )
        elif loss_count > WIN_LOSS_RECOMMENDED_MAX:
            warnings.append(
                f"Loss reason taxonomy has {loss_count} values "
                f"(recommended maximum: {WIN_LOSS_RECOMMENDED_MAX}). "
                "Consider consolidating to improve rep completion rates."
            )

        # Check for No Decision / Status Quo category
        if not re.search(r"no\s+decision|status\s+quo", loss_section, re.IGNORECASE):
            warnings.append(
                "'No Decision / Status Quo' loss reason not found. "
                "This is the most commonly omitted category — add it to capture "
                "deals where the prospect maintained the status quo rather than choosing a vendor."
            )

    # --- Check 8: Catch-all 'Other' category ---
    if re.search(r"\|\s*other\s*\|", text, re.IGNORECASE):
        warnings.append(
            "A catch-all 'Other' reason category was found in the taxonomy. "
            "In practice 'Other' becomes the dominant category and makes trend analysis impossible. "
            "Remove it and expand the taxonomy to cover the cases it would have captured."
        )

    # --- Check 9: Free-text field recommendation ---
    if re.search(r"free.?text", text, re.IGNORECASE):
        warnings.append(
            "A 'free-text' field reference was found. "
            "Free-text win/loss fields produce unusable data within 90 days. "
            "Use a constrained picklist with a defined taxonomy instead."
        )

    # --- Check 10: Handoff brief has Validation Rules section ---
    if "handoff brief" in text_lower and "validation rules required" not in text_lower:
        warnings.append(
            "Handoff brief is present but does not contain a 'Validation Rules Required' section. "
            "Every stage transition rule that requires enforcement must be listed as a "
            "validation rule specification so the opportunity-management skill can implement it correctly."
        )

    # --- Check 11: Path enforcement conflation ---
    if re.search(r"path\s+(enforces|requires|blocks|prevents|ensures)", text, re.IGNORECASE):
        errors.append(
            "The document uses language suggesting Path enforces stage requirements "
            "(e.g., 'Path enforces', 'Path requires', 'Path blocks'). "
            "Path is visual-only and does not block record saves. "
            "Stage enforcement requires validation rules. "
            "Replace Path enforcement language with explicit validation rule requirements."
        )

    return errors, warnings


# ---------------------------------------------------------------------------
# Metadata-level checks
# ---------------------------------------------------------------------------

def check_stage_metadata(manifest_dir: Path) -> tuple[list[str], list[str]]:
    """Check deployed OpportunityStage XML metadata for constraint violations.

    Returns (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    candidate_paths = [
        manifest_dir / "standardValueSets" / "OpportunityStage.standardValueSet-meta.xml",
        manifest_dir / "globalValueSets" / "OpportunityStage.globalValueSet-meta.xml",
    ]

    stage_file: Path | None = None
    for path in candidate_paths:
        if path.exists():
            stage_file = path
            break

    if stage_file is None:
        return errors, warnings  # Not finding the file is advisory

    try:
        tree = ET.parse(stage_file)
        root = tree.getroot()
    except ET.ParseError as exc:
        errors.append(f"Could not parse stage metadata {stage_file}: {exc}")
        return errors, warnings

    value_tag = (
        _sf_tag("standardValue")
        if "standardValueSet" in stage_file.name
        else _sf_tag("customValue")
    )
    all_values = root.findall(f".//{value_tag}")
    if not all_values:
        all_values = root.findall(f".//{_sf_tag('standardValue')}") or root.findall(
            f".//{_sf_tag('customValue')}"
        )

    active_names: list[str] = []
    generic_names = {
        "Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5",
        "Step 1", "Step 2", "Step 3", "Phase 1", "Phase 2",
    }

    for el in all_values:
        label = _find_text(el, "fullName") or _find_text(el, "label")
        is_active_text = _find_text(el, "isActive")
        is_active = is_active_text.lower() != "false" if is_active_text else True

        if not is_active or not label:
            continue

        active_names.append(label)

        # ForecastCategoryName must be a valid platform value
        forecast_category = _find_text(el, "forecastCategory")
        if forecast_category and forecast_category not in VALID_FORECAST_CATEGORIES:
            errors.append(
                f"Stage '{label}': ForecastCategoryName '{forecast_category}' is not a valid "
                f"platform value. Must be one of: {', '.join(sorted(VALID_FORECAST_CATEGORIES))}."
            )

        # IsWon=true requires IsClosed=true
        is_won = _find_text(el, "won").lower() == "true"
        is_closed = _find_text(el, "closed").lower() == "true"
        if is_won and not is_closed:
            errors.append(
                f"Stage '{label}': IsWon=true but IsClosed=false. "
                "A Won stage must also have IsClosed=true."
            )

        # Invalid picklist characters
        if INVALID_PICKLIST_CHARS_PATTERN.search(label):
            errors.append(
                f"Stage name '{label}' in deployed metadata contains character(s) "
                "not valid in Salesforce picklist values."
            )

    # Advisory: generic names risk cross-BU collisions
    generic_found = [n for n in active_names if n in generic_names]
    if generic_found:
        warnings.append(
            f"Generic stage name(s) found in deployed metadata: {', '.join(generic_found)}. "
            "Generic names risk cross-business-unit collisions in shared orgs. "
            "Consider prefixing with the business unit or motion name."
        )

    return errors, warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()

    if args.doc is None and args.manifest_dir is None:
        print(
            "No input provided. Usage examples:\n"
            "  python3 check_sales_process_mapping.py "
            "--doc path/to/mapping-document.md\n"
            "  python3 check_sales_process_mapping.py "
            "--manifest-dir path/to/metadata\n"
            "  python3 check_sales_process_mapping.py "
            "--doc path/to/mapping-document.md --strict"
        )
        return 0

    all_errors: list[str] = []
    all_warnings: list[str] = []

    if args.doc:
        errors, warnings = check_stage_map_document(Path(args.doc))
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        if not manifest_dir.exists():
            all_errors.append(f"Manifest directory not found: {manifest_dir}")
        else:
            errors, warnings = check_stage_metadata(manifest_dir)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

    if not all_errors and not all_warnings:
        print("No issues found.")
        return 0

    for warning in all_warnings:
        print(f"WARNING: {warning}")

    for error in all_errors:
        print(f"ERROR: {error}")

    if all_errors:
        return 1

    if args.strict and all_warnings:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
