#!/usr/bin/env python3
"""Checker script for SF-to-LLM Data Pipelines skill.

Inspects Salesforce project metadata and source files for common anti-patterns
related to external LLM data pipeline extraction. Uses stdlib only — no pip
dependencies.

Checks performed:
  1. Detects username/password OAuth patterns in Python/config files.
  2. Detects use of LastModifiedDate (vs SystemModstamp) in SOQL queries.
  3. Detects KnowledgeArticleVersion queries missing PublishStatus filter.
  4. Detects REST API nextRecordsUrl patterns used for large-volume extraction.
  5. Detects absence of HTML stripping before embedding calls.
  6. Detects PII field names in SOQL SELECT projections.
  7. Detects watermark advancement before write confirmation (heuristic).

Usage:
    python3 check_sf_to_llm_data_pipelines.py [--help]
    python3 check_sf_to_llm_data_pipelines.py --manifest-dir path/to/project
    python3 check_sf_to_llm_data_pipelines.py --manifest-dir . --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# OAuth username/password grant type — matches both:
#   grant_type=password  (URL-encoded form)
#   "grant_type": "password"  (JSON dict)
#   {"grant_type": "password"}
_PASSWORD_GRANT_RE = re.compile(
    r"""grant_type['"]?\s*[:=]\s*['"]?password['"]?""",
    re.IGNORECASE,
)

# LastModifiedDate in WHERE clause (incremental watermark anti-pattern)
_LAST_MODIFIED_WHERE_RE = re.compile(
    r"""WHERE\s+.*?LastModifiedDate\s*>=?""",
    re.IGNORECASE | re.DOTALL,
)

# SOQL against KnowledgeArticleVersion without PublishStatus filter
_KAV_QUERY_RE = re.compile(
    r"""FROM\s+KnowledgeArticleVersion""",
    re.IGNORECASE,
)
_PUBLISH_STATUS_RE = re.compile(
    r"""PublishStatus\s*=\s*['"]Online['"]""",
    re.IGNORECASE,
)

# REST API nextRecordsUrl pagination (large-volume extraction anti-pattern)
_NEXT_RECORDS_RE = re.compile(
    r"""nextRecordsUrl""",
    re.IGNORECASE,
)

# Embedding/upsert call without prior html strip in same file (heuristic)
_EMBED_CALL_RE = re.compile(
    r"""embed|get_embedding|create\.embeddings|openai\.embed""",
    re.IGNORECASE,
)
_HTML_STRIP_RE = re.compile(
    r"""strip_html|html\.unescape|BeautifulSoup|TAG_RE\.sub|re\.sub.*<|html_to_text""",
    re.IGNORECASE,
)

# Known PII field API names in SELECT clauses
_PII_FIELDS = [
    "Email",
    "Phone",
    "MobilePhone",
    "HomePhone",
    "OtherPhone",
    "PersonEmail",
    "PersonMobilePhone",
    "SSN__c",
    "SocialSecurityNumber__c",
    "DateofBirth__c",
    "BirthDate",
    "MailingStreet",
    "MailingCity",
    "OtherStreet",
]

_SOQL_SELECT_RE = re.compile(
    r"""SELECT\s+(.*?)\s+FROM""",
    re.IGNORECASE | re.DOTALL,
)

# Watermark advance before write (heuristic: save_watermark before upsert/write)
_SAVE_WATERMARK_RE = re.compile(
    r"""save_watermark|update_watermark|set_watermark|last_sync\s*=""",
    re.IGNORECASE,
)
_UPSERT_RE = re.compile(
    r"""upsert|index\.upsert|\.add_texts|write_vectors|insert_vectors""",
    re.IGNORECASE,
)

