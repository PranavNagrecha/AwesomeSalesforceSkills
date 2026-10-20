---
name: field-history-tracking
description: "Use when enabling, configuring, or querying Salesforce field history tracking to audit changes to field values over time. Covers enabling tracking on objects and fields, the 20-field-per-object limit, 18-month data retention, querying standard History sObjects (AccountHistory, OpportunityFieldHistory, custom __History), and troubleshooting missing records. NOT for Shield Field Audit Trail, FieldHistoryArchive, or keeping history past 18 months — use security/field-audit-trail. NOT for CreatedDate, LastModifiedDate, or SystemModstamp behavior — use admin/system-field-behavior-and-audit."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "how do I see who changed a field value in Salesforce"
  - "audit trail for field changes on an account or opportunity"
  - "field history is not showing changes — why are records missing"
  - "how do I query the history of a custom object field"
  - "set up field history tracking on a standard or custom object"
  - "how many fields can I track per object in Salesforce"
  - "join a history object to its parent record in one SOQL query"
  - "pull a record and its field history together with a relationship query"
tags:
  - field-history-tracking
  - audit
  - data-governance
  - soql
  - metadata
  - compliance
inputs:
  - "Name of the object(s) requiring field history (standard or custom)"
  - "List of fields to track on each object"
  - "Retention requirement in months (standard tracking covers up to 18 months in the UI and 24 via the API)"
  - "Query scope: specific record, user, date range, or field"
outputs:
  - "Field History Tracking enablement decisions per object and field"
  - "SOQL query patterns for XxxHistory and custom __History objects"
  - "Troubleshooting diagnosis for missing history records"
  - "Decision guidance on when to extend to Shield Field Audit Trail"
  - "Configuration checklist for enablement and review"
dependencies: []
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Field History Tracking

This skill activates when a practitioner needs to enable Salesforce Field History Tracking on standard or custom objects, query history sObjects to audit field value changes, or troubleshoot cases where expected history records are absent. It does NOT cover Shield Field Audit Trail (use `field-audit-trail`) or Event Monitoring (use security skills).

---

## Before Starting

Gather this context before working on anything in this domain:

