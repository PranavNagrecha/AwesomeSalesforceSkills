# Examples — ADRs

## Example 1: Platform Choice

```markdown
# ADR-0012: Use Platform Events for cross-org async instead of @future

## Status
Accepted — 2026-03-04 — Architecture Review Board

## Context
Customer-ops-processing requires async work triggered from prod but
consumed by an ERP-integration sandbox. @future is in-org only.
Queueable does not support cross-org. We need a mechanism that decouples
producer and consumer across org boundaries with at-least-once delivery.

## Decision
Use Platform Events published from prod and consumed by MuleSoft,
which relays to the sandbox's REST endpoint.

## Consequences
+ Decouples producer and consumer across orgs.
+ At-least-once delivery.
- Platform Event publish limits (daily allocation). Must monitor.
- Replay window = 72 hours; consumers must keep up.

## Alternatives Considered
- @future callout to sandbox — rejected: one org, no retries.
- Queueable chain — rejected: same-org only.
- REST callout only — rejected: no queue; loss risk on sandbox outage.

## Deciders
J. Smith (Tech Lead), R. Patel (Platform Architect)
```

## Example 2: Pattern Adoption

```markdown
# ADR-0003: Adopt Trigger Handler framework across all trigger code

## Status
Accepted — 2026-02-14

## Context
Repo has three different trigger patterns inherited from teams that
merged. Inconsistent logging, no recursion guards in 2/3.

## Decision
Adopt the repo's canonical `TriggerHandler` class from
`templates/apex/TriggerHandler.cls`. One handler per SObject.

## Consequences
+ Consistent logging, recursion guards, bypass path.
- One-time migration cost (estimated 3 sprints).
- Legacy triggers in managed package not addressable.

## Alternatives Considered
- Status quo, allow per-team — rejected: merge debt compounds.
- Write a new framework — rejected: no advantage over existing.
```

## Example 3: Supersession

```markdown
# ADR-0007: (Superseded by ADR-0012) Use @future for cross-org async

## Status
Superseded by ADR-0012 on 2026-03-04.

## Context (as of 2025-09-01)
At the time, cross-org was a single bilateral integration and @future
was sufficient. See ADR-0012 for revised decision under multi-target
requirements.
```
