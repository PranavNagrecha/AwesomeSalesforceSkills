"""Regression tests for the durable source-integration ledger."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_source_integrations as checker


class SourceIntegrationRecordTests(unittest.TestCase):
    def _record(self, rel: str, digest: str) -> dict:
        return {
            "$schema": "../../config/source-integration.schema.json",
            "schema_version": 1,
            "integration_id": "test-integration",
            "created_at": "2026-09-01T00:00:00Z",
            "baseline": {
                "requested_archive": "latest.zip",
                "reviewed_archive": "mounted.zip",
                "reviewed_archive_sha256": "a" * 64,
                "exact_requested_snapshot_available": False,
                "repository_baseline_commit": "baseline",
                "notes": "The requested archive was not mounted, so this record declares the reviewed fallback exactly.",
            },
            "sources": [
                {
                    "id": "source-one",
                    "requested_archive": "source.zip",
                    "repository": "https://example.invalid/source",
                    "pin": {
                        "kind": "unavailable",
                        "value": None,
                        "reason": "Archive bytes were not mounted.",
                    },
                    "license": {
                        "detected": "MIT",
                        "class": "permissive",
                        "conflict": False,
                        "conflict_reason": None,
                        "evidence": ["LICENSE"],
                    },
                    "candidate_count": 1,
                    "content_use": "Topic discovery only; all final content was authored independently.",
                }
            ],
            "decisions": [
                {
                    "source_id": "source-one",
                    "candidate_id": "candidate",
                    "disposition": "ADD",
                    "target": "architect/example",
                    "scope": "One bounded example capability.",
                    "rationale": "The canonical catalog has no equivalent package.",
                    "routing": "Positive and neighbor queries are required.",
                    "files": [rel],
                }
            ],
            "changed_files": {rel: digest},
            "validation": [{"command": "example", "status": "passed", "evidence": "log.txt"}],
            "attestation": {
                "clean_room": "No upstream prose, examples, templates, or code were copied.",
                "no_unverified_copy": True,
                "product_boundary": "The integration remains read-only and grants no org mutation authority.",
            },
        }

    def _write_record(self, root: Path, payload: dict) -> Path:
        record = root / "record.json"
        record.write_text(json.dumps(payload), encoding="utf-8")
        return record

    def _root_with_target(self) -> tuple[tempfile.TemporaryDirectory[str], Path, str]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        target = root / "changed.txt"
        target.write_text("content", encoding="utf-8")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        return temporary, root, digest

    def test_valid_record_and_hash_pass(self) -> None:
        temporary, root, digest = self._root_with_target()
        with temporary:
            record = self._write_record(root, self._record("changed.txt", digest))
            with patch.object(checker, "ROOT", root):
                self.assertEqual(checker.validate_record(record), [])

    def test_hash_drift_fails(self) -> None:
        temporary, root, _ = self._root_with_target()
        with temporary:
            record = self._write_record(root, self._record("changed.txt", "0" * 64))
            with patch.object(checker, "ROOT", root):
                errors = checker.validate_record(record)
            self.assertTrue(any("hash mismatch" in error for error in errors))

    def test_unknown_source_reference_fails(self) -> None:
        temporary, root, digest = self._root_with_target()
        with temporary:
            payload = self._record("changed.txt", digest)
            payload["decisions"][0]["source_id"] = "missing"
            record = self._write_record(root, payload)
            with patch.object(checker, "ROOT", root):
                errors = checker.validate_record(record)
            self.assertTrue(any("source_id is not declared" in error for error in errors))

    def test_unexpected_property_fails_published_schema(self) -> None:
        temporary, root, digest = self._root_with_target()
        with temporary:
            payload = self._record("changed.txt", digest)
            payload["unexpected"] = True
            record = self._write_record(root, payload)
            errors = checker.validate_record(record, check_hashes=False)
            self.assertTrue(any("Additional properties are not allowed" in error for error in errors))

    def test_license_conflict_must_be_boolean(self) -> None:
        temporary, root, digest = self._root_with_target()
        with temporary:
            payload = self._record("changed.txt", digest)
            payload["sources"][0]["license"]["conflict"] = "none"
            record = self._write_record(root, payload)
            errors = checker.validate_record(record, check_hashes=False)
            self.assertTrue(any("is not of type 'boolean'" in error for error in errors))

    def test_conflict_requires_explanation(self) -> None:
        temporary, root, digest = self._root_with_target()
        with temporary:
            payload = self._record("changed.txt", digest)
            payload["sources"][0]["license"]["conflict"] = True
            payload["sources"][0]["license"]["conflict_reason"] = None
            record = self._write_record(root, payload)
            errors = checker.validate_record(record, check_hashes=False)
            self.assertTrue(any("is not of type 'string'" in error for error in errors))

    def test_no_conflict_requires_null_explanation(self) -> None:
        temporary, root, digest = self._root_with_target()
        with temporary:
            payload = self._record("changed.txt", digest)
            payload["sources"][0]["license"]["conflict_reason"] = "No conflict exists."
            record = self._write_record(root, payload)
            errors = checker.validate_record(record, check_hashes=False)
            self.assertTrue(any("is not of type 'null'" in error for error in errors))

    def test_committed_records_conform_to_published_schema(self) -> None:
        root = Path(__file__).resolve().parents[1]
        records = sorted((root / "registry" / "source-integrations").glob("*.json"))
        self.assertTrue(records)
        failures: list[str] = []
        for record in records:
            data = json.loads(record.read_text(encoding="utf-8"))
            failures.extend(checker.validate_schema(data, record))
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
