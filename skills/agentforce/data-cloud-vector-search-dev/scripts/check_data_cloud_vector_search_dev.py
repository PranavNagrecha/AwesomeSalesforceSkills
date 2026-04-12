#!/usr/bin/env python3
"""Checker script for Data Cloud Vector Search Dev skill.

Inspects Salesforce metadata and Data Cloud configuration artifacts in a local
SFDX project or retrieved metadata directory for common vector search issues
documented in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_vector_search_dev.py [--help]
    python3 check_data_cloud_vector_search_dev.py --manifest-dir path/to/metadata
    python3 check_data_cloud_vector_search_dev.py --manifest-dir . --verbose
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
            "Check Salesforce/Data Cloud metadata for common vector search configuration issues.\n"
            "Inspects grounding XML, Data Kit JSON, Data Stream XML, and Connected App XML\n"
            "for patterns documented in the data-cloud-vector-search-dev skill gotchas."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce/Data Cloud metadata (default: current directory).",
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
    """Return all files matching a glob pattern under root, sorted for determinism."""
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


def read_json_safe(path: Path) -> dict | list | None:
    """Read and parse a JSON file, returning None on error."""
    content = read_text_safe(path)
    if not content:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def xml_text(root: ET.Element, tag: str) -> str | None:
    """Return the text of the first element matching tag (namespace-stripped)."""
    for elem in root.iter():
        if elem.tag.split("}")[-1] == tag:
            return (elem.text or "").strip() or None
    return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_grounding_topk(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn when a Grounding configuration sets top-K above 7 (prompt budget risk)."""
    issues: list[str] = []

    grounding_files = find_files(manifest_dir, "*.aiGrounding-meta.xml")
    if not grounding_files:
        grounding_files = find_files(manifest_dir, "*.aiGrounding")

    for path in grounding_files:
        root = parse_xml_safe(path)
        if root is None:
            continue
        for elem in root.iter():
            tag = elem.tag.split("}")[-1]
            if tag == "topK":
                try:
                    top_k = int(elem.text or "0")
                except ValueError:
                    continue
                if top_k > 7:
                    issues.append(
                        f"[HIGH-TOP-K] {path.name}: topK={top_k} exceeds recommended max of 7. "
                        "High top-K increases prompt token consumption and retrieval latency. "
                        "(Gotcha 1 in SKILL.md; also see references/gotchas.md)"
                    )
                elif verbose:
                    print(f"  OK  {path.name}: topK={top_k} is within recommended range.")

    return issues


def check_grounding_metadata_filter_merge_fields(manifest_dir: Path, verbose: bool) -> list[str]:
    """Advisory: flag Grounding configs with static metadata filter values (possible null risk)."""
    issues: list[str] = []

    grounding_files = find_files(manifest_dir, "*.aiGrounding-meta.xml")
    if not grounding_files:
        grounding_files = find_files(manifest_dir, "*.aiGrounding")

    for path in grounding_files:
        content = read_text_safe(path)
        if not content:
            continue
        has_filter = "<metadataFilter>" in content or "<filterExpression>" in content
        has_merge_field = "{!" in content

        if has_filter and not has_merge_field and verbose:
            print(
                f"  INFO  {path.name}: metadata filter uses a static value (no merge field). "
                "Confirm the static value matches the DMO field value casing exactly — "
                "case mismatch produces zero results without an error. "
                "(references/gotchas.md — Gotcha: Metadata Filters Are Pre-Filters)"
            )
        elif has_filter and has_merge_field and verbose:
            print(
                f"  INFO  {path.name}: metadata filter uses a merge field. "
                "Ensure the merge field cannot resolve to null at runtime — "
                "a null filter value returns zero results silently."
            )

    return issues


