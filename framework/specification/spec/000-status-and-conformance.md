# SFAEF-000 — Status, conformance, and requirement governance

## Status

This package is **Draft 0.9.0**. It is complete enough to drive a full local V2 implementation and review, but it has not yet been validated by all target hosts or the scratch-org behavioral lab. Version 1.0 requires the release gates in SFAEF-170.

## Sources of truth

SFAEF-000-001. The numbered specification under `spec/` MUST be the normative product source of truth.

SFAEF-000-002. JSON Schemas under `schemas/` MUST be the normative machine contract for the object they describe.

SFAEF-000-003. Product, agent, command, and MCP files MAY add detail but MUST NOT contradict the numbered specification or schemas.

SFAEF-000-004. Generated catalogs and host packages MUST be derived artifacts. They MUST NOT become independently hand-maintained sources of truth.

SFAEF-000-005. Existing SfSkills skill packages remain the canonical Salesforce knowledge units until individually superseded through the repository’s existing source-governance process.

## Requirement interpretation

SFAEF-000-010. Each normative requirement has a stable ID in the form `SFAEF-<document>-<number>`.

SFAEF-000-011. A conforming implementation MUST maintain a requirement traceability matrix linking each applicable requirement to code, tests, documentation, and review evidence.

SFAEF-000-012. “Not applicable” MUST include a reason and may be rejected during product-owner review.

SFAEF-000-013. A requirement cannot be marked complete solely because a file exists. Completion requires behavior and evidence.

## Conformance profiles

### Knowledge-compatible

A knowledge-compatible adapter:

- discovers skill metadata without loading all skill bodies;
- loads a selected `SKILL.md` and only the references needed for the task;
- preserves package-relative paths and provenance;
- validates skill frontmatter and missing references;
- reports selection reason and context cost.

### Tool-compatible

A tool-compatible adapter additionally:

- negotiates host capabilities;
- validates every tool input and output;
- records origin, timestamp, org association, freshness, pagination, and truncation;
- redacts secrets before persistence or model exposure;
- enforces the declared Salesforce permission class.

### Execution-compatible

An execution-compatible adapter additionally:

- uses the V2 run state machine;
- compiles a bounded context manifest;
- uses structured handoffs rather than transcripts;
- maintains a claim-evidence graph;
- validates the final envelope;
- writes or exports a replayable run bundle.

### Verified-compatible

A verified-compatible adapter additionally passes:

- deterministic unit and schema tests;
- fixture product tests;
- context overflow, distractor, second-task, and compaction tests;
- policy bypass and redaction tests;
- actual host discovery and invocation smoke tests.

### Behaviorally-qualified

A behaviorally-qualified product additionally passes known-truth Salesforce scenarios in a disposable scratch org, with product tools remaining read-only.

## Change control

SFAEF-000-030. Material changes to trust boundaries, evidence precedence, context limits, product mutation, or QA truth criteria MUST include an ADR.

SFAEF-000-031. Specification changes MUST include a changelog entry, affected requirement IDs, migration notes, and test updates.

SFAEF-000-032. A generated artifact drift check MUST fail when tracked generated output does not match canonical source.

SFAEF-000-033. The product owner may reject technically passing work when the behavior violates the product intent, hides uncertainty, or creates a misleading user experience.

## Review authority

The review decision has four states:

- **ACCEPT** — all P0 requirements and applicable release gates pass.
- **ACCEPT WITH CONDITIONS** — no P0 blocker; bounded P1 follow-ups have owners and deadlines.
- **CHANGES REQUESTED** — implementation is directionally correct but not releasable.
- **REJECT** — architecture or safety direction is incompatible with the framework.
