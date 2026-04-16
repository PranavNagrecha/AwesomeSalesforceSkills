---
name: slack-workflow-builder
description: "Use this skill when designing or troubleshooting Slack Workflow Builder workflows that call Salesforce — especially the Salesforce connector step Run a Flow, mapping inputs/outputs, handling failures, and understanding limits. Triggers on: Slack Workflow Builder Salesforce, Run a Flow from Slack, autolaunched flow from Slack, Slack automation calling Salesforce. NOT for Salesforce Flow Builder tutorials unrelated to Slack (use flow skills), not for Flow Core Actions that send Slack messages from Salesforce (use flow-for-slack), not for initial org-to-workspace connection (use slack-salesforce-integration-setup), and not for building custom Slack apps outside Workflow Builder."
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
inputs:
  - "Salesforce org already connected to the Slack workspace (Salesforce for Slack)"
  - "Slack workspace permission to create or edit workflows in Workflow Builder"
  - "Target Salesforce Flow API name and required input variables (if using Run a Flow)"
outputs:
  - "Correct choice of Salesforce step (Run a Flow vs alternatives)"
  - "Checklist for autolaunched-only targets, activation, and runtime permissions"
  - "Operational guidance on throttling, error handling, and governance"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Slack Workflow Builder

This skill activates when a practitioner builds or debugs **Slack Workflow Builder** automations that touch Salesforce. Slack Workflow Builder is Slack’s native no-code automation surface. When paired with the **Salesforce for Slack** connection, it can run Salesforce-side logic through connector steps such as **Run a Flow**. That path is distinct from **Salesforce Flow** calling Slack (Flow Core Actions), which is covered elsewhere. This document focuses on the Slack-initiated direction, prerequisites, supported Flow types, and the operational limits that affect high-volume notifications.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Org connectivity:** The Slack workspace must already be connected to the correct Salesforce org via the Salesforce for Slack app; Workflow Builder does not replace that handshake. If the workspace cannot see Salesforce steps, fix connection and permissions first (see slack-salesforce-integration-setup).
- **Wrong Flow type is the #1 failure:** The **Run a Flow** step can invoke **active autolaunched flows only**. Screen flows, record-triggered flows, and other interactive process types are not valid targets for that connector step. Practitioners often copy a working record-triggered flow name into Slack and see opaque failures.
- **Volume and async limits:** Salesforce-side automation that posts to Slack from record-triggered flows is subject to **asynchronous** execution rules and org-wide throttles (for example, caps on asynchronous calls over a rolling window). Design for bursts (bulk updates, imports) so Slack is not used as an unbounded fan-out channel.

---

## Core Concepts

### Slack Workflow Builder vs Salesforce Flow

**Slack Workflow Builder** runs inside Slack. Steps can react to messages, emoji, shortcuts, or schedules, then chain Slack actions and third-party connectors. **Salesforce Flow** runs inside Salesforce and can optionally use Slack Core Actions (for example, Send Slack Message). Treat these as opposite directions on the same integration backbone: Workflow Builder pulls Salesforce work **from Slack**; Salesforce Flow pushes Slack updates **from CRM events**.

### Run a Flow (Salesforce connector)

The Salesforce connector’s **Run a Flow** step starts a Salesforce Flow by API name. The invoked automation must be an **autolaunched** flow (no screens, no user interview). Inputs defined in the autolaunched flow appear as parameters in the Slack step; outputs can be mapped into later Slack steps. If the flow is inactive, renamed, or not autolaunched, the workflow run fails at that step.

### Governance and data exposure

Workflows often post to public channels or include form data from users who may not have Salesforce licenses. Any data returned from Salesforce into Slack should be treated as **visible to everyone who can see the channel or DM**. Combine channel policies with least-privilege Flow design (query only what the step needs, avoid dumping sensitive fields into Slack messages).

---

## Common Patterns

### Pattern 1: Slack shortcut runs an autolaunched approval or update Flow

**When to use:** A Slack user triggers a shortcut or button and Salesforce should create or update a record without opening Salesforce.

**How it works:**

1. In Flow Builder, create an **autolaunched** flow with input variables (for example, record Id, decision text) and the desired create/update elements.
2. Activate the flow and note the **API Name**.
3. In Slack Workflow Builder, add the **Run a Flow** (Salesforce) step, pick the org, select the flow, map Slack form fields or trigger payload fields to Flow inputs.
4. Add a follow-up Slack step (message or thread reply) that uses Flow output values for confirmation.

