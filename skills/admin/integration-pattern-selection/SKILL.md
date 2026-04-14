---
name: integration-pattern-selection
description: "Use this skill to select the right Salesforce integration pattern — from point-to-point to event-driven to hub-and-spoke — by applying the official Salesforce two-axis decision framework (integration type × timing) to a business integration scenario. Trigger keywords: integration pattern decision, choose integration approach, Salesforce integration architecture, when to use platform events vs API, integration type selection. NOT for implementation of any specific integration pattern (use domain-specific integration skills), MuleSoft architecture (use architect/mulesoft-anypoint-architecture), or middleware vendor selection."
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
tags:
  - integration
  - architecture
  - pattern-selection
  - ba-role
  - integration-pattern-selection
inputs:
  - "Integration type: Process, Data, or Virtual"
  - "Timing requirement: synchronous (real-time response needed) or asynchronous"
  - "Volume: approximate record count per transaction or batch"
  - "Latency tolerance: real-time, near-real-time, scheduled batch"
  - "Transactional requirements: rollback needed across systems or not"
outputs:
  - "Integration pattern decision record with selected pattern and rationale"
  - "Pattern comparison matrix for the specific integration scenario"
  - "Identified constraints and risks for the selected pattern"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-14
---

# Integration Pattern Selection

This skill activates when an architect or BA needs to select the right Salesforce integration pattern for a specific business integration scenario. It applies the Salesforce canonical two-axis decision framework to produce a documented pattern decision with rationale, replacing ad-hoc choices that lead to incorrect or unmaintainable integration designs.

---

## Before Starting

Gather this context before working on anything in this domain:

- The Salesforce canonical integration pattern selection uses two primary axes: (1) integration type — Process, Data, or Virtual — and (2) timing — Synchronous or Asynchronous. Every integration scenario maps to one or more of the 6 canonical patterns.
- The most critical constraint: Salesforce cannot participate in distributed transactions initiated outside Salesforce. Hub-and-spoke orchestration that requires cross-system transactional integrity (rollback across multiple systems) must live in middleware — not in Apex.
- Volume is a key threshold: above approximately 2,000 records per transaction, Bulk API 2.0 is required. Synchronous REST/SOAP patterns cannot handle high-volume batch operations reliably.
- This skill is upstream of implementation skills. It produces a decision record — not implementation code.

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

### Volume Thresholds

- Up to 200 records per transaction: SOAP/REST API or Platform Events
- 2,001–10M records: Bulk API 2.0 required (asynchronous CSV-based)
- Real-time streaming: Platform Events or CDC — up to 250K events/24 hours on standard plans
- Above platform limits: middleware layer required

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

| Integration Scenario | Integration Type | Timing | Recommended Pattern | Key Constraint |
|---|---|---|---|---|
| Salesforce creates Order in ERP when Opp closes | Process | Sync (if confirmation needed) | Remote Process Invocation — Request/Reply | 120s callout timeout; async if confirmation not needed in same transaction |
| ERP price list update needs to refresh Salesforce Products | Data | Async | Batch Data Synchronization | Bulk API 2.0 above 2,000 records; schedule outside business hours |
| External system creates Salesforce records via API | Process | Sync or Async | Remote Call-In | Use REST API (sync) or Platform Events (async) for external-to-Salesforce |
| Real-time ERP inventory status shown in Salesforce | Virtual | Sync | Data Virtualization | Salesforce Connect External Object; data not stored; query on every page load |
| Notify Salesforce of external shipment events | Process | Async | Remote Process Invocation — Fire-and-Forget or Remote Call-In | Platform Events preferred for loose coupling |
| Multi-system order management needing rollback | Process | Sync | Middleware-orchestrated transaction | Salesforce CANNOT participate in distributed transactions across systems |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Elicit the integration scenario: what event triggers the integration, what data flows, and what must happen as a result.
2. Classify the integration type: Process (triggering/monitoring), Data (synchronizing records), or Virtual (read-only external data display).
3. Determine timing requirement: does the source system need a synchronous response (waits for result), or can it proceed asynchronously (fire-and-forget or event-driven)?
4. Apply volume test: how many records per transaction or per day? Above 2,000 records triggers the Bulk API 2.0 requirement.
5. Check transactional requirement: does the integration require rollback across multiple systems on failure? If yes, middleware is mandatory — Salesforce cannot participate in distributed transactions.
6. Map to the canonical pattern using the two-axis matrix; document secondary pattern options and their tradeoffs.
7. Document the decision record: selected pattern, rationale, key constraints, and the integration implementation skill to use next.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Integration type classified (Process / Data / Virtual)
- [ ] Timing requirement confirmed (Sync / Async)
- [ ] Volume threshold applied (below 2,000 / above 2,000 / streaming)
- [ ] Transactional requirement checked (single-system or cross-system rollback needed?)
- [ ] Canonical pattern selected from the 6-pattern framework
- [ ] Pattern decision document completed with rationale
- [ ] If hub-and-spoke with cross-system transactions: middleware requirement noted
- [ ] Implementation skill identified for the next phase

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Salesforce cannot participate in distributed transactions initiated outside Salesforce** — If an integration requires atomic rollback across Salesforce AND an external system (ERP + Salesforce both commit or both roll back together), this cannot be implemented with Salesforce as the orchestrator. Salesforce Apex transactions can roll back Salesforce DML, but they cannot roll back external system operations. This orchestration must live in middleware (MuleSoft, Boomi, etc.).
2. **Synchronous callout timeout is 120 seconds** — Apex HTTP callouts timeout after 120 seconds. An integration designed as synchronous (Request/Reply) that calls an external system taking more than 120 seconds will fail. High-latency external systems require the Fire-and-Forget pattern with a callback mechanism.
3. **Platform Events are not a guaranteed delivery mechanism without retry handling** — Platform Events have a 72-hour replay window and EventBus.RetryableException provides up to 9 retries. However, if the trigger is suspended after 9 failures, messages are not automatically replayed — manual re-enable of the trigger is required. This means Platform Events are eventually consistent, not guaranteed delivery.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration pattern decision record | Selected pattern, integration type, timing, volume constraints, rationale |
| Pattern comparison matrix | All viable patterns for the scenario with tradeoffs |

---

## Related Skills

- `integration/event-driven-architecture-patterns` — use after selecting an event-driven pattern for implementation details
- `integration/salesforce-to-salesforce-integration` — use when the integration is cross-org Salesforce-to-Salesforce
- `architect/api-led-connectivity-architecture` — use for multi-system integration governance architecture
- `integration/error-handling-in-integrations` — use to design error recovery for the selected pattern
