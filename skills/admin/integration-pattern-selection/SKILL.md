---
name: integration-pattern-selection
description: "Use this skill to select the right Salesforce integration pattern — from point-to-point to event-driven to hub-and-spoke — by applying the official Salesforce two-axis decision framework (integration type × timing) to a business integration scenario. Trigger keywords: integration pattern decision, choose integration approach, Salesforce integration architecture, when to use platform events vs API, integration type selection. NOT for implementation of any specific integration pattern (use domain-specific integration skills), MuleSoft architecture (use architect/mulesoft-anypoint-architecture), or middleware vendor selection. More triggers: integration decision record, Bulk API vs REST for a nightly load, external Id upsert, Named Credential vs Remote Site Setting, platform event vs CDC, who calls whom."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "architect needs to choose between REST API, Platform Events, CDC, and Bulk API for an integration"
  - "stakeholder asks which integration pattern is best for syncing ERP data with Salesforce"
  - "team is debating point-to-point vs hub-and-spoke vs event-driven for a new integration project"
  - "integration requirements have been gathered and now a pattern decision is needed before build"
  - "need to document the rationale for choosing one integration approach over another"
  - "which integration pattern should I use for this requirement"
  - "should this integration be bulk api or rest api"
  - "erp needs to load 300k records into salesforce every night"
  - "write an integration decision record for this interface"
  - "should we use platform events or change data capture for this"
  - "justify why we rejected middleware for this integration"
  - "external system needs to call salesforce which api should it use"
  - "how do I choose between a named credential and a remote site setting"
tags:
  - integration
  - architecture
  - pattern-selection
  - ba-role
  - integration-pattern-selection
  - decision-record
  - bulk-api-vs-rest
  - named-credentials
inputs:
  - "Integration type: Process, Data, or Virtual"
  - "Timing requirement: synchronous (real-time response needed) or asynchronous"
  - "Volume: approximate record count per transaction or batch"
  - "Latency tolerance: real-time, near-real-time, scheduled batch"
  - "Transactional requirements: rollback needed across systems or not"
  - "Whether the external system holds Salesforce record Ids, a stable external key, or neither"
  - "Existing integrations already pointed at the same system"
outputs:
  - "Integration pattern decision record with selected pattern and rationale"
  - "Pattern comparison matrix for the specific integration scenario"
  - "Identified constraints and risks for the selected pattern"
  - "Named Credential and External Credential metadata the chosen pattern requires"
  - "Integration inventory of existing credentials, channels and remote sites"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Integration Pattern Selection

This skill activates when an architect or BA needs to select the right Salesforce integration pattern for a specific business integration scenario. It applies the Salesforce canonical two-axis decision framework to produce a documented pattern decision with rationale, replacing ad-hoc choices that lead to incorrect or unmaintainable integration designs.

**This skill does not hold the routing logic — the decision tree does.** `standards/decision-trees/integration-pattern-selection.md` picks the mechanism: Direction 1 (Q1–Q4) for Salesforce calling out, Direction 2 (Q5–Q9) for an external system writing in, Direction 3 (Q10–Q14) for events and replication, plus the Pattern summary table and the "Named Credentials — always, not sometimes" rule. What this skill adds is the worked application: how to run that tree against one real interface, write the answer down as a decision record that survives the person who made it, and hand the record to whoever builds it. Cite tree question numbers (`integration-pattern-selection.md Q7`); never paraphrase a branch.

Read the tree's directions as three checklists, not as a branching graph. Within a direction every question applies, and each narrows a different axis — latency, auth, payload, volume, idempotency.

---

## Before Starting

Gather this context before working on anything in this domain:

- The Salesforce canonical integration pattern selection uses two primary axes: (1) integration type — Process, Data, or Virtual — and (2) timing — Synchronous or Asynchronous. Every integration scenario maps to one or more of the 6 canonical patterns.
- The most critical constraint: Salesforce cannot participate in distributed transactions initiated outside Salesforce. Hub-and-spoke orchestration that requires cross-system transactional integrity (rollback across multiple systems) must live in middleware — not in Apex.
- Volume is a key threshold: above approximately 2,000 records per transaction, Bulk API 2.0 is required. Synchronous REST/SOAP patterns cannot handle high-volume batch operations reliably. UNVERIFIED (2026-09-04): the 2,000 figure is a rule of thumb, not a documented platform boundary — see the grounded numbers and the tree's own Q5 bands under *Volume Thresholds* below, and route on those.
- This skill is upstream of implementation skills. It produces a decision record — not implementation code.

