---
name: ha-dr-architecture
description: "Designing high availability and disaster recovery strategies for Salesforce: Trust site monitoring, backup strategies, cross-region considerations, business continuity planning, RTO/RPO target definition, and failover patterns for integrations. Use when designing org resilience architecture, planning for outages, or defining recovery objectives, or when asked to write a Salesforce DR runbook. NOT for picking a backup product or restore mechanics — use data/salesforce-backup-and-restore. NOT for a security posture review — use architect/security-architecture-review."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - high-availability
  - disaster-recovery
  - business-continuity
  - rto-rpo
  - trust-site
inputs:
  - Salesforce org edition and Hyperforce eligibility
  - Integration topology (inbound/outbound systems)
  - Business RTO and RPO requirements
  - Current backup tooling in use
  - On-call and incident response process maturity
outputs:
  - HA/DR architecture decision record
  - RTO/RPO target definition and gap analysis
  - Trust site monitoring and alerting plan
  - Integration failover pattern recommendations
  - DR runbook outline
  - Business continuity planning checklist
triggers:
  - "how do I design for Salesforce outage scenarios"
  - "RTO and RPO targets for Salesforce org"
  - "integration failover pattern when Salesforce is down"
  - "Trust site monitoring and alerting setup"
  - "business continuity planning for Salesforce implementation"
  - "write a disaster recovery runbook for our Salesforce org"
  - "calculate how long a full restore of our biggest object would take"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# HA/DR Architecture

## Overview

Salesforce operates on a shared responsibility model for availability. Salesforce owns infrastructure redundancy, data-center operations, and platform uptime commitments. Customers own data resilience strategy, integration failover design, runbook documentation, and the definition of their own RTO and RPO targets.

Understanding where that boundary falls is the starting point for every HA/DR engagement.

---

## Questions to Ask Before Configuring

Ask these before writing targets or picking tools. Each traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What a proper design adds over just doing it |
|---|---|---|---|
| "What RTO and RPO does each data category need, and who signed them off?" | Targets drive everything; the uptime figure is not a recovery plan (Gotcha 1) | A signed table of targets per records, files, metadata, integration state | Tooling is chosen against targets, not targets reverse-engineered from tooling |
| "How many rows are in the largest objects, and how much Bulk API allocation do integrations use daily?" | Restore throughput is capped at 15,000 batches and 150M records per rolling 24 hours, shared (Gotcha 7) | A restore-time calculation per object | An RTO that the platform can actually meet |
| "What happens when a restore re-inserts records: which automation must not run?" | A restore runs the full save path (Gotcha 8) | A bypass design and a restore user | Recovery does not email customers or re-trigger integrations |
| "Which external systems store Salesforce record IDs?" | After 15 days a restore is a re-insert with new IDs (Gotcha 9) | External ID fields and integration matching rules | Integrations survive a late restore |
| "How long can each subscriber or receiver be down, and how does it catch up?" | Event retention is 24 or 72 hours (three days for CDC) and outbound messaging retries stop at 24 hours (Gotchas 3 and 10) | Per-integration lag alerts and re-sync procedures | Outages longer than the window have a documented recovery |
| "Which instance and which services does the org depend on?" | Instance keys can change and service-level degradation hides under an "OK" instance (Gotchas 2 and 11) | `Organization.InstanceName` checks and a service list for monitoring | Alerts fire for the services users actually touch |

What a proper design adds over "just buying a backup tool": recovery targets that the platform's limits can meet, restores that do not re-run business automation, and integrations that can catch up after an outage longer than the event retention window.

---

## Salesforce's HA Model

Salesforce publishes a 99.9% monthly uptime SLA for production orgs on standard editions. Hyperforce deployments on applicable editions can access multi-region configurations, which improve physical redundancy but do not eliminate the shared responsibility boundary. Within a single instance, Salesforce uses redundant networking, active-active data replication across data centers, and automated failover at the infrastructure level — but customers cannot directly invoke infrastructure failover. Planned maintenance windows are published on the Trust site at least 48 hours in advance. UNVERIFIED (2026-10-03): the SLA figure, the replication and failover description, and the 48-hour notice are contractual or Help-only claims not found in a fetched source. What is verifiable: the Trust status API returns each instance's `maintenanceWindow` and a `Maintenances` list.

