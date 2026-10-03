# Examples — NFR Definition for Salesforce

## Example 1: Translating "must be fast" into testable performance NFRs

**Context:** A Service Cloud implementation for a 1,500-agent contact centre. The product owner's NFR document said "the system must be fast and responsive." The architecture review rejected it as untestable.

**Problem:** Without a specific metric, threshold, and measurement method, there is no way to verify the system meets the requirement before go-live or to detect regressions after deployment.

**Solution:**

```text
NFR-PERF-001: Lightning Record Page Load Time
  Metric:       Browser-side page load time (navigationStart to domContentLoadedEventEnd)
  Threshold:    p95 < 3 seconds, p99 < 5 seconds
  Method:       Browser Performance API instrumentation via custom LWC logging component
  Environment:  Full sandbox, 200 concurrent simulated users, representative data volume (5M cases)
  Owner:        Platform Architect
  Status:       Draft — pending sandbox availability

NFR-PERF-002: Case List View Render Time
  Metric:       Time to interactive for 2000-record list view
  Threshold:    p95 < 4 seconds
  Method:       Manual timing in Full sandbox with production-equivalent field count
  Environment:  Full sandbox
  Owner:        Platform Architect
  Status:       Draft
```

**Why it works:** Each NFR names a specific metric (not "responsiveness"), a percentile-based threshold (not "fast"), a measurement method that can be executed by a tester, and an environment qualifier that prevents false results from Developer Pro sandboxes.

---

## Example 2: Decomposing GDPR into per-control NFRs

**Context:** A Sales Cloud implementation for a European financial services firm. The compliance officer provided a single requirement: "The system must be GDPR compliant."

**Problem:** A single "must be GDPR compliant" NFR is unassignable, untestable, and will fail any compliance audit. Different reviewers will interpret it differently.

**Solution:**

```text
NFR-SEC-001: Right to Erasure Workflow
  Regulation:   GDPR Article 17
  Control:      Ability to erase all personal data for a named data subject within 30 days of request
  Salesforce Feature: Custom Flow + Apex batch to anonymise Contact, Lead, and related records
  Acceptance Criterion: Given a Subject Access Request, all personal data for that subject is
                        anonymised or deleted within 30 calendar days, verified by audit log
  Owner:        Data Protection Officer + Platform Architect

NFR-SEC-002: Consent Audit Log
  Regulation:   GDPR Article 7
  Control:      Immutable audit log of consent capture with timestamp, source, and version of consent text
  Salesforce Feature: Custom object + Field History Tracking or Event Monitoring
  Acceptance Criterion: Every consent record change is logged with actor, timestamp, old value,
                        new value — log is non-deletable by standard admin
  Owner:        Platform Architect

NFR-SEC-003: Data Residency
  Regulation:   GDPR Article 44–49 (international transfer restrictions)
  Control:      Personal data stored in EU-region Salesforce instance
  Salesforce Feature: EU region instance selection at org provisioning
  Acceptance Criterion: Org provisioned in EU datacenter, confirmed via trust.salesforce.com instance geography
  Owner:        Salesforce Account Executive + IT Operations
```

**Why it works:** Each NFR is traceable to a specific regulation article, names the Salesforce feature providing the control, and has an acceptance criterion that can be verified in a UAT environment.

---

## Example 3: Governor limit translation for a high-volume integration

**Context:** An integration team wants to sync 100,000 order records per hour from an ERP into Salesforce Opportunities using a REST API integration.

**Problem:** The team specified "integration must handle 100,000 records/hour" without verifying this against Salesforce API allocation limits.

**Solution:**

```text
Business target: 100,000 records/hour = ~28 records/second = 100,000 API calls/hour

Salesforce API allocation check (Limits Quick Reference, Total API Request Allocations):
  - Enterprise Edition with 100 Salesforce licenses:
    100,000 + 100 x 1,000 = 200,000 API calls per 24 hours (about 8,333 per hour)
    (corrected: an earlier version said ~1,000,000 per 24 hours)
  - 100,000 calls/hour = 2,400,000 calls/day = 1,200% of allocation: HARD CONSTRAINT VIOLATION

Resolution options documented in NFR:
  1. Bulk API 2.0 ingest jobs. Batches are created automatically; one job takes
     up to 150 MB of CSV (upload at most 100 MB to allow for base64 growth).
     100,000 rows of about 1 KB is one job per hour, a handful of API calls each.
     Ingest jobs consume batches from the 15,000-per-24-hours allocation shared
     with Bulk API. (Corrected: "up to 10,000 records" is the Bulk API 1.0 batch
     size, not a Bulk API 2.0 job limit.)
  2. Purchase additional API call allocation
  3. Reduce sync frequency and use delta sync instead of full refresh

NFR-SCALE-001: ERP Integration Throughput
  Metric:       Records processed per hour via ERP sync
  Threshold:    ≥ 100,000 records/hour without exceeding 80% of daily API allocation
  Method:       Bulk API v2 upsert jobs; monitor via API Usage report and Salesforce Limits API
  Environment:  Full sandbox for throughput; budget against production's allocation,
                because a Full sandbox has a flat 5,000,000-call allocation
  Owner:        Integration Architect
  Status:       Draft — Bulk API v2 approach selected, confirmed with API allocation calculation
```

**Why it works:** The NFR is grounded in actual Salesforce API allocation limits, shows the calculation, and records the architectural decision (Bulk API v2) that satisfies the NFR within platform constraints.

---

## Anti-Pattern: Setting availability NFRs against Salesforce's infrastructure SLA

**What practitioners do:** They write "System availability: 99.9% uptime" and point to the Salesforce Trust SLA as evidence the NFR is already satisfied.