- **Object and field list:** Identify which objects and which specific fields require history. Without Field Audit Trail you can track "up to 20 standard and custom fields per object" (secguide 262 L4795-4796, L4838); on accounts the 20 is shared by business and person accounts together (secguide 262 L4774-4775), and events and tasks allow only six (secguide 262 L4700). With Field Audit Trail the Security Guide says up to 200 fields per object (secguide 262 L4836), while the scratch-org `FieldAuditTrail` feature description says a total of 60 (sfdx_dev 264 L4606-4607); plan to the lower figure until you confirm it in the target org.
- **Retention window:** With Field Audit Trail off, Salesforce retains field history "for up to 18 months, and up to 24 months via the API" (secguide 262 L4553-4554, L4632-4633); history that is 18-24 months old is reachable with Data Loader or `queryAll()` (secguide 262 L4655). With Field Audit Trail on it is retained until you delete it (secguide 262 L4554-4555). If the requirement exceeds 24 months, this skill will not solve it alone — Field Audit Trail (part of Salesforce Shield, secguide 262 L120-121; "contact your Salesforce representative" to enable it, L4830) or custom logging is required.
- **Field eligibility:** You can't track formula, roll-up summary or auto-number fields, Created By and Last Modified By, fields with the AI Prediction checkbox, the Expected Revenue field on opportunities, or the Master Solution Title and Master Solution Details fields (secguide 262 L4797-4803). Multi-select picklist and large text fields are trackable only with "Track changes only" (secguide 262 L4793-4794): changes to fields over 255 characters are recorded as edited, without old and new values (secguide 262 L4656); time fields are not tracked (secguide 262 L4657). Field Audit Trail archives exclude long text and multi-select fields entirely (secguide 262 L4890-4891). Confirm field type before committing to a tracking strategy.
- **Deleted records:** "If you delete a record in your production data, the delete cascades to the related history tracking records, but Salesforce doesn't delete the history copied into the FieldHistoryArchive big object" (secguide 262 L4895-4897). UNVERIFIED (2026-10-20): whether Recycle Bin records keep their history rows until permanent deletion is not stated in the corpus.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| How long must field changes be retrievable, in months? | Gotcha 7 and Concept 3: 18 months in the UI, 24 via the API, without Field Audit Trail | Whether standard tracking is enough or Field Audit Trail or custom logging is needed |
| Which exact fields, and are any formula, roll-up, auto-number, long text or multi-select? | Gotcha 4: ineligible types; long text and multi-select record "edited" only | A field list that will actually produce old and new values |
| Is the object Account, Event or Task? | Account shares 20 between business and person accounts; Event and Task allow six (secguide 262 L4774-4775, L4700) | The real per-object ceiling |
| Do consumers need the value a field had at record creation? | Gotcha 2: the `"created"` row is UNVERIFIED and the guide's insert example records insert-time values (secguide 262 L4690-4696) | A decision to add a create-time logger |
| Do changes arrive through automation or an integration user? | Mode 3: field history honors the current user's permissions and skips system-context changes (secguide 262 L4687-4689) | The run-as user whose edit permission decides whether a change is tracked |
| Which sObject will queries target, and does the code use the right parent field? | Concept 2, Gotcha 5: `OpportunityFieldHistory` versus `OpportunityHistory`; `AccountId` versus `ParentId` | Correct object and relationship names before any SOQL ships |
| Is anyone assuming history consumes data storage or can be edited? | History data does not count against storage (secguide 262 L4555-4556); deletion is a deliberate API-enabled act | Stops a wrong storage-reclamation plan and a wrong immutability claim |

A proper configuration adds a documented retention decision, a field list matched to what the platform can record, and a tested query for every consumer, instead of ticking boxes and discovering the gaps in an audit.

---

## Core Concepts

### Concept 1: Enabling Field History Tracking

Field History Tracking is enabled in two steps. First, the feature must be activated on the object. The Security Guide's documented path is Setup > Quick Find "Field History Tracking" > View for the object > Enable {Object} History (secguide 262 L4778-4782). The Object Manager > Fields & Relationships > Set History Tracking path used below is UNVERIFIED (2026-10-20): that click path is not in the corpus. Enabling history on the object does not automatically track any fields — each field must be individually checked.

Second, within the object's history tracking settings, select up to 20 fields to track (secguide 262 L4795-4796). Salesforce stores any change to a tracked field as a new row in the object's History sObject (e.g., `AccountHistory` for Account, `MyObject__History` for a custom object `MyObject__c`). The History related list on page layouts surfaces these rows to end users without any additional code.

The History related list is configured separately: "customize your page layouts to include the object's history related list" (secguide 262 L4786-4787). It must be added to the layout for users to see it inline on a record. Without the related list, data is still stored and queryable via SOQL — it is just not visible on the page.

### Concept 2: History sObjects and Query Structure

Every object with Field History Tracking enabled has a corresponding History sObject. Standard objects use named sObjects: `AccountHistory`, `ContactHistory`, `LeadHistory`, `CaseHistory`, etc. Custom objects use the pattern `ObjectApiName__History` (e.g., `Project__History` for `Project__c`).

**Naming exception — Opportunity:** the field-history sObject for Opportunity is **`OpportunityFieldHistory`** ("the history of changes to the values in the fields of an opportunity", object_reference 264 L195717), not `OpportunityHistory`. The object named `OpportunityHistory` is a *different* object — "the stage history of an opportunity" (object_reference 264 L195801) with `Amount`, `CloseDate`, `ExpectedRevenue`, `ForecastCategory`, `Probability`, `StageName` and `PrevAmount`/`PrevCloseDate` columns (L195816-195916) and no `Field`/`OldValue`/`NewValue` columns. A field-history query must target `OpportunityFieldHistory`. (A handful of other standard objects follow the same `<Object>FieldHistory` pattern — always confirm the exact sObject name in the object reference.)

