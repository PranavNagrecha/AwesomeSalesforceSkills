---
name: slack-workflow-builder
description: "Use this skill when designing or troubleshooting Slack Workflow Builder workflows that call Salesforce — especially the Salesforce connector step Run a Flow, mapping inputs/outputs, handling failures, and understanding limits. Triggers on: Slack Workflow Builder Salesforce, Run a Flow from Slack, autolaunched flow from Slack, Slack automation calling Salesforce. NOT for sending a Slack message or creating a channel FROM a Salesforce Flow — use flow/flow-for-slack. NOT for first connecting the org to the Slack workspace — use integration/slack-salesforce-integration-setup."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
tags:
  - slack-workflow-builder
  - slack
  - salesforce-for-slack
  - autolaunched-flow
  - workflow-automation
  - integration
triggers:
  - "Slack Workflow Builder Run a Flow step fails and says the flow must be autolaunched"
  - "Slack automation calling Salesforce only works for some flows but not record-triggered ones"
  - "Salesforce connector in Slack Workflow Builder hits throttling or async limits during bulk updates"
  - "run a Salesforce flow from a Slack workflow"
  - "create a Salesforce record from a Slack form with Workflow Builder"
  - "choose whose Salesforce account a Slack workflow step uses"
inputs:
  - "Salesforce org already connected to the Slack workspace (Salesforce for Slack)"
  - "Slack workspace permission to create or edit workflows in Workflow Builder"
  - "Target Salesforce Flow API name and required input variables (if using Run a Flow)"
outputs:
  - "Correct choice of Salesforce step (Run a Flow vs alternatives)"
  - "Checklist for autolaunched-only targets, activation, and runtime permissions"
  - "Operational guidance on throttling, error handling, and governance"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Slack Workflow Builder

This skill activates when a practitioner builds or debugs **Slack Workflow Builder** automations that touch Salesforce through the Salesforce connector. The connector offers five steps: Create a record, Read a record, Update a record, Delete a record, and **Run a Flow**. That path is distinct from **Salesforce Flow** calling Slack (Flow Core Actions such as Send Slack Message), which is covered by `flow/flow-for-slack`. This document covers the Slack-initiated direction: which flows Run a Flow accepts, whose Salesforce identity a step uses, and the governance and operational limits around it.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Plan and approvals:** Workflow Builder and connector steps are available on paid Slack plans, and workspaces that require app approval must approve the Salesforce connector before its steps appear.
- **Target flow type:** The Run a Flow step's flow picker is titled "Select a Flow (Only auto-launched flows are currently supported)" in Slack's connector schema. Screen and record-triggered flows are not valid targets, and the flow must be active.
- **Identity:** Connector steps authenticate to Salesforce with an account. The builder chooses whether everyone uses the builder's account or each person authenticates their own ("The person using the workflow"). That choice decides whose permissions every run uses.
- **Audience:** If the workflow will run in Slack Connect channels, external people can only use connector steps that do not require them to authenticate, and only when admins allow it.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Does the Salesforce work start from a Slack action, or from a Salesforce record change?" | Slack-initiated work uses the connector; CRM-initiated work belongs in a Salesforce flow with Slack actions | The direction and the right product surface | No record-triggered logic forced through Slack |
| "Is a single record operation enough, or is logic needed?" | Create, Read, Update, and Delete steps need no flow; Run a Flow needs an active autolaunched flow | The simplest step that meets the need | Fewer flows to deploy and keep in sync with Slack |
| "Whose Salesforce account should each run use?" | With the builder's account, every run has the builder's permissions; with "The person using the workflow", each user authenticates and their permissions apply | An explicit identity decision per step | No accidental admin-level writes triggered by any channel member |
| "Who can start the workflow, including Slack Connect partners?" | External people cannot run connector steps that require their own authentication; admins control whether they can run any connector workflows | The audience and the Slack Connect setting | No partner running Salesforce writes under an internal account |
| "What happens when the flow is renamed, deactivated, or the builder leaves?" | Workflows reference the flow by name, and a builder who disconnects their account breaks steps that use it | An owner, a workflow manager list, and a deployment checklist | Workflows that survive releases and staff changes |
| "How often will it run, and what data returns to Slack?" | Every run is a Salesforce transaction, outputs post to whoever can read the channel, and activity logs keep only 90 days | A volume estimate and an output field list | No noisy channels, no leaked fields, and errors that are noticed |

What a proper configuration adds over "just adding the step": the target flow is autolaunched and active with explicit inputs and outputs, every run uses a deliberate identity, external use is governed, and Slack workflows are treated as dependents of the flows they call.

---

## Core Concepts

### Slack Workflow Builder vs Salesforce Flow

**Slack Workflow Builder** runs inside Slack. Workflows start from a link, a schedule, an emoji reaction, joining or creating a channel, or an external service, then chain Slack steps and third-party connector steps. **Salesforce Flow** runs inside Salesforce and can use Slack Core Actions. Workflow Builder pulls Salesforce work **from Slack**; Salesforce Flow pushes Slack updates **from CRM events**.

### Salesforce Connector Steps

