---
name: fsc-compliant-sharing-api
description: "Programmatic record access management in Financial Services Cloud using Compliant Data Sharing (CDS): inserting AccountParticipant/OpportunityParticipant records, working with ParticipantRole and ParticipantGroup objects, verifying sharing coverage, and understanding CDS recalculation behavior. NOT for admin setup of CDS via IndustriesSettings metadata, declarative sharing rules, or standard Apex managed sharing on non-FSC objects."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "how do I share an Account with a banker in FSC without writing to AccountShare directly"
  - "AccountParticipant insert not granting access to Opportunity in Financial Services Cloud"
  - "CDS share rows not appearing after inserting ParticipantRole record"
  - "how to bulk-assign relationship manager access to accounts using ParticipantGroup"
  - "compliant data sharing recalculation not picking up new participant records"
  - "ParticipantRoleId required field on AccountParticipant FSC apex"
tags:
  - compliant-data-sharing
  - fsc
  - account-participant
  - opportunity-participant
  - participant-role
  - participant-group
  - programmatic-sharing
inputs:
  - Confirmation that Compliant Data Sharing is enabled in IndustriesSettings for the target object (Account, Opportunity, or custom object)
  - User or group IDs that need access
  - ParticipantRole records defining the access level (e.g., Relationship Manager, Account Owner)
  - OWD setting for the target object (must NOT be Public Read/Write)
  - API version in use (API v50.0+ required for CDS participant objects)
outputs:
  - Apex code to insert or delete AccountParticipant/OpportunityParticipant records
  - Guidance on ParticipantGroup bulk assignment patterns
  - Verification queries to confirm CDS share row creation
  - Checker report identifying direct AccountShare/OpportunityShare DML that bypasses CDS
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# FSC Compliant Data Sharing API

This skill activates when a practitioner needs to grant or revoke record-level access programmatically in a Financial Services Cloud org that has Compliant Data Sharing (CDS) enabled. Instead of inserting Share rows directly, CDS requires inserting `AccountParticipant`, `OpportunityParticipant`, or equivalent participant records. The platform's CDS engine then writes the corresponding `AccountShare`/`OpportunityShare` rows automatically with `RowCause = 'CompliantDataSharing'`. Use this skill any time you are working with FSC participant objects, troubleshooting missing CDS grants, or bulk-assigning access via `ParticipantGroup`.

---

## Before Starting

Gather this context before working on anything in this domain:

- Verify that CDS is enabled for the target object. Open Setup > Industries Settings and confirm `enableCompliantDataSharingForAccount`, `enableCompliantDataSharingForOpportunity`, or the relevant custom-object flag is set to `true`. If CDS is not enabled, participant record inserts silently succeed but no share rows are written.
- Confirm the object's OWD is Private or Public Read Only. CDS share rows are never written when OWD is Public Read/Write because there is nothing to extend beyond universal access. This is the most common reason participant inserts appear to do nothing.
- Identify the `ParticipantRole` record IDs that map to the required access level. Every `AccountParticipant` and `OpportunityParticipant` insert requires a `ParticipantRoleId`; the role defines the access level (Read or Edit) granted by the platform share row.
- Confirm the running API version is 50.0 or later. The participant objects were introduced at API v50.0 and are not available in earlier API versions.
- For custom objects, confirm the org is on Summer '22 or later and that `enableCompliantDataSharingForCustomObjects` is enabled in addition to the per-object flag.

---

## Core Concepts

### CDS Participant Objects and Platform-Managed Share Rows

Compliant Data Sharing replaces direct Share object DML with an indirection layer. A developer inserts an `AccountParticipant` record linking a `UserId` (or `GroupId`) to an `AccountId` with a `ParticipantRoleId`. The CDS engine asynchronously evaluates this record and writes an `AccountShare` row with `RowCause = 'CompliantDataSharing'`. The developer never touches `AccountShare` directly.

Key participant object fields:

| Field | Required | Description |
|---|---|---|
| `AccountId` (or `OpportunityId`) | Yes | The record being shared |
| `UserId` | Yes (or GroupId) | The user or group receiving access |
| `ParticipantRoleId` | Yes | Determines the `AccessLevel` written to the share row |

The `ParticipantRole` object defines the label (e.g., "Relationship Manager") and the access level. Query `ParticipantRole` records to map role names to IDs before inserting participants.

### ParticipantGroup and ParticipantGroupMember for Bulk Access

