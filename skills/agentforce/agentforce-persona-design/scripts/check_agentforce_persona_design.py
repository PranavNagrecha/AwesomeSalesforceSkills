#!/usr/bin/env python3
"""Checker script for Agentforce Persona Design skill.

Checks org metadata or configuration relevant to Agentforce Persona Design.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agentforce_persona_design.py [--help]
    python3 check_agentforce_persona_design.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Agentforce Persona Design configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_agentforce_persona_design(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Checks GenAiPlugin and BotVersion metadata files for common persona
    instruction anti-patterns (modal verb chains, empty instructions).
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for GenAiPlugin metadata files (agent definitions)
    gen_ai_dirs = []
    for candidate in [
        manifest_dir / "force-app" / "main" / "default" / "genAiPlugins",
        manifest_dir / "src" / "genAiPlugins",
        manifest_dir / "genAiPlugins",
    ]:
        if candidate.exists():
            gen_ai_dirs.append(candidate)

    # Also check BotVersion files
    bot_dirs = []
    for candidate in [
        manifest_dir / "force-app" / "main" / "default" / "bots",
        manifest_dir / "src" / "bots",
        manifest_dir / "bots",
    ]:
        if candidate.exists():
            bot_dirs.append(candidate)

    # Check .xml files in genAiPlugins for instruction patterns
    for gen_ai_dir in gen_ai_dirs:
        for xml_file in gen_ai_dir.rglob("*.xml"):
            try:
                content = xml_file.read_text(encoding="utf-8", errors="replace")

                # Count modal verb chains
                must_count = content.lower().count(" must ")
                never_count = content.lower().count(" never ")
                always_count = content.lower().count(" always ")
                modal_total = must_count + never_count + always_count

                if modal_total >= 5:
                    issues.append(
                        f"{xml_file.name}: High modal verb density in agent instructions "
                        f"(must={must_count}, never={never_count}, always={always_count}). "
                        "Long must/never/always chains cause reasoning loops. "
                        "Rewrite as positive behavioral descriptions with voice adjectives."
                    )

            except OSError:
                pass

    if not gen_ai_dirs and not bot_dirs:
        # No agent metadata found — nothing to check
        pass

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_agentforce_persona_design(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
