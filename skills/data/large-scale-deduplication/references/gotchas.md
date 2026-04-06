# Gotchas — Large Scale Deduplication

Non-obvious Salesforce platform behaviors that cause real production problems in large-scale dedup projects.

## Gotcha 1: Database.merge() Is Limited to 10 Calls Per Transaction, Not Per Batch Chunk

**What happens:** A batch Apex job with scope size 200 attempts 200 merge calls in a single `execute()` block. The job fails with a governor limit exception on the 11th call. None of the merges in that chunk are committed (transaction rollback).

**When it occurs:** Any time `Database.merge()` is called more than 10 times in a single Apex execution context — including inside a trigger, an execute-anonymous script, or a batch `execute()` block.

**How to avoid:** Set the batch size to 10 when calling `Database.executeBatch(new MyBatch(), 10)`. This ensures each `execute()` invocation receives exactly 10 scope records and performs exactly 10 merge calls — the maximum allowed per transaction. Do not rely on the default batch size (200).

---

## Gotcha 2: Custom Objects Are Not Supported by Database.merge()

**What happens:** Calling `Database.merge()` with a custom object SObject fails at compile time with: `Illegal argument type for merge: MyObject__c`. Custom objects have no native merge DML equivalent.

**When it occurs:** Any deduplication project that targets custom objects assumes the merge DML pattern used for Account/Contact/Lead will work.

**How to avoid:** For custom object deduplication, implement a manual survivorship pattern:
1. Copy field values from the losing record to the master record (selective per field).
2. Re-parent any child/related records by updating the lookup field to point to the master ID.
3. Delete the losing record.

This is more complex and requires explicit handling of every related object — document the re-parenting logic before starting.

---

## Gotcha 3: Losing Record IDs Are Permanently Deleted — Redirects Are Not Universal

**What happens:** After a merge, the losing record's Salesforce ID is deleted. The Salesforce REST API returns an HTTP 301 redirect from the old ID to the master ID for record GET requests. However, systems that query by SOQL using a stored ID (e.g., `WHERE Id = :storedLosingId`) return zero rows — they do not follow the redirect.

**When it occurs:** Any integration, data warehouse ETL, or analytics pipeline that stores Salesforce IDs in an external system and queries by those IDs without an API-level lookup step.

**How to avoid:** Before running a large merge batch, audit all external systems that store Salesforce IDs for the target object. For each integration, determine whether it uses API record lookup (gets the redirect) or stored-ID SOQL (gets zero rows). Coordinate an ID refresh for systems that cannot follow redirects.

---

## Gotcha 4: Automation Fires on Every Merge at Volume — and Can Blow Governor Limits

**What happens:** A merge operation triggers "before update" and "after update" on the master record, and "before delete" and "after delete" on each losing record. At volume (thousands of merges per batch run), Flows or triggers that make callouts, run SOQL-heavy logic, or perform additional DML can quickly accumulate governor limit violations across the batch.

**When it occurs:** Orgs with active record-triggered Flows, Apex triggers, or Process Builder processes on the target object. Especially dangerous when those automations perform callouts or SOQL queries per-record.

**How to avoid:** Before running any merge batch in production:
1. Audit all active automation on the target object (Flows, triggers, process builders, workflows).
2. Disable or add a Custom Permission bypass flag to automation that is not safe to fire during bulk merges.
3. Re-enable automation after the batch completes and validate that no records are in an unexpected state.

---

## Gotcha 5: Standard Duplicate Jobs Have Per-Run Record Caps

**What happens:** A practitioner uses Salesforce's built-in Duplicate Jobs feature (Sales Cloud orgs) to identify and merge all duplicates across 2 million Account records. The job completes but only processes a fraction of the expected duplicate set. The rest are silently skipped.

**When it occurs:** Duplicate Jobs are designed for ongoing maintenance sweeps, not one-time retroactive deduplication of millions of existing records. Each job run has a processing cap that varies by edition and configuration.

**How to avoid:** Use Duplicate Jobs for ongoing post-go-live hygiene (scanning new or recently modified records). For a retroactive large-scale cleanup, use Bulk API 2.0 extraction with external matching, or a third-party tool (DemandTools, Cloudingo) designed for high-volume retroactive dedup.
