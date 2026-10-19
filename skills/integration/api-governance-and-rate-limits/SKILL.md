---
name: api-governance-and-rate-limits
description: "Monitor and govern Salesforce API consumption: per-user limits, org allocation, lightning-rest limits, and backoff. NOT for designing new endpoints — use security/api-security-and-rate-limiting."
category: integration
salesforce-version: "Summer '24+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "salesforce api limit exceeded"
  - "request limit exceeded 24 hour"
  - "rate limit integration user"
  - "api allocation dashboard"
  - "find out which integration is using up our daily API calls"
  - "handle REQUEST_LIMIT_EXCEEDED without a retry storm"
  - "cut API call volume by switching to composite or Bulk API"
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
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# API Governance and Rate Limits

Every org has a total inbound API request allocation per 24-hour period, set by edition and licences, plus a concurrency limit on long-running requests. The allocation is enforced against the aggregate of all API calls to the org, not per user, so one consumer's surge is every consumer's outage. This skill builds attribution (which app and user spend the allocation), a headroom gate for big jobs, a back-pressure client, and an escalation runbook.

---

## Before Starting

- Get the org's edition, licence counts, and any purchased API add-ons — they set the 24-hour total.
- List every integration with the connected app and user it authenticates as.
- Confirm someone holds View Event Log Object Data (for `ApiTotalUsageEventLog`) and View Setup and Configuration (for `/limits`).
- Collect the last incident: time, error code (`REQUEST_LIMIT_EXCEEDED`), and which jobs were running.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Does each integration have its own connected app and user? | The allocation is org-wide; attribution needs `ConnectedAppIdentifier` / `UserIdentifier` that differ per consumer (gotcha 3). | A per-consumer usage table from the first day. |
| Which APIs does each consumer call? | REST, SOAP, Bulk API, Bulk API 2.0, and most Connect REST APIs count toward the allocation; some Salesforce connected apps don't (gotcha 1). | A realistic consumption model instead of "Bulk is free". |
| Does any consumer use Composite Batch or loops of single-record calls? | `/composite` counts as one call; Composite Batch counts each subrequest (gotcha 2). | The right composite resource for each call pattern. |
| How long do the longest requests run? | More than 25 concurrent requests of 20 seconds or longer in production returns `REQUEST_LIMIT_EXCEEDED` (gotcha 4). | A concurrency cap in the middleware. |
| How do clients react to `REQUEST_LIMIT_EXCEEDED`? | The same code covers exhausted daily allocation (403) and concurrency; only one of them recovers by waiting seconds (gotcha 5). | A client that checks remaining allocation before retrying. |
| What alert thresholds and owners exist? | `/limits` is accurate within five minutes and API Usage Notifications email at a set percentage (gotcha 6). | 70% / 85% alerts with a named responder. |
| Is the org a paid production org, a sandbox, or Developer Edition? | Paid active orgs can go somewhat over the daily limit up to a hard cap; sandboxes, trials, and Developer Edition can't (gotcha 7). | Test-environment budgets that don't assume overage headroom. |

A governed integration estate adds per-consumer attribution, admission control for large jobs, and clients that read back-pressure, where "just raising the limit" buys more calls for the same uncontrolled consumer to burn.

---

## Core Concepts

### What the allocation is

