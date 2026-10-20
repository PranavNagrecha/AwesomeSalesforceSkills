---
name: record-merge-implications
description: "Use when merging Account, Contact, or Lead records in Salesforce and needing to understand what data is kept, what is deleted, and what side effects occur on related records. Triggers: 'which fields win in a merge', 'child records after merge', 'merge duplicate accounts', 'Lead merge field resolution'. NOT for deduplication strategy design — use admin/duplicate-management. NOT for Apex Merge DML beyond its direct implications."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Record Merge Implications

Use this skill when merging duplicate Account, Contact, or Lead records — or when auditing what data was lost or reassigned after a merge already happened. This covers field resolution rules, child record behavior, automation side effects, and the differences between UI merge, Duplicate Management merge, and Apex `Database.merge()`.

---

## Before Starting

Gather this context before working on any merge task:

- Identify the **master record** — the surviving record after the merge. The master record's ID is preserved; the other records are deleted and their `MasterRecordId` field is set to the winner (object_reference 264 L12945-12952). Only leads, contacts, cases and accounts can be merged, up to three records of the same sObject type (apexdev 264 L8173-8174, L8347).
- Confirm which **fields have conflicting values** across all merge candidates — these require explicit resolution decisions.
- Know which **child/related objects** exist on the losing records (Opportunities, Cases, Activities, Contacts on Account merges, etc.).
- Check whether any **automation** fires on the object being merged. Apex triggers are documented: one delete event for all losing records and one update event for the winner (apexdev 264 L15557-15566). UNVERIFIED (2026-10-20): Flows, Process Builder and workflow rules on merge are not described in the corpus.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is the merge UI-driven or `Database.merge()` in Apex? | references/gotchas.md Gotcha 1: Apex keeps the main record's values, nulls included (apexdev 264 L8349-8352) | Whether a pre-merge field-copy step is mandatory |
| Which fields on the losing records hold values the master lacks? | Gotcha 1 and references/examples.md Example 1: those values are discarded | A field-by-field copy list |
| Who must own the merged record? | Gotcha 2 below: Apex main-record values supersede, owner included; the UI rule is UNVERIFIED | The owner set on the master before the merge |
| Do external systems or integrations store the losing record Ids? | references/gotchas.md Gotcha 2: the losing Id is deleted and `MasterRecordId` points to the winner | An Id-mapping export taken before the merge |
| Which triggers exist on the object, and do any act on `MasterRecordId`? | references/gotchas.md Gotcha 5: delete fires on the losers, update on the winner, children fire nothing (apexdev 264 L15557-15573) | Triggers that read `MasterRecordId` in `after delete` |
| Are converted Leads or Campaign Member histories in scope? | references/gotchas.md Gotchas 3 and 4 and anti-patterns 2 and 5: both behaviours are UNVERIFIED, so test them | A sandbox test result instead of an assumption |
| Could anyone need to reverse the merge? | references/gotchas.md Gotcha 2 and Gotcha 5 below: undelete is possible but child re-parenting is not undone (apexdev 264 L8444-8445) | An agreed recovery path before bulk runs |

A proper configuration adds an owner and field-copy step, an Id-mapping export, trigger awareness of `MasterRecordId`, and a tested rollback story, instead of running the merge and finding the gaps afterwards.

---

## Core Concepts

### The Master Record

The master record is the surviving record. Its **Salesforce ID is preserved**. The losing records are deleted: "the merge operation merges the duplicate records into the main record, deletes the duplicate records, and reparents any related records" (apexdev 264 L8173-8174). Each deleted record keeps a pointer to the winner: "If this object was deleted as the result of a merge, this field contains the ID of the record that was kept" (`MasterRecordId`, object_reference 264 L12945-12952). To find losing records, query with `ALL ROWS` (apexdev 264 L8446) or REST `QueryAll`, which returns records soft deleted by a merge (api_rest 264 L17232). An earlier version of this skill described an "EntityId redirect" that makes old Ids resolve to the master; UNVERIFIED (2026-10-20): no corpus file describes any such redirect, so external systems must be re-pointed using `MasterRecordId` or an exported Id map.

### Field Resolution Rules

During a UI merge, the user explicitly selects field values from the merge candidates. UNVERIFIED (2026-10-20): the corpus does not describe the merge UI at all (grep of both directories finds only the Apex merge rules and the Help links in well-architected.md), so the three rules below are Help-level behaviour to verify in a sandbox:

- **Non-blank fields from the master record are kept by default** — but the user can override by selecting a value from a losing record.
- **Blank fields on the master record are automatically filled** from the first non-blank value found in the losing records.
- **Standard fields with special merge rules** (e.g., `OwnerId`, `CreatedDate`) are not user-selectable in the UI — the master record's value is always used for `OwnerId`.

For **Apex `Database.merge()`**, there is no field selection step: "Field values on the main record, including null and empty field values, always supersede the corresponding field values on the records to be merged. Therefore, if a field value on the main record is empty, the resulting field value remains empty after the merge operation regardless of the field value on the duplicate record. To preserve a field value from a duplicate record, manually set this field value on the main record before performing the merge" (apexdev 264 L8349-8352). External ID fields can't be used with merge (apexdev 264 L8353).

### Child Record Reassignment

