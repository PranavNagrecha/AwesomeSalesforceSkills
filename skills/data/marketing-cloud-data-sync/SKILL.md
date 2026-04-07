---
name: marketing-cloud-data-sync
description: "Use this skill when configuring, diagnosing, or extending Marketing Cloud Connect Synchronized Data Sources — the mechanism that pulls Salesforce CRM object records into read-only Synchronized Data Extensions (SDEs) in Marketing Cloud. Triggers on: synced data extension not updating, contact or lead records missing from Marketing Cloud, sync failures in Contact Builder, 250-field limit questions, CRM-to-MC data latency concerns. NOT for manual imports via Import Activity, NOT for SFTP-based data loads, NOT for Data Cloud (CDP) real-time data streams, NOT for direct Apex callouts into Marketing Cloud."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Performance
tags:
  - marketing-cloud
  - synchronized-data-extensions
  - mc-connect
  - contact-builder
  - crm-sync
  - data-extensions
inputs:
  - "MC Connect installation status and Salesforce Connector configuration in Marketing Cloud Setup"
  - "List of CRM objects to sync (Contact, Lead, Account, Campaign, CampaignMember, Case, User, or custom objects)"
  - "Field mapping intent — which CRM fields need to be available in Marketing Cloud"
  - "Send audience design — whether sends will target Contacts or Leads, and which DEs are sendable"
  - "Sync failure symptoms or error messages from Contact Builder or MC Connect logs"
outputs:
  - "Configured Synchronized Data Sources in Contact Builder with correct object and field selections"
  - "Contact Builder relationship map linking SDEs to sendable Data Extensions"
  - "Sync troubleshooting diagnosis (field type mismatch, deleted field, API limit, or audience shrink cause)"
  - "Decision guidance on full sync vs incremental sync frequency"
  - "Checklist confirming sync configuration is complete and audience pipeline is valid"
dependencies: []
triggers:
  - "synced data extension not updating with new CRM records"
  - "contact or lead records missing from Marketing Cloud after sync"
  - "sync failures showing in Contact Builder or MC Connect logs"
  - "250 field limit questions for synchronized objects"
  - "CRM to Marketing Cloud data latency concerns"
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Marketing Cloud Data Sync

This skill activates when a practitioner needs to configure, diagnose, or optimize the Marketing Cloud Connect Synchronized Data Sources feature — which pulls CRM object records from Salesforce into read-only Synchronized Data Extensions (SDEs) in Marketing Cloud on a near-real-time to 15-minute schedule. It covers the full pipeline from MC Connect setup through Contact Builder relationship configuration and sync failure triage.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm MC Connect is installed and the Salesforce Connector is configured in Marketing Cloud Setup — sync cannot function without it. The connected org must be an active Salesforce CRM production or sandbox org.
- The most common wrong assumption is that SDEs are writable or directly sendable. SDEs are strictly read-only and cannot be used as send audiences without being joined to a sendable Data Extension via Contact Builder relationships.
- The hard field cap is 250 fields per synchronized object. Fields beyond 250 are silently excluded — no error appears in the UI, so practitioners regularly discover missing data only after sends have already run.

---

## Core Concepts

### Synchronized Data Extensions (SDEs)

SDEs are read-only copies of Salesforce CRM object records maintained by Marketing Cloud Connect. They are stored in the Synchronized Data Sources section of Contact Builder, not in the main Data Extensions folder. Records are synced on an automatic (near-real-time, triggered by CRM change) or scheduled (up to every 15 minutes) basis. SDEs cannot be the target of an Import Activity, a Query Activity write, or an AMPscript `InsertDE()` call. Any attempt to write to an SDE will fail.

The objects that can be synchronized are: Contact, Lead, Account, Campaign, CampaignMember, Case, User, and eligible custom objects. Not every field type is supported — binary fields, rich text fields, and encrypted CRM fields cannot be synced.

### The 250-Field Limit and Silent Exclusion

Each synchronized object is subject to a hard cap of 250 fields. If the CRM object has more than 250 fields selected for sync, Marketing Cloud silently drops fields beyond the limit. No error message appears in Contact Builder or in sync logs. The only way to discover which fields were excluded is to inspect the SDE column list after sync and compare it to the intended field selection. This is a frequent source of missing personalization data discovered after campaign sends have gone out.

