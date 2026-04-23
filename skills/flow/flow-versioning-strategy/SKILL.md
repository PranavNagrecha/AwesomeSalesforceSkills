---
name: flow-versioning-strategy
description: "Manage Flow versions: activation policy, paused interview compatibility, cleanup cadence, and breaking-change detection. Trigger keywords: flow version management, activate flow version, paused interview, flow cleanup, flow breaking change, flow rollback. Does NOT cover: FlowDefinition metadata deploy order (see devops skill), Process Builder retirement, or Flow test coverage (separate skill)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "flow version strategy"
  - "paused interview compatibility"
  - "clean up old flow versions"
  - "flow breaking change detection"
  - "activate flow version plan"
tags:
  - flow
  - versioning
  - governance
  - lifecycle
inputs:
  - Flow inventory with active/inactive version counts
  - Rate of paused interviews per flow
  - Change history of flow versions
outputs:
  - Flow versioning convention
  - Cleanup cadence rule
  - Breaking-change detection checklist
dependencies:
  - devops/flow-deployment-activation-ordering
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Flow Versioning Strategy

## The Model

Each flow has many versions; only one is active. Paused interviews
(long-running) pin to the version that started them. Versioning is not
just housekeeping — it is correctness.

## Activation Policy

- **New feature** → create a new version, activate after test.
- **Non-breaking fix** → new version, same name, activate, retire the
  previous after paused-interview drain window.
- **Breaking change** → NEW flow, not a new version. Paused interviews
  cannot migrate between versions that break the contract.

## Paused Interview Compatibility

A paused interview resumes on the version it started on. Breaking
changes that cannot survive a resume:

- Added required input variable.
- Removed or renamed variable still referenced downstream.
- Changed element output shape (collection → single, etc.).
- Changed decision paths in a way that strands the paused node.

If any of these is needed, route NEW traffic to a new flow and let the
old one drain.

## Cleanup Cadence

- Retain the last 3 inactive versions (rollback depth).
- After 30 days without paused interviews on a version, delete.
- Cap total versions per flow at 10 (platform hard limit is 50) — force
  the discipline before the platform does.

## Breaking-Change Detection

Before activating, diff against current active:

- Added required variables? → breaking.
- Removed variables still referenced by callers? → breaking.
- Changed element outputs on a path before a Pause? → breaking.
- Added a Pause at the top of a flow that previously completed
  inline? → behaviour-changing; test callers.

## Change Log

Keep a `FLOWS_CHANGELOG.md` or equivalent block in the flow's PR body:

```text
Flow: CustomerOnboarding
From v12 → v13
- Added input variable `partnerAccountId` (optional, default null).
- Non-breaking. Paused interviews on v12 continue.
- Activate: after UAT sign-off.
- Retire v11: 2026-05-15.
```

## Metrics To Watch

- Count of paused interviews per version.
- Age of oldest paused interview.
- Activations per week (high churn = unstable flow).
- Version count per flow.

## Recommended Workflow

1. Define "breaking change" list for your flows.
2. Before new version, diff inputs/outputs against active.
3. Decide: new version or new flow.
4. Activate new version; monitor paused interview resume rates.
5. Retain the last 3 inactive; delete older.
6. Set alert on paused-interview age and version count.
7. Track activations in a changelog per flow.

## Official Sources Used

- Flow Versioning —
  https://help.salesforce.com/s/articleView?id=sf.flow_distribute_version.htm
- Paused Interviews —
  https://help.salesforce.com/s/articleView?id=sf.flow_concepts_runtime_paused.htm
- Activate A Flow —
  https://help.salesforce.com/s/articleView?id=sf.flow_distribute_activate.htm
