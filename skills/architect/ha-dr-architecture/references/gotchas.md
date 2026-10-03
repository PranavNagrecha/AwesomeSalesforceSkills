# Gotchas — HA/DR Architecture

Non-obvious Salesforce platform behaviors that cause real problems in HA/DR design.
Each gotcha names its source. Claims that no fetched source confirms carry an inline `UNVERIFIED (date):` marker.

---

## Gotcha 1: Salesforce's 99.9% SLA Covers Infrastructure — Not Your Data

**What happens:** Architects read "99.9% uptime" and assume Salesforce guarantees full data recovery if something goes wrong. UNVERIFIED (2026-10-03): the 99.9% figure and the scope of the availability commitment are contractual and appear in no fetched Salesforce guide; read the order form and Main Services Agreement.

**When it occurs:** Business continuity plans that cite the uptime figure as the recovery plan.

**How to avoid:** Separate the availability commitment from data recovery and document both. A user or integration that deletes or overwrites records is not a platform outage. The Apex Developer Guide ("Deleting Records", "Restoring Deleted Records") gives a 15-day Recycle Bin window and nothing beyond it, so budget for a backup product if the org holds data that cannot be recreated.

---

## Gotcha 2: The Monitored Instance Key Can Change

**What happens:** Trust monitoring is set up against production (for example `NA152`) and a critical sandbox (for example `CS9`). UNVERIFIED (2026-10-03): earlier text said a sandbox refresh can provision the sandbox on a different instance; this is field experience, not documented in a fetched guide. If it happens, the monitor keeps polling the old instance and reports a healthy instance the org no longer uses.

**When it occurs:** After a sandbox refresh or creation, and after any instance migration Salesforce schedules.

**How to avoid:** Read the instance from the org instead of from a runbook constant. The Object Reference documents `Organization.InstanceName` (read-only, API 31.0 and later). Query it in the post-refresh runbook step and in the monitor's own startup check, and alert when it differs from the configured key.

---

## Gotcha 3: Event Bus Retention Is a Fixed Window, and Salesforce Does Not Retry

**What happens:** An integration uses Platform Events or Change Data Capture as a buffer. A subscriber that stays down longer than the retention window loses the events published before the outage. The Platform Events Developer Guide ("Event Retention in the Event Bus") stores high-volume platform event messages for 72 hours and legacy standard-volume messages for 24 hours. The Change Data Capture Developer Guide keeps change events for three days. *Integration Patterns and Practices* ("Remote Process Invocation—Fire and Forget") adds that platform events are published to the bus once with no Salesforce-side retry, so the subscriber must replay by replay ID.

**When it occurs:** Subscriber outages over a long weekend, or a middleware upgrade that takes longer than planned.

**How to avoid:** Store the last processed replay ID durably on the subscriber side. Alert when subscriber lag approaches the retention window. For integrations where a gap is unacceptable, add an external durable queue with configurable retention and a full re-sync procedure for gaps longer than the window.

---

## Gotcha 4: Native Data Export (Weekly CSV) Is Not a Backup Strategy

**What happens:** Organizations point to the native Data Export service (weekly CSV download) as their backup and calculate RPO from it. UNVERIFIED (2026-10-03): Data Export frequency, file coverage, and scheduling options are documented only in Salesforce Help, which this pass could not fetch.

**When it occurs:** Orgs without a backup product, or audits that accept "we export weekly" as an answer.

**How to avoid:** Treat Data Export as an emergency last resort. Re-importing CSV inserts new records (new IDs), loses relationships unless they are re-mapped, and runs automation on every row (see Gotcha 8). Use Salesforce Backup and Restore or a third-party tool as the primary backup mechanism, and size the restore against API limits (Gotcha 7).

---

## Gotcha 5: Hyperforce Does Not Equal Customer-Controlled Cross-Region Failover

**What happens:** An architect proposes Hyperforce migration as the HA/DR strategy, implying the customer can trigger cross-region failover during an outage. UNVERIFIED (2026-10-03): Hyperforce redundancy and failover behavior are described only in Salesforce Help and marketing material, not in a fetched guide.

**When it occurs:** Resilience reviews where infrastructure migration is offered as the answer to an availability requirement.

**How to avoid:** Set accurate expectations. Treat Hyperforce region selection as a data-residency and compliance decision. Build customer-controlled resilience at the integration and data layers, which is where the customer has controls.

---

## Gotcha 6: Big Object Archives Need Their Own Recovery Plan

**What happens:** An org archives historical records into big objects and assumes the backup tool covers them. UNVERIFIED (2026-10-03): earlier text said most backup tools, including Salesforce Backup and Restore, did not support big objects as of Spring '25; vendor coverage was not checked in this pass.

Correction (2026-10-03): earlier text said big objects are "append-only and cannot be updated or deleted via standard DML". The *Big Objects Implementation Guide* says standard DML is not used, but `Database.insertImmediate()` is idempotent and overwrites a record with the same index, and `Database.deleteImmediate()` deletes records in batches of up to 50,000. So big object data can be changed and lost, which makes recovery planning more important, not less. The guide also says big objects support only object and field permissions and do not run triggers, flows, or processes.

