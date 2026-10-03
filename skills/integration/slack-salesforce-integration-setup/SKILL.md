---
name: slack-salesforce-integration-setup
description: "Use this skill when setting up or troubleshooting the Salesforce for Slack integrations, including connecting a Salesforce org to a Slack workspace through the three-step request, approve, and activate handshake, enabling Salesforce for Slack apps in Slack Apps Setup, link unfurling and record preview data sharing, and user account mapping. NOT for building custom Slack apps or Slack bots (separate development platform), and not for Workflow Builder automations — use integration/slack-workflow-builder."
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
  - "Slack workspace and its plan (multiple Salesforce orgs require Pro, Business+, or Enterprise)"
  - "Slack Workspace Owner or Admin credentials"
  - "Salesforce System Administrator credentials"
  - "Salesforce org type (Government Cloud and Government Cloud Plus orgs cannot connect)"
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
  - "salesforce for slack isn't working"
  - "connect our Salesforce org to Slack and map user accounts"
  - "control what Salesforce record links show when shared in Slack"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Slack Salesforce Integration Setup

This skill activates when a practitioner needs to connect a Salesforce org to a Slack workspace, enable the Salesforce for Slack apps (Sales Cloud for Slack, Service Cloud for Slack, and the rest), decide what record links reveal when shared in Slack, or understand who must do which step. It does NOT cover custom Slack app development, Slack Workflow Builder, or Flow-based Slack messaging.

Two related setups exist and are often confused:

| Setup | Where it starts | What it enables | Source |
|---|---|---|---|
| **Connect Salesforce and Slack** (org connection) | Slack: Tools & settings > Manage Salesforce Organizations | Slackbot, Salesforce channels, Agentforce in Slack, Slack Sales Elevate; member account mapping | Slack Help Center, Connect Salesforce and Slack |
| **Salesforce for Slack Integrations** (apps) | Salesforce Setup: Slack Apps Setup | Sales Cloud for Slack, Service Cloud for Slack, CRM Analytics for Slack, link unfurling, record detail security | Slack Integrations guide, Enable Salesforce for Slack Integrations |

---

## Before Starting

Gather this context before working on anything in this domain:

- The org connection has three steps across two systems: request the connection in Slack, approve it in Salesforce Setup (Platform Tools > Slack > Manage Slack Connection, by a Salesforce System Admin), and activate it in Slack (workspace Owners or people with the Salesforce Admin system role in Slack). One person can do all three only if they hold both roles.
- Government Cloud and Government Cloud Plus orgs cannot be connected, and Salesforce for Slack apps are not supported there. The apps are not FedRAMP or HIPAA certified and cannot be used within Blackjack.
- Each Slack user, including the workspace owner who adds apps, needs a permission set with the Connect Salesforce with Slack system permission on a Salesforce license that supports it.
- What a shared record link reveals is a configured choice (link unfurling data sharing options plus Slack Record Layouts), not a fixed behavior.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Is the org Government Cloud, Government Cloud Plus, or under FedRAMP or HIPAA obligations?" | Slack cannot connect to Government Cloud orgs, and Salesforce for Slack is not FedRAMP or HIPAA certified | A go or no-go before any setup work | No project that fails at the approval step or at an audit |
| "Who is the Slack Owner (or Salesforce Admin system role holder) and who is the Salesforce System Admin?" | Request and activation happen in Slack; approval happens in Salesforce Setup | A named person per step and a scheduled session | A connection finished in one sitting instead of days of hand-offs |
| "How many Salesforce orgs, including sandboxes, should this workspace reach, and on which Slack plan?" | Pro, Business+, and Enterprise plans can connect up to 20 additional orgs | A prioritized org list | The orgs that matter are connected and the limit is not hit mid-rollout |
| "How should Slack members map to Salesforce users: email, SAML NameID, or manual?" | Automatic mapping removes a manual sign-in for members; Unified Employee license users can only be mapped automatically | The mapping field and whether automatic mapping is on | Members who can use Salesforce features in Slack on day one |
| "What may a shared record link show, and to whom?" | Options range from Do Not Share Data to showing data viewable by the Default Render User or by the person who posted the link | A data sharing option per object and a Slack Record Layout for sensitive objects | Previews that never expose fields the channel should not see |
| "Are IP restrictions or a custom org URL change planned?" | Features may not work with Salesforce IP restrictions, and a changed org URL requires updating the connection | A network decision and a change runbook | No silent breakage after a My Domain or network change |

What a proper configuration adds over "just installing the app": every step has an owner with the right role, compliance blockers are found first, users are mapped and permissioned, and record previews reveal only what the channel is allowed to see.

---

## Core Concepts

### The Three-Step Org Connection

1. **Request (Slack):** workspace name > Tools & settings > Manage Salesforce Organizations > Connect Salesforce Org; enter the org URL, choose Email or SAML NameID for account mapping, and Request Connection.
2. **Approve (Salesforce):** a Salesforce System Admin opens Setup > Platform Tools > Slack > Manage Slack Connection, selects the user mapping field, accepts the terms, and approves.
3. **Activate (Slack):** an Owner or a person with the Salesforce Admin system role in Slack selects the pending connection and activates it.

Members with mapped accounts then get the Salesforce app in Slack. Connections use a Salesforce Platform Integration User to manage access to object types for features such as Salesforce channels.

### Enabling Salesforce for Slack Apps

In Salesforce Setup > Slack Apps Setup: accept the terms, enable the apps, assign the Connect Salesforce with Slack permission (and app-specific permissions such as Slack Sales User), set object permissions, record detail security, and link unfurling options, then a Slack workspace owner or Enterprise Grid admin installs the apps from the Slack App Directory and authorizes them with Salesforce admin credentials. Finally, each user adds the app to their Slack sidebar and connects their Salesforce account.