Key fields on all History sObjects:

| Field | Description |
|---|---|
| `Id` | Unique row identifier |
| `ParentId` | Id of the record that was changed (foreign key to the parent object). On standard-object history sObjects the guide lists the field as `StandardObjectNameId` — e.g., `AccountId` on `AccountHistory`, `OpportunityId` on `OpportunityFieldHistory` — rather than the literal `ParentId` (object_reference 264 L4628, L195749-195781). Custom `__History` objects use `ParentId`; UNVERIFIED (2026-10-20): the object reference lists no field table for `__History` objects (L4086 is only a naming row), so `ParentId` and the `Parent` relationship name there are unverified. |
| `Field` | Name of the field that changed (e.g., `"AnnualRevenue"`, `"StageName"`). Typed as a restricted picklist (object_reference 264 L4640-4643). |
| `DataType` | Data type of the field that changed (picklist). Present on standard-object history records (object_reference 264 L4634-4637); useful when interpreting `OldValue`/`NewValue`, which are `anyType` (L4658). |
| `OldValue` | Value before the change (`anyType`). Null if the record was created (new record) or if the field was previously blank. |
| `NewValue` | Value after the change. |
| `CreatedById` | Id of the user who made the change |
| `CreatedDate` | Timestamp when the change occurred |

UNVERIFIED (2026-10-20): `CreatedById` and `CreatedDate` are not in the Object Reference field tables for `StandardObjectNameHistory` (object_reference 264 L4628-4660) or `OpportunityFieldHistory` (L195716-195800); the Security Guide mentions only "Created Date and ID fields" on the History related list (secguide 262 L4682). Confirm with `describeSObject` before shipping queries that select them.

For a new record creation event, `Field` is set to `"created"`, `OldValue` is null, and `NewValue` is null. UNVERIFIED (2026-10-20): the `"created"` row is not described anywhere in the corpus (grep of object_reference 264 and secguide 262 finds no such row), and the guide's own insert example contradicts "no field-level rows at creation": a user inserts a record with Postal Code 12345, a trigger changes it to 94619, and the tracked history reads "No value through 12345" then "12345 through 94619" (secguide 262 L4690-4696). For a field change, `Field` contains the tracked field name.

Example SOQL — all history for a single Account record:

```soql
SELECT Field, OldValue, NewValue, CreatedById, CreatedDate
FROM AccountHistory
WHERE AccountId = '001XXXXXXXXXXXX'
ORDER BY CreatedDate DESC
LIMIT 200
```

Example SOQL — who changed StageName across all Opportunities in the last 30 days (note the `OpportunityFieldHistory` sObject — `OpportunityHistory` would fail here because it has no `Field` column):

```soql
SELECT OpportunityId, OldValue, NewValue, CreatedById, CreatedDate
FROM OpportunityFieldHistory
WHERE Field = 'StageName'
  AND CreatedDate = LAST_N_DAYS:30
ORDER BY CreatedDate DESC
```

Example SOQL — history for a custom object field:

```soql
SELECT Field, OldValue, NewValue, CreatedById, CreatedDate
FROM MyObject__History
WHERE ParentId = 'a01XXXXXXXXXXXX'
  AND Field = 'Status__c'
ORDER BY CreatedDate ASC
```

History sObjects are available in Salesforce Reports via the standard `[Object] History` report type when history is enabled on the object. UNVERIFIED (2026-10-20): the Security Guide documents field history reports only for "custom objects that are defined as detail objects" (secguide 262 L4644-4645); the standard report type name is not in the corpus.

**Relationship queries against history objects.** A history object is the child of its tracked parent, so SOQL can traverse the relationship in either direction and avoid a second round-trip to fetch parent fields.

