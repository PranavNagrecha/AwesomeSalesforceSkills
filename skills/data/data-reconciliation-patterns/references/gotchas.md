# Gotchas — Data Reconciliation Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SystemModstamp Updates on Formula Recalculation, Not Just DML

**What happens:** `SystemModstamp` on a record updates whenever the platform recalculates a formula field referencing that record — even when no user or API performed an explicit DML write. This causes delta load queries filtered on `SystemModstamp > :lastRun` to return records that appear functionally unchanged in the external system.

**When it occurs:** Most commonly when a child record is updated and a parent record has a formula or roll-up field that references the child. Salesforce recalculates the parent's formula and stamps `SystemModstamp`. Bulk operations (large data loads, workflow rules triggering en masse) can produce thousands of false positives.

**How to avoid:** Use `LastModifiedDate` if you only want records that received an explicit DML write (insert, update, delete, undelete by a user or API). Use `SystemModstamp` only when you also need to catch system-driven recalculations. Document which field drives the delta in the integration specification so the choice is intentional.

---

## Gotcha 2: Text External ID Fields Are Case-Sensitive

**What happens:** A custom Text field marked as External ID performs lookups with case-sensitive matching. If the source system sends `Abc-001` and the existing Salesforce record stores `ABC-001`, the upsert will not match the existing record and will attempt an insert — creating a duplicate.

**When it occurs:** Any time source data has inconsistent casing (e.g., user-entered strings, ERP exports where case normalisation varies by environment, legacy systems that changed casing conventions over time). The failure mode is silent: the upsert reports success, but the row is inserted rather than updated, and no error is raised unless the field also has a Unique constraint (in which case a `DUPLICATE_VALUE` error surfaces).

**How to avoid:** Enforce casing normalization at the ETL layer before loading — always uppercase or always lowercase. Alternatively, store the External ID as a formula field that uppercases the source value, and use that formula-derived field as the matching key. If using Bulk API 2.0, normalize the `externalIdFieldName` column in the CSV before upload.

---

## Gotcha 3: MULTIPLE_CHOICES on Non-Unique External ID Fields

**What happens:** Bulk API 2.0 upsert against an External ID field that is not marked Unique will fail with `MULTIPLE_CHOICES` for any row where more than one Salesforce record shares the same external ID value. The job does not fail entirely — it processes other rows and logs the affected rows in `failedResults` — so the failure is invisible unless `failedResults` is explicitly fetched.

**When it occurs:** When a custom field has the External ID checkbox checked but not the Unique checkbox, and duplicate values were loaded historically (often from a prior import without uniqueness validation). The platform allows duplicate external ID values when uniqueness is not enforced; the upsert operation is the first point where the ambiguity becomes an error.

**How to avoid:** Always check both the External ID and Unique checkboxes on the field definition before using it as an upsert key. Before enabling uniqueness on an existing field, run a SOQL duplicate-count query: `SELECT HR_Employee_Id__c, COUNT(Id) cnt FROM Contact GROUP BY HR_Employee_Id__c HAVING COUNT(Id) > 1`. Resolve duplicates before enforcing uniqueness.

---

## Gotcha 4: CDC Retention Is 72 Hours — Not Indefinite

**What happens:** If a CDC subscriber goes offline for more than 72 hours and attempts to replay from its stored `replayId`, the Pub/Sub API returns an error indicating the replay position is outside the retention window. Events from the gap period are permanently lost from the stream.

**When it occurs:** Subscriber outages longer than 3 days (planned maintenance windows, infrastructure failures, or a subscription that was silently disconnected and not monitored). The subscriber reconnects, tries to replay from the last stored `replayId`, and either receives an error or defaults to tip-of-stream, silently dropping the gap.

**How to avoid:** Monitor CDC subscriber health with alerting on connection state. Set up an alert that fires if no events are processed within a configurable window (e.g., 4 hours for active objects). When the retention window is exceeded, trigger a full record-level reconciliation job to identify and re-sync records that changed during the gap instead of relying on the event stream alone.

---

## Gotcha 5: Bulk API 2.0 Job Status "JobComplete" Does Not Mean All Rows Succeeded

**What happens:** A Bulk API 2.0 job transitions to `JobComplete` status even if some rows failed. The `numberRecordsFailed` field on the job status response reflects failures, but callers that only check the job state string (not `numberRecordsFailed`) treat a partially-failed job as fully successful.

**When it occurs:** Whenever validation rules, duplicate rules, required-field constraints, or trigger-thrown exceptions prevent individual rows from processing. The job completes because the remaining rows were processed; the failed rows are logged to the `failedResults` endpoint but require an explicit GET request to retrieve.

**How to avoid:** After any Bulk API 2.0 job reaches `JobComplete`, always: (1) check `numberRecordsFailed > 0` on the job status response, and (2) if non-zero, fetch and log the `failedResults` CSV. Build this check into the integration's post-job verification step rather than treating it as optional.