The Trust site (`trust.salesforce.com`) is the authoritative real-time status source. It provides per-instance status feeds and a public REST status API (verified 2026-10-03). UNVERIFIED (2026-10-03): the subscription mechanism for email, SMS, and webhook notifications was not checked in this pass. Any HA/DR plan that does not include automated Trust site monitoring is incomplete.

---

## Trust Site Monitoring

The Trust site exposes a JSON API at `https://api.status.salesforce.com/v1/instances/{instance}/status`. A request on 2026-10-03 returned, without authentication, the instance `status`, `maintenanceWindow`, a `Services` list (for example `coreService`, `Communities`, `EinsteinBots`, `Agentforce`), and `Incidents` and `Maintenances` arrays. You can poll this endpoint from external monitoring systems, feed it into PagerDuty/OpsGenie, or use the webhook subscription feature (UNVERIFIED 2026-10-03) to push alerts directly into incident management workflows. Alert on the services the org depends on, not only on the top-level status. Operational runbooks should define the exact instance key(s) the org uses (e.g., `NA152`, `CS9`, or a Hyperforce pod identifier) and confirm these are not subject to silent change during sandbox refreshes. Read the key from `Organization.InstanceName` (Object Reference) rather than from a runbook constant.

Monitoring should cover: Production instance status, any sandbox instances used for integration testing, and — if applicable — Experience Cloud or Shield platform components with separate status codes.

---

## Backup Strategies

Salesforce's native Backup and Restore product (separate add-on purchase) provides daily full-org snapshots and record-level restore with selective restore by object, time range, and relationship. It is the only Salesforce-supported mechanism for record-level recovery within the Salesforce product suite. UNVERIFIED (2026-10-03): the product's cadence and restore options are documented only in Salesforce Help, which this pass could not fetch. The platform's own recovery window is the 15-day Recycle Bin (Apex Developer Guide, "Restoring Deleted Records").

Third-party tools — including OwnBackup (now Own Company), Veeam Backup for Salesforce, and Odaseva (vendor capabilities UNVERIFIED 2026-10-03) — extend this with more granular scheduling, cross-org restore, file/attachment backup, and compliance-grade audit logging. Selection criteria include retention requirements, file content coverage, restore granularity, and whether a full-org clone or record-level restore is the primary DR use case.

Metadata backup is a separate concern. The recommended approach is source-control-driven metadata management (SFDX, Salesforce CLI) with version history in Git. Metadata recovery from Git is faster and more reliable than attempting metadata export from a degraded org.

---

## RTO and RPO Definition

RTO (Recovery Time Objective) defines the maximum acceptable time from incident declaration to restored business operation. RPO (Recovery Point Objective) defines the maximum acceptable data loss window. Both are business-driven inputs that the architecture must then satisfy — they are not outputs from the platform.

Salesforce's native capabilities bound what is achievable. The daily Backup and Restore snapshot cadence (UNVERIFIED 2026-10-03, see above) means the platform RPO for record-level data loss is up to 24 hours without supplemental tooling. Third-party backup tools that run hourly or near-real-time can tighten this. For metadata, Git-backed continuous deployment with automated promote-on-merge can bring metadata RPO to near zero. RTO is constrained by restore speed (record counts, org governor limits), runbook execution time, and integration cutover time — not just backup frequency. The hard ceiling on restore speed is the Bulk API allocation: 15,000 batches and 150,000,000 records per rolling 24 hours, shared between Bulk API and Bulk API 2.0 (*Salesforce Developer Limits and Allocations Quick Reference*). Every restored record also runs the full save path, so automation cost slows the restore further.

Document agreed RTO and RPO values for each major data category: records, metadata, files, integration state, and user authentication configuration.

---

## Hyperforce and Cross-Region Considerations

UNVERIFIED (2026-10-03): this section rests on Salesforce Help and marketing pages that this pass could not fetch.

