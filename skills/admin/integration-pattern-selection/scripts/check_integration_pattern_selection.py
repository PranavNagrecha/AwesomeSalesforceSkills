#!/usr/bin/env python3
"""Audit integration metadata, and lint integration pattern decision records.

Two modes, both stdlib-only:

  --manifest-dir DIR       Scan retrieved metadata for hard-coded endpoints
                           (RemoteSiteSetting), Named Credentials still on the Legacy
                           type, platform event definitions left on the
                           PublishImmediately default, and Apex that calls out from a
                           trigger or holds a callout URL as a literal.

  --decision-record FILE   Lint one record written from
                           templates/integration-pattern-selection-template.md:
                           required fields present and non-empty, decision-tree
                           citations in the documented
                           `integration-pattern-selection.md Q<n>` form, direction and
                           chosen_pattern inside the allowed sets, every rejected
                           alternative carrying a reason, an auth block naming a Named
                           Credential, and an ISO review_date.

Both emit the same JSON envelope: {"score", "findings", "summary"}.
Exit code is 1 when there is at least one finding, 0 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

# --- decision-record linting -------------------------------------------------
# The record shape is defined in templates/integration-pattern-selection-template.md
# and worked in references/decision-record-examples.md.
REQUIRED_RECORD_FIELDS = (
    "record_id",
    "requirement",
    "direction",
    "volume",
    "latency",
    "idempotency",
    "who_knows_ids",
    "ordering",
    "chosen_pattern",
    "tree_questions_cited",
    "rejected",
    "auth",
    "owner",
    "review_date",
)

ALLOWED_DIRECTIONS = {
    "salesforce_to_external",
    "external_to_salesforce",
    "bidirectional_or_decoupled",
}

# Mirrors the Pattern summary table in
# standards/decision-trees/integration-pattern-selection.md.
ALLOWED_PATTERNS = {
    "rest_api",
    "rest_composite",
    "bulk_api_2",
    "custom_rest",
    "apex_callout_named_credential",
    "continuation",
    "queueable_callout",
    "platform_event",
    "change_data_capture",
    "pub_sub_api",
    "salesforce_connect_odata",
    "streaming_api_pushtopic",
    "outbound_message",
    "mulesoft_ipaas",
}
# The tree's anti-patterns section rules both of these out for new work.
LEGACY_PATTERNS = {"streaming_api_pushtopic", "outbound_message"}

ALLOWED_LATENCY = {"realtime", "near_realtime", "batch"}
ALLOWED_IDEMPOTENCY = {
    "designed_idempotent",
    "idempotency_key_required",
    "not_guaranteed",
}
ALLOWED_WHO_KNOWS_IDS = {"salesforce_ids", "external_key", "neither"}
ALLOWED_ORDERING = {"strict", "at_least_once", "not_required"}

# A citation must name the tree and a numbered question in it, e.g.
# "integration-pattern-selection.md Q7".
TREE_STEP_RE = re.compile(r"\bintegration-pattern-selection\.md\s+Q\d+\b")
FRONT_MATTER_RE = re.compile(r"^\s*---\s*$", re.MULTILINE)
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$")
LIST_ITEM_RE = re.compile(r"^\s*-\s*(.*)$")
NESTED_KEY_RE = re.compile(r"^\s+([A-Za-z_][A-Za-z0-9_]*):(.*)$")
REVIEW_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# --- metadata scanning -------------------------------------------------------
NC_TYPE_RE = re.compile(r"<namedCredentialType>\s*([A-Za-z0-9_]+)\s*</namedCredentialType>")
PUBLISH_BEHAVIOR_RE = re.compile(r"<publishBehavior>\s*([A-Za-z0-9_]+)\s*</publishBehavior>")
TRIGGER_DECL_RE = re.compile(r"\btrigger\s+\w+\s+on\s+([A-Za-z0-9_]+)", re.IGNORECASE)
HTTP_USE_RE = re.compile(r"\bnew\s+Http\s*\(\s*\)|\bHttpRequest\s*\(|\bhttp\.send\s*\(", re.IGNORECASE)
LITERAL_ENDPOINT_RE = re.compile(r"setEndpoint\s*\(\s*'(?!callout:)(https?://[^']+)'", re.IGNORECASE)
IS_TEST_RE = re.compile(r"@istest", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan retrieved integration metadata for endpoint and event-publish risks, "
            "or lint an integration pattern decision record."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of retrieved Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--decision-record",
        default=None,
        help=(
            "Path to a decision record (markdown with a YAML front-matter block) to lint "
            "instead of scanning metadata."
        ),
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_front_matter(text: str) -> list[str] | None:
    """Return the record's YAML lines, or None if the file has no record block.

    Two shapes are accepted: a bare `---` front-matter block at the top of a real record
    file, and a ```yaml fenced block, which is how the template and the worked examples
    ship it. The fenced form is checked first, because a template also contains markdown
    `---` horizontal rules that would otherwise be mistaken for front matter.
    """
    lines = text.splitlines()

    for index, line in enumerate(lines):
        if line.strip().lower() in ("```yaml", "```yml"):
            for close in range(index + 1, len(lines)):
                if lines[close].strip().startswith("```"):
                    body = lines[index + 1: close]
                    # The block usually carries its own `---` delimiters; drop them.
                    while body and FRONT_MATTER_RE.match(body[0]):
                        body = body[1:]
                    while body and FRONT_MATTER_RE.match(body[-1]):
                        body = body[:-1]
                    return body
            return None

    fence_indexes = [i for i, line in enumerate(lines) if FRONT_MATTER_RE.match(line)]
    if len(fence_indexes) < 2:
        return None
    return lines[fence_indexes[0] + 1: fence_indexes[1]]


