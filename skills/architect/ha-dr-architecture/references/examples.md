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
- Trust site webhook feeds into PagerDuty; when the instance goes into "Maintenance" status the consumer pauses automatically and resumes when status returns to "OK". (UNVERIFIED 2026-10-03: a Trust webhook subscription was not confirmed in this pass; polling the status API, as in Example 4, achieves the same pause.)

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

---

## Example 5: DR Decision Record With Restore-Time Math for a Service Cloud Org

**Context:** A utility's Service Cloud org (Enterprise Edition) holds 18 million `Case` rows, 41 million `EmailMessage` rows and 6 million `Account` rows. A CTI vendor and a billing system both store Salesforce `Case` IDs. A nightly ETL uses about 2,000 Bulk API batches per day. Leadership asked for "4-hour RTO, 1-hour RPO" for cases.

**Decision record (machine-readable form):**

```yaml
adr: DR-004
title: Case recovery targets and the restore path
status: proposed
date: 2026-10-03
targets_requested: {Case: {rto_hours: 4, rpo_hours: 1}}
platform_constraints:
  bulk_allocation: 15,000 batches and 150,000,000 records per rolling 24h, shared Bulk API + Bulk API 2.0
  recycle_bin_days: 15            # undelete keeps original IDs inside this window
  event_retention: {platform_event_high_volume: 72h, platform_event_standard_volume: 24h, change_data_capture: 3 days}
  outbound_messaging_retry: 24h automatic (extendable to 7 days via Support)
restore_math:
  case_rows: 18,000,000
  batches_needed_at_10k: 1,800      # well inside 15,000 minus the ETL's ~2,000
  allocation_bound: met              # allocation is not the bottleneck for Case
  observed_sandbox_rate: 1.1M rows/hour with automation bypass on, 0.3M rows/hour with it off
  estimated_full_case_restore: ~16h  # 18M / 1.1M per hour
decision:
  rto_hours: {Case_last_90_days: 4, Case_full: 24}   # negotiated tiering, signed by service director
  rpo_hours: 1                                         # hourly incremental backup of Case and EmailMessage
  restore_user: dr_restore integration user holding custom permission Bypass_Automation
  id_strategy: External_Case_Key__c on Case; CTI and billing match on it, not on the Salesforce Id
  monitoring:
    instance_key_source: Organization.InstanceName (checked at monitor start and after each refresh)
    services_watched: [coreService, liveAgent, ServiceCloudVoice, Communities]
consequences:
  - restores older than 15 days produce new Case Ids; partner systems re-link through External_Case_Key__c
  - ETL pauses during a declared restore to protect the shared batch allocation
  - quarterly drill restores 500,000 cases into a full-copy sandbox and records the rate
```

**Monitoring poller (external host, runs every 60 seconds).** It uses only fields observed in the status API response on 2026-10-03: the instance `status`, and for each entry in `Incidents` its `status` (resolved incidents stay in the list, observed as `"Resolved"`), `serviceKeys`, and `isCore`. `Services` entries carried only `key`, `order` and `isCore`, with no per-service health field, so service health comes from the incidents that name the service.

```bash
#!/usr/bin/env bash
# Poll the Salesforce Trust status API for one instance and the services we depend on.
# INSTANCE comes from Organization.InstanceName, refreshed by the post-refresh runbook step.
set -euo pipefail
INSTANCE="${INSTANCE:?set from Organization.InstanceName}"
WATCH='["coreService","liveAgent","ServiceCloudVoice","Communities"]'
json=$(curl -sf --max-time 10 "https://api.status.salesforce.com/v1/instances/${INSTANCE}/status") \
  || { echo "ALERT: Trust API unreachable for ${INSTANCE}"; exit 2; }
status=$(jq -r '.status' <<<"$json")
[ "$status" = "OK" ] || echo "ALERT: ${INSTANCE} status=${status}"
# Open incidents only: the Incidents array also holds resolved ones.
jq -r --argjson watch "$WATCH" '
  .Incidents[]?
  | select(.status != "Resolved")
  | select(.isCore or ([.serviceKeys[]?] | any(. as $k | $watch | index($k))))
  | "ALERT: open incident \(.id) type=\(.type) services=\([.serviceKeys[]?] | join(","))"
' <<<"$json"
```

> UNVERIFIED (2026-10-03): the full set of incident `status` values was not documented in a fetched source; only `"Resolved"` was observed. The filter treats anything else as open, which errs toward paging.

**Why it works:** the RTO was negotiated from measured restore rates and the shared allocation, not from the vendor brochure; the restore path cannot email customers or re-trigger the CTI integration; and partner systems survive a restore that has to create new IDs.

