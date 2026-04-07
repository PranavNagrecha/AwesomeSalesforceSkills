---
name: marketing-cloud-connect
description: "Use this skill when configuring or troubleshooting Marketing Cloud Connect (MC Connect) — the managed package that links a Salesforce org to a Marketing Cloud account. Covers connector user setup, synchronized data sources, scope configuration, tracking sync, and triggered sends. NOT for MCAE (Marketing Cloud Account Engagement / Pardot) connector setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "subscribers from Salesforce are missing in Marketing Cloud sends"
  - "synchronized data extension is not updating with new Salesforce records"
  - "how to set up Marketing Cloud Connect managed package in Salesforce org"
  - "MC Connect connector user permissions and profile configuration"
  - "scope configuration mismatch causing partial subscriber visibility in Marketing Cloud"
  - "MC tracking data not syncing back to Salesforce campaign members"
  - "triggered send from Salesforce Flow or Process Builder to Marketing Cloud"
tags:
  - marketing-cloud-connect
  - synchronized-data-sources
  - mc-connect
  - email-studio
  - connector-user
inputs:
  - "Salesforce org edition and whether Marketing Cloud Connect managed package is installed"
  - "Marketing Cloud account ID and whether it is a parent or child BU"
  - "Connector user username and the permission set assigned"
  - "Objects being synchronized (Lead, Contact, Campaign, etc.)"
  - "Scope setting: Org-Wide or Business Unit-specific"
outputs:
  - "Validated connector user setup with correct permissions"
  - "Synchronized data source configuration for selected objects"
  - "Scope configuration aligned to intended subscriber set"
  - "Tracking sync confirmation for campaign member activity records"
  - "Triggered send configuration from Salesforce automation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Marketing Cloud Connect

This skill activates when a practitioner is installing, configuring, or troubleshooting Marketing Cloud Connect — the Salesforce-managed package that bridges a Salesforce CRM org and a Marketing Cloud account. It covers the full setup path: connector user, synchronized data sources, scope, tracking, and triggered sends. It does NOT cover MCAE (formerly Pardot) or Marketing Cloud Growth Edition.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Marketing Cloud Connect managed package is installed in the Salesforce org (AppExchange package: "Salesforce Marketing Cloud").
- Confirm the Marketing Cloud account type: single-org tenant, or multi-org (Enterprise 2.0 with multiple Business Units). Scope configuration differs.
- Identify the dedicated connector user in Salesforce — this must be a standard internal Salesforce user (not a community/Experience Cloud user, not a portal user). The connector user must have the "Marketing Cloud" permission set assigned.
- The most common wrong assumption: practitioners assume any admin user can be used as the connector user. Salesforce requires a dedicated, purpose-built user. Sharing the connector user's credentials or changing its profile after connect setup will silently break sync.
- Platform constraint: Synchronized Data Sources (SDS) support up to 250 fields per synchronized object. Fields beyond that limit are silently excluded with no error or warning.

---

## Core Concepts

### Connector User

MC Connect authenticates to Salesforce using a dedicated Salesforce user called the connector user. This user:

- Must be a standard internal Salesforce user (not community, not portal).
- Must have the "Marketing Cloud" permission set assigned.
- Must have API access enabled on its profile.
- Should have its own dedicated profile rather than sharing one with human users — profile or permission changes after connect setup can break sync without surfacing errors immediately.
- Its password must not be reset or expired; password expiration policies should exempt this user.

The connector user is set during initial Marketing Cloud account connection in Marketing Cloud Setup > Salesforce Integration. Once set, changes require re-authentication and re-linking.

### Synchronized Data Sources (SDS)

SDS replicates selected Salesforce objects (Lead, Contact, Campaign, CampaignMember, and others) as read-only data extensions in Marketing Cloud Contact Builder. Key behaviors:

- Sync runs approximately every 15 minutes.
- SDS data extensions are read-only. They cannot be used directly as a send audience.
- To use SDS data in a send, create a sendable data extension via a Contact Builder data relationship or an Automation Studio SQL query activity that selects from the SDS DE.
- The 250-field limit per synchronized object is hard. Fields beyond 250 are silently excluded — no log entry, no warning in the UI. Always count fields before enabling sync for wide objects.
- Contact Key in Marketing Cloud is matched to the Salesforce Contact ID or Lead ID. Mismatched Contact Key strategy is a common data hygiene issue.

### Scope Configuration

Scope determines which Salesforce records are accessible to Marketing Cloud sends when using MC Connect. Options:

- **Org-Wide scope**: All records in the org are accessible to the connected Marketing Cloud account.
- **Business Unit (BU) scope**: Only records associated with the specific Marketing Cloud Business Unit are accessible.