**When it occurs:** Archival designs that move data out of standard objects without moving the backup scope with it.

**How to avoid:** Back up the source data before archiving it into big objects. Confirm big object coverage with the backup vendor in writing before including it in RPO commitments. Because re-inserting is idempotent, a restore can replay the archive load safely.

---

## Gotcha 7: Restore Throughput Is Capped by a Shared Rolling Allocation

**What happens:** The DR plan promises a 4-hour RTO for a 120-million-row object. The *Salesforce Developer Limits and Allocations Quick Reference* ("Bulk API and Bulk API 2.0 Limits and Allocations") allows 15,000 batches per rolling 24-hour period, shared between Bulk API and Bulk API 2.0, and at most 150,000,000 records uploaded per rolling 24 hours. A restore competes with every other integration that uses the Bulk APIs that day.

**When it occurs:** RTO targets set before anyone calculated restore volume, and incidents where integrations keep loading during the restore.

**How to avoid:** Calculate RTO from record counts against the allocation, after subtracting normal daily integration usage. Pause or throttle non-critical bulk integrations during a restore. Restore in priority order (records users need first) and record that order in the runbook.

---

## Gotcha 8: A Restore Runs the Full Save Path

**What happens:** A backup tool re-inserts 50,000 deleted Cases. Every insert runs before-save flows, triggers, validation rules, duplicate rules, assignment and auto-response rules, workflow, after-save flows, and post-commit work such as email and queued async jobs. That is the order of execution in the Apex Developer Guide ("Triggers and Order of Execution"), and it applies to any insert, update, or upsert. Email alerts from workflow rules and flows go out for old cases, and integrations receive "new" records. (Whether API inserts also send auto-response emails depends on the request's email header settings; check before assuming either way.)

**When it occurs:** Any record-level restore through the API, including vendor backup tools.

**How to avoid:** Put a bypass mechanism in automation before you need it (a custom permission or setting that the restore user holds), and test the restore path with it in a sandbox. Restore with a dedicated integration user so the bypass and the audit trail are scoped to the restore.

---

## Gotcha 9: After 15 Days, a "Restore" Is a Re-Insert With New IDs

**What happens:** Records deleted more than 15 days ago are past the Recycle Bin window (Apex Developer Guide, "Restoring Deleted Records"). A backup tool can only re-insert them, and every re-inserted record gets a new record ID. External systems, reports, and URLs that stored the old IDs no longer resolve. Inside the window, `undelete` restores the original record.

**When it occurs:** Late discovery of a mass delete, or a corruption found in a quarterly audit.

**How to avoid:** Detect mass deletes fast (alert on delete volume) so recovery stays inside the 15-day window. Keep an external ID field on records that other systems reference, and have integrations match on it rather than on the Salesforce ID.

---

## Gotcha 10: Outbound Messaging Retries Stop After 24 Hours

**What happens:** A legacy integration uses outbound messaging and the receiver is down for two days. *Integration Patterns and Practices* says Salesforce retries for up to 24 hours with an exponentially increasing interval (15 seconds up to 60 minutes). The period can be extended to seven days by request to Salesforce Support, but automatic retries are limited to 24 hours. Failed messages then sit in a queue that administrators must monitor and retry manually.

**When it occurs:** Receiver outages longer than a day, often over weekends.

**How to avoid:** Put the outbound message queue on the incident runbook with an owner. Make the receiver idempotent on the message ID, which the same guide says stays constant across retries. For critical flows, move to an event pattern with a durable external queue.

---

## Gotcha 11: Instance Status "OK" Can Hide a Degraded Service

**What happens:** The monitor alerts only when the top-level `status` field is not `OK`. The Trust status API response for an instance (`https://api.status.salesforce.com/v1/instances/{key}/status`, checked 2026-10-03) also carries a `Services` list (for example `coreService`, `Communities`, `EinsteinBots`, `Agentforce`, `liveAgent`, `search`), plus `Incidents`, `Maintenances` and the instance `maintenanceWindow`. A degraded Experience Cloud or messaging service can sit under an instance that still reads `OK`.

**When it occurs:** Monitoring built from one example response that only checked the top-level field.

In the response checked on 2026-10-03, `Incidents` also contained resolved incidents (each entry has its own `status`, observed as `Resolved`, plus `serviceKeys` and `isCore`), and `Services` entries carried no health field at all. A monitor that pages on "incident count > 0" pages forever; one that reads `Services` for health finds nothing.

**How to avoid:** Monitor the services the org depends on, not just the instance. Page on incidents whose own `status` is not resolved and whose `serviceKeys` include a watched service (or that are `isCore`), and schedule against `Maintenances` and `maintenanceWindow`. The endpoint answered without authentication when checked; still give the poller a timeout and a fallback to the human-readable Trust site.
