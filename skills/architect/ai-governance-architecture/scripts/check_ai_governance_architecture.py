#!/usr/bin/env python3
"""Checker script for AI Governance Architecture skill.

Checks org metadata or configuration relevant to AI Governance Architecture.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_ai_governance_architecture.py [--help]
    python3 check_ai_governance_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check AI Governance Architecture configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# Known external LLM provider hostnames that indicate a direct (non-Trust-Layer) callout.
_EXTERNAL_LLM_PATTERNS = re.compile(
    r"(openai\.com|api\.openai|anthropic\.com|azure\.openai|"
    r"cohere\.ai|cohere\.com|mistral\.ai|ai\.google|generativelanguage\.googleapis)",
    re.IGNORECASE,
)

# Named Credential metadata suffix
_NAMED_CREDENTIAL_SUFFIX = ".namedCredential-meta.xml"

# Topic/guardrail metadata suffix used by Agentforce
_TOPIC_SUFFIX = ".botTopicPolicy-meta.xml"

# Common Einstein Trust Layer permission set API names or named credential labels
_TRUST_LAYER_INDICATORS = re.compile(
    r"(EinsteinTrustLayer|Einstein_Trust_Layer|TrustLayer|trust_layer|"
    r"GenAITrustLayer|GenerativeAITrustLayer)",
    re.IGNORECASE,
)

# Data Cloud integration metadata indicators
_DATA_CLOUD_INDICATORS = re.compile(
    r"(DataCloud|data_cloud|cdp_|c360|customerDataPlatform|SalesforceDataCloud)",
    re.IGNORECASE,
)


def _find_files(root: Path, suffix: str) -> list[Path]:
    """Recursively find files ending with suffix under root."""
    return list(root.rglob(f"*{suffix}"))


def check_trust_layer_presence(manifest_dir: Path) -> list[str]:
    """Check for Named Credential or Permission Set evidence of Trust Layer configuration."""
    issues: list[str] = []

    # Look for any metadata file referencing Trust Layer
    all_xml = list(manifest_dir.rglob("*.xml"))
    trust_layer_found = False
    for xml_file in all_xml:
        try:
            content = xml_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _TRUST_LAYER_INDICATORS.search(content) or _TRUST_LAYER_INDICATORS.search(xml_file.name):
            trust_layer_found = True
            break

    if not trust_layer_found and all_xml:
        issues.append(
            "No Einstein Trust Layer configuration detected in metadata. "
            "Confirm Trust Layer is enabled (Setup > Einstein Trust Layer) and that "
            "Named Credentials or Permission Sets referencing Trust Layer are present."
        )

    return issues


def check_byollm_routing(manifest_dir: Path) -> list[str]:
    """Check Named Credentials for direct LLM provider endpoints that bypass Trust Layer."""
    issues: list[str] = []

    named_credentials = _find_files(manifest_dir, _NAMED_CREDENTIAL_SUFFIX)
    for nc_file in named_credentials:
        try:
            content = nc_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _EXTERNAL_LLM_PATTERNS.search(content):
            # Check if it also references Trust Layer routing (heuristic: label/endpoint mentions trust layer)
            if not _TRUST_LAYER_INDICATORS.search(content):
                issues.append(
                    f"Named Credential '{nc_file.name}' appears to reference an external LLM provider "
                    f"directly (matched pattern: {_EXTERNAL_LLM_PATTERNS.pattern[:60]}...). "
                    "Verify this callout is routed through Einstein Trust Layer to ensure "
                    "BYOLLM interactions are captured in the Generative AI Audit Trail. "
                    "Direct callouts to external LLM APIs bypass the Audit Trail entirely."
                )

    return issues


def check_apex_direct_llm_callouts(manifest_dir: Path) -> list[str]:
    """Check Apex classes for HttpCallout patterns referencing external LLM providers directly."""
    issues: list[str] = []

    apex_files = list(manifest_dir.rglob("*.cls"))
    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _EXTERNAL_LLM_PATTERNS.search(content):
            # Flag if HttpRequest or Http.send is present alongside external LLM reference
            if re.search(r"\bHttpRequest\b|\bHttp\(\)", content, re.IGNORECASE):
                issues.append(
                    f"Apex class '{apex_file.name}' contains an HttpRequest callout that references "
                    "an external LLM provider endpoint. Direct HTTP callouts to LLM APIs bypass "
                    "the Einstein Trust Layer and will not appear in the Generative AI Audit Trail. "
                    "Route all LLM calls through Trust Layer Named Credentials or ConnectApi.EinsteinLLM."
                )

    return issues


def check_data_cloud_integration(manifest_dir: Path) -> list[str]:
    """Check for evidence of Data Cloud integration (required for Generative AI Audit Trail)."""
    issues: list[str] = []

    all_xml = list(manifest_dir.rglob("*.xml"))
    data_cloud_found = False
    for xml_file in all_xml:
        try:
            content = xml_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _DATA_CLOUD_INDICATORS.search(content) or _DATA_CLOUD_INDICATORS.search(xml_file.name):
            data_cloud_found = True
            break

    if not data_cloud_found and all_xml:
        issues.append(
            "No Data Cloud integration detected in metadata. "
            "The Salesforce Generative AI Audit Trail requires Data Cloud as its storage layer — "
            "there is no alternative storage path. Orgs without Data Cloud have no native AI Audit Trail. "
            "Confirm Data Cloud is provisioned and connected if audit trail is required."
        )

    return issues


def check_topic_guardrails(manifest_dir: Path) -> list[str]:
    """Check for Agentforce topic guardrail metadata files."""
    issues: list[str] = []

    # Check for botTopicPolicy metadata (topic guardrails)
    topic_files = _find_files(manifest_dir, _TOPIC_SUFFIX)

    # Also check for any bot/agent metadata to confirm agents are deployed
    bot_files = list(manifest_dir.rglob("*.bot-meta.xml")) + list(manifest_dir.rglob("*.botVersion-meta.xml"))

    if bot_files and not topic_files:
        issues.append(
            "Agentforce bot metadata found but no topic guardrail (botTopicPolicy) metadata detected. "
            "Agentforce agents should have explicit topic guardrails defining what topics agents "
            "CANNOT discuss. Without guardrails, agents may respond to out-of-scope or harmful topics. "
            "Define topic guardrails as Policy-as-Code in version control."
        )

    return issues


def check_flow_llm_callouts(manifest_dir: Path) -> list[str]:
    """Check Flow metadata for external LLM callout actions that may bypass Trust Layer."""
    issues: list[str] = []

    flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))
    for flow_file in flow_files:
        try:
            content = flow_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _EXTERNAL_LLM_PATTERNS.search(content):
            issues.append(
                f"Flow '{flow_file.name}' references an external LLM provider endpoint. "
                "Verify this Flow routes LLM calls through Einstein Trust Layer. "
                "Direct Flow callouts to external LLM APIs bypass the Audit Trail."
            )

    return issues


def check_ai_governance_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_trust_layer_presence(manifest_dir))
    issues.extend(check_byollm_routing(manifest_dir))
    issues.extend(check_apex_direct_llm_callouts(manifest_dir))
    issues.extend(check_data_cloud_integration(manifest_dir))
    issues.extend(check_topic_guardrails(manifest_dir))
    issues.extend(check_flow_llm_callouts(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_ai_governance_architecture(manifest_dir)

    if not issues:
        print("No AI governance architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
