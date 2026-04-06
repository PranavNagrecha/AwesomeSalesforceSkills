# Performance Testing Salesforce — Work Template

Use this template when planning and executing performance tests for a Salesforce org.

## Scope

**Skill:** `performance-testing-salesforce`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Org edition:** (Enterprise / Unlimited / Performance)
- **Available sandbox types:** (Full Copy / Partial Copy / Developer Pro / Developer)
- **Production data volume:** (record counts for key objects)
- **Daily active users:** (concurrent user estimate at peak)
- **API integrations:** (list of integrations and estimated daily API call volume)
- **Known performance complaints:** (specific pages, flows, or endpoints reported as slow)

## Performance NFRs

| Metric | Target | Measurement Method |
|---|---|---|
| Lightning EPT (median) | < 3 seconds | Lightning Usage App |
| Lightning EPT (p90) | < 5 seconds | Lightning Usage App / EventLogFile |
| REST API response time (p95) | < 2 seconds | k6 / JMeter |
| Bulk API job completion | < 30 minutes for 1M records | Bulk API status polling |
| Zero governor limit breaches | 0 errors under load | EventLogFile / debug logs |

## Test Environment

- **Sandbox name:** _______________
- **Sandbox type:** Full Copy (required)
- **Last refresh date:** _______________
- **Data volume verified:** [ ] Yes — matches production within 10%
- **Custom indexes verified:** [ ] Yes — Support case confirmed replication
- **Sharing recalculation complete:** [ ] Yes — checked in Setup > Sharing Settings

## Test Scenarios

### UI Scenarios (for Scale Test)

| # | User Journey | User Mix % | Steps |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

### API Scenarios (for k6 / JMeter)

| # | Endpoint | Method | Concurrency Target | Payload Size |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |

## Tooling Selection

- [ ] Scale Test (UI concurrency) — Support case opened: _______________
- [ ] k6 (API load testing)
- [ ] JMeter (API load testing)
- [ ] BlazeMeter (cloud-hosted load testing)
- [ ] Lightning Usage App (EPT monitoring)
- [ ] Chrome DevTools (single-page profiling)

## Execution Schedule

| Phase | Date | Concurrency | Purpose |
|---|---|---|---|
| Baseline | | Low (10% target) | Establish baseline metrics |
| Ramp test | | 25% → 50% → 75% → 100% | Identify degradation curve |
| Sustained load | | 100% target for 30+ minutes | Validate NFRs under steady state |
| Post-optimization retest | | 100% target | Confirm improvements |

## Results Summary

| Metric | Baseline | Under Load | NFR Target | Pass/Fail |
|---|---|---|---|---|
| EPT (median) | | | | |
| EPT (p90) | | | | |
| API p95 response time | | | | |
| Governor limit errors | | | | |
| HTTP 429/503 errors | | | | |

## Bottlenecks Identified

| # | Component / Query | Issue | Remediation | Status |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |

## Notes

Record any deviations from the standard pattern and why.
