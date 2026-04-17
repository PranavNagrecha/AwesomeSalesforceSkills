# /build-apex — Generate an Apex scaffold for any canonical surface

Wraps [`agents/apex-builder/AGENT.md`](../agents/apex-builder/AGENT.md). Produces Apex class(es) + test class that conform to `templates/apex/` (TriggerHandler, BaseService, BaseSelector, ApplicationLogger, SecurityUtils, HttpClient).

---

## Step 1 — Collect inputs

Ask the user:

```
1. What Apex surface do you need? (trigger+handler | service | selector | domain |
   controller | batch | queueable | schedulable | invocable | rest | soap |
   pe-subscriber | cdc-subscriber | iterator | async-continuation)

2. Primary sObject or functional area?
   Example: "Account", "Order fulfillment", "/external/billing endpoint"

3. Description of behavior (3+ sentences — drives field/method design)?

4. Test-class strategy? (default: TestDataFactory + positive/negative/bulk)
```

If the description is under 3 sentences or the surface is ambiguous, STOP and clarify.

---

## Step 2 — Load the agent

Read `agents/apex-builder/AGENT.md` + all mandatory reads (apex-trigger-framework, apex-service-selector-domain, apex-security-crud-fls, apex-bulkification, apex-testing-patterns, plus templates under `templates/apex/`).

---

## Step 3 — Execute the plan

Follow the agent's plan: choose surface → pick template → generate scaffold → wire SecurityUtils + ApplicationLogger → generate matching test class.

---

## Step 4 — Deliver the output

- Summary + confidence
- Apex class(es) (fenced ```apex blocks, one per file)
- Matching test class (≥ 90% coverage target, bulk + negative cases)
- Deployment order + any dependency notes
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/gen-tests` if coverage needs deepening
- `/optimize-soql` if the scaffold issues SOQL
- `/scan-security` before deploy
- `/consolidate-triggers` if a trigger scaffold overlaps an existing trigger

---

## What this command does NOT do

- Does not deploy.
- Does not run tests against a live org.
- Does not modify existing Apex — use `/refactor-apex` for that.
