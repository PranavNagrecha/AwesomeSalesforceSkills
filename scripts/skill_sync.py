#!/usr/bin/env python3
"""Synchronize registry, retrieval artifacts, and generated docs.

Validation runs before any artifact is written. If errors are found the
sync is aborted so broken skills can never land in the generated registry.
Use --skip-validation only in extraordinary circumstances.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines.registry_builder import discover_skill_dirs
from pipelines.sync_engine import build_state, write_state
from pipelines.validators import ValidationIssue, validate_frontmatter, validate_skill_structure


def _validate_dirs(root: Path, skill_dirs: list[Path]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for skill_dir in skill_dirs:
        issues.extend(validate_skill_structure(skill_dir))
        skill_path = skill_dir / "SKILL.md"
        if skill_path.exists():
            issues.extend(validate_frontmatter(root, skill_path))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync the repository registry, docs, and retrieval artifacts."
    )
    parser.add_argument("--all", action="store_true", help="Sync the entire repository.")
    parser.add_argument(
        "--skill",
        help="Skill directory to sync. Validation runs on this skill before writing.",
    )
    parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Sync changed scope when git context is available; otherwise sync all.",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip pre-sync validation. Not recommended — broken skills will enter the registry.",
    )
    args = parser.parse_args()

    if args.skill:
        candidate = Path(args.skill)
        if not candidate.exists():
            raise SystemExit(f"Skill path not found: {args.skill}")

    if not args.skip_validation:
        all_dirs = discover_skill_dirs(ROOT)

        if args.skill:
            target = Path(args.skill).resolve()
            dirs_to_validate = [d for d in all_dirs if d.resolve() == target]
            if not dirs_to_validate:
                raise SystemExit(
                    f"Path exists but is not a recognised skill directory: {args.skill}\n"
                    "Skill directories must live under skills/<domain>/<skill-name>/."
                )
        else:
            dirs_to_validate = all_dirs

        issues = _validate_dirs(ROOT, dirs_to_validate)
        errors = [i for i in issues if i.level == "ERROR"]
        warnings = [i for i in issues if i.level == "WARN"]

        for issue in issues:
            print(f"{issue.level}  {issue.path}: {issue.message}")

        if errors:
            print(
                f"\n✖  Sync aborted — {len(errors)} error(s) must be fixed before artifacts are written.\n"
                "   Fix the errors above, then re-run:  python3 scripts/skill_sync.py --skill <path>"
            )
            return 1

        if warnings:
            print(f"\n⚠  {len(warnings)} warning(s). Sync will proceed — address warnings before committing.")

    state = build_state(ROOT)
    changed = write_state(ROOT, state)

    if changed:
        print("\nUpdated:")
        for path in changed:
            print(f"  {path}")
    else:
        print("No generated changes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
