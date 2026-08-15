---
name: flow-deployment-activation-ordering
description: "Deploying Flow metadata across environments when activation order matters: which flow version becomes active, how paused interviews survive deploys, avoiding the 'two active versions for a moment' race, SFDX / Metadata API deploy flags, 'Deploy as Active', rollback. NOT for Change Set vs SFDX vs package choice for a flow — use flow/flow-deployment-and-packaging. NOT for whether a change needs a new version or a new flow — use flow/flow-versioning-strategy."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
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
6. **Deploy, verify, and plan rollback.** Use `--test-level RunSpecifiedTests --tests <ClassName> [...]` when Apex callers exist (Flow itself has no test framework parity). `--tests` is what names the classes to run — `RunSpecifiedTests` on its own specifies nothing — and this level changes the coverage rule: "Each class and trigger in the deployment package must be covered by the executed tests for a minimum of 75% code coverage." Re-query active versions post-deploy; run a smoke Flow interview; check for spikes in Flow error emails. Keep the prior active version id captured before deploy — rollback = flip the pointer on `FlowDefinition`, not redeploy.

## The Asymmetry Everything Turns On

**Deploying a flow always creates a new version. It never restores an old one.**
Activation, by contrast, is a pointer into versions that already exist in the
org. Deploy and activate are different operations with different rollback
properties, and conflating them causes most incidents in this domain.

## Active vs Draft Deploy

- Deploy a pending version with `<status>Draft</status>`, verify it, then
  activate as a separate step. `Obsolete` is what the platform assigns to a
  superseded version — it is never the right thing to choose for a new one. The
  `status` field has **five** valid values: `Active`, `Draft`, `Obsolete`,
  `InvalidDraft`, and `UnderReview`. They do not map one-to-one onto the UI
  labels — `Draft` and `Obsolete` both display as *Inactive*, `InvalidDraft`
  displays as *Draft*, and `UnderReview` displays as *Under Review* — so never
  infer the API value from what Setup shows you.
- Prefer `<status>Active</status>` on the `Flow` for routine deploys.
- Keep `FlowDefinition` **out** of routine packages. This recommendation is
  routinely misremembered as "upgrade flows to API version 44.0". What Salesforce
  actually says is: "In API version 44.0, we recommend upgrading your flows to
  flow metadata file names without version numbers and discontinue using the
  FlowDefinition object to activate or deactivate a flow." That is a
  recommendation made *in* 44.0, about file naming and about dropping
  `FlowDefinition` — not an instruction to move flows *to* API version 44.0. The
  precedence rule is the trap: "the active version numbers in the flow definitions
  override the status fields in the flows." A stale `FlowDefinition` silently wins
  over every `status` in the package.
- One production-only constraint: the **Deploy processes and flows as active**
  preference (Setup → Process Automation Settings) and its flow test coverage
  percentage do not exist in developer or sandbox orgs. A green sandbox deploy is
  not evidence the production deploy will pass. The coverage requirement applies
  to processes and autolaunched flows and does **not** apply to flows that have
  screens.

## Paused Interview Risk

Paused interviews resume on the version they started on. The deploy is safe — the
old version stays in the org. The **cleanup** is what breaks them, usually weeks
later in an unrelated change, which is why nobody connects the failure back.

- Snapshot `FlowInterview` before deploying. `InterviewLabel` embeds the flow's
  API name and version number, which is how you check "does anything still
  reference version 7?"
- Gate deletion on zero interview references, never on age.
- Since Spring '24 there is no platform cap on how many paused and waiting
  interviews an org accumulates, so this population grows quietly and will not
  self-limit.
- Screen flows with Pause elements are the most common victims.

## Subflow / Activation-Order Rules

Subflow resolution is late: the parent runs whatever version of the child is
active at interview time, and the *latest* version if the child has none active.

- Deploy both as `Draft`, verify the child, activate the **child**, then activate
  the **caller**. Between those two activations the old caller runs against the
  new child, which is the compatible direction.