def parse_record_block(block: list[str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Flat parse of the record's top-level keys and their nested lines.

    Deliberately not a YAML parser: this script is stdlib-only, and the record shape is
    fixed and shallow. Returns (scalar-ish values keyed by top-level name, raw nested
    lines keyed by top-level name).
    """
    scalars: dict[str, str] = {}
    nested: dict[str, list[str]] = {}
    current: str | None = None
    for raw in block:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        match = TOP_LEVEL_KEY_RE.match(raw)
        if match and not raw.startswith((" ", "\t")):
            current = match.group(1)
            value = match.group(2)
            # Strip a trailing `# ...` placeholder comment so the blank template reports
            # its unfilled fields instead of counting the hint as a value.
            if "#" in value:
                value = value.split("#", 1)[0]
            scalars[current] = value.strip().strip("\"'")
            nested[current] = []
            continue
        if current is not None:
            nested[current].append(raw)
    return scalars, nested


def nested_scalar(nested_lines: list[str], key: str) -> str:
    """Pull one `key: value` out of an indented block, with placeholder comments stripped."""
    for raw in nested_lines:
        match = NESTED_KEY_RE.match(raw)
        if match and match.group(1) == key:
            value = match.group(2)
            if "#" in value:
                value = value.split("#", 1)[0]
            return value.strip().strip("\"'")
    return ""


def check_enum(
    findings: list[str],
    path: Path,
    field: str,
    value: str,
    allowed: set[str],
    severity: str = "MEDIUM",
) -> None:
    if not value:
        return
    if value not in allowed:
        findings.append(
            f"{severity} {path}: `{field}` is `{value}`, which is not one of "
            f"{', '.join(sorted(allowed))}"
        )


def lint_decision_record(path: Path) -> tuple[list[str], str]:
    """Lint one decision record. Returns (findings, summary)."""
    if not path.exists():
        return ([f"HIGH {path}: decision record not found"], "Linted 0 decision records.")

    block = extract_front_matter(read_text(path))
    if block is None:
        return (
            [
                f"HIGH {path}: no `---` front-matter block found; copy "
                f"templates/integration-pattern-selection-template.md"
            ],
            "Linted 1 decision record; the record shape was missing entirely.",
        )

    scalars, nested = parse_record_block(block)
    findings: list[str] = []

    # 1. Every required field present, and not left as an empty placeholder.
    for field in REQUIRED_RECORD_FIELDS:
        if field not in scalars:
            findings.append(
                f"HIGH {path}: required field `{field}` is missing from the decision record"
            )
        elif not scalars[field] and not [ln for ln in nested[field] if ln.strip()]:
            findings.append(
                f"MEDIUM {path}: required field `{field}` is present but empty; fill it or "
                f"delete the record"
            )

    # 2. Tree citations must resolve to a numbered question in the integration tree.
    citation_lines = [
        ln for ln in nested.get("tree_questions_cited", []) if LIST_ITEM_RE.match(ln)
    ]
    if not citation_lines:
        findings.append(
            f"HIGH {path}: `tree_questions_cited` lists no steps; every branch of the choice "
            f"must cite a tree question number"
        )
    else:
        for line in citation_lines:
            if not TREE_STEP_RE.search(line):
                findings.append(
                    f"MEDIUM {path}: citation does not match `integration-pattern-selection.md "
                    f"Q<n>`: {line.strip()[:80]}"
                )

    # 3. Direction and chosen_pattern must sit inside the allowed sets.
    direction = scalars.get("direction", "")
    check_enum(findings, path, "direction", direction, ALLOWED_DIRECTIONS, "HIGH")
    pattern = scalars.get("chosen_pattern", "")
    check_enum(findings, path, "chosen_pattern", pattern, ALLOWED_PATTERNS, "HIGH")
    if pattern in LEGACY_PATTERNS:
        findings.append(
            f"REVIEW {path}: `chosen_pattern` is `{pattern}`, which the decision tree's "
            f"anti-patterns section rules out for new work; the record must say why the "
            f"migration is being deferred"
        )
    check_enum(findings, path, "latency", scalars.get("latency", ""), ALLOWED_LATENCY)
    check_enum(
        findings, path, "idempotency", scalars.get("idempotency", ""), ALLOWED_IDEMPOTENCY
    )
    check_enum(
        findings, path, "who_knows_ids", scalars.get("who_knows_ids", ""), ALLOWED_WHO_KNOWS_IDS
    )
    check_enum(findings, path, "ordering", scalars.get("ordering", ""), ALLOWED_ORDERING)

    # 4. Volume must carry a per-day number, because that is what Q5 is decided on.
    per_day = nested_scalar(nested.get("volume", []), "per_day")
    if not per_day:
        findings.append(
            f"HIGH {path}: `volume.per_day` is missing or empty; Q5 routes on a measured "
            f"24-hour number"
        )
    elif not re.fullmatch(r"[\d_,]+", per_day):
        findings.append(
            f"MEDIUM {path}: `volume.per_day` is not a number: {per_day[:40]}"
        )

    # 5. Every rejected alternative needs a reason, not just a name.
    alternatives = 0
    reasons = 0
    for raw in nested.get("rejected", []):
        stripped = raw.strip()
        if stripped.startswith("- alternative:") or stripped.startswith("-alternative:"):
            alternatives += 1
            if not stripped.split(":", 1)[1].strip():
                findings.append(f"MEDIUM {path}: a `rejected` entry names no alternative")
        elif stripped.startswith("reason:"):
            reasons += 1
            if not stripped.split(":", 1)[1].strip():
                findings.append(f"MEDIUM {path}: a `rejected` entry has an empty `reason:`")
    if alternatives == 0:
        findings.append(
            f"HIGH {path}: no rejected alternatives recorded; a choice with nothing rejected "
            f"is not a decision"
        )
    elif reasons < alternatives:
        findings.append(
            f"HIGH {path}: {alternatives} rejected alternative(s) but only {reasons} "
            f"reason(s); each rejected alternative must say why it loses"
        )

    # 6. Auth: a Named Credential is mandatory, per the tree's Named Credentials section.
    named_credential = nested_scalar(nested.get("auth", []), "named_credential")
    if not named_credential:
        findings.append(
            f"HIGH {path}: `auth.named_credential` is empty; the decision tree's "
            f"'Named Credentials - always, not sometimes' section makes this mandatory"
        )
    elif named_credential.lower().startswith(("http://", "https://")):
        findings.append(
            f"HIGH {path}: `auth.named_credential` holds a raw URL ({named_credential[:40]}); "
            f"it must name a Named Credential, not an endpoint"
        )

    # 7. review_date must be a real ISO date, not a placeholder.
    review_date = scalars.get("review_date", "")
    if review_date and not REVIEW_DATE_RE.match(review_date):
        findings.append(
            f"LOW {path}: `review_date` is not an ISO YYYY-MM-DD date: {review_date}"
        )

    summary = (
        f"Linted 1 decision record ({len(REQUIRED_RECORD_FIELDS)} required fields, "
        f"{len(citation_lines)} tree citation(s), {alternatives} rejected alternative(s)); "
        f"{len(findings)} finding(s)."
    )
    return findings, summary


def scan_metadata(root: Path) -> tuple[list[str], str]:
    """Scan retrieved metadata for endpoint, credential and event-publish risks."""
    findings: list[str] = []

    remote_sites = sorted(root.rglob("*.remoteSite*"))
    for path in remote_sites:
        findings.append(
            f"REVIEW {path}: Remote Site Setting found; this is a hard-coded endpoint "
            f"hostname whose credential lives somewhere else. Confirm where the secret is "
            f"stored and migrate to a Named Credential + External Credential"
        )

    named_credentials = sorted(root.rglob("*.namedCredential*"))
    for path in named_credentials:
        match = NC_TYPE_RE.search(read_text(path))
        nc_type = match.group(1) if match else ""
        if nc_type == "Legacy":
            findings.append(
                f"REVIEW {path}: namedCredentialType is Legacy, so it predates the External "
                f"Credential schema; rotating its secret means redeploying metadata"
            )
        elif not nc_type:
            findings.append(
                f"LOW {path}: no <namedCredentialType> element; the field is available in "
                f"API version 56.0 and later and should be set explicitly"
            )

    event_objects = [
        path for path in sorted(root.rglob("*.object-meta.xml")) if "__e" in path.name
    ]
    for path in event_objects:
        text = read_text(path)
        match = PUBLISH_BEHAVIOR_RE.search(text)
        if not match:
            findings.append(
                f"HIGH {path}: platform event defines no <publishBehavior>, so it defaults to "
                f"PublishImmediately and fires even when the transaction rolls back"
            )
        elif match.group(1) == "PublishImmediately":
            findings.append(
                f"REVIEW {path}: publishBehavior is PublishImmediately; confirm subscribers "
                f"can tolerate an event for a transaction that later failed"
            )

    apex_files = sorted(root.rglob("*.cls")) + sorted(root.rglob("*.trigger"))
    scanned_apex = 0
    for path in apex_files:
        text = read_text(path)
        if IS_TEST_RE.search(text):
            continue
        scanned_apex += 1
        if path.suffix == ".trigger" and TRIGGER_DECL_RE.search(text) and HTTP_USE_RE.search(text):
            findings.append(
                f"HIGH {path}: HTTP callout constructed inside a trigger; callouts must be "
                f"made asynchronously from a trigger (Apex Developer Guide, Trigger "
                f"Considerations)"
            )
        for literal in LITERAL_ENDPOINT_RE.findall(text):
            findings.append(
                f"HIGH {path}: setEndpoint() holds a literal URL ({literal[:60]}); use "
                f"callout:<NamedCredential>/<path> instead"
            )

    scanned = len(remote_sites) + len(named_credentials) + len(event_objects) + scanned_apex
    if scanned == 0:
        return (
            [
                f"HIGH {root}: no Named Credential, Remote Site Setting, platform event or "
                f"Apex metadata found; retrieve the inventory manifest in "
                f"references/decision-record-examples.md first"
            ],
            "Scanned 0 integration files.",
        )

    summary = (
        f"Scanned {scanned} integration file(s) "
        f"({len(named_credentials)} named credential(s), {len(remote_sites)} remote site "
        f"setting(s), {len(event_objects)} platform event definition(s), {scanned_apex} "
        f"Apex file(s)); {len(findings)} finding(s)."
    )
    return findings, summary


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def main() -> int:
    args = parse_args()

    if args.decision_record:
        findings, summary = lint_decision_record(Path(args.decision_record))
        return emit_result(findings, summary)

    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result(
            [f"HIGH {root}: manifest directory not found"],
            "Scanned 0 files; manifest directory was missing.",
        )

    findings, summary = scan_metadata(root)
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
