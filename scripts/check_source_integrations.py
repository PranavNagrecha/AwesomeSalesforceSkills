#!/usr/bin/env python3
"""Validate source-integration records against their schema and file hashes.

The published JSON Schema is the structural contract. This checker validates
that contract first, then enforces cross-record semantics and recomputes each
recorded repository file hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError:  # pragma: no cover - exercised only in an incomplete environment
    Draft202012Validator = None  # type: ignore[assignment]
    SchemaError = Exception  # type: ignore[assignment,misc]

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "registry" / "source-integrations"
SCHEMA_PATH = ROOT / "config" / "source-integration.schema.json"
ALLOWED_DISPOSITIONS = {"ADD", "DEEPEN", "MERGE", "STOP", "DEFER", "REJECT"}
ALLOWED_LICENSE_CLASSES = {"permissive", "clean-room", "rejected"}
ALLOWED_PIN_KINDS = {"commit", "tag", "archive-sha256", "unavailable"}
ALLOWED_VALIDATION_STATES = {"passed", "failed", "not-run", "blocked"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _json_path(parts: Iterable[Any]) -> str:
    rendered = "$"
    for part in parts:
        if isinstance(part, int):
            rendered += f"[{part}]"
        elif isinstance(part, str) and part.isidentifier():
            rendered += f".{part}"
        else:
            rendered += f"[{part!r}]"
    return rendered


@lru_cache(maxsize=1)
def _schema_validator() -> Any:
    if Draft202012Validator is None:
        raise RuntimeError(
            "jsonschema is required; install the repository requirements before "
            "running source-integration validation"
        )
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read JSON Schema {SCHEMA_PATH}: {exc}") from exc
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise RuntimeError(f"invalid JSON Schema {SCHEMA_PATH}: {exc.message}") from exc
    return Draft202012Validator(schema)


def validate_schema(data: Any, path: Path) -> list[str]:
    try:
        validator = _schema_validator()
    except RuntimeError as exc:
        return [f"{path}: {exc}"]

    errors: list[str] = []
    for issue in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path)):
        errors.append(f"{path}: {_json_path(issue.absolute_path)}: {issue.message}")
    return errors


def validate_record(path: Path, *, check_hashes: bool = True) -> list[str]:
    errors: list[str] = []
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: cannot read valid JSON: {exc}"]

    schema_errors = validate_schema(data, path)
    if schema_errors:
        return schema_errors

    require(data.get("schema_version") == 1, f"{path}: schema_version must be 1", errors)
    integration_id = data.get("integration_id")
    require(
        isinstance(integration_id, str) and bool(ID_RE.fullmatch(integration_id)),
        f"{path}: invalid integration_id",
        errors,
    )

    baseline = data["baseline"]
    archive_hash = baseline["reviewed_archive_sha256"]
    require(
        isinstance(archive_hash, str) and bool(SHA256_RE.fullmatch(archive_hash)),
        f"{path}: baseline reviewed_archive_sha256 must be a SHA-256",
        errors,
    )
    require(
        isinstance(baseline["exact_requested_snapshot_available"], bool),
        f"{path}: baseline exact_requested_snapshot_available must be boolean",
        errors,
    )
    require(
        len(baseline["notes"].strip()) >= 20,
        f"{path}: baseline notes must explain snapshot limitations",
        errors,
    )

    sources = data["sources"]
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        prefix = f"{path}: sources[{index}]"
        source_id = source["id"]
        require(source_id not in source_ids, f"{prefix}.id duplicates {source_id}", errors)
        source_ids.add(source_id)

        pin = source["pin"]
        kind = pin["kind"]
        value = pin["value"]
        require(kind in ALLOWED_PIN_KINDS, f"{prefix}.pin.kind invalid", errors)
        if kind == "unavailable":
            require(value is None, f"{prefix}.pin.value must be null when unavailable", errors)
        else:
            require(
                isinstance(value, str) and bool(value.strip()),
                f"{prefix}.pin.value required for {kind}",
                errors,
            )
        require(
            len(pin["reason"].strip()) >= 10,
            f"{prefix}.pin.reason must be explicit",
            errors,
        )

        license_info = source["license"]
        require(
            license_info["class"] in ALLOWED_LICENSE_CLASSES,
            f"{prefix}.license.class invalid",
            errors,
        )
        conflict = license_info["conflict"]
        conflict_reason = license_info["conflict_reason"]
        require(isinstance(conflict, bool), f"{prefix}.license.conflict must be boolean", errors)
        if conflict:
            require(
                isinstance(conflict_reason, str) and len(conflict_reason.strip()) >= 20,
                f"{prefix}.license.conflict_reason required when conflict is true",
                errors,
            )
        else:
            require(
                conflict_reason is None,
                f"{prefix}.license.conflict_reason must be null when conflict is false",
                errors,
            )
        require(
            bool(license_info["evidence"]),
            f"{prefix}.license.evidence must be non-empty",
            errors,
        )
        require(
            source["candidate_count"] > 0,
            f"{prefix}.candidate_count must be positive",
            errors,
        )

    decisions = data["decisions"]
    decision_keys: set[tuple[str, str]] = set()
    for index, decision in enumerate(decisions):
        prefix = f"{path}: decisions[{index}]"
        source_id = decision["source_id"]
        candidate_id = decision["candidate_id"]
        require(source_id in source_ids, f"{prefix}.source_id is not declared", errors)
        key = (source_id, candidate_id)
        require(key not in decision_keys, f"{prefix} duplicates {key}", errors)
        decision_keys.add(key)
        disposition = decision["disposition"]
        require(disposition in ALLOWED_DISPOSITIONS, f"{prefix}.disposition invalid", errors)
        target = decision["target"]
        if disposition in {"ADD", "DEEPEN", "MERGE", "STOP"}:
            require(
                isinstance(target, str) and bool(target.strip()),
                f"{prefix}.target required for {disposition}",
                errors,
            )
        for key_name, minimum in (("scope", 12), ("rationale", 20), ("routing", 12)):
            require(
                len(decision[key_name].strip()) >= minimum,
                f"{prefix}.{key_name} is too short",
                errors,
            )

    changed_files = data["changed_files"]
    for rel, expected in sorted(changed_files.items()):
        prefix = f"{path}: changed_files[{rel!r}]"
        require(
            not rel.startswith("/") and ".." not in Path(rel).parts,
            f"{prefix} must be a safe repository-relative path",
            errors,
        )
        require(
            bool(SHA256_RE.fullmatch(expected)),
            f"{prefix} value must be a SHA-256",
            errors,
        )
        target = ROOT / rel
        require(target.is_file(), f"{prefix} file does not exist", errors)
        if check_hashes and target.is_file():
            actual = sha256(target)
            require(
                actual == expected,
                f"{prefix} hash mismatch: expected {expected}, got {actual}",
                errors,
            )

    for index, item in enumerate(data["validation"]):
        prefix = f"{path}: validation[{index}]"
        require(item["status"] in ALLOWED_VALIDATION_STATES, f"{prefix}.status invalid", errors)

    attestation = data["attestation"]
    require(
        attestation["no_unverified_copy"] is True,
        f"{path}: attestation.no_unverified_copy must be true",
        errors,
    )

    return errors


def iter_records(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(target.rglob("*.json")) if target.is_dir() else []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SfSkills source-integration records.")
    parser.add_argument("path", nargs="?", default=str(DEFAULT_DIR), help="Record file or directory")
    parser.add_argument(
        "--skip-hashes",
        action="store_true",
        help="Validate structure and semantics without recomputing changed-file hashes",
    )
    args = parser.parse_args()

    target = Path(args.path)
    if not target.is_absolute():
        target = ROOT / target
    records = iter_records(target)
    if not records:
        print(f"ERROR: no source-integration JSON records found under {target}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for record in records:
        errors.extend(validate_record(record, check_hashes=not args.skip_hashes))
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print(f"OK: validated {len(records)} source-integration record(s) against schema and hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
