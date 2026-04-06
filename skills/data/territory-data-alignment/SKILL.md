---
name: territory-data-alignment
description: "Use this skill when querying, migrating, auditing, or maintaining account-to-territory and user-to-territory data in a Salesforce Enterprise Territory Management (ETM) org. Covers ObjectTerritory2Association DML via API, UserTerritory2Association data, Territory2ModelHistory audit queries, the Track Territory Assignment History feature (GA Spring '25), coverage analysis SOQL with AssociationCause filter, and data migration of territory associations between models. Trigger keywords: ObjectTerritory2Association, UserTerritory2Association, territory assignment data, territory coverage analysis, territory association bulk load, ETM data migration, track territory assignment history. NOT for ETM configuration or territory model setup — use territory-design-requirements for that. NOT for territory rule creation or activation — those are admin concerns."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "how do I query which accounts are assigned to which territories in ETM"
  - "I need to bulk load account-to-territory associations using the API or Data Loader"
  - "how do I audit territory assignment changes and who manually assigned an account to a territory"
  - "we are migrating to a new territory model and need to copy account assignments across"
  - "how do I find gaps in territory coverage — accounts that are not assigned to any territory"
  - "what is the difference between rule-driven and manual territory assignments in the data model"
  - "how do I use the Track Territory Assignment History feature released in Spring 25"
tags:
  - etm
  - territory-management-2
  - ObjectTerritory2Association
  - UserTerritory2Association
  - Territory2ModelHistory
  - territory-assignment
  - coverage-analysis
  - data-migration
  - audit
inputs:
  - target territory model ID or developer name
  - list of account IDs or a SOQL filter defining the account population to assess
  - whether the goal is read/audit, bulk insert, or migration between models
  - ETM feature flags enabled in the org (Track Territory Assignment History, Territory2Model state)
  - intended AssociationCause for new associations (Territory or Manual)
outputs:
  - SOQL queries for coverage analysis, gap detection, and AssociationCause audit
  - Data Loader or Bulk API 2.0 CSV structure for ObjectTerritory2Association inserts
  - step-by-step migration procedure for moving associations between territory models
  - audit query set using Territory2ModelHistory and UserTerritory2AssignmentHistory
  - coverage gap report template (accounts with no active territory association)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Territory Data Alignment

This skill activates when a practitioner needs to query, load, audit, or migrate account-to-territory and user-to-territory association data in an org using Enterprise Territory Management (ETM / Territory Management 2.0). It covers the data model objects, bulk DML patterns, coverage analysis SOQL, and the Track Territory Assignment History feature released as GA in Spring '25.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the org uses Territory Management 2.0 (ETM), not Legacy Territory Management.** The objects are entirely different. ETM uses `Territory2`, `ObjectTerritory2Association`, and `UserTerritory2Association`. Legacy TM uses `Territory`, `AccountTerritoryAssignment`, and `UserTerritory`. Mixing them in queries is a common source of confusion.
- **Know the target Territory2Model ID and its state.** Associations can only be inserted against an Active territory model. Attempting to write associations against a Planning or Archived model returns an error. Query `Territory2Model` to confirm `State = 'Active'` before any DML.
- **AssociationCause is set at insert time and cannot be updated.** An `ObjectTerritory2Association` row has `AssociationCause` of either `Territory` (rule-driven) or `Manual`. Manual associations are created via API; rule-driven associations are created by assignment rule runs. You cannot change a row's AssociationCause after creation — to switch from manual to rule-driven you must delete and let the rule engine re-create.
- **Track Territory Assignment History must be explicitly enabled in the org before history records are written.** If it is not enabled, `Territory2ModelHistory` will exist as an object but will have no rows for assignment changes. Confirm feature status before relying on audit queries.

---

## Core Concepts

### ObjectTerritory2Association — Account-to-Territory Data Model

`ObjectTerritory2Association` is the junction object that links a Salesforce record (typically an Account) to a `Territory2` node. Key properties:

- **Fields:** `ObjectId` (the Account ID or other supported object ID), `Territory2Id`, `AssociationCause` (`Territory` or `Manual`), `IsDeleted`, `SystemModstamp`.
- **Queryable and insertable via API.** You can SOQL query it directly and insert/delete rows using Bulk API 2.0, REST API, or Data Loader.
- **One account can appear in multiple rows** — once per territory it belongs to. Bulk deduplication checks are the caller's responsibility; the API does not prevent duplicate inserts.
- **Deleting a manual association via API immediately removes territory access for that account.** Rule-driven associations (`AssociationCause = 'Territory'`) should be removed by changing the rule or running a rule that excludes the account, not by direct delete, as the rule engine may re-create them on the next run.
- **Not all standard objects are supported** — `ObjectTerritory2Association` is used for Accounts by default. Opportunity-to-territory linkage is handled separately via Opportunity Territory Assignment (not through this object).

