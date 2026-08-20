# SFAEF-030 — Product model and experience contract

## Product definition

A SFAEF product is a versioned user job with:

- a clear outcome;
- typed inputs and execution modes;
- required and optional evidence;
- a context plan;
- agents or deterministic stages;
- read-only tool permissions;
- status and refusal semantics;
- a structured output schema;
- deterministic and behavioral tests;
- success metrics.

A skill, agent, command, or MCP tool alone is not a product.

## Product object

SFAEF-030-001. Every shipped product MUST conform to `schemas/product.schema.json` and have a human specification under `products/`.

Required fields include:

- `id`, `version`, `title`, `lifecycle_status`;
- `user_job`, `personas`, `supported_modes`;
- `command_ids`, `agent_ids`, `tool_ids`;
- `input_schema`, `output_schema`;
- `permissions`, `context_policy`, `evidence_policy`;
- `quality_gates`, `known_limitations`.

## Execution modes

A product declares a subset of:

1. **knowledge-only** — skills and official references; no target evidence.
2. **fixture** — local captured evidence with known provenance.
3. **local-project** — a discovered or explicitly selected Salesforce DX project.
4. **live-read-only** — read-only calls to an authenticated Salesforce org.
5. **hybrid** — local project plus live org/job evidence.
6. **scratch-qa** — product reasoning over evidence produced from a disposable known-truth scenario.

SFAEF-030-010. The mode MUST be recorded in the run envelope.

SFAEF-030-011. A product MUST state which findings are unavailable in each reduced mode.

## Experience anatomy

Every user-facing result SHOULD fit this sequence:

1. **What happened** — one-screen summary.
2. **Evidence status** — modes used, freshness, truncation, missing sources.
3. **Primary findings** — prioritized, claim-linked, confidence-calibrated.
4. **Root-cause structure** — shared causes versus downstream symptoms.
5. **Recommended sequence** — ordered actions with rationale and prerequisites.
6. **Safe verification** — commands/checks shown but not automatically executed unless harmless and explicitly permitted.
7. **Unknowns and contradictions** — what remains unresolved.
8. **Process observations** — useful adjacent observations, never padded.
9. **Evidence review** — pass, pass-with-warnings, or blocked.
10. **Provenance and run ID** — path to the replayable run bundle.

## First-run experience

SFAEF-030-020. Local installation SHOULD produce useful fixture output before Salesforce authentication is required.

SFAEF-030-021. `sfskills-doctor` MUST explain missing dependencies and how they affect capabilities.

SFAEF-030-022. The first useful product run SHOULD require no more than one command and one primary input artifact or job ID.

SFAEF-030-023. The framework MUST not ask users to choose among dozens of agents.

## Status semantics

- **completed** — all load-bearing evidence and review gates for the requested scope passed.
- **partial** — useful output exists, but one or more material dimensions are missing, stale, truncated, contradictory, or unsupported by the host.
- **refused** — the request is unsafe, ambiguous, outside product scope, or missing a hard prerequisite.
- **failed** — an unexpected system or tool error prevented a valid result.

SFAEF-030-030. `completed` MUST NOT be used when the evidence reviewer has a blocking finding.

SFAEF-030-031. `partial` MUST enumerate impact by dimension rather than merely lowering confidence.

## Product portfolio

### V2 release cohort

- P01 Deployment Failure Triage
- P02 Apex Test Failure Triage
- P03 Access Path Explainer
- P04 Change Impact Planner
- P05 Automation Transaction Profiler
- P06 Release Readiness Review

### Expansion cohort

- P07 Security Posture Review
- P08 Integration Incident Triage
- P09 Data Migration Reconciliation
- P10 Org Health Assessment
- P11 Agentforce Quality Engineer
- P12 Multi-Org Drift Analysis

The portfolio sequence is defined in `adoption/IMPLEMENTATION_SEQUENCE.md`.
