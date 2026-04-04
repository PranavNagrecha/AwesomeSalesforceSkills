#!/usr/bin/env python3
"""Checker script for Agentforce Guardrails skill.

Analyzes Salesforce metadata (Bot/GenAiPlanner XML files or plain-text instruction
exports) for common guardrail anti-patterns documented in references/gotchas.md and
references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agentforce_guardrails.py [--help]
    python3 check_agentforce_guardrails.py --manifest-dir path/to/metadata
    python3 check_agentforce_guardrails.py --instruction-file path/to/instructions.txt
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Imperative prohibition starters that cause reasoning loop instability
IMPERATIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\byou must not\b", re.IGNORECASE),
    re.compile(r"\byou must\b", re.IGNORECASE),
    re.compile(r"\bnever\b", re.IGNORECASE),
    re.compile(r"\bdo not\b", re.IGNORECASE),
    re.compile(r"\bunder no circumstances\b", re.IGNORECASE),
    re.compile(r"\byou should never\b", re.IGNORECASE),
    re.compile(r"\balways\b", re.IGNORECASE),
]

# Routing-intent language that belongs in Classification Description, not Scope
ROUTING_IN_SCOPE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bdo not handle\b", re.IGNORECASE),
    re.compile(r"\bdo not route\b", re.IGNORECASE),
    re.compile(r"\bonly route\b", re.IGNORECASE),
    re.compile(r"\bnot for\b.*\bquestions\b", re.IGNORECASE),
    re.compile(r"\bdo not select this topic\b", re.IGNORECASE),
]

IMPERATIVE_THRESHOLD = 2  # Warn when more than this many imperatives found in a block


def _count_imperative_hits(text: str) -> list[str]:
    """Return list of matched imperative patterns found in text."""
    hits = []
    for pat in IMPERATIVE_PATTERNS:
        matches = pat.findall(text)
        hits.extend(matches)
    return hits


def _has_routing_language(text: str) -> list[str]:
    """Return list of routing-intent phrases found (appropriate for ClassDesc, not Scope)."""
    hits = []
    for pat in ROUTING_IN_SCOPE_PATTERNS:
        matches = pat.findall(text)
        hits.extend(matches)
    return hits


# ---------------------------------------------------------------------------
# Plain-text instruction file checks
# ---------------------------------------------------------------------------

def check_instruction_file(instruction_file: Path) -> list[str]:
    """Check a plain-text agent instruction or topic Scope export for anti-patterns."""
    issues: list[str] = []

    if not instruction_file.exists():
        issues.append(f"Instruction file not found: {instruction_file}")
        return issues

    text = instruction_file.read_text(encoding="utf-8", errors="replace")

    # Check imperative overuse
    hits = _count_imperative_hits(text)
    if len(hits) > IMPERATIVE_THRESHOLD:
        issues.append(
            f"{instruction_file.name}: {len(hits)} imperative prohibition(s) found "
            f"({', '.join(repr(h) for h in hits[:6])}). "
            "Consider rewriting as declarative boundary statements to avoid reasoning loop instability."
        )

    # Check for routing language that belongs in Classification Description
    routing_hits = _has_routing_language(text)
    if routing_hits:
        issues.append(
            f"{instruction_file.name}: Routing-intent language detected "
            f"({', '.join(repr(h) for h in routing_hits)}). "
            "Routing exclusions belong in Classification Description, not Scope or system instructions."
        )

    # Check for very short restricted-topic-style keyword entries (single-word lines)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines:
        words = line.split()
        if len(words) == 1 and len(words[0]) > 3:
            issues.append(
                f"{instruction_file.name}: Single-word line '{words[0]}' may be a restricted topic "
                "keyword entry — restricted topic entries should be full subject descriptions, not keywords."
            )

    return issues


# ---------------------------------------------------------------------------
# XML metadata checks (Bot/GenAiPlanner metadata files)
# ---------------------------------------------------------------------------

def check_bot_xml(xml_file: Path) -> list[str]:
    """Check a Bot or GenAiPlanner XML metadata file for guardrail anti-patterns."""
    issues: list[str] = []

    try:
        tree = ET.parse(xml_file)
    except ET.ParseError as exc:
        issues.append(f"{xml_file.name}: XML parse error — {exc}")
        return issues

    root = tree.getroot()
    # Strip namespace for simpler element searches
    ns_prefix = ""
    if root.tag.startswith("{"):
        ns_uri = root.tag.split("}")[0].lstrip("{")
        ns_prefix = f"{{{ns_uri}}}"

    def find_text(element: ET.Element, tag: str) -> str:
        node = element.find(f"{ns_prefix}{tag}")
        return node.text.strip() if node is not None and node.text else ""

    # Check BotDialogs/BotTopics for Scope anti-patterns
    for topic_el in root.iter(f"{ns_prefix}botVersions"):
        for dialog in topic_el.iter(f"{ns_prefix}botDialogs"):
            topic_name = find_text(dialog, "developerName") or find_text(dialog, "label") or "UnknownTopic"
            scope_text = find_text(dialog, "description")  # 'description' = Scope field in some schemas
            if scope_text:
                routing_hits = _has_routing_language(scope_text)
                if routing_hits:
                    issues.append(
                        f"{xml_file.name} > Topic '{topic_name}': Routing-intent language in topic "
                        f"description/Scope ({', '.join(repr(h) for h in routing_hits)}). "
                        "This should be in Classification Description, not Scope."
                    )
                imperative_hits = _count_imperative_hits(scope_text)
                if len(imperative_hits) > IMPERATIVE_THRESHOLD:
                    issues.append(
                        f"{xml_file.name} > Topic '{topic_name}': {len(imperative_hits)} imperative "
                        f"prohibitions in Scope field. Use declarative boundary language instead."
                    )

    # Check for GenAiPlanner (Agentforce) topic instructions
    for topic_el in root.iter(f"{ns_prefix}genAiPlannerTopics"):
        topic_name = find_text(topic_el, "topicApiName") or "UnknownTopic"

        scope_text = find_text(topic_el, "scope")
        if scope_text:
            routing_hits = _has_routing_language(scope_text)
            if routing_hits:
                issues.append(
                    f"{xml_file.name} > Topic '{topic_name}' Scope: Routing-intent language detected "
                    f"({', '.join(repr(h) for h in routing_hits)}). Move to Classification Description."
                )
            imperative_hits = _count_imperative_hits(scope_text)
            if len(imperative_hits) > IMPERATIVE_THRESHOLD:
                issues.append(
                    f"{xml_file.name} > Topic '{topic_name}' Scope: "
                    f"{len(imperative_hits)} imperative prohibitions. Rewrite as declarative statements."
                )

        instructions_text = find_text(topic_el, "instructions")
        if instructions_text:
            imperative_hits = _count_imperative_hits(instructions_text)
            if len(imperative_hits) > IMPERATIVE_THRESHOLD:
                issues.append(
                    f"{xml_file.name} > Topic '{topic_name}' instructions: "
                    f"{len(imperative_hits)} imperative prohibitions. "
                    "Rewrite as declarative boundary statements to avoid reasoning loop instability."
                )

    # Check GenAiPlanner system prompt / agent instructions
    system_prompt_el = root.find(f"{ns_prefix}systemPrompt")
    if system_prompt_el is not None and system_prompt_el.text:
        sp_text = system_prompt_el.text.strip()
        imperative_hits = _count_imperative_hits(sp_text)
        if len(imperative_hits) > IMPERATIVE_THRESHOLD:
            issues.append(
                f"{xml_file.name} > systemPrompt: {len(imperative_hits)} imperative prohibitions. "
                "Consider declarative boundary language."
            )

    # Check that at least one topic has a classificationDescription / routing description
    routing_desc_found = False
    for el in root.iter(f"{ns_prefix}classificationDescription"):
        if el.text and el.text.strip():
            routing_desc_found = True
            break
    for el in root.iter(f"{ns_prefix}routingDescription"):
        if el.text and el.text.strip():
            routing_desc_found = True
            break

    if not routing_desc_found and (
        list(root.iter(f"{ns_prefix}genAiPlannerTopics"))
        or list(root.iter(f"{ns_prefix}botDialogs"))
    ):
        issues.append(
            f"{xml_file.name}: No classificationDescription or routingDescription elements found. "
            "Topics require Classification Descriptions to drive LLM routing."
        )

    return issues


# ---------------------------------------------------------------------------
# Directory scan
# ---------------------------------------------------------------------------

def check_agentforce_guardrails(manifest_dir: Path) -> list[str]:
    """Scan manifest_dir for Bot and GenAiPlanner XML files and instruction text files."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Collect XML files (Bots/, GenAiPlanners/, and similar metadata folders)
    xml_files = list(manifest_dir.rglob("*.bot-meta.xml"))
    xml_files += list(manifest_dir.rglob("*.genAiPlanner-meta.xml"))
    xml_files += [
        p for p in manifest_dir.rglob("*.xml")
        if any(kw in p.name.lower() for kw in ("bot", "genai", "agent", "copilot"))
        and p not in xml_files
    ]

    for xml_file in xml_files:
        issues.extend(check_bot_xml(xml_file))

    # Collect plain-text instruction exports
    txt_files = [
        p for p in manifest_dir.rglob("*.txt")
        if any(kw in p.name.lower() for kw in ("instruction", "scope", "prompt", "guardrail", "system"))
    ]
    for txt_file in txt_files:
        issues.extend(check_instruction_file(txt_file))

    if not xml_files and not txt_files:
        issues.append(
            "No Bot/GenAiPlanner XML files or instruction text files found. "
            "Pass --manifest-dir pointing to your Salesforce metadata root, or "
            "--instruction-file pointing to a specific instructions export."
        )

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Agentforce Guardrails configuration and metadata for common issues. "
            "Detects: routing logic in Scope fields, imperative instruction overuse, "
            "single-word restricted topic entries, missing Classification Descriptions."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata. Scans for Bot/GenAiPlanner XML files.",
    )
    parser.add_argument(
        "--instruction-file",
        default=None,
        help="Path to a plain-text agent instruction or topic Scope export to check directly.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.instruction_file:
        issues.extend(check_instruction_file(Path(args.instruction_file)))

    if args.manifest_dir:
        issues.extend(check_agentforce_guardrails(Path(args.manifest_dir)))

    if not args.manifest_dir and not args.instruction_file:
        # Default: try current directory
        issues.extend(check_agentforce_guardrails(Path(".")))

    if not issues:
        print("No guardrail issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
