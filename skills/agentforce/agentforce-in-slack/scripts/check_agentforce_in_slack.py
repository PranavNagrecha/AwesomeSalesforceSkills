#!/usr/bin/env python3
"""
check_agentforce_in_slack.py

Static checker for Agentforce-in-Slack configuration artifacts.

Usage:
    python3 check_agentforce_in_slack.py [path/to/agent/metadata/dir]

Checks performed:
  1. General Slack Actions topic present in agent XML metadata.
  2. User-specific SOQL patterns in public-scoped actions (flag as Private scope
     candidates).
  3. Canvas API calls (Create Canvas action references) without Slack plan
     validation guard in topic instructions.

All checks use stdlib only — no pip dependencies.

Exit codes:
  0 — no issues found
  1 — one or more issues found (details printed to stdout)
  2 — usage or file-access error
"""

import sys
import os
import re
import argparse
from pathlib import Path


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# Patterns indicating user-specific SOQL in action Apex or metadata
USER_SPECIFIC_SOQL_PATTERNS = [
    re.compile(r"WHERE\s+OwnerId\s*=\s*['\"]", re.IGNORECASE),
    re.compile(r"UserInfo\.getUserId\s*\(\s*\)", re.IGNORECASE),
    re.compile(r"my\s+open\s+cases", re.IGNORECASE),
    re.compile(r"my\s+open\s+opportunities", re.IGNORECASE),
    re.compile(r"my\s+pipeline", re.IGNORECASE),
    re.compile(r"my\s+tasks", re.IGNORECASE),
    re.compile(r"CurrentUser", re.IGNORECASE),
]

# Pattern for public scope designation in agent action metadata XML
PUBLIC_SCOPE_PATTERN = re.compile(
    r"<scope>\s*Public\s*</scope>", re.IGNORECASE
)

# Pattern for General Slack Actions topic reference in agent/topic XML
GENERAL_SLACK_ACTIONS_PATTERN = re.compile(
    r"General\s+Slack\s+Actions", re.IGNORECASE
)

# Pattern for canvas API calls or canvas action references
CANVAS_ACTION_PATTERNS = [
    re.compile(r"Create\s*Canvas", re.IGNORECASE),
    re.compile(r"canvas\.create", re.IGNORECASE),
    re.compile(r"CANVAS_CREATE", re.IGNORECASE),
    re.compile(r"createCanvas", re.IGNORECASE),
]

# Pattern for canvas plan validation guard in topic instructions or metadata
CANVAS_PLAN_GUARD_PATTERNS = [
    re.compile(r"paid\s+plan", re.IGNORECASE),
    re.compile(r"canvas.*plan", re.IGNORECASE),
    re.compile(r"plan.*canvas", re.IGNORECASE),
    re.compile(r"Free\s+plan", re.IGNORECASE),
    re.compile(r"CANVAS_CREATE_PLAN_RESTRICTION", re.IGNORECASE),
    re.compile(r"Slack\s+Pro", re.IGNORECASE),
    re.compile(r"Business\+", re.IGNORECASE),
    re.compile(r"Enterprise\s+Grid", re.IGNORECASE),
]

# File extensions to inspect
INSPECTABLE_EXTENSIONS = {".xml", ".cls", ".json", ".md", ".yaml", ".yml"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def collect_files(root: Path) -> list[Path]:
    """Return all inspectable files under root, recursively."""
    files = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in INSPECTABLE_EXTENSIONS:
            files.append(path)
    return sorted(files)


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"  [WARN] Could not read {path}: {exc}")
        return ""


def match_any(text: str, patterns: list[re.Pattern]) -> bool:
    return any(p.search(text) for p in patterns)


# ---------------------------------------------------------------------------
# Check 1: General Slack Actions topic present
# ---------------------------------------------------------------------------

