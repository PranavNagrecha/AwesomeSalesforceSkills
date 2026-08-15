---
name: flow-versioning-strategy
description: "Manage Flow versions: activation policy, paused interview compatibility, cleanup cadence, and breaking-change detection. Trigger keywords: flow version management, activate flow version, paused interview, flow cleanup, flow breaking change, flow rollback. NOT for the deploy-time activation order of FlowDefinition metadata — use devops/flow-deployment-activation-ordering. NOT for moving a flow from sandbox to production — use flow/flow-deployment-and-packaging."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
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
- Delete a version only when **zero interviews reference it**. Age is a cheap
  pre-filter for that condition, never a substitute — a paused interview resumes
  on the version it started on, and since Spring '24 the org has no cap on how
  many paused interviews accumulate.
- Size the retention window per flow from the observed interview lifetime. A
  screen flow with an overnight pause and a scheduled flow with a 90-day wait
  need different windows; one org-wide number is wrong for both.
- Cap total versions per flow at 10 by policy, so pruning happens on a calm
  cadence rather than in response to a failed save.
  The platform ceiling is **50 versions per flow** — stated in the Visual
  Workflow Implementation Guide's limits table, and the number Salesforce returns
  in the save error ("Maximum number of Versions per flow is 50").
  <!-- PARTIALLY VERIFIED: 50 is corroborated by the Implementation Guide's table
  and by the runtime error text. What was not confirmed during authoring is
  whether the current General Flow Limits page restates it, because that page is
  a Lightning SPA that fetchers cannot read. Two other figures on the same legacy
  page (2,000 executed elements, 500 active flows) are known stale, so cite 50
  from the error message rather than from that page. -->

## Breaking-Change Detection

The test is mechanical: **if anything outside the flow has to change at the same
moment the flow changes, it is a new flow, not a new version.** The contract
surface binds by *name* at run time — Apex `Flow.Interview.createInterview`,
`lightning-flow` with `inputVariables`, another flow's `<subflows>` input
assignments, quick actions, Experience Cloud pages — and nothing compiles over
it.

Before activating, diff against the current active version:

- Added required variables? → breaking.
- Renamed or removed variables still referenced by callers? → breaking.
- Changed element outputs on a path before a Pause? → breaking.
- Removed an element a paused interview could currently occupy? → breaking.
- Added a Pause at the top of a flow that previously completed inline? →
  behaviour-changing; test callers.
- API version moved? → behaviour-changing. Flow behaviour is versioned, and
  Flow Builder can bump the version on save. Crossing API 52.0 changes the
  run-mode default; crossing 57.0 removes the executed-elements cap.

## Querying the Right Object

Four objects answer four different questions, and picking the wrong one produces
"sObject type 'Flow' is not supported."

| Question | Object | API |
|---|---|---|
| Versions, their status, their definition | `Flow` | **Tooling API** |
| Which version is active per definition | `FlowDefinitionView` | Standard |
| Version metadata, read-only | `FlowVersionView` | Standard (46.0+) |
| Live and paused interviews | `FlowInterview` | Standard |

Flow version `Status` has five values: `Active`, `Draft`, `Obsolete`,
`InvalidDraft`, and `UnderReview`. None of them means "safe to delete," and the
API values do not match the UI labels — `Draft` and `Obsolete` both display as
*Inactive*, `InvalidDraft` displays as *Draft*, `UnderReview` as *Under Review*.
Filter cleanup queries on `Status != 'Active'` rather than enumerating the
inactive values, so a value you did not think of cannot fall out of the inventory.

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

1. **Inventory the callers first**, not last. Search the repository for the
   flow's API name and for every input/output variable name it exposes. This is
   the input to the decision, not a check afterwards.
2. **Apply the breaking-change test.** Anything outside the flow that must change
   at the same moment makes it a new flow. Otherwise, a new version.
3. **Capture the currently active version number, per environment,** before
   activating. It is the entire rollback plan.
4. **Activate, and write the changelog entry** — breaking or not with the reason,
   the callers checked, the live paused-interview count, and the rollback version
   number.
5. **Roll back by activating the prior version**, never by redeploying its
   source. Redeploying creates a new version whose content matches the old one;
   it does not restore the old one. Keep the bad version as evidence.
6. **Prune on the interview-reference condition,** retaining at least three
   inactive versions.
7. **Treat every subflow activation as a multi-caller production change.** Search
   the metadata for `<flowName>` references before activating; resolution is late,
   so the parent runs whatever version of the child is active at run time.

## Official Sources Used

- FlowDefinition (Metadata API) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_flowdefinition.htm
- Flow (Metadata API) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Flow (Tooling API) — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_flow.htm
- FlowVersionView (Object Reference) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_flowversionview.htm
- Have Unlimited Paused and Waiting Flows (Spring '24) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_mgmt_remove_paused_interview_limit.htm&release=248&type=5
- General Flow Limits — https://help.salesforce.com/s/articleView?id=platform.flow_considerations_limit.htm&type=5

The full annotated list is in `references/well-architected.md`.
