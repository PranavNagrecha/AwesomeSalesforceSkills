# SFAEF-130 — Observability, telemetry, and replay

## Run bundle

A replayable run bundle contains:

- product/agent/schema/policy versions;
- normalized inputs and selected targets;
- plan and state transitions;
- context manifests/checkpoints;
- selected knowledge digests and reasons;
- normalized evidence index and redacted payloads/pointers;
- structured handoffs;
- claim/evidence graph;
- draft, deterministic lint, independent review, and final envelope;
- timing, size, model/host, tool, and truncation metrics.

## Requirements

SFAEF-130-001. Local run artifacts MUST be gitignored by default.

SFAEF-130-002. Telemetry MUST distinguish local product telemetry from any upstream host/vendor telemetry.

SFAEF-130-003. Product telemetry MUST be opt-in beyond essential local diagnostics unless the owner explicitly chooses another policy.

SFAEF-130-004. A run MUST record model, host, adapter, product, schema, policy, and upstream-tool versions when available.

SFAEF-130-005. Raw secret-bearing payloads MUST not be persisted.

SFAEF-130-006. Evidence required for replay MUST include a digest; external pointers MUST include freshness and availability notes.

SFAEF-130-007. Replay MUST not call live tools unless explicitly requested; fixture replay is the default.

SFAEF-130-008. A non-replayable run MUST state why and which assertions cannot be reverified.

## Metrics

Required metrics include:

- context files and estimated tokens by class/stage;
- tool bytes before/after normalization;
- tool calls, errors, retries, pagination, and truncation;
- subagent calls and handoff sizes;
- claims, unsupported claims, contradictions, reviewer findings;
- total and stage durations;
- status and user acceptance signal when available.

SFAEF-130-020. Metrics MUST NOT record hidden chain-of-thought.
