#!/usr/bin/env python3
"""Checker script for GitHub Actions for Salesforce skill.

Validates GitHub Actions workflow YAML files in a repository for required
SFDX/sf CLI authentication steps, secrets hygiene, and deployment best practices.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_github_actions_for_salesforce.py [--help]
    python3 check_github_actions_for_salesforce.py --workflow-dir .github/workflows
    python3 check_github_actions_for_salesforce.py --workflow-file .github/workflows/deploy.yml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns the checker looks for (simple string matching — no YAML parser needed)
# ---------------------------------------------------------------------------

# Auth patterns
AUTH_COMMAND_PATTERNS = [
    "sf org login jwt",          # sf CLI v2 JWT auth (correct)
    "sfdx auth:jwt:grant",       # legacy — still works but deprecated
]
LEGACY_AUTH_PATTERN = "sfdx auth:jwt:grant"
CURRENT_AUTH_PATTERN = "sf org login jwt"

# Required JWT auth flags
JWT_FLAGS = {
    "--client-id": "JWT auth must specify --client-id (Consumer Key from Connected App)",
    "--jwt-key-file": "JWT auth must specify --jwt-key-file pointing to the server key file",
    "--username": "JWT auth must specify --username for the pre-authorized CI user",
}

# Secrets usage — credentials must come from ${{ secrets.* }}
HARDCODED_CREDENTIAL_ANTIPATTERNS = [
    "client_id:",        # Possible hardcoded client ID in YAML value
    "username: ci-",     # Common hardcoded username prefix
]

# Key file write pattern
KEY_WRITE_PATTERN = "/tmp/server.key"
KEY_CLEANUP_PATTERN = "rm -f"

# Cleanup step patterns
CLEANUP_PATTERNS = ["if: always()", "if: 'always()'"]

# Deploy command patterns
DEPLOY_COMMAND = "sf project deploy start"
LEGACY_DEPLOY_COMMAND = "sfdx force:source:deploy"

# Test-level flag
TEST_LEVEL_FLAG = "--test-level"

# Test command patterns
TEST_COMMAND_PATTERNS = [
    "sf apex run test",
    "sfdx force:apex:test:run",
]

# Branch guard patterns (deploy should be conditional)
BRANCH_GUARD_PATTERNS = [
    "github.ref",
    "github.event_name",
]

# Secret reference pattern
SECRET_PATTERN = "${{ secrets."


def check_workflow_file(workflow_path: Path) -> list[str]:
    """Check a single workflow YAML file for required patterns.

    Returns a list of issue strings. Each issue is actionable and cites
    the file and the specific problem found.
    """
    issues: list[str] = []
    label = str(workflow_path)

    try:
        content = workflow_path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"{label}: Cannot read file — {exc}")
        return issues

    lines = content.splitlines()

    # ── 1. Detect whether this looks like a Salesforce CI workflow ────────
    is_sf_workflow = any(
        pat in content for pat in AUTH_COMMAND_PATTERNS + [DEPLOY_COMMAND, LEGACY_DEPLOY_COMMAND]
    )
    if not is_sf_workflow:
        # Not a Salesforce workflow — skip silently
        return issues

    # ── 2. Auth method check ───────────────────────────────────────────────
    has_current_auth = CURRENT_AUTH_PATTERN in content
    has_legacy_auth = LEGACY_AUTH_PATTERN in content

    if not has_current_auth and not has_legacy_auth:
        issues.append(
            f"{label}: No JWT authentication command found. "
            f"Expected 'sf org login jwt' for non-interactive CI auth. "
            f"See: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_jwt_flow.htm"
        )
    elif has_legacy_auth and not has_current_auth:
        issues.append(
            f"{label}: Uses deprecated 'sfdx auth:jwt:grant'. "
            f"Migrate to 'sf org login jwt' (sf CLI v2). "
            f"The legacy 'sfdx force:*' namespace is deprecated as of Spring '24."
        )

    # ── 3. JWT flag checks (only if current auth present) ─────────────────
    if has_current_auth:
        auth_block_lines = []
        in_auth_step = False
        for line in lines:
            if CURRENT_AUTH_PATTERN in line:
                in_auth_step = True
            if in_auth_step:
                auth_block_lines.append(line)
                # Step ends at the next top-level `- name:` or `run:` key
                # Simple heuristic: collect until a blank line or next step marker
                if len(auth_block_lines) > 1 and line.strip().startswith("- name:"):
                    break

        auth_block = "\n".join(auth_block_lines)
        for flag, message in JWT_FLAGS.items():
            if flag not in auth_block and flag not in content:
                issues.append(f"{label}: {message}")

    # ── 4. Secrets hygiene — credentials should reference ${{ secrets.* }} ─
    # Check that consumer key and username are not hardcoded
    # Look for jwt-related env blocks that do NOT reference secrets
    if has_current_auth or has_legacy_auth:
        # Find lines near auth commands that set credentials
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Flag lines that look like they might hardcode a consumer key
            if "--client-id" in stripped and SECRET_PATTERN not in stripped and "secrets." not in stripped:
                # Allow multi-line where value is on next line — check next line too
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if SECRET_PATTERN not in next_line and "SF_CONSUMER_KEY" not in next_line:
                    issues.append(
                        f"{label} (line {i+1}): '--client-id' value may be hardcoded. "
                        f"Use ${{{{ secrets.SF_CONSUMER_KEY }}}} via an env: block."
                    )

    # ── 5. Key file cleanup check ─────────────────────────────────────────
    has_key_write = KEY_WRITE_PATTERN in content
    has_cleanup = KEY_CLEANUP_PATTERN in content and KEY_WRITE_PATTERN in content

    if has_key_write:
        has_always_cleanup = any(pat in content for pat in CLEANUP_PATTERNS) and has_cleanup
        if not has_always_cleanup:
            issues.append(
                f"{label}: JWT server key is written to a temp file but no 'if: always()' cleanup step "
                f"was found. Without 'if: always()', the key file persists on the runner if an earlier "
                f"step fails. Add: 'if: always()' on a step that runs 'rm -f /tmp/server.key'."
            )
    elif has_current_auth or has_legacy_auth:
        # Auth is present but no key file write — possible missing key setup
        issues.append(
            f"{label}: JWT auth command found but no 'echo \"$..._KEY\" > /tmp/server.key' step detected. "
            f"GitHub Secrets are env vars, not files. Write the key content to a temp file before "
            f"passing it to --jwt-key-file."
        )

    # ── 6. Deploy command checks ──────────────────────────────────────────
    has_deploy = DEPLOY_COMMAND in content
    has_legacy_deploy = LEGACY_DEPLOY_COMMAND in content

    if has_legacy_deploy and not has_deploy:
        issues.append(
            f"{label}: Uses deprecated 'sfdx force:source:deploy'. "
            f"Migrate to 'sf project deploy start' (sf CLI v2)."
        )

    if has_deploy or has_legacy_deploy:
        # Check for --test-level flag
        if TEST_LEVEL_FLAG not in content:
            issues.append(
                f"{label}: Deploy command found but '--test-level' flag is missing. "
                f"Without it, Salesforce defaults to NoTestRun on sandboxes (no coverage enforced). "
                f"Specify --test-level explicitly: RunLocalTests | RunAllTestsInOrg | NoTestRun."
            )

        # Check for branch guard on deploy
        has_branch_guard = all(pat in content for pat in BRANCH_GUARD_PATTERNS)
        if not has_branch_guard:
            issues.append(
                f"{label}: Deploy step may lack a branch/event guard (github.ref + github.event_name). "
                f"Without an 'if:' condition, the deploy runs on all triggers including pull_request events, "
                f"which can cause unintended deploys from PR branches."
            )

    # ── 7. Test command check ─────────────────────────────────────────────
    has_test = any(pat in content for pat in TEST_COMMAND_PATTERNS)
    if has_deploy and not has_test:
        issues.append(
            f"{label}: Deploy step found but no Apex test command detected. "
            f"Consider running 'sf apex run test --code-coverage' before deploying to validate coverage."
        )

    # ── 8. Legacy deploy without test-level ──────────────────────────────
    if has_legacy_auth:
        issues.append(
            f"{label}: DEPRECATION WARNING — 'sfdx auth:jwt:grant' is deprecated. "
            f"The 'sfdx force:*' namespace will be removed in a future Salesforce CLI version. "
            f"Migrate to 'sf org login jwt'. "
            f"Reference: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_ci_github.htm"
        )

    return issues


def check_workflow_directory(workflow_dir: Path) -> list[str]:
    """Scan all YAML files in a directory for Salesforce CI/CD issues."""
    issues: list[str] = []

    if not workflow_dir.exists():
        issues.append(f"Workflow directory not found: {workflow_dir}")
        return issues

    yaml_files = list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml"))

    if not yaml_files:
        issues.append(
            f"No YAML workflow files found in {workflow_dir}. "
            f"Expected .github/workflows/*.yml files."
        )
        return issues

    for yaml_file in sorted(yaml_files):
        issues.extend(check_workflow_file(yaml_file))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate GitHub Actions workflow YAML files for Salesforce CI/CD best practices. "
            "Checks JWT auth steps, secrets hygiene, key cleanup, test-level flags, and deprecated commands."
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--workflow-dir",
        default=".github/workflows",
        help="Directory containing workflow YAML files (default: .github/workflows).",
    )
    group.add_argument(
        "--workflow-file",
        help="Path to a single workflow YAML file to check.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.workflow_file:
        workflow_path = Path(args.workflow_file)
        issues = check_workflow_file(workflow_path)
        source_label = str(workflow_path)
    else:
        workflow_dir = Path(args.workflow_dir)
        issues = check_workflow_directory(workflow_dir)
        source_label = str(workflow_dir)

    if not issues:
        print(f"No issues found in: {source_label}")
        return 0

    print(f"Found {len(issues)} issue(s) in: {source_label}\n")
    for i, issue in enumerate(issues, start=1):
        print(f"[{i}] {issue}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
