#!/usr/bin/env python3
"""Static checks for Flow Orchestration design patterns.

Scans Flow Orchestration metadata for the high-confidence anti-patterns
documented in this skill:

  1. Orchestration with a single stage containing a single step —
     overkill (use Approval Process or screen flow on record page).
  2. Interactive step with a hardcoded specific-user assignee for a
     stage that may run multi-day — brittleness on user deactivation.
     Heuristic: any `actorType=User` step in an orchestration triggers
     a soft warning recommending queue assignment.
  3. Stage with multiple steps where the steps' connectors form a
     sequence (step A → step B → step C inside the stage). Steps
     within a stage run in parallel; in-stage sequencing is a smell
     that the design wanted multiple stages.

Stdlib only.

Usage:
    python3 check_flow_orchestration_patterns.py --src-root .
    python3 check_flow_orchestration_patterns.py --help
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = "http://soap.sforce.com/2006/04/metadata"
_NS_TAG = f"{{{_NS}}}"


def _strip_ns(tag: str) -> str:
    return tag[len(_NS_TAG):] if tag.startswith(_NS_TAG) else tag


def _is_orchestration(root: ET.Element) -> bool:
    if _strip_ns(root.tag) != "Flow":
        return False
    pt = root.find(f"{_NS_TAG}processType")
    if pt is None or not pt.text:
        return False
    return "Orchestrat" in pt.text  # FlowOrchestration / Orchestration


def _scan_flow(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError):
        return findings
    root = tree.getroot()
    if not _is_orchestration(root):
        return findings

    stages = root.findall(f"{_NS_TAG}stages")
    if not stages:
        return findings

    # Smell 1: single-stage single-step orchestration.
    if len(stages) == 1:
        steps_in_only_stage = stages[0].findall(f"{_NS_TAG}stageSteps")
        if len(steps_in_only_stage) == 1:
            findings.append(
                f"{path}: orchestration has only ONE stage with ONE step — "
                "use Approval Process or a screen flow on the record page; "
                "orchestration overhead has no multi-stage benefit here "
                "(references/llm-anti-patterns.md § 1)"
            )

    # Smell 2: hardcoded user assignee on interactive steps.
    for stage in stages:
        for step in stage.findall(f"{_NS_TAG}stageSteps"):
            actor_type = step.find(f"{_NS_TAG}actionInputParameters/{_NS_TAG}name")  # rough probe
            # The actual assignee shape varies by API version; we look for the
            # presence of a literal User Id (`005...` 15 or 18 chars) inside the step.
            step_text = ET.tostring(step, encoding="unicode")
            import re as _re
            for m in _re.finditer(r"\b005[a-zA-Z0-9]{12}([a-zA-Z0-9]{3})?\b", step_text):
                step_name_el = step.find(f"{_NS_TAG}name")
                step_name = step_name_el.text if step_name_el is not None else "<unnamed>"
                findings.append(
                    f"{path}: orchestration step `{step_name}` references a hardcoded "
                    f"User Id `{m.group(0)}` — brittleness on user deactivation. "
                    "Prefer queue-based assignment for long-running steps "
                    "(references/llm-anti-patterns.md § 3)"
                )
                break  # one warning per step is enough

    # Smell 3: sequential connectors between steps within a single stage.
    for stage in stages:
        steps = stage.findall(f"{_NS_TAG}stageSteps")
        step_names = set()
        for step in steps:
            name_el = step.find(f"{_NS_TAG}name")
            if name_el is not None and name_el.text:
                step_names.add(name_el.text)
        # If any step has a connector targeting another step in the SAME stage,
        # that's an in-stage sequence smell.
        for step in steps:
            conn = step.find(f"{_NS_TAG}connector")
            if conn is None:
                continue
            target_ref = conn.find(f"{_NS_TAG}targetReference")
            if target_ref is None or not target_ref.text:
                continue
            if target_ref.text in step_names:
                step_name_el = step.find(f"{_NS_TAG}name")
                step_name = step_name_el.text if step_name_el is not None else "<unnamed>"
                findings.append(
                    f"{path}: orchestration step `{step_name}` has a connector to "
                    f"another step `{target_ref.text}` in the SAME stage — steps "
                    "within a stage run in parallel by default; in-stage sequencing "
                    "is a smell that the design wanted separate stages "
                    "(references/llm-anti-patterns.md § 2)"
                )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for f in root.rglob("*.flow-meta.xml"):
        findings.extend(_scan_flow(f))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Flow Orchestration metadata for design anti-patterns "
            "(single-stage single-step overkill, hardcoded user assignees, "
            "in-stage sequential connectors)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the metadata tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Flow Orchestration anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
