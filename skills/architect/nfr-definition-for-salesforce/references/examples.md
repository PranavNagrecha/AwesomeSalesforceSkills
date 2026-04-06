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

Salesforce API allocation check:
  - Enterprise Edition with 100 licenses: ~1,000,000 API calls/24hr = ~41,666 calls/hour
  - 100,000 calls/hour = 240% of allocation → HARD CONSTRAINT VIOLATION

Resolution options documented in NFR:
  1. Batch upsert using Bulk API v2 (reduces API call count — up to 10,000 records per job)
     → 100,000 records / 10,000 per job = 10 Bulk API jobs/hour (well within limits)
  2. Purchase additional API call allocation
  3. Reduce sync frequency and use delta sync instead of full refresh

NFR-SCALE-001: ERP Integration Throughput
  Metric:       Records processed per hour via ERP sync
  Threshold:    ≥ 100,000 records/hour without exceeding 80% of daily API allocation
  Method:       Bulk API v2 upsert jobs; monitor via API Usage report and Salesforce Limits API
  Environment:  Production-equivalent (Bulk API not restricted in Full sandbox)
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
1. Infrastructure availability — governed by Salesforce Trust SLA (99.9%), referenced but not team-owned.
2. Application availability — team-owned, with RPO/RTO and monitoring approach defined.
