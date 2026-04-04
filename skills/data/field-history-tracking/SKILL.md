---
name: field-history-tracking
description: "Use when enabling, configuring, or querying Salesforce field history tracking to audit changes to field values over time. Covers enabling tracking on objects and fields, the 20-field-per-object limit, 18-month data retention, querying standard History sObjects (AccountHistory, OpportunityHistory, custom __History), and troubleshooting missing records. NOT for Event Monitoring (use security skills), NOT for Shield Field Audit Trail or FieldHistoryArchive (use field-audit-trail)."
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
  - "Retention requirement in months (standard tracking covers up to 18 months)"
  - "Query scope: specific record, user, date range, or field"
outputs:
  - "Field History Tracking enablement decisions per object and field"
  - "SOQL query patterns for XxxHistory and custom __History objects"
  - "Troubleshooting diagnosis for missing history records"
  - "Decision guidance on when to extend to Shield Field Audit Trail"
  - "Configuration checklist for enablement and review"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Field History Tracking

This skill activates when a practitioner needs to enable Salesforce Field History Tracking on standard or custom objects, query history sObjects to audit field value changes, or troubleshoot cases where expected history records are absent. It does NOT cover Shield Field Audit Trail (use `field-audit-trail`) or Event Monitoring (use security skills).

---

## Before Starting

Gather this context before working on anything in this domain:

- **Object and field list:** Identify which objects and which specific fields require history. Salesforce enforces a hard limit of 20 tracked fields per object. Exceeding this limit requires deselecting existing tracked fields — the platform will not allow a 21st field to be enabled.
- **Retention window:** Standard Field History Tracking retains data for up to 18 months on a rolling basis. History older than 18 months is deleted automatically. If the requirement exceeds 18 months, this skill will not solve it alone — Shield Field Audit Trail (a paid add-on) is required.
- **Field eligibility:** Not all field types are eligible for history tracking. Formula fields, roll-up summary fields, and auto-number fields cannot be tracked. Long text area fields are not trackable. Confirm field type before committing to a tracking strategy.
- **Deleted records:** History records for deleted records are also deleted. If a record is hard-deleted, its associated history sObject rows are purged. Soft-deleted records in the Recycle Bin retain their history until permanently deleted.

---

## Core Concepts

### Concept 1: Enabling Field History Tracking

Field History Tracking is enabled in two steps. First, the feature must be activated on the object. For standard objects this is done in Setup > Object Manager > [Object] > Fields & Relationships > Set History Tracking. For custom objects the same path applies. Enabling history on the object does not automatically track any fields — each field must be individually checked.

Second, within the object's history tracking settings, select up to 20 fields to track. Salesforce stores any change to a tracked field as a new row in the object's History sObject (e.g., `AccountHistory` for Account, `MyObject__History` for a custom object `MyObject__c`). The History related list on page layouts surfaces these rows to end users without any additional code.

The History related list is configured separately in Setup > Page Layouts. It must be added to the layout for users to see it inline on a record. Without the related list, data is still stored and queryable via SOQL — it is just not visible on the page.

### Concept 2: History sObjects and Query Structure

Every object with Field History Tracking enabled has a corresponding History sObject. Standard objects use named sObjects: `AccountHistory`, `ContactHistory`, `LeadHistory`, `OpportunityHistory`, `CaseHistory`, etc. Custom objects use the pattern `ObjectApiName__History` (e.g., `Project__History` for `Project__c`).

Key fields on all History sObjects:

| Field | Description |
|---|---|
| `Id` | Unique row identifier |
| `ParentId` | Id of the record that was changed (foreign key to the parent object) |
| `Field` | API name of the field that changed (e.g., `"AnnualRevenue"`, `"StageName"`) |
| `OldValue` | Value before the change. Null if the record was created (new record) or if the field was previously blank. |
| `NewValue` | Value after the change. |
| `CreatedById` | Id of the user who made the change |
| `CreatedDate` | Timestamp when the change occurred |

For a new record creation event, `Field` is set to `"created"`, `OldValue` is null, and `NewValue` is null. For a field change, `Field` contains the tracked field API name.

Example SOQL — all history for a single Account record:

```soql
SELECT Field, OldValue, NewValue, CreatedById, CreatedDate
FROM AccountHistory
WHERE AccountId = '001XXXXXXXXXXXX'
ORDER BY CreatedDate DESC
LIMIT 200
```

Example SOQL — who changed StageName across all Opportunities in the last 30 days:

