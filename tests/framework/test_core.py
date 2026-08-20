"""M1 deterministic core conformance tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class KernelBridgeTests(unittest.TestCase):
    def test_stable_ids_match_reference_kernel(self) -> None:
        from pipelines.framework.core import stable_claim_id, stable_evidence_id

        eid = stable_evidence_id("fixture", "deploy.json", {"job": "1"})
        self.assertTrue(eid.startswith("EV-"))
        cid = stable_claim_id("P01", "observation", "Deploy failed")
        self.assertTrue(cid.startswith("CL-"))

    def test_run_state_happy_path(self) -> None:
        from pipelines.framework.core import RunStateMachine

        machine = RunStateMachine(run_id="RUN-TEST")
        machine.transition("preflighted", "system", "ok")
        machine.transition("input_validated", "system", "ok")
        machine.transition("planned", "system", "ok")
        self.assertEqual(machine.state, "planned")


class RunSessionTests(unittest.TestCase):
    def test_target_attestation(self) -> None:
        from pipelines.framework.core.run_session import RunSession, TargetIdentity

        session = RunSession(product_id="P01", mode="fixture")
        session.targets = TargetIdentity(fixture_path="/tmp/fixture.json")
        self.assertEqual(session.targets.attestation_errors(require_job_or_fixture=True), [])

    def test_checkpoint_mismatch_detected(self) -> None:
        from pipelines.framework.core import RunSession

        session = RunSession(product_id="P01", mode="live-read-only")
        checkpoint = session.checkpoint_payload()
        checkpoint["authority_profile"] = "qa-scratch-setup"
        errors = session.resume_from_checkpoint(checkpoint)
        self.assertIn("checkpoint authority_profile mismatch", errors)


class EnvelopeTests(unittest.TestCase):
    def test_envelope_v2_shape(self) -> None:
        from pipelines.framework.core import build_output_envelope

        envelope = build_output_envelope(
            run_id="RUN-1",
            product_id="P01",
            status="partial",
            mode="fixture",
            summary="test",
            persisted=False,
        )
        self.assertEqual(envelope["schema_version"], "2.0.0")
        self.assertFalse(envelope["persisted"])
        self.assertIn("evidence_review", envelope)

    def test_completed_blocked_by_lint(self) -> None:
        from pipelines.framework.core import build_output_envelope, can_complete

        envelope = build_output_envelope(
            run_id="RUN-1",
            product_id="P01",
            status="completed",
            mode="fixture",
            summary="test",
        )
        ok, reasons = can_complete(
            output_envelope=envelope,
            deterministic_lint={"verdict": "fail", "errors": [{"code": "unsupported_material_claim"}]},
        )
        self.assertFalse(ok)
        self.assertTrue(reasons)


class RunBundleTests(unittest.TestCase):
    def test_write_load_redaction(self) -> None:
        from pipelines.framework.core import write_run_bundle, load_run_bundle, validate_bundle_redaction

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run_id = "RUN-BUNDLE-TEST"
            write_run_bundle(
                run_id,
                run_record={"run_id": run_id, "secret": "sfdxAuthUrl=bad"},
                base=base,
            )
            loaded = load_run_bundle(run_id, base=base)
            self.assertEqual(loaded["run"]["run_id"], run_id)
            self.assertEqual(validate_bundle_redaction(run_id, base=base), [])


class AdapterTests(unittest.TestCase):
    def test_unsupported_claim_still_fails(self) -> None:
        from pipelines.framework.core import lint_product_draft

        draft = {
            "status": "completed",
            "hypotheses": [{"summary": "x", "confidence": "HIGH"}],
            "findings": [{"severity": "high", "title": "missing evidence"}],
        }
        result = lint_product_draft(draft)
        self.assertFalse(result["passed"])

    def test_handoff_rejects_transcript(self) -> None:
        from pipelines.product.handoff import make_handoff, validate_handoff

        with self.assertRaises(ValueError):
            make_handoff(run_id="RUN-1", task="context_librarian", extra={"transcript": "long"})
        errors = validate_handoff({"run_id": "RUN-1", "task": "bad", "facts": []})
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
