# Gotchas — Real-Time vs Batch Integration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Apex Callout 120-Second Timeout Is Absolute and Cannot Be Extended

**What happens:** An Apex HTTP or SOAP callout that does not receive a response within 120 seconds throws a `System.CalloutException: Read timed out` and the entire transaction fails. There is no API to raise this limit. If the external system is slow (large payload, slow query, network degradation), the callout will time out regardless of retry logic inside the same transaction.

**When it occurs:** Most commonly seen with ERP or legacy SOAP services that perform synchronous database lookups before responding, with large payloads (XML responses over 1 MB), and during external system maintenance windows where the service accepts the connection but delays the response.

**How to avoid:** Move long-running callouts to `Queueable` with callout support (`Database.AllowsCallouts`) and implement a separate retry mechanism using a custom object or Platform Event to signal failures. If the external service cannot respond within 120 seconds under any conditions, the synchronous callout pattern is architecturally wrong for this integration — switch to an async event-driven approach.

---

## Gotcha 2: Apex Callout Limit of 100 Per Transaction Applies to Bulk DML

**What happens:** Each Apex transaction (including a bulk trigger invoked by a data load) can make at most 100 callouts. A trigger that fires a callout per record will silently fail or throw `System.LimitException: Too many callouts` once the 101st record is processed in the same transaction. Data Loader and Bulk API process records in batches of up to 200 (Bulk API v1) or variable chunk sizes (Bulk API 2.0), so a trigger with one callout per record fails at scale.

**When it occurs:** Any time a developer writes a trigger that calls `@future(callout=true)` or `Queueable` with callouts in a per-record pattern and a bulk operation (data migration, batch job, integration load) processes more than 100 records per execution context.

**How to avoid:** Never design one callout per record in a trigger. Aggregate the records from `Trigger.new`, publish a single Platform Event with a list payload, or collect record IDs and process them in a single batch callout outside the trigger context. Review all trigger callout patterns against the 100/transaction limit before any bulk data operation.

---

## Gotcha 3: Platform Events Are Not Rolled Back When the Publishing Transaction Fails (Default Behavior)

**What happens:** By default, Platform Events use `PUBLISH_IMMEDIATELY` publish behavior. This means the event is written to the event bus as soon as `EventBus.publish()` succeeds — even if the Salesforce DML transaction that called it subsequently fails and rolls back. Subscribers will receive the event and process it even though the underlying record change was never committed. This creates phantom events that cause external systems to act on data that does not exist in Salesforce.

**When it occurs:** Any time a Platform Event is published inside a trigger or Apex method that also performs DML, and a subsequent validation rule, duplicate rule, or exception causes the transaction to roll back. Common in Order and Opportunity triggers where the event fires early but a downstream validation fails.

**How to avoid:** Set `publishBehavior` to `PHASE_AFTER_COMMIT` on the Platform Event definition (available in Setup > Platform Events > Edit). This delays publishing until the transaction commits successfully. Be aware this adds slight latency. Alternatively, publish events in a separate Queueable that runs after the originating transaction confirms success — though this introduces its own ordering concerns.

---

## Gotcha 4: CDC Replay Window Is 3 Days — Silent Data Loss After Expiry

**What happens:** Change Data Capture events are stored in the event bus for exactly 3 days (72 hours for standard Platform Events). If a CDC subscriber (external system, Apex trigger, CometD client) is offline for more than 3 days and attempts to replay from a stored replay ID, the old events are no longer available. The subscriber will receive only events from the current window. There is no error — the system simply delivers from the oldest available event, silently skipping the gap.

**When it occurs:** During extended infrastructure outages, cloud provider incidents, or planned maintenance windows that exceed 72 hours. Also seen when a new subscriber is onboarded and the team assumes it can backfill months of history.

**How to avoid:** Monitor subscriber last-poll timestamps with alerting at 48 hours of inactivity (providing 24 hours of recovery time before window expiry). If a subscriber exceeds the replay window, trigger a full reconciliation via Bulk API 2.0 query job before resuming CDC-based sync. Document the replay window as a hard SLA constraint in the integration design.

---

## Gotcha 5: Bulk API 2.0 Has No Cross-Batch Atomicity — Partial Commits Are Permanent

**What happens:** A Bulk API 2.0 ingest job splits its records into internal server-side batches. Each batch is committed independently as it completes. If batch 4 of 10 fails (e.g., due to a validation rule, a field length violation, or a lock timeout), batches 1–3 are already permanently committed and cannot be rolled back. The job completes with a mix of successful and failed records.

**When it occurs:** Any Bulk API 2.0 job processing more than a few hundred records, particularly when: records have interdependencies (e.g., parent records must exist before child records), validation rules can fail for a subset of records, or the job runs during business hours when record locks cause contention.

**How to avoid:** Design all Bulk API 2.0 ingest operations to be idempotent using an external ID field for upsert. Retrieve the failed results CSV after every job and re-queue failed rows for the next cycle. For parent-child record loads, load parent objects in a separate job that completes before the child job starts. Never assume a single bulk job is atomic — treat every job as "best-effort with retry".

---

## Gotcha 6: Bulk API 2.0 Jobs Must Be Scheduled Outside Business Hours — Not Just Recommended

**What happens:** Salesforce documentation recommends (and support strongly advises) that large Bulk API jobs run outside peak business hours. During business hours, large jobs compete with interactive users and other async processes for the shared multi-tenant processing queue. Jobs submitted during peak hours may run significantly slower (hours instead of minutes), and in extreme cases Salesforce may throttle or deprioritize them. This is not just a performance concern — slow jobs can trigger downstream integration timeouts in systems polling for job completion.

**When it occurs:** ETL pipelines scheduled during business hours, particularly those triggered by business processes (e.g., "run the sync after the data team approves the file at 2pm"). Volume above 50,000 records is where the performance degradation becomes significant.

**How to avoid:** Schedule Bulk API 2.0 ingest jobs between midnight and 06:00 in the org's local timezone. If a job must run during business hours (e.g., for an urgent data correction), limit it to under 10,000 records and use a separate job for the remainder during the next off-peak window.
