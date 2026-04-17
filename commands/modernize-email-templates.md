# /modernize-email-templates — Audit and plan email template modernization

Wraps [`agents/email-template-modernizer/AGENT.md`](../agents/email-template-modernizer/AGENT.md). Classifies Classic vs Lightning vs Enhanced LEX templates, flags Visualforce risks, produces migration plan.

---

## Step 1 — Collect inputs

```
1. Scope?  folder:<DeveloperName>  OR  org
2. Target org alias?
```

## Step 2 — Load the agent

Read `agents/email-template-modernizer/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Inventory templates, classify by engine, score each, merge-field validation, attachment audit, emit migration plan.

## Step 4 — Deliver the output

Summary, classification table, per-template findings, migration plan, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/build-flow` for flows that reference deprecated templates
- `/analyze-field-impact` for fields used only by soon-to-retire templates

## What this command does NOT do

- Does not modify or deploy templates.
- Does not send test emails.
- Does not migrate templates into Marketing Cloud / Account Engagement.