def check_general_slack_actions_topic(files: list[Path]) -> list[str]:
    """
    Look for any file that references General Slack Actions.
    If none found, warn that the topic may be missing from the agent configuration.
    """
    issues = []
    found = False
    for path in files:
        text = read_file(path)
        if GENERAL_SLACK_ACTIONS_PATTERN.search(text):
            found = True
            break

    if not found:
        issues.append(
            "[CHECK-1] 'General Slack Actions' topic not found in any inspected file. "
            "This topic must be explicitly added in Agent Builder after Slack deployment "
            "to unlock Slack-native actions (Create Canvas, Send DM, Search Message "
            "History, Look Up User). If this repo does not contain agent XML metadata, "
            "verify the topic is present directly in Setup > Agentforce Agents > Topics."
        )

    return issues


# ---------------------------------------------------------------------------
# Check 2: User-specific SOQL in public-scoped actions
# ---------------------------------------------------------------------------

def check_user_specific_soql_in_public_actions(files: list[Path]) -> list[str]:
    """
    Flag files that appear to be public-scoped actions and also contain
    user-specific SOQL patterns. These should be Private scope.
    """
    issues = []
    for path in files:
        text = read_file(path)
        if not PUBLIC_SCOPE_PATTERN.search(text):
            continue
        matched_patterns = [p.pattern for p in USER_SPECIFIC_SOQL_PATTERNS if p.search(text)]
        if matched_patterns:
            issues.append(
                f"[CHECK-2] {path}: action appears to be Public scope but contains "
                f"user-specific SOQL pattern(s): {matched_patterns}. "
                "Public actions execute under the integration user's identity — "
                "user-specific queries will return the integration user's data to all "
                "invoking users, not each user's own data. Set the action scope to "
                "Private and configure Salesforce-to-Slack identity mappings."
            )

    return issues


# ---------------------------------------------------------------------------
# Check 3: Canvas API calls without plan validation guard
# ---------------------------------------------------------------------------

def check_canvas_calls_without_plan_guard(files: list[Path]) -> list[str]:
    """
    Flag files that reference canvas creation actions but do not include
    any reference to a plan validation guard or plan-restriction handling.
    """
    issues = []
    for path in files:
        text = read_file(path)
        if not match_any(text, CANVAS_ACTION_PATTERNS):
            continue
        if not match_any(text, CANVAS_PLAN_GUARD_PATTERNS):
            issues.append(
                f"[CHECK-3] {path}: file references canvas creation "
                "(Create Canvas / canvas.create) but contains no reference to a Slack "
                "plan check or plan restriction handling. Canvas creation is unavailable "
                "on the Slack Free plan. Add a plan validation step (confirm workspace is "
                "on Pro, Business+, or Enterprise Grid) and fallback behavior (plain text "
                "response) to any topic instructions or agent configuration that uses canvas."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Static checker for Agentforce-in-Slack configuration artifacts.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to agent metadata directory or file (default: current directory)",
    )
    args = parser.parse_args()
    root = Path(args.path)

    if not root.exists():
        print(f"Error: path does not exist: {root}", file=sys.stderr)
        return 2

    if not root.is_dir():
        # Support single file mode
        files = [root]
        root_label = str(root.parent)
    else:
        files = collect_files(root)
        root_label = str(root)

    if not files:
        print(f"No inspectable files found under: {root_label}")
        return 0

    print(f"check_agentforce_in_slack.py — inspecting {len(files)} file(s) under: {root_label}")
    print()

    all_issues: list[str] = []

    all_issues.extend(check_general_slack_actions_topic(files))
    all_issues.extend(check_user_specific_soql_in_public_actions(files))
    all_issues.extend(check_canvas_calls_without_plan_guard(files))

    if all_issues:
        print(f"Found {len(all_issues)} issue(s):\n")
        for issue in all_issues:
            print(f"  {issue}")
            print()
        return 1
    else:
        print("All checks passed. No Agentforce-in-Slack configuration issues detected.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