Available from Spring '21+, `ParticipantGroup` is a named collection of users. `ParticipantGroupMember` joins a user to a group. An `AccountParticipant` can reference a `GroupId` (the `ParticipantGroup.Id`) instead of a `UserId`. When the group membership changes, CDS automatically adjusts the corresponding share rows — removing access for removed members and granting access for new members — without requiring any Apex intervention.

This pattern is preferred for branch or team-based access: create one `AccountParticipant` per group per account, then manage membership through `ParticipantGroupMember`. This dramatically reduces the number of participant records compared to per-user inserts when team membership changes frequently.

### CDS Recalculation Behavior

When CDS settings change or a sharing recalculation is triggered by an administrator, the platform clears all `RowCause = 'CompliantDataSharing'` share rows and replays them from the current set of participant records. Developers do not implement a recalculation class — the participant records themselves are the source of truth. This means stale participant records that were not cleaned up will re-create share rows after a recalculation. Always delete participant records when access should be revoked; deleting the share row directly has no lasting effect.

### OWD and CDS Interaction

CDS only writes share rows when the object's OWD is Private or Public Read Only. The check happens at the time the CDS engine processes the participant record. If OWD is later changed to Public Read/Write (e.g., during testing), existing participant records are retained but no share rows exist. If OWD is reverted to Private, the next recalculation replays all participants and share rows reappear. Developers should not rely on share-row existence as the sole signal of participant record health; query `AccountParticipant` directly to verify the grant is recorded.

---

## Common Patterns

### Pattern 1: Grant Account Access to a Single User

**When to use:** A relationship event (e.g., account assignment trigger, relationship record creation) requires one specific user to gain access to an FSC Account record.

**How it works:**

1. Query `ParticipantRole` to retrieve the `Id` for the required role name (e.g., `SELECT Id FROM ParticipantRole WHERE Name = 'Relationship Manager' LIMIT 1`).
2. Construct an `AccountParticipant` record with `AccountId`, `UserId`, and `ParticipantRoleId`.
3. Insert with `Database.insert(participantList, false)` to handle duplicate errors gracefully.
4. Do not insert an `AccountShare` record — the CDS engine handles share row creation.

**Why not the alternative:** Inserting directly into `AccountShare` with `RowCause = 'CompliantDataSharing'` throws a `DmlException` — the platform reserves this row cause for internal use by the CDS engine. Using `RowCause = 'Apex'` will succeed but creates a parallel, unmanaged share row that is invisible to CDS recalculation and bypasses the audit trail that CDS maintains.

### Pattern 2: Bulk Team Access via ParticipantGroup

**When to use:** A team or branch needs access to a large set of accounts. Membership of the team changes regularly.

**How it works:**

1. Query or create a `ParticipantGroup` record representing the team.
2. Maintain `ParticipantGroupMember` records for the current team members.
3. Insert one `AccountParticipant` per group-account pair using the `ParticipantGroup.Id` in the `UserId` field (the field is polymorphic and accepts group IDs).
4. When team membership changes, insert or delete `ParticipantGroupMember` records only — existing `AccountParticipant` records remain unchanged.

