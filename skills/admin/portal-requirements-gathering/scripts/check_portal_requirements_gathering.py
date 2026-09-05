#!/usr/bin/env python3
"""Checker script for the Portal Requirements Gathering skill.

Two artefacts, two modes. Stdlib only — no pip dependencies.

Catalogue mode (``--file`` / ``--manifest-dir``) lints the requirements catalogue
described in ``references/worked-examples.md`` section 3:

- every row carries id, statement, persona, licence_implication, access_mechanism,
  content_type, auth, downstream, owner and status
- ids are unique within the file
- licence_implication, access_mechanism, content_type, auth and status each sit in
  their allowed set
- a ``downstream`` value that looks like a repo path resolves on disk
- every guest-facing row (guest licence, guest auth, or a public/guest mechanism)
  names a reviewer in ``guest_review``

Document mode (``--doc``) lints the narrative workshop document produced from
``templates/portal-requirements-gathering-template.md``.

The YAML read here is a deliberately small subset: a top-level ``requirements:``
key holding a list of flat mappings, with ``#`` comments, quoted or bare scalars,
and ``>``/``|`` block scalars. Anything richer (anchors, nested mappings inside a
row, flow sequences) is reported rather than silently accepted.

Exit codes: 0 clean, 1 findings, 2 usage error.

Usage:
    python3 check_portal_requirements_gathering.py --file requirements.yaml
    python3 check_portal_requirements_gathering.py --manifest-dir requirements/
    python3 check_portal_requirements_gathering.py --doc requirements.md [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint a portal requirements catalogue (YAML) or a portal requirements "
            "workshop document (Markdown)."
        ),
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Path to a portal requirements catalogue (YAML). See references/worked-examples.md.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Directory to scan for requirements catalogues (*.yaml, *.yml).",
    )
    parser.add_argument(
        "--doc",
        default=None,
        help="Path to the narrative portal requirements Markdown document to check.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root used to resolve 'downstream' repo paths. "
            "Defaults to the SfSkills checkout this script lives in."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Document mode only: treat warnings as errors.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Requirements catalogue vocabulary
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = (
    "id",
    "statement",
    "persona",
    "licence_implication",
    "access_mechanism",
    "content_type",
    "auth",
    "downstream",
    "owner",
    "status",
)

# Licence names follow the rows in the App Limits cheat sheet "Total API Request
# Allocations" table (Customer Community / ... Login / ... Plus / ... Plus Login /
# Partner Community / Partner Community Login / External Identity), plus the
# unlicensed guest visitor and internal Salesforce users who are site members.
ALLOWED_LICENCES = {
    "guest",
    "external-identity",
    "customer-community",
    "customer-community-login",
    "customer-community-plus",
    "customer-community-plus-login",
    "partner-community",
    "partner-community-login",
    "external-apps",
    "internal-salesforce",
}

ALLOWED_MECHANISMS = {
    "not-applicable",
    "guest-public-page",
    "external-owd",
    "ownership",
    "sharing-set",
    "sharing-rule",
    "account-role-hierarchy",
    "partner-super-user",
    "apex-managed-sharing",
    "manual-share",
    "guest-sharing-rule",
    "data-category-visibility",
    "object-permission-only",
}

ALLOWED_CONTENT_TYPES = {
    "record",
    "knowledge",
    "cms",
    "file",
    "external-object",
    "static-page",
}

ALLOWED_AUTH = {
    "self-registration",
    "sso",
    "admin-provisioned",
    "login-only",
    "guest",
}

ALLOWED_STATUS = {
    "draft",
    "in-review",
    "approved",
    "deferred",
    "out-of-scope",
}

GUEST_LICENCES = {"guest"}
GUEST_MECHANISMS = {"guest-public-page", "guest-sharing-rule"}

REPO_PATH_PREFIXES = ("skills/", "agents/", "templates/", "standards/", "evals/", "commands/")


# ---------------------------------------------------------------------------
# Minimal YAML subset reader
# ---------------------------------------------------------------------------

def _strip_scalar(raw: str) -> str:
    """Strip an inline comment and surrounding quotes from a scalar value."""
    value = raw.strip()
    if value.startswith(("'", '"')):
        quote = value[0]
        end = value.find(quote, 1)
        if end != -1:
            return value[1:end]
        return value[1:]
    # Bare scalar: an unquoted ' #' starts a comment.
    hash_at = value.find(" #")
    if hash_at != -1:
        value = value[:hash_at]
    return value.strip()


def read_catalogue(text: str) -> tuple[list[dict[str, str]], list[str]]:
    """Parse the requirements catalogue subset. Returns (rows, parse issues)."""
    issues: list[str] = []
    rows: list[dict[str, str]] = []

    lines = text.splitlines()
    in_requirements = False
    current: dict[str, str] | None = None
    block_key: str | None = None
    block_indent = 0
    block_lines: list[str] = []

    def close_block() -> None:
        nonlocal block_key, block_lines
        if current is not None and block_key is not None:
            current[block_key] = " ".join(part.strip() for part in block_lines).strip()
        block_key = None
        block_lines = []

    for number, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Inside a block scalar: keep consuming while indentation holds.
        if block_key is not None:
            indent = len(line) - len(line.lstrip())
            if not stripped:
                block_lines.append("")
                continue
            if indent > block_indent:
                block_lines.append(stripped)
                continue
            close_block()

        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        if not in_requirements:
            if indent == 0 and stripped.rstrip() == "requirements:":
                in_requirements = True
            continue

        # A new top-level key ends the requirements list.
        if indent == 0 and not stripped.startswith("-"):
            if current is not None:
                rows.append(current)
                current = None
            in_requirements = False
            continue

        if stripped.startswith("- "):
            if current is not None:
                rows.append(current)
            current = {}
            stripped = stripped[2:].strip()
        elif stripped == "-":
            if current is not None:
                rows.append(current)
            current = {}
            continue

        if current is None:
            issues.append(f"line {number}: key outside a requirements row: {stripped}")
            continue

        if ":" not in stripped:
            issues.append(f"line {number}: unparsable line in requirements row: {stripped}")
            continue

        key, _, raw_value = stripped.partition(":")
        key = key.strip()
        raw_value = raw_value.strip()

        if raw_value in (">", "|", ">-", "|-", ">+", "|+"):
            block_key = key
            block_indent = indent
            block_lines = []
            continue

        if raw_value.startswith("[") or raw_value.startswith("{"):
            issues.append(
                f"line {number}: flow collections are outside the supported subset "
                f"(key '{key}'). Write one scalar per row field."
            )
            continue

        current[key] = _strip_scalar(raw_value)

    close_block()
    if current is not None:
        rows.append(current)

    return rows, issues


def default_repo_root() -> Path:
    """Walk up from this script to the SfSkills checkout root."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "AGENT_RULES.md").exists() and (parent / "skills").is_dir():
            return parent
    return Path.cwd()