---

## Questions to Ask Before Configuring

Ask these before naming a mechanism. Each maps to a tree question and to a gotcha in `references/gotchas.md`; an agent that skips them produces a defensible-sounding recommendation with no record of what it rejected.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which way does the data actually move — Salesforce out, external in, or both?" | Direction is the only real branch in the tree, and it decides whether Q1–Q4, Q5–Q9 or Q10–Q14 apply | The `direction` field, and which nine-or-so questions are even in scope |
| "How many rows *and* how many requests per 24 hours, measured in production?" | The 24-hour API allocation is an org-wide, per-licence budget that no single integration's design mentions (gotcha 4) | The `volume` block with two numbers, and the Q5 band that follows from them |
| "Does the external system hold Salesforce record Ids, a stable external key, or neither?" | Q7 splits PATCH by Id, upsert on External Id, and "go back and require an External Id"; an External Id matching more than one record returns HTTP 300, not an error code most clients check (gotcha 8) | `who_knows_ids`, and a *verified* Unique attribute on the key field |
| "Can the same message be delivered twice without harm, and does order matter?" | Q8 and Q12 both hinge on this, and the event bus retains 72 hours of replay and nothing more (gotcha 7) | `idempotency` and `ordering` stated honestly rather than aspirationally |
| "What is the external system's p99 response time, and is a user waiting for it?" | Q1's branches split at 10s and 120s, and the *default* callout timeout is 10 seconds regardless of the 120-second cumulative ceiling (gotcha 5) | `latency`, and whether a trigger is even a legal entry point for the call |
| "Which Named Credential will this use, and who rotates its secret?" | The tree makes this non-negotiable, and a surviving `RemoteSiteSetting` is what the question flushes out (gotcha 10) | The `auth` block the checker script refuses to let you skip |
| "What already integrates with this system, and who owns it?" | An existing interface is a rejected alternative nobody wrote down | The inventory table, produced before anything new is proposed |

What a proper configuration adds over just picking a pattern: the choice is traceable to a numbered tree question, the alternatives carry recorded reasons instead of taste, the volume is a measured number rather than a sandbox one, the credential is named before the build starts, and the record carries an owner and a date at which the choice gets re-examined.

---

## Core Concepts

### The Two-Axis Canonical Pattern Framework

Salesforce architects use two axes for pattern selection:

**Axis 1: Integration Type**
- **Process** — Triggering or monitoring a business process in one system from another (e.g., creating an Order in Salesforce when ERP ships)
- **Data** — Synchronizing data between two systems (e.g., keeping Account data in sync between Salesforce and ERP)
- **Virtual** — Real-time query of external data without storing it in Salesforce (Salesforce Connect / OData)

**Axis 2: Timing**
- **Synchronous** — Response required before the Salesforce transaction completes; the calling system waits
- **Asynchronous** — Response not required immediately; fire-and-forget or event-driven

### The 6 Canonical Patterns

| Pattern | Type | Timing | Primary Use Case |
|---|---|---|---|
| Remote Process Invocation — Request/Reply | Process | Sync | Salesforce calls external system and waits for response |
| Remote Process Invocation — Fire-and-Forget | Process | Async | Salesforce triggers external process with no wait |
| Batch Data Synchronization | Data | Async | Scheduled bulk data sync between systems |
| Remote Call-In | Process | Sync or Async | External system calls Salesforce API |
| UI Update Based on Data Changes | Data | Async/Streaming | External changes reflected in Salesforce UI in real-time |
| Data Virtualization | Virtual | Sync | External data shown in Salesforce without storage |

### The Output Is A Record, Not An Opinion

The deliverable of this skill is a decision record: requirement, direction, volume, latency, idempotency, who holds the Ids, ordering, chosen pattern, the tree questions cited, the rejected alternatives with their reasons, the Named Credential the pattern will authenticate through, an owner and a review date. `references/decision-record-examples.md` holds the shape, three worked records, the auth metadata each one commits to, and the inventory and verification queries.

### Volume Thresholds

The tree's own bands are at `integration-pattern-selection.md` Q5 (< 1k rows/day → REST; 1k–1M → REST Composite; > 1M **or** any bulk upsert/delete → Bulk API 2.0). Read them there. What follows is the grounded arithmetic behind them:

| Fact | Value | Source |
|---|---|---|
| Records per sObject Collections request, and what the whole request costs | Up to 200 records; the entire request counts as a single call toward the API limits | REST API Developer Guide (api_rest.txt L22642–L22652) |
| Subrequests per composite request / per composite graph | 25 / 500 | REST API Developer Guide (api_rest.txt L6288) |
| Bulk API 2.0 batching and 24-hour ceiling | One batch per 10,000 records; 150,000,000 records per rolling 24 hours | Bulk API 2.0 Developer Guide (api_asynch.txt L1242); App Limits Cheat Sheet L779–L782 |
| Concurrent inbound requests lasting 20 seconds or longer | 25 in production and sandboxes, 5 in Developer Edition and Trial orgs | App Limits Cheat Sheet L481–L495 |
| Apex trigger batch size for platform events and Change Data Capture events | 2,000 | App Limits Cheat Sheet L417–L418 |

The old rule of thumb "above 2,000 records use Bulk API" is a reasonable default and is not a documented platform threshold. UNVERIFIED (2026-09-04): no 2,000-record Bulk-API boundary appears in the extracted Bulk API, REST API or App Limits text — 200 is the sObject Collections per-request ceiling and 10,000 is the Bulk batching unit. Route on Q5's bands and the org's measured API allocation, not on 2,000.

UNVERIFIED (2026-09-04): the "up to 250K events/24 hours on standard plans" figure has no grounding in the extracted guides. The App Limits Cheat Sheet's *Platform Event Allocations* chapter (L1244–L1254) names three allocation sets — platform events, Change Data Capture, Pub/Sub API — and carries no numbers; the tree sources them to the Platform Events Developer Guide page `platform_event_limits.htm`, which cannot be fetched here. Measure the org's actual figure from `PlatformEventUsageMetric` (see `references/decision-record-examples.md` § *Verification step*) before putting a number in a record.

---

## Common Patterns

### Pattern: Two-Axis Decision Matrix Application

**When to use:** At the start of any integration design — before any architecture is committed.

**How it works:**
1. Identify the integration type: Is this about triggering/monitoring a process, synchronizing data, or virtualizing read-only data?
2. Identify timing requirement: Does the calling system need a synchronous response, or can it proceed asynchronously?
3. Map to canonical pattern using the two-axis framework
4. Apply secondary constraints: volume, transactional requirements, latency tolerance
5. Document the selected pattern with rationale and known constraints

**Why not the alternative:** Without applying the framework, architects default to the pattern they are most familiar with (usually synchronous REST). This leads to synchronous callouts for high-volume batch scenarios (violating governor limits) or Apex-based orchestration for multi-system transactions (which cannot be rolled back atomically).

---

## Decision Guidance

Resolve the mechanism in `standards/decision-trees/integration-pattern-selection.md`, then use this table only to sanity-check that the tree's answer matches the shape of the requirement. The tree wins where they disagree.

| Integration Scenario | Integration Type | Timing | Recommended Pattern | Key Constraint |
|---|---|---|---|---|
| Salesforce creates Order in ERP when Opp closes | Process | Sync (if confirmation needed) | Remote Process Invocation — Request/Reply | 120s callout timeout; async if confirmation not needed in same transaction |
| ERP price list update needs to refresh Salesforce Products | Data | Async | Batch Data Synchronization | Route on `integration-pattern-selection.md` Q5's bands, not on 2,000 — see the UNVERIFIED note under Volume Thresholds; schedule outside business hours |
| External system creates Salesforce records via API | Process | Sync or Async | Remote Call-In | Use REST API (sync) or Platform Events (async) for external-to-Salesforce |
| Real-time ERP inventory status shown in Salesforce | Virtual | Sync | Data Virtualization | Salesforce Connect External Object; data not stored; query on every page load |
| Notify Salesforce of external shipment events | Process | Async | Remote Process Invocation — Fire-and-Forget or Remote Call-In | Platform Events preferred for loose coupling |
| Multi-system order management needing rollback | Process | Sync | Middleware-orchestrated transaction | Salesforce CANNOT participate in distributed transactions across systems |

---

## Recommended Workflow

