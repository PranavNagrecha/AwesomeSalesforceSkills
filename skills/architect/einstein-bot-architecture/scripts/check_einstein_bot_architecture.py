#!/usr/bin/env python3
"""Checker script for Einstein Bot Architecture skill.

Checks org metadata or configuration relevant to Einstein Bot Architecture.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_einstein_bot_architecture.py [--help]
    python3 check_einstein_bot_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Einstein Bot Architecture configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_bot_metadata(manifest_dir: Path) -> list[Path]:
    """Find Einstein Bot metadata files (.bot-meta.xml) in the manifest directory."""
    bot_files: list[Path] = []
    bots_dir = manifest_dir / "bots"
    if bots_dir.exists():
        for f in bots_dir.rglob("*.bot-meta.xml"):
            bot_files.append(f)
    # Also check force-app style layout
    force_app = manifest_dir / "force-app" / "main" / "default" / "bots"
    if force_app.exists():
        for f in force_app.rglob("*.bot-meta.xml"):
            bot_files.append(f)
    return bot_files


def _find_bot_version_metadata(manifest_dir: Path) -> list[Path]:
    """Find Einstein Bot Version metadata files."""
    version_files: list[Path] = []
    for search_root in [manifest_dir / "bots", manifest_dir / "force-app"]:
        if search_root.exists():
            for f in search_root.rglob("*.botVersion-meta.xml"):
                version_files.append(f)
    return version_files


def _check_bot_has_fallback_dialog(tree: ET.ElementTree, filepath: Path) -> list[str]:
    """Check that a bot version defines a fallback or confused dialog."""
    issues: list[str] = []
    root = tree.getroot()
    ns = ""
    # Detect namespace
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    dialog_names = []
    for dialog in root.iter(f"{ns}botDialogs"):
        label_el = dialog.find(f"{ns}label")
        name_el = dialog.find(f"{ns}developerName")
        name = ""
        if name_el is not None and name_el.text:
            name = name_el.text.lower()
        elif label_el is not None and label_el.text:
            name = label_el.text.lower()
        dialog_names.append(name)

    fallback_keywords = ["fallback", "confused", "not_understood", "notunderstood", "catch_all", "catchall"]
    has_fallback = any(
        any(kw in name for kw in fallback_keywords)
        for name in dialog_names
    )
    if dialog_names and not has_fallback:
        issues.append(
            f"{filepath.name}: No fallback/confused dialog detected. "
            f"Dialogs found: {', '.join(dialog_names)}. "
            f"A fallback dialog is required to handle unrecognized input."
        )
    return issues


def _check_transfer_has_variables(tree: ET.ElementTree, filepath: Path) -> list[str]:
    """Check that Transfer to Agent steps map at least one bot variable."""
    issues: list[str] = []
    root = tree.getroot()
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    for step in root.iter(f"{ns}botSteps"):
        step_type_el = step.find(f"{ns}type")
        if step_type_el is not None and step_type_el.text == "Transfer":
            # Check for variable mappings in the step
            has_mapping = False
            for mapping in step.iter(f"{ns}botVariableOperation"):
                has_mapping = True
                break
            if not has_mapping:
                # Also check for transferBotVariables
                for var in step.iter(f"{ns}transferBotVariables"):
                    has_mapping = True
                    break
            if not has_mapping:
                issues.append(
                    f"{filepath.name}: Transfer to Agent step found without variable mappings. "
                    f"Agents will not receive conversation context. Map bot variables to "
                    f"LiveChatTranscript or MessagingSession fields."
                )
    return issues


def _check_intent_utterance_count(manifest_dir: Path) -> list[str]:
    """Check that intent definitions have at least 20 utterances each."""
    issues: list[str] = []
    # MlDomain metadata contains intent definitions
    for search_root in [manifest_dir, manifest_dir / "force-app"]:
        if not search_root.exists():
            continue
        for f in search_root.rglob("*.mlDomain-meta.xml"):
            try:
                tree = ET.parse(f)
                root = tree.getroot()
                ns = ""
                if root.tag.startswith("{"):
                    ns = root.tag.split("}")[0] + "}"
                for intent in root.iter(f"{ns}mlIntents"):
                    label_el = intent.find(f"{ns}label")
                    label = label_el.text if label_el is not None and label_el.text else "unknown"
                    utterance_count = sum(1 for _ in intent.iter(f"{ns}mlIntentUtterances"))
                    if utterance_count < 20:
                        issues.append(
                            f"{f.name}: Intent '{label}' has only {utterance_count} utterances "
                            f"(minimum 20 required, 50+ recommended for production accuracy)."
                        )
            except ET.ParseError:
                issues.append(f"{f.name}: Failed to parse ML domain metadata.")
    return issues


def check_einstein_bot_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    bot_files = _find_bot_metadata(manifest_dir)
    version_files = _find_bot_version_metadata(manifest_dir)

    if not bot_files and not version_files:
        issues.append(
            f"No Einstein Bot metadata found in {manifest_dir}. "
            f"Expected .bot-meta.xml or .botVersion-meta.xml files "
            f"under bots/ or force-app/main/default/bots/."
        )
        return issues

    # Check each bot version for architectural issues
    for vf in version_files:
        try:
            tree = ET.parse(vf)
            issues.extend(_check_bot_has_fallback_dialog(tree, vf))
            issues.extend(_check_transfer_has_variables(tree, vf))
        except ET.ParseError:
            issues.append(f"{vf.name}: Failed to parse bot version metadata.")

    # Check intent utterance counts
    issues.extend(_check_intent_utterance_count(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_einstein_bot_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
