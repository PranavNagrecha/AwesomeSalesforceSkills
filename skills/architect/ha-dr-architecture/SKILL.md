---
name: ha-dr-architecture
description: "Designing high availability and disaster recovery strategies for Salesforce: Trust site monitoring, backup strategies, cross-region considerations, business continuity planning, RTO/RPO target definition, and failover patterns for integrations. Use when designing org resilience architecture, planning for outages, or defining recovery objectives. NOT for data backup mechanics (use salesforce-backup-and-restore). NOT for general security architecture (use security-architecture-review)."
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
  - how do I design for Salesforce outage scenarios
  - RTO and RPO targets for Salesforce org
  - integration failover pattern when Salesforce is down
  - Trust site monitoring and alerting setup
  - business continuity planning for Salesforce implementation
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# HA/DR Architecture

## Overview

Salesforce operates on a shared responsibility model for availability. Salesforce owns infrastructure redundancy, data-center operations, and platform uptime commitments. Customers own data resilience strategy, integration failover design, runbook documentation, and the definition of their own RTO and RPO targets.

Understanding where that boundary falls is the starting point for every HA/DR engagement.

---

## Salesforce's HA Model

Salesforce publishes a 99.9% monthly uptime SLA for production orgs on standard editions. Hyperforce deployments on applicable editions can access multi-region configurations, which improve physical redundancy but do not eliminate the shared responsibility boundary. Within a single instance, Salesforce uses redundant networking, active-active data replication across data centers, and automated failover at the infrastructure level — but customers cannot directly invoke infrastructure failover. Planned maintenance windows are published on the Trust site at least 48 hours in advance.

The Trust site (`trust.salesforce.com`) is the authoritative real-time status source. It provides per-instance status feeds, a public REST status API, and a subscription mechanism for email/SMS/webhook notifications. Any HA/DR plan that does not include automated Trust site monitoring is incomplete.

---

## Trust Site Monitoring

The Trust site exposes a JSON API at `https://api.status.salesforce.com/v1/instances/{instance}/status`. You can poll this endpoint from external monitoring systems, feed it into PagerDuty/OpsGenie, or use the webhook subscription feature to push alerts directly into incident management workflows. Operational runbooks should define the exact instance key(s) the org uses (e.g., `NA152`, `CS9`, or a Hyperforce pod identifier) and confirm these are not subject to silent change during sandbox refreshes.

Monitoring should cover: Production instance status, any sandbox instances used for integration testing, and — if applicable — Experience Cloud or Shield platform components with separate status codes.

---

## Backup Strategies

Salesforce's native Backup and Restore product (separate add-on purchase) provides daily full-org snapshots and record-level restore with selective restore by object, time range, and relationship. It is the only Salesforce-supported mechanism for record-level recovery within the Salesforce product suite.

Third-party tools — including OwnBackup (now Own Company), Veeam Backup for Salesforce, and Odaseva — extend this with more granular scheduling, cross-org restore, file/attachment backup, and compliance-grade audit logging. Selection criteria include retention requirements, file content coverage, restore granularity, and whether a full-org clone or record-level restore is the primary DR use case.

Metadata backup is a separate concern. The recommended approach is source-control-driven metadata management (SFDX, Salesforce CLI) with version history in Git. Metadata recovery from Git is faster and more reliable than attempting metadata export from a degraded org.

---

## RTO and RPO Definition

RTO (Recovery Time Objective) defines the maximum acceptable time from incident declaration to restored business operation. RPO (Recovery Point Objective) defines the maximum acceptable data loss window. Both are business-driven inputs that the architecture must then satisfy — they are not outputs from the platform.

Salesforce's native capabilities bound what is achievable. The daily Backup and Restore snapshot cadence means the platform RPO for record-level data loss is up to 24 hours without supplemental tooling. Third-party backup tools that run hourly or near-real-time can tighten this. For metadata, Git-backed continuous deployment with automated promote-on-merge can bring metadata RPO to near zero. RTO is constrained by restore speed (record counts, org governor limits), runbook execution time, and integration cutover time — not just backup frequency.

Document agreed RTO and RPO values for each major data category: records, metadata, files, integration state, and user authentication configuration.

---

## Hyperforce and Cross-Region Considerations

Hyperforce is Salesforce's next-generation infrastructure built on major public cloud providers (AWS, Azure, GCP). Applicable editions on Hyperforce can request data residency in specific regions. Hyperforce does not by default provide customer-controllable cross-region failover, but it does provide Salesforce-managed geographic redundancy within the infrastructure layer. When a customer's compliance requirements mandate data residency, Hyperforce region selection must be part of the HA/DR design — choosing a region that has a paired failover region on the same cloud provider is preferred where available.

---

## Integration Failover Patterns

Integrations are the most common HA/DR failure point because external systems assume Salesforce availability without circuit breakers.

**Circuit Breaker Pattern**: Middleware or an API gateway tracks Salesforce error rates. When errors exceed a threshold (e.g., 5xx rate > 20% over 60 seconds), the circuit opens and requests fail fast rather than queuing indefinitely. The circuit tests periodically and closes when Salesforce recovers. MuleSoft, Boomi, and major API management platforms have native circuit-breaker support.

**Fallback Queuing via Platform Events**: For outbound integrations calling external systems, Platform Events can serve as a reliable delivery buffer. If the external system is unavailable, events accumulate in the Pub/Sub API queue (up to 72 hours). For inbound integrations where Salesforce itself is unavailable, an external durable queue (AWS SQS, Azure Service Bus, MuleSoft Anypoint MQ) must buffer records until Salesforce recovers. This is the most important architectural control for inbound integration HA.

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
2. **Set up Trust site monitoring** — identify the org's instance key(s), configure automated polling or webhook subscription, and wire alerts into the incident management tool. Validate monitoring covers production and critical sandboxes.
3. **Define RTO and RPO by data category** — work with business stakeholders to assign target values for records, metadata, files, integration state, and authentication config. Map each target against current backup tooling capability and document gaps.
4. **Select and validate backup tooling** — confirm native Backup and Restore or a third-party tool is configured, test a record-level restore in a sandbox, and verify file/attachment coverage. Confirm metadata recovery via Git with a restore drill.
5. **Design integration failover patterns** — for each inbound and outbound integration, select a circuit-breaker and/or durable queue strategy. Document the recovery sequence (queue drain order, re-sync verification, idempotency checks).
6. **Write and test the DR runbook** — document the end-to-end recovery procedure from incident declaration through restored operations. Assign owners for each step. Run a tabletop exercise and update the runbook with findings.
7. **Review Hyperforce eligibility and region selection** — confirm whether the org is on Hyperforce, validate data-residency requirements, and ensure the selected region has adequate infrastructure redundancy for the org's compliance obligations.
