# Examples — HA/DR Architecture

Concrete worked examples of HA/DR design decisions in Salesforce contexts.

---

## Example 1: Inbound Integration Buffer for an ERP-to-Salesforce Order Sync

**Context:** A manufacturing company syncs order records from SAP to Salesforce every 15 minutes via a REST callout. During a Salesforce instance maintenance window, the SAP middleware retried indefinitely, creating a backlog of 40,000 failed requests.

**HA/DR Solution Applied:**
- Azure Service Bus queue added between SAP and the Salesforce REST endpoint.
- Middleware writes to the queue first; a separate consumer reads from the queue and upserts to Salesforce.
- Consumer implements exponential backoff when Salesforce returns 503 or 429.
- Queue TTL set to 72 hours — matching the Platform Event retention window for symmetry.
- Trust site webhook feeds into PagerDuty; when the instance goes into "Maintenance" status the consumer pauses automatically and resumes when status returns to "OK".

**Result:** Zero order records lost during the next planned maintenance window. Queue depth was monitored and drained within 8 minutes of Salesforce recovery.

---

## Example 2: RPO Gap Analysis for a Financial Services Org

**Context:** A wealth management firm stated an RPO of 4 hours for client account records. The org was using weekly Salesforce data export (CSV). The gap between the stated RPO and actual capability was 164 hours.

**HA/DR Solution Applied:**
- OwnBackup configured with hourly incremental backup for Account, Contact, Opportunity, and custom financial objects.
- Files and attachments included in the backup scope (previously excluded).
- Restore SLA tested in sandbox: 10,000 records restored in under 35 minutes.
- New effective RPO for records: 1 hour. Gap closed.
- Metadata captured via CI/CD pipeline on every deployment; effective metadata RPO: near zero.

**Key Lesson:** Never accept a stakeholder's stated RPO without mapping it to the current backup cadence. The gap is almost always larger than assumed.

---

## Example 3: Circuit Breaker for a Salesforce-to-Workday Outbound Integration

**Context:** A Salesforce Flow triggered an Apex callout to Workday on every Opportunity close. When Workday entered a maintenance window, the callout failures caused Flow errors that blocked Opportunity updates for 200 sales reps.

**HA/DR Solution Applied:**
- Callout moved from synchronous Flow Apex action to an asynchronous Queueable job.
- Custom Setting stores circuit breaker state: `CLOSED`, `OPEN`, `HALF_OPEN`.
- A scheduled job checks Workday health endpoint every 5 minutes and updates the Custom Setting.
- The Queueable job reads the Custom Setting; if `OPEN`, it publishes a Platform Event to a retry queue instead of attempting the callout.
- Retry queue is processed in sequence when state returns to `CLOSED`.

**Result:** Workday maintenance windows no longer surface as errors to end users. Retry queue drains automatically after Workday recovers.

---

## Example 4: Trust Site Monitoring Integration with PagerDuty

**Context:** A SaaS company discovered a production Salesforce outage 45 minutes after it started because users reported it via Slack before ops noticed.

**HA/DR Solution Applied:**
- Cron job on external monitoring host polls `https://api.status.salesforce.com/v1/instances/NA152/status` every 60 seconds.
- If `status` field is not `OK`, fires a PagerDuty high-urgency alert with the incident summary URL.
- PagerDuty on-call rotation notified within 60 seconds of status change.
- Runbook linked directly in the PagerDuty alert body.

**Key Lesson:** The Trust site API is unauthenticated and fast. There is no excuse for manual Trust site monitoring in any production environment.
