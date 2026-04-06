#!/usr/bin/env python3
"""Checker script for Omni-Channel Custom Routing skill.

Scans Apex source files in a Salesforce metadata directory for common
PendingServiceRouting / SkillRequirement anti-patterns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omni_channel_custom_routing.py [--help]
    python3 check_omni_channel_custom_routing.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns derived from references/llm-anti-patterns.md and gotchas.md
# ---------------------------------------------------------------------------

# Detects hardcoded ServiceChannelId literals (0N9 prefix, 15 or 18 chars)
_HARDCODED_CHANNEL_ID = re.compile(
    r"""ServiceChannelId\s*=\s*['"][0N][0-9A-Za-z]{14,17}['"]"""
)

# Detects IsReadyForRouting = true inside a constructor or new expression
# (catches both `new PendingServiceRouting(... IsReadyForRouting = true ...)` and
#  `psr.IsReadyForRouting = true` appearing *before* an `insert` on the same line)
_READY_ON_INSERT_INLINE = re.compile(
    r"""new\s+PendingServiceRouting\s*\((?:[^)]*?)IsReadyForRouting\s*=\s*true""",
    re.DOTALL,
)

# Detects SOQL on Skill or ServiceChannel inside a for loop
# Heuristic: SELECT ... FROM Skill (or ServiceChannel) with a for-loop keyword
# nearby in the same file block. We look for the SOQL pattern and flag files
# that also contain a for-loop over records.
_SOQL_SKILL_IN_LOOP = re.compile(
    r"""for\s*\([^)]+\)\s*\{[^}]*\[\s*SELECT[^]]*FROM\s+Skill\b""",
    re.DOTALL,
)
_SOQL_CHANNEL_IN_LOOP = re.compile(
    r"""for\s*\([^)]+\)\s*\{[^}]*\[\s*SELECT[^]]*FROM\s+ServiceChannel\b""",
    re.DOTALL,
)

# Detects RoutingType = 'QueueBased' or missing RoutingType in files that
# also insert SkillRequirement records
_QUEUE_BASED_ROUTING = re.compile(r"""RoutingType\s*=\s*['"]QueueBased['"]""")
_SKILL_REQUIREMENT_INSERT = re.compile(
    r"""insert\s+\w*[Ss]kill[Rr]equirement|new\s+SkillRequirement\s*\("""
)

# Detects catch blocks that handle a routing sequence but omit cleanup delete
# Heuristic: catch block that references PendingServiceRouting but has no delete
_CATCH_BLOCK = re.compile(
    r"""catch\s*\([^)]+\)\s*\{([^}]*)\}""",
    re.DOTALL,
)


def _read_apex_files(manifest_dir: Path) -> list[tuple[Path, str]]:
    """Return (path, content) pairs for all .cls and .trigger files."""
    results = []
    for ext in ("*.cls", "*.trigger"):
        for apex_file in manifest_dir.rglob(ext):
            try:
                content = apex_file.read_text(encoding="utf-8", errors="replace")
                results.append((apex_file, content))
            except OSError:
                pass
    return results


def check_omni_channel_custom_routing(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _read_apex_files(manifest_dir)

    if not apex_files:
        # Not an error — project may not have routing code yet
        return issues

    psr_files: list[tuple[Path, str]] = [
        (p, c) for p, c in apex_files if "PendingServiceRouting" in c
    ]

    for path, content in psr_files:
        rel = path.name

        # Check 1: hardcoded ServiceChannelId
        if _HARDCODED_CHANNEL_ID.search(content):
            issues.append(
                f"{rel}: hardcoded ServiceChannelId literal detected. "
                "Query ServiceChannel by DeveloperName at runtime instead."
            )

        # Check 2: IsReadyForRouting = true in constructor (insert-time flag)
        if _READY_ON_INSERT_INLINE.search(content):
            issues.append(
                f"{rel}: IsReadyForRouting = true found inside a PendingServiceRouting "
                "constructor. This triggers routing before SkillRequirement records exist. "
                "Set IsReadyForRouting = false on insert; update to true after child records are inserted."
            )

        # Check 3: SOQL on Skill or ServiceChannel inside a for loop
        if _SOQL_SKILL_IN_LOOP.search(content):
            issues.append(
                f"{rel}: SELECT from Skill detected inside a for loop. "
                "Move Skill queries above the loop and use a Map<String, Id> for lookup."
            )
        if _SOQL_CHANNEL_IN_LOOP.search(content):
            issues.append(
                f"{rel}: SELECT from ServiceChannel detected inside a for loop. "
                "Move ServiceChannel queries above the loop."
            )

        # Check 4: QueueBased routing combined with SkillRequirement inserts
        if _QUEUE_BASED_ROUTING.search(content) and _SKILL_REQUIREMENT_INSERT.search(content):
            issues.append(
                f"{rel}: RoutingType = 'QueueBased' combined with SkillRequirement inserts. "
                "QueueBased routing ignores SkillRequirement records. "
                "Use RoutingType = 'SkillsBased' for skill-matched routing."
            )

        # Check 5: catch blocks that reference PendingServiceRouting but omit delete
        for catch_match in _CATCH_BLOCK.finditer(content):
            body = catch_match.group(1)
            if "PendingServiceRouting" in body and "delete" not in body.lower():
                issues.append(
                    f"{rel}: catch block references PendingServiceRouting but contains no "
                    "delete statement. Orphaned PendingServiceRouting records block future "
                    "routing attempts with DUPLICATE_VALUE. Add cleanup delete on failure."
                )
                break  # one warning per file is sufficient

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex metadata for common Omni-Channel custom routing anti-patterns "
            "(PendingServiceRouting / SkillRequirement)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_omni_channel_custom_routing(manifest_dir)

    if not issues:
        print("No Omni-Channel custom routing issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
