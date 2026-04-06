#!/usr/bin/env python3
"""Checker script for Environment-Specific Value Injection skill.

Scans a Salesforce DX project's source tree for common environment injection
anti-patterns: hardcoded URLs/IPs in Named Credential XML, secrets in Custom
Metadata records, missing sfdx-project.json replacements entries for placeholder
tokens, and plaintext credential values in metadata files.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_environment_specific_value_injection.py [--help]
    python3 check_environment_specific_value_injection.py --manifest-dir force-app
    python3 check_environment_specific_value_injection.py --manifest-dir . --project-json sfdx-project.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# URLs that look like real endpoint values (not placeholders)
# A placeholder should be ${VAR_NAME} — real URLs have http:// or https://
HARDCODED_URL_PATTERN = re.compile(
    r"<calloutUrl>\s*https?://[^<${}]+</calloutUrl>",
    re.IGNORECASE,
)

# Placeholder token pattern — correct usage
PLACEHOLDER_PATTERN = re.compile(r"\$\{[A-Z0-9_]+\}")

# CMT field names that suggest secret values
SECRET_FIELD_NAME_PATTERN = re.compile(
    r"<field>(API_?Key|Password|Token|Secret|ClientSecret|AccessToken|RefreshToken|Private_?Key|Credential)[^<]*</field>",
    re.IGNORECASE,
)

# CMT field values that look non-empty (value in <value> tag after a secret-named field)
SECRET_VALUE_PATTERN = re.compile(
    r"<value[^>]*>[^<]{4,}</value>",  # non-empty value (4+ chars to exclude <value/>)
)

# sfdx-project.json replacement entry keys
REPLACEMENT_ENTRY_KEYS = {"stringToReplace", "replaceWithEnv", "filename"}

# Credentials that should never appear in Named Credential XML as plain values
PLAINTEXT_CREDENTIAL_PATTERNS = [
    re.compile(r"<password>[^<]{4,}</password>", re.IGNORECASE),
    re.compile(r"<token>[^<]{4,}</token>", re.IGNORECASE),
]

# Environment variable substitution suspects in source files
OBVIOUS_PLACEHOLDER_IN_SOURCE = re.compile(r"\$\{([A-Z0-9_]+)\}")


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def check_named_credentials(manifest_dir: Path) -> list[str]:
    """Check Named Credential XML files for hardcoded URLs and plaintext credentials."""
    issues: list[str] = []

    cred_files = list(manifest_dir.rglob("*.namedCredential")) + list(
        manifest_dir.rglob("*.externalCredential")
    )

    for cred_file in sorted(cred_files):
        try:
            content = cred_file.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"{cred_file}: Cannot read file — {exc}")
            continue

        label = str(cred_file.relative_to(manifest_dir))

        # Check for hardcoded callout URL (no placeholder token)
        hardcoded_url_match = HARDCODED_URL_PATTERN.search(content)
        if hardcoded_url_match:
            url_snippet = hardcoded_url_match.group(0)[:80]
            issues.append(
                f"{label}: Hardcoded endpoint URL found in <calloutUrl>: '{url_snippet}'. "
                f"Replace with a ${{ENV_VAR_NAME}} placeholder and add a 'replacements' entry "
                f"in sfdx-project.json so CI injects the org-specific value. "
                f"Reference: Salesforce DX Developer Guide — String Replacements"
            )

        # Check for plaintext password/token in Named Credential XML
        for pattern in PLAINTEXT_CREDENTIAL_PATTERNS:
            match = pattern.search(content)
            if match:
                tag_snippet = match.group(0)[:40]
                issues.append(
                    f"{label}: Possible plaintext credential found: '{tag_snippet}'. "
                    f"Named Credential XML must never contain real passwords or tokens. "
                    f"Deploy the stub with empty credentials and populate post-deploy via "
                    f"the Tooling API or Setup UI."
                )
                break  # one issue per file for this category is sufficient

    return issues


def check_custom_metadata_for_secrets(manifest_dir: Path) -> list[str]:
    """Scan Custom Metadata record files for secret-named fields with non-empty values."""
    issues: list[str] = []

    cmt_files = list(manifest_dir.rglob("*.md-meta.xml"))

    for cmt_file in sorted(cmt_files):
        try:
            content = cmt_file.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"{cmt_file}: Cannot read file — {exc}")
            continue

        label = str(cmt_file.relative_to(manifest_dir))

        # Look for secret-sounding field names with adjacent non-empty values
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if SECRET_FIELD_NAME_PATTERN.search(line):
                # Check the next few lines for a non-empty value
                context_lines = "\n".join(lines[i : i + 5])
                if SECRET_VALUE_PATTERN.search(context_lines):
                    field_match = SECRET_FIELD_NAME_PATTERN.search(line)
                    field_name = field_match.group(0) if field_match else line.strip()
                    issues.append(
                        f"{label} (line {i + 1}): Custom Metadata record appears to store a secret "
                        f"in field: {field_name.strip()[:60]}. "
                        f"Secrets (passwords, tokens, API keys) must not be stored in Custom Metadata. "
                        f"Use Named Credentials or External Credentials instead."
                    )
                    break  # one issue per file

    return issues


def check_sfdx_project_replacements(project_json_path: Path, manifest_dir: Path) -> list[str]:
    """Check sfdx-project.json replacements for completeness and warn about missing entries."""
    issues: list[str] = []

    if not project_json_path.exists():
        # Not an error — project JSON may be at a different path
        return issues

    try:
        project_data = json.loads(project_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"{project_json_path}: Cannot parse sfdx-project.json — {exc}")
        return issues

    replacements = project_data.get("replacements", [])

    # Collect all placeholders found in source files
    placeholder_files: dict[str, set[str]] = {}
    for source_file in manifest_dir.rglob("*.namedCredential"):
        try:
            content = source_file.read_text(encoding="utf-8")
        except OSError:
            continue
        placeholders = set(OBVIOUS_PLACEHOLDER_IN_SOURCE.findall(content))
        if placeholders:
            placeholder_files[str(source_file.relative_to(project_json_path.parent))] = placeholders

    # Check each found placeholder has a corresponding replacements entry
    covered_pairs: set[tuple[str, str]] = set()
    for entry in replacements:
        if not isinstance(entry, dict):
            continue
        filename = entry.get("filename", "")
        string_to_replace = entry.get("stringToReplace", "")
        # Extract var name from placeholder: ${VAR_NAME} -> VAR_NAME
        match = OBVIOUS_PLACEHOLDER_IN_SOURCE.search(string_to_replace)
        if match:
            covered_pairs.add((filename, match.group(1)))

    for filepath, placeholders in sorted(placeholder_files.items()):
        for placeholder_var in sorted(placeholders):
            if (filepath, placeholder_var) not in covered_pairs:
                issues.append(
                    f"sfdx-project.json: Placeholder '${{{placeholder_var}}}' found in '{filepath}' "
                    f"but no matching 'replacements' entry exists in sfdx-project.json. "
                    f"Add an entry with 'stringToReplace': '${{{placeholder_var}}}' and "
                    f"'replaceWithEnv': '{placeholder_var}' to ensure CI substitutes the value at deploy time."
                )

    # Check each replacements entry references an existing file
    for entry in replacements:
        if not isinstance(entry, dict):
            issues.append(
                "sfdx-project.json: 'replacements' contains a non-object entry. "
                "Each entry must be an object with 'filename', 'stringToReplace', and 'replaceWithEnv'."
            )
            continue

        missing_keys = REPLACEMENT_ENTRY_KEYS - set(entry.keys())
        if missing_keys:
            issues.append(
                f"sfdx-project.json: Replacements entry is missing required keys: {sorted(missing_keys)}. "
                f"Each entry must have 'filename', 'stringToReplace', and 'replaceWithEnv'."
            )
            continue

        entry_file = project_json_path.parent / entry["filename"]
        if not entry_file.exists():
            issues.append(
                f"sfdx-project.json: Replacements entry references a file that does not exist: "
                f"'{entry['filename']}'. Verify the path is correct relative to sfdx-project.json."
            )

    return issues


def check_environment_specific_value_injection(
    manifest_dir: Path,
    project_json_path: Path | None = None,
) -> list[str]:
    """Run all environment injection checks and return a list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_named_credentials(manifest_dir))
    issues.extend(check_custom_metadata_for_secrets(manifest_dir))

    if project_json_path is None:
        # Default: look for sfdx-project.json one level above manifest_dir
        candidate = manifest_dir.parent / "sfdx-project.json"
        if not candidate.exists():
            # Also try the manifest_dir itself
            candidate = manifest_dir / "sfdx-project.json"
        project_json_path = candidate

    issues.extend(check_sfdx_project_replacements(project_json_path, manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce DX project metadata for environment-specific value injection issues. "
            "Detects hardcoded URLs in Named Credentials, secrets in Custom Metadata records, "
            "and missing sfdx-project.json replacements entries for placeholder tokens."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default="force-app",
        help="Root directory of Salesforce source metadata (default: force-app).",
    )
    parser.add_argument(
        "--project-json",
        default=None,
        help="Path to sfdx-project.json (default: auto-detect adjacent to --manifest-dir).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    project_json_path = Path(args.project_json) if args.project_json else None

    issues = check_environment_specific_value_injection(manifest_dir, project_json_path)

    if not issues:
        print(f"No environment injection issues found in: {manifest_dir}")
        return 0

    print(f"Found {len(issues)} issue(s) in: {manifest_dir}\n")
    for i, issue in enumerate(issues, start=1):
        print(f"[{i}] {issue}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
