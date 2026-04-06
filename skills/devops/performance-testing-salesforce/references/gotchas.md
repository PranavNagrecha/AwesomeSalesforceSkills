# Gotchas — Performance Testing Salesforce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Concurrent API Limit Only Counts Requests Over 20 Seconds

**What happens:** Teams implement aggressive client-side throttling or request queuing because they believe each concurrent API call counts toward the 25-connection concurrency limit. In reality, only requests that have been running for more than 20 seconds are counted. Most REST API calls complete in under 5 seconds and never consume a concurrency slot.

**When it occurs:** During load test design when the team reads the "Concurrent API Request Limits" documentation without noticing the 20-second qualification. The result is artificially low concurrency targets that do not exercise the real bottleneck.

**How to avoid:** Read the full Salesforce API limits documentation. Design load tests that distinguish between short-lived requests (which are limited only by the daily total API limit) and long-running operations (Bulk API jobs, complex reports) which do count toward concurrency. Monitor HTTP 429 responses during the test to detect actual throttling rather than theoretical limits.

---

## Gotcha 2: Full Copy Sandbox May Not Have Custom Indexes

**What happens:** Custom indexes exist in production but are not automatically propagated to sandboxes, including Full Copy sandboxes. A query that uses a custom index in production falls back to a full table scan in the sandbox, producing artificially slow performance results that do not reflect production behavior.

**When it occurs:** After provisioning a Full Copy sandbox and running performance tests that involve SOQL queries on custom-indexed fields. The data is present (Full Copy includes data), but the index is not.

**How to avoid:** After provisioning a Full Copy sandbox, open a Support case to verify that production custom indexes are replicated. Compare query plans in the sandbox using the Query Plan tool in Developer Console against known production query plans. Document any index gaps in the performance test plan.

---

## Gotcha 3: Sharing Rule Recalculation Skews Sandbox Performance

**What happens:** Full Copy sandboxes include sharing rules and data, but sharing rule recalculation may not be complete after a sandbox refresh. During the recalculation window, record access checks are slower than normal, inflating response times. Teams attribute the slowness to application issues rather than infrastructure settling.

**When it occurs:** Immediately after a Full Copy sandbox refresh, especially in orgs with complex sharing rules, role hierarchies, or territory models. Recalculation can take hours to days depending on data volume and sharing complexity.

**How to avoid:** Wait for sharing rule recalculation to complete before running performance tests. Check recalculation status in Setup under Sharing Settings. Schedule sandbox refreshes far enough in advance of test windows to allow recalculation to finish.

---

## Gotcha 4: Scale Test Cannot Be Self-Scheduled

**What happens:** Teams assume they can trigger Scale Test on demand like a CI job. In reality, Scale Test engagements are coordinated through Salesforce Support with scheduling lead times. The Scale Test team configures the synthetic users and runs the test during the agreed window.

**When it occurs:** During sprint planning when the team allocates a 1-day story for "run Scale Test" without accounting for the Support case turnaround time, typically 1-2 weeks.

**How to avoid:** Open the Scale Test Support case at least 2-3 weeks before the desired test window. Include all scenario details in the initial request to minimize back-and-forth. Plan for at least two test cycles (baseline and post-optimization) and schedule both windows upfront.

---

## Gotcha 5: Lightning EPT Is Affected by Browser Extensions and VPN

**What happens:** EPT measurements taken on developer laptops show inconsistent or inflated numbers due to browser extensions (ad blockers, password managers, DevTools extensions), VPN overhead, or corporate proxy inspection. The same page shows 2s EPT on a clean browser and 5s EPT on a developer's daily browser.

**When it occurs:** During EPT profiling when different team members report different numbers for the same page, or when EPT measurements do not match Scale Test results.

**How to avoid:** Always measure EPT in an incognito/private browser window with all extensions disabled. Document the client environment (browser version, network path, geographic location) alongside every EPT measurement. Use the Lightning Usage App's server-side EPT aggregation as the authoritative source for trend analysis rather than individual browser measurements.
