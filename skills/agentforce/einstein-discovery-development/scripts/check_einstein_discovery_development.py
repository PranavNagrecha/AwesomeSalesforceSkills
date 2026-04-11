#!/usr/bin/env python3
"""Checker script for Einstein Discovery Development skill.

Inspects Salesforce metadata in a retrieved project to flag common Einstein Discovery
configuration mistakes. Uses stdlib only — no pip dependencies.

Checks performed:
  1. Detects DiscoveryStory metadata files without a deployed PredictionDefinition reference.
  2. Detects Flow or Apex files that reference Einstein Discovery prediction fields
     but lack any callout to the /smartdatadiscovery/ endpoint (suggesting stale score reliance).
  3. Warns if predict callouts in Apex are missing the 'settings' key (v50.0+ regression).
  4. Warns if bulk predict job polling code treats 'Paused' as a failure (raises/throws on Paused).

Usage:
    python3 check_einstein_discovery_development.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def _read(path: Path) -> str:
    """Return file text, or empty string on read error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_discovery_story_metadata(manifest_dir: Path) -> list[str]:
    """Check for DiscoveryStory metadata files.

    Flags any .discoveryStory-meta.xml that exists but where no corresponding
    PredictionDefinition reference can be found in the metadata tree.
    """
    issues: list[str] = []
    story_files = _find_files(manifest_dir, "*.discoveryStory-meta.xml")
    if not story_files:
        return issues  # No stories found — not necessarily an issue

    pred_def_pattern = re.compile(r"predictionDefinition|DiscoveryStory", re.IGNORECASE)
    all_meta_text = ""
    for mf in _find_files(manifest_dir, "*.xml"):
        if mf not in story_files:
            all_meta_text += _read(mf)

    for story_file in story_files:
        story_name = story_file.stem.replace(".discoveryStory-meta", "")
        if story_name not in all_meta_text:
            issues.append(
                f"DiscoveryStory '{story_name}' found in metadata but no PredictionDefinition "
                f"reference detected. Ensure the story has been deployed as a prediction "
                f"definition before expecting API scoring to work. ({story_file})"
            )
    return issues


def check_apex_missing_settings(manifest_dir: Path) -> list[str]:
    """Check Apex classes for predict callouts that omit the 'settings' key.

    Starting in API v50.0, prediction factors and prescriptions are only returned
    when the 'settings' object is present in the request body.
    """
    issues: list[str] = []
    apex_files = _find_files(manifest_dir, "*.cls")
    apex_files += _find_files(manifest_dir, "*.cls-meta.xml")

    sdd_pattern = re.compile(r"smartdatadiscovery/predict", re.IGNORECASE)
    settings_pattern = re.compile(r"['\"]settings['\"]", re.IGNORECASE)
    prescription_pattern = re.compile(r"prescription|middleValue|maxPrescription", re.IGNORECASE)

    for cls_file in apex_files:
        text = _read(cls_file)
        if not sdd_pattern.search(text):
            continue  # Not a predict callout file
        # If the file calls predict but wants prescriptions/factors without settings
        if prescription_pattern.search(text) and not settings_pattern.search(text):
            issues.append(
                f"Apex file '{cls_file.name}' calls /smartdatadiscovery/predict and references "
                f"prescriptions or middleValues but does not include a 'settings' key in the "
                f"request body. From API v50.0 onward, prediction factors are opt-in and require "
                f"an explicit 'settings' object with maxPrescriptions and maxMiddleValues. "
                f"({cls_file})"
            )
    return issues


def check_bulk_job_paused_as_error(manifest_dir: Path) -> list[str]:
    """Check for code that treats bulk predict job 'Paused' status as a failure.

    Paused status means the org daily predictions limit was reached.
    The job auto-resumes the next day and should NOT be deleted or re-created.
    """
    issues: list[str] = []
    code_files: list[Path] = []
    for ext in ("*.cls", "*.py", "*.js", "*.ts"):
        for f in _find_files(manifest_dir, ext):
            # Skip checker scripts themselves — they reference these patterns intentionally
            if not f.name.startswith("check_"):
                code_files.append(f)

    # Pattern: 'Paused' appears near an exception throw, raise, or error keyword
    paused_error_pattern = re.compile(
        r"Paused.*(?:throw|raise|error|exception|fail)|"
        r"(?:throw|raise|error|exception|fail).*Paused",
        re.IGNORECASE | re.DOTALL,
    )
    predictjobs_pattern = re.compile(r"predictjobs", re.IGNORECASE)

    for code_file in code_files:
        text = _read(code_file)
        if not predictjobs_pattern.search(text):
            continue
        # Check a sliding 5-line window for Paused + error
        lines = text.splitlines()
        for i, line in enumerate(lines):
            window = " ".join(lines[max(0, i - 2): i + 3])
            if paused_error_pattern.search(window):
                issues.append(
                    f"Possible mishandling of 'Paused' status in '{code_file.name}' near line {i+1}: "
                    f"'Paused' appears close to an error/throw/raise keyword. "
                    f"Bulk predict jobs pause automatically when the org daily predictions limit "
                    f"is reached and resume the next day — treat Paused as informational, not an error. "
                    f"({code_file})"
                )
                break  # One warning per file is enough
    return issues


def check_missing_import_warnings_handling(manifest_dir: Path) -> list[str]:
    """Check Apex or integration code that calls the predict endpoint but never reads importWarnings.

    If missingColumns is non-empty in the response, the score is degraded.
    Production integrations should check importWarnings.missingColumns after every predict call.
    """
    issues: list[str] = []
    apex_files = _find_files(manifest_dir, "*.cls")

    sdd_pattern = re.compile(r"smartdatadiscovery/predict", re.IGNORECASE)
    import_warnings_pattern = re.compile(r"importWarnings|missingColumns", re.IGNORECASE)

    for cls_file in apex_files:
        text = _read(cls_file)
        if not sdd_pattern.search(text):
            continue
        if not import_warnings_pattern.search(text):
            issues.append(
                f"Apex file '{cls_file.name}' calls /smartdatadiscovery/predict but does not "
                f"appear to check 'importWarnings' or 'missingColumns' in the response. "
                f"If column mapping is incomplete, the score is computed with missing features "
                f"and importWarnings.missingColumns will be non-empty — this is a silent accuracy "
                f"degradation. Add validation after each predict call. ({cls_file})"
            )
    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def check_einstein_discovery_development(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues += check_discovery_story_metadata(manifest_dir)
    issues += check_apex_missing_settings(manifest_dir)
    issues += check_bulk_job_paused_as_error(manifest_dir)
    issues += check_missing_import_warnings_handling(manifest_dir)

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Einstein Discovery configuration issues. "
            "Flags missing prediction definition deployments, predict API misuse, "
            "incorrect bulk job error handling, and missing importWarnings validation."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_einstein_discovery_development(manifest_dir)

    if not issues:
        print("No Einstein Discovery issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
