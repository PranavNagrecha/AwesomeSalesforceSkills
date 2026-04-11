#!/usr/bin/env python3
"""Checker script for Agent Conversation Design skill.

Scans Salesforce bot metadata files for conversation design anti-patterns:
  - Fallback intent with utterances (should always be empty)
  - Internal queue label exposure in transfer/escalation messages
  - Utterance sets below the minimum threshold (20 per intent)
  - Single-stage fallback copy without clarification offer

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agent_conversation_design.py [--help]
    python3 check_agent_conversation_design.py --manifest-dir path/to/metadata
    python3 check_agent_conversation_design.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

# Minimum utterance count per intent for production use.
MINIMUM_UTTERANCE_COUNT = 20

# Patterns that indicate an internal queue or system identifier leaked into copy.
# These look like Salesforce queue naming conventions (underscores, all-caps segments).
INTERNAL_ID_PATTERN = re.compile(
    r"(?:"
    r"QUEUE_[A-Z0-9_]+"          # e.g. QUEUE_BILLING_T2_EN_US
    r"|[A-Z][A-Z0-9_]{4,}_Q\d*"  # e.g. Billing_Specialist_SF_Q_2024
    r"|_[A-Z]{2,}_[A-Z]{2,}_"    # e.g. _EN_US_ locale suffixes in queue names
    r")"
)

# Keywords that indicate a fallback message with no clarification offer.
# A valid stage-1 fallback should contain question words or list indicators.
FALLBACK_OFFER_INDICATORS = re.compile(
    r"(?:are you asking|do you mean|which of|one of these|did you mean|\?)",
    re.IGNORECASE,
)

# Bot metadata file patterns
BOT_FILE_GLOBS = [
    "**/*.bot",
    "**/*.botVersion",
    "**/*.bot-meta.xml",
    "**/*.botVersion-meta.xml",
]

# ── Helpers ───────────────────────────────────────────────────────────────────


def find_files(manifest_dir: Path, globs: list[str]) -> list[Path]:
    """Return all files matching any of the given glob patterns under manifest_dir."""
    found: list[Path] = []
    for pattern in globs:
        found.extend(manifest_dir.rglob(pattern.lstrip("**/")))
    return sorted(set(found))


def parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on parse failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from a tag name."""
    return tag.split("}")[-1] if "}" in tag else tag


def iter_children(element: ET.Element, tag: str) -> list[ET.Element]:
    """Return all direct children of element whose local tag matches tag."""
    return [child for child in element if strip_ns(child.tag) == tag]


def get_text(element: ET.Element, tag: str, default: str = "") -> str:
    """Return the text of the first child with the given tag, or default."""
    children = iter_children(element, tag)
    if children and children[0].text:
        return children[0].text.strip()
    return default


# ── Checks ────────────────────────────────────────────────────────────────────


def check_fallback_intent_has_no_utterances(root: ET.Element, path: Path) -> list[str]:
    """GOTCHA 1: Fallback intent must have zero utterances."""
    issues: list[str] = []
    for ml_intent in root.iter():
        if strip_ns(ml_intent.tag) not in ("mlIntent", "intent"):
            continue
        intent_name = get_text(ml_intent, "intentName") or get_text(ml_intent, "name", "")
        if "fallback" not in intent_name.lower():
            continue
        # Count utterances / training data entries
        utterances = (
            iter_children(ml_intent, "utterances")
            + iter_children(ml_intent, "trainingData")
            + iter_children(ml_intent, "mlIntentUtterances")
        )
        if utterances:
            issues.append(
                f"{path.name}: Fallback intent '{intent_name}' has {len(utterances)} utterance(s). "
                "The fallback intent must have ZERO utterances — it activates below the confidence "
                "threshold, not by utterance matching. Adding utterances turns it into a competing "
                "intent and causes misroutes."
            )
    return issues


