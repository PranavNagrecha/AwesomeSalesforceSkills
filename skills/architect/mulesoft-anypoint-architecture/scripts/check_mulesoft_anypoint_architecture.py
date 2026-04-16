#!/usr/bin/env python3
"""Checker script for MuleSoft Anypoint Architecture skill.

Validates MuleSoft architecture documents and Mule application configs for common
deployment and governance issues. Uses stdlib only — no pip dependencies.

Usage:
    python3 check_mulesoft_anypoint_architecture.py --manifest-dir <path>

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

import argparse
import re
import sys
from pathlib import Path


def check_missing_autodiscovery(path: Path) -> list[str]:
    """Warn if Mule XML config files reference api-manager but lack autodiscovery."""
    issues = []
    xml_files = list(path.glob("**/*.xml"))

    for xml_file in xml_files:
        try:
            content = xml_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Only check files that look like Mule application configs
        if "mule" not in content.lower() and "http:listener" not in content.lower():
            continue
        has_api_manager_ref = re.search(r"api-manager|apimanager|API Manager", content, re.IGNORECASE)
        has_autodiscovery = re.search(r"api-gateway:autodiscovery|autodiscovery", content, re.IGNORECASE)
        if has_api_manager_ref and not has_autodiscovery:
            issues.append(
                f"WARN: {xml_file.name} references API Manager but does not configure Autodiscovery. "
                f"Without api-gateway:autodiscovery bound to the correct API Instance ID, the Mule runtime "
                f"will not contact API Manager and policies will not be enforced."
            )
    return issues


def check_runtime_fabric_with_edge(path: Path) -> list[str]:
    """Warn if architecture docs specify both Runtime Fabric and Anypoint Security Edge/Tokenization."""
    issues = []
    doc_files = (
        list(path.glob("**/*.md")) +
        list(path.glob("**/*.txt")) +
        list(path.glob("**/*.yaml")) +
        list(path.glob("**/*.yml"))
    )

    for doc_file in doc_files:
        try:
            content = doc_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        has_rtf = re.search(r"Runtime Fabric|runtime.fabric|RTF", content, re.IGNORECASE)
        has_edge = re.search(r"Anypoint Security Edge|Tokenization|anypoint.edge", content, re.IGNORECASE)
        if has_rtf and has_edge:
            issues.append(
                f"WARN: {doc_file.name} specifies both Runtime Fabric and Anypoint Security Edge or Tokenization. "
                f"Anypoint Security Edge and Tokenization are not supported on Runtime Fabric. "
                f"If Edge or Tokenization is required, the runtime model must be CloudHub 1.0 or CloudHub 2.0."
            )
    return issues


def check_rtf_without_kubernetes_assessment(path: Path) -> list[str]:
    """Warn if architecture docs recommend Runtime Fabric without mentioning Kubernetes requirements."""
    issues = []
    doc_files = list(path.glob("**/*.md")) + list(path.glob("**/*.txt"))

    for doc_file in doc_files:
        try:
            content = doc_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        has_rtf_recommendation = re.search(
            r"recommend.*Runtime Fabric|select.*Runtime Fabric|use.*Runtime Fabric|Runtime Fabric.*recommended",
            content, re.IGNORECASE
        )
        has_kubernetes_assessment = re.search(
            r"Kubernetes|k8s|cluster management|container orchestration", content, re.IGNORECASE
        )
        if has_rtf_recommendation and not has_kubernetes_assessment:
            issues.append(
                f"WARN: {doc_file.name} recommends Runtime Fabric but does not mention Kubernetes requirements. "
                f"Runtime Fabric requires the customer to provision and operate Kubernetes clusters. "
                f"Confirm the organization has Kubernetes operations capability before selecting RTF."
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate MuleSoft Anypoint architecture documents and Mule app configs."
    )
    parser.add_argument("--manifest-dir", type=Path, default=Path("."),
                        help="Directory to scan for Mule XML configs and architecture documents")
    args = parser.parse_args()

    all_issues: list[str] = []

    if args.manifest_dir.exists():
        all_issues.extend(check_missing_autodiscovery(args.manifest_dir))
        all_issues.extend(check_runtime_fabric_with_edge(args.manifest_dir))
        all_issues.extend(check_rtf_without_kubernetes_assessment(args.manifest_dir))
    else:
        all_issues.append(f"ERROR: Directory not found: {args.manifest_dir}")

    if all_issues:
        for issue in all_issues:
            print(issue)
        return 1

    print("OK: No MuleSoft Anypoint architecture issues detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