| Step (Slack connector function) | Inputs (required in bold) | Outputs |
|---|---|---|
| Create a record (`create_record`) | **`salesforce_object_name`**, `metadata` (field values), **`salesforce_access_token`** | `success`, `record_id`, `record_url` |
| Read a record (`read_record`) | **`salesforce_object_name`**, **`record_id`**, **`salesforce_access_token`** | `record`, `salesforce_object_type`, `record_url` |
| Update a record (`update_record`) | **`salesforce_object_name`**, **`record_id`**, `updates`, **`salesforce_access_token`** | `code`, `record_url`, `record_id` |
| Delete a record (`delete_record`) | **`salesforce_object_name`**, **`record_id`**, **`salesforce_access_token`** | `code`, `record_id` |
| Run a Flow (`run_flow`) | **`flow_name`** ("Select a Flow (Only auto-launched flows are currently supported)"), `metadata`, **`salesforce_access_token`** | `success`, `flow_name`, `result` (Flow outputs) |

Source: the autogenerated connector schemas in Slack's `slackapi/deno-slack-hub` repository (`src/connectors/salesforce/functions/*.ts`) and the connector catalog in the Slack developer docs. The no-code step UI labels these fields differently.

### Run a Flow

The step starts a Salesforce flow by name. The flow must be autolaunched and active. Input variables marked available for input appear as step inputs, and output variables come back in `result` for later Slack steps. If the flow is inactive, renamed, or not autolaunched, the step fails.

### Identity and Governance

When a builder adds a connector step and clicks Connect, they can let everyone use their account or require "The person using the workflow" to authenticate. In coded workflows, the same choice is `credential_source: "END_USER"` (the end user authenticates, and the workflow must start from a link trigger) or `"DEVELOPER"` (a collaborator's account). Outputs posted to Slack are visible to everyone in the channel or DM.

---

## Common Patterns

### Pattern 1: Shortcut Form Runs an Autolaunched Flow

**When to use:** A Slack user fills a form and Salesforce should create or update records without opening Salesforce.

**How it works:**

1. In Flow Builder, create an **autolaunched** flow with input variables (for example `opportunityId`, `taskSubject`) and output variables for the confirmation.
2. Activate it and note the API name.
3. In Workflow Builder, start from a link (shortcut), collect form answers, add **Run a Flow**, connect the Salesforce account, choose **The person using the workflow** when each user's permissions should apply, and map form fields to flow inputs.
4. Add a Slack message step that uses the flow outputs.

Deployable flow metadata and a coded equivalent are in [`references/metadata-examples.md`](references/metadata-examples.md).

**Why not a screen flow:** The connector supports auto-launched flows only.

### Pattern 2: Single Record Update Without a Flow

**When to use:** A Slack reaction or button should flag one record.

**How it works:** Use the connector's **Update a record** step directly with the object, record ID, and the field updates, and post the returned `record_url` back to the thread.

**Why not Run a Flow:** A flow adds a deployment dependency the single update does not need.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Salesforce logic from a Slack trigger | Run a Flow on an active autolaunched flow | The connector supports auto-launched flows only |
| One record created, read, updated, or deleted | The matching connector step, no flow | Fewer moving parts |
| Slack message when a Salesforce record changes | Record-triggered Salesforce Flow plus Slack Core Actions | CRM is the event source |
| A user must work through screens | Screen flow in Salesforce or a Lightning URL | Not invocable from Run a Flow |
| Partners in Slack Connect must trigger Salesforce work | Prefer a Salesforce-side intake, or a connector step that does not need their authentication with admin approval and a least-privilege account | External people cannot authenticate connector steps |

---

## Recommended Workflow

1. Confirm the paid plan, the Salesforce connector approval, and the direction of the integration; if CRM-initiated, use `flow/flow-for-slack` instead.
2. Choose the step: a record step for single-record work, Run a Flow for logic.
3. For Run a Flow, build or reuse an active autolaunched flow with explicit input and output variables, and record its API name.
4. In Workflow Builder, connect the Salesforce account and set "Whose account should be used for this step" deliberately; map inputs and handle the failure path with a visible message.
5. Set who can find and use the workflow, review the Slack Connect settings, and add workflow managers so the workflow survives staff changes.
6. Run `python3 skills/integration/slack-workflow-builder/scripts/check_slack_workflow_builder.py --manifest-dir force-app/main/default`, test with one user, then review the activity log (it keeps 90 days) after release.

---

## Review Checklist

- [ ] Target flow is autolaunched and Active, with API name matching the Slack step
- [ ] Input variables are available for input; outputs are minimal and non-sensitive
- [ ] "Whose account should be used for this step" chosen deliberately and documented
- [ ] Slack Connect usage of connector workflows reviewed with the workspace owner
- [ ] Workflow managers added; Flow deployments include a Slack workflow check
- [ ] Failure path informs the Slack user

---

## Salesforce-Specific Gotchas

One-line summaries; the full entries are in [`references/gotchas.md`](references/gotchas.md).

| Gotcha | Short form |
|---|---|
| Flow type | Run a Flow accepts auto-launched flows only, and they must be active |
| Identity | The builder's account is used for every run unless the step requires each person to authenticate |
| Builder leaves | Disconnecting the builder's account breaks steps that use it |
| Slack Connect | External people cannot use connector steps that need their own authentication |
| Renames | Deployments that rename or deactivate a flow break published workflows |
| Logs | Activity logs keep 90 days of history |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Workflow definition | Trigger, steps, identity choice per connector step, and mappings |
| Autolaunched flow package | Flow metadata with input and output variables and Active status |
| Runbook | Owners, workflow managers, Slack Connect settings, and failure triage |

---

## Related Skills

- slack-salesforce-integration-setup: connect the org to the workspace and resolve connector visibility issues
- flow-for-slack — Salesforce Flow actions that send Slack messages or launch flows from Slack messages
- error-handling-in-integrations — resilient patterns for callouts, retries, and partial failures across systems
