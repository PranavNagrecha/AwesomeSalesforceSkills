"""Phase 1 product tests: normalizer, policy, context pack, doctor, plugin, inputs."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "mcp" / "sfskills-mcp" / "tests" / "fixtures" / "deploy"


class DeployNormalizeTests(unittest.TestCase):
    def _load(self, name: str):
        from pipelines.product.deploy_result import normalize_deploy_report

        payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
        return normalize_deploy_report(payload)

    def test_component_failures_have_stable_ids(self):
        first = self._load("component_failures.json")
        second = self._load("component_failures.json")
        self.assertTrue(first["ok"])
        self.assertEqual(first["evidence_ids"], second["evidence_ids"])
        self.assertGreaterEqual(first["source_counts"]["component_failures"], 2)

    def test_test_failures(self):
        out = self._load("test_failures.json")
        self.assertEqual(len(out["test_failures"]), 1)
        self.assertEqual(out["test_failures"][0]["class_name"], "AccountServiceTest")

    def test_coverage(self):
        out = self._load("coverage.json")
        self.assertTrue(out["coverage"] or out["warnings"])
        kinds = {w["kind"] for w in out["warnings"]}
        self.assertIn("coverage_warning", kinds)

    def test_duplicate_symptoms_grouped(self):
        out = self._load("duplicate_symptoms.json")
        groups = [g for g in out["groups"] if g["occurrence_count"] >= 3]
        self.assertTrue(groups)
        self.assertEqual(len(groups[0]["evidence_ids"]), groups[0]["occurrence_count"])

    def test_in_progress(self):
        out = self._load("in_progress.json")
        self.assertTrue(out["in_progress"])
        self.assertFalse(out["done"])

    def test_pagination(self):
        from pipelines.product.deploy_result import normalize_deploy_report

        failures = [
            {
                "componentType": "ApexClass",
                "fullName": f"Class{i}",
                "problem": "compile error",
                "problemType": "Error",
                "success": False,
            }
            for i in range(50)
        ]
        payload = {"result": {"id": "0Af000000000006AAA", "status": "Failed", "done": True, "details": {"componentFailures": failures}}}
        page0 = normalize_deploy_report(payload, failure_limit=10, cursor=None)
        self.assertTrue(page0["truncated"])
        self.assertEqual(page0["next_cursor"], "10")
        page1 = normalize_deploy_report(payload, failure_limit=10, cursor="10")
        self.assertEqual(len(page1["component_failures"]), 10)

    def test_source_tracking_warnings_are_not_groups(self):
        from pipelines.product.deploy_result import normalize_deploy_report

        payload = {
            "status": 1,
            "warnings": [
                "ApexClass, SfskillsTriageProbeAlpha, returned from org, but not found in the local project"
            ],
            "result": {
                "id": "0Af000000000007AAA",
                "status": "Failed",
                "done": True,
                "success": False,
                "details": {
                    "componentFailures": [
                        {
                            "componentType": "ApexClass",
                            "fullName": "SfskillsTriageProbeAlpha",
                            "problem": "Invalid type: Ghost",
                            "problemType": "Error",
                            "success": False,
                        }
                    ]
                },
            },
        }
        out = normalize_deploy_report(payload)
        self.assertEqual(out["source_counts"]["component_failures"], 1)
        self.assertEqual(out["source_counts"]["warnings"], 0)
        symptoms = [g["symptom"] for g in out["groups"]]
        self.assertTrue(any("Invalid type" in s for s in symptoms))
        self.assertFalse(any("not found in the local project" in s for s in symptoms))

    def test_bound_32kib(self):
        from pipelines.product.deploy_result import MAX_INJECT_BYTES, normalize_deploy_report

        failures = [
            {
                "componentType": "ApexClass",
                "fullName": f"VeryLongClassName{i}" * 20,
                "problem": "x" * 400,
                "problemType": "Error",
                "success": False,
            }
            for i in range(80)
        ]
        payload = {"result": {"id": "0Af000000000007AAA", "status": "Failed", "done": True, "details": {"componentFailures": failures}}}
        out = normalize_deploy_report(payload, failure_limit=100)
        self.assertLessEqual(out["byte_size"], MAX_INJECT_BYTES)
        self.assertTrue(out["truncated"])


class PolicyTests(unittest.TestCase):
    def _shell(self, command: str) -> str:
        from pipelines.product.policy import evaluate_shell_command

        return evaluate_shell_command(command)["permission"]

    def test_allow_report(self):
        self.assertEqual(
            self._shell("sf project deploy report --job-id 0Af000000000001AAA --json"),
            "allow",
        )

    def test_deny_mutations(self):
        for cmd in (
            "sf project deploy start --source-dir force-app",
            "sf project deploy validate --source-dir force-app",
            "sf project deploy quick --job-id 0Af000000000001AAA",
            "sf project deploy cancel --job-id 0Af000000000001AAA",
            "sf project deploy resume --job-id 0Af000000000001AAA",
            "sf data create record --sobject Account --values Name=x",
            "sf apex run --file foo.apex",
            "sf org create scratch --definition-file c.json",
            "sfdx force:source:deploy -p force-app",
        ):
            self.assertEqual(self._shell(cmd), "deny", cmd)

    def test_bypass_attempts(self):
        for cmd in (
            "sf project deploy report --job-id 0Af000000000001AAA --json; sf project deploy start",
            "sf project deploy report --job-id 0Af000000000001AAA --json && sf project deploy start",
            "sf project deploy report --job-id 0Af000000000001AAA --json || sf project deploy start",
            "sf project deploy report --job-id 0Af000000000001AAA --json | cat",
            "sf project deploy report --job-id $(echo 0Af) --json",
            "sf project deploy report --job-id `echo 0Af` --json",
            "bash -c 'sf project deploy start'",
            "sh -c 'sf project deploy start'",
            "./sf project deploy start",
            "env sf project deploy start",
            "sf project deploy report --use-most-recent --json",
            "python3 -c 'import os; os.system(\"sf project deploy start\")'",
        ):
            self.assertEqual(self._shell(cmd), "deny", cmd)

    def test_report_requires_job_id_and_json(self):
        self.assertEqual(self._shell("sf project deploy report --json"), "deny")
        self.assertEqual(self._shell("sf project deploy report --job-id 0Af000000000001AAA"), "deny")

    def test_mcp_get_deployment_result(self):
        from pipelines.product.policy import evaluate_mcp_call

        deny = evaluate_mcp_call("deploy_metadata", {})
        self.assertEqual(deny["permission"], "deny")
        deny2 = evaluate_mcp_call("get_deployment_result", {})
        self.assertEqual(deny2["permission"], "deny")
        allow = evaluate_mcp_call("get_deployment_result", {"job_id": "0Af000000000001AAA"})
        self.assertEqual(allow["permission"], "allow")
        deny3 = evaluate_mcp_call("sf_project_deploy_start", {})
        self.assertEqual(deny3["permission"], "deny")


class ContextPackTests(unittest.TestCase):
    def test_budget_and_distractors(self):
        from pipelines.product.context_pack import DISTRACTORS, select_context_pack
        from pipelines.product.deploy_result import normalize_deploy_report

        payload = json.loads((FIXTURES / "component_failures.json").read_text(encoding="utf-8"))
        normalized = normalize_deploy_report(payload)
        pack = select_context_pack(normalized, repo_root=ROOT)
        self.assertLessEqual(pack["domain_skill_or_reference_files"], 12)
        selected = {f["path"] for f in pack["files"]}
        self.assertTrue(selected.isdisjoint(set(DISTRACTORS)))
        self.assertFalse(pack["overflow"] or pack["domain_skill_or_reference_files"] > 12)

    def test_missing_path_flagged(self):
        from pipelines.product.context_pack import select_context_pack

        pack = select_context_pack({}, repo_root=ROOT, extra_paths=["does/not/exist.md"])
        self.assertIn("does/not/exist.md", pack["missing_paths"])

    def test_handoff_rejects_transcript(self):
        from pipelines.product.handoff import make_handoff, validate_handoff

        good = make_handoff(run_id="run-test-01", task="context_librarian")
        self.assertEqual(validate_handoff(good), [])
        with self.assertRaises(ValueError):
            make_handoff(run_id="run-test-01", task="context_librarian", extra={"transcript": "nope"})
        bad = dict(good)
        bad["transcript"] = "x"
        self.assertTrue(any("banned" in e for e in validate_handoff(bad)))


class ReviewerFixtureTests(unittest.TestCase):
    def test_unsupported_claim(self):
        draft = {
            "run_id": "review-1",
            "task": "deployment_triager",
            "facts": [{"claim": "The org is missing Permission Set X", "evidence_refs": []}],
            "evidence_refs": [],
            "hypotheses": [{"id": "h1", "text": "Permission Set X is missing", "confidence": "HIGH"}],
            "unknowns": [],
            "recommended_next_agent": "sf-evidence-reviewer",
            "context_metrics": {
                "files_loaded": 3,
                "estimated_tokens": 100,
                "tool_output_bytes": 10,
                "truncated": False,
            },
        }
        unsupported = [
            h for h in draft["hypotheses"] if h.get("confidence") == "HIGH" and not draft["evidence_refs"]
        ]
        self.assertTrue(unsupported)


class InputValidationTests(unittest.TestCase):
    def test_missing_and_malformed(self):
        from pipelines.product.command_inputs import validate_triage_inputs

        self.assertIn("missing_evidence_source", validate_triage_inputs({}))
        self.assertIn("malformed_job_id", validate_triage_inputs({"job_id": "latest"}))
        self.assertIn("use_most_recent_forbidden", validate_triage_inputs({"job_id": "0Af000000000001AAA", "use_most_recent": True}))

    def test_fixture_path(self):
        from pipelines.product.command_inputs import validate_triage_inputs

        path = str(FIXTURES / "component_failures.json")
        self.assertEqual(validate_triage_inputs({"result_path": path}), [])


class InstallHelperTests(unittest.TestCase):
    def test_overwrite_protection(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "install_cursor_plugin", ROOT / "scripts" / "install_cursor_plugin.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        tmp = Path(tempfile.mkdtemp())
        try:
            foreign = tmp / "awesome-salesforce-skills"
            foreign.mkdir()
            (foreign / ".cursor-plugin").mkdir()
            (foreign / ".cursor-plugin" / "plugin.json").write_text(json.dumps({"name": "other-plugin"}), encoding="utf-8")
            self.assertFalse(mod._is_our_install(foreign))
            ours = tmp / "ours"
            ours.mkdir()
            (ours / ".cursor-plugin").mkdir()
            (ours / ".cursor-plugin" / "plugin.json").write_text(json.dumps({"name": "awesome-salesforce-skills"}), encoding="utf-8")
            self.assertTrue(mod._is_our_install(ours))
        finally:
            shutil.rmtree(tmp)


class DoctorAndIndexTests(unittest.TestCase):
    def test_doctor_json_shape(self):
        from pipelines.product.doctor import run_doctor

        report = run_doctor(ROOT)
        self.assertIn("checks", report)
        self.assertIn("search_index", report["checks"])

    def test_missing_index_search_payload(self):
        from pipelines.lexical_index import index_status

        tmp = Path(tempfile.mkdtemp())
        try:
            st = index_status(tmp / "vector_index" / "lexical.sqlite")
            self.assertEqual(st["status"], "index_missing")
        finally:
            shutil.rmtree(tmp)


class PluginPresenceTests(unittest.TestCase):
    def test_source_components(self):
        src = ROOT / "integrations" / "cursor"
        for rel in (
            "plugin.json",
            "mcp.json",
            "hooks/hooks.json",
            "hooks/sfskills_policy.py",
            "agents/sf-context-librarian.md",
            "agents/sf-repo-mapper.md",
            "agents/sf-org-grounder.md",
            "agents/deployment-failure-triager.md",
            "agents/sf-evidence-reviewer.md",
            "commands/triage-deployment.md",
            "commands/sfskills-doctor.md",
        ):
            self.assertTrue((src / rel).is_file(), rel)
        agents = list((src / "agents").glob("*.md"))
        self.assertLessEqual(len(agents), 5)
        self.assertEqual(len(agents), 5)


if __name__ == "__main__":
    unittest.main()