When a record is merged, its related child records are re-parented to the master record (apexdev 264 L8173-8174; the guide's own example moves a child Contact to the surviving Account, L8178-8179). UNVERIFIED (2026-10-20): the per-object cells in this table are Help-level and not in the corpus — only the Account-to-Contact row is shown there. Behavior by object type:

| Child Object | Account Merge | Contact Merge | Lead Merge |
|---|---|---|---|
| Opportunities | Re-parented to master Account | Not applicable | Converted Lead's Opportunity kept; merged Lead's Opportunity deleted |
| Cases | Re-parented to master Account/Contact | Re-parented to master Contact | Not applicable |
| Contacts | Re-parented to master Account | (Contacts are merged, not re-parented) | Not applicable |
| Activities (Tasks, Events) | Re-parented to master record | Re-parented to master record | Re-parented to master record |
| Notes and Attachments | Re-parented to master record | Re-parented to master record | Re-parented to master record |
| Campaign Members | Duplicate Campaign Members deduplicated; one kept | Duplicate Campaign Members deduplicated | Not applicable (Lead CampaignMember) |

### Automation Side Effects

A record merge fires no trigger event of its own: "Merge events do not fire their own trigger events. Instead, they fire delete and update events" (apexdev 264 L15557-15558). In order: before delete fires, the system deletes the losers, reparents children and sets `MasterRecordId`, after delete fires, then the master is updated and "normal update triggers apply" (apexdev 264 L15568-15573). Specifically:
- **Apex triggers on the losing records** get a single delete event for all of them; `MasterRecordId` is set only in `after delete` (apexdev 264 L15559-15563).
- **Apex triggers on the winner** get a single update event; reparented child records fire no triggers at all (apexdev 264 L15564-15567).
- UNVERIFIED (2026-10-20): Record-Triggered Flows, Workflow Rules and Duplicate Rules reacting to a merge are not described in the corpus; test them in a sandbox.

### Lead Merge vs. Account/Contact Merge

Lead merge is more limited:
- Only Leads can be merged with Leads — not with Contacts or Accounts (records must be "of the same sObject type", apexdev 264 L8173-8174).
- Up to three Leads can be merged (apexdev 264 L8173-8174); UNVERIFIED (2026-10-20): that the UI shows three at once is Help-only.
- Converted Leads cannot be merged. UNVERIFIED (2026-10-20): not in the corpus.
- After merge, the losing Lead's open Tasks and Events are re-parented to the master Lead. UNVERIFIED (2026-10-20): not in the corpus beyond the general "reparents any related records" (apexdev 264 L8173-8174).

---

## Common Patterns

### Preserving a Losing Record's Field Value Before Merge

**When to use:** A custom field on a losing record holds data not present on the master, and the Apex merge will not automatically copy it.

**How it works:**
1. Before calling `Database.merge()`, read the losing record's field values.
2. Copy the needed values to the master record using an update DML.
3. Call `Database.merge(masterRecord, losingRecordIds)` (a main record plus up to two others; apexref 262 L208482, apexdev 264 L8348).

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
| Automation is firing unexpectedly after merge | Check for update triggers on the master record and delete triggers on the losing records; child reparenting fires no triggers (apexdev 264 L15564-15567) |
| Campaign Member duplication after Account merge | Salesforce auto-deduplicates Campaign Members on the same Campaign — one member record is kept (UNVERIFIED (2026-10-20): not in the corpus; verify in a sandbox) |

---

## Recommended Workflow

1. **Identify the master record** — choose the record with the most complete data and the most critical relationships (e.g., the Account with Opportunities, or the Lead with the earliest Created Date).
2. **Review conflicting field values** — use the merge UI's field comparison screen or query the records directly to identify which fields differ.
3. **Preserve critical data from losing records** — if the merge is via Apex or if the UI does not expose a specific field, update the master record with the needed values before merging.
4. **Check automation exposure** — confirm whether any Flow, trigger, or workflow fires on the object. Disable or update if the automation would cause unintended side effects for a merge update.
5. **Execute the merge** — via the UI (UNVERIFIED (2026-10-20): the Setup path is Help-only) or `Database.merge()` in Apex.
6. **Verify child record re-parenting** — check related lists on the master record for re-parented Opportunities, Cases, and Activities.
7. **Re-point external references** — export the losing-Id to master-Id map before the merge (or read `MasterRecordId` from the deleted rows with `ALL ROWS`) and update any external system that holds old record Ids.

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
2. **OwnerId always comes from the master record** (UNVERIFIED (2026-10-20): for the UI this is Help-only; for Apex it follows from the main-record-supersedes rule, apexdev 264 L8349-8350) — No matter which merge UI fields you select, `OwnerId` is always taken from the master record. If the losing record has the correct owner, update the master's `OwnerId` before merging.
3. **Converted Leads cannot be merged** (UNVERIFIED (2026-10-20): not in the corpus; the error text is also unverified) — Attempting to merge a converted Lead raises an error. Filter out `IsConverted = true` Leads before processing a merge batch.
4. **Merges can trigger duplicate rules on the master record** (UNVERIFIED (2026-10-20): not in the corpus) — If Duplicate Rules are set to "Block" and the master record now appears to duplicate another record after the merge, the merge may be blocked.
5. **A merge can be partly undone, but not the re-parenting** — "You can undelete records that were deleted as the result of a merge. However, the merge reparents the child objects, and that reparenting can't be undone" (apexdev 264 L8444-8445).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field resolution summary | Table of conflicting fields and which record's value was selected |
| Child record audit | Before/after counts for Opportunities, Cases, Activities on master |
| Post-merge verification checklist | Confirms master record completeness and child re-parenting |

---

## Related Skills

- data/data-quality-and-governance — identifying and preventing duplicates at org level
- admin/duplicate-management — duplicate and matching rule design
- apex/apex-dml-patterns — Apex DML including Database.merge() usage
