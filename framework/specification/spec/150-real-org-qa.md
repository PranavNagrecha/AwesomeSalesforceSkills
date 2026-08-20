# SFAEF-150 — Real-org and scratch-org behavioral QA

## Three lanes

### Lane A — Hermetic

Captured fixtures, schemas, normalizers, policy, context, evidence, and host-package tests. Runs on every change.

### Lane B — Persistent read-only QA org

Scheduled/manual probes of official APIs, fields, metadata shapes, auth, and existing job/test retrieval. Detects platform and tool drift; does not prove known root cause.

### Lane C — Disposable scratch-org known truth

Protected workflow creates a scratch org, deploys scenario fixtures through non-model setup code, runs validation/tests, retrieves results through product read-only tools, invokes the actual host/product path, grades against planted truth, and deletes the org unconditionally.

## Requirements

SFAEF-150-001. Product agents and product MCP tools MUST remain read-only in all lanes.

SFAEF-150-002. Scratch mutation MUST be performed only by versioned QA setup scripts under `qa-scratch-setup` authority.

SFAEF-150-003. Setup scripts MUST verify a disposable scratch-org marker and refuse any other org.

SFAEF-150-004. Cleanup MUST execute even when setup, product, or grading fails.

SFAEF-150-005. Artifacts MUST record Dev Hub identifier in redacted form, scratch alias/username hash, creation/deletion timestamps, scenario version, Salesforce API/release version, CLI/MCP version, host/model version, and result IDs.

SFAEF-150-006. Ground truth MUST use stable finding IDs and required evidence facts, not exact expected prose.

SFAEF-150-007. Real-org execution MUST scan artifacts for secrets before upload.

SFAEF-150-008. A live test not run MUST be reported as `not_run`, never inferred from fixtures.

## Minimum 1.0 qualification

- At least six deployment scenarios.
- At least seven Apex test scenarios.
- At least six access-path scenarios.
- Actual selected skill contents and context compiler.
- Actual evidence broker path.
- Actual host invocation or a separately labelled harness run.
- Deterministic grade plus nonblocking qualitative review.
