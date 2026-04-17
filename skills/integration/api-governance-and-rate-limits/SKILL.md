---
name: api-governance-and-rate-limits
description: "Monitor and govern Salesforce API consumption: per-user limits, org allocation, lightning-rest limits, and backoff. NOT for designing new endpoints."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "salesforce api limit exceeded"
  - "request limit exceeded 24 hour"
  - "rate limit integration user"
  - "api allocation dashboard"
tags:
  - api-limits
  - governance
  - rate-limit
inputs:
  - "API usage report"
  - "problematic consumer"
outputs:
  - "governance dashboard + per-consumer throttling + allocation plan"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# API Governance and Rate Limits

Salesforce orgs have a 24-hour API allocation (varies by license). Hitting it halts all integrations. This skill builds a governance dashboard (API usage by consumer), a throttling pattern for heavy consumers, and an escalation runbook when usage trends toward limits.

## When to Use

Orgs with 10+ integrations or periodic '24-hour limit exceeded' incidents.

Typical trigger phrases that should route to this skill: `salesforce api limit exceeded`, `request limit exceeded 24 hour`, `rate limit integration user`, `api allocation dashboard`.

## Recommended Workflow

1. Pull `/services/data/v60.0/limits/` daily; record `DailyApiRequests.Max` and `Remaining`.
2. Attribute usage via EventLogFile `ApiTotalUsage` events — per user/consumer-key.
3. Identify top 3 consumers; review whether Bulk API 2.0 or Composite API could replace per-row calls.
4. Implement throttling on heaviest consumer (token bucket in the middleware layer, not in Salesforce).
5. Set 70% / 85% alerts; escalate at 85%.

## Key Considerations

- Bulk API 2.0 jobs are not counted in the REST 24h allocation (separate bucket).
- Composite API collapses N calls to 1 from the allocation standpoint.
- Platform Events and Pub/Sub have separate limits.
- LWC `@wire` calls count toward user limits — be careful with auto-refresh.

## Worked Examples (see `references/examples.md`)

- *Throttle heavy ETL* — ETL hit 95% at 3am
- *Composite for UI* — LWC needed 5 parallel fetches

## Common Gotchas (see `references/gotchas.md`)

- **Auto-refresh LWC** — Open dashboard burns 1000 calls/hour per user.
- **Retry storms on 429** — Doubles consumption.
- **Anonymous allocation** — Can't tell who is burning it.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Shared integration user across consumers
- No allocation dashboard
- Retry without backoff

## Official Sources Used

- Apex REST & Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Connect REST API — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/
- Private Connect — https://help.salesforce.com/s/articleView?id=sf.private_connect_overview.htm
- Bulk API 2.0 — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/
- Pub/Sub API — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/intro.html
