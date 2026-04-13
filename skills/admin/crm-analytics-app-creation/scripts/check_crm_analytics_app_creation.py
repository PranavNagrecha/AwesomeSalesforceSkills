#!/usr/bin/env python3
"""Checker script for CRM Analytics App Creation skill.

Checks CRM Analytics app metadata in a Salesforce project directory for common
configuration problems: missing security predicates, dashboards without steps,
sharing not configured, and dataflow direct connected-object output.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_crm_analytics_app_creation.py [--help]
    python3 check_crm_analytics_app_creation.py --manifest-dir path/to/metadata
    python3 check_crm_analytics_app_creation.py --skill-dir path/to/skill/package
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CRM Analytics App Creation configuration for common issues. "
            "Pass --manifest-dir to check Salesforce metadata, or --skill-dir to check "
            "skill package completeness."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata to inspect.",
    )
    parser.add_argument(
        "--skill-dir",
        default=None,
        help="Root directory of the skill package to check for completeness.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Salesforce metadata checks
# ---------------------------------------------------------------------------

def _locate_analytics_dir(manifest_dir: Path) -> Path | None:
    """Return the CRM Analytics metadata directory (wave/ or analytics/) if it exists."""
    for candidate in ("wave", "analytics"):
        d = manifest_dir / candidate
        if d.exists():
            return d
    return None


def check_dashboards(wave_dir: Path) -> list[str]:
    """Check dashboard JSON files for missing step definitions."""
    issues: list[str] = []
    for dashboard_file in wave_dir.rglob("*.dashboard"):
        try:
            raw = dashboard_file.read_text(encoding="utf-8").strip()
            if not raw.startswith("{"):
                continue
            data = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            continue

        steps = data.get("steps", {})
        widgets = data.get("widgets", {})
        if widgets and not steps:
            issues.append(
                f"Dashboard '{dashboard_file.name}': has {len(widgets)} widget(s) but no steps. "
                "Widgets must reference steps that query datasets — dashboards with widgets "
                "but no steps will render blank."
            )

        # Check for faceting enabled across steps that may reference different datasets
        state = data.get("state", {})
        faceting = state.get("facetId", {})
        if faceting and len(steps) > 1:
            datasets_referenced: set[str] = set()
            for step_name, step_def in steps.items():
                if isinstance(step_def, dict):
                    ds = step_def.get("datasets", [])
                    if isinstance(ds, list):
                        for d_entry in ds:
                            if isinstance(d_entry, dict):
                                datasets_referenced.add(d_entry.get("name", ""))
            if len(datasets_referenced) > 1:
                issues.append(
                    f"Dashboard '{dashboard_file.name}': faceting is enabled but steps reference "
                    f"{len(datasets_referenced)} different datasets {sorted(datasets_referenced)}. "
                    "Faceting only propagates filters within a single dataset. Use bindings for "
                    "cross-dataset filtering."
                )

    return issues


def check_datasets(wave_dir: Path) -> list[str]:
    """Check dataset metadata for missing security predicates or sharing inheritance."""
    issues: list[str] = []
    for dataset_file in wave_dir.rglob("*.dataset"):
        try:
            content = dataset_file.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"Could not read dataset file: {dataset_file}")
            continue

        has_predicate = "securityPredicate" in content
        has_sharing = "sharingSource" in content or "sharingInheritance" in content

        if not has_predicate and not has_sharing:
            issues.append(
                f"Dataset '{dataset_file.stem}': no securityPredicate or sharingSource found. "
                "All app Viewers will see every row in this dataset regardless of Salesforce "
                "object-level sharing. Add a SAQL securityPredicate or enable sharingSource "
                "if row-level restriction is required."
            )

    return issues


def check_app_sharing(wave_dir: Path) -> list[str]:
    """Check WaveApplication metadata for empty sharing configuration."""
    issues: list[str] = []
    # WaveApplication files use .wapp extension in source format
    for app_file in wave_dir.rglob("*.wapp"):
        try:
            content = app_file.read_text(encoding="utf-8").strip()
            if content.startswith("{"):
                data = json.loads(content)
                shares = data.get("shares", [])
                if not shares:
                    issues.append(
                        f"App '{app_file.stem}': sharing configuration is empty (no Viewer, "
                        "Editor, or Manager entries). Users with CRM Analytics permission sets "
                        "will not be able to see data unless they are added as Viewers."
                    )
            else:
                # XML-style metadata
                if "<shares>" not in content and "shares" not in content:
                    issues.append(
                        f"App '{app_file.stem}': no 'shares' element found. Verify app sharing "
                        "is configured in Analytics Studio > App > Share."
                    )
        except (json.JSONDecodeError, OSError):
            issues.append(f"Could not parse app file: {app_file}")

    return issues


def check_dataflows(wave_dir: Path) -> list[str]:
    """Check dataflow JSON for direct sfdcDigest-to-edgemart paths without transformations."""
    issues: list[str] = []
    for wdf_file in wave_dir.rglob("*.wdf"):
        try:
            content = wdf_file.read_text(encoding="utf-8")
            nodes = json.loads(content)
        except (json.JSONDecodeError, OSError):
            continue

        if not isinstance(nodes, dict):
            continue

        sfdcDigest_names: set[str] = set()
        for node_name, node_def in nodes.items():
            if isinstance(node_def, dict) and node_def.get("action") == "sfdcDigest":
                sfdcDigest_names.add(node_name)

        for node_name, node_def in nodes.items():
            if not isinstance(node_def, dict):
                continue
            if node_def.get("action") == "edgemart":
                source = node_def.get("parameters", {}).get("source", "")
                if source in sfdcDigest_names:
                    issues.append(
                        f"Dataflow '{wdf_file.stem}', output node '{node_name}': directly "
                        f"outputs connected object '{source}' with no transformation. This is "
                        "valid for simple syncs, but confirm that a security predicate is "
                        "applied to the resulting dataset if row-level security is required."
                    )

    return issues


def check_analytics_apps(manifest_dir: Path) -> list[str]:
    """Check all CRM Analytics metadata in the manifest directory."""
    issues: list[str] = []

    wave_dir = _locate_analytics_dir(manifest_dir)
    if wave_dir is None:
        # No CRM Analytics metadata found — nothing to report
        return issues

    issues.extend(check_dashboards(wave_dir))
    issues.extend(check_datasets(wave_dir))
    issues.extend(check_app_sharing(wave_dir))
    issues.extend(check_dataflows(wave_dir))

    return issues


# ---------------------------------------------------------------------------
# Skill package completeness checks
# ---------------------------------------------------------------------------

REQUIRED_SKILL_FILES = [
    "SKILL.md",
    "references/examples.md",
    "references/gotchas.md",
    "references/well-architected.md",
    "references/llm-anti-patterns.md",
]

REQUIRED_FRONTMATTER_FIELDS = [
    "name:", "description:", "category:", "salesforce-version:",
    "well-architected-pillars:", "triggers:", "tags:", "inputs:", "outputs:",
    "version:", "author:", "updated:",
]

REQUIRED_TAGS = ["crm-analytics", "analytics-studio", "datasets", "lenses", "dashboards"]

REQUIRED_SECTIONS = ["## Recommended Workflow", "## Review Checklist", "## Core Concepts"]

REQUIRED_OFFICIAL_SOURCES = [
    "https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm",
    "https://trailhead.salesforce.com/content/learn/projects/quickstart-analytics-studio",
    "https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html",
]


def check_skill_package(skill_dir: Path) -> list[str]:
    """Check a skill package directory for structural completeness."""
    issues: list[str] = []

    if not skill_dir.exists():
        issues.append(f"Skill directory not found: {skill_dir}")
        return issues

    for rel in REQUIRED_SKILL_FILES:
        if not (skill_dir / rel).exists():
            issues.append(f"Missing required skill file: {rel}")

    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8")

        for field in REQUIRED_FRONTMATTER_FIELDS:
            if field not in content:
                issues.append(f"SKILL.md missing frontmatter field: {field}")

        fm_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if fm_match:
            fm = fm_match.group(1)
            for tag in REQUIRED_TAGS:
                if tag not in fm:
                    issues.append(f"SKILL.md missing required tag in frontmatter: {tag}")
            if "- Security" not in fm:
                issues.append("SKILL.md missing well-architected-pillar: Security")
            if "- Performance" not in fm:
                issues.append("SKILL.md missing well-architected-pillar: Performance")
        else:
            issues.append("SKILL.md: cannot parse YAML frontmatter block.")

        for section in REQUIRED_SECTIONS:
            if section not in content:
                issues.append(f"SKILL.md missing section: '{section}'")

        workflow = re.search(r"## Recommended Workflow.*?(?=\n## |\Z)", content, re.DOTALL)
        if workflow:
            steps = re.findall(r"^\d+\.\s", workflow.group(), re.MULTILINE)
            if len(steps) < 3:
                issues.append(f"SKILL.md Recommended Workflow has {len(steps)} steps; need 3–7.")
            elif len(steps) > 7:
                issues.append(f"SKILL.md Recommended Workflow has {len(steps)} steps; maximum 7.")

        if "NOT for" not in content:
            issues.append("SKILL.md description missing 'NOT for' exclusion clause.")

        todo_count = len(re.findall(r"\bTODO\b", content))
        if todo_count > 0:
            issues.append(f"SKILL.md still has {todo_count} TODO marker(s).")

        body = re.sub(r"^---\n.*?\n---\n", "", content, count=1, flags=re.DOTALL)
        if len(body.split()) < 300:
            issues.append(f"SKILL.md body word count is under 300.")

    wa_md = skill_dir / "references" / "well-architected.md"
    if wa_md.exists():
        wa = wa_md.read_text(encoding="utf-8")
        if "## Official Sources Used" not in wa:
            issues.append("well-architected.md missing '## Official Sources Used' section.")
        for url in REQUIRED_OFFICIAL_SOURCES:
            if url not in wa:
                issues.append(f"well-architected.md missing required URL: {url}")

    ap_md = skill_dir / "references" / "llm-anti-patterns.md"
    if ap_md.exists():
        ap = ap_md.read_text(encoding="utf-8")
        count = len(re.findall(r"^## Anti-Pattern \d+", ap, re.MULTILINE))
        if count < 5:
            issues.append(f"llm-anti-patterns.md has {count} anti-pattern(s); minimum is 5.")
        todo_count = len(re.findall(r"\bTODO\b", ap))
        if todo_count > 0:
            issues.append(f"llm-anti-patterns.md still has {todo_count} TODO marker(s).")

    gt_md = skill_dir / "references" / "gotchas.md"
    if gt_md.exists():
        gt = gt_md.read_text(encoding="utf-8")
        count = len(re.findall(r"^## Gotcha \d+", gt, re.MULTILINE))
        if count < 3:
            issues.append(f"gotchas.md has {count} gotcha(s); minimum is 3.")
        if "permission set" not in gt.lower():
            issues.append("gotchas.md does not cover the permission set / data access gotcha.")

    ex_md = skill_dir / "references" / "examples.md"
    if ex_md.exists():
        ex = ex_md.read_text(encoding="utf-8")
        count = len(re.findall(r"^## Example \d+", ex, re.MULTILINE))
        if count < 2:
            issues.append(f"examples.md has {count} example(s); minimum is 2.")
        todo_count = len(re.findall(r"\bTODO\b", ex))
        if todo_count > 0:
            issues.append(f"examples.md still has {todo_count} TODO marker(s).")

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def check_crm_analytics_app_creation(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_analytics_apps(manifest_dir))
    return issues


def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    if args.skill_dir:
        skill_dir = Path(args.skill_dir)
        print(f"Checking skill package: {skill_dir}")
        all_issues.extend(check_skill_package(skill_dir))

    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        print(f"Checking Salesforce metadata: {manifest_dir}")
        all_issues.extend(check_crm_analytics_app_creation(manifest_dir))

    if not args.skill_dir and not args.manifest_dir:
        # Default: check current directory as Salesforce metadata
        print("Checking current directory as Salesforce metadata.")
        all_issues.extend(check_crm_analytics_app_creation(Path(".")))

    if not all_issues:
        print("No CRM Analytics app configuration issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
