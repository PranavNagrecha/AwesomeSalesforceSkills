#!/usr/bin/env python3
"""Checker script for Sandbox Data Isolation Gotchas skill.

Scans a Salesforce metadata project directory for patterns that indicate
sandbox isolation risks: hardcoded production endpoints in Named Credential
XML, SandboxPostCopy classes missing scheduled job abort logic, and workflow
or flow email alert configurations that target Contact/Lead email fields.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sandbox_data_isolation_gotchas.py [--help]
    python3 check_sandbox_data_isolation_gotchas.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, suffix: str) -> list[Path]:
    """Return all files under root with the given suffix."""
    if not root.exists():
        return []
    return sorted(root.rglob(f"*{suffix}"))


# ---------------------------------------------------------------------------
# Check 1: Named Credentials with non-sandbox endpoint patterns
# ---------------------------------------------------------------------------

_PRODUCTION_HOSTNAME_RE = re.compile(
    r"<endpoint>https?://(?!.*\b(sandbox|test|uat|staging|dev|qa)\b)[^<]+</endpoint>",
    re.IGNORECASE,
)

def check_named_credentials(manifest_dir: Path) -> list[str]:
    """Flag Named Credential XML files whose endpoint URL looks like a production host."""
    issues: list[str] = []
    named_cred_dir = manifest_dir / "namedCredentials"
    if not named_cred_dir.exists():
        return issues

    for nc_file in find_files(named_cred_dir, ".namedCredential-meta.xml"):
        content = nc_file.read_text(encoding="utf-8", errors="replace")
        if _PRODUCTION_HOSTNAME_RE.search(content):
            issues.append(
                f"Named Credential may point at a production endpoint: {nc_file.relative_to(manifest_dir)}"
                " — verify the endpoint URL is a sandbox/test target before re-entering credentials."
            )
    return issues


# ---------------------------------------------------------------------------
# Check 2: SandboxPostCopy classes missing abortJob calls
# ---------------------------------------------------------------------------

_SANDBOX_POST_COPY_IMPL_RE = re.compile(
    r"implements\s+(?:System\.)?SandboxPostCopy", re.IGNORECASE
)
_ABORT_JOB_RE = re.compile(r"System\.abortJob\s*\(", re.IGNORECASE)

def check_sandboxpostcopy_classes(manifest_dir: Path) -> list[str]:
    """Flag SandboxPostCopy classes that do not call System.abortJob()."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    for cls_file in find_files(classes_dir, ".cls"):
        content = cls_file.read_text(encoding="utf-8", errors="replace")
        if _SANDBOX_POST_COPY_IMPL_RE.search(content):
            if not _ABORT_JOB_RE.search(content):
                issues.append(
                    f"SandboxPostCopy class does not call System.abortJob(): {cls_file.relative_to(manifest_dir)}"
                    " — scheduled jobs copied from production will fire in the sandbox unless explicitly aborted."
                )
    return issues


# ---------------------------------------------------------------------------
# Check 3: SandboxPostCopy classes not wrapping DML in try/catch
# ---------------------------------------------------------------------------

_TRY_CATCH_RE = re.compile(r"\btry\s*\{", re.IGNORECASE)

def check_sandboxpostcopy_error_handling(manifest_dir: Path) -> list[str]:
    """Warn when SandboxPostCopy classes contain no try/catch blocks."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    for cls_file in find_files(classes_dir, ".cls"):
        content = cls_file.read_text(encoding="utf-8", errors="replace")
        if _SANDBOX_POST_COPY_IMPL_RE.search(content):
            if not _TRY_CATCH_RE.search(content):
                issues.append(
                    f"SandboxPostCopy class has no try/catch blocks: {cls_file.relative_to(manifest_dir)}"
                    " — an unhandled exception will silently skip all remaining isolation steps."
                )
    return issues


# ---------------------------------------------------------------------------
# Check 4: Workflow rules or email alerts with recipient type that could reach real contacts
# ---------------------------------------------------------------------------

_RECIPIENT_TYPE_CONTACT_RE = re.compile(
    r"<recipientType>(contactLookup|contactOwner|creator|relatedContactRoles)</recipientType>",
    re.IGNORECASE,
)

def check_workflow_email_recipients(manifest_dir: Path) -> list[str]:
    """Flag workflow email alerts that deliver to Contact-based recipients."""
    issues: list[str] = []
    workflow_dir = manifest_dir / "workflows"
    if not workflow_dir.exists():
        return issues

    for wf_file in find_files(workflow_dir, ".workflow-meta.xml"):
        content = wf_file.read_text(encoding="utf-8", errors="replace")
        if _RECIPIENT_TYPE_CONTACT_RE.search(content):
            issues.append(
                f"Workflow may send email to Contact addresses: {wf_file.relative_to(manifest_dir)}"
                " — Contact email fields are NOT obfuscated on sandbox refresh."
                " Ensure Contact emails are scrubbed or deliverability is set to 'No Access'."
            )
    return issues


# ---------------------------------------------------------------------------
# Check 5: Flow email actions present (warn — cannot fully analyze recipient source)
# ---------------------------------------------------------------------------

_FLOW_SEND_EMAIL_RE = re.compile(
    r"<actionType>emailSimple</actionType>|<actionName>emailSimple</actionName>",
    re.IGNORECASE,
)

def check_flow_email_actions(manifest_dir: Path) -> list[str]:
    """Warn when Flow metadata contains emailSimple action calls."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    for flow_file in find_files(flows_dir, ".flow-meta.xml"):
        content = flow_file.read_text(encoding="utf-8", errors="replace")
        if _FLOW_SEND_EMAIL_RE.search(content):
            issues.append(
                f"Flow contains email send action: {flow_file.relative_to(manifest_dir)}"
                " — verify the recipient source does not reference Contact/Lead email fields"
                " that are not scrubbed in the sandbox."
            )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for sandbox data isolation risks: "
            "production Named Credential endpoints, SandboxPostCopy missing abortJob, "
            "and email alert configurations that could reach real Contact/Lead addresses."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_sandbox_data_isolation_gotchas(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_named_credentials(manifest_dir))
    issues.extend(check_sandboxpostcopy_classes(manifest_dir))
    issues.extend(check_sandboxpostcopy_error_handling(manifest_dir))
    issues.extend(check_workflow_email_recipients(manifest_dir))
    issues.extend(check_flow_email_actions(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_sandbox_data_isolation_gotchas(manifest_dir)

    if not issues:
        print("No sandbox isolation issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