1. **Inventory what the org already integrates with** — retrieve the manifest in `references/decision-record-examples.md` § *The Integration Inventory* (`NamedCredential`, `ExternalCredential`, `ConnectedApp`, `PlatformEventChannel`, `PlatformEventChannelMember`, `RemoteSiteSetting`), then run `python3 scripts/check_integration_pattern_selection.py --manifest-dir <retrieved-metadata-dir>` to surface hard-coded endpoints, Legacy-type Named Credentials, platform events left on the publish-immediately default, and callouts made from triggers.
2. **Answer the Questions table above, writing each answer down verbatim** — those seven answers become the top half of the decision record, and the volume answer has to be a measured production number.
3. **Pick the direction, then walk that direction's questions as a checklist** in `standards/decision-trees/integration-pattern-selection.md`: Q1–Q4 for Salesforce → external, Q5–Q9 for external → Salesforce, Q10–Q14 for events and replication. Note the question number beside each answer. Do not restate a branch — cite it.
4. **Write the record** from `templates/integration-pattern-selection-template.md`, filling every field including the rejected alternatives with their reasons and the `auth` block, then lint the copy with `python3 scripts/check_integration_pattern_selection.py --decision-record <file.md>`. Three worked records, filled and grounded, are in `references/decision-record-examples.md`.
5. **Check the choice against `references/gotchas.md`** before the build starts — the ten entries there are the platform behaviours that make a defensible pattern wrong in production, and each names the limit it rests on.
6. **Produce the auth metadata the record commits to** — the `NamedCredential` and `ExternalCredential` XML in `references/decision-record-examples.md` § *Worked Decision 2*, plus `templates/apex/HttpClient.cls` when the pattern is an outbound callout.
7. **Hand off and diarise** — name the follow-on skill or agent from the Hand-Off table in `references/decision-record-examples.md`, set the record's `review_date`, and register the verification queries (`EventBusSubscriber`, `PlatformEventUsageMetric`, `GET /limits/`) as the check that the org agrees with the record.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Integration type classified (Process / Data / Virtual)
- [ ] Timing requirement confirmed (Sync / Async)
- [ ] Volume converted into *requests* per 24 hours and routed on `integration-pattern-selection.md` Q5's bands
- [ ] Transactional requirement checked (single-system or cross-system rollback needed?)
- [ ] Canonical pattern selected from the 6-pattern framework
- [ ] Pattern decision document completed with rationale
- [ ] If hub-and-spoke with cross-system transactions: middleware requirement noted
- [ ] Implementation skill identified for the next phase
- [ ] `direction` chosen before any mechanism was named, and every branch cites a numbered tree question
- [ ] Each rejected alternative carries a reason, not a strikethrough
- [ ] `who_knows_ids` verified, including that any External Id field is actually marked Unique
- [ ] `auth.named_credential` names a real Named Credential; no endpoint is hard-coded and no `RemoteSiteSetting` was left as the answer
- [ ] Existing integrations to the same system were inventoried before this one was proposed
- [ ] The record names an owner and a review date
- [ ] `check_integration_pattern_selection.py --decision-record` passes on the finished record

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Salesforce cannot participate in distributed transactions initiated outside Salesforce** — If an integration requires atomic rollback across Salesforce AND an external system (ERP + Salesforce both commit or both roll back together), this cannot be implemented with Salesforce as the orchestrator. Salesforce Apex transactions can roll back Salesforce DML, but they cannot roll back external system operations. This orchestration must live in middleware (MuleSoft, Boomi, etc.).
2. **Synchronous callout timeout is 120 seconds** — Apex HTTP callouts timeout after 120 seconds. An integration designed as synchronous (Request/Reply) that calls an external system taking more than 120 seconds will fail. High-latency external systems require the Fire-and-Forget pattern with a callback mechanism.
3. **Platform Events are not a guaranteed delivery mechanism without retry handling** — Platform Events have a 72-hour replay window and EventBus.RetryableException provides up to 9 retries. However, if the trigger is suspended after 9 failures, messages are not automatically replayed — manual re-enable of the trigger is required. This means Platform Events are eventually consistent, not guaranteed delivery.
4. **REST volume is capped by the org, not by the endpoint** — the 24-hour API allocation is per-org and per-licence, and there is a separate ceiling of 25 concurrent inbound requests lasting 20 seconds or longer.
5. **A trigger is not a legal place for a synchronous callout** — and pending DML blocks a callout even outside one.
6. **Bulk job evidence expires** — the successful, failed and unprocessed result sets survive 7 days after job completion and no longer.
7. **Replaying from the earliest stored event competes for the allocation it is recovering** — and nothing older than 72 hours exists to replay.
8. **A non-unique External Id turns an upsert into HTTP 300** — a status most clients' success checks do not catch.
9. **`publishBehavior` defaults to `PublishImmediately`** — so an unset event definition fires even when the transaction rolls back.
10. **A surviving Remote Site Setting is a hard-coded endpoint the org still honours** — and its secret is stored somewhere the tree forbids.