### UserTerritory2Association — User-to-Territory Data Model

`UserTerritory2Association` links a user to a `Territory2` node, granting them membership in that territory. Key properties:

- **Fields:** `UserId`, `Territory2Id`, `RoleInTerritory2` (`Salesperson` or `Manager`), `IsActive`.
- **Queryable and insertable via API.** Bulk loads of user-territory assignments are done via `UserTerritory2Association` inserts.
- **RoleInTerritory2 affects forecast visibility**, not record access. Both Salesperson and Manager members gain the same account record access within the territory; the role distinction only affects whether the user appears as a forecast manager in the territory forecast.
- **Deactivating a user does not automatically remove their UserTerritory2Association rows.** Stale rows for inactive users can inflate territory membership counts and affect forecast calculations. Coverage analysis should filter on `User.IsActive = true`.

### Territory2ModelHistory and Track Territory Assignment History (Spring '25 GA)

`Territory2ModelHistory` captures field-level changes to `Territory2Model` records (model state transitions: Planning → Active → Archived). It does not, by default, capture individual account assignment events.

The **Track Territory Assignment History** feature, released as GA in Spring '25, extends ETM audit to record who assigned or removed an account from a territory and when. When enabled:

- A separate history tracking mechanism records `ObjectTerritory2Association` create and delete events, including the `CreatedById` and timestamp.
- `UserTerritory2AssignmentHistory` (available when feature is on) similarly captures user assignment and removal events.
- **The feature must be enabled in Setup** under Territory Settings. It is not on by default. History records begin accumulating from the moment the feature is enabled — there is no backfill of prior assignments.

### Coverage Analysis with AssociationCause Filter

Coverage analysis means determining which accounts have territory coverage (at least one `ObjectTerritory2Association` row in an active model) and which do not. The `AssociationCause` filter is the key tool for distinguishing rule-driven from manual coverage:

- `AssociationCause = 'Territory'`: assigned by an ETM assignment rule run. Stable and repeatable.
- `AssociationCause = 'Manual'`: assigned directly via API or UI. May diverge from rule logic after a rule run if the manual association is not cleaned up.

Coverage gap detection requires a LEFT OUTER JOIN pattern: find Accounts where no `ObjectTerritory2Association` exists for the target territory model. In SOQL, this is achieved with a semi-join using `NOT IN` against the `ObjectId` set from `ObjectTerritory2Association` filtered by `Territory2.Territory2Model.State = 'Active'`.

---

## Common Patterns

### Bulk Insert of Manual Account-to-Territory Associations via Data Loader

**When to use:** You have a list of account-territory pairs (from a territory realignment exercise, a data migration, or a named account list) that need to be loaded into an Active ETM model without waiting for a rule run.

**How it works:**

1. Export current `Territory2` records with their IDs: `SELECT Id, Name, DeveloperName FROM Territory2 WHERE Territory2Model.State = 'Active'`.
2. Prepare a CSV with columns: `ObjectId` (Account ID), `Territory2Id`, `AssociationCause` (set to `Manual`).
3. Validate for duplicates against existing associations: `SELECT ObjectId, Territory2Id FROM ObjectTerritory2Association WHERE Territory2.Territory2Model.State = 'Active' AND AssociationCause = 'Manual'`.
4. Remove any rows from the CSV where the (ObjectId, Territory2Id) pair already exists.
5. Use Data Loader or Bulk API 2.0 to insert into `ObjectTerritory2Association`.
6. Verify: recount `ObjectTerritory2Association` rows per territory and spot-check five account-territory pairs in the UI.

**Why not use the UI for bulk loads:** The Territory Management UI supports individual account assignments but has no bulk import. API is the only path for loads above a few dozen records.

### Coverage Gap Analysis SOQL

**When to use:** Determining which accounts have no active territory assignment — either as a pre-migration audit or a recurring operational health check.

**How it works:**

```soql
-- Step 1: Get all Account IDs that have at least one active territory association
SELECT ObjectId
FROM ObjectTerritory2Association
WHERE Territory2.Territory2Model.State = 'Active'

-- Step 2: Find Accounts NOT in that set
SELECT Id, Name, BillingState, AnnualRevenue
FROM Account
WHERE IsDeleted = false
  AND Id NOT IN (
    SELECT ObjectId
    FROM ObjectTerritory2Association
    WHERE Territory2.Territory2Model.State = 'Active'
  )
ORDER BY AnnualRevenue DESC NULLS LAST
```

