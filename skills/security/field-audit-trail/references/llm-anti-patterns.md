# LLM Anti-Patterns — Field Audit Trail

Common mistakes AI coding assistants make when generating or advising on Salesforce Shield Field Audit Trail (FAT).
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Enabling FAT Without Enabling Field History Tracking

**What the LLM generates:** "Enable Field Audit Trail on the Account object and set the retention policy to 84 months" (there is no such setting: `archiveAfterMonths` is 1-18 and `archiveRetentionYears` is only a deletion reminder) without mentioning that Field History Tracking must also be enabled on the same fields.

**Why it happens:** LLMs treat FAT as a standalone capture mechanism. Training data often describes FAT in isolation from standard Field History Tracking.

**Correct pattern:**

```
Field Audit Trail does NOT independently capture field changes. Field History
Tracking must also be enabled on the same object and fields. FAT extends the
RETENTION of data that Field History Tracking captures — it is not a separate
capture engine. Without Field History Tracking enabled, FAT policies are active
but NO data flows into FieldHistoryArchive.
```

**Detection hint:** If the advice enables FAT without explicitly requiring Field History Tracking on the same fields, the archive will be empty.

---

## Anti-Pattern 2: Suggesting Reports on FieldHistoryArchive

**What the LLM generates:** "Create a report on FieldHistoryArchive to show auditors the field change history."

**Why it happens:** LLMs assume all sObjects are reportable. FieldHistoryArchive is intentionally excluded from Report Builder, but this is a non-obvious platform constraint.

**Correct pattern:**

```
FieldHistoryArchive is NOT available in Salesforce Reports or List Views.
The only supported query mechanism is SOQL — via Apex, Data Loader, Workbench,
or an external ETL tool. Plan for a SOQL-based audit extraction workflow and
export results to CSV for auditor delivery.
```

**Detection hint:** If the advice references creating a Salesforce Report against FieldHistoryArchive, the approach will fail.

---

## Anti-Pattern 3: Querying FieldHistoryArchive Without Bounded Filters

**What the LLM generates:** SOQL queries filtering on OldValue or NewValue without anchoring on ParentId or CreatedDate.

**Why it happens:** LLMs generate SOQL patterns that look syntactically correct but ignore indexing constraints on FieldHistoryArchive.

**Correct pattern:**

```
FieldHistoryArchive can contain billions of rows. Filtering on OldValue,
NewValue, or FieldHistoryType alone triggers unindexed full-table scans
that will time out.

Always include ParentId or a bounded CreatedDate range as the PRIMARY filter:

SELECT ParentId, FieldHistoryType, Field, OldValue, NewValue, CreatedDate
FROM FieldHistoryArchive
WHERE FieldHistoryType = 'Account'
  AND ParentId = '001XXXXXXXXXXXX'
  AND CreatedDate >= 2023-01-01T00:00:00Z
ORDER BY CreatedDate DESC
LIMIT 200
```

**Detection hint:** If the SOQL query filters only on OldValue, NewValue, or FieldHistoryType without ParentId or CreatedDate, it will time out on production data.

---

## Anti-Pattern 4: Assuming Archival Is Immediate After Enabling FAT

**What the LLM generates:** "Enable FAT and then query FieldHistoryArchive to verify the data."

**Why it happens:** LLMs present configuration steps as synchronous. The asynchronous migration window is a non-obvious platform behavior.

**Correct pattern:**

```
When FAT is enabled, migration of existing field history to FieldHistoryArchive
happens asynchronously in the background. There is no user-visible indicator of
when migration completes. Allow several days for the backfill before performing
compliance audits or validation queries against the archive. Do not treat empty
query results immediately after enabling FAT as a configuration failure.
```

**Detection hint:** If the advice tests FieldHistoryArchive immediately after enabling FAT and treats empty results as a problem, it is not accounting for the async migration window.

---

## Anti-Pattern 5: Claiming FAT Raises the Standard Field History Tracking Limit

**What the LLM generates:** "With Shield, you can track more than 20 fields per object using Field History Tracking."

**Why it happens:** LLMs conflate the Field Audit Trail 200-field ceiling with the 20-field limit that applies without it (security guide 262 L4835-4838).

**Correct pattern:**

```
Standard Field History Tracking remains limited to 20 fields per object even
with Shield. Field Audit Trail raises the per-object ceiling to 200 fields; the 20-field
limit applies without it (security guide 262 L4835-4838). UNVERIFIED
(2026-11-19): which of the tracked fields also appear in the standard
XxxHistory sObjects is not documented; confirm in a sandbox.
```

**Detection hint:** If the advice states that Shield raises the Field History Tracking limit above 20 fields per object (rather than specifically the FAT limit), the distinction is lost.

---

## Anti-Pattern 6: Using Default Retention Policy Without Explicit Configuration

**What the LLM generates:** "Enable FAT — the default retention is sufficient for compliance."

**Why it happens:** LLMs assume defaults are safe. The default FAT policy (archive after 18 months in production, one month in sandboxes; security guide 262 L4881-4883) is not tied to any specific compliance requirement (e.g., FINRA 7-year, HIPAA 6-year).

**Correct pattern:**

```
Always set an EXPLICIT HistoryRetentionPolicy per object. Do not rely on the
Salesforce default. Map each tracked object to the governing compliance requirement:
- FINRA Rule 17a-4: archiveRetentionYears 7
- HIPAA access log retention: archiveRetentionYears of at least 6
- SOX: varies by jurisdiction, typically 7

Archived data is kept until you delete it, and archiveRetentionYears is only a
reminder for manual deletion (api_meta.txt L46348-46351). Define the policy with
Metadata API (security guide 262 L4833-4835). Document the mapping between
regulation and years, and do not delete archive rows before that date.
```

**Detection hint:** If the advice enables FAT without specifying an explicit retention period tied to a compliance requirement, the default may create a compliance gap.
