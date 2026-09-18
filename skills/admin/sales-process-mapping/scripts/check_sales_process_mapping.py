#!/usr/bin/env python3
"""Checker script for Sales Process Mapping skill.

Three inputs, any combination:

  --map    a machine-readable sales-process map (YAML subset or CSV) - the
           artefact this skill produces. Linted for the design invariants that
           make the map safe to hand to admin/opportunity-management:
             * every stage carries non-empty entry AND exit criteria
             * probability is monotonic non-decreasing down the open/won ladder
             * forecast_category is a documented ForecastCategoryName value
             * every stage names at least one required field
             * no two stages share the same exit criteria
             * stage names are unique
           Warnings: more than 10 stages; a stage with no owner persona.

  --doc    the Markdown mapping document (narrative form).

  --manifest-dir
           a directory. Scans it, at any depth, for *.yaml / *.yml / *.csv
           sales-process maps (any file with a `stages:` key or a stage-map
           CSV header row) and for a retrieved OpportunityStage standard
           value set. A manifest-dir scan that matches zero files prints
           that plainly instead of a misleading "No issues found."

The Markdown document checks cover:
  - All required sections present in the mapping document
  - ForecastCategoryName values are restricted to the documented platform values
  - At least one Closed Won stage present
  - At least one Closed Lost stage present
  - Win/loss taxonomy size within the recommended 5-8 value range
  - Open questions log has no unresolved items
  - Stage names do not contain characters invalid in Salesforce picklist values
  - No catch-all "Other" win/loss category
  - No free-text field recommendation for win/loss capture

Optionally checks deployed Salesforce metadata (OpportunityStage XML) for
ForecastCategoryName violations and generic stage name collisions.

Accepted YAML subset for --map (deliberately small so no PyYAML is needed):

    process: New Logo - Enterprise      # top-level scalars
    object: Opportunity
    stages:                             # a list of mappings
      - name: Qualification
        entry: "SDR handoff accepted"
        exit: "Discovery call held"
        forecast_category: Pipeline
        probability: 10
        owner: SDR
        won: false                      # optional booleans
        closed: false
        required_fields: [LeadSource, Amount]

Scalars may be bare, 'single-quoted' or "double-quoted". Lists are inline
only ([a, b]). Block scalars (| and >) and nested mappings are not supported.
CSV form: one row per stage with the headers name, entry, exit,
forecast_category, probability, owner, required_fields (semicolon-separated),
and optional won / closed columns.

Uses stdlib only - no pip dependencies.

Exit code is 1 if any ERROR is reported, or if --strict is set and any WARNING
is reported.

Usage:
    python3 check_sales_process_mapping.py [--help]
    python3 check_sales_process_mapping.py --map path/to/stage-map.yaml
    python3 check_sales_process_mapping.py --map path/to/stage-map.csv
    python3 check_sales_process_mapping.py --doc path/to/mapping-document.md
    python3 check_sales_process_mapping.py --manifest-dir path/to/design-or-metadata
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


# ---------------------------------------------------------------------------
# Sales-process map (--map) constants
# ---------------------------------------------------------------------------

# OpportunityStage.ForecastCategoryName - the design vocabulary a stage map uses.
# object_reference.txt:195492-195504 (Object Reference, OpportunityStage).
FORECAST_CATEGORY_NAMES = {
    "Best Case",
    "Closed",
    "Commit",
    "Most Likely",
    "Omitted",
    "Pipeline",
}

# The Metadata API <forecastCategory> tokens (ForecastCategories enumeration,
# api_meta.txt:47578-47585) plus OpportunityStage.ForecastCategory
# (object_reference.txt:195466-195486). A stage MAP is a design artefact and
# must speak the ForecastCategoryName vocabulary, so seeing one of these here
# means the two vocabularies have been mixed in one column.
# ForecastCategories enumeration - the tokens the deployed XML accepts
# (api_meta.txt:47578-47585, CustomValue.forecastCategory).
METADATA_FORECAST_ENUM = {"Omitted", "Pipeline", "BestCase", "Forecast", "Closed"}

METADATA_FORECAST_TOKENS = {
    "BestCase": "Best Case",
    "Forecast": "Commit",
    "MostLikely": "Most Likely",
}

# Design convention, not a platform limit: past ten stages reps stop
# distinguishing them and stage data degrades.
STAGE_COUNT_WARN_THRESHOLD = 10

MAP_REQUIRED_STAGE_KEYS = ("name", "entry", "exit", "forecast_category", "probability")

CSV_HEADER_ALIASES = {
    "stage": "name",
    "stage_name": "name",
    "entry_criteria": "entry",
    "exit_criteria": "exit",
    "forecastcategory": "forecast_category",
    "forecastcategoryname": "forecast_category",
    "forecast_category_name": "forecast_category",
    "default_probability": "probability",
    "owner_persona": "owner",
    "persona": "owner",
    "required_field": "required_fields",
}


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
        "--map",
        dest="stage_map",
        default=None,
        help="Path to a machine-readable sales-process map (.yaml/.yml/.csv).",
    )
    parser.add_argument(
        "--doc",
        default=None,
        help="Path to the Markdown mapping document to validate.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help=(
            "Directory to scan recursively: any *.yaml/*.yml/*.csv sales-process map "
            "at any depth inside it is linted, and a retrieved OpportunityStage "
            "standard value set at any depth is checked."
        ),
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
# Sales-process map parsing (YAML subset / CSV) - stdlib only
# ---------------------------------------------------------------------------

def _scalar(raw: str):
    """Coerce one YAML/CSV scalar: quoted string, inline list, bool, int, or str."""
    value = raw.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part) for part in inner.split(",")]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def _strip_comment(line: str) -> str:
    """Drop a trailing # comment when it is not inside a quoted scalar."""
    quote = ""
    for index, char in enumerate(line):
        if quote:
            if char == quote:
                quote = ""
        elif char in ("'", '"'):
            quote = char
        elif char == "#" and (index == 0 or line[index - 1] in " \t"):
            return line[:index]
    return line