def check_connected_app_cdpapi_scope(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn when a Connected App XML lacks the cdpapi scope required for Data Cloud Query API."""
    issues: list[str] = []

    # Connected Apps in SFDX are stored as .connectedApp-meta.xml
    app_files = find_files(manifest_dir, "*.connectedApp-meta.xml")
    if not app_files:
        app_files = find_files(manifest_dir, "*.connectedApp")

    for path in app_files:
        content = read_text_safe(path)
        if not content:
            continue

        # Only inspect apps that appear to be intended for Data Cloud integration
        is_dc_app = (
            "cdpapi" in content.lower()
            or "data_cloud" in content.lower()
            or "datacloud" in content.lower()
            or "c360" in content.lower()
        )
        if not is_dc_app:
            continue

        # Check that cdpapi is in the OAuth scopes
        has_cdpapi = "cdpapi" in content.lower()
        if not has_cdpapi:
            issues.append(
                f"[MISSING-CDPAPI-SCOPE] {path.name}: Connected App appears intended for Data Cloud "
                "but does not include the 'cdpapi' OAuth scope. The Data Cloud Vector Search Query API "
                "requires a token from a Connected App with cdpapi scope. A standard CRM token will "
                "produce a 401 Unauthorized response. (Gotcha 2 in references/gotchas.md)"
            )
        elif verbose:
            print(f"  OK  {path.name}: includes cdpapi scope.")

    return issues


def check_data_kit_includes_vector_index(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn when a datakit.json exists but does not reference a vector search index component."""
    issues: list[str] = []

    kit_files = find_files(manifest_dir, "datakit.json")
    for path in kit_files:
        kit = read_json_safe(path)
        if not isinstance(kit, dict):
            continue

        components = kit.get("components", [])
        has_vector_index = any(
            c.get("type", "").lower() in (
                "vectorsearchdefinition",
                "vectorindex",
                "vectorsearchindex",
                "aisearchindex",
            )
            for c in components
            if isinstance(c, dict)
        )
        if not has_vector_index:
            issues.append(
                f"[DATAKIT-MISSING-VECTOR-INDEX] {path}: datakit.json does not include a vector "
                "search index component. Vector search index configuration must be packaged via a "
                "Data Kit — it cannot be deployed via standard SFDX metadata deployment. "
                "(references/llm-anti-patterns.md — Anti-Pattern 6)"
            )
        elif verbose:
            print(f"  OK  {path.name}: Data Kit includes a vector index component.")

        # Check that a Data Stream component is also present
        has_data_stream = any(
            c.get("type", "").lower() in ("datastream", "datastreamsource")
            for c in components
            if isinstance(c, dict)
        )
        if has_vector_index and not has_data_stream and verbose:
            print(
                f"  INFO  {path.name}: Data Kit includes a vector index but no Data Stream component. "
                "Confirm the Data Stream configuration is either included or pre-exists in the target org."
            )

    return issues


def check_data_stream_refresh_mode(manifest_dir: Path, verbose: bool) -> list[str]:
    """Advisory: warn when Data Streams feeding a vector index use default batch refresh."""
    issues: list[str] = []

    stream_files = find_files(manifest_dir, "*.dataStream-meta.xml")
    if not stream_files:
        stream_files = find_files(manifest_dir, "*.dataStream")

    for path in stream_files:
        content = read_text_safe(path)
        if not content:
            continue

        has_refresh_mode = (
            "refreshMode" in content
            or "RefreshMode" in content
            or "continuousMode" in content
            or "nearRealTime" in content.lower()
        )
        has_continuous = (
            "continuous" in content.lower()
            or "nearRealTime" in content.lower()
            or "near_real_time" in content.lower()
        )

        if has_refresh_mode and not has_continuous and verbose:
            print(
                f"  INFO  {path.name}: Data Stream appears to use batch/scheduled refresh mode. "
                "New or updated source records will not appear in the vector search index until "
                "the next scheduled batch window. If near-real-time index currency is required, "
                "configure continuous refresh mode. (Gotcha 5 in references/gotchas.md)"
            )
        elif not has_refresh_mode and verbose:
            print(
                f"  INFO  {path.name}: refresh mode not explicitly configured — defaults to "
                "batch/scheduled. Consider setting continuous mode if index currency is important."
            )

    return issues


def check_prompt_template_grounding_placement(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn when a prompt template places the grounding merge field before role-framing instructions."""
    issues: list[str] = []

    template_files = find_files(manifest_dir, "*.promptTemplate-meta.xml")
    if not template_files:
        template_files = find_files(manifest_dir, "*.promptTemplate")

    for path in template_files:
        content = read_text_safe(path)
        if not content:
            continue
        if "{!grounding.chunks}" not in content and "{!Grounding" not in content:
            continue  # no grounding merge field — skip

        grounding_pos = content.find("{!grounding")
        if grounding_pos == -1:
            grounding_pos = content.find("{!Grounding")

        role_phrases = ["You are", "you are", "Your role", "As a ", "Act as"]
        role_pos = next(
            (content.find(p) for p in role_phrases if content.find(p) != -1),
            -1,
        )

        if role_pos != -1 and grounding_pos < role_pos:
            issues.append(
                f"[GROUNDING-PLACEMENT] {path.name}: the grounding merge field appears before "
                "the role-framing instruction in the prompt template. Place role framing first, "
                "then grounding context, then the task instruction. Incorrect placement can degrade "
                "instruction-following behavior."
            )
        elif verbose and grounding_pos != -1:
            print(f"  OK  {path.name}: grounding merge field placement looks correct.")

    return issues


def check_agent_topic_has_grounding(manifest_dir: Path, verbose: bool) -> list[str]:
    """Advisory: flag agent topics that appear knowledge-oriented but lack a Grounding reference."""
    issues: list[str] = []

    topic_files = find_files(manifest_dir, "*.aiTopic-meta.xml")
    if not topic_files:
        topic_files = find_files(manifest_dir, "*.aiTopic")

    # Keywords that suggest the topic should be grounded
    knowledge_keywords = [
        "knowledge", "article", "document", "retriev", "search", "faq", "lookup"
    ]

    for path in topic_files:
        content = read_text_safe(path)
        if not content:
            continue

        is_knowledge_topic = any(kw in content.lower() for kw in knowledge_keywords)
        has_grounding = (
            "grounding" in content.lower()
            or "aiGrounding" in content
            or "groundingConfig" in content
        )

        if is_knowledge_topic and not has_grounding:
            issues.append(
                f"[TOPIC-NO-GROUNDING] {path.name}: agent topic references knowledge/search "
                "concepts but has no Grounding configuration reference. If this topic answers "
                "questions from a knowledge corpus, a vector search Grounding configuration "
                "should be attached to avoid hallucinated responses."
            )
        elif verbose and is_knowledge_topic and has_grounding:
            print(f"  OK  {path.name}: knowledge-oriented topic has a Grounding configuration.")

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_all_checks(manifest_dir: Path, verbose: bool) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    all_issues: list[str] = []

    if not manifest_dir.exists():
        all_issues.append(f"Manifest directory not found: {manifest_dir}")
        return all_issues

    checks = [
        ("Grounding top-K values", check_grounding_topk),
        ("Grounding metadata filter merge fields", check_grounding_metadata_filter_merge_fields),
        ("Connected App cdpapi scope", check_connected_app_cdpapi_scope),
        ("Data Kit vector index inclusion", check_data_kit_includes_vector_index),
        ("Data Stream refresh mode", check_data_stream_refresh_mode),
        ("Prompt template grounding placement", check_prompt_template_grounding_placement),
        ("Agent topic grounding presence", check_agent_topic_has_grounding),
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
        print(f"Checking Data Cloud vector search configuration in: {manifest_dir}\n")

    issues = run_all_checks(manifest_dir, args.verbose)

    if not issues:
        print("No Data Cloud vector search configuration issues found.")
        return 0

    print(f"\n{len(issues)} issue(s) found:\n")
    for issue in issues:
        print(f"  ISSUE: {issue}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