For large orgs, run this with the Bulk API 2.0 query mode or Data Loader to avoid governor limit timeouts. The result set is the coverage gap list — accounts requiring either manual association or assignment rule adjustment.

**AssociationCause breakdown query:**

```soql
SELECT Territory2Id, Territory2.Name, AssociationCause, COUNT(Id) total
FROM ObjectTerritory2Association
WHERE Territory2.Territory2Model.State = 'Active'
GROUP BY Territory2Id, Territory2.Name, AssociationCause
ORDER BY Territory2.Name ASC
```

This shows how many accounts per territory are rule-driven vs. manually assigned — useful for auditing territory health before a rule rerun (which will re-evaluate rule-driven rows but leave manual rows in place).

### Territory Model Migration — Copying Associations

**When to use:** Moving from one territory model to another (e.g., annual realignment, ETM model version bump). You need to carry manual associations from the old model to the new one; rule-driven associations will be re-created by the rule engine on the new model.

**How it works:**

1. Query manual associations from the old model: `SELECT ObjectId, Territory2Id FROM ObjectTerritory2Association WHERE Territory2.Territory2Model.DeveloperName = 'OldModel' AND AssociationCause = 'Manual'`.
2. Map old `Territory2Id` values to new `Territory2Id` values using the territory `DeveloperName` as the stable key (IDs differ between models).
3. Build the new CSV using new Territory2Ids and `AssociationCause = 'Manual'`.
4. Activate the new model (only one model can be Active at a time).
5. Bulk insert into `ObjectTerritory2Association` against the now-Active new model.
6. Run assignment rules on the new model to populate rule-driven associations.
7. Verify gap analysis: compare account count in new model vs. old model.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to assign specific accounts to territories outside rule logic | Insert `ObjectTerritory2Association` rows with `AssociationCause = 'Manual'` via Bulk API 2.0 | Rule engine will not overwrite manual rows; manual inserts are immediately effective |
| Need to remove a rule-driven association | Modify or deactivate the assignment rule, then rerun rules | Direct delete of rule-driven rows will be re-created by the next rule run |
| Coverage gap analysis for large orgs (>100K accounts) | Use Bulk API 2.0 query for the NOT IN subquery — standard SOQL will hit governor limits | Large subqueries in standard SOQL context hit 50K row limits; Bulk API avoids this |
| Audit who assigned an account to a territory | Enable Track Territory Assignment History in Setup; query history records | Feature must be on before events are recorded — no retroactive data |
| Migrating territory associations to a new model | Map via `Territory2.DeveloperName`, export manual rows only, bulk insert into new model | Rule-driven rows should be re-created by running rules on the new model; only manual rows require migration |
| User-territory membership is stale after rep turnover | Bulk delete `UserTerritory2Association` rows for inactive users; bulk insert for new reps | Deactivating a user in Salesforce does not remove their territory memberships |
| Determining if an account's territory is rule-assigned or manually assigned | Filter `ObjectTerritory2Association` on `AssociationCause` | The field is immutable after insert — it accurately reflects the assignment origin |

---

## Recommended Workflow

Step-by-step instructions for territory data alignment work:

1. **Confirm the active territory model and feature state** — Query `Territory2Model` to identify the Active model ID. Confirm whether Track Territory Assignment History is enabled in Setup. Confirm the target object type (Account is standard; other objects require custom ETM configuration).
2. **Run a coverage baseline query** — Use the coverage gap analysis SOQL pattern to determine how many accounts have no active territory association. Also run the `AssociationCause` breakdown query to see the ratio of rule-driven to manual assignments per territory. Document these numbers as the before-state.
3. **Identify the data operation needed** — Determine whether the goal is: (a) bulk insert of new manual associations, (b) cleanup of stale manual associations, (c) migration of associations to a new model, or (d) audit/reporting only. Select the appropriate pattern from Common Patterns.
4. **Prepare and validate the data payload** — For inserts: build the CSV with `ObjectId`, `Territory2Id`, `AssociationCause`. Deduplicate against existing rows. For deletes: query existing rows to get `Id` values — you delete by `ObjectTerritory2Association.Id`. For migrations: resolve `Territory2Id` mappings using `DeveloperName` as the stable key.
5. **Execute the data operation via Bulk API 2.0 or Data Loader** — For inserts/deletes exceeding a few hundred rows, use Bulk API 2.0 in parallel mode for throughput. Monitor job status via `SELECT Id, State, NumberRecordsProcessed, NumberRecordsFailed FROM AsyncApexJob` or the Bulk API job status endpoint.
6. **Run post-operation verification** — Re-run the coverage baseline queries and compare account counts per territory before and after. Spot-check five or more specific accounts in the Territory Management UI. If Track Territory Assignment History is enabled, verify that history records were written for the operation.
7. **Document deviations and manual association rationale** — Record why any accounts were manually assigned rather than rule-driven. Manual associations that survive a rule rerun are invisible to the rule logic — they can create silent coverage drift over time. Document the intent so future rule runs or realignments can account for them.