def parse_stage_map_yaml(text: str) -> tuple[dict, list[str]]:
    """Parse the documented YAML subset. Returns (document, parse_errors)."""
    errors: list[str] = []
    doc: dict = {}
    stages: list[dict] = []
    in_stages = False
    current: dict | None = None

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_comment(raw_line).rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        body = line.strip()

        if indent == 0:
            if body.rstrip() == "stages:":
                in_stages = True
                current = None
                continue
            in_stages = False
            current = None
            if ":" in body:
                key, _, value = body.partition(":")
                doc[key.strip()] = _scalar(value) if value.strip() else ""
            continue

        if not in_stages:
            continue

        if body.startswith("- "):
            current = {}
            stages.append(current)
            body = body[2:].strip()
        elif current is None:
            errors.append(
                f"line {lineno}: indented key outside a '- ' stage item: {body!r}"
            )
            continue

        if ":" not in body:
            errors.append(f"line {lineno}: expected 'key: value', found {body!r}")
            continue
        key, _, value = body.partition(":")
        current[key.strip()] = _scalar(value) if value.strip() else ""

    doc["stages"] = stages
    return doc, errors


def parse_stage_map_csv(text: str) -> tuple[dict, list[str]]:
    """Parse a stage-map CSV. Returns (document, parse_errors)."""
    import csv
    import io

    errors: list[str] = []
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return {"stages": []}, ["CSV has no header row."]

    stages: list[dict] = []
    for row in reader:
        stage: dict = {}
        for header, raw in row.items():
            if header is None:
                continue
            key = header.strip().lower().replace(" ", "_")
            key = CSV_HEADER_ALIASES.get(key, key)
            value = (raw or "").strip()
            if key == "required_fields":
                stage[key] = [v.strip() for v in value.split(";") if v.strip()]
            elif key == "probability":
                stage[key] = int(value) if re.fullmatch(r"-?\d+", value) else value
            elif key in ("won", "closed"):
                stage[key] = value.lower() == "true"
            else:
                stage[key] = value
        if any(str(v).strip() for v in stage.values()):
            stages.append(stage)

    return {"stages": stages}, errors