# ---------------------------------------------------------------------------
# Catalogue checks
# ---------------------------------------------------------------------------

def _check_allowed(row: dict[str, str], row_id: str, field: str, allowed: set[str]) -> list[str]:
    value = row.get(field, "").strip()
    if not value or value in allowed:
        return []
    return [
        f"{row_id}: {field} '{value}' is not an allowed value. "
        f"Allowed: {', '.join(sorted(allowed))}."
    ]


def check_catalogue(rows: list[dict[str, str]], repo_root: Path) -> list[str]:
    """Lint the parsed requirements catalogue rows."""
    issues: list[str] = []

    if not rows:
        return [
            "EMPTY: no requirements rows found. The catalogue needs a top-level "
            "'requirements:' key holding at least one row — see references/worked-examples.md."
        ]

    seen_ids: dict[str, int] = {}

    for position, row in enumerate(rows, start=1):
        row_id = row.get("id", "").strip() or f"row {position} (no id)"

        missing = [field for field in REQUIRED_FIELDS if not row.get(field, "").strip()]
        if missing:
            issues.append(
                f"{row_id}: missing required field(s): {', '.join(missing)}. "
                "Every row needs a persona, the licence it implies, the access mechanism "
                "that satisfies it, and a downstream owner."
            )

        identifier = row.get("id", "").strip()
        if identifier:
            if identifier in seen_ids:
                issues.append(
                    f"{identifier}: duplicate id — also used by row {seen_ids[identifier]}. "
                    "Ids must be unique so downstream skills can cite one row."
                )
            else:
                seen_ids[identifier] = position

        issues.extend(_check_allowed(row, row_id, "licence_implication", ALLOWED_LICENCES))
        issues.extend(_check_allowed(row, row_id, "access_mechanism", ALLOWED_MECHANISMS))
        issues.extend(_check_allowed(row, row_id, "content_type", ALLOWED_CONTENT_TYPES))
        issues.extend(_check_allowed(row, row_id, "auth", ALLOWED_AUTH))
        issues.extend(_check_allowed(row, row_id, "status", ALLOWED_STATUS))

        downstream = row.get("downstream", "").strip()
        if downstream.startswith(REPO_PATH_PREFIXES):
            target = repo_root / downstream
            if not target.exists():
                issues.append(
                    f"{row_id}: downstream '{downstream}' does not resolve under {repo_root}. "
                    "Cite a real skill, agent, or template path, or name a person instead."
                )

        licence = row.get("licence_implication", "").strip()
        auth = row.get("auth", "").strip()
        mechanism = row.get("access_mechanism", "").strip()
        guest_facing = (
            licence in GUEST_LICENCES
            or auth == "guest"
            or mechanism in GUEST_MECHANISMS
        )
        if guest_facing and not row.get("guest_review", "").strip():
            issues.append(
                f"{row_id}: guest-facing row (licence '{licence or 'n/a'}', auth "
                f"'{auth or 'n/a'}', mechanism '{mechanism or 'n/a'}') has no 'guest_review'. "
                "Guest rows expose data to unauthenticated visitors — name the security "
                "reviewer who signed the row before handing it to the build team."
            )

    return issues


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_contact_reason_analysis(text: str) -> list[str]:
    """Verify that a contact reason analysis section exists and contains data."""
    issues: list[str] = []
    if not re.search(r"contact reason", text, re.IGNORECASE):
        issues.append(
            "MISSING: No 'Contact Reason' section found. "
            "A 60–90 day contact reason analysis is required before feature scoping."
        )
        return issues

    # Look for the Answers/Status/Actions categorisation
    if not re.search(r"answers|status|action", text, re.IGNORECASE):
        issues.append(
            "INCOMPLETE: Contact reason section found but does not categorise reasons "
            "as Answers / Status / Actions. Add this breakdown."
        )

    # Look for at least one ranked table row carrying a real number
    rows = re.findall(r"\|\s*\d+\s*\|", text)
    if not rows:
        issues.append(
            "INCOMPLETE: Contact reason section appears to have no ranked data rows. "
            "Populate the top contact reasons table with real data before the requirements workshop."
        )

    return issues