### What Shared Record Links Reveal

| Unfurling option | What the channel sees |
|---|---|
| Do Not Share Data | The link is not unfurled |
| Preview Button Only | A button that opens the record with the viewer's permissions |
| Object Type and Preview Button | Object type plus the button |
| Name, Type, and Preview Button | Record name, object type, plus the button |
| Data Viewable by Slack Default Render User | Record data per the Default Render User's permissions |
| Data Viewable by User Sharing the Link | Record data per the poster's permissions |

For the two "data viewable" options, unfurling uses the URL Unfurling Slack Record Layout assigned for the object, or the object's compact layout if none is assigned. Separately, record detail security (Show object type only or Show record name) currently applies to the Sales Cloud for Slack app only, and "Show record name" includes the record name and key fields "even to users who don't have access in Salesforce".

An earlier version of this skill said previews always follow the page layout visible to the Platform Integration User. The fetched guides describe Slack Record Layouts, compact layouts, and the data sharing options above instead.

---

## Common Patterns

### Pattern 1: Initial Org Connection

**When to use:** First-time connection of a Salesforce org to a Slack workspace.

**How it works:** Schedule the Slack Owner (or Salesforce Admin system role holder) and the Salesforce System Admin together, run the three steps in order, choose automatic account mapping where possible, then verify that a mapped member sees the Salesforce app in Slack. The step-by-step plan file and the permission set are in [`references/metadata-examples.md`](references/metadata-examples.md).

**Why plan it:** The roles live in two systems; without both present the connection waits in a pending state.

### Pattern 2: Record Sharing Governance

**When to use:** Any org with sensitive fields that users might share as links.

**How it works:**

1. List objects with sensitive fields.
2. Pick an unfurling option per the table above; prefer Preview Button Only or Name, Type, and Preview Button where data must not appear in the channel.
3. If a "data viewable" option is used, create a URL Unfurling Slack Record Layout per sensitive object with only safe fields, and assign it to the relevant profiles.
4. Publish a channel policy for public channels, private channels, and Slack Connect channels.

**Why this matters:** Record preview exposure is the main data-leakage risk in this integration.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| First-time org connection | Three-step request, approve, activate with both role holders present | Steps span Slack and Salesforce |
| Government Cloud or Government Cloud Plus org | Do not connect; propose a custom integration | Not supported |
| More orgs than the plan allows | Prioritize production and key sandboxes, or split workspaces | Pro, Business+, and Enterprise allow up to 20 additional orgs |
| Sensitive fields shared in Slack | Preview-button options, or a restricted URL Unfurling Slack Record Layout | Previews follow the configured option, not each viewer's field access |
| User cannot see Salesforce data in Slack | Check mapping, the Connect Salesforce with Slack permission, and the personal account connection | Org connection alone does not authorize individual users |

---

## Recommended Workflow

1. Run the compliance gate: Government Cloud, Government Cloud Plus, FedRAMP, HIPAA, and Blackjack all stop the project.
2. Fill in the connection plan (roles, plan, org list, mapping field, unfurling option, IP restrictions) and run `python3 skills/integration/slack-salesforce-integration-setup/scripts/check_slack_salesforce_integration_setup.py --plan slack-connection-plan.json`.
3. Assign the Connect Salesforce with Slack permission set to every Slack user, including the workspace owner who installs apps.
4. Run the three-step org connection with both role holders present, then enable the Salesforce for Slack apps in Slack Apps Setup.
5. Configure link unfurling and Slack Record Layouts for sensitive objects, and publish the channel policy.
6. Confirm mapping (automatic or manual) and have each user connect their account from the app in Slack; spot-check with a low-access user.

---

## Review Checklist

- [ ] Not a Government Cloud or Government Cloud Plus org; no FedRAMP, HIPAA, or Blackjack requirement
- [ ] Org count within the plan's allowance (up to 20 additional orgs on Pro, Business+, Enterprise)
- [ ] Request, approve, and activate completed by the documented roles
- [ ] Connect Salesforce with Slack permission assigned to every Slack user, including the installing owner
- [ ] Account mapping configured (automatic for Unified Employee license users)
- [ ] Unfurling option chosen per object; Slack Record Layouts for sensitive objects
- [ ] Individual users connected their Salesforce accounts
- [ ] IP restriction and org URL change impacts documented

---

## Salesforce-Specific Gotchas

One-line summaries; the full entries are in [`references/gotchas.md`](references/gotchas.md).

| Gotcha | Short form |
|---|---|
| Roles, not people | Request and activation need Slack roles; approval needs a Salesforce System Admin |
| Government Cloud | Cannot connect; apps unsupported in Government Cloud and Government Cloud Plus |
| Per-user permission | Every Slack user needs Connect Salesforce with Slack on a supporting license |
| Previews | Follow the configured unfurling option and Slack Record Layout, not each viewer's FLS |
| Org limit | Up to 20 additional orgs on Pro, Business+, Enterprise |
| Legacy app | The Slack-built Salesforce app no longer supports new installations |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Connection plan | Roles, plan, orgs, mapping, unfurling, network decisions (checked by the skill script) |
| Data exposure register | Sensitive objects with their unfurling option and Slack Record Layout |
| User onboarding guide | Permission assignment and personal account connection steps |

---

## Related Skills

- slack-workflow-builder — for building Salesforce-connected automations in Slack Workflow Builder
- flow-for-slack — for Salesforce Flow-based Slack messaging and channel actions
- agentforce-in-slack — for deploying Agentforce agents into Slack
