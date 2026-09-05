---
name: callouts-and-http-integrations
description: "Use when building, reviewing, or debugging outbound Apex HTTP callouts, Named Credentials, request/response handling, timeout behavior, or mock-based tests. Triggers: 'HttpRequest', 'Named Credential', 'callout exception', 'uncommitted work pending', 'HttpCalloutMock', 'uncommitted work pending', 'Database.AllowsCallouts', 'callout:', 'setTimeout', 'CalloutException', 'idempotency key', 'retry on 500'. NOT for exposing Apex as an inbound REST endpoint — use apex/apex-rest-services. NOT for SOAP callouts generated from a WSDL — use apex/apex-wsdl2apex-patterns. NOT for the per-transaction callout ceiling or moving callouts async to stay under it — use integration/callout-limits-and-async-patterns."
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
  - "callout fails with You have uncommitted work pending"
  - "retry an Apex HTTP callout after a 500 without double-posting"
  - "set a timeout on an Apex HttpRequest and stay under the callout limit"
  - "why did my GET callout arrive as a POST"
  - "deploy a NamedCredential and ExternalCredential with the Apex class"
  - "callout from a trigger after insert"
  - "classify HTTP status codes as retryable or not in Apex"
  - "Apex callout response too large heap size"
inputs:
  - "authentication model and whether the target system uses per-user or org-wide identity"
  - "transaction context such as trigger, Queueable, controller, or Batch"
  - "timeout, retry, and failure-reporting expectations"
outputs:
  - "callout design recommendation"
  - "review findings for security, transaction safety, and testability"
  - "Apex callout scaffold using Named Credentials and mocks"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when an Apex integration needs to leave Salesforce safely. The aim is to use Named Credentials correctly, keep authentication and endpoint management out of code, separate callouts from unsafe transaction contexts, and make failure modes visible and testable.

## Before Starting

- Is this callout made from a trigger, a user-facing controller, a Queueable, a Batch job, or a scheduled process?
- Should authentication be org-wide or per-user, and is the target endpoint already modeled as a Named Credential with an External Credential?
- What is the acceptable timeout, retry strategy, and failure destination if the remote system is unavailable?

## Questions to Ask Before Configuring

Ask these before writing the first `HttpRequest`. Each one maps to a gotcha in
`references/gotchas.md`; an agent that skips them produces a callout that works in a scratch org and
double-posts in production.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is already pending in the transaction that reaches this code — DML, an enqueued job, a batch, a `@future`, an email?" | All five block a later callout in the same transaction, not just DML (Gotcha 1) | The async boundary: callout-then-DML inline, or hand it to a Queueable |
| "Is this POST/PUT safe to send twice, and does the remote system accept an idempotency key?" | A 5xx or a transport failure means *unknown*, not *failed*; retrying without a key is how you double-bill (Gotcha 11, anti-pattern 7) | Either a key header and a retry policy, or a documented no-retry decision |
| "How many records can arrive in one invocation, and how slow is the remote system per call?" | 100 callouts and 120 s cumulative are per transaction, so `n × timeout ≤ 120,000` decides the chunk size (Gotcha 3) | The per-job record budget and the `setTimeout` value that fits it |
| "What does each status code mean *for this integration* — 401, 409, 422, 429, 503?" | Retryable vs non-retryable cannot be inferred from the number alone; a 401 retried is a lockout (Gotcha 10) | The classification table in `references/examples.md` §3, which the tests then mirror |
| "Org-wide credential or per-user, and who grants principal access in each org?" | `NamedPrincipal` vs `PerUserPrincipal` changes who the integration works for, and the `principal` field was removed in API 58.0 (Gotcha 8) | The External Credential shape plus the permission set that grants it |
| "How large is the biggest request and response, and is this path sync or async?" | 6 MB sync / 12 MB async caps the payload *and* counts against heap (Gotcha 5) | A paging decision, or a decision to run async for the doubled ceiling |
| "Where does a permanent failure land, and who looks at it?" | A swallowed `CalloutException` is invisible; `AsyncApexJob` alone does not say which record failed | The failure field or log object, and the query operations will run |

