#!/usr/bin/env python3
"""Checker script for RAG Patterns in Salesforce skill.

Inspects Salesforce metadata in a local SFDX project or retrieved metadata directory
for common RAG configuration issues documented in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_rag_patterns_in_salesforce.py [--help]
    python3 check_rag_patterns_in_salesforce.py --manifest-dir path/to/metadata
    python3 check_rag_patterns_in_salesforce.py --manifest-dir . --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common RAG grounding configuration issues.\n"
            "Inspects agent topic XML, prompt template XML, and Data Cloud metadata "
            "for patterns documented in the rag-patterns-in-salesforce skill gotchas."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print informational messages in addition to issues.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return sorted(root.rglob(pattern))


def parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file, returning None on parse error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def read_text_safe(path: Path) -> str:
    """Read a file as text, returning empty string on error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_grounding_topk(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn when a Grounding configuration sets top-K above 7 (prompt budget risk)."""
    issues: list[str] = []

    # Grounding configs live in aiGrounding/ directory as XML metadata files
    grounding_files = find_files(manifest_dir, "*.aiGrounding")
    if not grounding_files:
        grounding_files = find_files(manifest_dir, "*.aiGrounding-meta.xml")

    for path in grounding_files:
        root = parse_xml_safe(path)
        if root is None:
            continue
        # Namespace-agnostic search
        for elem in root.iter():
            tag = elem.tag.split("}")[-1]  # strip namespace
            if tag == "topK":
                try:
                    top_k = int(elem.text or "0")
                except ValueError:
                    continue
                if top_k > 7:
                    issues.append(
                        f"[HIGH-TOP-K] {path.name}: topK={top_k} exceeds recommended max of 7. "
                        "High top-K increases prompt token consumption and retrieval latency. "
                        "See gotcha 5 in references/gotchas.md."
                    )
                elif verbose:
                    print(f"  OK  {path.name}: topK={top_k}")

    return issues


def check_grounding_filter_merge_fields(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn when a Grounding config uses a metadata filter but no fallback is apparent."""
    issues: list[str] = []

    grounding_files = find_files(manifest_dir, "*.aiGrounding")
    if not grounding_files:
        grounding_files = find_files(manifest_dir, "*.aiGrounding-meta.xml")

    for path in grounding_files:
        content = read_text_safe(path)
        if not content:
            continue
        has_filter = "<metadataFilter>" in content or "<filterExpression>" in content
        has_merge_field = "{!" in content
        if has_filter and has_merge_field:
            if verbose:
                print(
                    f"  INFO  {path.name}: uses metadata filter with merge field. "
                    "Ensure the merge field cannot resolve to null at runtime (gotcha 2)."
                )
            # This is advisory, not a hard issue — note it but don't flag as error
        elif has_filter and not has_merge_field:
            if verbose:
                print(
                    f"  INFO  {path.name}: metadata filter uses a static value (no merge field). "
                    "Confirm the static value matches DMO field casing exactly."
                )

    return issues


def check_prompt_template_grounding_placement(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn when a prompt template uses grounding but the merge field appears before role framing."""
    issues: list[str] = []

    # Prompt templates are stored as .promptTemplate-meta.xml or in promptTemplates/
    template_files = find_files(manifest_dir, "*.promptTemplate-meta.xml")
    if not template_files:
        template_files = find_files(manifest_dir, "*.promptTemplate")

    for path in template_files:
        content = read_text_safe(path)
        if not content:
            continue
        if "{!grounding.chunks}" not in content and "{!Grounding" not in content:
            continue  # no grounding merge field — skip

        # Heuristic: check if grounding merge field appears before a "You are" role-framing phrase
        grounding_pos = content.find("{!grounding")
        role_pos = min(
            (content.find(phrase) for phrase in ["You are", "you are", "Your role", "As a "]
             if content.find(phrase) != -1),
            default=-1,
        )
        if role_pos != -1 and grounding_pos < role_pos:
            issues.append(
                f"[GROUNDING-PLACEMENT] {path.name}: the grounding merge field appears before the "
                "role-framing instruction in the prompt template. Place role framing first, then "
                "grounding context, then the task instruction. See Pattern 3 in SKILL.md."
            )
        elif verbose and grounding_pos != -1:
            print(f"  OK  {path.name}: grounding merge field placement looks correct.")

    return issues


def check_agent_topic_grounding_present(manifest_dir: Path, verbose: bool) -> list[str]:
    """Advisory: flag agent topics that have no Grounding configuration attached."""
    issues: list[str] = []

    topic_files = find_files(manifest_dir, "*.aiTopic-meta.xml")
    if not topic_files:
        topic_files = find_files(manifest_dir, "*.aiTopic")

    for path in topic_files:
        content = read_text_safe(path)
        if not content:
            continue
        has_grounding_ref = (
            "<grounding" in content.lower()
            or "aiGrounding" in content
            or "groundingConfig" in content
        )
        if not has_grounding_ref and verbose:
            print(
                f"  INFO  {path.name}: agent topic has no grounding configuration reference. "
                "If this topic handles knowledge questions, consider adding RAG grounding. "
                "See SKILL.md for guidance."
            )

    return issues


def check_data_kit_includes_vector_index(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn when a datakit.json exists but does not reference a vector search index."""
    issues: list[str] = []

    kit_files = find_files(manifest_dir, "datakit.json")
    for path in kit_files:
        content = read_text_safe(path)
        if not content:
            continue
        try:
            kit = json.loads(content)
        except json.JSONDecodeError:
            continue

        # Check for vector index component type in the kit manifest
        components = kit.get("components", [])
        has_vector_index = any(
            c.get("type", "").lower() in ("vectorsearchdefinition", "vectorindex", "vectorsearchindex")
            for c in components
            if isinstance(c, dict)
        )
        if not has_vector_index:
            issues.append(
                f"[DATAKIT-MISSING-VECTOR-INDEX] {path}: datakit.json does not include a vector "
                "search index component. If this package includes RAG grounding, the vector index "
                "configuration must be included in the Data Kit. See gotcha 6 in references/gotchas.md."
            )
        elif verbose:
            print(f"  OK  {path.name}: Data Kit includes a vector index component.")

    return issues


def check_knowledge_stream_filter(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn when a Data Stream mapping Knowledge articles lacks a PublishStatus filter."""
    issues: list[str] = []

    # Data Stream metadata files
    stream_files = find_files(manifest_dir, "*.dataStream-meta.xml")
    if not stream_files:
        stream_files = find_files(manifest_dir, "*.dataStream")

    for path in stream_files:
        content = read_text_safe(path)
        if not content:
            continue
        is_knowledge_stream = (
            "KnowledgeArticle" in content or "Knowledge__kav" in content
        )
        if not is_knowledge_stream:
            continue

        has_publish_filter = "PublishStatus" in content or "publishStatus" in content
        if not has_publish_filter:
            issues.append(
                f"[KNOWLEDGE-NO-PUBLISH-FILTER] {path.name}: Knowledge article Data Stream does not "
                "appear to filter by PublishStatus. Draft and archived articles will be ingested "
                "into the vector index. Add a filter for PublishStatus = 'Online' to exclude "
                "non-published content. See anti-pattern in references/well-architected.md."
            )
        elif verbose:
            print(f"  OK  {path.name}: Knowledge Data Stream includes PublishStatus filter.")

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_all_checks(manifest_dir: Path, verbose: bool) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    all_issues: list[str] = []

    if not manifest_dir.exists():
        all_issues.append(f"Manifest directory not found: {manifest_dir}")
        return all_issues

    checks = [
        ("Grounding top-K values", check_grounding_topk),
        ("Grounding filter merge fields", check_grounding_filter_merge_fields),
        ("Prompt template grounding placement", check_prompt_template_grounding_placement),
        ("Agent topic grounding presence", check_agent_topic_grounding_present),
        ("Data Kit vector index inclusion", check_data_kit_includes_vector_index),
        ("Knowledge Data Stream publish filter", check_knowledge_stream_filter),
    ]

    for label, fn in checks:
        if verbose:
            print(f"\nRunning check: {label}")
        issues = fn(manifest_dir, verbose)
        all_issues.extend(issues)

    return all_issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    if args.verbose:
        print(f"Checking RAG configuration in: {manifest_dir}\n")

    issues = run_all_checks(manifest_dir, args.verbose)

    if not issues:
        print("No RAG configuration issues found.")
        return 0

    print(f"\n{len(issues)} issue(s) found:\n")
    for issue in issues:
        print(f"  ISSUE: {issue}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
