---
name: performance-testing-salesforce
description: "Use when planning or executing load tests, stress tests, or performance benchmarks against a Salesforce org. Covers Salesforce Scale Test, third-party tools (JMeter, BlazeMeter, k6), API throughput testing, Experience Page Time (EPT) measurement, and sandbox sizing for performance work. Triggers: 'load test Salesforce org', 'Scale Test Full Copy sandbox', 'EPT optimization', 'API concurrency limits', 'JMeter Salesforce performance'. NOT for Apex unit test performance assertions, LWC Jest tests, query optimization (see data/soql-query-optimization), or NFR definition (see architect/nfr-definition-for-salesforce)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Scalability
triggers:
  - "how do I run a load test against my Salesforce org"
  - "what is Salesforce Scale Test and how do I set it up"
  - "my Lightning pages are slow and I need to measure EPT before and after changes"
  - "how many concurrent API requests can Salesforce handle before throttling"
  - "which sandbox type do I need for performance testing"
tags:
  - performance-testing-salesforce
  - scale-test
  - load-testing
  - ept
  - api-throughput
  - jmeter
  - blazemeter
  - k6
  - sandbox-sizing
inputs:
  - "org edition and available sandbox types (Full Copy required for Scale Test)"
  - "target user concurrency and transaction mix"
  - "key business processes or pages to benchmark"
  - "current EPT baselines and performance NFRs"
  - "API integration volume and peak request rates"
outputs:
  - "performance test plan with scenarios, environment, and success criteria"
  - "load test script templates (JMeter, k6) for API and UI flows"
  - "EPT measurement checklist and optimization recommendations"
dependencies:
  - architect/nfr-definition-for-salesforce
  - devops/environment-strategy
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Performance Testing Salesforce

Activates when a practitioner needs to plan, execute, or interpret load tests, stress tests, or performance benchmarks against a Salesforce org. Covers the full lifecycle from environment selection through test design, execution with first-party (Scale Test) or third-party tools, and results interpretation with a focus on platform-specific constraints.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Sandbox type availability** — Scale Test requires a Full Copy sandbox. Developer and Developer Pro sandboxes have 200 MB storage limits and do not replicate production data volume or record distribution. Performance numbers from undersized sandboxes are meaningless.
- **API limit awareness** — The concurrent API request limit applies only to requests running longer than 20 seconds. Short-lived requests do not count toward the concurrency cap. The total daily API request limit is edition-dependent and shared across all integrations.
- **EPT baseline** — Experience Page Time (EPT) is the Salesforce-native metric for Lightning page load performance. The target is under 3 seconds. EPT is measured in the browser, not on the server, so network latency and client hardware affect results.

---

## Core Concepts

### Salesforce Scale Test

Scale Test is the first-party performance testing service from Salesforce. It runs synthetic load against a Full Copy sandbox to simulate user concurrency for Lightning UI flows. Scale Test is available at no additional cost for Enterprise, Unlimited, and Performance editions. Tests are requested through Salesforce Support and scheduled in coordination with the Scale Test team. Results include EPT measurements, server-side timings, and governor limit consumption per transaction.

Key constraints: Scale Test only runs against Full Copy sandboxes. It does not support API-only load generation. Test scenarios must be defined as UI-based user journeys. Maximum test duration and concurrency are coordinated per engagement.

### API Load Testing

For integration-heavy orgs, API throughput testing validates that REST, SOAP, Bulk, and Streaming API calls perform within acceptable bounds under production-like concurrency. The concurrent long-running request limit (default 25 for most editions) applies only to requests exceeding 20 seconds. The total API request limit is a 24-hour rolling window. API load tests should use authenticated sessions from a dedicated integration user with appropriate API permissions.

Third-party tools such as JMeter, k6, and BlazeMeter are the standard approach. Each test must include realistic authentication (OAuth 2.0 flows), proper session management, and representative payload sizes.

### Experience Page Time (EPT)

EPT measures the time from navigation start to the point where the page is interactive in Lightning Experience. Salesforce exposes EPT in the Lightning Usage App and via the EventLogFile (EPT event type). The EPT target of under 3 seconds applies to standard and custom Lightning pages. EPT is affected by component count, wire adapter calls, Apex controller round-trips, and third-party scripts loaded on the page.

---

## Common Patterns

### Pattern 1: Scale Test for UI Performance Baseline

**When to use:** Before a major release, org migration, or Lightning transition when you need to validate that UI performance meets NFRs under concurrent user load.

**How it works:**
1. Provision a Full Copy sandbox and ensure data volume matches production.
2. Open a Support case requesting Scale Test and provide target concurrency, key user journeys, and preferred test window.
3. Scale Test team configures synthetic users and runs the test during the scheduled window.
4. Review the results report for EPT distributions, server response times, and any governor limit warnings.
5. Address hotspots (slow Apex controllers, heavy LWC components, inefficient SOQL) and retest.

**Why not the alternative:** Third-party UI automation tools (Selenium, Playwright) do not execute inside the Lightning runtime the same way real users do, and they cannot produce EPT metrics natively. Scale Test uses Salesforce's own instrumentation.

### Pattern 2: API Throughput Testing with k6 or JMeter

**When to use:** When integrations are a significant part of the workload and you need to validate API response times and throughput under concurrent load.

**How it works:**
1. Identify the integration endpoints (REST, SOAP, Bulk API) and their expected peak concurrency.
2. Create test scripts that authenticate via OAuth 2.0 Connected App credentials (never hardcode passwords).
3. Ramp concurrency gradually: start at 10% of target, then 25%, 50%, 75%, 100%.
4. Monitor response times, HTTP status codes (watch for 429 and 503), and API usage via the API Usage Notification in Setup.
5. Correlate results with EventLogFile entries (API event type) for server-side timings.