### Sync Frequency: Automatic vs Scheduled

Marketing Cloud Connect supports two sync modes:
- **Automatic (triggered):** Syncs near-real-time when a CRM record changes. This is resource-efficient for typical CRM update volumes.
- **Scheduled:** Runs on a fixed interval, minimum every 15 minutes. Used when triggered sync is insufficient or for initial population.

Full sync re-pulls all records for an object and is resource-intensive. It should be reserved for initial setup or data corruption recovery. Incremental sync tracks changed records only and is the correct operational mode. Avoid triggering full syncs routinely as they consume Salesforce API calls and can hit API limits during peak business hours.

### Contact Builder Relationships and Send Audiences

SDEs cannot be used as send audiences directly. To send to contacts or leads from SDE data, practitioners must:
1. Create or identify a sendable Data Extension in the main DE folder (must have a field linked to a subscriber key or Contact Key).
2. In Contact Builder, define a relationship between the SDE and the sendable DE using a shared key (e.g., Contact ID or Lead ID mapped to a subscriber attribute).
3. Reference both DEs in the Audience or Query used for the send.

Without this relationship, marketers cannot send to records sourced from the CRM sync — a critical design requirement often overlooked during initial setup.

---

## Common Patterns

### Pattern: SDE-to-Sendable DE Join for Email Sends

**When to use:** A marketing team needs to send to Salesforce Contacts or Leads using CRM field data for personalization (e.g., Account Name, Case Status, Opportunity Stage).

**How it works:**
1. Confirm Contact and/or Lead SDE is syncing in Contact Builder > Synchronized Data Sources.
2. Ensure a sendable DE exists with Contact Key (or subscriber key) as the send relationship field.
3. In Contact Builder > Data Designer, create a link from the Contact (or Lead) SDE to the sendable DE using the subscriber key attribute.
4. In Journey Builder or Email Studio, build the audience from the sendable DE; use AMPscript or personalization strings to pull data from the SDE via the relationship.

**Why not the alternative:** Attempting to send directly to the SDE fails because SDEs have no send relationship defined and are not writable. Attempting to copy SDE data manually via Import Activity on a schedule is fragile and bypasses the sync mechanism entirely.

### Pattern: Diagnosing a Sync Failure

**When to use:** Records that exist in Salesforce CRM are not appearing in the corresponding SDE, or the SDE appears stale.

**How it works:**
1. In Marketing Cloud, navigate to Contact Builder > Synchronized Data Sources and inspect the sync status for the affected object. Note the last sync time and any error indicators.
2. Check for field type mismatches: if a CRM field type changed (e.g., Text to Picklist) without the SDE field mapping being refreshed, sync can fail silently for that field.
3. Check for deleted CRM fields still present in the sync mapping — remove them from the field selection in Contact Builder.
4. Check Salesforce API limit consumption. If the CRM org is approaching its daily API limit, MC Connect sync calls may be throttled or dropped during the sync window.
5. Validate that the connected user (the Salesforce user whose credentials MC Connect uses) has read access to all fields being synced, including FLS settings.

