#!/usr/bin/env python3
"""Pre-rollout checker for the Agentforce Sales Coach template.

Walks an SFDX-style metadata tree (force-app/) and reports configuration drift
that would degrade Sales Coach effectiveness or block the rollout entirely:

1. Missing or unpublished agent definition that references Sales Coach topics
   (looks under force-app/main/default/genAiPlannerBundles/, agents/, or
   bots/, depending on metadata vintage).
2. Opportunity stage list drift from the standard stage names that the
   shipped template prompts reference verbatim — `Prospecting`, `Qualification`,
   `Needs Analysis`, `Proposal/Price Quote`, `Negotiation/Review`,
   `Discovery`, plus the closed-stage canonicals `Closed Won` / `Closed Lost`.
3. Knowledge data sources tagged for agent grounding — warns if no Knowledge
   articles tagged `sales-methodology`, `objection-library*`, or
   `agent-grounded` are found, since grounding is the single biggest lever
   for coach quality.
4. Auto-launch utility-item configuration on app definitions referencing the
   Agentforce / Einstein utility — flags `start: true` because that maps to
   "Start automatically" which is the single most common adoption-killer.

Stdlib only — no pip dependencies. Heuristics are deliberately conservative:
each finding cites a path and line and explains why it's worth a look.

Usage:
    python3 check_sales_coach_agent_rollout.py [--root force-app/main/default]

Exit codes:
    0  no findings (or no metadata tree present)
    1  findings present (informational, non-blocking)
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"s": "http://soap.sforce.com/2006/04/metadata"}

# Standard Salesforce Opportunity stage labels referenced by the shipped
# Sales Coach template. Drift from these labels weakens stage-based triggers.
STANDARD_STAGE_LABELS = {
    "Prospecting",
    "Qualification",
    "Needs Analysis",
    "Value Proposition",
    "Id. Decision Makers",
    "Perception Analysis",
    "Proposal/Price Quote",
    "Negotiation/Review",
    "Closed Won",
    "Closed Lost",
    # Some packaged content uses 'Discovery' as a synonym for 'Needs Analysis'.
    "Discovery",
}

SALES_COACH_KEYWORDS = re.compile(
    r"sales[\s_-]*coach|salescoach|sellercoach|seller[\s_-]*coach",
    re.IGNORECASE,
)

GROUNDING_TAG_HINTS = re.compile(
    r"sales[-_]methodology|objection[-_]library|agent[-_]grounded|"
    r"battle[-_]card|value[-_]prop",
    re.IGNORECASE,
)


def detect_agent_definition(root: Path) -> tuple[bool, list[Path]]:
    """Look for an agent definition referencing Sales Coach.

    Salesforce has shipped Agentforce metadata under several directory names
    across releases. We check the common ones and any custom location we find.
    """
    candidate_dirs = [
        root / "genAiPlannerBundles",
        root / "genAiPlanners",
        root / "agents",
        root / "bots",
        root / "agentforce",
    ]
    matches: list[Path] = []
    for d in candidate_dirs:
        if not d.exists():
            continue
        for fp in d.rglob("*.xml"):
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if SALES_COACH_KEYWORDS.search(text):
                matches.append(fp)
    return (len(matches) > 0, matches)


def parse_opportunity_stages(root: Path) -> list[str]:
    """Read the StandardValueSet for OpportunityStage if present."""
    svs_dir = root / "standardValueSets"
    candidates = [svs_dir / "OpportunityStage.standardValueSet"]
    stages: list[str] = []
    for fp in candidates:
        if not fp.exists():
            continue
        try:
            tree = ET.parse(fp)
        except ET.ParseError:
            continue
        for sv in tree.getroot().findall(".//s:standardValue", NS):
            label_el = sv.find("s:label", NS)
            if label_el is not None and label_el.text:
                stages.append(label_el.text.strip())
    return stages


def find_grounding_tags(root: Path) -> list[Path]:
    """Heuristic: scan Knowledge / data-category metadata for grounding hints.

    Knowledge articles in SFDX vary widely by edition. We do a coarse scan
    across the metadata tree for tags or keywords that signal an article was
    authored with agent grounding in mind.
    """
    matches: list[Path] = []
    for ext in ("*.xml", "*.knowledge-meta.xml"):
        for fp in root.rglob(ext):
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if GROUNDING_TAG_HINTS.search(text):
                matches.append(fp)
    return matches


def find_autolaunch_utility_items(root: Path) -> list[tuple[Path, str]]:
    """Detect utility items that auto-start on console open and reference the
    Agentforce / Einstein utility — a common adoption-killer.
    """
    findings: list[tuple[Path, str]] = []
    apps_dir = root / "applications"
    if not apps_dir.exists():
        return findings
    for fp in apps_dir.rglob("*.app-meta.xml"):
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not (
            "einstein" in text.lower()
            or "agentforce" in text.lower()
            or SALES_COACH_KEYWORDS.search(text)
        ):
            continue
        try:
            tree = ET.parse(fp)
        except ET.ParseError:
            continue
        # Walk utility items; the precise schema varies but `<start>true</start>`
        # is the canonical auto-launch flag in app-meta utility entries.
        for ui in tree.getroot().findall(".//s:utilityItems", NS):
            start_el = ui.find("s:start", NS)
            if start_el is not None and start_el.text and start_el.text.strip().lower() == "true":
                label_el = ui.find("s:label", NS)
                label = label_el.text if (label_el is not None and label_el.text) else "(unlabeled)"
                findings.append((fp, label))
    return findings


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--root",
        default="force-app/main/default",
        help="Root directory of the Salesforce metadata (default: force-app/main/default).",
    )
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"metadata root not found: {root}", file=sys.stderr)
        return 0

    findings_count = 0

    # Check 1: agent definition presence
    has_agent, agent_paths = detect_agent_definition(root)
    if not has_agent:
        print("\n## Sales Coach agent definition")
        print(
            "  - WARN: no agent definition referencing 'Sales Coach' "
            "(or close synonyms) found under common Agentforce metadata paths."
        )
        print(
            "    Confirm the Sales Coach template is published and retrieved "
            "into your project. See SKILL.md → Recommended Workflow step 1."
        )
        findings_count += 1
    else:
        print("\n## Sales Coach agent definition")
        for fp in agent_paths:
            print(f"  - OK: agent definition referencing Sales Coach found at {fp.relative_to(root)}")

    # Check 2: opportunity stage drift
    stages = parse_opportunity_stages(root)
    if stages:
        print("\n## Opportunity stage hygiene")
        unknown = [s for s in stages if s not in STANDARD_STAGE_LABELS]
        if unknown:
            print(
                f"  - WARN: {len(unknown)} OpportunityStage label(s) drift from "
                "standard names referenced by the shipped Sales Coach prompts:"
            )
            for s in unknown[:20]:
                print(f"      - {s}")
            print(
                "    Either align labels back to standard, or remap stage "
                "triggers in the agent topic instructions. See gotchas.md → "
                "Gotcha 1."
            )
            findings_count += 1
        else:
            print("  - OK: all OpportunityStage labels match standard names.")
    else:
        print("\n## Opportunity stage hygiene")
        print(
            "  - INFO: OpportunityStage StandardValueSet not retrieved; "
            "skip-or-retrieve to verify stage hygiene."
        )

    # Check 3: grounding-tag presence
    grounded = find_grounding_tags(root)
    print("\n## Knowledge grounding")
    if grounded:
        print(f"  - OK: found {len(grounded)} metadata file(s) with grounding-related tags.")
        for fp in grounded[:5]:
            print(f"      - {fp.relative_to(root)}")
        if len(grounded) > 5:
            print(f"      ... and {len(grounded) - 5} more")
    else:
        print(
            "  - WARN: no Knowledge articles or metadata tagged with "
            "grounding hints (sales-methodology / objection-library / "
            "agent-grounded / battle-card / value-prop) found."
        )
        print(
            "    Without grounded methodology and objection content, Sales "
            "Coach defaults to LLM general knowledge. See SKILL.md → "
            "Concept 3 and Recommended Workflow step 2."
        )
        findings_count += 1

    # Check 4: auto-launch utility items
    autolaunch = find_autolaunch_utility_items(root)
    print("\n## Console utility-item configuration")
    if autolaunch:
        print(
            f"  - WARN: {len(autolaunch)} Agentforce/Einstein utility item(s) "
            "configured to auto-launch on console open:"
        )
        for fp, label in autolaunch:
            print(f"      - {fp.relative_to(root)}: utility {label!r}")
        print(
            "    Auto-launch is widely perceived as surveillance and erodes "
            "rep trust. See gotchas.md → Gotcha 6."
        )
        findings_count += 1
    else:
        print("  - OK: no auto-launch utility items detected.")

    if findings_count == 0:
        print("\nNo Sales Coach rollout drift detected in this metadata tree.")
        return 0

    print(f"\nTotal findings: {findings_count}")
    print("Refer to the skill workflow and gotchas for remediation steps.")
    print(f"ERROR: {findings_count} Sales Coach rollout finding(s); see report above.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
