---
name: apex-managed-sharing
description: "Sharing records programmatically via Apex: Share objects, row cause, Apex sharing reason, sharing recalculation, with/without sharing patterns. NOT for declarative sharing rules — use admin/sharing-and-visibility. NOT for recalc job runtime — use data/sharing-recalculation-performance."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "how do I share a record with a user programmatically in Apex"
  - "custom object share table insert row cause apex"
  - "sharing recalculation batch apex without sharing"
  - "apex managed sharing cleared after ownership change"
  - "how to create an apex sharing reason for a custom object"
tags:
  - apex-sharing
  - share-objects
  - row-cause
  - sharing-recalculation
  - programmatic-sharing
inputs:
  - Custom or standard object for which programmatic sharing is required
  - User or group IDs that need access
  - Desired access level (Read, Edit)
  - Whether a custom Apex sharing reason (row cause) is needed
outputs:
  - Share record DML (insert/delete of __Share or standard Share objects)
  - Apex sharing reason metadata definition guidance
  - Sharing recalculation batch class implementation
  - Checker report on Apex sharing patterns in existing classes
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Apex Managed Sharing

This skill activates when a practitioner needs to grant or revoke record-level access programmatically using Apex — by directly inserting or deleting rows in a Share object — rather than through declarative sharing rules, manual sharing, or role hierarchy. Use it for territory-based sharing, dynamic cross-role access, or any scenario where the sharing grant logic belongs in code, not setup.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the object's OWD (Org-Wide Default). Apex managed sharing only extends access beyond what OWD already grants: the share's access level "must be set to an access level that's higher than the organization's default access level" (apex dev guide 264 L12731-12732), and the OWD "must not be set to the most permissive access level" — Public Read/Write for custom objects (L12867-12868). A share at or below the default fails with `FIELD_FILTER_VALIDATION_EXCEPTION` whose message contains `AccessLevel` (L12803-12804, L12996-12999). Only users with "Modify All Data" can add or change Apex managed sharing on a record (L12610, L12873-12874).
- Decide between `Manual` and an Apex sharing reason. Manual shares are user managed sharing: "if the owner of the record changes, the sharing is automatically deleted" (apex dev guide 264 L12751-12752, L12756-12757). "Apex managed sharing must use an Apex sharing reason" and "is maintained when the record owner changes or is deactivated" (L12874-12875).
- Confirm that the Apex sharing reason exists before inserting rows that reference it. "Apex sharing reasons aren't available in Lightning Experience. Use Salesforce Classic to create sharing reasons within the UI", which is supported only for custom objects; for standard objects deploy a `SharingReason` component through the Metadata API (L12879-12883, L12916-12917; the earlier "Object Manager > Apex Sharing Reasons" path is CONTRADICTED). UNVERIFIED (2026-10-20): the exact exception when the reason is missing.
- Know the governor limits in play: records processed by DML are capped at 10,000 in both synchronous and asynchronous Apex (apex dev guide 264 L19759). Sharing recalculation frequently requires batch Apex.

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `SKILL.md` § Salesforce-Specific Gotchas and `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is the object's OWD, and what access will the grant give?" | A grant at or below the default level is rejected (gotcha 4) | A level strictly above the OWD, or a different mechanism |
| "Custom or standard object, and how long must the grant live?" | Manual shares go on an owner change; a reason on a standard object needs Metadata API 68.0+ and an org test, and the object reference still says Manual only (gotchas 1, 3; Core Concepts) | `Manual` or an Apex sharing reason, with the Classic-UI or Metadata API path chosen |
| "Who runs the code that writes the shares?" | Only Modify All Data can add or change Apex managed sharing (Before Starting) | A named running user or service context |
| "What rebuilds the shares after an OWD change?" | A recalculation class runs on an OWD change (gotcha 1) | A `Database.Batchable` associated with the object |
| "Does the recalculation class see every parent record?" | The guide's sample is `without sharing` (gotcha 2) | The sharing keyword and a comment justifying it |
| "Could the same grant be written twice?" | Repeat inserts update or collide (gotcha 5) | A query-then-insert path or `Database.insert(list, false)` |
| "Is the sharing reason deployed with the code?" | `RowCause` is a restricted picklist (gotcha 3) | The `SharingReason` component in the deployment package |

A proper configuration adds an OWD that leaves room above it, a named row cause, a recalculation class and a rebuild test, where "just doing it" gives grants that vanish on an owner change or never insert.

---

## Core Concepts

### Share Object Anatomy

Every Salesforce object that supports sharing has a corresponding Share object. For standard objects the name is `<ObjectName>Share` (e.g., `AccountShare`, `OpportunityShare`). For custom objects the name is `<ObjectAPIName>__Share` (e.g., `Territory_Assignment__Share`).

Every Share record has four core fields:

| Field | Type | Description |
|---|---|---|
| `ParentId` | ID | The ID of the record being shared |
| `UserOrGroupId` | ID | The ID of the User, Role, or Group being granted access |
| `AccessLevel` | String | `Read` or `Edit`; `All` is "an internal value and can't be granted" (apex dev guide 264 L12727-12730). On standard share objects the property is named `<Object>AccessLevel`, for example `LeadAccessLevel` (L12723-12725) or `AccountAccessLevel` (object_reference 264 L17371-17379) |
| `RowCause` | String | Why the share was granted. `Manual` is the default (apex dev guide 264 L12782; object_reference 264 L17472-17474). Custom reasons use the `__c` suffix. |

Objects on the detail side of a master-detail relationship have no share object (apex dev guide 264 L12713). For custom objects there is also a `RowCause` value of `Owner` (platform-created managed sharing, L12630) and any Apex sharing reasons you have defined.

### Apex Sharing Reasons (Custom Row Causes)

An Apex sharing reason is a metadata record created in Setup under Object Manager > [Custom Object] > Apex Sharing Reasons. Once created, its API name is available as a string constant on the Share object: `<ObjectAPIName>__Share.rowCause.<ReasonName>__c`.

Using a custom row cause instead of `Manual`:

- Apex managed sharing is maintained when the record owner changes or is deactivated; Manual sharing is removed on an owner change (apex dev guide 264 L12610-12611, L12606). The earlier "survives manual sharing recalculation" wording is replaced: the corpus does not describe a manual recalculation that clears `Manual` rows.
- When the OWD changes, Salesforce recalculates sharing and removes sharing that has become redundant, and "any Apex recalculation classes defined for associated custom object are also executed" (L13049-13052, L13071-13072). UNVERIFIED (2026-10-20): that all Apex-managed rows are deleted on an OWD change or a full recalculation.
- The reason name becomes auditable — queries on the Share table can filter by `RowCause` to isolate Apex-managed grants.

For standard objects the corpus disagrees with itself, and the disagreement has a version line. The Metadata API says sharing reasons for standard objects "are available in API version 68.0 and later" (Winter '27), for objects that have a share object (AccountShare, OpportunityShare) and whose OWD can be Private or Public Read-Only (api_meta 264 L47635-47637, L47650-47651; `standards/release-delta-winter27.md`). The Apex guide's newer notes agree: standard-object reasons are managed through the Metadata API, and recalculation "is supported for both custom and standard objects" (apex dev guide 264 L12880-12881, L12916-12920). Older text in the same corpus says the opposite: two Apex-guide notes say reasons and recalculation "are only available for custom objects" (L12613, L13057), and the AccountShare reference says that when creating a sharing entry "the only permitted value is Manual" (object_reference 264 L17340-17342, L17472-17474). The earlier flat claim "standard objects do not support custom Apex sharing reasons" is therefore CONTRADICTED at 68.0 and later, not settled. Safe reading: on a standard object use `RowCause = 'Manual'` (constant `Schema.OpportunityShare.rowCause.Manual`) unless the `SharingReason` is deployed at Metadata API 68.0 or later and a test insert with that row cause succeeds in the target org. UNVERIFIED (2026-10-20): which standard share objects accept a custom row cause on insert — the object reference still says Manual only.

### with sharing / without sharing / inherited sharing

Apex class sharing keywords control whether the running user's record access is enforced for SOQL and DML inside that class:

- `with sharing` — enforces the user's sharing rules. Use for most user-facing code.
- `without sharing` — bypasses sharing rules. Required in sharing recalculation batch classes because the class must query every record regardless of the running user's access.
- `inherited sharing` — adopts the sharing mode of the calling context. Use in service/utility classes that may be called from both `with sharing` and `without sharing` contexts.

A critical point: the guide's share-writing class `JobSharing` is `with sharing` (apex dev guide 264 L12758), and both it and the `JobApexSharing` trigger insert with `AccessLevel.USER_MODE` (L12788, L12929, L12978), so inserting Share records does not by itself call for `without sharing`; what it requires is permission: only users with "Modify All Data" can add or change Apex managed sharing (L12610, L12873-12874). The earlier "any Apex code that has access to the parent record's ID can insert a share row" is CONTRADICTED by that. The recalculation sample is `public without sharing class JobSharingRecalc` and queries with `AccessLevel.SYSTEM_MODE` (L13095, L13105-13106). Classes with no sharing declaration run `with sharing` at API 67.0 and later (L11930-11931).

### Sharing Recalculation

When programmatic sharing logic changes (e.g., territory assignments are restructured), stale share rows that were created with a custom row cause must be deleted and recreated. The platform provides a recalculation hook:

1. Create a class that implements `Database.Batchable<SObject>` (apex dev guide 264 L13078-13079); the same interface can be implemented more than once in an org (L13080-13081).
2. Implement `start`, `execute`, and `finish`; the guide's sample is `public without sharing`, not `global` (L13095) — UNVERIFIED (2026-10-20): that `global` is needed.
3. Declare the class `without sharing` so it can query all records, as the sample does.
4. In `execute`: delete existing share rows for the row cause, then insert fresh ones.
5. Associate the class with the custom object "on the custom object's detail page, in the Apex Sharing Recalculation related list" (L13053-13055); you can then run it from that page (L13059) or call `Database.executeBatch` (L13068-13069), and monitor it under Apex Jobs (L13073-13074). The earlier "register the class on the Apex Sharing Reason" is CONTRADICTED: the association is per object. UNVERIFIED (2026-10-20): that a Recalculate button appears on the reason.

The `start` method typically returns a `Database.QueryLocator` over the parent records; `execute` processes each batch of parent records, computes the correct users, and performs the share DML.

---

## Common Patterns

### Pattern 1: Insert Share Records from a Trigger

**When to use:** A trigger event (insert or update of a related record) determines which users gain access to a parent record. Example: an Account is shared with a partner when a Partner_Relationship__c record is created.

**How it works:**

1. Collect the `ParentId` values from the triggering records.
2. Query the Share table to determine which grants already exist (avoids duplicates).
3. Build a list of new Share sObjects for rows that do not yet exist.
4. Insert with `Database.insert(shareList, false, AccessLevel.USER_MODE)` to allow partial success (the guide's sample does exactly this, apex dev guide 264 L12975-12978). UNVERIFIED (2026-10-20): that duplicate rows produce `DUPLICATE_VALUE`; the guide says inserting a higher manual access level updates the original row (L13024-13025).
5. For removals, query the Share table by `RowCause` and `ParentId`, then delete.

**Why not the alternative:** Using declarative Sharing Rules would require a static criteria field. When sharing logic depends on related-object data (junction records, custom metadata), declarative rules cannot model the relationship.

### Pattern 2: Full Sharing Recalculation via Batch Apex

**When to use:** The underlying sharing logic has changed at bulk (e.g., territory reassignment affecting thousands of records) and all existing Apex-managed share rows must be rebuilt.

**How it works:**

1. Implement `Database.Batchable<SObject>` declared `without sharing`.
2. In `start`, return a `Database.QueryLocator` for all parent records: `Database.getQueryLocator('SELECT Id FROM CustomObject__c')`.
3. In `execute`, for the batch scope:
   a. Collect the parent IDs.
   b. Delete all existing `CustomObject__Share` rows where `RowCause = CustomObject__Share.rowCause.TerritoryAccess__c` and `ParentId IN :parentIds`.
   c. Compute the correct users by querying the related assignment records.
   d. Insert new share rows.
4. Associate the class with the object in the Apex Sharing Recalculation related list on the object's detail page (apex dev guide 264 L13053-13055).

**Why not the alternative:** Running recalculation in a trigger context hits DML row limits immediately for large datasets. A batch job stays within per-execute limits and can run asynchronously.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to share a record with a specific user based on a junction record | Apex trigger inserts `__Share` row with custom row cause | Declarative sharing rules cannot model junction-record logic |
| Sharing logic has changed org-wide and all shares need rebuilding | Batch Apex recalculation class registered on sharing reason | Volume exceeds synchronous DML limits; batch stays within per-execute limits |
| Standard object (Account, Opportunity) needs programmatic sharing | Insert share row with `RowCause = 'Manual'` | Creation of AccountShare rows permits only `Manual` (object_reference 264 L17472-17474); the Metadata API documents sharing reasons for standard objects at API 68.0 and later (api_meta 264 L47635-47637, L47650-47651) — see Core Concepts (UNVERIFIED (2026-10-20): which share objects accept one on insert) |
| A service method must read-then-share records in a mixed calling context | Declare service class `inherited sharing`; sharing class `without sharing` | Preserves caller's context for queries; bypasses for share DML only where needed |
| Share records must survive an owner change | Use a custom Apex sharing reason (not `Manual`) | `Manual` rows are removed when the owner changes (apex dev guide 264 L12606); Apex managed sharing is maintained (L12610-12611). UNVERIFIED (2026-10-20): behaviour under a manual recalculation run |
| Audit which records a user can access via Apex sharing | Query `__Share` filtered by `RowCause` | Row cause makes grants distinguishable from role-hierarchy or declarative grants |

---


## Recommended Workflow

1. Confirm the OWD is stricter than the access you will grant and that the running user has Modify All Data (Before Starting).
2. Choose the row cause: `Manual` for standard objects (a reason only at Metadata API 68.0+ after a test insert succeeds) and short-lived user grants, an Apex sharing reason for long-lived custom-object grants. Create the reason first (Classic UI for a custom object, a `SharingReason` component for a standard one).
3. Write the grant path (trigger or service) with `Database.insert(list, false, AccessLevel.USER_MODE)`, `Read` or `Edit` only, and a delete path for revoked grants. Use the examples in `references/examples.md`.
4. Write the recalculation class (`Database.Batchable`, `without sharing`, delete-then-insert for the row cause) and associate it with the object's Apex Sharing Recalculation related list.
5. Test: a grant at or below the OWD, a revoked grant, an owner change, and an OWD change in a sandbox; assert on the Share table by `RowCause`.
6. Run `python3 scripts/check_apex_managed_sharing.py --manifest-dir force-app` and walk the Review Checklist below.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] OWD for the object is Private or Public Read Only — if OWD is Public Read/Write, Apex sharing has no effect
- [ ] Apex sharing reason exists in the target org (Classic UI or Metadata API `SharingReason`) before code that references it is deployed
- [ ] Share inserts use `Database.insert(list, false)` and inspect `SaveResult` errors (the guide treats `FIELD_FILTER_VALIDATION_EXCEPTION` on `AccessLevel` as benign, apex dev guide 264 L12990-12999)
- [ ] Recalculation class is declared `without sharing` so all parent records are queryable
- [ ] Stale share rows are deleted before inserting fresh ones in recalculation (delete then insert)
- [ ] Recalculation class is associated with the object in the Apex Sharing Recalculation related list
- [ ] DML row count is within limits: 10,000 records processed by DML per transaction, synchronous or asynchronous (apex dev guide 264 L19759)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **An OWD change recalculates sharing** — Salesforce recalculates sharing for all records on the object and removes sharing that has become redundant, and Apex recalculation classes defined for a custom object also run (apex dev guide 264 L13049-13052, L13071-13072). UNVERIFIED (2026-10-20): that all Apex-managed share rows are deleted and that grants are permanently lost when no class is registered; register a recalculation class anyway.

2. **The recalculation sample is `without sharing`** — the guide's `JobSharingRecalc` is `public without sharing` and queries with `AccessLevel.SYSTEM_MODE` (apex dev guide 264 L13095, L13105-13106). UNVERIFIED (2026-10-20): that a `with sharing` class silently under-queries; the reasoning (the query is limited to records the running user can see) is sound but not stated for batch classes.

3. **Custom row causes must exist in the org before deployment** — `RowCause` is a restricted picklist on the share object (object_reference 264 L17456-17459 for AccountShare), and sharing reasons are a Metadata API type (`SharingReason`, api_meta 264 L47631). UNVERIFIED (2026-10-20): the exact `DmlException: FIELD_INTEGRITY_EXCEPTION` text. Include the sharing reason in the deployment package, or create it in the Classic UI for a custom object, first.

4. **`All` can't be granted, and the level must exceed the OWD** — valid values are `Edit`, `Read` and `All`, but "the All access level is an internal value and can't be granted"; the field "must be set to an access level that's higher than the organization's default" (apex dev guide 264 L12727-12732; AccountShare: object_reference 264 L17379). Using a level at or below the default raises `FIELD_FILTER_VALIDATION_EXCEPTION` mentioning `AccessLevel` (L12803-12804). UNVERIFIED (2026-10-20): the exact exception when `All` is inserted.

5. **Inserting a higher manual access level updates the existing row** — "a manual share access level is set to Read and you insert a new one set to Write. The original share rows are updated to Write" (apex dev guide 264 L13024-13025). UNVERIFIED (2026-10-20): the `(ParentId, UserOrGroupId, RowCause)` unique constraint and the `DUPLICATE_VALUE` error for an exact repeat. Query existing rows before inserting, or use `Database.insert(list, false)` and inspect `SaveResult` errors.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Share record DML snippet | Apex code to insert or delete share rows for a given object |
| Sharing recalculation batch class | Full `Database.Batchable` implementation for rebuilding Apex-managed shares |
| Apex sharing reason setup guidance | Steps to create the sharing reason metadata in Setup before code deployment |
| `check_apex_managed_sharing.py` report | Static analysis of Apex classes for sharing patterns and common errors |

---

## Related Skills

- `admin/sharing-and-visibility` — Use for declarative sharing rules, OWD decisions, role hierarchy design, and manual sharing; this skill handles programmatic extension of that foundation
- `apex/apex-security-patterns` — Use alongside this skill when designing the `with sharing` / `without sharing` / `inherited sharing` class hierarchy for the full feature
- `apex/async-apex` — Use when sharing recalculation volume requires batch or queueable patterns beyond what triggers can handle