Scope mismatch is the most frequent root cause of "missing subscribers" issues. If the send scope in Marketing Cloud does not match the records available in the SF connector scope, records will not appear in the audience. Review scope settings under Marketing Cloud Connect > Configuration in both the Salesforce org and Marketing Cloud Setup.

### Tracking Sync

After a Marketing Cloud send, engagement data (opens, clicks, bounces, unsubscribes) syncs back to Salesforce:

- Campaign Member records receive send/open/click/bounce/unsubscribe activity.
- Individual Lead and Contact records get email activity written to their activity timeline.
- SAP (Service and Support) object tracking allows sends tied to Cases; tracking writes back to Case activity.
- Tracking sync runs as a background job; there can be a delay of 15–30 minutes after a send before Salesforce reflects engagement data.

### Triggered Sends

MC Connect enables Salesforce automation (Flow, Process Builder, legacy Workflow Rules) to trigger transactional Marketing Cloud email sends:

- A "Triggered Send" in Marketing Cloud is created and linked to a Triggered Send Definition.
- In Salesforce, an outbound message or Flow action calls the MC Connect API to fire the triggered send when a record matches the criteria.
- Triggered sends require the connector user to have the correct API permissions and the Triggered Send Definition to be Active in Marketing Cloud.

---

## Common Patterns

### Pattern 1: Initial MC Connect Setup

**When to use:** First-time connection between a Salesforce org and Marketing Cloud account.

**How it works:**
1. Install the "Salesforce Marketing Cloud" managed package from AppExchange into the Salesforce org.
2. Create a dedicated connector user in Salesforce (standard internal user, unique email). Assign the "Marketing Cloud" permission set. Ensure API access is on the user's profile.
3. In Marketing Cloud Setup > Platform Tools > Apps > Salesforce Integration, click Connect Account and authenticate with the connector user credentials.
4. Configure scope (Org-Wide or BU-level) during the connection wizard.
5. Navigate to Marketing Cloud Connect > Configuration in the Salesforce org to verify connection status shows "Connected".
6. Enable Synchronized Data Sources for Lead, Contact, and Campaign under MC Connect > Synchronized Data Sources. Allow up to 15 minutes for initial sync.

**Why not the alternative:** Using an existing admin user as the connector user means any change to that admin's profile, permission, or password will break all MC Connect sync without warning. A dedicated connector user isolates the integration credential.

### Pattern 2: Fixing Missing Subscribers Due to Scope Mismatch

**When to use:** Marketing Cloud sends are reporting fewer subscribers than expected; records visible in Salesforce do not appear in MC audience builder.

**How it works:**
1. In the Salesforce org, go to Marketing Cloud Connect > Configuration and note the Scope setting.
2. In Marketing Cloud Setup > Salesforce Integration, confirm the connected org and Business Unit.
3. Compare the scope in both places. If the SF connector is set to Org-Wide but the MC send is scoped to a specific BU, records outside that BU's data scope will be excluded.
4. Align the scope: either set both to Org-Wide, or configure BU-specific scope and ensure the records' owner or assignment matches the BU scope rules.
5. Trigger a manual sync refresh and re-run the audience count to confirm records now appear.

**Why not the alternative:** Simply adding records to the Data Extension manually bypasses the relationship between SF CRM records and MC tracking, breaking click/open write-back to Campaign Members.

### Pattern 3: Triggered Send from Salesforce Flow

**When to use:** A transactional email (order confirmation, password reset, welcome) needs to fire from a Salesforce record update.

**How it works:**
1. In Marketing Cloud Email Studio, create a Triggered Send Definition. Set the send classification to Transactional. Publish and start the Triggered Send.
2. In Salesforce, create a Flow that fires on the desired record trigger condition.
3. Add a "Call MC Connect Triggered Send" action in the Flow (available after managed package install). Map the Salesforce record ID and subscriber key.
4. Test in Salesforce by triggering the Flow on a test record; verify the email lands and tracking writes back.

