#!/usr/bin/env python3
"""Checker script for AI Platform Architecture skill.

Scans Salesforce metadata (SFDX/Metadata API format) for common AI platform
architecture issues: BYOLLM model assignments to agents without documented
ZDR confirmation, missing audit trail configuration, and agent topic
configuration patterns that indicate Supervisor/Specialist design problems.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_ai_platform_architecture.py [--help]
    python3 check_ai_platform_architecture.py --manifest-dir path/to/metadata
    python3 check_ai_platform_architecture.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Metadata file extensions and directories used by Agentforce / Einstein
AGENT_TOPIC_EXTENSIONS = {".bot", ".botVersion"}
EINSTEIN_CONFIG_DIRS = {"einstein", "aiApplications", "aiSettings"}
CONNECTED_APP_DIRS = {"connectedApps"}

# Keywords that indicate a model configuration is BYOLLM (not Salesforce Default)
BYOLLM_KEYWORDS = [
    "byollm",
    "custom_model",
    "customModel",
    "externalModel",
    "external_model",
    "modelEndpoint",
    "model_endpoint",
]

# Words in topic descriptions that suggest broad/vague scope overlap risk
VAGUE_TOPIC_KEYWORDS = [
    "general",
    "anything",
    "all requests",
    "all tasks",
    "any question",
    "everything",
    "miscellaneous",
    "other",
    "default",
    "fallback",
]


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_byollm_in_agent_configs(manifest_dir: Path) -> list[str]:
    """Check for BYOLLM keyword patterns in agent/bot configuration files."""
    issues: list[str] = []
    found_files = list(manifest_dir.rglob("*.botVersion")) + list(manifest_dir.rglob("*.bot"))
    for fpath in found_files:
        content = fpath.read_text(encoding="utf-8", errors="replace")
        for kw in BYOLLM_KEYWORDS:
            if kw.lower() in content.lower():
                issues.append(
                    f"Potential BYOLLM model reference found in {fpath.name}: keyword '{kw}'. "
                    f"Confirm this agent does not access PII/PCI data, or document ZDR verification "
                    f"for the external model provider."
                )
                break  # one warning per file is enough
    return issues


def check_vague_topic_descriptions(manifest_dir: Path) -> list[str]:
    """Check bot/agent topic XML for vague description language that risks Supervisor routing errors."""
    issues: list[str] = []
    topic_files = list(manifest_dir.rglob("*.botTopic")) + list(manifest_dir.rglob("*.mlTopic"))
    for fpath in topic_files:
        try:
            tree = ET.parse(fpath)
            root = tree.getroot()
        except ET.ParseError:
            continue

        # Check description elements
        for elem in root.iter():
            if elem.tag.lower() in {"description", "topicdescription", "summary"}:
                desc = (elem.text or "").lower()
                for kw in VAGUE_TOPIC_KEYWORDS:
                    if kw in desc:
                        issues.append(
                            f"Vague topic description in {fpath.name}: contains '{kw}'. "
                            f"Supervisor routing is LLM-driven; vague descriptions cause misrouting. "
                            f"Use intent-specific, non-overlapping language."
                        )
                        break
    return issues


def check_einstein_settings_xml(manifest_dir: Path) -> list[str]:
    """Check EinsteinSettings or AiSettings metadata for audit trail and masking flags."""
    issues: list[str] = []
    settings_files = (
        list(manifest_dir.rglob("EinsteinSettings.settings"))
        + list(manifest_dir.rglob("AiSettings.settings"))
        + list(manifest_dir.rglob("EinsteinGptSettings.settings"))
    )

    for fpath in settings_files:
        try:
            tree = ET.parse(fpath)
            root = tree.getroot()
        except ET.ParseError:
            issues.append(f"Could not parse settings file: {fpath.name}")
            continue

        content_lower = fpath.read_text(encoding="utf-8", errors="replace").lower()

        # Check for audit trail / interaction log settings
        audit_enabled = any(
            kw in content_lower
            for kw in ["audittrail", "audit_trail", "interactionlog", "interaction_log", "enableaudit"]
        )
        if not audit_enabled:
            issues.append(
                f"No audit trail configuration detected in {fpath.name}. "
                f"Trust Layer audit trail must be explicitly enabled before AI features go live; "
                f"it is not retroactive. Verify audit trail is configured in Einstein Setup."
            )

        # Check for data masking settings
        masking_enabled = any(
            kw in content_lower
            for kw in ["datamasking", "data_masking", "enablemasking", "llmdatamasking"]
        )
        if not masking_enabled:
            issues.append(
                f"No data masking configuration detected in {fpath.name}. "
                f"If agents access PII or PCI data, confirm LLM data masking is enabled "
                f"in Trust Layer setup for applicable features."
            )

    return issues


def check_agent_model_alias_uniqueness(manifest_dir: Path) -> list[str]:
    """Check for multiple bot/agent files referencing the same model alias string."""
    issues: list[str] = []
    alias_to_files: dict[str, list[str]] = {}

    for fpath in list(manifest_dir.rglob("*.bot")) + list(manifest_dir.rglob("*.botVersion")):
        content = fpath.read_text(encoding="utf-8", errors="replace")
        # Simple heuristic: look for modelAlias or modelName XML elements
        try:
            tree = ET.parse(fpath)
            root = tree.getroot()
        except ET.ParseError:
            continue

        for elem in root.iter():
            if elem.tag.lower() in {"modelalias", "modelname", "llmmodel", "modelidentifier"}:
                alias = (elem.text or "").strip()
                if alias:
                    alias_to_files.setdefault(alias, []).append(fpath.name)

    for alias, files in alias_to_files.items():
        if len(files) > 1:
            issues.append(
                f"Model alias '{alias}' is shared across multiple agent files: {', '.join(files)}. "
                f"Shared model aliases mean a single Model Builder change affects all assigned agents "
                f"simultaneously. Consider dedicated aliases per agent role for independent change control."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_ai_platform_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_byollm_in_agent_configs(manifest_dir))
    issues.extend(check_vague_topic_descriptions(manifest_dir))
    issues.extend(check_einstein_settings_xml(manifest_dir))
    issues.extend(check_agent_model_alias_uniqueness(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for AI platform architecture issues: "
            "BYOLLM usage without ZDR documentation, vague agent topic descriptions, "
            "missing audit trail / masking configuration, and shared model aliases."
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
    issues = check_ai_platform_architecture(manifest_dir)

    if not issues:
        print("No AI platform architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
