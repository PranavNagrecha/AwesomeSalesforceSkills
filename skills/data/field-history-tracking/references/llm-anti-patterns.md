# LLM Anti-Patterns — Field History Tracking

Common mistakes AI coding assistants make when generating or advising on Salesforce field history tracking.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Querying the Wrong History Object Name

**What the LLM generates:** `SELECT Id, Field, OldValue, NewValue FROM Contact__History` for a standard object, or `SELECT Id FROM AccountHistory` for a custom object named Account_Record__c, using wrong naming conventions for History sObjects.

**Why it happens:** LLMs mix up the naming patterns for standard vs custom object history tables. Standard objects use `{ObjectName}History` (no underscores), while custom objects use `{ObjectName}__History` (double underscore before History).

**Correct pattern:**

```text
History object naming conventions:

Standard objects:
  Account -> AccountHistory
  Contact -> ContactHistory
  Lead -> LeadHistory
  Case -> CaseHistory

Exception (field history uses <Object>FieldHistory, not <Object>History):
  Opportunity -> OpportunityFieldHistory
  (OpportunityHistory is a DIFFERENT object — stage/pipeline history,
   with no Field/OldValue/NewValue columns. Always confirm the sObject
   name in the object reference.)

Custom objects:
  My_Object__c -> My_Object__History

Key query fields:
  SELECT Id, AccountId, Field, DataType, OldValue, NewValue, CreatedDate, CreatedById
  FROM AccountHistory
  WHERE AccountId = :recordId     -- standard history uses <Object>Id (object_reference 264 L4628)
  ORDER BY CreatedDate DESC       -- CreatedDate/CreatedById: UNVERIFIED (2026-10-20), see SKILL.md Concept 2
```

**Detection hint:** Flag History SOQL queries that use `__History` suffix on standard objects or omit `__` prefix on custom object history names. Regex: standard object names followed by `__History`.

---

## Anti-Pattern 2: Assuming All Field Types Can Be Tracked

**What the LLM generates:** "Enable field history tracking on the Formula__c field" or "Track changes to the Rich_Text__c field" without noting that certain field types cannot be tracked.

**Why it happens:** Training data focuses on the 20-field limit but rarely lists the specific field types that are excluded from tracking.

**Correct pattern:**

```text
Field types that CANNOT be tracked with Field History Tracking (secguide 262 L4797-4803):
- Formula fields
- Roll-Up Summary fields
- Auto-number fields
- Created By / Last Modified By, AI Prediction fields, Expected Revenue on opportunities

Trackable only as "Track changes only" (no old/new values; secguide 262 L4793-4794, L4656):
- Multi-select picklist fields
- Large text fields (over 255 characters)

(Rich Text Area: UNVERIFIED (2026-10-20), not named in the corpus. Field Audit Trail
archives exclude long text and multi-select fields, secguide 262 L4890-4891.)

Field types that CAN be tracked:
- Text, Number, Currency, Percent, Date, DateTime
- Picklist (single-select)
- Checkbox
- Lookup and Master-Detail relationship fields
- Email, Phone, URL

Maximum 20 fields per object (standard or custom) without Field Audit Trail;
events and tasks: 6 (secguide 262 L4700).
```

**Detection hint:** Flag field history tracking recommendations that include formula fields, roll-up summaries, rich text areas, or auto-number fields.

---

## Anti-Pattern 3: Not Accounting for the 18-Month Retention Limit

**What the LLM generates:** "Query AccountHistory to see all changes made to this field since the org was created" without noting that standard Field History Tracking retains records for only 18 months.

**Why it happens:** The 18-month limit is an operational constraint not always mentioned in SOQL or configuration documentation. LLMs generate queries against History objects without qualifying the time range that will return data.

**Correct pattern:**