Full treatment, with the guide line ranges each rests on, in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration pattern decision record | The deliverable: requirement, direction, volume, latency, idempotency, who knows the Ids, ordering, chosen pattern, tree questions cited, rejected alternatives with reasons, the `auth` block, owner and review date (`templates/integration-pattern-selection-template.md`) |
| Pattern comparison matrix | All viable patterns for the scenario with tradeoffs |
| Integration inventory | Existing Named Credentials, External Credentials, connected apps, platform event channels and remote site settings pointed at the same system |
| Named Credential + External Credential metadata | The deployable auth pair the record's `auth` block commits to (`references/decision-record-examples.md` § *Worked Decision 2*) |
| Verification query set | `EventBusSubscriber`, `PlatformEventUsageMetric` and `GET /services/data/vXX.X/limits/` — how the org is checked against the record after the build |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/decision-record-examples.md` | Writing the decision record itself: the field shape, three worked decisions (nightly Bulk API 2.0 upsert, synchronous validation callout, Closed Won event fan-out), the Named Credential and platform-event XML, the inventory manifest, the `sf project retrieve` commands, and the verification queries. This is this skill's metadata-examples file |
| `references/gotchas.md` | Before committing to a pattern — ten platform behaviours that make a defensible choice wrong in production, each with the guide line range behind it |
| `references/examples.md` | Looking for a short worked selection: sync vs async for an ERP order, a high-volume price sync, and the Apex-as-orchestrator anti-pattern |
| `references/llm-anti-patterns.md` | Reviewing a generated recommendation, and for the five mistakes an assistant makes most often in this domain |
| `references/well-architected.md` | Framing the choice against Reliability, Security and Operational Excellence, and for the source list |
| `templates/integration-pattern-selection-template.md` | Starting a new decision record — copy it, fill it, then lint the copy |
| `scripts/check_integration_pattern_selection.py` | Auditing retrieved metadata for endpoint and event-publish risks (`--manifest-dir`), or linting a finished decision record (`--decision-record`) |

---

## Related Skills

- `integration/event-driven-architecture-patterns` — use after selecting an event-driven pattern for implementation details
- `integration/salesforce-to-salesforce-integration` — use when the integration is cross-org Salesforce-to-Salesforce
- `architect/api-led-connectivity-architecture` — use for multi-system integration governance architecture
- `integration/error-handling-in-integrations` — use to design error recovery for the selected pattern
- `integration/bulk-api-2-patterns` — use when the record lands on `bulk_api_2` and the job lifecycle has to be built
- `integration/rest-api-patterns` — use when the record lands on `rest_api`, and `integration/composite-api-patterns` for the batched form
- `integration/platform-events-integration` — use when the record lands on `platform_event`; `integration/pub-sub-api-patterns` for the external subscriber half
- `integration/change-data-capture-integration` — use when the record lands on `change_data_capture` for replication
- `integration/salesforce-connect-external-objects` — use when Q9 or Q14 says the data should not be copied into Salesforce at all
- `integration/named-credentials-setup` — use to build the `auth` block the record commits to
- `integration/idempotent-integration-patterns` — use when `idempotency` is anything other than `designed_idempotent`
- `apex/callouts-and-http-integrations` — use when the record lands on `apex_callout_named_credential`
- `apex/continuation-callouts` — use when Q1 routes to a long synchronous user-initiated call
- `apex/callout-and-dml-transaction-boundaries` — use when the callout has to coexist with DML in the same transaction
- `integration/mulesoft-salesforce-connector` and `architect/mulesoft-anypoint-architecture` — use when Q14 or a cross-system rollback requirement lands on middleware
- `admin/api-contract-documentation` — use to document the contract the chosen pattern exposes
- `admin/process-automation-selection` — use when the question is which automation surface owns a rule rather than which mechanism moves the data