- *Child-to-parent* — from the history object, reach up to parent fields with the `Parent` relationship. This returns the change plus context about the record it belongs to in one query:

  ```soql
  SELECT OldValue, NewValue, Parent.Id, Parent.Name, Parent.CustomField__c
  FROM MyObject__History
  ```

- *Parent-to-child* — from the parent object, nest the history rows as a subquery, so each record carries its own change log inline:

  ```soql
  SELECT Name, CustomField__c, (SELECT OldValue, NewValue FROM MyObject__History)
  FROM MyObject__c
  ```

The child-to-parent relationship name depends on the object type: custom `__History` objects use `Parent` (matching their `ParentId` field), while standard history objects use the object name — `SELECT Account.Name FROM AccountHistory` (matching the `AccountId` field). Writing `Parent.Name` against a standard history object fails to compile; see Gotcha 5.

> **Scope note.** These relationship-query forms work only on standard and custom History objects. Shield's `FieldHistoryArchive` enforces a restricted SOQL grammar and does *not* accept them — see Gotcha 6 and the `field-audit-trail` skill.

### Concept 3: 18-Month Retention and Data Loss

Without Field Audit Trail, Salesforce "retains field history data for up to 18 months, and up to 24 months via the API" (secguide 262 L4553-4554). So a change that is 19 months old can still be returned by an API query (Data Loader or `queryAll()`, secguide 262 L4655) even though the History related list no longer shows it; past 24 months it is gone. An earlier version of this skill said everything older than 18 months is purged; the guide's two-tier wording replaces that. With Field Audit Trail on, Salesforce retains field history "until you delete it" (secguide 262 L4554-4555).

Organizations that require history beyond 18 months have two documented options:

1. **Shield Field Audit Trail** — Part of Salesforce Shield (secguide 262 L120-121). Archived records live in the `FieldHistoryArchive` big object (object_reference 264 L137979-137980) and are kept until you delete them; the archive default is 18 months in production and one month in sandboxes (secguide 262 L4881-4882), and `HistoryRetentionPolicy.archiveAfterMonths` takes 1 to 18 (api_meta 264 L46329-46332). An earlier version said "up to 10 years"; UNVERIFIED (2026-10-20): no corpus file states a 10-year figure, and the guide's wording is "until you delete it". See the `security/field-audit-trail` skill.
2. **Custom logging via Apex or Flow** — Capture field changes into a custom object at the time of change using a before-update trigger or Flow. This custom log is not subject to the 18-month purge and can be retained indefinitely. The tradeoff is implementation and maintenance overhead, and it does not backfill historical changes that occurred before the custom logger was deployed.

---

## Mode 1: Enabling Field History Tracking

**When to use:** An object has no history tracking configured and audit requirements call for capturing future field changes.

**Steps:**

1. Go to Setup > Object Manager.
2. Select the target object (e.g., Account, or a custom object).
3. Click **Fields & Relationships**, then **Set History Tracking** (for standard objects) or **Fields & Relationships > Set History Tracking** (for custom objects).
4. Check the **Enable [Object] History** checkbox at the top.
5. Select up to 20 fields to track (secguide 262 L4795-4796); use "Track old and new values" for ordinary fields and "Track changes only" for multi-select picklist and large text fields (L4789-4794).
6. Click **Save**.
7. Add the **[Object] History** related list to the relevant page layouts in Setup > Page Layouts.

History records begin accumulating from the moment tracking is enabled. No retroactive history is created for changes that occurred before enablement (secguide 262 L4653-4654).

---

## Mode 2: Auditing Existing Field History Configuration

**When to use:** Reviewing which objects and fields currently have history tracking enabled, or confirming configuration correctness before a compliance review.

Steps to audit without code:

1. Navigate to Setup > Object Manager > [Object] > Fields & Relationships > Set History Tracking. The checkboxes show which fields are currently tracked.
2. The Metadata API returns history configuration in the `CustomObject` type under `enableHistory` (boolean; also standard objects from API 29.0, including person account history on Account, api_meta 264 L44320-44323) and in `CustomField` under `trackHistory` (boolean; standard-object fields only for picklist and lookup fields from API 30.0, and not for external objects, api_meta 264 L45893-45898).

Using the Metadata API to audit history configuration programmatically:

```bash
# Retrieve custom object metadata including history settings
sf project retrieve start --metadata "CustomObject:MyObject__c" --target-org my-org
```

In the retrieved XML, confirm `<enableHistory>true</enableHistory>` on the object and `<trackHistory>true</trackHistory>` on each tracked field.

---

## Mode 3: Troubleshooting Missing History Records

**When to use:** A practitioner reports that a known field change is not appearing in the history related list or SOQL results.

Diagnosis checklist:

| Symptom | Likely Cause | Resolution |
|---|---|---|
| No history rows at all for an object | History tracking not enabled on the object | Enable tracking in Object Manager |
| Specific field change missing | Field not selected in history tracking settings | Enable the specific field (check 20-field limit) |
| History existed but is now gone | Change is past the 18-month (UI) or 24-month (API) window | Data is purged; Field Audit Trail or a custom log is the only way to keep future history (secguide 262 L4553-4555) |
| History missing for a deleted record | The delete cascades to the history rows (secguide 262 L4895-4896) | History is deleted with the record; only `FieldHistoryArchive` copies survive |
| Formula field changes not tracked | Formula fields are not eligible for tracking | Use a regular field or custom log pattern |
| Changes by automation or an integration user not visible | "Field history honors the permissions of the current user and doesn't record changes that occur in the system context" if that user cannot edit the field (secguide 262 L4687-4689) | Grant the running user edit access to the field, or log the change yourself |
| Change just made is not listed yet | "It can take up to a few minutes for changes to appear in history" (activity history, secguide 262 L4699) | Wait and re-query before diagnosing further |
| New record creation not showing field values | UNVERIFIED (2026-10-20): the "created" row and its null values are not described in the corpus | Do not rely on creation-time values being in history; log them yourself |

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Track field changes for 18 months or less | Standard Field History Tracking | Built-in; "up to 18 months" in the UI and 24 via the API (secguide 262 L4553-4554) |
| Track field changes for more than 24 months | Field Audit Trail (`security/field-audit-trail` skill) or custom logging | Standard retention ends at 18/24 months; Field Audit Trail keeps archives until you delete them |
| Need more than 20 tracked fields on one object | Field Audit Trail (200 per object per secguide 262 L4836; 60 per sfdx_dev 264 L4606-4607) or custom logging | Without Field Audit Trail the cap is 20 (secguide 262 L4838) |
| Formula, roll-up or auto-number field must be audited | Custom logging via Apex trigger or Flow | These field types cannot be tracked (secguide 262 L4797-4799) |
| A long text or multi-select field's old and new values must be audited | Custom logging via Apex trigger or Flow | Standard tracking records only that it was edited (secguide 262 L4656) |
| Custom object field history in SOQL | Query `ObjectApiName__History` | Platform auto-generates this sObject when history is enabled |
| Pull a record plus its field-change log in one round-trip | Parent-to-child subquery `SELECT ..., (SELECT OldValue, NewValue FROM Object__History) FROM Object__c` | History is a child of its parent; a subquery avoids a second query and keeps rows grouped by record |
| Report the change alongside parent context (owner, name) | Child-to-parent traversal to parent fields — `Parent.*` on custom `__History`, the object name (`Account.*`) on standard history | One query returns `OldValue`/`NewValue` plus parent fields; no separate lookup needed |
| Build a report of field changes | Use a field history report (custom detail objects documented at secguide 262 L4644-4645) | UNVERIFIED (2026-10-20): the `[Object] History` report type name is not in the corpus |
| Audit field changes after record deletion | Consider Shield FAT or custom logging pre-deletion | History is deleted along with the parent record |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Answer the Questions table above: retention in months, exact field list and types, and whether the object is Account, Event or Task.
2. Pick the mode: enable (Mode 1), audit (Mode 2) or troubleshoot (Mode 3), and read the matching gotchas in `references/gotchas.md`.
3. For Mode 1 and Mode 2, retrieve the object and field metadata and run `python3 scripts/check_field_history_tracking.py --manifest-dir <source root>`; fix ERROR findings, review WARN findings.
4. Write each query against the right sObject (`OpportunityFieldHistory`, `AccountHistory` with `AccountId`, `Custom__History`) and test it once with a real change.
5. Record the retention decision (18/24 months, Field Audit Trail or custom log) in `templates/field-history-tracking-template.md`.

