---
name: salesforce-shield-deployment
description: "Roll out Shield (Platform Encryption + Event Monitoring + Field Audit Trail) end-to-end, sequencing feature enablement to avoid data lockout. NOT for Classic Encryption or general PE design."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "shield rollout plan"
  - "enable event monitoring"
  - "field audit trail retention"
  - "shield encryption field by field"
tags:
  - shield
  - encryption
  - event-monitoring
  - fhr
inputs:
  - "Shield license"
  - "scoped field list"
  - "log retention SLA"
outputs:
  - "Rollout runbook with order of operations"
  - "validation report"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Salesforce Shield Deployment

Shield bundles Platform Encryption, Event Monitoring (RTEM + log files), and Field Audit Trail. Deployment order matters: encrypt fields first (with key) → turn on audit trail → onboard log consumers. This skill lays out the sequence, the gotchas for SOQL filters, and retention policy targets.

## When to Use

Initial Shield enablement, or expanding coverage to a new object. Not for day-2 tweaks (see encryption-key-rotation).

Typical trigger phrases that should route to this skill: `shield rollout plan`, `enable event monitoring`, `field audit trail retention`, `shield encryption field by field`.

## Recommended Workflow

1. Confirm Shield license + Tenant Secret strategy (platform or BYOK).
2. Encrypt fields one object at a time; pause for SOQL regression (filter on encrypted fields requires deterministic mode).
3. Turn on Field Audit Trail policies — set retention per regulatory requirement (up to 10 years).
4. Subscribe log consumer (Splunk / Sumo / S3 via Event Monitoring Analytics App) to RealTimeEventMonitoring streams.
5. Rehearse an incident: pull LoginEventStream for a user, correlate with SetupAuditTrail, prove end-to-end visibility.

## Key Considerations

- Deterministic vs. probabilistic encryption affects SOQL queryability.
- Event Monitoring EventLogFile is hourly/daily; RealTime is streaming — wire both for completeness.
- Field Audit Trail consumes storage; plan archive pipeline to S3 for long-term retention.
- Event Monitoring + Shield require different licenses; confirm before planning.

## Worked Examples (see `references/examples.md`)

- *PCI program Shield rollout* — Retailer with PAN tokenized externally but transaction amounts must be encrypted at rest.
- *Zero-trust log monitoring* — Fraud detection team needs suspicious login alerts.

## Common Gotchas (see `references/gotchas.md`)

- **SOQL LIKE on probabilistic encrypted field** — Returns zero rows silently.
- **Unbounded FHR storage** — Storage bill balloons.
- **Real-time events dropped** — Consumer lagging.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Turning on Shield without a SOQL regression pass
- Never rehearsing an incident log pull
- Buying Shield but never onboarding to SIEM

## Official Sources Used

- Apex Developer Guide — Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security.htm
- Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Session Security Levels — https://help.salesforce.com/s/articleView?id=sf.security_hap_session.htm
- CSP and Trusted URLs — https://help.salesforce.com/s/articleView?id=sf.security_csp_overview.htm
- API Only User Profile — https://help.salesforce.com/s/articleView?id=sf.users_profiles_api_only.htm
- Privacy Center and DSR — https://help.salesforce.com/s/articleView?id=sf.privacy_center_overview.htm