**Why not the alternative:** Triggering a full sync as a first response to a stale SDE is wasteful and can exhaust API limits. Diagnose incrementally before resorting to full sync.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| CRM object has more than 250 fields | Prioritize and select only the 250 fields needed for marketing use; document excluded fields | Silent exclusion at 250 makes unmapped fields invisible; selection must be intentional |
| Records deleted in CRM are unexpectedly removed from send audience | Audit Contact Builder relationship and check SDE for deleted record sync behavior; use a filter on the sendable DE | Deleted CRM records sync as deleted in the SDE, which can silently shrink the audience |
| Need real-time CRM data in Marketing Cloud sends | Use automatic (triggered) sync mode and design journeys that fire on CRM updates via Marketing Cloud Connect triggers | Scheduled sync at 15-min intervals may be too stale for transactional or behavioral triggers |
| Encrypted CRM fields needed in MC | Identify an alternative non-encrypted field or create a formula field with safe representation | Encrypted fields cannot be synced — no workaround exists at the sync layer |
| Custom object sync needed | Confirm the custom object is enabled for MC Connect sync in the connector settings; map external ID field | Not all custom objects are automatically available — explicit enablement is required |
| Binary or rich text fields required | Extract content to a separate plain text field in CRM before sync | Binary and rich text field types are not supported by the sync mechanism |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify MC Connect prerequisites:** Confirm Marketing Cloud Connect is installed in Salesforce and the Salesforce Connector is active in Marketing Cloud Setup > Platform Tools > Apps > Salesforce Integration. Without this, no sync is possible.
2. **Select synchronized objects and fields in Contact Builder:** Navigate to Contact Builder > Synchronized Data Sources. Add or edit each CRM object (Contact, Lead, Account, etc.). Select only the fields needed — stay under the 250-field cap. Document which fields are selected and which are excluded.
3. **Configure sync frequency:** Set each object to Automatic sync for near-real-time updates. Reserve Scheduled sync for objects with low change volume or full sync scenarios. Avoid triggering manual full syncs unless recovering from data corruption.
4. **Build Contact Builder relationships:** In Contact Builder > Data Designer, map the SDE to the sendable Data Extension using a shared key field (Contact Key / subscriber key). Validate that the relationship is complete and traversable before building any send audience.
5. **Validate sync health:** After initial sync, inspect each SDE's column list against the intended field selection to confirm no silent exclusions occurred due to the 250-field cap. Check the last sync timestamp and record count against CRM source counts.
6. **Diagnose and resolve sync failures:** If records are missing or the SDE is stale, check: field type mismatches, deleted mapped fields, Salesforce API limit consumption, and FLS access for the connected user. Fix root cause before triggering a full sync.
7. **Test the full send pipeline:** Run a test send or preview against a small segment that uses the SDE relationship to confirm personalization fields resolve correctly and audience counts match expectations before launching to full audience.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] MC Connect is installed and the Salesforce Connector is active in Marketing Cloud Setup
- [ ] All synchronized objects have been configured in Contact Builder > Synchronized Data Sources with field selections at or below 250 fields per object
- [ ] SDE column list has been inspected post-sync to confirm no silent field exclusions
- [ ] Contact Builder relationships are defined linking each SDE to the appropriate sendable DE via a shared subscriber key
- [ ] Sync mode (Automatic vs Scheduled) is configured appropriately for each object's update frequency
- [ ] Encrypted fields, binary fields, and rich text fields have been identified and excluded from sync mapping
- [ ] A test send or preview has been run and personalization fields from the SDE resolve correctly
- [ ] Sync failure triage completed: field type mismatches, deleted field mappings, and API limit exposure all checked

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Silent 250-field exclusion** — When a CRM object has more than 250 fields selected for sync, Marketing Cloud drops the excess fields with no error, warning, or log entry. Practitioners discover the problem only when a personalization field is blank in live sends. Always audit the SDE column list against the intended field mapping after initial sync.

2. **Deleted CRM records propagate to SDE and shrink audiences** — When a Contact or Lead is deleted in Salesforce CRM, the record is synced as deleted in the SDE. Any audience built purely from the SDE will silently shrink. If the sendable DE is not refreshed, subscribers may receive emails but unsubscription or bounce processing may be affected by the missing record. Design audiences to filter on active status fields rather than relying on record existence alone.

3. **SDEs are not writable by any mechanism** — There is no supported path to insert, update, or delete SDE records from within Marketing Cloud (no AMPscript, no SSJS, no Import Activity, no Query Activity write). Practitioners sometimes attempt to use Query Activity to populate an SDE — this will throw an error. All data in SDEs must originate from the CRM sync process.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Synchronized Data Source configuration | Contact Builder object and field selection for each synced CRM object, with sync mode documented |
| Contact Builder relationship map | Data Designer link between each SDE and the corresponding sendable DE, keyed on subscriber/Contact Key |
| Sync health validation report | Post-sync field count comparison and record count audit confirming no silent exclusions |
| Sync failure diagnosis | Root cause identification (field mismatch, deleted field, API limit, FLS gap) with remediation steps |

---

## Related Skills

- `admin/marketing-cloud-connect` — Use when configuring the initial MC Connect installation and Salesforce Connector in Marketing Cloud Setup; this skill assumes Connect is already installed
- `data/data-extension-design` — Use when designing the sendable Data Extension that will receive the Contact Builder relationship from the SDE
- `admin/journey-builder-administration` — Use when the sync feeds a Journey Builder entry source or real-time trigger based on CRM record changes