```text
Field History Tracking retention (secguide 262 L4553-4555):
- Without Field Audit Trail: up to 18 months in the UI, up to 24 months via the API
  (Data Loader or queryAll() reach the 18-24 month rows, L4655)
- Beyond that the data is gone
- With Field Audit Trail: retained until you delete it

For longer retention:
- Field Audit Trail (Shield): archived data stored in the FieldHistoryArchive big
  object; the retention policy is a HistoryRetentionPolicy on the object,
  archiveAfterMonths 1-18 (api_meta 264 L46329-46332). "Up to 10 years" and
  "contractual limit" are UNVERIFIED (2026-10-20): not in the corpus.

When querying field history, always include a CreatedDate filter:
  WHERE CreatedDate >= :eighteenMonthsAgo
  to make the retention limit explicit in your code.
```

**Detection hint:** Flag field history queries or reports that do not acknowledge the 18-month limit, especially when the use case involves compliance or long-term audit requirements.

---

## Anti-Pattern 4: Expecting Field History to Capture Bulk API and Migration Changes

**What the LLM generates:** "Field history tracking will capture all changes including data loads and migrations" without noting that field history tracking may not fire for certain bulk operations or when triggers are disabled.

**Why it happens:** Field history tracking is presented as automatic for all DML operations. Edge cases where tracking does not fire (mass transfers, certain bulk API operations, field updates by workflow rules in some contexts) are not well-documented in training data.

**Correct pattern:**

```text
When field history tracking does NOT capture changes:
- Changes by Process Builder, Apex or Flow on an object the current user cannot
  edit: "Field history honors the permissions of the current user and doesn't
  record changes that occur in the system context" (secguide 262 L4687-4689)
- Changes made before tracking was turned on (secguide 262 L4653-4654)
- Time fields (secguide 262 L4657)
- Recurring and child events: "doesn't track all changes" (secguide 262 L4703)
- UNVERIFIED (2026-10-20) (no corpus line): Mass Transfer, lead conversion field
  changes, record merges, back-end patches, sharing recalculation, formula recalc

When field history tracking DOES capture changes (UNVERIFIED (2026-10-20) as a list;
the guide confirms automation changes are tracked when the user can edit the field):
- Standard UI edits
- REST/SOAP API updates
- Apex DML operations
- Data Loader (insert, update, upsert)
- Flow and Process Builder field updates
- Bulk API operations (tracked but may be batched)

For comprehensive audit coverage, combine Field History Tracking with
Event Monitoring (LoginEvent, ApiEvent) for a complete picture.
```

**Detection hint:** Flag claims that field history tracking captures "all changes" without noting the exceptions. Look for migration plans that rely solely on field history for audit verification.

---

## Anti-Pattern 5: Tracking Too Many Fields and Hitting the 20-Field Limit Prematurely

**What the LLM generates:** "Enable tracking on all important fields" without a strategy for prioritizing which 20 fields to track per object, leading to requests to track more than 20 fields.

**Why it happens:** The 20-field limit is mentioned in documentation but LLMs do not apply it as a design constraint. Recommendations to "track everything important" quickly exhaust the limit on objects like Account or Opportunity that have many business-critical fields.

**Correct pattern:**

```text
Field history tracking allocation strategy (20 fields per object):

Priority 1 (track always):
- Fields required by compliance or audit (Stage, Amount, OwnerId)
- Fields involved in business-critical decisions (Status, Close Date)
- Fields frequently disputed by users ("I didn't change that")

Priority 2 (track if slots available):
- Fields changed by automation (to verify automation behavior)
- Fields involved in integration sync (to diagnose sync issues)

Do NOT track:
- Fields that change every day on every record (last activity date)
- Fields with high-cardinality updates (description, notes)
- Fields better tracked by Event Monitoring or custom audit triggers

If 20 fields is not enough:
- Field Audit Trail: up to 200 fields per object (secguide 262 L4836); the scratch-org
  feature description says 60 total (sfdx_dev 264 L4606-4607)
- Custom audit trigger: write to a custom Audit_Log__c object
```

**Detection hint:** Flag "enable field history on all fields" recommendations without a prioritization framework or mention of the 20-field limit.
