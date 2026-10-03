# Examples — Slack Workflow Builder

## Example 1: Shortcut in Slack runs an autolaunched “create task” Flow

**Context:** Sales wants a **Slack shortcut** so anyone in a private deal channel can log a follow-up task on the related Opportunity without opening Salesforce.

**Problem:** The team initially pointed the **Run a Flow** step at an existing **screen flow** used by inside sales. Runs failed because that invocation path only supports **autolaunched** flows.

**Solution:**

1. Clone the business logic into a new **autolaunched** flow with inputs `opportunityId`, `taskSubject`, and `ownerId` (text or reference variables as required by your org).
2. Replace user prompts with inputs supplied from the Slack workflow **shortcut form** (or from channel metadata gathered in earlier Slack steps).
3. In Workflow Builder, add **Run a Flow**, select the org, choose the new autolaunched flow, map form answers to Flow inputs, and under **Whose account should be used for this step** pick **The person using the workflow** so each rep's own Salesforce permissions apply.
4. Add a Slack **Send a message** step that posts a confirmation using output variables from the Flow.

```text
Trigger:        Link (shortcut) in #deal-acme
Step 1 Form:    Opportunity Id (text), Follow-up subject (text)
Step 2 Run a Flow (Salesforce):
                flow_name    = AL_Slack_Log_Follow_Up        (autolaunched, Active)
                opportunityId <- Form: Opportunity Id
                taskSubject   <- Form: Follow-up subject
                Account used  = The person using the workflow
Step 3 Send a message to #deal-acme:
                "Follow-up logged: {Run a Flow > result > taskId}"
```

The flow metadata for `AL_Slack_Log_Follow_Up` is in [`metadata-examples.md`](metadata-examples.md).

**Why it works:** The connector's flow picker is limited to auto-launched flows ("Only auto-launched flows are currently supported" in Slack's connector schema), there is no UI runtime, and the per-person account choice keeps each rep inside their own Salesforce permissions.

---

## Example 2: Emoji reaction should not call a record-triggered flow

**Context:** A practitioner wants “when a user reacts with :white_check_mark: on a message, start the same flow that runs when an Opportunity hits Closed Won.”

**Problem:** The Closed Won automation is a **record-triggered** flow. That flow is not a valid target for **Run a Flow** from Workflow Builder.

**Solution:**

1. Keep the record-triggered flow for CRM-driven updates.
2. Create a small **autolaunched** flow (or invocable subflow) that accepts `opportunityId` and performs only the side effects you want from Slack (for example, post a chatter update or enqueue a Platform Event).
3. Optionally call that autolaunched flow from the record-triggered path too, so logic stays DRY.
4. Point **Run a Flow** in Slack only at the autolaunched entry point.

**Why it works:** Record-triggered entry is owned by Salesforce data events; Slack must call an invocable, headless entry point.

---

## Anti-Pattern: Using Workflow Builder for CRM-volume notifications

**What practitioners do:** Chain **Run a Flow** on every message in a high-traffic channel to echo data into Salesforce and post back to Slack.

**What goes wrong:** Bulk message or import scenarios create **DML and async pressure** in Salesforce and noisy channels. You hit operational limits and erode trust in notifications.

**Correct approach:** For high-volume CRM-driven notifications, use **Salesforce Flow** (after-save asynchronous paths) with **Slack Core Actions**, or batch to Platform Events and a subscriber Flow. Reserve Workflow Builder for **human-initiated** or low-volume Slack triggers.