Hyperforce is Salesforce's next-generation infrastructure built on major public cloud providers (AWS, Azure, GCP). Applicable editions on Hyperforce can request data residency in specific regions. Hyperforce does not by default provide customer-controllable cross-region failover, but it does provide Salesforce-managed geographic redundancy within the infrastructure layer. When a customer's compliance requirements mandate data residency, Hyperforce region selection must be part of the HA/DR design — choosing a region that has a paired failover region on the same cloud provider is preferred where available.

---

## Integration Failover Patterns

Integrations are the most common HA/DR failure point because external systems assume Salesforce availability without circuit breakers.

**Circuit Breaker Pattern**: Middleware or an API gateway tracks Salesforce error rates. When errors exceed a threshold (e.g., 5xx rate > 20% over 60 seconds), the circuit opens and requests fail fast rather than queuing indefinitely. The circuit tests periodically and closes when Salesforce recovers. MuleSoft, Boomi, and major API management platforms have native circuit-breaker support.

**Fallback Queuing via Platform Events**: For outbound integrations calling external systems, Platform Events can serve as a reliable delivery buffer. If the external system is unavailable, events stay on the event bus for the retention window: 72 hours for high-volume platform events, 24 hours for legacy standard-volume events (Platform Events Developer Guide), and three days for change events (Change Data Capture Developer Guide). Salesforce publishes each event once and does not retry; the subscriber replays from its last stored replay ID (*Integration Patterns and Practices*). For inbound integrations where Salesforce itself is unavailable, an external durable queue (AWS SQS, Azure Service Bus, MuleSoft Anypoint MQ) must buffer records until Salesforce recovers. This is the most important architectural control for inbound integration HA.

**Read Replica Pattern**: For reporting and analytics workloads, Salesforce Connect external objects or Data Cloud replication can serve as a read path that survives partial org degradation. This is not a full substitute for org availability but protects business intelligence workloads.

---

## Business Continuity Planning Checklist

- Define RTO and RPO for each data category and integration stream.
- Confirm Trust site monitoring is automated with runbook-integrated alerting.
- Confirm backup tooling covers records, files, and attachments.
- Confirm metadata is version-controlled in Git with automated retrieve.
- Document integration circuit-breaker configurations and test them quarterly.
- Document inbound integration buffer strategies and test drain procedures.
- Identify which Salesforce features have no offline fallback (CPQ quoting, real-time approvals) and design compensating business processes.
- Assign named incident commander role and documented escalation chain.
- Schedule annual DR tabletop exercise with integration partners.
- Validate sandbox refresh procedures do not inadvertently alter production instance monitoring references.

---

## Recommended Workflow

1. **Establish the shared responsibility boundary** — document which HA controls Salesforce owns (infrastructure failover, data-center redundancy, SLA commitments) versus which the customer must build (data backup, integration failover, runbooks, RTO/RPO definition).
2. **Set up Trust site monitoring** — read the org's instance key from `Organization.InstanceName`, poll the status API for the instance and the services the org depends on, and wire alerts into the incident management tool. Validate monitoring covers production and critical sandboxes.
3. **Define RTO and RPO by data category** — work with business stakeholders to assign target values for records, metadata, files, integration state, and authentication config. Map each target against current backup tooling capability and document gaps.
4. **Select and validate backup tooling** — confirm native Backup and Restore or a third-party tool is configured, calculate restore time against the Bulk API allocation, test a record-level restore in a sandbox with the automation bypass on, and verify file/attachment coverage. Confirm metadata recovery via Git with a restore drill.
5. **Design integration failover patterns** — for each inbound and outbound integration, select a circuit-breaker and/or durable queue strategy. Document the recovery sequence (queue drain order, re-sync verification, idempotency checks).
6. **Write and test the DR runbook** — document the end-to-end recovery procedure from incident declaration through restored operations. Assign owners for each step. Run a tabletop exercise and update the runbook with findings.
7. **Review Hyperforce eligibility and region selection** — confirm whether the org is on Hyperforce, validate data-residency requirements, and ensure the selected region has adequate infrastructure redundancy for the org's compliance obligations.