# Source file extensions to inspect
_SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".yaml", ".yml", ".json", ".cls", ".soql"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_file(path: Path) -> str:
    """Read a file, returning empty string on decode error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _iter_source_files(root: Path) -> list[Path]:
    """Return source files under root that are worth scanning."""
    this_script = Path(__file__).resolve()
    results = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in _SOURCE_EXTENSIONS:
            # Skip node_modules, .git, __pycache__, build artifacts, and this checker itself
            parts = p.parts
            if any(part in (".git", "node_modules", "__pycache__", ".sfdx", ".sf") for part in parts):
                continue
            if p.resolve() == this_script:
                continue
            results.append(p)
    return results


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_password_oauth(content: str, path: Path) -> list[str]:
    """Flag username/password OAuth grant type patterns."""
    issues = []
    if _PASSWORD_GRANT_RE.search(content):
        issues.append(
            f"{path}: uses OAuth username/password grant type (grant_type=password). "
            "Production pipelines must use JWT Bearer flow with a certificate-based "
            "connected app. Username/password credentials in pipeline config can be "
            "logged or leaked."
        )
    return issues


def check_last_modified_watermark(content: str, path: Path) -> list[str]:
    """Flag LastModifiedDate used as an incremental extraction watermark."""
    issues = []
    if _LAST_MODIFIED_WHERE_RE.search(content):
        issues.append(
            f"{path}: SOQL WHERE clause uses LastModifiedDate for incremental "
            "watermark. LastModifiedDate can be frozen by Data Loader imports "
            "(setbulkheader). Use SystemModstamp instead — it is always advanced "
            "by any write, including system-initiated changes."
        )
    return issues


def check_knowledge_publish_status(content: str, path: Path) -> list[str]:
    """Flag KnowledgeArticleVersion queries missing PublishStatus = 'Online'."""
    issues = []
    for match in _KAV_QUERY_RE.finditer(content):
        # Check whether PublishStatus = 'Online' appears in the surrounding block
        # Use a 400-char window around the match for context
        start = max(0, match.start() - 400)
        end = min(len(content), match.end() + 200)
        context = content[start:end]
        if not _PUBLISH_STATUS_RE.search(context):
            issues.append(
                f"{path}: SOQL query against KnowledgeArticleVersion is missing "
                "WHERE PublishStatus = 'Online'. Without this filter, draft and "
                "archived article versions are included in the extraction, "
                "potentially indexing confidential draft content in the external "
                "vector store."
            )
    return issues


def check_rest_next_records_url(content: str, path: Path) -> list[str]:
    """Flag nextRecordsUrl pagination pattern (REST API large-volume anti-pattern)."""
    issues = []
    if _NEXT_RECORDS_RE.search(content):
        issues.append(
            f"{path}: uses nextRecordsUrl REST API pagination. For extractions "
            "exceeding ~10,000 records, use Bulk API v2 query jobs instead. "
            "REST API pagination consumes standard API call quota and provides no "
            "native asynchronous retry for large volumes."
        )
    return issues


def check_html_stripping_before_embed(content: str, path: Path) -> list[str]:
    """Flag files that call an embedding function without any HTML stripping."""
    issues = []
    if _EMBED_CALL_RE.search(content) and not _HTML_STRIP_RE.search(content):
        issues.append(
            f"{path}: calls an embedding function but contains no HTML stripping. "
            "If any source field is a Rich Text Area (e.g., KnowledgeArticleVersion.Body, "
            "Case.Description), HTML tags will be encoded as semantic tokens by the "
            "embedding model. Add HTML stripping before the embedding call."
        )
    return issues


def check_pii_fields_in_select(content: str, path: Path) -> list[str]:
    """Flag known PII field names appearing in SOQL SELECT projections."""
    issues = []
    for match in _SOQL_SELECT_RE.finditer(content):
        select_clause = match.group(1)
        for field in _PII_FIELDS:
            # Match as a word boundary to avoid false positives (e.g., EmailOptOut)
            pattern = re.compile(r"\b" + re.escape(field) + r"\b", re.IGNORECASE)
            if pattern.search(select_clause):
                issues.append(
                    f"{path}: SOQL SELECT includes known PII field '{field}'. "
                    "Verify that this field has a documented PII treatment in the "
                    "field classification matrix. If classified as 'scrub', remove "
                    "it from the SELECT projection entirely. If classified as "
                    "'pseudonymize', apply HMAC-SHA256 pseudonymization in-process "
                    "before any outbound network call."
                )
    return issues


def check_watermark_before_write(content: str, path: Path) -> list[str]:
    """Heuristic: flag if watermark save appears before upsert in same file."""
    issues = []
    save_match = _SAVE_WATERMARK_RE.search(content)
    upsert_match = _UPSERT_RE.search(content)
    if save_match and upsert_match:
        if save_match.start() < upsert_match.start():
            issues.append(
                f"{path}: watermark save/update appears to occur before the vector "
                "store upsert (based on line order heuristic). The SystemModstamp "
                "watermark must be advanced ONLY after the vector store write is "
                "confirmed. Advancing the watermark before the write causes silent "
                "data gaps if the write fails."
            )
    return issues


# ---------------------------------------------------------------------------
# Main check orchestrator
# ---------------------------------------------------------------------------

def check_sf_to_llm_data_pipelines(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    source_files = _iter_source_files(manifest_dir)

    if not source_files:
        if verbose:
            print(f"No source files found under {manifest_dir} — skipping file-level checks.")
        return issues

    if verbose:
        print(f"Scanning {len(source_files)} source file(s) under {manifest_dir}...")

    for path in source_files:
        content = _read_file(path)
        if not content:
            continue

        issues.extend(check_password_oauth(content, path))
        issues.extend(check_last_modified_watermark(content, path))
        issues.extend(check_knowledge_publish_status(content, path))
        issues.extend(check_rest_next_records_url(content, path))
        issues.extend(check_html_stripping_before_embed(content, path))
        issues.extend(check_pii_fields_in_select(content, path))
        issues.extend(check_watermark_before_write(content, path))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce-to-external-LLM pipeline code and configuration "
            "for common issues: PII in SOQL projections, wrong OAuth flow, "
            "LastModifiedDate watermarks, missing KnowledgeArticleVersion filters, "
            "REST API large-volume anti-patterns, missing HTML stripping, and "
            "watermark-before-write ordering."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the project to scan (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information during scanning.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_sf_to_llm_data_pipelines(manifest_dir, verbose=args.verbose)

    if not issues:
        print("No issues found.")
        return 0

    print(f"\nFound {len(issues)} issue(s):\n")
    for i, issue in enumerate(issues, start=1):
        print(f"[{i}] ISSUE: {issue}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
