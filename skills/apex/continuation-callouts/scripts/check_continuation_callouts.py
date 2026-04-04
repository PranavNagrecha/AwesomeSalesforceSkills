#!/usr/bin/env python3
"""Checker script for the Continuation Callouts skill.

Scans Apex (.cls) files in the given metadata directory for common
Continuation anti-patterns and missing requirements.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_continuation_callouts.py [--manifest-dir path/to/metadata]
    python3 check_continuation_callouts.py --help

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Detects `new Continuation(` — class is being instantiated
CONTINUATION_INSTANTIATION_RE = re.compile(
    r'\bnew\s+Continuation\s*\(',
    re.IGNORECASE,
)

# Detects `con.continuationMethod = '...'` — captures the assigned value
CONTINUATION_METHOD_ASSIGN_RE = re.compile(
    r'\.continuationMethod\s*=\s*[\'"]([^\'"]+)[\'"]',
    re.IGNORECASE,
)

# Detects `con.state = ` being assigned
STATE_ASSIGN_RE = re.compile(
    r'\.state\s*=\s*',
    re.IGNORECASE,
)

# Detects passing an SObject directly as state — heuristic: variable names
# ending in common SObject suffixes assigned to .state
SOBJECT_STATE_RE = re.compile(
    r'\.state\s*=\s*\b\w*(Account|Contact|Opportunity|Lead|Case|Order|Quote)\b',
    re.IGNORECASE,
)

# Detects more than 3 addHttpRequest calls in a single method — heuristic
ADD_HTTP_REQUEST_RE = re.compile(
    r'\baddHttpRequest\s*\(',
    re.IGNORECASE,
)

# Detects continuation usage inside a trigger context — the file name ends
# with 'Trigger' and contains 'new Continuation('
# (file-level heuristic; not 100% precise but catches the most common case)

# Detects @future annotation alongside Continuation
FUTURE_AND_CONTINUATION_RE = re.compile(
    r'@future.*callout\s*=\s*true',
    re.IGNORECASE,
)

# Detects callback method signatures — looking for the correct signature
# `public Object methodName(List<String> labels, Object state)`
CORRECT_CALLBACK_SIGNATURE_RE = re.compile(
    r'public\s+Object\s+\w+\s*\(\s*List\s*<\s*String\s*>\s+\w+\s*,\s*Object\s+\w+\s*\)',
    re.IGNORECASE,
)

# Detects hardcoded http/https endpoints (not Named Credential callout: prefix)
HARDCODED_ENDPOINT_RE = re.compile(
    r'setEndpoint\s*\(\s*[\'"]https?://',
    re.IGNORECASE,
)

# Detects Named Credential endpoint pattern
NAMED_CREDENTIAL_ENDPOINT_RE = re.compile(
    r'setEndpoint\s*\(\s*[\'"]callout:',
    re.IGNORECASE,
)

# Detects `@AuraEnabled` without `continuation=true` in files that also
# instantiate Continuation
AURA_ENABLED_NO_CONTINUATION_RE = re.compile(
    r'@AuraEnabled\s*(?!\(.*continuation\s*=\s*true)',
    re.IGNORECASE,
)

AURA_ENABLED_WITH_CONTINUATION_RE = re.compile(
    r'@AuraEnabled\s*\(.*continuation\s*=\s*true',
    re.IGNORECASE,
)

# Detects static modifier on what might be the callback (if it also has the
# correct parameter shape)
STATIC_CALLBACK_RE = re.compile(
    r'public\s+static\s+Object\s+\w+\s*\(\s*List\s*<\s*String\s*>\s+\w+\s*,\s*Object\s+\w+\s*\)',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Per-file checks
# ---------------------------------------------------------------------------

def check_file(path: Path) -> list[str]:
    """Return a list of issue strings for the given Apex file."""
    issues: list[str] = []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path.name}: cannot read file — {exc}"]

    if not CONTINUATION_INSTANTIATION_RE.search(source):
        # File does not use Continuation at all — skip further checks
        return []

    file_label = path.name

    # ------------------------------------------------------------------
    # 1. Trigger file using Continuation
    # ------------------------------------------------------------------
    trigger_name_re = re.compile(r'trigger\s+\w+\s+on\s+\w+', re.IGNORECASE)
    if trigger_name_re.search(source):
        issues.append(
            f"{file_label}: Continuation instantiated inside a trigger. "
            "Continuation is not supported in trigger context — move callout to "
            "a Visualforce controller or @AuraEnabled(continuation=true) method."
        )

    # ------------------------------------------------------------------
    # 2. @future(callout=true) alongside Continuation
    # ------------------------------------------------------------------
    if FUTURE_AND_CONTINUATION_RE.search(source):
        issues.append(
            f"{file_label}: @future(callout=true) and Continuation both present. "
            "Continuation cannot be used inside a @future method. "
            "Separate the Continuation pattern into a Visualforce/LWC entry point."
        )

    # ------------------------------------------------------------------
    # 3. continuationMethod assigned — verify a matching public callback exists
    # ------------------------------------------------------------------
    method_assignments = CONTINUATION_METHOD_ASSIGN_RE.findall(source)
    if not method_assignments:
        issues.append(
            f"{file_label}: Continuation instantiated but `continuationMethod` "
            "is never assigned. The callback will never fire."
        )
    else:
        for assigned_name in method_assignments:
            # Check that a public instance method with this name and correct
            # signature exists in the file
            callback_pattern = re.compile(
                r'public\s+Object\s+' + re.escape(assigned_name) +
                r'\s*\(\s*List\s*<\s*String\s*>\s+\w+\s*,\s*Object\s+\w+\s*\)',
                re.IGNORECASE,
            )
            if not callback_pattern.search(source):
                issues.append(
                    f"{file_label}: continuationMethod is set to '{assigned_name}' "
                    "but no matching public instance method with signature "
                    "`public Object {name}(List<String> labels, Object state)` "
                    "was found. Verify the method name and signature."
                )

    # ------------------------------------------------------------------
    # 4. Static callback anti-pattern
    # ------------------------------------------------------------------
    if STATIC_CALLBACK_RE.search(source):
        issues.append(
            f"{file_label}: A static method with the Continuation callback "
            "signature was detected. Continuation callbacks must be non-static "
            "public instance methods. Removing `static` fixes this."
        )

    # ------------------------------------------------------------------
    # 5. More than 3 addHttpRequest calls in a single method (heuristic)
    # ------------------------------------------------------------------
    add_req_count = len(ADD_HTTP_REQUEST_RE.findall(source))
    if add_req_count > 3:
        issues.append(
            f"{file_label}: {add_req_count} calls to `addHttpRequest` detected. "
            "A single Continuation supports at most 3 parallel callouts. "
            "Use chained Continuations (return a new Continuation from the callback) "
            "for more than 3 callouts."
        )

    # ------------------------------------------------------------------
    # 6. Hardcoded HTTP endpoint instead of Named Credential
    # ------------------------------------------------------------------
    hardcoded_matches = HARDCODED_ENDPOINT_RE.findall(source)
    named_cred_matches = NAMED_CREDENTIAL_ENDPOINT_RE.findall(source)
    if hardcoded_matches and not named_cred_matches:
        issues.append(
            f"{file_label}: `setEndpoint` uses a hardcoded `http(s)://` URL "
            "instead of a Named Credential (`callout:CredentialName/path`). "
            "Use Named Credentials to avoid hard-coded secrets and enable "
            "credential rotation without code changes."
        )

    # ------------------------------------------------------------------
    # 7. SObject assigned directly as state (heuristic)
    # ------------------------------------------------------------------
    if SOBJECT_STATE_RE.search(source):
        issues.append(
            f"{file_label}: `con.state` appears to be assigned an SObject "
            "(detected common SObject type in the assignment). SObjects with "
            "relationship fields are not JSON-serializable and will cause "
            "`SerializationException` in the callback. Serialize with "
            "`JSON.serialize()` first, then deserialize in the callback."
        )

    # ------------------------------------------------------------------
    # 8. @AuraEnabled without continuation=true in a file using Continuation
    # ------------------------------------------------------------------
    if AURA_ENABLED_NO_CONTINUATION_RE.search(source) and \
       not AURA_ENABLED_WITH_CONTINUATION_RE.search(source):
        issues.append(
            f"{file_label}: `@AuraEnabled` annotation found without "
            "`continuation=true` in a file that uses Continuation. "
            "LWC Continuation methods must be annotated "
            "`@AuraEnabled(continuation=true)` to activate the async callout path."
        )

    return issues


# ---------------------------------------------------------------------------
# Directory-level scan
# ---------------------------------------------------------------------------

def check_continuation_callouts(manifest_dir: Path) -> list[str]:
    """Scan all Apex .cls files under manifest_dir and return all issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    cls_files = list(manifest_dir.rglob("*.cls"))
    if not cls_files:
        # Not necessarily an error — directory might be non-Apex
        return issues

    for cls_file in cls_files:
        file_issues = check_file(cls_file)
        issues.extend(file_issues)

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex Continuation callout implementations for common "
            "anti-patterns and missing requirements. "
            "Exits 0 if no issues found, 1 if issues are found."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory containing Apex .cls files "
            "(searched recursively). Default: current directory."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_continuation_callouts(manifest_dir)

    if not issues:
        print("No Continuation callout issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
