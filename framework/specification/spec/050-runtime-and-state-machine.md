# SFAEF-050 — Runtime, planning, and state machine

## Run lifecycle

```text
created
  -> preflighted
  -> input_validated
  -> planned
  -> context_ready
  -> evidence_gathering
  -> evidence_ready
  -> diagnosing
  -> draft_ready
  -> reviewing
  -> completed | partial | refused | failed
```

A run may enter `checkpointed` from any nonterminal state and resume only through validated rehydration.

## Requirements

SFAEF-050-001. Every product invocation MUST create a run ID before tool use.

SFAEF-050-002. Every state transition MUST be recorded with time, actor, reason, and previous state.

SFAEF-050-003. Invalid transitions MUST fail deterministically.

SFAEF-050-004. Input validation MUST occur before agent delegation or Salesforce access.

SFAEF-050-005. Preflight MUST resolve host capability, product version, requested execution mode, project selection, org identity, index state, and permission policy.

SFAEF-050-006. Planning MUST declare stages, agents, tools, evidence needs, context budgets, optional enrichments, and stop conditions.

SFAEF-050-007. A plan MUST NOT silently add tools or permissions after execution begins.

SFAEF-050-008. A product MAY re-plan when evidence invalidates the initial plan, but the delta and reason MUST be recorded.

SFAEF-050-009. Retry behavior MUST be limited to declared transient failures, bounded, and recorded.

SFAEF-050-010. A human approval request MUST include the exact requested action, target identity, authority, and consequence. V2 diagnostic products MUST not request approval for Salesforce mutation because mutation is out of scope.

## Terminal status rules

SFAEF-050-020. `completed` requires valid output, no blocking evidence-review finding, no undisclosed hard prerequisite failure, and no silent truncation.

SFAEF-050-021. `partial` requires useful validated output and an explicit impact statement for every missing, stale, contradictory, or truncated dimension.

SFAEF-050-022. `refused` is required for unsafe requests, ambiguous target identity that cannot be resolved safely, prohibited authority, or missing mandatory user input.

SFAEF-050-023. `failed` is reserved for unexpected system/tool failure after safe handling; it MUST include a sanitized error class and retry guidance.

## Idempotence and resumption

SFAEF-050-030. Replaying a run with the same immutable fixture evidence and product version SHOULD produce structurally equivalent claims and status.

SFAEF-050-031. Resumption MUST validate product version, schema version, target identity, evidence freshness, and policy version before continuing.

SFAEF-050-032. A resumed run MUST not inherit a previous run's org, project, evidence, or unverified memory by default.
