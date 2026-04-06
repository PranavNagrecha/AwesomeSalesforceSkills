#!/usr/bin/env python3
"""Validate skills, manifests, and generated retrieval artifacts."""

from __future__ import annotations

import argparse
import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines.registry_builder import discover_skill_dirs
from pipelines.sync_engine import build_state, diff_state
from pipelines.validators import ValidationIssue, validate_frontmatter, validate_knowledge_source, validate_skill_registry_record, validate_skill_structure
from pipelines.knowledge_builder import load_sources_manifest


def print_issue(issue: ValidationIssue) -> None:
    print(f"{issue.level} {issue.path}: {issue.message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the repository skill framework and generated artifacts.")
    args = parser.parse_args()

    issues: list[ValidationIssue] = []
    seen_ids: dict[str, str] = {}
    seen_names: dict[str, str] = {}

    for skill_dir in discover_skill_dirs(ROOT):
        skill_path = skill_dir / "SKILL.md"
        issues.extend(validate_skill_structure(skill_dir))
        issues.extend(validate_frontmatter(ROOT, skill_path))

        try:
            parsed = __import__("pipelines.frontmatter", fromlist=["parse_markdown_with_frontmatter"]).parse_markdown_with_frontmatter(skill_path)
            metadata = parsed.metadata
            skill_id = f"{metadata['category']}/{metadata['name']}"
            if skill_id in seen_ids:
                issues.append(ValidationIssue("ERROR", str(skill_path), f"duplicate skill id `{skill_id}` also seen in {seen_ids[skill_id]}"))
            else:
                seen_ids[skill_id] = str(skill_path)
            if metadata["name"] in seen_names:
                issues.append(ValidationIssue("ERROR", str(skill_path), f"duplicate skill name `{metadata['name']}` also seen in {seen_names[metadata['name']]}"))
            else:
                seen_names[metadata["name"]] = str(skill_path)
        except Exception as exc:
            issues.append(ValidationIssue("ERROR", str(skill_path), f"unable to parse frontmatter: {exc}"))

    for source in load_sources_manifest(ROOT):
        issues.extend(validate_knowledge_source(ROOT, source))

    state = build_state(ROOT)
    for record in state.registry_records:
        issues.extend(validate_skill_registry_record(ROOT, record))

    for script_path in sorted(ROOT.glob("skills/*/*/scripts/*.py")):
        try:
            py_compile.compile(str(script_path), doraise=True)
        except py_compile.PyCompileError as exc:
            issues.append(ValidationIssue("ERROR", str(script_path), f"py_compile failed: {exc.msg}"))
            continue
        help_run = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if help_run.returncode != 0:
            issues.append(ValidationIssue("ERROR", str(script_path), "--help exited non-zero"))

    fixtures_path = ROOT / "vector_index" / "query-fixtures.json"
    if fixtures_path.exists():
        fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
        covered_skills = {fixture["expected_skill"] for fixture in fixtures.get("queries", [])}
        for skill_id in seen_ids:
            if skill_id not in covered_skills:
                issues.append(ValidationIssue("ERROR", "vector_index/query-fixtures.json", f"skill `{skill_id}` has no query fixture — add at least one entry to vector_index/query-fixtures.json"))
        for fixture in fixtures.get("queries", []):
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "search_knowledge.py"),
                    fixture["query"],
                    "--json",
                ]
                + (["--domain", fixture["domain"]] if fixture.get("domain") else []),
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                issues.append(ValidationIssue("ERROR", "search_knowledge.py", f"fixture query failed: {fixture['query']}"))
                continue
            payload = json.loads(result.stdout)
            top_skill_ids = [item["id"] for item in payload.get("skills", [])[: fixture.get("top_k", 3)]]
            if fixture["expected_skill"] not in top_skill_ids:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "vector_index/query-fixtures.json",
                        f"query `{fixture['query']}` did not return `{fixture['expected_skill']}` in top {fixture.get('top_k', 3)} results",
                    )
                )

    drift = diff_state(ROOT, state)
    for path in drift:
        issues.append(ValidationIssue("ERROR", path, "generated artifact is stale; run `python3 scripts/skill_sync.py --all`"))

    for issue in issues:
        print_issue(issue)

    error_count = sum(1 for issue in issues if issue.level == "ERROR")
    warn_count = sum(1 for issue in issues if issue.level == "WARN")
    print(f"Validated {len(seen_ids)} skill(s); {error_count} error(s), {warn_count} warning(s).")
    return 1 if error_count else 0


if __name__ == "__main__":
    sys.exit(main())