def check_access_architecture(text: str) -> list[str]:
    """Verify that an access architecture decision is recorded."""
    issues: list[str] = []
    if not re.search(r"access architecture", text, re.IGNORECASE):
        issues.append(
            "MISSING: No 'Access Architecture' section found. "
            "The portal access model (public / authenticated / hybrid) must be locked in requirements."
        )
        return issues

    # Check that one of the three models is chosen
    if not re.search(r"\b(public|authenticated|hybrid)\b", text, re.IGNORECASE):
        issues.append(
            "INCOMPLETE: Access Architecture section found but no decision keyword detected "
            "(public / authenticated / hybrid). Record the decision explicitly."
        )

    return issues


def check_license_selection(text: str) -> list[str]:
    """Verify that a license selection is documented."""
    issues: list[str] = []
    license_keywords = [
        "customer community",
        "partner community",
        "external apps",
        "community plus",
    ]
    found = any(re.search(kw, text, re.IGNORECASE) for kw in license_keywords)
    if not found:
        issues.append(
            "MISSING: No license type recorded (Customer Community, Customer Community Plus, "
            "Partner Community, or External Apps). License selection must be locked in requirements."
        )
    return issues


def check_top_jobs(text: str) -> list[str]:
    """Verify that top-3 jobs are defined with success criteria."""
    issues: list[str] = []

    if not re.search(r"job\s*(1|2|3|statement|high.volume)", text, re.IGNORECASE):
        issues.append(
            "MISSING: No 'Top-3 Jobs' section found. "
            "Define the three highest-volume customer jobs before any feature scoping."
        )
        return issues

    # Check for success criterion per job
    success_hits = len(re.findall(r"success criterion", text, re.IGNORECASE))
    if success_hits < 3:
        issues.append(
            f"INCOMPLETE: Found {success_hits} 'Success Criterion' reference(s); expected 3. "
            "Each of the top-3 jobs must have a measurable success criterion."
        )

    return issues


def check_content_taxonomy(text: str) -> list[str]:
    """Verify that a content taxonomy section is present with at least one owner."""
    issues: list[str] = []
    if not re.search(r"content taxonomy|content type|content owner", text, re.IGNORECASE):
        issues.append(
            "MISSING: No content taxonomy or content ownership section found. "
            "Every content type (Knowledge Articles, documents, assets) must have a named owner "
            "and review cadence."
        )
    return issues


def check_deferred_features(text: str) -> list[str]:
    """Verify that social and gamification features are explicitly deferred."""
    issues: list[str] = []
    if not re.search(r"deferred|phase 2", text, re.IGNORECASE):
        issues.append(
            "MISSING: No 'Deferred' or 'Phase 2' section found. "
            "Social and gamification features must be explicitly deferred until the core "
            "deflection loop is validated."
        )
        return issues

    social_terms = ["idea exchange", "gamification", "leaderboard", "badges", "forum", "chatter"]
    missing_deferrals = [
        term for term in social_terms
        if not re.search(term, text, re.IGNORECASE)
    ]
    if missing_deferrals:
        issues.append(
            "INCOMPLETE: Deferred section found but these social/gamification items were not "
            f"explicitly addressed: {', '.join(missing_deferrals)}. "
            "Record each one as deferred or out-of-scope to prevent scope creep."
        )

    return issues


