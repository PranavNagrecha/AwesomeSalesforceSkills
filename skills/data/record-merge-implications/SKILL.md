---
name: record-merge-implications
description: "Use when merging Account, Contact, or Lead records in Salesforce and needing to understand what data is kept, what is deleted, and what side effects occur on related records. Triggers: 'which fields win in a merge', 'child records after merge', 'merge duplicate accounts', 'what happens to opportunities after contact merge', 'Lead merge field resolution'. NOT for deduplication strategy design (use data-quality-and-deduplication), NOT for Apex Merge DML beyond its direct implications."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
triggers:
  - "which record fields are kept when merging duplicate Accounts"
  - "what happens to child Opportunities when I merge Contacts"
  - "Lead merge losing important field values I need to preserve"
  - "merged record has wrong owner after Account merge"
  - "Activities and Cases after record merge — which survive"
  - "how does Salesforce resolve conflicting field values during merge"
tags:
  - data
  - merge
  - duplicates
  - account
  - contact
  - lead
  - field-resolution
inputs:
  - "Object type being merged (Account, Contact, or Lead)"
  - "Which record is the Master record"
  - "Which fields have conflicting values across merge candidates"
  - "Child/related objects present on the losing records (Opportunities, Cases, Activities)"
outputs:
  - "Field resolution rules for the merge outcome"
  - "List of child record reassignment behavior per related object"
  - "Side effects checklist for automation and reporting"
  - "Recommendations for preserving data before merge"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Record Merge Implications

Use this skill when merging duplicate Account, Contact, or Lead records — or when auditing what data was lost or reassigned after a merge already happened. This covers field resolution rules, child record behavior, automation side effects, and the differences between UI merge, Duplicate Management merge, and Apex `Database.merge()`.

---

## Before Starting

Gather this context before working on any merge task:

- Identify the **master record** — the surviving record after the merge. The master record's ID is preserved; all other record IDs are deleted and redirected.
- Confirm which **fields have conflicting values** across all merge candidates — these require explicit resolution decisions.
- Know which **child/related objects** exist on the losing records (Opportunities, Cases, Activities, Contacts on Account merges, etc.).
- Check whether any **automation** (Flows, Process Builder, Apex triggers) fires on the object being merged — merges can trigger record-triggered automation.

---

## Core Concepts

### The Master Record

The master record is the surviving record. Its **Salesforce ID is preserved**. All losing records' IDs are permanently deleted and replaced with a redirect (EntityId redirect). Any external system that stored the losing record's ID will receive a redirect on subsequent API calls — but only if the caller follows the redirect.

### Field Resolution Rules

During a UI merge, the user explicitly selects field values from the merge candidates. Each field value displayed in the merge UI comes from one of the selected records. Rules:

- **Non-blank fields from the master record are kept by default** — but the user can override by selecting a value from a losing record.
- **Blank fields on the master record are automatically filled** from the first non-blank value found in the losing records.
- **Standard fields with special merge rules** (e.g., `OwnerId`, `CreatedDate`) are not user-selectable in the UI — the master record's value is always used for `OwnerId`.

For **Apex `Database.merge()`**, there is no field selection step — the master record's existing field values are kept exactly as they are. Any field values on losing records that differ from the master are discarded unless you manually copy them to the master record before calling `Database.merge()`.

### Child Record Reassignment

When a record is merged, its related child records are re-parented to the master record. Behavior by object type:

| Child Object | Account Merge | Contact Merge | Lead Merge |
|---|---|---|---|
| Opportunities | Re-parented to master Account | Not applicable | Converted Lead's Opportunity kept; merged Lead's Opportunity deleted |
| Cases | Re-parented to master Account/Contact | Re-parented to master Contact | Not applicable |
| Contacts | Re-parented to master Account | (Contacts are merged, not re-parented) | Not applicable |
| Activities (Tasks, Events) | Re-parented to master record | Re-parented to master record | Re-parented to master record |
| Notes and Attachments | Re-parented to master record | Re-parented to master record | Re-parented to master record |
| Campaign Members | Duplicate Campaign Members deduplicated; one kept | Duplicate Campaign Members deduplicated | Not applicable (Lead CampaignMember) |

### Automation Side Effects

A record merge triggers:
- **Record-Triggered Flows and Apex triggers** configured on "before update" or "after update" — the merge itself is an update to the master record.
- **Workflow Rules** — fire on the master record update if criteria are met.
- **Duplicate Rules** — fire during merge if configured to block or alert on duplicates within the same merge operation.

