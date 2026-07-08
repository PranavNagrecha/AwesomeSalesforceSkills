# Gotchas — Field History Tracking

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Checkbox Fields Store `true`/`false` Strings, Not Display Labels

**What happens:** When a checkbox field (Boolean) is tracked, `OldValue` and `NewValue` in the History sObject contain the literal strings `"true"` or `"false"` — not values like `"Checked"`, `"Yes"`, `"No"`, or the field label. Any code that performs a string comparison against a checkbox history value using non-boolean string representations will silently produce wrong results. Reports and the History related list display these values in a human-friendly way, masking the underlying storage format.

**When it occurs:** When developers write Apex or SOQL logic that evaluates `OldValue` or `NewValue` for a checkbox field and checks for strings like `"Yes"` or compares against non-`"true"`/`"false"` strings. Also occurs when integrations parse exported history data and apply the wrong mapping.

**How to avoid:** Always compare checkbox history values using the literal strings `"true"` and `"false"` in SOQL `WHERE` clauses or Apex conditionals. Example:

```soql
SELECT ParentId, OldValue, NewValue, CreatedDate
FROM AccountHistory
WHERE Field = 'IsActive__c'
  AND OldValue = 'true'
  AND NewValue = 'false'
```

---

## Gotcha 2: New Record Creation Stores Null for OldValue and NewValue

**What happens:** When a record is first created, a single history row is written with `Field = "created"` and both `OldValue = null` and `NewValue = null`. The individual field values at creation time are NOT stored as field-level history rows. This means if a practitioner queries history to determine what a field's value was when a record was created, no rows exist for those fields — only the `"created"` row.

**When it occurs:** When stakeholders ask "what was the value of X when this record was first created?" or when a SOQL query expects to find a row for each field set during record creation. For example, if `StageName` is set to `"Prospecting"` at Opportunity creation, there is no history row showing `NewValue = "Prospecting"` — only the `"created"` row with null values.

**How to avoid:** Capture initial field values at creation time using a separate mechanism. An Apex after-insert trigger or a Record-Triggered Flow set to run on Create can write the initial values to a custom log object or a custom field. Communicate this behavior clearly to stakeholders during requirements — if initial values matter for audit purposes, standard history tracking alone is insufficient.

---

## Gotcha 3: History Tracking Is Not Retroactive — No Backfill for Pre-Enablement Changes

**What happens:** Enabling Field History Tracking on a field captures all changes from that moment forward. No history rows are created for changes that occurred before the feature was enabled. If an object has existed for years without history tracking, there is no way to retrieve the historical field change record from before enablement.

**When it occurs:** Most commonly when a compliance or audit requirement surfaces after the fact — e.g., a project completes, and an auditor asks for a change log going back 12 months, but history tracking was only enabled 2 months ago. Organizations that enabled tracking "eventually" after go-live have a gap in their audit record.

**How to avoid:** Enable Field History Tracking as early as possible — ideally during initial object design and before go-live. Once the requirement is identified, enable tracking immediately even if the full configuration is still in progress. There is no retroactive fix. If historical changes before enablement are required for compliance, document the gap explicitly and assess whether a compensating control (e.g., email audit logs, external system records) can fill it.

---

## Gotcha 4: Formula Fields, Roll-Up Summary Fields, and Auto-Number Fields Are Not Eligible

**What happens:** Attempting to select a formula field, roll-up summary field, or auto-number field in the history tracking settings has no effect — Salesforce does not display them in the tracking selection UI, or they are greyed out. If a practitioner designs an audit strategy around tracking a formula field (e.g., a field that derives a status from multiple source fields), the tracking will not work.

**When it occurs:** When an admin wants to track a "computed" status value stored in a formula field. The formula itself is not a stored value that changes — it re-computes on read. There is nothing to track. Roll-up summaries are similarly platform-computed.

**How to avoid:** If the computed value must be audited, replace the formula field with a regular field that is written by an Apex trigger or Flow whenever the source fields change. Enable history tracking on the regular field instead. This adds implementation complexity but is the only path to tracking formula-derived values.

---

## Gotcha 5: The Child-to-Parent Relationship Name Differs — `Parent` on Custom History, the Object Name on Standard History

**What happens:** The relationship name for traversing from a history object up to its parent record is not uniform. On a custom `__History` object the parent field is `ParentId`, so you reach parent fields with `Parent.Name`, `Parent.CustomField__c` — regardless of the parent's API name. On a standard history object the parent field is object-specific (`AccountId` on `AccountHistory`, `ContactId` on `ContactHistory`), so the traversal uses the object name: `Account.Name`, `Contact.Name`. Writing `Parent.Name` against `AccountHistory` — or `Project__r.Name` against `Project__History` — fails to compile.

**When it occurs:** Writing child-to-parent relationship queries against history objects, especially in Apex where a wrong relationship name is a hard compile error, or when porting a query between a standard object (relationship `Account`, field `AccountId`) and a custom object (relationship `Parent`, field `ParentId`).

**How to avoid:** Choose the relationship name by object type — `Parent.<field>` on custom `__History`, the object name (`Account.<field>`) on standard history — and match the parent-id filter field the same way (`ParentId` on custom, `AccountId`/`ContactId` on standard). When unsure, confirm the relationship name with a `describeSObject` call or in Setup before hardcoding it.

---

## Gotcha 6: History Relationship-Query Syntax Does Not Apply to Shield `FieldHistoryArchive`

**What happens:** The clean relationship-query patterns that work against standard and custom History objects — child-to-parent traversal to the parent record and parent-to-child subqueries — silently do not carry over to Shield Field Audit Trail's `FieldHistoryArchive`. That object enforces a restricted SOQL grammar: the `WHERE` clause must lead with `FieldHistoryType`, followed by `ParentId` or `CreatedDate`; the operators `!=`, `LIKE`, `NOT IN`, `EXCLUDES`, and `INCLUDES` are rejected; and a query returns at most 2,000 rows unless a `LIMIT` clause raises the cap (page the rest with `queryMore()`).

**When it occurs:** When a team graduates from standard history to Shield FAT for longer retention and assumes their existing history queries will keep working. A query that filtered on `Field != 'StageName'` or traversed to the parent record throws when re-pointed at `FieldHistoryArchive`.

**How to avoid:** Treat `FieldHistoryArchive` as a separate query surface with its own rules — see the `field-audit-trail` skill. Structure filters as `FieldHistoryType = '...' AND ParentId = '...'` (or `AND CreatedDate ...`), avoid the disallowed operators, and always set an explicit `LIMIT` when you expect more than 2,000 rows.

---

## Gotcha 7: The 20-Field Limit Is Per Object and Cannot Be Raised Without Shield

**What happens:** Salesforce enforces a hard limit of 20 tracked fields per object for standard Field History Tracking. When the 20th field is already selected and an admin tries to enable an additional field, the Save operation fails with an error. There is no way to raise this limit within standard editions — the only path to tracking more than 20 fields on a single object is to license Salesforce Shield Field Audit Trail, which supports up to 60 fields per object.

**When it occurs:** High-complexity objects (e.g., Opportunity with many custom fields) often accumulate field tracking selections incrementally until the limit is hit. When a new compliance requirement surfaces requiring tracking of field 21, the team is forced to make a tradeoff — either remove an existing tracked field or license Shield.

**How to avoid:** Audit tracked field selections periodically. Remove fields that are no longer required for active compliance or operational monitoring. Treat the 20-field limit as a design constraint during initial planning. If the object is likely to need more than 20 fields tracked over time, include Shield Field Audit Trail in the licensing discussion early.