**Why not the alternative:** Scale Test does not cover API-only workloads. Manual spot-checks with Postman or Workbench do not reveal concurrency-related degradation.

### Pattern 3: EPT Measurement and Optimization Cycle

**When to use:** When Lightning pages feel slow and you need data-driven evidence to prioritize optimizations.

**How it works:**
1. Enable the Lightning Usage App in Setup and review the EPT dashboard for baseline metrics.
2. Identify pages with EPT above 3 seconds.
3. Use Chrome DevTools Performance tab with the Lightning Extension to profile specific pages.
4. Reduce component count, defer non-critical wire calls, replace imperative Apex with cacheable wire adapters, and remove unused third-party scripts.
5. Remeasure EPT and compare against baseline.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Pre-release UI performance validation | Scale Test on Full Copy sandbox | First-party tool with native EPT instrumentation; no additional licensing |
| API integration throughput testing | k6 or JMeter against Full Copy or Partial Copy sandbox | Scale Test does not support API-only scenarios |
| Quick EPT spot-check on a single page | Lightning Usage App + Chrome DevTools | No test infrastructure needed; immediate feedback |
| Continuous performance regression detection | Automated k6 scripts in CI pipeline against scratch org or sandbox | Catch regressions early; integrate with existing DevOps tooling |
| Data volume testing for SOQL performance | Full Copy sandbox with production-scale data | Query performance is data-volume-dependent; small sandboxes hide problems |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Define performance NFRs** — Confirm EPT targets (under 3 seconds default), API response time SLAs, and peak concurrency expectations. Reference the `architect/nfr-definition-for-salesforce` skill if NFRs are not yet defined.
2. **Select the test environment** — Provision a Full Copy sandbox for realistic testing. Verify that data volume, sharing rules, and org configuration match production. Developer and Developer Pro sandboxes are not valid for performance testing.
3. **Design test scenarios** — Map critical user journeys (UI flows) and integration patterns (API calls) to test scripts. Include realistic think times and data variation. A test scenario that always reads the same record is not representative.
4. **Choose tooling** — Use Scale Test for UI concurrency validation. Use k6, JMeter, or BlazeMeter for API load testing. Use Lightning Usage App and Chrome DevTools for EPT profiling.
5. **Execute tests incrementally** — Ramp load gradually. Start at low concurrency to establish baseline, then increase to target. Monitor for HTTP 429 (rate limit) and 503 (service unavailable) responses.
6. **Analyze results and act** — Compare EPT and response times against NFRs. Investigate governor limit warnings. Address the top bottleneck first — typically slow Apex, heavy SOQL, or oversized LWC component trees.
7. **Retest and document** — After optimizations, retest at the same concurrency level. Document before/after metrics, environment details, and any platform limits encountered.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Performance NFRs are defined with specific, measurable targets (EPT < 3s, API p95 < 2s, etc.)
- [ ] Full Copy sandbox is provisioned and verified to have production-representative data volume
- [ ] Test scenarios cover both UI user journeys and API integration patterns
- [ ] OAuth 2.0 authentication is used in API test scripts (no hardcoded credentials)
- [ ] Load ramp-up is gradual, not a spike to full concurrency
- [ ] Results are compared against defined NFRs, not just "it didn't break"
- [ ] EventLogFile data (EPT and API event types) is reviewed for server-side confirmation
- [ ] Bottlenecks are documented with root cause and remediation actions

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Concurrent API limit applies only to long-running requests** — The 25-request concurrent limit (most editions) only counts requests that have been running for more than 20 seconds. Short-lived API calls do not consume concurrency slots. Teams often over-engineer throttling for fast endpoints based on a misunderstanding of this limit.
2. **Developer Pro sandbox is not a valid performance environment** — Developer Pro sandboxes have a 200 MB data storage cap and do not replicate production data volume, custom indexes, or sharing rule calculations. Performance numbers from Developer Pro are not transferable to production. Full Copy is the minimum for meaningful results.
3. **EPT is a client-side metric that varies by browser and network** — EPT measures time-to-interactive in the browser. The same page can show 1.5s EPT on a corporate LAN and 4.5s on a VPN connection. Always document the client environment alongside EPT measurements. Server-side response time (from EventLogFile) is the stable comparison point.
4. **Scale Test results include sandbox overhead** — Full Copy sandboxes may have slightly different performance characteristics than production due to infrastructure differences. Use Scale Test results for relative comparisons (before vs. after optimization) rather than absolute production predictions.
5. **API daily limit is shared across all integrations** — A load test consuming 100,000 API calls may exhaust the daily limit for the entire sandbox, blocking other development work. Schedule API load tests during off-hours and notify the team before running.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Performance test plan | Document specifying NFRs, test scenarios, environment requirements, tooling, and schedule |
| Load test scripts | k6 or JMeter scripts configured with OAuth auth, realistic payloads, and ramp-up profiles |
| EPT measurement report | Before/after EPT metrics by page with environment details and optimization actions taken |
| Results summary | Comparison of measured performance against NFRs with pass/fail status and bottleneck analysis |

---

## Related Skills

- `architect/nfr-definition-for-salesforce` — Use first to define measurable performance requirements before testing
- `devops/environment-strategy` — Use to plan sandbox allocation and determine which sandbox types are available for performance work
- `data/soql-query-optimization` — Use when performance testing reveals slow queries as a bottleneck
- `apex/apex-cpu-and-heap-optimization` — Use when Apex governor limits are hit during load testing