- Ordering inside a single deploy changes nothing — the deploy is atomic. It is
  the *activation* order that matters.
- Activation is not atomic across two flows. For a breaking child change no
  ordering helps; that needs a new child flow with a caller repoint, which is
  `flow/flow-versioning-strategy`'s call.
- Deactivating a child does **not** stop callers. It drops them onto the latest
  version, possibly an untested draft.

## Rollback Pattern

- Capture the active version number per flow per environment **before** the
  deploy. That capture is the entire rollback plan, and the repository does not
  contain it — activation is org state.
- Roll back by activating the version that already exists: one click on the
  flow's detail page, or a standalone `FlowDefinition` deployment with
  `activeVersionNumber` set to the version you want live. This is the one case
  where `FlowDefinition` earns its place, because pointing at an existing version
  number is the thing `status` cannot express. To take a flow *off* rather than
  move the pointer, deactivate on the flow's detail page or deploy the version
  with `<status>Draft</status>` — both are documented behaviours.
  <!-- UNVERIFIED: `activeVersionNumber` = 0 is widely reported to deactivate a
  flow, but meta_flowdefinition.htm documents the field only as "The version
  number of the active flow" and states no behaviour for 0. Nothing in this
  runbook depends on it; if you want to use it, confirm in a sandbox first. -->
- Do **not** delete the bad version. It is the evidence and it preserves the
  forward-fix path.
- Rollback stops future damage and repairs nothing past. Records already written
  stay wrong, published platform events are gone and their subscribers already
  acted, and enqueued scheduled paths are still queued. Write the data-remediation
  plan alongside the deploy plan.

## CI/CD

- **Pre-deploy:** capture `FlowDefinitionView` (standard API — `ActiveVersionId`,
  `LatestVersionId`, `IsActive`) plus a Tooling API query against `Flow` for
  version *numbers*, plus a `FlowInterview` snapshot. `Flow` is a Tooling API
  object; a standard-API query returns "sObject type 'Flow' is not supported" and
  a careless script degrades to checking nothing.
- **Post-deploy:** re-query `FlowDefinitionView` and diff. An unexplained row is a
  finding — a managed package upgrade can move a flow's active version without
  appearing in your release notes.
- **Then the checks a script cannot make:** run one real interview of each changed
  flow through its actual entry point, watch flow error email volume for a step
  change, and check Setup → Environments → Monitoring → **Time-Based Workflow**
  for scheduled and async entries that should have drained.

## Anti-Patterns (see `references/llm-anti-patterns.md`)

- Rolling back by redeploying prior source — creates a new version, does not
  restore the old one.
- `<status>Obsolete</status>` used to mean "inactive".
- Bundling `FlowDefinition` with `Flow` "for certainty" — it silently overrides.
- Inventing `FlowDefinition.ActiveVersion`; the field is `activeVersionNumber`.
- Querying `Flow` without `--use-tooling-api`.
- Treating deactivation as a kill switch.
- Ending the runbook at "the deploy succeeded."
- Assuming rollback undoes the data.

## Related

- `flow/flow-versioning-strategy` — new version vs new flow, and the retention
  rule this skill enforces at deploy time.
- `flow/flow-deployment-and-packaging` — change sets vs SFDX vs packages.
- `devops/devops-center-advanced` — promoting flows through a work-item pipeline.
- `devops/deployment-error-diagnosis` — reading a failed deploy.
- `flow/flow-interview-debugging` — why the version in an error email is usually
  not the active one.

## Official Sources Used

- FlowDefinition (Metadata API) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_flowdefinition.htm
- Flow (Metadata API) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Flow (Tooling API) — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_flow.htm
- FlowDefinitionView (Object Reference) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_flowdefinitionview.htm
- Deploy Processes and Flows as Active — https://help.salesforce.com/s/articleView?id=platform.flow_distribute_deploy_active.htm&type=5
- Salesforce CLI Command Reference, `sf project deploy` — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_project_commands_unified.htm

The full annotated list is in `references/well-architected.md`.
