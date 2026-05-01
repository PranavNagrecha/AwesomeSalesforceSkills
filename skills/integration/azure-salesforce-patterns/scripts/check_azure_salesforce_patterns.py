#!/usr/bin/env python3
"""Static checks for Azure-Salesforce integration code in a project tree.

Scans Apex sources and metadata for high-confidence anti-patterns
documented in this skill's references/llm-anti-patterns.md and
references/gotchas.md. Stdlib only — no pip dependencies.

What this script catches:

  1. Hard-coded Azure endpoint hosts in Apex source (Function URLs,
     APIM, Service Bus REST, Blob Storage). Should be in a Named
     Credential.
  2. Azure Function `x-functions-key` headers set in Apex — Function
     Keys for any non-trivial endpoint should be replaced by Named
     Credential + External Credential with OAuth 2.0.
  3. Apex `@future(callout=true)` posts to Azure hosts — likely a
     missed Azure Service Bus Connector opportunity.
  4. Standard (non-high-volume) PlatformEvent custom-metadata-only
     declarations whose label contains 'service bus' / 'azure'
     keywords — Service Bus Connector listeners need high-volume PE
     channels (gotcha #1).

Signal tool, not a gate. Prints findings; exits 1 if any are found so
a CI step can flag the diff for review. Exit 0 means clean.

Usage:
    python3 check_azure_salesforce_patterns.py --src-root .
    python3 check_azure_salesforce_patterns.py --src-root force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Patterns that should never appear hard-coded in Apex source — auth and
# endpoint config belongs in a Named Credential, not in code.
_AZURE_HOST_RE = re.compile(
    r"https?://[^\s'\"<>]*(?:"
    r"\.azurewebsites\.net|"             # Functions default host
    r"\.azure-api\.net|"                 # API Management
    r"\.servicebus\.windows\.net|"       # Service Bus REST / AMQP host
    r"\.blob\.core\.windows\.net|"       # Blob Storage
    r"\.azurefd\.net|"                   # Azure Front Door
    r"\.cognitiveservices\.azure\.com"   # OpenAI / Cognitive
    r")",
    re.IGNORECASE,
)

# Function-Key header is the smell that says "no Named Credential".
_FUNCTION_KEY_RE = re.compile(
    r"setHeader\s*\(\s*['\"]x-functions-key['\"]",
    re.IGNORECASE,
)

# @future callouts to Azure hosts — flag for Service Bus Connector review.
_FUTURE_CALLOUT_RE = re.compile(
    r"@future\s*\([^)]*callout\s*=\s*true[^)]*\)",
    re.IGNORECASE,
)

# Custom Metadata or PlatformEvent metadata file with Azure/Service-Bus
# label and no high-volume marker.
_PE_LABEL_RE = re.compile(
    r"<label>([^<]*(?:azure|service\s*bus)[^<]*)</label>",
    re.IGNORECASE,
)
_HV_PE_RE = re.compile(r"<publishBehavior>PublishAfterCommit</publishBehavior>", re.IGNORECASE)
_PE_FILE_SUFFIX = ".platformEvent-meta.xml"


def _scan_apex_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for match in _AZURE_HOST_RE.finditer(text):
        line_no = text[: match.start()].count("\n") + 1
        findings.append(
            f"{path}:{line_no}: hard-coded Azure endpoint `{match.group(0)}` "
            "— move to a Named Credential + External Credential "
            "(see references/llm-anti-patterns.md § 2 and § 1)"
        )

    for match in _FUNCTION_KEY_RE.finditer(text):
        line_no = text[: match.start()].count("\n") + 1
        findings.append(
            f"{path}:{line_no}: Azure Function Key (`x-functions-key`) set in Apex "
            "— prefer OAuth 2.0 client-credentials via External Credential "
            "(see references/gotchas.md § 2)"
        )

    has_future = bool(_FUTURE_CALLOUT_RE.search(text))
    has_azure_host = bool(_AZURE_HOST_RE.search(text))
    if has_future and has_azure_host:
        findings.append(
            f"{path}: `@future(callout=true)` paired with an Azure host — "
            "consider the native Azure Service Bus Connector for async event "
            "shipping (see SKILL.md Pattern A and references/llm-anti-patterns.md § 1)"
        )

    return findings


def _scan_pe_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    label_match = _PE_LABEL_RE.search(text)
    if not label_match:
        return findings

    if not _HV_PE_RE.search(text):
        findings.append(
            f"{path}: Platform Event '{label_match.group(1).strip()}' looks "
            "Service-Bus-related but is not declared High Volume "
            "(`<publishBehavior>PublishAfterCommit</publishBehavior>`). "
            "Listener path will lose messages under load "
            "(see references/gotchas.md § 1)."
        )

    return findings


def scan_tree(root: Path) -> list[str]:
    findings: list[str] = []
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    apex_files = list(root.rglob("*.cls")) + list(root.rglob("*.trigger"))
    pe_files = list(root.rglob(f"*{_PE_FILE_SUFFIX}"))

    for apex_file in apex_files:
        findings.extend(_scan_apex_file(apex_file))
    for pe_file in pe_files:
        findings.extend(_scan_pe_file(pe_file))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex + PlatformEvent metadata for Azure-integration "
            "anti-patterns (hard-coded endpoints, Function Keys, missed "
            "Service Bus Connector opportunities, non-high-volume PE "
            "channels for the listener path)."
        ),
    )
    parser.add_argument(
        "--src-root",
        default=".",
        help="Root of the source tree to scan (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Azure-Salesforce integration anti-patterns detected.")
        return 0

    for finding in findings:
        print(f"WARN: {finding}", file=sys.stderr)
    print(
        f"\n{len(findings)} finding(s). See references/llm-anti-patterns.md "
        "and references/gotchas.md for rationale and the correct pattern.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