def parse_stage_map(path: Path) -> tuple[dict, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"stages": []}, [f"Could not read stage map {path}: {exc}"]

    if path.suffix.lower() == ".csv":
        return parse_stage_map_csv(text)
    return parse_stage_map_yaml(text)


def _is_lost_terminal(stage: dict) -> bool:
    """A stage that ends the deal without a win: excluded from the probability ladder.

    Explicit won/closed flags win; otherwise fall back to the stage name, which
    is what a design-stage map usually carries.
    """
    name = str(stage.get("name", "")).lower()
    if stage.get("won") is True or "won" in name:
        return False
    if stage.get("closed") is True:
        return True
    return "lost" in name or "abandon" in name


# ---------------------------------------------------------------------------
# Sales-process map checks (--map)
# ---------------------------------------------------------------------------

def check_stage_map(map_path: Path) -> tuple[list[str], list[str]]:
    """Lint a machine-readable sales-process map. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    if not map_path.exists():
        return [f"Stage map not found: {map_path}"], warnings

    doc, parse_errors = parse_stage_map(map_path)
    errors.extend(f"{map_path.name}: {e}" for e in parse_errors)

    stages = doc.get("stages") or []
    if not stages:
        errors.append(
            f"{map_path.name}: no stages found. A sales-process map needs a "
            "'stages:' list (YAML) or one row per stage (CSV)."
        )
        return errors, warnings

    label = map_path.name

    # --- Structural: required keys present and non-empty ---
    seen_names: dict[str, int] = {}
    exits: dict[str, str] = {}

    for index, stage in enumerate(stages, start=1):
        name = str(stage.get("name", "")).strip()
        display = name or f"stage #{index}"

        for key in MAP_REQUIRED_STAGE_KEYS:
            value = stage.get(key)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(
                    f"{label}: {display} is missing '{key}'. Every stage needs a "
                    "name, entry criteria, exit criteria, forecast_category and probability "
                    "before the map can be handed to admin/opportunity-management."
                )

        # Stage names unique - they become global picklist values.
        if name:
            key_name = name.lower()
            if key_name in seen_names:
                errors.append(
                    f"{label}: stage name '{name}' appears twice (rows "
                    f"{seen_names[key_name]} and {index}). Stage names become global "
                    "OpportunityStage picklist values and must be unique."
                )
            else:
                seen_names[key_name] = index

        # Exit criteria must discriminate one stage from the next.
        exit_text = str(stage.get("exit", "")).strip()
        if exit_text:
            normalised = re.sub(r"[^a-z0-9 ]", "", exit_text.lower())
            normalised = re.sub(r"\s+", " ", normalised).strip()
            if normalised in exits:
                errors.append(
                    f"{label}: {display} has the same exit criteria as "
                    f"'{exits[normalised]}'. Two stages that exit on the same condition "
                    "are one stage; merge them or sharpen the criteria."
                )
            else:
                exits[normalised] = display

        # At least one required field per stage - this is what becomes the
        # validation-rule intent in the handoff brief.
        required_fields = stage.get("required_fields")
        if isinstance(required_fields, str):
            required_fields = [f for f in re.split(r"[;,]", required_fields) if f.strip()]
        if not required_fields:
            errors.append(
                f"{label}: {display} names no required_fields. A stage with no field "
                "requirement is a label, not a gate - it produces no validation rule "
                "and nothing for a rep to complete."
            )

        # Forecast category must be a documented ForecastCategoryName value.
        category = str(stage.get("forecast_category", "")).strip()
        if category:
            if category in METADATA_FORECAST_TOKENS:
                errors.append(
                    f"{label}: {display} uses forecast_category '{category}', which is a "
                    f"Metadata API token, not a ForecastCategoryName. Use "
                    f"'{METADATA_FORECAST_TOKENS[category]}' in the design map; the "
                    "metadata token belongs only in the deployed XML "
                    "(see admin/opportunity-management references/gotchas.md Gotcha 13)."
                )
            elif category not in FORECAST_CATEGORY_NAMES:
                errors.append(
                    f"{label}: {display} uses forecast_category '{category}', which is not a "
                    "documented OpportunityStage.ForecastCategoryName value. Allowed: "
                    f"{', '.join(sorted(FORECAST_CATEGORY_NAMES))}."
                )

        # Owner persona - advisory. A stage nobody owns never gets advanced.
        owner = str(stage.get("owner", "")).strip()
        if not owner:
            warnings.append(
                f"{label}: {display} has no owner persona. Name the role that advances "
                "the stage, or the swim-lane handoff is undefined."
            )

    # --- Probability ladder: monotonic non-decreasing over open + won stages ---
    ladder: list[tuple[str, int]] = []
    for index, stage in enumerate(stages, start=1):
        name = str(stage.get("name", "")).strip() or f"stage #{index}"
        probability = stage.get("probability")
        if not isinstance(probability, int):
            continue
        if not 0 <= probability <= 100:
            errors.append(
                f"{label}: {name} has probability {probability}. "
                "OpportunityStage.DefaultProbability is a percent "
                "(object_reference.txt:195451-195457) and must be 0-100."
            )
            continue
        if _is_lost_terminal(stage):
            if probability != 0:
                errors.append(
                    f"{label}: {name} is a closed-lost terminal stage with probability "
                    f"{probability}. A lost stage must be 0."
                )
            continue
        ladder.append((name, probability))

    for (prev_name, prev_p), (next_name, next_p) in zip(ladder, ladder[1:]):
        if next_p < prev_p:
            errors.append(
                f"{label}: probability drops from {prev_p} at '{prev_name}' to {next_p} at "
                f"'{next_name}'. A stage ladder must be monotonic non-decreasing - a "
                "later stage that is less likely to close means the stage boundary is "
                "in the wrong place."
            )

    # --- Advisory: ladder length ---
    if len(stages) > STAGE_COUNT_WARN_THRESHOLD:
        warnings.append(
            f"{label}: {len(stages)} stages. Past {STAGE_COUNT_WARN_THRESHOLD} stages reps "
            "stop distinguishing adjacent gates and pipeline reports lose resolution. "
            "Check whether any two stages share an owner and an exit condition."
        )

    if not any("won" in str(s.get("name", "")).lower() for s in stages):
        warnings.append(
            f"{label}: no Closed Won stage found. Every sales process needs a won "
            "terminal stage (OpportunityStage.IsWon, object_reference.txt:195536-195542)."
        )

    return errors, warnings


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


def discover_stage_maps(root: Path) -> list[Path]:
    """Find sales-process maps under root.

    A YAML file qualifies if it has a top-level `stages:` key; a CSV file
    qualifies if its header row carries a stage-name column and either an entry
    or an exit column. Anything else in the directory is ignored, so this is
    safe to point at a mixed design/metadata folder.
    """
    found: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".yaml", ".yml", ".csv"):
            continue
        try:
            head = path.read_text(encoding="utf-8", errors="replace")[:4096]
        except OSError:
            continue
        if path.suffix.lower() == ".csv":
            header = head.splitlines()[0].lower() if head.splitlines() else ""
            cells = {c.strip().replace(" ", "_") for c in header.split(",")}
            cells = {CSV_HEADER_ALIASES.get(c, c) for c in cells}
            if "name" in cells and ({"entry", "exit"} & cells):
                found.append(path)
        elif re.search(r"^stages:\s*$", head, re.MULTILINE):
            found.append(path)
    return found


# ---------------------------------------------------------------------------
# Metadata-level checks
# ---------------------------------------------------------------------------

# Filename -> required immediate parent directory name. This is the shape the
# Metadata API retrieves an OpportunityStage value set in; a build step may
# nest it at any depth under the manifest directory, so the parent-name check
# is what keeps this from matching an unrelated file with the same name.
STAGE_METADATA_FILENAMES = {
    "OpportunityStage.standardValueSet-meta.xml": "standardValueSets",
    "OpportunityStage.globalValueSet-meta.xml": "globalValueSets",
}


def discover_stage_metadata_files(root: Path) -> list[Path]:
    """Find deployed OpportunityStage value-set metadata anywhere under root.

    Walks the whole tree (a build manifest directory nests each step's
    metadata under its own step folder) rather than pinning the lookup to
    root's immediate children.
    """
    found: list[Path] = []
    for filename, parent_name in STAGE_METADATA_FILENAMES.items():
        for path in root.rglob(filename):
            if path.is_file() and path.parent.name == parent_name:
                found.append(path)
    return sorted(found)


def check_stage_metadata(stage_files: list[Path]) -> tuple[list[str], list[str]]:
    """Check deployed OpportunityStage XML metadata file(s) for constraint violations.

    Returns (errors, warnings). Not finding any file is advisory (the caller
    decides how to report a manifest-dir scan that matched nothing).
    """
    errors: list[str] = []
    warnings: list[str] = []

    for stage_file in stage_files:
        try:
            tree = ET.parse(stage_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            errors.append(f"Could not parse stage metadata {stage_file}: {exc}")
            continue

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

            # The XML element is typed as the ForecastCategories enumeration
            # (api_meta.txt:47578-47585), NOT as ForecastCategoryName. Checking the
            # XML against the UI labels flags every correct file, so use the tokens.
            forecast_category = _find_text(el, "forecastCategory")
            if forecast_category and forecast_category not in METADATA_FORECAST_ENUM:
                hint = ""
                for token, ui_label in METADATA_FORECAST_TOKENS.items():
                    if forecast_category == ui_label:
                        hint = f" Did you mean <forecastCategory>{token}</forecastCategory>?"
                errors.append(
                    f"Stage '{label}': <forecastCategory>{forecast_category}</forecastCategory> is not "
                    f"a member of the ForecastCategories enumeration. Must be one of: "
                    f"{', '.join(sorted(METADATA_FORECAST_ENUM))}.{hint}"
                )

            # <won> is the only won/closed flag documented for the opportunity Stage
            # picklist: "Indicates whether this value is associated with a closed or
            # won status ... only relevant for the standard Stage field in
            # opportunities" (api_meta.txt:47611-47614). <closed> is documented as
            # relevant only to the case and task Status fields, up to API 36.0
            # (api_meta.txt:47542-47546), so its absence here is normal and is NOT
            # an error. Only a file that carries both and contradicts itself is.
            won_text = _find_text(el, "won").lower()
            closed_el = el.find(_sf_tag("closed"))
            if won_text == "true" and closed_el is not None:
                closed_text = (closed_el.text or "").strip().lower()
                if closed_text == "false":
                    errors.append(
                        f"Stage '{label}': <won>true</won> with <closed>false</closed>. "
                        "A won stage cannot be open; remove the <closed> element or set it to true."
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

    if args.stage_map is None and args.doc is None and args.manifest_dir is None:
        print(
            "No input provided. Usage examples:\n"
            "  python3 check_sales_process_mapping.py "
            "--map path/to/stage-map.yaml\n"
            "  python3 check_sales_process_mapping.py "
            "--doc path/to/mapping-document.md\n"
            "  python3 check_sales_process_mapping.py "
            "--manifest-dir path/to/design-or-metadata\n"
            "  python3 check_sales_process_mapping.py "
            "--doc path/to/mapping-document.md --strict"
        )
        return 0

    all_errors: list[str] = []
    all_warnings: list[str] = []

    # Set only when --manifest-dir is given and the directory exists, so the
    # summary below can tell a manifest-dir scan that matched nothing apart
    # from a manifest-dir scan that was never requested.
    manifest_dir_scanned_count: int | None = None

    if args.stage_map:
        errors, warnings = check_stage_map(Path(args.stage_map))
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    if args.doc:
        errors, warnings = check_stage_map_document(Path(args.doc))
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        if not manifest_dir.exists():
            all_errors.append(f"Manifest directory not found: {manifest_dir}")
        else:
            stage_maps = discover_stage_maps(manifest_dir)
            for map_path in stage_maps:
                errors, warnings = check_stage_map(map_path)
                all_errors.extend(errors)
                all_warnings.extend(warnings)

            stage_metadata_files = discover_stage_metadata_files(manifest_dir)
            errors, warnings = check_stage_metadata(stage_metadata_files)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

            manifest_dir_scanned_count = len(stage_maps) + len(stage_metadata_files)

    if not all_errors and not all_warnings:
        if manifest_dir_scanned_count == 0:
            print("Scanned 0 file(s) — nothing asserted; check --manifest-dir")
        else:
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