**What goes wrong:** Salesforce's 99.9% SLA covers infrastructure — datacenter, network, and platform services. It does not cover:
- Custom Apex code that throws unhandled exceptions
- Scheduled jobs that fail due to governor limits
- Integration endpoints going down
- Admin errors (bad deployments, deleted fields, record type misconfiguration)
- Data recovery after bulk delete accidents

A production incident caused by a deployed Apex bug that disables case creation for two hours is not covered by the Salesforce SLA. If the business's availability NFR means "agents can create cases 99.9% of the time," that is a customer-owned application availability requirement — and it must be addressed with test automation, deployment gates, and monitoring.

**Correct approach:** Split the availability NFR into two explicit rows:
1. Infrastructure availability: governed by the customer's contract and monitored on trust.salesforce.com, referenced but not team-owned. UNVERIFIED (2026-10-03): the 99.9% figure quoted above was not found in a fetched source.
2. Application availability — team-owned, with RPO/RTO and monitoring approach defined.

---

## Example 4: An NFR Register Excerpt With Its Measurement Sources, For A 1,500-Agent Service Cloud Rollout

**Context:** Unlimited Edition org, 1,500 Service Cloud users, Event Monitoring licensed, one ERP integration and one telephony integration. The register lives at `docs/nfr/nfr-register.md` and is the go-live gate.

**The register excerpt:**

| Id | Category | Metric | Threshold | Measurement source and environment | Owner |
|---|---|---|---|---|---|
| NFR-PERF-001 | Performance | Effective Page Time of the Case record page | p95 < 3,000 ms, p99 < 5,000 ms over 7 days | `EFFECTIVE_PAGE_TIME` from the Lightning Page View event log in production; browser timing in a Full sandbox before go-live | Platform Architect |
| NFR-SCALE-001 | Scalability | Inbound API calls per 24 hours, all integrations | < 80% of production allocation (100,000 + 1,500 x 5,000 = 7,600,000) | `DailyApiRequests` from REST `/limits`, sampled hourly | Integration Architect |
| NFR-SCALE-002 | Scalability | Concurrent inbound requests of 20 s or longer | Peak <= 10 (platform limit 25) | Integration middleware metrics; API errors with `REQUEST_LIMIT_EXCEEDED` = 0 | Integration Architect |
| NFR-SCALE-003 | Scalability | Child records per parent | No Account with more than 10,000 Contacts or Cases | Weekly aggregate query (below) | Data Architect |
| NFR-AVAIL-001 | Availability | Application RTO after a failed deployment | Case creation restored within 30 minutes | Rollback rehearsal in Full sandbox each release | Release Manager |
| NFR-BATCH-001 | Scalability | Nightly entitlement recalculation | Completes 01:00 to 04:00 local; starter is Schedulable, work runs as Batch Apex | Apex job history (`AsyncApexJob`) | Platform Architect |

**Measurement artifacts.** Find the page-view logs for NFR-PERF-001 (requires View Event Log Files and API Enabled):

```soql
SELECT Id, EventType, LogDate, LogFileFieldNames
FROM EventLogFile
WHERE EventType = 'LightningPageView' AND LogDate = LAST_N_DAYS:7
ORDER BY LogDate DESC
```

The `LogFile` field holds base64-encoded CSV whose columns are listed in `LogFileFieldNames`; compute the percentiles from the `EFFECTIVE_PAGE_TIME` column. Export the files, because Event Monitoring logs are not durable.

Read the allocation for NFR-SCALE-001:

```bash
curl https://MyDomainName.my.salesforce.com/services/data/v67.0/limits/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" -H "X-PrettyPrint:1"
# Response includes: "DailyApiRequests": { "Max": ..., "Remaining": ... }
```

Check skew for NFR-SCALE-003:

```soql
SELECT AccountId, COUNT(Id) contacts
FROM Contact
GROUP BY AccountId
HAVING COUNT(Id) > 10000
```

UNVERIFIED (2026-10-03): an aggregate over every Contact can exceed query time limits in a large data volume org; run it in a Full sandbox or with Bulk API 2.0 query if it times out.

**The decision it forced**, recorded at `docs/adr/0017-entitlement-recalc-batch.md`:

```markdown
# ADR-0017: Run entitlement recalculation as Batch Apex, started by a thin Schedulable

## Status
Accepted (2026-10-03), Design Authority

## Context
- NFR-BATCH-001 needs 2.4 million Cases recalculated inside 01:00 to 04:00.
- The current Schedulable class does the work itself. Scheduled Apex runs
  under synchronous limits: 10,000 ms CPU, 100 SOQL queries, 6 MB heap.
- Daily async Apex allocation: 250,000 or licences x 200; here
  1,500 x 200 = 300,000 executions.

## Decision
The Schedulable only calls Database.executeBatch(new EntitlementRecalcBatch(), 200).
Each batch execution gets asynchronous limits (60,000 ms CPU, 200 queries, 12 MB heap).

## Consequences
- 12,000 batch executions per night against a 300,000 daily allocation.
- Recalculation is no longer one transaction; partial completion must be
  visible in AsyncApexJob and alerted.

## Date
2026-10-03
```

UNVERIFIED (2026-10-03): the ADR counts each batch `execute` chunk as one execution against `DailyAsyncApexExecutions`; the Apex Guide lists batch Apex among counted executions but this revision did not confirm the per-chunk counting rule.

**Why it works:** each row names a metric, a threshold, a measurement source that exists in this org, and an owner. The figures come from the limits documents rather than memory: the allocation formula, the 25-request concurrency limit, the 10,000-child skew guidance, and the synchronous limits on scheduled Apex.

