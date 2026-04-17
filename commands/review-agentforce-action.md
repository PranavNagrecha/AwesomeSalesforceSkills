# /review-agentforce-action — Review Agentforce agent/action quality

Wraps [`agents/agentforce-action-reviewer/AGENT.md`](../agents/agentforce-action-reviewer/AGENT.md). Per-action A–F scorecard, topic coherence, guardrails gap list, observability and persona review.

---

## Step 1 — Collect inputs

```
1. Agent id or agent developer name?
2. Target org alias?
3. Review depth?  topic_only | per_action (default)
```

## Step 2 — Load the agent

Read `agents/agentforce-action-reviewer/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Fetch agent + topics + actions → per-action scoring → topic coherence → guardrails → persona + handoff → observability → remediation plan.

## Step 4 — Deliver the output

Summary, per-action scorecard, topic coherence table, guardrails gaps, observability + persona review, remediation plan, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/govern-prompt-library` for template sprawl
- `/catalog-integrations` if agent actions do callouts

## What this command does NOT do

- Does not modify agents, topics, actions, or prompts.
- Does not deploy or activate agents.
- Does not generate agent test data.
