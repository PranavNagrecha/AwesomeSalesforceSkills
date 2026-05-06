---
name: omnistudio-error-handling-patterns
description: "Use when designing fault behavior across Integration Procedures, DataRaptors, OmniScripts, and FlexCards — error routing, user-facing messaging, retry semantics, and idempotency. Triggers: 'omnistudio error', 'integration procedure fault', 'dataraptor error handling', 'omniscript retry', 'flexcard action failure'. NOT for general Apex exception design or Flow fault paths."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
  - Operational Excellence
triggers:
  - "integration procedure is failing silently"
  - "how should omniscript handle a callout error"
  - "dataraptor returns empty when source has errors"
  - "flexcard action failed but UI stayed happy"
  - "retry semantics across omnistudio callouts"
tags:
  - omnistudio
  - error-handling
  - integration-procedure
  - idempotency
  - retry
inputs:
  - "integration procedure, dataraptor, and omniscript in scope"
  - "downstream systems and their failure modes"
  - "user-facing surfaces and what they should show on failure"
outputs:
  - "fault routing plan per component"
  - "retry and idempotency strategy"
  - "user-message catalog for error states"
dependencies: []
runtime_orphan: true
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# OmniStudio Error Handling Patterns

OmniStudio components fail in more ways than they succeed — callouts time out, DataRaptors hit governor limits, OmniScripts abandon mid-flow, FlexCard actions return errors the card ignores. The default behavior across these tools is to surface a generic "An error occurred" or — worse — to silently complete with empty data. Good error handling across OmniStudio means naming each failure boundary, deciding who catches it, and deciding what the user sees.

Integration Procedures are the first and most important error boundary. They compose Apex, DataRaptors, HTTP actions, and conditional steps, and every one of those can fail. IP steps have a `Fail On Step Error` flag and a `Response Action` branch — both must be set deliberately. An IP that leaves these defaults often swallows downstream failures and returns a 200 with incomplete data.

DataRaptors are the second boundary. Extract operations that hit SOQL governor limits will throw; Load operations that violate validation rules surface field-level errors. Unless the caller inspects the response, these are lost.

OmniScripts sit closest to the user. They should translate technical errors into business-readable messages, let the user retry where safe, and preserve filled-in data so the user is not punished for a transient failure.

---

## Before Starting

- Map each OmniScript/FlexCard action to the Integration Procedure or DataRaptor it invokes.
- List the downstream systems and their realistic failure modes (timeout, 4xx, 5xx, partial success).
- Decide which failures are user-recoverable (retry) and which require escalation.

## Core Concepts

### Failure Boundaries

1. **HTTP Action** — callout failures, timeouts, non-2xx responses.
2. **DataRaptor** — governor limits, validation errors, mapping failures.
3. **Integration Procedure** — any step can bubble; IP-level `Response Action` decides routing.
4. **OmniScript step** — action returns an error; step can branch to a fault screen or loop back.
5. **FlexCard action** — action handler returns a fault; card decides whether to show error state or silently fail.

### Response Action Routing

Every IP step has four relevant controls:
- `Fail On Step Error` — if false, step error is ignored and IP continues.
- `Response Action` — "Cache Then Ignore" / "Terminate IP" / "Continue on Error".
- `Send JSON Node` — controls what response payload is returned on failure.
- `Send JSON Path` — controls partial result shape.

Setting these to "Terminate on Error" for downstream-critical steps and explicit continue for best-effort steps is the difference between a resilient IP and a silent one.

### Idempotency Contract

Any IP that writes must be idempotent at the callout or the caller must track attempts. Use an external ID, a correlation ID in the payload, or a DataRaptor load that treats upsert + external ID as its signature.

---

## Common Patterns

### Pattern 1: Fail-Fast IP With User-Facing Fault Screen

Critical write steps terminate the IP on error. The OmniScript inspects the IP response envelope and branches to a fault screen that summarizes what failed, what was saved, and what the user should do next.

### Pattern 2: Best-Effort Enrichment Step

An enrichment step (e.g. fetching a nice-to-have third-party score) is marked `Continue on Error` with a default value. The consumer treats missing enrichment as normal.

### Pattern 3: Retry With Correlation ID

HTTP actions write a correlation ID into the payload. On a retryable failure (timeout, 502, 503), the OmniScript allows the user to retry — the downstream system deduplicates by correlation ID.

### Pattern 4: Compensating DataRaptor Load

A multi-step write that can partially succeed uses a compensating DataRaptor load on failure to roll back committed records, or flags them for async cleanup.

### Pattern 5: Explicit User Messages

Every recoverable failure maps to a business-readable message and an action the user can take. Unrecoverable failures go to a support pathway (case creation, hotline, Slack channel) with enough diagnostic data attached.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Step is critical to downstream data integrity | `Terminate on Error` + fault screen | Avoid half-written records |
| Step is enrichment only | `Continue on Error` + default value | Do not block user for nice-to-have |
| Downstream system is idempotent-by-external-id | Retry enabled, correlation ID in payload | Safe user-initiated retry |
| Write spans multiple systems | Compensating DataRaptor or async cleanup | Partial success is the default |
| User reaches unrecoverable state | Fault screen + support escalation | Do not strand the user |

## Review Checklist

- [ ] Every IP step has deliberate `Fail On Step Error` and `Response Action` settings.
- [ ] Critical writes terminate the IP on failure.
- [ ] User-facing surfaces render a fault screen, not a generic alert.
- [ ] Every retry path is idempotent (external ID or correlation ID).
- [ ] Partial-success paths have a compensating action.
- [ ] Errors are logged with correlation IDs.

## Recommended Workflow

1. Inventory components — IPs, DRs, OmniScripts, FlexCard actions.
2. Classify each step as critical or best-effort.
3. Set `Fail On Step Error` and `Response Action` accordingly.
4. Write the user-facing fault surface and the support escalation path.
5. Add correlation IDs and idempotency checks to every writable callout.
6. Validate with negative-path test runs.

---

## Salesforce-Specific Gotchas

1. IP step defaults silently swallow failures — unset defaults must be corrected per step.
2. DataRaptor Extract returns empty-but-OK on row-level failures.
3. OmniScript navigation to "fault step" does not preserve user-entered data unless you wire it.
4. FlexCard `On Failure` branches are often left empty in auto-generated actions.
5. Retried HTTP actions without correlation IDs produce duplicate writes downstream.

## Proactive Triggers

- Step with `Fail On Step Error = false` writing to a record → Flag Critical.
- No `On Failure` branch on a FlexCard save action → Flag High.
- Retry-enabled action without correlation ID → Flag High.
- OmniScript with no fault step in a multi-callout flow → Flag High.
- IP returns 200 with `errors` array the caller ignores → Flag High.

## Output Artifacts

| Artifact | Description |
|---|---|
| Fault routing table | Per-step `Fail On` + `Response Action` + user message |
| Retry and idempotency design | Correlation ID strategy |
| Compensating action plan | Rollback or async cleanup per partial-success scenario |

## Related Skills

- `omnistudio/integration-procedures` — IP step design.
- `omnistudio/dataraptor-patterns` — DR error modes.
- `omnistudio/omnistudio-debugging` — tracing faults end to end.
- `integration/retry-and-backoff-patterns` — retry semantics for downstream systems.
