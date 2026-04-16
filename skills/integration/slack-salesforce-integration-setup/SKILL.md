---
name: slack-salesforce-integration-setup
description: "Use this skill when setting up or troubleshooting the Salesforce for Slack managed app — including connecting a Salesforce org to a Slack workspace, configuring the three-party admin handshake, linking Slack channels to Salesforce records, enabling record preview sharing, and managing org-level limits. Triggers on: Salesforce for Slack app not connecting, Slack org connection setup, Salesforce record sharing in Slack, Slack workspace admin approval, connecting Salesforce to Slack. NOT for building custom Slack apps or Slack bots (separate development platform), not for Slack Workflow Builder Salesforce connector (use slack-workflow-builder skill), not for Flow-based Slack messaging (use flow-for-slack skill)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
tags:
  - slack
  - salesforce-for-slack
  - integration
  - workspace
  - admin-setup
  - record-sharing
  - oauth
inputs:
  - "Slack workspace (paid plan — Free plan cannot connect to Salesforce)"
  - "Slack Workspace Owner or Admin credentials"
  - "Salesforce System Administrator credentials"
  - "Salesforce edition: Enterprise, Unlimited, or Developer (required)"
outputs:
  - "Connected Salesforce org in Slack workspace"
  - "Record preview sharing enabled in Slack channels"
  - "Salesforce for Slack app installed and authorized"
  - "Known data exposure risk documentation for record previews"
triggers:
  - "Salesforce for Slack not connecting to workspace"
  - "Slack Salesforce integration admin handshake steps"
  - "how to link Salesforce org to Slack"
  - "Salesforce record preview in Slack channel"
  - "Slack org connection limit Salesforce"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Slack Salesforce Integration Setup

This skill activates when a practitioner needs to connect a Salesforce org to a Slack workspace using the Salesforce for Slack managed app, troubleshoot the three-party admin handshake, configure record sharing, or understand workspace-level limits. It does NOT cover custom Slack app development, Slack Workflow Builder, or Flow-based Slack messaging.

---

## Before Starting

Gather this context before working on anything in this domain:

- The connected-org setup requires THREE parties: a Slack Workspace Owner/Admin to initiate, a Salesforce System Admin to approve in Setup, and a Slack Owner/Admin to activate. A single administrator cannot complete all three steps alone.
- Hard limits: maximum 20 Salesforce orgs per Slack workspace. Government Cloud orgs CANNOT be connected at all.
- Record previews shared into Slack channels are visible to ALL channel members regardless of their individual Salesforce object permissions — this is the primary data-exposure risk.

---

## Core Concepts

### Three-Party Admin Handshake

The connection process requires coordination between three distinct administrative roles:

1. **Slack Workspace Owner/Admin** — Initiates the connection from the Slack App Directory or Salesforce AppExchange. Installs the Salesforce for Slack managed app into the workspace.
2. **Salesforce System Admin** — Approves the connection in Salesforce Setup under Platform Tools > Slack > Manage Slack Connection. This grants the app permission to access the Salesforce org.
3. **Slack Workspace Owner/Admin** — Completes the activation after Salesforce approval.

These steps must happen in order. If the Salesforce System Admin has not approved the connection, the Slack side cannot activate. If the Slack Workspace Owner has not initiated, the Salesforce approval step is not visible.

### Org-Level Limits

- Maximum **20 Salesforce orgs** per Slack workspace (across all plans)
- **Government Cloud** orgs cannot be connected — this is a hard platform restriction, not a configuration choice
- Standard Salesforce editions supported: Enterprise, Unlimited, Developer

### Record Preview Data Exposure

When a Salesforce record URL is shared in a Slack channel, the Salesforce for Slack app unfurls a record preview card visible to ALL channel members. This preview displays field values according to the Salesforce page layout, NOT the channel member's individual Salesforce sharing and field-level security settings. A user without Salesforce access (or with restricted field access) can see field values in the Slack preview that they could not see directly in Salesforce.

This is not a bug — it is documented platform behavior. Organizations with sensitive field data (compensation, legal case details, PII) must review which Salesforce records can be shared in Slack channels and apply channel-level governance policies.

### Platform Integration User and Permission Sets

The Salesforce for Slack app uses a dedicated Platform Integration User in the connected Salesforce org. This user requires specific permission sets to access Salesforce data for previews and search. The exact permission sets may vary by release — verify in the current AppExchange listing or help documentation.

---

## Common Patterns

### Pattern 1: Initial Org Connection (Three-Party Handshake)

**When to use:** First-time setup of Salesforce for Slack in a workspace.

**How it works:**

