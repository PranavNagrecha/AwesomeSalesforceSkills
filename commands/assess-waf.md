# /assess-waf — Well-Architected Framework assessment

Wraps [`agents/waf-assessor/AGENT.md`](../agents/waf-assessor/AGENT.md). Scores the org across the five WAF pillars (Trusted, Easy, Adaptable, Resilient, Composable), surfaces top risks per pillar, produces a remediation backlog.

---

## Step 1 — Collect inputs

```
1. Target org alias?
2. Workload?  e.g. "sales cloud + CPQ + agentforce"
3. NFRs (optional)?  availability, RTO/RPO, peak TPS
4. Scope pillars (optional)?  default: all 5
```

## Step 2 — Load the agent

Read `agents/waf-assessor/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Workload confirmation → per-pillar probes → scoring → NFR gap analysis → backlog.

## Step 4 — Deliver the output

Summary, 5-pillar scorecard, NFR sheet, pillar findings, remediation backlog, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/audit-sharing`, `/catalog-integrations`, `/plan-release-train`, `/design-sandbox-strategy` — one per pillar gap

## What this command does NOT do

- Does not remediate (backlog only).
- Does not certify against WAF formally.
- Does not run Salesforce Optimizer (different tool).
