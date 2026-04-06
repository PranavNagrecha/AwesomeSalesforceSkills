# LLM Anti-Patterns — Field Audit Trail

Common mistakes AI coding assistants make when generating or advising on Salesforce Shield Field Audit Trail (FAT).
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Enabling FAT Without Enabling Field History Tracking

**What the LLM generates:** "Enable Field Audit Trail on the Account object and set the retention policy to 84 months" without mentioning that Field History Tracking must also be enabled on the same fields.

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

SELECT ParentId, FieldHistoryType, OldValue, NewValue, CreatedById, CreatedDate
FROM FieldHistoryArchive
WHERE SobjectType = 'Account'
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

**Why it happens:** LLMs conflate the FAT 60-field ceiling with the standard Field History Tracking 20-field limit. These are separate limits.

**Correct pattern:**

```
Standard Field History Tracking remains limited to 20 fields per object even
with Shield. FAT raises the ceiling to 60 fields for FAT-tracked fields
specifically, but the standard 20-field limit still governs the non-FAT
history window. Plan field selection carefully: you can track up to 60 fields
in FAT, but only 20 of those will also appear in the standard XxxHistory
sObjects during the 18-month standard window.
```

**Detection hint:** If the advice states that Shield raises the Field History Tracking limit above 20 fields per object (rather than specifically the FAT limit), the distinction is lost.

---

## Anti-Pattern 6: Using Default Retention Policy Without Explicit Configuration

**What the LLM generates:** "Enable FAT — the default retention is sufficient for compliance."

**Why it happens:** LLMs assume defaults are safe. The default FAT retention period may not match the specific compliance requirement (e.g., FINRA 7-year, HIPAA 6-year).

**Correct pattern:**

```
Always set an EXPLICIT retention policy per object. Do not rely on the Salesforce
default. Map each tracked object to the governing compliance requirement:
- FINRA Rule 17a-4: 84 months (7 years)
- HIPAA access log retention: at least 72 months (6 years)
- SOX: varies by jurisdiction, typically 84 months

Set the retention policy in Setup > Field Audit Trail to match or exceed the
compliance minimum. Document the mapping between regulation and retention months.
```

**Detection hint:** If the advice enables FAT without specifying an explicit retention period tied to a compliance requirement, the default may create a compliance gap.
