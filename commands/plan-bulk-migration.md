# /plan-bulk-migration — Pick the right Salesforce integration pattern

Wraps [`agents/bulk-migration-planner/AGENT.md`](../agents/bulk-migration-planner/AGENT.md). Given a volume + latency + source + direction, returns an implementation plan selecting between Bulk API 2.0, Platform Events, Pub/Sub API, REST Composite, Salesforce Connect, Apex REST, or CDC.

---

## Step 1 — Collect inputs (ask all four upfront)

Ask:

```
1. Direction? inbound / outbound / bidirectional

2. Volume per run?
   Example: 8M records/week, 50k/day, real-time event stream

3. Latency tolerance?
   T+24h / T+1h / near-real-time (seconds) / sub-second

4. Source or target system?
   Example: SAP S/4HANA, Snowflake, Kafka, SFMC

Optional:
5. Does the integration require idempotency? (yes/no)
6. Expected error rate / PII handling needs?
7. Target-org alias for ground-truth lookups?
```

If any of the four required inputs is missing, STOP and ask all four.

---

## Step 2 — Load the agent

Read `agents/bulk-migration-planner/AGENT.md` fully + `integration-pattern-selection.md` + the integration skills it lists.

---

## Step 3 — Execute

Follow the 5-step plan:
1. Route via the decision tree → pick one pattern + note alternatives
2. Sketch the runtime (job/topic/endpoint specs, chunking, auth)
3. Idempotency + exactly-once strategy
4. Observability (`Application_Log__c`, Event Monitoring, alerts)
5. Rollout plan (dev → prod + feature flags + cutover)

---

## Step 4 — Deliver

- Executive summary: selected pattern + decision-tree branch
- Runtime spec (fenced code blocks for job / topic / endpoint definitions)
- Named Credential + Auth spec
- Idempotency strategy
- Observability plan
- Rollout plan
- Alternative patterns considered
- Citations

---

## Step 5 — Recommend follow-ups

- `/gen-tests` on any Apex scaffolds the plan produces
- `/scan-security` on the Named Credential and inbound endpoint
- `/score-deployment` before first production push

---

## What this command does NOT do

- Does not build the integration client — produces the spec.
- Does not create Named Credentials in the org.
- Does not recommend MuleSoft unless the decision tree routes there.
