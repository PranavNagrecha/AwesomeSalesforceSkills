# Examples — OmniStudio Scalability Patterns

## Example 1: Portal SOQL Limit Errors Fixed With Queueable Chainable

**Scenario:** A healthcare payer portal built on OmniStudio + Experience Cloud serves 600 concurrent member users during peak enrollment periods. A key OmniScript — "View My Benefits Summary" — invokes an Integration Procedure that queries MemberPlan, CoverageBenefitItem, and ClaimLine across 3 SOQL calls. Under load, the IP occasionally fails with `Too many SOQL queries: 101` errors when combined with trigger-side SOQL from concurrent record saves.

**Problem:** The IP was running synchronously within the OmniScript transaction. Each of the 600 concurrent user sessions competed for the same Apex governor pool. When triggers on related objects consumed additional SOQL from the shared 100-query budget, the IP tipped into limit violations.

**Solution:** The DataRaptor queries within the IP were restructured into a dedicated Integration Procedure step configured as Queueable Chainable. The Queueable step runs in a fresh async Apex transaction with its own 100 SOQL quota — completely isolated from the concurrent user trigger stack.

```json
// Integration Procedure step configuration (OmniStudio Designer — Step Properties)
{
  "Type": "IntegrationProcedure",
  "StepName": "FetchBenefitsSummary",
  "ExecutionMode": "QueueableChainable",
  "NextStepOnSuccess": "RenderBenefitsUI",
  "NextStepOnError": "ShowErrorMessage"
}
```

**Why it works:** Queueable Chainable runs each designated IP step as a Salesforce Queueable Apex job. The job receives a completely fresh governor context: 100 SOQL, 150 DML, 60,000ms CPU, 12MB heap. It does not share the originating OmniScript's transaction budget. SOQL limit errors under concurrency are eliminated because the heavy query work runs outside the shared synchronous transaction pool.

---

## Example 2: Read-Heavy Integration Procedure CPU Reduction With Direct Platform Access

**Scenario:** A utilities company's self-service portal (Spring '25 org, LWR site) has an Integration Procedure that performs 5 DataRaptor Extract operations to build a dashboard view: account details, service agreements, billing history, active cases, and product entitlements. Under 400 concurrent users, CPU time on this IP averages 7,200ms — approaching the 10,000ms synchronous limit. Page load times degrade noticeably.

**Problem:** Each DataRaptor Extract routes through the Apex runtime, accumulating CPU time toward the synchronous limit. The IP is read-only — no DML, no callouts — so it is a perfect candidate for Direct Platform Access mode.

**Solution:** Enable Direct Platform Access in the Integration Procedure's execution settings. All 5 DataRaptor Extract steps now execute via native platform data access, bypassing Apex CPU governor accumulation.

Additionally, IP-level output caching is configured with a 10-minute TTL for the account details and product entitlements steps (which change rarely) while billing history and active cases remain uncached (high churn).

```
// OmniStudio IP Execution Settings (Designer → Properties → Execution Settings)
Direct Platform Access: ENABLED
Cache Output: ENABLED
Cache TTL (seconds): 600  // 10 minutes for reference-data-heavy outputs
```

**Why it works:** DPA moves the data access layer outside the Apex CPU governor loop. The IP no longer accumulates CPU time for read operations, so the 10,000ms ceiling becomes a non-issue. Under 400 concurrent users, average CPU time drops to under 200ms (the residual Apex overhead for IP orchestration). The caching layer further reduces database load by serving cached responses to users making identical requests within the TTL window.

---

## Anti-Pattern: Using Fire-and-Forget to "Fix" Governor Limit Errors

**What practitioners do:** An Integration Procedure starts hitting `Too many SOQL queries: 101` errors under portal concurrency. The architect adds `useFuture: true` (fire-and-forget) to the IP, expecting it to "run separately" and escape the limit.

**What goes wrong:** Fire-and-forget (`useFuture: true`) runs the IP as a future Apex method. Future Apex has the same SOQL limit (100 per transaction) as synchronous Apex. The governor limit error continues to occur — now asynchronously, surfacing as a silent failure that is harder to debug because the error no longer reaches the OmniScript UI directly. The user sees a blank result or timeout rather than a clear error.

**Correct approach:** When governor limits are the constraint, use Queueable Chainable — not fire-and-forget. Queueable Chainable runs the offending step in a Queueable Apex context, which has identical SOQL and DML limits but higher CPU and heap. For SOQL limit relief specifically, restructure the IP to consolidate queries, use DataRaptor Extracts with caching, or move the query-heavy steps to a single Queueable Chainable step with a clean transaction budget.

Fire-and-forget is the right choice only when the goal is to remove UI blocking for an operation whose duration is acceptable but whose governor limits are not the problem.
