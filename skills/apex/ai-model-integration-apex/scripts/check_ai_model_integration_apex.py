#!/usr/bin/env python3
"""Checker script for AI Model Integration Apex skill.

Scans Apex source files for common anti-patterns in AI model callout code:
- Synchronous per-record aiplatform.ModelsAPI calls in trigger handlers
- Missing Code200 null-check before response traversal
- Hardcoded model API name strings across multiple classes
- Missing AllowsCallouts on Batch/Queueable classes that use ModelsAPI
- Direct token logging via System.debug

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_ai_model_integration_apex.py [--help]
    python3 check_ai_model_integration_apex.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# ModelsAPI call patterns
MODELS_API_CALL = re.compile(
    r"\bnew\s+aiplatform\.ModelsAPI\(\)\s*\."
    r"(createChatGenerations|createGenerations|createEmbeddings)\b"
)

# Code200 direct access without a preceding null-check in the same method
CODE200_ACCESS = re.compile(r"response\.Code200\s*\.")

# Code200 null-check pattern
CODE200_NULL_CHECK = re.compile(
    r"response\.Code200\s*(==|!=)\s*null"
)

# Hardcoded default model API name
HARDCODED_MODEL_API = re.compile(
    r"['\"]sfdc_ai__Default[A-Za-z0-9_]+"
)

# Batch / Queueable class declaration without AllowsCallouts
BATCH_CLASS_DECL = re.compile(
    r"class\s+\w+\s+implements\s+[^{]*Database\.Batchable"
)
QUEUEABLE_CLASS_DECL = re.compile(
    r"class\s+\w+\s+implements\s+[^{]*Queueable"
)
ALLOWS_CALLOUTS = re.compile(r"Database\.AllowsCallouts")

# System.debug with a token/bearer variable nearby
TOKEN_DEBUG = re.compile(
    r"System\.debug\s*\([^)]*\b(token|bearer|jwt|access_token)\b",
    re.IGNORECASE,
)

# Trigger context: Trigger.new or Trigger.newMap inside a for loop
TRIGGER_LOOP = re.compile(
    r"for\s*\([^)]*Trigger\.(new|newMap)"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def collect_apex_files(manifest_dir: Path) -> list[Path]:
    apex_files: list[Path] = []
    for pattern in ("**/*.cls", "**/*.trigger"):
        apex_files.extend(manifest_dir.rglob(pattern.lstrip("**/")))
    return apex_files


def _method_body_has_null_check(source: str, match_pos: int) -> bool:
    """
    Heuristic: look for a Code200 null-check anywhere within ±800 chars
    of the Code200 direct access. This is not AST-accurate but catches
    the common patterns and avoids false positives on helper methods.
    """
    window_start = max(0, match_pos - 800)
    window_end = min(len(source), match_pos + 400)
    window = source[window_start:window_end]
    return bool(CODE200_NULL_CHECK.search(window))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_missing_code200_null_guard(path: Path, source: str, issues: list[str]) -> None:
    """Warn when Code200 is accessed without a nearby null-check."""
    for m in CODE200_ACCESS.finditer(source):
        if not _method_body_has_null_check(source, m.start()):
            line_num = source[: m.start()].count("\n") + 1
            issues.append(
                f"{path.name}:{line_num} — response.Code200 accessed without a "
                f"null-check guard nearby. Non-200 model responses leave Code200 null "
                f"and cause NullPointerException."
            )
            break  # one warning per file is sufficient


def check_hardcoded_model_api_names(
    apex_files: list[Path], issues: list[str]
) -> None:
    """Warn when the same hardcoded model API name appears in multiple files."""
    name_to_files: dict[str, list[str]] = {}
    for path in apex_files:
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in HARDCODED_MODEL_API.finditer(source):
            raw = m.group(0).strip("'\"")
            name_to_files.setdefault(raw, [])
            if path.name not in name_to_files[raw]:
                name_to_files[raw].append(path.name)

    for name, files in name_to_files.items():
        if len(files) > 1:
            issues.append(
                f"Hardcoded model API name '{name}' appears in {len(files)} files "
                f"({', '.join(files)}). Store this value in Custom Metadata or a "
                f"Custom Setting to avoid scattered configuration strings."
            )


def check_missing_allows_callouts(
    path: Path, source: str, issues: list[str]
) -> None:
    """Warn when a Batch or Queueable class uses ModelsAPI but lacks AllowsCallouts."""
    uses_models_api = bool(MODELS_API_CALL.search(source))
    if not uses_models_api:
        return

    is_batch = bool(BATCH_CLASS_DECL.search(source))
    is_queueable = bool(QUEUEABLE_CLASS_DECL.search(source))

    if (is_batch or is_queueable) and not ALLOWS_CALLOUTS.search(source):
        kind = "Batch" if is_batch else "Queueable"
        issues.append(
            f"{path.name} — {kind} class makes aiplatform.ModelsAPI calls but does "
            f"not implement Database.AllowsCallouts. Callouts in async contexts "
            f"require this interface."
        )


def check_trigger_synchronous_ai_callout(
    path: Path, source: str, issues: list[str]
) -> None:
    """Warn when a trigger iterates Trigger.new and makes a direct ModelsAPI call."""
    if not path.suffix == ".trigger":
        return
    if TRIGGER_LOOP.search(source) and MODELS_API_CALL.search(source):
        issues.append(
            f"{path.name} — Trigger iterates Trigger.new and calls aiplatform.ModelsAPI "
            f"directly. This will exceed the 100-callout limit at bulk scale. "
            f"Move AI processing to a Queueable (Database.AllowsCallouts)."
        )


def check_token_debug_logging(
    path: Path, source: str, issues: list[str]
) -> None:
    """Warn when a token or bearer credential is passed to System.debug."""
    m = TOKEN_DEBUG.search(source)
    if m:
        line_num = source[: m.start()].count("\n") + 1
        issues.append(
            f"{path.name}:{line_num} — Possible debug logging of a bearer/JWT token. "
            f"Never log credential values. Log only whether a token was obtained."
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex metadata for AI model integration anti-patterns "
            "(aiplatform.ModelsAPI, Einstein Platform Services, token management)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_ai_model_integration_apex(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = collect_apex_files(manifest_dir)

    if not apex_files:
        # No Apex files is not an error for this checker
        return issues

    # Cross-file check (needs all files)
    check_hardcoded_model_api_names(apex_files, issues)

    # Per-file checks
    for path in apex_files:
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        check_missing_code200_null_guard(path, source, issues)
        check_missing_allows_callouts(path, source, issues)
        check_trigger_synchronous_ai_callout(path, source, issues)
        check_token_debug_logging(path, source, issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_ai_model_integration_apex(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
