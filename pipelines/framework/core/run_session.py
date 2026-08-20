"""Run session: identity, target attestation, lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .kernel_bridge import InvalidTransition, RunStateMachine, new_run_id

TERMINAL_STATUSES = {"completed", "partial", "refused", "failed"}
AUTHORITY_PROFILES = {
    "product-read-only",
    "fixture-offline",
    "qa-scratch-setup",
    "maintainer-local-write",
    "future-approved-action",
}
RUN_MODES = {
    "knowledge-only",
    "fixture",
    "local-project",
    "live-read-only",
    "hybrid",
    "scratch-qa",
}


@dataclass
class TargetIdentity:
    org_alias: str | None = None
    org_id: str | None = None
    job_id: str | None = None
    project_path: str | None = None
    fixture_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "org_alias": self.org_alias,
            "org_id": self.org_id,
            "job_id": self.job_id,
            "project_path": self.project_path,
            "fixture_path": self.fixture_path,
        }

    def attestation_errors(self, *, require_org: bool = False, require_job_or_fixture: bool = False) -> list[str]:
        errors: list[str] = []
        if require_org and not (self.org_alias or self.org_id):
            errors.append("target org_alias or org_id is required")
        if require_job_or_fixture and not (self.job_id or self.fixture_path):
            errors.append("target job_id or fixture_path is required")
        if self.org_alias and self.org_id and self.org_alias.startswith("00D") is False:
            pass
        return errors


@dataclass
class RunSession:
    product_id: str
    mode: str
    authority_profile: str = "product-read-only"
    run_id: str = field(default_factory=new_run_id)
    targets: TargetIdentity = field(default_factory=TargetIdentity)
    product_version: str = "0.9.0-draft"
    host: dict[str, Any] = field(default_factory=dict)
    _machine: RunStateMachine = field(init=False, repr=False)
    status: str | None = None
    context_manifests: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    claim_refs: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.mode not in RUN_MODES:
            raise ValueError(f"invalid mode: {self.mode}")
        if self.authority_profile not in AUTHORITY_PROFILES:
            raise ValueError(f"invalid authority_profile: {self.authority_profile}")
        self._machine = RunStateMachine(run_id=self.run_id)

    @property
    def state(self) -> str:
        return self._machine.state

    @property
    def state_history(self) -> list[dict]:
        return list(self._machine.history)

    def transition(self, new_state: str, actor: str, reason: str) -> None:
        self._machine.transition(new_state, actor, reason)

    def set_terminal_status(self, status: str) -> None:
        if status not in TERMINAL_STATUSES:
            raise ValueError(f"invalid terminal status: {status}")
        self.status = status

    def to_run_record(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "product_id": self.product_id,
            "product_version": self.product_version,
            "mode": self.mode,
            "authority_profile": self.authority_profile,
            "state": self.state,
            "status": self.status,
            "targets": self.targets.to_dict(),
            "host": self.host,
            "context_manifests": self.context_manifests,
            "evidence_refs": self.evidence_refs,
            "claim_refs": self.claim_refs,
            "state_history": self.state_history,
            "metrics": self.metrics,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    def checkpoint_payload(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "state": self.state,
            "status": self.status,
            "targets": self.targets.to_dict(),
            "authority_profile": self.authority_profile,
            "context_manifests": self.context_manifests,
            "evidence_refs": self.evidence_refs,
            "claim_refs": self.claim_refs,
        }

    def resume_from_checkpoint(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if payload.get("run_id") != self.run_id:
            errors.append("checkpoint run_id mismatch")
        if payload.get("authority_profile") != self.authority_profile:
            errors.append("checkpoint authority_profile mismatch")
        if payload.get("targets") != self.targets.to_dict():
            errors.append("checkpoint targets mismatch")
        return errors


__all__ = ["RunSession", "TargetIdentity", "TERMINAL_STATUSES"]
