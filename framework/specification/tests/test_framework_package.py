from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


class FrameworkPackageTests(unittest.TestCase):
    def test_requirement_catalog_has_unique_stable_ids(self):
        module = load_module("build_requirements", "scripts/build_requirement_catalog.py")
        rows = module.collect_requirements(ROOT)
        ids = [item["requirement_id"] for item in rows]
        self.assertGreaterEqual(len(ids), 250)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(value.startswith("SFAEF-") for value in ids))

    def test_definition_counts_are_nontrivial(self):
        self.assertEqual(len(list((ROOT / "products" / "definitions").glob("*.json"))), 12)
        self.assertGreaterEqual(len(list((ROOT / "agents" / "definitions").glob("*.json"))), 20)
        self.assertGreaterEqual(len(list((ROOT / "commands" / "specs").glob("*.json"))), 18)
        self.assertGreaterEqual(len(list((ROOT / "mcp" / "tool-specs").glob("*.json"))), 18)
        self.assertGreaterEqual(len(list((ROOT / "qa" / "scenarios").glob("*.json"))), 70)

    def test_all_product_tools_are_read_only(self):
        for path in (ROOT / "mcp" / "tool-specs").glob("*.json"):
            data = json.loads(path.read_text())
            self.assertTrue(data["read_only"], path.name)
            self.assertEqual(data["unknown_tool_default"], "deny", path.name)
            self.assertLessEqual(data["max_page_bytes"], 32768, path.name)

    def test_legacy_migration_ledgers_cover_uploaded_baseline(self):
        import csv
        expected = {
            "current-skills.csv": 1034,
            "current-agents.csv": 78,
            "current-commands.csv": 70,
            "current-mcp-tools.csv": 40,
        }
        for name, count in expected.items():
            with (ROOT / "migration" / "catalogs" / name).open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), count, name)

    def test_local_report_persistence_is_not_salesforce_mutation(self):
        for path in (ROOT / "products" / "definitions").glob("*.json"):
            data = json.loads(path.read_text())
            self.assertIn("local_reports.write", data.get("permissions", []), path.name)

    def test_product_commands_have_review_and_read_only_contracts(self):
        for path in (ROOT / "commands" / "specs").glob("*.json"):
            data = json.loads(path.read_text())
            self.assertTrue(data["aliases"], path.name)
            self.assertTrue(data["validation_rules"], path.name)
            self.assertTrue(data["examples"], path.name)
            allowed = set(data["allowed_statuses"])
            self.assertTrue(all(item["status"] in allowed for item in data["errors"]), path.name)
            if data.get("product_id"):
                self.assertTrue(data["requires_independent_review"], path.name)
                self.assertIn("independent_review", data["orchestration_stages"], path.name)
                self.assertEqual(data["side_effects"]["salesforce"], "read-only", path.name)

    def test_tools_have_bounded_replayable_contracts(self):
        required_never_retry = {"invalid_input", "policy_denied", "authentication_unavailable", "redaction_failure"}
        for path in (ROOT / "mcp" / "tool-specs").glob("*.json"):
            data = json.loads(path.read_text())
            self.assertEqual(data["result_schema"], "tool-result.schema.json", path.name)
            self.assertFalse(data["cache_policy"]["cross_target"], path.name)
            self.assertLessEqual(data["pagination"]["max_page_bytes"], 32768, path.name)
            self.assertLessEqual(data["pagination"]["default_limit"], data["pagination"]["max_limit"], path.name)
            self.assertTrue(required_never_retry.issubset(set(data["retry_policy"]["never_retry_errors"])), path.name)
            self.assertGreaterEqual(len(data["normalization_rules"]), 5, path.name)
            self.assertGreaterEqual(len(data["audit_events"]), 5, path.name)
            error_codes = [item["code"] for item in data["error_codes"]]
            self.assertEqual(len(error_codes), len(set(error_codes)), path.name)
            if data["requires_target_pinning"]:
                self.assertIn("target_mismatch", error_codes, path.name)

    def test_agents_cannot_gain_authority_from_prompts(self):
        agent_ids = {path.stem for path in (ROOT / "agents" / "definitions").glob("*.json")}
        for path in (ROOT / "agents" / "definitions").glob("*.json"):
            data = json.loads(path.read_text())
            authority = data["authority_profile"]
            self.assertFalse(authority["authority_from_user_prose"], path.name)
            self.assertFalse(authority["authority_from_other_agents"], path.name)
            self.assertIn(authority["salesforce_access"], {"none", "read-only"}, path.name)
            self.assertTrue(data["evidence_required"], path.name)
            self.assertTrue(data["evidence_prohibited"], path.name)
            self.assertTrue(set(data["collaborators"]).issubset(agent_ids), path.name)
            if data["kind"] == "product":
                self.assertTrue(data["completion_review_required"], path.name)
                self.assertNotEqual(data["recommended_host_exposure"], "top-level", path.name)

    def test_generated_api_references_are_current(self):
        module = load_module("api_reference_builder", "scripts/build_api_references.py")
        for path, builder in module.OUTPUTS.items():
            self.assertEqual(path.read_text(encoding="utf-8"), builder(), path.name)

    def test_context_packs_enforce_hard_limit(self):
        for path in (ROOT / "context" / "context-packs").glob("*.json"):
            data = json.loads(path.read_text())
            self.assertLessEqual(data["target_files"], data["hard_files"], path.name)
            self.assertLessEqual(data["hard_files"], 12, path.name)
            self.assertLessEqual(data["max_tool_page_bytes"], 32768, path.name)

    def test_validator_reports_package_valid(self):
        module = load_module("framework_validator", "scripts/validate_framework_package.py")
        result = module.Validator(ROOT).validate()
        self.assertTrue(result["valid"], result["findings"])

    def test_return_zip_verifier_rejects_empty_zip(self):
        module = load_module("return_verifier", "scripts/verify_cursor_return_zip.py")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.zip"
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr("top/README.txt", "empty")
            result = module.verify(path)
            self.assertFalse(result["valid"])
            self.assertTrue(any(item["code"] == "required_missing" for item in result["issues"]))


if __name__ == "__main__":
    unittest.main()
