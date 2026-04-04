---
name: callouts-and-http-integrations
description: "Use when building, reviewing, or debugging outbound Apex HTTP callouts, Named Credentials, request/response handling, timeout behavior, or mock-based tests. Triggers: 'HttpRequest', 'Named Credential', 'callout exception', 'uncommitted work pending', 'HttpCalloutMock'. NOT for inbound Apex REST service design or non-HTTP integration architecture."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
tags:
  - http-callout
  - named-credentials
  - httprequest
  - httpcalloutmock
  - integration-reliability
triggers:
  - "how should I use Named Credentials in Apex callouts"
  - "uncommitted work pending before callout"
  - "HttpRequest timeout and error handling pattern"
  - "how do I test Apex HTTP callouts with mocks"
  - "callout exception in queueable or trigger flow"
  - "how to call external API from apex"
inputs:
  - "authentication model and whether the target system uses per-user or org-wide identity"
  - "transaction context such as trigger, Queueable, controller, or Batch"
  - "timeout, retry, and failure-reporting expectations"
outputs:
  - "callout design recommendation"
  - "review findings for security, transaction safety, and testability"
  - "Apex callout scaffold using Named Credentials and mocks"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when an Apex integration needs to leave Salesforce safely. The aim is to use Named Credentials correctly, keep authentication and endpoint management out of code, separate callouts from unsafe transaction contexts, and make failure modes visible and testable.

## Before Starting

- Is this callout made from a trigger, a user-facing controller, a Queueable, a Batch job, or a scheduled process?
- Should authentication be org-wide or per-user, and is the target endpoint already modeled as a Named Credential with an External Credential?
- What is the acceptable timeout, retry strategy, and failure destination if the remote system is unavailable?

## Core Concepts

### Named Credentials Are The Default Endpoint Boundary

Salesforce recommends Named Credentials for outbound authentication and endpoint management. Modern setups also use External Credentials and User External Credentials for principal mapping and secret handling. In practice, this means Apex should usually call `callout:My_Named_Credential/...` instead of embedding URLs, tokens, or headers directly in code.

### Transaction Context Determines Whether The Callout Is Safe

Callouts from the wrong place cause production pain. A trigger or synchronous transaction that already performed DML can hit "uncommitted work pending" or create user-facing latency. The right fix is often to persist the business data first, then hand off outbound work to Queueable Apex with `Database.AllowsCallouts`.

### HTTP Work Needs Explicit Failure Handling

A successful callout is not just "no exception thrown." You must check status codes, timeouts, payload parsing, and idempotency assumptions. Set an explicit timeout, classify retryable versus non-retryable errors, and log or surface failures with enough context to support operations.

### Tests Must Mock The Remote System

Real HTTP traffic is not allowed in Apex tests. `Test.setMock(HttpCalloutMock.class, mock)` should cover both success and failure responses so integration logic can be exercised deterministically.

## Common Patterns

### Named Credential Service Wrapper

**When to use:** A service class owns outbound communication to one remote system.

**How it works:** Keep endpoint paths relative to a Named Credential, centralize request construction, set timeouts explicitly, and throw a domain-specific exception when the response is unusable.

**Why not the alternative:** Hardcoded endpoints and inline auth headers create release drift and security risk across environments.

### Queueable After Commit For Outbound Sync

**When to use:** A trigger or controller must perform a callout after saving Salesforce data.

**How it works:** Enqueue one Queueable with IDs, re-query inside the job, make the callout there, and update integration status in a controlled way.

### Mock-Driven Test Matrix

**When to use:** The callout code must prove success, non-200 responses, and timeout-like failures.

**How it works:** Build focused `HttpCalloutMock` classes and assert on side effects, not just on response parsing.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Outbound HTTP integration with managed credentials | Named Credential + External Credential | Keeps secrets and endpoint config out of Apex |
| Trigger or save transaction needs to notify an external API | Queueable + `Database.AllowsCallouts` | Safe post-commit boundary for callouts |
| Small synchronous lookup that must block the user | Direct callout with timeout and safe error messaging | Sometimes acceptable when latency is part of the workflow |
| Tests need to validate HTTP behavior | `HttpCalloutMock` with explicit success and failure cases | Deterministic and CI-safe |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] Endpoints use Named Credential `callout:` syntax instead of hardcoded URLs.
- [ ] Authentication details are outside Apex code.
- [ ] Queueable or Batch contexts that make callouts implement `Database.AllowsCallouts`.
- [ ] Requests set explicit timeouts and inspect HTTP status codes.
- [ ] Trigger-driven integrations do not perform direct outbound HTTP in the trigger transaction.
- [ ] Tests use mocks for both happy-path and failure-path callout scenarios.

## Salesforce-Specific Gotchas

1. **Callouts after prior DML in the same transaction can fail with uncommitted-work behavior** — the safe design is usually to move the callout into Queueable Apex.
2. **Queueables that make callouts need `Database.AllowsCallouts`** — forgetting the interface turns a valid design into a runtime failure.
3. **Hardcoded endpoints sabotage environment promotion** — sandbox, UAT, and production URLs drift unless endpoint management is externalized.
4. **A 200-series response is not the whole contract** — integration code still needs schema validation and error-path handling for malformed responses.

## Output Artifacts

| Artifact | Description |
|---|---|
| Callout review | Findings on endpoint security, transaction safety, timeout handling, and tests |
| Callout scaffold | Named Credential-based service wrapper with response classification and mock hooks |
| Retry/failure notes | Guidance on which failures should be retried, surfaced to users, or logged for operations |

## Related Skills

- `apex/async-apex` — use when the core design choice is whether this callout belongs in Queueable, Batch, or Scheduled Apex.
- `apex/exception-handling` — use when integration failures need a cleaner classification, logging, or boundary-specific error mapping.
- `apex/test-class-standards` — use alongside this skill to improve `HttpCalloutMock` coverage and async callout assertions.