**Why not the alternative:** Using a Scheduled Journey in Marketing Cloud for transactional sends introduces latency and requires Journey Builder licensing. Triggered Sends are lower-latency and Transactional classified — they respect suppression lists differently than commercial sends.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to use SF Contact/Lead data as send audience in MC | Create sendable DE from SDS via SQL query or Contact Builder relationship; do not send directly to SDS DE | SDS DEs are read-only and not directly sendable |
| Connector user password expired or profile changed | Reset connector user password, update in MC Setup > Salesforce Integration, re-authenticate | Stale credentials silently break all sync jobs |
| Object has more than 250 fields and all are needed | Prioritize the 250 fields that will be used in MC; document excluded fields explicitly | 250-field limit is hard and silent; no error surfaced |
| Multi-BU MC account sending to SF records from different divisions | Use BU-specific scope with record ownership/territory aligned to BU; avoid Org-Wide if sends must be BU-isolated | Org-Wide scope exposes all records to all BUs, which can violate data governance |
| Tracking data not appearing on Campaign Members | Check connector user API access; verify Campaign and CampaignMember are in SDS sync; allow 30 min post-send | Tracking sync runs asynchronously and depends on SDS being active for Campaign objects |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites**: Confirm the MC Connect managed package is installed in the org, a dedicated connector user exists with the Marketing Cloud permission set, and the connector user is not a community or Experience Cloud user.
2. **Check connection status**: In Salesforce, go to Marketing Cloud Connect > Configuration. Status must show "Connected." If not, re-authenticate using the connector user credentials in Marketing Cloud Setup > Salesforce Integration.
3. **Review scope configuration**: Note the scope setting on both the Salesforce side (MC Connect > Configuration) and the Marketing Cloud side (Setup > Salesforce Integration). Confirm they are aligned to the intended subscriber population.
4. **Audit Synchronized Data Sources**: Identify which objects are enabled for sync. For each enabled object, verify the field count is under 250. Check the Last Sync Timestamp to confirm sync is running. If sync has stalled, check the connector user's profile and API access.
5. **Validate sendable DE setup**: Confirm that no send job is targeting an SDS DE directly. Verify sendable DEs are created via SQL activity or Contact Builder relationship, with a valid Contact Key mapping.
6. **Test tracking write-back**: After a test send, wait 30 minutes and check a Campaign Member record for email activity fields (Send Date, Open Date, etc.). If empty, verify Campaign and CampaignMember are in SDS and the connector user has read/write access to those objects.
7. **Document configuration**: Record the connector user username, scope setting, synced objects, and any excluded fields in a configuration log. This simplifies future troubleshooting.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Connector user is a standard internal Salesforce user with the Marketing Cloud permission set assigned
- [ ] Connector user profile has API Enabled and is not subject to password expiration policies that will expire it
- [ ] MC Connect configuration in Salesforce shows status "Connected"
- [ ] Scope setting is intentionally configured and matches between Salesforce and Marketing Cloud sides
- [ ] All synchronized objects have fewer than 250 fields enabled; fields beyond 250 are documented
- [ ] No send jobs target SDS DEs directly; sendable DEs are built via SQL or Contact Builder relationship
- [ ] Tracking sync confirmed by checking Campaign Member email activity after a test send
- [ ] Triggered send definitions (if used) are Active in Marketing Cloud and tested end-to-end

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **250-field limit is silent** — When a synchronized object exceeds 250 fields, fields beyond the limit are excluded from the SDS data extension with no error, warning, or log entry in either Salesforce or Marketing Cloud. Discovery only happens when a marketer reports a missing merge field. Audit field counts before enabling sync.
2. **Connector user profile changes break sync without alerting** — If an admin modifies the connector user's profile, removes a permission set, or resets its password without updating Marketing Cloud, all SDS jobs and triggered sends silently fail. The status page may still show "Connected" for hours until the next sync attempt. Always treat the connector user as infrastructure — changes require a change-control process.
3. **SDS DEs are read-only and not directly sendable** — Practitioners routinely try to select an SDS DE as a send audience and receive errors or get 0 sends. SDS DEs cannot be targeted directly. A SQL query activity or Contact Builder sendable relationship must be created on top of the SDS DE.
4. **Scope mismatch produces no error — just missing records** — If scope is misconfigured, Marketing Cloud will silently exclude records rather than surfacing an error. A send will complete "successfully" with a smaller-than-expected subscriber count. Always validate subscriber counts against the expected CRM population before a production send.
5. **Contact Key strategy misalignment causes duplicate contacts** — MC Connect defaults to using the Salesforce Contact ID as the Contact Key in Marketing Cloud. If the org has a custom Contact Key strategy (e.g., email address as key), mismatched keys will create duplicate MC contacts, split engagement history, and corrupt subscription status. Align Contact Key strategy before initial sync.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| MC Connect configuration status | Screenshot or log confirming "Connected" status in Marketing Cloud Connect > Configuration |
| Synchronized objects list | Table of synced objects, field counts, last sync timestamp, and any excluded fields |
| Scope configuration record | Documentation of scope type (Org-Wide or BU) and alignment with MC Business Unit |
| Sendable DE mapping | List of sendable DEs built from SDS, including Contact Key field mapping |
| Tracking verification log | Post-send check confirming email activity on Campaign Member records |

---

## Related Skills

- admin/email-studio-administration — for Email Studio content, sender authentication, and deliverability settings within Marketing Cloud
- admin/mcae-pardot-setup — for Marketing Cloud Account Engagement (Pardot) connector; a distinct product and distinct setup path from MC Connect
- admin/campaign-management — for Salesforce Campaign and Campaign Member setup that feeds MC Connect tracking write-back