The **losing records are deleted** — this fires "before delete" and "after delete" triggers/flows on those records.

### Lead Merge vs. Account/Contact Merge

Lead merge is more limited:
- Only Leads can be merged with Leads — not with Contacts or Accounts.
- The standard Lead merge UI shows up to 3 Leads at once.
- Converted Leads cannot be merged.
- After merge, the losing Lead's open Tasks and Events are re-parented to the master Lead.

---

## Common Patterns

### Preserving a Losing Record's Field Value Before Merge

**When to use:** A custom field on a losing record holds data not present on the master, and the Apex merge will not automatically copy it.

**How it works:**
1. Before calling `Database.merge()`, read the losing record's field values.
2. Copy the needed values to the master record using an update DML.
3. Call `Database.merge(masterRecord, losingRecordIds)`.

This ensures the master record's fields contain the preserved values before the merge completes.

### Auditing Child Record Count After Merge

**When to use:** After a merge, verifying that all related records were correctly re-parented.

Run a SOQL count before and after merge:
```
SELECT COUNT() FROM Opportunity WHERE AccountId = :losingAccountId
```
After merge, the same query on the losing Account ID should return 0. The master Account's count should have increased by the same number.

---

## Decision Guidance

| Scenario | Recommendation |
|---|---|
| Field values conflict between master and losing records | Explicitly select correct values in UI merge; or update master record fields before Apex merge |
| Losing record has Opportunities the master does not | Opportunities are re-parented automatically — verify in related list after merge |
| Merge is being done via Apex in bulk | Use `Database.merge()` with explicit field copy before merge; test in sandbox first |
| Automation is firing unexpectedly after merge | Check for before/after update triggers on master record and before/after delete triggers on losing records |
| Campaign Member duplication after Account merge | Salesforce auto-deduplicates Campaign Members on the same Campaign — one member record is kept |

---

## Recommended Workflow

1. **Identify the master record** — choose the record with the most complete data and the most critical relationships (e.g., the Account with Opportunities, or the Lead with the earliest Created Date).
2. **Review conflicting field values** — use the merge UI's field comparison screen or query the records directly to identify which fields differ.
3. **Preserve critical data from losing records** — if the merge is via Apex or if the UI does not expose a specific field, update the master record with the needed values before merging.
4. **Check automation exposure** — confirm whether any Flow, trigger, or workflow fires on the object. Disable or update if the automation would cause unintended side effects for a merge update.
5. **Execute the merge** — via the UI (Setup > Merge Accounts/Contacts/Leads) or `Database.merge()` in Apex.
6. **Verify child record re-parenting** — check related lists on the master record for re-parented Opportunities, Cases, and Activities.
7. **Confirm losing record IDs are redirected** — test any external system integrations that may hold old record IDs.

---

## Review Checklist

- [ ] Master record identified with correct ID preserved
- [ ] Conflicting field values reviewed and resolved
- [ ] Losing record's custom field values captured or copied to master if needed
- [ ] Child records verified in master's related lists post-merge
- [ ] Automation side effects evaluated — triggers, flows, workflows
- [ ] External systems holding losing record IDs updated or notified
- [ ] Converted Leads excluded from Lead merge operations

---

## Salesforce-Specific Gotchas

1. **`Database.merge()` does not copy fields automatically** — Unlike the UI merge which prompts for field selection, Apex merge keeps only the master record's current field values. Any data on losing records is discarded unless explicitly copied first.
2. **OwnerId always comes from the master record** — No matter which merge UI fields you select, `OwnerId` is always taken from the master record. If the losing record has the correct owner, update the master's `OwnerId` before merging.
3. **Converted Leads cannot be merged** — Attempting to merge a converted Lead raises an error. Filter out `IsConverted = true` Leads before processing a merge batch.
4. **Merges can trigger duplicate rules on the master record** — If Duplicate Rules are set to "Block" and the master record now appears to duplicate another record after the merge, the merge may be blocked.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field resolution summary | Table of conflicting fields and which record's value was selected |
| Child record audit | Before/after counts for Opportunities, Cases, Activities on master |
| Post-merge verification checklist | Confirms master record completeness and child re-parenting |

---

## Related Skills

- data-quality-and-deduplication — identifying and preventing duplicates at org level
- apex-dml-patterns — Apex DML including Database.merge() usage