What a proper callout design adds over just calling `Http.send()`: the endpoint and secret live in a
Named Credential that can be repointed per org without a code deploy, every status code has a
declared retry decision that a test proves, retries carry an idempotency key so a lost reply cannot
double-write, and a permanent failure leaves a queryable row instead of a debug-log line.

---

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
| Remote call is slow and must return to a user-facing page | Continuation | Only mechanism that suspends the request; costs its own limit set — 3 parallel / 3 chained callouts, 1 MB response, `setTimeout` ignored (apexdev L36301–36315). See apex/continuation-callouts |
| More records than the transaction's callout budget | Chunk in the Queueable, carry the remainder into the single allowed re-enqueue | 100 callouts per transaction (apexdev L35844); async context allows one `System.enqueueJob` |
| The "we never found out" case must leave a row | `System.Finalizer` on the Queueable | The parent's own DML is rolled back when `execute()` dies. See apex/apex-transaction-finalizers |
| Remote system requires mutual TLS | Named Credential `ClientCertificate` parameter, or `setClientCertificateName` | Keeps the private key in Certificate and Key Management, never in Apex |


## Recommended Workflow

1. **Answer the questions above and fill the worksheet.** `templates/callouts-and-http-integrations-template.md` captures the identity model, the header contract, and the retryable status list — the three things reviewers ask for and generated code never has.
2. **Fix the transaction boundary before writing any HTTP code.** Decide inline callout-then-DML, Queueable, `@Future(callout=true)`, or Continuation. If a trigger is anywhere on the path, the answer is async (`references/gotchas.md` Gotcha 1 and 7).
3. **Write the credential metadata first.** Take the `NamedCredential` + `ExternalCredential` XML from `references/code-examples.md` §4; the Apex must never contain a literal `https://` endpoint or an `Authorization` header it built itself.
4. **Write the service against `templates/apex/HttpClient.cls`.** Copy `BillingApiService.cls` from `references/code-examples.md` §1: explicit `setTimeout`, idempotency-key header, typed response DTO, and a `classify()` method whose branches match the table in `references/examples.md` §3. Leave `retryOnTransient(false)` — backoff belongs on the job boundary, not in a busy-wait.
5. **Write the async wrapper and the test class together.** `BillingSyncQueueable` (`implements Queueable, Database.AllowsCallouts`, callouts before DML, bounded re-enqueue) and `BillingApiServiceTest`, which must cover 200, 5xx, 401, a malformed 2xx and a transport failure. `Test.startTest()` goes before `Test.setMock(...)`, with the data setup outside the block.
6. **Run the checker.** `python3 skills/apex/callouts-and-http-integrations/scripts/check_callouts_and_http_integrations.py --manifest-dir force-app` — it flags literal endpoints, callouts in loops, DML before a callout, synchronous callouts on a trigger path, a missing `setTimeout`, a body on a GET, tests without `Test.setMock`, and swallowed `CalloutException`s.
7. **Deploy and verify.** `sf project deploy start -x manifest/package.xml`, then `sf apex run test -n BillingApiServiceTest -r human -w 10 -c`, then the `NamedCredential` and `AsyncApexJob` checks in `references/code-examples.md` §9 — a Named Credential that resolves to the wrong endpoint is the failure that reaches production silently.
8. **Walk the Review Checklist below** before handing the change to a reviewer.

---

## Review Checklist

- [ ] Endpoints use Named Credential `callout:` syntax instead of hardcoded URLs.
- [ ] Authentication details are outside Apex code.
- [ ] Queueable or Batch contexts that make callouts implement `Database.AllowsCallouts`.
- [ ] Requests set explicit timeouts and inspect HTTP status codes.
- [ ] Trigger-driven integrations do not perform direct outbound HTTP in the trigger transaction.
- [ ] Tests use mocks for both happy-path and failure-path callout scenarios.
- [ ] Every status code the integration can receive has a declared retryable / non-retryable decision, and a test asserts it.
- [ ] `401` and `403` are never retried.
- [ ] Any retried POST or PUT carries a stable idempotency key.
- [ ] No `setBody` on a request whose method is `GET`.
- [ ] Callouts are not inside a loop that can exceed the per-transaction budget; the record count per job is bounded.
- [ ] `Test.startTest()` appears before `Test.setMock(...)`, with test-data DML outside the start/stop block.
- [ ] No `catch (CalloutException e) {}` that logs nothing and rethrows nothing.
- [ ] No savepoint is still active when the callout runs.