| Item | Value (Summer '26 cheat sheet) |
|---|---|
| Developer Edition total per 24 h | 15,000 |
| Enterprise / Professional with API | 100,000 + licences × per-licence calls (Salesforce licence: 1,000) + add-ons |
| Unlimited / Performance | 100,000 + licences × per-licence calls (Salesforce licence: 5,000) + add-ons |
| Full sandbox (not from a template) | 5,000,000 |
| Concurrent requests ≥ 20 s | 25 (production and sandboxes), 5 (Developer Edition and trials) |
| Calls with `DebuggingHeader` | Separate 1,000 per 24 h |

Worked example from the guide: Enterprise Edition with 15 Salesforce licences = 100,000 + 15 × 1,000 = 115,000 calls. Calls from installed managed packages count against the org.

### Reading the meter

`GET /services/data/v67.0/limits/` returns `DailyApiRequests.Max` and `Remaining`, accurate within five minutes; avoid rapid or concurrent polling. Every REST response carries `Sforce-Limit-Info: api-usage=<used>/<limit>`. For attribution, `ApiTotalUsageEventLog` (API 61.0+) records Platform SOAP, REST, and Bulk API requests with `ConnectedAppIdentifier`, `UserIdentifier`, `ApiFamily`, and `IsApiLimitCounted`:

```soql
SELECT ConnectedAppIdentifier, UserIdentifier, ApiFamily, COUNT(Id) calls
FROM ApiTotalUsageEventLog
WHERE IsApiLimitCounted = true AND Timestamp = LAST_N_DAYS:1
GROUP BY ConnectedAppIdentifier, UserIdentifier, ApiFamily
ORDER BY COUNT(Id) DESC
LIMIT 20
```

Metadata XML: not applicable — governance here is runtime configuration, queries, and client code.

---

## Recommended Workflow

1. Answer the Questions table; give every consumer its own connected app and integration user.
2. Schedule a daily `/limits` read and the `ApiTotalUsageEventLog` query above; chart `Remaining` against `Max` and the top consumers.
3. Configure API Usage Notifications (Setup > API Usage Notifications) at 70% and 85% with named recipients.
4. Fix the top consumers: Bulk API 2.0 for volume, `/composite` (single call) instead of Composite Batch or loops, and the headroom guard from `references/examples.md` before large jobs.
5. Run `python3 skills/integration/api-governance-and-rate-limits/scripts/check_api_governance_and_rate_limits.py --manifest-dir <integration-repo>` — it ERRORs on `REQUEST_LIMIT_EXCEEDED` handling inside unbounded loops and WARNs on retry-on-429 logic, limit handling that never reads `/limits`, Composite Batch, and `/limits` polling faster than once a minute.
6. Write the escalation runbook: who opens the circuit breaker, who talks to partners, when to buy add-ons.

---

## Decision Guidance

| Situation | Approach | Why |
|---|---|---|
| Hundreds of thousands of rows | Bulk API 2.0 job | Requests count; rows don't each cost a call |
| Several related writes per business event | `/composite` | The whole series counts as one call |
| Independent reads batched together | Composite Batch only if 25 subrequests ≠ 25 separate needs | Each Composite Batch subrequest counts |
| `REQUEST_LIMIT_EXCEEDED` with allocation remaining | Exponential backoff with jitter, bounded | Concurrency clears as long requests finish |
| `REQUEST_LIMIT_EXCEEDED` with none remaining | Open the circuit breaker until the window moves | No retry can succeed |

---

## Review Checklist

- [ ] Each consumer has its own connected app and integration user
- [ ] `ApiTotalUsageEventLog` (or `EventLogFile` API Total Usage) attribution runs daily
- [ ] API Usage Notifications set at agreed thresholds
- [ ] Large jobs check headroom before starting
- [ ] Clients branch on remaining allocation before retrying `REQUEST_LIMIT_EXCEEDED`
- [ ] Composite Batch is not used where `/composite` would count once
- [ ] The checker exits 0 on integration code

---

## Salesforce-Specific Gotchas

Full list in `references/gotchas.md`. The two most misunderstood:

1. **Bulk API 2.0 counts** — it is in the list of APIs that count toward the allocation.
2. **The daily limit returns 403, not 429** — with error code `REQUEST_LIMIT_EXCEEDED`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Governance dashboard | `Remaining` vs `Max`, top consumers by app and user |
| Per-consumer quotas | Allocation share per integration, enforced in middleware |
| Headroom guard | Pre-flight check for large jobs |
| Escalation runbook | Thresholds, owners, circuit-breaker rules |

---

## Reference Files

| File | Use it for |
|---|---|
| `references/examples.md` | Overnight ETL at 95% of allocation; a back-pressure-aware client |
| `references/gotchas.md` | Seven allocation behaviours with avoidance steps |
| `references/llm-anti-patterns.md` | Limit-handling mistakes AI assistants make |
| `references/well-architected.md` | Pillar framing and the guide lines behind each claim |
| `references/monitoring-queries.md` | `/limits` response shape, attribution queries, and threshold arithmetic |

---

## Related Skills

- `security/api-security-and-rate-limiting` — designing new endpoints and their own rate limits
- `integration/mutual-tls-callouts` — outbound callout security from Salesforce
