#!/usr/bin/env python3
"""Detect rollout-readiness gaps for an Agentforce Employee HR Service agent.

Walks an SFDX-style metadata tree (force-app/) and reports:

1. Agent (`Bot` / `GenAiPlanner` / `GenAiPlugin`) definitions whose subagents
   (called topics before April 2026) or actions reference Employee Service /
   HR concepts (leave, benefits, onboarding, time-off, paystub, hris) — these
   are the candidate agents for rollout.
2. Slack / Microsoft Teams app integration metadata under `connectedApps/`
   or `slackApps/` — the rollout requires a chat surface; absence is a
   warning.
3. Apex `@InvocableMethod` actions that take an employee identifier as
   input (potential PII / cross-employee leak surface — actions should
   bind to `UserInfo.getUserId()` instead).
4. Apex `@InvocableMethod` actions that perform HRIS callouts (look for
   Named Credentials matching common HRIS vendors) and flag any that do
   NOT use a Named Credential (raw endpoint string = secret leak risk).
5. Knowledge / Data Category metadata where a category named like
   compensation / pay / payroll is exposed via Public Knowledge Base
   (likely-internal HR content leaking to public channels).

Stdlib only — no pip dependencies.

Usage:
    python3 check_employee_hr_service_agent_rollout.py [--root force-app/main/default]

Exit codes:
    0  no findings
    1  findings present (informational, non-blocking)
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"s": "http://soap.sforce.com/2006/04/metadata"}

# Concept regexes — case-insensitive, applied to subagent / action / content.
HR_CONCEPT_RE = re.compile(
    r"\b(leave|pto|time[\s_-]?off|benefits?|onboard(?:ing)?|paystub|"
    r"payslip|hris|workday|adp|bamboohr|ukg|successfactors|enrollment|"
    r"open[\s_-]?enrollment|employee[\s_-]?service)\b",
    re.IGNORECASE,
)
HRIS_VENDOR_RE = re.compile(
    r"\b(workday|adp|bamboohr|ukg|successfactors|namely|gusto|paychex|"
    r"rippling|paycom)\b",
    re.IGNORECASE,
)
COMPENSATION_RE = re.compile(
    r"\b(compensation|pay[\s_-]?rate|payroll|salary|salaries|wage|bonus)\b",
    re.IGNORECASE,
)
INVOCABLE_METHOD_RE = re.compile(r"@InvocableMethod\b", re.IGNORECASE)
INVOCABLE_VAR_EMPLOYEE_RE = re.compile(
    r"@InvocableVariable[^\n;]*?\b(employee[\s_]?id|user[\s_]?id|"
    r"worker[\s_]?id|target[\s_]?employee)\b",
    re.IGNORECASE,
)
NAMED_CRED_CALLOUT_RE = re.compile(
    r"setEndpoint\s*\(\s*['\"]callout:([A-Za-z0-9_]+)",
    re.IGNORECASE,
)
HARDCODED_HTTP_RE = re.compile(
    r"setEndpoint\s*\(\s*['\"]https?://",
    re.IGNORECASE,
)


def find_hr_agent_definitions(metadata_root: Path) -> list[tuple[Path, str]]:
    findings: list[tuple[Path, str]] = []
    for ext in ("*.bot-meta.xml", "*.genAiPlanner-meta.xml",
                "*.genAiPlugin-meta.xml", "*.genAiPlannerBundle-meta.xml"):
        for fp in metadata_root.rglob(ext):
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if HR_CONCEPT_RE.search(text):
                findings.append((fp, _first_match(HR_CONCEPT_RE, text)))
    return findings


def _first_match(pattern: re.Pattern[str], text: str) -> str:
    m = pattern.search(text)
    return m.group(0) if m else ""


def find_chat_surface_metadata(metadata_root: Path) -> dict[str, list[Path]]:
    surfaces: dict[str, list[Path]] = {"slack": [], "teams": [], "embedded": []}
    for fp in metadata_root.rglob("*.connectedApp-meta.xml"):
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lower = text.lower()
        if "slack" in lower:
            surfaces["slack"].append(fp)
        if "teams" in lower or "microsoft teams" in lower:
            surfaces["teams"].append(fp)
    for fp in metadata_root.rglob("*.embeddedServiceConfig-meta.xml"):
        surfaces["embedded"].append(fp)
    for fp in metadata_root.rglob("*.embeddedServiceMenuSettings-meta.xml"):
        surfaces["embedded"].append(fp)
    return surfaces


def find_employee_id_inputs(apex_dirs: list[Path]) -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    for d in apex_dirs:
        if not d.exists():
            continue
        for fp in d.rglob("*.cls"):
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not INVOCABLE_METHOD_RE.search(text):
                continue
            for i, line in enumerate(text.splitlines()):
                if INVOCABLE_VAR_EMPLOYEE_RE.search(line):
                    findings.append((fp, i + 1, line.strip()))
    return findings


def find_hris_callouts(apex_dirs: list[Path]) -> list[tuple[Path, int, str, bool, bool]]:
    """Return (file, line, snippet, uses_named_credential, vendor_match)."""
    findings: list[tuple[Path, int, str, bool, bool]] = []
    for d in apex_dirs:
        if not d.exists():
            continue
        for ext in ("*.cls", "*.trigger"):
            for fp in d.rglob(ext):
                try:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                lines = text.splitlines()
                for i, line in enumerate(lines):
                    nc = NAMED_CRED_CALLOUT_RE.search(line)
                    raw = HARDCODED_HTTP_RE.search(line)
                    if not (nc or raw):
                        continue
                    name = nc.group(1) if nc else ""
                    vendor_match = bool(HRIS_VENDOR_RE.search(name)) or bool(
                        HRIS_VENDOR_RE.search(line)
                    )
                    if vendor_match or HRIS_VENDOR_RE.search("\n".join(lines[max(0, i - 30):i + 5])):
                        findings.append((fp, i + 1, line.strip(), bool(nc), vendor_match))
    return findings


def find_compensation_knowledge_leaks(metadata_root: Path) -> list[tuple[Path, str]]:
    findings: list[tuple[Path, str]] = []
    for fp in metadata_root.rglob("*.dataCategoryGroup-meta.xml"):
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if COMPENSATION_RE.search(text):
            findings.append((fp, _first_match(COMPENSATION_RE, text)))
    for fp in metadata_root.rglob("*.knowledge.publication-meta.xml"):
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lower = text.lower()
        if "publickb" in lower and COMPENSATION_RE.search(text):
            findings.append((fp, "PublicKb + compensation category"))
    return findings


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="force-app/main/default")
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"metadata root not found: {root}", file=sys.stderr)
        return 0

    classes_dir = root / "classes"
    triggers_dir = root / "triggers"

    findings_count = 0

    agent_findings = find_hr_agent_definitions(root)
    if agent_findings:
        print("\n## Candidate HR / Employee Service agent definitions")
        for fp, kw in agent_findings:
            print(f"  - {fp.relative_to(root)}: HR concept matched: {kw!r}")
        findings_count += len(agent_findings)

    surfaces = find_chat_surface_metadata(root)
    surface_count = sum(len(v) for v in surfaces.values())
    if agent_findings and surface_count == 0:
        print(
            "\n## WARN: HR-style agent found, but no Slack / Teams / "
            "Embedded Service deployment metadata in this tree"
        )
        print(
            "    Employees are unlikely to use the agent if it lives only "
            "in the Salesforce console. Consider Slack-first or Teams-first."
        )
        findings_count += 1
    elif surfaces["slack"] or surfaces["teams"] or surfaces["embedded"]:
        print("\n## Chat surface metadata found")
        for label, paths in surfaces.items():
            for fp in paths:
                print(f"  - {label}: {fp.relative_to(root)}")

    emp_id_findings = find_employee_id_inputs([classes_dir])
    if emp_id_findings:
        print(
            "\n## WARN: @InvocableMethod actions accepting an employee / user / "
            "worker id input (cross-employee data-leak surface)"
        )
        for fp, ln, snippet in emp_id_findings:
            print(f"  - {fp.relative_to(root)}:{ln}: {snippet}")
        print(
            "    Bind to UserInfo.getUserId() inside the action. Do not accept "
            "an employee id as input from the agent."
        )
        findings_count += len(emp_id_findings)

    hris_findings = find_hris_callouts([classes_dir, triggers_dir])
    if hris_findings:
        print("\n## HRIS-style callouts in Apex")
        for fp, ln, snippet, uses_nc, vendor in hris_findings:
            tag = ""
            if not uses_nc:
                tag = " [WARN: hard-coded endpoint — use Named Credentials]"
            print(f"  - {fp.relative_to(root)}:{ln}: {snippet}{tag}")
        findings_count += len(hris_findings)

    kb_leaks = find_compensation_knowledge_leaks(root)
    if kb_leaks:
        print(
            "\n## WARN: Compensation / payroll Data Category or Knowledge "
            "publication may be exposed to Public Knowledge Base"
        )
        for fp, why in kb_leaks:
            print(f"  - {fp.relative_to(root)}: {why}")
        findings_count += len(kb_leaks)

    if findings_count == 0:
        print(
            "No employee-HR-agent rollout gaps detected in this metadata tree."
        )
        return 0

    print(f"\nTotal findings: {findings_count}")
    print("Refer to the skill workflow for remediation steps.")
    print(f"ERROR: {findings_count} employee-HR-agent rollout gap(s); see report above.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