```soql
SELECT OpportunityId, OldValue, NewValue, CreatedById, CreatedDate
FROM OpportunityHistory
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

History sObjects are available in Salesforce Reports via the standard `[Object] History` report type when history is enabled on the object.

### Concept 3: 18-Month Retention and Data Loss

Salesforce automatically purges Field History records older than 18 months on a rolling basis. This is a platform-enforced limit and cannot be extended for standard history tracking. There is no setting to disable this purge. If a field change occurred 19 months ago, that history row no longer exists.

Organizations that require history beyond 18 months have two documented options:

1. **Shield Field Audit Trail** — A paid Salesforce Shield add-on that extends retention up to 10 years and stores archived records in the `FieldHistoryArchive` sObject. Requires a Shield or standalone FAT license. See the `field-audit-trail` skill.
2. **Custom logging via Apex or Flow** — Capture field changes into a custom object at the time of change using a before-update trigger or Flow. This custom log is not subject to the 18-month purge and can be retained indefinitely. The tradeoff is implementation and maintenance overhead, and it does not backfill historical changes that occurred before the custom logger was deployed.

---

## Mode 1: Enabling Field History Tracking

**When to use:** An object has no history tracking configured and audit requirements call for capturing future field changes.

**Steps:**

1. Go to Setup > Object Manager.
2. Select the target object (e.g., Account, or a custom object).
3. Click **Fields & Relationships**, then **Set History Tracking** (for standard objects) or **Fields & Relationships > Set History Tracking** (for custom objects).
4. Check the **Enable [Object] History** checkbox at the top.
5. Select up to 20 fields to track. The platform enforces the 20-field limit — attempting to save with more than 20 checked will produce a validation error.
6. Click **Save**.
7. Add the **[Object] History** related list to the relevant page layouts in Setup > Page Layouts.

History records begin accumulating from the moment tracking is enabled. No retroactive history is created for changes that occurred before enablement.

---

## Mode 2: Auditing Existing Field History Configuration

**When to use:** Reviewing which objects and fields currently have history tracking enabled, or confirming configuration correctness before a compliance review.

Steps to audit without code:

1. Navigate to Setup > Object Manager > [Object] > Fields & Relationships > Set History Tracking. The checkboxes show which fields are currently tracked.
2. For custom objects, the Salesforce Metadata API returns history configuration in the `CustomObject` metadata type under `enableHistory` (boolean) and in `CustomField` metadata under `trackHistory` (boolean).

Using the Metadata API to audit history configuration programmatically:

```bash
# Retrieve custom object metadata including history settings
sfdx force:source:retrieve -m "CustomObject:MyObject__c"
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
| History existed but is now gone | Change occurred more than 18 months ago | Data is purged; use Shield FAT for future retention |
| History missing for a deleted record | Record was hard-deleted | History is deleted with the record |
| Formula field changes not tracked | Formula fields are not eligible for tracking | Use a regular field or custom log pattern |
| Changes by an integration user not visible | Integration user not the `CreatedById` — may be a System context | Check trigger context; history records the running user |
| New record creation not showing field values | For new records, `OldValue` and `NewValue` are null for the "created" row | Expected behavior; creation event stores Field = "created" only |

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Track field changes for 18 months or less | Standard Field History Tracking | No additional license required; built-in and reportable |
| Track field changes for more than 18 months | Shield Field Audit Trail (`field-audit-trail` skill) | Standard tracking purges at 18 months — FAT is the only Salesforce-native extension |
| Need more than 20 tracked fields on one object | Shield Field Audit Trail (up to 60 fields) or custom logging | Standard FHT hard-caps at 20 fields per object |
| Formula, roll-up, or long text area field must be audited | Custom logging via Apex trigger or Flow | These field types are ineligible for standard history tracking |
| Custom object field history in SOQL | Query `ObjectApiName__History` | Platform auto-generates this sObject when history is enabled |
| Build a report of field changes | Use the built-in `[Object] History` report type | History sObjects are available natively in Report Builder |
| Audit field changes after record deletion | Consider Shield FAT or custom logging pre-deletion | History is deleted along with the parent record |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking field history tracking work complete:

- [ ] History tracking enabled on the object (not just individual fields)
- [ ] Required fields selected — count does not exceed 20 per object
- [ ] Ineligible field types (formula, roll-up, long text area, auto-number) excluded from selection
- [ ] History related list added to the relevant page layouts
- [ ] SOQL query validated against the correct History sObject name (standard or `__History`)
- [ ] 18-month retention limit communicated to stakeholders; escalation path to Shield FAT documented if longer retention is anticipated
- [ ] Deleted record behavior communicated to stakeholders
- [ ] Tracking confirmed active by making a test change and verifying a history row appears

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Checkbox fields store `true`/`false`, not the field label** — When a checkbox field is tracked, `OldValue` and `NewValue` contain the literal strings `"true"` or `"false"`, not any display label. SOQL comparisons must use these string values. Reports and list views typically display these correctly, but programmatic comparisons that check for `"Yes"` or `"Checked"` will fail silently.

2. **New record creation sets `OldValue` and `NewValue` to null** — When a record is first created, a history row is written with `Field = "created"`, `OldValue = null`, and `NewValue = null`. Field values at creation time are NOT captured as individual field-level rows. If the requirement includes capturing initial values at creation, a custom trigger or Flow must store these separately at insert time.

3. **History tracking is not retroactive** — Enabling history on a field records changes from that point forward only. No history rows are created for changes that occurred before enablement. Stakeholders who expect to see historical changes from before the feature was turned on will be disappointed; communicate this limitation clearly before enablement.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field history enablement decisions | Per-object table of enabled fields, tracking status, and field type eligibility |
| SOQL query set | Parameterized queries for AccountHistory, OpportunityHistory, custom `__History` objects |
| Troubleshooting diagnosis | Root cause analysis for missing history records |
| Retention advisory | Documentation of the 18-month limit and recommended escalation to Shield FAT if needed |

---

## Related Skills

- `field-audit-trail` — Shield Field Audit Trail for retention beyond 18 months, up to 10 years. Required when compliance frameworks (FINRA, HIPAA, SOX) mandate multi-year retention of field change data.
- `data-quality-and-governance` — Broader data governance frameworks and audit trail design at the org level.
- `event-monitoring` — Captures user activity and API events (not field-level changes). Complement to field history when the requirement includes behavioral audit of user actions.