## Salesforce-Specific Gotchas

The full list with **What happens / When it occurs / How to avoid** and guide line numbers is in
`references/gotchas.md` (12 entries). The ones that most often survive review:

1. **The blocker is "pending work", not "DML".** Enqueuing a job, running `Database.executeBatch`, calling a `@future` method or sending email all block a later callout the same way an `insert` does (apexdev L35379–35380).
2. **`setTimeout` is a connect timeout.** It bounds establishing the connection, not the transfer (apexrefguide L216720–216723). The real ceiling is 120 s cumulative across the transaction (apexdev L35856–35857).
3. **A body on a GET silently becomes a POST** (apexdev L35377–35378) — no exception, no warning.
4. **The 6 MB / 12 MB payload cap is also a heap cap** (cheat sheet L389–391, L415), so a large response leaves almost nothing for parsing it.
5. **Queueables that make callouts need `Database.AllowsCallouts`** (apexdev L16164–16166); future methods need `@Future(callout=true)`, whose default is `false` (apexdev L5134–5135).
6. **An unreleased savepoint blocks the callout even after a rollback** — a different `CalloutException` with a different message (apexdev L8747–8748).
7. **A 200-series response is not the whole contract** — a 200 carrying an HTML maintenance page is the case that reaches production.

## Output Artifacts

| Artifact | Description |
|---|---|
| Callout review | Findings on endpoint security, transaction safety, timeout handling, and tests |
| Callout scaffold | Named Credential-based service wrapper with response classification and mock hooks |
| Retry/failure notes | Guidance on which failures should be retried, surfaced to users, or logged for operations |

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are writing the code — service, Queueable, test class, `NamedCredential` / `ExternalCredential` / `RemoteSiteSetting` XML, `-meta.xml`, `package.xml`, deploy and verification commands |
| `references/gotchas.md` | A callout fails in a way the code does not explain — 12 grounded platform behaviours with guide line numbers |
| `references/examples.md` | You want the narrative walk-through, the status-code classification table, or the mutual-TLS variant |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated callout code, or self-checking your own output (8 anti-patterns with detection hints) |
| `references/well-architected.md` | You are justifying the async boundary, the identity model, or Continuation vs Queueable — and need the source list |
| `templates/callouts-and-http-integrations-template.md` | You are capturing the endpoint, identity, header and retry decisions before writing code |

---

## Related Skills

- `apex/async-apex` — use when the core design choice is whether this callout belongs in Queueable, Batch, or Scheduled Apex.
- `apex/exception-handling` — use when integration failures need a cleaner classification, logging, or boundary-specific error mapping.
- `apex/test-class-standards` — use alongside this skill to improve `HttpCalloutMock` coverage and async callout assertions.
- `apex/apex-http-callout-mocking` — owns `HttpCalloutMock` in depth: static-resource mocks, per-endpoint routing, multi-response sequences.
- `apex/callout-and-dml-transaction-boundaries` — owns the transaction-ordering analysis when the fix is not simply "move it to a Queueable".
- `apex/apex-callout-retry-and-resilience` — owns backoff strategy, circuit breaking, and dead-lettering once the retry decision is made.
- `apex/apex-transaction-finalizers` — use when the failure that must be recorded is the one that kills the Queueable itself.
- `apex/continuation-callouts` — use when a long-running call must return to a user-facing page rather than run in a job.
- `integration/named-credentials-setup` — owns the Setup-side configuration of Named Credentials, External Credentials and Auth. Providers.
- `integration/callout-limits-and-async-patterns` — use when the per-transaction callout ceiling itself is the design constraint.
- `integration/mutual-tls-callouts` — use when the remote system requires client-certificate authentication.
- `apex/apex-rest-services` — the inbound direction: exposing Apex as a REST endpoint rather than calling one.