**Why not the alternative:** Per-user `AccountParticipant` inserts for a team of 20 users across 5,000 accounts produces 100,000 participant records. When two users leave the team, 10,000 participant records need deletion. With `ParticipantGroup`, only the `ParticipantGroupMember` records change regardless of how many accounts the group accesses.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Grant access to a single user on an FSC Account | Insert `AccountParticipant` with `ParticipantRoleId` | Platform writes the share row; audit trail and recalculation are maintained |
| Grant access to a team or branch | Insert `AccountParticipant` referencing a `ParticipantGroup` | Reduces participant volume; membership changes update share rows automatically |
| Revoke access for a user | Delete the `AccountParticipant` record | Deleting the participant triggers CDS engine to remove the share row; direct share deletion is overwritten on recalculation |
| Verify that CDS access was granted | Query `AccountShare WHERE RowCause = 'CompliantDataSharing'` | The share row proves CDS processed the participant record |
| CDS not enabled yet (planning phase) | Use standard Apex managed sharing temporarily with `RowCause = 'Manual'` | Avoids platform dependency on IndustriesSettings enablement; migrate to CDS when enabled |
| Custom object sharing under CDS | Enable `enableCompliantDataSharingForCustomObjects` in IndustriesSettings; insert the custom object's participant record | Custom object CDS requires Summer '22+ and an explicit enable flag in addition to per-object settings |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Verify prerequisites — confirm CDS is enabled for the target object in IndustriesSettings, OWD is not Public Read/Write, and the org API version is 50.0+.
2. Identify ParticipantRole IDs — query `SELECT Id, Name FROM ParticipantRole` to map role names to IDs required for participant record inserts.
3. Implement participant record DML — write Apex (or a data load) to insert `AccountParticipant` / `OpportunityParticipant` records with the correct `AccountId`/`OpportunityId`, `UserId` or group ID, and `ParticipantRoleId`. Use `Database.insert(list, false)` to handle duplicates gracefully.
4. Verify share row creation — query `AccountShare WHERE RowCause = 'CompliantDataSharing' AND AccountId IN :targetIds` to confirm the CDS engine processed the participant records. Allow a short asynchronous delay in sandboxes.
5. Test recalculation safety — confirm that revoking access is done by deleting participant records, not share rows. Delete a participant record and verify the share row is removed; check that it does not reappear after a sharing recalculation.
6. Run the checker script — execute `python3 scripts/check_fsc_compliant_sharing_api.py --manifest-dir <path>` to scan for direct share-table DML that bypasses CDS.
7. Review the checklist below before marking work complete.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] CDS is enabled in IndustriesSettings for every object targeted by participant record inserts
- [ ] OWD for each targeted object is Private or Public Read Only
- [ ] No Apex code inserts or deletes `AccountShare`/`OpportunityShare` rows with `RowCause = 'CompliantDataSharing'` or `RowCause = 'Apex'` as a CDS substitute
- [ ] Every `AccountParticipant` / `OpportunityParticipant` insert includes a valid `ParticipantRoleId`
- [ ] Access revocation deletes participant records, not share rows
- [ ] Bulk access patterns use `ParticipantGroup` + `ParticipantGroupMember` to avoid per-user participant explosion
- [ ] Tests query `AccountShare WHERE RowCause = 'CompliantDataSharing'` to verify grants rather than asserting on participant record count alone

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CDS share rows are never written when OWD is Public Read/Write** — When an org administrator sets Account OWD to Public Read/Write (often done for testing), all existing CDS share rows remain in place but no new ones are created for new participant inserts. When OWD is later reverted to Private, share rows are not automatically recreated until the next CDS recalculation. Developers must trigger a recalculation or wait for the nightly job to restore coverage.

2. **Deleting a share row does not revoke CDS access permanently** — If you delete an `AccountShare` row created by CDS, the CDS engine rewrites it during the next recalculation (triggered by an OWD change, org-level recalculation, or nightly processing). The only way to permanently revoke CDS access is to delete the corresponding `AccountParticipant` record.

3. **CDS is asynchronous — share rows may not exist immediately after participant insert** — In production the CDS engine processes participant records asynchronously. A test or post-insert query for `AccountShare` rows may return zero results immediately after an `AccountParticipant` insert, causing false negatives in tests. In Apex tests, use `Test.startTest()`/`Test.stopTest()` around the insert and verify in the assertion block. In integration tests, allow for processing delay.

4. **`enableCompliantDataSharingForAccount` alone is insufficient for custom objects** — Custom object CDS requires both `enableCompliantDataSharingForCustomObjects = true` AND the per-object flag. Enabling only the per-object flag on a custom object results in participant inserts that silently succeed but produce no share rows. Summer '22+ is also required.

5. **ParticipantGroup membership changes propagate automatically but not instantly** — Adding a `ParticipantGroupMember` record does not immediately update all `AccountShare` rows for accounts where the group is a participant. The CDS engine processes the membership change asynchronously, similar to standard participant inserts. Do not assert on share rows immediately after group membership DML in integration test scenarios.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| AccountParticipant insert snippet | Apex code to grant user or group access to an FSC Account via CDS |
| ParticipantGroup bulk assignment pattern | Pattern for managing team-level access via ParticipantGroup and ParticipantGroupMember |
| CDS verification query | SOQL to confirm share rows were written by the CDS engine |
| `check_fsc_compliant_sharing_api.py` report | Static analysis report identifying direct share-table DML that bypasses CDS |

---

## Related Skills

- apex-managed-sharing — Use for programmatic sharing on non-FSC objects or when CDS is not enabled; this skill extends apex-managed-sharing concepts into the CDS layer
- sharing-recalculation-performance — Use when CDS recalculation volume or frequency is causing performance issues in large FSC orgs
- health-cloud-consent-management — Use alongside this skill when consent-driven access patterns interact with CDS in Health Cloud orgs