**Why not a screen flow:** Screen flows require a Salesforce UI context. Slack Workflow Builder cannot host that runtime; only autolaunched flows are supported for this connector pattern.

### Pattern 2: Channel signal enriches CRM (lightweight sync)

**When to use:** A message in a deal room should log an activity or flag an opportunity without leaving Slack.

**How it works:**

1. Trigger the workflow on **New message in channel** (or a relevant trigger).
2. Use Slack steps to parse or capture the needed identifiers (thread timestamp, channel metadata, or user input).
3. Call **Run a Flow** with those identifiers as inputs; keep the Flow idempotent where possible (duplicate messages should not create duplicate tasks).

**Why not record-triggered from Slack:** Record-triggered flows start from DML in Salesforce, not from Slack’s connector. If the requirement is CRM-driven, implement in Salesforce Flow instead.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need Salesforce logic from a Slack trigger | Slack Workflow Builder + **Run a Flow** on an **autolaunched** flow | Supported connector path from Slack into Salesforce |
| Need Slack message when Salesforce record changes | Record-triggered (or scheduled) Salesforce Flow + Slack Core Actions | CRM is the system of record for the event |
| Need a user to fill a screen in Salesforce | Screen flow or Experience Cloud / Lightning URL | Screen flows are not invocable from Slack Workflow Builder’s Run a Flow step |
| High-volume record updates must notify Slack | Batch, platform events, or async paths; throttle notifications | Prevents hitting asynchronous limits and flooding channels |

---

## Recommended Workflow

1. Confirm the Slack workspace is connected to the intended Salesforce org and that the practitioner can add Salesforce steps in Workflow Builder; if not, stop and use slack-salesforce-integration-setup.
2. List the exact Salesforce behavior required (read-only vs DML) and identify whether the entry point is Slack-side or Salesforce-side; if Salesforce-side, prefer flow-for-slack or record-triggered patterns instead of Workflow Builder.
3. In Salesforce, implement or locate an **autolaunched** flow with explicit input/output variables; activate it and record the API name.
4. In Slack Workflow Builder, add the **Run a Flow** step, map inputs from the Slack trigger or prior steps, and handle null or error paths with a user-visible Slack message.
5. Test with a single user and a low-traffic channel, then scale-test bulk scenarios (imports, mass edits) if the flow performs DML or callouts.
6. Document channel governance (who can run the shortcut, what data may appear in Slack) and add monitoring for failed workflow runs in Slack’s workflow history.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Target flow is **autolaunched** and **Active**, with API name matching the Slack step
- [ ] Input/output mappings cover null-safe paths and do not leak sensitive fields into public channels
- [ ] Practitioners understand this is **not** the same as Flow Core Actions from Salesforce to Slack
- [ ] Bulk and scheduled scenarios have been considered for limits and noise
- [ ] Error handling in the Slack workflow informs the user when Salesforce returns a fault

---

## Salesforce-Specific Gotchas

1. **Wrong process type** — Selecting a record-triggered or screen flow in **Run a Flow** fails or is blocked. Always create a dedicated autolaunched orchestration flow if reusable logic lives in a record-triggered flow (delegate from autolaunched subflow pattern in Flow documentation).
2. **Inactive or renamed flows** — Slack stores the selection by reference; deployments that deactivate or rename flows break in-flight workflows until the Slack step is re-saved.
3. **Permission context** — The Salesforce operation runs in an integration context governed by the Salesforce for Slack connection and the running user’s or connected app’s permissions (exact behavior per product release). Do not assume the clicking user’s personal Salesforce session applies unless the product explicitly documents that model.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Workflow definition | Slack Workflow Builder configuration including Salesforce steps and mappings |
| Autolaunched Flow package | Salesforce metadata for the invocable flow (API name, inputs, status) |
| Runbook | Channel governance, test matrix, and failure triage for workflow + Flow changes |

---

## Related Skills

- slack-salesforce-integration-setup — connect org to workspace and resolve connector visibility issues
- flow-for-slack — Salesforce Flow actions that send Slack messages or launch flows from Slack messages
- error-handling-in-integrations — resilient patterns for callouts, retries, and partial failures across systems
