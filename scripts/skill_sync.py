#!/usr/bin/env python3
"""Synchronize registry, retrieval artifacts, and generated docs.

Validation runs before any artifact is written. If errors are found the
sync is aborted so broken skills can never land in the generated registry.
Use --skip-validation only in extraordinary circumstances.
"""

from __future__ import annotations

import argparse
import subprocess
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


def _changed_skill_dirs(root: Path, all_dirs: list[Path]) -> list[Path] | None:
    """Return the subset of skill dirs that have any STAGED changes about
    to be committed. Returns None if git is unavailable — caller should
    fall back to validating ``all_dirs``.

    Used by ``--changed-only``: a commit that touches one skill (or none)
    shouldn't be blocked by a pre-existing ERROR in an unrelated skill
    that was never properly cleaned up — including untracked WIP scaffolds
    in skills/ that nobody chose to commit. The full-repo gate stays
    available via ``python3 scripts/validate_repo.py`` (no ``--changed-only``
    flag) and the explicit ``python3 scripts/skill_sync.py --all`` path.

    Staged-only is the right scope here because pre-commit fires on the
    set of files about to be committed; untracked WIP that the user did
    NOT stage is explicitly out of scope.
    """
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    if out.returncode != 0:
        return None
    changed_paths: set[Path] = set()
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        changed_paths.add((root / line).resolve())
    if not changed_paths:
        return []
    skills_root = (root / "skills").resolve()
    out_dirs: list[Path] = []
    for skill_dir in all_dirs:
        skill_dir_resolved = skill_dir.resolve()
        try:
            skill_dir_resolved.relative_to(skills_root)
        except ValueError:
            continue
        # A skill dir is "changed" if any staged path lives under it.
        for path in changed_paths:
            try:
                path.relative_to(skill_dir_resolved)
            except ValueError:
                continue
            out_dirs.append(skill_dir)
            break
    return out_dirs


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
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help=(
            "Skip embeddings rebuild even if config has embeddings.enabled=true. "
            "Used by .githooks/pre-commit to keep commits fast — the explicit "
            "python3 scripts/build_index.py path runs without this flag."
        ),
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
        elif args.changed_only:
            # Scope validation to skills that this commit actually touches.
            # Pre-existing ERRORs in unrelated skills should not block an
            # unrelated commit (e.g. infra-only changes). Full-repo gate is
            # still enforced by `validate_repo.py` (no --changed-only) and
            # by `skill_sync.py --all`.
            changed = _changed_skill_dirs(ROOT, all_dirs)
            if changed is None:
                # Git unavailable — fall back to full validation.
                dirs_to_validate = all_dirs
            else:
                dirs_to_validate = changed
                if not dirs_to_validate:
                    print(
                        "[skill_sync] --changed-only: no skill files changed "
                        "in this commit; skipping per-skill validation.",
                        file=sys.stderr,
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

    state = build_state(ROOT, skip_embeddings=args.skip_embeddings)
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
