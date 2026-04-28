---
name: flow-deployment-activation-ordering
description: "Use when deploying Flow metadata across environments and worrying about activation order: which flow version becomes active, how paused interviews survive deploys, and how to avoid the 'two active versions for a moment' race. Covers SFDX / Metadata API deploy flags, 'Deploy as Active', rollback, and paused-interview safety. Does NOT cover Flow authoring best practices (see flow-bulkification) or general release management."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "flow deployment activation order"
  - "sfdx deploy flow activate"
  - "paused interview after flow deploy"
  - "flow rollback after deploy"
  - "multiple flow versions active"
tags:
  - devops
  - flow
  - deployment
  - activation
  - release
inputs:
  - Target environment + branching strategy
  - Flows changing in this release
  - Paused interviews / scheduled interviews in flight
  - Rollback SLA
outputs:
  - Pre-deploy inspection (which flow versions, paused interviews)
  - Deploy procedure (activation order, guards)
  - Rollback plan
  - Post-deploy verification
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Flow Deployment & Activation Ordering

## Purpose

Flow deployments are deceptively tricky. Unlike Apex, Flow preserves
previous versions in the org; the "active" version is a pointer. A deploy
can inadvertently deactivate the currently-running flow, leave two flows
active in sequence, or break paused interviews that refer to the old
version. The team hits production incidents: "the approval flow stopped
triggering," "paused interviews threw after deploy," "rollback just
deactivated everything." This skill codifies the sequence, guards, and
verification to make Flow deploys boring.

## Recommended Workflow

1. **Inventory changes.** Which flows changed? Which have paused
   interviews or scheduled runs currently in progress?
2. **Check active versions in target org.** `sf data query` against
   `FlowDefinition` and `Flow` to confirm what is active today.
3. **Pick activation mode.** Deploy as active (default) vs deploy as
   inactive then activate via `FlowDefinition` update. Inactive-first is
   safer for risky flows.
4. **Plan the order.** If Flow A calls Subflow B, deploy B first (active
   before A switches).
5. **Communicate pause windows.** If paused interviews exist on the
   changing flow, delay deploy or accept that paused interviews may fail
   on resume.
6. **Deploy.** Use `--test-level RunSpecifiedTests` when Apex callers
   exist; Flow itself has no test framework parity.
7. **Verify.** Re-query active versions post-deploy; run a smoke Flow
   interview; check for spikes in Flow error emails.
8. **Rollback plan.** Keep prior active version id; rollback = flip
   pointer on `FlowDefinition`, not redeploy.

## Active vs Inactive Deploy

- Default SFDX behavior: deploys a new flow VERSION; activation depends on
  flags.
- `--ignore-warnings` can mask inactive deploys silently activating.
- For risky flows, explicitly deploy as inactive, then flip activation in
  a separate step once verified.

## Paused Interview Risk

Paused interviews reference a specific version. If that version is
deactivated or deleted, resume fails. Mitigations:

- Do not delete prior versions for N days (retain for paused interview
  survival).
- For large deploys, drain paused interviews first (resume or cancel via
  Setup).
- Screen Flows with wait elements are the most common victims.

## Subflow / Calling-Order Rules

- Deploy callee subflow FIRST, then caller.
- If both change together, deploy as inactive, activate callee, then
  activate caller.
- Cross-package dependencies (packaged subflow + unmanaged caller) need
  extra care.

## Rollback Pattern

- Keep the prior version active-id BEFORE deploy.
- Rollback = `FlowDefinition.ActiveVersion` pointer update, via
  Metadata API or Tooling API.
- Do NOT delete the new version during rollback; keeping it makes
  forward-fix possible.

## CI/CD

- Source-tracked orgs: every deploy includes the flow source as xml.
- Pre-deploy hook: capture active version ids (for rollback).
- Post-deploy hook: verify expected active version became active.
- Scratch-org test: run any Apex invokers that call the flow.

## Anti-Patterns (see references/llm-anti-patterns.md)

- "Deploy and pray" — no pre-deploy inventory.
- Deleting old flow versions as cleanup.
- Rolling back by redeploying the prior source (creates a new version,
  not the prior version).
- Deploying caller + callee subflow in random order.

## Official Sources Used

- Flow Metadata API — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_flow.htm
- SFDX Deploy Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_sf_project.htm
- Flow Versioning — https://help.salesforce.com/s/articleView?id=sf.flow_distribute_deploy.htm
- Paused Interviews — https://help.salesforce.com/s/articleView?id=sf.flow_admin_paused.htm
