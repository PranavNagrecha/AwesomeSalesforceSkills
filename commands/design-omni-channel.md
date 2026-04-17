# /design-omni-channel — Design or audit Omni-Channel routing

Wraps [`agents/omni-channel-routing-designer/AGENT.md`](../agents/omni-channel-routing-designer/AGENT.md). Produces queue + routing-config topology, capacity model, presence config, and (audit) findings.

---

## Step 1 — Collect inputs

```
1. Mode?  design | audit
2. Target org alias (required for audit)?
3. Channels?  case, chat, messaging, lead
4. Peak volume per channel (design only)?
5. Agent count by skill (design only)?
```

## Step 2 — Load the agent

Read `agents/omni-channel-routing-designer/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Capacity math → queue topology → presence config → bot handoff → (audit) live config cross-check.

## Step 4 — Deliver the output

Summary, capacity table, queue topology, presence design, handoff plan, audit findings, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/audit-case-escalation` for SLA + escalation coverage
- `/architect-perms` for Omni-Channel user + supervisor perms

## What this command does NOT do

- Does not deploy queues, routing configs, or presence configs.
- Does not build Einstein Bots.
- Does not size the service headcount.