def check_utterance_count_per_intent(root: ET.Element, path: Path) -> list[str]:
    """Check that non-fallback intents have at least MINIMUM_UTTERANCE_COUNT utterances."""
    issues: list[str] = []
    for ml_intent in root.iter():
        if strip_ns(ml_intent.tag) not in ("mlIntent", "intent"):
            continue
        intent_name = get_text(ml_intent, "intentName") or get_text(ml_intent, "name", "")
        if not intent_name or "fallback" in intent_name.lower():
            continue
        utterances = (
            iter_children(ml_intent, "utterances")
            + iter_children(ml_intent, "trainingData")
            + iter_children(ml_intent, "mlIntentUtterances")
        )
        count = len(utterances)
        if 0 < count < MINIMUM_UTTERANCE_COUNT:
            issues.append(
                f"{path.name}: Intent '{intent_name}' has only {count} utterance(s) "
                f"(minimum {MINIMUM_UTTERANCE_COUNT} for production). "
                "Expand with case-mined phrasings covering formal, casual, frustrated, and typo registers."
            )
    return issues


def check_escalation_copy_for_internal_ids(root: ET.Element, path: Path) -> list[str]:
    """Check transfer/escalation messages for internal queue label patterns."""
    issues: list[str] = []
    # Walk all text nodes in dialog steps and message variants
    for element in root.iter():
        local = strip_ns(element.tag)
        if local not in (
            "message",
            "text",
            "transferMessage",
            "messageText",
            "responseText",
            "label",
        ):
            continue
        text = (element.text or "").strip()
        if not text:
            continue
        if INTERNAL_ID_PATTERN.search(text):
            issues.append(
                f"{path.name}: Possible internal queue/system identifier in message copy: "
                f'"{text[:120]}". '
                "Replace with user-facing team name (e.g., 'billing support team') — "
                "internal identifiers erode user trust and break when queues are renamed."
            )
    return issues


def check_fallback_copy_has_clarification_offer(root: ET.Element, path: Path) -> list[str]:
    """Check that fallback dialog messages include a clarification offer, not just an apology."""
    issues: list[str] = []
    for element in root.iter():
        local = strip_ns(element.tag)
        if local not in ("message", "messageText", "responseText", "text"):
            continue
        text = (element.text or "").strip().lower()
        # Detect messages that look like fallback responses (contain apology/failure language)
        fallback_indicators = re.compile(
            r"(?:didn.t understand|not sure i understand|couldn.t understand|"
            r"sorry.*(?:understand|catch|follow)|try rephrasing|rephrase)",
            re.IGNORECASE,
        )
        if not fallback_indicators.search(text):
            continue
        # This looks like a fallback message — check it has a clarification offer
        if not FALLBACK_OFFER_INDICATORS.search(text):
            issues.append(
                f"{path.name}: Fallback message appears to lack a clarification offer: "
                f'"{(element.text or "").strip()[:120]}". '
                "Add a pick list or question to guide the user to a valid topic. "
                "A single apology with no offer produces high escalation rates."
            )
    return issues


# ── Main ──────────────────────────────────────────────────────────────────────


def check_agent_conversation_design(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    bot_files = find_files(manifest_dir, BOT_FILE_GLOBS)

    if not bot_files:
        # Not an error — org may use Agentforce topics (no bot XML) or metadata not exported
        return issues

    for bot_file in bot_files:
        root = parse_xml_safe(bot_file)
        if root is None:
            issues.append(f"{bot_file.name}: Could not parse XML — skipping checks.")
            continue

        issues.extend(check_fallback_intent_has_no_utterances(root, bot_file))
        issues.extend(check_utterance_count_per_intent(root, bot_file))
        issues.extend(check_escalation_copy_for_internal_ids(root, bot_file))
        issues.extend(check_fallback_copy_has_clarification_offer(root, bot_file))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Einstein Bot / Agentforce conversation design metadata for common issues. "
            "Flags: fallback intent with utterances, thin utterance sets, internal ID leaks "
            "in escalation copy, and single-stage fallback messages without a clarification offer."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_agent_conversation_design(manifest_dir)

    if not issues:
        print("No conversation design issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