---

## Review Checklist

Run through these before marking territory data alignment work complete:

- [ ] Active territory model confirmed; no attempt made to write to Planning or Archived models
- [ ] `AssociationCause` is correctly set for all inserted rows (`Manual` for API-driven inserts)
- [ ] Duplicate check completed before bulk insert (no duplicate ObjectId + Territory2Id pairs)
- [ ] Coverage gap analysis run before and after the operation; gap count reduced as expected
- [ ] `AssociationCause` breakdown query shows expected ratio of rule vs. manual assignments
- [ ] For model migrations: `Territory2Id` mapping validated using `DeveloperName` (not ID) as the stable key
- [ ] Stale `UserTerritory2Association` rows for inactive users identified and addressed
- [ ] If Track Territory Assignment History is enabled, audit records verified for key association events
- [ ] Bulk API 2.0 job completed with zero or acceptable failed records; failed record log reviewed
- [ ] Manual association rationale documented for any account forced outside rule-driven logic

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **AssociationCause is immutable — rule reruns do not remove manual associations** — When you run or rerun ETM assignment rules, the rule engine creates and deletes rows with `AssociationCause = 'Territory'`. Rows with `AssociationCause = 'Manual'` are never touched by rule runs. This means a manually assigned account will remain in a territory even if its account fields no longer match the rule criteria. Over time, manual associations silently diverge from rule logic. Audit manual associations regularly and document the rationale for each.

2. **Direct delete of rule-driven rows is temporary** — If you delete an `ObjectTerritory2Association` row where `AssociationCause = 'Territory'`, the next assignment rule run will re-create it if the account still matches the territory's criteria. You must modify the rule or exclude the account from rule criteria to permanently remove a rule-driven association.

3. **Only one Active territory model at a time — transition is not instantaneous** — Activating a new territory model and archiving the old one is a sequential process. During the transition window, account record access through territories may be temporarily inconsistent. Plan model migrations during low-traffic windows, and validate that the new model is fully activated and rules have run before communicating go-live to users.

4. **Track Territory Assignment History does not backfill** — Enabling the feature after the fact gives you a clean history log starting from the enablement date. All prior territory assignment events (including the initial bulk load) are not captured. If you need a historical snapshot, export `ObjectTerritory2Association` before enabling and store it externally.

5. **SOQL governor limits apply to coverage gap NOT IN subqueries** — A query like `SELECT Id FROM Account WHERE Id NOT IN (SELECT ObjectId FROM ObjectTerritory2Association ...)` is subject to the 50,000-row subquery row limit in synchronous SOQL. For orgs with more than 50K account-territory associations, this query will fail or return incomplete results in a synchronous context. Use Bulk API 2.0 query or split the analysis into batches.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Coverage gap report | List of Account IDs and basic fields with no active `ObjectTerritory2Association` row in the active model |
| AssociationCause breakdown table | Per-territory count of rule-driven vs. manual associations, used to assess territory health |
| Bulk insert CSV | `ObjectId`, `Territory2Id`, `AssociationCause` CSV ready for Data Loader or Bulk API 2.0 insert into `ObjectTerritory2Association` |
| Territory model migration mapping | Old `Territory2Id` to new `Territory2Id` mapping table keyed on `DeveloperName` |
| UserTerritory2Association audit | List of `UserTerritory2Association` rows for inactive users requiring cleanup |
| Audit query set | SOQL queries leveraging `Territory2ModelHistory` and Track Territory Assignment History records |

---

## Related Skills

- admin/territory-design-requirements — use before data alignment work to ensure the territory hierarchy and assignment rule criteria are correct; data alignment should follow design, not precede it
- apex/territory-api-and-assignment — use for Apex-driven territory assignment logic, trigger-based association management, and programmatic rule invocation
- data/opportunity-pipeline-migration — use when territory alignment changes co-occur with opportunity data migration (territory changes affect opportunity territory assignment)
