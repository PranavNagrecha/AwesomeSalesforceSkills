#!/usr/bin/env python3
"""Lint Salesforce API contract records produced by the api-contract-documentation skill.

The artifact this skill produces is a YAML contract record: one per endpoint per
direction. This script checks that a record is complete enough to hand to a
partner and to `agents/integration-catalog-builder/AGENT.md`.

Checks performed
  1. Required top-level fields are present and non-empty.
  2. Enumerated fields hold allowed values (direction, status, auth.type) and
     `salesforce_api_version` is either vNN.0 or, for an outbound contract, n/a.
  3. Every error_contract row maps a Salesforce errorCode + HTTP status to a
     partner action and carries an explicit `retryable` boolean; no duplicate
     (status, errorCode) pairs.
  4. A retry policy exists with a strategy and a positive max_attempts whenever
     any error row is marked retryable.
  5. An owner is named and review_date (and eol_review_date, if present) parse
     as ISO dates.
  6. Repo references (skills/, agents/, standards/, templates/) resolve on disk.
  7. Across a manifest directory, contract `id` values are unique.

Usage
  python3 check_api_contract_documentation.py --file contract.yaml
  python3 check_api_contract_documentation.py --manifest-dir docs/api/contracts
  python3 check_api_contract_documentation.py          # lints references/worked-examples.md

Stdlib only. Exits 1 on any error, 0 when clean.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_DIR.parent.parent.parent  # skills/<domain>/<skill>/ -> repo root

REQUIRED_FIELDS = [
    "id",
    "name",
    "direction",
    "status",
    "endpoint",
    "salesforce_api_version",
    "auth",
    "idempotency",
    "rate_limit",
    "error_contract",
    "retry_policy",
    "owner",
    "review_date",
]

DIRECTIONS = {"inbound", "outbound", "bidirectional"}
STATUSES = {"draft", "active", "deprecated", "retired"}
AUTH_TYPES = {
    "named-credential",
    "connected-app-oauth",
    "jwt-bearer",
    "client-credentials",
    "session-id",
    "mutual-tls",
    "external-credential",
}
VERSION_RE = re.compile(r"^v\d{1,3}\.0$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REPO_PREFIXES = ("skills/", "agents/", "standards/", "templates/", "commands/", "evals/")


# --------------------------------------------------------------------------
# Minimal YAML subset reader (maps, lists of maps, lists of scalars, comments).
# Deliberately not a general YAML parser: contract records use a flat subset.
# --------------------------------------------------------------------------

def _strip_comment(line: str) -> str:
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line


def _split_kv(text: str):
    quote = None
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch == ":" and (i + 1 == len(text) or text[i + 1] in " \t"):
            return text[:i].strip(), text[i + 1:].strip()
    return None, None


def _scalar(raw: str):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    low = raw.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~", ""):
        return None
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    return raw


def _tokenize(text: str):
    """Return [(indent, content)], with '- ' items re-indented to indent+2."""
    tokens = []
    for raw in text.splitlines():
        body = _strip_comment(raw.rstrip())
        if not body.strip():
            continue
        indent = len(body) - len(body.lstrip(" "))
        content = body.strip()
        while content.startswith("- "):
            tokens.append((indent, "-"))
            content = content[2:].lstrip()
            indent += 2
        if content == "-":
            tokens.append((indent, "-"))
            continue
        tokens.append((indent, content))
    return tokens


def _parse(tokens, pos, indent):
    if pos[0] >= len(tokens):
        return None
    content = tokens[pos[0]][1]
    if content == "-":
        return _parse_list(tokens, pos, indent)
    key, _ = _split_kv(content)
    if key is None:
        # A bare scalar (a list item such as `- "skills/<domain>/<slug>"`).
        pos[0] += 1
        return _scalar(content)
    return _parse_map(tokens, pos, indent)


def _parse_list(tokens, pos, indent):
    out = []
    while pos[0] < len(tokens) and tokens[pos[0]][0] == indent and tokens[pos[0]][1] == "-":
        pos[0] += 1
        if pos[0] < len(tokens) and tokens[pos[0]][0] > indent:
            out.append(_parse(tokens, pos, tokens[pos[0]][0]))
        else:
            out.append(None)
    return out


def _parse_map(tokens, pos, indent):
    out = {}
    while pos[0] < len(tokens) and tokens[pos[0]][0] == indent and tokens[pos[0]][1] != "-":
        key, value = _split_kv(tokens[pos[0]][1])
        if key is None:
            break  # not a mapping entry - leave it for the caller
        pos[0] += 1
        if value:
            out[key] = _scalar(value)
        elif pos[0] < len(tokens) and tokens[pos[0]][0] > indent:
            out[key] = _parse(tokens, pos, tokens[pos[0]][0])
        else:
            out[key] = None
    return out


def load_record(text: str):
    return _parse(_tokenize(text), [0], 0) or {}


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def _walk_strings(node):
    if isinstance(node, dict):
        for value in node.values():
            yield from _walk_strings(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_strings(item)
    elif isinstance(node, str):
        yield node


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def check_record(record, label: str, repo_root: Path) -> list[str]:
    errors: list[str] = []

    if not isinstance(record, dict):
        return [f"{label}: not a YAML mapping"]

    # 1. Required fields.
    for field in REQUIRED_FIELDS:
        if field not in record or _is_blank(record[field]):
            errors.append(f"{label}: required field '{field}' is missing or empty")

    # 2. Enumerated values and version format.
    direction = record.get("direction")
    if direction is not None and direction not in DIRECTIONS:
        errors.append(
            f"{label}: direction '{direction}' not in {sorted(DIRECTIONS)}"
        )
    status = record.get("status")
    if status is not None and status not in STATUSES:
        errors.append(f"{label}: status '{status}' not in {sorted(STATUSES)}")

    auth = record.get("auth")
    if isinstance(auth, dict):
        auth_type = auth.get("type")
        if _is_blank(auth_type):
            errors.append(f"{label}: auth.type is missing")
        elif auth_type not in AUTH_TYPES:
            errors.append(
                f"{label}: auth.type '{auth_type}' not in {sorted(AUTH_TYPES)}"
            )
        named = [k for k in ("named_credential", "connected_app", "external_credential")
                 if not _is_blank(auth.get(k))]
        if not named:
            errors.append(
                f"{label}: auth names no named_credential / connected_app / "
                "external_credential - the contract cannot be traced to a Setup record"
            )
    elif "auth" in record:
        errors.append(f"{label}: auth must be a mapping with a 'type'")

    version = record.get("salesforce_api_version")
    if isinstance(version, str):
        if version == "n/a":
            if direction != "outbound":
                errors.append(
                    f"{label}: salesforce_api_version 'n/a' is only valid on an "
                    "outbound contract; an inbound contract must pin a version"
                )
        elif not VERSION_RE.match(version):
            errors.append(
                f"{label}: salesforce_api_version '{version}' is not vNN.0 (or 'n/a' outbound)"
            )

    # 3. Error contract rows.
    rows = record.get("error_contract")
    if not isinstance(rows, list) or not rows:
        errors.append(f"{label}: error_contract must be a non-empty list of rows")
        rows = []
    seen = set()
    retryable_rows = 0
    for index, row in enumerate(rows, start=1):
        where = f"{label}: error_contract[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{where} is not a mapping")
            continue
        http_status = row.get("http_status")
        code = row.get("salesforce_error_code")
        if not isinstance(http_status, int):
            errors.append(f"{where} has no integer http_status")
        if _is_blank(code):
            errors.append(
                f"{where} has no salesforce_error_code - every row must name the "
                "code the partner will actually see, or '(none)' with a reason"
            )
        if _is_blank(row.get("partner_action")):
            errors.append(
                f"{where} maps no partner_action - a code without an action is a "
                "glossary entry, not a contract"
            )
        if not isinstance(row.get("retryable"), bool):
            errors.append(f"{where} needs an explicit boolean 'retryable'")
        elif row["retryable"]:
            retryable_rows += 1
        key = (http_status, code)
        if key in seen:
            errors.append(f"{where} duplicates an earlier (http_status, errorCode) pair {key}")
        seen.add(key)

    # 4. Retry policy.
    retry = record.get("retry_policy")
    if isinstance(retry, dict):
        if _is_blank(retry.get("strategy")):
            errors.append(f"{label}: retry_policy.strategy is missing")
        attempts = retry.get("max_attempts")
        if not isinstance(attempts, int) or attempts < 1:
            errors.append(f"{label}: retry_policy.max_attempts must be an integer >= 1")
    elif retryable_rows:
        errors.append(
            f"{label}: {retryable_rows} error row(s) are retryable but no "
            "retry_policy mapping is defined"
        )

    # 5. Owner and dates.
    if _is_blank(record.get("owner")):
        errors.append(f"{label}: owner is missing - every contract needs a named human")
    for field, container in (
        ("review_date", record),
        ("eol_review_date", record.get("versioning") if isinstance(record.get("versioning"), dict) else {}),
    ):
        value = container.get(field) if isinstance(container, dict) else None
        if value is None:
            if field == "review_date":
                errors.append(f"{label}: review_date is missing")
            continue
        if not (isinstance(value, str) and DATE_RE.match(value)):
            errors.append(f"{label}: {field} '{value}' is not an ISO YYYY-MM-DD date")
            continue
        try:
            date.fromisoformat(value)
        except ValueError:
            errors.append(f"{label}: {field} '{value}' is not a real calendar date")

    # 6. Repo references resolve.
    for value in _walk_strings(record):
        candidate = value.strip()
        if not candidate.startswith(REPO_PREFIXES):
            continue
        target = repo_root / candidate
        if not target.exists() and not target.with_suffix(".md").exists():
            errors.append(f"{label}: reference '{candidate}' does not resolve under {repo_root}")

    return errors


def extract_embedded_records(md_path: Path):
    """Pull fenced yaml blocks that look like contract records out of a markdown file."""
    records = []
    if not md_path.exists():
        return records
    in_block = False
    buffer: list[str] = []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not in_block and stripped == "```yaml":
            in_block, buffer = True, []
            continue
        if in_block and stripped == "```":
            body = "\n".join(buffer)
            if re.search(r"^id:", body, re.MULTILINE):
                records.append(body)
            in_block = False
            continue
        if in_block:
            buffer.append(line)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Lint Salesforce API contract records.")
    parser.add_argument("--file", help="A single contract record (.yaml/.yml).")
    parser.add_argument("--manifest-dir", help="Directory of contract records to lint.")
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repo root used to resolve skills/ agents/ standards/ references.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    sources: list[tuple[str, str]] = []

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"ERROR: --file {path} does not exist")
            sys.exit(1)
        sources.append((str(path), path.read_text(encoding="utf-8")))

    if args.manifest_dir:
        directory = Path(args.manifest_dir)
        if not directory.is_dir():
            print(f"ERROR: --manifest-dir {directory} is not a directory")
            sys.exit(1)
        found = sorted(
            p for p in directory.rglob("*")
            if p.suffix in (".yaml", ".yml") and p.is_file()
        )
        if not found:
            print(f"ERROR: no .yaml/.yml contract records found under {directory}")
            sys.exit(1)
        sources.extend((str(p), p.read_text(encoding="utf-8")) for p in found)

    if not sources:
        worked = SKILL_DIR / "references" / "worked-examples.md"
        blocks = extract_embedded_records(worked)
        if not blocks:
            print(f"ERROR: no contract records found in {worked}")
            sys.exit(1)
        sources.extend(
            (f"{worked.name}#record-{i}", body) for i, body in enumerate(blocks, start=1)
        )

    all_errors: list[str] = []
    ids: dict[str, str] = {}

    for label, text in sources:
        try:
            record = load_record(text)
        except Exception as exc:  # noqa: BLE001 - surface parse failure as a lint error
            all_errors.append(f"{label}: could not parse as a contract record ({exc})")
            continue
        all_errors.extend(check_record(record, label, repo_root))
        record_id = record.get("id") if isinstance(record, dict) else None
        if isinstance(record_id, str) and record_id:
            if record_id in ids:
                all_errors.append(
                    f"{label}: contract id '{record_id}' already used by {ids[record_id]}"
                )
            else:
                ids[record_id] = label

    if all_errors:
        print(f"FAIL: {len(all_errors)} problem(s) across {len(sources)} contract record(s)")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)

    print(f"OK: {len(sources)} contract record(s) pass all checks")
    sys.exit(0)


if __name__ == "__main__":
    main()
