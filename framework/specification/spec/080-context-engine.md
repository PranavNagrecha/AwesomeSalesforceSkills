# SFAEF-080 — Context engine, budgets, and compaction resilience

## Context classes

- **Control context** — product/agent contract, permissions, output schema.
- **Core knowledge** — minimal Salesforce guidance required for the job.
- **Conditional knowledge** — selected from observed failure/evidence classes.
- **Evidence context** — normalized facts and bounded excerpts.
- **Working state** — claims, unknowns, contradictions, and plan status.
- **Output reserve** — capacity protected for final synthesis and review.

## Default budget

For flagship products, starting defaults are:

- 3–5 core knowledge files;
- target total knowledge/reference files: at most 8;
- hard limit: 12 unless explicit overflow is returned;
- one injected MCP page: at most 32 KiB;
- no full subagent transcript;
- at least 15% of available working context reserved for output/review.

These are defaults, not claims about every model's tokenization.

## Requirements

SFAEF-080-001. Every stage MUST have a context manifest.

SFAEF-080-002. Every context item MUST include source, reason, priority, estimated cost, digest, and stage.

SFAEF-080-003. Required control context MUST be loaded before optional knowledge.

SFAEF-080-004. Evidence summaries MUST preserve IDs, counts, severity, timestamps, target identity, and contradiction links.

SFAEF-080-005. Silent truncation is prohibited. Truncation MUST include original count/bytes, retained count/bytes, strategy, and continuation token when available.

SFAEF-080-006. Context selection MUST be stable for equivalent inputs and versions, subject to documented model ranking only for conditional tie-breaking.

SFAEF-080-007. A second unrelated user task MUST start a new run context unless the user explicitly links it to the current run.

## Compaction

SFAEF-080-020. Before host compaction where observable, the framework SHOULD write a context checkpoint containing run state, target identities, selected knowledge, evidence IDs, claims, unknowns, policy version, and next stage.

SFAEF-080-021. A checkpoint MUST NOT contain complete raw transcripts or secrets.

SFAEF-080-022. After compaction, the runtime MUST rehydrate from the checkpoint and evidence store, then validate continuity before continuing.

SFAEF-080-023. If the host does not expose compaction events, the runtime SHOULD checkpoint at deterministic stage boundaries.

## Quality tests

SFAEF-080-030. Every flagship product MUST test irrelevant distractors, oversized evidence, duplicate symptoms, contradictory evidence, long first task followed by a second task, and checkpoint/resume.

SFAEF-080-031. Context efficiency MUST be reported with quality; lower context is not a success if required finding recall drops.