def check_sign_off(text: str) -> list[str]:
    """Verify that a sign-off section exists."""
    issues: list[str] = []
    if not re.search(r"sign.off|signed off|approver", text, re.IGNORECASE):
        issues.append(
            "MISSING: No sign-off section found. "
            "Requirements must be signed off by both a business stakeholder and a technical lead "
            "before build begins."
        )
    return issues


def check_deflection_baseline(text: str) -> list[str]:
    """Verify that a deflection baseline and target are recorded."""
    issues: list[str] = []
    if not re.search(r"deflection|containment rate|self.service rate", text, re.IGNORECASE):
        issues.append(
            "MISSING: No deflection baseline or target found. "
            "Record the current self-service containment rate and a measurable phase 1 target."
        )
    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_checks(text: str) -> list[str]:
    """Run all checks and return a flat list of issue strings."""
    all_issues: list[str] = []
    all_issues.extend(check_contact_reason_analysis(text))
    all_issues.extend(check_access_architecture(text))
    all_issues.extend(check_license_selection(text))
    all_issues.extend(check_top_jobs(text))
    all_issues.extend(check_content_taxonomy(text))
    all_issues.extend(check_deferred_features(text))
    all_issues.extend(check_deflection_baseline(text))
    all_issues.extend(check_sign_off(text))
    return all_issues


def lint_catalogue_file(path: Path, repo_root: Path) -> list[str]:
    """Parse and lint one catalogue file; returns prefixed issue strings."""
    text = path.read_text(encoding="utf-8")
    rows, parse_issues = read_catalogue(text)
    issues = [f"PARSE: {issue}" for issue in parse_issues]
    issues.extend(check_catalogue(rows, repo_root))
    return [f"{path}: {issue}" for issue in issues]


def main() -> int:
    args = parse_args()

    modes = [bool(args.file), bool(args.manifest_dir), bool(args.doc)]
    if sum(modes) == 0:
        print(
            "Nothing to check. Pass one of:\n"
            "  --file <requirements.yaml>      lint a requirements catalogue\n"
            "  --manifest-dir <dir>            lint every *.yaml / *.yml catalogue in a folder\n"
            "  --doc <requirements.md>         lint the narrative workshop document",
            file=sys.stderr,
        )
        return 2
    if sum(modes) > 1:
        print(
            "ERROR: pass exactly one of --file, --manifest-dir, or --doc.",
            file=sys.stderr,
        )
        return 2

    repo_root = Path(args.repo_root).resolve() if args.repo_root else default_repo_root()

    # ---- Catalogue modes --------------------------------------------------
    if args.file or args.manifest_dir:
        if args.file:
            catalogue_path = Path(args.file)
            if not catalogue_path.is_file():
                print(f"ERROR: catalogue not found: {catalogue_path}", file=sys.stderr)
                return 2
            targets = [catalogue_path]
        else:
            manifest_dir = Path(args.manifest_dir)
            if not manifest_dir.is_dir():
                print(f"ERROR: not a directory: {manifest_dir}", file=sys.stderr)
                return 2
            targets = sorted(
                path
                for path in manifest_dir.rglob("*")
                if path.is_file() and path.suffix in {".yaml", ".yml"}
            )
            if not targets:
                print(
                    f"ERROR: no *.yaml or *.yml requirements catalogue found under {manifest_dir}",
                    file=sys.stderr,
                )
                return 2

        issues: list[str] = []
        for target in targets:
            issues.extend(lint_catalogue_file(target, repo_root))

        if not issues:
            noun = "catalogue" if len(targets) == 1 else "catalogues"
            print(f"All checks passed. {len(targets)} requirements {noun} clean.")
            return 0

        for issue in issues:
            print(f"ERROR: {issue}", file=sys.stderr)
        print(
            f"\n{len(issues)} issue(s) found across {len(targets)} file(s). "
            "Fix them before handing the catalogue to admin/experience-cloud-site-setup.",
            file=sys.stderr,
        )
        return 1

    # ---- Document mode ----------------------------------------------------
    doc_path = Path(args.doc)
    if not doc_path.is_file():
        print(f"ERROR: Document not found: {doc_path}", file=sys.stderr)
        return 2

    text = doc_path.read_text(encoding="utf-8")
    findings = run_checks(text)

    if not findings:
        print("All checks passed. Portal requirements document looks complete.")
        return 0

    for finding in findings:
        print(f"WARN: {finding}", file=sys.stderr)

    if args.strict:
        print(
            f"\n{len(findings)} issue(s) found. Resolve before proceeding to build.",
            file=sys.stderr,
        )
        return 1

    print(
        f"\n{len(findings)} issue(s) found. Review the warnings above before marking "
        "requirements complete.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
