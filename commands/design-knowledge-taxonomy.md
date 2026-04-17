# /design-knowledge-taxonomy — Design or audit Knowledge taxonomy

Wraps [`agents/knowledge-article-taxonomy-agent/AGENT.md`](../agents/knowledge-article-taxonomy-agent/AGENT.md). Produces data category groups, article-type/record-type plan, channel-audience matrix, and (audit) remediation queue.

---

## Step 1 — Collect inputs

```
1. Mode?  design | audit
2. Target org alias (audit)?
3. Audiences?  internal / customer / partner / public-web
4. Languages?  e.g. en_US, es, fr, ja
5. Article types (optional)?
```

## Step 2 — Load the agent

Read `agents/knowledge-article-taxonomy-agent/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Channel strategy → taxonomy → lifecycle → search/AI fit → (audit) remediation queue.

## Step 4 — Deliver the output

Summary, channel-audience matrix, taxonomy design, translation plan, search/AI notes, audit queue, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/migrate-approval-to-orchestrator` for authoring workflows
- `/review-agentforce-action` if agents cite Knowledge

## What this command does NOT do

- Does not author, import, translate, or delete articles.
- Does not wire Einstein Search.
- Does not migrate to external CMS.
