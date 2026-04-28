---
name: shield-event-log-retention-strategy
description: "Use when designing Salesforce Shield Event Monitoring retention, SIEM routing, and storage-tier strategy — which event types to keep, for how long, where, and how to answer audit queries across hot/warm/cold tiers. Triggers: 'shield event log retention', 'route event monitoring to splunk', 'how long to keep login history', 'siem salesforce integration', 'event monitoring storage tier'. NOT for enabling Shield (see salesforce-shield-deployment)."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "how long to keep event monitoring logs"
  - "route shield events to siem"
  - "splunk salesforce shield integration"
  - "event log cold storage tier"
  - "audit retention policy salesforce"
tags:
  - security
  - shield
  - event-monitoring
  - retention
  - siem
inputs:
  - "event types currently emitted and their volume"
  - "regulatory retention requirements"
  - "SIEM or log-storage target"
outputs:
  - "per-event retention policy"
  - "hot/warm/cold tier plan"
  - "SIEM routing and search strategy"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Shield Event Log Retention Strategy

Salesforce Shield Event Monitoring emits dozens of event types — login, API, report export, URI, lightning performance, Apex execution — and each has its own volume, value, and retention implication. The default Shield retention is short (typically 30 days for Event Monitoring log files); the default volume is high; the default search experience is slow. Teams that do not design a retention strategy end up either paying to keep everything forever, or losing audit evidence exactly when they need it.

A working strategy assigns each event type to a retention tier (hot for recent investigation, warm for routine audit, cold for regulatory retention), picks a routing target (Splunk, Sentinel, Datadog, native Big Objects), and writes a query runbook so auditors can answer "did X happen" without re-ingesting cold data.

---

## Before Starting

- List the Event Monitoring event types enabled in the org.
- Estimate daily volume per type (rows and bytes).
- List regulatory retention rules that apply (SOX, HIPAA, FedRAMP, industry-specific).
- Confirm SIEM target and its ingestion cost model.

## Core Concepts

### Event Value Tiers

| Tier | Examples | Retention |
|---|---|---|
| **High-value** | Login, LoginAs, APITotalUsage, ReportExport, RestApi | 1-7 years depending on regulation |
| **Medium-value** | ApexExecution, ApexCallout, VisualforceRequest | 90-365 days |
| **Low-value** | URI, LightningPageView | 30-90 days |
| **Very-low-value** | LightningInteraction, LightningPerformance | 7-30 days |

### Storage Tiers

1. **Hot** — queryable from your SIEM directly. Typical retention: 30-90 days. Cost dominates here.
2. **Warm** — archived to cheaper storage (S3, Azure Blob) with a re-hydration path. Typical retention: 1-2 years.
3. **Cold** — immutable object storage with legal-hold support. Typical retention: 5-7+ years.

### Routing Paths

- **Event Monitoring Analytics App** — built-in dashboards, short retention.
- **Pull via Event Log File API** — hourly batch pull into SIEM; standard path.
- **Push via Streaming** — real-time event bus subscription; higher cost.
- **Big Objects** — in-platform archive for long-retention data.

### The Query Runbook

A retention strategy is incomplete without a query runbook — documented steps to answer audit questions against each tier. Without it, cold storage is theoretically compliant and practically useless.

---

## Common Patterns

### Pattern 1: SIEM Hot + Object Storage Cold

Event Log Files pulled hourly into the SIEM for 60 days of hot retention; nightly export to S3 (or equivalent) for 7-year cold retention. Queries ≤ 60 days run in SIEM; older queries trigger an Athena (or equivalent) scan.

### Pattern 2: Split By Event Type

High-value events go to a long-retention SIEM index; low-value events go to a short-retention index or are discarded. Cuts SIEM cost dramatically.

### Pattern 3: Big Objects For Regulatory Audit

Use Salesforce Big Objects to archive high-value events in-platform. Auditors can query without leaving Salesforce; no SIEM round-trip.

### Pattern 4: Streaming For Real-Time Detection

Subscribe to the real-time event bus for Login, LoginAs, and any event that feeds fraud detection or anomaly alerting. Batch ELF stays as the archival source.

### Pattern 5: Sampling For Very-Low-Value Events

Keep a 10% sample of LightningInteraction for UX debugging; drop the rest. Useful when full retention would balloon ingest.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Regulated industry, long audit retention | SIEM hot + object storage cold | Cost-effective compliance |
| Real-time fraud / anomaly detection | Streaming + SIEM correlation | Detection lag matters |
| Cost-sensitive org | Split by event value + sample low-value | Largest SIEM savings |
| In-platform audit preferred | Big Objects for high-value events | Simpler auditor experience |
| Multi-region / sovereignty | Regional SIEM indices | Data residency |

## Review Checklist

- [ ] Each event type has a retention tier.
- [ ] SIEM ingestion cost is modeled and monitored.
- [ ] Cold tier is immutable / legal-hold ready.
- [ ] Query runbook exists and was tested against a real audit question.
- [ ] Regulatory rules are mapped to the retention policy.
- [ ] Sampling strategy (if any) is documented.

## Recommended Workflow

1. Enumerate event types and their volumes.
2. Classify each event by value tier.
3. Select retention per tier (aligned with regulation).
4. Design storage-tier architecture (hot / warm / cold).
5. Implement the hourly pull and archive pipeline.
6. Write the query runbook; test against a sample audit question.

---

## Salesforce-Specific Gotchas

1. Default Event Monitoring log-file retention is short; do not assume the platform keeps logs for audits.
2. Event Log File API emits hourly; gaps happen — monitor for missing intervals.
3. Big Objects have no standard SOQL reporting UI; Auditors must be trained or tooling built.
4. Some event types are off by default; "Shield" doesn't mean "every event on."
5. Real-time event bus events have their own retention (shorter) — not a substitute for ELF.

## Proactive Triggers

- Retention < regulatory minimum → Flag Critical.
- No cold tier for high-value events → Flag High.
- SIEM ingest cost > 30% of security budget → Flag Medium. Consider splitting.
- No query runbook → Flag High.
- Event Monitoring enabled but no event types selected → Flag High.

## Output Artifacts

| Artifact | Description |
|---|---|
| Retention matrix | Event type → tier → retention |
| Routing architecture | Pull/push, hot/warm/cold topology |
| Query runbook | Steps per common audit question |

## Related Skills

- `security/event-monitoring` — enabling Shield Event Monitoring.
- `security/salesforce-shield-deployment` — Shield deployment overall.
- `security/security-incident-response` — incident runbook.
- `data/big-objects-for-audit-archive` — Big Object archive patterns.
