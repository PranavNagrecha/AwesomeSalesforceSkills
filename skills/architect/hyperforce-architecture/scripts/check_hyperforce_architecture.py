#!/usr/bin/env python3
"""Static auditor for a Hyperforce migration architecture/runbook.

Walks a docs / runbook / architecture directory and flags concrete gaps
this skill cares about. Stdlib only — no pip dependencies.

Heuristics:

  1. Mentions Hyperforce migration without an IP-allowlist inventory section.
  2. References hard-coded First-Gen instance URLs (`naX.salesforce.com`,
     `csX.salesforce.com`, `euX.salesforce.com`, `apX.salesforce.com`,
     `umX.salesforce.com`) — these break post-migration.
  3. Talks about residency/sovereignty without distinguishing the two.
  4. Describes "active-active" or "customer-triggered failover" with
     Hyperforce — neither exists.
  5. Bundles Salesforce Functions decommission into the Hyperforce migration plan.
  6. Treats Government Cloud as a Hyperforce region option.
  7. Hyperforce migration plan with no post-cutover validation test plan.

Usage:
    python3 check_hyperforce_architecture.py [--manifest-dir path]

Default scans common roots: docs/, architecture/, adr/, runbooks/.
Exits 1 when issues are found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


SCAN_GLOBS = ("**/*.md", "**/*.txt", "**/*.adoc", "**/*.rst")
DEFAULT_ROOTS = ("docs", "architecture", "adr", "runbooks", ".")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Hyperforce migration documentation for common gaps.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory to scan (default: docs/, architecture/, adr/, runbooks/, current dir).",
    )
    return parser.parse_args()


def candidate_roots(arg: str | None) -> list[Path]:
    if arg:
        return [Path(arg)]
    found = [Path(name) for name in DEFAULT_ROOTS if Path(name).exists() and Path(name).is_dir()]
    return found or [Path(".")]


def iter_doc_files(roots: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for root in roots:
        for pattern in SCAN_GLOBS:
            for path in root.glob(pattern):
                if path in seen or not path.is_file():
                    continue
                if {"node_modules", ".git", "vendor", "__pycache__"} & set(path.parts):
                    continue
                seen.add(path)
                yield path


# ---------- pattern matchers ----------

HYPERFORCE_MENTION = re.compile(r"\bhyperforce\b", re.IGNORECASE)
MIGRATION_MENTION = re.compile(r"\b(migration|migrate|cutover|move to hyperforce)\b", re.IGNORECASE)

ALLOWLIST_SECTION = re.compile(
    r"\b(allowlist|allow[\s-]?list|whitelist|ip\s*range|firewall\s*rule|cidr)\b",
    re.IGNORECASE,
)

# First-Gen instance URL patterns: na32, cs1, eu5, ap22, um1, etc.
FIRSTGEN_URL = re.compile(
    r"\b(na|cs|eu|ap|um)\d{1,3}\.salesforce\.com\b",
    re.IGNORECASE,
)

RESIDENCY_MENTION = re.compile(r"\b(residency|data\s*reside|stored\s*in\s*region)\b", re.IGNORECASE)
SOVEREIGNTY_DISTINCT = re.compile(
    r"\b(sovereignty|legal\s*process|schrems|distinct\s*from\s*sovereignty|residency.{0,40}not\s*sovereignty|sovereignty.{0,40}not\s*residency)\b",
    re.IGNORECASE,
)

ACTIVE_ACTIVE_CLAIM = re.compile(
    r"\b(active[\s-]active|customer[\s-]triggered\s*failover|customer[\s-]controlled\s*failover|orchestrate\s*failover\s*across\s*hyperforce)\b",
    re.IGNORECASE,
)

FUNCTIONS_BUNDLED = re.compile(
    r"\bsalesforce\s*functions?\b[\s\S]{0,200}\b(retire|decommission|replace)",
    re.IGNORECASE,
)
HYPERFORCE_FUNCTIONS_LINK = re.compile(
    r"\bhyperforce\b[\s\S]{0,400}\bfunction[s]?\b",
    re.IGNORECASE,
)

GOVCLOUD_AS_REGION = re.compile(
    r"\b(government\s*cloud|govcloud|fedramp)\b[\s\S]{0,80}\b(hyperforce\s*region|region\s*option)",
    re.IGNORECASE,
)

VALIDATION_PLAN = re.compile(
    r"\b(validation\s*test|post[-\s]migration\s*test|cutover\s*validation|smoke\s*test\s*plan|post[-\s]cutover\s*test)\b",
    re.IGNORECASE,
)


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = path.as_posix()
    issues: list[str] = []

    if not HYPERFORCE_MENTION.search(text):
        return issues
    is_migration_doc = bool(MIGRATION_MENTION.search(text))

    if is_migration_doc and not ALLOWLIST_SECTION.search(text):
        issues.append(
            f"{rel}: Hyperforce migration plan with no IP-allowlist inventory. "
            "Customer-side firewalls, middleware, and Setup allowlists must be listed before cutover."
        )

    if is_migration_doc and not VALIDATION_PLAN.search(text):
        issues.append(
            f"{rel}: Hyperforce migration plan with no post-cutover validation test plan. "
            "Add a named test plan (APIs, SSO, integrations, scheduled jobs, partner orgs)."
        )

    for match in FIRSTGEN_URL.finditer(text):
        issues.append(
            f"{rel}: hard-coded First-Generation instance URL `{match.group(0)}`. "
            "Replace with `*.my.salesforce.com` — instance URLs do not survive migration."
        )

    if RESIDENCY_MENTION.search(text) and not SOVEREIGNTY_DISTINCT.search(text):
        issues.append(
            f"{rel}: discusses residency without distinguishing sovereignty. "
            "State explicitly that Hyperforce regions deliver at-rest residency, not legal-process sovereignty."
        )

    if ACTIVE_ACTIVE_CLAIM.search(text):
        issues.append(
            f"{rel}: claims active-active or customer-controlled failover for Hyperforce. "
            "Hyperforce manages failover at platform level — customers cannot trigger or orchestrate."
        )

    if FUNCTIONS_BUNDLED.search(text) and HYPERFORCE_FUNCTIONS_LINK.search(text):
        issues.append(
            f"{rel}: bundles Salesforce Functions decommission with the Hyperforce migration plan. "
            "These are unrelated programs with separate timelines."
        )

    if GOVCLOUD_AS_REGION.search(text):
        issues.append(
            f"{rel}: treats Government Cloud as a Hyperforce region option. "
            "Government Cloud is a separate licensed product, not a commercial Hyperforce region."
        )

    return issues


def main() -> int:
    args = parse_args()
    roots = candidate_roots(args.manifest_dir)
    files = list(iter_doc_files(roots))
    if not files:
        print(f"No documentation files found under {[str(r) for r in roots]}.")
        return 0

    relevant = 0
    issues: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if HYPERFORCE_MENTION.search(text):
            relevant += 1
        issues.extend(check_file(path))

    if not relevant:
        print(f"OK: scanned {len(files)} files; none mention Hyperforce.")
        return 0

    if not issues:
        print(f"OK: {relevant} Hyperforce-related file(s) scanned, no issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