---

## Review Checklist

Run through these before marking field history tracking work complete:

- [ ] History tracking enabled on the object (not just individual fields)
- [ ] Required fields selected — count does not exceed 20 per object
- [ ] Ineligible field types (formula, roll-up, auto-number) excluded; long text and multi-select set to "Track changes only" or logged separately
- [ ] History related list added to the relevant page layouts
- [ ] SOQL query validated against the correct History sObject name (standard or `__History`)
- [ ] 18-month (UI) and 24-month (API) retention communicated to stakeholders; escalation path to Field Audit Trail documented if longer retention is anticipated
- [ ] Deleted record behavior communicated to stakeholders
- [ ] Tracking confirmed active by making a test change and verifying a history row appears

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Checkbox fields store `true`/`false`, not the field label** (UNVERIFIED (2026-10-20): the corpus does not describe how checkbox values are stored in `OldValue`/`NewValue`) — When a checkbox field is tracked, `OldValue` and `NewValue` contain the literal strings `"true"` or `"false"`, not any display label. SOQL comparisons must use these string values. Reports and list views typically display these correctly, but programmatic comparisons that check for `"Yes"` or `"Checked"` will fail silently.

2. **New record creation sets `OldValue` and `NewValue` to null** (UNVERIFIED (2026-10-20): see Concept 2, the `"created"` row is not in the corpus) — When a record is first created, a history row is written with `Field = "created"`, `OldValue = null`, and `NewValue = null`. Do not assume creation-time values are absent either: the guide's own insert example contradicts "no field-level rows at creation": a user inserts a record with Postal Code 12345, a trigger changes it to 94619, and the tracked history reads "No value through 12345" then "12345 through 94619" (secguide 262 L4690-4696); test in the target org. If the requirement includes capturing initial values at creation, a custom trigger or Flow must store these separately at insert time.

3. **History tracking is not retroactive** (secguide 262 L4653-4654) — Enabling history on a field records changes from that point forward only. No history rows are created for changes that occurred before enablement. Stakeholders who expect to see historical changes from before the feature was turned on will be disappointed; communicate this limitation clearly before enablement.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field history enablement decisions | Per-object table of enabled fields, tracking status, and field type eligibility |
| SOQL query set | Parameterized queries for AccountHistory, OpportunityFieldHistory, custom `__History` objects |
| Troubleshooting diagnosis | Root cause analysis for missing history records |
| Retention advisory | Documentation of the 18-month (UI) and 24-month (API) limits and recommended escalation to Field Audit Trail if needed |

---

## Related Skills

- `security/field-audit-trail` — Field Audit Trail for retention beyond the 18/24-month window; archives are kept until you delete them. Use when compliance frameworks mandate multi-year retention of field change data.
- `data/data-quality-and-governance` — Broader data governance frameworks and audit trail design at the org level.
- `security/event-monitoring` — Captures user activity and API events (not field-level changes). Complement to field history when the requirement includes behavioral audit of user actions.
- `data/data-storage-management` — History data does not count against data storage (secguide 262 L4555-4556); read it before treating history tables as a storage lever.
