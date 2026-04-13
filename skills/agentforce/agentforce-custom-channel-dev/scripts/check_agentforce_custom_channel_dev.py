#!/usr/bin/env python3
"""Checker script for Agentforce Custom Channel Dev skill.

Validates Agent API integration patterns in a Salesforce metadata directory or
source file for common misconfigurations identified in the skill's gotchas and
anti-patterns.

Checks performed:
  1. UUID format validation for externalSessionKey references in source files
  2. sequenceId increment patterns — detects non-monotonic or timestamp-based IDs
  3. OAuth scope completeness — detects Connected App configs missing chatbot_api
  4. Session DELETE presence — warns if sessions are created without DELETE cleanup
  5. Mid-session context variable mutation attempts — warns if /messages payloads
     contain non-language variables

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agentforce_custom_channel_dev.py [--help]
    python3 check_agentforce_custom_channel_dev.py --manifest-dir path/to/metadata
    python3 check_agentforce_custom_channel_dev.py --source-file path/to/integration.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
_UUID_V4_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
    re.IGNORECASE,
)

# Detects externalSessionKey assigned to a non-UUID value (heuristic)
_BAD_EXTERNAL_KEY_RE = re.compile(
    r'externalSessionKey\s*[=:]\s*["\'](?!.*[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})[^"\']{1,80}["\']',
    re.IGNORECASE,
)

# Detects sequenceId set to a timestamp-like value (bad pattern)
_BAD_SEQUENCE_ID_RE = re.compile(
    r'sequenceId\s*[=:]\s*(?:time\.|Date\.now\(\)|System\.currentTimeMillis\(\)|int\(time\)|random\.|Math\.random)',
    re.IGNORECASE,
)

# Detects session POST without DELETE (crude heuristic: file has POST sessions but no DELETE)
_SESSION_POST_RE = re.compile(
    r'/sessions["\'\s]',
    re.IGNORECASE,
)
_SESSION_DELETE_RE = re.compile(
    r'(?:delete|DELETE)\s*[\(\s].*?/sessions',
    re.IGNORECASE,
)
_HTTP_DELETE_RE = re.compile(
    r'(?:method\s*=\s*["\']DELETE["\']|requests\.delete|\.delete\s*\(|HttpDelete|deleteMethod)',
    re.IGNORECASE,
)

# Detects Connected App XML missing chatbot_api scope
_CONNECTED_APP_RE = re.compile(r'<ConnectedApp>', re.IGNORECASE)
_CHATBOT_SCOPE_RE = re.compile(r'chatbot_api', re.IGNORECASE)

# Detects mid-session variable update attempts (variables in /messages payload
# that are not Context.EndUserLanguage)
_MESSAGES_VARIABLES_RE = re.compile(
    r'/messages.*?variables.*?name.*?Context\.(?!EndUserLanguage)',
    re.IGNORECASE | re.DOTALL,
)

# Detects BYOC and raw Agent API mixed in same file
_RAW_AGENT_SESSIONS_RE = re.compile(
    r'/einstein/ai-agent/agents/.+?/sessions',
    re.IGNORECASE,
)
_BYOC_CONVERSATIONS_RE = re.compile(
    r'/einstein/ai-agent/byoc/conversations',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# File-level checks
# ---------------------------------------------------------------------------

def check_source_file(path: Path) -> list[str]:
    """Check a single source file for Agent API anti-patterns."""
    issues: list[str] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return issues

    # Check 1: externalSessionKey assigned to non-UUID literal
    for match in _BAD_EXTERNAL_KEY_RE.finditer(content):
        line_num = content[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_num}: externalSessionKey appears to be assigned a non-UUID value. "
            "Use a UUIDv4 generator (e.g., uuid.uuid4() / UUID.randomUUID()) — "
            "arbitrary strings are rejected by the Agent API with a 400 error."
        )

    # Check 2: sequenceId set to a timestamp or random value
    for match in _BAD_SEQUENCE_ID_RE.finditer(content):
        line_num = content[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_num}: sequenceId appears to use a timestamp or random value. "
            "sequenceId must be a monotonically increasing integer per session, starting at 1. "
            "Timestamps and random values will cause message ordering errors."
        )

    # Check 3: Session POST without any DELETE (heuristic)
    has_session_post = bool(_SESSION_POST_RE.search(content))
    has_delete = bool(_SESSION_DELETE_RE.search(content)) or bool(_HTTP_DELETE_RE.search(content))
    if has_session_post and not has_delete:
        issues.append(
            f"{path}: Agent API session POST detected but no session DELETE found. "
            "Always call DELETE /sessions/{{sessionId}} when the conversation ends "
            "to prevent orphaned sessions that deplete the concurrent session pool."
        )

    # Check 4: Mid-session context variable mutation for non-language variables
    if _MESSAGES_VARIABLES_RE.search(content):
        issues.append(
            f"{path}: Possible mid-session context variable update detected in a /messages payload "
            "for a non-language variable. Context variables set at session creation are immutable "
            "for the session lifetime (except Context.EndUserLanguage). "
            "Use agent actions (Apex/Flow) for dynamic context instead."
        )

    # Check 5: Mixed raw Agent API and BYOC CCaaS endpoints in same file
    has_raw_api = bool(_RAW_AGENT_SESSIONS_RE.search(content))
    has_byoc = bool(_BYOC_CONVERSATIONS_RE.search(content))
    if has_raw_api and has_byoc:
        issues.append(
            f"{path}: Both raw Agent API (/agents/{{agentId}}/sessions) and BYOC CCaaS "
            "(/byoc/conversations) endpoints detected in the same file. "
            "These are mutually exclusive integration paths — do not mix them "
            "in a single conversation lifecycle."
        )

    return issues


def check_connected_app_xml(path: Path) -> list[str]:
    """Check a Connected App metadata XML file for missing chatbot_api scope."""
    issues: list[str] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return issues

    if not _CONNECTED_APP_RE.search(content):
        return issues  # Not a Connected App file

    if not _CHATBOT_SCOPE_RE.search(content):
        issues.append(
            f"{path}: Connected App definition does not include 'chatbot_api' OAuth scope. "
            "The Agent API requires both 'api' and 'chatbot_api' scopes. "
            "Add 'chatbot_api' to the oauthScopes section of the Connected App."
        )

    return issues


# ---------------------------------------------------------------------------
# Directory scan
# ---------------------------------------------------------------------------

_SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".cls", ".apex"}
_XML_EXTENSION = ".xml"


def check_agentforce_custom_channel_dev(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Walk all files in the directory
    for file_path in manifest_dir.rglob("*"):
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()

        if suffix in _SOURCE_EXTENSIONS:
            issues.extend(check_source_file(file_path))
        elif suffix == _XML_EXTENSION:
            issues.extend(check_connected_app_xml(file_path))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Agentforce custom channel integration code and metadata for common "
            "anti-patterns: non-UUID externalSessionKey, bad sequenceId, missing session DELETE, "
            "mid-session context variable mutation, mixed API endpoints, and missing chatbot_api scope."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata or integration source (default: current directory).",
    )
    parser.add_argument(
        "--source-file",
        default=None,
        help="Single source file to check instead of scanning a directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.source_file:
        source_path = Path(args.source_file)
        if not source_path.exists():
            print(f"ERROR: Source file not found: {source_path}", file=sys.stderr)
            return 2
        issues.extend(check_source_file(source_path))
    else:
        manifest_dir = Path(args.manifest_dir) if args.manifest_dir else Path(".")
        issues.extend(check_agentforce_custom_channel_dev(manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