1. **Slack Workspace Owner/Admin:** Go to Slack App Directory, search "Salesforce for Slack", install to workspace. Or install from Salesforce AppExchange.
2. **Salesforce System Admin:** In Salesforce Setup, navigate to Platform Tools > Apps > Salesforce for Slack. Click "Manage Slack Connection" and authorize the pending connection.
3. **Slack Workspace Owner/Admin:** Return to Slack and complete the activation by confirming the connection.
4. Users then individually connect their personal Salesforce accounts from the Salesforce app in Slack (each user authorizes their own account separately from the org connection).

**Why not do this solo:** The platform requires Slack admin, Salesforce admin, and Slack admin roles at different steps. A single admin doing all steps will hit an authorization gap at step 2 if they lack Salesforce System Admin, or at step 3 if they lack Slack Workspace Owner role.

### Pattern 2: Record Sharing Governance

**When to use:** Restricting which Salesforce records can generate preview cards in Slack channels.

**How it works:**

1. Document which Salesforce objects contain sensitive fields that should not be preview-shared.
2. Educate users that pasting a Salesforce record URL in any Slack channel (including private channels) generates a preview visible to all members.
3. For high-sensitivity objects, implement a Salesforce sharing rule that restricts the record URL from being accessible to the Platform Integration User used by the app.
4. Consider channel governance policies: define which Salesforce record types are acceptable to share in which channel types (public vs. private).

**Why this matters:** Record preview exposure is the primary compliance and data-leakage risk in Salesforce for Slack implementations.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| First-time org connection | Three-party handshake (Slack admin + SF admin + Slack admin) | Required by platform — single admin cannot complete alone |
| Government Cloud org | Cannot connect | Platform restriction — no workaround |
| 20+ orgs needed in one workspace | Re-evaluate workspace architecture | Hard limit — cannot exceed 20 orgs per workspace |
| Sensitive field data shared in Slack | Channel governance policy + Platform Integration User sharing rules | Preview shows data regardless of individual permissions |
| User cannot see Salesforce records in Slack | User needs personal account connection + Salesforce permissions | Org connection alone does not authorize individual users |

---

## Recommended Workflow

1. Confirm the Salesforce edition is Enterprise, Unlimited, or Developer — Essential/Professional editions are not supported.
2. Confirm the Slack workspace is on a paid plan (Free plan cannot connect to Salesforce).
3. Confirm the workspace has fewer than 20 existing Salesforce org connections.
4. Coordinate the three-party handshake: Slack admin initiates, Salesforce System Admin approves, Slack admin activates.
5. Assign the required permission sets to the Platform Integration User in Salesforce.
6. Communicate the record preview data exposure risk to all workspace members and define channel-level governance policies.
7. Have each individual user connect their personal Salesforce account from the Salesforce app in Slack.

---

## Review Checklist

- [ ] Salesforce edition confirmed: Enterprise, Unlimited, or Developer
- [ ] Slack workspace is on paid plan
- [ ] Workspace has fewer than 20 connected Salesforce orgs
- [ ] Three-party handshake completed in correct order
- [ ] Platform Integration User has required permission sets
- [ ] Record preview data exposure risk documented and communicated
- [ ] Individual users have connected their personal Salesforce accounts
- [ ] Government Cloud exclusion confirmed if applicable

---

## Salesforce-Specific Gotchas

1. **Three-Party Handshake Cannot Be Done Solo** — The connection requires separate Slack admin approval, Salesforce admin approval, and Slack admin activation. If any party is unavailable or lacks the right role, the connection stalls. Plan the handshake as a coordinated event with all three parties present.

2. **Record Previews Bypass Salesforce Field-Level Security** — Previews render fields based on page layout visible to the Platform Integration User, not the Slack user's individual Salesforce permissions. Sensitive fields can be exposed to channel members who lack Salesforce access.

3. **Government Cloud Orgs Cannot Connect** — This is an absolute restriction with no workaround. Organizations with Government Cloud orgs must use alternative integration patterns (custom Slack apps via Slack SDK, or MuleSoft-based integration).

4. **20-Org Workspace Limit** — Large enterprises with many Salesforce orgs across divisions may hit the 20-org limit. There is no configuration to increase this limit. Workspace architecture may need to be split.

5. **User Personal Account Connection Is Separate from Org Connection** — Connecting the org grants workspace-level access, but each individual user must separately authorize their personal Salesforce account in the Slack app. Users who skip this step cannot see personalized Salesforce data or use Salesforce search in Slack.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Connection setup checklist | Step-by-step three-party handshake with role assignments |
| Data exposure risk register | List of sensitive Salesforce objects with channel-sharing governance policy |
| User onboarding guide | Instructions for individual users to connect personal Salesforce accounts |

---

## Related Skills

- slack-workflow-builder — for building Salesforce-connected automations in Slack Workflow Builder
- flow-for-slack — for Salesforce Flow-based Slack messaging and channel actions
- agentforce-in-slack — for deploying Agentforce agents into Slack
