# OmniStudio Scalability Patterns — Architecture Review Template

Use this template when designing or reviewing an OmniStudio deployment for high-volume concurrent usage.

## Scope

**Skill:** `omnistudio-scalability-patterns`

**Request summary:** (fill in what the practitioner or user asked for)

**Review date:** YYYY-MM-DD

---

## 1. Concurrency Baseline

| Parameter | Value | Notes |
|---|---|---|
| Peak concurrent users (portal) | | |
| Average IP execution time (seconds) | | |
| Maximum observed IP execution time (seconds) | | |
| IPs with execution time > 20s under load? | Yes / No | If Yes: triggers concurrent Apex limit concern |
| Other Apex workloads during portal peak hours | | Batch jobs, scheduled classes, triggers |
| Estimated concurrent long-running Apex requests at peak | | Must remain below 25 org-wide |

---

## 2. Integration Procedure Async Mode Audit

List all Integration Procedures invoked under portal load:

| IP Name | Current Execution Mode | Governor Limit Pressure? | Recommended Mode | Notes |
|---|---|---|---|---|
| | Synchronous / Fire-and-Forget / IP Chainable / Queueable Chainable | Yes / No | | |
| | | | | |
| | | | | |

**Async mode decision rules:**
- UI blocking only (no limit pressure): fire-and-forget
- Governor limit pressure (SOQL/CPU/heap): Queueable Chainable
- Modularity with no limit pressure: IP Chainable
- Read-heavy on Spring '25+ LWR org: Direct Platform Access

---

## 3. Direct Platform Access Assessment

| Check | Status | Notes |
|---|---|---|
| Org is on Spring '25+ | Yes / No | Required for DPA |
| Experience Cloud site is on LWR runtime | Yes / No | Required for DPA |
| Read-heavy IPs identified (DataRaptor Extracts, SOQL-only) | Yes / No | DPA candidates |
| Write operations in candidate IPs? | Yes / No | If Yes: DPA applies only to read steps |
| DPA enabled on eligible IPs | Yes / No / N/A | |

**IPs recommended for DPA enablement:**

| IP Name | Read-Only? | DPA Enabled? | Expected CPU Reduction |
|---|---|---|---|
| | | | |
| | | | |

---

## 4. LWR + CDN Configuration

| Check | Status | Notes |
|---|---|---|
| Experience Cloud site runtime | LWR / Aura | LWR required for high-volume |
| CDN caching enabled (site Administration) | Yes / No | |
| Static assets confirmed serving from CDN edge | Yes / No | Verify via browser devtools or CDN dashboard |
| Page time-to-first-byte under load (with CDN) | ms | Target: < 200ms for cached pages |
| Page time-to-first-byte under load (without CDN) | ms | For baseline comparison |

**Risk flag:** If site is on Aura runtime, CDN page caching is not available. High-volume deployment requires LWR migration before go-live.

---

## 5. Caching Strategy

| IP Name | Cache Type | TTL (seconds) | Cache Key Inputs | User-Specific Data? | Approved? |
|---|---|---|---|---|---|
| | IP-level / DataRaptor Extract / None | | | Yes / No | Yes / No |
| | | | | | |
| | | | | | |

**Caching safety rule:** IP-level caching must NOT be enabled for Integration Procedures that return user-specific or account-specific data without a user-context cache key. Verify: would two different users with the same input parameters always receive the same correct response?

---

## 6. API Limit Management

| Concern | Current State | Mitigation |
|---|---|---|
| Total concurrent long-running Apex at peak | / 25 | |
| HTTP callout volume (external APIs) | requests/hour | |
| DataRaptor caching for high-frequency reference queries | Enabled / Not enabled | |
| Batch jobs scheduled during portal peak hours | Yes / No | Reschedule if Yes |

---

## 7. MuleSoft Escalation Criteria

Document the thresholds at which the team will escalate from OmniStudio Integration Procedures to MuleSoft middleware:

| Signal | Threshold | Current State | Action |
|---|---|---|---|
| Peak concurrent sessions | > ___ simultaneous users | | |
| External APIs aggregated per IP | > ___ external systems per IP | | |
| Response time SLA | < ___ms under full load | | |
| External API rate limit breaches | Any | | |

**Decision:** Escalate to MuleSoft? Yes / No / Review at ___

---

## 8. Risk Summary

| Category | Risk Level | Key Finding | Recommended Action | Owner | Target Date |
|---|---|---|---|---|---|
| Concurrent Apex limit | Low / Medium / High / Critical | | | | |
| Async execution mode correctness | Low / Medium / High / Critical | | | | |
| Direct Platform Access coverage | Low / Medium / High / Critical | | | | |
| LWR + CDN deployment | Low / Medium / High / Critical | | | | |
| Caching configuration | Low / Medium / High / Critical | | | | |
| MuleSoft escalation readiness | Low / Medium / High / Critical | | | | |

**Risk levels:**
- Critical: ceiling breach likely at projected peak
- High: ceiling breach possible; requires mitigation before go-live
- Medium: headroom exists but should be monitored
- Low: no near-term concern

---

## 9. Notes and Deviations

Record any deviations from standard patterns documented in SKILL.md and the reason for each deviation:

- 
- 

## 10. Sign-Off

| Role | Name | Date | Approved |
|---|---|---|---|
| Integration Architect | | | Yes / No |
| Platform Architect | | | Yes / No |
| Release Manager | | | Yes / No |
